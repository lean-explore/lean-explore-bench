# Benchmark status

The [full-collection report](benchmark-full-collection.md) covers all prepared sources: 38,566 source records and 33,075 distinct query-and-package requests. It includes all prepared discussion-derived queries, usage logs, MathlibQR, MathlibMPR, FATE-H and the earlier development collections. [Corrected reranker results](benchmark-reranker-corrected.md) use the same candidate pools across that entire schedule. The [new preprint](full-collection-preprint.md) explains the process, findings and remaining work.

The reranker integration fix uses yes/no scoring, chat wrapping and truncation that preserves the answer position. It is available on the [engine fix branch](https://github.com/lean-explore/lean-explore/tree/fix/qwen-reranker-contract). The benchmark preserves the original implementation as a separate baseline. Neither branch push deploys the change.

Upstream reference targets, proposed reply-link targets and unlabelled usage traffic have separate reporting. Logs and FATE-H have no declaration-relevance judgments in these inputs; nonempty output is not an accuracy measure. The complete collection is exposed material, not a fresh held-out evaluation. Independent relevance review remains pending.

Use [assisted-v2](benchmark-assisted-v2.md) for the historical diagnostic pilot. Its [dataset card](dataset-card.md), [manuscript](preprint.md) and [reproduction instructions](benchmark-reproduction.md) retain their original scope and execution requirements.

## Preserve the historical pilot scope

- Retain all 20 development and 30 test requests in operational accounting. Use 19 development and 26 test cases for relevance means; preserve the invalid development case and four unknown test cases in the review register.
- Distinguish 759 AI relevance proposals from four accepted human decisions. Keep the 850 human-review targets open until their acceptance criteria are met.
- Report all 946 MathlibQR variants, the original shared171 subset of 810 queries and the separate present-only subset of 927 queries. All 946 scheduled queries have successful final records; retain the additional cancelled attempt and continuation provenance.
- Separate the ten-candidate pilot from the 100-candidate external condition. Compare all eight configurations within their recorded pools and report judgment coverage.
- Limit the Lean verification claim to decoded metadata normalization. Seven theorems check preservation and validation properties; 37 pinned declaration records and twelve runtime fixtures exercise the executable boundary.
- Treat the two-snapshot, 351-module cache fixture as an invalidation check. Its recording builders do not establish production inference savings.

## Preserve historical validation evidence

Retain the 125 passing Python tests, 15 subtests, Lean proof logs and artifact checks. Reconstruct the two pilot profiles and 16 score reports, all 946 reference scores and the cache fixture from the external package. Preserve the identical rankings and scores from the two complete pilot test runs.

Keep raw data, annotation exports, model files and measured runs outside Git. Publish source code, methods and aggregate results under the [repository publication scope](benchmark-consolidation.md).

## Complete human review

Start with HC-D20 and HC-T18, HC-T26, HC-T27, HC-T29. Follow the [review workflow](assisted-human-review.md), retain accepted decisions and create new label versions for corrections. Require explicit decisions for calibration, source-family separation, semantic evidence, redistribution, authorship and submission.

Treat reranker fine-tuning, new-model informalization and production cache integration as separate experiments. Use [assisted-v1](benchmark-assisted-v1.md) and the [methods checkpoint](benchmark-methods-draft.md) only for their historical scopes.
