# Evaluation protocol

This document describes how the LeanExplore pilot grades relevance and scores search engines. The
rubric is still a draft: it has not been validated by independent human reviewers, and the results
in the [pilot report](pilot-report.md) are engineering diagnostics, not a leaderboard.

## Cases and queries

A case is one information need with a documented interpretation. Its query variants stay attached
to it and are not counted as independent observations. Query form, intent, mathematical area,
difficulty, provenance and answerability are recorded as separate axes.

Development cases are spread over five query forms: declaration name, keywords, natural-language
prose, formula or formal statement, and mixed text and code. The planned allocation is 20 cases per
form if the pilot reaches 100 cases. The balance exists for diagnostic coverage and says nothing
about how often real users issue each form.

## Relevance grades

The reviewer settles the intended need before looking at candidates, then grades each
query-document pair against the candidate's full statement.

| Grade | Meaning |
|---:|---|
| 3 | Directly satisfies the need, or is an equivalent result that is equally usable. |
| 2 | Usable after a documented, reasonable adaptation, such as routine specialization of a more general result. |
| 1 | Related or supporting, but not sufficient for the task. |
| 0 | Irrelevant, or mathematically unusable under the stated assumptions. |

Grades depend on the task. An exact-name query is graded as exact lookup unless its interpretation
explicitly admits mathematical alternatives, and an explicit task restriction takes precedence over
the general-result rule for grade 2. A pair whose relevance is uncertain is left unjudged.

## Answerability

Whether a target exists in the pinned corpus is recorded separately from relevance. The statuses
are: target present, target name absent, availability unresolved, and expert-reviewed absence of
any adequate answer. A failed name lookup, a failed engine search or a negative pool does not show
that no adequate answer exists, because an equivalent older result may be present. A repaired
query becomes a new, answer-informed development variant; the original run and grades are not
carried over to it.

## Pooling and review

Candidates are pooled from several first-stage retrieval channels and from selected final rankings,
then deduplicated. Pools start from the top 10 results of each run plus proposed targets, which
enter as candidates and not as accepted labels. Deeper candidates are audited where traces reveal
a miss. Engine identity and rank are hidden from the reviewer.

Current labels come from an assisted profile: an AI assistant proposed 402 grades and left 17
pairs unresolved. Four earlier human decisions take precedence over them. No inter-rater agreement
is reported, because no independent second review has been done.
[Human review](human-review.md) describes how labels are corrected.

## Metrics

| Metric | Definition | Used for |
|---|---|---|
| Success@1/5/10 | At least one acceptable answer (grade 2 or 3) in the top k. | Known-item tasks |
| MRR@10 | Reciprocal rank of the first acceptable answer in the top 10. | Known-item tasks |
| nDCG@10 | Graded ranking quality with linear gain equal to the grade. | Graded declaration search |
| Success@50/100, Recall@50/100 | Recall is the fraction of known relevant declarations retrieved. | Candidate generation |
| Judged@10 | Fraction of the top 10 that has a judgment. | Label coverage |

Because judgments are incomplete, recall is relative to known answers. Judged@10 and pool depth
are therefore reported next to every quality metric. Results are given per query form and per
intent, together with a declared balanced summary.

## Unjudged documents and failed requests

The evaluator gives an unjudged retrieved document zero gain. This is a computational convention
and does not establish that the document is irrelevant. Judged@k divides by k, so short responses
and unjudged results both lower it.

Every scheduled request stays in the denominator. Errors and timeouts are recorded as failures with
no documents, and a query missing from a run counts as a failure, not as an exclusion. A cutoff
deeper than the candidate lists an engine actually returned is reported as unavailable.

## Splits and leakage

Split units are the connected components of a grouping graph built from source thread, original
request, paraphrases, declaration aliases and equivalents, and theorem family. These components
are reported separately from mathematical families, which remain provisional: a component can
merge tasks that are not one family.

All previously explored material is development-only. Test cases come from fresh sources reserved
before tuning. Model choices, prompts, training mixtures and thresholds use development evidence
only; a test family that informs any of them moves to development and is replaced. Held-out
families are excluded from supervised training examples, but their declarations stay searchable.

The pilot test set is a frozen set of 30 queries. Its eight prespecified configurations were run
without tuning on test results, and the queries are now exposed. The two source documents disagree
here: one records this run as complete, and the other says to report zero final test cases until
family review is finished.

## Statistical comparison

Comparisons are paired and grouped by family; the [offline tools](../tools/offline/README.md)
provide group bootstrap intervals and a paired group-randomization test. The set of comparisons is
small and fixed in advance. Confirmatory comparisons use the Holm correction, and any other
analysis is labelled exploratory. Reports give the number of independent families alongside the
number of queries. Small differences in the pilot are not a reliable basis for choosing between
models.
