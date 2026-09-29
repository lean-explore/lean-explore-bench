# Loogle

- **Kind:** search engine (name / constant / type-pattern search over Mathlib)
- **Links:** service and help <https://loogle.lean-lang.org/>; JSON API `https://loogle.lean-lang.org/json?q=…`; code <https://github.com/nomeata/loogle>
- **Authors / org, date:** Joachim Breitner. Announced on Lean Zulip #general, topic "Loogle!", 2023-08-19 ([msg 386143361](https://leanprover.zulipchat.com/#narrow/channel/113488-general/topic/Loogle!/near/386143361); [public archive](https://leanprover-community.github.io/archive/stream/113488-general/topic/Loogle!.html)). Breitner describes it as "a Mathlib search engine inspired by Haskell's Hoogle" ([blog, 2023-11-01](https://www.joachim-breitner.de/blog/809-Joining_the_Lean_FRO)). Now hosted by the Lean FRO (help page footer).
- **Status:** Live and answering on 2026-09-28. The help page reported Loogle rev `9f11169` and Mathlib rev `bc5fddb` ([loogle.lean-lang.org](https://loogle.lean-lang.org/)). It "tries to upgrade to the latest Mathlib every 6 hours" ([README](https://github.com/nomeata/loogle)). Apache-2.0 ([README](https://github.com/nomeata/loogle)).

## What it is

A web, API, and bot front-end for **formal, structural** search over Mathlib declarations. It is the de facto standard tool when the user can write part of the statement in Lean syntax.

## How it works

Query language ([help page](https://loogle.lean-lang.org/)):

- a constant (`Real.sin`): lemmas mentioning it
- a quoted name substring (`"differ"`)
- a subexpression pattern with `_` and named `?a` metavariables, including non-linear ones (`Real.sqrt ?a * Real.sqrt ?a`)
- a conclusion pattern with `|-` or `⊢` (`|- tsum _ = _ * tsum _`)
- kind filters (`⊢ (_ : Prop)`)

Comma-separated filters are ANDed. A metavariable is not shared across comma-separated filters ([Zulip "loogle miss"](https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/loogle.20miss/near/485125724)).

Implementation, briefly: a constant-mention index plus a suffix trie over names narrow the candidates, which are then matched by reducible `isDefEq` ([Loogle/Find.lean](https://github.com/nomeata/loogle/blob/master/Loogle/Find.lean), per a sub-agent's reading).

- **Output:** an unranked set that is exact under the filters, returned in index order. At most 200 hits are shown, e.g. `"differ"` → "Found 1863 declarations … only the first 200 are shown" (live query, 2026-09-28).
- **Strengths against semantic search:**
  - Precise, predictable, and complete for what the pattern says.
  - Handles notation and non-linear patterns.
  - Answers "all lemmas about X and Y".
- **Weaknesses:**
  - No natural language.
  - Fails if the user guesses the wrong constant (`Real.sqrt` vs `NNReal.sqrt`) or the wrong form of the statement.
  - No relevance ranking.
  - Only the indexed Mathlib revision; other projects must self-host.
  - Related work describes it as having "strict matching criteria, which often leads to failures in retrieving relevant theorems" ([arXiv 2501.13959](https://arxiv.org/abs/2501.13959)), and says it depends "on exact names or goal states" ([arXiv 2510.15940](https://arxiv.org/abs/2510.15940)).

## Availability

- **Web and JSON API.** The API has "no stability of the format guaranteed" ([README](https://github.com/nomeata/loogle)). A live response has the fields `count`, `header`, `heartbeats`, and `hits[{name,type,module,doc}]`.
- **Zulip bot:** `@**loogle** query`.
- **Editors:** the "Loogle Lean" VS Code extension ([marketplace](https://marketplace.visualstudio.com/items?itemName=ShreyasSrinivas.loogle-lean)), the Lean 4 VS Code extension's command palette, and lean.nvim.
- **In Lean:** `#loogle` from LeanSearchClient, which is a Mathlib dependency.
- **MCP:** the `lean_loogle` tool in lean-lsp-mcp, which can also run it locally (see `tool-lean-lsp-mcp.md`).

## Evaluation

**No quantitative evaluation of Loogle was found.** Papers that cite it use it only in related work: LeanStateSearch ([2501.13959](https://arxiv.org/abs/2501.13959)), Lean Finder ([2510.15940](https://arxiv.org/abs/2510.15940)), and LeanSearch v2 ([2605.13137](https://arxiv.org/abs/2605.13137)), which lists "Moogle and Loogle provide semantic and syntactic search respectively" but does not include Loogle among its baselines. LeanExplore ([2506.11085](https://arxiv.org/abs/2506.11085)) cites it only in the bibliography. No usage statistics have been published (unverified).

## Relevance to lean-explore-bench

- **Harness:**
  - `GET /json?q=<urlencoded>`.
  - Record `heartbeats` as a cost proxy, and record the served Mathlib rev from the help page on each run.
  - The public server publishes no rate limit (unverified), but lean-lsp-mcp throttles it to 3 requests per 30 s client-side ([upstream README/config](https://github.com/oOo0oOo/lean-lsp-mcp)). The CLI or a local server avoids both the limit and version drift.
  - Local build: `lake`, pinned to our Mathlib commit. lean-lsp-mcp's local mode reports about 13 GiB RSS on the first index build and about 7 GiB on later loads.
  - **Pin a local instance for any published numbers.**
- **Role:** Loogle cannot answer natural-language queries, so scoring it on an NL track is meaningless. Two uses make sense:
  1. **A separate "formal pattern" query track.** Each item carries a Loogle-syntax query, written by hand or derived from the gold statement by abstracting subterms. Score Loogle, `#find`, and semantic engines given the same string. This measures whether semantic engines match structural search on structural queries.
  2. **A candidate generator or verifier.** Check whether the gold declaration is in the exact set that a correct pattern returns.
- **Metrics:** Loogle returns an unranked set, so report set metrics (hit/recall, result-set size) or define a deterministic ranking (e.g. by statement length) before computing MRR or nDCG.
- **Query-writing effort:** this is the hidden cost of the tool. A user study or LLM-written Loogle queries (an "agent + Loogle" baseline) would capture it.

## Open questions

- Exact behavior on instances and coercions beyond reducible defeq (unverified).
- Whether Loogle query logs or bot usage could seed realistic structural queries.

## Sources

- Help page and query syntax: <https://loogle.lean-lang.org/>
- README (API, bot, editors, update cadence, license): <https://github.com/nomeata/loogle>
- Matcher implementation: <https://github.com/nomeata/loogle/blob/master/Loogle/Find.lean>
- Zulip announcement: <https://leanprover.zulipchat.com/#narrow/channel/113488-general/topic/Loogle!/near/386143361>
- Zulip "loogle miss": <https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/loogle.20miss/near/485125724>
- Breitner blog: <https://www.joachim-breitner.de/blog/809-Joining_the_Lean_FRO>
- VS Code extension: <https://marketplace.visualstudio.com/items?itemName=ShreyasSrinivas.loogle-lean>
- Community overview "Searching for Theorems in Mathlib" (2025-06-25): <https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/>
- Papers citing Loogle: <https://arxiv.org/abs/2501.13959>, <https://arxiv.org/abs/2510.15940>, <https://arxiv.org/abs/2605.13137>, <https://arxiv.org/abs/2506.11085>
- lean-lsp-mcp (rate limit, local mode): <https://github.com/oOo0oOo/lean-lsp-mcp>
