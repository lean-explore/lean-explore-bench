# Learning an Effective Premise Retrieval Model for Efficient Mathematical Formalization (Tao, Liu, Wang, Xu)

- **Kind:** paper
- **Links:**
  - paper: https://arxiv.org/abs/2501.13959
  - code and model: https://github.com/ruc-ai4math/Premise-Retrieval
  - search engine: https://premise-search.com/
- **Authors / org, date:** Yicheng Tao, Haotian Liu, Shanwen Wang, Hongteng Xu (Renmin University of China). arXiv v1 2025-01-21, v3 2025-07-16. The LaTeX source uses the ICML 2025 style with the `accepted` option, which suggests ICML 2025 (unverified against the proceedings).
- **Status:** Code and trained model are said to be released, and a public search engine is said to be deployed "featuring a real-time updating database" ([paper §1](https://arxiv.org/abs/2501.13959)). Liveness of premise-search.com and the license were not checked (unverified).

## What it is

A lightweight retriever that takes a **formal proof state** as the query and returns Mathlib premises. It has two stages ([paper §3](https://arxiv.org/abs/2501.13959)):

- **Context-free retrieval (CFR):** a BERT bi-encoder.
- **Context-aware re-ranking (CAR):** a BERT cross-encoder.

Both are pre-trained from scratch on a Lean corpus with a WordPiece tokenizer trained for Lean.

## How it works

A small BERT pre-trained from scratch on Lean text retrieves candidates as a bi-encoder, and a cross-encoder re-ranks the top-20 ([paper §3, §4.1](https://arxiv.org/abs/2501.13959)).

## Evaluation

- **Dataset:** Mathlib tag v4.10.0, extracted with LeanDojo scripts, giving 149,549 premises ([paper Fig. 3, App. A](https://arxiv.org/abs/2501.13959)). Relevance labels come from the premises used at each tactic step. Both the state before and the state after the tactic count as queries ([paper §3.1](https://arxiv.org/abs/2501.13959)).
- **Anti-shortcut choice:** theorem names are stripped from the premise text, which is rendered as `<VAR> args <GOAL> goal` ([paper §3.2](https://arxiv.org/abs/2501.13959)).
- **Splits.** The paper builds **its own four splits** rather than reusing LeanDojo's. Each has 65,567 training theorems and 2,000 validation and 2,000 test theorems ([paper §4.1 "Data Split"](https://arxiv.org/abs/2501.13959)):
  - **RD (Random).**
  - **RI (Reference Isolated).** "Premises in the validation and test sets will not appear in the training set." This is the leakage-avoiding split, analogous to LeanDojo's novel_premises.
  - **PL (Proof Length).** Test proofs are sampled weighted by proof length.
  - **PF (Premise Frequency).** Test proofs are sampled weighted by premises per tactic.
- **Metrics.** Recall, Precision, F1 and nDCG, each at k ∈ {1, 5, 10}. nDCG uses graded relevance ([paper Table 1 "Relevance criteria"](https://arxiv.org/abs/2501.13959)):
  - 1 for an exact used premise;
  - **0.3 for a premise in the same module as a used premise**;
  - 0 otherwise.

  The graded scheme follows the LeanSearch v1 setup ([Gao et al. 2403.13310](https://arxiv.org/abs/2403.13310)).
- **Baselines.** All baselines were fine-tuned or re-trained on the same splits:
  - ReProver, re-trained;
  - UniXcoder-base;
  - E5-large-v2;
  - BGE-m3.

  LeanSearch and Moogle are discussed as natural-language search engines but **not** benchmarked ([paper §2.2, §4.1](https://arxiv.org/abs/2501.13959)).
- **Headline numbers** ([paper Table 2](https://arxiv.org/abs/2501.13959)), R@1 / R@5 / R@10 in %, and nDCG@10:

| Split | ReProver R@1/5/10 | Ours R@1/5/10 | ReProver nDCG@10 | Ours nDCG@10 |
|---|---|---|---|---|
| RD | 11.79 / 28.78 / 36.69 | 15.17 / 38.20 / 46.53 | 0.4617 | 0.5163 |
| RI | 5.05 / 14.26 / 19.48 | 7.79 / 23.38 / 30.91 | 0.3563 | 0.4322 |
| PL | 11.16 / 26.83 / 33.96 | 14.39 / 34.99 / 41.61 | 0.4232 | 0.4781 |
| PF | 8.29 / 22.74 / 30.21 | 11.44 / 31.02 / 38.88 | 0.4544 | 0.5238 |

  - RI is the hardest split for every method.
  - On RI, ReProver falls *below* the fine-tuned general embedders at R@10 (19.48 against 24.16–24.73). Its advantage is mostly memorisation of seen premises.
  - The general embedders stay roughly flat between RD and RI.

  ([paper Table 2, §4.2](https://arxiv.org/abs/2501.13959))
- **Ablations.**
  - Without re-ranking, CFR beats ReProver only for k ≥ 10. Re-ranking closes the gap at small k ([paper Fig. 4, §4.3](https://arxiv.org/abs/2501.13959)).
  - The Lean-specific tokenizer helps at k = 5 and k = 10 but slightly hurts at k = 1 ([paper Table 3](https://arxiv.org/abs/2501.13959)).
- **End-to-end.** A ByT5 tactic generator is trained **independently of any retriever**. Its training prompts contain randomly mixed positive and negative premises, so the retrievers can be compared fairly ([paper §3.3 "Training Tactic Generator"](https://arxiv.org/abs/2501.13959)).
  - On miniF2F, pass@1 is 30.74% with this retriever against 28.28% with ReProver ([paper §4.5](https://arxiv.org/abs/2501.13959)).
  - On the RD test set, proving is *slightly worse* than with ReProver despite better retrieval. The authors attribute this to longer contexts overwhelming a small generator ([paper §4.5](https://arxiv.org/abs/2501.13959)). Per-split proving numbers appear only in a figure (Fig. 7), so exact values were not extracted.
- **Robustness.** Shuffling the context or dropping 20% of it degrades performance by at most about 6% at k = 5 or 10. Training on 25% of the data is about 25% worse at k = 5 or 10 ([paper §4.4](https://arxiv.org/abs/2501.13959)).

## Relevance to lean-explore-bench

- **Retrieval gains do not guarantee proving gains.** Better R@k gave worse proving on RD. We should report retrieval-only and end-to-end results separately and never infer one from the other.
- **Decoupling the downstream consumer from the retriever** is a good protocol. The generator was trained on random premise mixes rather than on the outputs of a specific retriever. Any end-to-end track we build should use a consumer (LLM or agent) that has not been tuned to one engine.
- A **premise-isolated split** (RI) is decisive. It reverses the ranking of ReProver against general-purpose embedders. The same can happen to trained engines on our benchmark, so we need held-out-premise or time-based queries.
- **Name-stripping** in the premise representation is a deliberate anti-shortcut choice. For a search-engine benchmark, whether engines may see names is a design axis we must fix and document.
- Reusable items:
  - The RD/RI/PL/PF split recipes, especially RI.
  - The graded nDCG relevance scheme (1 / 0.3 same-module / 0). It gives partial credit for "right neighbourhood" results, which suits interactive search.
  - Precision@k and F1@k alongside Recall@k, for multi-premise queries.
  - premise-search.com as a proof-state-query engine to include in our comparison.

## Open questions

- Is premise-search.com still live, and which Mathlib version does it index now ("real-time updating database")?
- Were queries or states from the RI test set seen during MLM pre-training? Pre-training used training-split states plus *all premise* statements, so test premises' statements were seen, but not as positives.

## Sources

- Paper (LaTeX source read in full via arXiv): https://arxiv.org/abs/2501.13959 (v3)
- Code: https://github.com/ruc-ai4math/Premise-Retrieval (from the paper; not opened)
- Search engine: https://premise-search.com/ (from the paper; not opened, unverified)
- LeanSearch v1 (source of the relevance scheme): https://arxiv.org/abs/2403.13310
