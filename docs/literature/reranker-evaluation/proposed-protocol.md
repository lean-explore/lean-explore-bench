# Proposed protocol: evaluating the reranking stage in lean-explore-bench

- **Kind:** synthesis and recommendation (derived from the other `eval-reranker-*` notes)
- **Links:**
  - [fixed-candidate-protocol.md](fixed-candidate-protocol.md)
  - [llm-order-cost-contamination.md](llm-order-cost-contamination.md)
  - [model-card-reporting.md](model-card-reporting.md)
  - [tooling.md](tooling.md)
- **Status:** a proposal, not yet implemented.

## What it is

This is a concrete protocol for measuring what a second-stage reranker contributes to a Lean search engine, measured both **separately** from first-stage retrieval and **together** with it. Each element cites the literature precedent it follows.

## Protocol

1. **Freeze first-stage candidate lists.** Precedent: TREC DL rerank subtask; ir_datasets `scoreddocs`.
   - For each query, publish frozen top-K run files from at least three first stages:
     - (a) BM25 over names plus docstrings;
     - (b) a dense retriever, for example Qwen3-Embedding-0.6B over informalizations;
     - (c) LeanExplore's own fused list (BM25 + FAISS, RRF, dependency boost), taken from its local backend with the reranker disabled. Whether `rerank_top = 0` disables it is unverified; check `local-backend.md`.
   - Set K = 100, plus K = 1000 for depth studies.
   - Use strictly decreasing scores, because of the trec_eval tie-break on docno.
2. **Report the ceiling of each first stage.** Precedent: survey §3.2.2; Expando-Mono-Duo §5.4.
   - Report R@K and nDCG@10 for each first stage.
   - Also report an **oracle rerank**: the candidates sorted by graded qrels, giving the best nDCG@10 attainable from that list. This makes "headroom captured = (reranked − retrieve-only) / (oracle − retrieve-only)" computable.
3. **Rerank-only track.** Precedent: Jina v3, Qwen3, RankVicuna, RankZephyr.
   - Every reranker, including LeanExplore's Qwen3-Reranker-0.6B, the larger Qwen3-Reranker sizes, bge-reranker-v2-m3 and any LLM listwise ranker, reranks *the same* frozen lists.
   - Report nDCG@10 and RR@10 per first stage, not averaged across first stages. Gains shrink over strong first stages, and a single number hides this.
4. **Depth sweep.** Precedent: Drowning in Documents; RankVicuna top-20 vs top-100.
   - Sweep rerank depth k ∈ {10, 25, 50, 100, 200, 1000}. Where feasible, add full-corpus reranking on a query subsample.
   - Plot nDCG@10 against k, and latency against k.
   - LeanExplore ships `rerank_top` at 25–50, so this directly tests whether that choice is on the frontier.
5. **End-to-end track.** Precedent: ColBERT's end-to-end mode; the TREC DL full-ranking task.
   - Each engine as shipped, at a pinned data version, is compared against other engines.
   - Include within-engine ablations: retrieve-only against retrieve+rerank (as LeanSearch v2 reports), and for LeanExplore each component removed in turn (BM25-names, dense, dependency boost, reranker).
6. **Robustness for LLM or listwise stages only.** Precedent: RankGPT, PRP, Setwise, RankZephyr, permutation self-consistency.
   - Evaluate under the original, reversed and ≥5 shuffled candidate orders, reporting mean ± 99% CI.
   - Run ≥3 repeats for API models.
   - Count malformed outputs and document the fallback policy.
   - Pointwise cross-encoders can skip this, but a one-time shuffle sanity check confirms order invariance cheaply.
7. **Cost columns on every row.** Precedent: Setwise; RankGPT's API Cost appendix.
   - Report pairs scored (cross-encoder), LLM calls, prompt and generated tokens, p50/p95 latency per query with stated hardware and batch size, and USD for APIs.
   - Report the reranker's cost separately from the first stage's.
8. **Contamination slice.** Precedent: NovelEval, FutureQueryEval.
   - Tag queries whose gold declarations entered Mathlib after the release date of each model under test.
   - Report the old-vs-new gap per stage. The first stage and the reranker may be differently contaminated.
9. **Judgment coverage.** Precedent: RankZephyr Judged@10; TREC pooling.
   - Pool judgments across all first stages *and* all reranked outputs to depth 10 at least.
   - Report Judged@10 per run, so that rerankers surfacing unjudged declarations are not penalised silently.
10. **Statistics and tooling.**
    - Compute per-query results with ir-measures or trec_eval. Use paired randomization tests with Holm correction (ranx `compare()` plus our own correction).
    - Release all run files, so reranker-only claims can be re-checked against the frozen candidates.

## Open questions

- Which first stage should be the "canonical" one for the rerank-only leaderboard? A reasonable default is the strongest open first stage, since weak-first-stage gains overstate reranker value. Reporting BM25 as a second column keeps comparability with the literature.
- How should the pipelines of engines that cannot expose their candidates (hosted-only APIs) be handled? These can only enter the end-to-end track.

## Sources

See the four linked notes. Key primary sources:

- https://arxiv.org/abs/2010.06467
- https://arxiv.org/abs/2101.05667
- https://arxiv.org/abs/2309.15088
- https://arxiv.org/abs/2312.02724
- https://arxiv.org/abs/2411.11767
- https://arxiv.org/abs/2310.09497
- https://arxiv.org/abs/2304.09542
- https://arxiv.org/abs/2508.16757
- https://arxiv.org/abs/2003.07820
- https://github.com/usnistgov/trec_eval
