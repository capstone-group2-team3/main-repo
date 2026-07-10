from app.services.clinical_pattern_scorer import ClinicalPatternScorer
import json

scorer = ClinicalPatternScorer()

print("Patterns loaded:")
for i, p in enumerate(scorer.patterns):
    print(f"\n[{i}] {p.get('pattern_code')}")
    print(f"    Panel: {p.get('panel')}")
    print(f"    Required Labs: {p.get('required_abnormal_labs')}")

print("\n\n--- Test ---")
result = scorer.score_patterns(
    selected_panel="CBC_Panel",
    lab_results=[{"test_name": "Hemoglobin", "status": "Low"}],
    symptoms=[],
)
print(f"Result: {result}")

# Check normalizer
print(f"\n--- Normalization ---")
print(f"Hemoglobin -> {scorer.normalizer.normalize_lab_name('Hemoglobin')}")
print(f"Low -> lowercase: {'Low'.lower()}")
