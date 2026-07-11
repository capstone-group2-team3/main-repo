# Executive Briefing: MedDx Assistant

## The Problem

Clinicians reviewing lab results often spend significant time manually cross-referencing abnormal values against clinical knowledge to decide what might be going on and how urgently a case needs attention. This manual process is slow and easy to get inconsistent, especially under time pressure.

## The Solution

MedDx Assistant is a clinician-facing support tool that automates the first pass of lab result review. Given a structured set of lab values and symptoms, it:

1. Flags which values are abnormal and by how much.
2. Suggests the top 3 clinical patterns worth investigating, with supporting and missing evidence clearly listed.
3. Estimates how urgent the case is (Routine, Urgent, or Critical).
4. Surfaces relevant medical reference text that supports each suggestion.
5. Produces a clean, structured report the clinician can review in seconds.

**The system does not diagnose or prescribe.** Every output is explicitly framed as decision *support* — the clinician remains the final decision-maker.

## How It Works (Non-Technical)

Think of it as a well-organized assistant who:
- Reads the lab report and highlights anything unusual.
- Cross-checks a reference library and says, "this combination of results often shows up in cases like X — here's why, and here's what's still missing to be sure."
- Flags how urgently the case might need attention.
- Never says "this patient definitely has X" or suggests treatment — it always leaves the judgment call to the doctor.

## Key Results

- Automated test suite: 39 tests passing, covering the analysis pipeline end-to-end.
- Evaluation run against 50 hand-validated synthetic cases measuring Top-3 Clinical Pattern Recall, Evidence Grounding Rate, and Average Latency (see `eval/results.json`).
- Severity classifier evaluated separately with a focus on Critical-case recall, since missing a truly urgent case is the highest-risk failure mode.

## Safety Approach

Every report passes through a dedicated safety layer before reaching the clinician:
- Unsafe or overly definitive language (e.g., "the patient has X") is automatically rewritten to supportive phrasing (e.g., "findings may be consistent with X, pending clinician review").
- A fixed safety notice is always attached, reminding the clinician that this tool supports review only.
- The severity indicator is explicitly labeled as an AI-generated alert based on synthetic training data, not a clinical determination.

## Limitations & Future Work

- Current evaluation data is synthetic; validating against real (de-identified) clinical data would be a natural next step.
- The medical knowledge base currently covers a limited set of panels; expanding coverage would broaden applicability.
- The severity classifier's labels are rule-derived rather than clinician-labeled; a future iteration could incorporate real clinician-reviewed severity labels.