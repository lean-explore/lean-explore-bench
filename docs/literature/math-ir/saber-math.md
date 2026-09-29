# SABER-Math

- **Kind:** benchmark / dataset
- **Links:** https://arxiv.org/abs/2606.29894 · https://github.com/insait-institute/sabermath/ · https://huggingface.co/collections/INSAIT-Institute/saber-math
- **Authors / org, date:** Georgiev, Drencheva, Ibragimova, Petrov, Dimitrov, Vechev (INSAIT, Sofia University; Vechev also ETH Zurich), arXiv June 2026; accepted at EMNLP 2026 per arXiv comment ([arXiv](https://arxiv.org/abs/2606.29894))
- **Status:** code and data links given in the paper header (links not fetched)

## What it is
A **fully automated** (no expert annotation) reranking benchmark for math IR. It is built from 283K high-school and olympiad problem–solution pairs, with 1,000 queries across Algebra, Geometry, Number Theory, Combinatorics and Calculus. Each query has 150 candidates with fine-grained graded relevance ([abstract, intro](https://arxiv.org/abs/2606.29894)).

## How it works (benchmark construction)
1. An LLM extracts a short solution summary and ontology topics for each problem.
2. **Candidate discovery** uses two signals: topic overlap in a math ontology, and lexical overlap between solution summaries. These are used *only* to choose candidates, not as labels. Candidates are split evenly between the two signals ([intro, Fig. 1](https://arxiv.org/abs/2606.29894)).
3. **Labels** come from pairwise LLM judgments by GPT-OSS-120B in a 20-round **Swiss tournament**, aggregated with **Bradley–Terry** into continuous scores. Scores are normalised per query, so every query contributes a bounded amount to nDCG ([bradley-terry.tex](https://arxiv.org/abs/2606.29894)). The Swiss tournament needs 1,500 comparisons instead of 11,175 for all pairs, with 700 inversions against the exhaustive ranking ([appendix](https://arxiv.org/abs/2606.29894)).
4. **Metric:** nDCG@10 with exponential gain. Changing the gain or score range reordered only 9 of 861 model pairs ([appendix "Final Metric Choice"](https://arxiv.org/abs/2606.29894)).

## Evaluation
- **Human validation** on 200 triplets (query plus two candidates) ([appendix](https://arxiv.org/abs/2606.29894)):
  - Two annotators agreed on **75.0%** of the 20 items they both labelled.
  - The pairwise LLM judge agreed with humans on 78.0% (95% CI 0.718–0.832). An *ordinal* (absolute-score) judge reached 75.0%, and a 5-vote majority 77.5%.
  - The Swiss-tournament ordering agreed 78.0%, full Bradley–Terry 79.0%, and random scheduling 75.6%.
- **Headline scores** (nDCG@10) ([tables/dedup_*.tex](https://arxiv.org/abs/2606.29894)): ReasonEmbed-Qwen3-8B-Rewrite scores 0.738, Qwen3-Embedding-8B 0.611, Approach Zero 0.468, BM25 0.416 and Jaccard 0.412.
- **External validity:** SABER nDCG@10 correlates with a downstream deduplication task at Spearman ρ = 0.96 (over the full 71K pool). Correlation with MTEB is Pearson 0.77 and Spearman 0.82, falling to 0.62 and 0.73 for models released in 2025 or later ([main_results.tex, appendix](https://arxiv.org/abs/2606.29894)).
- **Formula over-reliance:** Approach Zero (a structural formula engine) gets median duplicate rank 1 on the dedup task but ranks 43rd of 49 on SABER. Rewrites that keep formula structure reward formula matching while real relevance does not ([appendix](https://arxiv.org/abs/2606.29894)).

## Relevance to lean-explore-bench
- **Pairwise LLM judging beats absolute grading** here (78% against 75% human agreement). For our graded relevance labels, consider pairwise or tournament judging per query, then fit Bradley–Terry, as an alternative to 0–3 absolute scales.
- **Human–human agreement is only about 75%** on math relevance after easy negatives are removed. Any LLM-judge validation should report human–human agreement alongside it, which sets a realistic ceiling.
- **Validate the benchmark against a downstream task.** Their dedup check has a Lean analogue: whether retrieval helps a prover or autoformalizer succeed.
- **Limitation:** this is a reranking benchmark over preselected candidates, not first-stage retrieval, and it covers school-level math only ([limitations](https://arxiv.org/abs/2606.29894)).

## Open questions
- Licence of the 283K-problem source corpus.

## Sources
- Georgiev et al., SABER-Math, arXiv:2606.29894 (LaTeX source read: introduction.tex, bradley-terry.tex, limitations.tex, main_results.tex, appendix/app_additional.tex, tables/dedup_*.tex): https://arxiv.org/abs/2606.29894
