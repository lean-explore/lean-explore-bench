# Legendre Leaderboard

- **Kind:** leaderboard
- **Links:** https://www.legendre-leaderboard.com/ (pages: `/leaderboard`, `/datasets`, `/playground`, `/methodology`, `/changelog`)
- **Authors / org, date:** Yaro Kharkov, Ph.D. (individual; the footer reads "AI/ML scientist, theoretical physicist, entrepreneur, math nerd"), 2026. First public run 27 Aug 2026; last changelog entry 2 Sep 2026.
- **Status:** Live as of 2026-09-28. The site is static and ships its curves as JSON. The pages mention a harness (`harness/legendre_search/eval/curves.py`, `harness/benchmarks/`) and name commits (`61d54c2`, `164bece`, `1a20e42`), but I found no public repository. The site links no source, and a GitHub search for "legendre leaderboard" returned nothing. The site has no license statement for its own artifacts. It accepts submissions through a "Request to add my model or dataset" link.

## What it is

Legendre is a third-party leaderboard for Mathlib search engines and embedding models. It puts every system on the same footing: one pinned Mathlib corpus, one document renderer, one query set, and one metric implementation. The motivation, quoted from the site: "Published Lean search engines each evaluate on their own corpus with their own metrics, so their numbers are not comparable to one another — and nobody has measured how general-purpose embedding models do on Lean-specific retrieval."

The task on the leaderboard is **Theorem search on MathlibQR** (see `mathlibqr.md`), used unmodified. The methodology page also defines the protocol for **MathlibMPR** premise selection (n = 69) and a **LeanDojo Benchmark 4** premise task, which is kept separate from the other tasks because it uses a different corpus. The home page and leaderboard show only theorem-search results. Whether published MathlibMPR or LeanDojo results exist is unverified.

## How it works

- **Corpus:** `mathlib-4280`, which is Hugging Face `FrenzyMath/lsv2-mathlib-v4.28.0-rc1-jsonl` pinned at revision `c5f07cc71d42`. It holds 310,579 declarations, one per row. Pinning means an upstream re-upload cannot silently change the scores.
- **Document renderer:** `lsv2-compat` (hash `5f1e87b6661e`). Every locally run model embeds byte-identical text. The format is an instruction, then `Informal content: [kind]: <informal name>: <informal description>`, then `Formal content: <name> <type> := by sorry` (an example appears on `/datasets`). The renderer hash is part of the vector path, so a changed renderer invalidates the cached vectors.
- **Search:** exact inner product over L2-normalized vectors, with no HNSW or IVF approximate index. The stated reason is so that approximate-index recall error is not mixed into model error. Instruction-aware models get the instruction on the query side only, following each model card, and a harness test enforces this.
- **Published engines:** these are queried over their own public HTTP APIs, and the ranking each returns is scored. The engine, its index, and its snapshot belong to the engine's operators. Endpoints:
  - LeanSearch v2: `POST leansearch.net/search`
  - LeanExplore: `POST leanexplore.com/api/v2/search` as the site states. On 2026-09-28 we found this endpoint answers `GET` and returns 405 to `POST` (see [../lean-engines/leanexplore.md](../lean-engines/leanexplore.md)), so either the site's description or the endpoint has changed.
  - Lean Finder v1: a Hugging Face inference endpoint
- **Rate limits the site applies to itself:** leansearch.net at 3 requests per 30 s, LeanExplore at 24 POST per 60 s (its published limit is 30), and Lean Finder at 1 request per second. Every response is cached permanently, so each query is fetched once.
- **Engine-specific caveats the site documents:**
  - **LeanSearch v2:** the hosted API returns at most 50 results, so metrics above k = 50 are marked undefined (a `k≤50` badge), not flat. The API serves Qwen3-Reranker-4B, while the paper's Table 1 used the 8B reranker, so the site never presents paper numbers as API numbers.
  - **Lean Finder:** the site requests its v4.19.0 index, not v4.28.0. By the site's measurement, the v4.24.0 and v4.28.0 indexes contain only definitions, theorems and inductives, with no structures or classes. That would zero 317 of the 894 queries. The price is a nine-release version gap.
  - **Engines with their own snapshots:** these can also be compared on `MathlibQR_shared171`, the 171 declarations present in every corpus, with a coverage column and a "different corpus" badge.
