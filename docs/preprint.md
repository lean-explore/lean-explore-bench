# An AI-assisted pilot for Lean declaration retrieval

## Judgments, ranking diagnostics and verified metadata preservation

Technical report, 8 November 2026. Assisted-v2 pilot. Require author review before submission and independent human review before treating the labels as validated.

## Abstract

This report describes a reproducible pilot for evaluating retrieval of Lean declarations. The local collection contains 20 development and 30 frozen test requests. Its usable labels comprise 759 AI proposals and four previously accepted human decisions; independent validation remains pending. Report request success, mathematical answerability, relevance coverage and rank quality separately. Nineteen development cases and 26 test cases enter relevance means. On the test set, reranking the same ten candidates raises Success@1 from 0.192 to 0.462 and nDCG@10 from 0.481 to 0.652, while Success@10 stays 0.692. These are descriptive results under assisted labels, not a validated superiority claim. The external evaluation covers all 946 MathlibQR query variants using upstream single-gold labels on the local corpus, with separate full, original shared171 and present-target conditions. A pinned exporter recovers complete elaborated types for 37 declarations. A Lean-checked normalization function preserves decoded records and validates identity and alias constraints. Manual cache fixtures exercise dependency invalidation on two Mathlib revisions. The release includes immutable rankings, provenance, score reconstruction, explicit trust boundaries and 850 human-review targets.

## 1. Motivation and questions

A declaration search result can fail at several boundaries. The corpus may not contain the requested concept; a retrieval channel may miss a useful declaration; selection can remove it before reranking; or the final score can place an inferior declaration first. An evaluation based only on the first result hides these distinctions. Judgments themselves can also fail when source snippets omit section assumptions or when generated declarations inherit a misleading source span.

This pilot asks three bounded questions. Which useful declarations survive each stage of the inspected local engine? How does reranking change an ordered response when its candidate set is fixed? Can the metadata used to inspect mathematical relevance retain complete types and environment identities through a checked normalization boundary? The package is intended for diagnosis and subsequent human correction. It does not estimate the experience of the full Lean user population.

The four-week roadmap originally proposed a larger development tranche. The executed scope is a 20-case pilot with a 30-request frozen test. This reduction is explicit. Use AI labels for the diagnostic evaluation and retain named targets for independent human validation. Keep AI proposals distinct from accepted expert judgments.

## 2. Related evaluation settings

MathlibQR evaluates recovery of one designated declaration for each query variant. Its source release contains 200 targets and 946 variants, with a shared171 subset of 810 variants used for the main cross-engine comparison [1, 2]. That task provides a useful external reference, but its single-gold scoring does not credit every mathematically useful alternative. The pilot retains graded judgments over pooled candidates. Keep the two label systems and denominators separate.

The local models belong to the Qwen3 embedding and reranking family [3]. Evaluate the fixed downloaded revisions and existing ranking mixture. No model training is included in these results. Lean distinguishes source parsing from elaboration and kernel checking [4]. Obtain semantic types from the pinned elaborated environment. The normalization proof concerns preservation and validation of decoded metadata, rather than semantic recovery from arbitrary source text.

## 3. Collection and annotation

### 3.1 Sources, scope and exposure

Development uses an exposed set of synthetic, anonymous queries. The test reservation was screened for mathematical declaration needs before retrieval. Five reserved sources were retained and 25 replaced. The final 30 test queries are synthetic and anonymous, with AI-authored wording. Some source text includes theorem names or proofs, and one earlier answer-link exposure is recorded. Do not describe this construction as uniformly answer-blind.

A pre-run freeze binds the test query bytes and retrieval settings. The test query SHA256 is b65ed4e5fba684b5b0fd2939db831a9598c38a7353fc8e84c5e52b304d617d27. No test result was used to change models, mixture weights or prompts. The released test is now exposed and cannot be reused as a fresh holdout.

Source and theorem-family relationships remain provisional. Development has 14 conservative exposure components and 19 proposed mathematical families; test has 29 proposed families. Do not use provisional groups to claim independent-family significance. Review mathematical equivalence and cross-split overlap under HC-FAMILY.

### 3.2 Labels and unresolved cases

