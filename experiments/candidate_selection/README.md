# Candidate selection experiments

These scripts measure how the LeanExplore engine chooses the candidates it passes to its
reranker. They vary the reranking depth, the exclusion of candidates with a zero BM25 score
and the dependency boost applied before reranking, and they record which candidates survive
each retrieval stage. Models, input rendering and final score weights stay fixed. Results are
in the [pilot report](../../docs/pilot-report.md).

## Setup

The scripts need a clean LeanExplore checkout at the commit recorded in `patches/bases.json`;
any other commit or a dirty tree is refused.

```sh
python experiments/candidate_selection/prepare_engine.py --checkout /external/engine
python -m pip install -e "/external/engine[local]" pytest pytest-asyncio
```

The first command applies `patches/lean-explore.patch` and copies `runner.py` to the engine's
`scripts/candidate_selection.py`. The corpus, model snapshots and queries are external files.
No script overwrites existing output.

## Ablation runner

From the prepared engine checkout:

```sh
python -m scripts.candidate_selection --data-directory /external/corpus \
  --queries /external/queries.json --output /external/report.json
```

The query file is a list of objects with `id`, `query`, `category`, `relevant` (declaration
names) and optional `packages`. Each query runs under twelve settings in shuffled order. The
run stops if a relevant name is absent from the corpus or if any search fails.

## Diagnostic replay

```sh
python experiments/candidate_selection/diagnostic_replay.py \
  --cases /external/cases.json --data /external/corpus \
  --models /external/models.json --out /external/diagnostic-run
```

This runs one fixed setting and writes `replay.json`, `records.jsonl` and
`executed_runner.py`. The cases use the
[offline workflow](../../tools/offline/docs/benchmark-workflow.md) format, and their
`corpus_revision` must equal the SHA-256 of `lean_explore.db`. The model manifest maps
`Qwen/Qwen3-Embedding-0.6B` and `Qwen/Qwen3-Reranker-0.6B` to a local `path`. Each record
holds the status, stage traces and three scorings of one candidate pool: `current_mixture`,
`without_final_dependency` and `neural_only`.

| Mode | Required cases | Results |
|---|---|---|
| default | `split: development` | 10 |
| `--frozen-evaluation FILE` | `split: test`, `validation_profile: assisted-v1` | 10 |
| `--external-reference FILE` | development, `validation_profile: mathlibqr-remapped-v1` | 100 |

`FILE` is a JSON contract holding `cases_sha256`, the fixed `settings` and a `phase` of
`before_test_retrieval` or `before_reference_retrieval`. `--resume CHECKPOINT` continues a
reference run with unchanged inputs in a new output directory.

## Representation probe and reference scoring

```sh
python experiments/candidate_selection/representation_probe.py \
  --models /external/models.json --lean /path/to/lean \
  --out /external/representation-probe
python experiments/candidate_selection/reference_score.py /external/root
```

The probe checks four true statements and two counterexamples in Lean, then scores them as
description-only, formal-only and combined inputs, writing `scores.json`. The reference
scorer reads a finished MathlibQR replay under the root and writes `reference-summary.json`
and `reference-per-query.json`. The [reproduction guide](../../docs/reproduction.md) gives
the full sequence.

## Tests

`python -m pytest -q` in this directory needs the patched engine. It uses SQLite, BM25, FAISS
and fake model scores; no model weights are downloaded.

## Limits

- Timings include tracing overhead and are not serving latency.
- Disabling the boost before reranking leaves the dependency term in the final score.
- The labels may omit relevant declarations, and a changed order is not by itself a relevance
  improvement.
- The frozen test queries have been used and cannot serve as a fresh holdout.

Engine-derived code keeps its Apache-2.0 attribution in `LICENSE.LeanExplore`.
