# lean-explore-bench

A benchmark for search engines that find Lean 4 declarations in Mathlib.

You give your engine 3,200 queries, it returns ten declarations for each, and the
benchmark tells you how often a correct one is among them.

## What is in it

Each query has one or more correct answers. The queries are in four buckets of 800:

| Bucket | Example query |
| --- | --- |
| Names and keywords | `annihilator span singleton membership` |
| Natural language | `tail of interleaving two infinite streams` |
| Formal | `⊢ WithBot.succ x = ⊥ ↔ x = ⊥` |
| Real questions | Questions rewritten from Lean Zulip threads |

The score is the mean of the four buckets. 2,560 queries are the test split and 640
are the development split.

## Score your engine

1. Install the scorer and download the data. Scoring needs only Python 3.10 or later.

   ```sh
   pip install git+https://github.com/lean-explore/lean-explore-bench huggingface_hub
   hf download lean-explore/lean-explore-bench --repo-type dataset --local-dir bench
   ```

2. Run your engine on every query in `bench/queries/test.jsonl`. Each line is one
   query with its answers:

   ```json
   {"id": "a067a6f76126",
    "query": "dependent if-then-else on propositions is equivalent to an existential disjunction over both branches",
    "bucket": "natural language", "form": "prose", "split": "test",
    "answers": [{"name": "dite_prop_iff_or", "grade": 3}]}
   ```

3. Write your results to `bench/runs/myengine.jsonl`, one line per query, with the
   full names of the declarations you return, best first:

   ```json
   {"id": "a067a6f76126", "documents": ["dite_prop_iff_or", "dite_eq_ite"]}
   ```

4. Score it:

   ```sh
   leb score bench --engine myengine --split test
   ```

Tune on the development split only (`bench/queries/development.jsonl`).

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

Lean Finder, LeanSearch and LeanExplore are the hosted services, queried from 11 to
13 November 2026. Their results are in `bench/runs/`, so you can reproduce this
table with `leb score bench --engine leanfinder leansearch leanexplore bm25 --split test`.

## Before you compare scores

- **Your engine may be right where the labels are silent.** Extra answers were
  found by grading what the engines above returned. A correct declaration that none
  of them returned is not labelled and counts as a miss. This is why BM25's scores
  are lower bounds. [Evaluation](docs/evaluation.md#adding-an-engine) explains how
  to grade new results.
- **Answers predate January 2026.** Every answer is a Mathlib declaration that
  already existed then, so an engine with an older index is not penalized.
- **Labels come from language models.** Queries and grades have not been reviewed by
  people yet. This is version 1.

## More

- [Method](docs/method.md): how the queries and answers were made, and the limits.
- [Evaluation](docs/evaluation.md): grades, metrics, and adding an engine.
- [Dataset card](docs/dataset-card.md): the files and fields of the dataset.

No search query from LeanExplore's users is in the benchmark. The search log was
used only to count how long real searches are and what form they take.

To work on the code, run `pip install -e ".[dev]"`, then
`ruff check . && mypy && pytest -q`. Code that built the benchmark is in
`src/lean_explore_bench/builder/`. Licensed under Apache 2.0.
