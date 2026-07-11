from app.services.severity_classifier_service import severity_service

def test_normal_prediction():
    text = "Patient presents with mild symptoms, no immediate danger."
    result = severity_service.predict_severity(case_text=text, has_critical_lab_value=False)
    
    assert "severity_label" in result
    assert result["source"] in ["model", "rule_fallback"]
    assert 0.0 <= result["confidence"] <= 1.0
    
def test_hard_override():
    text = "Patient has some mild pain."
    result = severity_service.predict_severity(case_text=text, has_critical_lab_value=True)
    
    assert result["severity_label"] == "Critical"
    assert result["confidence"] == 1.0
    assert result["source"] == "hard_override"

def test_fallback_behavior():
    text = "jdksgh dfkjgh dkfjhg"
    result = severity_service.predict_severity(case_text=text, has_critical_lab_value=False, rule_based_fallback="Urgent")
    
    if result["source"] == "rule_fallback":
        assert result["severity_label"] == "Urgent"
        assert result["confidence"] < 0.6