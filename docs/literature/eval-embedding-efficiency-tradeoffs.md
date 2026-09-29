# Evaluating embeddings under efficiency constraints: Matryoshka truncation, quantization, exact vs ANN indexes

- **Kind:** methodology note
- **Links:** MRL [arXiv:2205.13147](https://arxiv.org/abs/2205.13147); jina-embeddings-v3 [arXiv:2409.10173](https://arxiv.org/abs/2409.10173); HF "Embedding Quantization" blog [hf.co/blog/embedding-quantization](https://huggingface.co/blog/embedding-quantization); HF "Matryoshka Embeddings" blog [hf.co/blog/matryoshka](https://huggingface.co/blog/matryoshka); Lin, "Operational Advice for Dense and Sparse Retrievers" [arXiv:2409.06464](https://arxiv.org/abs/2409.06464); ANN-Benchmarks [arXiv:1807.05614](https://arxiv.org/abs/1807.05614); Big-ANN NeurIPS'23 [arXiv:2409.17424](https://arxiv.org/abs/2409.17424); NV-Embed compression appendix [arXiv:2405.17428](https://arxiv.org/abs/2405.17428); LIMIT [arXiv:2508.21038](https://arxiv.org/abs/2508.21038); CoIR [arXiv:2407.02883](https://arxiv.org/abs/2407.02883)
- **Authors / org, date:** 2018–2025 (see links)
- **Status:** Papers read from arXiv LaTeX. Blog numbers were read through a summarizing fetch and are quoted as given there.

## What it is

A deployed embedding stage is defined by three things:

1. the model;
2. the stored representation (dimension, precision);
3. the search structure (exact/flat, HNSW, IVF, with parameters).

Model papers mostly report (1) with exact search at full dimension and fp32/bf16. Real engines, including Lean ones, change all three. This note collects how the literature measures quality loss and cost when (2) and (3) change.

## How it works

### Dimension truncation (Matryoshka)

- **Original protocol (MRL).** Evaluate retrieval at each nested dimension with **mAP@10**, and measure cost as MFLOPs per query under exact search. Compare against independently trained fixed-size models, SVD and random-feature truncation ([MRL, Retrieval section](https://arxiv.org/abs/2205.13147)).
- **Adaptive retrieval.** MRL also tests a cascade: shortlist K=200 with a low-dimensional prefix (for example D_s=16), then rerank with the full vector (D_r=2048). It plots accuracy against compute as a Pareto frontier.

  For us this is the right shape: a quality-vs-cost curve, not one number.
- **Text-embedding practice.** jina-embeddings-v3 reports average retrieval nDCG@10 by dimension: 52.54 (32), 58.54 (64), 61.64 (128), 62.72 (256), 63.16 (512), 63.30 (768), 63.35 (1024) ([jina-v3 Table MRL](https://arxiv.org/abs/2409.10173)). Over the same range, STS moves only from 76.35 to 77.58. **Retrieval degrades much faster than STS under truncation.**
- **Measure truncation on retrieval, not STS.** The widely cited HF Matryoshka blog measures truncation on the STSBenchmark test set with Spearman correlation ("Even at 8.3% of the embedding size, the Matryoshka model preserves 98.37% of the performance") ([HF blog](https://huggingface.co/blog/matryoshka)). Given the jina numbers, STS retention overstates retrieval retention.
- **Re-normalize after truncating.** The blog's author advises that embeddings be "(re-)normalized after the Matryoshka truncation" (comment on [HF blog](https://huggingface.co/blog/matryoshka)). Whether this was done is an evaluation detail to record.
- **Model papers usually support truncation without showing its cost.**
  - Gemini Embedding supports 3,072 dimensions "with the MRL support on 768 and 1,536 dimensions" but reports headline results at full size ([Gemini](https://arxiv.org/abs/2503.07891)).
  - Qwen3 lists "MRL Support: Yes" without per-dimension retrieval numbers ([Qwen3 Table 1](https://arxiv.org/abs/2506.05176)).
  - LIMIT does sweep truncated dimensions and marks MRL-trained models, noting that truncating a non-MRL model "will result in sub-par scores" ([LIMIT](https://arxiv.org/abs/2508.21038)).
- **There is a theoretical floor.** LIMIT shows that the number of distinct top-k sets an embedding can return is bounded by its dimension, and extrapolates a "critical-n" for k=2 of about 500k documents at d=512 and about 4M at d=1024 under free (test-set-optimized) embeddings ([LIMIT, free-embedding experiment](https://arxiv.org/abs/2508.21038)). Mathlib's roughly 200k+ declarations are below these best-case numbers, but real models sit well below the free-embedding optimum. Aggressive truncation should be tested, not assumed safe.

### Vector quantization (int8, binary)

- **HF / sentence-transformers protocol** (Shakir, Aarsen, Lee, 22 Mar 2024), on "the retrieval subset of the MTEB containing 15 benchmarks" with nDCG@10 ([HF blog](https://huggingface.co/blog/embedding-quantization)):
  - binary without rescoring keeps "roughly ~92.5%" of the retrieval performance, and "up to ~96%" with rescoring;
  - int8 keeps about 97–100% depending on the model;
  - speedups are reported as about 3.66× for int8 and about 24.76× for binary, with 4× and 32× less storage than fp32.
- **Rescoring is part of the method and must be reported.** Retrieve `rescore_multiplier × top_k` with the quantized query, then rescore with the float query. The blog used a multiplier of 4, giving 400 candidates for top-k=100, and found that 4–5 already retains about 99% for int8 ([HF blog](https://huggingface.co/blog/embedding-quantization)). The blog also cautions that "Quantization doesn't universally work with all embedding models."
- **Model-weight quantization is a separate axis.** NV-Embed reports that its pruned model at INT8 "maintains nearly identical MTEB scores", while smaller baselines lose 0.14–0.84%. FP8 (E4M3/E5M2) is comparable to INT8 ([NV-Embed App. compression](https://arxiv.org/abs/2405.17428)). This is measured as an MTEB average, not as retrieval at depth.

### Exact vs ANN index

- **Lin (2024) is the best template we found for index-aware evaluation.** Setup ([arXiv:2409.06464](https://arxiv.org/abs/2409.06464)):
  - BEIR with BGE-base in Lucene, comparing flat, HNSW, and int8-quantized variants of each;
  - M=16, efC=100, efSearch=1000, "retrieved 1000 hits and evaluated retrieval quality in terms of nDCG@10";
  - QPS on 16 threads, measured with both cached and freshly encoded queries;
  - indexing time;
  - the **nDCG@10 difference from flat with a confidence interval, averaged over 5 trials**, because "both HNSW indexing and quantization are non-deterministic".
- **Findings:**
  - On BioASQ (about 15M documents), HNSW plus int8 lowers nDCG@10 by 0.017 on average and up to 0.024 (4% and 5.8%).
  - "For corpora with fewer than 1M documents, we do not see a compelling advantage to using HNSW indexes."
  - The methodological point: "These effects are potentially problematic when comparing different embedding models that are 'close' in terms of quality, because it would be hard to tease apart model quality from an 'unlucky' sub-optimal index. Nearly all academic papers sweep these differences under the rug ... flat indexes are appealing ... to isolate the quality of embedding models."
- **ANN-Benchmarks and Big-ANN** evaluate the index alone. They plot recall against the *exact* k nearest neighbours versus queries per second across parameter sweeps, as a Pareto frontier ([ANN-Benchmarks](https://arxiv.org/abs/1807.05614); [Big-ANN'23](https://arxiv.org/abs/2409.17424)). This k-NN recall is independent of relevance labels, which makes it a clean way to measure index error separately from model error.
- **Some Lean evaluation already follows this.** Legendre uses exact inner product "so that approximate-index recall error is not mixed into model error" ([bench-legendre-leaderboard.md](bench-legendre-leaderboard.md)). LeanExplore in production uses FAISS IVF with `nprobe=64` ([embed-mteb.md](embed-mteb.md)).

### Latency and cost reporting

- **CoIR reports "embedding latency"** as the time per batch divided by batch size, for example 1840 ms per sample for E5-Mistral ([CoIR, efficiency analysis](https://arxiv.org/abs/2407.02883)).
- **Lin separates query encoding from search** by measuring QPS with cached versus ONNX-encoded queries ([arXiv:2409.06464](https://arxiv.org/abs/2409.06464)). Without this split, a 7B encoder's latency hides the index cost, or the other way round.

## Evaluation (issues)

- Quality numbers in model papers come from exact search at full dimension and precision. They are an **upper bound** for any deployed configuration.
- Retention is often reported as "% of full-dimension score" averaged over tasks. That hides per-task collapse and the difference between STS and retrieval.
- HNSW and IVF results are non-deterministic: build order and threads matter. A single run can flip the order of two close models.

## Relevance to lean-explore-bench

1. **Model track uses flat exact search.** Score every embedder (and its dimension/precision variants) with brute-force inner product over normalized vectors. At about 200k–500k vectors this is cheap, and Lin's under-1M advice applies.
2. **System track reports the deployed index.** Evaluate engines as shipped, and when we can rebuild their index, also report **Δ = system(ANN) − system(flat)** with a CI over at least 3 index builds. Report k-NN recall@K of the ANN index against flat, so that index error is separated from model error.
3. **Efficiency curves, not points.**
   - For MRL-capable models, sweep d ∈ {full, 1024, 512, 256, 128}, re-normalizing after truncation.
   - For precision, test {fp32, int8, binary with rescoring ×4}.
   - Report retrieval metrics (Recall@50, nDCG@10), never STS, against index bytes per vector and p50/p95 latency.
4. **Split latency** into query encoding (hardware stated), search, and reranking. Report cached-query QPS separately.
5. **Pin the configuration:** the FAISS/Lucene version, index type and parameters (nlist, nprobe, M, efSearch), rescoring multiplier, and seeds.

## Open questions

- Should the efficiency axis be a hard budget (for example "best nDCG@10 under 512 bytes per vector and 50 ms p95 on CPU") or a reported Pareto frontier? A budget makes a leaderboard. A frontier is more honest.
- For hosted engines whose index we cannot rebuild, is the black-box latency measured from our client meaningful enough to publish, given network variance?

## Sources

- MRL: https://arxiv.org/abs/2205.13147 (apps+expts.tex: retrieval, adaptive retrieval, funnel retrieval)
- jina-embeddings-v3 MRL table: https://arxiv.org/abs/2409.10173 (paper.tex Table "MRL ablation")
- HF Embedding Quantization blog (2024-03-22): https://huggingface.co/blog/embedding-quantization
- HF Matryoshka blog (2024-02-23): https://huggingface.co/blog/matryoshka
- Lin 2024, HNSW vs flat: https://arxiv.org/abs/2409.06464 (main.tex, table-rq1/rq2)
- ANN-Benchmarks: https://arxiv.org/abs/1807.05614
- Big-ANN NeurIPS'23: https://arxiv.org/abs/2409.17424
- NV-Embed compression appendix: https://arxiv.org/abs/2405.17428
- Gemini Embedding MRL dims: https://arxiv.org/abs/2503.07891
- Qwen3 MRL support: https://arxiv.org/abs/2506.05176
- LIMIT: https://arxiv.org/abs/2508.21038
- CoIR latency: https://arxiv.org/abs/2407.02883
