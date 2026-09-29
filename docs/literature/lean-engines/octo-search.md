# Axiomatic Octo Search

- **Kind:** search engine (for any Lean project)
- **Links:** web search https://octo.axiomatic-ai.com/search ; product page https://prover.axiomatic-ai.com/octo ; manual https://axiomatic-ai.github.io/octo/ ; VS Code extension https://marketplace.visualstudio.com/items?itemName=AxiomaticAI.axiomatic-octo ; Zulip announcement https://leanprover.zulipchat.com/#narrow/near/617203019
- **Authors / org, date:** Axiomatic AI (announced by Austin Letson), 2026-08-18. Web search, public repo listing and MCP were added 2026-09-07 ([Zulip](https://leanprover.zulipchat.com/#narrow/near/622195251)).
- **Status:** Live, and described as "alpha" in the [manual](https://axiomatic-ai.github.io/octo/). Not yet open source: "We're also preparing to release Octo Search open source" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/617203019)). A technical report is promised but not yet out ([Zulip](https://leanprover.zulipchat.com/#narrow/near/617871976)).

## What it is

Octo is a semantic search engine that indexes *your* Lean project, all its branches and its dependencies within minutes of a push to GitHub. It also offers a shared web corpus of publicly listed repositories, scoped by version, for example `mathlib@v4.32.0` ([Zulip](https://leanprover.zulipchat.com/#narrow/near/622195251)). The authors credit LeanSearch v2, LeanExplore and doc-gen4 as major influences ([Zulip](https://leanprover.zulipchat.com/#narrow/near/617203019)).

## How it works (brief)

"Indexing extracts Lean declarations with lean-extract (inspired by jixia and doc-gen4), describes each one informally with an LLM, and embeds the descriptions with an open embedding model. Queries embed your question the same way and rank declarations by similarity." The index is SQLite with `sqlite-vec` ([manual](https://axiomatic-ai.github.io/octo/)). The model names are not published.

## Evaluation

- **Self-reported, informal (Zulip, not a paper):** On MathlibQR from the LeanSearch v2 paper, "on the same subset, our best configuration reaches 0.765 nDCG@10 / 0.914 Recall@10, against the 0.623 / 0.780 reported for LeanSearch v2". The team adds: "The configuration we ship makes some tradeoffs for lower query latency" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/617871976)). The shipped configuration therefore has not been evaluated publicly, and the comparison mixes Octo's own run with numbers LeanSearch reported rather than a joint run.
- No released data or code yet.

## Programmatic access (for a harness)

- **MCP:** The manual describes connecting Claude Code, Codex and Cursor to "Octo's two MCP servers: `octo-mcp`, over your own project", plus a public-corpus server ([manual](https://axiomatic-ai.github.io/octo/), [agents page](https://axiomatic-ai.github.io/octo/agents/#add-it-to-your-client)). There is also a CLI and a skills interface ([Zulip](https://leanprover.zulipchat.com/#narrow/near/617203019)).
- **Snapshot pinning:** Search scopes carry explicit versions (`core@v4.32.0`, `batteries@v4.32.0`, `mathlib@v4.32.0`) in the URL ([example link](https://octo.axiomatic-ai.com/search?scopes=core%40v4.32.0%2Cbatteries%40v4.32.0%2Cmathlib%40v4.32.0%2Crepo%3ARemyDegenne%2Fbrownian-motion)). That is very useful for benchmark reproducibility if other scopes can be pinned too.
- **Rate limits, auth and REST API:** Not documented in anything we read (unverified). Accounts may be required for private repos.

## Relevance to lean-explore-bench

- It is the newest engine that may lead on quality, and it is the first to adopt MathlibQR as a shared yardstick. Include it once programmatic access is confirmed.
- Its per-project, per-branch indexing points to a benchmark slice this field lacks: searching a non-Mathlib or freshly changed project, where most engines' static indices fail.

## Open questions

- Which embedding and informalization models does it use, and what are the latency and quality tradeoffs of the shipped configuration?
- Is there a REST endpoint, and what are its rate limits? When will the code and technical report be released?

## Sources

- Zulip announcement: https://leanprover.zulipchat.com/#narrow/near/617203019 ; feature update: https://leanprover.zulipchat.com/#narrow/near/622195251 ; discussion and benchmark claim: https://leanprover.zulipchat.com/#narrow/near/617871976 , https://leanprover.zulipchat.com/#narrow/near/617853947
- Manual: https://axiomatic-ai.github.io/octo/
- MathlibQR reference numbers: https://arxiv.org/abs/2605.13137
