# Candidate selection experiments

The runner compares reranking depth, zero-score BM25 exclusion and dependency
boosting before reranking. Models, input rendering and final weights stay fixed.

## Prepare the engine

Use a separate checkout at the base recorded in `patches/bases.json`.
The preparation command refuses a different base or a dirty worktree.

```sh
python experiments/candidate_selection/prepare_engine.py --checkout /external/engine
python -m pip install -e "/external/engine[local]" pytest pytest-asyncio
```

The helper applies the engine patch and copies the runner into the engine's
scripts directory. Corpus files, local model snapshots and queries are supplied
externally. Record their revisions and hashes alongside each run.

The runner accepts an external query list with `id`, `query`, `category`,
`relevant` declaration names and optional `packages`. These labels must be
reviewed for the intended experiment. Use the offline preparation workflow
before turning proposed targets into scored labels.

From the prepared engine checkout:

```sh
python -m scripts.candidate_selection --help
```

The runner refuses existing output files and verifies that labeled targets are
available in the corpus and requested package scope. It warms the engine and
shuffles query/variant order. Errors stop this experiment runner. For operational
evaluation, retain failed and missing requests in the offline run contract.

## Traces and interpretation

Traces record candidate identities through lexical and semantic retrieval,
fusion, selection, filtering, reranker input and final output. Timings include
trace overhead and are not serving load tests.

Disabling the selection boost preserves the dependency term in the final score.
Increasing the pool also changes pool-normalized final score components.
Unknown relevant declarations can be absent from supplied labels. Report
judgment coverage and keep candidate-name recovery distinct from reviewed
mathematical relevance.

## Validation

Run the invented fixtures from this directory:

```sh
python -m pytest -q
```

The tests use SQLite, BM25 and FAISS with fake model scores. They require the
patched engine and its local dependencies, without downloading model weights.

Engine-derived code and fixtures retain their Apache-2.0 attribution in
`LICENSE.LeanExplore`.

## Reproduce development diagnostics

Use `diagnostic_replay.py` with external cases in the offline workflow format.
Require every case to have `split: development` and match the database digest.
Supply a local model manifest with entries for the embedding and reranker model,
including `path` and `revision`. Use the prepared engine environment described
above; do not install model weights into this repository.

```sh
python experiments/candidate_selection/diagnostic_replay.py \
  --cases /external/cases.json --data /external/corpus \
  --models /external/models.json --out /external/diagnostic-run
```

Retain `replay.json` and `executed_runner.py`. Inspect `scheduled_ids`, per-request
status, stage IDs, exact-name lookup, the input audit and fixed-pool scores.
Resolve stage IDs using the pinned database. Compare lexical, semantic, fusion
and selection prefixes at the same depth. Keep the final dependency ablation
separate from removing the dependency boost before candidate selection.

Use `current_mixture`, `without_final_dependency` and `neural_only` on identical
candidate names. Do not infer relevance improvement from a changed order.
Record the model snapshots and their weight/tokenizer inventories alongside the
run; the runner records source and corpus/index file hashes, but does not certify
missing upstream build provenance.

Treat an interrupted checkpoint as incomplete. Account for scheduled IDs without
records as missing requests until a validated continuation completes them. Start
a new output directory for each attempt and retain cancellation records. Use
tracing timings only for diagnostic cost accounting.

## Check controlled input representations

Run the small invented controls with an explicit local Lean executable:

```sh
python experiments/candidate_selection/representation_probe.py \
  --models /external/models.json --lean /path/to/lean \
  --out /external/representation-probe
```

Verify four true statements and two counterexamples before scoring the fixed
pairs under description-only, formal-only and combined inputs. Retain the Lean
source, verifier output, runner source, input hashes, token counts and raw scores.
Do not interpret the deliberately false candidate statements as indexed
library declarations. Treat the results as a formal-consistency diagnostic,
not human relevance judgments or evidence of corpus-wide retrieval quality.

## Evaluate frozen test and external reference profiles

Use `--frozen-evaluation` only with the matching assisted test freeze. Require
`validation_profile: assisted-v1`, test-only cases, the recorded query hash and
the fixed ten-candidate configuration. Keep these exposed queries out of later
claims about a fresh holdout.

Use `--external-reference` for the separate MathlibQR condition. Require
`validation_profile: mathlibqr-remapped-v1`, development-only reference cases
and a contract with `phase: before_reference_retrieval`, `cases_sha256` and
`settings`. Set `bm25_k` and `faiss_k` to 1000, `rerank_top` and `limit` to 100,
`dependency_boost` to true, `exclude_zero_bm25` to false and `seed` to 42.
Record the initial runner hash in the contract and retain each executed source.
Do not combine the reference and assisted-test flags.

Store per-request records in the append-only `records.jsonl` journal and retain
periodic `replay.json` checkpoints. Set `--checkpoint-every` to a positive number
of completed requests. Use `--resume` only for a reference checkpoint with an
unchanged schedule prefix, corpus, model manifest, engine source and settings.
Keep the old output and account separately for interrupted attempts. The runner
resumes from completed checkpoint records; it does not recover partial journal
entries automatically.

Run `reference_score.py` against the external root to preserve upstream
single-gold scoring, full/shared171/present-only slices and target-group
resampling. Follow the [reproduction guide](../../docs/benchmark-reproduction.md)
for complete commands. Read [assisted-v2](../../docs/benchmark-assisted-v2.md)
for results and limits of the ten- and 100-candidate comparisons.
