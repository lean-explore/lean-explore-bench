# LeanExplore assisted pilot: dataset card

Version: assisted-v2, 8 November 2026. This is a local research package prepared for manual review. Independent human validation and public redistribution approval are pending. The earlier assisted-v1 archive remains immutable.

## Purpose and intended use

The pilot measures retrieval of Lean declarations for mathematical information needs. Its response is an ordered declaration list. It supports inspection of retrieval channels, candidate selection, reranking and annotation changes on a pinned local corpus. It does not measure generated explanations, proof completion, user satisfaction or deployment performance.

Use this package to reproduce the reported diagnostic comparisons and to review individual judgments. Do not treat its AI labels as an independently validated leaderboard, use exposed test cases as a new holdout, or train on them and then claim held-out performance. The small source mixture does not represent all Lean users or all mathematical domains.

## Composition

The local pilot contains 20 development requests and 30 frozen test requests. Nineteen development cases and 26 test cases enter relevance means. One development statement is invalid without an additional assumption; four test cases have unknown answerability. All 50 remain in operational accounting and in the review registry.

The review pools contain 786 distinct query-document pairs: 419 development and 367 test. There are 763 usable judgments, comprising 759 AI proposals and four previously accepted human decisions. The other 23 pairs belong to the excluded development case; nine of those proposals remain unresolved. Their records are retained. No new human decisions have been inferred from silence or from successful automated checks.

The external MathlibQR condition contains 946 query variants for 200 upstream target groups. Its original shared171 membership contains 810 variants. In the local corpus, 196 target names are present and four are absent. These upstream single-gold labels are separate from the pilot's graded relevance. The reference run does not expand the pilot's human-reviewed sample size.

## Collection and authorship

Development uses an exposed set of synthetic, anonymous queries. Test requests were screened for the mathematical-declaration task before retrieval: five reserved sources were retained and 25 replaced. The frozen test queries are synthetic and anonymous, with AI-authored wording. Source material sometimes includes declaration names or proofs, and one prior answer-link exposure is recorded. Query generation was not uniformly answer-blind.

Original source identity, query text, provenance, target proposals and source hashes remain separate fields. A source's proposed answer is not automatically a relevance judgment. Case-family labels are provisional: development has 14 conservative exposure components and 19 proposed mathematical families; test has 29 proposed families for 30 requests. Human review of mathematical equivalence and cross-split leakage is HC-FAMILY.

No private usage logs are included in this benchmark package. The available corpus-build history and hosted-service configuration are incomplete. HC-PROVENANCE records those limitations. The package identifies the exact local bytes that were evaluated.

## Annotation procedure and rubric

The rubric assigns grades from zero to three. Grade 3 is a direct answer under the requested assumptions. Grade 2 is a useful answer requiring a clear adaptation. Grade 1 is related material that does not adequately answer the request. Grade 0 is irrelevant or mathematically incompatible. Relevance for binary metrics means grade at least 2. Mathematical assumptions, implication direction, object types and generality matter more than shared vocabulary.

AI review inspected pooled candidates, source context and, where needed, full elaborated types. AI records retain their assessor type, rationale, packet binding and stable pair target. Previously accepted human decisions take precedence. Uncertainty remains explicit; a set of negative pool judgments does not prove that the corpus lacks an answer.

The label workflow rejects mismatched packets and corpus identities, duplicate canonical pairs and attempts to relabel an assisted profile as a human-only base. A human correction must explicitly identify the case, document, reviewer, accepted grade and reason. Corrections produce a new label history and recompute metrics on unchanged run hashes. A repaired query or changed engine requires a new run.

There is no independent annotation agreement statistic, calibrated AI error rate or measured annotation throughput. Complete HC-CALIBRATION and HC-TIMING through measured human review. Four historical accepted decisions do not substitute for independent validation of the full collection.

## Corpus and model identities

The local database contains 408,970 canonical declaration names. Its SHA256 is `5ffc35ab68db5c60b535a416148a327de9a862a03048c41d62bfcb0b3903424d`. The semantic evidence uses Mathlib revision `aae61ae084c21995ee248964a81e3750ad0db2db` and Lean 4.32.0. The complete corpus inventory is external to the source repository.

