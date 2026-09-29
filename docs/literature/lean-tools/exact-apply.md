# `exact?` / `apply?` (library search tactics, formerly `library_search`)

- **Kind:** tool (in-editor tactic, Lean 4 core)
- **Links:** [`src/Lean/Meta/Tactic/LibrarySearch.lean`](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/LibrarySearch.lean), [`src/Lean/Elab/Tactic/LibrarySearch.lean`](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Elab/Tactic/LibrarySearch.lean)
- **Authors / org, date:** Gabriel Ebner, Joe Hendrix, Kim Morrison (per file headers). Moved from Std into Lean core in [`710c3ae`](https://github.com/leanprover/lean4/commit/710c3ae9e8e28616f5819d46b3c6e1d8f23d8896) "chore: upstream exact? and apply? from Std (#3447)" (2024-02-23).
- **History:**
  - First Mathlib 4 `librarySearch` by Gabriel Ebner (mathlib4#65, 2021).
  - Renamed from `library_search` to `apply?`, and `exact?` added, in [mathlib4#4885](https://github.com/leanprover-community/mathlib4/pull/4885) (merged 2023-06-14).
  - Moved into core in [lean4#3447](https://github.com/leanprover/lean4/pull/3447), shipped in v4.7.0.
  - Later changes, per the [release notes](https://lean-lang.org/doc/reference/latest/releases/): LazyDiscrTree performance fixes in v4.8.0; `+grind`/`+try?`, the star-lemma fallback, and `+all` in v4.27.0 (#11469, #11494, #11556); deprecated lemmas filtered in v4.28.0 (#11918); a hang near the top of long files fixed in v4.33.0 (#13712).
- **Status:** In every Lean 4 install (checked at `f459c14`, 2026-05-14).

## What it is

Goal-directed library search. "Searches environment for definitions or theorems that can solve the goal using `exact` with conditions resolved by `solve_by_elim`" ([Init/Tactics.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Init/Tactics.lean)).

- `exact?` must close the goal. `apply?` also reports lemmas that leave subgoals.
- A term form, `exact?%`, also exists.
- The output is a verified `Try this: exact foo …` suggestion.

## How it works

- **Query:** the current goal only. There is no user text.
- **Candidates:** the goal's conclusion is looked up in a lazily built discrimination tree over every imported declaration, including `↔` `mp`/`mpr` variants. Very generic keys (`*`, `Eq * * *`) are dropped "because they match too much" but kept as a fallback. Each candidate is tried with `apply`, and side goals are closed by `solve_by_elim`, depth 6 ([LibrarySearch.lean](https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/LibrarySearch.lean)).
- **Options:** `using h` requires a hypothesis to be used. `+grind` and `+try?` add fallback dischargers. `+all` collects every solution. `-star` disables the fallback.
- **Strengths against semantic search:** it is exact, since a returned lemma provably closes the goal, and it needs no query writing.
- **Weaknesses:**
  - It only finds lemmas that unify with the goal up to reducible defeq. It cannot find a lemma that needs rewriting first, or one that is not yet imported.
  - It can be slow and hit heartbeat limits on large imports. Results carry no relevance score.

## Evaluation

No published quantitative evaluation of `exact?`/`apply?`/`library_search` as a retriever was found. Papers mention it only qualitatively:

- Lean Copilot: "Lean's `apply?` tactic tries to find premises that unify symbolically with the current goal" ([arXiv 2404.12534](https://arxiv.org/abs/2404.12534)). Its numeric baseline is aesop, not `apply?`.
- Piotrowski et al.: "suggest or library_search propose lemmas that strictly match the goal at the current proof state … They may also suggest too many trivial lemmas if the goal is simple" ([arXiv 2304.00994](https://arxiv.org/abs/2304.00994)).
- Lean Finder: "#find, library_search, and Loogle depend on exact names or goal states and often fail when naming conventions drift" ([arXiv 2510.15940](https://arxiv.org/abs/2510.15940)).
- The major premise-selection evaluations use different symbolic baselines: LeanDojo uses `tidy` ([2306.15626](https://arxiv.org/abs/2306.15626)), and LeanHammer uses MePo ([2506.07477](https://arxiv.org/abs/2506.07477)).

**This is a gap a benchmark can fill.** Other papers such as LLMSTEP and Aesop were not checked (unverified).

## Relevance to lean-explore-bench

- **Harness:**
  - Put `by exact?` (or `by apply?`) at a goal and run `lake env lean`, lean-lsp-mcp `lean_multi_attempt`, or a REPL such as Pantograph/LeanInteract.
  - Parse `Try this:` to get the lemma name.
  - It is offline and pinned to the project's Mathlib, with no rate limit. Set `maxHeartbeats` and a wall-clock timeout in the harness.
- **Role:** the **strongest symbolic baseline for a proof-state track**. For a goal extracted from a Mathlib proof step, "did `exact?` find the gold lemma (or any closing lemma)?" is binary, success@1-style, and fully reproducible. Semantic engines queried with the same goal text should be compared against it.
- **Data caveat:** goals where the gold lemma is a single `exact foo` are exactly where `exact?` shines. Stratify the query set by the proof step type (`exact`, `rw`, `simp [...]`, `apply`) so it is not biased toward that case.

## Open questions

- Is there a published success rate for `exact?` on Mathlib goals? None was found. A benchmark could measure it on held-out proof steps.

## Sources

- Library search core: <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Lean/Meta/Tactic/LibrarySearch.lean>
- Tactic syntax and docstrings: <https://github.com/leanprover/lean4/blob/f459c1436e4a3f84b907c8d1b4eeef0c50ac4948/src/Init/Tactics.lean>
- Upstreaming commit: <https://github.com/leanprover/lean4/commit/710c3ae9e8e28616f5819d46b3c6e1d8f23d8896>
- Rename PR: <https://github.com/leanprover-community/mathlib4/pull/4885>; Lean release notes: <https://lean-lang.org/doc/reference/latest/releases/>
- Papers that mention it qualitatively: <https://arxiv.org/abs/2404.12534>, <https://arxiv.org/abs/2304.00994>, <https://arxiv.org/abs/2510.15940>; other baselines used: <https://arxiv.org/abs/2306.15626>, <https://arxiv.org/abs/2506.07477>
