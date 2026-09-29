# LLM reranker evaluation: order sensitivity, nondeterminism, cost reporting and contamination

- **Kind:** evaluation methodology (paper cluster: RankGPT, RankVicuna, RankZephyr, PRP, Setwise, permutation self-consistency, FutureQueryEval)
- **Links:** see Sources
- **Authors / org, date:** 2023–2025
- **Status:** the code for these papers is open source, mostly in [castorini/rank_llm](https://github.com/castorini/rank_llm) and [ielab/llm-rankers](https://github.com/ielab/llm-rankers).

## What it is

LLM rerankers bring evaluation concerns that cross-encoders mostly do not have:

- sensitivity to the **order** in which candidates appear in the prompt;
- **nondeterminism** even at temperature 0;
- **cost** that scales with prompts and tokens rather than with model forward passes;
- **contamination** of public benchmarks.

This note records how the main papers measured and reported each of these. It does not cover which method wins.

## Order and position sensitivity

- **RankGPT** used a sliding window of size 20, step 10, run back to front over the BM25 top-100 ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)). It found performance "highly sensitive to the initial passage order".

  | Initial order (gpt-3.5-turbo, DL19) | nDCG@10 |
  |---|---|
  | BM25 | 65.80 |
  | random | 25.17 |
  | reversed BM25 | 32.77 |

  - A window/step sweep on DL19 (20/10, 40/20, 60/30, 80/40) gave nDCG@10 of 67.05, 65.51, 65.03 and 65.57.
  - Running two or three passes raised nDCG@10 slightly but "hurts … top passages (e.g., nDCG@1 decreased by 3.88)".
