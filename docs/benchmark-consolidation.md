# Benchmark tools

The repository contains query-log analysis, standalone offline evaluation tools
and candidate-selection experiment code.

The offline tools live under [tools/offline](../tools/offline/README.md).
Their migration inventory records source-code provenance. The original report
builder and evaluator interfaces remain available.

The [benchmark workflow](../tools/offline/docs/benchmark-workflow.md) adds corpus
membership checks, split audits and blinded review exports. It consumes external
inputs and preserves unreviewed cases without creating relevance labels.

[Candidate-selection tools](../experiments/candidate_selection/README.md)
include a runner, invented index fixtures and an engine preparation patch.

## Repository contents

Keep benchmark inputs, annotations, source inventories, hashes of inputs,
measured outputs and reports outside Git checkouts. Source code and
documentation use generic contracts. Tests construct invented records.

The publication check permits code, method documentation and a small explicit
set of source-migration and patch artifacts. It rejects data directories and
data formats even when renamed into a documentation subtree. Content review is
still necessary: a source-file extension cannot prove that its text is suitable
for publication.

Existing upstream history is not rewritten by this change.

## Published review records

Publish calibration decisions and aggregate progress reports as Markdown.
Include only the public or synthetic cases needed to explain a method decision.
Use impersonal instructions and preserve the distinction between accepted
judgments and unresolved proposals. Keep raw datasets, full annotation exports,
private query logs, model artifacts and measured run files outside Git checkouts.