# Metrics for the first-stage (embedding) retriever: Recall@K as a ceiling, nDCG@10, MRR@10

- **Kind:** methodology note
- **Links:** BEIR [arXiv:2104.08663](https://arxiv.org/abs/2104.08663); DPR [arXiv:2004.04906](https://arxiv.org/abs/2004.04906); Drowning in Documents [arXiv:2411.11767](https://arxiv.org/abs/2411.11767); Qwen3 Embedding [arXiv:2506.05176](https://arxiv.org/abs/2506.05176); BRIGHT [arXiv:2407.12883](https://arxiv.org/abs/2407.12883); LitSearch [arXiv:2407.18940](https://arxiv.org/abs/2407.18940); LIMIT [arXiv:2508.21038](https://arxiv.org/abs/2508.21038); InstructIR [arXiv:2402.14334](https://arxiv.org/abs/2402.14334)
- **Authors / org, date:** various, 2020–2026
- **Status:** General metric definitions and significance testing are in [../ir-evaluation/offline-metrics-and-significance-testing.md](../ir-evaluation/offline-metrics-and-significance-testing.md), and capped recall is in [beir.md](beir.md). This note is only about **which metric answers which question for an embedding stage inside a multi-stage engine**.

## What it is

An embedding model in a search engine has one of two jobs, and each job calls for a different metric:

1. **Final ranker** (no reranker, or a user who sees its top-10): measure the top of the list with **nDCG@10**, or **MRR@10** for known-item queries.
2. **Candidate generator** for a reranker, fusion step or LLM filter: measure whether the right items are anywhere in the top K it passes on, with **Recall@K**, where K is the downstream stage's input depth.

MTEB and BEIR report nDCG@10 as the headline for every model. That answers question 1 even when the model is deployed for job 2.

## How it works

### Recall@K at the reranker's depth: necessary, not sufficient

- **The standard two-stage protocol freezes the candidate list.** Qwen3 evaluates all of its rerankers on "the retrieval top-100 results" of one embedder ([Qwen3 Table 3](https://arxiv.org/abs/2506.05176)). The reranker cannot recover a relevant item outside those 100, so first-stage Recall@100 is an upper bound on what any reranker can find.
- **DPR reported "top-20 passage retrieval accuracy"**, the share of questions with an answer-bearing passage in the top 20, because a reader consumes those 20 ([DPR abstract](https://arxiv.org/abs/2004.04906)). This is the same idea for a known-answer setting.
- **Deeper K does not automatically help.** "Drowning in Documents" measures Recall@10 after reranking the top-K for K up to more than 5,000. It finds that rerankers "provide initial improvements when scoring progressively more documents, but their effectiveness gradually declines and can even degrade quality beyond a certain limit". It classifies each (dataset, retriever, reranker) run as "Never Hurts / Distracted / Scaling is Best / Scaling Hurts" ([arXiv:2411.11767](https://arxiv.org/abs/2411.11767)). Its method is to plot first-stage Recall@10 as a dashed line against reranked Recall@10 as a function of K. The implications:
  - Report first-stage Recall@K at **several K values** (for example 10, 25, 50, 100, 1000), not only at the production depth.
  - Report the **end-to-end metric as a function of K**, because the best first stage for a given reranker depends on K.
- **Recall@K treats every relevant item as equal.** For graded relevance, NCG@K or nDCG at depth K is the graded analogue (see [../ir-evaluation/offline-metrics-and-significance-testing.md](../ir-evaluation/offline-metrics-and-significance-testing.md)).

### Matching the metric to the number of relevant items and the corpus size

- **When few items are relevant or the corpus is small, nDCG@10 gets noisy.** In BRIGHT's long-document setting, "most datasets contain only a few hundred documents", so "nDCG@10 ... becomes more susceptible to randomness", and the authors switched to **recall@1** ([BRIGHT, long-document analysis](https://arxiv.org/abs/2407.12883)).
- **LitSearch splits queries by specificity and uses a different cutoff for each.** It reports "recall@20 (R@20) for broad questions and recall@5 and @20 (R@5, R@20) for specific questions", where specificity is an annotation from the manual filtering stage ([LitSearch Table 3 caption](https://arxiv.org/abs/2407.18940)). This fits Lean well: "the lemma named X" is a specific, known-item query, while "lemmas about compactness in metric spaces" is broad.
- **When every query has several required items, a set-style recall is needed.** LIMIT gives each query exactly two relevant documents and reports recall@2/10/100. It finds that models "struggle to reach even 20% recall@100" on a 50k-document corpus ([LIMIT, results on the LIMIT dataset](https://arxiv.org/abs/2508.21038)). The Lean premise benchmarks use group recall and Covered@k for the same reason: all premises must be retrieved ([../lean-benchmarks/mathlibmpr.md](../lean-benchmarks/mathlibmpr.md)).

### MRR@10 vs nDCG@10

- **MRR@10 fits queries with one correct answer.** It only looks at the first relevant hit, which is exactly the known-item case such as "find `Finset.sum_comm`". MS MARCO's official metric is MRR@10 ([../ir-evaluation/msmarco-trecdl-beir-benchmarks.md](../ir-evaluation/msmarco-trecdl-beir-benchmarks.md)).
- **With one relevant item and binary labels, MRR and nDCG measure the same thing on different scales.** nDCG@10 is then 1/log2(rank+1) and MRR@10 is 1/rank. Both are monotone in the rank of the single hit, but they discount differently. Choose one and say why.
- **nDCG@10 is needed when there are graded labels or several acceptable answers**, which is the normal Mathlib case: an exact lemma plus acceptable `_left` / `'` / generalized variants. BEIR's reasons for choosing nDCG@10 are in [beir.md](beir.md).

### Worst-case and paraphrase metrics

- **InstructIR's Robustness@k** groups instances that share a query but differ in instruction, takes "the minimum nDCG@k score within each group", and averages these minima ([InstructIR, metric definition](https://arxiv.org/abs/2402.14334)).
- **Applied to Lean**, the same construction over *paraphrase groups* rewards engines that find the lemma however it is asked: informal, symbolic, name-fragment, or Loogle-style phrasing. More in [critiques-and-robustness.md](critiques-and-robustness.md).

### Two meanings of "recall"

ANN benchmarks report **k-NN recall**: the share of the exact top-k nearest neighbours that an approximate index returns ([ANN-Benchmarks](https://arxiv.org/abs/1807.05614)). This is not relevance recall. A study must say which one it means. Index error is covered in [efficiency-tradeoffs.md](efficiency-tradeoffs.md).

## Evaluation (known issues)

- **Headline tables rarely show the candidate-generation view.** MTEB-style leaderboards rank embedders by nDCG@10, while deployed Lean engines rerank a small candidate set: LeanExplore top-25 ([beir.md](beir.md)), LeanSearch v2 top-50 ([../lean-engines/leansearch.md](../lean-engines/leansearch.md)). A model can be worse at @10 and better at @50.
- **Hosted APIs cap depth.** Legendre marks metrics above k = 50 as undefined for LeanSearch v2 because its API returns at most 50 hits ([../lean-benchmarks/legendre-leaderboard.md](../lean-benchmarks/legendre-leaderboard.md)). Deep Recall@K is only measurable for systems we run locally.
- **Unjudged documents deflate deep recall more than nDCG@10.** The deeper K goes, the more likely a retrieved item was never judged ([beir.md](beir.md) on Hole@k).

## Relevance to lean-explore-bench

For the **embedding stage** of each engine, and for standalone embedders:

1. **Primary metrics per query type.**
   - Known-item and name queries: MRR@10 and Recall@1/5.
   - Topical and conceptual queries with graded labels: nDCG@10.
   - Premise or "all of these" queries: set or group recall.
2. **Candidate-generation curve.** Report Recall@K for K ∈ {1, 5, 10, 25, 50, 100, 1000} (capped recall when relevant items exceed K). Mark each engine's actual reranker depth (25 for LeanExplore, 50 for LeanSearch v2).
3. **End-to-end vs K.** For engines with a reranker we can run locally, sweep K and plot final nDCG@10 against K, with the first-stage curve on the same plot, as "Drowning in Documents" does.
4. **Robustness.** Collect a paraphrase group (at least 3 phrasings) for a subset of targets and report min-over-group nDCG@10 (Robustness@10) next to the mean.
5. **Report the hit-rank distribution**, not just means. The share of queries with no relevant item in the top 1000 is the hard floor that no later stage can fix.

## Open questions

- Should the published headline be end-to-end nDCG@10 (a user-facing number), with first-stage Recall@K as a diagnostic, or should the two be separate tracks with separate leaderboards?
- What K should an embedder-only track use when no reranker is assumed? Candidates are 50, a common Lean reranker depth, and 100, the MTEB/Qwen3 convention.

## Sources

- BEIR: https://arxiv.org/abs/2104.08663
- DPR (top-20 retrieval accuracy): https://arxiv.org/abs/2004.04906
- Drowning in Documents: https://arxiv.org/abs/2411.11767 (LaTeX: scaling analysis, Recall@10 figures, classification of runs)
- Qwen3 Embedding reranker protocol: https://arxiv.org/abs/2506.05176 (Table 3 caption)
- BRIGHT long-document recall@1 rationale: https://arxiv.org/abs/2407.12883 (texts/analysis.tex)
- LitSearch broad/specific cutoffs: https://arxiv.org/abs/2407.18940 (results table caption)
- LIMIT: https://arxiv.org/abs/2508.21038
- InstructIR Robustness@k: https://arxiv.org/abs/2402.14334 (Source/4_instructIR.tex)
- ANN-Benchmarks: https://arxiv.org/abs/1807.05614
