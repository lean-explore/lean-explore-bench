# HOL-family premise selection: HolStep, HOList/DeepHOL, HOL(y)Hammer, HOL4 hammer, TacticToe

- **Kind:** cluster note (datasets / benchmarks)
- **Links:** HolStep [arXiv 1703.00426](https://arxiv.org/abs/1703.00426); HOList [arXiv 1904.03241](https://arxiv.org/abs/1904.03241); GNN on HOList [arXiv 1905.10006](https://arxiv.org/abs/1905.10006); HOL(y)Hammer/Flyspeck [arXiv 1211.7012](https://arxiv.org/abs/1211.7012); HOL4 hammer [arXiv 1509.03534](https://arxiv.org/abs/1509.03534); TacticToe [arXiv 1804.00596](https://arxiv.org/abs/1804.00596); HOL4 [DB.match docs](https://hol-theorem-prover.org/trindemossen-2-helpdocs/help/Docfiles/HTML/DB.match.html)
- **Authors / org, date:** Kaliszyk, Chollet, Szegedy, ICLR 2017; Bansal, Loos, Rabe, Szegedy, Wilcox (Google), ICML 2019; Paliwal et al. (Google), 2019; Kaliszyk & Urban, JAR 2014; Gauthier & Kaliszyk, CPP 2015; Gauthier, Kaliszyk, Urban, Kumar, Norrish, JAR 2021
- **Status:** HolStep is BSD-licensed ([abstract](https://arxiv.org/abs/1703.00426)). HOList is open source ([abstract](https://arxiv.org/abs/1904.03241)). Current maintenance was not checked (unverified).

## What it is

These are HOL Light and HOL4 datasets and benchmarks where "relevance" means *a premise was used in a proof*. Tool context: HOL4's `DB.match` returns theorems of given theories that have a subterm matching a pattern ([docs](https://hol-theorem-prover.org/trindemossen-2-helpdocs/help/Docfiles/HTML/DB.match.html)); `DB.find` searches by name (per [HOL4 docs listing](https://hol-theorem-prover.org/kananaskis-14-helpdocs/help/Docfiles/HTML/DB.matches.html); detail unverified). None of these symbolic search commands has a published relevance evaluation that we found.

## How it works (evaluation protocols only)

- **HolStep (2017).** 11,400 HOL Light proofs (core library + Flyspeck) give 2,013,046 training and 196,030 test examples. Each example is an intermediate statement labelled useful or not useful in the final proof, with **exactly 50/50 balance per proof**. The main task is binary classification, unconditioned or conditioned on the conjecture, scored by accuracy ([§2–4](https://arxiv.org/abs/1703.00426)).
- **HOList / DeepHOL (2019).** Corpora: core, complex (complex analysis) and Flyspeck, about 30k theorems in total. Top-level theorems are split **60:20:20 at random**, and every subgoal inherits its theorem's split. Premise ranking (the "tactic argument" list) is trained on human proof logs, with hard negatives. The primary metric is **end-to-end % of theorems closed** on the validation set of the complex corpus (3,225 theorems). Proxy metrics were also tracked: tactic accuracy, and "success rate of selecting a positive tactic argument over a randomly selected negative", with about 1% error ([§4, §6](https://arxiv.org/abs/1904.03241)).
- **HOL(y)Hammer on Flyspeck (2014).** A **bootstrapping, chronological** evaluation that "emulat[es] the development of Flyspeck from axioms to the last theorem, each time using only the previous theorems and proofs". It covers 14,185 theorems and measures ATP success in 30 s ([abstract](https://arxiv.org/abs/1211.7012)).
- **HOL4 hammer (2015).** Compares four accessible-fact settings on 13,910 standard-library conjuncts ([§3.2](https://arxiv.org/abs/1509.03534)):
  - exact dependencies (reproving, no filtering);
  - transitive dependencies;
  - loaded theories;
  - linear order.
- **TacticToe (2018/2021).** Retrieves tactics used for similar goals, then runs MCTS. Evaluated by % of 7,164 HOL4 standard-library theorems proved in 60 s ([abstract](https://arxiv.org/abs/1804.00596)).

## Evaluation

| Benchmark | Ground truth | Metric | Numbers |
|---|---|---|---|
| HolStep | step used in the final proof (balanced) | accuracy | Logistic regression 0.71; 1D CNN 0.82–0.83; conditioning on the conjecture gave no gain ([Tables 2–3, §5.3](https://arxiv.org/abs/1703.00426)) |
| HOList (complex, validation) | proof found | % closed | ASM_MESON_TAC 6.1%; with learned argument selection 9.2%; best RL loop 38.9% ([Table 2](https://arxiv.org/abs/1904.03241)) |
| HOList + GNN | proof found | % closed (validation) | 49.95% best ([Paliwal et al.](https://arxiv.org/abs/1905.10006)) |
| Flyspeck HOL(y)Hammer | ATP success, chronological | % proved | 39% of 14,185 ([abstract](https://arxiv.org/abs/1211.7012)); later raised to 47%, per [HOL4 hammer paper](https://arxiv.org/abs/1509.03534) |
| HOL4 hammer | ATP success, 4 accessibility settings | % reproved | Loaded-theories and linear-order settings did *better* than exact-dependency reproving, which the authors attribute to the HOL4 library being dense and to alternative proofs ([§4](https://arxiv.org/abs/1509.03534)) |
| TacticToe | proof found | % proved in 60 s | 66.4% vs. E prover 34.5%; 69.0% combined ([abstract](https://arxiv.org/abs/1804.00596)) |

## Relevance to lean-explore-bench

- **HolStep shows how balanced binary labels overstate retrieval quality.** A context-free logistic regression reached 71% ([§5.1](https://arxiv.org/abs/1703.00426)), and conditioning on the conjecture added nothing. The task mostly measures a statement's prior "usefulness", not relevance to the query. Our benchmark needs **ranking over the full candidate pool** with realistic class imbalance, not pairwise accuracy. It should also include a **query-agnostic popularity baseline**, e.g. rank by how often a declaration is used in Mathlib, to expose this effect.
- **Proxy vs. end-to-end.** HOList's pairwise proxy error was about 1% while its end-to-end proof rates were in the 30s ([§6.2](https://arxiv.org/abs/1904.03241)). Pairwise-with-random-negative metrics saturate, so we should use hard negatives, or full-corpus ranking.
- **Accessibility settings matter.** The HOL4 study shows that the candidate set (exact dependencies, transitive dependencies, loaded theories, or chronological order) changes measured performance substantially ([§3.2, §4](https://arxiv.org/abs/1509.03534)). We must fix and document the candidate corpus: Mathlib version, which packages are included, and whether private or auxiliary declarations count.
- **"Better than ground truth" results mean the labels are incomplete.** Provers found alternative proofs that beat reproving from the exact dependencies ([§4](https://arxiv.org/abs/1509.03534)). A single gold premise under-counts relevant results, which argues for judged pools or graded multi-answer qrels.
- **Random theorem-level splits (HOList 60:20:20) leak cross-theorem information.** Flyspeck's chronological bootstrapping is the stricter alternative ([abstract](https://arxiv.org/abs/1211.7012)).

## Open questions

- Is HOList still runnable, and is its premise-ranking data reusable as a cross-system sanity benchmark? (unverified)
- The exact numbers in the HOL4 hammer's per-setting Table 3 were not extracted cleanly from the PDF; re-check before quoting ([arXiv 1509.03534](https://arxiv.org/abs/1509.03534)).

## Sources

- Kaliszyk, Chollet, Szegedy, "HolStep", ICLR 2017: https://arxiv.org/abs/1703.00426
- Bansal et al., "HOList", ICML 2019: https://arxiv.org/abs/1904.03241
- Paliwal et al., "Graph Representations for Higher-Order Logic and Theorem Proving", 2019: https://arxiv.org/abs/1905.10006
- Kaliszyk & Urban, "Learning-Assisted Automated Reasoning with Flyspeck", JAR 2014: https://arxiv.org/abs/1211.7012
- Gauthier & Kaliszyk, "Premise Selection and External Provers for HOL4", CPP 2015: https://arxiv.org/abs/1509.03534
- Gauthier et al., "TacticToe: Learning to Prove with Tactics", JAR 2021: https://arxiv.org/abs/1804.00596
- HOL4 help docs, DB.match: https://hol-theorem-prover.org/trindemossen-2-helpdocs/help/Docfiles/HTML/DB.match.html ; DB.matches: https://hol-theorem-prover.org/kananaskis-14-helpdocs/help/Docfiles/HTML/DB.matches.html