There are 419 development and 367 test pairs in the review pools. Of 786 pairs, 763 have usable judgments: 759 AI proposals and four historical human acceptances. The excluded development case contributes the remaining 23 pair records, including nine unresolved proposals. Accepted human decisions take precedence over AI proposals.

Grades range from 0 to 3. Grade 3 directly answers the request under its assumptions; grade 2 gives a useful answer requiring a clear adaptation; grade 1 is related but insufficient; grade 0 is irrelevant or incompatible. Binary relevance means grade at least 2. Labels require attention to assumptions, domains, implication direction and generality, rather than name overlap alone.

The development request about a path-connected indexed union is false for an empty index type even when the stated intersection condition holds. It is retained operationally and excluded from quality means. A repair must introduce a new query version and run. Test-18, test-26, test-27 and test-29 have unknown answerability: their judged pools do not establish a useful answer or corpus absence. Consequently, quality means use 19 development cases and 26 test cases. None of these exclusions is hidden as a successful abstention.

### 3.3 Human correction and label provenance

Each pair and case has a stable human target. Packet fingerprints and corpus identities bind proposals to evidence. The correction command requires explicit reviewer, accepted grade and reason; it creates a new label version and recomputes scores over immutable rankings. Rewriting a query or changing an engine requires new retrieval evidence. Opening a review card does not accept its proposed label.

The v2 register has 850 targets: 786 pairs, 50 cases and 14 release-level checks. Four prior human decisions remain on file. The registry does not claim that these decisions independently validate the rest of the collection. Calibration, source-family review and annotation timing remain manual work. No inter-annotator agreement or AI-judge error rate is estimated.

## 4. System and experimental method

### 4.1 Pinned local system

The local corpus contains 408,970 canonical declaration names. Its database SHA256 is 5ffc35ab68db5c60b535a416148a327de9a862a03048c41d62bfcb0b3903424d. The corpus is the measured artifact; its original build environment and the configuration of a hosted service are not fully known. The report does not generalize local results to that service.

Embedding uses Qwen/Qwen3-Embedding-0.6B revision 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3; reranking uses Qwen/Qwen3-Reranker-0.6B revision e61197ed45024b0ed8a2d74b80b4d909f1255473. The respective limits are 512 and 256 tokens, with bfloat16 and float16 execution. FAISS nprobe is 64. Executed source hashes, model and index identities, token counts and truncation flags are retained. In the external run, 1,079 of 94,600 reranker pairs exceed the 256-token limit; median and 95th-percentile untruncated token counts are 115 and 202. The runtime audit retains the full distribution inputs.

Pilot retrieval requests lexical and dense depths of 1,000, applies the existing fusion and selection procedure, and reranks ten candidates. The current final mixture combines neural, lexical, fuzzy-name and dependency signals. Comparisons include lexical, dense, fusion, selection, the pre-rerank ten-candidate order, current mixture, neural-only and removal of the final dependency term. The three final-score variants use identical candidate pools. They are diagnostics of one system, not independent model-training experiments.

### 4.2 Metrics and coverage

Success@k is one when a relevant declaration occurs in the first k ranks. MRR@k uses the reciprocal rank of the first relevant declaration, with zero on a miss. Graded nDCG uses the sum of grade divided by log2(rank + 1), normalized by the ideal ordering of known judgments. Gain is linear. Precision, recall and MAP are also stored; recall uses known pooled positives and does not enumerate every valid library answer.

Unjudged documents receive zero computational gain but remain unjudged, rather than becoming accepted negatives. Judged@k accompanies relevance scores. Channel rankings extend to depth 100; the pilot's reranked response extends only to ten. A missing higher-cutoff result is not padded into a measured score. Failed requests would score zero on eligible cases and remain in operational accounting. Both test executions completed all 30 requests.

### 4.3 External reference condition

The reference contract freezes all 946 upstream variants on the local corpus. It preserves original full and shared171 membership and reports a separate present-only slice. Four target names are absent by exact identity. Absent targets and failed requests score zero in full and shared171; they are excluded only from the explicitly conditional present-only slice.

This condition uses 100 reranker candidates and up to 100 returned declarations, enabling all published nDCG and recall cutoffs. It differs from the pilot's ten-candidate setting. The original single-gold metric functions are retained and checked against the local scorer [2]. The original cross-engine LLM-judge experiment is outside this local target-recovery comparison. Raw channel stages and the final visible response are distinguished. The shared subset is the original membership; it is not redefined to make the new corpus look better.

