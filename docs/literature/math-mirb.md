# MIRB: Mathematical Information Retrieval Benchmark

- **Kind:** benchmark / dataset (aggregator)
- **Links:** https://arxiv.org/abs/2505.15585 · code https://github.com/j991222/mirb · data https://huggingface.co/collections/hcju/mirb-6827001711765454f58c5a76
- **Authors / org, date:** Haocheng Ju, Bin Dong (Peking University), arXiv May 2025 ([arXiv](https://arxiv.org/abs/2505.15585))
- **Status:** public code and data; NeurIPS 2025 template, preprint ([source](https://arxiv.org/abs/2505.15585))

> See also `bench-mirb.md` (written by another agent); this note focuses on the non-Lean tasks and construction choices.

## What it is
A BEIR/MTEB-style collection of 12 math retrieval datasets in 4 tasks. It is the closest thing to a unified leaderboard spanning informal math IR and formal premise selection ([§3, Table 1](https://arxiv.org/abs/2505.15585)):

| Task | Dataset | Relevance | #Q | #corpus | avg rel/Q |
|---|---|---|---|---|---|
| Semantic statement retrieval | Informalized Mathlib4 Retrieval (from LeanSearch) | 3-level | 40 | 124,254 | 7.23 |
| | MSE duplicate question | binary | 25,116 | 1,350,505 | 1.78 |
| | MathOverflow duplicate question | binary | 225 | 108,301 | 1.08 |
| QA retrieval | ARQMath-3 Task 1 | 4-level | 78 | 33,369 | 100.79 |
| | ProofWiki theorem→proof | binary | 1,099 | 15,763 | 1.03 |
| | Stacks theorem→proof | binary | 776 | 10,423 | 1.00 |
| Premise retrieval | NaturalProofs | binary | 2,060 | 40,806 | 3.94 |
| | LeanDojo (novel_premises) | binary | 4,109 | 180,944 | 2.33 |
| | MAPL (Isabelle, Magnushammer) | binary | 4,000 | 493,029 | 7.07 |
| | HolStep (HOL Light) | binary | 1,411 | 3,973 | 22.82 |
| Formula retrieval | NTCIR-12 WFB | 3-level | 39 | 1,994 | 38.95 |
| | ARQMath-3 Task 2 | 4-level | 76 | 9,969 | 63.18 |

## How it works (construction choices worth noting)
- **Dynamic corpus to fight false negatives.** For the MSE and MO duplicate tasks, duplicate links are closed transitively. For each query, any candidate that shares at least 50% of the query's tags is *removed* from that query's corpus, so unlabelled duplicates cannot appear as false negatives. The idea is borrowed from BRIGHT's LeetCode subset ([§3.1](https://arxiv.org/abs/2505.15585)).
- **Judged-only corpora for pooled collections.** ARQMath is scored with nDCG′, which drops unjudged documents. MIRB therefore restricts each ARQMath or NTCIR query's corpus to its judged documents, averaging 446.8 annotated answers per query for ARQMath-3 Task 1 ([§3.2, §3.4](https://arxiv.org/abs/2505.15585)). Scores are then *reranking over the judged pool*, not open retrieval.
- **Premise sets:** these follow LeanDojo's `novel_premises` split. For MAPL the authors built a similar split, in which every test state uses at least one premise not seen in training ([§3.3](https://arxiv.org/abs/2505.15585)).
- **Metric:** nDCG@10 throughout. Dense models use cosine similarity with per-dataset instructions ([§4.1](https://arxiv.org/abs/2505.15585)).

## Evaluation (nDCG@10, [Table 4](https://arxiv.org/abs/2505.15585))
| Model | Inf. Mathlib4 | NaturalProofs | LeanDojo | MAPL | HolStep | Avg (12) |
|---|---|---|---|---|---|---|
| BM25 | 31.49 | 24.14 | 6.91 | 15.27 | 25.88 | 32.23 |
| SFR-Embedding-2_R | 60.98 | 34.67 | 11.83 | 17.07 | 30.76 | 52.29 |
| NV-Embed-v2 | 59.48 | 37.21 | 12.27 | 16.58 | 32.77 | 52.00 |
| voyage-3-large | 57.36 | 32.74 | 13.02 | 17.77 | 32.68 | 54.54 |

- Premise retrieval is by far the hardest task. Off-the-shelf embedders reach only about 10–20 nDCG@10 on the formal sets ([§4.2](https://arxiv.org/abs/2505.15585)).
- **General-purpose rerankers hurt.** Reranking the top 10 with bge-reranker-v2-m3 or jina-reranker-v2 mostly *lowered* scores; voyage-3-large's average fell from 54.54 to 48.36 and 50.42 ([Table 5](https://arxiv.org/abs/2505.15585)).
- The authors' stated limitations: there are no hard negatives in the ProofWiki and Stacks theorem→proof tasks, and there is no Coq premise dataset. Premise gold comes from successful proofs, so "other premises may also be helpful", which means false negatives ([Limitations](https://arxiv.org/abs/2505.15585)).

## Relevance to lean-explore-bench
- **Harness pattern:** we can use MIRB's per-dataset instruction plus nDCG@10 protocol, and its HF-hosted format, as the external-validity suite. Report Lean engines' embedders on MIRB alongside our own set.
- **Informalized Mathlib4 Retrieval is only 40 queries** and uses a 3-level scale; our benchmark should be far larger. Relevance criteria come from the LeanSearch paper (covered by the Lean-engine notes).
- **Borrow the dynamic-corpus trick.** Removing near-duplicates of the gold from the candidate pool is a reasonable way to handle the many near-identical Mathlib lemma variants (`foo`, `foo'`, `foo_of_le`). Better still, grade those variants as partially relevant rather than delete them.
- **Caveat:** reranking-over-judged-pool numbers (the ARQMath and NTCIR parts) are not comparable to open-corpus retrieval numbers. Keep the two separate in our reporting.

## Open questions
- The Hugging Face data for Informalized Mathlib4 is pinned to a 2024 Mathlib snapshot. Declaration renames since then would break gold IDs; we would need to check this before reuse.

## Sources
- Ju & Dong, MIRB, arXiv:2505.15585 (LaTeX source read): https://arxiv.org/abs/2505.15585
- GitHub and HF links as given in the paper's abstract footnote (not separately fetched).
