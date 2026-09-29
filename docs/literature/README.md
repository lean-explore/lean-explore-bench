# Literature review: how to benchmark search

This folder holds one note per system, benchmark, paper or methodology topic,
collected while working out how to benchmark Lean 4 search engines well. Each
note follows [`_TEMPLATE.md`](_TEMPLATE.md), links a source for every claim,
and marks anything that could not be checked as *(unverified)*. Research was
done on 2026-09-28; hosted services and leaderboards change, so check dates
before relying on a number.

The first half of this file distils the notes into a working guide. The second
half is an index.

## How to benchmark search well

### 1. What already exists, and the gap

- Every published Lean search comparison was run by one engine's authors, on
  their own query set, and the authors' engine wins each time
  ([engine-leanexplore](engine-leanexplore.md),
  [engine-lean-finder](engine-lean-finder.md),
  [paper-leansearch-v2](paper-leansearch-v2.md)).
- The only independent comparison is the
  [Legendre leaderboard](bench-legendre-leaderboard.md): 13 systems on
  [MathlibQR](bench-mathlibqr.md), with a pinned corpus and bootstrap CIs, but
  no published code. The top three are statistically tied at about 73–74% R@10.
  LeanExplore is 8th (R@10 56.5%, nDCG@10 0.385).
- Existing Lean sets are small (50–200 targets), mostly synthetic or written
  by an engine team, and mostly allow one correct answer per query
  ([bench-mathlibqr](bench-mathlibqr.md),
  [bench-leansearch-v1-benchmark](bench-leansearch-v1-benchmark.md),
  [bench-mathlibmpr](bench-mathlibmpr.md)).
- No published numbers exist for Loogle, `exact?`/`apply?`, `rw?`, `#find` or
  doc-gen4 search ([tool-loogle](tool-loogle.md),
  [tool-exact-apply](tool-exact-apply.md)).
- No paper compares search engines as tools inside the same agent loop, in Lean
  or in code search
  ([paper-agents-with-search-tools](paper-agents-with-search-tools.md),
  [code-embedding-vs-grep-evidence](code-embedding-vs-grep-evidence.md)).

The gap is a neutral, reproducible, multi-track benchmark with open code. It
should have graded, pooled judgments and enough queries to separate engines.

### 2. Queries: where they come from and what shape they take

- **Match real use.** Models trained on docstring-like text did worse on real
  search-engine queries, and simple lexical baselines held up
  ([code-codesearchnet](code-codesearchnet.md)). Mix query sources and tag each
  query by source:
  - Agent traces: queries an agent issued while proving, labelled by the lemmas
    the finished proof used.
  - Real human queries, for example Zulip "is there a lemma for…" threads.
  - Expert-written queries.
  - LLM-generated queries.
- **Free seed set.** Mathlib's `docs/100.yaml`, `docs/1000.yaml`,
  `overview.yaml`, `undergrad.yaml` and `@[stacks]` tags hold roughly 1,300
  informal-to-declaration pairs
  ([math-informal-formal-alignment](math-informal-formal-alignment.md)).
- **Separate tracks by query type.** Natural language, name, type pattern
  (Loogle syntax), proof state, multi-premise and agent-issued queries rank
  systems differently. Tuning for one can hurt another
  ([bench-legendre-leaderboard](bench-legendre-leaderboard.md),
  [tool-loogle](tool-loogle.md)). Report each track separately, never one
  blended score.
- **Watch for the keyword shortcut.** Queries built from statements or
  docstrings often contain the target's own name parts, and more than half of
  SWE-bench Lite issues name the file to fix
  ([code-swe-bench-localization](code-swe-bench-localization.md)).
  - Measure word overlap between each query and its target after splitting
    snake_case, CamelCase and namespaces.
  - Put high-overlap queries in their own bucket, and add rephrased variants
    that avoid the target's name parts
    ([eval-embedding-domain-benchmarks](eval-embedding-domain-benchmarks.md)).
