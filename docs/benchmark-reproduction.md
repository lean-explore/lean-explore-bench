# Reproduce the assisted benchmark

Use the published source for synthetic tests and evaluation code. Supply the measured inputs and model assets from the external assisted-v2 package. Keep raw cases, annotations, rankings and binary assets outside the Git checkout. Preserve the original manifests before modifying any input.

## Check source without measured data

Run the standalone offline suite from the repository root:

```sh
python tools/offline/scripts/check.py
```

Install the development dependencies, then run the metadata and cache fixtures:

```sh
python -m pip install pytest
cd experiments/declaration_metadata
python -m pytest -q
```

Use the pinned engine preparation and dependency installation in the [candidate experiment guide](../experiments/candidate_selection/README.md) before running its synthetic tests. These tests use fake model scores and do not download neural weights.

Check the normalization proof with Lean 4.32.0:

```sh
lean experiments/declaration_metadata/VerifiedNormalization.lean
```

Require a successful exit and inspect the printed axiom dependencies. Expect only `propext` and `Quot.sound`; reject `sorryAx` or custom axioms. Keep JSON, IO, the envelope adapter and upstream semantic completeness outside the proof claim.

## Reconstruct measured scores

From the external package root, run:

```sh
python recompute_all.py
```

Verify every manifest entry, reconstruct the two pilot profiles and 16 score reports, recompute all 946 external-reference rows and rebuild the two-snapshot cache fixture. Compare the preserved 402-record prefix with the initial checkpoint and retain the cancelled-attempt record. This operation requires the recorded artifacts but does not require model inference.

Use `human-checks.json` as the review registry. Apply explicit human decisions through the [correction workflow](assisted-human-review.md), write a new profile version and preserve the run hashes. Create a new query and run when repairing a mathematical statement.

## Repeat inference

Prepare the exact model snapshots, corpus and indexes recorded in the package. Verify the file hashes and runtime configuration. Treat unavailable original corpus-build provenance as an open limitation; do not claim that a database can be rebuilt from source without that evidence.

For the frozen 30-query pilot, run the retained runner with its matching query file and freeze:

```sh
python /external/pilot-v1/test-run/executed_runner.py   --cases /external/pilot-v1/inputs/test-cases.frozen.json   --data /external/corpus --models /external/models.json   --out /external/new-pilot-run   --frozen-evaluation /external/pilot-v1/inputs/experiment-freeze.json
```

For all 946 reference variants, use the external-reference profile:

```sh
python experiments/candidate_selection/diagnostic_replay.py   --cases /external/mathlibqr-cases.frozen.json   --data /external/corpus --models /external/models.json   --out /external/new-reference-run   --external-reference /external/reference-contract.json
```

Use a fresh output directory. Keep the reference configuration at 100 reranker candidates and the pilot at ten. Record executed source, runtime, model identities, input audits and all scheduled requests.

To resume an interrupted reference run, add `--resume /external/initial-run/replay.json` and use another new output directory. Require the same schedule, corpus, model manifest, engine source and retrieval settings. Retain the initial checkpoint and runner. Account separately for cancelled or repeated attempts. Keep the append-only journal alongside periodic checkpoints; do not treat uncheckpointed or incomplete journal entries as a completed schedule.

## Recompute reference metrics separately

Place `mathlibqr-cases.frozen.json`, `upstream/benchmark/MathlibQR.json`, `upstream/benchmark/MathlibQR_shared171.json` and `reference-run/replay.json` under one external root. Then run:

```sh
python experiments/candidate_selection/reference_score.py /external/reference-root
```

Use `--run-directory DIRECTORY_NAME` when the replay is stored under a different child directory. Preserve the full 946-query slice and original shared171 membership. Keep absent targets and request failures in their denominators; report present-only results separately. Distinguish query-micro means, target-macro means and target-group bootstrap intervals.

Read [assisted-v2 results](benchmark-assisted-v2.md) for the measured outcomes and [the dataset card](dataset-card.md) for provenance and redistribution constraints.
