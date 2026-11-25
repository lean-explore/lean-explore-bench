# Synthetic queries: training-time generators (InPars, Promptagator, GPL), query simulation, and LLM query variants

- **Kind:** paper survey (evaluation methodology)
- **Links:**
  - InPars: [arXiv:2202.05144](https://arxiv.org/abs/2202.05144); InPars-v2: [arXiv:2301.01820](https://arxiv.org/abs/2301.01820); Promptagator: [arXiv:2209.11755](https://arxiv.org/abs/2209.11755); GPL: [arXiv:2112.07577](https://arxiv.org/abs/2112.07577)
  - Azzopardi, de Rijke, Balog, "Building simulated queries for known-item topics", SIGIR 2007: [doi:10.1145/1277741.1277820](https://dl.acm.org/doi/10.1145/1277741.1277820)
  - Breuer, Fuhr, Schaer, "Validating Simulations of User Query Variants", ECIR 2022: [arXiv:2201.07620](https://arxiv.org/abs/2201.07620), code [irgroup/ecir2022-uqv-sim](https://github.com/irgroup/ecir2022-uqv-sim)
  - Kruff, Bernard, Schaer, "Validating Search Query Simulations: A Taxonomy of Measures", 2026: [arXiv:2601.11412](https://arxiv.org/abs/2601.11412)
  - Balog & Zhai, "User Simulation for Evaluating Information Access Systems" (FnTIR book): [arXiv:2306.08550](https://arxiv.org/abs/2306.08550)
  - Alaofi, Gallagher, Sanderson, Scholer, Thomas, "Can Generative LLMs Create Query Variants for Test Collections?", SIGIR 2023: [arXiv:2501.17981](https://arxiv.org/abs/2501.17981), data [GitHub](https://github.com/MarwahAlaofi/SIGIR-23-SRP-UQV100-GPT-Query-Variants)
  - UQV100 (Bailey, Moffat, Scholer, Thomas, SIGIR 2016): [doi:10.1145/2911451.2914671](https://doi.org/10.1145/2911451.2914671)
- **Authors / org, date:** 2007–2026, see links
- **Status:** all code/data linked above is public, except Azzopardi et al. (paper only).

**Scope.** Fully synthetic collections and bias checks: [synthetic-test-collections.md](synthetic-test-collections.md). Human-label budgets and the Lean protocol: [synthetic-validation-budget-and-protocol.md](synthetic-validation-budget-and-protocol.md). Lexical-overlap filtering of generated queries (LitSearch, BRIGHT): [../embedding-evaluation/domain-benchmarks.md](../embedding-evaluation/domain-benchmarks.md). Paraphrase robustness (PTEB): [../embedding-evaluation/critiques-and-robustness.md](../embedding-evaluation/critiques-and-robustness.md). Tip-of-the-tongue / known-item query simulation is covered in the sibling note [known-item-tot-query-simulation.md](known-item-tot-query-simulation.md) (written separately; not cross-checked here).

## What it is

Three research lines generate queries without users:

1. **Doc → query generators for training** (InPars, Promptagator, GPL). A document is sampled and an LM writes a query it should answer. The resulting pairs train a retriever. These papers evaluate on *human* test sets and never validate their queries as test queries.
2. **Query simulation** (Azzopardi et al., Breuer et al., Balog & Zhai). Simulated queries are used *for evaluation*, so this line developed validation criteria.
3. **LLM query variants** (Alaofi et al.). An LLM writes many phrasings of one information need, compared with crowd-sourced variants (UQV100).

## How it works and what each says about evaluation

### InPars / InPars-v2 (training)
- **InPars.** GPT-3 was prompted with 3 MS MARCO examples plus a document to write a query. Only the top K = 10,000 of 100,000 pairs, ranked by the generator's mean token log-probability, were kept ([arXiv:2202.05144](https://arxiv.org/abs/2202.05144) §3). Training on all 100k instead of the filtered 10k cost 4 MRR@10 points on MS MARCO. The authors tuned this filter only on MS MARCO "to avoid relying on the test sets" (§6.3).
- **InPars-v2.** Swapped to open GPT-J-6B, still with 3 MS MARCO examples. Filtering now keeps the top 10k of 100k pairs *by a monoT5-3B reranker score* ([arXiv:2301.01820](https://arxiv.org/abs/2301.01820) §2).
- **Evaluation lesson.** Raw generator output is noisy enough that 90% is thrown away, and the filter is itself a retrieval model. If such a filter were used to build a *test* set, it would pre-select queries that monoT5-like systems already get right, which is a circularity trap.

### Promptagator (training)
- 2–8 task-specific examples prompt FLAN to generate queries per BEIR corpus. **Round-trip consistency filtering** keeps a (q, d) pair only if a retriever trained on the synthetic data ranks d in the top K for q ([arXiv:2209.11755](https://arxiv.org/abs/2209.11755) §3.2).
- **What the filter removed.** Manual inspection found most removed pairs had a query that was "too general which matches many documents" or contained "hallucination irrelevant to the document". Some good pairs were also wrongly removed (§4.3). Filtering helped on 8 of 11 datasets (+2.5 nDCG@10 on average) and hurt on the smallest ones (NFCorpus, SciFact).
- **Evaluation hygiene.** Few-shot examples taken from BEIR *test* sets are to be "treated as 'failed to retrieve'" when scoring (§2). The authors also retrained FLAN without NQ and Quora to check that pre-training exposure did not inflate results (§4.3). Both are contamination controls worth copying.
- **Distribution shift.** Figure 3 compares the first words of gold, few-shot-generated and NQ-QGen queries on ArguAna. Few-shot queries sit close to the gold distribution, while the NQ-trained generator produces "mostly questions" (§4.4). Query style follows whatever the generator was trained or prompted on, which is why a test-query generator's style has to be checked against real queries.

### GPL (training)
- Queries come from a T5 doc2query model (4 per passage, nucleus sampling). Hard negatives come from dense retrievers. A cross-encoder **pseudo-labels** each (query, positive, negative) triple with a score margin, and training uses MarginMSE ([arXiv:2112.07577](https://arxiv.org/abs/2112.07577) §3).
- **Why.** The authors state the two failure modes of generated pairs directly: the generator "might generate queries that are not answerable by the passage", and "other passages might actually be relevant as well" (false negatives). Soft cross-encoder labels absorb both (§3).
- **Evaluation lesson.** Both failure modes carry over to test sets: the source document may not answer the query, and it is rarely the only relevant one. Rahmani et al. measured the second as a collapse to τ = 0.157 ([synthetic-test-collections.md](synthetic-test-collections.md)).

### Query simulation for evaluation
- **Azzopardi, de Rijke & Balog (SIGIR 2007).** This line is the closest match to Lean search.
  - **Method.** Pick a target document, then sample query terms from its language model (Controlled Query Generation) to simulate *known-item* queries. Breuer et al. describe it as Azzopardi et al. applying CQG "when generating queries for known-item search" ([arXiv:2201.07620](https://arxiv.org/abs/2201.07620) §2).
  - **Validation.** "Replicative validity": are simulated queries' MRR distributions statistically indistinguishable from manual known-item queries, tested with a Kolmogorov–Smirnov test, across six European languages? (via search summary; unverified)
- **Breuer, Fuhr & Schaer (ECIR 2022).** A validation framework for simulated query variants against real UQVs on TREC Common Core 2017 ([arXiv:2201.07620](https://arxiv.org/abs/2201.07620) §3). It has five facets:
  1. Average retrieval performance
  2. Topic score distributions, via RMSE and paired t-tests
  3. "Shared task utility": Kendall's τ of system orderings, following Huurnink et al.
  4. Effort/effect: sDCG and isoquants
  5. Query-term overlap

  Findings (§5):
  - Queries simulated from topic text are a **lower bound** and known-item queries an **upper bound** on real-query effectiveness.
  - A parameterised simulator reproduced mean effectiveness and score distributions, and preserved system orderings "up to the fifth reformulation".
  - Term overlap with real queries was only slight.
- **Kruff, Bernard & Schaer (2026).** Literature review of 24 papers that validate query simulations, turned into a taxonomy with two meta-facets: *indistinguishability* from real queries and *performance approximation* ([arXiv:2601.11412](https://arxiv.org/abs/2601.11412) §3). Factor analysis on four datasets, including UQV100 GPT variants and DL seed-query variants:
  - Classical IR metrics (nDCG, P, R, MAP, MRR) are largely redundant with each other (mean Pearson 0.77).
  - Query-similarity measures (BERTScore, Jaccard, cosine) and SERP-overlap measures (Jaccard, RBO) add complementary information.
  - Recommendation: report one from each cluster rather than several IR metrics (§5). A measures library is released.
- **Balog & Zhai (FnTIR).** Book-length survey of user simulation for evaluation, including query simulation ([arXiv:2306.08550](https://arxiv.org/abs/2306.08550), abstract). Not read in detail for this note.

### LLM query variants (Alaofi et al., SIGIR 2023)
- **Human baseline (UQV100).** 100 backstories from TREC Web 2013/14. Crowd workers wrote about 57 variants per backstory on average (as summarised in [arXiv:2501.17981](https://arxiv.org/abs/2501.17981) §1).
- **Setup.** text-davinci-003, one-shot with one UQV100 topic's human variants (that topic excluded from analysis), temperatures 0 / 0.5 / 1. Zero-shot produced long question-like queries, so it was dropped (§2.1).
- **Query-level similarity was low.** Jaccard with human variants ranged from 7.1% (exact match) to 13.5% at most (normalised). The GPT sets reproduced at most 18.7% of human queries (§3.1).
- **Pool-level similarity was higher.** Overlap of *relevant* retrieved documents reached 43.7% at depth 10 and **71.1% at depth 100** (temperature 1.0) (§3.2).
- **But the GPT sets were less diverse and scored worse.** Their pools were about half the size of the human pools (94–105 vs 190.69 docs at depth 10) and grew more slowly. They had higher RBO between variants and significantly lower P@10 / nDCG@10 / RBP than human variants (Table 2, Bonferroni t-tests). The share of unjudged documents was higher (0.31–0.37 vs 0.13), so part of the gap may be missing judgments.
- **Authors' framing.** Promising for *pool construction*, not a replacement for human variants. UQV100 is itself "somewhat artificial" as a reference (§3.1).

## Relevance to lean-explore-bench

- **Lean search is mostly known-item search.** A user wants a specific lemma or definition. The known-item simulation line (Azzopardi, Breuer) applies directly. Breuer's result that known-item-seeded queries are an effectiveness **upper bound** matches Rahmani's "synthetic is easier". Queries written by an LLM *looking at the declaration* will leak its vocabulary (names, hypotheses), unless the prompt forbids it and a lexical-overlap filter enforces it (LitSearch-style; see [../embedding-evaluation/domain-benchmarks.md](../embedding-evaluation/domain-benchmarks.md)).
- **Generate from needs, not only from targets.** Alaofi et al. generate from *backstories*, i.e. information needs, not documents. For Lean that means seeding from real questions (Zulip, GitHub, proof states) as well as from declarations. Lean Finder mined intent clusters from 693 real questions and then generated with GPT-4o ([../lean-benchmarks/lean-finder-eval.md](../lean-benchmarks/lean-finder-eval.md)). The generation idea is good; the same-pipeline test set is the problem.
- **Diversity has to be measured.** LLM variants cover fewer distinct formulations and produce smaller pools. Report per-target variant count, pairwise query similarity, and pool growth across variants, and compare them with the human anchor (MathlibQR's six expert styles per target are a ready anchor; [../lean-benchmarks/mathlibqr.md](../lean-benchmarks/mathlibqr.md)).
- **Validation facets to report (Breuer / Kruff):** one IR metric's score distribution vs human queries (RMSE or KS); Kendall's τ of engine ordering; SERP overlap (RBO) between human and synthetic queries for the same target; query similarity. More IR metrics add little.
- **Do not borrow a training filter for test data.** Round-trip or reranker-score filters (Promptagator, InPars-v2) select queries that some retriever already solves, which biases the test set toward that retriever family. Filter test queries with human review or retriever-independent checks: answerability by the target, no leakage of the target's name, well-formedness.

## Open questions

- No study validates LLM-generated *formal or mixed* (Lean syntax + prose) queries against human ones. Every result above is for English web or news text.
- Does a KS / τ validation on 30–50 human-anchored targets detect a leakage-driven inflation that affects only engines with name-BM25?
- How many variants per Lean target does it take to saturate the pool? UQV100's figure of about 57 comes from web backstories.

## Sources

- InPars: https://arxiv.org/abs/2202.05144 (§3, §6.3)
- InPars-v2: https://arxiv.org/abs/2301.01820 (§2)
- Promptagator: https://arxiv.org/abs/2209.11755 (§2, §3.2, §4.3, Fig. 3)
- GPL: https://arxiv.org/abs/2112.07577 (§3)
- Breuer et al. 2022: https://arxiv.org/abs/2201.07620 (§§2–5)
- Kruff et al. 2026: https://arxiv.org/abs/2601.11412 (§§3–5)
- Balog & Zhai: https://arxiv.org/abs/2306.08550 (abstract only)
- Alaofi et al. 2023: https://arxiv.org/abs/2501.17981 (Tables 1–2, §§2–3)
- Azzopardi et al. 2007: https://dl.acm.org/doi/10.1145/1277741.1277820. Method confirmed via Breuer et al.; the MRR and KS-test validation details come from a search summary (unverified).
