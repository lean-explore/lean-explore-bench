# CoSQA, CodeXGLUE WebQueryTest, and CoSQA+

- **Kind:** benchmark / dataset
- **Links:** CoSQA https://arxiv.org/abs/2105.13239 (code: https://github.com/Jun-jie-Huang/CoCLR) ; WebQueryTest https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-WebQuery ; CoSQA+ https://arxiv.org/abs/2406.11589 (code/data: https://github.com/DeepSoftwareAnalytics/CoSQA_Plus)
- **Authors / org, date:** CoSQA: Huang et al. (Microsoft et al.), ACL 2021. CoSQA+: Gong et al. (Sun Yat-sen University), arXiv June 2024, accepted to TSE 2025 ([arXiv comment](https://arxiv.org/abs/2406.11589)).
- **Status:** Both datasets are public. CoSQA is included as a task in CoIR ([CoIR](https://arxiv.org/abs/2407.02883)).

## What it is

- **CoSQA:** 20,604 (web query, Python function) pairs, each labelled 1/0 for "does this code answer the query", with at least 3 annotators per pair ([paper, abstract and §3](https://arxiv.org/abs/2105.13239)).
- **WebQueryTest:** a 1,046-pair Python test set built the same way (Bing queries, CodeSearchNet code), framed as binary classification ([README](https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-WebQuery)).
- **CoSQA+:** re-pairs the CoSQA queries with *multiple* candidate functions from CodeSearchNet. It releases CoSQA+_all (412,080 agent-annotated pairs) and CoSQA+_verified (1,000 human-verified pairs) ([abstract](https://arxiv.org/abs/2406.11589)).

## How it works

- **Queries (CoSQA):** taken from Microsoft Bing search logs. A filter removes queries without code-search intent; the filter was checked on 250 hand-labelled queries ([paper §3](https://arxiv.org/abs/2105.13239)). These are real user queries: short (average 6.6 tokens, per Table 4) and casual.
- **Candidates (CoSQA):** the candidate pool was *pre-filtered by a model*. A CodeBERT matcher fine-tuned on StaQC retrieved high-confidence functions per query, and only those were annotated ([paper §3](https://arxiv.org/abs/2105.13239)).
- **Labels (CoSQA):** a two-step guideline, first intent and then whether the code answers the query. More than 100 annotators took part. Pairs with poor agreement were removed. Mean Krippendorff's α is 0.63 ([paper §3](https://arxiv.org/abs/2105.13239)).
- **Retrieval metric (CoSQA):** MRR, with one gold function per query ([paper §4](https://arxiv.org/abs/2105.13239)).
- **CoSQA+ labelling:** candidates come from several retrievers. Labels come from a "test-driven agent" pipeline in which an LLM writes and runs test programs against each candidate function. The authors report that this pipeline reached 93.9% accuracy, compared with a single LLM annotator or Python experts without tests ([abstract](https://arxiv.org/abs/2406.11589)). About 33% of candidates were ambiguous and went to further agent adjudication (paper §3; figure from PDF text).
- **CoSQA+ metric:** MAP@10 is primary; MRR, NDCG@10 and Recall are also reported. The motivation is that MRR "measures the rank position of the first relevant code snippet" but developers want several examples. Their survey of Python developers reports that 63.2% of their queries have multiple acceptable answers ([paper §1](https://arxiv.org/abs/2406.11589)).

## Evaluation

- **CoSQA MRR baselines** (UniXcoder Table 1; values read from PDF text): CodeBERT 65.7, GraphCodeBERT 68.4, UniXcoder 70.1 ([arXiv 2203.03850](https://arxiv.org/abs/2203.03850)).
- **CoIR's CoSQA subset (NDCG@10):** BM25 13.96, E5-base 32.59, Voyage-Code-002 29.79. General text embedders do about as well as the code-specific one here ([CoIR Table 3](https://arxiv.org/abs/2407.02883)).
- **CoSQA+ absolute numbers are low.** The best model in their Table V (CodeBERT) has NDCG@10 0.232, MRR 0.175 and MAP 0.164 ([paper §5](https://arxiv.org/abs/2406.11589)). This reflects the much larger multi-positive pool.

## Known flaws

1. **Model-in-the-loop candidate selection.** CoSQA only labels what a CodeBERT matcher already ranked highly, which biases the benchmark toward systems similar to that matcher. This is the same pooling-bias issue as CodeSearchNet.
2. **False negatives from single-positive evaluation.** CoSQA+ shows that many CodeSearchNet functions satisfy a CoSQA query; 36.7% of codes satisfy two or more queries ([paper §6](https://arxiv.org/abs/2406.11589)). One-to-one MRR penalizes retrievers that find those other valid answers.
3. **Label noise.** CoSQA+ attributes residual errors to ambiguous queries (30%), annotator bias (30%), semantic misalignment (20%) and test-validation misalignment (20%) ([paper §6](https://arxiv.org/abs/2406.11589); percentages from PDF text).
4. **Functional versus semantic relevance.** CoSQA+ argues that annotators judge by reading rather than execution. Their test-driven labels are functional. For Lean the analogue is "does this lemma actually close or rewrite the goal", which the compiler can check.
5. **Python only; data is public and old** (Bing logs from before 2021, CodeSearchNet code from 2019), so contamination is likely for modern models (not quantified in the papers).

## Relevance to lean-explore-bench

- **Query source:** real search logs are the gold standard for realism. The closest Lean analogue is Zulip "is there a lemma that..." threads. Filtering for search intent is needed there too.
- **Multi-positive labels are essential in Mathlib.** It has many near-duplicate or equivalent lemmas (`_left`/`_right`, `'`-variants, deprecated aliases, `simp` normal forms). Use MAP@k, Recall@k or nDCG over graded sets, not single-gold MRR.
- **"Test-driven" labelling transfers unusually well to Lean.** An LLM can propose a candidate lemma, and `exact?`/`apply`/`rw` in a real Lean environment can mechanically check whether it closes the target goal. That is a stronger oracle than CoSQA+ had, but it only works for goal-shaped queries.
- **Pool from many diverse engines,** not one model, to avoid CoSQA's candidate-selection bias.

## Open questions

- How do we label "relevant but weaker/stronger" lemmas? A graded scale (exact / generalization / specialization / related) may be better than binary.

## Sources

- CoSQA: https://arxiv.org/abs/2105.13239
- WebQueryTest README: https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-WebQuery
- CoSQA+: https://arxiv.org/abs/2406.11589 ; https://github.com/DeepSoftwareAnalytics/CoSQA_Plus
- UniXcoder baselines: https://arxiv.org/abs/2203.03850
- CoIR: https://arxiv.org/abs/2407.02883
