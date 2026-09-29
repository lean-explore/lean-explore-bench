# Offline ranking metrics and significance testing for IR

- **Kind:** evaluation methodology (cluster)
- **Links:** see Sources
- **Authors / org, date:** various, 2002–2026
- **Status:** standard practice. The Wilcoxon test is being actively re-examined (SIGIR 2026).

## What it is

This note covers the metrics used to score ranked lists against qrels, the tools that compute them, and how differences between systems are tested for significance.

## Metrics and when benchmarks use them

- **nDCG@k.** Graded, rank-discounted gain normalised by the ideal ordering (Järvelin & Kekäläinen, TOIS 2002, doi:10.1145/582415.582418).
  - BEIR uses **nDCG@10** everywhere. Its reasoning: precision and recall are rank-unaware, and "binary rank-aware metrics such as MRR ... and MAP ... fail to evaluate tasks with graded relevance judgements" ([BEIR §3.3](https://arxiv.org/abs/2104.08663)).
  - TREC DL's headline metric is also NDCG@10, "since it makes use of our 4-level judgments and focuses on the first results that users will see" ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)).
- **MRR@10.** This was the MS MARCO leaderboard metric because labels are sparse, typically one relevant passage per query ([arXiv:2109.00062](https://arxiv.org/abs/2109.00062)). ColBERT and SPLADE report MRR@10 on MS MARCO dev ([ColBERT](https://arxiv.org/abs/2004.12832), [SPLADE](https://arxiv.org/abs/2107.05720)).
- **Recall@k and NCG@k at depth.** These measure a first stage's ceiling.
  - SPLADE reports Recall@1000.
  - TREC DL reports NCG@100/1000 for full-ranking runs, noting that NCG "correlates strongly" with recall.
  - TREC DL also observed that higher NCG did not translate into much higher NDCG@10: the best "fullrank" document run was only 0.9% above the best rerank run ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)).
  - Bruch et al. evaluate fusion with Recall@1000 and NDCG@1000 so that the whole candidate list is assessed ([arXiv:2210.11934](https://arxiv.org/abs/2210.11934)).
- **Capped recall@k.** BEIR defines this variant for queries with more relevant documents than k ([BEIR appendix G](https://arxiv.org/abs/2104.08663)).
- **Top-k accuracy.** DPR reports "top-20 passage retrieval accuracy" for QA, the fraction of queries with at least one answer-bearing passage in the top k ([arXiv:2004.04906](https://arxiv.org/abs/2004.04906)). This is effectively Success@k.
- **Criticism of the metrics themselves.** Fuhr (SIGIR Forum 2017) lists common mistakes:
  - MRR and ERR "violate basic requirements for a metric", and MAP rests on unrealistic assumptions.
  - Relative improvements of means are inappropriate.
  - Significance tests often ignore multiple comparisons, and effect sizes are ignored.
  - Hypotheses are often formulated after the experiment.

  See the summary of [Fuhr 2017](https://dl.acm.org/doi/10.1145/3190580.3190586) and [Sakai's response](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf).

## Significance testing

- **Smucker, Allan & Carterette (CIKM 2007).** Over TREC 3 and 5–8 runs they found "little practical difference between the randomization, bootstrap, and t tests". The Wilcoxon and sign tests "have a poor ability to detect significance and have the potential to lead to false detections ... their use should be discontinued" ([PDF](https://maroo.cs.umass.edu/getpdf.php?id=744)).
- **Parapar et al. (JASIST 2019).** Using simulated score distributions, they reached a *contrary* result: sign and Wilcoxon tests had more power with good type-I behaviour ([arXiv:1901.10696](https://arxiv.org/abs/1901.10696)).
- **Urbano (SIGIR 2026).** Argues that Wilcoxon "easily loses control of its Type I error rate in IR settings" and should be abandoned ([arXiv:2604.25349](https://arxiv.org/abs/2604.25349)).
- **In practice.** Paired two-tailed t-tests are what recent IR papers report. Bruch et al., for example, use them for fusion comparisons ([arXiv:2210.11934](https://arxiv.org/abs/2210.11934)).

## Tooling

- **trec_eval.** BEIR computes metrics through "the Python interface of the official TREC evaluation tool" ([BEIR](https://arxiv.org/abs/2104.08663)).
- **ir-measures** (MacAvaney et al., ECIR 2022). A single interface over several evaluation back-ends ([arXiv:2111.13466](https://arxiv.org/abs/2111.13466)).
- **Pyserini.** Ships qrels, prebuilt indexes and evaluation scripts, and emphasises replicability through automated regression testing ([arXiv:2102.10073](https://arxiv.org/abs/2102.10073)).

## Relevance to lean-explore-bench

- **Primary metric.** Use nDCG@10 on graded judgments. Report Recall@k at the candidate depth (for example @50/@100) as a separate diagnostic, and MRR@10 or Success@k only for known-item sub-tasks with a single gold declaration.
- **Significance.** Use paired randomization (permutation) or t-tests, with bootstrap confidence intervals per engine. Correct for multiple comparisons when comparing many engines (Holm or Bonferroni). Report effect sizes and absolute differences, not only relative improvements, per Fuhr.
- **Tooling.** Compute metrics with trec_eval or ir-measures rather than a hand-rolled implementation. Store runs in TREC run format so outside parties can reproduce them.
- **Pre-registration.** Freeze the query set and the primary metric before running engines, to avoid post-hoc hypotheses (Fuhr).
- **Per-query results.** Publish per-query scores. Lean query types (name lookup, natural-language concept, type-signature pattern) will likely behave differently, and averages hide that.

## Open questions

- How many queries are needed for adequate statistical power at the effect sizes we expect between Lean engines? A power analysis on pilot data is needed.

## Sources

- nDCG: Järvelin & Kekäläinen, "Cumulated gain-based evaluation of IR techniques", TOIS 2002, https://doi.org/10.1145/582415.582418
- BEIR: https://arxiv.org/abs/2104.08663 ; TREC DL 2019: https://arxiv.org/abs/2003.07820 ; shallow pooling: https://arxiv.org/abs/2109.00062
- ColBERT: https://arxiv.org/abs/2004.12832 ; SPLADE: https://arxiv.org/abs/2107.05720 ; DPR: https://arxiv.org/abs/2004.04906 ; fusion: https://arxiv.org/abs/2210.11934
- Fuhr 2017: https://dl.acm.org/doi/10.1145/3190580.3190586 (claims via search-result summary)
- Smucker et al. 2007: https://maroo.cs.umass.edu/getpdf.php?id=744 ; Parapar et al.: https://arxiv.org/abs/1901.10696 ; Urbano 2026: https://arxiv.org/abs/2604.25349
- ir-measures: https://arxiv.org/abs/2111.13466 ; Pyserini: https://arxiv.org/abs/2102.10073
