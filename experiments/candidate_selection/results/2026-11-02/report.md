# Candidate selection pilot

This 12-query diagnostic pilot does not support changing serving defaults.
Larger reranking pools admit more labeled targets but lose one target from
the final output. The experiment keeps the embedding and reranking models
fixed.

Each query has one source target. Equivalent answers have not been
exhaustively judged, and this small sample is not a search-quality benchmark.
The four exact-name, four short-nickname and four description queries have
equal weight; those proportions do not represent production traffic.

## Setup

- Public LeanExplore corpus: `20260714_172516`, 408,970 declarations.
- Source tasks: [MathlibQR](https://github.com/frenzymath/LeanSearch-v2/blob/94f4888cbaf9f4322535755f86cbac690ec18080/benchmark/MathlibQR.json).
- Embedding: Qwen3-Embedding-0.6B, revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`.
- Reranker: Qwen3-Reranker-0.6B, revision `e61197ed45024b0ed8a2d74b80b4d909f1255473`.
- Hardware: NVIDIA GeForce RTX 5080 Laptop GPU; PyTorch 2.9.1+cu130.
- BM25: 1,000 candidates per name index; semantic retrieval: 1,000.
- Mathlib package filter; one measured repetition; seed 42; warmed models.

196 of the source's 200 targets exist in this snapshot. Before retrieval,
we selected 12 from the 22 Mathlib theorems/lemmas that have both nickname
and natural-description fields. The source list is shuffled with seed 42,
the first 12 records are retained, and query form rotates between exact name,
nickname and description. The four absent source targets are recorded in
[pilot-provenance.json](pilot-provenance.json).

## Results

The table retains zero-score BM25 matches and enables dependency boosting.
Every row uses the same 12 queries.

| Results returned | Reranking depth | Target reaches reranker | Target in final output | Median traced latency |
| --- | --- | --- | --- | --- |
| 5 | 5 | 6/12 | 6/12 | 162 ms |
| 5 | 50 | 8/12 | 5/12 | 579 ms |
| 5 | 100 | 8/12 | 5/12 | 999 ms |
| 10 | 10 | 7/12 | 7/12 | 192 ms |
| 10 | 50 | 8/12 | 6/12 | 552 ms |
| 10 | 100 | 8/12 | 6/12 | 975 ms |

Timings are descriptive on this machine, include tracing, and have only 12
observations per row. They are not serving-capacity measurements.

- The baseline retrieval union contains 11/12 targets. All 11 survive the
  top-500 cut and package filter. Six reach a depth-5 reranker; seven reach
  a depth-10 reranker.
- The eight non-name queries have 987-1,000 zero-score BM25 candidates each.
  Removing them does not change final target-hit counts at the tested depths.
- Disabling the selection boost does not improve final target-hit counts.
  At depth 100 with zero-score matches retained, it admits one extra target,
  9/12 instead of 8/12. The final dependency score term remains enabled.
- The exact-name query for
  `MeasureTheory.tendsto_lintegral_of_dominated_convergence` enters reranking
  in position five. It finishes fifth with a five-candidate pool, tenth
  with ten candidates, and outside the top ten with 50 candidates.
- `R7-short_nickname` has no labeled target in the retrieval union.
  Selection changes cannot recover a declaration absent from that union.

Increasing the pool changes both its membership and the normalization of
final score components. The pilot does not isolate the neural reranker from
the final score mixture. Inspect the exact-name regression and expand the
judged set, including equivalent lemmas, before choosing a serving default.

## Artifacts and verification

[pilot-5.json](pilot-5.json) and [pilot-10.json](pilot-10.json) contain 144
measured searches each, all variant summaries, per-query target ranks and
timings. Their absolute local paths were replaced with relative labels;
metric values, measured records and hashes are unchanged.

[Queries](pilot-queries.json), [provenance](pilot-provenance.json),
[asset checksums](download-manifest.json), [model revisions](model-manifest.json)
and the [lexical audit](lexical-audit.json) accompany the results. Only public
MathlibQR inputs are included. The [source license](LICENSE.MathlibQR) is
retained. Database/index files and model weights are downloaded separately.

The original implementation passed 612 package tests and 35 app tests, plus
mypy, Ruff, formatting and size checks. The package run had three deselections,
one expected failure and an aiosqlite worker shutdown warning. The
[experiment instructions](../../README.md) explain how to apply the patches
and run the migrated synthetic tests. No serving defaults were deployed.
