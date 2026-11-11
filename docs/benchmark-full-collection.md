# Full collection benchmark

The local replay covers 33,075 distinct requests from 38,566 source records. It finished with 0 request errors and 2 empty result lists. Every supplied query was scheduled. Exact duplicates share one execution and retain every source membership.

This expands the earlier pilot to the full prepared query collections. Raw archive messages are source material, not additional benchmark queries. No query text, user identifiers, per-request results or input hashes are published here.

Read the [preprint](full-collection-preprint.md) for what these findings mean and which experiments they support. This report retains the detailed source and category tables.

## Coverage

| Collection | Source records / query variants | Distinct requests |
|---|---|---|
| Discussion-derived queries | 2,079 | 2,078 |
| MathlibQR | 946 | 945 |
| MathlibMPR | 138 | 138 |
| FATE-H | 200 | 200 |
| Synthetic discussion queries | 28 | 28 |
| Development pilot | 20 | 20 |
| Historical test requests | 30 | 30 |
| Candidate-selection pilot | 12 | 12 |
| Earlier calibration queries | 10 | 10 |
| Usage logs | 35,103 | 29,628 |

Source counts overlap where the same request belongs to several collections. Usage-log records include repeated searches. MathlibQR has 200 target groups; MathlibMPR has 69 problems and both natural-language and formal queries; FATE-H has 100 problems and both statement forms.

| Query form | Distinct requests |
|---|---|
| formula | 1,567 |
| keywords | 12,829 |
| mixed | 6,914 |
| name | 1,242 |
| prose | 10,523 |

The five forms use documented surface rules. The additional surface, intent-cue and domain-cue breakdowns below retain unknown categories. They are not human annotations or a refit of the earlier first-day Gaussian-mixture categories.

## Evaluation conditions

End-to-end instrumented baseline replay.

The run uses the pinned local LeanExplore engine and corpus, Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B. BM25 and dense retrieval each request 1,000 candidates. Selection operates on the top 500 fused candidates. The current mixture reranks 25 candidates and returns up to 25 results. Original package filters are retained. The external run manifest pins code, data and model inputs.

Eight diagnostic rankings are derived from each search: lexical, dense, fusion, selection, the same pool before reranking, the current mixture, neural-only scores, and the mixture without its final dependency term. Raw retrieval stages precede package filtering; only the same-pool comparisons isolate reranking. These are not eight independently executed search services.

The earlier pilot used ten reranker candidates and the earlier MathlibQR reference used 100. Their scores are separate conditions and are not pooled with this run.

Mean instrumented end-to-end time was 517.8 ms per distinct request. Reranking changed the first result relative to the selected pool's incoming order for 28,131 requests. Of 825,391 query-document pairs sent to the reranker, 33,269 exceeded its input limit. The journal records per-pair token counts.

## Results by collection and label type

Success means at least one recorded target appears in the cutoff; recall is the fraction of recorded targets recovered. nDCG uses binary relevance for those targets. Absent target names and failed requests remain in the denominator. These metrics do not establish that other results are irrelevant. Reply-link and historical-proposal scores are diagnostics, not validated relevance.

### Candidate-selection pilot: Historical proposed targets

12 source records; 12 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 16.67% | 33.33% | 33.33% | 0.2718 |
| Dense retrieval | 25.00% | 58.33% | 58.33% | 0.4122 |
| Rank fusion | 8.33% | 58.33% | 58.33% | 0.3483 |
| After candidate selection | 0.00% | 58.33% | 58.33% | 0.2735 |
| Selected pool, before reranking | 0.00% | 58.33% | 58.33% | 0.2863 |
| Final score mixture | 25.00% | 50.00% | 50.00% | 0.3859 |
| Neural score only | 16.67% | 50.00% | 50.00% | 0.3196 |
| Mixture without final dependency term | 25.00% | 50.00% | 50.00% | 0.3859 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 41.67% | 58.33% |
| Dense retrieval | 83.33% | 83.33% |
| Rank fusion | 66.67% | 91.67% |
| After candidate selection | 66.67% | 91.67% |

### Development pilot: Historical proposed targets

19 source records; 19 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 15.79% | 36.84% | 30.70% | 0.2538 |
| Dense retrieval | 31.58% | 52.63% | 49.12% | 0.3972 |
| Rank fusion | 10.53% | 57.89% | 53.51% | 0.3484 |
| After candidate selection | 0.00% | 57.89% | 53.51% | 0.2640 |
| Selected pool, before reranking | 0.00% | 57.89% | 53.51% | 0.2640 |
| Final score mixture | 15.79% | 52.63% | 46.49% | 0.2912 |
| Neural score only | 10.53% | 47.37% | 42.98% | 0.2650 |
| Mixture without final dependency term | 15.79% | 47.37% | 41.23% | 0.2737 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 30.70% | 37.72% |
| Dense retrieval | 71.93% | 80.70% |
| Rank fusion | 61.40% | 78.95% |
| After candidate selection | 61.40% | 77.19% |

### Development pilot: No target labels in replay inputs

1 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

### Earlier calibration queries: Historical proposed targets

