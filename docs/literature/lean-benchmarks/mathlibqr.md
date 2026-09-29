# MathlibQR (LeanSearch v2 theorem-search benchmark)

- **Kind:** benchmark / dataset
- **Links:**
  - Paper: https://arxiv.org/abs/2605.13137 (Section 4.1, Appendix A.1, Appendix B.2)
  - Data: https://github.com/frenzymath/LeanSearch-v2/tree/main/benchmark (`MathlibQR.json`, `MathlibQR_shared171.json`)
  - Eval code: `src/leansearchv2/eval/search_metrics.py` and `scripts/reproduce_search.py` in the same repo
- **Authors / org, date:** Gao, Sun, Jiang, Wang, Xu, Wu, Dai, Dong. Peking University / BICMR, IQuest Research, and others (FrenzyMath). arXiv v1 dated 13 May 2026.
- **Status:** Downloadable. The repo is Apache-2.0 and the benchmark sits inside it; no separate data license is stated. The repo was created 2026-05-13 and last pushed 2026-05-18. The Legendre leaderboard has adopted MathlibQR as its main task, and so have later papers and announcements (see Evaluation).

## What it is

MathlibQR is an expert-written query set for single-declaration Mathlib search. Given a query, the task is to retrieve the one gold declaration.
- **Size:** 200 target declarations and 946 queries (each query is one "row").
- **Query styles:** each target has up to six, at most one per style: Lean-flavoured, LaTeX, plain natural language, conceptual slogan, informal nickname, and special-case instance.
- **Per-style counts** (paper Table 4): Lean 199, LaTeX 200, Natural 199, Slogan 197, Nickname 128, Special case 23.
- **Difficulty:** each target is tagged Easy (101) or Hard (99), based on "mathematical obscurity and technical complexity".
- **Declaration kinds** (my count from `MathlibQR.json`): theorem 74, structure 39, class 29, def 26, instance 25, inductive 6, lemma 1. Theorems are therefore only about 37% of targets, which is unusual; many earlier sets targeted theorems only.

## How it works (construction)

- **Target selection:** formalization experts picked 8 declarations from each of 25 top-level Mathlib folders. The six folders excluded were Control, Deprecated, Lean, Tactic, Testing and Util. The aim was balance across declaration types and difficulty (Appendix A.1).
- **Query writing:** experts then wrote up to six queries per target "wherever a given style was applicable". The special-case style models a user who knows a concrete instance, such as ℝⁿ, but not Mathlib's generalization.
- **Snapshot:** the queries were written against Mathlib **v4.29.1**. The LeanSearch v2 corpus is v4.28.0-rc1, and the competing engines index other snapshots.
- **Fair subset:** the main comparison uses 171 declarations and **810 queries** present in every compared system's corpus. `MathlibQR_shared171.json` lists them. Looser 937-row and full 946-row results are in Appendix C.4.
- **File format:** one JSON object per target with the fields `id`, `full_name`, `file` (path:line), `difficulty`, `kind`, `q1a_lean`, `q1b_latex`, `q1c_natural`, `q2_slogan`, `q3_nickname`, `q4_special_case`. An empty string means the style is absent. Example: `Lattice` has the nickname "lattice" and the slogan "a poset with binary joins and meets".
- **Relevance:** binary, with exactly one relevant declaration per query. Near-equivalent or more general lemmas are not credited.

## Evaluation

**Metrics:**
- nDCG@{1,5,10} and Recall@{10,50,100}, with binary single-document relevance.
- An LLM-as-judge ranking, which the paper says follows "the protocol introduced for Mathlib search by Asher (2025)", i.e. LeanExplore's. Claude Sonnet 4.5 sees each system's top-5 results in three random permutations per query and produces a strict 1–4 ordering, giving 2,430 judgments per system.
- The judge sees six fields per hit: name, kind, informal name, signature truncated to 800 characters, body truncated to 400, and informal statement truncated to 600. All systems' results are hydrated from one shared metadata source.
- The paper measures and reports the judge's primacy bias: position A improves mean rank by about 0.42–0.58 relative to position D. It averages the bias out with balanced permutations (Appendix B.2, Table 5).

**Paper Table 1** (fair subset, 810 queries):

| System | nDCG@1 | nDCG@5 | nDCG@10 | R@10 | R@50 | R@100 | LLM-judge mean rank |
|---|---|---|---|---|---|---|---|
| LeanExplore | 0.246 | 0.358 | 0.393 | 0.569 | 0.743 | 0.789 | 3.32 |
| LeanFinder | 0.370 | 0.514 | 0.533 | 0.698 | 0.824 | 0.875 | 2.87 |
| LeanSearch v2 (retriever only) | 0.340 | 0.472 | 0.494 | 0.657 | 0.790 | 0.830 | 2.18 |
| LeanSearch v2 (rerank) | 0.470 | 0.601 | 0.623 | 0.780 | 0.847 | 0.858 | 1.63 |

