# Benchmark consolidation

The repository now contains the existing database analysis, the standalone
offline tools from `shalashaska117/leanexplore-benchmark`, and the candidate
selection pilot.

## Offline tools

All 26 tracked files from source commit
`8330c10` were imported under [tools/offline](../tools/offline/README.md).
The [migration inventory](../tools/offline/migration.json) records the full
source commit and original file hashes. Documentation and the publication
checker are adapted to the new location.

This includes the report builder and HTML template, annotation interface,
retrieval evaluator and paired comparisons, public-data downloader, synthetic
tests, data contracts, protocol, research sources and the dated telemetry
privacy assessment. The latter remains a planning document from October
2026, with its original scope and caveats.

The standalone layout preserves the Python-only report command:

```sh
python tools/offline/benchmark.py --input /private/export.json --out /private/report
```

Installing `tools/offline` also preserves the `leq-bench` command. The existing
`leb-querylog` database workflow and its dependencies are unchanged.

## Candidate selection

[experiments/candidate_selection](../experiments/candidate_selection/README.md)
contains the runner, synthetic tests, the engine integration patch, the
12 public pilot queries, all 288 measured records and reproduction manifests.

Published result files replace absolute machine paths with relative labels.
Metric values, candidate counts, target ranks, timings and source hashes are
preserved. Large corpus/model assets are referenced by revision and checksum;
the reproduction helper downloads them outside the repository.

## Publication scope

Private query exports, annotations, export-derived reports and input hashes
are not part of this migration. Source repository histories, local environments,
model weights and database/index files are not imported.

The publication check allows source and documentation plus an explicit set of
reviewed public artifacts with fixed checksums. Adding another result file
requires reviewing its source and updating that list. Path and checksum checks
supplement a content review; they cannot determine whether arbitrary prose
contains private information.

Original repositories and worktrees remain intact. The integration branch
does not deploy the engine patch. The matching app change is in the private
`lean-explore-app` repository (lean-explore/lean-explore-app#66).
