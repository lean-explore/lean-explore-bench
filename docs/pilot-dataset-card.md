# Pilot dataset card

Version: assisted-v2, 8 November 2026. Results and methods are in the
[pilot report](pilot-report.md).

## What the data contains

The pilot data supports evaluation of Lean declaration search: a query goes in and a ranked list
of declarations comes out. It contains:

- 20 development and 30 test queries, all synthetic and anonymous. No private usage logs are
  included.
- 786 query-declaration pairs with graded relevance records (419 development, 367 test).
- The stored rankings of every pipeline stage for each query.
- The 946 MathlibQR query variants (200 targets) with their upstream single-gold targets, of
  which 196 are present in the local corpus by name.
- A register of 850 human-review items.

The 7 November methods checkpoint described ten development queries as taken from public
discussions and ten from reference tasks or controls, four in each of five query forms; the
later documents describe all development queries as synthetic.

## How the labels were made

An AI assessor reviewed the pooled candidates with their source context and, where needed, their
full elaborated types, and proposed a grade from 0 to 3 with a rationale. **Of the 763 usable
judgments, 759 are AI proposals and four are earlier human-accepted decisions; nothing has been
independently validated.** The assessor had seen the candidates before grading, so its judgments
are not blind. Human decisions take precedence over AI proposals, and a correction creates a new
label version instead of overwriting the old one. The rubric is in the
[evaluation protocol](evaluation-protocol.md) and the correction procedure in the
[human review guide](human-review.md).

## Exposure

The development queries were exposed throughout. The test queries were frozen before retrieval,
but their sources sometimes contain theorem names or proofs, and one answer link was seen
earlier. All test queries are now exposed, so they cannot serve as a fresh holdout, and a model
trained on them cannot claim held-out performance. Grouping of queries into mathematical families
is provisional and unreviewed.

## Provenance and redistribution

The data is a local research package. No public dataset license has been chosen, and
redistribution needs a source-by-source review that has not been done.

| Material | Status |
| --- | --- |
| Pilot queries and source excerpts | Source records and hashes kept; attribution and rights not yet reviewed |
| AI proposals and human decisions | Assessor type, rationale and packet hashes kept; no license assigned |
| MathlibQR input | Upstream commit `94f4888cbaf9f4322535755f86cbac690ec18080`; the repository states Apache-2.0, with no separate data-license statement found |
| Lean and Mathlib excerpts | Revision-specific references and upstream notices kept; each excerpt still to be checked |
| Database, indexes and model weights | External dependencies, identified by hash and manifest |

The corpus build history and the hosted-service configuration are incomplete; the package
identifies the exact local bytes that were evaluated.

## Where the data lives

Queries, labels, rankings and run records are kept outside Git in the external assisted-v2
package, which also contains the unchanged assisted-v1 evidence. A manifest lists the SHA256 of
every file. Within the package, `benchmark-report.html` shows all 50 pilot responses, the 946
MathlibQR comparisons and the review items, and `human-checks.json` is the machine-readable
register. The repository holds only source code, methods and aggregate results. Steps for
recomputing scores are in [reproduction](reproduction.md).
