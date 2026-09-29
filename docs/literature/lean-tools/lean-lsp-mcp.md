# lean-lsp-mcp search tools (MCP bundle for agents)

- **Kind:** tool (MCP server that wraps Lean LSP plus external search engines)
- **Links:** upstream <https://github.com/oOo0oOo/lean-lsp-mcp>; Project Numina fork <https://github.com/project-numina/lean-lsp-mcp> (local clone at `/Users/justinasher/Documents/Repositories/lean-lsp-mcp`, commit `5c0eddf`, 2026-01-28)
- **Authors / org, date:** upstream by oOo0oOo (checked at commit `bb176c5`, 2026-08-19, by a sub-agent). The fork is by Project Numina.
- **Status:** Active and open source.

## What it is

The most common way LLM agents such as Claude Code and Codex reach Lean search in 2025–2026. It exposes, as MCP tools:

- **Local, no network:** `lean_local_search`, `lean_completions`, `lean_hover_info`, `lean_multi_attempt`, `lean_run_code`. The last two can run `exact?`, `rw?`, and `#find`.
- **Remote engines:**
  - `lean_leansearch` (LeanSearch, natural language)
  - `lean_loogle` (Loogle)
  - `lean_leanfinder` (Lean Finder)
  - `lean_state_search` (LeanStateSearch)
  - `lean_hammer_premise` (LeanPremise server)
  - `lean_leandex`, only in the Numina fork (Numina's semantic search)

([fork server.py](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py); [upstream README](https://github.com/oOo0oOo/lean-lsp-mcp))

## How it works

- **`lean_local_search`:** a ripgrep regex over the `.lean` sources of the project, its dependencies, and the Lean stdlib. It matches `theorem|lemma|def|…` followed by a name that contains the query as a prefix of a name component. It returns `{name, kind, file}`. This is pure lexical name search over source text and needs no index build ([search_utils.py](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/search_utils.py)). Its docstring advertises it to agents as "Confirm declarations exist ... to prevent hallucinating APIs. VERY USEFUL AND FAST!"
- **Proof-state tools** (`lean_state_search`, `lean_hammer_premise`) read the first goal at a file position through LSP and send it to the remote engine.
- **Client-side rate limits.** In upstream `config.py` (requests / 30 s): leansearch 90, loogle 3, leanfinder 10, lean_state_search 6, hammer_premise 6. They are skipped when a self-hosted backend URL is set (upstream, per sub-agent). The fork hard-codes 3/30 s for loogle, state_search, and hammer, and 10/30 s for leanfinder.
- **Local Loogle:** `--loogle-local` / `LEAN_LOOGLE_LOCAL` runs Loogle against the project's own Mathlib. It needs a built Mathlib, is Unix-only, uses about 13 GiB RSS on the first index build and about 7 GiB after, and falls back to the remote API (upstream README, per sub-agent).
- **Backend health on 2026-09-28:** from our machine, premise-search.com gave no response, the default hammer URL `http://leanpremise.net` returned 404 (per sub-agent), and Loogle responded. The defaults are therefore fragile.

## Evaluation

No evaluation of the MCP bundle or of `lean_local_search` was found.

## Relevance to lean-explore-bench

- **Harness:**
  - lean-lsp-mcp is a ready-made **uniform adapter** for running several engines from one Python process (or through MCP) with consistent JSON output.
  - It does not pin index versions, so for published numbers call each engine's own pinned or self-hosted backend. Use lean-lsp-mcp for an **agentic track**.
- **Agentic track:** "an LLM agent with tool set X finds the right declaration or finishes the proof". This matches how the tools are actually used in 2025–26 and captures query-reformulation effort. Useful arms:
  - no tools
  - `lean_local_search` only
  - `+ lean_loogle`
  - `+` semantic engines
  - all tools
- **`lean_local_search` as a baseline:** a strong, cheap lexical baseline for identifier-like queries. Agents lean on it heavily, so it is the bar a semantic engine must beat in agent loops.
- **Rate limits:** they make large benchmark runs against public endpoints impractical, and running one would also be poor etiquette. Self-host, or ask the maintainers.

## Open questions

- Upstream details (`bb176c5` config values, local Loogle memory figures) were read by a sub-agent and not re-checked here.

## Sources

- Fork source (read locally): <https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py>, <https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/search_utils.py>
- Upstream repo/README: <https://github.com/oOo0oOo/lean-lsp-mcp>
- Backends: <https://loogle.lean-lang.org/>, <https://premise-search.com/>, <https://github.com/hanwenzhu/lean-premise-server>, <https://leansearch.net/>, <https://arxiv.org/abs/2510.15940>

## Merged detail (from the former `lean-engines/lean-lsp-mcp.md`)

| Tool | Backend | Query style | Client throttle (upstream) |
|---|---|---|---|
| `lean_leansearch` | `POST https://leansearch.net/search` | NL, mixed, names, Lean terms | 90 / 30 s |
| `lean_leanfinder` | HF inference endpoint (`LEAN_FINDER_URL`) | NL, questions, proof state and intent | 10 / 30 s |
| `lean_loogle` | loogle.lean-lang.org or a local Loogle | formula and pattern | 3 / 30 s |
| `lean_state_search` | premise-search.com (`LEAN_STATE_SEARCH_URL`) | goal at a file position | 6 / 30 s |
| `lean_hammer_premise` | leanpremise.net (`LEAN_HAMMER_URL`) | goal | 6 / 30 s |
| `lean_local_search` | ripgrep over the local project | name prefix | none |

Sources: [tools/search.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py), [config.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/config.py).

- **Usage context.** LeanSearch reported usage rising sharply from January 2026 "coinciding with the wave of coding agents" and asked lean-lsp-mcp to raise its throttle ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)).
- **Output normalisation differs per engine.** Upstream `lean_leansearch` returns only `name`, `module_name`, `kind` and `type` and drops the informal text; `lean_leanfinder` drops any result whose URL is not a mathlib4_docs link. An agent therefore sees different evidence from different engines, so any LLM-judge protocol should present results in one uniform format hydrated from one metadata source, as LeanSearch v2 did.
- **Numina fork:** adds `lean_leandex` (LeanDex SSE API with `generate_query=False`, `analyze_result=False`, rate limiter commented out) and has no `lean_leansearch` in code although its README documents one. Neither version wraps LeanExplore, which ships its own MCP server ([../lean-engines/leanexplore.md](../lean-engines/leanexplore.md)).
