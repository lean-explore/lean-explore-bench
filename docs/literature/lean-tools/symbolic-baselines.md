# Small symbolic baselines: `#check` and completion, doc-gen4 search, `#find`, `rw?`, `hint`

- **Kind:** tool cluster (in-editor commands, tactics and the docs search box)
- **Links:** see each section
- **Status:** all live in Lean 4 core, Mathlib or doc-gen4 as of the commits cited (checked 2026-09-28)

None of these tools has a published retrieval evaluation. Each is a cheap, local, version-pinned baseline for one query type. Loogle, `exact?`/`apply?`, LeanStateSearch and Lean core's library suggestions have their own notes because they carry more evaluation-relevant detail.

## `#check` and editor name completion (floor baseline for name queries)

- `#check foo` is an exact lookup and verifier: it succeeds only if the name resolves. LSP completion ranks in-scope names against a typed prefix or subsequence using a fuzzy matcher "based on the algorithm used in LLVM ... itself based on VS code's client side filtering algorithm" ([FuzzyMatching.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Data/FuzzyMatching.lean)). Only imported declarations are visible, and dot-completion gives a weak type-directed search.
- **Harness:** any LSP client, lean-lsp-mcp (`lean_completions`, `lean_hover_info`, `lean_run_code`), or `lake env lean` on a file of `#check` lines. Fix imports and `open`s.
- **Roles:** (1) floor baseline for name-shaped queries, simulable offline by fuzzy-matching against all names; (2) oracle that a returned name exists at the pinned Mathlib revision, needed when engines index other revisions; (3) an agentic baseline where an LLM guesses names and verifies them with `#check`.

## doc-gen4 search (the Mathlib docs search box and `/find`)

- Matches **declaration names only** by subsequence ("fuzzy") match, ranked by an error score the source calls "quite hacky"; autocomplete shows at most 30 hits; `/find?pattern=Nat.add#doc` resolves an exact name ([declaration-data.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/declaration-data.js), [search.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/search.js), [find.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/find/find.js), commit `d555f83`).
- **Harness:** no server API; port the ~30-line scorer and run it over the doc-gen4 declaration JSON of a pinned Mathlib build. Deterministic and free.
- **Role:** the lexical name baseline every Mathlib user already has; expect good results on identifier queries and near zero on natural language. `/find?pattern=<name>#doc` is a convenient canonical link format for gold declarations.

## Mathlib `#find` (offline type-pattern search)

- "Finds definitions & lemmas using pattern matching on the type", e.g. `#find _ + _ = _ + _`; indexes lemmas by the head symbol of their conclusion and checks candidates by defeq matching; also a `find` tactic for `apply`able lemmas ([Find.lean](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Find.lean), Ullrich, 2021).
- **Role:** an offline stand-in for Loogle at an exact Mathlib revision. It fails on patterns whose conclusion head is a variable and returns unranked results, so rank metrics need a tie-break rule.

## `rw?` (ranked rewrite search)

- Indexes every imported `=`/`↔` lemma in a discrimination tree by LHS and RHS, matches subterms of the goal, excludes injectivity and deprecated lemmas, and ranks by specificity (forward rewrites weighted 2, backward 1) ([Rewrites.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/Rewrites.lean)). In core since v4.8.0; Mathlib's multi-step `rw_search` was removed in September 2025 as unmaintained ([#29196](https://github.com/leanprover-community/mathlib4/commit/2b95c333180a76ec65acc618e20c0de59ff86636)).
- **Role:** unlike `exact?` it returns a ranked list, so it is the natural symbolic baseline for `rw`-step premise retrieval (gold = the lemma in a Mathlib `rw [foo]` step), scored with Recall@k and MRR. It tends to return many valid but irrelevant rewrites.

## Mathlib `hint` (not a retriever; a filter)

- Runs every tactic registered with `register_hint` (including `exact?`, `simp_all?`, `grind`, `omega`, `aesop`, `linarith`) and prints those that succeed ([Hint.lean](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Hint.lean)).
- **Role:** in a proof-state track, use it to **filter out** goals existing automation already closes, since those are too easy to count as retrieval tasks.

## Harness notes common to all five

All run offline, pinned to the project's Mathlib, with no rate limits. Set `maxHeartbeats` and a wall-clock timeout. Report results per query type so that name tools are not scored meaninglessly on natural-language queries.
