# LeanSearchClient (`#search`, `#leansearch`, `#loogle`, `#statesearch` in Lean)

- **Kind:** tool (in-editor client for remote search engines)
- **Links:** <https://github.com/leanprover-community/LeanSearchClient>
- **Authors / org, date:** `leanprover-community`. Examined at commit `c5d5b8f` (2026-02-12), taken from a local Mathlib project's `.lake/packages`.
- **Status:** A Mathlib dependency: it is in [`lake-manifest.json`](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/lake-manifest.json) and imported by [`Mathlib/Tactic/Common.lean`](https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Common.lean). Every `import Mathlib` user therefore has these commands.

## What it is

Lean syntax that sends a query to a remote engine and shows the hits as clickable "Try this" suggestions ([README](https://github.com/leanprover-community/LeanSearchClient)):

- `#leansearch "…"` queries LeanSearch with natural language.
- `#loogle <filters>` queries Loogle's JSON API.
- `#statesearch`, or `#search` with no string inside a tactic block, queries LeanStateSearch (premise-search.com) with the current goal.
- `#search "…"` dispatches according to the option `leansearchclient.backend`.

In tactic mode, only hits that form valid tactics are shown.

## How it works

It is a thin HTTP client. The endpoints can be overridden with the environment variables `LEANSEARCHCLIENT_LEANSEARCH_API_URL`, `LEANSEARCHCLIENT_LEANSTATESEARCH_API_URL`, and `LEANSEARCHCLIENT_LOOGLE_API_URL` (see `Syntax.lean` and [`LoogleSyntax.lean`](https://github.com/leanprover-community/LeanSearchClient/blob/main/LeanSearchClient/LoogleSyntax.lean)).

## Evaluation

None. It is a client, not an engine.

## Relevance to lean-explore-bench

- **Query modalities:** it shows the three modalities that Mathlib surfaces in the editor: natural language (LeanSearch), type/pattern (Loogle), and proof state (LeanStateSearch). A user-facing benchmark should have a track for each.
- **Harness:** call the backends' HTTP APIs directly rather than going through Lean. The env-var overrides let you point the real in-editor experience at pinned, self-hosted backends, for example in a user study.
- **Scoring caveat:** in-editor results are post-filtered (valid tactics only), so the engine "as users see it" is not the same as its raw API ranking.

## Open questions

- Whether backends have been added since Feb 2026 (not checked).

## Sources

- Repo/README: <https://github.com/leanprover-community/LeanSearchClient>
- Loogle syntax: <https://github.com/leanprover-community/LeanSearchClient/blob/main/LeanSearchClient/LoogleSyntax.lean>
- Mathlib manifest/import: <https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/lake-manifest.json>, <https://github.com/leanprover-community/mathlib4/blob/ab4e75d4a94f9bb4c0f47bded965aa5504e39422/Mathlib/Tactic/Common.lean>
