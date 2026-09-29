# MIRB: Mathematical Information Retrieval Benchmark

- **Kind:** benchmark / dataset
- **Links:**
  - Paper: https://arxiv.org/abs/2505.15585
  - Code: https://github.com/j991222/mirb (Apache-2.0)
  - Data: https://huggingface.co/collections/hcju/mirb-6827001711765454f58c5a76
- **Authors / org, date:** Haocheng Ju, Bin Dong (Peking University), 21 May 2025.
- **Status:** Downloadable. The Lean-relevant components (`hcju/mathlibretrieval`) are CC-BY-4.0. The repo was last pushed 2025-05-29.

## What it is

MIRB is an MTEB/BEIR-style suite of 12 math retrieval datasets in 4 tasks: semantic statement retrieval, question-answer retrieval, premise retrieval, and formula retrieval. It evaluates embedding models, not search engines or services. Two datasets are Lean-relevant:

| Dataset | Relevance | #queries | #corpus | avg relevant docs per query |
|---|---|---|---|---|
| Informalized Mathlib4 Retrieval (from LeanSearch v1) | 3-level | 40 | 124,254 | 7.23 |
| LeanDojo premise retrieval (`novel_premises` split) | binary | 4,109 | 180,944 | 2.33 |

The other datasets are MSE and MO duplicate questions, ARQMath 1 and 2, ProofWiki, Stacks, NaturalProofs, MAPL (Isabelle), HolStep, and NTCIR-WFB (paper Table 1).

## How it works

- **Format:** BEIR-style `corpus.jsonl`, `queries.jsonl` and `qrels/test.jsonl`.
- **Metric:** nDCG@10 throughout.
- **Instructions:** per-dataset query instructions for instruction-tuned models (Table 8). For LeanDojo the instruction is "Given a Lean 4 proof state, retrieve the declarations that are useful for proving it."
- **Rerankers:** also tested (Table 10). They generally made results worse on math data.

## Evaluation

nDCG@10 from paper Table 9:

| Model | Informalized Mathlib4 | LeanDojo |
|---|---|---|
| BM25 | 31.49 | 6.91 |
| bge-large-en-v1.5 | 41.99 | 5.45 |
| e5-mistral-7b-instruct | 57.33 | 10.80 |
| NV-Embed-v2 | 59.48 | 12.27 |
| SFR-Embedding-2_R | **60.98** | 11.83 |
| text-embedding-3-large | 49.38 | 11.34 |
| voyage-3-large (best overall average) | 57.36 | **13.02** |

**Later use:** MathLeap (arXiv 2606.23959, Table 4) reports "mathlib Retrieval" nDCG@10 on this data:
- Qwen3-Embedding-8B: 0.559
- Octen-Embedding-8B: 0.653
- MathLeap-Octen-8B: 0.667

On Lean premise retrieval, the MathLeap fine-tunes scored lower than their base models (0.103 vs. 0.136 to 0.143).

## Relevance to lean-explore-bench

- **Harness format:** BEIR/MTEB format means any embedding model can be scored with off-the-shelf tooling. That is worth copying for the embedding-model track of our harness.
- **The Mathlib part is small:** the Informalized Mathlib4 task is only 40 queries, a re-packaging of the LeanSearch v1 benchmark. Its corpus is informal text only, so an engine's formal index cannot be used as is.
- **Premise retrieval:** LeanDojo premise retrieval scores are very low for general embedders (nDCG@10 about 5 to 13). This shows why proof-state queries need a separate track from natural-language search.
- **Scope:** MIRB does not test hosted engines or type-pattern search.

## Open questions

- Is the corpus exactly LeanSearch v1's informalization (126,208 rows in `hcju/leansearch_bench` versus 124,254 here)? The difference is unexplained (unverified).

## Sources

- Paper (Table 1 statistics, §3.1, §3.3, Tables 8–10): https://arxiv.org/abs/2505.15585 and https://arxiv.org/html/2505.15585v1
- Code: https://github.com/j991222/mirb (license via the GitHub API)
- Hugging Face dataset card: https://huggingface.co/datasets/hcju/mathlibretrieval
- MathLeap's use of the data: https://arxiv.org/abs/2606.23959 (Table 4)