- **Robustness.** Write 3–5 paraphrases per target and report the worst case
  (Robustness@k)
  ([eval-embedding-critiques-and-robustness](eval-embedding-critiques-and-robustness.md)).
  Add a hard set of near-identical distractors that differ in a hypothesis, a
  direction or a type class ([code-newer-retrieval-benchmarks](code-newer-retrieval-benchmarks.md)).
- **Hidden intent note.** Each query gets a short narrative for judges only,
  describing the need and what counts as relevant
  ([math-arqmath](math-arqmath.md)).

### 3. Relevance labels

- **Graded, several correct answers.** A single gold answer marks equivalent
  lemmas, `_left`/`_right` variants and more general lemmas as wrong. Use a
  0–3 scale with Lean anchors:
  - 3: this is the declaration.
  - 2: usable with trivial glue.
  - 1: related and could help.
  - 0: irrelevant.

  Group aliases and deprecated names before judging
  ([math-arqmath](math-arqmath.md), [code-cosqa](code-cosqa.md)).
- **Pool across every engine.** Judge the union of the top 10–20 results from
  every system, including BM25, name-match and grep baselines. Drawing
  candidates only from BM25 or name matching biases the benchmark against
  semantic engines ([math-bright-theoremqa](math-bright-theoremqa.md)).
  - Report the unjudged share of each engine's top 10. On TREC-COVID, judging
    the missing results raised one system's nDCG@10 from 0.654 to 0.735
    ([embed-beir](embed-beir.md),
    [ir-trec-pooling-and-relevance-judgments](ir-trec-pooling-and-relevance-judgments.md)).
- **Treat "used in a proof" as a silver label.** Proof dependencies miss valid
  alternatives, and one study found only 48% of labels taken from source text
  appear in the elaborated proof term
  ([paper-cslib-premise-bench](paper-cslib-premise-bench.md)). Use them for
  scale and for known-item metrics, not as the headline judgments.
- **Measure agreement.** Human agreement on math relevance is low: κ 0.24–0.56
  in ARQMath and NTCIR, yet system rankings stay stable. Double-judge 15–20% of
  pairs and report κ on both the graded and the binary labels
  ([eval-stats-judgment-reliability-and-llm-assessors](eval-stats-judgment-reliability-and-llm-assessors.md)).
- **Use LLM judges only as helpers.** UMBRELA's system rankings match human
  ones closely (τ 0.87–0.94). But when the systems under test use the judge
  model, agreement on the top systems turns negative (τ −0.40).
  - Validate the judge against the double-judged set before using it.
  - Use a different model family from every engine's reranker.
  - Randomise the order results are shown in. LeanSearch v2 measured a 0.4–0.6
    rank bias toward whichever engine was shown first
    ([bench-leanexplore-llm-judge-eval](bench-leanexplore-llm-judge-eval.md)).
  - Keep a human-only holdout for final claims.
- **Lean can verify some answers mechanically.** For goal-shaped queries,
  `exact`/`apply`/`rw` succeeding with the returned lemma is a check that code
  search can only approximate with tests
  ([code-search-evaluation-methodology](code-search-evaluation-methodology.md)).

### 4. Leakage, snapshots and splits

- **Pin one corpus.** Engines index different Mathlib versions. Pin a Mathlib
  commit, record which gold answers each engine actually contains, and report
  results both on the subset every engine indexes and on the full set. Count a
  missing target separately from a retrieval miss
  ([bench-legendre-leaderboard](bench-legendre-leaderboard.md),
  [paper-leansearch-v2](paper-leansearch-v2.md)).
