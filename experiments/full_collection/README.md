# Full collection replay

This workflow schedules every record from the supplied query collections. It
deduplicates only identical query text with the same package filters, and keeps
all source memberships. It has no sample-size or category cap.

Keep inputs and output directories outside Git. A source manifest is an object
with a `sources` list. Each entry has `name`, `kind` and an absolute `path`.
The adapters support usage logs, discussion-derived queries, MathlibQR, MathlibMPR,
FATE-H and earlier case collections. Adapter identifiers are defined in
`collection.py`. Use the original local exports and pinned public references.
The earlier preparation artifacts contain copies and annotations of those
queries; they are not extra independent observations.

```sh
python collection.py --sources /external/sources.json --out /external/collection
python run.py --cases /external/collection/cases.json \
  --data /external/corpus --models /external/models.json --out /external/run
python score.py --cases /external/collection/cases.json \
  --run /external/run --out /external/scores
python report.py --summary /external/scores/summary.json \
  --out /external/aggregate-report.md
python -m unittest discover -s . -p test_full_collection.py -v
```

Use the pinned engine environment described in the candidate-selection
workflow and install this benchmark project's dependencies, including pandas.
The source and model hashes are recorded before retrieval. Repeating
the run command resumes only an unchanged schedule prefix with identical
inputs. It refuses a corrupt or partial journal line; inspect and preserve that
line before repairing a checkpoint. Scoring requires a complete journal whose
hash matches the completion record.

The first-stage settings are BM25 depth 1,000 and dense depth 1,000. Reranking
uses 25 candidates, with up to 25 returned results. All original package filters
are retained. Raw retrieval-stage rankings precede package filtering. Compare
the same candidate pool to isolate reranking. Recorded timings include input
inspection and are not production serving latency.

## Categories

Every request receives the existing offline `surface`, `intent_cue` and
`domain_cue` labels. Intent and domain are unvalidated cues, and unknown values
are preserved. Source-supplied styles, forms and domains remain separate fields.

The five primary forms use this precedence: an identifier-only query is `name`;
a proof state or formal statement is `formula`; mixed identifier text is `mixed`;
symbolic or LaTeX input is `mixed` when its measured English function-word share
is at least 0.1, otherwise `formula`; remaining input is `prose` when question-like
or at that function-word threshold, otherwise `keywords`. Empty input has its
own category and is retained. These rules are independent of relevance labels.
They do not reproduce the earlier Gaussian-mixture cluster IDs.

## Adapter comparison

`adapter_ablation.py` evaluates every request that has recorded targets on its
unchanged baseline candidate pool. It uses a yes/no answer head and chat wrapping
compatible with the Qwen model card, with a custom short system instruction.
The two conditions use total input limits of 256 and 512 tokens. The initial
comparison changes both the answer head and input wrapper; it does not identify
their separate effects. The wrapper consumes part of the total token budget.
The context-length comparison keeps that wrapper fixed.

This is a separate exploratory experiment. It leaves the engine baseline and
production unchanged. `score_adapter.py` reports each source separately and
uses paired topic/target-group bootstrap intervals. `diagnose.py` locates the
first observed loss of each recorded target in the baseline pipeline. Selection
has a 500-candidate cap before the final 25-candidate reranker pool.

## Corrected engine replay

`replay_reranker.py` imports the corrected production client from an isolated
engine checkout and rescores every distinct request on its frozen baseline pool.
Set `PYTHONPATH` to that checkout's `src` directory without changing the environment
used by a running baseline. The runner reads the engine's context-length constant,
records source hashes, checks candidate identities and preserves output filters.
It can follow a still-running baseline journal. Its output is accepted only after
the full schedule and baseline integrity checks pass.

```sh
PYTHONPATH=/external/corrected-engine/src python replay_reranker.py \
  --cases /external/collection/cases.json --base /external/run \
  --data /external/corpus --out /external/corrected-run
python score.py --cases /external/collection/cases.json \
  --run /external/corrected-run --out /external/corrected-scores
python report.py --summary /external/corrected-scores/summary.json \
  --out /external/corrected-report.md
```

