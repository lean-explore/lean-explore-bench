# Pinned declaration metadata

This directory holds three prototypes for the extraction side of a Lean search index: an
extractor that reads full declaration types from a pinned Lean project, a Lean module that
validates the extracted records with proofs about what it preserves, and a cache that decides
which build steps must be repeated when sources change. The design is described in
[extraction and cache](../../docs/extraction-and-cache.md).

## Extractor

```text
python extract_metadata.py --project PINNED_MATHLIB_CHECKOUT --request EXTERNAL_REQUEST_JSON --out NEW_EXTERNAL_OUTPUT_DIRECTORY
```

The request is a JSON object with `revision`, `toolchain`, `modules` and `names`. The project
must be at that revision without tracked modifications, and `lake env lean --version` must
match the toolchain. The output directory must be new and outside any Git checkout. It
receives:

| File | Content |
|---|---|
| `Extract.lean` | The generated Lean program |
| `lean-output.txt` | Compiler output, also written when extraction fails |
| `metadata.json` | One record per name, plus revision, Lean version, platform and hashes |

Each record gives the declaration kind, universe parameters, a fully explicit type
(`rendered_type`), a readable type (`readable_type`) and the elaborated expression
(`type_expression`). A missing or duplicate name, a metavariable or a loose bound variable
fails the run without `metadata.json`.

## Verified normalization

```text
lean VerifiedNormalization.lean
lean --run VerifiedNormalization.lean INPUT_ENVELOPE_JSON NEW_OUTPUT_JSON
```

The first command checks the proofs; the second validates an envelope with the keys
`schema_version`, `environment`, `artifact_digest`, `declarations` and `aliases`. `normalize`
either rejects the envelope or returns every record unchanged. Seven theorems state when it
succeeds and that it preserves records, environment, count and order, that names are unique
and that aliases resolve. They depend only on the axioms `propext` and `Quot.sound`.

## Incremental cache

`incremental_cache.py` provides `SnapshotCache.build`. The caller supplies a snapshot ID,
the source hash and imports of each module, a complete configuration and a builder that
returns bytes. The layers are extraction, normalization, informalization, embedding and
index. A change to a module or its imports invalidates everything that depends on it. A
failed build leaves the current snapshot intact.

## Tests

`python -m pytest -q` runs all 31 tests; `python -m unittest -v` runs the five extractor tests.

## Limits

- The Lean compiler, pretty printer, JSON decoding and file IO are trusted, not proved.
- The cache has a single writer, does not watch repositories and never runs Lean or a model.
