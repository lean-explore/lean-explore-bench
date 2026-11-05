# Extraction boundary for benchmark records

The first component to specify is normalization of a versioned declaration
envelope from elaborated metadata. The immediate benchmark requirement is a
stable identity, complete statement context and traceable corpus membership.

## Input and output

Input is a versioned envelope containing a corpus revision and declaration
records. Each record has a fully qualified name, package/module identity,
statement text and explicit context, plus its upstream artifact reference.
The upstream extractor supplies resolved names and types. A source snippet alone
does not establish them.

Normalization validates the supported schema, rejects duplicate identities and
missing required context, and preserves each accepted record's identity and
mathematical text. Unknown schema versions and unsupported records return
explicit errors. No parser implementation or proof is claimed by this document.

The candidate proof target is field preservation and identity uniqueness for
successful normalization of the declared envelope schema. Specify a total
function from decoded envelopes to either an error or normalized records.
Prove that accepted records preserve name, statement and context; no record is
invented, merged or silently dropped; output identities are unique.

This boundary does not prove parsing or elaboration of arbitrary Lean syntax.
Upstream Lean/doc-gen semantics, byte decoding, IO, serialization, runtime and
hashing remain trusted. Proving a weak validator correct would not establish
that a statement contains all relevant section assumptions; that requirement
must be part of the input contract and checked against pinned elaborated output.

## Fixtures and acceptance

Use invented records for schema and identity tests. Differential extraction
fixtures stay outside the repository and bind to a pinned toolchain, dependency
lock and extractor revision.

Cover namespace qualification, section variables, implicit arguments, overloaded
notation, Unicode, generated declarations and anonymous instances. Check source
spans against complete module context. Malformed envelopes, duplicate names,
missing context and unsupported versions must fail visibly.

Before implementation, review the specification against at least one observed
extraction failure. A proof attempt starts only after the input subset and
trusted boundary are settled.

## Cache identities

A build/extraction cache key includes toolchain, dependency lock, module input,
extractor revision and settings. An unchanged source file can change meaning
when its imported environment changes.

A normalization key includes artifact hash, schema and transformation revision.
An informalization key includes the exact semantic input, docstring, selected
context hashes, model and prompt revisions, and generation settings.
An embedding key includes the rendered text, model/tokenizer revisions,
normalization and truncation. An index manifest records corpus membership,
record/vector hashes and index parameters.

Keep incompatible semantic environments separate. Test rename, deletion,
dependency-only changes and a no-change rerun before relying on incremental
updates. The next implementation should address the smallest demonstrated
failure within this boundary.
