# MedDx Assistant

## Overview

MedDx Assistant is a clinician-facing Clinical Decision Support system that helps doctors review structured lab results. It analyzes abnormal lab values, matches them against known clinical patterns, retrieves supporting medical evidence using Retrieval-Augmented Generation (RAG), classifies case severity, and generates a structured clinical review report.

**Important:** This tool supports clinician review only. It does not provide a final diagnosis, does not prescribe medication, and does not replace physician judgment.

## Problem Statement

Clinicians reviewing lab results often need to cross-reference abnormal values against clinical knowledge manually, which is time-consuming. MedDx Assistant automates this first pass: it flags abnormal values, suggests possible clinical patterns worth investigating, estimates case urgency, and surfaces relevant medical documentation to support (not replace) clinical judgment.

## Architecture Summary

**Backend:** Python, FastAPI, SQLAlchemy, SQLite, Pydantic, pytest
**Frontend:** Next.js, TypeScript, Tailwind CSS, Framer Motion, Lucide React
**Vector Database:** Qdrant (medical knowledge embeddings)
**Embedding Model:** NeuML/pubmedbert-base-embeddings (medical-domain), with fallback to sentence-transformers/all-MiniLM-L6-v2
**Severity Model:** Fine-tuned DistilBERT (distilbert-base-uncased) classifier trained on synthetic labeled cases

### Analysis Pipeline

Request → Panel Validation → Save Case → Lab Normalization →
Missing Required Labs Check → Lab Classification → Save Results →
Clinical Pattern Scoring → Save Patterns → Severity Classification →
Evidence Retrieval (RAG) → Dashboard JSON → Safety Sanitization →
Markdown Report → HTML Report → Save Report → API Response

### Core Services

- `lab_normalizer` — standardizes lab test names and symptom text
- `lab_analysis_agent` — classifies lab values (Low/Normal/High/Critical)
- `clinical_pattern_scorer` — matches abnormal labs to known clinical patterns
- `severity_classifier` — fine-tuned model estimating case urgency (Routine/Urgent/Critical)
- `evidence_retrieval_agent` — retrieves relevant medical evidence via RAG/Qdrant
- `report_generator_agent` — builds the structured clinician-facing report
- `safety_agent` — sanitizes unsafe phrasing and enforces the safety notice

## Features

- Lab result analysis against configurable reference ranges
- Clinical pattern matching (e.g., anemia, hyperglycemia, kidney dysfunction)
- Case severity classification (Routine / Urgent / Critical) with confidence score and rule-based fallback
- RAG-based evidence retrieval from a curated medical knowledge base
- Automatic safety sanitization of clinical language
- Markdown and HTML report generation with download support
- Interactive Next.js dashboard for clinicians, with a severity alert banner

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/templates` | GET | List available lab panels |
| `/templates/{panel_name}` | GET | Get a specific panel template |
| `/reports/analyze` | POST | Run the full analysis pipeline |
| `/reports/{report_id}` | GET | Retrieve a generated report |
| `/cases/{case_id}` | GET | Retrieve a saved case |
| `/index/medical-knowledge` | POST | Index medical knowledge into Qdrant |

## Setup

### Requirements
- Python 3.11+
- Docker & Docker Compose
- Node.js (for the Next.js frontend)

### Installation

```bash
pip install -r requirements.txt --break-system-packages
```

## Run the Full Project

### Prerequisites

- Docker Desktop or Docker Engine with Docker Compose
- Optional local severity model artifact at `models/severity_classifier/`

Start the complete local system:

```bash
docker compose up --build
```

Optional detached mode:

```bash
docker compose up -d --build
```

Open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Backend health: http://localhost:8000/health
- Qdrant dashboard: http://localhost:6333/dashboard

Stop:

```bash
docker compose down
```

Index the medical knowledge base when Qdrant is empty or after knowledge files change:

```bash
docker compose run --rm indexer
```

Alternative setup profile command:

```bash
docker compose --profile setup up indexer
```

The normal `docker compose up --build` path does not reindex or delete Qdrant collections. Qdrant data is stored in the `qdrant_storage` volume, SQLite is stored in the `meddx_data` volume, and generated Markdown/HTML/PDF reports are stored in the `meddx_reports` volume.

Severity model behavior:

- With `./models/severity_classifier` mounted into the backend container, severity predictions can return `source = fine_tuned_model`.
- If the model directory is missing or cannot be loaded, the backend still starts and uses `source = rule_based_fallback`.
- Critical lab values override all model output and return `Critical`.

Manual model checkpoint cleanup, after confirming the final root model files load:

```bash
du -sh models/severity_classifier/checkpoint-*
rm -rf models/severity_classifier/checkpoint-*
```

Keep the final root artifacts: `config.json`, model weights, tokenizer files, and result JSON files.

Troubleshooting:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f qdrant
docker compose ps
```

## Local Development

Start the backend and Qdrant vector database:

```bash
docker compose up -d
uvicorn app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Index the medical knowledge base (first run only):

```bash
curl -X POST http://localhost:8000/index/medical-knowledge
```

## How to Run Evaluation

```bash
python eval/run_eval.py
```

Results are saved to `eval/results.json`.
The evaluation run intentionally refreshes both `eval/results.json` and `eval/failure_cases.md` so the latest metrics and observed failure analysis are kept together.

## Results

- Top-3 Clinical Pattern Recall, Evidence Grounding Rate, Average Latency, Safety Notice Presence Rate, Abnormal Findings Match Rate, Severity Accuracy, and Critical Recall: see `eval/results.json` after running the evaluation harness.
- Severity Classifier: overall accuracy and Critical-case recall are reported in `eval/results.json` (Critical recall is prioritized to stay near 100%, since missing a truly critical case is the highest-risk failure mode).

## Testing

- `pytest`: 71 passed
- `python -m compileall app`: PASS
- `npm run lint`: PASS
- `npm run build`: PASS

## Limitations

- Clinical patterns and reference ranges are simplified for educational use and may differ by lab, age, sex, and clinical context.
- The severity classifier is trained on synthetic data with labels derived from rule-based logic, not real clinical outcomes.
- The system does not provide a final diagnosis, treatment plan, or medication advice.
- Evaluation dataset is synthetic, not real patient data.

## Team Roles

| Role | Responsibilities |
|---|---|
| Person 1 — Backend/API | FastAPI, routes, Docker Compose, Agent Orchestrator |
| Person 2 — Data/Evaluation | Reference data, evaluation set, run_eval.py, severity evaluation, failure analysis |
| Person 3 — RAG/AI Pipeline | Embedding service, Qdrant, knowledge indexer, evidence retrieval, severity classifier fine-tuning |
| Person 4 — UI/Docs/Presentation | Next.js dashboard, severity alert UI, README, architecture docs, demo |

## Safety Notice

This tool supports clinician review only. It does not provide a final diagnosis, does not prescribe medication, and does not replace physician judgment. The severity indicator is a supportive AI-generated alert based on synthetic training data — it does not replace clinical judgment and must be verified by the treating physician.
