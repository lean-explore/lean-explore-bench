# Lean `#check` and editor name completion (baseline)

- **Kind:** tool (built into Lean 4 core and its language server)
- **Links:** <https://github.com/leanprover/lean4>; fuzzy matcher [`src/Lean/Data/FuzzyMatching.lean`](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Data/FuzzyMatching.lean); completion [`src/Lean/Server/Completion/`](https://github.com/leanprover/lean4/tree/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Server/Completion)
- **Authors / org, date:** Lean FRO and Lean developers. The fuzzy matcher is by Lars König (2022), per its file header.
- **Status:** Always available in any Lean 4 editor and over LSP.

## What it is

The zero-infrastructure baseline. `#check foo` is an **exact lookup and verifier**: it succeeds only if the name resolves in the current environment. **LSP completion** ranks in-scope names against a typed prefix or subsequence. The matcher is "based on the algorithm used in LLVM ... itself based on VS code's client side filtering algorithm" ([FuzzyMatching.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Data/FuzzyMatching.lean)). Dot-completion (`h.`) lists names in the namespace of the term's head type, which gives a weak type-directed search. Only **imported** declarations are visible.

## How it works

The query language is an identifier prefix or subsequence. There are no types, patterns, or natural language.

## Evaluation

No published retrieval evaluation found.

## Relevance to lean-explore-bench

- **Harness:** run it through any LSP client. lean-lsp-mcp exposes `lean_completions`, `lean_hover_info`, and `lean_run_code` ([server.py](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py#L582)). You can also run `lake env lean` on a generated file containing `#check` lines. Everything is local and pinned to the project's Mathlib revision, with no rate limits. Completion depends on imports and `open`s, so fix the context (for example `import Mathlib` and no `open`s).
- **Role 1: floor baseline for name-shaped queries.** You can simulate it offline by fuzzy-matching the query against all names.
- **Role 2: oracle.** `#check` checks that a returned name exists at the benchmark's pinned Mathlib revision. This is needed to score engines that index a different revision.
- **Role 3: agentic baseline.** An LLM guesses names and verifies them with `#check`, with no search engine. It is a realistic competitor that a benchmark should include.

## Open questions

- How completion ranking weighs namespace proximity against string score (not examined).

## Sources

- FuzzyMatching.lean: <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Data/FuzzyMatching.lean>
- Completion code: <https://github.com/leanprover/lean4/tree/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Server/Completion>
- lean-lsp-mcp tools: <https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py>
