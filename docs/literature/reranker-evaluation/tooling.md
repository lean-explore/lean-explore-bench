# Reranker evaluation tooling: trec_eval, ir-measures, ranx, ir_datasets, Pyserini, RankLLM, rerankers

- **Kind:** tool (cluster)
- **Links:** see Sources
- **Authors / org, date:** NIST (trec_eval); Glasgow (ir-measures, 2022); Bassani (ranx, ECIR 2022); MacAvaney et al. (ir_datasets, SIGIR 2021); Castorini (Pyserini, RankLLM); Answer.AI (rerankers, 2024)
- **Status:** all open source and maintained as of 2026-09-28 (unverified for each repo's latest commit).

## What it is

This note covers the infrastructure that the reranker literature uses to supply fixed candidates, run rerankers and score runs. The emphasis is on the behaviours that matter specifically for evaluating a *second stage*. General metric tooling is also covered in [../ir-evaluation/offline-metrics-and-significance-testing.md](../ir-evaluation/offline-metrics-and-significance-testing.md).

## Tools

- **trec_eval** ([github](https://github.com/usnistgov/trec_eval))
  - Run format: `qid iter docno rank sim run_id`. Qrels format: `qid iter docno rel`.
  - **It ignores the rank column.** The source says: "the rank field is ignored here; internally ranks will be assigned by sorting by the sim field with ties broken determinstically (using docno)" (`get_trec_results.c`). The comparator breaks ties on docno in descending lexicographic order (`form_res_rels.c`).
  - This is a trap for rerankers that output only an order, and for runs written with constant scores. Such runs are silently re-sorted by docno. The fix is to write monotone scores, for example `score = N - rank`.
  - The README recommends `trec_eval -q -c -M1000`.
- **ir_datasets** ([arXiv:2103.02280](https://arxiv.org/abs/2103.02280), [catalog](https://ir-datasets.com/))
  - Provides standard fixed candidate lists as `scoreddocs`. For MS MARCO dev these are "the top 1000 results from BM25. These are used for the 're-ranking' setting" ([msmarco-passage page](https://ir-datasets.com/msmarco-passage.html)).
  - Caveat: "The BM25 scores from scoreddocs are not available (all have a score of 0)". Scoring the scoreddocs directly as a BM25 baseline would therefore hit trec_eval's docno tie-break.
- **Pyserini** ([arXiv:2102.10073](https://arxiv.org/abs/2102.10073))
  - Produces the BM25 first-stage runs that most LLM-reranker papers start from, for example RankGPT's "top-100 passages retrieved by BM25 using pyserini" ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)).
  - Its "two-click reproduction" pages report AP, nDCG@10 and R@1K for DL19/DL20 ([2CR](https://castorini.github.io/pyserini/2cr/msmarco-v1-passage.html)). This gives each first stage's recall ceiling alongside its nDCG.
- **RankLLM** ([arXiv:2505.19284](https://arxiv.org/abs/2505.19284), [github](https://github.com/castorini/rank_llm))
  - Scope: a reranking package with "optional integration with Pyserini for retrieval and … integrated evaluation for multi-stage pipelines".
  - Defaults: "By default BM25 is used for retrieval of top 100 candidates" and "By default ndcg@10 is the eval metric". Retriever and k are configurable.
  - Also provides window-size flags, a trec_eval wrapper, 2CR pages for DL19–DL23, and prompt/response logging for nondeterminism analysis.
  - It reproduces RankGPT, LRL, RankVicuna and RankZephyr.
- **rerankers** ([arXiv:2408.17344](https://arxiv.org/abs/2408.17344), [github](https://github.com/AnswerDotAI/rerankers))
  - A unified *inference* API over cross-encoders, T5 rankers, LLM rankers and API rerankers. Swapping models is "only changing a single line of Python code".
  - Its only evaluation support is consistency notebooks on SciFact. RankGPT is excepted because it is "harder to reproduce".
  - Useful as a harness for running many rerankers on the same candidates. It is not an evaluator.
- **ir-measures** ([arXiv:2111.13466](https://arxiv.org/abs/2111.13466))
  - A common interface over pytrec_eval, gdeval, trectools, cwl_eval, the MS MARCO RR evaluator and others. It covers more than 30 measures with syntax like `nDCG@10` and `AP(rel=2)`.
  - It supports `Judged@k`, which reports the unjudged-document rate that confounds reranker comparisons ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)).
- **ranx** ([github](https://github.com/AmenRa/ranx); Bassani, ECIR 2022, doi:10.1007/978-3-030-99739-7_30)
  - Metrics have been "tested against TREC Eval for correctness".
  - `compare()` runs paired tests: Fisher randomization, Student's t (the default) or Tukey HSD. It exports LaTeX tables with significance superscripts ([compare docs](https://amenra.github.io/ranx/compare/)).
  - It includes about 25 fusion methods (RRF, CombSUM/MNZ and others) and 7 score normalisations. That is useful for rebuilding hybrid first stages such as LeanExplore's BM25+dense RRF as a controlled baseline.
  - Whether `compare()` corrects for multiple comparisons is not documented on that page (unverified).

## Relevance to lean-explore-bench

- **Formats.** Store every stage's output as a TREC run file with strictly decreasing scores. Store qrels in TREC format, graded.
- **Scoring.** Score with ir-measures (nDCG@10, R@k, RR@10, Judged@10) and test significance with ranx `compare()` or a paired randomization test. Apply a Holm correction ourselves if ranx does not.
- **Candidate lists.** Publish the frozen first-stage candidate lists as a `scoreddocs`-style artifact, so any reranker can be evaluated on identical inputs. Ideally also register the dataset with ir_datasets.
- **Harness.** Use `rerankers` or RankLLM to run off-the-shelf rerankers over our candidate lists, instead of writing per-model glue.

## Open questions

- Should lean-explore-bench register an ir_datasets entry (corpus = pinned Mathlib declarations, queries, qrels, scoreddocs per first stage)? That would make the standard tooling work unchanged.

## Sources

- trec_eval: https://github.com/usnistgov/trec_eval
- ir_datasets: https://arxiv.org/abs/2103.02280 ; https://ir-datasets.com/msmarco-passage.html
- Pyserini: https://arxiv.org/abs/2102.10073 ; https://castorini.github.io/pyserini/2cr/msmarco-v1-passage.html
- RankLLM: https://arxiv.org/abs/2505.19284 ; https://github.com/castorini/rank_llm
- rerankers: https://arxiv.org/abs/2408.17344 ; https://github.com/AnswerDotAI/rerankers
- ir-measures: https://arxiv.org/abs/2111.13466
- ranx: https://github.com/AmenRa/ranx ; https://amenra.github.io/ranx/compare/
- RankGPT: https://arxiv.org/abs/2304.09542 ; RankZephyr: https://arxiv.org/abs/2312.02724
