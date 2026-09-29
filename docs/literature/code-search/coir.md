# CoIR (Code Information Retrieval Benchmark)

- **Kind:** benchmark / leaderboard
- **Links:** paper https://arxiv.org/abs/2407.02883 ; code https://github.com/CoIR-team/coir
- **Authors / org, date:** Li, Dong, Lee et al. (Huawei Noah's Ark Lab). arXiv July 2024; ACL 2025 Main ([arXiv comment](https://arxiv.org/abs/2407.02883)).
- **Status:** Open source and pip-installable. It uses the BEIR/MTEB data schema ([abstract](https://arxiv.org/abs/2407.02883)), and code-embedding papers commonly report on it (for example [CodeXEmbed](https://arxiv.org/abs/2411.12644)).

## What it is

CoIR is a BEIR-style suite of 10 datasets covering 8 retrieval tasks across 7 domains ([abstract](https://arxiv.org/abs/2407.02883)). The tasks are grouped as follows ([paper §3, Table 3](https://arxiv.org/abs/2407.02883)):

- **Text-to-Code:** APPS, CosQA, Synthetic Text2SQL
- **Code-to-Text:** CodeSearchNet
- **Code-to-Code:** CodeSearchNet-CCR, CodeTransOcean-Contest, CodeTransOcean-DL
- **Hybrid:** StackOverflow QA, CodeFeedback-ST, CodeFeedback-MT

## How it works

- Each dataset is converted to (queries, corpus, qrels) in the BEIR format. The primary metric is NDCG@10, "in line with BEIR and MTEB" ([paper §4](https://arxiv.org/abs/2407.02883)).
- Queries are mostly *derived* from existing datasets: problem statements, docstrings, translated code and StackOverflow questions. They are not logged user searches.
- The paper also reports embedding and retrieval latency and index size per model ([paper, Table 4](https://arxiv.org/abs/2407.02883)).

## Evaluation

Average NDCG@10 from the paper's Table 3 ([arXiv 2407.02883](https://arxiv.org/abs/2407.02883)):

| Model | Avg NDCG@10 |
|---|---|
| BM25 | 29.79 |
| UniXcoder (123M) | 37.33 |
| OpenAI-Ada-002 | 45.59 |
| E5-base (110M) | 50.90 |
| E5-Mistral (7B) | 55.18 |
| Voyage-Code-002 | 56.26 |

- APPS is the hardest subset: the best model gets NDCG@10 26.52 ([paper App. B](https://arxiv.org/abs/2407.02883)).
- Voyage-Code-002 has the best average but "high variance, suggesting weaker generalization"; BGE-M3 has the lowest variance ([paper §4](https://arxiv.org/abs/2407.02883)).
- Later models report large gains on CoIR. For example, CodeXEmbed-7B claims more than 20% over Voyage-Code ([CodeXEmbed abstract](https://arxiv.org/abs/2411.12644)).

## Known flaws

1. **Many queries are derived, not natural.** Docstrings, problem statements and translation sources behave differently from how people search. The authors' own overfitting figure shows CodeSearchNet scores inflated relative to CoIR ([paper Fig. 4](https://arxiv.org/abs/2407.02883)).
2. **Contamination and training overlap are likely.** Component datasets (CodeSearchNet, CosQA, APPS, StackOverflow) are public and widely used to train code embedders. The paper explicitly suspects that Ada-002 and Voyage-Code-002 "may have already overfitted to CodeSearchNet" ([paper §5](https://arxiv.org/abs/2407.02883)).
3. **Single averaged NDCG@10 hides task heterogeneity.** Per-task winners differ; for example, E5-base beats Voyage on CodeFeedback-MT ([paper §4](https://arxiv.org/abs/2407.02883)).
4. **Mostly one relevant document per query.** This inherits the false-negative issue discussed in [cosqa.md](cosqa.md).

## Relevance to lean-explore-bench

- **Reuse the engineering pattern:** ship the benchmark as BEIR/MTEB-format (queries, corpus, qrels) with a pip-installable runner. Then any embedding model or search API can be evaluated with existing tooling, and results can be compared with MTEB-style leaderboards.
- **Split by task type, not one number.** Report per-stratum results for Lean: NL→decl, name/partial-name→decl, type/pattern→decl, informal statement→theorem, and decl→related decl.
- **Include BM25 as a baseline,** plus a note on index size and latency, following CoIR's efficiency reporting.
- **CoIR does not model** structured or type queries (Loogle-style), and it does not use a per-query candidate filter such as "must typecheck".

## Open questions

- Should lean-explore-bench be submitted as an MTEB task so that general embedders get scored on it automatically?

## Sources

- CoIR paper: https://arxiv.org/abs/2407.02883
- CoIR code: https://github.com/CoIR-team/coir
- CodeXEmbed: https://arxiv.org/abs/2411.12644
