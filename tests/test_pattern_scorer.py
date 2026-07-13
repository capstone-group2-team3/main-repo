from app.services.clinical_pattern_scorer import ClinicalPatternScorer


def test_anemia_pattern_triggered_with_display_panel_name():
    scorer = ClinicalPatternScorer()
    result = scorer.score_patterns(
        selected_panel="CBC Panel",
        lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
        symptoms=[],
    )

    assert len(result) >= 1
    assert result[0]["pattern_code"] == "anemia_pattern"
    assert result[0]["rank"] == 1


def test_anemia_pattern_triggered_with_internal_panel_key():
    scorer = ClinicalPatternScorer()
    result = scorer.score_patterns(
        selected_panel="CBC_Panel",
        lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
        symptoms=[],
    )

    assert len(result) >= 1
    assert result[0]["pattern_code"] == "anemia_pattern"
    assert result[0]["rank"] == 1


def test_no_match_returns_empty():
    scorer = ClinicalPatternScorer()
    result = scorer.score_patterns(
        selected_panel="CBC_Panel",
        lab_results=[],
        symptoms=[],
    )

    assert result == []
