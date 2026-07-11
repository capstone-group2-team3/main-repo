# MedDx Assistant

## Overview

Doctor-facing emergency and lab report support dashboard.

## Setup

To be completed later.

## Run

To be completed later.

## Eval

The canonical held-out set is `eval/heldout.jsonl`. Each row is a de-identified,
structured educational case or a clearly labelled reconstruction derived from a
public source. It is not a collection of patient records.

Validate and run the evaluation from the repository root:

```bash
source .venv/bin/activate
python eval/validate_heldout.py
python eval/run_eval.py
```

The runner invokes `AgentOrchestrator.analyze_report` directly with an isolated
temporary SQLite database and report directory. It writes aggregate and per-case
results to `eval/results.json`, then derives observed failure details in
`eval/failure_cases.md`. Evidence grounding requires a reachable, populated
Qdrant medical-knowledge index; without it, retrieval failures are recorded and
the run continues.
