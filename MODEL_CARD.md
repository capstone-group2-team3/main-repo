# Model Card: MedDx Severity Classifier

## Model Details

- **Model name:** MedDx severity classifier
- **Repository version:** Current uncommitted audit state on branch `feature/severity-alert-ui`
- **Base model:** `distilbert-base-uncased`
- **Loaded architecture:** `DistilBertForSequenceClassification`
- **Local model path:** `models/severity_classifier` locally and `/app/models/severity_classifier` in Docker
- **Inference target:** CPU-only local inference
- **Labels:** `Routine`, `Urgent`, `Critical`
- **Safety notice:** For clinicians only — supports review, not diagnosis or prescribing.

## Intended Use

This classifier supports prioritization inside MedDx Assistant, a clinician-facing educational capstone prototype for structured laboratory review. It estimates whether a case should be surfaced as Routine, Urgent, or Critical after the application has normalized labs and evaluated configured clinical patterns.

The model is not a diagnostic model, prescribing tool, or treatment recommendation system. It is used only as one component in a guarded pipeline that includes deterministic critical-value override, confidence thresholding, fallback logic, evidence retrieval, and safety sanitization.

## Out-of-Scope Use

- Standalone clinical decision-making
- Diagnosis, prescribing, medication advice, or treatment planning
- Use with real patient records without institutional review, privacy controls, and clinical validation
- Use outside the supported panels, reference ranges, and laboratory units documented by the repository

## Input and Output Format

The service converts the structured report payload into a compact text summary containing panel, age, sex, symptoms, clinical notes, normalized lab classifications, and matched pattern text.

The classifier returns a label and confidence. The severity service exposes a normalized result:

```json
{
  "label": "Urgent",
  "confidence": 0.8423,
  "source": "fine_tuned_model"
}
```

## Decision Policy

The application-level severity decision order is:

1. Analyze configured laboratory values.
2. If any lab is classified `Critical`, return `Critical` with confidence `1.0` and source `critical_override`.
3. Otherwise use the fine-tuned DistilBERT classifier when the local model is available and its confidence meets the configured threshold.
4. Otherwise use the existing rule-based fallback.

The configured confidence threshold is `0.60`.

## Training Data Summary

Training files are present at `data/severity_training_data.jsonl` and `data/severity_val_data.jsonl`. They contain synthetic, project-generated severity examples rather than real patient records or clinician-adjudicated outcomes.

The current repository does not fully document the exact generation run, random seed, reviewer names, or external source licenses for all training examples.

## Evaluation Data Summary

The held-out evaluation file is `eval/heldout.jsonl` with 57 synthetic cases. Each case includes age, sex, selected panel, symptoms, clinical notes, labs, expected patterns, expected abnormal findings, expected missing labs, expected severity, source metadata, and the required safety notice.

The held-out set covers seven supported panels and two useful metadata dimensions: panel and sex. It also records source type/reference metadata.

## Metrics

Current evaluation values from `eval/results.json`:

| Metric | Value |
|---|---:|
| Held-out cases | 57 |
| Successful cases | 57 |
| Top-3 Clinical Pattern Recall | 1.0000 |
| Evidence Grounding Rate | 0.9298 |
| Critical Recall | 1.0000 |
| Severity Accuracy | 0.6316 |
| Average Latency | 268.66 ms |

The majority-class baseline in `eval/baseline_results.json` predicts `Urgent` for every held-out case. It reaches severity accuracy `0.9123` because the held-out severity labels are imbalanced, but critical recall is `0.0000`. The final guarded pipeline has lower overall severity accuracy but preserves critical recall through the deterministic critical override.

## Limitations

- Synthetic data limits generalization claims.
- Severity labels are project labels, not real clinical outcome labels.
- The majority baseline exposes a class-imbalance problem in the held-out severity distribution.
- The fine-tuned classifier over-prioritizes or under-prioritizes some non-critical cases.
- Reference ranges are simplified and do not model lab-specific, age-specific, pregnancy-specific, or institution-specific ranges.
- The repository does not document complete training provenance or clinician review sign-off.

## Ethical and Clinical Safety Considerations

MedDx Assistant is an educational decision-support prototype. It should be reviewed only in controlled demo or educational contexts unless a future team completes privacy, security, regulatory, clinical validation, and human factors work.

The pipeline keeps a fixed safety notice, rewrites unsafe language, avoids diagnostic certainty, and prevents critical laboratory values from being downgraded by the classifier.

## Reproducibility

Use these commands for the current audit workflow:

```bash
.venv/bin/python -m eval.run_eval
.venv/bin/python -m eval.run_baseline
.venv/bin/python -m eval.generate_error_analysis
```

Docker loads the model from `/app/models/severity_classifier` with the bind mount declared in `docker-compose.yml`. Direct local-only loading is verified with Transformers `local_files_only=True`.
