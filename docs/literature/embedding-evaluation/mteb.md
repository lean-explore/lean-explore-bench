# MTEB / MMTEB / RTEB (Massive Text Embedding Benchmark family)

- **Kind:** benchmark / dataset + leaderboard + evaluation library
- **Links:** MTEB paper [arXiv:2210.07316](https://arxiv.org/abs/2210.07316); MMTEB paper [arXiv:2502.13595](https://arxiv.org/abs/2502.13595); "Maintaining MTEB" [arXiv:2506.21182](https://arxiv.org/abs/2506.21182); code [github.com/embeddings-benchmark/mteb](https://github.com/embeddings-benchmark/mteb); leaderboard [hf.co/spaces/mteb/leaderboard](https://huggingface.co/spaces/mteb/leaderboard); MTEB v2 release post [docs/blog/posts/mteb-v2.md](https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md); RTEB post [hf.co/blog/rteb](https://huggingface.co/blog/rteb)
- **Authors / org, date:** Muennighoff, Tazi, Magne, Reimers (Hugging Face), Oct 2022 (EACL 2023); MMTEB by Enevoldsen et al. (86 authors), Feb 2025 (ICLR 2025); MTEB v2 package released 2025-09-22; RTEB announced 2025-10-01 (MongoDB + MTEB maintainers).
- **Status:** Live, Apache-2.0 library, actively maintained (a video extension, MVEB, [arXiv:2606.14958](https://arxiv.org/abs/2606.14958), was added June 2026).

## What it is

The standard benchmark and leaderboard for text embedding models. The original MTEB covered "8 embedding tasks covering a total of 58 datasets and 112 languages", and found that "no particular text embedding method dominates across all tasks" ([arXiv:2210.07316](https://arxiv.org/abs/2210.07316)). Retrieval is one task type among classification, clustering, pair classification, reranking, STS, summarization and bitext mining. The retrieval part was taken from BEIR (see [beir.md](beir.md)).

MMTEB extends this to "over 500 quality-controlled evaluation tasks across 250+ languages" and defines curated sub-benchmarks: `MTEB(Multilingual)`, `MTEB(Europe)`, `MTEB(Indic)`, `MTEB(eng, v2)`, plus domain benchmarks such as CoIR for code ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), §2.4). BRIGHT is also available as the task `BrightRetrieval` / `BrightLongRetrieval` ([mteb source](https://github.com/embeddings-benchmark/mteb/blob/main/mteb/tasks/retrieval/eng/bright_retrieval.py)).

RTEB (Retrieval Embedding Benchmark) is a retrieval-only section of the leaderboard. It mixes open datasets with **private** datasets that only the MTEB maintainers can evaluate on. The motivation it gives: "When models are repeatedly evaluated against the same public datasets, a gap emerges between their reported scores and their actual performance on new, unseen data" ([RTEB blog](https://huggingface.co/blog/rteb)).

## How it works

**Retrieval task format (MTEB v2).** Each retrieval task has `corpus`, `queries`, `qrels` (`query-id`, `corpus-id`, integer or float `score`), and optionally `top_ranked` (a per-query candidate list). Reranking is now the same task type as retrieval, run over a `top_ranked` list, and there is a `CrossEncoderProtocol` for rerankers ([MTEB v2 post](https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md)).

**Whole systems, not just encoders.** MTEB v2 adds a `SearchProtocol` with `index(corpus, ...)` and `search(queries, ..., top_k, top_ranked)`. It exists so that "non-embedding based retrieval systems" and custom indexes can be evaluated. Encoders and cross-encoders are wrapped into it automatically ([MTEB v2 post](https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md)). This matters directly to us: a hybrid engine like LeanExplore can be run as one opaque `search` implementation.

**Metrics.** For retrieval the main score is nDCG@10, following BEIR. The library also reports MAP, MRR, recall and precision at several cutoffs through pytrec_eval ([arXiv:2210.07316](https://arxiv.org/abs/2210.07316); [BEIR §metrics](https://arxiv.org/abs/2104.08663)). An `ignore_identical_ids` flag drops a query's own id from the results when queries and corpus overlap ([retrieval_evaluator.py](https://github.com/embeddings-benchmark/mteb/blob/main/mteb/_evaluators/retrieval_evaluator.py)).

**Aggregation.** MMTEB reports the mean over tasks, the mean per task category, and a category-weighted mean. It ranks models with a **Borda count**, treating "each task as a preference voter", because Borda is "more robust for comparing NLP systems" than a plain mean ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), §3.2).

**Making evaluation cheaper while keeping the ranking.**
- *Retrieval corpus downsampling by TREC-style pooling.* For each query, MMTEB kept the union of the top 250 documents from BM25, multilingual-e5-large and e5-mistral-7b-instruct. It capped each task at 1,000 queries, which shrank the largest corpora "from over 5 million documents to a maximum of 250,000" ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), §2.3.1). An ablation on NQ (1 relevant document per query) and TREC-COVID (500+ per query) found that keeping more than 100 hard negatives per query preserves both absolute scores and model ranking. They chose 250 to be conservative ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), App. C).
- *Task selection by inter-task correlation.* Tasks whose scores are most predictable from the remaining tasks are dropped greedily, using Spearman correlation as the similarity. `MTEB(eng, v2)` has 40 tasks instead of 56 and correlates with `MTEB(eng, v1)` at Spearman 0.90 ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), §4).

**Reproducibility machinery** ([arXiv:2506.21182](https://arxiv.org/abs/2506.21182), §3):
- Versioning at four levels: task, dataset (pinned HF revision), model (checkpoint or API version) and code (semver).
- Fixed seeds.
- CO2 logging.
- The leaderboard moved "from relying on self-reported results in Hugging Face model cards to a centralized repository of verified results". A submission needs a reference implementation and goes through PR review.

## Evaluation (known issues and what they teach)

**Leaderboard overfitting through in-distribution training data.** The "Maintaining MTEB" paper plots mean score against zero-shot score and states that "the highest ranking models achieve their scores by training on benchmark tasks, even though models with lower scores might generalize better" ([arXiv:2506.21182](https://arxiv.org/abs/2506.21182), zero-shot figure caption). The response was:
- Model contributors are asked to disclose their training datasets.
- The leaderboard shows a **zero-shot score** `z = 1 - n_train / n_total`, where `n_train` counts benchmark datasets whose training split the model saw. Example: e5-mistral-7b-instruct has 95% on `MTEB(eng, v2)`.
- An earlier version hid every model below 100% zero-shot. It was relaxed "as community members noted it penalized transparency" (same paper, §5.1; discussion threads [#2119](https://github.com/embeddings-benchmark/mteb/discussions/2119), [#2351](https://github.com/embeddings-benchmark/mteb/discussions/2351)).
- `MTEB(eng, v2)` leaves out MS MARCO and NQ "which are frequently used in fine-tuning" and is intended as a zero-shot benchmark ([arXiv:2502.13595](https://arxiv.org/abs/2502.13595), §2.4).

**Reproducing reported scores is fragile.** Moving to verified results showed that scores depend on details that model cards often leave out ([arXiv:2506.21182](https://arxiv.org/abs/2506.21182), §5.2 and the appendix "Reproducing Reported Results"):
- query and passage prefixes (E5/BGE)
- prompts that differ per task type (Nomic)
- instructions placed on both sides (E5-mistral) versus on the query only (NV-Embed)
- whether embeddings are normalized
- custom encode arguments (jina-v3 `task_type` LoRA)
- multi-stage encoders (CDE)

Adding prefix support "allowed us to reproduce the reported performance of BGE models, which had previously shown significant performance degradation".

**Private held-out data has its own trust problem.** On 2026-01-14 the maintainers temporarily removed the private RTEB column. One vendor (Voyage) had co-developed the private data, and "this joint development structure means Voyage has direct access to the private evaluation data, an undeniable structural advantage". It will be restored once there are more private datasets from diverse sources ([mteb#3934](https://github.com/embeddings-benchmark/mteb/issues/3934)).

**General benchmarks are poor proxies for narrow domains.**
- MTEB-BR reports that a model's multilingual-leaderboard rank predicts its Portuguese rank only moderately (Spearman 0.75 over 55 models) ([arXiv:2607.04581](https://arxiv.org/abs/2607.04581)).
- SABER-Math reports that "general-purpose IR benchmarks such as MTEB do not reliably predict mathematical performance, especially for recent embedding models" ([arXiv:2606.29894](https://arxiv.org/abs/2606.29894), abstract).

**Statistical reporting.** Core MTEB reports point estimates only. Derivative benchmarks have begun adding per-task bootstrap CIs and paired-bootstrap significance tests. MTEB-BR finds its "top six are statistically too close to order" ([arXiv:2607.04581](https://arxiv.org/abs/2607.04581)).

## Relevance to lean-explore-bench

- **Reuse the data format and harness.** Use `corpus` / `queries` / `qrels` / `top_ranked` so the benchmark can be loaded as an MTEB custom task. We then get pytrec_eval metrics, caching and result files for free. LeanExplore (hybrid BM25 + dense + reranker + dependency boost) and other Lean engines can each be wrapped as a `SearchProtocol`. An embedding model on its own can be wrapped as an `Encoder`.
- **Borrow the zero-shot disclosure idea.** Record for each system whether its training or informalization data overlaps the benchmark's queries or gold declarations. Examples: LeanSearch's own eval set, LeanDojo premise data, Mathlib docstrings used as queries.
- **Pooling and hard-negative downsampling are cheap, but they bias the benchmark toward the systems in the pool.** For a Mathlib-sized corpus (roughly 200k+ declarations) we can afford to evaluate against the full corpus. Relevance *judging* will still be pooled, so we need a hole analysis (see [beir.md](beir.md)).
- **Pin every version:** Mathlib commit, corpus snapshot, model revisions, prompts/instructions, and the index type. Include ANN parameters: LeanExplore uses FAISS IVF with `nprobe=64` ([indexes.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/indexes.py)), not exact search.
- **Consider a private held-out split** of queries, and settle its governance up front. RTEB shows that it matters who can see it.

## Open questions

- Should our headline aggregate be a mean or Borda across query categories (natural-language / name / type-signature / premise)? Borda is robust but hides effect sizes.
- How should the zero-shot score be defined when the "training data" is an LLM informalization of the corpus itself? This is the case for LeanExplore and LeanSearch.

## Sources

- MTEB: https://arxiv.org/abs/2210.07316
- MMTEB: https://arxiv.org/abs/2502.13595 (methodology details read from the arXiv LaTeX source: §2–4 and the speed-up appendix)
- Maintaining MTEB: https://arxiv.org/abs/2506.21182 (§3, §5, appendices)
- MTEB v2 release post (2025-09-22): https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md
- BRIGHT in MTEB: https://github.com/embeddings-benchmark/mteb/blob/main/mteb/tasks/retrieval/eng/bright_retrieval.py
- RTEB blog (2025-10-01): https://huggingface.co/blog/rteb
- RTEB private column removal (2026-01-14): https://github.com/embeddings-benchmark/mteb/issues/3934
- MTEB-BR: https://arxiv.org/abs/2607.04581
- SABER-Math: https://arxiv.org/abs/2606.29894
- MVEB: https://arxiv.org/abs/2606.14958