Report query-micro and target-macro means for each slice. Percentile intervals use 2,000 seeded bootstrap draws over upstream target groups, preserving variants within a sampled group. They describe resampling variability for this condition, not annotation error, independent trials of the model or a confirmatory comparison with published engines.

## 5. Results

### 5.1 Frozen pilot test

Table 1 reports relevance means for the 26 eligible test cases. The ten-candidate pool is unchanged by final reranking. Success@1 rises from 5/26 to 12/26, while Success@10 remains 18/26. The first returned declaration changes for 26 of all 30 scheduled test requests. All 30 ordered lists change. The report exposes every before/after list, including the four unknown cases.

| Configuration | S@1 | S@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.038 | 0.077 | 0.043 | 0.065 | 0.527 |
| dense | 0.500 | 0.731 | 0.570 | 0.670 | 0.535 |
| fusion | 0.231 | 0.731 | 0.401 | 0.512 | 0.996 |
| fusion with selection boost | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| pre rerank same pool | 0.192 | 0.692 | 0.323 | 0.481 | 1.000 |
| current mixture | 0.462 | 0.692 | 0.553 | 0.652 | 1.000 |
| neural only | 0.500 | 0.692 | 0.590 | 0.673 | 1.000 |
| without final dependency | 0.500 | 0.692 | 0.574 | 0.660 | 1.000 |

Neural-only has the highest nDCG@10 among the fixed-pool variants in this pilot (0.673), compared with 0.652 for the current mixture. This observation supports further investigation of the mixture. It does not establish a production winner: labels are assisted, the sample is small, and family independence is unreviewed. Dense-channel scores also depend on partially judged top tens; its 0.670 nDCG@10 and 0.535 Judged@10 should be read together.

### 5.2 Development and label sensitivity

Table 2 uses 19 eligible development cases. These cases informed curation and diagnosis and are not independent test evidence. The first result changes for 18/20 scheduled development requests. Together with test, all 50 ordered responses are available in the comparison report.

| Configuration | S@1 | S@10 | MRR@10 | nDCG@10 | Judged@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.158 | 0.421 | 0.254 | 0.272 | 1.000 |
| dense | 0.526 | 0.947 | 0.667 | 0.721 | 1.000 |
| fusion | 0.158 | 0.895 | 0.439 | 0.512 | 1.000 |
| fusion with selection boost | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| pre rerank same pool | 0.053 | 0.895 | 0.312 | 0.457 | 1.000 |
| current mixture | 0.263 | 0.895 | 0.514 | 0.560 | 1.000 |
| neural only | 0.526 | 0.895 | 0.643 | 0.585 | 1.000 |
| without final dependency | 0.263 | 0.895 | 0.515 | 0.561 | 1.000 |

An additional calculation holds the original four accepted cases and their stored responses fixed, then expands their labels using AI proposals. nDCG@10 changes from 0.6404 to 0.7203 without an engine change. This isolates a label effect. Comparing that number with the full 19-case development mean would change the denominator and would not measure the same effect.

### 5.3 MathlibQR on the local corpus

Table 3 reports the original shared171 slice (810 query variants). Full and present-only tables are in the reference report.

| Configuration | nDCG@1 | nDCG@5 | nDCG@10 | R@10 | R@50 | R@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.115 | 0.148 | 0.158 | 0.210 | 0.302 | 0.330 |
| dense | 0.256 | 0.373 | 0.397 | 0.553 | 0.712 | 0.764 |
| fusion | 0.184 | 0.320 | 0.351 | 0.527 | 0.698 | 0.742 |
| selection | 0.156 | 0.290 | 0.327 | 0.537 | 0.705 | 0.769 |
| current mixture 100 | 0.240 | 0.362 | 0.398 | 0.583 | 0.740 | 0.769 |
| neural only 100 | 0.141 | 0.246 | 0.280 | 0.447 | 0.701 | 0.769 |
| without final dependency 100 | 0.205 | 0.315 | 0.353 | 0.536 | 0.731 | 0.769 |
| pre rerank same pool 100 | 0.156 | 0.290 | 0.327 | 0.537 | 0.705 | 0.769 |

