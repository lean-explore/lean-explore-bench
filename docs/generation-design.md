# Generating synthetic benchmark queries (design, beta)

The goal is good benchmark data that never shows what users actually search
for and does not mirror any user's queries or research areas.

## Style from the log, topics from mathematics

Each synthetic query combines two independent choices:

- **Style**, learned from the query log: one of the statistical categories
  from `lean_explore_bench.analysis.categories`. Categories are fitted on
  topic-free features (length, identifier, prose and symbol shares, and query
  skeletons), so they describe how people search, not what about.
- **Topic**, drawn from mathematics as a whole, not from the log. The first
  step is to build a large, broad distribution of mathematical topics, for
  example from the Mathematics Subject Classification (MSC2020) and
  Mathlib's module tree, with sampling flattened so that no area dominates.

Keeping the two apart means a category dominated by one user's research
cannot turn into many synthetic queries about that research.

## Target kinds

Not every query has an answer in the library. Each topic seed gets one of:

1. **Existing target**: a Mathlib declaration. Its source declaration is
   the known answer.
2. **Future target**: a declaration added after a pinned snapshot, taken
   from Mathlib's history. It has no answer at the snapshot and an answer
   later, which tests index freshness.
3. **No target**: mathematics not formalised in any indexed library. It is
   confirmed only after all engines and a judge fail to find it, and scored
   in a separate no-answer track.

The mix is our choice and each kind is reported as its own track.

## Generation loop

1. For each style category, write a prompt describing the category from its
   statistics, with synthetic examples based on the real data. The prompt
   contains no real query.
2. An LLM via the OpenRouter API writes queries for sampled (category,
   topic) pairs, then uses its own accepted outputs as further references.
   Calls go through `lean_explore_bench.infra.OpenRouterClient`: batches via
   `complete_many`, structured output via `complete_json` (validated against
   its schema), provider routing with `data_collection: "deny"`, and cost
   tracked in `client.usage`.
3. The prompt and sampling are designed so the output fits the category's
   distribution directly, not by filtering after the fact.

## Checks (run on the server)

- **Style fidelity:** synthetic queries fall into their intended category,
  and their feature distributions match the real category's.
- **Topic breadth:** coverage is broad and even across the topic
  distribution, and does *not* follow the log's topics.
- **Diversity:** no near-duplicates among synthetic queries, and wide spread
  in embedding space within each category.
- **Privacy:** no synthetic query is close to any real query by exact match,
  n-gram overlap or embedding distance.

Only queries that pass every check are published, together with aggregate
statistics that cannot identify anyone or reproduce any query.
