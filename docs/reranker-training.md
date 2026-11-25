# Reranker training proposal

This is a proposal for a first reranker fine-tuning experiment; no training has been run. Training
waits on reviewed labels, because the four accepted calibration pairs and the unreviewed proposed
targets are not enough to train on.

## Task and input

The model reranks candidates for declaration search. Proof-route and premise-selection examples
are kept in separate tracks. The reference input is the existing rendering, declaration name plus
informal description. A rendering based on the formal statement is compared only where the
statement's complete assumptions have been verified; the two synthetic representation controls
are not sufficient grounds for choosing a representation.

## Examples

| Judgment | Use in training |
|---|---|
| Grade 2 or 3 | Positive |
| Grade 0, after review of assumptions, equivalents and reasonable specializations | Negative |
| Grade 1, or unresolved | Excluded from the initial binary objective |
| Unjudged, or target absent from the corpus | Never a negative |

Hard negatives are sampled from lexical, semantic and fused retrieval. The run and rank that
produced each one are hidden during annotation. Each pair keeps its original grade, reviewer, task
interpretation, grouping identifiers, corpus snapshot, input hash and tokenizer revision.

## Separation from evaluation

The current pilot and the imported reference collection stay development-only, so training needs
separately reviewed families. Shared requests, aliases, equivalent theorems and generated variants
are grouped before splitting, and any overlap between train, development and test is rejected.
Evaluation families are held out of the supervised examples, while their declarations remain
searchable.

## First experiment

| Setting | Proposed limit |
|---|---|
| Training data | At most 500 reviewed query-document judgments |
| Loss | Pairwise logistic ranking loss on within-query pairs with both judgments accepted |
| In-batch negatives | Same-query and same-family examples are not used as implicit negatives |
| Schedule | One seed, at most one epoch |
| Compute | Cap of two GPU-hours |

These are limits, not measured runtimes. A memory and throughput pilot decides between full
fine-tuning and parameter-efficient training.

One trained checkpoint is compared with the unchanged reranker on frozen development pools, with
candidates, input rendering and final score mixture held fixed. Neural-only rankings are reported
separately, so that a change in mixture weights is not mistaken for a training effect. The
experiment is exploratory.

## Cost

Judging 500 pairs takes 8.3, 16.7 or 33.3 reviewer-hours at one, two or four minutes per pair,
before query interpretation, independent review and adjudication. Active review time has not been
measured, so these are scenarios. Compute is estimated from measured training throughput, not
from inference timing. The experiment uses locally cached models and no API calls.