- **Coverage handling:** 11 of the 200 gold declarations are absent from the pinned corpus. Their queries count as unresolved and are dropped, not scored as misses, which leaves 894 of 946 queries scored. The site argues that scoring coverage gaps as misses would "understate every system by the same amount — which looks like a valid comparison but is not." Each row reports its n next to the scores.
- **Deduplication rule:** a declaration returned twice counts only at its first position. The stated reason is so that "a backend must not be able to improve its score by repeating itself".
- **Gold matching:** the gold `full_name` resolves to every corpus row that carries that name, and any copy counts as correct.

## Evaluation

**Metrics** are all macro-averaged over queries and truncated at k_max = 200. Per-query rank positions are stored, so every metric is re-derived from them without re-running retrieval.
- **R@k:** reported as a full curve over k = 1…200.
- **nDCG@k:** binary relevance, with IDCG capped at min(k, |G|). This is the default sort key.
- **MRR:** a query with no hit contributes 0.
- **MAP:** defined on the methodology page.
- **Covered@k:** premise tasks only; 1 only when every gold premise group is in the top k.
- **P@k:** suppressed on theorem search. With one gold per query it is mechanically R@k/k.
- **Confidence intervals:** percentile bootstrap, 1,000 resamples, fixed seed, shown on R@10.

The site also breaks results down by query style, declaration kind and difficulty. The `/datasets` page shows every query with each system's rank.

**Results on MathlibQR** (run `m1`, n = 894/946, from `/leaderboard` and the home-page table):

| System | nDCG@10 | R@1 | R@5 | R@10 [95% CI] | R@50 | R@100 | MRR | p95 latency |
|---|---|---|---|---|---|---|---|---|
| Lean Finder v1 (API, v4.19.0 index) | 0.591 | 45.7 | 66.6 | 72.6 [70–76] | 83.6 | 86.9 | 0.555 | 1049 ms* |
| MathLeap-Qwen-8B (in-domain fine-tune) | 0.572 | 42.4 | 65.3 | 72.8 [70–76] | 83.8 | 87.8 | 0.529 | 104 ms* |
| LeanSearch v2 (API, k≤50) | 0.571 | 40.3 | 67.7 | 74.4 [72–77] | 78.9 | n/a | 0.519 | 2069 ms* |
| MathLeap-Octen-8B (in-domain fine-tune) | 0.562 | 41.4 | 64.3 | 71.6 [69–74] | 83.1 | 86.9 | 0.520 | 74 ms* |
| Nemotron-3-Embed-8B | 0.526 | 36.9 | 62.3 | 68.3 [65–71] | 79.5 | 83.7 | 0.482 | 65 ms* |
| Qwen3-Embedding-8B | 0.456 | 31.9 | 53.4 | 60.1 [57–63] | 73.9 | 77.9 | 0.417 | 55 ms* |
| Qwen3-Embedding-4B | 0.427 | 29.2 | 49.8 | 57.3 [54–61] | 72.5 | 77.7 | 0.389 | 30 ms* |
| LeanExplore (API) | 0.385 | 23.4 | 45.5 | 56.5 [53–60] | 74.7 | 78.7 | 0.340 | 1457 ms* |
| Nemotron-3-Embed-1B | 0.354 | 21.1 | 43.5 | 51.0 [48–54] | 69.5 | 73.9 | 0.315 | 33 ms* |
| Qwen3-Embedding-0.6B | 0.331 | 21.1 | 38.8 | 46.4 [44–50] | 60.9 | 66.9 | 0.298 | 1137 ms |
| BGE-M3 | 0.266 | 16.8 | 31.2 | 37.9 [35–41] | 50.7 | 56.3 | 0.238 | 272 ms |
| EmbeddingGemma-300M | 0.243 | 14.3 | 29.0 | 36.1 [33–39] | 51.8 | 58.3 | 0.215 | 211 ms |
| BM25 | 0.227 | 14.7 | 26.2 | 32.6 [29–36] | 47.1 | 53.9 | 0.205 | 16 ms |

Recall values are percentages. `*` marks latencies that are not in-container end-to-end measurements. For API rows that means an internet round trip; for large encoders it means the vector search only.