- **Split by time.** Random splits inflated Rango's results by 15–43%
  ([paper-rango-coq](paper-rango-coq.md)). The clean control is queries whose
  targets entered Mathlib after every engine's index date and after the models'
  training cutoffs. Libraries outside Mathlib (CSLib, miniCTX-v2) also work
  ([paper-premise-retrieval-model-tao](paper-premise-retrieval-model-tao.md),
  [paper-leanhammer-leanpremise](paper-leanhammer-leanpremise.md)).
- **Keep a private test set.** Teams tuning against NTCIR-11's live
  leaderboard gained 50% or more MRR ([math-ntcir-math](math-ntcir-math.md)),
  and RTEB pulled its private-set leaderboard after a vendor helped build the
  data ([embed-mteb](embed-mteb.md)). Tune only on a dev split, hold out a test
  split, publish only aggregate test scores, and refresh the test split over
  time.
- **Disclose training exposure.** Each system gets a card recording whether it
  was fine-tuned on Mathlib, overlaps our queries, or is unknown. Report
  in-domain and zero-shot results separately
  ([eval-embedding-reporting-protocols](eval-embedding-reporting-protocols.md)).

### 5. Metrics

- **Primary metric:** nDCG@10 on graded judgments.
- **Alongside it:**
  - MRR@10 and Success@k for known-item and name queries.
  - Recall@K curves for K in {1, 5, 10, 25, 50, 100, 1000}, marking each
    engine's real rerank depth (25 for LeanExplore).
  - Group recall and Full@k for multi-premise queries
    ([eval-embedding-first-stage-metrics](eval-embedding-first-stage-metrics.md),
    [math-naturalproofs](math-naturalproofs.md)).
- **Unranked tools.** Loogle and `#find` return sets, not rankings. Report
  hit rate, recall and result-set size, or fix a deterministic tie-break before
  computing rank metrics ([tool-loogle](tool-loogle.md)).
- **Result caps.** Engines that cap results (LeanSearch v2 returns at most 50)
  get "undefined" for metrics beyond the cap, not zero.
- **Unjudged results.** Report nDCG′ (unjudged results removed) as a
  sensitivity check. One math search system scored P@10 of 0.285, 0.405 or
  0.785 depending on how unjudged results were treated
  ([math-arqmath](math-arqmath.md)).

### 6. Evaluate each stage and the whole system

- **Full-retrieval track:** each engine as shipped, at a pinned version.
- **Fixed-candidate rerank track:** every reranker reorders the same published
  top-100 lists from at least three first stages:
  - BM25;
  - a dense retriever;
  - LeanExplore's fused list with its reranker off.

  Report results per first stage, never averaged, next to each stage's Recall@K
  ceiling and an oracle rerank that perfectly sorts the candidates.
  - Reranker gains shrink sharply over strong first stages: 30–55% over BM25,
    against 2–20% over a strong retriever.
  - Sweep rerank depth from 10 to 1000, since reranking more candidates hurts
    in about half of published settings
    ([eval-reranker-fixed-candidate-protocol](eval-reranker-fixed-candidate-protocol.md),
    [eval-reranker-proposed-protocol](eval-reranker-proposed-protocol.md)).
- **Component ablations:** retrieve-only vs retrieve+rerank, and removing each
  fusion component in turn ([ir-hybrid-fusion-rrf](ir-hybrid-fusion-rrf.md)).
- **Embedding model track:** exact search at full precision. Separately, report
  the loss from an approximate index against exact search, and how scores fall
  as vectors are truncated or quantized. Measure on retrieval, not sentence
  similarity; retrieval degrades much faster
  ([eval-embedding-efficiency-tradeoffs](eval-embedding-efficiency-tradeoffs.md)).
- **Agent track:** the same agent, model and budget, varying only the search
  tools:
  - no search;
  - grep or local name search;
  - Loogle;
  - each semantic engine;
  - a gold-premises ceiling.

  Measure task success, tool calls, tokens, and whether the correct lemma was
  ever shown to the agent. Recall gains become much smaller proving gains
  (LeanDojo: about +3–4 Pass@1). Use Mathlib-heavy targets, since
  competition-style problems barely need the library
  ([paper-leandojo-reprover](paper-leandojo-reprover.md),
  [code-agent-retrieval-evals](code-agent-retrieval-evals.md)).
