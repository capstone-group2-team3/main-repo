from app.services.severity_classifier_service import SeverityClassifierService


def make_service():
    service = SeverityClassifierService()
    service._initialized = True
    service.model_available = False
    return service

def test_normal_prediction():
    service = make_service()
    text = "Patient presents with mild symptoms, no immediate danger."
    result = service.predict_severity(
        case_text=text,
        lab_results=[{"test_name": "Hemoglobin", "status": "Normal"}],
    )
    
    assert result["label"] == "Routine"
    assert result["source"] == "rule_based_fallback"
    assert 0.0 <= result["confidence"] <= 1.0
    
def test_hard_override():
    service = make_service()
    text = "Patient has some mild pain."
    result = service.predict_severity(
        case_text=text,
        lab_results=[{"test_name": "Troponin", "status": "Critical"}],
    )
    
    assert result["label"] == "Critical"
    assert result["confidence"] == 1.0
    assert result["source"] == "critical_override"

def test_fallback_behavior():
    service = make_service()
    text = "jdksgh dfkjgh dkfjhg"
    result = service.predict_severity(
        case_text=text,
        lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
        rule_based_fallback="Urgent",
    )
    
    assert result["label"] == "Urgent"
    assert result["source"] == "rule_based_fallback"
