# Benchmark status

Updated 5 November 2026.

The technical workflow for preparing and reviewing a benchmark is ready on
`feat/benchmark-calibration`, in [PR #7](https://github.com/lean-explore/lean-explore-bench/pull/7).
The PR is still a draft. It has not been merged into `main` or deployed.

The benchmark is not yet ready for claims about search quality. Human relevance
judgments, review of related theorem families, and a final test set are still
needed.

## What is ready

- Corpus validation: checks the corpus version, document identities and aliases.
  Missing documents in an incomplete inventory remain unresolved.
- Case preparation: validates inputs and keeps linked cases in the same split.
  Test cases require reviewed family assignments and no development exposure.
- Run adaptation: converts ranked results into the evaluator format. Failed and
  missing requests remain in operational counts.
- Review packets: combine candidates from multiple runs, remove duplicates and
  hide engine names and ranks. A separate audit records how the pool was built.
- Review validation: checks that judgments belong to the assigned packet.
  Acceptance is explicit. Assistant proposals and unresolved labels are not
  scored as accepted human judgments.
- Offline evaluation: the existing evaluator computes ranking metrics and paired
  comparisons when the required judgments and runs are available.
- Supporting tools: local report generation, an annotation interface and
  candidate-selection experiment runners remain available.

The new commands are `prepare`, `adapt-run`, `pool` and `check-reviews`.
They connect to the existing `evaluate` command. The preparation and review
workflow has been exercised end to end.

## What has been checked

For the implementation in commit `3929440`:

- 116 main-package tests and 46 offline tests passed.
- Main-package test coverage was 100%.
- Lint, formatting and strict type checks passed for both packages.
- Both publication checks passed.
- All three CI jobs passed: `test`, `offline` and `candidate-selection`.

Tests cover invalid aliases, linked cases crossing splits, test exposure,
conflicting judgments, failed requests and review-packet identity. Passing these
checks establishes software behavior; mathematical validity still needs review.

## Publication scope

The repository contains code, method documentation and invented test fixtures.
Benchmark inputs, annotations, corpus inventories, input fingerprints and
measured outputs stay outside Git checkouts. The new workflow commands reject
outputs inside a Git checkout and refuse existing output directories.

Publication checks enforce allowed paths and file types. Content review is
still required. Removing files from the current branch does not remove them
from earlier Git history.

## What remains

1. Calibrate the relevance rubric with human reviewers and measure review time.
2. Review theorem families and equivalences before assigning the final test set.
3. Freeze a collection with accepted judgments and reproduce a baseline.
4. Compare retrieval methods at fixed budgets, then examine reranking on fixed
   candidate pools, including context completeness and truncation.
5. Complete build provenance and deployed-process verification before claiming
   an exact reproduction of the hosted service.

The extraction work is a specification of a bounded normalization step. A
general Lean parser and a formal correctness proof have not been implemented.
Fine-tuning and serving changes are outside this milestone.

## Documentation

- [Preparation and review workflow](../tools/offline/docs/benchmark-workflow.md)
- [Offline tools and evaluation](../tools/offline/README.md)
- [Candidate-selection experiments](../experiments/candidate_selection/README.md)
- [Extraction boundary](extraction-boundary.md)
- [Repository publication scope](benchmark-consolidation.md)
