# Severity Labeling Schema

This document defines the rules for automatically labeling synthetic cases with severity levels (`Routine`, `Urgent`, `Critical`) for the Fine-tuned Severity Classifier (T31-T32).

## 1. Base Levels (Default Severity)
Each clinical pattern in `clinical_patterns.json` is assigned a base severity:
- **Routine**: Mild abnormal results with no immediate danger (e.g., Anemia, Thyroid Imbalance, Hyperglycemia).
- **Urgent**: Conditions requiring timely clinical attention (e.g., Infection, Kidney Dysfunction, Electrolyte Imbalance).
- **Critical**: Life-threatening patterns (e.g., "Emergency warning", "Needs urgent clinician review").

## 2. Hard Override Rule (Critical Safety Net)
Regardless of the pattern's `default_severity`, if ANY individual lab value in the case is classified as **Critical** (Critical Low or Critical High), the overall case severity is IMMEDIATELY escalated to **Critical**.
This is a strict safety override to ensure the model never downgrades a genuinely critical lab result.