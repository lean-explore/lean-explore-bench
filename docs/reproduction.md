# Reproducing the pilot

## What lives where

Git holds source code, method documentation, tests built on invented records, and a small explicit
set of source-migration and patch artifacts. Cases, annotations, rankings, private query logs,
model assets and measured run files live in an external package (assisted-v2). The reason is
redistribution and privacy: see the [pilot dataset card](pilot-dataset-card.md).
`tools/offline/scripts/check_publication.py` rejects data directories and data formats in the
checkout, although it cannot judge whether a text file's content is suitable for publication.

`recompute_all.py`, `human-checks.json` and all `/external/...` paths below belong to that package
and are not in this repository.

## Checking the source without data

From the repository root:

```sh
python tools/offline/scripts/check.py
```

The metadata and cache fixtures:

```sh
python -m pip install pytest
cd experiments/declaration_metadata
python -m pytest -q
```

The candidate-selection tests use fake model scores and download no weights; their setup is in the
[candidate selection experiments](../experiments/candidate_selection/README.md). The normalization
proof needs Lean 4.32.0:

```sh
lean experiments/declaration_metadata/VerifiedNormalization.lean
```

The printed axiom dependencies should be only `propext` and `Quot.sound`.

## Recomputing scores from stored runs

From the external package root:

```sh
python recompute_all.py
```

This verifies every manifest entry, rebuilds the two pilot profiles and 16 score reports,
recomputes all 946 external-reference rows and rebuilds the two-snapshot cache fixture. It needs no
model inference. Label corrections are applied as described in [human review](human-review.md).

## Rerunning inference

Rerunning requires the model snapshots, corpus and indexes recorded in the package, with matching
file hashes. The provenance of the original corpus build is not available, so the database cannot
be rebuilt from source. Each run needs a fresh output directory.

The frozen 30-query pilot (10 reranker candidates):

```sh
python /external/pilot-v1/test-run/executed_runner.py   --cases /external/pilot-v1/inputs/test-cases.frozen.json   --data /external/corpus --models /external/models.json   --out /external/new-pilot-run   --frozen-evaluation /external/pilot-v1/inputs/experiment-freeze.json
```

All 946 reference variants (100 reranker candidates):

```sh
python experiments/candidate_selection/diagnostic_replay.py   --cases /external/mathlibqr-cases.frozen.json   --data /external/corpus --models /external/models.json   --out /external/new-reference-run   --external-reference /external/reference-contract.json
```

An interrupted reference run resumes with `--resume /external/initial-run/replay.json` and another
new output directory. The schedule, corpus, model manifest, engine source and retrieval settings
must be unchanged.

## Recomputing reference metrics

With `mathlibqr-cases.frozen.json`, `upstream/benchmark/MathlibQR.json`,
`upstream/benchmark/MathlibQR_shared171.json` and `reference-run/replay.json` under one root:

```sh
python experiments/candidate_selection/reference_score.py /external/reference-root
```

`--run-directory DIRECTORY_NAME` selects a replay stored under a different child directory. Absent
targets and failed requests stay in the denominators, and present-only results are reported
separately. Measured outcomes are in the [pilot report](pilot-report.md).
