# "Nothing relevant here" on the retrieval side: empty relevance sets, ranked-list truncation, and query performance prediction (QPP) evaluation

- **Kind:** evaluation methodology (paper cluster + tooling behaviour)
- **Links:**
  - trec_eval source (`m_map.c`, `m_ndcg.c`) https://github.com/usnistgov/trec_eval
  - Choppy (ranked-list truncation) https://arxiv.org/abs/2004.13012
  - Ranked list truncation for LLM re-ranking https://arxiv.org/abs/2404.18185
  - QPP for neural IR, "Are we there yet?" https://arxiv.org/abs/2302.09947
  - sMARE, Faggioli et al., Inf. Retr. J. 25(2), 2022 (cited in 2302.09947; not fetched)
  - QPP-GenRE https://arxiv.org/abs/2404.01012
  - Combining QPP predictors (reproducibility) https://arxiv.org/abs/2503.24251
  - Agent Retrieval Bench, selective track https://arxiv.org/abs/2607.24882 (main note: [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md))
- **Authors / org, date:** 2020 (Choppy, Google) to 2026 (Agent Retrieval Bench); QPP work from Padova / Naver / Amsterdam / Glasgow groups.
- **Status:** Methods papers; trec_eval is the de-facto scorer.

## What it is

Standard ranked-retrieval evaluation cannot score an engine on a query whose gold set is empty. Every ranking metric normalizes by the number of relevant items or by the ideal DCG. This note covers the three IR traditions that address "the right output is nothing":
1. How standard tooling treats empty relevance sets.
2. **Ranked-list truncation (RLT).** The system chooses how many results to return, possibly zero, and the metric penalizes non-relevant results.
3. **Query performance prediction (QPP).** A per-query score is meant to predict effectiveness without judgments. It is the natural "nothing good here" signal, and it has its own evaluation protocol.

## How it works

### 1. Empty relevance sets in standard metrics

