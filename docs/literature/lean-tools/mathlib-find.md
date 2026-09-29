# Mathlib `#find` command and `find` tactic

- **Kind:** tool (in-editor command/tactic)
- **Links:** [`Mathlib/Tactic/Find.lean`](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Find.lean)
- **Authors / org, date:** Sebastian Ullrich. Added in [`a199b46`](https://github.com/leanprover-community/mathlib4/commit/a199b46a550483efe0185916ebe0ccc3bb7a9232) (#51, 2021-09-29). Docstrings revised in [#35077](https://github.com/leanprover-community/mathlib4/commit/b5be74f625bd01be15a170e2981c657ed96731b5) (2026-02-13).
- **Status:** Still in Mathlib at `ab4e75d` (2026-07-03).

## What it is

Local type-pattern search over the imported environment:

> The `#find` command finds definitions & lemmas using pattern matching on the type. For instance: `#find _ + _ = _ + _`, `#find ?n + _ = _ + ?n`, `#find (_ : Nat) + _ = _ + _`, `#find Nat → Nat`. Inside tactic proofs, there is a `#find` tactic with the same syntax, or the `find` tactic which looks for lemmas which are `apply`able against the current goal. ([Find.lean](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Find.lean))

## How it works

It indexes lemmas by the head symbol of their conclusion, then checks candidates by definitional-equality matching against the pattern. It has no name-substring or constant-mention filters. Loogle is the hosted, richer successor (see `loogle.md`).

## Evaluation

No published evaluation found.

## Relevance to lean-explore-bench

- **Harness:** write `import Mathlib` plus `#find <pattern>` lines into a file and run `lake env lean` on it, or use lean-lsp-mcp `lean_run_code`. Parse the messages. It is offline, pinned to the project's Mathlib revision, and has no rate limit. Expect an expensive cache build on first use (unverified; no timings found).
- **Role:** an offline **type-pattern baseline** when you need a Loogle-like tool at an exact Mathlib revision. It fails on patterns whose conclusion head is a variable, and it returns matches unranked, so rank-based metrics need a tie-break rule.

## Open questions

- Runtime on full Mathlib and the ordering of results (not measured).

## Sources

- Find.lean at `ab4e75d`: <https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Find.lean>
- Introducing commit: <https://github.com/leanprover-community/mathlib4/commit/a199b46a550483efe0185916ebe0ccc3bb7a9232>
- Docstring update: <https://github.com/leanprover-community/mathlib4/commit/b5be74f625bd01be15a170e2981c657ed96731b5>
