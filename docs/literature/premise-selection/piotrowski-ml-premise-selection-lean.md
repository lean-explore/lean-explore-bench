# Machine-Learned Premise Selection for Lean (Piotrowski, Fernández Mir, Ayers)

- **Kind:** paper
- **Links:** paper [arXiv:2304.00994](https://arxiv.org/abs/2304.00994); code [github.com/BartoszPiotrowski/lean-premise-selection](https://github.com/BartoszPiotrowski/lean-premise-selection)
- **Authors / org, date:** Bartosz Piotrowski (University of Warsaw / CTU Prague), Ramon Fernández Mir (Edinburgh), Edward Ayers (CMU). Submitted March 2023, v2 June 2023. Supported by the Hoskinson Center ([arXiv](https://arxiv.org/abs/2304.00994)).
- **Status:** Research prototype written entirely in Lean 4. It was trained on `mathlib3port` (commit `f4e5dfe`), i.e. Mathlib as auto-ported from Lean 3 at the time ([arXiv §2](https://arxiv.org/abs/2304.00994)). Current maintenance status is unknown (unverified).

## What it is

The first ML premise selector for Lean 4, exposed to users as the interactive tactic `suggest_premises`. Given the *statement* of the theorem being proved, it returns a ranked list of likely-useful Mathlib lemmas ([arXiv abstract, §5](https://arxiv.org/abs/2304.00994)). Design goals: tight integration with Lean, easy installation, lightweight and fast. There is no external neural model or server.

## How it works

Online random forest / k-NN implemented in Lean 4 over bag-of-symbol features of the theorem statement, exposed as the `suggest_premises` tactic ([arXiv §2–3, §5](https://arxiv.org/abs/2304.00994)).

## Evaluation

- **Task:** given a theorem *statement* (not a proof state), rank Mathlib premises; one data point per theorem ([arXiv §2, §3](https://arxiv.org/abs/2304.00994)).
- **Labels = propositional constants in the proof term, under three filters** ([arXiv §2.2, Table 1](https://arxiv.org/abs/2304.00994)):

  | Filter | What it keeps | Premises | Examples | Premises per example |
  |---|---|---|---|---|
  | `all` | Everything except auto-generated `_`-prefixed names | 96,915 | 41,755 | 3.12 |
  | `source` | Only premises that appear in the proof's source text | 28,784 | 20,571 | 2.35 |
  | `math` | Only names on a Mathlib whitelist; core lemmas such as `Eq.refl` dropped | 67,462 | 40,187 | 2.09 |

  - An auxiliary per-tactic-state `intermediate` set (via LeanInk) has 91,292 examples, about 1.57 premises each.
- **Split: module-level, dependency-based** ([arXiv §4](https://arxiv.org/abs/2304.00994)). Test examples come from the **592 modules that are not dependencies of any other module** (leaves of the import DAG). Training uses the remaining 2,436 modules. This "simulates a realistic scenario in which a user ... develops a new mathlib module." It also guarantees that no training theorem depends on a test theorem.
- **Metrics** ([arXiv §4](https://arxiv.org/abs/2304.00994)): for a theorem with n ground-truth premises P and ranking R,
  - Cover = |P ∩ R[:n]| / n, i.e. R-precision / recall at n.
  - Cover₊ = |P ∩ R[:n+10]| / n, a tolerance of 10 extra slots because users browse about 10 suggestions.
- **Results, random forest vs k-NN** ([arXiv Table 2](https://arxiv.org/abs/2304.00994)), Cover (Cover₊):

  | Filter | Random forest, `n+b` (best) | k-NN, `n+b` |
  |---|---|---|
  | `all` | 0.57 (0.67) | 0.52 (0.66) |
  | `source` | 0.29 (0.36) | 0.25 (0.36) |
  | `math` | 0.26 (0.33) | 0.23 (0.34) |

  - `names + bigrams` was best for both models; trigrams overfit.
  - `all` scores look high because many examples have a single trivial premise such as `rfl`.
  - On the `intermediate` (per-state) data, the random forest scores Cover 0.09 / Cover₊ 0.24 and k-NN 0.08 / 0.21. Using that data for pretraining or augmentation gave no significant gain.
  - **Latency:** 0.28 s for the random forest vs 5.65 s for k-NN per ranking (`source`, `n+b`).
- **No end-to-end proving evaluation.** The paper reports ranking quality only.
- **Later external re-evaluation.** LeanHammer ([arXiv:2506.07477](https://arxiv.org/abs/2506.07477), App. C) retrained this random forest on all of Mathlib, *including* LeanHammer's test theorems, which is an acknowledged "unfair advantage". It still got only 22.1% recall@16 and a 19.1% hammer proof rate, versus 16.9% with no premises. About 300 of 500 retrievals errored through timeouts or >30 GB RAM, so those numbers cover only about 200 theorems.

## Successor infrastructure in Lean core

- The premise-selection idea now has a home in Lean core. LeanHammer's acknowledgments credit Kim Morrison with "implementing a premise selection API and the MePo selector in Lean core" ([arXiv:2506.07477](https://arxiv.org/abs/2506.07477)).
- The LeanPremise README says its cloud selector `Lean.LibrarySuggestions.Cloud.premiseSelector` "extends the `Lean.LibrarySuggestions` API from Lean 4 core". Users configure it with `set_library_suggestions ...` and invoke it via a `premises` tactic ([hanwenzhu/premise-selection README](https://github.com/hanwenzhu/premise-selection)).
- The exact core module names, tactic names and Lean version history were not checked against Lean source (unverified).

## Relevance to lean-explore-bench

- **The leaf-module split is a clean leakage-avoiding protocol for Mathlib.** Holding out modules that nothing imports ensures test theorems never appear as premises or dependencies in training. It is directly reusable for building our held-out query set. The cost is bias: leaf modules may skew toward application-heavy or late-stage files.
- **Label definition drives the numbers.** Moving from `all` to `source` to `math` halves scores. Our benchmark must state its relevance definition explicitly and preferably report several variants:
  - premises in the proof term (includes `simp`-implicit ones);
  - premises in the source text;
  - a Mathlib-only whitelist.
  This exact choice later explains why LeanHammer's recall for ReProver differs from LeanDojo's.
- **Cover₊ (recall at n+10)** is a user-centred metric: "is the answer in what a human would scan". Worth adopting alongside recall@k and MRR.
- **Statement-level vs state-level queries behave very differently** (Cover 0.29 vs 0.09). Benchmarks should keep the two query types separate.
- **Concrete reusable items:**
  - The leaf-module test split.
  - The three label filters (`all` / `source` / `math`).
  - The Cover / Cover₊ definitions.
  - The `H:`/`T:` bag-of-symbols features as a cheap non-neural baseline, alongside BM25.

## Open questions

- Is the random-forest tactic usable on current Mathlib, or is it effectively superseded by the Lean core `LibrarySuggestions` API and MePo? (unverified)

## Sources

- Piotrowski, Fernández Mir, Ayers, "Machine-Learned Premise Selection for Lean" — https://arxiv.org/abs/2304.00994 (full LaTeX read: §2 data/filters/Table 1, §3 models, §4 split/metrics/Table 2, §5 tactic)
- Code — https://github.com/BartoszPiotrowski/lean-premise-selection
- LeanHammer re-evaluation of the random forest (App. C) and acknowledgments — https://arxiv.org/abs/2506.07477
- LeanPremise README (Lean core `LibrarySuggestions` API) — https://github.com/hanwenzhu/premise-selection
