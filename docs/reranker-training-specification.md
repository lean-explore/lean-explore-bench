# Reranker training specification

Use this specification to prepare a bounded training experiment after annotation. Do not start training from proposed targets or from the four accepted calibration positives alone.

## Define the task and input

Train a reranker for declaration search. Preserve the query, the declaration identity, the complete task interpretation and the graded relevance decision. Keep proof-route and premise-selection examples in separate tracks.

Use the existing name-plus-description rendering as the initial reference. Record the exact rendered bytes, tokenizer revision, query instruction, truncation policy and model revision. Compare a formal-statement rendering only when its complete assumptions have been verified. Do not choose a training representation from the two synthetic representation controls alone.

## Construct examples

Accept grades 2 and 3 as positive examples under the frozen task rubric. Accept grade 0 as a negative only after review of assumptions, equivalents and reasonable specializations. Exclude grade 1 and unresolved judgments from the initial binary training objective. Preserve all original grades in the source records.

Sample hard-negative candidates from lexical, semantic and fused retrieval, with their generating run and rank in a separate audit. Hide that information during annotation. Treat a target absent from the corpus as an availability issue, not a negative example. Never convert an unjudged candidate into a negative.

Retain these fields for each training pair:

| Field | Required content |
| --- | --- |
| Task | Query text, query form, intent, interpretation revision and ambiguity status |
| Grouping | Original request, equivalent variants, target family and source-group identifiers |
| Corpus | Snapshot identity, canonical declaration ID and availability |
| Input | Rendering revision, exact input hash, tokenizer revision and truncation evidence |
| Judgment | Original grade, accepted status, reviewer identifier and independent-review status |
| Evidence | Assumptions checked, equivalences considered and adjudication references |
| Generation | Generator revision, prompt/input hashes and answer-exposure status where applicable |

## Separate training from evaluation

Keep the current pilot and imported reference collection development-only. Acquire separate reviewed training families. Group shared requests, aliases, equivalent theorems and generated variants before splitting. Reject any train/dev/test overlap in the recorded groups. Review mathematical-family assignments rather than relying solely on name prefixes.

Hold evaluation families out of supervised examples while retaining their declarations in the searchable corpus. Preserve a reservation ledger for test material and record any exposure that requires reassignment to development. Do not use reserved-test scores to choose negatives, prompts, hyperparameters or stopping points.

## Prespecify a bounded first experiment

Start with at most 500 reviewed query-document judgments from separate training families. Construct within-query positive/negative pairs only where both judgments are accepted. Use a pairwise logistic ranking loss; leave pairs with uncertain ordering out. Do not treat same-query or same-family examples as implicit in-batch negatives.

Compare one trained checkpoint with the unchanged reranker on frozen development pools. Keep candidate identities, input rendering and final mixture fixed for the primary comparison. Report neural-only rankings separately so that changes in final mixture weights do not masquerade as training effects.

Record optimizer, learning rate, batch size, precision, seed, number of updates and trainable parameters before training. Use one seed and a maximum of one epoch for the feasibility run. Stop at a two-GPU-hour cap. Treat these as proposed limits, not measured runtime or a promise that training will fit. Run a memory and throughput pilot before selecting full fine-tuning or parameter-efficient training.

Evaluate a form-transfer split separately from the family-held-out development split. Report judged coverage and family-grouped uncertainty; label this small experiment exploratory. Freeze later test evaluation before inspecting test results.

## Estimate cost without inventing measurements

For 500 pair judgments, budget 8.3, 16.7 or 33.3 reviewer-hours at one, two or four minutes per pair. Add query interpretation, independent review and adjudication. Use these as scenarios until active review time has been measured.

Estimate compute from measured training throughput: divide tokenized training tokens times epochs by observed training tokens per second. Add checkpoint evaluation and startup time. Do not extrapolate training speed from inference-only timing. Convert GPU hours to money only after recording the applicable resource rate.

Use local cached models for the initial feasibility experiment and budget zero API calls. Keep the current two-week deliverable at the data contract and experiment specification; schedule training after annotation capacity and data separation are established.