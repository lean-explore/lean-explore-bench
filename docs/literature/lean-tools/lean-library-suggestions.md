# Lean core library suggestions (`suggestions`, `set_library_suggestions`, `grind +suggestions`)

- **Kind:** tool (premise-selection API in Lean 4 core)
- **Links:** [`src/Lean/LibrarySuggestions/`](https://github.com/leanprover/lean4/tree/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions)
- **Authors / org, date:** Kim Morrison / Lean FRO. From the lean4 git log: API [#7061](https://github.com/leanprover/lean4/pull/7061) (2025-02-14); MePo selector [#7844](https://github.com/leanprover/lean4/pull/7844) (2025-09-23); Sine Qua Non selector (2025-10-30); rename from "premise selection" to "library suggestions" [#11029](https://github.com/leanprover/lean4/pull/11029) (2025-10-31).
- **Releases:** per the [release notes](https://lean-lang.org/doc/reference/latest/releases/), as summarized by a sub-agent:
  - v4.18.0: API only (#7061)
  - v4.25.0: MePo (#7844)
  - v4.26.0: SInE (#11002), `grind +suggestions` (#10920/#11029), `simp? +suggestions` (#11032), and a default of SInE plus current-file theorems (#11168)
  - v4.27.0: `solve_by_elim +suggestions` (#11468)
  - v4.33.0: opt-in automatic `try?` (#13830)
  - v4.35.0-rc: indexes computed on demand (#15159)

  There is no core `hammer`. LeanHammer is external ([repo](https://github.com/JOSHCLUNE/LeanHammer)).
- **Status:** In Lean core at master `f459c14` (2026-05-14).

## What it is

A pluggable, goal-conditioned premise-selection interface: "used to suggest relevant theorems from the library for the current goal. In the literature this is usually known as 'premise selection'" ([Basic.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions/Basic.lean)).

- `set_library_suggestions <selector>` registers an engine. It can be symbolic or a downstream neural engine.
- The engine is consumed by the `suggestions` tactic, `grind +suggestions`, `simp? +suggestions`, and `try?`.
- The default engine combines **Sine Qua Non** with theorems from the current file ([Default.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions/Default.lean)). **MePo** is also built in. Both are classic symbol-overlap ATP relevance filters.

## How it works

The query is the current goal. Results are ranked by symbol relevance.

## Evaluation

- The source says both built-in selectors still "need to be tuned and evaluated for Lean" ([MePo.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions/MePo.lean), [SineQuaNon.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions/SineQuaNon.lean)).
- The only numbers found are for MePo, in the LeanHammer paper. It uses "a recent adaptation of MePo from Isabelle to Lean (implemented by Kim Morrison)", tuned on its own eval ([arXiv 2506.07477](https://arxiv.org/abs/2506.07477)). Whether that is identical to the core `MePo.lean` is unverified.
  - On Mathlib-test, MePo gets R@16 38.4 and R@32 42.1, with a cumulative hammer proof rate of 27.5%.
  - LeanPremise gets 63.5 / 72.7 / 33.3%, and the union LeanPremise ∪ MePo reaches 37.6%. Symbolic and neural selectors are complementary.
- No evaluation of SInE in Lean was found. A benchmark could fill that gap directly.

## Relevance to lean-explore-bench

- **Harness:** run it locally in Lean. Insert `suggestions` at a goal and parse the output, or call the `Selector` from a Lean metaprogram over many goals. It is deterministic, offline, pinned to the Lean/Mathlib version, and has no rate limit.
- **Roles:**
  - MePo and SInE are **free symbolic baselines** for a proof-state track.
  - The `Selector` type is a **standard adapter**: any engine wrapped as a selector can be scored by what it retrieves and by what `grind +suggestions` then proves.
- **Where it is headed:** this is the official in-editor proof-state retrieval interface, so results on it are likely to matter to Lean users.

## Open questions

- Whether Mathlib installs a non-default selector (none found by grep at `ab4e75d`; unverified).

## Sources

- LibrarySuggestions: <https://github.com/leanprover/lean4/tree/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/LibrarySuggestions>
- grind config (`suggestions` option): <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Init/Grind/Config.lean>
- LeanHammer paper (MePo numbers): <https://arxiv.org/abs/2506.07477>
- PRs: <https://github.com/leanprover/lean4/pull/7061>, <https://github.com/leanprover/lean4/pull/7844>, <https://github.com/leanprover/lean4/pull/11029>