9 source records; 9 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 33.33% | 44.44% | 38.89% | 0.3627 |
| Dense retrieval | 33.33% | 55.56% | 55.56% | 0.4590 |
| Rank fusion | 22.22% | 66.67% | 61.11% | 0.4330 |
| After candidate selection | 0.00% | 66.67% | 61.11% | 0.3069 |
| Selected pool, before reranking | 0.00% | 66.67% | 61.11% | 0.3069 |
| Final score mixture | 11.11% | 66.67% | 61.11% | 0.3118 |
| Neural score only | 0.00% | 55.56% | 50.00% | 0.2253 |
| Mixture without final dependency term | 11.11% | 55.56% | 50.00% | 0.2748 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 38.89% | 38.89% |
| Dense retrieval | 66.67% | 74.07% |
| Rank fusion | 66.67% | 70.37% |
| After candidate selection | 66.67% | 66.67% |

### Earlier calibration queries: No target labels in replay inputs

1 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

### FATE-H: No target labels in replay inputs

200 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

FATE-H remains a retrieval diagnostic; no proof-completion claim is made.

### MathlibMPR: Upstream alternative premise sets

138 source records; 138 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 2.17% | 10.14% | 5.15% | 0.0271 |
| Dense retrieval | 0.72% | 30.43% | 9.78% | 0.0595 |
| Rank fusion | 2.90% | 25.36% | 9.09% | 0.0482 |
| After candidate selection | 2.17% | 21.74% | 7.66% | 0.0395 |
| Selected pool, before reranking | 2.17% | 21.74% | 7.66% | 0.0395 |
| Final score mixture | 0.00% | 26.81% | 7.65% | 0.0426 |
| Neural score only | 4.35% | 27.54% | 8.10% | 0.0594 |
| Mixture without final dependency term | 0.00% | 29.71% | 8.40% | 0.0488 |

At least one complete recorded premise route appears in the top ten for 18.12% of queries. This checks premise retrieval; it does not prove the theorem.

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 14.64% | 28.29% |
| Dense retrieval | 37.44% | 62.33% |
| Rank fusion | 32.45% | 56.55% |
| After candidate selection | 32.35% | 48.79% |

### MathlibQR: Upstream single-target labels

946 source records; 946 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 11.21% | 20.61% | 20.61% | 0.1546 |
| Dense retrieval | 25.37% | 54.44% | 54.44% | 0.3925 |
| Rank fusion | 18.50% | 51.90% | 51.90% | 0.3468 |
| After candidate selection | 15.01% | 52.96% | 52.96% | 0.3217 |
| Selected pool, before reranking | 15.01% | 52.96% | 52.96% | 0.3217 |
| Final score mixture | 24.31% | 57.29% | 57.29% | 0.3961 |
| Neural score only | 15.22% | 52.01% | 52.01% | 0.3186 |
| Mixture without final dependency term | 21.99% | 54.44% | 54.44% | 0.3678 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 33.83% | 45.56% |
| Dense retrieval | 74.74% | 85.94% |
| Rank fusion | 72.94% | 85.52% |
| After candidate selection | 75.37% | 82.98% |

### Usage logs: No target labels in replay inputs

35,103 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

### Historical test requests: No target labels in replay inputs

30 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

These frozen test requests are included in full. Their historical graded judgments remain in the separately versioned assisted-v2 pilot reports; this replay does not convert them into a target list.

### Discussion-derived queries: Reply-link targets (unverified proxies)

2,079 source records; 2,079 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 3.13% | 7.89% | 5.75% | 0.0414 |
| Dense retrieval | 3.85% | 16.45% | 11.98% | 0.0748 |
| Rank fusion | 3.70% | 16.45% | 12.19% | 0.0741 |
| After candidate selection | 4.62% | 18.28% | 13.49% | 0.0831 |
| Selected pool, before reranking | 4.62% | 18.28% | 13.49% | 0.0831 |
| Final score mixture | 6.01% | 21.07% | 15.42% | 0.1012 |
| Neural score only | 4.67% | 20.01% | 14.53% | 0.0921 |
| Mixture without final dependency term | 3.42% | 19.53% | 14.37% | 0.0832 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 13.09% | 25.46% |
| Dense retrieval | 28.52% | 49.14% |
| Rank fusion | 28.12% | 46.41% |
| After candidate selection | 29.73% | 41.21% |

### Synthetic discussion queries: Historical proposed targets

26 source records; 26 with recorded targets; 0 request errors.

| Ranking | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| Lexical retrieval | 0.00% | 0.00% | 0.00% | 0.0000 |
| Dense retrieval | 19.23% | 26.92% | 22.44% | 0.1929 |
| Rank fusion | 3.85% | 23.08% | 18.59% | 0.1325 |
| After candidate selection | 3.85% | 23.08% | 18.59% | 0.1143 |
| Selected pool, before reranking | 3.85% | 23.08% | 18.59% | 0.1143 |
| Final score mixture | 7.69% | 30.77% | 26.28% | 0.1747 |
| Neural score only | 3.85% | 30.77% | 26.28% | 0.1317 |
| Mixture without final dependency term | 3.85% | 30.77% | 26.28% | 0.1663 |

| Raw retrieval stage | Known-target recall@100 | Known-target recall@1000 |
|---|---|---|
| Lexical retrieval | 7.69% | 30.77% |
| Dense retrieval | 53.85% | 76.28% |
| Rank fusion | 50.00% | 80.13% |
| After candidate selection | 51.92% | 73.08% |

