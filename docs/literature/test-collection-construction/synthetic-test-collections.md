# Synthetic test collections: LLM-written queries and LLM labels (Rahmani et al. SIGIR 2024, SynDL, and the bias evidence)

- **Kind:** paper (evaluation methodology) + benchmark / dataset
- **Links:**
  - Rahmani, Craswell, Yilmaz, Mitra, Campos, "Synthetic Test Collections for Retrieval Evaluation", SIGIR 2024 short paper: [arXiv:2405.07767](https://arxiv.org/abs/2405.07767), code/data [github.com/rahmanidashti/SyntheticTestCollections](https://github.com/rahmanidashti/SyntheticTestCollections)
  - Rahmani, Wang, Yilmaz, Craswell, Mitra, Thomas, "SynDL: A Large-Scale Synthetic Test Collection for Passage Retrieval", WWW 2025 resource paper: [arXiv:2408.16312](https://arxiv.org/abs/2408.16312), [project page](https://rahmanidashti.github.io/SynDL/)
  - Balog, Metzler, Qin, "Rankers, Judges, and Assistants", SIGIR 2025: [arXiv:2503.19092](https://arxiv.org/abs/2503.19092)
  - Dai et al., "Neural Retrievers are Biased Towards LLM-Generated Content", KDD 2024: [arXiv:2310.20501](https://arxiv.org/abs/2310.20501)
- **Authors / org, date:** UCL, Microsoft, Snowflake (2024); Google (Balog et al., 2025); Renmin Univ. et al. (Dai et al., 2023–24)
- **Status:** SynDL queries, qrels and baseline runs are public via the project page. The SIGIR 2024 queries are part of the official TREC DL 2023 collection.

**Scope.** This note covers *fully* synthetic collections (LLM queries + LLM labels) and the bias checks run on them. Related material lives elsewhere and is not repeated:
- LLM judges on human queries (UMBRELA, Thomas et al., Clarke & Dietz, κ vs τ): [../statistics/judgment-reliability-and-llm-assessors.md](../statistics/judgment-reliability-and-llm-assessors.md)
- AIR-Bench's generated queries/labels and its Spearman-vs-MS-MARCO validation: [../embedding-evaluation/critiques-and-robustness.md](../embedding-evaluation/critiques-and-robustness.md)
- Query generators used for training (InPars, Promptagator, GPL) and query simulation: [synthetic-query-generation-and-simulation.md](synthetic-query-generation-and-simulation.md)
- How many human labels are needed to validate: [synthetic-validation-budget-and-protocol.md](synthetic-validation-budget-and-protocol.md)

## What it is

Two papers from the same group ask whether a test collection can be built with *no* human queries and *no* human relevance labels, and still rank systems the way a human collection does.

1. **Synthetic Test Collections (SIGIR 2024)** is the controlled experiment. Synthetic queries were placed inside TREC DL 2023, so the same 31 submitted systems were run on both real and synthetic queries and both were judged by NIST ([arXiv:2405.07767](https://arxiv.org/abs/2405.07767) §2.1).
2. **SynDL (WWW 2025)** is the scaled-up resource: all 1,988 "initial" TREC DL 2019–2023 queries, judged by GPT-4 over depth-10 pools of past TREC runs ([arXiv:2408.16312](https://arxiv.org/abs/2408.16312) §3).

## How it works

### SIGIR 2024: query generation
- **Seed passages.** 1,000 random MS MARCO v2 passages. A GPT-4 prompt scored query-independent "passage quality"; malformed outputs dropped 8.9% and a score < 50 dropped 14.6%. The filter targets passages that make no sense out of context, e.g. an unnamed "she" ([§2.1](https://arxiv.org/abs/2405.07767)).
- **Generators.** One query per passage from (a) the BEIR T5 query generator trained on MS MARCO and (b) zero-shot GPT-4.
- **Human query filter (important).** Professional assessors removed queries that "did not look reasonable" or had too few or too many relevant documents: **13 of 48 T5 queries and 18 of 49 GPT-4 queries were kept** ([§2.1](https://arxiv.org/abs/2405.07767)). So roughly two thirds of generated queries were discarded by humans before use. The "fully synthetic" collection is synthetic *after* human curation.
- **Query shape.** GPT-4 queries averaged 10.72 words vs 5.76 for real queries and 5.69 for T5 (Table 1). Synthetic queries had fewer relevant documents: 71.76 (T5) and 77.87 (GPT-4) with grade > 0, vs 120.1 for real queries (Table 2).

### SIGIR 2024: labels
- **Sparse labels.** Treating only the seed passage as relevant (the usual "one generated query, one gold" design) gave Kendall's τ = **0.157** against the human-query/human-label system ranking ([§2.2, Fig. 2a](https://arxiv.org/abs/2405.07767)).
- **LLM labels.** GPT-4 with the Thomas et al. prompt, temperature 0, re-labelled the pooled documents. Cohen's κ against NIST on the 4-point scale was 0.24 (real queries) and 0.26 (synthetic queries) (Table 3). GPT-4 under-assigned "perfectly relevant": it matched humans on only 28% of those.

### SynDL
- **Queries.** 1,988 queries = all initial queries from DL 2019–2023, including the 500 synthetic DL-23 queries (250 T5, 250 GPT-4) ([§3](https://arxiv.org/abs/2408.16312)).
- **Pools.** Depth-10 pools from 37 / 59 / 63 / 100 / 35 TREC runs (DL-19 … DL-23), giving 637,063 query–passage pairs, about 320 per query (Table 1).
- **Labels.** GPT-4, 4-grade scale. The authors note GPT-4 gave roughly equal numbers of "highly" and "perfectly" relevant labels, whereas humans were more sparing with "perfectly relevant" (§3).

## Evaluation

| Collection vs. human reference | Systems | Metric | Kendall's τ | Source |
|---|---|---|---|---|
| Synthetic queries, **human** labels vs real queries, human labels | 31 DL-23 runs | nDCG@10 | 0.8151 | [2405.07767 §2.1](https://arxiv.org/abs/2405.07767) |
| Synthetic queries, **sparse** (seed-only) labels | 31 | nDCG@10 | 0.157 | [§2.2](https://arxiv.org/abs/2405.07767) |
| Synthetic queries, **GPT-4** labels (fully synthetic) | 31 | nDCG@10 | 0.8568 | [§2.2](https://arxiv.org/abs/2405.07767) |
| SynDL vs DL-19 human qrels | 37 DL-19 runs | nDCG@10 / nDCG@100 | 0.8571 / 0.8286 | [2408.16312 §4](https://arxiv.org/abs/2408.16312) |

- **SynDL top systems.** The top 5 DL-23 runs on SynDL were the top 5 on DL-23, in identical order for nDCG@10 and nDCG@100 ([§4, Table 2](https://arxiv.org/abs/2408.16312)). SynDL reports only DL-19 correlations in the paper; the other years are said to be similar and deferred to GitHub (unverified).
- **Synthetic collections are easier.** "For all system types, systems consistently achieve higher performance on synthetic test collections when compared to real queries", so synthetic collections "tend to overestimate system performance across all system types" ([2405.07767 §3](https://arxiv.org/abs/2405.07767)). Rankings can transfer while absolute scores do not. AIR-Bench saw the same pattern ([critiques-and-robustness.md](../embedding-evaluation/critiques-and-robustness.md)).

### Per-system bias check (the method worth copying)
- **Design.** Runs were tagged by the LM inside the pipeline: GPT (GPT-4/3.5), T5 (monoT5, FlanT5, RankT5), GPT+T5, or other (BM25 etc.). Each run's score on the synthetic collection was plotted against its score on the real collection, separately for GPT-4 queries and T5 queries ([§3, Fig. 3](https://arxiv.org/abs/2405.07767)).
- **Result.** "Synthetic test collections based on GPT-4 do not systematically overestimate the performance of systems based on GPT", and T5 queries showed "almost no bias" toward T5 systems. SynDL repeated the plot with GPT-4 labels and concluded "GPT-based systems do not get higher ranks" ([2408.16312 §4](https://arxiv.org/abs/2408.16312)).
- **Limits of that check.** It is visual only: no per-group residual, test or effect size is reported. It rests on one collection and 31 runs. The authors themselves say "further experiments are needed" ([2405.07767 §3](https://arxiv.org/abs/2405.07767)).

### Counter-evidence: judge bias toward LLM rankers (Balog, Metzler & Qin, SIGIR 2025)
- **Setup.** TREC DL 2019/2020 with BM25 top-100, reranked by RankT5, RG (FLAN-T5/UL2) and PRP rankers, including PRP with Gemini v1.5 Flash. Also **oracle** rankers built from the human qrels with controlled swaps. Judges: four Gemini models with the UMBRELA-style prompt. Unjudged documents were filtered out ([arXiv:2503.19092](https://arxiv.org/abs/2503.19092) §4.2).
- **Rank reversal.** On DL-19 the humans score the Perfect oracle 0.892 and PRP-Gemini-v1.5-Flash 0.747. The Gemini v1.5 Flash judge scores them 0.876 and **0.961**; the v1.5 Pro judge gives 0.864 and 0.947 (Table 1). The authors: the bias "is sufficient to completely reverse the relative ranking" of LLM rankers and oracles, and non-LLM systems are "severely underestimated" (§4.3).
- **Composition matters.** Kendall's τ vs humans was only 0.033–0.143 over "All systems" for the three usable judges, but 0.600 (DL-19) and 0.867 (DL-20) over oracles alone (Table 2). Correlation depends heavily on which systems are in the pool, which they present as evidence that correlation-based meta-evaluation can be "manipulated by the choice of systems".
- **Discrimination.** The judges missed significant human differences (RankT5 vs RG-FLAN-T5-XXL on DL-19) and invented others (PRP-FLAN-UL2 vs PRP-Gemini) (§4.3).
- **What was *not* found.** No inflation for LLM-*rewritten* documents under a same-family judge. This contradicts earlier "self-preference" findings for this setup (§4.3).
- **Guidelines.** Use one judge configuration for all systems; do not use LLM labels to fill "relevance holes" in human qrels only for some systems; use multiple LLM judges; validate on a representative human sample (§5.1).

### Source bias in the retrievers themselves (Dai et al., KDD 2024)
Neural retrievers and rerankers "tend to rank LLM-generated documents higher", which the authors call *source bias*. They attribute it to LLM text having "more focused semantics with less noise" ([arXiv:2310.20501](https://arxiv.org/abs/2310.20501), abstract). This is a separate route to circularity: the engine's *index text*, not the judge, is LLM-written.

## Relevance to lean-explore-bench

- **The headline result supports LLM collections for ranking engines, not for absolute numbers.** τ ≈ 0.82–0.86 is high but below the conventional 0.9 "equivalent rankings" threshold (and that threshold is itself contested; see [../statistics/judgment-reliability-and-llm-assessors.md](../statistics/judgment-reliability-and-llm-assessors.md)), so close pairs of systems can still swap. And every study found scores inflated on synthetic data, so report LLM-collection scores as relative rankings only.
- **Do not use "the source declaration is the only relevant item".** Seed-only labels gave τ = 0.157 on MS MARCO. Mathlib has many near-duplicates, generalizations and `simp` variants, so a query generated from declaration X usually has other acceptable answers. MathlibQR makes exactly this choice ([../lean-benchmarks/mathlibqr.md](../lean-benchmarks/mathlibqr.md)). Pool across engines and label the pool.
- **Circularity is concrete here.** LeanExplore indexes Gemini informalizations and LeanSearch v2 indexes Qwen3-32B informalizations ([../lean-engines/leanexplore.md](../lean-engines/leanexplore.md), [../lean-engines/leansearch.md](../lean-engines/leansearch.md)). Lean Finder was trained on GPT-4o synthetic queries, and its synthetic test set comes from the same pipeline ([../lean-benchmarks/lean-finder-eval.md](../lean-benchmarks/lean-finder-eval.md)). A query generator or judge from any of these families is not neutral toward that engine. Rahmani et al.'s null result covers GPT/T5 rankers on web passages. Balog et al.'s positive result covers LLM rerankers. Neither covers "the index text was written by the same LLM that wrote the query", which is the Lean case (Dai et al. is the nearest evidence).
- **Copy the per-system bias plot and turn it into a test.** Group engines by LLM family (generator family, index-text family, reranker family, none). For each engine compute score(synthetic) − score(human anchor) and compare groups. See the protocol in [synthetic-validation-budget-and-protocol.md](synthetic-validation-budget-and-protocol.md).
- **Include oracle and non-LLM systems in the validation pool.** Balog et al. show that a heterogeneous pool inflates τ and that oracles expose judge bias. BM25-over-names, doc-gen4 search, and "gold-first" oracle runs are cheap to add.
- **Expect to discard many generated queries.** TREC kept 31 of 97 after expert review. Budget for a filtering step and report its acceptance rate.

## Open questions

- Would Rahmani et al.'s "no same-model bias" result hold if the *index text* (informalizations) came from the same model as the queries? No paper tests this directly.
- Their bias check uses 31 runs and no statistic. How large a per-family residual could it miss?
- SynDL's τ uses TREC runs, whose pools were built from those same runs. How would a new engine that retrieves outside the pool be treated? (See the pooling note [../ir-evaluation/trec-pooling-and-relevance-judgments.md](../ir-evaluation/trec-pooling-and-relevance-judgments.md).)

## Sources

- Rahmani et al. 2024, SIGIR: https://arxiv.org/abs/2405.07767 (Tables 1–3, Figs. 1–3, §§2–3)
- Rahmani et al. 2025, SynDL: https://arxiv.org/abs/2408.16312 (Table 1, §§3–4); https://rahmanidashti.github.io/SynDL/
- Balog, Metzler, Qin 2025: https://arxiv.org/abs/2503.19092 (Tables 1–2, §§4.2–5.1)
- Dai et al. 2024: https://arxiv.org/abs/2310.20501 (abstract only)
- Unverified: SynDL's correlations for DL-20 to DL-23 (paper defers them to GitHub; not checked).
