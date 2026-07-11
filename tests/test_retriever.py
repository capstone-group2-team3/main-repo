from types import SimpleNamespace

from app.services.evidence_retrieval_agent import EvidenceRetrievalAgent
from app.services.clinical_pattern_scorer import ClinicalPatternScorer
from app.services.lab_analysis_agent import LabAnalysisAgent
from app.services.lab_normalizer import LabNormalizer


class FakeEmbeddingService:
    def embed_text(self, text):
        self.last_text = text
        return [0.1, 0.2, 0.3]


class FakeClient:
    def __init__(self, strict_hits, relaxed_hits=None):
        self.strict_hits = strict_hits
        self.relaxed_hits = relaxed_hits if relaxed_hits is not None else strict_hits
        self.filters = []

    def query_points(self, **kwargs):
        self.filters.append(kwargs.get("query_filter"))
        hits = self.strict_hits if kwargs.get("query_filter") is not None else self.relaxed_hits
        return SimpleNamespace(points=hits)


def hit(score, **payload):
    return SimpleNamespace(score=score, payload=payload)


def cardiac_context():
    pattern = {
        "pattern_code": "muscle_injury_marker_concern",
        "pattern_name": "Elevated CPK requiring clinician review in context.",
        "evidence_for": ["CPK is High"],
    }
    labs = [{"test_name": "CPK", "status": "High", "value": 450, "unit": "U/L"}]
    return pattern, labs


def test_high_cpk_query_is_panel_test_pattern_and_symptom_aware():
    embedding = FakeEmbeddingService()
    agent = EvidenceRetrievalAgent(embedding_service=embedding)
    pattern, labs = cardiac_context()

    query = agent.build_query(pattern, "Cardiac_Enzymes_Panel", labs, ["chest pain", "shortness of breath"])

    assert "Cardiac_Enzymes_Panel" in query
    assert "High CPK" in query
    assert "muscle_injury_marker_concern" in query
    assert "creatine kinase" in query
    assert "chest pain" in query


def test_high_cpk_retrieves_cardiac_source_and_rejects_creatinine():
    embedding = FakeEmbeddingService()
    cardiac = hit(
        0.78, source_id="cardiac_enzymes", title="Cardiac Enzymes", canonical_panel="Cardiac_Enzymes_Panel",
        related_tests=["CPK"], pattern_codes=["muscle_injury_marker_concern"], section_title="High CPK or CK",
        normalized_terms=["cpk", "ck", "creatine kinase"], chunk_text="### High CPK\n- CPK or CK elevation supports muscle injury context.",
    )
    creatinine = hit(
        0.92, source_id="renal_thyroid", title="Renal", canonical_panel="Renal_Thyroid_Panel",
        related_tests=["Creatinine"], pattern_codes=["kidney_dysfunction_pattern"], section_title="High Creatinine",
        normalized_terms=["creatinine"], chunk_text="### High Creatinine\nReduced renal filtration.",
    )
    agent = EvidenceRetrievalAgent(embedding_service=embedding)
    agent.client = FakeClient([cardiac, creatinine])
    pattern, labs = cardiac_context()

    sources = agent.retrieve_for_pattern(pattern, 3, "Cardiac_Enzymes_Panel", labs, ["chest pain"])

    assert [source["source_id"] for source in sources] == ["cardiac_enzymes"]
    assert "CPK" in sources[0]["snippet"]
    assert "###" not in sources[0]["snippet"]
    assert "creatinine" not in sources[0]["snippet"].lower()
    assert agent.client.filters[0] is not None


