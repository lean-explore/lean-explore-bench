# Extraction and cache contract

Implement the first verified component as normalization of elaborated declaration metadata. Use the contract below before starting a parser or proof. Preserve complete statements and stable identities; do not infer missing semantic context from a source snippet.

## Address the observed failure

Treat a snippet containing free section variables as incomplete input. For example, a statement mentioning a field, a finite group and a group-algebra module does not expose the required assumptions when those are declared outside the snippet. Retain the full enclosing context for inspection, then obtain the elaborated declaration type from the pinned Lean environment before marking the semantic record complete.

Distinguish source inspection from successful elaboration. Check generated aliases and source spans against the actual pinned file; do not assume that a declaration's displayed source span is a complete statement.

## Accept a versioned envelope

Use schema version 1 with the following required fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Accept only the supported integer version. |
| `environment` | Bind the toolchain, dependency lock, module/import closure, extractor revision and extraction settings. |
| `artifact_digest` | Identify the immutable upstream elaborated artifact. |
| `declarations` | Supply a finite list of declaration records, including an explicit empty list when valid. |
| `identity` | Preserve environment identity and fully qualified declaration name; retain package and module provenance. |
| `kind` | Distinguish definitions, theorems, axioms and generated declarations; reject unsupported kinds explicitly. |
| `type_expression` | Supply the upstream elaborated type, including implicit parameters and section assumptions. |
| `rendered_type` | Preserve a deterministic rendering with its pretty-printing options and environment binding. |
| `source_reference` | Retain the upstream artifact reference and any source span without treating the span as semantic completeness. |
| `context_evidence` | Bind completeness to the upstream extraction procedure and artifact, not to an unchecked Boolean alone. |

Define identity within an environment by fully qualified name. Reject duplicate identities, conflicting metadata, unsupported versions and missing required fields. Keep aliases explicit and require each alias to resolve to a canonical record in the same environment. Do not silently merge records from different environments.

Return either a structured error or the entire normalized record list. Avoid partial success that silently drops declarations. Preserve the input mathematical text exactly; keep whitespace normalization or display formatting in a separate, versioned rendering step.

## State the proof obligations

Define a total normalization function over the decoded envelope type. Prove that successful normalization preserves identity, elaborated type and recorded context; produces unique identities; preserves record count and order; and neither invents nor silently drops records. Prove that aliases resolve to accepted canonical identities.

Separate these properties from semantic correctness of the upstream extractor. Keep byte decoding, JSON decoding, file IO, serialization, hashing, the Lean compiler/runtime and upstream elaboration in the trusted boundary. Do not describe field-preservation proofs as proofs of arbitrary Lean parsing or semantic completeness.

Reject unsupported input visibly. Do not count admitted obligations or an unchecked completeness flag as verified results. Review the contract against the section-context failure before implementing the proof target.

## Specify differential fixtures

Prepare external fixtures bound to a toolchain, dependency lock and extractor revision. Include namespace qualification, section variables, implicit typeclass arguments, overloaded notation, Unicode spans, generated declarations, aliases, anonymous instances and mutual declarations.

Compare the exported type and context with pinned elaborated output. Include malformed envelopes, duplicate identities, dangling aliases, unsupported versions and missing context as rejection fixtures. Keep invented schema fixtures in the repository and real extraction artifacts outside it.

## Define cache keys and invalidation

| Layer | Key inputs | Invalidate when |
| --- | --- | --- |
| Build/extraction | Toolchain, dependency lock, imported environment, module input, extractor and settings | Any input or transitive imported semantic dependency changes. |
| Normalization | Upstream artifact digest, envelope schema and transformation revision | Artifact, schema or normalization behavior changes. |
| Informalization | Exact semantic input, docstring, selected context, model, prompt and generation settings | Any effective generation input changes. |
| Embedding | Rendered input, model/tokenizer revision, normalization, truncation and numerical settings | Effective text or embedding configuration changes. |
| Index | Corpus membership, canonical record/vector hashes and index parameters | Membership, vectors or index configuration changes. |

Keep incompatible environments separate. Share identical content-addressed artifacts without merging their provenance. Track module imports for invalidation and treat declaration-level dependency cycles explicitly.

Require these acceptance fixtures before relying on incremental updates:

- Reuse all artifacts on a no-change rerun.
- Invalidate affected consumers after an imported declaration changes, even if the consuming source is unchanged.
- Remove stale identities after deletion and preserve explicit rename/alias history.
- Reject a cache hit after model, tokenizer, prompt, extraction or toolchain changes.
- Publish a new complete index manifest atomically; retain the previous snapshot until the replacement is ready.

Use the next implementation phase for one bounded normalization component. Keep general Lean parsing, production integration and a completed formal proof outside the current specification milestone.