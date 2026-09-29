# Magnushammer: A Transformer-Based Approach to Premise Selection

- **Kind:** paper
- **Links:** paper [arXiv:2303.04488](https://arxiv.org/abs/2303.04488) (ICLR 2024); dataset [HF: Simontwice/premise_selection_in_isabelle](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle); data-generation code [github.com/Simontwice/MagnusData](https://github.com/Simontwice/MagnusData)
- **Authors / org, date:** Maciej Mikuła, Szymon Tworkowski, Szymon Antoniak, Bartosz Piotrowski, Albert Q. Jiang, Jin Peng Zhou, Christian Szegedy, Łukasz Kuciński, Piotr Miłoś, Yuhuai Wu (University of Warsaw / IDEAS NCBR / Cambridge / Google, among others). First version March 2023, v3 March 2024 ([arXiv](https://arxiv.org/abs/2303.04488)).
- **Status:** Research paper. The dataset is public ([paper, Reproducibility statement](https://arxiv.org/abs/2303.04488)). A GitHub repo with dataset-generation code exists ([MagnusData](https://github.com/Simontwice/MagnusData)). Trained model weights and training/eval code appear not to be released (unverified). **Proof assistant: Isabelle, not Lean.**

## What it is

A neural premise selector for Isabelle/HOL, positioned as a replacement for Sledgehammer's relevance filter plus ATP pipeline. Given a proof state, it ranks the facts available in context and passes the top-k facts to Isabelle's built-in tactics (`smt`, `metis`, `auto`, ...). No external ATP or proof reconstruction is involved ([arXiv §2–3](https://arxiv.org/abs/2303.04488)).

## How it works

Two-stage contrastive retriever (bi-encoder SELECT to top-1024, then cross-encoder RERANK) over Isabelle's textual proof states and premises, with top-k premises handed to built-in Isabelle tactics ([arXiv §3](https://arxiv.org/abs/2303.04488)).

**Training data / labels (benchmark-relevant):** MAPL = (proof_state, premise) pairs from the Archive of Formal Proofs + Isabelle standard library: HPL (human proofs; 1.1M pairs, 570K states, 300K premises) plus SH (alternative Sledgehammer-found proofs; 3.3M pairs) = 4.4M pairs, 433K unique premises; the SH augmentation is explicitly motivated by reducing **false negatives** (a "negative" premise may appear in some alternative proof) ([arXiv §4, Table 1](https://arxiv.org/abs/2303.04488)). Candidate pool: ~30K–50K premises available per state out of 433K total ([arXiv §1](https://arxiv.org/abs/2303.04488)).

## Evaluation

- **Primary metric: proof success rate, not a retrieval metric** ([arXiv §5.1](https://arxiv.org/abs/2303.04488)). "Single-step" means trying tactics × top-k premises for k in powers of 2 up to 2^10, with a 2 s timeout each; the theorem counts as proved if any attempt closes the goal. "Multi-step" means using Magnushammer in place of Sledgehammer inside the Thor LM prover.
- **Compute-budget normalization:** C = |tactics| × |K| × T, with C ≈ 1000 for the main results and ≈ 800 for ablations. Sledgehammer is approximated as C = S × T with S = 10 ([arXiv §5.1, App. D](https://arxiv.org/abs/2303.04488)).
  - The main text says 36 tactics are used, but App. D lists 10 tactic names. The discrepancy is unresolved (unverified).
- **Benchmarks:**
  - PISA: the same 1000 AFP problems as Thor.
  - miniF2F: 244 valid and 244 test problems.
  - **Leakage handling:** "When training on data from the Archive of Formal Proofs, we remove the subset of it appearing in PISA." This is a theorem-level removal. No project- or time-level split is described ([arXiv §5.1 footnote](https://arxiv.org/abs/2303.04488)).
- **Headline numbers:**

  | Setting | Method | Proof rate |
  |---|---|---|
  | PISA single-step | BM25 | 30.6 |
  | PISA single-step | TF-IDF | 31.8 |
  | PISA single-step | OpenAI text-embedding-ada-002 | 36.1 |
  | PISA single-step | Sledgehammer | 38.3 |
  | PISA single-step | **Magnushammer** | **59.5** |
  | PISA multi-step | Thor | 57.0 |
  | PISA multi-step | **Thor + Magnushammer** | **71.0** |
  | miniF2F test, single-step | Sledgehammer + heuristics | 20.9 |
  | miniF2F test, single-step | **Magnushammer** | **34.0** |
  | miniF2F test, multi-step | Thor + Magnushammer | 37.3 |
  | miniF2F test, multi-step | DSP (Minerva 62B) | 39.3 |

  Sources: [arXiv Tables 2–3](https://arxiv.org/abs/2303.04488).
- **Ablations** ([arXiv §5.3–5.4, App. B/E](https://arxiv.org/abs/2303.04488)):
  - **SELECT alone (38M model) scores 54.2%, versus 56.3% with RERANK.** Reranking adds only about 2 points.
  - **Data efficiency:** trained on 0.1% of MAPL (about 4K examples, pretrained backbone), it scores 39.2%, which already beats Sledgehammer's 38.3%.
  - **Data source:** training on MAPL versus HPL gives 56.3% versus 54.0%.
  - **Model size:** a 920K-parameter model scores 40.7%; an 86.2M model scores 57.0%.
  - **Oracle:** the union of all single-step methods proves 65.5% of PISA, a practical upper bound.
- **Rank-sensitive proxy** ([arXiv App. E](https://arxiv.org/abs/2303.04488)): the "number of premises used" metric counts problems solved using at most k premises as k grows. A better ranker closes proofs with smaller k, so this is effectively a recall-at-depth curve measured through the prover.

## Relevance to lean-explore-bench

- **Downstream proof rate can separate retrievers that retrieval metrics might rank closely.** Generic dense embeddings (ada-002, 36.1%) sit near BM25/TF-IDF (30.6/31.8%), while a domain-trained retriever reaches 59.5%. The benchmark should report at least one *downstream* signal ("does the retrieved set let a fixed prover close the goal") alongside IR metrics.
- **Compute-budget normalization** is a reusable idea. When comparing search engines inside an agent loop, fix the number of calls, top-k and timeout, and plot success against budget rather than reporting a single point.
- **False negatives are real.** Human proofs record only one valid premise set. Magnushammer mitigates this with alternative (Sledgehammer) proofs. For us, "gold = premises in the human proof" undercounts relevant results. We should consider graded or multi-reference relevance, or verify candidate alternatives with a prover.
- **A cross-encoder reranker gave only a small gain here** (54.2 → 56.3). This is useful context when evaluating engines that advertise LLM reranking.
- **Leakage caveat:** PISA theorems are removed only at theorem level from AFP training data. Nearby lemmas from the same AFP entries remain in training. For our splits, theorem-level exclusion is insufficient.
- **Concrete reusable items:**
  - The "tactic × top-k sweep" oracle protocol, adapted to Lean as `exact?`/`simp only [...]`/`aesop` with the top-k premises (and akin to LeanHammer's Aesop setting).
  - The success-vs-k curve (App. E) as a rank-sensitive downstream metric.
  - The BM25 / TF-IDF / generic-embedding baseline trio.

## Open questions

- Would the SELECT-only bi-encoder transfer to Lean with the same margin? The authors planned a LeanDojo evaluation ([arXiv §7](https://arxiv.org/abs/2303.04488)). No published Lean result was found (unverified).
- Are model weights available anywhere? (unverified)

## Sources

- Mikuła et al., "Magnushammer: A Transformer-Based Approach to Premise Selection", ICLR 2024 — https://arxiv.org/abs/2303.04488 (full LaTeX read: §3 method, §4 dataset/Table 1, §5 Tables 2–3, App. B/D/E)
- Dataset — https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle
- Data-generation repo — https://github.com/Simontwice/MagnusData
