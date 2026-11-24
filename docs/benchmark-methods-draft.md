# Pilot methods draft

Use this document as the 7 November checkpoint. Read [assisted-v2](benchmark-assisted-v2.md) for the current results; independent human validation remains pending.

This text describes the observed development pilot, not a released benchmark.

## Collection and scope

The development pilot contained 20 cases with four cases in each of five query forms: declaration names, keywords, prose, formulas and mixed text/code. Ten cases came from public discussions and ten from public reference tasks or explicit controls. Equal allocation was chosen for diagnostic coverage and does not estimate real usage frequency. Query form, intended task, provenance and answerability were stored separately.

All exposed queries and imported reference variants were assigned to development. Original queries were retained when their interpretation was clarified after candidate exposure. A formula that contains its answer's name was treated as answer-exposed material. Targets supplied by upstream sources were proposals rather than relevance labels.

The reference adapter imported 946 nonempty MathlibQR variants in 200 target groups. In the pinned canonical-name inventory, 196 target names were present and four were absent. This establishes the local import and grouping contract; it does not reproduce the original evaluation.

## Retrieval and candidate pools

The local retrieval snapshot contained 408,970 canonical declaration names. The evidence retained corpus and index hashes, model/tokenizer revisions, executed source, effective settings and request-level traces. The original artifact-build environment and the effective hosted-service process configuration were not fully available. Results therefore concern the pinned local snapshot.

The original review packet contained 213 pairs. Pooling lexical, semantic, fused and final-ranked candidates expanded this to 419 distinct query-document pairs. Packet identities were retained separately. Candidate order was shuffled and engine identities and ranks were stored outside the annotation packet. The AI assessor had prior candidate exposure, so its judgments are not blind independent annotations.

The comparison used prefixes of length 50 and 100 from retrieval runs requesting 1,000 candidates per lexical and semantic channel. First-stage recovery was reported as proposed-target-name recovery, without interpreting missing proposals as unanswerable queries. Fixed-pool analyses separated the dependency contribution in final ranking from the earlier selection boost. Ordering changes alone were not treated as improvements.

## Judgments and formal checks

The relevance rubric uses grade 3 for a direct or equally usable equivalent answer, 2 for a usable answer with documented adaptation, 1 for a supporting but insufficient result, and 0 for an irrelevant or unusable result under the task assumptions. Scope restrictions are task preferences: for example, requiring a natural-number-specific declaration does not make a general theorem mathematically false.

AI review screened all 419 pairs and proposed 402 grades: 18 at grade 3, 26 at grade 2, 108 at grade 1 and 250 at grade 0. Eight pairs retained unresolved type evidence. Nine pairs belonged to an invalid query and remained unjudged. Four previously accepted human positives were preserved; no additional human acceptance or independent second review was recorded.

Source inspection covered complete contexts for selected declarations at the retrieval revision. Thirteen additional examples compiled in an available Mathlib environment with Lean 4.32.0-rc1. This environment differs from the retrieval snapshot. Report these checks under their recorded environment, separately from compilation of the pinned corpus. One check demonstrates that an indexed path-connected union can fail when the index is empty; the repaired query adds a nonempty-index assumption and is stored separately.

## Splits and test reservation

Grouping constraints cover source requests, normalized query text, target identities and recorded review documents. They are conservative exposure constraints, not automatically established mathematical families. The expanded review produces 14 connected components, while a separate AI inventory proposes 19 mathematical families. Neither count supports independent-family inference without review.

The initial reservation of 30 source topics included 25 requests outside the primary mathematical-declaration track. Question-text inspection led to replacement of those slots. The revised ledger contains 30 provisional sources with 29 proposed family labels, no generated test queries and no final test cases. Topic overlap with recorded development sources was rejected. Source-authored answers, curation exposure and unresolved family relationships remain explicit.

## Evaluation and limitations

The scorer uses linear gain and treats grades of at least 2 as relevant. Ranking calculations assign zero gain to unjudged results; this computational convention does not label them irrelevant. Only accepted, resolved human judgments enter the official collection. Failed and missing requests remain in operational denominators.

Recalculation preserved the point metrics from the four accepted positives. Given the sparse positive-only labels, these values are calibration diagnostics and do not estimate benchmark quality. Family-grouped comparisons and confirmatory significance claims are deferred until grouping and judgments are accepted.

Two stored local runs agree on all 20 final rankings and stage traces. Two representation probes agree on 18 scored records. The representation probe uses invented, Lean-checked controls and is reported separately from retrieval accuracy.

No inter-rater agreement or observed human annotation rate is reported. The first two weeks deliver a tested workflow, diagnostic results, AI review proposals and specifications for training and extraction. A scientific release still requires completed human calibration, final test eligibility and a frozen evaluation protocol.
