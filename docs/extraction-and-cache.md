# Declaration extraction and cache

Relevance review needs the complete statement of each candidate declaration. This document says
what the two extraction components guarantee, what they still take on trust, and how the
incremental cache is keyed. The code is in the
[metadata experiments](../experiments/declaration_metadata/README.md).

## The problem

A source snippet is not a complete statement. A theorem about a field, a finite group and a
group-algebra module can take all three from section variables declared outside the snippet.
Generated declarations are worse: the source span of a generated extensionality theorem is its
parent structure, and that of an additive declaration is the multiplicative original. The only
reliable statement is the elaborated type in the pinned Lean environment.

## Metadata exporter

`experiments/declaration_metadata/extract_metadata.py` verifies the requested Git revision and
Lean toolchain, imports the named modules and exports each declaration's complete environment
type. It checks the record count and identities, and that the exported types are closed. It has
five validation tests, and the pilot used it for one real extraction of 37 declarations at the
retrieval Mathlib revision; the output is kept outside Git.

The exporter proves nothing formally and does not parse arbitrary source. It trusts the Lean
compiler, the imported environment, the pretty printer, IO and hashing. Human inspection of the
environment and statements is tracked as the review item `HC-EXTRACTION`.

## Lean-checked normalization

`experiments/declaration_metadata/VerifiedNormalization.lean` defines a total function over a
decoded envelope (schema version 1): the environment, an artifact digest, the declaration records
and the aliases. Each record has its identity, kind, elaborated type expression, rendered type,
source reference and context evidence. The function returns either a rejection or the whole record
list.

Seven kernel-checked theorems establish that successful normalization:

- preserves every record and its environment;
- preserves record count and order;
- yields unique identities (fully qualified name within one environment);
- resolves every alias to an accepted canonical record;
- rejects every envelope that is not well formed.

The proof uses only the axioms `propext` and `Quot.sound`, with no `sorry`. The same function
accepts the 37 pinned records and passes twelve acceptance and rejection fixtures.

These theorems are about preserving fields. They say nothing about whether the upstream extractor
captured the right mathematics: type expressions and context evidence are opaque strings to the
proof. Byte and JSON decoding, file IO, serialization, hashing, the Lean compiler and runtime, and
upstream elaboration all remain trusted. Review of the specification itself is tracked as
`HC-NORMALIZATION-SPEC`.

## Cache keys

`experiments/declaration_metadata/incremental_cache.py` caches five layers. Each key covers every
input that can change that layer's output.

| Layer | Key inputs | Invalidated when |
|---|---|---|
| Extraction | Toolchain, dependency lock, imported environment, module input, extractor and settings | Any input or transitively imported dependency changes |
| Normalization | Upstream artifact digest, envelope schema, transformation revision | Artifact, schema or normalization behavior changes |
| Informalization | Exact semantic input, docstring, selected context, model, prompt, generation settings | Any effective generation input changes |
| Embedding | Rendered input, model and tokenizer revision, normalization, truncation, numerical settings | Effective text or embedding configuration changes |
| Index | Corpus membership, canonical record and vector hashes, index parameters | Membership, vectors or index configuration changes |

Incompatible environments are kept apart. An incomplete configuration, a missing import or a
module cycle is rejected. A new snapshot is published atomically by a single writer, and the
previous snapshot stays current until the replacement is complete.

The tests cover reuse on an unchanged rerun, invalidation for every configuration field, deletion
and rename, corrupt objects and a failed build. A fixture built from two pinned Mathlib revisions
confirms that an unchanged consumer is invalidated when a module it imports changes. The test
builders do not compile Lean or call models, so the cache shows correct invalidation, not measured
savings, and it is not integrated into production. Review of the cache specification is tracked as
`HC-CACHE-SPEC`.