### Synthetic discussion queries: No target labels in replay inputs

2 source records; 0 with recorded targets; 0 request errors.

No target labels are present in this collection's replay inputs. The run records retrieval results, failures and ranking changes.

## Results by category

The following tables use the current mixture. Repeated source records retain their frequency; the coverage table separately shows distinct requests. Usage-log category cells with fewer than ten records are suppressed. Metrics are never pooled across label types.

Top-1 changes in these tables compare each condition with its candidate pool's order before reranking. The preprint reports the separate paired comparison between the original and corrected implementations.

Upstream domain tags can overlap: a FATE-H query contributes to each of its recorded tags.

### Form

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Candidate-selection pilot | keywords | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Candidate-selection pilot | name | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Candidate-selection pilot | prose | 6 | 50.00% | 0.3333 | 0 | 100.00% | 83.33% |
| Development pilot | formula | 6 | 33.33% | 0.1273 | 0 | 100.00% | 83.33% |
| Development pilot | keywords | 3 | 33.33% | 0.1111 | 0 | 100.00% | 100.00% |
| Development pilot | mixed | 2 | 100.00% | 0.6577 | 0 | 100.00% | 100.00% |
| Development pilot | name | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Development pilot | prose | 4 | 50.00% | 0.1224 | 0 | 100.00% | 100.00% |
| Development pilot | formula | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Earlier calibration queries | formula | 2 | 50.00% | 0.1667 | 0 | 100.00% | 50.00% |
| Earlier calibration queries | keywords | 2 | 50.00% | 0.1667 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | mixed | 1 | 100.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | name | 2 | 100.00% | 0.8155 | 0 | 100.00% | 50.00% |
| Earlier calibration queries | prose | 2 | 50.00% | 0.0967 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | formula | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | formula | 102 | unlabelled | unavailable | 0 | 100.00% | 92.16% |
| FATE-H | mixed | 83 | unlabelled | unavailable | 0 | 100.00% | 89.16% |
| FATE-H | prose | 15 | unlabelled | unavailable | 0 | 100.00% | 73.33% |
| MathlibMPR | formula | 70 | 28.57% | 0.0500 | 0 | 100.00% | 77.14% |
| MathlibMPR | mixed | 55 | 25.45% | 0.0354 | 0 | 100.00% | 81.82% |
| MathlibMPR | prose | 13 | 23.08% | 0.0328 | 0 | 100.00% | 76.92% |
| MathlibQR | formula | 157 | 48.41% | 0.3234 | 0 | 100.00% | 91.72% |
| MathlibQR | keywords | 197 | 69.54% | 0.4747 | 0 | 100.00% | 77.16% |
| MathlibQR | mixed | 214 | 49.07% | 0.3288 | 0 | 100.00% | 86.92% |
| MathlibQR | prose | 378 | 59.26% | 0.4234 | 0 | 100.00% | 83.07% |
| Usage logs | formula | 582 | unlabelled | unavailable | 0 | 100.00% | 90.55% |
| Usage logs | keywords | 16,214 | unlabelled | unavailable | 0 | 99.99% | 86.33% |
| Usage logs | mixed | 6,714 | unlabelled | unavailable | 0 | 99.99% | 84.73% |
| Usage logs | name | 1,543 | unlabelled | unavailable | 0 | 100.00% | 71.61% |
| Usage logs | prose | 10,050 | unlabelled | unavailable | 0 | 100.00% | 87.00% |
| Historical test requests | formula | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | mixed | 10 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | prose | 19 | unlabelled | unavailable | 0 | 100.00% | 84.21% |
| Discussion-derived queries | formula | 854 | 16.04% | 0.0721 | 0 | 100.00% | 87.82% |
| Discussion-derived queries | keywords | 2 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Discussion-derived queries | mixed | 151 | 19.21% | 0.0967 | 0 | 100.00% | 88.08% |
| Discussion-derived queries | prose | 1,072 | 25.37% | 0.1252 | 0 | 100.00% | 85.54% |
| Synthetic discussion queries | formula | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | keywords | 2 | 50.00% | 0.3155 | 0 | 100.00% | 50.00% |
| Synthetic discussion queries | mixed | 5 | 40.00% | 0.1602 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | prose | 18 | 27.78% | 0.1728 | 0 | 100.00% | 94.44% |
| Synthetic discussion queries | mixed | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | prose | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Surface

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Candidate-selection pilot | identifier only | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Candidate-selection pilot | other text | 8 | 37.50% | 0.2500 | 0 | 100.00% | 87.50% |
| Development pilot | identifier only | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Development pilot | mixed identifier text | 1 | 100.00% | 1.0000 | 0 | 100.00% | 100.00% |
| Development pilot | other text | 7 | 42.86% | 0.1175 | 0 | 100.00% | 100.00% |
| Development pilot | proof state or statement | 4 | 0.00% | 0.0000 | 0 | 100.00% | 75.00% |
| Development pilot | symbolic expression | 3 | 100.00% | 0.3598 | 0 | 100.00% | 100.00% |
| Development pilot | proof state or statement | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Earlier calibration queries | identifier only | 2 | 100.00% | 0.8155 | 0 | 100.00% | 50.00% |
| Earlier calibration queries | other text | 4 | 50.00% | 0.1317 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | proof state or statement | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Earlier calibration queries | symbolic expression | 2 | 100.00% | 0.3244 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | proof state or statement | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | latex present | 78 | unlabelled | unavailable | 0 | 100.00% | 89.74% |
| FATE-H | mixed identifier text | 3 | unlabelled | unavailable | 0 | 100.00% | 66.67% |
| FATE-H | other text | 14 | unlabelled | unavailable | 0 | 100.00% | 71.43% |
| FATE-H | proof state or statement | 100 | unlabelled | unavailable | 0 | 100.00% | 92.00% |
| FATE-H | question like | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | symbolic expression | 4 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| MathlibMPR | mixed identifier text | 22 | 36.36% | 0.0540 | 0 | 100.00% | 68.18% |
| MathlibMPR | other text | 6 | 33.33% | 0.0354 | 0 | 100.00% | 83.33% |
| MathlibMPR | proof state or statement | 69 | 27.54% | 0.0468 | 0 | 100.00% | 76.81% |
| MathlibMPR | question like | 7 | 14.29% | 0.0306 | 0 | 100.00% | 71.43% |
| MathlibMPR | symbolic expression | 34 | 20.59% | 0.0303 | 0 | 100.00% | 91.18% |
| MathlibQR | latex present | 201 | 51.74% | 0.3483 | 0 | 100.00% | 91.04% |
| MathlibQR | mixed identifier text | 62 | 41.94% | 0.2601 | 0 | 100.00% | 82.26% |
| MathlibQR | other text | 554 | 63.72% | 0.4451 | 0 | 100.00% | 80.69% |
| MathlibQR | question like | 21 | 38.10% | 0.3316 | 0 | 100.00% | 90.48% |
| MathlibQR | symbolic expression | 108 | 47.22% | 0.3242 | 0 | 100.00% | 88.89% |
| Usage logs | identifier only | 1,543 | unlabelled | unavailable | 0 | 100.00% | 71.61% |
| Usage logs | latex present | 31 | unlabelled | unavailable | 0 | 100.00% | 80.65% |
| Usage logs | mixed identifier text | 6,398 | unlabelled | unavailable | 0 | 99.98% | 84.34% |
| Usage logs | other text | 26,123 | unlabelled | unavailable | 0 | 100.00% | 86.57% |
| Usage logs | proof state or statement | 84 | unlabelled | unavailable | 0 | 100.00% | 77.38% |
| Usage logs | question like | 141 | unlabelled | unavailable | 0 | 100.00% | 90.07% |
| Usage logs | symbolic expression | 783 | unlabelled | unavailable | 0 | 100.00% | 93.23% |
| Historical test requests | mixed identifier text | 3 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | other text | 14 | unlabelled | unavailable | 0 | 100.00% | 85.71% |
| Historical test requests | question like | 5 | unlabelled | unavailable | 0 | 100.00% | 80.00% |
| Historical test requests | symbolic expression | 8 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Discussion-derived queries | latex present | 89 | 23.60% | 0.1144 | 0 | 100.00% | 87.64% |
| Discussion-derived queries | mixed identifier text | 56 | 14.29% | 0.0812 | 0 | 100.00% | 87.50% |
| Discussion-derived queries | other text | 17 | 11.76% | 0.0599 | 0 | 100.00% | 76.47% |
| Discussion-derived queries | proof state or statement | 851 | 15.98% | 0.0719 | 0 | 100.00% | 87.78% |
| Discussion-derived queries | question like | 1,057 | 25.54% | 0.1261 | 0 | 100.00% | 85.53% |
| Discussion-derived queries | symbolic expression | 9 | 11.11% | 0.0215 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | mixed identifier text | 3 | 33.33% | 0.1003 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | other text | 19 | 26.32% | 0.1646 | 0 | 100.00% | 89.47% |
| Synthetic discussion queries | question like | 1 | 100.00% | 0.6131 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | symbolic expression | 3 | 33.33% | 0.1667 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | mixed identifier text | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | question like | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Upstream style

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| FATE-H | Formal statement | 100 | unlabelled | unavailable | 0 | 100.00% | 92.00% |
| FATE-H | Informal statement | 100 | unlabelled | unavailable | 0 | 100.00% | 87.00% |
| MathlibMPR | Natural-language main result | 69 | 26.09% | 0.0383 | 0 | 100.00% | 81.16% |
| MathlibMPR | Formal statement | 69 | 27.54% | 0.0468 | 0 | 100.00% | 76.81% |
| MathlibQR | Lean statement | 199 | 45.73% | 0.3027 | 0 | 100.00% | 85.43% |
| MathlibQR | LaTeX statement | 200 | 56.50% | 0.4064 | 0 | 100.00% | 91.50% |
| MathlibQR | Natural-language statement | 199 | 59.80% | 0.4284 | 0 | 100.00% | 83.42% |
| MathlibQR | Short description | 197 | 60.41% | 0.3936 | 0 | 100.00% | 83.76% |
| MathlibQR | Nickname | 128 | 72.66% | 0.5220 | 0 | 100.00% | 71.88% |
| MathlibQR | Special case | 23 | 30.43% | 0.1551 | 0 | 100.00% | 86.96% |

