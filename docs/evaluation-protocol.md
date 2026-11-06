# LeanExplore pilot evaluation protocol

Proposed protocol for the first two weeks. Freeze a numbered version after calibration. Record later changes and rerun affected development judgments. The final test follows the frozen version.

## What each case represents

A case is an information need, with query variants attached. Give it a source record, task-family ID, intended output, corpus scope and review status. Variants are not independent observations. Separate query form, intent, mathematical area, difficulty, provenance and answerability; they are different axes.

| Primary query form | Initial development allocation if the pilot reaches 100 cases | Intended coverage |
|---|---:|---|
| Declaration name | 20 | Exact names, partial namespaces, spelling/case variants; distinguish exact lookup from requests for alternatives |
| Keywords | 20 | Short mathematical terms and terse requests without a full sentence |
| Natural-language prose | 20 | Explicit information needs, including assumptions and definitions |
| Formula or formal statement | 20 | Lean or mathematical expressions, notation changes and fine mathematical distinctions |
| Mixed text and code | 20 | Names/formulas combined with prose or relevant local hypotheses |

Assign one primary form using a written tie-breaking rule; preserve secondary tags. Balance is for diagnostic coverage, not a claim about usage frequency. The old single-day log is dominated by one client; the later export also has channel and first-day biases. Neither determines a population mixture.

Aim to source no more than half the pilot from any one previously explored source tranche. Fill the rest with independently curated public tasks, including declaration-name needs and context-sensitive mathematical cases. This is a proposed quota to test during calibration. Cover several mathematical areas without letting one family generate most examples. Do not require a full Cartesian product of every axis.

Proof-state premise selection, complete proof routes and verified no-answer tasks are separate diagnostic tracks. Add them only when their judgments and metrics are defined. They should not silently dilute the primary declaration-search score.

## Source and generation rules

Keep previously explored synthetic queries development-only. Treat upstream answer-status flags as source annotations, not final benchmark correctness. Preserve the distinction between an original question, a synthetic reformulation and a proposed answer.

Generate question-derived queries from question-only inputs. Record the input actually shown to the generator; do not infer blinding from the absence of an exact target name. Declaration-to-query generation is a separate, explicitly synthetic source. Do not describe it as an observed user need.

Audit generation exposure and query repairs as separate fields. Reconcile all categories against the total before reporting a blinding breakdown.

For every source, retain attribution and redistribution status. Keep private usage logs and their annotations out of the public collection. The source inventory and public release are separate products.

## Split and test reservation

Build grouping constraints from source thread, original request, paraphrases, declaration aliases/equivalents and theorem family. Use their connected components as split units and inspect oversized components. Record how theorem families were assigned; a name-prefix heuristic alone is insufficient.

Before tuning, reserve fresh sources intended to produce about 30 test cases outside previously explored sources and development families. Keep the reservation manifest separate from development inputs. The reservation is a starting tranche, not a claim that 30 cases establish a reliable leaderboard.

Benchmark designers may fix form/domain strata, but model choices, prompts, training mixtures and thresholds must use development evidence only. If an affected test family informs those choices, reclassify it as development and replace it. Freeze test membership and judgments before the final comparison; do not repeatedly check test scores while iterating.

For training experiments, hold out task and target families from supervised training examples, not from the searchable corpus. Test declarations must remain searchable. Compare cross-form transfer separately from cross-family transfer; different query styles are not automatically independent tasks.

## Review and relevance

Review the query's intended need before looking at suggested answers. Resolve target availability in the pinned corpus. Inspect assumptions, types, imports and alternative declarations. Keep candidate availability separate from whether any valid answer exists.

For each query-document pair, record a relation such as direct answer, equivalent answer, usable specialization, supporting lemma, irrelevant or unresolved. Assign a grade according to the task:

- 3: directly satisfies the need, including an equivalent result when equally usable.
- 2: usable with documented, reasonable adaptation.
- 1: related or supporting, but insufficient for this task by itself.
- 0: irrelevant or mathematically unusable under the stated assumptions.

These grades are not a universal ordering of theorem relations. A supporting lemma can satisfy a premise-selection task. Multi-premise routes need their own annotations and scoring.

Use explicit statuses for target present, target name absent, unresolved availability and expert-reviewed absence of an adequate answer within the defined corpus/task. A newly introduced name, failed engine search or failed LLM judge does not prove absence of equivalent older results. Keep unknown relevance unjudged. For ranking calculations, disclose that the evaluator assigns unjudged documents zero gain; this does not establish irrelevance.

