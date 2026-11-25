# Evaluation

How answers are graded, how an engine is scored, and how to add an engine.

## Relevance grades

Every labelled answer of a query has a grade.

| Grade | Meaning |
| ---: | --- |
| 3 | Directly answers the query, or is an equivalent result that is equally usable. |
| 2 | Usable after a clear, reasonable adaptation, such as specializing a more general result. |
| 1 | Related or supporting, but not enough for the task. |

A result is a **hit** when its grade is 2 or 3. Grade 1 labels are published but do
not count. A declaration with no label counts as a miss; this is a convention of the
scoring and does not show that the declaration is irrelevant.

An exact-name query is graded as a lookup: the answer is the declaration named, and
when a shortened name matches several declarations (at most five), each of them.

## Metrics

An engine is run on each query and its first ten results are kept.

| Metric | Definition |
| --- | --- |
| Success@10 | Share of queries with a hit in the first ten results. |
| Success@1 | Share of queries whose first result is a hit. |
| MRR@10 | Mean reciprocal rank of the first hit in the first ten results. |
| nDCG@10 | Graded ranking quality, with gain equal to the grade. |

Each metric is computed per bucket, and **the benchmark score is the plain mean of
the four bucket scores**. Buckets are not weighted by the traffic of any engine:
people send an engine what it handles well, so one engine's traffic favours that
engine.

Every query stays in the denominator. A failed or missing request counts as a miss.

Success@k and MRR are exact with respect to grading all ten results of the pooled
engines, because each engine's list was graded up to its first labelled answer.
nDCG@10 is not: results after the first hit may be unlabelled.

## Splits

A fifth of each bucket is the development split (640 queries) and the rest is the
test split (2,560). Two queries from one thread, and a query and its rewrite, are
always in the same split.

Tune only on the development split. Report test scores with the version of the
benchmark.

## Adding an engine

An engine that was not part of the pool can return correct answers that nobody has
graded. Before its score is compared with the published ones, its results up to the
first labelled answer should be graded and added.

1. Write the engine's results to `runs/<name>.jsonl`, one line per query:
   `{"id": ..., "documents": [names, best first]}`. A query with no line counts
   as a failed request. To have `leb run` do
   this, add a class to `lean_explore_bench.engines`.
2. Score it with `leb score DIR --engine <name> --split test`.
3. To grade its unlabelled results, export the candidates with
   `leb-build pool --out DIR --corpus lean_explore.db --shape balanced --established january.db --engine <name> --until-answer --to tasks.jsonl`,
   grade each candidate from 0 to 3 without looking at which engine returned it, and
   add the grades with `leb-build pool --out DIR --corpus lean_explore.db --grades grades.jsonl --judge NAME`.
   This step needs a build directory, the corpus snapshot and the January 2026
   snapshot that defines which declarations can be answers.

Hosted engines index their own snapshots of Mathlib and change over time. A score
describes a service on the dates it was queried.

## Comparing two runs

`lean_explore_bench.evaluate.compare` gives a paired difference between two runs
with a bootstrap interval and a randomization test.
