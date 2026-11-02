# Input and output contracts

All files use UTF-8 JSON. The query export and evaluator collections are different
formats: private search requests do not become relevance judgments automatically.

## Query export

Root keys are any subset of `web`, `web_account`, `api`, `mcp`. Each maps to a list
of objects with `query` (string), `package_filters` (list of nonempty strings),
`result_count` (nonnegative integer or null), and `collected_on` (YYYY-MM-DD).
Unknown sources and invalid records cause failure with position-only errors.
Empty queries and null result counts remain observable. Dates are inclusive under
`--since`; all records are validated even when the filter excludes them.

The importer assigns positions local to the source-ordered export. They do not
represent user IDs, database IDs, chronological order, or sessions. Annotation
files are bound to the export SHA256 and sampling configuration.

## Collection for evaluation

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

The example illustrates structure only. Supply an actual corpus hash for a real
run. `group_id` is an independent target/task family: keep all paraphrases in the
same group. `track` is `human`, `agent`, or `unknown`, based on task provenance,
not inferred from source. `answerability` is `answerable`, `unanswerable`, or
`unknown`. An answerable query requires at least one grade >= 2; unanswerable
queries cannot have such a judgment. Grades are integers 0..3.

Optional `premise_routes` is a list of routes, each a list of groups, each a list
of interchangeable relevant document IDs:

```json
{"premise_routes": [[["lemmaA", "equivalentA"], ["lemmaB"]], [["lemmaC"]]]}
```

Here either A (or its equivalent) plus B, or C alone, completes an annotated route.
Every referenced premise must have a relevant judgment. This representation is
not an automatic interpretation of upstream MathlibMPR groups.

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

Document order is rank order. IDs must resolve to the declared corpus. Corpus
membership is a collection-building responsibility; the scorer verifies revision
equality, not an external index. `max_k` is the engine's requested/retrievable
depth, not the longest successful response. Cutoffs beyond it are unavailable.

Status is `ok`, `error`, or `timeout`. Failed requests have no documents.
Omitted query IDs become `missing` failures, not exclusions. Explicit abstention
requires a successful response with no documents; an empty response alone is not
an abstention. Optional latency/cost must be finite and nonnegative. Missing
measurements stay missing, not zero. Record end-to-end latency including retries
consistently; the scorer reports measurement counts alongside quantiles.

## Evaluation output

The output contains per-query scores, group and track metadata, status, supplied
cost/latency, and separate all/human/agent/unknown summaries. Each metric carries
its own denominator. A collection hash prevents comparing different judgments
under the same corpus revision. The overall mean is a descriptive query mean;
it is not traffic-weighted or population-weighted.

The comparison output reports candidate-minus-baseline difference, a 95% cluster
bootstrap interval, a two-sided paired group-randomization p-value, sample size,
seed, query count, and independent-group count. It refuses mismatched collections,
unequal metric coverage, or fewer than two independent groups. Two groups permit
calculation but do not provide a persuasive experiment; the demo is not evidence.

No automatic multiple-comparison correction is applied by `compare`. Use the
provided `holm` function on the planned comparison family. No annotation-agreement,
power analysis, traffic weighting, or Lean verification is implied by these files.

## Local annotations

The review output stores metadata and an object keyed by export position. Labels
cover intent, actor, certainty, evidence, language, and expected output, plus
channel and stratum population/sample counts. It stores no query text. These
positions still link to private data: keep annotations private. Two reviewers
must use different files. The original label files are retained for adjudication.
