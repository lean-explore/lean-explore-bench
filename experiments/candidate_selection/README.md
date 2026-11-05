# Candidate selection experiments

The runner compares reranking depth, zero-score BM25 exclusion and dependency
boosting before reranking. Models, input rendering and final weights stay fixed.

## Prepare the engine

Use a separate checkout at the base recorded in `patches/bases.json`.
The preparation command refuses a different base or a dirty worktree.

```sh
python experiments/candidate_selection/prepare_engine.py --checkout /external/engine
python -m pip install -e "/external/engine[local]" pytest pytest-asyncio
```

The helper applies the engine patch and copies the runner into the engine's
scripts directory. Corpus files, local model snapshots and queries are supplied
externally. Record their revisions and hashes alongside each run.

The runner accepts an external query list with `id`, `query`, `category`,
`relevant` declaration names and optional `packages`. These labels must be
reviewed for the intended experiment. Use the offline preparation workflow
before turning proposed targets into scored labels.

From the prepared engine checkout:

```sh
python -m scripts.candidate_selection --help
```

The runner refuses existing output files and verifies that labeled targets are
available in the corpus and requested package scope. It warms the engine and
shuffles query/variant order. Errors stop this experiment runner. For operational
evaluation, retain failed and missing requests in the offline run contract.

## Traces and interpretation

Traces record candidate identities through lexical and semantic retrieval,
fusion, selection, filtering, reranker input and final output. Timings include
trace overhead and are not serving load tests.

Disabling the selection boost preserves the dependency term in the final score.
Increasing the pool also changes pool-normalized final score components.
Unknown relevant declarations can be absent from supplied labels. Report
judgment coverage and keep candidate-name recovery distinct from reviewed
mathematical relevance.

## Validation

Run the invented fixtures from this directory:

```sh
python -m pytest -q
```

The tests use SQLite, BM25 and FAISS with fake model scores. They require the
patched engine and its local dependencies, without downloading model weights.

Engine-derived code and fixtures retain their Apache-2.0 attribution in
`LICENSE.LeanExplore`.
