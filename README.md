# lean-explore-bench

A benchmark for search engines that find Lean 4 declarations in Mathlib.

It has 3,200 queries, each with one or more correct answers, in four equal buckets:
names and keywords, natural language, formal statements and proof states, and
questions from Lean Zulip threads. The score is the mean of the four buckets.

## Results

Each test query scores 1/n, where n is the position of the first correct result
among the first ten, and 0 if there is none (MRR@10). In brackets, the share of
queries where the first result is correct.

| Bucket | Lean Finder | LeanSearch | LeanExplore | BM25 |
| --- | ---: | ---: | ---: | ---: |
| Names and keywords | 0.82 (0.75) | 0.74 (0.62) | 0.66 (0.52) | 0.41 (0.29) |
| Natural language | 0.93 (0.88) | 0.82 (0.72) | 0.63 (0.48) | 0.21 (0.13) |
| Formal | 0.92 (0.89) | 0.79 (0.68) | 0.27 (0.14) | 0.46 (0.30) |
| Real questions | 0.64 (0.56) | 0.56 (0.45) | 0.36 (0.27) | 0.14 (0.10) |
| **Score** | **0.83 (0.77)** | **0.73 (0.62)** | **0.48 (0.35)** | **0.30 (0.20)** |

The three hosted engines were queried from 11 to 13 November 2026.

## Use it

```sh
pip install git+https://github.com/lean-explore/lean-explore-bench huggingface_hub
hf download lean-explore/lean-explore-bench --repo-type dataset --local-dir bench
leb score bench --engine myengine --split test
```

The last command scores `bench/runs/myengine.jsonl`, which you write: one line per
query in `bench/queries/test.jsonl`, with the declarations your engine returns.

```json
{"id": "a067a6f76126", "documents": ["dite_prop_iff_or", "dite_eq_ite"]}
```

## Know before comparing

- A correct answer that no engine above returned is not labelled, and counts as a
  miss. BM25's scores are lower bounds for this reason.
- Every answer existed in Mathlib before January 2026, so older indexes are not
  penalized.
- Queries and labels come from language models and are not yet reviewed by people.
- No search query from LeanExplore's users is in the benchmark.

## Where things are

| | |
| --- | --- |
| [Method](docs/method.md) | How the queries and answers were made |
| [Evaluation](docs/evaluation.md) | Grades, metrics, adding an engine |
| [Dataset card](docs/dataset-card.md) | Files and fields of the dataset |
| `src/lean_explore_bench/engines/` | One file per engine |
| `src/lean_explore_bench/builder/` | The code that built the benchmark |

Apache 2.0.