def test_exact_ui_cpk_case_scores_expected_pattern_and_keeps_retrieval_relevant():
    normalizer = LabNormalizer()
    lab_results = LabAnalysisAgent(normalizer=normalizer).analyze_labs(
        "Cardiac_Enzymes_Panel",
        normalizer.normalize_labs([
            {"name": "Troponin", "value": 0.2, "unit": "ng/L"},
            {"name": "CPK", "value": 450, "unit": "U/L"},
        ]),
    )
    patterns = ClinicalPatternScorer(normalizer=normalizer).score_patterns(
        "Cardiac_Enzymes_Panel", lab_results, ["chest pain", "shortness of breath"],
    )
    assert [pattern["pattern_code"] for pattern in patterns] == ["muscle_injury_marker_concern"]

    cardiac = hit(
        0.8, source_id="cardiac_enzymes", title="Cardiac Enzymes", canonical_panel="Cardiac_Enzymes_Panel",
        related_tests=["CPK"], pattern_codes=["muscle_injury_marker_concern"], section_title="High CPK or CK",
        normalized_terms=["cpk", "ck"], chunk_text="High CPK or CK supports muscle injury context.",
    )
    creatinine = hit(
        0.95, source_id="renal", title="Renal", canonical_panel="Renal_Thyroid_Panel",
        related_tests=["Creatinine"], pattern_codes=["kidney_dysfunction_pattern"], section_title="High Creatinine",
        normalized_terms=["creatinine"], chunk_text="High creatinine and renal filtration.",
    )
    agent = EvidenceRetrievalAgent(embedding_service=FakeEmbeddingService())
    agent.client = FakeClient([cardiac, creatinine])
    sources = agent.retrieve_for_pattern(
        patterns[0], 3, "Cardiac_Enzymes_Panel",
        [lab for lab in lab_results if lab["status"] not in {"Normal", "Unknown"}],
        ["chest pain", "shortness of breath"],
    )
    assert [source["source_id"] for source in sources] == ["cardiac_enzymes"]
    assert all("creatinine" not in source["snippet"].lower() for source in sources)


def test_renal_creatinine_candidate_remains_relevant():
    agent = EvidenceRetrievalAgent(embedding_service=FakeEmbeddingService())
    renal = hit(
        0.75, source_id="renal_thyroid", title="Renal and Thyroid", canonical_panel="Renal_Thyroid_Panel",
        related_tests=["Creatinine"], pattern_codes=["kidney_dysfunction_pattern"], section_title="High Creatinine",
        normalized_terms=["creatinine"], chunk_text="High creatinine supports kidney function review.",
    )
    agent.client = FakeClient([renal])
    pattern = {"pattern_code": "kidney_dysfunction_pattern", "pattern_name": "Kidney review", "evidence_for": ["Creatinine is High"]}
    labs = [{"test_name": "Creatinine", "status": "High"}]

    sources = agent.retrieve_for_pattern(pattern, 3, "Renal_Thyroid_Panel", labs)

    assert len(sources) == 1
    assert sources[0]["source_id"] == "renal_thyroid"


def test_irrelevant_or_low_similarity_candidates_return_empty():
    agent = EvidenceRetrievalAgent(embedding_service=FakeEmbeddingService(), minimum_similarity=0.4)
    irrelevant = hit(
        0.9, source_id="albumin", title="Albumin", canonical_panel="Albumin_Protein_Panel",
        related_tests=["Albumin"], pattern_codes=["hypoalbuminemia_concern"], section_title="Low Albumin",
        normalized_terms=["albumin"], chunk_text="Low albumin review.",
    )
    weak = hit(
        0.2, source_id="cardiac", title="Cardiac", canonical_panel="Cardiac_Enzymes_Panel",
        related_tests=["CPK"], pattern_codes=["muscle_injury_marker_concern"], section_title="High CPK",
        normalized_terms=["cpk"], chunk_text="High CPK review.",
    )
    agent.client = FakeClient([irrelevant, weak], [irrelevant, weak])
    pattern, labs = cardiac_context()

    assert agent.retrieve_for_pattern(pattern, 3, "Cardiac_Enzymes_Panel", labs) == []


def test_snippet_cleaning_removes_markdown_artifacts():
    agent = EvidenceRetrievalAgent(embedding_service=FakeEmbeddingService())
    assert agent.clean_snippet("### High CPK\n- First point\n* Second point") == "High CPK First point Second point"
