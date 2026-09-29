# Combining Textual and Structural Information for Premise Selection in Lean (Petrovčič, Narváez, Todorovski)

- **Kind:** paper
- **Links:** paper https://arxiv.org/abs/2510.23637 ; code https://github.com/JobPetrovcic/GNNReProver/tree/lighweight (branch name spelled `lighweight` in the paper)
- **Authors / org, date:** Job Petrovčič, David Eliecer Narváez Denis, Ljupčo Todorovski (Faculty of Mathematics and Physics, University of Ljubljana; Jožef Stefan Institute). arXiv v1 2025-10-24, v2 2025-11-28. Accepted at the NeurIPS 2025 MATH-AI workshop, per the LaTeX header (`\workshoptitle{MATH-AI}`, `neurips_2025` style).
- **Status:** Workshop paper. Extraction code and training pipeline released at the GitHub link above. The license was not checked (unverified).

## What it is

A premise retriever for Lean 4 that refines ReProver's ByT5 text embeddings with a relational graph convolutional network (RGCN). The RGCN runs over a heterogeneous dependency graph containing premise→premise and premise→proof-state edges. The task is the LeanDojo per-tactic premise selection task: given a proof state, rank the library premises that the next tactic uses. ([paper §2.1](https://arxiv.org/abs/2510.23637))

## How it works

ReProver's ByT5 embeddings are refined by a 2-layer relational GCN over a dependency graph that joins premises and proof states, and the model is trained with InfoNCE loss using all other library premises as negatives ([paper §3](https://arxiv.org/abs/2510.23637)).

## Evaluation

- **Dataset:**
  - Mathlib commit `29dcec074de168ac2bf835a77ef68bbe069194c5`, the same commit as the official LeanDojo benchmark.
  - The graph-augmented version has 180,907 premise nodes, 259,580 state nodes and 379,861 next-tactic premise labels ([paper §2.2, App. A](https://arxiv.org/abs/2510.23637)).
- **Task:** LeanDojo per-tactic premise selection. The query is a proof state; the gold set is the premises used by the next tactic ([paper §2.1](https://arxiv.org/abs/2510.23637)).
- **Leakage controls:**
  - At evaluation, candidates are restricted to LeanDojo's accessible premises: the import closure plus premises defined earlier in the same file ([paper §2.1](https://arxiv.org/abs/2510.23637)).
  - The graph is used transductively, but proof-dependency edges are excluded "to prevent trivial memorization" ([paper §3.2](https://arxiv.org/abs/2510.23637)).
  - The paper does not say whether test theorems' signature edges are in the training graph. They probably are (unverified inference). This is benign under the random split.
- **Split:** only the LeanDojo **random** split. The **novel_premises** split was *not* evaluated. The authors list it, and a split by premise creation time, as future work. ([paper §4.1, §5](https://arxiv.org/abs/2510.23637))
- **Metrics:** Recall@1, Recall@10, MRR, matching LeanDojo. Hyperparameters were tuned with Optuna on the validation set, selecting on validation R@10. ([paper §4.1, App. B](https://arxiv.org/abs/2510.23637))
- **Headline numbers** (LeanDojo random test set, [paper Table 1](https://arxiv.org/abs/2510.23637)):

| Model | R@1 | R@10 | MRR |
|---|---|---|---|
| ReProver (re-run baseline) | 13.42% | 39.60% | 0.3283 |
| GNN-augmented | 17.98% | 50.04% | 0.4095 |
| GNN-augmented + EMA | 18.31% | 50.33% | 0.4140 |

  The ReProver baseline numbers differ from the original LeanDojo paper. The authors point to a [ReProver GitHub discussion #51](https://github.com/lean-dojo/ReProver/discussions/51) that attributes the gap to later changes in ReProver.
- **Ablation undercuts the headline** ([paper Table 2, §4.3](https://arxiv.org/abs/2510.23637)). Removing the context (state) graph or the premise graph does not hurt, and sometimes helps. For example, the premise-graph ablation with EMA reaches R@10 49.98% against 48.70% for the full non-ensembled model. The authors conclude the gain may come from the changed loss function and negative-sampling strategy rather than from the graph structure.
- There is no end-to-end proving evaluation.

## Relevance to lean-explore-bench

- This is a clear example of a retriever gain that is **confounded by training changes**. The ablation shows a +25% relative gain that is not attributable to the method's headline idea. Our benchmark should report baselines under matched conditions and encourage ablations.
- It also shows **baseline drift**: re-running ReProver gives numbers different from the published ones. We should re-run every baseline ourselves on a pinned snapshot rather than copy published numbers.
- **Random-split-only results are weak evidence.** LeanDojo's random split lets test premises appear as training positives. A benchmark aimed at search engines should prefer novel-premise or time-based splits.
- Reusable items:
  - The typed edge taxonomy (signature-hypothesis / signature-goal / proof), useful for building graph-based candidate filters or for labelling relevance.
  - The practice of enforcing LeanDojo's accessible-premises candidate restriction at eval time.
  - The R@1 / R@10 / MRR metric triple, for comparability with LeanDojo-lineage results.

## Open questions

- Would the gains survive on novel_premises, where graph-based priors (such as degree) may matter more or less?
- Are test theorems' signature edges present during transductive training, and does that matter on a non-random split?

## Sources

- Paper (LaTeX source read in full via arXiv): https://arxiv.org/abs/2510.23637 (v2)
- Code: https://github.com/JobPetrovcic/GNNReProver/tree/lighweight (not opened; link taken from the paper)
- ReProver discussion on baseline drift: https://github.com/lean-dojo/ReProver/discussions/51 (cited by the paper; not opened, unverified)