Pool deduplicated candidates from diverse retrieval channels and selected reranked results. Start with top-10 outputs plus proposed answers; audit deeper candidates where traces reveal misses. Record pool depth and judged coverage. A 100-case pilot does not imply exhaustive judgments of all top-50 pools.

Hide engine identity and rank during judgments. Preserve individual reviews before adjudication. Request independent second judgments on the ten calibration cases and a stratified subset of the remaining cases, sized from available reviewer hours. Report actual double-review counts and disagreements; do not fabricate agreement from a single assessor or use an LLM as a second human.

## Metrics and reporting

Reuse the existing evaluator: linear gain equals grade, binary relevance is grade at least 2. Use Success@1/5/10 and MRR@10 for known-item tasks; nDCG@10 for graded declaration search. For candidate generation, report Success@50/100 and recall of known relevant declarations at those cutoffs. Success means at least one acceptable answer; recall measures the fraction of known relevant answers retrieved.

With incomplete judgments, recall is relative to known answers and oracle rankings are relative to judged candidates. Report Judged@10 and pool construction. Record unsupported cutoffs as unavailable. Preserve errors, timeouts and missing requests in operational denominators.

Report per-form and per-intent results, a declared balanced summary, and independent family counts. Use family-grouped paired comparisons and uncertainty intervals. Prespecify a small comparison family; use Holm correction for confirmatory multiple tests or label additional analyses exploratory. Small pilot differences are not reliable model-selection guarantees.

Separate query ambiguity, faulty labels, target absence, extraction/index omission, candidate-selection loss, reranker error, final-mixture regression and request failure. Record the first observed failure stage and any contributing causes.

## Minimal experiment sequence

| Experiment | Question | Controls and output |
|---|---|---|
| E0, reproduction | Can we replay the recorded baseline? | Corpus and model hashes, patches, seeds, hardware and settings; rankings plus stage traces |
| E1, first-stage channels | Which channels add useful candidates? | Exact-name reference, lexical-only, dense-only and current fusion on one corpus; fixed final candidate budgets of 50/100; union overlap and marginal coverage |
| E2, existing signals | What does dependency boosting contribute? | Separate pre-rerank boost from the dependency term after reranking; current mixture versus neural score alone on fixed candidates |
| E3, mathematical inputs | Can models distinguish equations under the right assumptions? | Same query-candidate pairs; name/description, trusted formal statement, and combined input; embedding similarity versus reranker scores |

E0 and E1 take priority. Run E2 and E3 as bounded diagnostics within the Week 2 budget. Do not expand into a full grid of methods, depths and models.

BM25+ appears in name retrieval and in the final informal-text mixture. Ablate these uses separately. A positive BM25+ score may reflect smoothing; use verified token overlap when testing lexical-match gates. A channel ablation does not establish whether BM25+ beats BM25: that requires matched documents, tokenization and parameters. Keep that controlled variant comparison optional.

Treat exact-name lookup as a scoped route respecting package/version filters. Treat a gate based on a word such as scheme as an untested routing hypothesis. Compare any routing rule with an unrestricted union and count the relevant candidates it excludes. Do not assume such gates are established mathematical-search practice.

For E3, use positive transformations such as valid bound-variable renaming and checked equivalent formulations; use reviewed near-misses involving quantifiers, hypotheses, types or inequality direction. A changed symbol is not automatically a negative. Keep a challenge-set score separate from ordinary retrieval accuracy.

The inspected reranker receives name plus informalization, without a separate formal-signature field. Formal-input experiments must include complete hypotheses and track truncation. Use existing trusted metadata for the bounded sample; a new general parser must not block the pilot.

On fixed pools, compute the best ranking achievable from the judged candidates to distinguish missing-candidate failures from reranking headroom. Then check end-to-end behavior with the original request and cost budget. The final score currently mixes neural, lexical, dependency and fuzzy-name signals, so it is not a pure reranker measurement.

## Training plan after diagnosis

Specify the reranker input and desired notion of relevance first. Build positives and hard negatives from several retrieval channels, reviewing false negatives and equivalents. Hold source and theorem families out across train/dev/test; record generation model, prompt and revisions. Include a cross-bucket transfer experiment rather than tuning solely to the benchmark mixture.

Week 2 delivers a data and training specification, with a cost estimate. A full fine-tuning run is not required for the November benchmark paper.
