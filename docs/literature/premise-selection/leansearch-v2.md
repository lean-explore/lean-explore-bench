# LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving (and LeanSearch v1 benchmark)

- **Kind:** paper
- **Links:** v2 paper https://arxiv.org/abs/2605.13137 ; v2 code/data/benchmarks https://github.com/frenzymath/LeanSearch-v2 ; service https://leansearch.net/ ; v1 paper "A Semantic Search Engine for Mathlib4" https://arxiv.org/abs/2403.13310 ; v1 code/data https://github.com/reaslab/LeanSearch
- **Authors / org, date:** v2: Guoxiong Gao, Zeming Sun, Jiedong Jiang, Yutong Wang, Jingda Xu, Peihao Wu, Bryan Dai, Bin Dong (Peking University, IQuest Research, Kyoto RIMS, Westlake, et al.), arXiv May 2026 (v2 of preprint 14 May 2026). v1: Guoxiong Gao, Haocheng Ju, Jiedong Jiang, Zihan Qin, Bin Dong (Peking University), arXiv March 2024.
- **Status:** v2 claims all code, data and benchmarks are open-sourced; standard mode is live with API at leansearch.net ([abstract](https://arxiv.org/abs/2605.13137)). License of the benchmark data not stated in the paper (unverified).

## What it is

A retrieval paper that defines three evaluation tasks for Lean retrieval and releases two new benchmarks: **MathlibQR** (single-query search, 200 declarations / 946 queries) and **MathlibMPR** (global premise retrieval, 69 theorems from merged Mathlib PRs), plus a downstream "Prove" experiment that holds a prover loop fixed and swaps only the retriever ([§4](https://arxiv.org/abs/2605.13137)). This is the most complete head-to-head evaluation of Lean search engines (including LeanExplore and LeanFinder) in the literature as of this writing.

## How it works

One sentence: standard mode embeds a dependency-aware LLM-informalized Mathlib corpus with Qwen3-Embedding-8B and reranks the top-50 with Qwen3-Reranker-8B (no Mathlib fine-tuning), and reasoning mode runs an LLM sketch-retrieve-filter-judge loop over standard mode ([§3](https://arxiv.org/abs/2605.13137)).

## Evaluation

### Task 1: Search (query -> single declaration), MathlibQR

- **Construction:** formalization experts picked 8 declarations from each of 25 top-level Mathlib folders (excluding `Control`, `Deprecated`, `Lean`, `Tactic`, `Testing`, `Util`), balanced over declaration kinds and difficulty, then wrote up to six query styles per declaration: Lean-flavored, LaTeX, plain English, conceptual slogan, informal nickname, special-case instance. Totals: 199 / 200 / 199 / 197 / 128 / 23 queries per style; 101 Easy vs 99 Hard declarations. Built on Mathlib v4.29.1 ([App. A.1](https://arxiv.org/abs/2605.13137)).
- **Labels:** binary single-document relevance, one gold declaration per query ([§4.1](https://arxiv.org/abs/2605.13137)).
- **Snapshot-drift control:** because systems index different Mathlib snapshots, the headline uses a "fair" subset of 810 queries / 171 declarations present in every system's snapshot; "at-least-one" (937) and "full" (946) perspectives are reported in the appendix, where scores drop 4 to 6 points but ordering is unchanged ([§4.1, App. C](https://arxiv.org/abs/2605.13137)).
- **Metrics:** nDCG@{1,5,10}, Recall@{10,50,100}, plus an LLM-as-judge protocol "following LeanExplore": Claude Sonnet 4.5 sees each system's top-5 in three random permutations and produces a strict 1-4 ranking; mean rank over 2430 judgments per system ([§4.1](https://arxiv.org/abs/2605.13137)).
- **Headline numbers (fair subset, 810 rows)** ([Table 1](https://arxiv.org/abs/2605.13137)):

| System | nDCG@1 | nDCG@5 | nDCG@10 | R@10 | R@50 | R@100 | LLM-judge mean rank |
|---|---|---|---|---|---|---|---|
| LeanExplore | 0.246 | 0.358 | 0.393 | 0.569 | 0.743 | 0.789 | 3.32 |
| LeanFinder | 0.370 | 0.514 | 0.533 | 0.698 | 0.824 | 0.875 | 2.87 |
| LeanSearch v2 (retriever only) | 0.340 | 0.472 | 0.494 | 0.657 | 0.790 | 0.830 | 2.18 |
| LeanSearch v2 (rerank) | 0.470 | 0.601 | 0.623 | 0.780 | 0.847 | 0.858 | 1.63 |

- **Slices:** by query style, the "special case" slice is hardest: nDCG@10 0.079 (LeanExplore), 0.218 (LeanFinder), 0.500 (v2 rerank); on Lean-flavored queries LeanFinder's R@10 (0.735) edges v2 (0.729) ([App. C, Table "MathlibQR by query style"](https://arxiv.org/abs/2605.13137)). Per-kind slices (theorem/def/instance) also reported.
- **Ablation:** reranking adds about +0.10 nDCG@5 overall; kind-aware prompting adds about +0.03, mostly on definitions ([App. D.1](https://arxiv.org/abs/2605.13137)).
- LeanSearch v1 is not in the MathlibQR table (only LeanExplore, LeanFinder, and v2 variants).

### Task 2: Global premise retrieval, MathlibMPR

- **Task:** given a theorem (informal description + formal statement), retrieve the set of library lemmas the whole proof needs ([§1, §4.2](https://arxiv.org/abs/2605.13137)).
- **Construction:** 69 theorems from merged Mathlib PRs; experts identified the main theorem, summarized key steps and annotated the premises used; for some queries they also annotated alternative viable proof routings. PRs were filtered to exclude trivial restatements, special cases, notational rewrites ([§4.2, App. A.2](https://arxiv.org/abs/2605.13137)).
- **Premise groups:** ground truth is 1 to 8 groups per query (mean 2.96); lemmas within a group are interchangeable for a proof step ([§4.2](https://arxiv.org/abs/2605.13137)).
- **Leakage control:** selected PRs "postdate the corpora of all search engines compared", and were merged more than six months after the prover model's (Claude Sonnet 4.5) knowledge cutoff ([App. A.2](https://arxiv.org/abs/2605.13137)).
- **Metrics:** Recall@k (group) = fraction of premise groups with at least one member in top-k, macro-averaged; Covered@k = 1 iff some complete routing (original or expert alternative) has every group hit; k in {5,10,20,30,50}. A stricter "original routing only" Covered variant changes numbers by roughly 1-3 points and preserves ordering ([§4.2, App. C](https://arxiv.org/abs/2605.13137)).
- **Input contracts differ by system:** reasoning retrievers get informal+formal statement over the v2 informalized corpus; premise selectors (ReProver, LeanPremise, LeanStateSearch) get the proof state extracted by appending `:= sorry` and running the Lean REPL via LeanInteract, and each uses its own corpus ([App. B, Table "Per-system pipelines"](https://arxiv.org/abs/2605.13137)).
- **Headline numbers** ([Table 2](https://arxiv.org/abs/2605.13137)): Recall@10 (group): LeanSearch v2 reasoning 46.1, DIVER full pipeline 38.0, INF-X 28.2, ReasonIR 26.9, LeanStateSearch 9.3, ReProver 5.5, LeanPremise 4.8. Covered@10: v2 30.4, DIVER 24.6, LeanStateSearch 2.9, ReProver 1.4. Authors read the premise-selector gap as a scope mismatch (per-state vs whole-proof), not system quality.
- **Cost:** reasoning mode costs about $1.10 per query at API prices; standard mode about 0.2 s per query on two accelerators ([App. E](https://arxiv.org/abs/2605.13137)).

### Task 3: Prove (downstream, fixed loop, retriever swapped)

- **Setup:** a "simple reflection loop" with Claude Sonnet 4.5 as prover, 8 reflection rounds; solved = compiles with no live `sorry`. Datasets: FATE-H (100 graduate-level algebra problems) and MathlibMPR-Prop (50 MathlibMPR theorems expressible as `:= by sorry`). Each retriever is queried in its native contract; NL search engines (LeanFinder, v2 standard) get LLM-rewritten NL queries only on reflection rounds ([§4.3, App. B.2](https://arxiv.org/abs/2605.13137)).
- **Results** (solved / n) ([Table 3](https://arxiv.org/abs/2605.13137)):

| Retriever | FATE-H (100) | MathlibMPR-Prop (50) |
|---|---|---|
| no retrieval | 4 | 2 |
| LeanFinder | 12 | 5 |
| LeanStateSearch | 7 | 3 |
| INF-X-Retriever | 16 | 5 |
| LeanSearch v2 standard | 14 | 5 |
| LeanSearch v2 reasoning | 20 | 7 |

- With Kimi K2 Instruct as prover on FATE-H: no retrieval 1, standard 8, reasoning 12 ([App. D.2](https://arxiv.org/abs/2605.13137)). Removing the reasoning-mode judge/reflection drops FATE-H from 20 to 16 ([App. D.3](https://arxiv.org/abs/2605.13137)).
- Authors claim the downstream ordering matches the upstream group-recall ordering; with n=50-100 and single runs, differences of 1-4 problems are not significance-tested in the paper.

### LeanSearch v1 benchmark (arXiv 2403.13310)

- **Queries:** 50 queries in 18 intent groups, in four forms (natural description 18, LaTeX 15, theorem name 7, Lean 4 term 10) ([§4.1](https://arxiv.org/abs/2403.13310)).
- **Labels:** graded (Exact Match = 1, Relevant = 0.3, Irrelevant = 0), assessed on the top-50 of an intermediate version of their own engine plus manual additions from the same files; unlabeled items assumed irrelevant ([§4.2](https://arxiv.org/abs/2403.13310)). This pooling from one system biases toward it.
- **Metrics:** nDCG@20, P@10, R@10. Best (E5-mistral-7b, formal+informal corpus, augmented query): nDCG@20 0.733, P@10 0.196, R@10 0.913; Moogle 0.365 / 0.092 / 0.513 (non-theorem hits counted irrelevant); BM25 on formal corpus 0.024 nDCG@20 ([Table 3](https://arxiv.org/abs/2403.13310)).
- Pinned to Mathlib commit db04a978 ([§3](https://arxiv.org/abs/2403.13310)).

## Relevance to lean-explore-bench

- Directly benchmarks LeanExplore: it ranks last on MathlibQR (nDCG@10 0.393 on the fair subset) and was not included in the MathlibMPR or Prove experiments. Our benchmark should be able to reproduce or dispute this with a transparent protocol.
- The "fair subset" (intersection of snapshots) is the right answer to snapshot drift across engines; we should always report both intersection and full-set numbers.
- Query-style stratification (Lean / LaTeX / NL / slogan / nickname / special case) exposes big differences hidden by the aggregate; "special case" is the most discriminative slice.
- Set-valued ground truth with interchangeable-lemma groups and alternative routings is a better model of "was the search useful" than a single gold item.
- PR-merge-date filtering (after engine index dates and after the LLM's cutoff) is a concrete, cheap leakage control.
- Downstream "fixed loop, swap retriever" design with a no-retrieval row is the template for end-to-end evaluation, but it confounds retriever quality with when/how it is invoked (round 1 vs reflection only).
- Weaknesses to avoid: single annotator team who also built the winning system; LLM judge from the same vendor as the downstream prover; small n and no confidence intervals in the Prove task.

**Concrete reusable items:**
1. MathlibQR (946 queries, 6 styles, Easy/Hard tags) from github.com/frenzymath/LeanSearch-v2, as an external test set (check license).
2. MathlibMPR (69 theorems, premise groups, alt routings) and MathlibMPR-Prop (50) for set-valued retrieval and downstream proving.
3. Metrics: nDCG@k, Recall@k, group-Recall@k, Covered@k; LLM-judge rank with 3 permutations per query and position-bias diagnostics.
4. Proof-state extraction recipe: append `:= sorry`, run through LeanInteract REPL, read the `Sorry` goal.
5. Prove harness: 8-round reflection loop, "compiles and no live sorry" criterion, no-retrieval baseline row.

## Open questions

- Does the Prove success check exclude proofs that cite the target theorem itself when Mathlib in the verifier environment already contains the merged PR? The paper states only "compiles and no live sorry" ([App. B.2](https://arxiv.org/abs/2605.13137)); which Mathlib version the verifier used is not stated (unverified).
- Which LeanExplore version/snapshot and query mode were used in MathlibQR (unverified).
- Inter-annotator agreement for MathlibQR and MathlibMPR labels is not reported.

## Sources

- LeanSearch v2 paper: https://arxiv.org/abs/2605.13137 (read in full, LaTeX source v2)
- LeanSearch v2 repo: https://github.com/frenzymath/LeanSearch-v2 (not fetched; availability claim from the paper)
- LeanSearch v1 paper: https://arxiv.org/abs/2403.13310 (read via arXiv HTML)
- See also `../lean-engines/leansearch.md` in this directory for the engine itself.
