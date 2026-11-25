# lean-explore-bench

A benchmark for search engines over Lean 4 declarations.

It has 3,200 queries about Mathlib, each with one or more graded answers, in four
buckets of 800: names and keywords, natural language, formal statements and proof
states, and questions derived from Lean Zulip threads. The benchmark score is the
plain mean of the four bucket scores.

This is version 1. The queries and labels were produced with language models and
have not yet been reviewed by people; see [limits](docs/method.md#limits).

The data is published as a dataset at
[`lean-explore/lean-explore-bench`](https://huggingface.co/datasets/lean-explore/lean-explore-bench)
on Hugging Face. This repository holds the code that builds, runs and scores it.

## Results

Success@10 on the 2,560 test queries, with Success@1 in brackets. The four hosted
engines were queried from 11 to 13 November 2026.

| Bucket | Lean Finder | LeanSearch | LeanExplore | BM25 | Loogle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Names and keywords | 0.94 (0.75) | 0.93 (0.62) | 0.91 (0.52) | 0.66 (0.29) | 0.07 (0.07) |
| Natural language | 0.98 (0.88) | 0.98 (0.72) | 0.86 (0.48) | 0.41 (0.13) | 0.00 (0.00) |
| Formal | 0.96 (0.89) | 0.95 (0.68) | 0.54 (0.14) | 0.75 (0.30) | 0.10 (0.10) |
| Real questions | 0.80 (0.56) | 0.77 (0.45) | 0.50 (0.27) | 0.24 (0.10) | 0.00 (0.00) |
| **Benchmark score** | **0.92 (0.77)** | **0.91 (0.62)** | **0.70 (0.35)** | **0.52 (0.20)** | **0.04 (0.04)** |

BM25 results were not graded for extra answers, so its scores are lower bounds.
Loogle searches by name and pattern, so only bare names and some formal statements
suit it.

## Score an engine

```sh
pip install -e . huggingface_hub
hf download lean-explore/lean-explore-bench --repo-type dataset --local-dir bench
```

Write one line per query to `bench/runs/<name>.jsonl`, with the names of the
declarations your engine returns, best first:

```json
{"id": "prose-mathlib-010af69aea", "status": "ok", "limit": 10, "documents": ["dite_prop_iff_or", "dite_eq_ite"]}
```

Then score it:

```sh
leb-mix score --out bench --engine <name> --split test
```

Tune only on the development split (640 queries). A new engine can return correct
answers that are not labelled yet, and they count as misses until they are graded;
[evaluation](docs/evaluation.md#adding-an-engine) explains how to grade them.

`leb-mix run --engine leanexplore --out bench` queries one of the engines that the
package knows (`leanexplore`, `leansearch`, `leanfinder`, `loogle`).

## Documentation

| Document | Contents |
| --- | --- |
| [Method](docs/method.md) | Query forms, how queries and answers were made, limits |
| [Evaluation](docs/evaluation.md) | Relevance grades, metrics, splits, adding an engine |
| [Dataset card](docs/dataset-card.md) | Files and fields of the published dataset |
| [BM25 baseline](experiments/bm25_baseline/run.py) | The baseline with no learned component |
| [Paper](paper/README.md) | Draft of the paper |

## Privacy

No search query from LeanExplore's users is in the benchmark or in this repository.
LeanExplore's search log was used only to count how searches divide over query forms
and how long they are. `leb-mix profile --log` computes those counts on the server
that holds the log and writes shares only, leaving out any count under ten.
`.gitignore` and `scripts/check_publication.py` keep data files out of Git.

## Development

```sh
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest -q
```

Building the benchmark from scratch (`leb-mix generate`, `zulip`, `contribute`,
`build`, `pool`) needs a LeanExplore corpus snapshot and an `OPENROUTER_API_KEY`;
the steps are in [method](docs/method.md#building).

The code is under the Apache License 2.0.