**The site's own significance commentary (from the changelog):**
- Lean Finder vs. MathLeap-Qwen, nDCG@10: the margin is +0.019, with 95% interval [−0.007, +0.046] and p ≈ 0.16.
- R@10: a three-way tie among Lean Finder, MathLeap-Qwen and LeanSearch v2.
- R@1: the only separated result. Lean Finder leads LeanSearch v2 by +5.5 pt, with interval [+1.9, +9.2] and p ≈ 0.003.
- Lean Finder's best query style is nickname (nDCG@10 0.672) and its worst is Lean syntax (0.536).
- MathLeap-Qwen and Qwen3-Embedding-8B share weights before and after fine-tuning, so the gap between them is the board's one controlled comparison.

## Relevance to lean-explore-bench

This is the closest existing thing to what we want to build, and the obvious reference point.

**What to reuse:**
- The whole reproducibility contract:
  - pinned corpus revision plus renderer hash
  - exact search
  - store per-query rank positions and derive every metric from them
  - k_max pinned in the manifest
  - bootstrap CIs on every headline number
  - n printed next to every row
  - unresolved gold dropped, not scored as a miss
  - deduplication at the first occurrence
  - query-side-only instructions
- The per-style, per-kind and per-difficulty breakdowns.
- The per-query explorer.
- The changelog discipline: a run id, and a new run id whenever the corpus, renderer or metric code changes.

**What it leaves out or gets wrong for our purposes:**
- **Single dataset.** Its conclusions rest entirely on MathlibQR, which is 200 targets written by the LeanSearch v2 authors. Legendre did not write the queries, which helps neutrality, but it inherits MathlibQR's biases, one of which is that the LeanSearch v2 team built both the benchmark and a ranked engine.
- **Mixed conditions for API engines.** Their rows are scored against their own live snapshots: Lean Finder on v4.19.0, LeanSearch v2 on its own v4.28.0-rc1 snapshot, LeanExplore on its own snapshot. Local models use v4.28.0-rc1. Snapshot drift therefore counts against an engine, unless you read the shared171 view.
- **Hosted-service drift.** API results reflect a moment in time and are not reproducible later. The site cached responses but, as far as I found, has not published them.
- **Recall cap.** LeanSearch v2's API cap of k ≤ 50 makes its deep-recall numbers undefined.
- **Narrow query types.** No type-signature, Loogle-pattern, or proof-state queries are evaluated for engines, and no graded relevance. Any near-equivalent lemma counts as a miss.
- **Not open source.** The harness has not been released, so the numbers can be checked against the site's JSON but not re-run by us (unverified whether the JSON is downloadable as a bundle).
- **Neutrality caveat for us:** LeanExplore is ranked 8th of 13, below several off-the-shelf embedding models.

## Open questions

- Will the harness or the cached engine responses be released? Can we obtain the per-query rank JSON to cross-check our own implementation?
- Are MathlibMPR and LeanDojo B4 results published anywhere on the site, or only planned?
- How was the renderer `lsv2-compat` chosen? It is the LeanSearch v2 document format, which may favour models tuned to that format, as MathLeap was.
- Does Legendre plan a second query set that it controls, or other query styles such as type patterns?

## Sources

- Home page with the R@k table, dataset description and endpoints: https://www.legendre-leaderboard.com/
- Leaderboard table, CIs, latencies and licenses: https://www.legendre-leaderboard.com/leaderboard
- Metric definitions, caveats, rate limits, the Lean Finder version choice, and the MathLeap sequence-length override: https://www.legendre-leaderboard.com/methodology
- Per-query ranks and the renderer example: https://www.legendre-leaderboard.com/datasets
- Run history and significance statements: https://www.legendre-leaderboard.com/changelog
- Pinned corpus: https://huggingface.co/datasets/FrenzyMath/lsv2-mathlib-v4.28.0-rc1-jsonl
- MathlibQR source file: https://github.com/frenzymath/LeanSearch-v2/blob/main/benchmark/MathlibQR.json
- Web-search listing, where the site titles itself "LegendreTransform — Lean 4 retrieval leaderboard": https://www.legendre-leaderboard.com/
- Absence of a public repository: my own `gh search repos` queries, not a published statement.
