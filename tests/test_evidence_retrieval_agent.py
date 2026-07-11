from app.services.evidence_retrieval_agent import EvidenceRetrievalAgent


def test_build_query_combines_pattern_name_and_evidence():
    agent = EvidenceRetrievalAgent()
    pattern = {
        "pattern_name": "Low Hemoglobin levels indicating potential anemia.",
        "evidence_for": ["Hemoglobin Low"],
    }
    query = agent.build_query(pattern)

    assert "Hemoglobin" in query
    assert "anemia" in query.lower()


def test_retrieve_for_pattern_returns_results():
    agent = EvidenceRetrievalAgent()
    pattern = {
        "pattern_code": "anemia_pattern",
        "pattern_name": "Low Hemoglobin levels indicating potential anemia.",
        "evidence_for": ["Hemoglobin Low"],
    }

    results = agent.retrieve_for_pattern(pattern, top_k=3)

    assert isinstance(results, list)
    assert len(results) <= 3

    if results:
        first = results[0]
        assert "source_id" in first
        assert "title" in first
        assert "snippet" in first
        assert "similarity_score" in first


def test_retrieve_for_patterns_returns_one_entry_per_pattern():
    agent = EvidenceRetrievalAgent()
    patterns = [
        {
            "pattern_code": "anemia_pattern",
            "pattern_name": "Low Hemoglobin levels indicating potential anemia.",
            "evidence_for": ["Hemoglobin Low"],
        },
        {
            "pattern_code": "hyperglycemia_pattern",
            "pattern_name": "Elevated Glucose indicating impaired glucose tolerance.",
            "evidence_for": ["Glucose High"],
        },
    ]

    results = agent.retrieve_for_patterns(patterns, top_k=3)

    assert len(results) == 2
    assert results[0]["pattern_code"] == "anemia_pattern"
    assert results[1]["pattern_code"] == "hyperglycemia_pattern"
    assert "retrieved_sources" in results[0]