The full slice has 946 queries in 200 target groups; current-mixture nDCG@10 is 0.390, Recall@10 is 0.572, and Recall@100 is 0.754. The shared171 slice has 810 queries in 171 target groups; current-mixture nDCG@10 is 0.398, Recall@10 is 0.583, and Recall@100 is 0.769. The present only slice has 927 queries in 196 target groups; current-mixture nDCG@10 is 0.398, Recall@10 is 0.584, and Recall@100 is 0.769. The full-slice Recall@10 target-group bootstrap interval is [0.532, 0.613]. All 946 requests completed with 0 recorded errors. The first result changes in 810 requests after reranking.

The ablation ordering changes across conditions. On all MathlibQR variants, the current mixture has nDCG@10 of 0.390, neural-only 0.261 and removal of the final dependency term 0.344; selection before reranking is 0.322. In the ten-candidate pilot, neural-only instead has the highest fixed-pool nDCG@10. The reference uses different query forms, single-gold labels and a 100-candidate pool, so this reversal cannot be attributed to query style alone. It argues against choosing a production replacement from the small assisted pilot. No mixture was changed in response to either test.

The external scores use upstream single-gold targets and therefore do not depend on the pilot's AI relevance grades. They still depend on corpus coverage, exact target identities and the selected retrieval configuration. Do not infer cross-engine improvements by subtracting published Table 1 numbers from these results: corpus versions, artifacts and execution conditions differ. Per-style scores, target-macro means, confidence intervals and every query's target rank are included in the artifact.

### 5.4 Representation and mathematical evidence

The representation probe has 18 scored pairs: two controls, three statement variants and three representations. Four valid statements and two counterexamples were checked with Lean 4.35.0. Scores reproduce exactly across the two stored runs on the common measured fields. The probe is synthetic and small; it does not estimate semantic fidelity over Mathlib.

Thirteen earlier development examples use Lean 4.32.0-rc1 and a different Mathlib revision. Their evidence is retained under that environment. Full semantic inspection for the 37 selected release declarations instead uses Lean 4.32.0 and Mathlib aae61ae084c21995ee248964a81e3750ad0db2db. These environments are never silently equated.

## 6. Verified metadata and incremental cache

### 6.1 The verified boundary

The exporter imports requested modules from a clean pinned checkout and reads full elaborated declaration types, universe parameters and kinds. It rejects missing/duplicate identities and open expressions. The exported types support annotation; retrieval uses the frozen corpus inputs. This resolves cases where a generated theorem's source span describes its parent declaration or where a snippet omits enclosing assumptions. Both readable and explicit type renderings are kept; expression representations remain available when the pretty printer suppresses detail.

The normalization input is a decoded, versioned envelope containing environment identity, artifact digest, declarations and aliases. Each declaration has its full name, package/module, kind, type-expression string, rendered type, source reference and context evidence. Validation rejects unsupported versions/kinds, empty required fields, duplicate canonical or alias names, conflicting environments and aliases without a canonical target. It either returns the entire snapshot or fails.

Seven Lean theorems characterize success, preserve records and environment, preserve count and order, establish unique identities, ensure alias resolution and reject invalid envelopes. Because the record list is preserved by equality, identity, mathematical text and recorded context are preserved together. The kernel reports only propext and Quot.sound, with no sorryAx or custom axioms. The runtime entry point calls this same function. The 37 exported records and twelve runtime acceptance/rejection fixtures pass.

This proof treats semantic fields as opaque strings. It cannot establish that an upstream expression is the correct theorem, that a provenance reference is truthful or that nonempty context text is complete. JSON decoding, the adapter, upstream extraction/elaboration, serialization, hashes and compiler/runtime remain trusted. HC-NORMALIZATION-SPEC asks a human to assess whether the chosen contract captures the intended boundary.

### 6.2 Manual cache validation

Cache keys bind source inputs, toolchain, dependency lock, import dependencies, transformation revisions, generation configuration, embedding inputs and index membership. A transitive imported change propagates through effective input keys even if the consumer's own source is unchanged. Immutable content-addressed objects are verified on reuse. A complete new snapshot is published before replacing the current pointer. Failure leaves the previous snapshot available. Concurrent writers must be serialized by the caller.

