---
license: cc-by-4.0
language:
  - en
pretty_name: lean-explore-bench
size_categories:
  - 1K<n<10K
task_categories:
  - text-retrieval
tags:
  - lean4
  - mathlib
  - theorem-proving
  - search
  - benchmark
configs:
  - config_name: queries
    default: true
    data_files:
      - split: test
        path: queries/test.jsonl
      - split: development
        path: queries/development.jsonl
  - config_name: runs
    data_files:
      - split: leanexplore
        path: runs/leanexplore.jsonl
      - split: leansearch
        path: runs/leansearch.jsonl
      - split: leanfinder
        path: runs/leanfinder.jsonl
      - split: loogle
        path: runs/loogle.jsonl
      - split: bm25
        path: runs/bm25.jsonl
---

# lean-explore-bench

A benchmark for search engines over Lean 4 declarations: 3,200 queries about Mathlib,
each with one or more graded answers. Version 1.

Code, method and scoring: <https://github.com/lean-explore/lean-explore-bench>.

## What it measures

A search engine receives a query and returns Lean declarations. A result is a hit
when it is a labelled answer of grade 2 or 3. The benchmark reports Success@10 and
Success@1 per bucket, and **the benchmark score is the plain mean of the four bucket
scores**.

| Bucket | Queries | Made of |
| --- | ---: | --- |
| Names and keywords | 800 | 160 `name`, 80 `names`, 240 `names+keywords`, 320 `keywords` |
| Natural language | 800 | 480 `prose`, 320 `prose+names` |
| Formal | 800 | 480 `formal` (statements and patterns), 320 `goal` (proof states) |
| Real questions | 800 | Queries derived from Lean Zulip threads |

There are 2,560 test queries and 640 development queries, a fifth of each bucket.
Tune only on the development split.

Every answer is a Mathlib declaration that has the same name and module in a
January 2026 snapshot, so that every engine compared can have indexed it.

## Loading

```python
from datasets import load_dataset

queries = load_dataset("lean-explore/lean-explore-bench", "queries", split="test")
runs = load_dataset("lean-explore/lean-explore-bench", "runs", split="leanexplore")
```

To score an engine, download the files and use the `leb-mix score` command of the
GitHub repository.

## Fields of `queries`

| Field | Content |
| --- | --- |
| `id` | Stable identifier. |
| `query` | The text sent to a search engine. |
| `bucket` | One of the four buckets. |
| `form` | `name`, `names`, `names+keywords`, `keywords`, `prose`, `prose+names`, `formal`, `goal`, or `question` for a thread query. |
| `variant` | How the query was made within its form, for example `typo` for a name query or `goal-only` for a proof state. |
| `split` | `test` or `development`. |
| `source` | `declaration` for a query written from a Mathlib declaration, `zulip` for one derived from a thread. |
| `area` | Area of Mathlib of the target, for example `Topology`. |
| `target` | The declaration the query was written for, or the best proposed answer of a thread. |
| `answers` | List of `{name, grade, pooled}`, best grade first. `pooled` marks an answer found by grading engine results. |
| `group_id` | Queries that share a group are not independent and are in the same split. |
| `method` | `language-model`, `programmatic` (name queries), `zulip-thread` or `contributed`. |
| `writer_model` | The model that wrote the query, when recorded. |
| `rewritten` | Whether the query is a reviewed rewrite of an earlier one. |
| `judge_model` | The model that accepted the query. |
| `pool_judge` | The model that graded the pooled answers, when there are any. |
| `thread_url` | Link to the Zulip thread, when recorded. |
| `writer_saw_answers` | For thread queries, whether the writer had seen the replies. |

Grades: 3 answers the query directly, 2 is usable after a clear adaptation, 1 is
related but not enough. Grades 2 and 3 count as hits.

## Fields of `runs`

One row per query and engine: `engine`, `id`, `status` (`ok` when the request
succeeded), `limit` (results requested), `documents` (declaration names, best
first) and `latency_ms`. LeanExplore, LeanSearch, Lean Finder and Loogle are the
hosted services, queried from 11 to 13 November 2026. BM25 is a baseline over the
name, documentation and source of every Mathlib declaration.

## Results

Success@10 on the test split, with Success@1 in brackets.

| Bucket | Lean Finder | LeanSearch | LeanExplore | BM25 | Loogle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Names and keywords | 0.94 (0.75) | 0.93 (0.62) | 0.91 (0.52) | 0.66 (0.29) | 0.07 (0.07) |
| Natural language | 0.98 (0.88) | 0.98 (0.72) | 0.86 (0.48) | 0.41 (0.13) | 0.00 (0.00) |
| Formal | 0.96 (0.89) | 0.95 (0.68) | 0.54 (0.14) | 0.75 (0.30) | 0.10 (0.10) |
| Real questions | 0.80 (0.56) | 0.77 (0.45) | 0.50 (0.27) | 0.24 (0.10) | 0.00 (0.00) |
| **Benchmark score** | **0.92 (0.77)** | **0.91 (0.62)** | **0.70 (0.35)** | **0.52 (0.20)** | **0.04 (0.04)** |

BM25 results were not graded for extra answers, so its scores are lower bounds.

## How it was made

- **Written queries (2,400).** A language model sees a Mathlib declaration drawn at
  random and writes a query of a given form and length. Forms and lengths follow
  counts taken from LeanExplore's search traffic. A judge from another model family
  must grade the target 3 and find the query specific to it. The 160 `name` queries
  are made by a program.
- **Real questions (800).** A language model rewrites the opening request of a Lean
  Zulip thread as one search query. The declarations named in the replies are
  proposed answers, and the query is kept when the judge grades one of them 2 or 3.
- **Pooled answers.** The first ten results of four engines were pooled for each
  query and 20,141 candidates were graded without engine or rank. This added 1,551
  answers to 984 queries.

The full method is in the
[repository](https://github.com/lean-explore/lean-explore-bench/blob/main/docs/method.md).

## Personal and private data

The dataset contains no search query from LeanExplore's users. The search log was
used only for aggregate counts of query form and length.

Thread queries are rewrites in new words. The dataset holds no text of any Zulip
post and no author name; a query that repeats more than five consecutive words of a
post was rejected. 210 queries carry a link to the public thread they came from.

## Limits

- Queries, acceptance and grades come from language models and have not been
  reviewed by people.
- Extra answers were found only among the results of four engines. A new engine can
  return a correct answer that is not labelled, and it counts as a miss until graded.
- The writer of a query is shown LeanExplore's natural-language description of the
  target, so written queries may share wording with LeanExplore's index. The real
  questions bucket does not have this bias.
- Every query has an answer, and every answer is in Mathlib as of January 2026.
- Hosted engines change. The runs describe each service on the dates given.

## Licence and citation

The dataset is released under CC BY 4.0. The answers are names of declarations in
Mathlib, which is under the Apache License 2.0.

```bibtex
@misc{asher2026leanexplorebench,
  title  = {A Benchmark for Lean 4 Declaration Search},
  author = {Asher, Justin and Pellegrino, Pietro},
  year   = {2026},
  url    = {https://github.com/lean-explore/lean-explore-bench}
}
```
