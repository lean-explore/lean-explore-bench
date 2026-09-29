# Mathlib `hint` tactic

- **Kind:** tool (in-editor tactic)
- **Links:** [`Mathlib/Tactic/Hint.lean`](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Hint.lean); registrations in [`Mathlib/Tactic/Common.lean`](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Common.lean#L149-L159)
- **Authors / org, date:** Added in Mathlib [`5c59815`](https://github.com/leanprover-community/mathlib4/commit/5c5981529b191ca31e9014b8866271990d94cf0c) (#8363, 2023-11-16).
- **Status:** In Mathlib at `ab4e75d` (2026-07-03).

## What it is

A meta-tactic that runs every tactic registered with `register_hint` and prints "Try these:" for each one that succeeds. It stops early if one closes the goal ([Hint.lean](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Hint.lean)). It searches over **tactics**, not declarations. One of the registered tactics is `exact?` (priority 600), alongside `simp_all?`, `grind`, `omega`, `aesop`, `linarith`, and others ([Common.lean](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Common.lean#L149-L159)).

## How it works

The query is the current goal. There is no user query.

## Evaluation

No published evaluation found.

## Relevance to lean-explore-bench

- **Harness:** replace a proof with `by hint` and run through Lean or lean-lsp-mcp `lean_multi_attempt`. It is local, pinned, and has no rate limit. Its cost is the sum of the registered tactics' costs.
- **Role:** not a search engine. It belongs only in a **proof-state / downstream track** as a "can existing automation already close this goal?" control. Goals that `hint` closes are arguably too easy to count as retrieval tasks, so use it to **filter** easy items from a goal-based query set.

## Open questions

- None specific.

## Sources

- Hint.lean: <https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Hint.lean>
- Registrations: <https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Common.lean#L149-L159>
- Introducing commit: <https://github.com/leanprover-community/mathlib4/commit/5c5981529b191ca31e9014b8866271990d94cf0c>