A manual source fixture covers 351 modules reachable from Mathlib.Order.Atoms at revisions 783ccda4ee524f13cc5636237be0a1942bc04824 and aae61ae084c21995ee248964a81e3750ad0db2db. A no-change run reuses all artifacts. The update reuses 349 artifacts per module layer and invalidates two, including unchanged Order.Atoms after Order.ModularLattice changes. The index is rebuilt. Twenty-six tests also cover every configuration field, deletion/rename history, corruption and interrupted publication.

These builders record effective inputs; they do not invoke Lean compilation, informalization or embedding models. The experiment establishes cache behavior under the fixture contract and reports stored bytes. It does not claim measured production speedup or model-cost savings. A production adapter and an unattended repository watcher are outside the pilot.

## 7. Reproducibility and release

The assisted-v1 artifact remains immutable. Its score-reconstruction command rebuilds both label profiles and 16 evaluation reports using the Python standard library and bundled source. Two 30-query test runs match in final rankings, stage identities, input audits and reranker scores. One intermediate attempt failed during input hashing because WSL lacked memory; its failure log is retained. The package does not hide that attempt.

Assisted-v2 adds the external contract and raw rankings, the upstream metric source, per-query target ranks, the normalization proof and runtime evidence, cache validation, dataset card and this manuscript. The MathlibQR run was resumed after an administrative interruption to reduce checkpoint IO. The first 402 completed records are retained unchanged, and one cancelled in-flight request is recorded before its successful re-execution. The final schedule has 946 records; this is not a claim that only 946 attempts occurred. A manifest hashes every included file. Executed source is retained separately from any later formatting of repository source. Heavy database, index and model files remain external dependencies with exact identities. Re-running inference requires those assets and the recorded environment; recomputing scores does not.

Reported latencies include tracing, input inspection and exact-name lookup. They are not serving latency. Local inference uses existing model snapshots, while GPU utilization, energy and annotation time are not complete cost measurements. No new hosted-model translation experiment or reranker training is included.

## 8. Limitations and manual review

The central limitation is label validity. Most pilot judgments are AI proposals. AI assistance covered request curation, mathematical evidence inspection and result interpretation, so those stages do not provide independent validation of one another. Independent experts have not validated this release. Formal preservation of metadata does not validate those relevance decisions. Pooling is incomplete, corpus build provenance is partly unknown, and the provisional source families limit statistical interpretation.

The source mixture is small and synthetic; it underrepresents declaration-name, formula and proof-state needs relative to an intended broader benchmark. The four unknown test requests and invalid development request remain visible. Negative pools do not prove absence. The observed ranking differences concern declaration lists; no generated natural-language answer or downstream proof-success claim is made.

Redistribution also requires source-by-source review. The dataset card records upstream provenance, retained notices, external assets and unresolved release decisions. Public availability alone is not treated as a dataset license. HC-REDISTRIBUTION, HC-MANUSCRIPT and HC-SUBMISSION keep rights review, author review and the final publication decision separate from automated completion.

Begin manual review with the invalid development case and four unknown test cases. Calibrate positive and difficult negative judgments, review theorem-family boundaries, inspect the metadata contract and check manuscript claims. Create new label versions for corrections and report their effect on unchanged rankings. A later confirmatory study needs new held-out requests and independently accepted labels.

## References

[1] Gao, G., Sun, Z., Jiang, J., Wang, Y., Xu, J., Wu, P., Dai, B., and Dong, B. LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving. arXiv:2605.13137v2, 2026. https://arxiv.org/abs/2605.13137v2

[2] FrenzyMath. LeanSearch-v2 benchmark and single-gold evaluation source. Commit 94f4888cbaf9f4322535755f86cbac690ec18080. https://github.com/frenzymath/LeanSearch-v2/tree/94f4888cbaf9f4322535755f86cbac690ec18080

[3] Zhang, Y., Li, M., Long, D., and colleagues. Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models. arXiv:2506.05176v3, 2025. https://arxiv.org/abs/2506.05176v3

[4] Lean Language Reference. Elaboration and Compilation. Accessed 8 November 2026. https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/
