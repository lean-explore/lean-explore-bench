# BEIR (Benchmarking IR)

- **Kind:** benchmark / dataset + evaluation library (+ later an official leaderboard)
- **Links:** paper [arXiv:2104.08663](https://arxiv.org/abs/2104.08663); code [github.com/beir-cellar/beir](https://github.com/beir-cellar/beir) (originally `UKPLab/beir`); reference implementations and leaderboard paper "Resources for Brewing BEIR" [arXiv:2306.07471](https://arxiv.org/abs/2306.07471); Touché-2020 re-analysis [arXiv:2407.07790](https://arxiv.org/abs/2407.07790)
- **Authors / org, date:** Thakur, Reimers, Rücklé, Srivastava, Gurevych (UKP Lab, TU Darmstadt), Apr 2021 (NeurIPS 2021 Datasets & Benchmarks).
- **Status:** Open source (Apache-2.0). It is the retrieval core of MTEB (see [embed-mteb.md](embed-mteb.md)).

## What it is

BEIR is a zero-shot retrieval benchmark: "18 English zero-shot evaluation datasets from 9 heterogeneous retrieval tasks", including fact checking, QA, bio-medical, news, argument retrieval, duplicate question and entity retrieval. MS MARCO is reported but kept out of the zero-shot average "as the majority of the evaluated approaches are trained on" it ([arXiv:2104.08663](https://arxiv.org/abs/2104.08663), §3). Its headline finding: "BM25 is a robust baseline and re-ranking and late-interaction based models on average achieve the best zero-shot performances, however, at high computational costs" (abstract).

## How it works

- **Unified format:** `corpus.jsonl` (`_id`, `title`, `text`), `queries.jsonl`, and `qrels/{split}.tsv` (`query-id  corpus-id  score`). MTEB and CoIR use the same schema ([CoIR](https://arxiv.org/abs/2407.02883) states it "shares same data schema as other popular benchmarks like MTEB and BEIR").
- **Relevance labels** come from the source datasets. They are binary for most tasks and graded for some (TREC-COVID 3-level, TREC-NEWS 5-level, Robust04 3-level, Touché 3-level) (Table 1 of the paper). Relevant documents per query range from about 1.1 (MS MARCO) to about 70 (Robust04).
- **Metric choice, argued explicitly.** Precision and recall are "rank unaware". MRR and MAP "fail to evaluate tasks with graded relevance judgements". So BEIR uses **nDCG@10**, computed with pytrec_eval (the official TREC tool) ([arXiv:2104.08663](https://arxiv.org/abs/2104.08663), §4). Recall@100 is reported as a secondary metric for first-stage retrievers. It is *capped* recall, `|top-k ∩ relevant| / min(k, |relevant|)`, so that queries with more than k relevant documents can still reach 1.0 (App. "Capped Recall@k").
- **Systems compared by architecture:** lexical (BM25), sparse (DeepCT, SPARTA, docT5query), dense (DPR, ANCE, TAS-B, GenQ), late-interaction (ColBERT), and re-ranking (BM25 top-100 + cross-encoder).

## Evaluation (known issues)

**Pooling bias against non-lexical systems.** This is the most important lesson for us. Unjudged documents are treated as non-relevant, and many BEIR qrels were built from lexical candidate pools. BEIR measured this with **Hole@10**, the share of a system's top-10 that annotators never saw, on TREC-COVID:
- Hole@10 was 6.4% for BM25 and 2.8% for docT5query, but 14.4% for ANCE and 31.8% for TAS-B.
- The authors then judged 980 missing pairs themselves. ANCE's nDCG@10 went from 0.654 to 0.735, while docT5query barely moved (0.713 to 0.714). This happened "even though many systems contributed to the TREC-COVID annotation pool" ([arXiv:2104.08663](https://arxiv.org/abs/2104.08663), §6 and Table "Hole@10 analysis").

**Length and label noise.** A 2024 reproducibility study of Touché-2020 found "an inherent bias of neural models towards retrieving short passages" and "quite a few of the neural models' results are unjudged". Dropping passages under 20 words and adding post-hoc judgments raised neural nDCG@10 by up to 0.52, "but BM25 is still more effective" ([arXiv:2407.07790](https://arxiv.org/abs/2407.07790)). BEIR itself also noted that TAS-B prefers very short documents, such as title-only TREC-COVID entries (App. "Document Length Preference").

**Comparability.** "Brewing BEIR" identified two problems. Complex software created "barriers to entry", and there was no "single authoritative nexus for reporting". It answered with reproducible reference implementations (Pyserini) and a self-service official leaderboard ([arXiv:2306.07471](https://arxiv.org/abs/2306.07471)).

**Contamination.** BEIR test sets have been public since 2021, and many are derived from datasets whose training splits are used to train embedders. MTEB's zero-shot score was introduced to track this ([embed-mteb.md](embed-mteb.md)).

## Relevance to lean-explore-bench

- **Metrics.** Adopt nDCG@10 as the headline, with capped Recall@k at the reranker's input depth as the first-stage metric. For LeanExplore that is Recall@25, since it reranks the top 25 (`rerank_top=25` in [engine.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/engine.py)). Report MRR@10 as well for known-item queries that have one correct declaration.
- **Hole@k is a must.** Each engine we test indexes something different: names, informalizations, docstrings, types, or Loogle patterns. Relevance pools built from any subset of engines will under-credit the others. We should:
  1. pool from *every* engine under test plus BM25 plus at least one dense baseline;
  2. report Hole@10 per engine;
  3. re-judge holes (LLM-judge plus human audit) before publishing.
- **Mathlib has many near-duplicates** (`_left`/`_right`, `'` variants, `Nat`/`Int`/general versions, simp lemmas). The graded labels (exact / acceptable variant / related) and the length-bias warnings from Touché carry over directly.
- **Keep the BEIR file schema** so that off-the-shelf BEIR, MTEB, Pyserini and ranx tooling works unchanged.

## Open questions

- What is the right "unjudged" policy: treat as non-relevant (the BEIR default), or report condensed-list metrics that ignore unjudged documents (e.g. bpref or nDCG'), as in the TREC literature (unverified that BEIR tooling supports these directly)?

## Sources

- BEIR paper: https://arxiv.org/abs/2104.08663 (details from arXiv LaTeX source: §3–4, §6 hole analysis, capped recall and length appendices)
- Resources for Brewing BEIR: https://arxiv.org/abs/2306.07471
- Touché-2020 systematic evaluation: https://arxiv.org/abs/2407.07790
- CoIR (schema compatibility statement): https://arxiv.org/abs/2407.02883
- LeanExplore engine defaults: https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/engine.py (read locally at commit 17b9d6c)
