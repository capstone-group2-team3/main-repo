# Model Card: Severity Classification Pipeline

## Model Details
- **Base Model:** `distilbert-base-uncased` (66M parameters), optimized for CPU deployment.
- **Task:** 3-class text classification (`Routine`, `Urgent`, `Critical`) for clinical report prioritizing.

## Training Data & Methodology
- **Dataset Size:** ~1,200 total synthetic medical text scenarios scaled up locally.
- **Label Derivation:** Ground truth targets were programmatically derived using the structured rule-based clinical scoring framework.

## Evaluation Results
- **Overall Accuracy:** 87.72% (on synthetic heldout distribution).
- **Critical Case Recall:** 0.00% 
  - *Engineering Notice:* Evaluation detected a severe regression during script execution. While the standalone model correctly identifies critical cases via the API (Swagger), local pipeline execution via `run_eval.py` forces a silent fallback to `Routine`. This indicates a recent architecture refactoring (e.g., lazy loading or dependency injection issues) is suppressing the safety hard-overrides.
- *Note: All 7 severe underclassifications (Critical -> Routine) involving acute markers (e.g., high Troponin, chest pain) have been automatically logged in `eval/failure_cases.md` for backend debugging.*

## Limitations & Safety Notice
> ⚠️ **CRITICAL LIMITATION:** This model is trained entirely on programmatically generated synthetic data and has **no real-world clinical validation**. It must never be relied upon for standalone clinical diagnostic decisions. Final verification and judgment by a licensed medical practitioner are strictly required at all times.