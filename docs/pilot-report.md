# Pilot report: evaluating Lean declaration retrieval on 50 queries

Status: assisted-v2, 8 November 2026. This is a pilot of the evaluation method, not a finished
benchmark.

## Summary

We built a small evaluation of the local LeanExplore search engine: 20 development and 30 frozen
test queries, graded relevance labels over pooled candidates, and eight pipeline configurations
scored from the same recorded runs. We also ran the engine over all 946 MathlibQR query variants
[1, 2], and prototyped a Lean-checked metadata normalization step and an incremental cache.

**The relevance labels are AI proposals.** Of 763 usable judgments, 759 were proposed by an AI
assessor and four are earlier human-accepted decisions. No independent human validation has been
done, and no inter-annotator agreement or AI-judge error rate has been estimated. Every pilot
number below is therefore descriptive. The MathlibQR numbers use upstream single-gold targets and
do not depend on these labels.

Two observations stand out. Reranking a fixed set of ten candidates more than doubles Success@1
on the test set. The neural-only reranker score slightly outperforms the current score mixture
in the pilot, but on MathlibQR the ordering reverses and the current mixture is clearly best.

## What was evaluated

**Corpus.** The local corpus contains 408,970 canonical declaration names (database SHA256
`5ffc35ab68db5c60b535a416148a327de9a862a03048c41d62bfcb0b3903424d`). Its original build environment
and the configuration of the hosted service are not fully known, so the results describe this
local snapshot only.