### Difficulty

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| MathlibQR | Easy | 472 | 58.69% | 0.4041 | 0 | 100.00% | 82.84% |
| MathlibQR | Hard | 474 | 55.91% | 0.3881 | 0 | 100.00% | 85.44% |

### Intent cue

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Candidate-selection pilot | known item candidate | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Candidate-selection pilot | unknown | 8 | 37.50% | 0.2500 | 0 | 100.00% | 87.50% |
| Development pilot | discovery | 1 | 100.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Development pilot | known item candidate | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Development pilot | multiple cues | 4 | 0.00% | 0.0000 | 0 | 100.00% | 75.00% |
| Development pilot | proof support | 1 | 100.00% | 1.0000 | 0 | 100.00% | 100.00% |
| Development pilot | unknown | 9 | 55.56% | 0.1763 | 0 | 100.00% | 100.00% |
| Development pilot | unknown | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Earlier calibration queries | discovery | 1 | 100.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | known item candidate | 2 | 100.00% | 0.8155 | 0 | 100.00% | 50.00% |
| Earlier calibration queries | multiple cues | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Earlier calibration queries | unknown | 5 | 60.00% | 0.1720 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | unknown | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | enumeration | 1 | unlabelled | unavailable | 0 | 100.00% | 0.00% |
| FATE-H | proof support | 49 | unlabelled | unavailable | 0 | 100.00% | 83.67% |
| FATE-H | unknown | 150 | unlabelled | unavailable | 0 | 100.00% | 92.00% |
| MathlibMPR | discovery | 1 | 100.00% | 0.1131 | 0 | 100.00% | 100.00% |
| MathlibMPR | proof support | 4 | 0.00% | 0.0000 | 0 | 100.00% | 75.00% |
| MathlibMPR | unknown | 133 | 27.07% | 0.0433 | 0 | 100.00% | 78.95% |
| MathlibQR | unknown | 946 | 57.29% | 0.3961 | 0 | 100.00% | 84.14% |
| Usage logs | discovery | 42 | unlabelled | unavailable | 0 | 100.00% | 95.24% |
| Usage logs | explanation | 24 | unlabelled | unavailable | 0 | 100.00% | 79.17% |
| Usage logs | known item candidate | 1,543 | unlabelled | unavailable | 0 | 100.00% | 71.61% |
| Usage logs | proof support | 98 | unlabelled | unavailable | 0 | 100.00% | 90.82% |
| Usage logs | unknown | 33,362 | unlabelled | unavailable | 0 | 99.99% | 86.27% |
| Usage logs | usage or example | 21 | unlabelled | unavailable | 0 | 100.00% | 80.95% |
| Historical test requests | discovery | 12 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | multiple cues | 7 | unlabelled | unavailable | 0 | 100.00% | 71.43% |
| Historical test requests | proof support | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | unknown | 9 | unlabelled | unavailable | 0 | 100.00% | 88.89% |
| Discussion-derived queries | discovery | 529 | 25.71% | 0.1261 | 0 | 100.00% | 85.82% |
| Discussion-derived queries | enumeration | 1 | 100.00% | 0.6309 | 0 | 100.00% | 0.00% |
| Discussion-derived queries | explanation | 51 | 33.33% | 0.1628 | 0 | 100.00% | 90.20% |
| Discussion-derived queries | multiple cues | 593 | 15.85% | 0.0689 | 0 | 100.00% | 88.03% |
| Discussion-derived queries | proof support | 209 | 17.22% | 0.0788 | 0 | 100.00% | 89.00% |
| Discussion-derived queries | unknown | 531 | 22.79% | 0.1172 | 0 | 100.00% | 85.50% |
| Discussion-derived queries | usage or example | 165 | 20.00% | 0.0919 | 0 | 100.00% | 83.64% |
| Synthetic discussion queries | discovery | 2 | 50.00% | 0.1173 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | proof support | 4 | 50.00% | 0.3110 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | unknown | 20 | 25.00% | 0.1531 | 0 | 100.00% | 90.00% |
| Synthetic discussion queries | unknown | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Domain cue

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Candidate-selection pilot | analysis | 3 | 33.33% | 0.1667 | 0 | 100.00% | 100.00% |
| Candidate-selection pilot | probability measure | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Candidate-selection pilot | unknown | 8 | 62.50% | 0.5164 | 0 | 100.00% | 75.00% |
| Development pilot | algebra | 1 | 100.00% | 0.3333 | 0 | 100.00% | 100.00% |
| Development pilot | analysis | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Development pilot | combinatorics | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Development pilot | linear algebra | 1 | 100.00% | 0.1934 | 0 | 100.00% | 100.00% |
| Development pilot | multiple domains | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Development pilot | order logic sets | 2 | 50.00% | 0.1577 | 0 | 100.00% | 100.00% |
| Development pilot | probability measure | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Development pilot | unknown | 11 | 63.64% | 0.4265 | 0 | 100.00% | 90.91% |
| Development pilot | algebra | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Earlier calibration queries | algebra | 1 | 100.00% | 0.3333 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | combinatorics | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Earlier calibration queries | linear algebra | 1 | 100.00% | 0.1934 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | order logic sets | 1 | 100.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | unknown | 5 | 60.00% | 0.3929 | 0 | 100.00% | 80.00% |
| Earlier calibration queries | algebra | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | algebra | 96 | unlabelled | unavailable | 0 | 100.00% | 89.58% |
| FATE-H | analysis | 2 | unlabelled | unavailable | 0 | 100.00% | 50.00% |
| FATE-H | linear algebra | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | multiple domains | 42 | unlabelled | unavailable | 0 | 100.00% | 85.71% |
| FATE-H | number theory | 9 | unlabelled | unavailable | 0 | 100.00% | 77.78% |
| FATE-H | order logic sets | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | unknown | 48 | unlabelled | unavailable | 0 | 100.00% | 95.83% |
| MathlibMPR | algebra | 18 | 38.89% | 0.0535 | 0 | 100.00% | 77.78% |
| MathlibMPR | analysis | 7 | 28.57% | 0.0376 | 0 | 100.00% | 71.43% |
| MathlibMPR | category theory | 6 | 0.00% | 0.0000 | 0 | 100.00% | 66.67% |
| MathlibMPR | combinatorics | 4 | 0.00% | 0.0000 | 0 | 100.00% | 75.00% |
| MathlibMPR | linear algebra | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| MathlibMPR | multiple domains | 66 | 24.24% | 0.0434 | 0 | 100.00% | 80.30% |
| MathlibMPR | number theory | 3 | 33.33% | 0.0987 | 0 | 100.00% | 66.67% |
| MathlibMPR | order logic sets | 11 | 45.45% | 0.0776 | 0 | 100.00% | 81.82% |
| MathlibMPR | probability measure | 6 | 16.67% | 0.0188 | 0 | 100.00% | 100.00% |
| MathlibMPR | topology | 1 | 100.00% | 0.0909 | 0 | 100.00% | 0.00% |
| MathlibMPR | unknown | 15 | 26.67% | 0.0289 | 0 | 100.00% | 86.67% |
| MathlibQR | algebra | 69 | 62.32% | 0.4590 | 0 | 100.00% | 81.16% |
| MathlibQR | analysis | 27 | 48.15% | 0.3208 | 0 | 100.00% | 88.89% |
| MathlibQR | category theory | 26 | 57.69% | 0.3463 | 0 | 100.00% | 80.77% |
| MathlibQR | combinatorics | 12 | 66.67% | 0.3944 | 0 | 100.00% | 91.67% |
| MathlibQR | linear algebra | 11 | 45.45% | 0.2347 | 0 | 100.00% | 90.91% |
| MathlibQR | multiple domains | 43 | 67.44% | 0.4874 | 0 | 100.00% | 79.07% |
| MathlibQR | number theory | 7 | 57.14% | 0.2927 | 0 | 100.00% | 100.00% |
| MathlibQR | order logic sets | 67 | 50.75% | 0.3498 | 0 | 100.00% | 89.55% |
| MathlibQR | probability measure | 22 | 45.45% | 0.2022 | 0 | 100.00% | 81.82% |
| MathlibQR | programming | 19 | 73.68% | 0.4374 | 0 | 100.00% | 89.47% |
| MathlibQR | topology | 16 | 81.25% | 0.5398 | 0 | 100.00% | 75.00% |
| MathlibQR | unknown | 627 | 56.46% | 0.3991 | 0 | 100.00% | 83.89% |
| Usage logs | algebra | 4,361 | unlabelled | unavailable | 0 | 100.00% | 83.40% |
| Usage logs | analysis | 3,733 | unlabelled | unavailable | 0 | 100.00% | 92.39% |
| Usage logs | category theory | 219 | unlabelled | unavailable | 0 | 100.00% | 89.04% |
| Usage logs | combinatorics | 616 | unlabelled | unavailable | 0 | 100.00% | 84.42% |
| Usage logs | linear algebra | 1,256 | unlabelled | unavailable | 0 | 100.00% | 87.74% |
| Usage logs | multiple domains | 3,840 | unlabelled | unavailable | 0 | 100.00% | 87.01% |
| Usage logs | number theory | 624 | unlabelled | unavailable | 0 | 100.00% | 68.43% |
| Usage logs | order logic sets | 1,100 | unlabelled | unavailable | 0 | 100.00% | 81.55% |
| Usage logs | probability measure | 512 | unlabelled | unavailable | 0 | 100.00% | 85.16% |
| Usage logs | programming | 325 | unlabelled | unavailable | 0 | 100.00% | 85.23% |
| Usage logs | topology | 507 | unlabelled | unavailable | 0 | 100.00% | 88.76% |
| Usage logs | unknown | 18,010 | unlabelled | unavailable | 0 | 99.99% | 85.13% |
| Historical test requests | algebra | 4 | unlabelled | unavailable | 0 | 100.00% | 50.00% |
| Historical test requests | category theory | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | linear algebra | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | multiple domains | 4 | unlabelled | unavailable | 0 | 100.00% | 75.00% |
| Historical test requests | order logic sets | 4 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | programming | 3 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | unknown | 13 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Discussion-derived queries | algebra | 165 | 21.82% | 0.1143 | 0 | 100.00% | 90.30% |
| Discussion-derived queries | analysis | 33 | 24.24% | 0.1312 | 0 | 100.00% | 87.88% |
| Discussion-derived queries | category theory | 39 | 30.77% | 0.1357 | 0 | 100.00% | 84.62% |
| Discussion-derived queries | combinatorics | 52 | 23.08% | 0.1367 | 0 | 100.00% | 84.62% |
| Discussion-derived queries | linear algebra | 30 | 20.00% | 0.0866 | 0 | 100.00% | 83.33% |
| Discussion-derived queries | multiple domains | 593 | 21.25% | 0.1030 | 0 | 100.00% | 87.69% |
| Discussion-derived queries | number theory | 13 | 30.77% | 0.1795 | 0 | 100.00% | 92.31% |
| Discussion-derived queries | order logic sets | 163 | 14.72% | 0.0759 | 0 | 100.00% | 83.44% |
| Discussion-derived queries | probability measure | 14 | 28.57% | 0.1599 | 0 | 100.00% | 85.71% |
| Discussion-derived queries | programming | 305 | 26.56% | 0.1155 | 0 | 100.00% | 81.97% |
| Discussion-derived queries | topology | 15 | 20.00% | 0.1345 | 0 | 100.00% | 86.67% |
| Discussion-derived queries | unknown | 657 | 18.57% | 0.0867 | 0 | 100.00% | 87.82% |
| Synthetic discussion queries | algebra | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | linear algebra | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | multiple domains | 4 | 75.00% | 0.3907 | 0 | 100.00% | 75.00% |
| Synthetic discussion queries | order logic sets | 2 | 50.00% | 0.5000 | 0 | 100.00% | 50.00% |
| Synthetic discussion queries | programming | 5 | 20.00% | 0.1226 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | unknown | 13 | 23.08% | 0.1050 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | order logic sets | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Upstream domain

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| FATE-H | Abstract Algebra | 132 | unlabelled | unavailable | 0 | 100.00% | 87.88% |
| FATE-H | Algebraic Number Theory and Valuation Theory | 10 | unlabelled | unavailable | 0 | 100.00% | 90.00% |
| FATE-H | Basic Axioms and Examples | 8 | unlabelled | unavailable | 0 | 100.00% | 87.50% |
| FATE-H | Basic Definitions and Examples | 4 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Commutative Algebra | 68 | unlabelled | unavailable | 0 | 100.00% | 92.65% |
| FATE-H | Completions and Hensel's lemma | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Dedekind Domains and DVRs | 8 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Dimension Theory and Smoothness | 12 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Elementary Number Theory | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Explicit Computations | 22 | unlabelled | unavailable | 0 | 100.00% | 90.91% |
| FATE-H | Field Extensions | 22 | unlabelled | unavailable | 0 | 100.00% | 81.82% |
| FATE-H | Field Theory | 66 | unlabelled | unavailable | 0 | 100.00% | 87.88% |
| FATE-H | Galois theory | 22 | unlabelled | unavailable | 0 | 100.00% | 90.91% |
| FATE-H | Group Actions and Sylow theorems | 18 | unlabelled | unavailable | 0 | 100.00% | 88.89% |
| FATE-H | Group Theory | 36 | unlabelled | unavailable | 0 | 100.00% | 88.89% |
| FATE-H | Heights and Dimensions | 4 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Ideal Theory | 44 | unlabelled | unavailable | 0 | 100.00% | 90.91% |
| FATE-H | Ideals and Modules | 10 | unlabelled | unavailable | 0 | 100.00% | 80.00% |
| FATE-H | Integral Dependence and the Nullstellensatz | 14 | unlabelled | unavailable | 0 | 100.00% | 92.86% |
| FATE-H | Linear Algebra | 6 | unlabelled | unavailable | 0 | 100.00% | 83.33% |
| FATE-H | Localization and Decomposition of Ideals | 6 | unlabelled | unavailable | 0 | 100.00% | 83.33% |
| FATE-H | Noetherian rings and Chain Conditions | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Other Topics | 20 | unlabelled | unavailable | 0 | 100.00% | 90.00% |
| FATE-H | PID, ED and UFD | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Polynomials | 16 | unlabelled | unavailable | 0 | 100.00% | 81.25% |
| FATE-H | Regular Sequences and Regular Local Rings | 8 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Ring Theory | 22 | unlabelled | unavailable | 0 | 100.00% | 86.36% |
| FATE-H | Subgroups and Quotient groups | 6 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | Tensor Product and Flatness | 4 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| FATE-H | p-Groups, Nilpotent Groups and Solvable Groups | 4 | unlabelled | unavailable | 0 | 100.00% | 75.00% |

