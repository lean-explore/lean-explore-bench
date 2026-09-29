# Hybrid lexical + semantic fusion: RRF and convex combination, and how they were evaluated

- **Kind:** method + evaluation (paper cluster, with product docs)
- **Links:**
  - Cormack, Clarke & Büttcher, SIGIR 2009: https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
  - Bruch, Gai & Ingber (TOIS): https://arxiv.org/abs/2210.11934
  - Elasticsearch RRF: https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
  - OpenSearch normalization processor: https://docs.opensearch.org/latest/search-plugins/search-pipelines/normalization-processor/
- **Authors / org, date:** University of Waterloo and Google (2009); Pinecone (2022/23); Elastic and OpenSearch docs (current).
- **Status:** RRF is a built-in retriever in Elasticsearch. OpenSearch offers score normalisation plus combination.

## What it is

Hybrid search merges a lexical ranking (such as BM25) with a semantic ranking (dense or learned-sparse). Two families exist:

- **Reciprocal Rank Fusion (RRF):** `score(d) = Σ_q 1/(k + rank_q(d))`, which uses ranks only.
- **Convex combination (CC):** `α·norm(s_lex) + (1-α)·norm(s_sem)`, which uses normalised scores.

LeanExplore's own ranking mixes semantic, BM25+ and PageRank scores ([arXiv:2506.11085](https://arxiv.org/abs/2506.11085)), so this is directly relevant to what we will benchmark.

## Evaluation

- **Original RRF paper (2009).**
  - The constant **k = 60 "was fixed during a pilot investigation"**. Pilot results over TREC topics 351–400 showed k = 60 was "near-optimal".
  - Evaluated by MAP when fusing TREC 3, 5 and 9 ad hoc runs, TREC 2004 Robust runs, and LETOR 3 learning-to-rank baselines.
  - RRF beat Condorcet, CombMNZ and the best single system "by 4% to 5% on average", with significance established by a simple **sign test**.
  - Source: the PDF, extracted text.
- **Bruch et al.**
  - Evaluated fusion on MS MARCO passage (in-domain) plus 8 BEIR datasets (out-of-domain). Hybrid scores are computed over the **union** of both candidate sets, and quality is measured with **Recall@1000 and NDCG@1000**. They argue for deep rather than shallow metrics "to understand the performance of each system more completely", and use a cutoff of 100 for the small SciFact and NFCorpus.
  - Significance is tested with paired two-tailed t-tests.
  - Findings: RRF *is* sensitive to its parameter; CC is largely agnostic to the normalisation choice; CC beats RRF in- and out-of-domain; and CC is "sample efficient", needing only a handful of labelled queries to tune α ([arXiv:2210.11934](https://arxiv.org/abs/2210.11934)).
- **Elasticsearch.** Default `rank_constant` is 60, and `rank_window_size` defaults to `size`. The docs present RRF as needing "no tuning", with each child retriever weighted equally ([ES docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html)).
- **OpenSearch.** The normalization processor supports `min_max` (default), `l2` and `z_score` normalisation, optional per-query lower and upper score bounds, and combination techniques including `arithmetic_mean` and `geometric_mean` ([OpenSearch docs](https://docs.opensearch.org/latest/search-plugins/search-pipelines/normalization-processor/)).

## Relevance to lean-explore-bench

- **Fusion baselines.** For every hybrid engine we test, include its single-signal components as baselines (lexical-only and semantic-only) where the engine exposes them. Also include generic fusion baselines built from our own BM25 and embedding runs: RRF with k = 60, and CC with α tuned on a small **dev split**. This shows whether an engine's bespoke fusion adds anything beyond textbook fusion.
- **Dev/test split.** Bruch et al. show CC needs only a few labelled queries to tune. The benchmark should therefore ship a small dev split for tuning and a held-out test split, so tuned and untuned engines are compared fairly.
- **Evaluate at depth.** Report deep metrics (Recall@100 or NDCG@100) as well as nDCG@10, because fusion changes which candidates exist at all.
- **Reproducibility of fusion.** Fusion depends on each component's rank window, so record `rank_window_size` or candidate depth per engine in run metadata.

## Open questions

- Should PageRank-style priors be treated as a third fused ranking or as a re-scoring feature for evaluation purposes? This is design-dependent, and we have no literature answer.

## Sources

- https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf (also https://dl.acm.org/doi/10.1145/1571941.1572114)
- https://arxiv.org/abs/2210.11934
- https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
- https://docs.opensearch.org/latest/search-plugins/search-pipelines/normalization-processor/
- https://arxiv.org/abs/2506.11085 (LeanExplore hybrid ranking description)
