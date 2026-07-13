import torch

from app.services.severity_classifier_service import SeverityClassifierService


class FakeTokenizer:
    def __call__(self, *args, **kwargs):
        return {}


class LowConfidenceModel:
    def __call__(self, **kwargs):
        return type("Output", (), {"logits": torch.tensor([[0.0, 0.0, 0.0]])})()


class PredictingModel:
    def __init__(self, logits):
        self.logits = torch.tensor([logits])
        self.called = False

    def __call__(self, **kwargs):
        self.called = True
        return type("Output", (), {"logits": self.logits})()


class FailingModel:
    def __call__(self, **kwargs):
        raise RuntimeError("inference unavailable")


def unavailable_service() -> SeverityClassifierService:
    service = SeverityClassifierService()
    service._initialized = True
    service.model_available = False
    return service


def available_service_with_model(model) -> SeverityClassifierService:
    service = SeverityClassifierService()
    service._initialized = True
    service.model_available = True
    service.tokenizer = FakeTokenizer()
    service.model = model
    service.confidence_threshold = 0.60
    return service


def test_initialize_missing_model_fails_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("SEVERITY_MODEL_PATH", str(tmp_path / "missing-model"))

    service = SeverityClassifierService()

    assert service.initialize() is False
    assert service.model_available is False


def test_all_normal_labs_returns_routine_fallback():
    result = unavailable_service().predict_severity(
        case_text="Normal CBC review.",
        lab_results=[
            {"test_name": "Hemoglobin", "status": "Normal"},
            {"test_name": "WBC", "status": "Normal"},
        ],
    )

    assert result == {
        "label": "Routine",
        "confidence": 0.82,
        "source": "rule_based_fallback",
    }


def test_abnormal_non_critical_labs_return_urgent_fallback():
    result = unavailable_service().predict_severity(
        case_text="Low hemoglobin with fatigue.",
        lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
        clinical_patterns=[{"pattern_code": "anemia_pattern"}],
    )

    assert result["label"] == "Urgent"
    assert result["source"] == "rule_based_fallback"


def test_critical_lab_returns_critical_override_with_full_confidence():
    result = unavailable_service().predict_severity(
        case_text="Critical troponin.",
        lab_results=[{"test_name": "Troponin", "status": "Critical"}],
    )

    assert result == {
        "label": "Critical",
        "confidence": 1.0,
        "source": "critical_override",
    }


def test_critical_override_wins_over_routine_model_prediction():
    model = PredictingModel([12.0, 0.0, 0.0])
    result = available_service_with_model(model).predict_severity(
        case_text="Model would call this routine.",
        lab_results=[{"test_name": "Potassium", "status": "Critical"}],
    )

    assert result == {
        "label": "Critical",
        "confidence": 1.0,
        "source": "critical_override",
    }
    assert model.called is False


def test_critical_override_wins_over_urgent_model_prediction():
    model = PredictingModel([0.0, 12.0, 0.0])
    result = available_service_with_model(model).predict_severity(
        case_text="Model would call this urgent.",
        lab_results=[{"test_name": "Potassium", "status": "Critical"}],
    )

    assert result == {
        "label": "Critical",
        "confidence": 1.0,
        "source": "critical_override",
    }
    assert model.called is False


def test_critical_override_wins_regardless_of_model_confidence():
    model = PredictingModel([0.0, 0.0, 0.0])
    result = available_service_with_model(model).predict_severity(
        case_text="Model confidence would be below threshold.",
        lab_results=[{"test_name": "Potassium", "status": "Critical"}],
    )

    assert result == {
        "label": "Critical",
        "confidence": 1.0,
        "source": "critical_override",
    }
    assert model.called is False


def test_critical_override_wins_before_rule_based_fallback():
    result = unavailable_service().predict_severity(
        case_text="Critical result with otherwise urgent fallback context.",
        lab_results=[
            {"test_name": "Potassium", "status": "Critical"},
            {"test_name": "Sodium", "status": "Low"},
        ],
        clinical_patterns=[{"pattern_code": "electrolyte_imbalance"}],
    )

    assert result == {
        "label": "Critical",
        "confidence": 1.0,
        "source": "critical_override",
    }


def test_multiple_labs_are_critical_when_any_one_is_critical():
    result = unavailable_service().predict_severity(
        case_text="One critical lab among multiple results.",
        lab_results=[
            {"test_name": "Sodium", "status": "Normal"},
            {"test_name": "Potassium", "status": "Critical"},
            {"test_name": "Calcium", "status": "Normal"},
        ],
    )

    assert result["label"] == "Critical"
    assert result["confidence"] == 1.0
    assert result["source"] == "critical_override"


def test_symptoms_alone_do_not_force_critical():
    result = unavailable_service().predict_severity(
        case_text="Symptoms: chest pain, jaw pain, shortness of breath.",
        lab_results=[{"test_name": "Troponin", "status": "Normal"}],
    )

    assert result["label"] == "Routine"
    assert result["source"] == "rule_based_fallback"


def test_low_confidence_model_uses_fallback():
    service = SeverityClassifierService()
    service._initialized = True
    service.model_available = True
    service.tokenizer = FakeTokenizer()
    service.model = LowConfidenceModel()
    service.confidence_threshold = 0.60

    result = service.predict_severity(
        case_text="Low hemoglobin.",
        lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
    )

    assert result["label"] == "Urgent"
    assert result["source"] == "rule_based_fallback"


def test_inference_exception_uses_fallback():
    service = SeverityClassifierService()
    service._initialized = True
    service.model_available = True
    service.tokenizer = FakeTokenizer()
    service.model = FailingModel()

    result = service.predict_severity(
        case_text="Normal findings.",
        lab_results=[{"test_name": "Hemoglobin", "status": "Normal"}],
    )

    assert result["label"] == "Routine"
    assert result["source"] == "rule_based_fallback"