- **PRP** handles order within each pair by asking both orders: "we will inquire the LLM twice by swapping their order". Inconsistent answers count as a tie ([arXiv:2306.17563](https://arxiv.org/abs/2306.17563)).
  - Its input-order table on DL19 (nDCG@10, BM25 order → inverted BM25) shows that robustness depends on the aggregation method:

    | Method | BM25 order | Inverted BM25 |
    |---|---|---|
    | PRP-Allpair | 72.42 | 72.40 |
    | PRP-Sliding-10 | 72.65 | 64.84 |
    | PRP-Sliding-1 | 57.58 | 26.04 |

- **Setwise** tests three initial orderings: BM25, inverted BM25 and randomly shuffled BM25. Listwise generation and pairwise bubblesort degrade under these, while setwise is "far more robust" ([arXiv:2310.09497 §5.4](https://arxiv.org/abs/2310.09497)).
- **RankVicuna and RankZephyr** report **six random shuffles** of the candidate list as mean ± 99% CI. DL19 nDCG@10 ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088), [arXiv:2312.02724](https://arxiv.org/abs/2312.02724)):

  | Model | BM25 order | Shuffled BM25 | SPLADE++ ED order | Shuffled SPLADE++ ED |
  |---|---|---|---|---|
  | RankZephyr | 0.7420 | 0.7378±0.009 | 0.7816 | 0.7670±0.011 |
  | RankGPT-3.5 | 0.6855 | 0.6158±0.012 | 0.7504 | 0.6028±0.007 |

  Without shuffle data augmentation, RankVicuna dropped "up to 34%".
- **Permutation self-consistency** (Tang et al.) is both a *measurement* and a *mitigation* ([arXiv:2310.07712](https://arxiv.org/abs/2310.07712)).
  - **Measurement.** It counts "reversions": pairs whose input order is flipped in the output, plotted by input position. Under no positional bias, "the distribution of reversions should be uniform". GPT-3.5 "does not focus well on items past the fifteenth".
  - **Mitigation.** It shuffles the list m = 20 times and aggregates with a Kemeny central ranking. Returns "sharply diminish after 5–10" shuffles.
  - The related "lost in the middle" effect in long contexts is documented in [arXiv:2307.03172](https://arxiv.org/abs/2307.03172).
- **Window size as a robustness axis.** RankZephyr was trained only on windows of 20. At window 10 / stride 5 only 38.74% of its outputs were well-formed ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)).

## Nondeterminism and output validity

- **Temperature 0 is not deterministic.** RankVicuna observed "non-deterministic outputs for GPT-3.5 and GPT-4, even with a temperature of zero" and reports means over 6 and 3 runs with 99% CIs ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
  - Permutation self-consistency reports the median of 3 runs with the maximum in parentheses, and significance by a one-tailed signed-rank test ([arXiv:2310.07712](https://arxiv.org/abs/2310.07712)).
- **Malformed outputs are counted.**
  - RankGPT counts repeated, missing and rejected IDs per model. For gpt-3.5-turbo on TREC these were 14, 153 and 7. Missing passages are appended "in their original order at the end" ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542) appendix).
  - RankVicuna tabulates malformed responses out of 873 requests ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
  - PRP falls back to BM25 order on conflicts and failures ([arXiv:2306.17563](https://arxiv.org/abs/2306.17563)).
  - The consequence: a failure-handling policy is part of the system under test and must be documented.
- **Tooling for this.** RankLLM includes "a module for detailed analysis of input prompts and LLM responses, addressing reliability concerns with LLM APIs and non-deterministic behavior in Mixture-of-Experts (MoE) models" ([arXiv:2505.19284](https://arxiv.org/abs/2505.19284)).

## Cost and latency reporting

- **RankGPT** is the most explicit ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542), API Cost appendix). Per query on TREC:

  | Configuration | Tokens | API calls | Cost (USD) |
  |---|---|---|---|
  | gpt-3.5-turbo | 19,960 | 10 | 0.040 |
  | gpt-4 | 19,890 | 10 | 0.596 |
  | gpt-4, top-30 only | 3,271 | 1 | 0.098 |

  - Latency is about 1.1 s per call for gpt-3.5-turbo and 3.2 s for gpt-4, giving about 11 s and 32 s per query.
  - GPT-4 on BEIR reranked only the gpt-3.5 top-30, to save money. This means the GPT-4 BEIR numbers come from a *cascade*, not a like-for-like protocol.
- **Setwise** is the reference design for efficiency reporting. It reports four quantities per query, each averaged:
  1. LLM inferences;
  2. prompt tokens;
  3. generated tokens;
  4. latency on a single stated GPU (RTX A6000), "queries are issued one at a time", with maximum batch size where supported.

  It also reports USD cost for closed models, and it traces an effectiveness–latency trade-off by sweeping the number of documents per prompt ([arXiv:2310.09497](https://arxiv.org/abs/2310.09497)).
- **PRP** gives only asymptotic call counts: O(N²) for all-pairs, O(N log N) for heapsort, O(N) per sliding pass. Each comparison is two prompts because of the order swap ([arXiv:2306.17563](https://arxiv.org/abs/2306.17563)). RankVicuna points out that PRP-Sliding-10 includes each passage in about 40 prompts on average, against 2 prompts to bring the top 10 to the top with a listwise window ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
- **Other cost figures.**
  - RankVicuna: about 30 s per query at batch size 1 on an RTX A6000 ([arXiv:2309.15088](https://arxiv.org/abs/2309.15088)).
  - Permutation self-consistency: 20 parallel calls add "no more than 25%" running time over one call, and it estimates $100–200 to reproduce its GPT results ([arXiv:2310.07712](https://arxiv.org/abs/2310.07712)).
  - FutureQueryEval: MRR against total processing time. For example, MonoT5-base takes 129.91 s, while a 1B-parameter RankGPT variant takes "over 53 minutes" ([arXiv:2508.16757 §7.1](https://arxiv.org/abs/2508.16757)).

## Contamination and novel test sets

- **NovelEval-2306** (RankGPT) ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)):
  - Queries: 21 questions from 4 domains, "published after the release of GPT-4".
  - Novelty check: questions were checked against gpt-4-0314 and gpt-4-0613, which achieved 0% QA accuracy.
  - Candidates: 20 per query from Google search (420 passages). Some were retrieved by entity alone, to add relevant-but-non-answering pages.
  - Labels: graded 0/1/2, with counts 290/40/90. Annotated by the authors and colleagues, twice.
  - The candidate order was randomly shuffled.
  - Results, nDCG@10: BM25 55.77, monoT5-3B 84.62, gpt-3.5-turbo 75.71, gpt-4 90.45.
- **RankZephyr on NovelEval** reranks the Google top-20 with no progressive passes and emphasises nDCG@1 ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)):

  | Model | nDCG@1 | nDCG@5 | nDCG@10 |
  |---|---|---|---|
  | RankZephyr | 0.9286 | 0.8615 | 0.8934 |
  | RankGPT-4 | 0.8571 | 0.8749 | 0.9045 |

  The abstract's "outperforms GPT-4" claim therefore holds only at nDCG@1.
- **FutureQueryEval** (Abdallah et al., EMNLP Findings 2025) ([arXiv:2508.16757](https://arxiv.org/abs/2508.16757)):
  - Size: 148 queries, 2,787 documents, about 6.5 relevant documents per query, graded 0/1/2.
  - Dates: collected "from April 2025 onward"; the paper also says May 2025, which is inconsistent.
  - Candidates come from a general web search engine. Annotation was by one author, with novelty "validated against GPT-4" on a subset.
  - Finding: "a consistent 5-15% performance drop across all method categories" on novel queries. Listwise methods degrade least (average 8%) and pairwise most (15%). The authors conclude that "claims of 'generalization' based on standard benchmarks may be overstated."
- **Contamination through training data.** PRP notes that "FLAN models have a question answering task based on MSMARCO" ([arXiv:2306.17563](https://arxiv.org/abs/2306.17563) appendix). "Zero-shot" LLM rerankers may therefore have seen the benchmark's source distribution.
- **Internal test sets.** Drowning in Documents builds internal enterprise sets because "Rerankers have been directly tuned for these evaluations [MSMARCO, BEIR]" ([arXiv:2411.11767 §2.4](https://arxiv.org/abs/2411.11767)).
- **Common weaknesses.** Novel sets are small (21 and 148 queries), judged by few annotators, and draw candidates from a proprietary search engine. They show a contamination *gap*, but have little statistical power for ranking systems against each other.

## Relevance to lean-explore-bench

- **Test order robustness.** LeanExplore's reranker is a pointwise cross-encoder (Qwen3-Reranker-0.6B), so it is order-invariant by construction. LLM-based stages are not; examples are LeanSearch v2 reasoning mode, or any listwise or judge-based reranker ([../premise-selection/leansearch-v2.md](../premise-selection/leansearch-v2.md)). For any listwise or LLM stage, report results under the original order, reversed order and ≥5 shuffles (mean ± CI), following RankVicuna, RankZephyr and Setwise.
- **Report nondeterminism.** For API-hosted LLM stages, run ≥3 repeats and report mean ± CI, plus counts of malformed outputs and the fallback policy.
- **Cost columns.** Use the Setwise set: LLM calls, prompt tokens, generated tokens, p50/p95 latency on stated hardware, and USD where an API is used. For cross-encoders, add the number of (query, candidate) pairs scored, which equals `rerank_top`.
- **Lean contamination.** Mathlib declarations, their docstrings and informalizations are public and very likely in LLM training data (unverified for specific models). The Lean analogue of NovelEval is a set of queries targeting declarations **added to Mathlib after** the rerankers' and embedders' release or training cutoff, evaluated against a Mathlib snapshot that contains them. Report the gap between old and new declarations, as FutureQueryEval does, rather than using the novel set alone to rank systems.

## Open questions

- Does the Qwen3-Reranker training mix include Lean or Mathlib text? The Qwen3 Embedding paper mentions code retrieval and synthetic data but does not list Lean (unverified).
- How many post-cutoff Mathlib declarations are there per quarter? Is that enough for a novel slice with useful statistical power?

## Sources

- RankGPT: https://arxiv.org/abs/2304.09542
- RankVicuna: https://arxiv.org/abs/2309.15088
- RankZephyr: https://arxiv.org/abs/2312.02724
- PRP: https://arxiv.org/abs/2306.17563
- Setwise: https://arxiv.org/abs/2310.09497 ; code https://github.com/ielab/llm-rankers
- Permutation self-consistency: https://arxiv.org/abs/2310.07712
- Lost in the Middle: https://arxiv.org/abs/2307.03172
- FutureQueryEval: https://arxiv.org/abs/2508.16757
- Drowning in Documents: https://arxiv.org/abs/2411.11767
- RankLLM: https://arxiv.org/abs/2505.19284 ; https://github.com/castorini/rank_llm
