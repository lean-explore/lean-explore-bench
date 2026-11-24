# Benchmark preparation and review

The workflow reads external benchmark inputs and writes external artifacts.
The repository contains code and invented test fixtures. Keep queries, labels,
provenance records, corpus inventories, fingerprints and measured runs outside
Git checkouts. Outputs refuse existing directories.

Run the CLI with an installed `tools/offline` package, or set
`PYTHONPATH=tools/offline/src` and use `python -m leanexplore_benchmark`.

## Inputs

A corpus inventory has `corpus_revision`, a Boolean `complete`, and a
`documents` object keyed by canonical document ID. Optional `aliases` map an
equivalent ID directly to a canonical ID. Reject collisions and dangling aliases.
Document evidence can contain `name`, `statement`, `context` and `module`.
An incomplete inventory yields unresolved availability for missing IDs.

A benchmark input has `schema_version: 1`, `corpus_revision` and `cases`.
Each case requires:

- `id` and `query`;
- `split`: train, development or test;
- `form`: name, keywords, prose, formula or mixed;
- `track`: human, agent or unknown, based on the query's provenance;
- `links`: nonempty opaque source, original-request or theorem-family keys;
- `family_reviewed` and `test_exposed`: explicit Booleans.

Optional `targets` are proposed document IDs. Optional `provenance` and
generation metadata are preserved in the external sidecar. These fields do not
become relevance labels. `answerability` defaults to unknown.

The grouping audit takes connected components of shared links, normalized query
text and target identities, including aliases and reviewed documents. Text uses
Unicode NFC and whitespace normalization, preserving case. Every component must
have one split. Inspect large components: shared broad lemmas can over-connect
tasks. The audit cannot discover an equivalence that nobody recorded.

Test cases require reviewed family assignments and no exposure to development.
Reserve source and target families before generation or tuning. Hold test
families out of training examples while retaining their declarations in the
searchable corpus.

## Reviews and adjudication

Each entry in `reviews` contains `id`, `document_id`, `reviewer`,
`assessor_type` (human or assistant), `status` (proposed, accepted or rejected),
`grade` (integer 0..3 or null), `uncertain` and `reason`. Store assumptions,
formal-check evidence and measured minutes with the record when available.

Only explicitly accepted, resolved human judgments enter the scorer. This is a
data contract, not authentication of a claimed assessor identity. Assistant
proposals remain available for review. A missing target does not establish that
the information need has no answer.

Conflicting accepted labels require an entry in `adjudications`. It contains
the same assessor, status, evidence and grade fields, plus `review_ids`
referencing every accepted original label for that document. Original reviews
remain in the sidecar. Agreement statistics require independently collected
reviews; adjudication is not an independent second review.

An unanswerable case requires an accepted `answerability_review` using the
same assessor/status/uncertainty/reason fields. Its rationale must describe the
searched corpus and task scope. Answerable cases need a relevant accepted grade.
Unknown cases remain in operational denominators without relevance scores.

## Commands

Prepare one split:

```sh
leq-bench prepare --cases /external/cases.json --corpus /external/corpus.json \
  --split development --out /external/prepared
```

The output contains `collection.json`, `prepared.json` with the sidecar, and
`split-audit.json`. Every scored document must resolve in the pinned inventory.

Adapt observations:

```sh
leq-bench adapt-run --observations /external/observations.json \
  --collection /external/prepared/collection.json --corpus /external/corpus.json \
  --name baseline --max-k 10 --out /external/adapted
```

Observations have `corpus_revision` and a `records` list. Each record has
`id`, `status` and ranked `documents`; optional `latency_ms`, `cost_usd`
and `abstained` follow the evaluator contract. Preserve errors and timeouts.
Omitted scheduled cases remain missing requests. The adapter does not run an
engine, infer relevance, or silently lower the requested retrieval depth.

Export a candidate pool from one or more runs:

```sh
leq-bench pool --prepared /external/prepared/prepared.json \
  --corpus /external/corpus.json --run /external/adapted/run.json \
  --depth 10 --seed 42 --out /external/review
```

Use repeated `--run` arguments for different retrieval channels. The pool
deduplicates canonical documents, adds proposed targets and accepted labels,
and orders candidates by a seeded hash. `packet.json` contains the query and
document evidence. `pool-audit.json` separately retains rank, run bindings and
failure status. The development export refuses test cases.

First assess the information need without the candidate list. Then grade the
pairs while hiding rank and engine identity. Preserve unresolved labels.

An assessor submission contains `packet_sha256`, `reviewer`,
`assessor_type` and `records`. Each record contains `case_id`,
`document_id`, `grade`, `uncertain`, `reason` and optional measured
`minutes`. An uncertain record leaves its grade null.

```sh
leq-bench check-reviews --packet /external/review/packet.json \
  --submission /external/assessor.json --out /external/validated-review
leq-bench evaluate --collection /external/prepared/collection.json \
  --run /external/adapted/run.json --out /external/evaluation.json
```

Review validation verifies packet identity and pairs, then preserves the
submission as proposed. Acceptance and adjudication are explicit subsequent
decisions in the external case input. Rebuild the collection after those decisions.

## Calibration and reporting

Use five primary forms with a written tie-break: a bare declaration identifier
is a name; prose with essential code is mixed; a standalone mathematical or Lean
statement is formula; a short non-sentential request is keywords; remaining
natural-language requests are prose. Keep secondary tags. A formula containing
its target's name is not a name-free representation test.

Grade direct or equally usable equivalent answers as 3, answers requiring a
documented reasonable adaptation as 2, insufficient supporting results as 1,
and irrelevant or unusable results as 0. Check all hypotheses and types. A
supporting lemma can be sufficient in a separately defined premise-selection
task. Unknown is unjudged, not zero.

Report query counts, distinct task-family counts and query-document judgment
counts separately. Measure time for query assessment, pair judgments and
adjudication. Estimate remaining work from those measurements; if they are
missing, show scenarios rather than a claimed observed rate.

Freeze a protocol revision after calibration. Record label corrections, retain
the original submissions, and repeat affected development evaluations. Report
judgment coverage with metrics. Limit method comparisons to a prespecified set
and use family-grouped paired uncertainty estimates.
