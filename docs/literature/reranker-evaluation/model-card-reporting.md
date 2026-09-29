# How reranker model cards report evaluation (BGE, Jina, mixedbread, Cohere, Qwen3)

- **Kind:** evaluation methodology (vendor reports and model cards)
- **Links:** see Sources
- **Authors / org, date:** BAAI, Jina AI, mixedbread, Cohere, Alibaba Qwen; 2024–2025
- **Status:** cards are live and may change. Content was checked on 2026-09-28.

## What it is

This note is a survey of the *evaluation choices* behind published reranker scores. It exists so that lean-explore-bench does not compare numbers that were produced under different protocols. It says nothing about which model is better.

## Reporting choices by vendor

| Model | First stage | Depth | Benchmarks and metric | Latency reported? |
|---|---|---|---|---|
| bge-reranker-v2 ([HF](https://huggingface.co/BAAI/bge-reranker-v2-m3), [README](https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/research/llm_reranker/README.md)) | BAAI's own embedders; BEIR is run twice (bge-en-v1.5 large and e5-mistral-7b-instruct) | top-100 | BEIR, CMTEB-retrieval, MIRACL, llama-index; charts only, metric not named in text | not found |
| jina-reranker-v2 ([HF](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual), [blog](https://jina.ai/news/jina-reranker-v2-for-agentic-rag-ultra-fast-multilingual-function-calling-and-code-search/)) | not stated | not stated | BEIR nDCG@10, MKQA, MLDR R@10, CodeSearchNet MRR@10, ToolBench R@3, etc. | throughput: "documents retrieved in 50ms" on an RTX 4090 |
| jina-reranker-v3 ([arXiv:2509.25085](https://arxiv.org/abs/2509.25085)) | jina-embeddings-v3 | top-100 | BEIR, MIRACL, MKQA, CoIR, nDCG@10 | not found |
| mxbai-rerank-v1 ([blog](https://www.mixedbread.com/blog/mxbai-rerank-v1)) | lexical (Pyserini) | top-100 | 11-dataset BEIR subset; NDCG@10 and Accuracy@3 | not found |
| mxbai-rerank-v2 ([blog](https://www.mixedbread.com/blog/mxbai-rerank-v2)) | BM25 | not stated | BEIR NDCG@10 | seconds per query on NFCorpus, A100 80GB |
| Cohere Rerank 3 ([blog](https://cohere.com/blog/rerank-3)) | BM25, for the LLM comparison only | top-100 | a mix of recall@5, nDCG@10 per domain; a SciFact query subsample for the LLM comparison | time to rank 50 docs at uniform lengths, relative to Rerank 2 |
| Cohere Rerank 3.5 ([blog](https://cohere.com/blog/rerank-3pt5)) | not stated | not stated | nDCG@10, P@1 of 2, and relative gains on an unreleased financial dataset | not found |
| Qwen3-Reranker ([HF](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B), [arXiv:2506.05176](https://arxiv.org/abs/2506.05176)) | Qwen3-Embedding-0.6B | top-100 | MTEB-R, CMTEB-R, MMTEB-R, MTEB-Code, MLDR, FollowIR | not found |

Notes on individual cards:

- **Jina v2 has conflicting MKQA metrics.** The blog reports MKQA as recall@10, but the HF card labels it nDCG@10.
- **Jina v3 states its method.** "All scores are our runs based on the retrieval top-100 results from the first row", and fixing the candidates "eliminates retrieval variance and isolates reranking effectiveness" ([arXiv:2509.25085](https://arxiv.org/abs/2509.25085)).
- **mxbai v1 gives its reason for the BEIR subset:** it was "chosen for its appropriate ratio between computational demand and real-world applicability" ([mixedbread v1 blog](https://www.mixedbread.com/blog/mxbai-rerank-v1)).
- **mxbai v2 depth.** The depth may be in the spreadsheet linked from the blog (unverified).
- **Cohere 3.5.** The financial-dataset gains are "+23.4% better than Hybrid Search and +30.8% better than BM25" on data that has not been released ([Cohere 3.5 blog](https://cohere.com/blog/rerank-3pt5)).
- **Qwen3 metric.** Metric names are not given per column on the card. nDCG@10 is inferred from the MTEB defaults (unverified).
- **Qwen3 reranks its own embedder's candidates.** On MTEB-R, the Qwen3-Embedding-0.6B first stage scores 61.82 and Qwen3-Reranker-0.6B scores 65.80 ([arXiv:2506.05176](https://arxiv.org/abs/2506.05176) Table 5).

## Patterns and pitfalls

- **The same depth hides different first stages.** Top-100 is near-universal, but the candidates come from BM25 (mixedbread, Cohere's LLM comparison), the vendor's own dense embedder (BGE, Jina v3, Qwen3) or an unstated source (Jina v2, Cohere 3.5). Because reranker gains shrink over strong first stages ([fixed-candidate-protocol.md](fixed-candidate-protocol.md)), scores on BM25 candidates and scores on dense candidates are **not comparable across cards**.
- **Vendors pair the reranker with their own embedder.** This is a legitimate end-to-end number, but it is not a reranker-only number. BGE reporting BEIR over two different first stages is the more informative pattern.
- **Benchmark subsets differ.** Examples are an 11-dataset BEIR subset (mixedbread v1), 17 BEIR datasets (Jina v2), and an MTEB retrieval subset (Qwen3). Averages over different subsets are not comparable.
- **Latency is reported in three incompatible units:**
  - seconds per query on one small dataset (mixedbread);
  - documents per 50 ms (Jina);
  - relative time to rank 50 fixed-length docs (Cohere).

  None gives p95 latency, candidate count plus document length together, and batch size in one place.
- **Proprietary evaluation sets.** Cohere 3.5 and the internal enterprise sets in Drowning in Documents ([arXiv:2411.11767](https://arxiv.org/abs/2411.11767)) cannot be reproduced. They do reduce contamination risk.

## Relevance to lean-explore-bench

- **Do not reuse vendor numbers.** Treat vendor BEIR or MTEB scores as uninformative for Lean. Re-run every candidate reranker (Qwen3-Reranker 0.6B/4B/8B, bge-reranker-v2-m3, jina-v2/v3, mxbai-v2) ourselves on **identical Lean candidate lists** from ≥2 first stages, for example a BM25-on-names/docstrings list and LeanExplore's fused list.
- **Publish a full protocol record per run:** first-stage run file, depth, truncation length (document tokens), prompt/instruction string (Qwen3-Reranker is instruction-conditioned), batch size, hardware, and latency percentiles.
- **Instruction-conditioned rerankers.** LeanSearch v2 uses a "kind-aware" prompt with Qwen3-Reranker ([../premise-selection/leansearch-v2.md](../premise-selection/leansearch-v2.md)). The instruction text is therefore a hyperparameter and should be fixed or ablated.

## Open questions

- What document text does each Lean engine feed its reranker: signature, docstring, informalization or a concatenation? This interacts with truncation and needs to be recorded per engine.

## Sources

- https://huggingface.co/BAAI/bge-reranker-v2-m3 ; https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/research/llm_reranker/README.md
- https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual ; https://jina.ai/news/jina-reranker-v2-for-agentic-rag-ultra-fast-multilingual-function-calling-and-code-search/
- https://arxiv.org/abs/2509.25085 (jina-reranker-v3) ; https://huggingface.co/jinaai/jina-reranker-m0
- https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v1 ; https://www.mixedbread.com/blog/mxbai-rerank-v1 ; https://www.mixedbread.com/blog/mxbai-rerank-v2
- https://cohere.com/blog/rerank-3 ; https://cohere.com/blog/rerank-3pt5
- https://huggingface.co/Qwen/Qwen3-Reranker-0.6B ; https://arxiv.org/abs/2506.05176
- https://arxiv.org/abs/2411.11767 (Drowning in Documents)
