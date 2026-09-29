# lean-lsp-mcp search tools (upstream and Project Numina fork)

- **Kind:** tool (MCP server that wraps several engines)
- **Links:** upstream https://github.com/oOo0oOo/lean-lsp-mcp ; Numina fork https://github.com/project-numina/lean-lsp-mcp (local clone `/Users/justinasher/Documents/Repositories/lean-lsp-mcp`, HEAD `5c0eddf`, 2026-01-28)
- **Authors / org, date:** Oliver Dressler (upstream, 2025–). The Numina fork is by Project Numina.
- **Status:** Upstream active (last push 2026-08-19, per the GitHub API). It is currently the de facto way coding agents reach Lean search engines. LeanSearch saw usage rise sharply from January 2026 "coinciding with the wave of coding agents" and asked lean-lsp-mcp to raise its throttle ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)).

## What it is

It is an MCP server for agentic Lean work. Besides LSP tools, it exposes search tools that proxy external engines.

## Search tools and backends

| Tool | Backend | Query style | Client throttle (upstream) |
|---|---|---|---|
| `lean_leansearch` | `POST https://leansearch.net/search` | NL, mixed, names, Lean terms | 90 / 30 s |
| `lean_leanfinder` | HF inference endpoint (`LEAN_FINDER_URL`) | NL, questions, proof state and intent | 10 / 30 s |
| `lean_loogle` | loogle.lean-lang.org or a local Loogle | formula and pattern | 3 / 30 s |
| `lean_state_search` | premise-search.com (`LEAN_STATE_SEARCH_URL`) | goal at a file position | 6 / 30 s |
| `lean_hammer_premise` | leanpremise.net (`LEAN_HAMMER_URL`) | goal | 6 / 30 s |
| `lean_local_search` | ripgrep over the local project | name prefix | none |

Sources: [tools/search.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py), [config.py `RATE_LIMITS`](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/config.py), [README](https://github.com/oOo0oOo/lean-lsp-mcp).

**Output normalization:** Upstream `lean_leansearch` returns only `name`, `module_name`, `kind` and `type`, and drops the informal text ([search.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py)). `lean_leanfinder` drops any result whose URL is not a mathlib4_docs link (same file).

**Numina fork differences:** It adds `lean_leandex`, which calls the LeanDex SSE API with `generate_query=False` and `analyze_result=False` and has its rate limiter commented out. It has no `lean_leansearch` tool in code, although the README still documents one (local `src/lean_lsp_mcp/server.py` and `README.md`). LeanExplore is not wrapped by either version. LeanExplore ships its own MCP server instead ([leanexplore.md](leanexplore.md)).

## Evaluation

None of the tools themselves are evaluated. The upstream README asks users to cite the underlying engines.

## Relevance to lean-explore-bench

- It is the reference integration for the "agent" setting. The benchmark could include an agent-in-the-loop track in which an LLM chooses among these tools, and compare it with direct API calls.
- It is also a record of how engines are actually reached in practice: request shapes, fields kept and rate limits. The harness adapters can borrow its request code.
- Because it strips informal descriptions, an agent sees different evidence from different engines. Any LLM-judge protocol should present results in a uniform format hydrated from one metadata source, as LeanSearch v2 did ([arXiv:2605.13137](https://arxiv.org/abs/2605.13137)).

## Open questions

- Will upstream add LeanExplore, LeanDex, LeanSearch v2 augmentation or Octo backends?

## Sources

- Upstream repo, search tools, config: https://github.com/oOo0oOo/lean-lsp-mcp
- Numina fork: https://github.com/project-numina/lean-lsp-mcp
- LeanSearch usage and rate-limit note: https://leanprover.zulipchat.com/#narrow/near/596070778