- **Cost columns:** p50/p95 latency with the hardware stated, index size, and
  LLM calls and tokens per query. Keep engines that put an LLM in the query
  loop (LeanDex rewriting, LeanSearch reasoning mode) in their own class
  ([ir-industry-online-evaluation](ir-industry-online-evaluation.md),
  [engine-leandex](engine-leandex.md)).

### 7. Statistics

From [eval-stats-reporting-and-reproducibility](eval-stats-reporting-and-reproducibility.md)
and the other `eval-stats-` notes:

1. **Pre-register** the query set (with a hash), the primary metric
   (nDCG@10), α = 0.05, and the smallest difference worth detecting
   (proposed: 0.05).
2. **Query count.** Run a pilot of about 50 judged queries to measure how much
   per-query differences between engines vary. No Lean benchmark reports this.
   The planning figure is about 300 queries, with 60–100 per query type.
   Results within a single query type are descriptive only. Success@k needs
   3–5× more queries than graded nDCG to detect the same difference.
3. **Tests.** Use a paired t-test, confirmed by a paired permutation test with
   at least 10,000 permutations.
   - For all-pairs comparisons, use randomised Tukey HSD, implemented ourselves:
     ranx's `"tukey"` ignores that engines answer the same queries.
   - Use Holm correction when comparing only against one reference engine.
   - Do not use Wilcoxon or sign tests.
4. **Effect sizes.** Report each engine's mean with a 95% bootstrap CI over
   queries, and each pair's absolute difference with a CI. Never report a
   relative "% improvement" alone.
5. **LLM-judge noise.** Report run-to-run judge spread separately from query
   uncertainty. LeanExplore's published ± SE is judge noise, not query
   uncertainty.
6. **Stopping rule.** Never keep adding queries until a difference becomes
   significant.

### 8. Reproducibility

- Pin engine versions, index snapshot dates, the Mathlib commit, models,
  prompts and truncation lengths.
- Cache and publish raw engine responses, since hosted APIs drift.
- Publish runs in TREC format together with the judgments and per-query
  scores.
- Use the BEIR/MTEB format so existing tools can run the benchmark.
- Emit strictly decreasing scores. trec_eval breaks score ties by document ID
  and silently reorders runs that don't
  ([eval-reranker-tooling](eval-reranker-tooling.md)).
- Self-host engines where possible. LeanExplore's hosted API allows 30
  requests/min, Loogle's public endpoint is throttled, and LeanStateSearch was
  unreachable on 2026-09-28 ([engine-lean-lsp-mcp](engine-lean-lsp-mcp.md)).
- This benchmark is being built by LeanExplore's author. Say so, publish the
  code, and apply every rule above to LeanExplore first.

### Found along the way: LeanExplore's reranker prompt

`src/lean_explore/util/reranker_client.py` in lean-explore passes
Qwen3-Reranker a bare `<Instruct>/<Query>/<Document>` string and scores the
`"true"`/`"false"` tokens. The model card uses a chat template with a system
prompt and scores `"yes"`/`"no"`. The embedder also uses the generic
web-search instruction rather than a Lean-specific one. General rerankers
already *lowered* scores on math retrieval in BRIGHT and MIRB. The first
ablation should therefore compare retrieve-only, the current reranker, and a
correctly prompted reranker
([embed-benchmark-lessons](embed-benchmark-lessons.md)).

## Index