The embedding model is Qwen/Qwen3-Embedding-0.6B at revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`. The reranker is Qwen/Qwen3-Reranker-0.6B at revision `e61197ed45024b0ed8a2d74b80b4d909f1255473`. Embedding inputs use a 512-token limit and bfloat16; reranker inputs use a 256-token limit and float16. Input hashes, token counts and truncation flags are stored. FAISS uses nprobe 64. Model weights, indexes and the database remain external dependencies, identified by hashes and manifests.

Pilot retrieval uses BM25 and dense depths of 1,000, candidate selection with the existing dependency signal, ten reranker candidates and ten returned results. Eight configurations are scored from the recorded stages and identical pools. The external reference uses 100 reranker candidates and up to 100 returned results, fixed in its own pre-run contract. Its results must not be described as the pilot's ten-candidate configuration.

## Evaluation and uncertainty

Pilot quality reporting uses Success@k, MRR@k and nDCG@k, with linear gain for graded nDCG and relevance threshold 2. The stored reports also include precision, recall and MAP. Recall is relative to known pooled positives, not every valid theorem in the library. Query failures count as zero on eligible cases; unknown and excluded cases remain in request accounting. The four unknown test cases do not establish correct abstention.

Unjudged documents have zero computational gain but are not accepted negatives. The test channel top tens are only partly judged; the ten-candidate fixed-pool comparison is fully judged under the assisted profile. Coverage is reported alongside quality. No independent-family significance claim is made for the pilot.

MathlibQR uses its upstream binary, single-target scoring. The full slice includes absent targets and failed requests as zero; shared171 keeps the original target membership; present-only is a separate coverage-conditioned slice. Query-micro and target-macro means are reported. Seeded target-group bootstrap intervals describe resampling variability, not label correctness or a new model population. This is a remapped local-corpus condition, not a replication of other engines' published scores. It covers single-gold target recovery; the original cross-engine LLM-judge comparison is not rerun.

The frozen test was executed twice with identical final rankings, stage identities and score values. A failed reproduction attempt during artifact hashing is retained. Diagnostic latency includes tracing and input inspection and is not a production serving measure. No API generation cost or human review duration was measured; local runtime and instrumentation scope are recorded where available.

## Extraction and verification

The exporter obtains closed elaborated types for 37 selected declarations from the pinned environment, including generated declarations whose source spans are misleading. Readable and explicit renderings, expression representations and universe parameters are retained. Earlier development proof examples and representation controls keep their different Lean environment identities.

A total Lean normalization function validates a decoded envelope and either returns its complete snapshot or rejects it. Proofs establish record and environment preservation, count and order, identity uniqueness, alias resolution and rejection of invalid envelopes. The runtime command invokes that function. JSON decoding, the envelope adapter, source provenance, upstream semantic completeness, hashing, IO and the compiler/runtime remain trusted. This is a bounded metadata proof, not a proof of an arbitrary Lean frontend. HC-NORMALIZATION-SPEC asks a human to review whether the specification is sufficient.

The incremental cache is a manual, single-writer component. Effective inputs cover extraction, normalization, informalization, embeddings and index membership. Its two-snapshot source fixture uses deterministic recording builders; it does not execute generation or embeddings and does not measure inference savings. Production integration and automatic repository watchers are outside this pilot. HC-CACHE-SPEC covers the effective-input contract and fixture interpretation.

## Provenance and redistribution inventory

| Material | Evidence retained | Release disposition |
| --- | --- | --- |
| Pilot queries and source excerpts | Source records, source URLs where available, generation/exposure audits and hashes | Local review package; review source attribution and redistribution before public release: HC-REDISTRIBUTION. |
| AI proposals and four accepted decisions | Assessor type, rationale, packet hashes and historical human session | Local review package; preserve provenance and avoid assigning an unapproved blanket data license. |
| MathlibQR input | Upstream commit 94f4888cbaf9f4322535755f86cbac690ec18080, file hashes, repository LICENSE and provenance | Repository states Apache-2.0; no distinct MathlibQR data-license statement was identified. Keep original attribution and license; confirm data scope under HC-REDISTRIBUTION. |
| Lean/Mathlib declarations and source evidence | Revision-specific source references and upstream notices | Preserve upstream attribution. Check each packaged excerpt and non-Mathlib package before public redistribution. |
| Retrieval engine source | Source hashes, patch base and retained LeanExplore license | Preserve the existing license and notices. |
| Model weights, database and indexes | Exact identities and runtime manifests | External dependencies; not copied into the lightweight release archive. |
| New code and manuscript | Source files and artifact manifest | Prepared locally for author review. No new public dataset license or authorship agreement is asserted. |

The upstream MathlibQR repository license is available at https://github.com/frenzymath/LeanSearch-v2/blob/94f4888cbaf9f4322535755f86cbac690ec18080/LICENSE. This inventory records observed provenance and unresolved release decisions; it is not a legal determination about every included source.

## Packaging, versioning and maintenance

The v2 package contains the immutable v1 evidence, external-reference contract and rankings, score reconstruction tools, verified normalization source and logs, cache fixtures, this card, the manuscript and an extended human-check registry. Heavy assets stay outside the archive. A manifest lists every included file's SHA256. Real benchmark data remain outside Git; the repository contains methods and source.

Rerun pure score reconstruction before changing labels. Record accepted manual decisions in a new version, retain the previous profile and run hashes, and compare before/after metrics. Never overwrite the frozen query file to repair a mathematical statement. All released test material is now exposed. A later confirmatory study needs new independently curated sources and human-reviewed family boundaries.

## Outstanding human work

The inherited registry contains 844 targets. V2 adds six specification, provenance, manuscript and external-reference checks with stable IDs, for 850 targets total. Every target remains pending unless an explicit accepted decision already exists. Start with HC-D20 and HC-T18, HC-T26, HC-T27, HC-T29; then calibrate positives and difficult negatives, review families, inspect source rights and verify manuscript claims. A successful program or proof does not close a human target automatically.

The optional new-model translation study, reranker fine-tuning and production cache integration are future experiments. They are not prerequisites in the four-week core benchmark plan and have no results in this release.
