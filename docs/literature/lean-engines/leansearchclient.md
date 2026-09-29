# LeanSearchClient (in-editor search commands for Mathlib)

- **Kind:** tool (client, not an engine)
- **Links:** https://github.com/leanprover-community/LeanSearchClient
- **Authors / org, date:** leanprover-community, originally by Siddhartha Gadgil. Active in 2024–2026 (last push 2026-09-28, per the GitHub API).
- **Status:** Maintained, Apache-2.0, and a Mathlib dependency ([repo](https://github.com/leanprover-community/LeanSearchClient)).

## What it is

LeanSearchClient provides Lean syntax that sends queries to external engines and shows clickable `TryThis` suggestions: `#search`, `#leansearch`, `#statesearch` and `#loogle`. They work as commands, terms and tactics, and a bare `#search` inside a tactic block uses the current goal ([README](https://github.com/leanprover-community/LeanSearchClient)).

## How it works (brief)

- **Backends:**
  - leansearch.net for natural language
  - premise-search.com (LeanStateSearch) for proof states
  - loogle.lean-lang.org for formula and pattern queries
- **Backend selection:** The `leansearchclient.backend` option chooses the backend for `#search` ([README](https://github.com/leanprover-community/LeanSearchClient)).
- **Query triggering:** A natural-language query is sent only when the sentence ends with "." or "?".
- **Tactic filtering:** In tactic mode, only valid tactics are shown.
- **Moogle:** Support was removed as "defunct" on 2025-10-21 ([PR #24](https://github.com/leanprover-community/LeanSearchClient/pull/24)).

## Evaluation

None. It is a client.

## Relevance to lean-explore-bench

- It fixes which engines Mathlib users reach by default: LeanSearch for natural language, LeanStateSearch for goals, Loogle for patterns. The benchmark's headline engines should include these defaults.
- The tactic-mode `#search` (goal to premises) is a query style the benchmark could simulate. It overlaps with the premise-selection review.
- It is not suited to driving a harness (Lean-side, interactive), so a harness should call the backend HTTP APIs directly.

## Open questions

- Does it send a user agent or other identifier that engines could use to tell editor traffic apart in their stats? (unverified)

## Sources

- README: https://github.com/leanprover-community/LeanSearchClient
- Moogle removal: https://github.com/leanprover-community/LeanSearchClient/pull/24
- Zulip, Kim Morrison on `#leansearch` being "alive and well": https://leanprover.zulipchat.com/#narrow/near/541372221
