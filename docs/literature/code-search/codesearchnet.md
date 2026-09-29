# CodeSearchNet (Corpus, Challenge) and CodeXGLUE AdvTest

- **Kind:** benchmark / dataset
- **Links:** paper https://arxiv.org/abs/1909.09436 ; code/data https://github.com/github/CodeSearchNet ; AdvTest https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-Adv ; CodeXGLUE paper https://arxiv.org/abs/2102.04664
- **Authors / org, date:** Husain, Wu, Gazit, Allamanis, Brockschmidt (GitHub + Microsoft Research), Sept 2019. AdvTest: Lu et al. (Microsoft), CodeXGLUE, Feb 2021.
- **Status:** Data still downloadable (AdvTest points to a Zenodo mirror). The Weights & Biases leaderboard from the paper is no longer maintained (unverified). The dataset is still the most-used code-search training and evaluation source.

## What it is

- **CodeSearchNet Corpus:** about 6.45M functions in Go, Java, JavaScript, PHP, Python and Ruby. About 2.33M of them are paired with the first paragraph of their docstring. Split 80/10/10 ([paper, Table 1](https://arxiv.org/abs/1909.09436)).
- **CodeSearchNet Challenge:** 99 natural-language queries with 4,026 expert relevance annotations over corpus functions ([paper §3](https://arxiv.org/abs/1909.09436)).
- **AdvTest (CodeXGLUE):** a Python-only re-split of CodeSearchNet (train 251,820 / dev 9,604 / test 19,210). In the test set, function names and variables are replaced by special tokens "to test the generalization ability of a model" ([AdvTest README](https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-Adv)).

## How it works

- **Training/proxy task (docstring → code):** the docstring is used as the query and its function as the only positive. The paper's test protocol ranks the gold function against 999 fixed distractors and reports MRR ([paper, Table 2](https://arxiv.org/abs/1909.09436)). Nearly all later "CSN" numbers use this style of setup, often with the whole test set as the candidate pool.
- **Corpus filtering:** docstrings truncated to the first paragraph; pairs with docstrings under 3 tokens dropped; functions under 3 lines dropped; names containing "test", constructors and standard extension methods dropped; near-duplicates removed ([paper §2](https://arxiv.org/abs/1909.09436)).
- **Challenge queries:** "common search queries from Bing that had high click-through rates to code", combined with intent rewrites from StaQC. Queries that were "clearly technical keywords (e.g. the exact name of a function such as tf.gather_nd)" were removed by hand ([paper §3](https://arxiv.org/abs/1909.09436)). This is important for us: **name-style queries were deliberately excluded**.
- **Relevance judgments:** a 0–3 graded scale. Candidates were pooled from an ensemble of the baseline neural models plus ElasticSearch, taking the top 10 per query and language. Annotators were volunteer experts who saw one pair at a time in randomized order, with a link to the source context. Inter-annotator agreement on the 891 doubly-annotated pairs was moderate: Cohen's κ = 0.47 ([paper §3](https://arxiv.org/abs/1909.09436)).
- **Metric:** NDCG, reported two ways. "Within" computes NDCG only over annotated functions. "All" computes it over the whole corpus, where unannotated results count as non-relevant ([paper §3.1](https://arxiv.org/abs/1909.09436)).

## Evaluation

- **Challenge baselines:** ElasticSearch reached avg NDCG-Within 0.337 and NDCG-All 0.205. Neural bag-of-words was best, at 0.574 and 0.340. Self-attention, the best model on the docstring-proxy MRR task, did worse on real queries (0.493 / 0.240). The authors conclude that keyword matching is "a crucial facility" and that docstring-trained proxies are "not a good match for the code search task" ([paper, Tables 2–3](https://arxiv.org/abs/1909.09436)).
- **Proxy baselines:** self-attention reached MRR 0.7011 on the 1-of-1000 docstring task ([paper, Table 2](https://arxiv.org/abs/1909.09436)).
- **AdvTest MRR, one-line baselines** (as extracted from the UniXcoder paper's Table 1; column alignment was read from PDF text, so treat as approximately verified): CodeBERT 27.2, GraphCodeBERT 35.2, UniXcoder 41.3 ([UniXcoder, arXiv 2203.03850](https://arxiv.org/abs/2203.03850)).
- **Overfitting evidence:** the CoIR authors report that most models score far higher on CodeSearchNet than on CoIR, "indicating a strong overfitting tendency". OpenAI-Ada-002 and Voyage-Code-002 show the largest gaps ([CoIR, arXiv 2407.02883, Fig. 4](https://arxiv.org/abs/2407.02883)).

## Known flaws

1. **Docstring ≠ query.** The authors themselves note that docstrings are written by the code author "and hence tend to use the same vocabulary, unlike search queries". Some docstrings are also outdated or not in English ([paper §2 Limitations](https://arxiv.org/abs/1909.09436)).
2. **One positive per query.** The proxy task has exactly one relevant item per query. Semantically equivalent functions elsewhere in the pool count as negatives, which is the false-negative problem that CoSQA+ later targets ([CoSQA+](https://arxiv.org/abs/2406.11589)).
3. **Pooling bias.** Challenge relevance labels exist only for the top-10 pool of 2019 baselines, so "NDCG-All" penalizes novel relevant results ([paper §3.1](https://arxiv.org/abs/1909.09436)).
4. **Contamination.** The corpus is public GitHub code from 2019. Code LLMs and embedding models are trained on it, and on CSN itself as training data. CoIR's overfitting analysis suggests this matters ([CoIR](https://arxiv.org/abs/2407.02883)).
5. **Annotator disagreement is large (κ = 0.47).** Reported causes: code quality, query ambiguity, project-specific versus general code, missing context, and **directionality** (for example, `stringToInt` returned for "convert int to string") ([paper §3](https://arxiv.org/abs/1909.09436)).
6. **An evaluation bug changed published numbers.** v3 of the paper says "Updated evaluation numbers after fixing indexing bug" ([arXiv v3 comment](https://arxiv.org/abs/1909.09436)).

## Relevance to lean-explore-bench

- **Reuse the protocol shape:** a small, real, expert-graded query set (99 queries), graded 0–3 relevance, NDCG, and pooling from diverse systems. The Lean analogue is pooling top-k from LeanSearch, Moogle, LeanExplore, Loogle, exact-name search and BM25.
- **Report both "within judged" and "all" metrics**, or use condensed-list / bpref-style metrics, because new engines will surface unjudged Mathlib lemmas.
- **Do not use docstring→declaration as the headline benchmark.** Mathlib docstrings share vocabulary with declaration names, which is the same failure CSN documents. It is fine as a cheap auxiliary or training signal.
- **CSN excluded name-style queries.** A Lean benchmark must include them explicitly as a separate stratum, because "find `Finset.sum_comm`" or partial names are a large share of real Lean usage.
- **AdvTest-style identifier masking is a good robustness probe.** Mask or strip declaration names, and ask whether the engine still finds the lemma by statement or informal meaning.
- **Directionality errors map directly to Lean** (`a ≤ b` versus `b ≤ a`, `mul_comm` variants, `_left`/`_right`). Include them as hard negatives.

## Open questions

- Is the CSN Challenge relevance file still retrievable with its original 0–3 scale, and is the leaderboard archived? (unverified)
- What is a sensible κ target for Lean relevance labels, given code search achieved 0.47?

## Sources

- CodeSearchNet paper: https://arxiv.org/abs/1909.09436
- CodeSearchNet repo: https://github.com/github/CodeSearchNet
- CodeXGLUE paper: https://arxiv.org/abs/2102.04664
- AdvTest README: https://github.com/microsoft/CodeXGLUE/tree/main/Text-Code/NL-code-search-Adv
- UniXcoder (baseline numbers): https://arxiv.org/abs/2203.03850
- CoIR (overfitting comparison): https://arxiv.org/abs/2407.02883
- CoSQA+ (single-positive critique): https://arxiv.org/abs/2406.11589
