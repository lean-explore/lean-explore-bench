# Offline query analysis and retrieval evaluation

Code for rebuilding a query analysis and offline report from a private JSON
export. Python 3.10 or later is the only requirement. No installation, API key,
model, database connection or network access is needed.

From this tool directory:

```sh
python benchmark.py --input /path/to/private-export.json --out /path/outside/repository/report
```

Open `index.html` in the chosen output directory. Quote paths that contain
spaces. Use `python3` if that is your Python command.

The command rebuilds full-export, first-day and later-day views; per-channel
comparisons; request-weighted and distinct-request views; query length and form;
repetition; daily volume; and detailed audits. It writes local aggregate HTML,
CSV and JSON plus a reproduction manifest.

The same input and code produce the same report on Windows and Linux.
The local manifest records input and source hashes and the Python version.
Those manifests stay outside the repository.

## Tool contents

This tool directory contains code, tests and documentation of the method only.
It contains no private export, query records, dataset files, measured results,
aggregate reports, input fingerprints or annotations. Tests construct invented
inputs in code; no test fixture comes from usage logs.

Keep private inputs and generated outputs outside the checkout. Git ignores data and
report files, and `scripts/check_publication.py` rejects data files in the Git
index. That path check supplements a content review; it cannot prove that prose
contains no private information.

The report describes the supplied workload. Scoring search quality requires
separate relevance judgments and ranked engine outputs.

## Method and tools

- [Input contracts](docs/data-contract.md).
- [Benchmark protocol](docs/protocol.md).
- [Research sources](docs/sources.md).
- [Search telemetry: privacy and legal assessment](docs/search-telemetry-privacy.md).
- A local annotation interface with stratified sampling.
- A retrieval evaluator and paired statistical comparisons.
- An optional downloader for public reference tasks, stored locally and ignored
  by Git.

Counts in local reports are rounded to tens. Small cells and a complementary
cell are suppressed. Percentages use rounded counts. Missing categories are
unavailable, not zero. These measures reduce disclosure; they are not a formal
anonymity guarantee.

## Annotation and evaluation

The optional installed CLI provides additional commands:

```sh
python -m pip install -e .
leq-bench review --input /path/to/private-export.json --out /private/review.json --reviewer reviewer-1 --size 400 --seed 42
leq-bench evaluate --collection /private/collection.json --run /private/run.json --out /private/evaluation.json
leq-bench compare --collection /private/collection.json --run /private/run.json --baseline /private/baseline.json --metric ndcg@10 --out /private/comparison.json
```

The review interface runs on `127.0.0.1:8051`. Annotators should use separate
files with the same sample size and seed. The interface displays private query
text locally and saves labels linked to export positions. Keep those files
private. No command sends query text to an external service.

The evaluator's outputs can contain task identifiers. They also stay outside
the repository.

## Validation

```sh
python scripts/check.py
python scripts/check_publication.py
```

The synthetic suite checks import validation, normalization, deduplication,
suppression, absence of input text in generated reports, evaluation metrics,
date boundaries and deterministic rebuilding.

With Node installed, check the logic of a locally generated report:

```sh
node scripts/check_report.js /path/outside/repository/report/index.html
```

That check exercises the report controls with a minimal document stub; it does
not check browser layout.

This tool was imported from the personal benchmark repository. See the
[consolidation note](../../docs/benchmark-consolidation.md) for provenance and
the public candidate-selection results elsewhere in this repository.