- In trec_eval, AP is assigned only `if (rel_so_far)`, and nDCG only `if (ideal_dcg > 0.0)`. There is no else-branch ([m_map.c](https://raw.githubusercontent.com/usnistgov/trec_eval/master/m_map.c), [m_ndcg.c](https://raw.githubusercontent.com/usnistgov/trec_eval/master/m_ndcg.c)). A no-answer query therefore keeps its initialized value, which is presumably 0 (initialization not checked, unverified), for *every* system. It contributes nothing to discriminating systems and only dilutes the mean.
- Consequence: no-answer queries must be scored with a separate metric, not averaged into nDCG/MRR/Recall@k. The known-item metrics in [../statistics/metric-scales-and-correlation.md](../statistics/metric-scales-and-correlation.md) and [../ir-evaluation/offline-metrics-and-significance-testing.md](../ir-evaluation/offline-metrics-and-significance-testing.md) all assume at least one relevant item.

### 2. Ranked-list truncation: letting the engine return fewer (or zero) results

- Choppy frames the problem as "how many results to return" and trades usefulness against "the user cost of processing more results" ([arXiv 2004.13012](https://arxiv.org/abs/2004.13012), abstract).
- The key metric change: standard DCG "always increases monotonically with the length of the returned ranked list and so the optimal solution under this definition would be to not truncate at all" (§4). Choppy therefore uses a DCG in which each result gains y_i = 1 if relevant and **−1 if non-relevant** (problem setup and §4.2), alongside set F1.
- Under this penalized DCG, the optimal output for a no-answer query is the **empty list** (score 0). Any returned item scores negative. A metric that rewards abstention falls straight out of ranking evaluation.
- Evaluation was on Robust04 (250 queries, average 70 relevant each), BM25 and DRMM runs, top-300 candidates (§4.1). Every Robust04 query has relevant documents, so the empty-list case is *possible* under the metric but never *tested*.
- Meng et al. reproduce 8 RLT methods in retrieve-then-rerank pipelines (3 retrievers × 2 re-rankers, TREC DL 19/20). In that setting RLT decides how many candidates to send to an LLM re-ranker ([arXiv 2404.18185](https://arxiv.org/abs/2404.18185), abstract). This matters for us because agent tool calls pay per returned result in context tokens.

### 3. QPP: predicting "this query will go badly"

- **Classic QPP evaluation.** Compute a predictor score per query, compute the actual effectiveness per query (e.g. AP or nDCG@10 against qrels), and report the correlation across queries: Pearson's r, Kendall's τ, or Spearman's ρ ([arXiv 2302.09947](https://arxiv.org/abs/2302.09947), §3).
- **sMARE.** The criticism is that correlation "summariz[es] ... a QPP model into a single observation for each system and collection". Faggioli et al. propose the per-query scaled Absolute Rank Error, sARE(q) = |R_q^e − R_q^p| / |Q|, the rank gap between effectiveness-ordering and prediction-ordering. Its mean is sMARE (lower is better). Because it is a per-query distribution, it supports ANOVA-style analyses and failure analysis (§3).
- **Neural retrievers are harder to predict.** 19 QPP methods were tested on 7 bag-of-words and 7 BERT-based systems (DL'19, Robust'04). QPPs "perform statistically significantly worse on neural IR systems", dropping by up to 10% in passage retrieval ([arXiv 2302.09947](https://arxiv.org/abs/2302.09947), abstract). Dense-specific coherence predictors improve on this ([arXiv 2310.11405](https://arxiv.org/abs/2310.11405)).
- **LLM-judged QPP.** QPP-GenRE predicts per-item relevance with a fine-tuned open LLM and computes any IR measure from the pseudo-labels. It reports state-of-the-art QPP on TREC DL 19–22 for lexical and neural rankers ([arXiv 2404.01012](https://arxiv.org/abs/2404.01012), abstract).
- **Combining predictors.** Saha et al. re-evaluate QPP combinations with sMARE, correlations and RMSE ([arXiv 2503.24251](https://arxiv.org/abs/2503.24251), abstract).
- **Gap.** QPP is evaluated by correlation with effectiveness on queries that *have* relevant documents. A no-answer query has undefined effectiveness under AP/nDCG (see §1), so it simply falls out of standard QPP evaluation. Using QPP as an abstention signal requires the classification framing below.

### 4. Selective retrieval in coding agents (link, key lesson only)

Agent Retrieval Bench's selective track is summarized in [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md). The methodological lesson not recorded there:
- **Setup.** The no-gold items fall into two strata: 50 *natural* evidence-backed no-gold issues (resolution attributed to an upstream dependency, external service, or user error) and 32 *counterfactual wrong-repository* controls. The abstention rule is "top retrieval score < threshold". The threshold maximizes balanced accuracy under repo-grouped 5-fold CV ([arXiv 2607.24882](https://arxiv.org/abs/2607.24882), §4.5, §8.8).
- **The mixed pool flatters lexical abstention.** Pooled, abstention seems to help: selective success@20 goes from 0.461 to 0.496. But lexical abstains on all 32 counterfactual controls and on only 34% of the natural cases.
- **Natural-only, no ranker improves.** Recalibrated on natural cases only, selective success drops for every ranker: lexical 0.499→0.294, Jina 0.489→0.334, BM25 0.463→0.220. Jina abstains on 94.0% of no-gold cases but passes only 37.7% of positives (§8.8).
- **Authors' conclusion.** Raw top scores "are not sufficient repository-independent abstention signals", and easy controls "must not be pooled into the primary natural-abstention claim".

## Evaluation

Protocol summary, for reuse:

| Question | Metric | Source |
|---|---|---|
| Does the engine return nothing, or only low-confidence items, when nothing exists? | Abstention recall/precision, or hallucination rate FP/(FP+TN) | [NoMIRACL](https://arxiv.org/abs/2312.11361); see [no-answer-qa-rag-abstention.md](no-answer-qa-rag-abstention.md) |
| Does it pay a price for padding results? | Penalized DCG (non-relevant gain −1), set F1 | [Choppy §4.2](https://arxiv.org/abs/2004.13012) |
| Does its confidence rank queries by how well it will do? | Pearson/Kendall/Spearman vs per-query nDCG; sMARE | [2302.09947 §3](https://arxiv.org/abs/2302.09947) |
| Does its confidence separate answerable from unanswerable? | AUROC of the confidence score (answerable = positive); risk–coverage AUC; coverage at fixed risk | [Kamath et al.](https://arxiv.org/abs/2006.09462) for risk–coverage. AUROC is the standard binary-classifier summary and is our proposal here; I did not find it used in the papers above (unverified) |
| Is the abstention result an artifact of easy negatives? | Report no-answer strata separately | [Agent Retrieval Bench §8.8](https://arxiv.org/abs/2607.24882) |

## Relevance to lean-explore-bench

- **Keep no-answer queries out of the nDCG/MRR mean.** Otherwise they add a constant 0 to every engine. Report them on a separate track.
- **Penalized DCG / F1 is a drop-in "padding cost" metric.** Rescore each engine's top-k with gain −1 per non-relevant result, which lets the engine truncate to 0. On answerable queries this measures precision of the returned set. On no-answer queries the best achievable score is 0, reached by returning nothing.
- **Most Lean engines cannot abstain today.** They always return k results. The fair protocol is to let each engine expose a confidence (its top score, or an engine-provided threshold like LeanExplore's 0.525 similarity cutoff, [../lean-engines/leanexplore.md](../lean-engines/leanexplore.md)) and evaluate the *confidence* by AUROC and risk–coverage, with the threshold tuned on dev. That compares engines that never truncate with engines that do.
- **Evaluate QPP twice.**
  1. On answerable queries: correlation or sMARE with per-query nDCG@10 ("does low confidence mean bad results?").
  2. On the answerable-vs-no-answer mix: AUROC ("does low confidence mean no lemma exists?").
  These can disagree, and Agent Retrieval Bench's negative result suggests the second is much harder.
- **Stratify no-answer items by construction.** Report easy controls (off-topic, or wrong library such as a Coq-only concept) separately from hard natural cases (plausible Mathlib-style requests for results that are absent). Pooling them inflates abstention numbers, as Agent Retrieval Bench shows.

## Open questions

- Raw similarity scores from different engines are not on one scale. Should we compare engines by AUROC (scale-free) only, or also at a fixed operating point with a per-engine dev-tuned threshold?
- Is the penalized-DCG gain of −1 for a non-relevant result right for agents? The agent cost of a wrong-but-plausible lemma (a failed compile, a wasted turn, or a silent misuse) may be much larger than the benefit of a hit. The cost ratio should come from agent-level experiments.
- Standard QPP is post-retrieval on BM25-style score distributions. Hybrid Lean engines (embedding + BM25 + PageRank) may need their own predictors.

## Sources

- trec_eval `m_map.c` and `m_ndcg.c`, usnistgov/trec_eval master. https://github.com/usnistgov/trec_eval (fetched 2026-09-28; the default-zero behaviour is inferred, unverified)
- Bahri et al. "Choppy: Cut Transformer For Ranked List Truncation", SIGIR 2020. https://arxiv.org/abs/2004.13012 (problem-setup label definition, §4.1 data, §4.2 metrics)
- Meng et al. "Ranked List Truncation for Large Language Model-based Re-Ranking", SIGIR 2024. https://arxiv.org/abs/2404.18185 (abstract only)
- Faggioli et al. "Query Performance Prediction for Neural IR: Are We There Yet?", 2023. https://arxiv.org/abs/2302.09947 (§3 evaluation methodology, abstract)
- Faggioli, Zendel, Culpepper, Ferro, Scholer. "sMARE: a new paradigm to evaluate and understand query performance prediction methods", Inf. Retr. J. 25(2):94–122, 2022 (as cited in 2302.09947; not read directly)
- Vlachou, Macdonald. "On Coherence-based Predictors for Dense Query Performance Prediction", 2023. https://arxiv.org/abs/2310.11405 (abstract)
- Meng et al. "Query Performance Prediction using Relevance Judgments Generated by LLMs" (QPP-GenRE), TOIS. https://arxiv.org/abs/2404.01012 (abstract)
- Saha et al. "Combining Query Performance Predictors: A Reproducibility Study", 2025. https://arxiv.org/abs/2503.24251 (abstract)
- Agent Retrieval Bench, 2026. https://arxiv.org/abs/2607.24882 (§4.5, §8.8)
- Kamath, Jia, Liang, ACL 2020. https://arxiv.org/abs/2006.09462 (risk–coverage)
- Thakur et al. NoMIRACL. https://arxiv.org/abs/2312.11361
