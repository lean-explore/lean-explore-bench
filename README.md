# lean-explore-bench

Benchmarks for Lean 4 search engines.

> **Early development.** This project is in its first beta and highly
> unstable: interfaces, categories, data formats and numbers will change
> without notice. Do not rely on it yet.

The goal of this repository is to measure how well search engines — such as
[LeanExplore](https://github.com/lean-explore/lean-explore) — help find the
declarations needed to write Lean 4 code, and to compare them on a fair,
reproducible footing.

The literature review behind the benchmark design is in
[`docs/literature/`](docs/literature/README.md).

## Query log analysis

`lean_explore_bench.querylog` loads LeanExplore's de-identified search log,
removes duplicate and near-duplicate queries (automated bursts), and measures
each query's topic-free surface features: length, share of Lean identifiers,
share of prose, symbols, and a *skeleton* that keeps its structure but drops
its content. `lean_explore_bench.analysis` finds query categories
statistically from those features (Gaussian mixtures, keeping the largest
number of categories that all reproduce on subsamples) and builds summary
statistics and charts.
Categories describe how people search, never what they search for.

Real queries are private: our Privacy Policy allows publishing only synthetic
queries and aggregate statistics. So the code is public, but it runs on the
server that holds the log, decrypts in memory, and writes nothing that could
reproduce a query:

```sh
pip install -e ".[dev]"            # add ",embed" for the query map (GPU)

# Aggregate charts and CSV tables. Groups under 10 are suppressed.
leb-querylog report --out reports/2026-09-29

# Server-only page with individual queries, served from memory on 127.0.0.1.
leb-querylog explore --embed --device cuda:7
ssh -L 8050:localhost:8050 xtx     # then open http://localhost:8050
```

By default the log is read from `~/lean-explore-app/data/website_user_data.db`
and the key from `~/lean-explore-app/.env`; override them with
`LEB_QUERY_LOG_DB`, `LEB_QUERY_LOG_ENV_FILE` or `SEARCH_HISTORY_ENCRYPTION_KEY`.
`.gitignore` keeps data files, notebooks and `.env` files out of git. CI runs
ruff, strict mypy and the tests.

The categories found in the first day of the log are in
[`docs/search-categories.md`](docs/search-categories.md), and the plan for
generating synthetic benchmark queries is in
[`docs/generation-design.md`](docs/generation-design.md).

## Shared infrastructure

`lean_explore_bench.infra` holds code shared across the project. It currently
has an async OpenRouter client (`OpenRouterClient`) with retries on
transient errors, a cap on requests in flight, JSON output validated against
a schema, and running token and cost totals. By default it only routes to
providers that do not store or train on prompts (`data_collection: "deny"`).

```python
import asyncio
from lean_explore_bench.infra import OpenRouterClient, OpenRouterSettings

async def main() -> None:
    settings = OpenRouterSettings.from_env()  # reads OPENROUTER_API_KEY
    async with OpenRouterClient(settings) as client:
        reply = await client.complete(
            [{"role": "user", "content": "Hello"}], model="anthropic/claude-sonnet-5.5"
        )
        print(reply.text, client.usage.cost)

asyncio.run(main())
```

Set `OPENROUTER_API_KEY`, and optionally `OPENROUTER_MODEL` (the default
model) and `OPENROUTER_MAX_CONCURRENCY`.
