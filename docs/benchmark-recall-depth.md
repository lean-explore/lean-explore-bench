# First-stage recall by depth

This report measures how many labelled targets each first-stage channel retrieves at depths from 50 to 5,000, and how many of them survive candidate selection. It replays the labelled requests of the [full collection replay](benchmark-reranker-corrected.md) with the same pinned engine, corpus and models: Qwen3-Embedding-0.6B, BM25+ on declaration names, and a FAISS IVF index with 639 lists searched at nprobe 64. BM25 and FAISS both run at depth k, without reranking. The code and the commands to reproduce it are in [experiments/full_collection](../experiments/full_collection/README.md#first-stage-depth).

The replay covered 3,215 labelled requests with 0 errors. At depth 1,000 it gives the same ranks as the archived end-to-end run for all 4,790 target and stage pairs.

Recall follows the existing scoring: a target name that is absent from the index stays in the denominator. The columns are:

- BM25 and Dense: the top k of each channel.
- BM25 ∪ Dense: targets found by either channel at depth k.
- Fused top-k: the first k candidates of the engine's fusion.
- All fused: the whole fused list at depth k, up to about 3k candidates.
- Selection: the dependency-boosted pool that is reranked today, capped at 500.

The max row gives each channel's ceiling. For BM25 it counts targets that share at least one token with the query. For dense it counts targets inside the probed IVF lists, and the result of an exhaustive search at 5,000.

## Recall

### MathlibMPR (n=138)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 11.1 | 30.4 | 32.1 | 24.9 | 32.1 | 24.5 |
| 100 | 14.6 | 37.4 | 39.0 | 32.1 | 39.0 | 31.6 |
| 250 | 18.3 | 47.5 | 48.8 | 42.0 | 48.8 | 41.7 |
| 500 | 23.3 | 55.1 | 57.3 | 48.4 | 57.3 | 48.4 |
| 1000 | 28.3 | 62.3 | 64.6 | 56.6 | 64.6 | 48.8 |
| 2000 | 33.6 | 69.2 | 71.4 | 63.8 | 71.4 | 49.1 |
| 3000 | 38.8 | 73.7 | 75.0 | 68.7 | 75.0 | 49.1 |
| 5000 | 47.0 | 77.9 | 79.4 | 73.1 | 79.4 | 49.2 |
| max | lexical overlap 81.3 | probed lists 87.7 · exhaustive@5000 79.8 | | | | |

### MathlibQR (n=946)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 30.9 | 70.1 | 73.0 | 67.1 | 73.0 | 67.9 |
| 100 | 33.8 | 74.7 | 77.3 | 72.0 | 77.3 | 73.4 |
| 250 | 37.6 | 80.9 | 82.9 | 78.3 | 82.9 | 79.3 |
| 500 | 40.9 | 83.7 | 85.8 | 83.0 | 85.8 | 83.0 |
| 1000 | 45.6 | 85.9 | 88.2 | 85.5 | 88.2 | 83.0 |
| 2000 | 49.7 | 88.4 | 90.6 | 87.8 | 90.6 | 83.1 |
| 3000 | 51.7 | 89.6 | 91.8 | 89.5 | 91.8 | 83.1 |
| 5000 | 54.0 | 90.3 | 92.5 | 91.2 | 92.5 | 83.1 |
| max | lexical overlap 59.8 | probed lists 92.1 · exhaustive@5000 95.0 | | | | |

### Discussion-derived (n=2,079)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 10.4 | 23.2 | 27.5 | 21.7 | 27.5 | 22.6 |
| 100 | 13.1 | 28.5 | 33.4 | 27.3 | 33.4 | 28.1 |
| 250 | 16.8 | 36.3 | 40.8 | 35.0 | 40.8 | 35.9 |
| 500 | 20.8 | 42.5 | 46.6 | 40.8 | 46.6 | 40.8 |
| 1000 | 25.5 | 49.1 | 53.1 | 46.4 | 53.2 | 41.2 |
| 2000 | 30.5 | 55.1 | 59.2 | 52.8 | 59.5 | 41.4 |
| 3000 | 33.6 | 58.8 | 62.7 | 56.8 | 63.1 | 41.4 |
| 5000 | 39.0 | 62.9 | 66.3 | 61.0 | 66.9 | 41.6 |
| max | lexical overlap 65.5 | probed lists 75.2 · exhaustive@5000 63.9 | | | | |

An exhaustive dense search beats nprobe 64 on MathlibQR at every depth, for example 77.8 against 74.7 at 100 and 89.7 against 85.9 at 1,000. Discussion-derived targets are reply links, not verified relevance judgments.

### Small sets

#### Candidate-selection pilot (n=12)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 41.7 | 66.7 | 66.7 | 66.7 | 66.7 | 58.3 |
| 100 | 41.7 | 83.3 | 83.3 | 66.7 | 83.3 | 66.7 |
| 250 | 50.0 | 83.3 | 91.7 | 83.3 | 91.7 | 83.3 |
| 500 | 50.0 | 83.3 | 91.7 | 91.7 | 91.7 | 91.7 |
| 1000 | 58.3 | 83.3 | 91.7 | 91.7 | 91.7 | 91.7 |
| 2000 | 75.0 | 83.3 | 91.7 | 91.7 | 91.7 | 91.7 |
| 3000 | 75.0 | 83.3 | 91.7 | 91.7 | 91.7 | 91.7 |
| 5000 | 75.0 | 83.3 | 91.7 | 91.7 | 91.7 | 91.7 |
| max | lexical overlap 75.0 | probed lists 83.3 · exhaustive@5000 91.7 | | | | |

#### Synthetic discussion pilot (n=26)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 1.9 | 48.1 | 50.0 | 35.3 | 50.0 | 35.3 |
| 100 | 7.7 | 53.8 | 57.7 | 46.2 | 57.7 | 48.1 |
| 250 | 12.8 | 61.5 | 69.2 | 57.7 | 69.2 | 63.5 |
| 500 | 29.5 | 70.5 | 80.1 | 73.1 | 80.1 | 73.1 |
| 1000 | 30.8 | 76.3 | 85.3 | 80.1 | 85.3 | 73.1 |
| 2000 | 38.5 | 85.9 | 91.0 | 85.3 | 91.0 | 73.1 |
| 3000 | 46.2 | 91.0 | 94.2 | 87.2 | 94.2 | 73.1 |
| 5000 | 55.1 | 94.9 | 96.2 | 91.0 | 96.2 | 73.1 |
| max | lexical overlap 66.0 | probed lists 100.0 · exhaustive@5000 94.9 | | | | |

#### Development pilot (n=19)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 30.7 | 61.4 | 61.4 | 61.4 | 61.4 | 56.1 |
| 100 | 30.7 | 71.9 | 71.9 | 61.4 | 71.9 | 61.4 |
| 250 | 37.7 | 77.2 | 77.2 | 71.9 | 77.2 | 71.9 |
| 500 | 37.7 | 78.9 | 78.9 | 77.2 | 78.9 | 77.2 |
| 1000 | 37.7 | 80.7 | 80.7 | 78.9 | 80.7 | 77.2 |
| 2000 | 49.1 | 84.2 | 84.2 | 80.7 | 84.2 | 77.2 |
| 3000 | 54.4 | 84.2 | 84.2 | 84.2 | 84.2 | 77.2 |
| 5000 | 59.6 | 84.2 | 84.2 | 84.2 | 84.2 | 77.2 |
| max | lexical overlap 64.9 | probed lists 93.0 · exhaustive@5000 84.2 | | | | |

#### Earlier calibration (n=9)

| k | BM25 | Dense | BM25 ∪ Dense | Fused top-k | All fused | Selection (500 cap) |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 38.9 | 66.7 | 66.7 | 66.7 | 66.7 | 66.7 |
| 100 | 38.9 | 66.7 | 66.7 | 66.7 | 66.7 | 66.7 |
| 250 | 38.9 | 66.7 | 66.7 | 66.7 | 66.7 | 66.7 |
| 500 | 38.9 | 70.4 | 70.4 | 66.7 | 70.4 | 66.7 |
| 1000 | 38.9 | 74.1 | 74.1 | 70.4 | 74.1 | 66.7 |
| 2000 | 51.9 | 81.5 | 81.5 | 74.1 | 81.5 | 66.7 |
| 3000 | 63.0 | 81.5 | 81.5 | 81.5 | 81.5 | 66.7 |
| 5000 | 63.0 | 81.5 | 81.5 | 81.5 | 81.5 | 66.7 |
| max | lexical overlap 63.0 | probed lists 85.2 · exhaustive@5000 81.5 | | | | |

## Targets missing at 5,000

1,436 target instances are still missing at depth 5,000, and none of them is caused by a package filter. A probe against Mathlib 56a00585 classifies them:

| Cause | Instances |
|---|---:|
| Name absent from the index | 459 (417 distinct names) |
| Outside the probed IVF lists, found by an exhaustive search within 5,000 | 93 |
| Outside the probed lists and beyond 5,000 even exhaustively | 421 |
| No token shared with the query, beyond 5,000 in dense | 234 |
| Shares a token with the query, beyond 5,000 in both channels | 229 |

Of the 417 absent names, 333 exist neither in the corpus nor in current Mathlib, 70 are renames whose new name is indexed (for example `Basis`, now `Module.Basis`), 45 are structure projections, constructors and recursors that the corpus does not index, and 11 exist in Mathlib or its dependencies but not in the corpus. Absent names carry 12.4% of the discussion-derived target weight and about 2% for MathlibQR and MathlibMPR.

## Selection cap

Dense is the best single channel on every set. The 500-candidate cap drops targets that dense retrieval has already found:

| | MathlibMPR | MathlibQR | Discussion-derived |
|---|---:|---:|---:|
| Dense targets at depth 1,000 dropped by the cap | 115 of 434 | 45 of 813 | 380 of 1,698 |
| Fused cutoff that recovers the dense@1000 count | 2,450 | 1,116 | 1,409 |
| Fused cutoff holding 95% of BM25 ∪ Dense | 2,005 | 631 | 1,754 |
| Dense targets at depth 500 dropped by the cap | 55 | 26 | 191 |
| Fused cutoff that recovers the dense@500 count | 1,152 | 689 | 658 |

Fused top-k also stays below dense top-k on MathlibMPR at every depth, for example 56.6 against 62.3 at 1,000, because the BM25 channel on names takes about half of the fused positions.

## Fusion variants

These pools of N candidates are built from the same channel outputs at depth 1,000, without the dependency boost. `engine_rrf` is the current fusion, `rrf_c60` is reciprocal rank fusion with constant 60, `rrf_c60_dense2` counts dense ranks twice, and `slots_denseX` reserves X% of the pool for dense candidates.

### MathlibMPR

| N | engine_rrf | rrf_c60 | rrf_c60_dense2 | slots_dense75 | slots_dense90 | dense_only | lexical_only |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 26.3 | 27.8 | 30.6 | 27.6 | 29.1 | 30.4 | 11.1 |
| 100 | 32.5 | 32.6 | 36.8 | 35.0 | 37.0 | 37.4 | 14.6 |
| 250 | 43.3 | 42.8 | 45.8 | 46.0 | 47.4 | 47.5 | 18.3 |
| 500 | 48.8 | 48.8 | 51.2 | 51.5 | 54.1 | 55.1 | 23.3 |
| 1000 | 56.6 | 56.6 | 58.5 | 59.6 | 61.6 | 62.3 | 28.3 |

### MathlibQR

| N | engine_rrf | rrf_c60 | rrf_c60_dense2 | slots_dense75 | slots_dense90 | dense_only | lexical_only |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 68.4 | 67.1 | 71.2 | 70.2 | 70.7 | 70.1 | 30.9 |
| 100 | 72.9 | 73.2 | 75.7 | 75.3 | 75.9 | 74.7 | 33.8 |
| 250 | 78.9 | 79.0 | 81.1 | 81.1 | 81.8 | 80.9 | 37.6 |
| 500 | 83.0 | 82.9 | 83.6 | 84.4 | 84.7 | 83.7 | 40.9 |
| 1000 | 85.5 | 85.5 | 86.2 | 87.0 | 87.2 | 85.9 | 45.6 |

### Discussion-derived

| N | engine_rrf | rrf_c60 | rrf_c60_dense2 | slots_dense75 | slots_dense90 | dense_only | lexical_only |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 22.5 | 22.8 | 24.8 | 23.9 | 24.2 | 23.2 | 10.5 |
| 100 | 28.1 | 28.1 | 30.4 | 29.5 | 29.7 | 28.5 | 13.1 |
| 250 | 35.7 | 35.8 | 37.4 | 36.9 | 37.3 | 36.3 | 16.8 |
| 500 | 41.2 | 41.1 | 42.5 | 42.8 | 43.7 | 42.5 | 20.8 |
| 1000 | 46.4 | 46.3 | 48.1 | 49.1 | 50.3 | 49.1 | 25.5 |

Raising each channel to depth 2,000 changes these pools by at most about 1 point. Dense only lowers MathlibQR keyword queries at N=100 from 82.2 to 76.6, while dense-weighted RRF keeps them at 82.7.

## Cost

Medians over 200 requests without tracing, with p95 where shown.

| k | BM25 ms (p50/p95) | FAISS ms (p50/p95) | fusion ms | fused candidates | retrieval+fusion ms (profile) | load k rows ms (p50/p95) | load peak MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 12.3/18.3 | 7.0/8.2 | 0.9 | 149 | 22.8 | 2/3 | 1.9 |
| 100 | 11.6/17.4 | 6.8/7.9 | 0.1 | 298 | 21.0 | 4/5 | 3.7 |
| 250 | 11.6/17.2 | 6.9/8.1 | 0.3 | 739 | 23.0 | 9/11 | 9.3 |
| 500 | 11.6/17.3 | 6.9/8.1 | 0.6 | 1468 | 23.3 | 16/29 | 18.5 |
| 1000 | 11.8/17.5 | 7.1/8.4 | 1.3 | 2921 | 24.6 | 37/53 | 37.1 |
| 2000 | 12.3/18.0 | 7.6/8.8 | 2.4 | 5801 | 26.4 | 67/231 | 74.7 |
| 3000 | 12.7/18.5 | 8.0/9.3 | 3.6 | 8657 | 29.6 | 94/294 | 112.3 |
| 5000 | 13.5/19.5 | 8.9/10.3 | 6.3 | 14307 | 35.2 | 162/381 | 187.0 |

Query embedding takes 24.9 ms and an exhaustive FAISS search at depth 5,000 takes 62.3 ms. The process uses 1.96 GB once the indexes are loaded. Retrieval cost barely changes with depth; loading full declaration rows is what grows.

## Recommendation

- Keep 1,000 candidates per channel and pass 500 to the next stage. Going from 500 to 1,000 adds about 7 points on MathlibMPR and discussion-derived queries and about 2 on MathlibQR, for about 37 ms and 39 MB of row loading per request.
- Pass about 50 candidates to the cross-encoder. LeanSearch v2 reranks its top 50, BEIR reranks the top 100 of BM25, and Elastic's reranking depth sweep peaks near 30.
- Fill the pool with more dense candidates: dense-weighted RRF for pools up to about 100 (2 to 4 points), and about 90% dense slots for pools of 500 or more (5.3 points on MathlibMPR, 1.7 on MathlibQR and 2.5 on discussion-derived queries at 500). A convex combination of normalised scores is the next variant to test.
- Raise nprobe or search exhaustively: 3 to 4 points on MathlibQR at every depth, for about 55 ms.
- Index structure projections and constructors, and resolve renamed names. No depth recovers them.

Only 10 labelled requests are identifier queries, so a reserved position for an exact name match should stay. The variants were chosen on these sets and need confirmation on a held-out split.

## Sources

- LeanExplore: [arXiv 2506.11085](https://arxiv.org/abs/2506.11085)
- LeanSearch: [arXiv 2403.13310](https://arxiv.org/abs/2403.13310); LeanSearch v2: [arXiv 2605.13137](https://arxiv.org/abs/2605.13137)
- LeanDojo and ReProver: [arXiv 2306.15626](https://arxiv.org/abs/2306.15626)
- BEIR: [arXiv 2104.08663](https://arxiv.org/abs/2104.08663)
- Nogueira and Cho, passage re-ranking with BERT: [arXiv 1901.04085](https://arxiv.org/abs/1901.04085)
- Kuzi et al., hybrid lexical and semantic retrieval: [arXiv 2010.01195](https://arxiv.org/abs/2010.01195)
- Cormack et al., reciprocal rank fusion: [SIGIR 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- Bruch et al., fusion functions for hybrid retrieval: [arXiv 2210.11934](https://arxiv.org/abs/2210.11934)
- Wang et al., Balancing the Blend: [arXiv 2508.01405](https://arxiv.org/abs/2508.01405)
- Elastic, reranking depth: [Search Labs](https://www.elastic.co/search-labs/blog/elastic-semantic-reranker-part-3)
