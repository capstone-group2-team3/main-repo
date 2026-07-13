from app.services.pattern_scorer import ClinicalPatternScorer as MyScorer
from app.services.clinical_pattern_scorer import ClinicalPatternScorer as TheirScorer
from app.services.lab_normalizer import LabNormalizer


def test_compare_both_scorers_same_input():
    lab_results = [
        {"test_name": "Hemoglobin", "status": "Low", "value": 10.2, "unit": "g/dL"},
    ]
    symptoms = ["fatigue"]
    selected_panel = "CBC_Panel"

    my_scorer = MyScorer()
    my_result = my_scorer.score_patterns(
        selected_panel=selected_panel,
        lab_results=lab_results,
        symptoms=symptoms,
    )

    their_scorer = TheirScorer(normalizer=LabNormalizer())
    their_result = their_scorer.score_patterns(
        selected_panel=selected_panel,
        lab_results=lab_results,
        symptoms=symptoms,
    )

    print("\n--- نتيجة ملفي (pattern_scorer.py) ---")
    print(my_result)

    print("\n--- نتيجة ملف زميلي (clinical_pattern_scorer.py) ---")
    print(their_result)

    assert True