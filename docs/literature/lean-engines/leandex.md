# LeanDex (Project Numina)

- **Kind:** search engine (agentic, LLM in the loop)
- **Links:** https://leandex.projectnumina.ai ; API `https://leandex.projectnumina.ai/api/v1/search` ; fork of LeanExplore https://github.com/project-numina/lean-explore ; Zulip announcement https://leanprover.zulipchat.com/#narrow/near/554153512
- **Authors / org, date:** Project Numina (announced by Bolton Bailey), 2025-11-06.
- **Status:** Live on 2026-09-28 (site HTTP 200 and working API, checked by us), but the site returned HTTP 522 twice on 2026-09-29. The GitHub fork's description is "A search engine for Lean 4 declarations for numina" and it was last pushed 2026-01-29 ([GitHub API](https://github.com/project-numina/lean-explore)). Whether the deployed service matches the fork is unverified. The Numina maintainers said "Yes, I think so" when asked ([Zulip](https://leanprover.zulipchat.com/#narrow/near/554181117)). No license was checked for the fork (upstream LeanExplore is Apache-2.0).

## What it is

LeanDex is "an agentic semantic search tool for Lean declarations", based on LeanExplore. It "uses an LLM to elaborate search queries for more precise semantic search and ranking of results" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/554153512)). At launch it indexed Mathlib (v4.24), FLT and "a few others", with monthly updates planned ([Zulip](https://leanprover.zulipchat.com/#narrow/near/554153512), [Kevin Buzzard](https://leanprover.zulipchat.com/#narrow/near/554166812)). Numina's Putnam-solving agent reportedly used it (unverified; source is a private message citing [this X post](https://x.com/JiaLi52524397/status/2013619608956346773)).

## How it works (brief)

A LeanExplore-derived hybrid retriever runs underneath. Two optional LLM stages sit on top of it: `generate_query` rewrites the user query, and `analyze_result` asks an LLM to pick the closest matches. Both are exposed as API flags ([numina lean-lsp-mcp client](https://github.com/project-numina/lean-lsp-mcp), `src/lean_lsp_mcp/server.py`, and our probe on 2026-09-28). Results are StatementGroup-style records with `primary_declaration`, `source_file`, line ranges, `docstring` and `informal_description` ([numina lean-lsp-mcp README](https://github.com/project-numina/lean-lsp-mcp)).

## Evaluation

None published that we could find: no paper, benchmark or numbers. Any comparison would be first-party to lean-explore-bench.

## Programmatic access (for a harness)

- `GET /api/v1/search?q=...&limit=N&generate_query={true|false}&analyze_result={true|false}` returns a **server-sent event stream**. The stages are `generate_query`, then `search`, then analysis, and the final `data:` event holds `data.search_results` (our probe, 2026-09-28; client code in [project-numina/lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp)).
- With both flags off it behaves as a plain retriever. With them on, results are non-deterministic and involve an LLM. A benchmark should test both settings separately and label the LLM-in-loop run as a different system class.
- **Rate limit:** undocumented. The Numina lean-lsp-mcp fork has its rate limiter commented out ([server.py](https://github.com/project-numina/lean-lsp-mcp)).
- **Snapshot:** Mathlib v4.24 at launch. The current version is unverified, and the API does not report it.
- **MCP:** Only through the Numina fork of lean-lsp-mcp (`lean_leandex` tool). Numina said it was "thinking of developing our own MCP server" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/554181117)).

## Relevance to lean-explore-bench

- It is the main deployed example of query rewriting plus LLM result analysis on top of a hybrid retriever. That makes it a good test of whether an LLM in the loop beats a better base retriever such as LeanSearch v2's reranker.
- It indexes more than Mathlib (FLT), which is useful for any multi-package slice.
- Because it shares a lineage with LeanExplore, gains measured on it may partly reflect LeanExplore's base retriever.

## Open questions

- What does the deployed pipeline use now (LLM model, embedder, snapshot)? Is it still being updated monthly?
- What are the rate limits and terms of use for automated benchmarking?

## Sources

- Zulip announcement and discussion: https://leanprover.zulipchat.com/#narrow/near/554153512 , https://leanprover.zulipchat.com/#narrow/near/554166812 , https://leanprover.zulipchat.com/#narrow/near/554181117
- Fork: https://github.com/project-numina/lean-explore
- Numina lean-lsp-mcp fork (LeanDex client, `lean_leandex`): https://github.com/project-numina/lean-lsp-mcp (local clone `/Users/justinasher/Documents/Repositories/lean-lsp-mcp`)
- Live API probe: `https://leandex.projectnumina.ai/api/v1/search?q=Cauchy%20Schwarz%20inequality&limit=2&generate_query=false&analyze_result=false` (2026-09-28)
