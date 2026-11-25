# Input and output formats

This page defines the UTF-8 JSON files that the offline tool reads and writes.

## Query export

The root object has any of the keys `web`, `web_account`, `api` and `mcp`. Each maps to a list
of records with `query` (string), `package_filters` (list of nonempty strings), `result_count`
(nonnegative integer or null) and `collected_on` (`YYYY-MM-DD`). An unknown key or an invalid
record stops the import with an error that names only the record's position.
`leq-bench audit --since` keeps records from that day on. Positions are indices into the
export, not user or session identifiers.

## Collection

```json
{
  "corpus_revision": "a-real-pinned-corpus-hash",
  "queries": [{
    "id": "task-1-variant-a",
    "group_id": "task-1",
    "track": "human",
    "answerability": "answerable",
    "judgments": {"Namespace.relevant": 3, "Namespace.partial": 1}
  }]
}
```

`group_id` names an independent task; all paraphrases of one task share it. `track` is
`human`, `agent` or `unknown`. `answerability` is `answerable`, `unanswerable` or `unknown`.
Grades are integers 0 to 3. An answerable query has at least one grade of 2 or more; an
unanswerable query has none.

Optional `premise_routes` lists alternative proof routes. Each route is a list of groups, and
each group a list of interchangeable documents with grade 2 or more:

```json
{"premise_routes": [[["lemmaA", "equivalentA"], ["lemmaB"]], [["lemmaC"]]]}
```

Here A (or its equivalent) with B completes one route, and C alone another.

## Ranked run

```json
{
  "name": "engine-version-and-configuration",
  "corpus_revision": "a-real-pinned-corpus-hash",
  "max_k": 100,
  "results": {
    "task-1-variant-a": {
      "status": "ok",
      "documents": ["Namespace.relevant", "Namespace.partial"],
      "latency_ms": 42.5,
      "cost_usd": 0.001,
      "abstained": false
    }
  }
}
```

`documents` is in rank order. `max_k` is the depth requested from the engine; cutoffs beyond
it are not scored. `status` is `ok`, `error` or `timeout`, and a failed request has no
documents. A query absent from `results` is scored as a `missing` failure. `abstained: true`
requires status `ok` and no documents. `latency_ms` and `cost_usd` are optional, finite and
nonnegative.

The scorer checks that both files name the same `corpus_revision`. It does not check that
document IDs exist in a corpus.

## Evaluation and comparison output

`evaluate` writes per-query scores and summaries for all queries and for each track. Every
metric carries its own count `n`. Means are over queries, without traffic weighting.

`compare` writes the candidate-minus-baseline difference, a 95% cluster bootstrap interval, a
two-sided paired group randomization p-value, and the numbers of queries and groups. It refuses
runs with different collections, different metric coverage or fewer than two groups. It applies
no multiple-comparison correction; `evaluate.py` provides `holm`.

## Review output

`leq-bench review` writes metadata (export SHA-256, reviewer, seed, sample size) and one entry
per export position with `intent`, `actor`, `certainty`, `evidence`, `language`,
`expected_output`, the channel and the stratum population and sample size. The file contains
no query text, but its positions point into private data. Each reviewer needs a separate file.
