# NaturalProofs (and ProofWiki premise selection)

- **Kind:** benchmark / dataset
- **Links:** paper https://arxiv.org/abs/2104.01112 · code/data https://github.com/wellecks/naturalproofs · follow-up NaturalProver https://arxiv.org/abs/2205.12910 · predecessor PS-ProofWiki https://aclanthology.org/2020.lrec-1.266/ and https://aclanthology.org/2020.acl-main.657/
- **Authors / org, date:** Welleck, Liu, Le Bras, Hajishirzi, Choi, Cho (UW / AI2 / NYU), arXiv March 2021, NeurIPS 2021 Datasets & Benchmarks track ([arXiv](https://arxiv.org/abs/2104.01112); venue from the LaTeX style `neurips_data_2021`)
- **Status:** data released; frozen snapshot (ProofWiki dump 2020-11-12, Stacks commit 4df67b8 from 2021-04-15) ([paper §3](https://arxiv.org/abs/2104.01112))

## What it is
An informal-math corpus of 32k theorem statements plus proofs, 14k definitions, and 2k other pages. It draws on ProofWiki (broad coverage), the Stacks project (deep coverage of algebraic geometry), and two textbooks: Trench's *Introduction to Real Analysis* and Stein's *Elementary Number Theory* ([paper §3](https://arxiv.org/abs/2104.01112)). The main task is **mathematical reference retrieval**. Given a theorem, the system must rank the whole reference set (theorems, lemmas, definitions) so that the references cited in the theorem's proof come first. The authors present this explicitly as the informal analogue of premise selection ([paper §1, §4](https://arxiv.org/abs/2104.01112)).

## How it works (benchmark design)
- **Ground truth = hyperlinks/`\ref`s used in the human-written proof.** References are binary relevant. Each test theorem has about 7.4 references on ProofWiki, 2.9 on Stacks, 2.2 on RA and 1.5 on NT ([Table 3](https://arxiv.org/abs/2104.01112)).
- **Leakage-aware split.** The evaluation theorems are randomly sampled **leaf nodes of the reference graph**, so no test theorem appears as a reference in training. The evaluation set is split roughly half validation and half test. As a result the training reference set is smaller than the evaluation reference set ([§4](https://arxiv.org/abs/2104.01112)).
- **Sizes (test):** ProofWiki has 1,135 queries over 30,671 references. Stacks has 776 over 15,134. RA has 167 over 384 and NT has 40 over 105; the two textbooks are used only zero-shot ([Table 3](https://arxiv.org/abs/2104.01112)).
- **Metrics:** mAP, Recall@k (micro-averaged) and **Full@k**, the fraction of theorems whose *entire* reference set appears in the top k ([§4, Table 4](https://arxiv.org/abs/2104.01112)).
- **Queries** are the theorem title plus its contents (mixed LaTeX and prose).

## Evaluation (reported numbers, test set, [Table 4/5](https://arxiv.org/abs/2104.01112))
| Model | PW mAP | PW R@10 | PW Full@100 | Stacks mAP | Stacks R@10 |
|---|---|---|---|---|---|
| TF-IDF | 6.19 | 10.27 | 9.43 | 13.64 | 25.46 |
| BERT pairwise (per-source) | 16.82 | 23.73 | 38.50 | 20.93 | 37.43 |
| BERT joint (per-source) | 36.75 | 42.45 | 50.22 | 28.32 | 39.10 |

- **Zero-shot on the textbooks:** TF-IDF *beats* the neural models on Real Analysis (mAP 15.79 against 13.24 for BERT-pair trained on ProofWiki), and the two are comparable on Number Theory. Joint training did not help out of domain ([Table 6](https://arxiv.org/abs/2104.01112)).
- **Title ablation:** on ProofWiki, TF-IDF and pairwise BERT did better with **titles only** than with title plus content. Descriptive names carry most of the signal ([title/content ablation table](https://arxiv.org/abs/2104.01112)).
- The authors note in their qualitative analysis that highly ranked non-gold references were often topically *relevant* but not cited. The citation-based ground truth therefore undercounts relevance ([qualitative evaluation paragraph](https://arxiv.org/abs/2104.01112)).
- MIRB later reuses NaturalProofs as its natural-language premise-retrieval task. Best nDCG@10 there is 37.21 (NV-Embed-v2) ([MIRB Table 4](https://arxiv.org/abs/2505.15585)); see `../lean-benchmarks/mirb.md`.

## Relevance to lean-explore-bench
- **Split pattern to borrow.** Holding out leaf nodes of the dependency graph maps directly onto Mathlib: evaluate on declarations that nothing else in the corpus uses. For Lean you can hold out whole recent files or modules instead.
- **Full@k** is a useful extra metric for multi-premise queries: "did the engine surface *everything* needed?"
- **Warning on proof-citation ground truth.** "Cited in proof" is only a *lower bound* on relevance: false negatives are common, as the authors' qualitative analysis shows. If we derive gold sets from Mathlib proof dependencies, we should add graded human or LLM judgments on top, or report results as a lower bound.
- **Title/name effect.** The title ablation corresponds to Lean declaration names. Report engines with and without access to names and docstrings, so name-matching cannot pass for semantic understanding.
- **Zero-shot domain shift** (textbook language vs. wiki language) is a good model for a test set of "queries written by a textbook author, not a Mathlib contributor".
- **Cross-link to Mathlib:** the Stacks subset uses Stacks tags, and Mathlib tags declarations with `@[stacks XXXX]` (see `informal-formal-alignment.md`). NaturalProofs Stacks statements can therefore be joined to Mathlib declarations.

## Open questions
- How many NaturalProofs/ProofWiki statements have a Mathlib counterpart? This has not been measured.
- The licenses (ProofWiki CC BY-SA 3.0, RA CC BY-NC-SA 3.0; [paper footnotes](https://arxiv.org/abs/2104.01112)) constrain redistribution of derived query sets.

## Sources
- Welleck et al., NaturalProofs, arXiv:2104.01112 (LaTeX source read via arXiv): https://arxiv.org/abs/2104.01112
- Welleck et al., NaturalProver, arXiv:2205.12910: https://arxiv.org/abs/2205.12910
- Ferreira & Freitas, Natural Language Premise Selection (LREC 2020): https://aclanthology.org/2020.lrec-1.266/ ; Premise Selection in Natural Language Mathematical Texts (ACL 2020): https://aclanthology.org/2020.acl-main.657/ ; code https://github.com/debymf/nl-ps
- Ju & Dong, MIRB, arXiv:2505.15585: https://arxiv.org/abs/2505.15585
- Repo: https://github.com/wellecks/naturalproofs (GitHub description confirms NeurIPS 2021 Datasets & Benchmarks)
