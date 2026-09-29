# How retrieval model papers evaluate: BM25, SPLADE, DPR, ColBERT/PLAID, cross-encoders, LLM rerankers, HyDE/query2doc

- **Kind:** paper cluster (focus on evaluation protocol, not model internals)
- **Links:** see Sources
- **Authors / org, date:** 2016–2023
- **Status:** all are open source with public checkpoints or code (details per link).

## What it is

This note surveys the evaluation protocol that each major retrieval method family used: its datasets, metrics and efficiency reporting. The aim is to align a Lean benchmark with conventions that outside readers will recognise. Model internals get one line each.

## Evaluation protocols by family

- **BM25 / Lucene / Elasticsearch.** This is the universal baseline. Lucene switched its default similarity from TF-IDF to BM25 in 6.0, and Elasticsearch followed in 5.0 ([Elastic blog](https://www.elastic.co/blog/found-bm-vs-lucene-default-similarity); [Lucene 6.0 BM25Similarity](https://lucene.apache.org/core/6_0_0/core/org/apache/lucene/search/similarities/BM25Similarity.html); version claims via search summary). Pyserini provides reproducible BM25 runs with pre-built indexes and regression tests ([arXiv:2102.10073](https://arxiv.org/abs/2102.10073)). DPR's baseline was specifically "a strong Lucene-BM25 system" ([arXiv:2004.04906](https://arxiv.org/abs/2004.04906)).
- **DPR (dense bi-encoder).** Evaluated on open-domain QA by **top-k retrieval accuracy**: it beat BM25 "by 9%-19% absolute in terms of top-20 passage retrieval accuracy" ([arXiv:2004.04906](https://arxiv.org/abs/2004.04906)).
- **ColBERT (late interaction).**
  - Reports MRR@10 on the MS MARCO dev set against **mean query latency** (log scale) on a V100 GPU. The headline figure plots the effectiveness–latency frontier.
  - Evaluated in two modes: re-ranking the official top-1000 and end-to-end retrieval.
  - Claims to be "two orders-of-magnitude faster" with "four orders-of-magnitude fewer FLOPs per query" than BERT rerankers ([arXiv:2004.12832](https://arxiv.org/abs/2004.12832)).
- **ColBERTv2.** Reports quality in-domain and out-of-domain together with **index space footprint**, which it reduces 6–10× ([arXiv:2112.01488](https://arxiv.org/abs/2112.01488)).
- **PLAID.** Reports latency speedups "up to 7× on a GPU and 45× on a CPU against vanilla ColBERTv2" at unchanged quality. Latency is reported separately for GPU and CPU, at corpus scales up to 140M passages ([arXiv:2205.09707](https://arxiv.org/abs/2205.09707)).
- **SPLADE (learned sparse).** Reports MRR@10, NDCG@10 and Recall@1000 on MS MARCO dev and TREC DL 2019. Efficiency is measured with **FLOPS**, the expected number of floating-point operations per query–document pair implied by posting-list sparsity, and the paper sweeps the regulariser to trace effectiveness against FLOPS ([arXiv:2107.05720](https://arxiv.org/abs/2107.05720)). SPLADE v2 adds BEIR results and reports "more than 9% gains on NDCG@10 on TREC DL 2019" ([arXiv:2109.10086](https://arxiv.org/abs/2109.10086)). SPLADE++ studies in-domain and zero-shot results together with efficiency ([arXiv:2205.04733](https://arxiv.org/abs/2205.04733)).
- **Cross-encoder rerankers.**
  - monoBERT was "top entry" on the MS MARCO passage leaderboard, +27% relative MRR@10 ([arXiv:1901.04085](https://arxiv.org/abs/1901.04085)).
  - monoT5 adds zero-shot transfer to TREC 2004 Robust, and a **data-poor regime** comparison ([arXiv:2003.06713](https://arxiv.org/abs/2003.06713)).
  - The Lin, Nogueira & Yates survey frames the whole area as an effectiveness/efficiency trade-off ([arXiv:2010.06467](https://arxiv.org/abs/2010.06467)).
- **LLM rerankers.**
  - RankGPT evaluates on TREC DL and BEIR, plus NovelEval for contamination ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)).
  - RankZephyr additionally tests robustness to "variations in initial document ordering and the number of documents reranked" ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)).
  - RankLLaMA/RepLLaMA evaluate on MS MARCO passage and document ranking and BEIR zero-shot ([arXiv:2310.08319](https://arxiv.org/abs/2310.08319)).
- **Query expansion with LLMs.**
  - HyDE is evaluated fully zero-shot, with no relevance labels, against Contriever and fine-tuned retrievers across web search, QA, fact verification and multiple languages ([arXiv:2212.10496](https://arxiv.org/abs/2212.10496)).
  - query2doc reports BM25 gains of 3–15% on MS MARCO and TREC DL "without any model fine-tuning" ([arXiv:2303.07678](https://arxiv.org/abs/2303.07678)).
  - Both add an LLM call per query, but neither abstract reports that cost (unverified whether the bodies do).

## Relevance to lean-explore-bench

- **Report efficiency alongside effectiveness.** Include latency (p50/p95, stating CPU or GPU and the batch size), index size and, where relevant, per-query LLM calls or cost. Show them as an effectiveness–efficiency plot, as ColBERT, SPLADE and PLAID do.
- **Evaluate rerankers with ColBERT's two modes.** Test both "rerank a fixed top-k" and "end-to-end", and vary the rerank depth and the initial ordering, as RankZephyr does.
- **Handle contamination.** For LLM-based engines and rerankers, include a post-cutoff query set, in the manner of NovelEval.
- **Query-expansion engines.** Engines that use HyDE-style expansion (for example, informalising a Lean goal before embedding) must be benchmarked with the expansion LLM fixed and its cost reported.

## Open questions

- Does any Lean engine publish a latency or cost number we can reproduce? This is not covered here and belongs to the Lean-engine notes.

## Sources

- https://arxiv.org/abs/2004.04906 (DPR), https://arxiv.org/abs/2004.12832 (ColBERT), https://arxiv.org/abs/2112.01488 (ColBERTv2), https://arxiv.org/abs/2205.09707 (PLAID)
- https://arxiv.org/abs/2107.05720, https://arxiv.org/abs/2109.10086, https://arxiv.org/abs/2205.04733 (SPLADE family)
- https://arxiv.org/abs/1901.04085 (monoBERT), https://arxiv.org/abs/2003.06713 (monoT5), https://arxiv.org/abs/2010.06467 (survey)
- https://arxiv.org/abs/2304.09542 (RankGPT), https://arxiv.org/abs/2312.02724 (RankZephyr), https://arxiv.org/abs/2310.08319 (RankLLaMA)
- https://arxiv.org/abs/2212.10496 (HyDE), https://arxiv.org/abs/2303.07678 (query2doc)
- https://arxiv.org/abs/2102.10073 (Pyserini); https://www.elastic.co/blog/found-bm-vs-lucene-default-similarity
