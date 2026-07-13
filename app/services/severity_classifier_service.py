import logging
import os
from pathlib import Path
from typing import Any, Literal


SeverityLabel = Literal["Routine", "Urgent", "Critical"]

logger = logging.getLogger(__name__)


class SeverityClassifierService:
    def __init__(self) -> None:
        self.model_path = Path(os.getenv("SEVERITY_MODEL_PATH", "models/severity_classifier"))
        self.confidence_threshold = self._read_confidence_threshold()
        self.tokenizer: Any | None = None
        self.model: Any | None = None
        self.model_available = False
        self._initialized = False
        self.id2label: dict[int, SeverityLabel] = {
            0: "Routine",
            1: "Urgent",
            2: "Critical",
        }

    def _read_confidence_threshold(self) -> float:
        raw_value = os.getenv("SEVERITY_CONFIDENCE_THRESHOLD", "0.60")

        try:
            threshold = float(raw_value)
        except ValueError:
            logger.warning(
                "Invalid SEVERITY_CONFIDENCE_THRESHOLD=%r; using 0.60.",
                raw_value,
            )
            return 0.60

        if not 0.0 <= threshold <= 1.0:
            logger.warning(
                "SEVERITY_CONFIDENCE_THRESHOLD must be between 0 and 1; using 0.60."
            )
            return 0.60

        return threshold

    def _model_artifact_status(self) -> tuple[bool, str | None]:
        if not self.model_path.exists():
            return False, f"path does not exist: {self.model_path}"

        if not self.model_path.is_dir():
            return False, f"path is not a directory: {self.model_path}"

        required_files = [
            "config.json",
            "tokenizer_config.json",
            "tokenizer.json",
            "model.safetensors",
        ]
        missing = [name for name in required_files if not (self.model_path / name).is_file()]
        if missing:
            return False, f"missing required artifact(s): {', '.join(missing)}"

        return True, None

    def initialize(self) -> bool:
        if self._initialized:
            return self.model_available

        self._initialized = True
        self.model_path = Path(os.getenv("SEVERITY_MODEL_PATH", str(self.model_path)))
        self.confidence_threshold = self._read_confidence_threshold()

        artifacts_available, reason = self._model_artifact_status()
        if not artifacts_available:
            logger.warning(
                "Severity classifier model unavailable at %s; rule-based fallback active (reason: %s).",
                self.model_path,
                reason,
            )
            self.model_available = False
            return False

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )
            self.model.eval()
            config_labels = getattr(self.model.config, "id2label", None)
            if isinstance(config_labels, dict):
                self.id2label = {
                    int(index): label
                    for index, label in config_labels.items()
                    if label in {"Routine", "Urgent", "Critical"}
                } or self.id2label
            self.model_available = True
            logger.warning(
                "Severity classifier loaded successfully from %s (labels=%s, threshold=%.2f).",
                self.model_path,
                self.id2label,
                self.confidence_threshold,
            )
        except Exception as error:
            logger.warning(
                "Severity classifier model unavailable at %s; rule-based fallback active (reason: %s).",
                self.model_path,
                error,
            )
            self.tokenizer = None
            self.model = None
            self.model_available = False

        return self.model_available

    def _has_critical_lab(self, lab_results: list[dict[str, Any]]) -> bool:
        return any(str(lab.get("status", "")).lower() == "critical" for lab in lab_results)

    def _has_abnormal_lab(self, lab: dict[str, Any]) -> bool:
        return str(lab.get("status", "")).lower() not in {"normal", "unknown", ""}

    def _rule_based_fallback(
        self,
        lab_results: list[dict[str, Any]] | None = None,
        clinical_patterns: list[dict[str, Any]] | None = None,
        clinical_warnings: list[Any] | None = None,
        preferred_label: SeverityLabel | None = None,
    ) -> dict[str, Any]:
        labs = lab_results or []
        patterns = clinical_patterns or []
        warnings = clinical_warnings or []

        if self._has_critical_lab(labs):
            return {
                "label": "Critical",
                "confidence": 1.0,
                "source": "critical_override",
            }

        abnormal_count = sum(1 for lab in labs if self._has_abnormal_lab(lab))
        has_pattern_context = bool(patterns)
        has_warning_context = bool(warnings)

        if preferred_label in {"Routine", "Urgent", "Critical"}:
            label: SeverityLabel = preferred_label
        elif abnormal_count >= 2:
            label = "Urgent"
        elif abnormal_count == 1 and (has_pattern_context or has_warning_context):
            label = "Urgent"
        elif abnormal_count == 1:
            label = "Urgent"
        else:
            label = "Routine"

        confidence = 0.82 if label == "Routine" else 0.78
        return {
            "label": label,
            "confidence": confidence,
            "source": "rule_based_fallback",
        }

    def predict_severity(
        self,
        case_text: str,
        lab_results: list[dict[str, Any]] | None = None,
        clinical_patterns: list[dict[str, Any]] | None = None,
        clinical_warnings: list[Any] | None = None,
        rule_based_fallback: SeverityLabel | None = None,
        has_critical_lab_value: bool | None = None,
    ) -> dict[str, Any]:
        labs = lab_results or []

        if has_critical_lab_value is True or self._has_critical_lab(labs):
            return {
                "label": "Critical",
                "confidence": 1.0,
                "source": "critical_override",
            }

        fallback = self._rule_based_fallback(
            lab_results=labs,
            clinical_patterns=clinical_patterns,
            clinical_warnings=clinical_warnings,
            preferred_label=rule_based_fallback,
        )

        if not self._initialized:
            self.initialize()

        if not self.model_available or self.tokenizer is None or self.model is None:
            return fallback

        try:
            import torch
            import torch.nn.functional as functional

            inputs = self.tokenizer(
                case_text,
                return_tensors="pt",
                truncation=True,
                padding=True,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)

            probabilities = functional.softmax(outputs.logits, dim=-1)
            max_prob, predicted_idx = torch.max(probabilities, dim=1)
            confidence = round(float(max_prob.item()), 4)
            predicted_label = self.id2label.get(int(predicted_idx.item()), "Routine")

            if confidence < self.confidence_threshold:
                return fallback

            return {
                "label": predicted_label,
                "confidence": confidence,
                "source": "fine_tuned_model",
            }
        except Exception as error:
            logger.warning("Severity inference failed; using rule-based fallback: %s", error)
            return fallback


severity_service = SeverityClassifierService()