### Channel

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Usage logs | api | 32,580 | unlabelled | unavailable | 0 | 100.00% | 86.53% |
| Usage logs | mcp | 583 | unlabelled | unavailable | 0 | 99.66% | 77.02% |
| Usage logs | web | 1,930 | unlabelled | unavailable | 0 | 100.00% | 73.16% |
| Usage logs | web account | 10 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Discussion-derived queries | Is there code for X? | 1,048 | 21.66% | 0.1051 | 0 | 100.00% | 88.55% |
| Discussion-derived queries | lean4 | 380 | 18.95% | 0.0942 | 0 | 100.00% | 87.37% |
| Discussion-derived queries | mathlib4 | 651 | 21.35% | 0.0989 | 0 | 100.00% | 82.95% |

### Original form

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Candidate-selection pilot | declaration name | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Candidate-selection pilot | natural description | 4 | 75.00% | 0.5000 | 0 | 100.00% | 75.00% |
| Candidate-selection pilot | short nickname | 4 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Development pilot | formula | 3 | 66.67% | 0.2547 | 0 | 100.00% | 100.00% |
| Development pilot | keywords | 4 | 25.00% | 0.0833 | 0 | 100.00% | 100.00% |
| Development pilot | mixed | 4 | 25.00% | 0.0789 | 0 | 100.00% | 75.00% |
| Development pilot | name | 4 | 75.00% | 0.6577 | 0 | 100.00% | 75.00% |
| Development pilot | prose | 4 | 75.00% | 0.3724 | 0 | 100.00% | 100.00% |
| Development pilot | formula | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Historical test requests | prose | 30 | unlabelled | unavailable | 0 | 100.00% | 90.00% |
| Synthetic discussion queries | keywords | 13 | 23.08% | 0.1740 | 0 | 100.00% | 84.62% |
| Synthetic discussion queries | sentence or lean fragment | 13 | 38.46% | 0.1754 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | keywords | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | sentence or lean fragment | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Original intent

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Earlier calibration queries | Find a bundled maximal-spectrum definition. | 1 | 100.00% | 0.3333 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find a formal statement of Maschke's theorem. | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find a translation rule for iterated deriv of a complex-valued function. | 1 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find finite-supremum distribution of multiplication and compatible order assumptions. | 1 | 0.00% | 0.0000 | 0 | 100.00% | 0.00% |
| Earlier calibration queries | Find natural-number addition commutativity. | 1 | 100.00% | 0.3333 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find the Hom-functor injectivity statement made explicit in the later question. | 1 | 100.00% | 0.1934 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find the non-surjectivity theorem for a map into its powerset. | 1 | 100.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Earlier calibration queries | Find this exact declaration name. | 2 | 100.00% | 0.8155 | 0 | 100.00% | 50.00% |
| Earlier calibration queries | Find finite-evaluation polynomial extensionality over an integral domain. | 1 | unlabelled | unavailable | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Build a function on the whole domain from functions on subsets that cover it. | 2 | 50.00% | 0.5000 | 0 | 100.00% | 50.00% |
| Synthetic discussion queries | Carry strict positivity from a natural number to its rational cast. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Characterize preconnected subsets of the real line as intervals, including open and closed variants. | 2 | 50.00% | 0.1173 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Find zero-power and successor-power identities for integers. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Map over a list with a proof that each argument belongs to that list. | 2 | 50.00% | 0.3066 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Move the epsilon bound outside the almost-everywhere quantifier to deduce f <= a almost everywhere. | 2 | 50.00% | 0.2500 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Prove filtering preserves the absence of duplicate list elements. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Push function composition through the finite-vector constructor. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Relate the algebra norm of a complex number over the reals to its squared absolute value. | 2 | 100.00% | 0.4660 | 0 | 100.00% | 50.00% |
| Synthetic discussion queries | Show a continuous injective real function on a closed interval is monotone or antitone. | 2 | 50.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Split a list into the elements satisfying a Boolean predicate and those failing it. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Transfer independence to a pair of random variables with the same joint distribution. | 2 | 50.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | View a subgroup of H, where H is a subgroup of G, as a subgroup of G. | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | Construct pairs whose first coordinate belongs to s or whose second coordinate belongs to t. | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

