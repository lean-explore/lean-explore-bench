# Domain-specific embedding evaluations: how CoIR (code), BRIGHT (reasoning/math), LitSearch and SciRepEval (science) build queries and labels

- **Kind:** methodology note across benchmarks / datasets
- **Links:** CoIR [arXiv:2407.02883](https://arxiv.org/abs/2407.02883), [github.com/CoIR-team/coir](https://github.com/CoIR-team/coir); BRIGHT [arXiv:2407.12883](https://arxiv.org/abs/2407.12883); LitSearch [arXiv:2407.18940](https://arxiv.org/abs/2407.18940); SciRepEval [arXiv:2211.13308](https://arxiv.org/abs/2211.13308)
- **Authors / org, date:** CoIR: Huawei Noah's Ark et al., Jul 2024 (ACL 2025). BRIGHT: HKU / Princeton / Stanford et al., Jul 2024 (ICLR 2025). LitSearch: Princeton, Jul 2024 (EMNLP 2024). SciRepEval: AI2, Nov 2022 (EMNLP 2023).
- **Status:** All public. CoIR and BRIGHT are also MTEB tasks ([embed-mteb.md](embed-mteb.md)).
- **Not repeated here:** BRIGHT's theorem subsets (TheoremQA-Q/T, AoPS), their numbers and the TheoremQA de-lexicalization are in [math-bright-theoremqa.md](math-bright-theoremqa.md). CodeSearchNet itself is in [code-codesearchnet.md](code-codesearchnet.md). Math-retrieval suites are in [bench-mirb.md](bench-mirb.md) and [math-saber-math.md](math-saber-math.md).

## What it is

When a general benchmark does not predict performance in a domain, groups build a domain benchmark. The methodological differences between these benchmarks come down to three choices:

1. **Where queries come from:** repurposed pairs, LLM-generated, or human-written.
2. **How relevance is defined and labeled:** structural pairing, metadata, LLM judge, or experts.
3. **How trivial lexical matches and false negatives are controlled.**

## How it works

### CoIR (code retrieval): labels by construction from existing pairs

- **Composition.** 10 datasets, 8 sub-tasks, 4 task families (text-to-code, code-to-text, code-to-code, hybrid), 14 languages. BEIR/MTEB schema. Headline metric nDCG@10, with MAP, recall and precision also available ([CoIR](https://arxiv.org/abs/2407.02883)).
- **Queries and positives are derived structurally** from existing paired data. No new relevance judging is done ([CoIR appendix, dataset details](https://arxiv.org/abs/2407.02883)):
  - APPS: problem description → its solutions.
  - CoSQA: web query → code, with 20,604 human labels inherited from the source.
  - CodeSearchNet: roles reversed, code → docstring.
  - **CodeSearchNet-CCR:** each function is cut in two. The first 40–70% of characters (length drawn at random) is the query, and the remainder is the only positive.
  - StackOverflow QA: question → highest-voted answer.
  - CodeTransOcean: code → its translation in another framework or language.
- **Cleaning.** Hash-based exact deduplication, removal of pairs with missing or irrelevant docs, and manual inspection "to filter out instances that lack valid answers, exhibit ambiguity, contain irrelevant information" ([CoIR main text and appendix "Dataset Filtering and Cleaning"](https://arxiv.org/abs/2407.02883)).
- **Consequence:** usually one positive per query and no pooling. Every other equally valid snippet counts as non-relevant, so there are false negatives by design.
- **"Zero-shot" with shipped training splits.** CoIR calls itself "a one-stop zero-shot evaluation benchmark", but it keeps the source datasets' train splits (APPS 5,000 train; CoSQA 19,604/500/500; CodeSearchNet 905k/41k/53k). Any model fine-tuned on CodeSearchNet or CoSQA train data is in-domain there, and the benchmark does not track this.
- **Reports that general rank does not transfer.** Over seven models, GTE-Base drops from 2nd on BEIR to 6th on CoIR while E5-Base rises from 4th to 2nd ([CoIR "Comparison of CoIR and BEIR Rankings"](https://arxiv.org/abs/2407.02883)).
- **Reports efficiency and input length.** It measures latency per sample. GTE's scores on some sets change sharply when input length goes from 512 to 4,096 (StackOverflow QA 64.36 → 78.63), while BGE-M3 moves both ways ([CoIR input-length analysis](https://arxiv.org/abs/2407.02883)). Truncation length is therefore part of the protocol.

### BRIGHT (reasoning-intensive retrieval): relevance defined by shared reasoning

These are the parts beyond the theorem subsets.

- **Relevance is defined by what helps answer the query, not by topical similarity.** For theorem splits it is "references the same theorem". For StackExchange splits, a document is relevant "only if it is cited in an accepted or highly voted answer and unanimously confirmed by annotators and domain experts that it helps reason through the query" ([BRIGHT, data section](https://arxiv.org/abs/2407.12883)). Negatives include the rest of those web pages and Google results.
- **Per-query exclusion lists to avoid false negatives.** In the STEM problem-solution corpus used for TheoremQA-Q and AoPS, the authors "leverage the metadata from the original datasets to exclude specific documents from the corpus for each test query". For example, for chain-rule queries they drop CAMEL-Math "Calculus" pairs. The exclusions are chosen per query from category metadata, and the authors mention exhaustive annotation as the costlier alternative ([BRIGHT appendix, STEM corpus](https://arxiv.org/abs/2407.12883)). Mathlib has the same problem: many near-equivalent lemmas.
- **Metric changes with corpus size.** In the long-document variant, corpora have a few hundred documents, so BRIGHT switches from nDCG@10 to recall@1 ([BRIGHT, long-document analysis](https://arxiv.org/abs/2407.12883); see [eval-embedding-first-stage-metrics.md](eval-embedding-first-stage-metrics.md)).
- **Active leakage test.** Continued training on the StackExchange documents leaves the average essentially unchanged (20.5 → 20.4), with large per-domain swings (see [eval-embedding-critiques-and-robustness.md](eval-embedding-critiques-and-robustness.md)).
- **Query augmentation reported as its own condition.** LLM-generated reasoning steps added to the query improve scores, "but even the best model still achieves a score below 30" ([BRIGHT conclusion](https://arxiv.org/abs/2407.12883)). Query rewriting is reported as a separate system condition, not folded into the embedder's score.

### LitSearch (scientific literature): LLM-drafted plus author-written queries, filtered for lexical overlap

- **Two query sources** ([LitSearch](https://arxiv.org/abs/2407.18940)):
  1. GPT-4 drafts a question from an inline-citation context in S2ORC, and the cited paper is the target.
  2. Authors of ICLR 2024 and ACL 2023 papers write "challenging" questions about their own papers, with instructions to be specific and to reduce word overlap.
- **Word-overlap filter.** Generated questions with high overlap with the target title are discarded, because overlap "makes their retrieval trivial even for BM25". Overlap is measured as the "percentage of words in the generated question that are also included in the target paper titles", with a threshold such as 0.3 for ACL-sourced questions ([LitSearch, word-overlap filtering](https://arxiv.org/abs/2407.18940)).
- **Manual rubric.** Every question is annotated for quality (discarded / acceptable / …) and for **specificity** (broad vs specific). Specificity then decides the metric: R@20 for broad questions, R@5 and R@20 for specific ones.
- **Final size:** 597 questions.
- **Scope of engine comparisons.** Commercial search engines were evaluated on only 80 specific questions and are marked "not apples-to-apples as search engines use a much larger retrieval corpus".

### SciRepEval (scientific documents): explicit in-train vs out-of-train tasks

- **24 tasks in four formats:** classification, regression, proximity, ad-hoc search.
- **Search labels come from Semantic Scholar click-through data.** Queries with at least 10 results, heuristic bot and noise filtering, and removal of author-name queries detected with NER. Relevance is graded, derived from clicks, so the metric is nDCG. Candidates are ranked by embedding distance with pytrec_eval ([SciRepEval eval framework and task appendix](https://arxiv.org/abs/2211.13308)).
- **Tasks are split into in-train (models may train on them) and out-of-train (held out).** Example pairs: in-train FoS, Citation Count, Same Author Detection, Search; out-of-train DRSM, Peer Review Score, Peer-Reviewer Matching, TREC-CoVID. Results are analyzed on both sides ([SciRepEval analysis](https://arxiv.org/abs/2211.13308)).

## Evaluation (cross-benchmark comparison)

| | CoIR | BRIGHT | LitSearch | SciRepEval (search) |
|---|---|---|---|---|
| Query source | Repurposed pairs | Human posts plus LLM-rewritten TheoremQA | GPT-4 from citations, and paper authors | Real user queries (click logs) |
| Relevance source | Structural pairing | Human (StackExchange links), GPT-4 judge validated against humans (theorem splits) | Citation target or author's own paper | Clicks (graded) |
| Positives per query | ~1 | ~1–5 | 1 (specific) to several (broad) | Many, graded |
| Lexical-shortcut control | None explicit | LLM de-lexicalization (TheoremQA) | Title-overlap filter plus manual check | n/a (real queries) |
| False-negative control | Deduplication only | Per-query exclusion via metadata | Manual review | n/a |
| Headline metric | nDCG@10 | nDCG@10 (recall@1 for long documents) | Recall@5/20 by specificity | nDCG |
| Train/test separation | Ships train splits; called zero-shot | No training split | No training split | Explicit in-train vs out-of-train |

## Relevance to lean-explore-bench

- **Query sources.** Combine three:
  - real user queries (Zulip, search logs where licensed), the analogue of SciRepEval;
  - expert-written queries about declarations the writer knows well, the analogue of LitSearch's author questions: ask Mathlib contributors for queries about lemmas they wrote;
  - LLM-drafted queries from usage context, for example the proof context where a lemma is applied, the analogue of LitSearch's inline citations.

  Tag each query with its source and report per source.
- **Lexical-shortcut filter.** Compute token overlap between each query and the gold declaration's *name and docstring*, after splitting `snake_case`/`CamelCase` and dotted namespaces. Drop or separately bucket high-overlap queries, as LitSearch does with titles. Otherwise name-matching engines (BM25 over names, Loogle-like) win trivially.
- **De-lexicalized variants** for a subset, following BRIGHT's TheoremQA rewrite, checked by a human to still pin down the same lemma.
- **Per-query acceptable-set or exclusion lists.** Mathlib's `_left`/`_right`, primed, `Nat`/`Int`/general variants and `simp`-normal-form duplicates behave like BRIGHT's false negatives. Either label them "acceptable" (graded) or exclude them from that query's ranking, as BRIGHT does. Record which option is used.
- **Structural "free" tasks with caveats.** CoIR-style pairs are cheap: docstring → declaration, statement prefix → full statement, and proof step → premise, which is the LeanDojo style. They label one positive and ignore all equivalents, so treat them as a separate, clearly marked track.
- **Specificity annotation drives the metric:** known-item or specific queries get MRR/Recall@5, broad ones get nDCG@10/Recall@20 (LitSearch).
- **Declare any training split** and track which engines trained on it (a SciRepEval-style in-train/out-of-train flag), instead of calling the whole benchmark zero-shot as CoIR does.

## Open questions

- Is a "usage context → lemma" query (from a proof where the lemma is applied) closer to what people actually search for, or closer to premise selection? It might belong in the premise track instead.
- What overlap threshold counts as "trivial" for Lean names? LitSearch's 0.3 on titles is a starting point, but Lean names are compositional descriptions, so the threshold may need to be calibrated against BM25-over-names success.

## Sources

- CoIR: https://arxiv.org/abs/2407.02883 (acl_latex.tex: tasks, implementation details, efficiency, input length, CoIR vs BEIR rankings; appendix.tex: per-dataset construction, filtering, deduplication)
- BRIGHT: https://arxiv.org/abs/2407.12883 (texts/appendix.tex STEM corpus exclusions and TheoremQA rewrite; texts/analysis.tex leakage and long-document metric; texts/conclusion.tex)
- LitSearch: https://arxiv.org/abs/2407.18940 (LaTeX: data collection, word-overlap filtering, manual rubric, results table caption)
- SciRepEval: https://arxiv.org/abs/2211.13308 (3_eval_framework.tex, app1_tasks_description.tex, 7_analysis.tex, tables/1_eval_tasks.tex)
