# Other Lean premise-selection papers: Lean Copilot, LeanAgent, graph-augmented ReProver

- **Kind:** paper cluster, kept for the evaluation lessons only
- **Status:** all three released code (links below)

## Lean Copilot `select_premises` (Song, Yang, Anandkumar; NeuS 2025)

- `select_premises` scores the goal against precomputed ReProver embeddings over a **fixed October 2023 mathlib4 snapshot** and marks hits as in scope or needing an import ([arXiv:2404.12534](https://arxiv.org/abs/2404.12534); [repo](https://github.com/lean-dojo/LeanCopilot)).
- **It was never evaluated as a retriever:** "it remains a challenge in the field to effectively evaluate premise selection due to the inherent lack of ground truths" (§5).
- The paper's only evaluation is a human-in-the-loop simulation on the 168 tactic-proved theorems of *Mathematics in Lean*: how many tactics a human must enter before a tool finishes the proof (`aesop` 3.86, `suggest_tactics` 3.10, `search_proof` 2.08; 63.7% of theorems proved autonomously). This "human steps saved" metric is a reusable **assistive** end-to-end measure.
- The in-scope/out-of-scope annotation suggests an import-aware metric: does the engine surface lemmas the current file can use?

## LeanAgent (Kumarappan et al.; ICLR 2025, unverified venue)

- Keeps a ReProver retriever updated across a curriculum of 23 GitHub Lean repositories and reports six lifelong-learning metrics from per-repo R@10 (plasticity on the newest repo, stability averaged over previous ones) ([arXiv:2410.06209](https://arxiv.org/abs/2410.06209), v8).
- **Leakage warning:** random splits throughout, a retriever pre-trained on LeanDojo's random split, and MiniF2F validation and test used together; some "proved" `sorry` theorems had placeholder `0=1` statements.
- **What to reuse:** a multi-repo test pool (PFR, Carleson, SciLean, Coxeter) for an out-of-Mathlib track, and the "average R@10 over previously seen repositories" protocol for index-freshness studies.

## Graph-augmented ReProver (Petrovčič, Narváez, Todorovski; NeurIPS 2025 MATH-AI workshop)

- An RGCN over a premise/proof-state dependency graph refines ReProver embeddings; evaluated only on LeanDojo's **random** split with accessible-premise candidates ([arXiv:2510.23637](https://arxiv.org/abs/2510.23637)).
- Headline R@10 39.60 → 50.33 over a re-run ReProver, but the authors' ablation shows removing either graph does not hurt, so the gain probably comes from the changed loss and negative sampling, not the graph.
- **Lessons:** gains can be confounded by training changes, so require matched ablations; re-run baselines yourself, since the re-run ReProver differs from published numbers ([ReProver discussion #51](https://github.com/lean-dojo/ReProver/discussions/51)); random-split-only results are weak evidence.