**Models.** Embedding uses Qwen/Qwen3-Embedding-0.6B at revision
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` (512-token limit, bfloat16). Reranking uses
Qwen/Qwen3-Reranker-0.6B at revision `e61197ed45024b0ed8a2d74b80b4d909f1255473` (256-token limit,
float16) [3]. FAISS nprobe is 64. No model was trained or tuned.

**Pipeline.** Pilot retrieval requests 1,000 candidates from each of the lexical and dense
channels, fuses and selects them, and reranks ten candidates. The final score mixes neural,
lexical, fuzzy-name and dependency signals. Eight configurations are scored:

| Configuration | What it ranks |
| --- | --- |
| lexical | Lexical (BM25) channel alone |
| dense | Dense embedding channel alone |
| fusion | Fused lexical and dense candidates |
| fusion with selection boost | Fused candidates after the selection step |
| pre rerank same pool | The ten selected candidates in their order before reranking |
| current mixture | The ten candidates reranked by the current score mixture |
| neural only | The ten candidates ranked by the reranker score alone |
| without final dependency | The current mixture without its final dependency term |

The last four share an identical candidate pool, so they differ only in ordering.

**Metrics.** A declaration counts as relevant at grade 2 or above. Success@k asks whether a
relevant declaration appears in the first k ranks, and nDCG uses linear gain. Unjudged documents
contribute zero gain but are not treated as negatives; Judged@10 is the labelled fraction of the
top ten. Details are in the [evaluation protocol](evaluation-protocol.md).

## Queries and labels

All 50 queries are synthetic and anonymous. The 30 test queries were written by an AI from
scope-screened sources (five reserved sources retained, 25 replaced) and frozen with the retrieval
settings before any retrieval ran (query file SHA256
`b65ed4e5fba684b5b0fd2939db831a9598c38a7353fc8e84c5e52b304d617d27`). No test result was used to
change models, weights or prompts. Query writing was not uniformly answer-blind: some source text
contains theorem names or proofs, and one earlier answer-link exposure is recorded.

Grades run from 0 to 3: 3 answers the request directly under its assumptions, 2 is useful after a
clear adaptation, 1 is related but insufficient, and 0 is irrelevant or incompatible. The review
pools hold 786 query-declaration pairs (419 development, 367 test), of which 763 have usable
judgments. The other 23 belong to one excluded development query, and nine of those are
unresolved.

Five queries are left out of the relevance means, giving denominators of 19 development and 26
test cases:

- One development query, about a path-connected indexed union, states something false when the
  index type is empty.
- Test queries 18, 26, 27 and 29 have no proposed relevant answer, and their pools do not
  establish that the corpus lacks one.

## Results

### Pilot test set

Means over the 26 eligible test cases. Both test runs completed all 30 requests.

| Configuration | S@1 | S@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.038 | 0.077 | 0.043 | 0.065 | 0.527 |
| dense | 0.500 | 0.731 | 0.570 | 0.670 | 0.535 |
| fusion | 0.231 | 0.731 | 0.401 | 0.512 | 0.996 |
| fusion with selection boost | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| pre rerank same pool | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| current mixture | 0.462 | 0.692 | 0.553 | 0.652 | 1.000 |
| neural only | 0.500 | 0.692 | 0.590 | 0.673 | 1.000 |
| without final dependency | 0.500 | 0.692 | 0.574 | 0.660 | 1.000 |

Reranking raises Success@1 from 0.192 (5/26) to 0.462 (12/26) and nDCG@10 from 0.481 to 0.652.
Success@10 stays at 0.692 (18/26) because the pool of ten is unchanged. The first result changes
for 26 of the 30 test queries. Neural-only has the highest nDCG@10 among the fixed-pool variants.
The lexical and dense top tens are only about half judged, so their scores are not directly
comparable with the fully judged rows.

### Development set

Means over the 19 eligible development cases. These queries informed curation and diagnosis and
are not independent evidence. The first result changes after reranking for 18 of the 20 queries.

| Configuration | S@1 | S@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.158 | 0.421 | 0.254 | 0.272 | 1.000 |
| dense | 0.526 | 0.947 | 0.667 | 0.721 | 1.000 |
| fusion | 0.158 | 0.895 | 0.439 | 0.512 | 1.000 |
| fusion with selection boost | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| pre rerank same pool | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| current mixture | 0.263 | 0.895 | 0.514 | 0.560 | 1.000 |
| neural only | 0.526 | 0.895 | 0.643 | 0.585 | 1.000 |
| without final dependency | 0.263 | 0.895 | 0.515 | 0.561 | 1.000 |

### Label sensitivity

Scores move with the labels alone. For the four cases that had human-accepted labels, keeping the
stored responses fixed and adding the AI proposals changes nDCG@10 from 0.6404 to 0.7203. This
figure is not comparable with the 19-case development mean, which has a different denominator.

### MathlibQR on the local corpus

MathlibQR has 946 query variants for 200 target declarations, each scored against a single gold
target. Four target names are absent from the local corpus and score zero. This run reranks 100
candidates and returns up to 100 results, unlike the ten-candidate pilot. All 946 requests
completed without error. The table covers the original shared171 subset (810 variants, 171
targets).

| Configuration | nDCG@1 | nDCG@5 | nDCG@10 | R@10 | R@50 | R@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.115 | 0.148 | 0.158 | 0.210 | 0.302 | 0.330 |
| dense | 0.256 | 0.373 | 0.397 | 0.553 | 0.712 | 0.764 |
| fusion | 0.184 | 0.320 | 0.351 | 0.527 | 0.698 | 0.742 |
| selection | 0.156 | 0.290 | 0.327 | 0.537 | 0.705 | 0.769 |
| current mixture 100 | 0.240 | 0.362 | 0.398 | 0.583 | 0.740 | 0.769 |
| neural only 100 | 0.141 | 0.246 | 0.280 | 0.447 | 0.701 | 0.769 |
| without final dependency 100 | 0.205 | 0.315 | 0.353 | 0.536 | 0.731 | 0.769 |
| pre rerank same pool 100 | 0.156 | 0.290 | 0.327 | 0.537 | 0.705 | 0.769 |

Current-mixture scores on the three slices:

| Slice | Queries | Targets | nDCG@10 | Recall@10 | Recall@100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full | 946 | 200 | 0.390 | 0.572 | 0.754 |
| Original shared171 | 810 | 171 | 0.398 | 0.583 | 0.769 |
| Present targets only | 927 | 196 | 0.398 | 0.584 | 0.769 |

The bootstrap interval for full-slice Recall@10 is [0.532, 0.613] (2,000 seeded draws over target
groups). These numbers are not comparable with the published cross-engine scores [1], because
the corpus version and execution conditions differ.

### The ablation ordering reverses

On the full MathlibQR set the current mixture has nDCG@10 of 0.390, against 0.344 without the
final dependency term, 0.322 for selection before reranking, and 0.261 for neural-only. In the
pilot, neural-only is the best fixed-pool variant. The two conditions differ in query form, label
type and pool size (100 against ten), so the cause is not identified. The small assisted pilot
therefore gives no basis for replacing the production mixture.

## Verified metadata and cache prototype

Relevance review needs complete statements, and source snippets can omit section assumptions or,
for generated declarations, show the parent declaration. An exporter reads full elaborated types
for 37 declarations from Lean 4.32.0 and Mathlib `aae61ae084c21995ee248964a81e3750ad0db2db` [4].
A normalization function, written in Lean, validates the decoded records and either returns the
whole snapshot or rejects it. Seven kernel-checked theorems cover preservation of records and
environment, count and order, unique identities, alias resolution and rejection of invalid input,
with no axioms beyond `propext` and `Quot.sound`. The proofs treat the semantic fields as opaque
strings: JSON decoding, the adapter, upstream extraction and hashing remain trusted.

The cache prototype keys each artifact on its effective inputs, including transitive imports. On
a fixture of 351 modules reachable from `Mathlib.Order.Atoms` at two Mathlib revisions, an
unchanged run reuses everything, and the update reuses 349 artifacts per layer and invalidates
two. The fixture records inputs without running Lean, informalization or embedding, so it shows
correct invalidation and not a measured speedup. See
[extraction and cache](extraction-and-cache.md).

## Reproducibility

The two 30-query test runs agree exactly in final rankings, stage identities and reranker scores.
One intermediate attempt failed when WSL ran out of memory, and the MathlibQR run was resumed
once from a checkpoint after 402 completed records. Scores can be recomputed from the stored
rankings with the Python standard library; rerunning inference needs the external database, index
and model files. The single-gold metric code matches the upstream functions [2] on 560 boundary
comparisons. Steps are in [reproduction](reproduction.md) and the
[offline tools](../tools/offline/README.md).

## Limits and what remains

- **Label validity.** AI assistance also covered query curation, evidence inspection and
  interpretation, so those stages do not check one another.
- **Size and coverage.** Fifty synthetic queries underrepresent declaration-name, formula and
  proof-state needs, and pooling is incomplete.
- **Independence.** Query families are provisional (14 exposure components and 19 proposed
  families in development, 29 proposed families in test), so no significance claim is made.
- **Exposure.** The test queries are now exposed and cannot serve as a fresh holdout.

The human-review register has 850 open items: 786 pairs, 50 queries and 14 release-level checks
such as family boundaries, redistribution rights and the normalization specification. (The
assisted-v1 write-up counted 844; assisted-v2 added six.) The five cases to review first are the
invalid development query (D20) and test queries 18, 26, 27 and 29. Corrections create a new
label version and are rescored against the unchanged rankings, as described in the
[human review guide](human-review.md). A confirmatory study needs new held-out queries and
independently accepted labels.

## References

[1] Gao, G., Sun, Z., Jiang, J., Wang, Y., Xu, J., Wu, P., Dai, B., and Dong, B. LeanSearch v2:
Global Premise Retrieval for Lean 4 Theorem Proving. arXiv:2605.13137v2, 2026.
https://arxiv.org/abs/2605.13137v2

[2] FrenzyMath. LeanSearch-v2 benchmark and single-gold evaluation source. Commit
94f4888cbaf9f4322535755f86cbac690ec18080.
https://github.com/frenzymath/LeanSearch-v2/tree/94f4888cbaf9f4322535755f86cbac690ec18080

[3] Zhang, Y., Li, M., Long, D., and colleagues. Qwen3 Embedding: Advancing Text Embedding and
Reranking Through Foundation Models. arXiv:2506.05176v3, 2025. https://arxiv.org/abs/2506.05176v3

[4] Lean Language Reference. Elaboration and Compilation. Accessed 8 November 2026.
https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/
