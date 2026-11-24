# Assisted benchmark v2: weeks 1 through 4

Use assisted-v2 as the completed four-week diagnostic pilot. Report AI label provenance and keep independent human validation pending until its review targets are resolved. Use the measured scope of 20 development cases and 30 test requests; the initial 100-case development target was reduced. Keep optional model training and translation experiments outside these results.

| Period | Completed artifact | Human follow-up |
| --- | --- | --- |
| Week 1 | Corpus/model manifests, 20-case development pilot, rubric, pooling, accepted-decision provenance and baseline diagnostics | Relevance calibration and source-family review |
| Week 2 | Eight retrieval configurations, fixed-pool reranker comparisons, representation controls, source screening and extraction contract | Judgment validity, source attribution and mathematical interpretation |
| Week 3 | Frozen 30-query test, full pinned types for 37 declarations, seven Lean preservation theorems, incremental-cache implementation and external reference evaluation | Specification and upstream semantic/provenance review |
| Week 4 | Final scores, 946-query reference condition, dataset card, complete manuscript/PDF, portable score reconstruction, hash manifest and review register | Independent human validation, authorship, redistribution and submission decisions |

## Measured scope

There are 20 development and 30 test requests, with 19 and 26 entering relevance means. The assisted label set has 759 AI proposals and four prior accepted human decisions. Twenty-three pair records belong to the excluded invalid development case; nine remain unresolved. The four unknown test cases remain visible. No human acceptance has been manufactured.

On the same ten test candidates, Success@1 changes from 0.192 to 0.462 and nDCG@10 from 0.481 to 0.652. Success@10 remains 0.692. The first result changes in 26/30 test requests and 18/20 development requests. The response is an ordered list of Lean declarations. These figures are descriptive under AI-assisted labels.

MathlibQR now has a complete external run, with 946 variants and 200 target groups. All 946 scheduled queries have final records. There are 0 final request errors. Its original shared171 slice has 810 queries; the present-only slice has 927. Four names are absent from the local corpus. The external condition uses 100 reranker candidates, separately frozen from the ten-candidate pilot.

| Slice | nDCG@10 | Recall@10 | Recall@100 |
| --- | ---: | ---: | ---: |
| Full 946 | 0.390 | 0.572 | 0.754 |
| Original shared171 / 810 | 0.398 | 0.583 | 0.769 |
| Present only | 0.398 | 0.584 | 0.769 |

This is a local-corpus evaluation with upstream single-gold labels. It is not a replication of published cross-engine scores. Query-micro and target-macro estimates, target-group bootstrap intervals and per-style results are retained. The metric implementation matches the upstream functions on 560 boundary comparisons.

The first 402 reference responses were retained across an administrative restart to reduce checkpoint IO. One in-flight request was cancelled and then re-executed. Both source versions, the partial checkpoint, cancellation log and continuation provenance are included. There were 946 finalized scheduled requests plus that cancelled attempt; automatic retries within each process were disabled.

## Parser and cache result

The Lean 4.32.0 normalization module has seven kernel-checked theorems, without `sorry` or custom axioms. Its executable preserves all 37 pinned records and passes twelve runtime fixtures. The proof covers decoded-record preservation, environment, count/order, uniqueness and aliases. Upstream semantic correctness, the adapter, JSON, hashing and IO remain trusted. This is a bounded verified component, not a general Lean frontend.

The manual cache implements all five effective-input layers. Its two-revision fixture covers 351 Mathlib modules, reuses 349 per-layer artifacts and invalidates two after a dependency change. No-change snapshots reuse everything. Twenty-six tests cover configuration changes, deletion/rename, corruption and failed publication. The fixture builders record inputs rather than executing models, so the release makes no production speedup claim.

## Validation and artifacts

The final checks comprise 56 offline tests, 38 candidate/runner/scoring tests and 31 metadata/cache tests: 125 tests, plus 15 subtests. Strict typing passes for the 16 offline source modules. Targeted lint, source-only publication checks, Lean proof checks and release integrity checks are recorded separately. Both 30-query pilot inference runs agree exactly; external-reference scores are reconstructed from the complete recorded schedule.

Use the external assisted-v2 package for raw evidence and score reconstruction. Open `benchmark-report.html` within that package to inspect all 50 pilot responses, 946 reference comparisons and 850 human targets. Read [reproduction instructions](benchmark-reproduction.md) before running inference or changing labels. Keep raw inputs, annotations, model assets and run files outside Git.

The [dataset card](dataset-card.md) records intended use, labels, exposure and redistribution status. The [manuscript](preprint.md) reports the complete methods and results. The [human workflow](assisted-human-review.md) describes accepted corrections and rescores. The [extraction contract](extraction-boundary.md) separates proved properties from trusted components.

## Complete independent review

The 850-target registry preserves the previous 844 targets and adds HC-NORMALIZATION-SPEC, HC-CACHE-SPEC, HC-REDISTRIBUTION, HC-MANUSCRIPT, HC-REFERENCE-PROTOCOL and HC-SUBMISSION. Start with HC-D20 and HC-T18, HC-T26, HC-T27, HC-T29, then review positive and difficult negative judgments and the cross-cutting checks. The four historical human decisions are retained and do not need to be silently replaced.

Require explicit human decisions for independent validation, source rights, authorship and submission. Keep these targets open after automated tests and proof checks. Treat reranker fine-tuning, new-model informalization and production cache integration as separate experiments; no results for them are included.
