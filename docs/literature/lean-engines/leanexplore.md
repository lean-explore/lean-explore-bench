# LeanExplore

- **Kind:** search engine
- **Links:** live service https://www.leanexplore.com ; code https://github.com/lean-explore/lean-explore (also at https://github.com/justincasher/lean-explore) ; paper [arXiv:2506.11085](https://arxiv.org/abs/2506.11085) (PDF also in the repo as `LeanExplore.pdf`) ; PyPI `lean-explore`
- **Authors / org, date:** Justin Asher (independent). Launched 2025-05-09 ([Zulip](https://leanprover.zulipchat.com/#narrow/near/517187812)). Paper June 2025. Rewritten as v1.0.0 in January 2026; the CHANGELOG labels 1.0.0 "2025-01-27", but 1.0.1 follows on 2026-01-28, so 2026 is likely what was meant (unverified). v1.3.0 released 2026-08-02 ([CHANGELOG](https://github.com/lean-explore/lean-explore/blob/main/CHANGELOG.md)).
- **Status:** Live (the hosted API answered on 2026-09-28, checked by us). Apache-2.0. Actively maintained. **Note:** lean-explore-bench is built by the LeanExplore author, which is a conflict of interest to disclose in any published comparison.

## What it is

LeanExplore is a hybrid lexical, semantic and graph search engine over several Lean packages. It currently indexes Batteries, CSLib, FLT, FormalConjectures, Init, Lean, Mathlib, PhysLean and Std ([README](https://github.com/lean-explore/lean-explore)). Accounts and API keys have not been required since v1.3.0 ([CHANGELOG](https://github.com/lean-explore/lean-explore/blob/main/CHANGELOG.md)). Project Numina's LeanDex is built on it ([leandex.md](leandex.md)).

## How it works (brief)

The engine has had two generations, and they differ a lot. Any benchmark result has to say which one it tested.

- **v0.x (paper, June 2025):** "StatementGroups" are embedded from several sources: name, docstring, a Gemini-2.0-Flash informalization produced in dependency order, and file-path keywords. The embedder is bge-base-en-v1.5 (109M parameters), indexed in FAISS IVF. Candidates below a similarity threshold of 0.525 are dropped. The final score is a weighted sum of normalized semantic, BM25+ and PageRank scores with weights 1 / 1 / 0.2 ([paper §3](https://arxiv.org/abs/2506.11085)).
- **v1.x (current):** Declarations are extracted through doc-gen4 and informalized with `google/gemini-3-flash-preview` by default. Retrieval combines two BM25 indices over names (raw and split into sub-tokens) with FAISS over Qwen3-Embedding-0.6B embeddings of the informalizations. The lists are merged with reciprocal-rank fusion, candidates get a dependency boost, and a Qwen3-Reranker-0.6B cross-encoder reranks the top 25–50. The final score is not the reranker score alone: it adds BM25 over the informal text (weight 0.4), the dependency score (0.2) and a fuzzy name-match bonus (1.0 above 0.7 similarity) (`src/lean_explore/search/ranking.py`), so a reranker ablation must hold these fixed ([docs/local-backend.md](https://github.com/lean-explore/lean-explore/blob/main/docs/local-backend.md), [docs/extraction-pipeline.md](https://github.com/lean-explore/lean-explore/blob/main/docs/extraction-pipeline.md)).
- **Query styles:** declaration names (`List.map`, including fuzzy forms like `list.map`) and natural language ([local-backend.md](https://github.com/lean-explore/lean-explore/blob/main/docs/local-backend.md)). Proof-state queries are not supported (the paper lists them as future work).

## Evaluation

### Self-reported (paper §6, [arXiv:2506.11085](https://arxiv.org/abs/2506.11085)), v0.x engine
- **Queries:** 300 AI-generated short topical queries such as "group definition", "Heine-Borel theorem" and "Krull dimension". All are listed in Appendix C, so they are effectively released. There is no gold set.
- **Protocol:** The top 5 results from LeanExplore, LeanSearch (v1-era) and Moogle were shown blind, in permuted order, to Gemini 2.5 Flash. The judge ranked the engines with ties allowed. This was repeated 3 times (900 trials), and the prompt is in Appendix B.
- **1st-place rates:** LeanExplore 55.4 ± 0.7%, LeanSearch 46.3 ± 1.4%, Moogle 12.0 ± 0.6%.
- **Head-to-head:** LeanExplore beat LeanSearch 50.0% vs 39.4% (10.6% ties) and beat Moogle 79.2% vs 15.9%.
- **Caveats the paper states:** Moogle results sometimes had no informal text ("N/A"). LeanExplore was weaker on very general queries such as "vector space axioms".
- **Unstated caveats:** The judge is a single LLM with no human agreement check. The queries are topic-level with no gold answers, and the engine author wrote them.

### Third-party evaluations (all worse for LeanExplore; check which version was tested)
- **Lean Finder paper (Oct 2025; tested the v0.x engine):** On the test subset whose gold statement exists in LeanExplore's database, R@1 / R@10 / MRR were ([arXiv:2510.15940, "Additional Experiments" appendix](https://arxiv.org/abs/2510.15940)):
  - Informalized statements: LeanExplore 35.0 / 68.0 / 0.46 vs Lean Finder 65.7 / 93.2 / 0.76
  - Synthetic user queries: LeanExplore 26.3 / 60.1 / 0.37 vs Lean Finder 57.3 / 91.2 / 0.69
  - Noisy formal statements: LeanExplore 85.8 / 95.2 / 0.89 vs Lean Finder 86.8 / 98.0 / 0.91
- **LeanSearch v2 paper (May 2026):** On the MathlibQR fair subset, LeanExplore scored nDCG@10 0.393, R@10 0.569, and LLM-judge mean rank 3.32, last of four ([arXiv:2605.13137 Table 1](https://arxiv.org/abs/2605.13137)). The paper does not say which LeanExplore version it queried. The timing suggests v1.x (unverified). On the looser "full" perspective, LeanExplore moves ahead of LeanFinder on some metrics (["MathlibQR across benchmark perspectives" appendix](https://arxiv.org/abs/2605.13137)).
- **Lightweight LLM-free search (AITP 2025; tested the v0.x engine, Lean 4.19.0 snapshot):** Top-10 accuracy over 2,400 DeepSeek-generated queries was LeanExplore 59.00% vs LeanSearch 72.71% vs the author's model 92.58%. LeanExplore's accuracy fell to 26–31% on formula-style paraphrases with renamed variables ([abstract PDF](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)).

## Programmatic access (for a harness)

- **REST:** `GET https://www.leanexplore.com/api/v2/search?q=...&limit=N` and `GET /api/v2/declarations/{id}`. The search response includes `results`, `count` and `processing_time_ms` ([openapi.yaml](https://github.com/lean-explore/lean-explore/blob/main/openapi.yaml)). A `POST` to `/search` returns 405 (checked 2026-09-28). The Python `ApiClient.search(query, limit, packages=...)` also exists, but its `rerank_top` argument is ignored by the hosted API ([docs/api-client.md](https://github.com/lean-explore/lean-explore/blob/main/docs/api-client.md)).
- **MCP:** The hosted endpoint is `https://www.leanexplore.com/mcp`, with tools `search_summary`, `search` (deprecated), `get_source_code`, `get_docstring`, `get_description`, `get_module`, `get_dependencies` and `get_source_link` ([docs/mcp-server.md](https://github.com/lean-explore/lean-explore/blob/main/docs/mcp-server.md)).
- **Rate limit:** 30 POST requests per IP per 60 s on the MCP endpoint. The MCP endpoint returns 429 with `Retry-After` ([mcp-server.md](https://github.com/lean-explore/lean-explore/blob/main/docs/mcp-server.md)). The REST search endpoints allow 30 requests per minute per IP; declaration and dependency endpoints allow 240/min, with default caps of 2,000/hour and 10,000/day (lean-explore-app `app/backend/app.py`, `app/backend/api/search.py`, checked 2026-09-29). At that rate a 1,000-query run takes more than 30 minutes, so local mode is better for benchmarking.
- **Local / frozen snapshot:** Install with `pip install lean-explore[local]`, then run `lean-explore data fetch`. This downloads versioned data under `~/.lean_explore/cache/<version>/`, and the local engine exposes `faiss_k`, `bm25_k`, `rerank_top` and `packages` ([local-backend.md](https://github.com/lean-explore/lean-explore/blob/main/docs/local-backend.md)). This is the cleanest option for reproducible runs and for ablations such as turning the reranker off.
- **Versioning:** Data is versioned by timestamp (for example `data/20260127_103630` in the repo), and nightly refreshes are a design goal ([CHANGELOG 1.0.0](https://github.com/lean-explore/lean-explore/blob/main/CHANGELOG.md)). The hosted API does not report which Mathlib commit it serves (unverified; not in the OpenAPI schema).

## Relevance to lean-explore-bench

- The pairwise LLM-judge protocol (blind order, permuted, top 5) came from this paper and was reused by LeanSearch v2, which shows it is portable. Its weaknesses are no gold labels, a single judge, and ties allowed.
- The 300 topic queries are a ready-made "concept lookup" query set that nobody else covers. They need gold labels before they can be scored with IR metrics.
- Published numbers on LeanExplore mostly measure the old v0.x engine. The benchmark should re-test the current version and record `processing_time_ms`, the version string and the package filter.
- Coverage of several packages (FLT, PhysLean, CSLib and others) is a distinguishing feature, but no current benchmark tests it.

## Open questions

- Which LeanExplore version and data snapshot did the LeanSearch v2 authors query?
- Does the hosted API expose a data version or Mathlib commit? If not, it should be added for reproducibility.
- How do the rewrite components (reranker, dependency boost, BM25 on names) each contribute on MathlibQR?

## Sources

- Paper: https://arxiv.org/abs/2506.11085 (local copy `/Users/justinasher/Documents/Repositories/lean-explore/LeanExplore.pdf`)
- Repo, README, CHANGELOG, docs, openapi.yaml: https://github.com/lean-explore/lean-explore
- Zulip launch: https://leanprover.zulipchat.com/#narrow/near/517187812 ; June 2025 update: https://leanprover.zulipchat.com/#narrow/near/522433695
- Lean Finder comparison: https://arxiv.org/abs/2510.15940
- LeanSearch v2 comparison: https://arxiv.org/abs/2605.13137
- AITP 2025 comparison: https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf
