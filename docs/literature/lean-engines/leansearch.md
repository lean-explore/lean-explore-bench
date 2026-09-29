# LeanSearch (v1, 2024; v2, 2026)

- **Kind:** search engine (plus two benchmark datasets)
- **Links:** live service https://leansearch.net ; API docs https://leansearch.net/docs (OpenAPI at https://leansearch.net/openapi.json) ; v1 paper [arXiv:2403.13310](https://arxiv.org/abs/2403.13310) (EMNLP 2024 Findings) ; v2 paper [arXiv:2605.13137](https://arxiv.org/abs/2605.13137) ; code [frenzymath/LeanSearch](https://github.com/frenzymath/LeanSearch) (v1) and [frenzymath/LeanSearch-v2](https://github.com/frenzymath/LeanSearch-v2) ; prebuilt v2 corpus [cuVS](https://huggingface.co/datasets/FrenzyMath/lsv2-mathlib-v4.28.0-rc1-cuvs) / [JSONL](https://huggingface.co/datasets/FrenzyMath/lsv2-mathlib-v4.28.0-rc1-jsonl)
- **Authors / org, date:** Guoxiong Gao, Haocheng Ju, Jiedong Jiang, Zihan Qin, Bin Dong et al., AI4Math team at BICMR, Peking University. v1 preprint March 2024, public launch 2024-07-30 ([Zulip announcement](https://leanprover.zulipchat.com/#narrow/near/455071791)); v2 paper May 2026 ([Zulip "LeanSearch update"](https://leanprover.zulipchat.com/#narrow/near/596070778)).
- **Status:** Live (HTTP 200 and a working `POST /search` on 2026-09-28, checked by us). Both repos are Apache-2.0 ([v1](https://github.com/frenzymath/LeanSearch), [v2](https://github.com/frenzymath/LeanSearch-v2)). It is the default natural-language backend of Mathlib's `#search`/`#leansearch` commands ([LeanSearchClient](https://github.com/leanprover-community/LeanSearchClient)) and of lean-lsp-mcp's `lean_leansearch` tool ([source](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py)). `/stats` reported 18.4M cumulative searches on 2026-09-28 ([stats](https://leansearch.net/stats)).

## What it is

LeanSearch is the most widely used natural-language search engine for Mathlib. The live service has run the "v2 standard mode" pipeline since roughly March 2026, and the maintainers call it a "major update" ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)). A separate "reasoning mode" retrieves the set of premises a whole theorem needs, but it is research-only and has no public API ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)).

## How it works (brief)

