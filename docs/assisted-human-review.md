# Review assisted benchmark judgments

All AI labels retain `assessor_type: assistant` and proposed status. Four earlier accepted human decisions retain precedence. No independent human validation is claimed. The local report and `human-checks.json` contain the pending targets; opening a card does not accept a label.

## One decision at a time

1. Open the case query and scope. Check whether the source interpretation and assumptions are right. For an invalid or changed query, create a new case version and rerun it; do not reuse the original response as if the query had stayed the same.
2. Read the candidate's complete statement, including implicit parameters and typeclass assumptions. Generated declarations need their own exported type.
3. Choose grade 3 for a direct answer, 2 for a usable answer with a stated adaptation, 1 for a related but insufficient result, or 0 for a result that does not answer the request. Leave genuine uncertainty unresolved.
4. Record the actual reviewer, decision, reason and active review time. Independent calibration requires a separate assessor who has not seen the AI grade. Do not calculate agreement from a joint assisted pass.
5. Apply the explicit decision to a new label version and compare scores on the stored rankings. If model or query text changes, schedule a new retrieval run instead.

## Record and rescore

A decisions file is a JSON list. Each entry needs `case_id`, `document_id`, integer `grade` from 0 to 3, `reviewer`, `assessor_type: human`, `status: accepted`, `uncertain: false` and a substantive `reason`. These fields describe a decision actually supplied by a human. The tool rejects assistant proposals presented as accepted decisions. No human record is prefilled in the delivered artifact.

From `tools/offline`, with the package installed or `PYTHONPATH` pointing to `src`, run:

```text
python -m leanexplore_benchmark.human_rescore --profile PATH_TO_ASSISTED_JSON --decisions PATH_TO_HUMAN_DECISIONS_JSON --runs PATH_TO_EVALUATION_RUNS --out NEW_REVIEW_VERSION_DIRECTORY
```

The command refuses an existing output directory. It saves the new profile and before/after evaluations with the hash of each unchanged run. For the next correction, use the new `profile.json`. It does not turn the release-wide independent-validation flag on. Query repairs, family decisions, provenance recovery and independent calibration remain separate targets in the register.

The pair identifiers are stable across label versions. The per-case targets are `HC-D*` and `HC-T01` through `HC-T30`; release targets cover calibration, family separation, provenance, extraction, timing, reproducibility, reference scope and answer presentation.