### Lean search benchmarks and leaderboards
- [bench-legendre-leaderboard](bench-legendre-leaderboard.md): independent leaderboard, 13 systems on MathlibQR
- [bench-mathlibqr](bench-mathlibqr.md): 200 declarations × up to 6 phrasings; single gold answer
- [bench-mathlibmpr](bench-mathlibmpr.md): 69 theorems with groups of interchangeable premises
- [bench-leansearch-v1-benchmark](bench-leansearch-v1-benchmark.md): 50 queries, graded pooled labels
- [bench-lean-finder-eval](bench-lean-finder-eval.md): Lean Finder test sets and user study
- [bench-leanexplore-llm-judge-eval](bench-leanexplore-llm-judge-eval.md): LeanExplore paper's LLM-judge protocol
- [bench-mathleap-meld-blueprints](bench-mathleap-meld-blueprints.md): MELD and the Blueprints set
- [bench-leandojo-premise-retrieval](bench-leandojo-premise-retrieval.md): LeanDojo Benchmark 4 as a search eval
- MIRB, seen three ways: [bench-mirb](bench-mirb.md) (Lean parts), [embed-mirb](embed-mirb.md) (as an embedding benchmark), [math-mirb](math-mirb.md) (non-Lean parts)

### Lean search engines
- [engine-leanexplore](engine-leanexplore.md), [engine-leansearch](engine-leansearch.md), [engine-lean-finder](engine-lean-finder.md), [engine-leandex](engine-leandex.md), [engine-octo-search](engine-octo-search.md), [engine-lightweight-llm-free-search](engine-lightweight-llm-free-search.md), [engine-moogle](engine-moogle.md) (defunct)
- How engines are reached: [engine-leansearchclient](engine-leansearchclient.md) / [tool-leansearchclient](tool-leansearchclient.md), [engine-lean-lsp-mcp](engine-lean-lsp-mcp.md) / [tool-lean-lsp-mcp](tool-lean-lsp-mcp.md)

### Name, pattern and in-editor tools (baselines)
- [tool-loogle](tool-loogle.md), [tool-mathlib-find](tool-mathlib-find.md), [tool-doc-gen4-search](tool-doc-gen4-search.md), [tool-lean-check-and-completion](tool-lean-check-and-completion.md)
- [tool-exact-apply](tool-exact-apply.md), [tool-rw-search](tool-rw-search.md), [tool-hint](tool-hint.md), [tool-lean-state-search](tool-lean-state-search.md), [tool-lean-library-suggestions](tool-lean-library-suggestions.md)

### Premise selection and retrieval-augmented proving
- Lean: [paper-leandojo-reprover](paper-leandojo-reprover.md), [paper-lean-copilot](paper-lean-copilot.md), [paper-leanagent](paper-leanagent.md), [paper-leanhammer-leanpremise](paper-leanhammer-leanpremise.md), [paper-piotrowski-ml-premise-selection-lean](paper-piotrowski-ml-premise-selection-lean.md), [paper-graph-augmented-premise-selection-lean](paper-graph-augmented-premise-selection-lean.md), [paper-premise-retrieval-model-tao](paper-premise-retrieval-model-tao.md), [paper-cslib-premise-bench](paper-cslib-premise-bench.md), [paper-theoremgraph](paper-theoremgraph.md), [paper-leansearch-v2](paper-leansearch-v2.md), [paper-real-prover](paper-real-prover.md)
- Agents and provers: [paper-agents-with-search-tools](paper-agents-with-search-tools.md), [paper-frontier-provers-retrieval-usage](paper-frontier-provers-retrieval-usage.md), [paper-retrieval-augmented-autoformalization](paper-retrieval-augmented-autoformalization.md)
- Other systems: [paper-magnushammer](paper-magnushammer.md) (Isabelle), [paper-rango-coq](paper-rango-coq.md) (Coq)

