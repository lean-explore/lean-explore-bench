# MIRB (Mathematical Information Retrieval Benchmark)

- **Kind:** benchmark / dataset
- **Links:** paper [arXiv:2505.15585](https://arxiv.org/abs/2505.15585); code [github.com/j991222/mirb](https://github.com/j991222/mirb) (Apache-2.0, last push 2025-05-29, checked via GitHub API 2026-09-28); data [HF collection hcju/mirb](https://huggingface.co/collections/hcju/mirb-6827001711765454f58c5a76)
- **Authors / org, date:** Haocheng Ju, Bin Dong (Peking University; same group as LeanSearch, [arXiv:2403.13310](https://arxiv.org/abs/2403.13310)), May 2025.
- **Status:** Open data and code; not an MTEB task (no MIRB task found in the mteb repo by GitHub code search, 2026-09-28).

> The math-IR agent covers MIRB as math IR. This note looks at it only as an **embedding-model benchmark with formal (Lean) components**.

## What it is

MIRB is an MTEB/BEIR-style benchmark that evaluates general embedding models on math retrieval. It has 12 datasets in four tasks ([arXiv:2505.15585](https://arxiv.org/abs/2505.15585), Table 1):

| Task | Dataset | Relevance | #query | #corpus |
|---|---|---|---|---|
| Semantic statement retrieval | **Informalized Mathlib4 Retrieval** | 3-level | 40 | 124,254 |
| | MSE Dup. Question | binary | 25,116 | 1,350,505 |
| | MO Dup. Question | binary | 225 | 108,301 |
| QA retrieval | ARQMath-Task-1 | 4-level | 78 | 33,369 |
| | ProofWiki | binary | 1,099 | 15,763 |
| | Stacks | binary | 776 | 10,423 |
| Premise retrieval | NaturalProofs | binary | 2,060 | 40,806 |
| | **LeanDojo** (Lean 4 proof state → Mathlib premise) | binary | 4,109 | 180,944 |
| | MAPL (Isabelle) | binary | 4,000 | 493,029 |
| | HolStep | binary | 1,411 | 3,973 |
| Formula retrieval | NTCIR-WFB; ARQMath-Task-2 | 3-level; 4-level | 39; 76 | 1,994; 9,969 |

- **Informalized Mathlib4 Retrieval** reuses the LeanSearch evaluation set ([arXiv:2403.13310](https://arxiv.org/abs/2403.13310)). It keeps only the informal queries, 40 of the original 50. The corpus is informalized Mathlib4 statements, and relevance is graded on 3 levels.
- **LeanDojo** is built from the premises used in the next tactic step ([arXiv:2306.15626](https://arxiv.org/abs/2306.15626)). It uses the `novel_premises` split, "in which each proof in the test set uses at least one premise not seen during training".

## How it works

- **Setup:** dense models use cosine similarity. Each model has its own max query/document length and instruction choice, and the instructions are listed per dataset (for LeanDojo: "Given a Lean 4 proof state, retrieve the declarations that are useful for proving it"). The metric is nDCG@10, following prior work (BEIR, BRIGHT) (§4.1).
- **Models evaluated:** BM25; small encoders (gte-large-en-v1.5, UAE-Large-V1, bge-large-en-v1.5); 1.5–7B LLM embedders (gte-Qwen2, e5-mistral, NV-Embed-v2, SFR-Embedding-2_R, GritLM); and APIs (Cohere v3, text-embedding-3-large, voyage-3-large). No Qwen3-Embedding models; the paper predates them.
- **Reranking:** bge-reranker-v2-m3 and jina-reranker-v2-base-multilingual rerank the **top 10** from the five best retrievers.

## Evaluation

Selected nDCG@10 scores from the main results table ([arXiv:2505.15585](https://arxiv.org/abs/2505.15585), May 2025):

| Model | Inf. Mathlib4 | LeanDojo | Avg (12) |
|---|---|---|---|
| BM25 | 31.49 | 6.91 | 32.23 |
| bge-large-en-v1.5 | 41.99 | 5.45 | 39.00 |
| gte-Qwen2-1.5B-instruct | 55.17 | 8.40 | 45.62 |
| NV-Embed-v2 | 59.48 | 12.27 | 52.00 |
| SFR-Embedding-2_R | **60.98** | 11.83 | 52.29 |
| voyage-3-large | 57.36 | **13.02** | **54.54** |

- Formal premise retrieval (LeanDojo, MAPL, HolStep) is far harder than informal statement retrieval. The authors attribute this to models "not extensively pre-trained on large corpora of formal language data" (§4.2).
- **General-purpose rerankers made things worse.** Reranking with bge-reranker-v2-m3 lowered voyage-3-large's average from 54.54 to 48.36, and on Informalized Mathlib4 from 57.36 to 55.22. The authors conclude that "rerankers trained on general text retrieval tasks may not transfer effectively to mathematical retrieval" (§4.2 "Results of Reranking" and its table).
- Limitations the authors list (§6):
  - Premise sets built from successful proofs have **false negatives**, because other premises may also be useful.
  - Several QA sets lack hard negatives.

## Relevance to lean-explore-bench

- **Direct overlap with our task.** Informalized Mathlib4 Retrieval is essentially "natural-language query → Mathlib declaration". But 40 queries is too few for tight confidence intervals, and it comes from one engine's authors. Our benchmark should include it (or its source queries) as a baseline slice and report per-query bootstrap CIs.
- **LeanDojo premise retrieval** gives us a large, automatically labeled "goal → useful lemma" slice with a leakage-aware split (`novel_premises`). The false-negative caveat applies, so graded or partial credit is needed.
- **Reranker result.** Rerankers hurt even when applied only to the top 10. That strongly motivates evaluating LeanExplore's Qwen3-Reranker stage *separately*. The first thing to check is whether it helps at all on Lean queries (see [benchmark-lessons.md](benchmark-lessons.md)).
- **Gap to fill:** MIRB does not evaluate current small on-device models such as Qwen3-Embedding-0.6B, or Lean *engines* as opposed to raw embedders.

## Open questions

- Is the 3-level LeanSearch relevance scale still valid for current Mathlib, given renames and deprecations since 2024? Mapping it forward needs a declaration-rename table.

## Sources

- MIRB: https://arxiv.org/abs/2505.15585 (tables and sections read from the arXiv LaTeX source)
- LeanSearch / "A Semantic Search Engine for Mathlib4": https://arxiv.org/abs/2403.13310
- LeanDojo: https://arxiv.org/abs/2306.15626
- MIRB code: https://github.com/j991222/mirb
