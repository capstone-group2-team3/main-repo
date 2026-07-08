from app.services.pattern_scorer import ClinicalPatternScorer

def test_anemia_pattern_triggered():
    scorer = ClinicalPatternScorer()
    result = scorer.score_patterns(
        abnormal_labs=[{"test_name": "Hemoglobin", "status": "Low"}]
    )
    assert len(result) >= 1
    assert result[0]["pattern_code"] == "anemia_pattern"
    assert result[0]["rank"] == 1

def test_no_match_returns_empty():
    scorer = ClinicalPatternScorer()
    result = scorer.score_patterns(abnormal_labs=[])
    assert result == []