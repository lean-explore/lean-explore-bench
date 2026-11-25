# Offline query analysis and retrieval evaluation

This tool turns a private JSON export of LeanExplore search requests into an aggregate report,
and scores ranked search results against relevance judgments. It needs only Python 3.10 or
later: no installation, API key, model, database or network access.

## Build the report

From this directory:

```sh
python benchmark.py --input /path/to/private-export.json --out /path/outside/repository/report
```

The output directory then contains:

| File | Content |
|---|---|
| `index.html` | Overview by time window, channel, query length and form, repetition and day |
| `summary.json`, `summary.csv` | The same aggregates as data |
| `manifest.json` | Input hash, source hashes and Python version |
| `full/`, `without-first-day/` | Detailed count tables for each window |

The same input and code give the same report. Counts are rounded to tens, and cells below ten
are suppressed together with one complementary cell.

## Other commands

`python -m pip install -e .` installs the `leq-bench` command.

```sh
leq-bench review --input /path/to/private-export.json --out /private/review.json --reviewer reviewer-1 --size 400 --seed 42
leq-bench evaluate --collection /private/collection.json --run /private/run.json --out /private/evaluation.json
leq-bench compare --collection /private/collection.json --run /private/run.json --baseline /private/baseline.json --metric ndcg@10 --out /private/comparison.json
```

`review` serves a labelling page for a stratified sample on `127.0.0.1:8051`. It shows query
text locally and saves only labels, keyed by export position. `evaluate` scores one run;
`compare` tests a run against a baseline. The [data contract](docs/data-contract.md) defines
the files, and the [benchmark workflow](docs/benchmark-workflow.md) covers `prepare`,
`adapt-run`, `pool` and `check-reviews`.

`python scripts/fetch_public_data.py` downloads the public LeanSearch v2 benchmark files into
the Git-ignored `data/public/leansearch-v2`. No other script uses the network.

## Checks

```sh
python scripts/check.py
python scripts/check_publication.py
node scripts/check_report.js /path/outside/repository/report/index.html
```

The first runs the tests, which use invented inputs. The second rejects data files in the Git
index. The third exercises a generated report's controls.

## Limits

- The report describes the supplied workload. Measuring search quality needs relevance
  judgments and ranked engine outputs.
- Rounding and suppression reduce disclosure; they are not an anonymity guarantee.
- Exports and all outputs are private and belong outside the checkout.

See also the [protocol](docs/protocol.md), [sources](docs/sources.md) and
[telemetry assessment](docs/search-telemetry-privacy.md).
