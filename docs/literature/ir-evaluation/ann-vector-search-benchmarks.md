# Vector search (FAISS, HNSW, ScaNN) and how ANN is benchmarked (ANN-Benchmarks, big-ann, VIBE)

- **Kind:** tool + benchmark (cluster)
- **Links:**
  - FAISS: https://github.com/facebookresearch/faiss ; papers https://arxiv.org/abs/1702.08734 and https://arxiv.org/abs/2401.08281
  - HNSW: https://arxiv.org/abs/1603.09320
  - ScaNN: https://arxiv.org/abs/1908.10396 ; code https://github.com/google-research/google-research/tree/master/scann
  - ANN-Benchmarks: https://arxiv.org/abs/1807.05614 ; repo https://github.com/erikbern/ann-benchmarks
  - NeurIPS'21 big-ann: https://arxiv.org/abs/2205.03763
  - VIBE: https://arxiv.org/abs/2505.17810
- **Authors / org, date:** Meta (FAISS), Malkov & Yashunin (HNSW), Google (ScaNN), Aumüller et al. (ANN-Benchmarks, VIBE), 2016–2026.
- **Status:** the ANN-Benchmarks README now says it "is no longer actively maintained" and points to VIBE (checked 2026-09-28).

## What it is

Approximate nearest-neighbour (ANN) indexes trade exactness for speed. They include:

- graph indexes (HNSW);
- inverted-file and product-quantisation indexes (FAISS IVF-PQ);
- anisotropic quantisation for maximum inner product search (ScaNN).

The benchmarks measure **recall against exact k-NN ground truth** versus **throughput or latency**. They do not measure task relevance.

## Evaluation methodology

- **ANN-Benchmarks.**
  - Datasets are pre-split into train and test sets and include ground truth for the top-100 nearest neighbours.
  - Each algorithm runs in Docker and is swept over parameter settings, producing recall vs queries-per-second Pareto plots.
  - The April 2025 results were run on AWS r6i.16xlarge with "hyperthreading disabled. All benchmarks are single-CPU" ([README](https://github.com/erikbern/ann-benchmarks)).
  - The paper notes that "very different approaches ... yield comparable quality-performance trade-offs" ([arXiv:1807.05614](https://arxiv.org/abs/1807.05614)).
- **big-ann (NeurIPS'21).**
  - Billion-scale datasets, with hardware-constrained tracks: T1 limited DRAM with a FAISS baseline, T2 DRAM+SSD with a DiskANN baseline, T3 any hardware.
  - Ranked by "recall at a query throughput threshold". T3 also has cost-normalised and power-normalised leaderboards ([arXiv:2205.03763](https://arxiv.org/abs/2205.03763)).
- **VIBE.** Argues that older datasets "no longer represent modern ANN applications". It generates datasets with modern embedding models, adds **out-of-distribution** query sets where queries and corpus come from different distributions, and evaluates 22 index implementations on 11 in-distribution and 8 OOD datasets ([arXiv:2505.17810](https://arxiv.org/abs/2505.17810)).
- **Library papers.**
  - HNSW reports performance at high recall and on clustered data against prior open-source methods ([arXiv:1603.09320](https://arxiv.org/abs/1603.09320)).
  - ScaNN claims state of the art on the ann-benchmarks.com public benchmarks ([arXiv:1908.10396](https://arxiv.org/abs/1908.10396)).
  - The Faiss library paper "describes the trade-off space of vector search" ([arXiv:2401.08281](https://arxiv.org/abs/2401.08281)).
- **Production practice.**
  - Facebook EBR measured ANN accuracy as **1-recall@10**: how often the exact top-1 result appears in the ANN top-10.
  - Its advice is to retune ANN parameters after any non-trivial model change. A model with better exact-kNN recall lost that advantage after quantisation, so "the actual benefit diminished when serving it online" ([arXiv:2006.11632](https://arxiv.org/abs/2006.11632), §4 and §6).
  - Twitter's repo has an equivalent harness that compares HNSW and Annoy against brute force across `efSearch` settings (see [twitter-the-algorithm.md](twitter-the-algorithm.md)).

## Relevance to lean-explore-bench

- **Separate embedding quality from ANN loss.** For engines where we control the index, such as self-hosted LeanExplore, run the embedding model with **exact** search and with the production ANN index. Report both task nDCG and ANN recall@k against exact. Mathlib is on the order of hundreds of thousands of declarations (unverified count), so exact search is cheap, and the ANN gap can be measured outright.
- **OOD queries.** VIBE's OOD point applies directly: Lean queries (natural language) and the corpus (formal statements or informalisations) come from different distributions. ANN recall measured with in-distribution queries may overstate recall.
- **Latency reporting.** Adopt ANN-Benchmarks-style hygiene: fixed hardware, single-thread and batch settings stated, and warm cache stated.

## Open questions

- Which Lean engines expose ANN parameters? Hosted APIs will not, so for those we can measure only end-to-end latency.

## Sources

- https://github.com/erikbern/ann-benchmarks ; https://arxiv.org/abs/1807.05614
- https://arxiv.org/abs/2205.03763 ; https://arxiv.org/abs/2505.17810
- https://arxiv.org/abs/1603.09320 ; https://arxiv.org/abs/1908.10396 ; https://arxiv.org/abs/1702.08734 ; https://arxiv.org/abs/2401.08281
- https://arxiv.org/abs/2006.11632 (Facebook EBR)
- https://github.com/twitter/the-algorithm/blob/main/ann/src/main/scala/com/twitter/ann/experimental/Runner.scala