- **v1:** An LLM (GPT-3.5) turns each Mathlib theorem into an informal name and statement, using hyperlinked definitions as context. The formal and informal text is embedded together with E5-mistral-7b. At query time, an optional GPT-4 step rewrites the query into a formal plus informal statement before the embedding search ([v1 paper §3](https://arxiv.org/abs/2403.13310)).
- **v2 standard mode:** Jixia extracts every declaration kind from Mathlib v4.28.0-rc1. Qwen3-32B informalizes them bottom-up along the dependency DAG. Qwen3-Embedding-8B does dense retrieval, and Qwen3-Reranker-8B reranks the top 50 using a kind-aware prompt. No model is fine-tuned ([v2 paper, "Standard mode"](https://arxiv.org/abs/2605.13137)). The public API uses a 4B reranker variant ([v2 README](https://github.com/frenzymath/LeanSearch-v2)).
- **Query styles:** natural language, LaTeX, theorem names or nicknames, and Lean terms. Lean-lsp-mcp's documented examples include `bijective map from injective`, `Cauchy Schwarz`, `List.sum`, and `{f : A → B} (hf : Injective f) : ∃ h, Bijective h` ([lean-lsp-mcp README](https://github.com/oOo0oOo/lean-lsp-mcp)).

## Evaluation

### v1: "Mathlib4 Semantic Search Benchmark" ([arXiv:2403.13310 §4–5](https://arxiv.org/abs/2403.13310))
- **Queries:** 50 queries in 18 intent groups. They fall into four forms: natural description (18), LaTeX formula (15), theorem name (7), and Lean 4 term (10). The corpus was Mathlib at commit `db04a978…`, theorems only.
- **Relevance labels:** Graded as Exact match (score 1), Relevant (0.3), or Irrelevant (0). Assessors labelled the top 50 results of an intermediate LeanSearch build and added missing items by looking in the same files. Anything left unlabelled is assumed irrelevant. That assumption makes the pool biased toward LeanSearch.
- **Metrics:** nDCG@20, P@10 and R@10, where P and R count only "Exact match".
- **Headline results (Table 3):** E5-mistral-7b with the formal+informal corpus and augmented queries scored nDCG@20 0.733, P@10 0.196, R@10 0.913. Moogle scored 0.365 / 0.092 / 0.513, but Moogle's non-theorem results were counted as irrelevant, so it is flagged as not directly comparable. BM25 on the formal corpus scored 0.024. OpenAI text-embedding-3-large on the formal+informal setup scored 0.691.
- **Per-category results:** The largest gains from augmentation were on theorem-name queries (nDCG@20 0.294 → 0.855). On Lean-term queries the formal-only corpus did better (0.774 vs 0.654).
- **Data release:** Not in the v1 code repo ([file tree](https://github.com/frenzymath/LeanSearch)), but released on Hugging Face as `hcju/leansearch_bench` (judged lists) and `hcju/mathlibretrieval` (40 informal queries, BEIR format), both CC-BY-4.0. See [../lean-benchmarks/leansearch-v1-benchmark.md](../lean-benchmarks/leansearch-v1-benchmark.md).

### v2: MathlibQR (single-query search) ([arXiv:2605.13137 §4 "Search" and "MathlibQR" appendix](https://arxiv.org/abs/2605.13137))
- **Queries:** 200 Mathlib declarations picked by formalization experts, 8 from each of 25 top-level folders, balanced across declaration kinds and marked Easy or Hard. There are up to six expert-written query styles per declaration: Lean (199), LaTeX (200), natural (199), slogan (197), nickname (128), and special case (23), for 946 queries in total, built against Mathlib v4.29.1.
- **Relevance:** Binary, with a single ground-truth declaration per query.
- **Metrics:** nDCG@{1,5,10} and Recall@{10,50,100}. There is also an LLM judge that follows LeanExplore's protocol, using Claude Sonnet 4.5 and 3 random permutations, forcing a strict 1–4 ordering, and reporting mean rank.
- **Snapshot fairness:** The main table uses only the "fair" subset: 810 queries over 171 declarations that exist in every compared engine's snapshot.
- **Results (Table 1), in the order nDCG@10 / R@10 / judge mean rank:**
  - LeanSearch v2 with reranking: 0.623 / 0.780 / 1.63
  - LeanSearch v2 retriever only: 0.494 / 0.657 / 2.18
  - LeanFinder: 0.533 / 0.698 / 2.87
  - LeanExplore: 0.393 / 0.569 / 3.32
- The reranker adds about +10 points at k ≤ 10. The LLM judge shows a primacy bias of about 0.42–0.58 rank between positions A and D, which is balanced out by permuting the order (["LLM-as-judge protocol" appendix](https://arxiv.org/abs/2605.13137)).
- **Data release:** `benchmark/MathlibQR.json` and `MathlibQR_shared171.json` are in the repo, with metrics code in `src/leansearchv2/eval/search_metrics.py` ([repo](https://github.com/frenzymath/LeanSearch-v2)).

### v2: MathlibMPR (global premise retrieval) and Prove
- **MathlibMPR:** 69 theorems taken from merged Mathlib PRs, with ground-truth "premise groups" and expert-annotated alternative routings. In reasoning mode, LeanSearch v2 recovers 46.1% of premise groups within 10 candidates. The best reasoning-retrieval baseline gets 38.0% and premise-selection baselines get 9.3% ([abstract](https://arxiv.org/abs/2605.13137)).
- **Prove:** This is a downstream test with a fixed prover loop: LeanSearch v2 reaches 20% proof success, the next-best system 16%, and no retrieval 4% ([abstract](https://arxiv.org/abs/2605.13137)).
- These tasks belong mostly to the premise-selection review. They are relevant here because they measure extrinsic usefulness.

## Programmatic access (for a harness)

- **API:** `POST https://leansearch.net/search` with body `{"query": [str, ...], "num_results": int ≤ 150}`. It accepts a batch of queries. Each result includes `name`, `module_name`, `kind`, `signature`, `type`, `value`, `docstring`, `informal_name`, `informal_description`, and a `distance` score. Other endpoints are `POST /augment` (LLM query augmentation), `POST /fetch`, `GET /stats`, and `POST /feedback` ([OpenAPI](https://leansearch.net/openapi.json), checked 2026-09-28).
- **Rate limits:** Capacity is about 40 req/s with a per-IP limit of 120 req/min (as of 2026-05-19), adjusted dynamically. IPs are now logged ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)). The upstream lean-lsp-mcp throttles itself to 90 requests per 30 s ([config.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/config.py)).
- **Index snapshot:** Mathlib v4.28.0-rc1 as of May 2026, with an update pending that needs a Jixia upgrade ([Zulip](https://leanprover.zulipchat.com/#narrow/near/596070778)). Whether it has been updated since is unverified. The API does not expose which snapshot it serves, so a harness should record the response date and check whether gold declarations exist through `/fetch`.
- **Self-hosting:** `scripts/serve.sh` runs standard mode on 2 GPUs ([README](https://github.com/frenzymath/LeanSearch-v2)). This makes a frozen, reproducible copy possible.
- **MCP:** LeanSearch has no first-party MCP server. It is reached through lean-lsp-mcp (see [../lean-tools/lean-lsp-mcp.md](../lean-tools/lean-lsp-mcp.md)).

## Relevance to lean-explore-bench

- MathlibQR is currently the most useful released NL→declaration benchmark. It has expert queries in six styles, covers all declaration kinds, labels difficulty, and ships a fair-subset protocol for snapshot drift. The Octo team already reports against it ([octo-search.md](octo-search.md)).
- **Weaknesses:** Each query has a single gold declaration with binary relevance, although near-duplicates and generalizations such as `_left`/`_right` variants or `Nat.` vs root namespace are common. It has only 200 declarations, and the authors of the engine that wins built it themselves.
- v1's graded labels (0 / 0.3 / 1) are worth keeping as a scheme. Its pooling from a single engine is a pitfall to avoid.
- The API is the easiest of all the engines to drive in batches, so LeanSearch is a natural reference engine.

## Open questions

- Which Mathlib snapshot does leansearch.net serve today? Has the post-v4.28 update shipped?
- Is `/augment` query augmentation still considered part of the recommended pipeline in v2? The Lean Finder paper found that augmentation lowered LeanSearch's R@1 ([arXiv:2510.15940, "Additional Experiments" appendix](https://arxiv.org/abs/2510.15940)).
- Is the full 50-query v1 set (including the 10 Lean-term queries) recoverable from the Hugging Face release? See [../lean-benchmarks/leansearch-v1-benchmark.md](../lean-benchmarks/leansearch-v1-benchmark.md).

## Sources

- v1 paper: https://arxiv.org/abs/2403.13310
- v2 paper: https://arxiv.org/abs/2605.13137
- v2 code and benchmarks: https://github.com/frenzymath/LeanSearch-v2
- v1 code: https://github.com/frenzymath/LeanSearch
- OpenAPI schema (fetched 2026-09-28): https://leansearch.net/openapi.json ; stats: https://leansearch.net/stats
- Zulip launch (2024-07-30): https://leanprover.zulipchat.com/#narrow/near/455071791 ; API and all-kinds update (2024-09-08): https://leanprover.zulipchat.com/#narrow/near/468640723
- Zulip v2 / service update (2026-05-19): https://leanprover.zulipchat.com/#narrow/near/596070778
- lean-lsp-mcp rate limits: https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/config.py
- Lean Finder paper (augmentation comparison): https://arxiv.org/abs/2510.15940
