# BRIGHT theorem subsets (TheoremQA-Q, TheoremQA-T, AoPS) and TheoremQA

- **Kind:** benchmark / dataset
- **Links:** BRIGHT https://arxiv.org/abs/2407.12883 · https://github.com/xlang-ai/BRIGHT · https://huggingface.co/datasets/xlangai/BRIGHT · TheoremQA https://arxiv.org/abs/2305.12524 · https://github.com/wenhuchen/TheoremQA
- **Authors / org, date:** BRIGHT: Su, Yen, Xia et al. (HKU, Princeton, Stanford, UW, Google Cloud AI Research), arXiv July 2024, ICLR 2025 ([arXiv](https://arxiv.org/abs/2407.12883); ICLR style file in source). TheoremQA: Chen et al., EMNLP 2023 ([arXiv](https://arxiv.org/abs/2305.12524)).
- **Status:** public data and code; BRIGHT has become a standard "reasoning-intensive retrieval" leaderboard.

> See also `../embedding-evaluation/bright.md` (whole-benchmark view, written by another agent); this note covers only the theorem subsets.

## What it is
TheoremQA contains 800 expert-curated questions covering 350 theorems in math, physics, EE/CS and finance. It is a QA benchmark, not retrieval ([TheoremQA abstract](https://arxiv.org/abs/2305.12524)). BRIGHT builds 12 retrieval datasets and 1,384 queries in which relevance requires reasoning. Three of them are "theorem-based" ([BRIGHT abstract, §3](https://arxiv.org/abs/2407.12883)):

| Subset | #Q | Corpus | avg gold/Q | Query source → docs |
|---|---|---|---|---|
| AoPS | 111 | 188,002 | 4.7 | Olympiad problem → solved STEM problems |
| TheoremQA-Q | 194 | 188,002 | 3.2 | theorem-based question → solved STEM problems |
| TheoremQA-T | 76 | 23,839 | 2.0 | theorem-based question → ProofWiki theorem statements |

(numbers from [BRIGHT Table 1](https://arxiv.org/abs/2407.12883))

## How it works (benchmark construction)
- **Relevance definition:** a document is positive if it "references the same theorem used in the query" ([§3.3](https://arxiv.org/abs/2407.12883)). For AoPS, a positive shares the same problem-solving skill, taken from AoPS Wiki annotations ([§3.3, App. AoPS](https://arxiv.org/abs/2407.12883)).
- **De-lexicalised queries.** The authors found that TheoremQA questions often *name the theorem outright*, so keyword retrievers would win trivially. They had GPT-4 rewrite each question into an applied scenario that needs the same theorem. Humans then checked solvability and consistency and discarded failures, leaving 206 of the 800 questions ([App. TheoremQA](https://arxiv.org/abs/2407.12883)). AoPS problems were not rewritten because they are already phrased diversely.
- **TheoremQA-T gold construction** ([App. "Annotating relevant theorems"](https://arxiv.org/abs/2407.12883)):
  1. Build a candidate pool from the ProofWiki corpus (MathPile preprocessing) in two ways: take documents whose text contains the theorem name as a substring (the set is dropped if it has more than 100 hits), and add the BM25 top-10 using the theorem name plus its definition as the query.
  2. GPT-4 judges whether each candidate's theorem is used in the solution.
  3. Authors hand-annotated 50 instances, with **Cohen's κ = 0.62** against GPT-4.
  4. Queries with no positive are dropped.
- **Metric:** nDCG@10 is the headline, with Recall@10 and P@10 in the appendix ([Table 2](https://arxiv.org/abs/2407.12883)).

## Evaluation (nDCG@10, [BRIGHT Table 2](https://arxiv.org/abs/2407.12883))
| Model | AoPS | TheoQ | TheoT |
|---|---|---|---|
| BM25 | 6.2 | 10.4 | 4.9 |
| SFR-Embedding-Mistral | 7.4 | 24.3 | 26.0 |
| E5-Mistral | 7.1 | 26.1 | 26.8 |
| gte-Qwen1.5-7B-instruct | 14.4 | 27.8 | 32.9 |
| OpenAI text-embedding-3-large | 8.5 | 23.5 | 11.7 |

- Overall, the best model averages 22.5 across the 12 datasets. The MTEB leader, SFR-Embedding-Mistral (59.0 nDCG@10 on MTEB retrieval), drops to 18.3 on BRIGHT ([abstract](https://arxiv.org/abs/2407.12883)).
- Having an LLM reason about the query first (query rewriting / chain of thought) improves nDCG@10 by up to 12.2 points ([abstract](https://arxiv.org/abs/2407.12883)).

## Relevance to lean-explore-bench
- **TheoremQA-T is the closest informal analogue of our task:** a problem statement goes in and a library theorem statement comes out. Its construction is directly reusable. Swap ProofWiki for Mathlib, generate the candidate pool (name substring plus BM25 over the name and definition), then have an LLM judge with a human κ check on a sample. This gives a cheap way to build query-to-Mathlib gold sets from existing theorem-tagged QA data.
- **De-lexicalisation is essential.** If queries name the theorem ("by Lagrange's theorem..."), lexical and name-matching engines win. We should keep separate query strata: (a) named-concept queries, (b) paraphrased or definitional queries, (c) application or scenario queries where the theorem is implicit.
- **Report κ between the LLM judge and humans.** BRIGHT's 0.62 on 50 items is a floor that reviewers will accept. We should also report per-stratum κ.
- **Pooling weakness:** positives come only from name-substring and BM25 candidates, so the pool is biased toward lexical systems. Dense or semantic engines that surface valid theorems outside that pool are counted as wrong. With several Lean engines to compare, pool from **all** engines under test, as in TREC/ARQMath.
- **Small query counts** (76 for TheoremQA-T) give wide confidence intervals. Report bootstrap CIs.

## Open questions
- How much of TheoremQA-T's 76 queries map to Mathlib (TheoremQA covers physics and finance too)?
- Is the "same theorem" criterion too coarse for Mathlib, where one informal theorem splits into many lemma variants? That calls for graded relevance: exact statement, variant or specialisation, useful ingredient.

## Sources
- Su et al., BRIGHT, arXiv:2407.12883 (LaTeX source read: data.tex, appendix.tex, tables/statistics, tables/main_results, tables/models): https://arxiv.org/abs/2407.12883
- Chen et al., TheoremQA, arXiv:2305.12524: https://arxiv.org/abs/2305.12524
- Model identities (e5-mistral-7b-instruct, SFR-Embedding-Mistral, gte-Qwen1.5-7B-instruct, text-embedding-3-large) come from BRIGHT's `tables/models.tex`.
