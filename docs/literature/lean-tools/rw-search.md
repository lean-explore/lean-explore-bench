# `rw?` (rewrite search tactic) and the removed `rw_search`

- **Kind:** tool (in-editor tactic, Lean 4 core)
- **Links:** [`src/Lean/Meta/Tactic/Rewrites.lean`](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/Rewrites.lean), [`src/Lean/Elab/Tactic/Rewrites.lean`](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Elab/Tactic/Rewrites.lean)
- **Authors / org, date:** Kim Morrison (2023, per file header). Moved into Lean core in [`6c8976a`](https://github.com/leanprover/lean4/commit/6c8976abbea74e6abb059de6267a0804cf14f614) "feat: upstream rw? tactic (#3719)" (2024-03-23).
- **History:** Began as Mathlib `rewrites` ([mathlib4#3119](https://github.com/leanprover-community/mathlib4/pull/3119), 2023-05-10). Renamed to `rw?` in [mathlib4#4885](https://github.com/leanprover-community/mathlib4/pull/4885). Shipped in core in Lean v4.8.0 ([release notes](https://lean-lang.org/doc/reference/latest/releases/)).
- **Status:** In core. Mathlib's multi-step `rw_search` was removed in [#29196](https://github.com/leanprover-community/mathlib4/commit/2b95c333180a76ec65acc618e20c0de59ff86636) (2025-09-01): "removed from Mathlib, as it was unmaintained, broken on v4.23.0, and rarely used" ([RewriteSearch.lean stub](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/RewriteSearch.lean)).

## What it is

"`rw?` tries to find a lemma which can rewrite the goal ... Suggestions are printed as `rw [h]` or `rw [← h]`. You can use `rw? [-my_lemma]` to prevent `rw?` using the named lemmas" ([Init/Tactics.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Init/Tactics.lean)).

## How it works

- **Query:** the goal, or a hypothesis via `at h`.
- **Candidates:** every imported `=`/`↔` lemma is indexed in a discrimination tree by its LHS (forward) and RHS (backward). The tree is matched against subterms of the goal. Local hypotheses are also tried.
- **Exclusions:** injectivity lemmas, deprecated lemmas, and metaprogramming namespaces are left out.
- **Ranking:** results are ranked by specificity, with forward rewrites weighted 2 and backward 1. Results that are then closable by `rfl` are flagged ([Rewrites.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/Rewrites.lean)).
- **Weakness:** it tends to return many valid but irrelevant rewrites. Relevance to the user's intent is not modeled.

## Evaluation

No published evaluation found.

## Relevance to lean-explore-bench

- **Harness:** the same approach as `exact?`: insert `rw?` at a goal, run Lean locally, and parse the `Try this: rw [...]` list. It is offline and pinned, with no rate limit.
- **Role:** unlike `exact?`, it returns a **ranked list**. It is therefore the natural symbolic baseline for **`rw`-step premise retrieval** (the gold is the lemma used in a Mathlib `rw [foo]` step), scored with Recall@k and MRR.

## Open questions

- Its default cap on the number of results was not checked.

## Sources

- Rewrites core: <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/Rewrites.lean>
- Syntax and docstring: <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Init/Tactics.lean>
- Upstreaming commit: <https://github.com/leanprover/lean4/commit/6c8976abbea74e6abb059de6267a0804cf14f614>
- `rw_search` removal: <https://github.com/leanprover-community/mathlib4/commit/2b95c333180a76ec65acc618e20c0de59ff86636>
- History: <https://github.com/leanprover-community/mathlib4/pull/3119>, <https://github.com/leanprover-community/mathlib4/pull/4885>, <https://lean-lang.org/doc/reference/latest/releases/>
