# Dataset Card

## Overview

MedDx Assistant does not use real patient data. All data used for development, indexing, and evaluation is either synthetic or derived from public, general medical reference sources.

## Data Sources

### 1. Clinical Configuration Data (`data/`)
- `reference_ranges.json` — normal/abnormal lab value thresholds
- `lab_name_aliases.json` — alternate names mapped to standard lab test names (e.g., Hgb → Hemoglobin, CK → CPK, TnI/TnT → Troponin)
- `panel_templates.json` — supported lab panels and their required tests
- `clinical_patterns.json` — rule-based clinical pattern definitions (conditions + logic)

These were manually curated based on general, publicly available medical reference guidance and are simplified for educational use.

### 2. Medical Knowledge Base (`medical_knowledge/`)
Markdown documentation files covering clinical pattern interpretation (e.g., anemia, infection/inflammation, hyperglycemia, kidney function, thyroid imbalance, electrolyte imbalance). These files are chunked, embedded, and indexed into Qdrant for retrieval-augmented generation (RAG).

### 3. Synthetic Evaluation Cases (`eval/heldout.jsonl`)
- 50 hand-validated synthetic cases used to evaluate the system.
- Each case includes: patient age/sex, symptoms, lab values, selected panel, and an expected clinical pattern.
- Cases are distributed across all supported lab panels (CBC, Diabetic/Glucose, Renal & Thyroid, Lipids & Inflammation, Cardiac Enzymes, Electrolytes & Calcium, Coagulation, Protein/Albumin, Pancreatic/Salivary Enzyme).
- Difficulty levels (easy/medium/hard) vary by number of abnormal labs and symptoms present.
- A teammate manually validated expected labels before the final evaluation run.

### 4. Severity Classifier Training Data
- Synthetic cases with severity labels (Routine / Urgent / Critical).
- Labels were derived programmatically from existing rule-based logic (`clinical_patterns.json` status/pattern combinations), not from real clinical outcomes or human clinician labeling.
- Used to fine-tune a small DistilBERT (`distilbert-base-uncased`) classifier.

## Intended Use

This dataset and the resulting models are intended **for educational and evaluation purposes only** within this capstone project. They do not represent real patient records and should not be used for actual clinical decision-making.

## Known Limitations

- Synthetic data cannot capture the full complexity or variability of real clinical presentations.
- Severity labels are rule-derived, not clinician-validated, so the severity classifier reflects the rules it learned from, not ground-truth clinical urgency.
- Reference ranges are simplified and may not reflect lab-specific, age-specific, or sex-specific variation.
