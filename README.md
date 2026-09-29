# lean-explore-bench

Benchmarks for Lean 4 search engines.

The goal of this repository is to measure how well search engines — such as
[LeanExplore](https://github.com/lean-explore/lean-explore) — help find the
declarations needed to write Lean 4 code, and to compare them on a fair,
reproducible footing.

## Shared infrastructure

`lean_explore_bench.infra` holds code shared across the project. It currently
has an async OpenRouter client (`OpenRouterClient`) with retries on
transient errors, a concurrency cap, JSON-schema output, and running token
and cost totals. By default it only routes to providers that do not store
or train on prompts (`data_collection: "deny"`).

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