### Math information retrieval outside Lean
- Evaluation campaigns: [math-arqmath](math-arqmath.md), [math-ntcir-math](math-ntcir-math.md), [math-saber-math](math-saber-math.md)
- Datasets: [math-naturalproofs](math-naturalproofs.md), [math-bright-theoremqa](math-bright-theoremqa.md), [math-mse-duplicate-detection](math-mse-duplicate-detection.md), [math-informal-formal-alignment](math-informal-formal-alignment.md)
- Engines and other proof assistants: [math-formula-search-engines](math-formula-search-engines.md), [math-isabelle-search](math-isabelle-search.md), [math-coq-rocq-search](math-coq-rocq-search.md), [math-hol-premise-selection](math-hol-premise-selection.md), [math-metamath-mizar-agda](math-metamath-mizar-agda.md)

### General IR evaluation
- [ir-trec-pooling-and-relevance-judgments](ir-trec-pooling-and-relevance-judgments.md), [ir-offline-metrics-and-significance-testing](ir-offline-metrics-and-significance-testing.md), [ir-msmarco-trecdl-beir-benchmarks](ir-msmarco-trecdl-beir-benchmarks.md), [ir-retrieval-models-evaluation-practices](ir-retrieval-models-evaluation-practices.md)
- [ir-hybrid-fusion-rrf](ir-hybrid-fusion-rrf.md), [ir-ann-vector-search-benchmarks](ir-ann-vector-search-benchmarks.md), [ir-industry-online-evaluation](ir-industry-online-evaluation.md), [ir-twitter-the-algorithm](ir-twitter-the-algorithm.md)

### Statistics of evaluation
- [eval-stats-significance-tests-and-multiple-comparisons](eval-stats-significance-tests-and-multiple-comparisons.md), [eval-stats-effect-sizes-power-and-topic-set-size](eval-stats-effect-sizes-power-and-topic-set-size.md), [eval-stats-judgment-reliability-and-llm-assessors](eval-stats-judgment-reliability-and-llm-assessors.md), [eval-stats-metric-scales-and-correlation](eval-stats-metric-scales-and-correlation.md), [eval-stats-reporting-and-reproducibility](eval-stats-reporting-and-reproducibility.md)

### Embedding model evaluation
- Benchmarks: [embed-mteb](embed-mteb.md), [embed-beir](embed-beir.md), [embed-bright](embed-bright.md), [embed-coir](embed-coir.md), [embed-benchmark-lessons](embed-benchmark-lessons.md)
- Methodology: [eval-embedding-reporting-protocols](eval-embedding-reporting-protocols.md), [eval-embedding-first-stage-metrics](eval-embedding-first-stage-metrics.md), [eval-embedding-efficiency-tradeoffs](eval-embedding-efficiency-tradeoffs.md), [eval-embedding-critiques-and-robustness](eval-embedding-critiques-and-robustness.md), [eval-embedding-domain-benchmarks](eval-embedding-domain-benchmarks.md)

### Reranker evaluation
- [eval-reranker-fixed-candidate-protocol](eval-reranker-fixed-candidate-protocol.md), [eval-reranker-llm-order-cost-contamination](eval-reranker-llm-order-cost-contamination.md), [eval-reranker-model-card-reporting](eval-reranker-model-card-reporting.md), [eval-reranker-tooling](eval-reranker-tooling.md), [eval-reranker-proposed-protocol](eval-reranker-proposed-protocol.md)

### Code search
- Benchmarks: [code-codesearchnet](code-codesearchnet.md), [code-cosqa](code-cosqa.md), [code-coir](code-coir.md), [code-coderag-bench](code-coderag-bench.md), [code-swe-bench-localization](code-swe-bench-localization.md), [code-repo-completion-retrieval](code-repo-completion-retrieval.md), [code-newer-retrieval-benchmarks](code-newer-retrieval-benchmarks.md)
- Agents and production: [code-agent-retrieval-evals](code-agent-retrieval-evals.md), [code-embedding-vs-grep-evidence](code-embedding-vs-grep-evidence.md), [code-production-search-engines](code-production-search-engines.md)
- Synthesis: [code-search-evaluation-methodology](code-search-evaluation-methodology.md)
