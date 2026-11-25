# Jev as a reranker

A small comparison of [Jev](https://docs.typesafe.ai), TypeSafe's hosted System One model,
with the Qwen3-Reranker-0.6B that LeanExplore uses. Every system reorders the same pool of 50
candidates per query, so differences come from the reranker alone.

Jev does not generate text. It answers typed questions about a state; a Noul question returns
the probability that a statement holds, which is used here as the relevance score. It has no
open weights, so requests go to OpenRouter (`OPENROUTER_API_KEY`).

## Steps

```sh
# 1. On a GPU machine, inside a LeanExplore checkout's environment: dump the pools the
#    engine would rerank, with the deployed reranker's scores.
python dump_pools.py --data-directory /corpus/20260714_172516 \
  --queries queries.development.jsonl --output pools.jsonl

# 2. Optional, same machine: Qwen prompted as its model card specifies.
python qwen_official.py --pools pools.jsonl --output qwen.official.256.jsonl

# 3. Anywhere: score the pools with Jev, then compare.
python jev_scores.py --pools pools.jsonl --output jev.listwise.jsonl --mode listwise
python jev_scores.py --pools pools.jsonl --output jev.pointwise.jsonl --mode pointwise
python compare.py --pools pools.jsonl --jev jev.listwise.jsonl jev.pointwise.jsonl \
  --extra "Qwen3-Reranker-0.6B model-card prompt=qwen.official.256.jsonl"
```

The query file holds the mix queries of one split, one JSON object per line with `id`,
`query`, `query_type`, `library` and `judgments`. `dump_pools.py` checks its first ten pools
against `SearchEngine.search`. Outputs go under `data/`, which is not committed.

## Limits

- Only synthetic and public queries may be sent to Jev. Real search-log queries must not
  leave the server.
- Most queries have one labelled target, chosen by a language model. Other relevant
  declarations in a pool count as wrong.
- Jev's instructions list the query types of the mix; Qwen runs with LeanExplore's short
  deployed instruction. Neither was tuned on results.
- Jev's timings are wall clock through OpenRouter; Qwen's are on one H100.
