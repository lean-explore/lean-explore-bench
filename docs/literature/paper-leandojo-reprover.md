# LeanDojo / ReProver (LeanDojo Benchmark, LeanDojo Benchmark 4)

- **Kind:** paper (benchmark / dataset + retrieval-augmented prover)
- **Links:** paper [arXiv:2306.15626](https://arxiv.org/abs/2306.15626) (NeurIPS 2023 Datasets & Benchmarks, oral); site <https://leandojo.org/>; tool <https://github.com/lean-dojo/LeanDojo>; model code <https://github.com/lean-dojo/ReProver>; data: LeanDojo Benchmark (Lean 3) [doi:10.5281/zenodo.8016385](https://doi.org/10.5281/zenodo.8016385), LeanDojo Benchmark 4 (Lean 4) [doi:10.5281/zenodo.8040109](https://doi.org/10.5281/zenodo.8040109)
- **Authors / org, date:** Kaiyu Yang, Aidan M. Swope, Alex Gu, Rahul Chalamala, Peiyang Song, Shixing Yu, Saad Godil, Ryan Prenger, Anima Anandkumar (Caltech, NVIDIA, MIT, UCSB, UT Austin); v1 June 2023, v2 Oct 2023 ([arXiv](https://arxiv.org/abs/2306.15626)).
- **Status:** Open source. Tool and code MIT; datasets CC BY 2.0; mathlib/Lean content Apache 2.0 attributed in the dataset ([paper, App. "Data Hosting, Licensing, and Maintenance"](https://arxiv.org/abs/2306.15626)). Both benchmark snapshots are frozen at 2023 mathlib commits.

## What it is

The canonical academic benchmark for **premise selection / premise retrieval in Lean**, plus end-to-end theorem proving on the same theorems. It introduced the `random` vs `novel_premises` split, which is still the standard way Lean premise retrievers report recall ([arXiv:2306.15626](https://arxiv.org/abs/2306.15626)).

**Task definition (premise retrieval).** Query = the pretty-printed proof state *before* a tactic; gold = the premises (lemmas/definitions) that tactic references, as annotated by LeanDojo's instrumented elaborator; candidate pool = premises *accessible* to the current theorem (defined earlier in the same file, or in transitively imported files). Only tactics with at least one premise are evaluated; the retriever returns 100 premises per state ([paper, Sec. 4-5](https://arxiv.org/abs/2306.15626)).

## How it works

ReProver is a DPR-style dense retriever: a ByT5-small encoder with cosine similarity, trained contrastively with "in-file" hard negatives. Its top retrieved premises are concatenated with the state and passed to a ByT5 tactic generator that runs inside best-first search ([paper, Sec. 5](https://arxiv.org/abs/2306.15626)).

## Evaluation

**Dataset (Lean 3, LeanDojo Benchmark).** Mathlib commit `19c869ef…`: 98,734 theorems/proofs from 3,384 files; 130,262 premises; 217,776 tactics, of which 129,243 have at least one premise, with an average of 2.13 premises per such tactic. Train/val/test = 94,734 / 2,000 / 2,000 theorems. On average 33,160 premises are accessible per theorem, compared with about 128K in total ([paper, Sec. 4 and macros](https://arxiv.org/abs/2306.15626)).

**Dataset (Lean 4, LeanDojo Benchmark 4).** mathlib4 commit `3ce43c18…` (the paper says "released on October 21, 2023"): 102,514 theorems, 213,067 tactics, 152,695 premises; 2,000 val / 2,000 test; the same two splits ([paper, App. "LeanDojo for Lean 4"](https://arxiv.org/abs/2306.15626)).

**Splits (leakage control).**
- `random`: theorems are split at random.
- `novel_premises`: "It requires testing proofs to use at least one premise that has never been used in training." The paper motivates this split with blocks of near-duplicate theorems/proofs in mathlib. Under a random split, "the model can easily prove the other one by memorization" ([paper, Sec. 4](https://arxiv.org/abs/2306.15626)).
- A community discussion on Zulip (Morrison, Macbeth, Xu, Yang) notes several effects of this split. It "would encourage clustering of subject matter": 449 of ~3,000 files appear in test, and the whole `analysis.convex.*` folder was cited as an example. Yang acknowledged the clustering and noted that single-tactic proofs end up restricted to training. Junyan Xu proposed a stricter criterion: the premises of a test proof should not be a subset of the premises of any training proof ([Zulip archive, "Releasing LeanDojo"](https://leanprover-community.github.io/archive/stream/219941-Machine-Learning-for-Theorem-Proving/topic/Releasing.20LeanDojo.html)).
- Note: the split constrains *premise usage*, not premise *existence*. "Novel" premises are still in the retrieval corpus, and the theorem that defines one may appear in training with its own statement and proof. It is an inductive-generalization split, not a temporal or corpus-disjoint one. (This is our reading of the definition above; the paper does not discuss it.)

**Metrics.** Retrieval: R@1, R@10 ("recall for the top k retrieved premises") and MRR. Proving: Pass@1, meaning one attempt within a 10-minute wall-clock limit ([paper, Sec. 6](https://arxiv.org/abs/2306.15626)).

**Premise selection results, Lean 3 (Table 2 of the paper)** ([source](https://arxiv.org/abs/2306.15626)):

| Method | random R@1 | R@10 | MRR | novel_premises R@1 | R@10 | MRR |
|---|---|---|---|---|---|---|
| BM25 | 6.7 | 17.2 | 0.15 | 5.9 | 15.5 | 0.14 |
| BM25 w/ all premises | 1.9 | 11.9 | 0.08 | 2.1 | 12.4 | 0.08 |
| ReProver retriever | 13.5 | 38.4 | 0.31 | 9.1 | 27.6 | 0.24 |
| w/ all premises | 11.7 | 36.2 | 0.27 | 7.1 | 23.1 | 0.20 |
| w/o in-file negatives | 10.8 | 33.1 | 0.25 | 7.9 | 25.7 | 0.22 |

**Premise selection results, Lean 4 (appendix table):** ReProver R@1/R@10/MRR = 12.8 / 34.7 / 0.29 (`random`) and 9.8 / 32.1 / 0.24 (`novel_premises`). No BM25 row is reported for Lean 4 ([source](https://arxiv.org/abs/2306.15626)).

**End-to-end Pass@1 (%), Lean 3** ([source](https://arxiv.org/abs/2306.15626)):

| Method | random | novel_premises |
|---|---|---|
| `tidy` | 23.8 | 5.3 |
| GPT-4 (zero-shot, 35 tactics/state + best-first search) | 29.0 | 7.4 |
| ReProver | 51.2 | 26.3 |
| ReProver w/o retrieval | 47.6 | 23.2 |

**End-to-end Pass@1 (%), Lean 4:** ReProver 48.6 / 19.9 and w/o retrieval 44.5 / 16.2 (random / novel_premises) ([source](https://arxiv.org/abs/2306.15626)).

**Out-of-distribution results.** MiniF2F test Pass@1 26.5%; ProofNet Pass@1 13.8% (48/349). Of the ProofNet proofs, only 3 "can only be proved with the help of premise retrieval" ([paper, App. MiniF2F/ProofNet](https://arxiv.org/abs/2306.15626)).

**Contamination caveat.** The GPT-4 baseline may be contaminated: "many proofs had been publicly available on GitHub before GPT-4's data cutoff date (September 2021)" ([paper, Sec. 6](https://arxiv.org/abs/2306.15626)).

## Relevance to lean-explore-bench

- **The query distribution differs from search-engine queries.** LeanDojo queries are raw proof states and gold labels come from tactic premises. That is the "premise selection for a prover" task, not "a human or agent types a natural-language or name query." Retrieval numbers from this benchmark are therefore not directly comparable to search-engine evaluations.
- **The candidate pool matters a lot.** Restricting to accessible premises moves ReProver's novel_premises R@10 from 23.1 to 27.6, and BM25's from 12.4 to 15.5. Our benchmark must fix and document the candidate corpus, including the Mathlib commit and whether the pool is import-scoped, or cross-engine numbers are meaningless.
- **The retrieval gain end to end is modest.** Retrieval adds about 3-4 Pass@1 points on both Lean 3 and Lean 4 (51.2 vs 47.6; 48.6 vs 44.5). A big recall gap can translate into a small downstream gap, so both kinds of evaluation need reporting.
- **Leakage.** The `novel_premises` split is the field's standard leakage control, but it has known side effects (topic clustering, and the corpus is not disjoint). For search engines trained on or informalized from Mathlib, the relevant leakage is different: whether the engine's index or embeddings were fit on the evaluation queries' targets.
- **Reusable items:**
  - LeanDojo Benchmark 4 `corpus.jsonl` plus the `novel_premises` test split (2,000 theorems), usable as a proof-state-to-premise retrieval track with R@1, R@10 and MRR.
  - The BM25 row as a floor baseline.
  - The accessible-premise filter as an optional pool setting.
  - LeanDojo tracing to regenerate gold premise labels on a newer Mathlib commit, which is useful for a fresh, post-training-cutoff test set.

## Open questions

- How many LeanDojo Benchmark 4 test theorems still exist, unchanged, in current Mathlib? A snapshot mismatch will hurt engines that index a newer Mathlib, because of renames and deprecations.
- Does per-tactic gold (average 2.13 premises) over-penalize engines that return a semantically equivalent lemma? This benchmark has no graded relevance.

## Sources

- Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models", arXiv:2306.15626v2 (LaTeX source read in full): <https://arxiv.org/abs/2306.15626>
- LeanDojo site: <https://leandojo.org/>; code: <https://github.com/lean-dojo/LeanDojo>, <https://github.com/lean-dojo/ReProver>
- Zenodo datasets: <https://doi.org/10.5281/zenodo.8016385>, <https://doi.org/10.5281/zenodo.8040109>
- Lean Zulip archive, "Releasing LeanDojo" thread (split critique): <https://leanprover-community.github.io/archive/stream/219941-Machine-Learning-for-Theorem-Proving/topic/Releasing.20LeanDojo.html>