**Other reported MathlibQR results:**
- **Legendre leaderboard:** 894 of 946 queries against a pinned v4.28.0-rc1 corpus. LeanSearch v2 API: nDCG@10 0.571 and R@10 74.4%. Lean Finder v1: 0.591 and 72.6%. LeanExplore: 0.385 and 56.5%. See `legendre-leaderboard.md`. This is not the same subset as Table 1, so the numbers are not directly comparable.
- **TheoremGraph (arXiv 2606.25363), fair-810 subset:** their best configuration, without a reranker, reaches R@10 0.775 with 95% CI [0.746, 0.802] and nDCG@10 0.548. Configuration F reaches nDCG@10 0.558.
- **Axiomatic "Octo Search":** a Lean Zulip post (21 Aug 2026) claims 0.765 nDCG@10 and 0.914 R@10 "on the same subset" versus LeanSearch v2's 0.623 / 0.780. There is no report or code yet, so this is **(unverified)**.

## Relevance to lean-explore-bench

**What to reuse:**
- It is the current de facto shared benchmark, so we should report on it for comparability.
- The multi-style design, where the same target is phrased six ways, is a strong idea. It separates lexical from semantic failure modes. On Legendre, BM25 and dense models fail in opposite directions across styles.
- The per-kind and per-difficulty tags.
- The shared-snapshot subset, as a device for cross-engine fairness.
- The LLM-judge protocol, including its reported bias diagnostics.

**Limitations to design around:**
- **Small:** 200 targets, and effectively 171 on the fair subset. Bootstrap CIs on R@10 are about ±3 pt, which is wider than many headline gaps.
- **Only 23 special-case queries.** The style that matters most for "I don't know Mathlib's generality" is barely sampled.
- **Single gold per query.** Mathlib has many near-duplicate lemmas, API variants and more general lemmas that would satisfy a user. Binary single-gold scoring penalizes them. The LeanSearch v1 benchmark (`leansearch-v1-benchmark.md`) used graded, multi-gold labels.
- **Snapshot mismatch built in.** Queries target v4.29.1 while the reference corpus is v4.28.0-rc1, so 11 gold targets are missing from the LeanSearch v2 corpus (per Legendre).
- **Conflict of interest:** the same team built the benchmark and one of the ranked engines, and its document format, `lsv2-compat`, was later adopted as Legendre's renderer.
- **No real user queries**, no type-pattern (Loogle-style) queries, and no proof-state queries. Queries were written by experts looking at the target, which risks leaking vocabulary from the target.

## Open questions

- Will a larger or held-out MathlibQR v2 exist? Nothing is announced (unverified).
- What license applies specifically to the benchmark JSON? The repo is Apache-2.0, but the data has no separate statement.
- The fair subset is fully specified. `MathlibQR_shared171.json` holds `shared_declarations` (171 names) plus the lists `missing_in_4160` (26), `missing_in_4280` (11) and `missing_in_LE` (4, meaning LeanExplore). Its note field reads "shared = full_name ∈ Mathlib(4160) ∩ Mathlib(4280) ∩ Mathlib(LE)". I checked that these 171 names carry exactly 810 non-empty queries in `MathlibQR.json`. The "4160" snapshot is presumably Lean Finder's corpus; the file does not say so.

## Sources

- Paper (abstract, §4.1, Table 1, App. A.1 Table 4, App. B.2 Table 5): https://arxiv.org/abs/2605.13137 and https://arxiv.org/html/2605.13137v2
- Data and code: https://github.com/frenzymath/LeanSearch-v2 (license and dates via the GitHub API)
- `MathlibQR.json`: https://raw.githubusercontent.com/frenzymath/LeanSearch-v2/main/benchmark/MathlibQR.json. The kind, difficulty and 946-query counts are my own tally of this file.
- Legendre results: https://www.legendre-leaderboard.com/ and https://www.legendre-leaderboard.com/methodology
- TheoremGraph MathlibQR results (§ on concept retrieval, Table 6): https://arxiv.org/abs/2606.25363
- Octo Search claim: Lean Zulip, #general › "Discussion thread for Octo Search", message by Austin Letson, 2026-08-21 (https://leanprover.zulipchat.com/#narrow/channel/113488-general/topic/Discussion.20thread.20for.20Octo.20Search/near/617871976) **(unverified; no report released)**