### Original domain

| Collection | Category | Records | Success@10 | nDCG@10 | Errors | Nonempty results | Top-1 changed / records |
|---|---|---|---|---|---|---|---|
| Synthetic discussion queries | algebra | 4 | 50.00% | 0.2330 | 0 | 100.00% | 75.00% |
| Synthetic discussion queries | analysis | 2 | 50.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | coercions | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | group theory | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | lists | 6 | 16.67% | 0.1022 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | measure theory | 2 | 50.00% | 0.2500 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | probability | 2 | 50.00% | 0.3155 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | sets | 2 | 50.00% | 0.5000 | 0 | 100.00% | 50.00% |
| Synthetic discussion queries | topology | 2 | 50.00% | 0.1173 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | vectors | 2 | 0.00% | 0.0000 | 0 | 100.00% | 100.00% |
| Synthetic discussion queries | sets | 2 | unlabelled | unavailable | 0 | 100.00% | 100.00% |

## Limits and remaining review

No relevance labels for usage logs or FATE-H retrieval diagnostics.

Discussion reply links are candidate-answer proxies, not verified relevance.

Historical pilot targets are proposals; existing human judgments remain in the earlier release.

Forms are rule-based; intent and domain cues are unvalidated.

Full available collection, not a fresh held-out test or a representative sample of all Lean users.

Pinned local engine, models and corpus; instrumented timing is not production latency.

No global relevance score mixes different label types.

A linked reply can mention a supporting lemma, an unsuitable answer or a newer declaration absent from the pinned corpus. The 2,079 discussion-derived queries came from a prior extraction that required a declaration link in a later reply. This selection excludes many unanswered requests and cannot measure general no-answer detection.

Unknown intent and domain are retained explicitly. A larger run does not resolve missing judgments, source bias or mathematical equivalence. No model was tuned on this full collection, and the exposed material must not be presented as a fresh test set.

## Reproduction

See [the full-collection workflow](../experiments/full_collection/README.md). The external package contains the source inventory, frozen schedule, complete result journal, label provenance and per-request scores. Reconstruction refuses missing records, changed inputs or a changed schedule.
