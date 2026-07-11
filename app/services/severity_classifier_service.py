import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

class SeverityClassifierService:
    def __init__(self):
        model_path = "./models/severity_classifier"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.id2label = {0: "Routine", 1: "Urgent", 2: "Critical"}

    def predict_severity(self, case_text: str, has_critical_lab_value: bool = False, rule_based_fallback: str = "Routine") -> dict:
        if has_critical_lab_value:
            return {
                "severity_label": "Critical",
                "confidence": 1.0,
                "source": "hard_override"
            }

        inputs = self.tokenizer(case_text, return_tensors="pt", truncation=True, padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        probabilities = F.softmax(outputs.logits, dim=-1)
        max_prob, predicted_idx = torch.max(probabilities, dim=1)
        
        confidence = round(max_prob.item(), 2)
        predicted_label = self.id2label[predicted_idx.item()]

        if confidence < 0.6:
            return {
                "severity_label": rule_based_fallback,
                "confidence": confidence,
                "source": "rule_fallback"
            }

        return {
            "severity_label": predicted_label,
            "confidence": confidence,
            "source": "model"
        }

severity_service = SeverityClassifierService()