# mathlas (community MCP server, Krishi Attri), local informal theorem search plus a Loogle/LeanSearch proxy

> **Name collision:** this is **not** Matlas (matlas.ai, PKU). For that engine see [informal-matlas.md](informal-matlas.md).

- **Kind:** tool (MCP server bundling an informal theorem-search index, a Lean-search proxy and verification tools)
- **Links:**
  - code (Apache-2.0): https://github.com/Archerkattri/mathlas
  - package: https://pypi.org/project/mathlas-mcp/
  - corpus: https://huggingface.co/datasets/kattri15/mathlas-corpus
  - results: https://github.com/Archerkattri/mathlas/blob/main/RESULTS.md
  - announcement: [Lean Zulip, 2026-06-10](https://leanprover.zulipchat.com/#narrow/near/601608319)
- **Authors / org, date:** Krishi Attri (individual). The repo was created 2026-06-05 (GitHub API).
- **Status (checked 2026-09-28):**
  - Active. PyPI is at 1.5.0 and the repo was last pushed 2026-09-18, with 12 stars (GitHub and PyPI APIs).
  - Runs **locally** as a stdio MCP server (`uvx mathlas-mcp`). There is no hosted endpoint, so there is no service rate limit. The index is large: the fp16 matrix is 30 GB, and quantized sidecars bring it down to 0.47–1.9 GB ([README](https://github.com/Archerkattri/mathlas)).
  - We did not install or run it.

## What it is

An MCP server with 12 tools. Two of them matter for search ([README, "The 12 tools"](https://github.com/Archerkattri/mathlas)):

- **`search_existing_math(query, k)`** searches a local **3,683,428-document** index. It combines:
  - the 1,341,083-statement openly licensed **TheoremSearch subset** (see [informal-theoremsearch.md](informal-theoremsearch.md));
  - 2,342,345 slogan-embedded arXiv-math documents from Dolma.

  Retrieval is Qwen3-Embedding-8B dense search plus Okapi BM25, fused with RRF. Optional source filters or weights are available.
- **`search_formal_math(query, backend)`** is a thin proxy over the **public Loogle and LeanSearch services**. It returns Mathlib declaration names and types labelled with their provenance, backed by a 7-day on-disk cache that is served, and labelled `cached`, when a backend is down. It is the only tool that makes a web call.

It indexes **no Lean content of its own**: the formal results come entirely from Loogle and LeanSearch.

## Evaluation

All numbers below are self-reported in the repo.

- **Self-recall proxy** ([RESULTS.md §3a0](https://github.com/Archerkattri/mathlas/blob/main/RESULTS.md)):
  - **Protocol.** 3,000 sampled documents. Each document's raw *body* is the query, and its own slogan-embedded entry is the target.
  - **Results.** R@1 is 0.614 and R@10 is 0.832 on the 8B index. A 0.6B encoder gives 0.545 and 0.745. A "dual-channel" setup that also embeds the statement text gives 0.965 and 0.999, but the authors note that the statement channel "indexes the very text the queries are drawn from".
  - **Our assessment.** This is a known-item self-retrieval proxy with no human queries, and it measures representation consistency rather than search quality.
- **TheoremSearch's 110 human-written queries** ([RESULTS.md §3b](https://github.com/Archerkattri/mathlas/blob/main/RESULTS.md)):
  - **Full 110 queries.** Theorem Hit@20 is 10.0% and paper Hit@20 is 11.8%, compared with 45.0% and 56.8% for TheoremSearch.
  - **Coverage.** Only 15 of the 110 targets are in the openly licensed corpus.
  - **"Reachable" 15 targets.** Theorem Hit@20 is 73.3% and paper Hit@20 is 86.7%. The authors acknowledge that "n=15 is small (1 query = 6.7 pts)".
  - **Distractors hurt.** Adding the 2.34M Dolma documents *lowered* paper Hit@20 on the reachable set from 100% to 86.7% by crowding. Excluding Dolma recovers it.
- **"Self-augmenting loop"** ([README](https://github.com/Archerkattri/mathlas)):
  - **Claim.** Theorem Hit@20 of 59.1% (65/110), "beating TheoremSearch".
  - **How it was obtained.** An AI web-searches for each *missing* target, embeds it, and inserts it into the index with `add_finding` before retrieval is scored, using an 82-finding worklist.
  - **Our assessment.** This inserts gold targets into the corpus, so it is **not a retrieval result** and should not be compared with engine scores. The README itself calls it "the loop's value, not a native-corpus claim".
- **Formal search.** The Zulip post claims Hit@5 of 0.96 on "a 25-query gold set" for `search_formal_math`, with "Loogle 4/4 at rank 1 on type patterns, LeanSearch carrying natural language" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/601608319)). We did not find this table in the README or in RESULTS.md (unverified).
- **Agent A/B.** The same agent (the README says "Claude Fable 5") scored 18/18 with the tool against 15/18 without it, and 8/8 against 5/8 on the hard subset ([README](https://github.com/Archerkattri/mathlas)). The tasks are mostly numeric and OEIS identification, not theorem search.

## Relevance to lean-explore-bench

- **As an engine to benchmark:**
  - Low priority for the Lean track. Its formal search is Loogle plus LeanSearch, so scoring it would double-count those engines, with an extra cache layer that can serve stale results.
  - For an informal track it is a reproducible, offline, open-data stand-in for TheoremSearch. The index is pinned to a PyPI version and an HF dataset, whereas the live TheoremSearch index cannot be rebuilt. The trade-off is coverage: only 15 of TheoremSearch's 110 test targets are reachable.
- **Methodological lessons (mostly cautionary):**
  - A self-retrieval proxy (a body query against its own slogan) can look strong while reflecting little about real query performance.
  - Adding distractor corpora can lower scores on a fixed query set, so corpus composition must be pinned per run.
  - "Augment the corpus with the missing targets, then retrieve" is leakage. Our protocol should forbid any corpus mutation driven by the evaluation queries.
  - Reporting a "reachable subset" alongside the full set is the right idea, and matches the fair-subset handling in [../premise-selection/theoremgraph.md](../premise-selection/theoremgraph.md). The reachable subset needs to be large enough to be informative, though.
- **Caching proxies can hide outages.** A harness that goes through `search_formal_math` must log the `cached` flag and the cache age.

## Open questions

- Where is the 25-query formal gold set? Can it be obtained for cross-checking against our own Loogle and LeanSearch results?
- How is the Dolma arXiv-math subset deduplicated against the TheoremSearch subset?

## Sources

- README and RESULTS.md (fetched 2026-09-28): https://github.com/Archerkattri/mathlas , https://github.com/Archerkattri/mathlas/blob/main/RESULTS.md
- PyPI JSON (version 1.5.0, fetched 2026-09-28): https://pypi.org/pypi/mathlas-mcp/json
- HF corpus: https://huggingface.co/datasets/kattri15/mathlas-corpus (from the README; not downloaded)
- Lean Zulip announcement, #Machine Learning for Theorem Proving > "MCP Tools for LLMs and Agentic Mathematics": https://leanprover.zulipchat.com/#narrow/near/601608319
