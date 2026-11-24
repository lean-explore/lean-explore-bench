# Pinned declaration metadata

This extractor reads full declaration types from a Lean environment. It is used by the assisted benchmark to inspect generated declarations and inherited section assumptions.

Provide an external JSON request with `revision`, `toolchain`, `modules` and `names`. The project must be a clean tracked Git checkout at that revision. The active `lake env lean --version` must match the requested toolchain. Store output outside Git checkouts:

```text
python extract_metadata.py --project PINNED_MATHLIB_CHECKOUT --request EXTERNAL_REQUEST_JSON --out NEW_EXTERNAL_OUTPUT_DIRECTORY
```

The output includes the generated Lean program, compiler output and a metadata JSON file. Each record contains the declaration kind, universe parameters, a readable type, an explicit rendering and the elaborated expression representation. Readable rendering can suppress proof terms; the expression representation is retained. The environment records source revision, dependency-lock hash, actual Lean version, platform and extractor hash.

The command rejects an existing output directory, invalid module names, missing or duplicate declarations, metavariables and loose bound variables. Failed extraction preserves diagnostics but does not emit a successful metadata file. UTF-8 is explicit at the process and file boundaries.

Run `python -m pytest -q` in this directory for all 31 metadata and cache tests.
Use `python -m unittest -v` to run only the five exporter validation tests. They cover identity/count preservation, malformed semantic input, wrong active toolchains and modified pinned projects. The assisted release also records an actual 37-declaration extraction.

The Lean compiler, imported environment, pretty printer, IO and hashing are trusted. This executable does not prove the normalization contract in `docs/extraction-boundary.md` and does not parse arbitrary source snippets. Human inspection remains `HC-EXTRACTION`.

## Verified normalization

`VerifiedNormalization.lean` is a standalone Lean 4.32.0 module. Run the actual
pinned binary, then use its executable entry point on a decoded-envelope JSON:

```text
lean VerifiedNormalization.lean
lean --run VerifiedNormalization.lean INPUT_ENVELOPE_JSON NEW_OUTPUT_JSON
```

The required envelope has `schema_version`, `environment`, `artifact_digest`,
`declarations` and `aliases`. Each declaration carries its name, environment,
package, `moduleName`, kind, complete `type_expression`, `rendered_type`,
`source_reference` and `context_evidence`. Environment and provenance are opaque
strings, which can hold canonical JSON. The adapter must bind them to inspected
upstream artifacts; nonempty text alone does not prove semantic completeness.

The total `normalize` function either rejects the envelope or returns every
record unchanged. Its seven theorems establish success conditions, record and
environment preservation, count/order, identity uniqueness, alias resolution
and rejection. The kernel reports only `propext` and `Quot.sound`, with no
`sorryAx` or custom axioms. `main` calls that same function after JSON decoding.
Use a new output path; the IO wrapper is trusted and is not a transactional store.

The v2 evidence runs all 37 pinned records through this path and checks twelve
runtime fixtures, including malformed and missing fields, duplicate identities,
foreign environments, unsupported versions/kinds and dangling aliases. Review
of the specification remains HC-NORMALIZATION-SPEC. Upstream extraction, JSON,
serialization, hashing and compiler/runtime are outside this preservation proof.

## Manual incremental cache

`incremental_cache.py` provides `SnapshotCache.build`. Supply a snapshot ID,
module source hashes/imports, all required effective configuration fields and a
builder returning bytes for each layer. The supported layers are extraction,
normalization, informalization, embedding and index. Entries bind both effective
input keys and output digests; transitive imported changes invalidate consumers.
An incomplete configuration, missing import or module cycle is rejected.

Publication is single-writer. Builders finish and objects are hash-checked before
a complete immutable snapshot and the current pointer are atomically replaced.
An interrupted build can leave reusable unreferenced objects, while the old
snapshot stays current. Rename history is explicit and removed modules disappear
from the new index membership; prior manifests stay intact.

The tests exercise no-change reuse, every configuration field, dependency-only
changes, deletion/rename, corrupt objects and a failed build. The manual fixture
uses two pinned Mathlib revisions and 351 modules reachable from Order.Atoms.
Its builders record effective inputs. They do not compile Lean or call models,
so cache hits are validation evidence rather than measured inference savings.
Production integration and an unattended watcher are outside this component.
