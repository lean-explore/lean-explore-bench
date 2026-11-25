# lean-explore-bench

Benchmarks for Lean 4 search engines.

> **Early development.** This project is in its first beta and highly
> unstable: interfaces, categories, data formats and numbers will change
> without notice. Do not rely on it yet.

The repository has three parts:

- **The query mix**: a benchmark of 3,200 queries in four buckets of 800
  (names and keywords, natural language, formal, and real questions from the
  Lean Zulip), scored as the plain mean of the buckets. Inside the buckets are
  the eight forms that real searches take (a name, several names, names with
  keywords, keywords, prose, prose with names, formal statements, proof states). Queries are written to match the length
  and style of real searches of each form, and every answer is a Mathlib
  declaration that all engines index, so the score measures search and not
  coverage. See [the query mix](docs/query-mix.md).
- **The evaluation pilot**: a 50-query study of the LeanExplore pipeline,
  stage by stage, with graded relevance labels. See the
  [pilot report](docs/pilot-report.md).
- **Query log analysis**: statistics on how people and agents search, computed
  without exposing what they search for. See below.

## The query mix

`leb-mix` builds the mix from a LeanExplore corpus snapshot, sends it to
search engines and scores the results by query type and by library.

```sh
pip install -e ".[dev]" -e tools/offline

leb-mix profile  --log --to log-profile.json                # on the server that holds the log
leb-mix generate --corpus lean_explore.db --out data/mix --style log-profile.json
leb-mix zulip    --corpus lean_explore.db --out data/mix    # questions from the Lean Zulip
leb-mix build    --corpus lean_explore.db --out data/mix    # assemble, split, export
leb-mix compare  --reference log-profile.json --candidate mix-profile.json
leb-mix run      --engine leanexplore --out data/mix        # also: leansearch, loogle, leanfinder
leb-mix score    --engine leanexplore leansearch --out data/mix --weights log-profile.json
```

`profile` describes a set of queries by form and style using shares only, so a
profile of the real log can leave the server. `compare` measures how far any
query set is from it, and `score --weights` weights results by real traffic.

`generate` and `zulip` call language models through OpenRouter and need
`OPENROUTER_API_KEY`; both stop at a spending limit (`--budget`) and resume
where they stopped. `zulip` also needs a `~/.zuliprc` for the Lean Zulip.
Generated data is written under `data/`, which is not committed.

## Documentation

| Document | Contents |
| --- | --- |
| [Query mix](docs/query-mix.md) | Query forms, what real searches look like, how queries are written and checked, first results |
| [Pilot report](docs/pilot-report.md) | The 50-query pilot: method, results, limits |
| [Pilot dataset card](docs/pilot-dataset-card.md) | What the pilot data contains and where it lives |
| [Evaluation protocol](docs/evaluation-protocol.md) | Relevance grades, metrics, splits, statistics |
| [Human review](docs/human-review.md) | How to review labels; calibration decisions; open questions |
| [Reproduction](docs/reproduction.md) | Recomputing the pilot scores; what is kept outside Git |
| [Extraction and cache](docs/extraction-and-cache.md) | Verified metadata normalization and cache keys |
| [Reranker training](docs/reranker-training.md) | A proposal; no training has been run |
| [Search categories](docs/search-categories.md) | Query categories found in the search log |
| [Generation design](docs/generation-design.md) | Plan for log-style synthetic queries |
| [Literature review](docs/literature/README.md) | Background on search evaluation and Lean search engines |

Tools with their own documentation:

- [Offline evaluator](tools/offline/README.md): metrics, paired comparisons,
  annotation and reports, in standard-library Python.
- [Candidate selection experiments](experiments/candidate_selection/README.md):
  retrieval and reranking ablations on the local engine.
- [Declaration metadata](experiments/declaration_metadata/README.md): the
  metadata exporter, its Lean-checked normalization and the cache prototype.

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
