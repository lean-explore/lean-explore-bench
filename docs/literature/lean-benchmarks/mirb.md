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
