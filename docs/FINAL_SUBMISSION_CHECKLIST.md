# Final Submission Checklist

## Technical Items Codex Verified

| Requirement | Status | Evidence/path | Owner action | Blocker |
|---|---|---|---|---|
| FastAPI backend | PASS | `app/main.py`, `app/api/routes.py` | Keep final checks passing | None |
| Next.js frontend | PASS | `frontend/src/app/page.tsx`, `frontend/src/components/meddx/` | Keep final checks passing | None |
| SQLite persistence | PASS | `app/db/`, `docker-compose.yml` runtime volume | None | None |
| Qdrant RAG pipeline | PASS | `app/services/knowledge_indexer.py`, `app/services/evidence_retrieval_agent.py` | Run indexer for fresh deployments | None |
| PubMedBERT embeddings | PASS | `app/services/embedding_service.py`, `.env.example` | Ensure model cache/network availability for indexing | None |
| Fine-tuned DistilBERT classifier | PASS | `models/severity_classifier/config.json`, `app/services/severity_classifier_service.py` | Keep local model artifact available | None |
| Critical override | PASS | `app/services/severity_classifier_service.py`, tests | None | None |
| Safety notice | PASS | `app/services/safety_agent.py`, tests | None | None |
| Markdown/HTML/PDF reports | PASS | `app/services/report_generator_agent.py` | None | None |
| Docker Compose runtime shape | PASS | `docker-compose.yml` | Do not delete persistent volumes accidentally | None |
| CPU-only PyTorch packaging | PASS | `Dockerfile` | Keep using the CPU PyTorch package index | None |
| `/metrics` endpoint | PASS | `app/services/observability.py`, `app/api/routes.py` | Keep labels low-cardinality | None |
| Structured request logs | PASS | `app/services/observability.py`, tests | None | None |
| Evaluation results | PASS | `eval/results.json` | Rerun before final submission if code changes | None |
| Baseline result | PASS | `eval/run_baseline.py`, `eval/baseline_results.json` | None | None |
| Error analysis | PASS | `eval/generate_error_analysis.py`, `eval/error_analysis.json` | None | None |
| Model Card | PASS | `MODEL_CARD.md` | Review for team-specific provenance | None |
| Dataset Card | PASS | `DATASET_CARD.md` | Fill missing source-license provenance if available | User/team provenance needed |
| Executive Briefing | PASS | `docs/EXECUTIVE_BRIEFING.md` | Update readiness line after final validation | None |
| LICENSE | PASS | `LICENSE` | None | None |
| `.gitignore` | PASS | `.gitignore` | Keep generated runtime artifacts ignored | None |
| `.env.example` | PASS | `.env.example` | Copy locally only; do not commit real `.env` | None |

## Human and External Items

| Requirement | Status | Evidence/path | Owner action | Blocker |
|---|---|---|---|---|
| Public portfolio artifact URL | BLOCKED — USER INPUT REQUIRED | README has no real external portfolio URL | Add the actual public URL after publishing | URL not provided |
| 4-6 minute demo video | BLOCKED — USER INPUT REQUIRED | No verified public video link | Record, upload, and verify the link | External deliverable |
| Presentation deck | BLOCKED — USER INPUT REQUIRED | No final deck file/link found | Finalize presentation deck | External deliverable |
| 12-15 minute presentation rehearsal | BLOCKED — USER INPUT REQUIRED | Cannot verify from repository | Team rehearsal | Human action |
| Final PR opened | BLOCKED — USER INPUT REQUIRED | Remote GitHub actions were not performed | Open final PR from approved branch | User/team action |
| Two teammate approvals | BLOCKED — USER INPUT REQUIRED | Remote approvals not inspected or modified | Obtain two approvals | GitHub workflow action |
| Merge through approved workflow | BLOCKED — USER INPUT REQUIRED | Remote merge not performed | Merge after approvals | GitHub workflow action |
| GitHub Project cards Done | BLOCKED — USER INPUT REQUIRED | No `.github` project evidence in repo | Move project cards after review | GitHub workflow action |
| Demo Day attendance | BLOCKED — USER INPUT REQUIRED | Cannot verify from repository | Attend Demo Day | Human action |
| Individual reflection | BLOCKED — USER INPUT REQUIRED | Not present in repo | Complete in assigned platform | Human action |
| Peer reflection | BLOCKED — USER INPUT REQUIRED | Not present in repo | Complete in assigned platform | Human action |

For clinicians only — supports review, not diagnosis or prescribing.
