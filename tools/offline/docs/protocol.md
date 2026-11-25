# Proposed protocol for evaluating Lean search

Version 0.1, 28 October 2026. This document proposes experiments for measuring how well a
search engine serves people and automated agents looking for Lean declarations. It is a plan.
The tool in this directory implements the log audit, the annotation interface and the scorer;
the [pilot report](../../../docs/pilot-report.md) describes what has been run since.
[sources.md](sources.md) lists the references.

## Questions

What need triggers a query? Which declarations are useful? Does better ranking improve task
completion, and at what cost? Logs alone cannot answer these, so the protocol combines logs,
annotation, controlled tasks with stated goals, and observed outcomes.

## Describing a query

| Axis | Values |
|---|---|
| Actor | confirmed human, confirmed agent, unknown |
| Intent | known item, lemma, next step, premise bundle, definition or API, example, explanation, exploration, formalization, debugging, multiple, unknown |
| Form | name, keywords, prose, formula, LaTeX, proof state, Lean snippet, mixed |
| Answerability | target present, name absent, verified no answer, unknown |

Further axes are channel, expected output, specificity, supplied context, domain and
difficulty.
Query length, syntax and channel do not establish expertise or actor identity.

## Data and splits

Private usage logs, public reference tasks and new tasks with stated goals are separate
collections, scored separately. Two logged requests are identical when their text, after
Unicode NFC and whitespace normalization, and their package filters agree; Lean case is
preserved. Semantic deduplication is not implemented.

Paraphrases and queries that share a target or proof family stay in one split. A future time
window is reserved for testing.

## Annotation

The pilot budget is 400 distinct requests, stratified by channel and form and labelled
independently by two annotators. The review tool records stratum populations, because
unweighted pilot proportions do not describe traffic. The planned agreement measures are
Cohen's kappa and Krippendorff's alpha; neither is implemented yet.

## Relevance judgments

Candidates are pooled from the top 20 to 50 results of diverse systems and shown in random
order without engine identity or rank. Pooling can favour the participating systems, so
judgment coverage and leave-one-system-out sensitivity are checked.

Grades are 3 (directly satisfies the need), 2 (usable with reasonable adaptation), 1 (related
but insufficient) and 0 (irrelevant or wrong). A pair without a judgment is missing, not
negative. A language model may suggest labels only after a human gold set exists, and its
labels are not gold.

## Tracks

| Track | Task | Main measurements |
|---|---|---|
| Human, known item | Recover a known declaration | Success@1/5/10, MRR@10 |
| Human, description | Retrieve from prose or formulas | nDCG@10, Recall@50/100 |
| Human, use | Explore or use results | Task success, time, blinded preference |
| Agent, lemma | Find a lemma for a goal | Recall@k, next-step success |
| Agent, premises | Recover the premises of a proof | Group recall, route coverage |
| Agent, proof | Complete a proof | Proofs verified by Lean, time, cost |
| No answer | Unanswerable or ambiguous needs | Correct and false abstention |
| Freshness | Index new declarations | Target coverage, ingestion delay |

## Metrics as implemented

The scorer covers ranking and premise coverage, not user studies or Lean verification.

- nDCG uses the grade as linear gain. Binary metrics count grades 2 and 3 as relevant.
- The default cutoffs are 1, 5, 10, 20, 50 and 100. A cutoff above the depth a system
  declares is unavailable.
- AP@k divides by min(k, number of known relevant documents).
- A duplicate result consumes its rank and earns nothing.
- `judged@k` divides by k, so short responses and unjudged results both lower it.
- Queries of unknown answerability receive no relevance scores; unanswerable queries are
  scored on abstention.

## Systems and controls

Candidate systems are exact-name search, BM25, Loogle, dense retrieval, fusion, reranking, and
the Lean engines LeanExplore, LeanSearch v2, Lean Finder V2 and LeanGraphSearch. Each run pins
the Mathlib commit, Lean version, index, models and candidate budget. Evaluation on one shared
corpus is kept apart from evaluation of hosted services on their own indices.

## Statistics

Paraphrases form one statistical group. The evaluator provides group bootstrap intervals and
a paired group randomization test. Metric, seed and comparisons are fixed in advance, with
Holm correction for planned families.
