# Benchmark methods and reporting

Read the [assisted-v2 results](benchmark-assisted-v2.md) and [manuscript](preprint.md) for the measured evaluation. Use the [7 November methods checkpoint](benchmark-methods-draft.md) only as historical evidence.

Use this specification when preparing the benchmark methods section. Replace open review fields with measured values before describing a released collection.

## Define the evaluation unit

Treat a case as an information need with a documented interpretation. Keep query variants attached to that case. Record query form separately from mathematical domain, task intent, answerability and difficulty. Report case, query, query-document pair and reviewed family counts separately.

Use the five development forms: declaration name, keywords, prose, formula and mixed text/code. Treat the equal allocation as diagnostic coverage, not an estimate of user traffic. Preserve original queries and record any clarification or answer exposure. Do not describe a formula containing its target name as a name-free query.

## Freeze corpus and runs

Bind the collection to a complete canonical-name inventory and a database digest. Record the source and index manifests, model and tokenizer revisions, rendering, truncation, retrieval depths, filtering order, score weights, seeds and numerical settings. Preserve explicit unknown fields for the original build environment and any hosted deployment.

Reproduce the local snapshot before comparing methods. Preserve all scheduled requests, including failures and missing responses. Keep tracing and input-inspection time separate from any claim about serving latency. Refuse outputs that would overwrite an existing run.

## Construct and review pools

Pool deduplicated candidates from multiple first-stage channels and selected final rankings. Add proposed targets without treating them as accepted labels. Freeze each packet identity and keep engine names and ranks in a separate audit.

Review intent before candidates. Record whether later clarification used candidate evidence. Preserve individual judgments and distinguish accepted decisions from proposals. Obtain independent review before adjudication when reporting agreement. Measure active review time rather than elapsed communication time.

Apply the draft grades: 3 for a direct or equally usable equivalent answer; 2 for a usable answer with documented adaptation; 1 for a related but insufficient result; 0 for an irrelevant or unusable result under the task assumptions. Leave uncertainty unjudged. Review general specializations, aliases and missing assumptions before accepting a negative.

## Separate availability from relevance

Resolve proposed names against the pinned inventory. Distinguish a name absent from the corpus, a query without a proposed target, a candidate lost during retrieval, and a mathematically unsuitable retrieved result. Do not infer that no adequate answer exists from a failed name lookup.

For first-stage diagnostics, report recovery of present proposed targets explicitly as a proxy. Preserve the denominator of scheduled cases and disclose how many have a present target. Report 50/100-depth coverage only where those candidate lists were actually collected.

## Report metrics with coverage

Use linear graded gain, binary relevance at grade 2 or above, Success@1/5/10 and MRR@10 for known-item tasks, and nDCG@10 for graded declaration search. Report Judged@10 and pool depth alongside quality metrics.

Keep unjudged annotations distinct from accepted grade 0. Explain that the evaluator assigns zero gain to unjudged retrieved documents when calculating ranking metrics; this computational convention does not establish irrelevance. Label partial-positive-only evaluations as calibration diagnostics.

Group variants and related theorem families before estimating uncertainty. Prespecify the comparison family and use family-grouped paired inference after family review. Use Holm correction for confirmatory multiple comparisons; label additional analyses exploratory. Do not report independent-family uncertainty using unreviewed grouping components as if they were certified mathematical families.

## Preserve the development/test boundary

Keep all exposed material in development. Reserve fresh source groups before generation and tuning. Validate recorded overlaps automatically and review mathematical family equivalences separately. Keep held-out declarations searchable while excluding their families from supervised training examples.

Freeze test membership, interpretations and judgments before final scoring. Move any test family used for model, prompt or threshold selection back to development and replace it. Report zero final test cases until those checks are complete.

## Bound the claims

Separate local reproduction, first-stage target recovery, fixed-pool reranking and synthetic formal-consistency probes. Do not combine their counts into one accuracy measure. Keep extraction, label construction and candidate loss distinct in failure analysis.

Limit the current results to engineering diagnostics. Require completed relevance review and a frozen test collection before claiming search-quality improvements or publishing a leaderboard.
