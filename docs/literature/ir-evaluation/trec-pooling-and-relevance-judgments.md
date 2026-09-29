# TREC-style judged relevance sets: pooling, incompleteness, sparse labels, LLM assessors

- **Kind:** evaluation methodology (cluster of papers)
- **Links:** see Sources
- **Authors / org, date:** NIST/TREC community, 1998–2026
- **Status:** active research area. TREC 2024 RAG used LLM assessment tooling (UMBRELA).

## What it is

Cranfield-style evaluation has three parts: a fixed corpus, a set of topics (queries), and relevance judgments ("qrels") for (query, document) pairs. Judging the whole corpus is infeasible, so TREC **pools** the top-k results of many participating systems and judges only the pool. This note collects what is known about when such judgments can be trusted.

## Key findings

- **Pooling misses relevant documents but mostly preserves system rankings.** Zobel (SIGIR 1998) found "the measured relative performance of systems appears to be reliable, but that recall is overestimated", and proposed a pooling strategy that finds more relevant documents ([ACM](https://dl.acm.org/doi/pdf/10.1145/290941.291014); summary via search).
- **Incomplete judgments call for robust metrics.** Buckley and Voorhees (SIGIR 2004) introduced **bpref**. It is highly correlated with standard measures when judgments are complete and is more robust when they are incomplete ([NIST PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=150469)).
- **Pools built from one family of systems penalise systems from another family.**
  - BEIR's TREC-COVID analysis measured **Hole@10**, the share of a system's top-10 hits that were never judged. It was 6.4% for BM25 and 2.8% for docT5query, versus 14.4% for ANCE and 31.8% for TAS-B.
  - After the authors judged 980 missing pairs, ANCE's nDCG@10 rose from 0.654 to 0.735, while docT5query moved only from 0.713 to 0.714.
  - The authors conclude that datasets "that use diverse pooling strategies are needed" ([BEIR, arXiv:2104.08663](https://arxiv.org/abs/2104.08663), §6 and Table 4).
- **TREC Deep Learning practice** ([TREC DL 2019 overview, arXiv:2003.07820](https://arxiv.org/abs/2003.07820)):
  - A small number of queries is judged deeply: 43 test queries per task in 2019.
  - The judging pool combined the full-retrieval and rerank subtasks, was supplemented with classifier-selected documents, and was extended for queries with many relevant documents, "to allow reliable future dataset reuse".
  - Judgments are graded on a four-point scale, where 3 means "perfectly relevant ... worthy of being a top result".
  - By contrast, the MS MARCO training labels are "sparse, with no negative labels and often only one positive label per query".
- **Sparse labels can fail to recognise real improvements.** Arabzadeh et al. had crowd workers make preference judgments between a neural stack's top result and the MS MARCO judged-relevant passage. Searchers often preferred the neural top result, which makes the ranker "better than perfect" under MRR. The authors argue that MS MARCO "may no longer be able to recognize genuine improvements" and that a single "right answer" should be the most-preferred answer, maintained with ongoing judgments ([arXiv:2109.00062](https://arxiv.org/abs/2109.00062)).
- **LLM relevance assessors.**
  - Thomas et al. (Bing) found that LLM labels had "accuracy as good as human labellers" when the prompt is tuned against first-party gold labels from real searchers. They also found that prompt paraphrases alone change accuracy ([arXiv:2309.10621](https://arxiv.org/abs/2309.10621)).
  - UMBRELA, an open-source reproduction with GPT-4o, reports that LLM-derived judgments "correlate highly" with system rankings on TREC DL 2019–2023. It was used in the TREC 2024 RAG Track ([arXiv:2406.06519](https://arxiv.org/abs/2406.06519)).
  - Counterpoint from Clarke and Dietz: a system built deliberately to exploit the LLM judge got inflated scores. If systems adopt the judge model as a reranker, the evaluation becomes circular and distorts Kendall's tau between system rankings ([arXiv:2412.17156](https://arxiv.org/abs/2412.17156)). Faggioli et al. propose a spectrum of human–machine collaboration rather than full automation ([arXiv:2304.09161](https://arxiv.org/abs/2304.09161)).

## Relevance to lean-explore-bench

- **Pool across all engines under test.** Pool LeanExplore, Loogle, Moogle/LeanSearch-style engines, BM25, pure-embedding baselines and others at a fixed depth (for example top-10 or top-20). Judge the union of the pools. Then report **Judged@k / Hole@k per engine**, so an engine that surfaces unusual but correct lemmas is not penalised. BEIR's TREC-COVID result is the cautionary example.
- **Use graded labels, not single gold answers.** A Lean query often has several acceptable declarations: the exact lemma, a more general version, an `iff` variant, or a simp-normal form. A four-level scale in the TREC DL style avoids the MS MARCO "better than perfect" problem. A single-answer set ("the declaration the user eventually used") can still be kept as a secondary *known-item* task scored with MRR.
- **Depth versus breadth.** TREC DL used 43 deeply judged queries per task, which favours reuse. For statistical power, though, many shallowly judged queries beat a few deep ones for the same judging budget (Webber, Moffat & Zobel 2008; see [../statistics/effect-sizes-power-and-topic-set-size.md](../statistics/effect-sizes-power-and-topic-set-size.md)). The statistics notes take precedence: judge many queries to depth 10–20.
- **LLM judges.** Use them to pre-screen or to extend pools. Calibrate them against a human-judged (Lean expert) subset and report agreement (for example Cohen's κ, and Kendall's τ of system rankings). Do not use the same LLM family as both a reranker under test and the judge.
- **Keep the benchmark reusable.** Version qrels, and allow re-judging of unjudged hits when new engines are added, as TREC does for reusable collections.

## Open questions

- What pool depth is affordable with Lean-expert assessors? This needs a pilot.
- Can Lean itself provide partial automatic relevance, for example "declaration X closes goal G" via `exact?`/`apply?`? That would be a Lean-specific analogue to judged relevance (idea, not from the literature).

## Sources

- Zobel 1998: https://dl.acm.org/doi/pdf/10.1145/290941.291014 (finding quoted from search-result summary)
- Buckley & Voorhees 2004: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=150469 and https://dl.acm.org/doi/10.1145/1008992.1009000
- BEIR: https://arxiv.org/abs/2104.08663
- TREC DL 2019: https://arxiv.org/abs/2003.07820 ; TREC DL 2020: https://arxiv.org/abs/2102.07662
- Shallow pooling for sparse labels: https://arxiv.org/abs/2109.00062
- Thomas et al.: https://arxiv.org/abs/2309.10621 ; UMBRELA: https://arxiv.org/abs/2406.06519
- Clarke & Dietz: https://arxiv.org/abs/2412.17156 ; Faggioli et al.: https://arxiv.org/abs/2304.09161
