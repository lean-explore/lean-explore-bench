# Axiomatic Octo Search

- **Kind:** search engine (for any Lean project)

## How it works (brief)

"Indexing extracts Lean declarations with lean-extract (inspired by jixia and doc-gen4), describes each one informally with an LLM, and embeds the descriptions with an open embedding model. Queries embed your question the same way and rank declarations by similarity." The index is SQLite with `sqlite-vec` ([manual](https://axiomatic-ai.github.io/octo/)). The model names are not published.

## Evaluation

- No released data or code yet.

## Programmatic access (for a harness)

- **Snapshot pinning:** Search scopes carry explicit versions (`core@v4.32.0`, `batteries@v4.32.0`, `mathlib@v4.32.0`) in the URL ([example link](https://octo.axiomatic-ai.com/search?scopes=core%40v4.32.0%2Cbatteries%40v4.32.0%2Cmathlib%40v4.32.0%2Crepo%3ARemyDegenne%2Fbrownian-motion)). That is very useful for benchmark reproducibility if other scopes can be pinned too.
- **Rate limits, auth and REST API:** Not documented in anything we read (unverified). Accounts may be required for private repos.

## Relevance to lean-explore-bench

- It is the newest engine that may lead on quality, and it is the first to adopt MathlibQR as a shared yardstick. Include it once programmatic access is confirmed.
- Its per-project, per-branch indexing points to a benchmark slice this field lacks: searching a non-Mathlib or freshly changed project, where most engines' static indices fail.

## Open questions

- Which embedding and informalization models does it use, and what are the latency and quality tradeoffs of the shipped configuration?
- Is there a REST endpoint, and what are its rate limits? When will the code and technical report be released?

## Sources

- Manual: https://axiomatic-ai.github.io/octo/
- MathlibQR reference numbers: https://arxiv.org/abs/2605.13137