## Merged detail: the rest of MIRB (from the former `embedding-evaluation/mirb.md` and `math-ir/mirb.md`)

**All 12 datasets** ([arXiv:2505.15585](https://arxiv.org/abs/2505.15585), Table 1):

| Task | Dataset | Relevance | #Q | #corpus | avg rel/Q |
|---|---|---|---|---|---|
| Semantic statement retrieval | Informalized Mathlib4 Retrieval (LeanSearch v1) | 3-level | 40 | 124,254 | 7.23 |
| | MSE duplicate question | binary | 25,116 | 1,350,505 | 1.78 |
| | MathOverflow duplicate question | binary | 225 | 108,301 | 1.08 |
| QA retrieval | ARQMath-3 Task 1 | 4-level | 78 | 33,369 | 100.79 |
| | ProofWiki theorem→proof | binary | 1,099 | 15,763 | 1.03 |
| | Stacks theorem→proof | binary | 776 | 10,423 | 1.00 |
| Premise retrieval | NaturalProofs | binary | 2,060 | 40,806 | 3.94 |
| | LeanDojo (`novel_premises`) | binary | 4,109 | 180,944 | 2.33 |
| | MAPL (Isabelle, Magnushammer) | binary | 4,000 | 493,029 | 7.07 |
| | HolStep (HOL Light) | binary | 1,411 | 3,973 | 22.82 |
| Formula retrieval | NTCIR-12 WFB | 3-level | 39 | 1,994 | 38.95 |
| | ARQMath-3 Task 2 | 4-level | 76 | 9,969 | 63.18 |

**Construction choices worth knowing** ([§3](https://arxiv.org/abs/2505.15585)):
- **Dynamic corpus against false negatives.** For the MSE and MO duplicate tasks, duplicate links are closed transitively, and any candidate sharing at least 50% of the query's tags is removed from that query's corpus (borrowed from BRIGHT's LeetCode subset). This removes likely unlabelled duplicates, but also the hardest distractors, which inflates scores.
- **Judged-only corpora.** For ARQMath and NTCIR, each query's corpus is restricted to its judged documents. Those scores are therefore *reranking over the judged pool*, not open retrieval, and are not comparable to open-corpus numbers.
- **Premise splits** follow LeanDojo's `novel_premises`; the authors built a similar split for MAPL.
- **Models evaluated:** BM25; small encoders (gte-large-en-v1.5, UAE-Large-V1, bge-large-en-v1.5); 1.5–7B LLM embedders (gte-Qwen2, e5-mistral, NV-Embed-v2, SFR-Embedding-2_R, GritLM); APIs (Cohere v3, text-embedding-3-large, voyage-3-large). No Qwen3-Embedding models; the paper predates them.
- **Rerankers** (bge-reranker-v2-m3, jina-reranker-v2) rerank only the top 10 of the five best retrievers, and still lowered scores: voyage-3-large's average fell from 54.54 to 48.36 and 50.42; on Informalized Mathlib4 from 57.36 to 55.22 ([Table 5](https://arxiv.org/abs/2505.15585)).
- **Premise retrieval is the hardest task:** off-the-shelf embedders reach only about 10–20 nDCG@10 on the formal sets (MAPL 15–18, HolStep 26–33, NaturalProofs 24–37).
- **Stated limitations:** premise gold from successful proofs has false negatives; ProofWiki and Stacks theorem→proof tasks lack hard negatives; no Coq premise dataset.

**For lean-explore-bench:** MIRB does not evaluate current small on-device models such as Qwen3-Embedding-0.6B, or Lean *engines* as opposed to raw embedders. Its reranker result is a direct reason to ablate LeanExplore's reranker (see [../embedding-evaluation/benchmark-lessons.md](../embedding-evaluation/benchmark-lessons.md)).
