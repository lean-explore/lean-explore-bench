# Moogle (Morph Labs), defunct

- **Kind:** search engine (historical)
- **Links:** formerly https://www.moogle.ai (also mirrored at https://moogle-morphlabs.vercel.app) ; Zulip announcement https://leanprover.zulipchat.com/#narrow/near/399587531
- **Authors / org, date:** Morph Labs (announced by Jesse Michael Han). Public beta 2023-10-31, "Moogle v2" 2023-11-08 ([Zulip](https://leanprover.zulipchat.com/#narrow/near/400837692)).
- **Status:** **Dead.** Both URLs returned HTTP 404 on 2026-09-28 (checked by us). vscode-lean4 removed its Moogle integration because "the Moogle website is now defunct" ([vscode-lean4 commit 8480ce4, #666](https://github.com/leanprover/vscode-lean4/commit/8480ce43f0fe306c1c2f7f29a98b3d638b467592)), and LeanSearchClient dropped `#moogle` on 2025-10-21 ([LeanSearchClient PR #24](https://github.com/leanprover-community/LeanSearchClient/pull/24)). Kim Morrison noted in 2025 that it had "not been updated in some time" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/544874730)). It was never open source (unverified; we found no public code).

## What it is

Moogle was the first widely used natural-language semantic search engine for Mathlib. The announcement says it "builds on some of the same techniques as our recent Morph Prover v0 7B" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/399587531)). The v2 announcement claimed "99% coverage of all declarations including all instances in mathlib" and "better top-1 recall on the same test set", but the test set was never published ([Zulip](https://leanprover.zulipchat.com/#narrow/near/400837692)).

## How it works (brief)

No technical description was published. Third-party summaries describe query-vector to theorem-vector cosine similarity (unverified; [callin.io summary](https://callin.io/ai-tools/moogle/)).

## Evaluation

- **Self-reported:** Only the qualitative "better top-1 recall" claim above, with no data.
- **LeanSearch v1 benchmark:** nDCG@20 0.365, P@10 0.092, R@10 0.513. Moogle's non-theorem hits were counted as irrelevant, so the authors flag it as not directly comparable ([arXiv:2403.13310 Table 3](https://arxiv.org/abs/2403.13310)).
- **LeanExplore LLM judge (June 2025):** Ranked 1st in 12.0% of 900 trials and 3rd in 63.2%. It lost head-to-head to LeanSearch 23.2% vs 72.0%. Results were partly handicapped by missing informal text ([arXiv:2506.11085 §6](https://arxiv.org/abs/2506.11085)).

## Programmatic access

None today. Historically LeanSearchClient called a Moogle JSON endpoint (see that repo's history before [PR #24](https://github.com/leanprover-community/LeanSearchClient/pull/24)).

## Relevance to lean-explore-bench

- Exclude it from live runs. Mention it only as historical context and as an example of the failure mode Kevin Buzzard called "the achilles heal [sic] with all previous semantic search engines": the index going stale ([Zulip](https://leanprover.zulipchat.com/#narrow/near/554166812)). Users were "burned on moogle which seemed ok but stopped updating" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/606788372)).
- Takeaway for the benchmark: record index freshness (Mathlib version or date) for each engine, and consider a "recently added declarations" slice.

## Open questions

- Did Morph Labs ever publish Moogle's test set or architecture? We found neither.

## Sources

- Zulip announcements: https://leanprover.zulipchat.com/#narrow/near/399587531 , https://leanprover.zulipchat.com/#narrow/near/400837692
- Zulip "moogle dead" thread (2025-09-25): https://leanprover.zulipchat.com/#narrow/near/541366533
- vscode-lean4 removal: https://github.com/leanprover/vscode-lean4/commit/8480ce43f0fe306c1c2f7f29a98b3d638b467592
- LeanSearchClient removal: https://github.com/leanprover-community/LeanSearchClient/pull/24
- LeanSearch v1 paper: https://arxiv.org/abs/2403.13310 ; LeanExplore paper: https://arxiv.org/abs/2506.11085
- Lean community blog (2025-06-25, calls Moogle "somewhat outdated"): https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/