This executes the actual corrected reranker on all requests, including unlabelled
ones. Retrieval is reused from the baseline, so replay timings exclude retrieval.
It is a controlled comparison of ranking on fixed pools. The corrected aggregate
report includes every available source/category breakdown.

## Analysis and preprint

Run these steps after the required journals are complete. The adapter check can
run once every target-bearing request has a production-client record; it reports
floating-point and ranking differences without requiring bitwise equality.

```sh
python diagnose.py --cases /external/collection/cases.json \
  --run /external/run --scores /external/scores --out /external/diagnosis.json
python score_adapter.py --cases /external/collection/cases.json \
  --base /external/run --ablation /external/adapter --out /external/adapter-summary.json
python check_adapter.py --cases /external/collection/cases.json \
  --ablation /external/adapter --corrected /external/corrected-run \
  --out /external/adapter-check.json
python compare_replay.py --cases /external/collection/cases.json \
  --base /external/run --corrected /external/corrected-run \
  --base-scores /external/scores --corrected-scores /external/corrected-scores \
  --out /external/comparison.json
python preprint.py --summary /external/scores/summary.json \
  --diagnosis /external/diagnosis.json --adapter /external/adapter-summary.json \
  --corrected /external/corrected-scores/summary.json \
  --comparison /external/comparison.json --adapter-check /external/adapter-check.json \
  --out /external/preprint.md
```

Review the generated prose against the recorded conditions before publication.

Reports use neutral source identifiers. For an archive with earlier identifiers,
pass `--source-aliases /external/source-aliases.json` to `report.py` and
`preprint.py`. This external object maps exact string labels to their reporting
aliases. The renderer rejects key collisions and leaves numeric measurements
unchanged. Keep the original provenance and alias mapping with the external
artifacts; do not rewrite frozen inputs or execution contracts.

The campaign's original corrected-client journal copied the baseline's `results`
trace stage and timing diagnostics while recording the new returned ranking in
`results` and `fixed_pool`. Evaluation reads those returned results and scores.
`replay_trace.py` writes a derived journal with the trace's result order synchronized
and copied timings explicitly labelled as baseline timings. It verifies that all
inference fields remain unchanged, records the parent hashes and preserves the
original journal and executed source. For that archive, run this normalization
before scoring and use the derived directory as `--run`/`--corrected`:

```sh
python replay_trace.py --run /external/corrected-run \
  --out /external/corrected-normalized
```

The current runner emits this corrected trace metadata directly, including for
empty results and failed baseline requests. That bookkeeping fix was applied after
the campaign completed; the exact earlier runner remains archived with its journal.

## Labels and denominators

MathlibQR uses its upstream single target. MathlibMPR preserves each alternative
premise set and evaluates both the natural and formal query. Complete-route
success requires one entire recorded route in the cutoff.

Declaration links in discussion replies are candidate-target proxies. They are not
accepted relevance judgments. Historical proposed targets retain that status.
Usage logs and FATE-H have no declaration-relevance labels in these inputs.
The frozen historical test request file also has no target lists; its separate
graded annotation package retains the assisted-v2 pilot's own reporting scope.
They receive operational statistics and recorded rankings, with relevance
metrics unavailable. The workflow neither fabricates judgments nor turns an
unjudged result into a negative label.

Missing target names stay in the denominator. Errors receive zero recovery on
labelled cases and remain visible in operational counts. Per-source counts
include repeated memberships; the inventory also reports distinct requests.
No combined relevance score mixes sources with different label types.

Publish only aggregate Markdown. Keep raw queries, source inventories, per-case
scores and run journals external. The report suppresses usage-log category cells
with fewer than ten records. Apply the repository's publication check before
committing, and review text content as well as paths.
