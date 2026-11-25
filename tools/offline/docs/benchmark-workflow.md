# Benchmark preparation and review

This workflow turns a file of benchmark cases into a scored evaluation: it checks the
train/development/test split, exports candidates for blind grading, validates the grades and
scores engine runs. All files are JSON and stay outside Git checkouts; the first four
commands refuse an output directory that exists or lies inside a checkout.

The commands need the `tools/offline` package installed. Alternatively,
`PYTHONPATH=tools/offline/src python -m leanexplore_benchmark` replaces `leq-bench`.

## Steps

1. Validate the cases and build the collection for one split.

   ```sh
   leq-bench prepare --cases /external/cases.json --corpus /external/corpus.json \
     --split development --out /external/prepared
   ```

   This writes `collection.json` (scorer input), `prepared.json` (the collection plus the
   full case records) and `split-audit.json`.

2. Convert engine observations into a run.

   ```sh
   leq-bench adapt-run --observations /external/observations.json \
     --collection /external/prepared/collection.json --corpus /external/corpus.json \
     --name baseline --max-k 10 --out /external/adapted
   ```

   This writes `run.json`. A case without a record counts as a missing request.

3. Export a candidate pool; `--run` may be repeated.

   ```sh
   leq-bench pool --prepared /external/prepared/prepared.json \
     --corpus /external/corpus.json --run /external/adapted/run.json \
     --depth 10 --seed 42 --out /external/review
   ```

   `packet.json` holds each query with its candidates (top results of every run, proposed
   targets, judged documents) in seeded order. Ranks go to `pool-audit.json`. Test cases are
   refused.

4. Validate an assessor's grades, then score.

   ```sh
   leq-bench check-reviews --packet /external/review/packet.json \
     --submission /external/assessor.json --out /external/validated-review
   leq-bench evaluate --collection /external/prepared/collection.json \
     --run /external/adapted/run.json --out /external/evaluation.json
   ```

   Validated grades remain proposals until they are entered in the case file as accepted
   reviews and step 1 is repeated.

## Input files

| File | Contents |
|---|---|
| Corpus | `corpus_revision`, Boolean `complete`, `documents` keyed by ID (optional `name`, `statement`, `context`, `module`), optional `aliases` from equivalent to canonical IDs |
| Cases | `schema_version: 1`, `corpus_revision`, `cases` |
| Observations | `corpus_revision`, `records` with `id`, `status`, ranked `documents`, optional `latency_ms`, `cost_usd`, `abstained` |
| Submission | `packet_sha256`, `reviewer`, `assessor_type`, `records` with `case_id`, `document_id`, `grade`, `uncertain`, `reason`, optional `minutes` |

Each case has `id`, `query`, `split` (train, development, test), `form` (name, keywords,
prose, formula, mixed), `track` (human, agent, unknown), a nonempty list `links` of source or
theorem-family keys, and Booleans `family_reviewed` and `test_exposed`. Optional fields are
`targets`, `answerability` (default unknown), `reviews` and `adjudications`.

A review has `id`, `document_id`, `reviewer`, `assessor_type` (human or assistant), `status`
(proposed, accepted, rejected), `grade` (0 to 3 or null), `uncertain` and `reason`.

## Rules the code enforces

- Cases that share a link, normalized query text or target form one group, and a group must
  lie in one split.
- A test case needs `family_reviewed: true` and `test_exposed: false`.
- Only accepted human reviews that are not uncertain become judgments. Proposed targets and
  assistant reviews do not.
- Conflicting accepted grades need an adjudication whose `review_ids` name every accepted
  review of that document.
- An unanswerable case needs an accepted `answerability_review`; an answerable case needs a
  grade of at least 2.

## Limits

The split audit cannot find an equivalence that nobody recorded. A missing target does not
show that a query has no answer.
