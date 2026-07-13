# Architecture

## Overview

MedDx Assistant follows an agentic pipeline architecture: each stage of clinical analysis is handled by a focused, single-responsibility service, orchestrated by a central `AgentOrchestrator`.

## Data Flow
Doctor submits structured lab report
↓
FastAPI Backend (POST /reports/analyze)
↓
Agent Orchestrator
↓

Lab Normalizer — standardize test/symptom names
↓
Lab Analysis Agent — classify values (Low/Normal/High/Critical)
↓
Clinical Pattern Scorer — match abnormal labs to known patterns
↓
Severity Classifier — estimate case urgency (Routine/Urgent/Critical)
↓
Evidence Retrieval Agent (RAG) — search Qdrant for supporting medical text
↓
Report Generator Agent — build structured Markdown/HTML report
↓
Safety Agent — sanitize unsafe phrasing, enforce safety notice
↓
Final Doctor-Facing Clinical Support Report
## Services

| Service | Responsibility |
|---|---|
| `lab_normalizer.py` | Standardizes lab test names and symptom text using alias mappings |
| `lab_analysis_agent.py` | Compares lab values against reference ranges and classifies them |
| `clinical_pattern_scorer.py` | Scores and ranks candidate clinical patterns from abnormal labs |
| `severity_classifier.py` | Fine-tuned DistilBERT model producing a severity label + confidence, with a rule-based fallback for low-confidence predictions |
| `embedding_service.py` | Converts text into vector embeddings (PubMedBERT, with MiniLM fallback) |
| `knowledge_indexer.py` | Chunks medical knowledge files and indexes them into Qdrant |
| `evidence_retrieval_agent.py` | Builds search queries from clinical patterns and retrieves relevant evidence from Qdrant |
| `report_generator_agent.py` | Assembles the final structured report (Markdown + HTML) |
| `safety_agent.py` | Removes/rewrites unsafe clinical language and enforces the safety notice |

## Database Schema

| Table | Purpose |
|---|---|
| `report_cases` | Stores each submitted patient case |
| `lab_results` | Individual lab test results per case |
| `clinical_pattern_results` | Top-ranked clinical patterns per case |
| `retrieved_sources` | Medical evidence snippets retrieved per pattern |
| `generated_reports` | Markdown/HTML report content and file paths |
| `knowledge_docs_metadata` | Metadata for indexed medical knowledge files |
| `evaluation_cases` | Held-out test cases for evaluation |
| `evaluation_results` | Evaluation run outputs (predicted vs. expected) |

## Infrastructure

- **Backend:** FastAPI application served via Uvicorn
- **Database:** SQLite (via SQLAlchemy ORM)
- **Vector Store:** Qdrant, running as a Docker Compose service alongside the backend
- **Frontend:** Next.js application (TypeScript, Tailwind CSS, shadcn/ui)
- **Containerization:** Docker Compose orchestrates the FastAPI service and Qdrant together

## Design Principles

- **Agentic, not monolithic:** each pipeline stage is an independent, testable service.
- **Safety by design:** every response passes through a dedicated safety layer before reaching the clinician.
- **Explainability:** every clinical pattern suggestion includes supporting evidence and lists missing evidence, so the clinician can see *why* a pattern was suggested.
