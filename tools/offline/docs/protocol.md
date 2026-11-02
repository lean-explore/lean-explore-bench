# Proposed protocol: Lean search for people and agents

Version 0.1, 28 October 2026. This specifies experiments to run.
The log audit and evaluator are available; human judgments, engine comparisons,
and Lean proof outcomes have not yet been collected.

## Research questions

What need triggers a query? How does formulation depend on context and channel?
Which declarations are useful? Does better ranking improve task completion?
What does improvement cost in time, calls, and tokens?

Combine logs, annotation, controlled tasks, and observed outcomes.
Code-search studies already combine logs and surveys; stated goals and
log-based interpretations remain different evidence.
[Sadowski et al., 2015](https://research.google.com/pubs/archive/43835.pdf).

## Taxonomy on independent axes

| Axis | Labels or observations | Evidence |
|---|---|---|
| Channel | web, web_account, api, mcp | Recorded field |
| Actor | confirmed human, confirmed agent, unknown | Self-report or client attestation, never channel alone |
| Intent | known item, lemma, next step, premise bundle, definition/API, example, explanation, exploration, formalization, debugging, multiple, unknown | Annotation with provenance |
| Expected output | declaration, premise set, step, proof, explanation, example | Annotation or task objective |
| Form | name, keywords, prose, formula, LaTeX, proof state, Lean snippet, mixed | Rules plus human checks |
| Specificity | explicit target, partial name, conceptual description, ambiguous need | Independent assessors |
| Context | hypotheses, goal, imports, version, snippet, none | Inputs available to the engine |
| Domain | broad Mathlib/MSC class, multiple, unknown | Annotation; private-log topics stay private |
| Answerability | target present, name absent, verified no answer, unknown | Corpus inventory and expert assessment |
| Difficulty | lexical, semantic, specialization, equivalence, lemma composition | Assessor rubric |

Query length, syntax, and channel do not establish expertise or actor identity.
A short query may express a difficult need.

## Data and sampling

Keep private usage logs, public reference tasks, and new tasks with stated goals
as separate collections. Do not merge their scores without specifying the mixture.

For logs, retain request-frequency and distinct-request views.
Current identity uses NFC/whitespace-normalized text plus package filters,
preserving Lean case. Semantic deduplication is not implemented:
inspect near-duplicate families before fixing splits.

The initial pilot proposes 400 distinct requests across channel/form strata,
labelled independently by two annotators. This is a starting budget, not a proven
sample-size requirement. The review tool records stratum populations.
Weight estimates using the sampling design; unweighted pilot proportions do not
describe traffic. Very small samples may omit strata.

Compare the full export with the window excluding the first day.
Reserve a future time window for testing.
Keep paraphrases and queries sharing a target/proof family in one split.
Audit target and near-duplicate overlap across public sources.
A possible development split is 60/20/20 by groups, to be fixed after coverage
analysis. It has not been applied. Keep a closed test set out of tuning.

## Annotation

The review interface does not show automatic intent predictions.
Allow unknown and multiple intents. Distinguish interpretation, self-report,
and client attestation.

For the pilot, measure raw agreement, confusion matrices, Cohen's kappa for two
raters, and Krippendorff's alpha for suitable multi-rater/missing-label settings.
For multilabel tasks, report per-label agreement and F1.
Agreement is not truth: compare interpretations with stated goals where available.
Adjudicate disagreements and retain original labels.
Agreement statistics are not yet implemented in this prototype.

For relevance, pool the top 20-50 results from diverse systems; depth is a budget
parameter. Add deeper candidates and results from new systems.
Hide engine identity and rank; randomize presentation.
Check judgment coverage and leave-one-system-out sensitivity because pooling
can favour participating systems.
[NIST on pooling bias](https://www.nist.gov/publications/bias-and-limits-pooling-large-collections).

Proposed grades: 0 irrelevant/wrong; 1 related but insufficient; 2 usable with
reasonable adaptation; 3 directly satisfies the need.
Assess hypotheses, types, version, and imports.
Check equivalence/specialization in Lean when feasible.
Unassigned judgments are missing, not explicit negatives.

A local LLM may suggest labels after a human gold set exists.
Validate per channel, intent, language, and difficulty; inspect position,
verbosity, and model-family bias. Model labels are not gold.
Recent evidence includes both methodological objections and encouraging ranking
correlations, so validate in this domain.
[Soboroff, 2025](https://www.nist.gov/publications/dont-use-llms-make-relevance-judgments),
[Upadhyay et al., 2025](https://www.nist.gov/publications/large-scale-study-relevance-assessments-large-language-models-initial-look).

## Tracks and metrics

| Track | Task | Primary measurements | Controls |
|---|---|---|---|
| H1 | Recover a known declaration | Success@1/5/10, MRR@10 | Name variants, equivalents, coverage |
| H2 | Retrieve from prose/formulas | nDCG@10, Recall@50/100 | Graded relevance and judgment coverage |
| H3 | Explore, understand, or use results | Task success, time to useful result, blinded preference | User study; ranking is intermediate |
| A1 | Find a lemma for a local goal | Recall@k, next-step success | Same goal, context, prover, budget |
| A2 | Recover premises for a proof | Group recall, complete-route coverage | Interchangeable lemmas, alternative routes |
| A3 | Complete a proof | Verified proofs/budget, time and cost | Lean kernel, no sorry or unapproved axioms |
| N | Handle unanswerable/ambiguous needs | Correct/false abstention, false returns, success after clarification | Annotated answerability; errors separate |
| F | Index freshness | Target coverage, ingestion delay | Before/after snapshots; absent name does not exclude equivalents |

Separate target retrieval, premise recovery, and proof completion.
[LeanSearch v2](https://arxiv.org/html/2605.13137v2).
Include concise/ambiguous and context-enriched variants; test whether rewriting
improves ranking without changing the need.
[Lean Finder V2](https://arxiv.org/html/2610.30843v2).

The scorer implements ranking and premise coverage, not user studies or Lean
verification. `best_route_group_recall` takes the best annotated route:
this is our explicit convention, not a claim of parity with all published metrics.
`route_covered` requires a complete route without mixing incompatible routes.

Use linear nDCG gain equal to grade; binary relevance is grade >= 2.
Default cutoffs: 1, 5, 10, 20, 50, 100.
AP@k divides by min(k, number of known relevant documents), unlike untruncated AP.
Duplicates consume rank without extra credit.
`judged@k` divides by k: both short responses and unjudged results reduce it.
With incomplete pools, Recall covers known relevant documents.

Unknown answerability is excluded from relevance metrics, retained in
operational counts. Verified unanswerability uses explicit abstention metrics.
Cutoffs above a system's declared limit are unavailable, not flat curves.

## Systems, fairness, and ablations

Include exact-name/prefix search, BM25, symbolic Loogle, dense retrieval,
lexical/dense fusion, reranking, and specialized Lean engines.
Current candidates include LeanExplore, LeanSearch v2, Lean Finder V2,
and LeanGraphSearch. These are literature-motivated candidates, not results of
our experiments or a universal leaderboard.
[BEIR](https://github.com/beir-cellar/beir),
[Loogle](https://github.com/nomeata/loogle),
[LeanGraphSearch](https://arxiv.org/abs/2610.22339).

Pin Mathlib commit, Lean version, declaration renderer, filters, index, models,
numeric precision, hardware, and candidate budget.
Separate same-corpus local evaluation from hosted-product evaluation on each
service's own index; the latter also measures coverage and availability.

Ablate retrievers on an identical corpus, rerankers on a fixed pool, rewriting
with a fixed retriever, graph expansion on/off, and a fixed prover with/without
retrieval. Match agent tokens, time, calls, and attempts.
Repeat stochastic components with declared seeds.

## Robustness, performance, and statistics

Test typos, partial namespaces, variable renaming, Unicode/ASCII variants,
paraphrases, languages, empty/long input, invalid filters, missing hypotheses,
and out-of-domain requests. Verify meaning-preservation for transformations.
Measure degradation against original queries by task family.

Measure p50/p95/p99 latency, timeouts, failures, throughput at fixed concurrency,
warm/cold cache, memory, and cost. Prespecify timeouts and retry policies.
Missing requests remain failures. Use a controlled replica for load tests,
not public endpoints.

Report effect sizes, confidence intervals, and independent task counts.
Keep paraphrases in one statistical group.
The evaluator supplies group bootstrap intervals and paired group randomization.
Prespecify metric, seed, and comparisons. Apply Holm to planned comparison
families or label the analysis exploratory.
P-values are not improvement magnitudes.
[Urbano et al., SIGIR 2019](https://arxiv.org/abs/1905.11096).

Size the test from pilot task-level differences and a minimum useful effect,
using simulation. A 400-label pilot does not automatically provide sufficient
power for small differences or rare subgroups.

## Additional observations to collect

| Data | Purpose | Proposed collection |
|---|---|---|
| Requested limit, filters, index version | Client defaults versus quality | Search event with ephemeral ID |
| Ranked document IDs, scores, stages | Impressions and ablations | Public declaration IDs; private text separate |
| Stage latency, status, retries, timeout | Operational quality | All requests, including failures |
| Click, copy, document open | Possible utility | Link to specific impression |
| Stated intent and success | Actual goal and outcome | Voluntary micro-survey and controlled study |
| Reformulation/clarification | Completion across queries | Opt-in ephemeral linkage |
| Client type and attested actor | Human versus agent | Unknown by default |
| Goal, attempted lemma, Lean outcome | Utility to prover | Reproducible opt-in task |
| Tokens, cost, calls | Agent efficiency | Experimental-run counters |

Clicks and dwell time are not relevance: rank, interface, and task affect them.
For causal claims, use A/A checks, randomized A/B testing, sample-ratio checks,
and prespecified duration/primary metric.
Interleaving can compare ranking preference but needs validation against task
success. Choose a randomization unit limiting within-task contamination.
[Kohavi et al., 2007](https://ai.stanford.edu/~ronnyk/GuideControlledExperiments.pdf).

Do not retrofit persistent identifiers to reconstruct people/sessions in the
current log. Define collection and retention before activating future studies.

## Execution order

1. Audit and temporal sensitivity: completed.
2. Annotation pilot: interface ready; 400 requests need two independent reviews.
3. Fix corpus, tasks, rubrics, and splits; resolve coverage and licences.
4. Collect real rankings, pool candidates, obtain expert judgments.
5. Score tracks and paired comparisons; cross-check compatible fixtures with
   `trec_eval`.
6. Run Lean verification and user studies; then consider online experiments.

Release a dataset card, manifests, seeds, configurations, qrels, rankings, and
failure records using publishable data only.
Private logs and annotations do not automatically become public benchmark data.
