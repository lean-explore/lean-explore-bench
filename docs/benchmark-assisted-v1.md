# Assisted benchmark v1 methods and results

Report assisted-v1 within its measured scope: 20 development cases, 30 frozen test queries, eight retrieval configurations, representation controls and pinned declaration-type extraction. Independent human validation remains pending and is not claimed.

The release contains 763 usable query-document judgments: 4 prior accepted human decisions and 759 AI proposals. The review packets contain 786 pairs in total. Unresolved or excluded pairs remain in the review register. The register has 844 stable targets covering pairs, all 50 cases and cross-cutting release checks.

## Scope and denominators

Development has 19 quality-eligible cases out of 20. The original empty-index path-connected-union statement is false; its request remains in operational accounting and its original ranking is preserved. A repaired query needs a new version and run. Test has 26 cases with at least one proposed relevant answer out of 30. The remaining cases are test-18, test-26, test-27, test-29; no corpus-absence or correct-abstention claim follows from their negative pools.

All 30 test queries completed successfully twice. Final rankings and stage identities agree for all 30; reranker score comparison is recorded in the release verification. A prior reproduction attempt failed during artifact hashing because WSL ran out of memory. That failed attempt is retained. Latencies include diagnostic instrumentation and exact-name lookup, so they are not production serving latency.

The test was frozen before retrieval with configuration and query hashes. Queries were written from 30 scope-screened source requests, five retained and 25 replacements. Their wording is AI-authored prose, and source text sometimes contained theorem names or proofs. One earlier answer-link exposure is recorded. No test result was used to tune models, weights or prompts. The source-family inventory is provisional. After this release these queries are exposed and cannot be described as fresh holdout material.

## How the response changes

The response measured here is a ranked list of Lean declarations. With the same ten candidates, reranking changes the first result in 26/30 test queries and 18/20 development queries. The set of ten candidates is unchanged in this comparison, which explains the unchanged Success@10. The report contains all 50 before/after lists, proposed grades and the neural-only alternative.

### Test results

The relevance means below use 26 eligible cases. Query failures would count as zero on those cases; all 30 scheduled requests remain in request-success reporting.

| Configuration | Success@1 | Success@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.038 | 0.077 | 0.043 | 0.065 | 0.527 |
| dense | 0.500 | 0.731 | 0.570 | 0.670 | 0.535 |
| fusion | 0.231 | 0.731 | 0.401 | 0.512 | 0.996 |
| fusion_with_selection_boost | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| pre_rerank_same_pool | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| current_mixture | 0.462 | 0.692 | 0.553 | 0.652 | 1.000 |
| neural_only | 0.500 | 0.692 | 0.590 | 0.673 | 1.000 |
| without_final_dependency | 0.500 | 0.692 | 0.574 | 0.660 | 1.000 |

### Development results

The relevance means below use 19 eligible cases. These cases informed development and annotation policy.

| Configuration | Success@1 | Success@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.158 | 0.421 | 0.254 | 0.272 | 1.000 |
| dense | 0.526 | 0.947 | 0.667 | 0.721 | 1.000 |
| fusion | 0.158 | 0.895 | 0.439 | 0.512 | 1.000 |
| fusion_with_selection_boost | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| pre_rerank_same_pool | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| current_mixture | 0.263 | 0.895 | 0.514 | 0.560 | 1.000 |
| neural_only | 0.526 | 0.895 | 0.643 | 0.585 | 1.000 |
| without_final_dependency | 0.263 | 0.895 | 0.515 | 0.561 | 1.000 |

The channel rankings have partially judged top tens. Unjudged documents receive zero computational gain but are not accepted negatives. The fixed-pool comparison, known-positive stage survival and label-informed oracle are stored separately. No significance, independent-family confidence interval or superiority claim is made. The current mixture contains neural, lexical, fuzzy-name and dependency terms; neural-only is an ablation, not a newly trained model.

A separate calculation compares the original four accepted cases with their expanded AI labels on identical stored responses. It isolates label changes from engine changes. Full development averages have a different denominator and should not be read as a before/after improvement.

## Parser and mathematical-input diagnostics

The executable extractor exports full elaborated types, universe parameters, declaration kinds and expression representations for 37 declarations from Mathlib `aae61ae084c21995ee248964a81e3750ad0db2db` and `leanprover/lean4:v4.32.0`. It rejects missing or duplicate identities and open types. Both readable and explicit type renderings are retained. The implementation uses Lean's elaborated environment and does not parse incomplete source snippets into supposed full statements.

This export resolves the eight earlier type-evidence gaps and the generated-declaration gaps observed in the test pool. AI grades based on those types remain proposals. The exporter is not a proved normalization component or a general parser. Its trusted boundary and remaining proof target are documented in [the extraction contract](extraction-boundary.md), with `HC-EXTRACTION` for human inspection.

The existing mathematical-input probe retains 18 scored pairs: two controls, three variants and three representations. Four valid statements and two counterexamples were checked in Lean 4.35.0; the probe scores reproduce exactly across the two saved runs. This separate environment and synthetic scope do not certify retrieval accuracy on Mathlib. The 13 earlier development proof examples use Lean 4.32.0-rc1 and a different Mathlib revision; that evidence keeps its original environment identity.

## Weeks 1 and 2

| Work | Assisted-v1 disposition | Human follow-up |
| --- | --- | --- |
| W1 baseline and calibration | Local manifests, replay and all 419 development pairs screened. | `HC-CALIBRATION`, all development pair targets. |
| W1 corpus and scorer | Canonical inventory, split audit, pooling and provenance-preserving assisted scoring implemented. | `HC-FAMILY`, `HC-PROVENANCE`. |
| W1 scope and methods | Pilot held at 20 cases, interpretations and exclusions recorded. | Case targets `HC-D*`, `HC-TIMING`. |
| W2 sources and test | 30 test queries frozen and executed twice. | Case targets `HC-T01` through `HC-T30`. |
| W2 channel and reranker diagnosis | Eight configurations, 50/100-depth channel scores and fixed-pool oracle stored. | All relevance targets and `HC-ANSWER`. |
| W2 representations and extraction | 18-pair probe preserved; 37 pinned types exported. | `HC-EXTRACTION`. |
| W2 training specification | Input, sampling and training plan retained; fine-tuning is outside this benchmark. | Review relevance before training. |
| W2 closure | Report, checks registry, correction/rescore command and hash manifest delivered locally. | Independent validation and publication decisions remain separate. |

The imported reference has 946 variants in 200 target groups, with 196 target names present and four absent by name. It remains a reference mapping, not a replication of published evaluation results (`HC-REFERENCE`). Original corpus-build provenance and effective hosted-process configuration remain unavailable (`HC-PROVENANCE`). Annotation-time estimates remain scenarios until human time is measured (`HC-TIMING`).

## Reproduce and review

Use the external assisted-v1 artifact package. Open `benchmark-report.html` for the side-by-side results and searchable checks; `human-checks.json` is the machine-readable register. The `release` directory contains the delivery snapshot and manifest. Real queries, reviews and run data remain outside the source repository.

Start with uncertain case interpretations and the excluded development query, then review positive labels and the independent calibration subset, followed by negatives. Every target gives the evidence to inspect and a completion criterion. Four earlier human decisions retain precedence; they do not establish independent validation. Use [the human review guide](assisted-human-review.md) to record one decision at a time and see its effect on scores.

Validation: 56 offline tests, 21 candidate-diagnostic tests and five extraction validation tests pass. Strict offline typing and targeted lint checks pass. Reproduction and artifact hashes are recorded in the release verification.
