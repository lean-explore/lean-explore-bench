# lean-explore-bench

A benchmark for search engines that find Lean 4 declarations in Mathlib.

It has 3,200 queries, each with one or more correct answers, in four equal buckets:
names and keywords, natural language, formal statements and proof states, and
questions from Lean Zulip threads. The score is the mean of the four buckets.

## Results

Share of test queries with a correct answer in the first ten results, and in
brackets the share where the first result is correct.

| Bucket | Lean Finder | LeanSearch | LeanExplore | BM25 |
| --- | ---: | ---: | ---: | ---: |
| Names and keywords | 0.94 (0.75) | 0.93 (0.62) | 0.91 (0.52) | 0.66 (0.29) |
| Natural language | 0.98 (0.88) | 0.98 (0.72) | 0.86 (0.48) | 0.41 (0.13) |
| Formal | 0.96 (0.89) | 0.95 (0.68) | 0.54 (0.14) | 0.75 (0.30) |
| Real questions | 0.80 (0.56) | 0.77 (0.45) | 0.50 (0.27) | 0.24 (0.10) |
| **Score** | **0.92 (0.77)** | **0.91 (0.62)** | **0.70 (0.35)** | **0.52 (0.20)** |

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
