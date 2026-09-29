# Mathlib4 Semantic Search Benchmark (LeanSearch v1)

- **Kind:** benchmark / dataset
- **Links:**
  - Paper: https://arxiv.org/abs/2403.13310 (EMNLP 2024 Findings), Section 4
  - Data on Hugging Face: https://huggingface.co/datasets/hcju/leansearch_bench (raw judged lists) and https://huggingface.co/datasets/hcju/mathlibretrieval (BEIR-format informal subset, as used in MIRB)
  - Code: https://github.com/frenzymath/LeanSearch (the older https://github.com/reaslab/LeanSearch now only redirects)
- **Authors / org, date:** Guoxiong Gao, Haocheng Ju, Jiedong Jiang, Zihan Qin, Bin Dong (PKU). arXiv March 2024. The Hugging Face datasets were uploaded 2025-05-16 by Haocheng Ju.
- **Status:** Both Hugging Face datasets are CC-BY-4.0 and not gated. The corpus is mathlib4 at commit `db04a978b67b…` (2024), so the benchmark is frozen on a stale snapshot.

## What it is

This was the first Mathlib search benchmark with graded relevance judgments. It has 50 queries in 18 "query groups", each group sharing one search intent and each containing at least two queries. The queries come in four forms:

| Form | Count |
|---|---|
| Natural description | 18 |
| LaTeX formula | 15 |
| Theorem name (e.g. "Schroeder Bernstein Theorem") | 7 |
| Lean 4 term | 10 |

The topics are calculus, abstract algebra, linear algebra, number theory, algebraic number theory, set theory, and logic (paper Table 1). The intents are theorem-only; Moogle's non-theorem hits were counted as irrelevant.

## How it works

- **Relevance scale** (Table 2), modelled on ARQMath:
  - Exact match (label 2, gain 1.0): the target, or a stronger statement.
  - Relevant (label 1, gain 0.3): "useful in locating where the corresponding statement should be".
  - Irrelevant (label 0).
- **Pooling:** assessors judged the top 50 results of an intermediate LeanSearch version for each group. They then added missed items by inspecting the files that held exact matches. Anything unjudged is assumed irrelevant, and every query has at least one exact match.
- **Metrics:**
  - nDCG@20, using the graded gains above.
  - P@10 and R@10, which count only exact matches.
- **Released files:**
  - `hcju/leansearch_bench/benchmark_data.txt`: 18 `#Query` blocks, each with its query variants and the judged ranked list as `rank name |label`. It holds 134 nonzero labels in total, by my count.
  - `name_formal_informal.jsonl`: the 126,208-row informalized corpus.
- **MIRB subset:** `hcju/mathlibretrieval` keeps **40** informal queries, 289 qrels (203 labelled 1 and 86 labelled 2), and a 124,254-document corpus. MIRB describes this as "retaining 40 out of the original 50", with the formal queries dropped.

## Evaluation

**Paper Table 3** (all 50 queries):

| System | nDCG@20 | P@10 | R@10 |
|---|---|---|---|
| Moogle† (non-theorems counted irrelevant) | 0.365 | 0.092 | 0.513 |
| BM25 (formal corpus) | 0.024 | 0.004 | 0.030 |
| text-embedding-3-large, formal corpus, no augmentation | 0.493 | 0.128 | 0.622 |
| E5-mistral-7b, formal corpus, no augmentation | 0.593 | 0.132 | 0.687 |
| E5-mistral-7b, formal+informal corpus, augmented query (LeanSearch) | **0.733** | **0.196** | **0.913** |

Per-category results are in Table 4. The Lean-term category favoured the formal-only corpus, which the paper explains as lexical matching dominating that category.

## Relevance to lean-explore-bench

**What to reuse:**
- Graded, multi-gold relevance with pooling. This is the right answer to the single-gold problem in MathlibQR.
- Query groups that share one intent across several phrasings, which is a precursor to MathlibQR's styles.
- The judged lists can seed a small graded track.

**Limitations:**
- Tiny: 18 intents.
- Theorem-only.
- Stale mathlib snapshot. Names may have changed, so the gold would need to be remapped by name.
- The pool was drawn from the authors' own system, which is a pooling bias.
- Moogle was scored with a special rule.
- The released data has 40 informal queries plus the raw lists, not an obvious 50-query qrels file.

## Open questions

- Is the full 50-query version, including the 10 Lean-term queries, recoverable from `benchmark_data.txt`? There are 18 groups; the `#Query` lines per group appear to include both formal and informal variants. Not fully checked.
- How many gold names still resolve in current Mathlib? Remapping has not been attempted.

## Sources

- Paper (§4.1 Table 1, §4.2 Table 2, §4.3, §5 Tables 3–4): https://arxiv.org/abs/2403.13310 and https://arxiv.org/html/2403.13310
- Hugging Face metadata and files: https://huggingface.co/api/datasets/hcju/leansearch_bench and https://huggingface.co/api/datasets/hcju/mathlibretrieval (license, created date, split sizes). The label counts are my own tally of the downloaded files.
- MIRB's description of the subset: https://arxiv.org/abs/2505.15585 (§3.1)
- Code-location redirect: README of https://github.com/reaslab/LeanSearch
