# Reranker evaluation: the fixed-candidate protocol, first-stage dependence and rerank depth

- **Kind:** evaluation methodology (paper cluster)
- **Links:** see Sources. Main sources:
  - Lin, Nogueira & Yates survey ([arXiv:2010.06467](https://arxiv.org/abs/2010.06467))
  - Expando-Mono-Duo ([arXiv:2101.05667](https://arxiv.org/abs/2101.05667))
  - RankVicuna ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)) and RankZephyr ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724))
  - Gao et al. LCE ([arXiv:2101.08751](https://arxiv.org/abs/2101.08751))
  - Drowning in Documents ([arXiv:2411.11767](https://arxiv.org/abs/2411.11767))
- **Authors / org, date:** 2020–2025, mostly Waterloo/Castorini, CMU and Databricks
- **Status:** the fixed-candidate protocol is standard practice. Whether reranker quality keeps improving at very large depths is disputed (see below).

## What it is

A second-stage ranker (reranker) can only reorder what the first stage gives it. The reranking literature therefore evaluates rerankers in a **controlled setting**: every reranker gets an identical, fixed candidate list per query, and only the order is scored. This note covers:

- what the protocol looks like;
- why the first stage must be held fixed;
- how results move when the first stage or the candidate depth changes;
- how papers separate the contribution of each stage.

Background on MS MARCO, TREC DL and BEIR is in [ir-msmarco-trecdl-beir-benchmarks.md](ir-msmarco-trecdl-beir-benchmarks.md), and background on metrics and significance testing is in [ir-offline-metrics-and-significance-testing.md](ir-offline-metrics-and-significance-testing.md). They are not repeated here.

## The standard protocol

- **Fixed candidate list.** TREC DL's rerank subtask gives every participant the same BM25 top-1000 ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)). ir_datasets ships these as `scoreddocs`: "the top 1000 results from BM25. These are used for the 're-ranking' setting" ([ir-datasets.com](https://ir-datasets.com/msmarco-passage.html)).
- **Typical depths.**
  - Cross-encoder papers rerank the top-1000. monoT5 in Expando-Mono-Duo uses k0 = 1000, and the pairwise duoT5 then reranks only the top k1 = 50 ([arXiv:2101.05667 §4.1](https://arxiv.org/abs/2101.05667)).
  - LLM rerankers mostly use BM25 top-100: "we re-rank the top-100 passages retrieved by BM25 using pyserini" ([RankGPT](https://arxiv.org/abs/2304.09542)). PRP and Setwise do the same ([arXiv:2306.17563](https://arxiv.org/abs/2306.17563), [arXiv:2310.09497 §4.1](https://arxiv.org/abs/2310.09497)).
- **Metrics.**
  - nDCG@10 is the headline metric on TREC DL and BEIR. MRR@10 is used on MS MARCO dev.
  - RankVicuna and RankZephyr add MAP@100 ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
  - RankGPT and PRP add nDCG@1 and nDCG@5 ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)).
- **Why this is fair.** A reranker cannot add documents, so a pipeline that reranks another pipeline's output has "the same recall, since … the latter reranks output from the former and thus cannot find any additional relevant documents" ([arXiv:2101.05667 §5.2](https://arxiv.org/abs/2101.05667)). Holding candidates fixed attributes any metric change to ordering alone.
  - Jina v3 states the principle explicitly: "consistent use of jina-embeddings-v3 retrieval candidates eliminates retrieval variance and isolates reranking effectiveness" ([arXiv:2509.25085](https://arxiv.org/abs/2509.25085)).
  - Qwen3 uses the same wording: top-100 from Qwen3-Embedding-0.6B "ensures a fair evaluation" ([arXiv:2506.05176 §5.2](https://arxiv.org/abs/2506.05176)).

## The first-stage recall ceiling

- The survey frames Recall@1000 as the ceiling of the whole pipeline. It "helps to quantify the upper bound effectiveness of the retrieve-and-rerank strategy … if first-stage retrieval fails to return relevant passages, the reranker cannot conjure relevant results out of thin air" ([arXiv:2010.06467 §3.2.2](https://arxiv.org/abs/2010.06467)).
- Expando-Mono-Duo calls R@1K "the most important metric for first-stage retrieval since it sets the effectiveness upper bound for the entire reranking pipeline" ([arXiv:2101.05667 §5.4](https://arxiv.org/abs/2101.05667)).
- **Oracle reranking** means perfectly sorting the candidate list by qrels. It yields an explicit upper-bound nDCG@10 per first stage. We did not find a text-retrieval paper that reports it as a formal baseline; papers use R@k as a proxy instead.
  - A 2026 recommender-systems preprint argues that oracle protocols which *inject* the gold item into the candidate list "overestimate realistic NDCG@10 by 92–95%". It derives a recall ceiling E[NDCG@k] ≤ Recall@|W| ([arXiv:2609.27953](https://arxiv.org/abs/2609.27953), abstract only; unverified beyond the abstract).
  - The lesson for us: never evaluate a reranker on candidate lists where gold items have been planted, unless that is explicitly labelled an oracle condition.

## Gains depend on the first stage

Reranker gains are largest over weak first stages and shrink over strong ones. A reranker must therefore be reported over more than one first stage.

- **monoT5-3B on MS MARCO passage dev (MRR@10)** ([arXiv:2101.05667 Table 1](https://arxiv.org/abs/2101.05667)). A first-stage gap of 0.093 shrinks to 0.011 after reranking.

  | First stage | Alone | + monoT5-3B |
  |---|---|---|
  | BM25 | 0.184 | 0.398 |
  | doc2query-T5 | 0.277 | 0.409 |

- **monoBERT on DL19 (nDCG@10)** ([arXiv:2010.06467](https://arxiv.org/abs/2010.06467)). Better candidates "*does* improve end-to-end effectiveness after reranking … although the magnitude of the gain is smaller."

  | First stage | Alone | + monoBERT |
  |---|---|---|
  | BM25 | 0.5058 | 0.7383 |
  | BM25+RM3 | 0.5180 | 0.7421 |

- **RankVicuna** tests 5 first stages, each at top-20 and top-100: BM25, BM25+RM3, ada2, TAS-B and SPLADE++ ED. Reranking "improves effectiveness by 30%–45%" over BM25 but "only 2%–4%" over SPLADE++ ED. With a strong first stage, "reranking only the top 20 candidates achieves an nDCG@10 score on par with reranking the top 100" ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
- **RankZephyr** finds a 45–55% gain over BM25 but 7–20% over SPLADE++ ED. It recommends "meticulously evaluating reranker models over different first-stage retrievers."
  - A candidate set with higher MAP@100 did not yield better reranked output: "Despite RepLLaMA exhibiting a higher MAP@100, reranking it does not translate to better results than reranking SPLADE++ ED" ([arXiv:2312.02724 §6.3](https://arxiv.org/abs/2312.02724)).
  - DL19 nDCG@10: BM25 0.5058 alone, 0.6489 at top-20, 0.7420 at top-100; SPLADE++ 0.7308 / 0.7780 / 0.7816; RepLLaMA 0.7384 / 0.7848 / **0.7660** (top-100 is *worse* than top-20).
- **Rerankers can get worse on better candidates.** Gao, Dai & Callan find a "popular reranker cannot fully exploit the improved retrieval result … An improved candidate list sometimes causes inferior reranking". They attribute this to a mismatch between the negatives seen in training and the candidates seen at test time. They show it with a train-retriever × test-retriever grid ([arXiv:2101.08751](https://arxiv.org/abs/2101.08751)).
  - The survey makes the same point: "increased recall in candidate generation may not translate into higher end-to-end effectiveness" because of a training/inference mismatch ([arXiv:2010.06467 §5](https://arxiv.org/abs/2010.06467)).
- **Some rerankers lose to a strong dense first stage outright.** In the Qwen3 paper, third-party rerankers score 57.03–59.51 on MTEB-R, *below* the 61.82 of the Qwen3-Embedding-0.6B first stage they rerank ([arXiv:2506.05176 Table 5](https://arxiv.org/abs/2506.05176)).

## Rerank depth: more is not always better

- **Older view: go as deep as you can afford.** For monoBERT on MS MARCO dev, going "from 1000 hits to 10000 hits increases MRR@10 from 0.372 to 0.377. Further increasing k to 50000 does not measurably change MRR@10". The survey concludes that "system designers should simply select the largest k practical" ([arXiv:2010.06467 §3.2.2](https://arxiv.org/abs/2010.06467)).
- **Contrary evidence: Drowning in Documents.** This paper reranks up to more than 5,000 candidates and, at the limit, the *whole* corpus. It uses strong dense first stages (voyage-2, text-embedding-3-large) and BM25, and scores Recall@10 as a function of K.
  - Datasets include BRIGHT, BIRCO and SciFact, plus three internally curated enterprise sets built "to avoid contamination".
  - In 53.3% (academic) and 44.4% (enterprise) of settings, reranking helped at some K but "scaling hurts": at the maximum K it ends below the retriever alone.
  - Only 3.3% / 14.8% of settings were "scaling is best".
  - A listwise LLM reranker (gpt-4o-mini, window 20, stride 10) instead "consistently improves as we scale K".
  - Source: [arXiv:2411.11767](https://arxiv.org/abs/2411.11767).
  - Caveat: the exact grid of K values was not in the LaTeX source we read (unverified).
- **Pairwise second stages** get most of their benefit at small depth: "most of the impact of pairwise reranking comes from a small value of k1" ([arXiv:2101.05667 §5.1](https://arxiv.org/abs/2101.05667)). The survey recommends spending the compute budget on a mono→duo cascade and plots cost as k0 + k1(k1−1) inferences on a Pareto frontier ([arXiv:2010.06467 §3.4.1](https://arxiv.org/abs/2010.06467)).
- **Judged-rate confound.** Deeper or different candidates bring in unjudged documents, which count as non-relevant.
  - RankZephyr notes that Judged@10 rates of 0.942 and 0.983 make its nDCG@10 "a lower bound". It partly attributes the RepLLaMA top-100 < top-20 anomaly to judged-document rates ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)).
  - Pooling is covered in [ir-trec-pooling-and-relevance-judgments.md](ir-trec-pooling-and-relevance-judgments.md).

## Separating stage contributions: the four reported views

The papers above report some combination of four views:

1. **Retrieve-only.** First-stage nDCG@10 plus R@k at the rerank depth (the ceiling).
2. **Rerank on fixed candidates.** The same candidates for every reranker, repeated for ≥2 first stages and ≥2 depths (RankVicuna and RankZephyr tables).
3. **End-to-end pipeline.** The shipped configuration, compared against other full systems. ColBERT reports both "rerank official top-1000" and end-to-end modes ([arXiv:2004.12832](https://arxiv.org/abs/2004.12832)).
4. **Full-corpus reranking.** The reranker scores every document, which isolates reranker quality from candidate recall ([arXiv:2411.11767](https://arxiv.org/abs/2411.11767)). This is feasible for small corpora.

## Relevance to lean-explore-bench

- **LeanExplore can be ablated directly.** LeanExplore v1 retrieves with BM25 on names plus FAISS over Qwen3-Embedding-0.6B, fuses with RRF, adds a dependency boost, then reranks the top 25–50 with Qwen3-Reranker-0.6B. The local backend exposes `faiss_k`, `bm25_k` and `rerank_top` ([engine-leanexplore.md](engine-leanexplore.md)). That makes views 1–3 directly measurable.
- **LeanSearch v2 already reports the retrieve-only vs rerank ablation.** On MathlibQR, nDCG@10 goes from 0.494 to 0.623 ([paper-leansearch-v2.md](paper-leansearch-v2.md)). It does *not* report the recall ceiling or how the gain varies across first stages.
- **Mathlib is small enough for view 4.** At roughly hundreds of thousands of declarations, full-corpus scoring with a 0.6B cross-encoder is feasible offline, though expensive (unverified cost; needs measurement). Drowning in Documents suggests we should check whether deeper `rerank_top` hurts.
- **Watch the depth trade-off.** LeanExplore's `rerank_top` of 25–50 is shallow. RankVicuna's finding (top-20 ≈ top-100 given a strong first stage) and Drowning's (deeper can hurt) mean the depth should be swept, not assumed.

## Open questions

- There is no public text-IR convention for reporting oracle-reranking nDCG@10. Should we define one, as "perfect sort of candidates by graded qrels"?
- Does Qwen3-Reranker, trained on general data, suffer the train/test candidate mismatch that Gao et al. describe when its candidates come from Lean-specific BM25 on names?

## Sources

- Lin, Nogueira, Yates, *Pretrained Transformers for Text Ranking*: https://arxiv.org/abs/2010.06467
- Expando-Mono-Duo: https://arxiv.org/abs/2101.05667
- RankGPT: https://arxiv.org/abs/2304.09542 ; RankVicuna: https://arxiv.org/abs/2309.15088 ; RankZephyr: https://arxiv.org/abs/2312.02724
- PRP: https://arxiv.org/abs/2306.17563 ; Setwise: https://arxiv.org/abs/2310.09497
- Gao, Dai, Callan, LCE: https://arxiv.org/abs/2101.08751
- Drowning in Documents: https://arxiv.org/abs/2411.11767
- Qwen3 Embedding: https://arxiv.org/abs/2506.05176 ; jina-reranker-v3: https://arxiv.org/abs/2509.25085
- TREC DL 2019 overview: https://arxiv.org/abs/2003.07820 ; ColBERT: https://arxiv.org/abs/2004.12832
- ir_datasets MS MARCO passage page: https://ir-datasets.com/msmarco-passage.html
- Recall-ceiling / oracle-injection preprint (abstract only): https://arxiv.org/abs/2609.27953
