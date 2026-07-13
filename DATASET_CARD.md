# Dataset Card: MedDx Assistant Data

## Dataset Purpose

MedDx Assistant uses project-curated configuration, synthetic training data, synthetic held-out evaluation cases, and local medical knowledge markdown files to support an educational laboratory review prototype.

The data is intended for capstone development, testing, and demonstration. It is not intended for direct clinical deployment.

## Sources and Availability

- `data/reference_ranges.json`: configured laboratory thresholds.
- `data/lab_name_aliases.json`: lab aliases such as Hgb, CK, and TnI.
- `data/panel_templates.json`: supported panels and required tests.
- `data/clinical_patterns.json`: deterministic clinical pattern rules.
- `data/severity_training_data.jsonl`: synthetic severity classifier training records.
- `data/severity_val_data.jsonl`: synthetic severity validation records.
- `eval/heldout.jsonl`: held-out synthetic evaluation set.
- `medical_knowledge/`: markdown knowledge files indexed into Qdrant for retrieval.

The repository does not fully document every source license or public availability detail for the curated medical knowledge and configuration files.

## Collection or Creation Process

The current repository indicates that the severity data and evaluation cases are synthetic/project-generated. The held-out cases include validation notes and expected outputs, but the current repository does not document individual reviewer names, dates, or a formal clinical adjudication protocol.

No real patient records are intentionally used.

## Schema

Held-out cases in `eval/heldout.jsonl` include:

- `case_id`
- `age`
- `sex`
- `selected_panel`
- `symptoms`
- `clinical_notes`
- `labs`
- `expected_patterns`
- `expected_abnormal_findings`
- `expected_missing_labs`
- `expected_severity`
- `expected_safety_notice`
- `source_reference`
- `source_type`
- `validation_notes`

## Held-Out Split

The held-out evaluation set contains 57 cases and is separate from `data/severity_training_data.jsonl` and `data/severity_val_data.jsonl`.

Panel distribution:

| Panel | Cases |
|---|---:|
| Albumin_Protein_Panel | 6 |
| CBC_Panel | 9 |
| Cardiac_Enzymes_Panel | 8 |
| Diabetic_Panel | 9 |
| Electrolytes_Calcium_Panel | 8 |
| Lipids_Inflammation_Panel | 8 |
| Renal_Thyroid_Panel | 9 |

Severity distribution:

| Severity | Cases |
|---|---:|
| Critical | 5 |
| Urgent | 52 |

## Metadata Dimensions

The held-out set includes panel, sex, age, source type, source reference, symptoms, and validation notes. Sex distribution is 27 female and 30 male cases.

## Quality Checks

Repository checks verify the held-out schema, case count, unique case identifiers, expected safety notice, and evaluation compatibility. The evaluation harness verifies pattern recall, evidence grounding, abnormal-finding matching, missing-lab matching, safety notice presence, severity accuracy, critical recall, and latency.

## Known Limitations

- Synthetic cases are not a substitute for de-identified real clinical validation.
- The held-out severity distribution is imbalanced toward Urgent.
- Demographic coverage is limited and not designed for fairness claims.
- Reference ranges are simplified.
- Source licensing and reviewer provenance are not fully documented in the current repository.

## Privacy and Safety Considerations

The dataset should not contain patient-identifying information. Examples and fixtures use fictional data. The project should not ingest real patient records without privacy review, data-use approval, access controls, and de-identification safeguards.

## Intended and Prohibited Use

Intended use: educational evaluation of the MedDx Assistant prototype.

Prohibited use: diagnosis, prescribing, treatment recommendation, autonomous triage, or clinical deployment without formal validation and governance.

For clinicians only — supports review, not diagnosis or prescribing.
