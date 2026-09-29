# Premise Selection for a Lean Hammer (LeanPremise + LeanHammer)

- **Kind:** paper
- **Links:**
  - Paper: [arXiv:2506.07477](https://arxiv.org/abs/2506.07477) (v2 Feb 2026; ICLR-format camera-ready)
  - LeanPremise: [github.com/hanwenzhu/premise-selection](https://github.com/hanwenzhu/premise-selection)
  - LeanHammer: [github.com/JOSHCLUNE/LeanHammer](https://github.com/JOSHCLUNE/LeanHammer)
  - Data extraction: [cmu-l3/ntp-toolkit (hammer branch)](https://github.com/cmu-l3/ntp-toolkit/tree/hammer)
  - Training: [hanwenzhu/LeanHammer-training](https://github.com/hanwenzhu/LeanHammer-training)
  - Server: [hanwenzhu/lean-premise-server](https://github.com/hanwenzhu/lean-premise-server)
- **Authors / org, date:** Thomas Zhu, Joshua Clune, Jeremy Avigad, Albert Q. Jiang, Sean Welleck (CMU; Mistral AI). First version June 2025, v2 Feb 2026 ([arXiv](https://arxiv.org/abs/2506.07477)).
- **Status:** Open source. The authors state that data, trained models and baselines are released ([arXiv, Reproducibility statement](https://arxiv.org/abs/2506.07477)). A hosted backend exists at `http://leanpremise.net`, the default for `Lean.LibrarySuggestions.Cloud.premiseSelector` ([README](https://github.com/hanwenzhu/premise-selection)).

## What it is

- **LeanPremise** is a contrastively trained bi-encoder premise selector for Lean 4, callable as a Lean tactic. It can embed *new, user-local premises* at runtime.
- **LeanHammer** combines it with Aesop, Lean-auto (dependent type theory to higher-order logic translation), Zipperposition and Duper (proof reconstruction). The paper calls this the first end-to-end, domain-general hammer for Lean ([arXiv abstract, §3.1](https://arxiv.org/abs/2506.07477)).

## How it works

Contrastively fine-tuned sentence-transformer bi-encoder (23M–82M params; no reranker) doing cosine top-k over the *accessible* premises at the query position, served via a FAISS server callable from Lean, with new user-local premises embedded on the fly ([arXiv §3.3](https://arxiv.org/abs/2506.07477)).

**Candidate set and labels (benchmark-relevant):** premises are serialized as `docstring? kind name arguments* : type` with notation off and fully-qualified names; a 479-lemma blacklist of trivial logic lemmas (e.g. `and_true`) plus metaprogramming decls is removed from candidates ([arXiv §3.2.1](https://arxiv.org/abs/2506.07477)). Ground truth ("hammer-aware") pairs each state with the premises of the *whole remaining proof* — term-style and tactic-style proofs, implicit proof-term premises (e.g. from `simp`) plus explicit `rw`/`simp` args — rather than the next tactic only ([arXiv §3.2.2](https://arxiv.org/abs/2506.07477)).

## Evaluation

- **Data and split** ([arXiv §4.1](https://arxiv.org/abs/2506.07477)):
  - Mathlib, Lean v4.16.0: 469,965 states from 206,005 theorems.
  - 265,348 filtered premises (Mathlib + Batteries + core), with 12.45 relevant premises per state on average and 5,817,740 training pairs.
  - **500 validation and 500 test theorems are held out at random** (theorem-level, not module-level).
- **Out-of-distribution evaluation:** the non-Mathlib splits of **miniCTX-v2-test** (Carleson, ConNF, FLT, Foundation, HepLean, Seymour). These are libraries unseen in training, and their local premises must be embedded dynamically ([arXiv §4.1, Table 4](https://arxiv.org/abs/2506.07477)).
- **Metrics** ([arXiv §4.2](https://arxiv.org/abs/2506.07477)):
  - Retrieval: **recall@k**, the mean fraction of ground-truth premises in the top k, for k = 16 and 32. Recall is favored over precision "because a hammer can tolerate irrelevant premises much more than missing important ones".
  - End-to-end: **proof rate** under 5 pipeline settings. The per-theorem budget is 300 s wall clock, 10 s per Zipperposition call, and 200k heartbeats. k is tuned on validation: 16 premises to Lean-auto and 32 to Aesop.
- **Ground-truth-premise oracle:** feeding the human-proof premises gives an upper bound, **43.0% (cumulative)** on Mathlib-test. This separates retrieval error from prover error.
- **Mathlib-test headline** ([arXiv Table 3](https://arxiv.org/abs/2506.07477)):

  | Selector | R@16 | R@32 | Full proof rate | Cumulative proof rate |
  |---|---|---|---|---|
  | None | 0 | 0 | 16.9 | 16.9 |
  | Random forest (Piotrowski et al.; upper bound, trained on test) | 22.1 | 22.3 | 19.1 | 19.1 |
  | MePo (Lean port) | 38.4 | 42.1 | 26.3 | 27.5 |
  | ReProver (218M, retrained on these splits) | 35.1 | 38.7 | 12.0 | 22.3 |
  | **LeanPremise 82M** | **63.5** | **72.7** | **30.1** | **33.3** |
  | LeanPremise ∪ MePo | — | — | 35.9 | 37.6 |
  | Ground truth | — | — | 41.0 | 43.0 |

  - The headline claim is "21% more goals than existing premise selectors": 33.3 vs 27.5 (MePo), cumulative.
  - Relative to ReProver: +150% in the full setting and +50% cumulative. Recall@32 is 73% higher than MePo's.
- **The ReProver comparison hinges on label definitions** ([arXiv §4.3, App. C](https://arxiv.org/abs/2506.07477)). ReProver's ground truth is "premises used in the next tactic"; LeanPremise's is "premises used in the whole proof". The authors checked that under ReProver's own definition their retrained ReProver gets about 38% recall@10, matching the LeanDojo paper.
- **Neural and symbolic retrievers are complementary.** The union with MePo beats either alone.
- **Ablations on validation** ([arXiv Table 5](https://arxiv.org/abs/2506.07477)):

  | Variant | R@16 | Full proof rate |
  |---|---|---|
  | LeanPremise | 61.1 | 34.6 |
  | Naive extraction (default pretty-printing, no blacklist, no `simp`/`rw` premises) | 57.5 | 33.1 |
  | No sampled negatives | 51.8 | 33.0 |
  | No loss mask | 59.1 | 34.4 |

  - **Recall moves much more than proof rate.** The authors note that "proof rate has higher variance than recall".
- **Out-of-distribution generalization** ([arXiv Tables 4, 7](https://arxiv.org/abs/2506.07477)). Average full proof rate over the miniCTX-v2 splits: 14.9 with no premises, **20.7** with LeanPremise, 26.1 with ground truth.
  - The share of the ground-truth ceiling captured is 73.5% on Mathlib and 79.4% on miniCTX, so no drop out of distribution.
  - Carleson scored 0.0 because of a pipeline error; treat it as a lower bound.
- **Where it helps** ([arXiv App. D.4](https://arxiv.org/abs/2506.07477)): solved theorems almost all have 1–2-line human proofs and ≤8 ground-truth premises.
- **Error breakdown, Lean-auto setting, ground-truth premises** ([arXiv App. D.5](https://arxiv.org/abs/2506.07477)):
  - 21.7% could not be translated;
  - 43.6% were not proven by Zipperposition;
  - 1.6% failed reconstruction.

## Relevance to lean-explore-bench

- **The strongest template for "retrieval metric + downstream metric + oracle".**
  - Report recall@k *and* a fixed-consumer success rate.
  - Include a "no retrieval" floor and a "ground-truth premises" ceiling.
  - Normalize as the fraction of the ceiling achieved.
  - We can reuse this almost directly, with LeanHammer (or `aesop`/`exact?` with the given premises) as the fixed consumer.
- **The label definition must be explicit.** "Next-tactic premises" (LeanDojo) and "whole-proof premises including implicit `simp` lemmas" (LeanPremise) give incomparable recall numbers for the same model. Our benchmark should fix one definition, publish the extraction code, and ideally report both.
- **Leakage caveats in this paper to avoid:**
  1. The test split is **random at theorem level**, so neighbouring lemmas from the same file and module are in training. A module- or project-level split (Piotrowski leaf modules, miniCTX) is stricter; miniCTX-v2 provides one.
  2. **MePo's p/c hyperparameters were tuned "on our test data"** (App. C). That is a baseline-favoring leak, but still a test-set leak.
  3. The random-forest baseline was trained on test theorems.
- **Accessible-premise filtering.** Candidates must be restricted to what is importable or declared earlier at the query position. A search engine indexing all of Mathlib can return premises that are not yet available or are defined later. We need an "accessible set" filter, or at least to report both filtered and unfiltered metrics.
- **Dynamic, out-of-index premises.** LeanPremise embeds user-local declarations at query time. Most web search engines index a fixed Mathlib snapshot. A benchmark slice on non-Mathlib projects (miniCTX-style) tests whether an engine can see local context at all.
- **Complementarity.** The neural ∪ symbolic union beat both. A benchmark should report per-query overlap and oracle unions across engines, not just a leaderboard.
- **Concrete reusable items:**
  - recall@16/@32 under the whole-proof label.
  - The no-premise and ground-truth-premise bracket.
  - The miniCTX-v2 non-Mathlib splits as an out-of-distribution slice.
  - The normalized signature format for indexing (docstring, kind, name, args : type, no notation, fully qualified).
  - The 479-lemma blacklist idea, to avoid rewarding trivial premises.
  - The released ntp-toolkit extraction code for gold labels.

## Open questions

- Recall is averaged per theorem over *all* whole-proof premises (12.45 on average). Does per-premise weighting or "all-premises-found" (success@k) correlate better with hammer success?
- The v2 paper still evaluates at Lean v4.16.0. Whether the hosted `leanpremise.net` index tracks current Mathlib is unknown (unverified).

## Sources

- Zhu, Clune, Avigad, Jiang, Welleck, "Premise Selection for a Lean Hammer" — https://arxiv.org/abs/2506.07477 (full LaTeX read: §3 methods, §4 Tables 3–5, App. C baseline settings, App. D.2–D.5)
- LeanPremise README — https://github.com/hanwenzhu/premise-selection
- LeanHammer — https://github.com/JOSHCLUNE/LeanHammer
- Data extraction — https://github.com/cmu-l3/ntp-toolkit/tree/hammer
