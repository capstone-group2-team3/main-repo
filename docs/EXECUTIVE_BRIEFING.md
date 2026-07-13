# Executive Briefing: MedDx Assistant

## 1. Executive Summary

MedDx Assistant is an AI-powered laboratory review prototype for clinicians. It normalizes submitted lab values, flags abnormal and critical findings, suggests configured clinical patterns, retrieves supporting evidence, estimates severity, and generates Markdown/HTML/PDF reports.

For clinicians only — supports review, not diagnosis or prescribing.

## 2. Stakeholder and Problem

The target stakeholder is a clinician or clinical reviewer who needs a fast first pass over structured laboratory panels. Manual review can be slow and inconsistent when multiple values, symptoms, and reference materials must be cross-checked.

## 3. Proposed Solution

The system provides a guarded decision-support workflow: normalize labs, classify findings, score clinical patterns, retrieve evidence, classify severity, sanitize unsafe language, persist the report, and show results in a Next.js dashboard.

## 4. Primary AI Capability

The primary AI capability is severity prioritization using a fine-tuned DistilBERT sequence classifier, with deterministic critical override and rule-based fallback. PubMedBERT embeddings support retrieval-augmented evidence search through Qdrant.

## 5. System Architecture

FastAPI coordinates the backend service layer. SQLite stores report cases, pattern results, retrieved sources, generated reports, severity records, and evaluation records. Qdrant stores embedded medical knowledge chunks. The frontend is a Next.js application. Docker Compose runs backend, frontend, Qdrant, and an optional indexer profile.

## 6. Data Sources and Permissions

The project uses configured reference ranges, aliases, clinical patterns, markdown knowledge files, and synthetic training/evaluation cases. No real patient records are intentionally used. Full source licensing and public availability details for all curated medical knowledge files are not documented in the current repository.

## 7. Safety Architecture

Safety controls include the fixed clinician-only notice, recursive safety sanitization, no diagnosis/prescribing/treatment recommendation claims, deterministic critical-value override, confidence thresholding, fallback behavior, and evidence grounding. Potassium `7.4 mEq/L` is Critical under the active `critical_high: 6.5` configuration.

## 8. Evaluation Methodology

`eval/run_eval.py` evaluates the full pipeline against `eval/heldout.jsonl`. The run records top-3 pattern recall, evidence grounding, abnormal-finding match, missing-lab match, safety notice presence, severity accuracy, critical recall, and latency. Runtime inference is deterministic for a fixed repository state and model artifacts; no random seed is used in the evaluation harness.

## 9. Baseline

`eval/run_baseline.py` implements a majority-class severity baseline on the same 57 held-out cases and same primary metric, severity accuracy. The baseline predicts `Urgent` for every case.

## 10. Evaluation Results

| Metric | Value |
|---|---:|
| Held-out cases | 57 |
| Successful cases | 57 |
| Top-3 Clinical Pattern Recall | 1.0000 |
| Evidence Grounding Rate | 0.9298 |
| Critical Recall | 1.0000 |
| Severity Accuracy | 0.6316 |
| Average Latency | 268.66 ms |
| Baseline Severity Accuracy | 0.9123 |
| Baseline Critical Recall | 0.0000 |

The baseline has higher overall accuracy because the held-out severity set is imbalanced, but it misses all Critical cases. The final system preserves Critical recall through deterministic override logic.

## 11. Error Analysis

`eval/error_analysis.json` documents 22 observed failures. Grouping by reason: severity accuracy `21`, evidence grounding `4`. Grouping by panel: CBC `5`, Diabetic `4`, Renal/Thyroid `4`, Lipids/Inflammation `4`, Albumin/Protein `3`, Cardiac Enzymes `2`.

Next-iteration hypothesis: improve severity calibration for non-critical synthetic cases and add evidence chunks/metadata for pattern-linked grounding gaps without weakening the critical override.

## 12. Five Actual Failure Cases

| Case | Panel | Expected | Actual | Error Category | Likely Cause |
|---|---|---|---|---|---|
| heldout-001 | CBC_Panel | Urgent | Critical | severity_accuracy | Fine-tuned model over-prioritized anemia-pattern case |
| heldout-003 | CBC_Panel | Urgent | Critical | evidence_grounding, severity_accuracy | Missing pattern-linked evidence plus model over-prioritization |
| heldout-005 | CBC_Panel | Urgent | Routine | evidence_grounding, severity_accuracy | Missing pattern-linked evidence plus model under-prioritization |
| heldout-007 | CBC_Panel | Urgent | Critical | evidence_grounding, severity_accuracy | Multi-pattern CBC case over-prioritized and not fully grounded |
| heldout-011 | Diabetic_Panel | Urgent | Critical | severity_accuracy | Fine-tuned model over-prioritized non-critical diabetic case |

These cases are derived from `eval/error_analysis.json`; no invented failures are included.

## 13. Deployment Shape

The selected deployment shape is local Docker Compose plus a public portfolio artifact. Docker Compose runs the backend, frontend, Qdrant, persistent SQLite runtime volume, generated-report volume, Hugging Face cache volume, and read-only local severity model bind mount. The public portfolio artifact URL is not present in the repository and remains a human deliverable.

## 14. Limitations

The system is an educational prototype. It uses synthetic data, simplified reference ranges, limited panels, non-clinician-adjudicated severity labels, and local model artifacts. It has not been clinically validated and should not be used as a medical device.

## 15. Specific Future Work

- Calibrate severity classifier behavior for non-critical cases.
- Expand evidence chunks and pattern metadata for grounding gaps.
- Add clinician-reviewed severity labels.
- Add authentication and authorization before any real deployment.
- Expand panels only with documented source permissions.
- Add privacy review before real patient data is considered.

## 16. Readiness Decision

READY — HUMAN DELIVERABLES REMAIN. Technical validation passed in this audit. Human deliverables remain: demo video, public portfolio artifact URL, final presentation, PR approvals, project board closure, and reflections.

## 17. Final Safety Notice

For clinicians only — supports review, not diagnosis or prescribing.
