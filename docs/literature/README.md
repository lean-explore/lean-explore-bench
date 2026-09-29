# Literature review: how to benchmark search

This folder holds one note per system, benchmark, paper or methodology topic,
grouped into topic subfolders (listed in the index below),
collected while working out how to benchmark Lean 4 search engines well. Notes
on a single system follow [`_TEMPLATE.md`](_TEMPLATE.md); cluster and synthesis
notes are organised by topic and cite inline. Every note links a source for every claim,
and marks anything that could not be checked as *(unverified)*. Research was
done on 2026-09-28; hosted services and leaderboards change, so check dates
before relying on a number.

The first half of this file distils the notes into a working guide. The second
half is an index.

## How to benchmark search well

### 1. What already exists, and the gap

- Every Lean search comparison run by an engine's own authors on their own
  query set favours that engine
  ([lean-engines/leanexplore](lean-engines/leanexplore.md),
  [lean-engines/lean-finder](lean-engines/lean-finder.md),
  [premise-selection/leansearch-v2](premise-selection/leansearch-v2.md)). The
  one comparison by an outside team on another team's queries, TheoremGraph on
  MathlibQR, did not beat LeanSearch v2 (nDCG@10 0.558 vs 0.623)
  ([premise-selection/theoremgraph](premise-selection/theoremgraph.md)).
- The only independent comparison is the
  [Legendre leaderboard](lean-benchmarks/legendre-leaderboard.md): 13 systems on
  [MathlibQR](lean-benchmarks/mathlibqr.md), with a pinned corpus and bootstrap CIs, but
  no published code. The top three are statistically tied at 72.6–74.4% R@10.
  LeanExplore is 8th (R@10 56.5%, nDCG@10 0.385).
- Existing Lean sets are small (50–200 targets), mostly synthetic or written
  by an engine team, and mostly allow one correct answer per query
  ([lean-benchmarks/mathlibqr](lean-benchmarks/mathlibqr.md),
  [lean-benchmarks/leansearch-v1-benchmark](lean-benchmarks/leansearch-v1-benchmark.md),
  [lean-benchmarks/mathlibmpr](lean-benchmarks/mathlibmpr.md)).
- No published numbers exist for Loogle, `exact?`/`apply?`, `rw?`, `#find` or
  doc-gen4 search ([lean-tools/loogle](lean-tools/loogle.md),
  [lean-tools/exact-apply](lean-tools/exact-apply.md),
  [lean-tools/symbolic-baselines](lean-tools/symbolic-baselines.md)).
- Only LeanSearch v2's Prove task compares retrievers inside one fixed proving
  loop, and Lean Finder swaps retrievers inside REAL-Prover. No paper compares
  search engines as tools an agent calls itself under one fixed loop, in Lean
  or in code search, and none includes LeanExplore
  ([premise-selection/agents-with-search-tools](premise-selection/agents-with-search-tools.md),
  [code-search/embedding-vs-grep-evidence](code-search/embedding-vs-grep-evidence.md)).

The gap is a neutral, reproducible, multi-track benchmark with open code. It
should have graded, pooled judgments and enough queries to separate engines.

### 2. Queries: where they come from and what shape they take

- **Match real use.** Models trained on docstring-like text did worse on real
  search-engine queries, and simple lexical baselines held up
  ([code-search/codesearchnet](code-search/codesearchnet.md)). Mix query sources and tag each
  query by source:
  - Agent traces: queries an agent issued while proving, labelled by the lemmas
    the finished proof used.
  - Real human queries, for example Zulip "is there a lemma for…" threads.
  - Expert-written queries.
  - LLM-generated queries.
- **Free seed set.** Mathlib's `docs/100.yaml`, `docs/1000.yaml`,
  `overview.yaml`, `undergrad.yaml` and `@[stacks]` tags hold roughly 1,600
  informal entries before deduplication: about 290 famous theorems, 950
  concepts and 370 distinct Stacks tags. Counted as links to declarations this
  is about 1,900, and the 1000-theorem list contains the 100-theorem list
  ([math-ir/informal-formal-alignment](math-ir/informal-formal-alignment.md)).
- **Separate tracks by query type.** Natural language, name, type pattern
  (Loogle syntax), proof state, multi-premise and agent-issued queries rank
  systems differently. Tuning for one can hurt another
  ([lean-benchmarks/legendre-leaderboard](lean-benchmarks/legendre-leaderboard.md),
  [lean-tools/loogle](lean-tools/loogle.md)). Report each track separately, never one
  blended score.
- **Watch for the keyword shortcut.** Queries built from statements or
  docstrings often contain the target's own name parts, and more than half of
  SWE-bench Lite issues mention a file, class or function name
  ([code-search/swe-bench-localization](code-search/swe-bench-localization.md)).
  - Measure word overlap between each query and its target after splitting
    snake_case, CamelCase and namespaces.
  - Put high-overlap queries in their own bucket, and add rephrased variants
    that avoid the target's name parts
    ([embedding-evaluation/domain-benchmarks](embedding-evaluation/domain-benchmarks.md)).
- **Robustness.** Write 3–5 paraphrases per target and report the worst case
  (Robustness@k)
  ([embedding-evaluation/critiques-and-robustness](embedding-evaluation/critiques-and-robustness.md)).
  Add a hard set of near-identical distractors that differ in a hypothesis, a
  direction or a type class ([code-search/newer-retrieval-benchmarks](code-search/newer-retrieval-benchmarks.md)).
- **Hidden intent note.** Each query gets a short narrative for judges only,
  describing the need and what counts as relevant
  ([math-ir/arqmath](math-ir/arqmath.md)).
- **Sample the way users actually search.** Logs are heavy-tailed: in math web
  search about 90% of distinct queries occur once, so frequency buckets
  collapse. Stratify by query form × intent × client instead. Log-based
  collections usually draw a traffic-weighted sample for the headline number
  and over-sample rare forms (goals, partial names) as reweighted strata, as
  Baidu-ULTR did. We instead use the log only to find categories and weight
  them equally (§2b). Every filter (difficulty, frequency band, privacy threshold)
  moves the set away from real traffic, so document each one
  ([test-collection-construction/query-logs-characterisation-and-sampling](test-collection-construction/query-logs-characterisation-and-sampling.md)).
- **Estimate the intent mix from logs, not surveys.** Surveys and forums skew
  it badly: in Broder's study sexual queries were under 1% of survey answers but
  about 12% of the log. Label intent multi-label, since about a quarter of
  queries are ambiguous
  ([test-collection-construction/query-logs-intent-taxonomies](test-collection-construction/query-logs-intent-taxonomies.md)).
- **Treat agents and humans as separate populations.** Agent queries run 7.6–12.7
  terms, against about 2 in classic web and code search logs, come in bursts of 2–4+, repeat themselves, and
  draw about half their new words from earlier results. Sample whole agent
  searches, deduplicate loops, and score at the fixed k agents request
  ([test-collection-construction/query-logs-agent-vs-human-queries](test-collection-construction/query-logs-agent-vs-human-queries.md)).
- **Publicly released query sets look easier than real traffic.** Any
  privacy threshold drops the rare tail, where engines do worst. Pair a public
  set with a held-out set that keeps the tail
  ([test-collection-construction/query-logs-privacy-and-release](test-collection-construction/query-logs-privacy-and-release.md)).

### 2a. Synthetic queries: generate, then validate against real ones

Most of the benchmark will likely be LLM-generated, which works only under
conditions:

- **Synthetic sets reproduce engine *rankings*, not scores.** Fully synthetic
  collections ranked 31 TREC systems with Kendall's τ ≈ 0.86 against human
  ones, but systems of every type scored higher on synthetic queries. Report rankings and
  differences, not absolute numbers
  ([test-collection-construction/synthetic-test-collections](test-collection-construction/synthetic-test-collections.md)).
- **Never label only the source declaration as correct.** That design dropped
  τ to 0.157; pool and grade instead (same note).
- **Humans filter first.** TREC kept only 31 of 97 generated queries after
  expert review. Do not filter with a retriever or reranker (the InPars /
  Promptagator training filters), since that favours similar engines
  ([test-collection-construction/synthetic-query-generation-and-simulation](test-collection-construction/synthetic-query-generation-and-simulation.md)).
- **Same-model bias is real.** A Gemini judge scored a Gemini reranker above a
  perfect ordering built from human labels (0.961 vs 0.876; humans gave 0.747
  vs 0.892) ([test-collection-construction/synthetic-test-collections](test-collection-construction/synthetic-test-collections.md)). LeanExplore's index text is
  written by Gemini and LeanSearch v2's by Qwen3, so pick query generators and
  judges from other families, or use two of each and report per family.
- **Validate on a small human anchor set.** Tune the generator until engine
  rankings on synthetic queries match rankings on real queries for the same
  targets. TREC's tip-of-the-tongue track did this, reaching τ = 0.847 between
  forum and synthetic queries (0.737 against NIST-written queries). A role-play prompt with MUST/COULD rules, a
  summary of the target, low temperature, and rejecting any query that leaks
  the name were what worked
  ([test-collection-construction/known-item-trec-tot](test-collection-construction/known-item-trec-tot.md),
  [test-collection-construction/known-item-tot-query-simulation](test-collection-construction/known-item-tot-query-simulation.md)).
  - Size: statistical correction (prediction-powered inference) gave valid
    intervals from about 30 human-labelled queries for one system's score;
    comparing engines needs more (about 150 labelled items in ARES). Plan on
    50–80 human-judged queries plus 30 real Zulip questions, frozen and private
    ([test-collection-construction/synthetic-validation-budget-and-protocol](test-collection-construction/synthetic-validation-budget-and-protocol.md)).
  - Include oracle and deliberately degraded runs in the validation pool; they
    expose judge bias and keep τ from being inflated by easy comparisons.
  - Re-validate whenever the generator, judge, Mathlib snapshot or engine set
    changes.

### 2b. Building categories from our own logs

Our plan: use LeanExplore's de-identified query log to *discover* query
categories, then write 60–100 synthetic queries per category and report each
category separately. **Categories come from the log; benchmark weights do
not.** Copying log shares would let one heavy API client set the benchmark.

- **Privacy constraints come first.** Our Privacy Policy forbids publishing
  real queries or sending them to external LLM APIs. So the code is public, runs
  on the server next to the data, and tests against a generated dummy log.
  - Embeddings, cluster assignments and centroids never leave the server.
    Embeddings can be inverted back to text.
  - Only aggregate tables (cells ≥ 10), reviewed category descriptions and
    synthetic queries may leave. Synthetic queries are generated from
    descriptions, never from real queries in the prompt, and are checked for
    overlap with the log before release
  ([test-collection-construction/query-logs-private-analysis-pipeline](test-collection-construction/query-logs-private-analysis-pipeline.md)).
- **Deduplicate first.** Collapse exact and near-duplicate queries (MinHash,
  edit similarity > 0.8) within each source and day, and work on distinct
  queries. This absorbs agent bursts, which make up most of today's log.
- **Split by form with rules, then cluster within each form.**
  - Regexes sort queries into proof state, type pattern, exact name, fuzzy
    name, LaTeX/Unicode and natural language. Check them on 200 hand-labelled
    queries.
  - Within each form, embed with a local Qwen3-Embedding model and cluster
    two ways: UMAP → HDBSCAN, and agglomerative clustering for a hierarchy.
    Over-cluster; merging is cheap
  ([test-collection-construction/query-clustering-embeddings](test-collection-construction/query-clustering-embeddings.md)).
- **Name and organise categories with a local LLM.** Use TnT-LLM-style
  taxonomy generation and Clio-style facet clustering, run several times, and
  keep categories that recur. Don't prune by traffic share, since that removes
  the rare but distinct types we want
  ([test-collection-construction/query-logs-llm-taxonomy-induction](test-collection-construction/query-logs-llm-taxonomy-induction.md)).
- **Validate without labels.**
  - Internal indices (silhouette, DBCV) only to compare runs, against a
    shuffled-embedding null.
  - Bootstrap stability: a cluster becomes a category only at Hennig Jaccard
    ≥ 0.75.
  - Intrusion tests and two annotators on about 15 queries per category
    (Krippendorff α ≥ 0.667).
  - Usefulness: categories should differ in zero-result rate or in how
    engines rank on them; merge categories that rank engines identically.
  - UMAP plots are for private exploration only; never read distances or
    cluster sizes from them
  ([test-collection-construction/query-clustering-validation-and-visualization](test-collection-construction/query-clustering-validation-and-visualization.md)).
- **Floors and freezing.** A candidate category needs at least 5 distinct
  queries over at least 2 days to be kept for generation. That is separate from
  the publication floor of 10 per cell. Freeze the category granularity before
  scoring any engine, because splitting a category doubles its weight in an
  equal-weight average.
- **Validate the pipeline on a planted log** with known categories, including
  rare ones at about 1%, before trusting it on real data.

### 3. Relevance labels

- **Graded, several correct answers.** A single gold answer marks equivalent
  lemmas, `_left`/`_right` variants and more general lemmas as wrong. Use a
  0–3 scale with Lean anchors:
  - 3: this is the declaration.
  - 2: usable with trivial glue.
  - 1: related and could help.
  - 0: irrelevant.

  Group aliases and deprecated names before judging
  ([math-ir/arqmath](math-ir/arqmath.md), [code-search/cosqa](code-search/cosqa.md)).
- **Pool across every engine.** Judge the union of the top 10–20 results from
  every system, including BM25, name-match and grep baselines. Drawing
  candidates only from BM25 or name matching biases the benchmark against
  semantic engines ([embedding-evaluation/bright](embedding-evaluation/bright.md)).
  - Report the unjudged share of each engine's top 10. On TREC-COVID, judging
    the missing results raised one system's nDCG@10 from 0.654 to 0.735
    ([embedding-evaluation/beir](embedding-evaluation/beir.md),
    [ir-evaluation/trec-pooling-and-relevance-judgments](ir-evaluation/trec-pooling-and-relevance-judgments.md)).
- **Treat "used in a proof" as a silver label.** Proof dependencies miss valid
  alternatives, and one study found only 48% of labels taken from source text
  appear in the elaborated proof term (on a 300-task audit subset)
  ([premise-selection/cslib-premise-bench](premise-selection/cslib-premise-bench.md)). Use them for
  scale and for known-item metrics, not as the headline judgments.
- **Measure agreement.** Human agreement on math relevance is low: κ 0.24–0.69
  in ARQMath and NTCIR, yet system rankings stay stable. Double-judge 15–20% of
  pairs and report κ on both the graded and the binary labels
  ([math-ir/arqmath](math-ir/arqmath.md), [math-ir/ntcir-math](math-ir/ntcir-math.md),
  [statistics/judgment-reliability-and-llm-assessors](statistics/judgment-reliability-and-llm-assessors.md)).
- **Use LLM judges only as helpers.** UMBRELA's system rankings match human
  ones closely (τ 0.87–0.94). But when the systems under test use the judge
  model, agreement on the top systems turns negative (τ −0.40).
  - Validate the judge against the double-judged set before using it.
  - Use a different model family from every engine's reranker.
  - Randomise the order results are shown in. LeanSearch v2 measured a 0.4–0.6
    rank bias toward whichever engine was shown first
    ([lean-benchmarks/mathlibqr](lean-benchmarks/mathlibqr.md),
    [premise-selection/leansearch-v2](premise-selection/leansearch-v2.md)).
  - Keep a human-only holdout for final claims.
- **Lean can verify some answers mechanically.** For goal-shaped queries,
  `exact`/`apply`/`rw` succeeding with the returned lemma is a check that code
  search can only approximate with tests
  ([code-search/search-evaluation-methodology](code-search/search-evaluation-methodology.md)).

### 4. Leakage, snapshots and splits

- **Pin one corpus.** Engines index different Mathlib versions. Pin a Mathlib
  commit, record which gold answers each engine actually contains, and report
  results both on the subset every engine indexes and on the full set. Count a
  missing target separately from a retrieval miss
  ([lean-benchmarks/legendre-leaderboard](lean-benchmarks/legendre-leaderboard.md),
  [premise-selection/leansearch-v2](premise-selection/leansearch-v2.md)).
- **Split by time.** Random splits inflated Rango's results by 15%, and by 43%
  for its no-retrieval ablation
  ([premise-selection/rango-coq](premise-selection/rango-coq.md)). The clean control is queries whose
  targets entered Mathlib after every engine's index date and after the models'
  training cutoffs. Libraries outside Mathlib (CSLib, miniCTX-v2) also work
  ([premise-selection/premise-retrieval-model-tao](premise-selection/premise-retrieval-model-tao.md),
  [premise-selection/leanhammer-leanpremise](premise-selection/leanhammer-leanpremise.md)).
- **Keep a private test set.** Teams tuning against NTCIR-11's live
  leaderboard gained 50% or more MRR ([math-ir/ntcir-math](math-ir/ntcir-math.md)),
  and RTEB pulled its private-set leaderboard after a vendor helped build the
  data ([embedding-evaluation/mteb](embedding-evaluation/mteb.md)). Tune only on a dev split, hold out a test
  split, publish only aggregate test scores, and refresh the test split over
  time.
- **Disclose training exposure.** Each system gets a card recording whether it
  was fine-tuned on Mathlib, overlaps our queries, or is unknown. Report
  in-domain and zero-shot results separately
  ([embedding-evaluation/reporting-protocols](embedding-evaluation/reporting-protocols.md)).

### 5. Metrics

- **Primary metric:** nDCG@10 on graded judgments.
- **Alongside it:**
  - MRR@10 and Success@k for known-item and name queries.
  - Recall@K curves for K in {1, 5, 10, 25, 50, 100, 1000}, marking each
    engine's real rerank depth (25 for LeanExplore).
  - Group recall and Full@k for multi-premise queries
    ([embedding-evaluation/first-stage-metrics](embedding-evaluation/first-stage-metrics.md),
    [math-ir/naturalproofs](math-ir/naturalproofs.md)).
- **Unranked tools.** Loogle and `#find` return sets, not rankings. Report
  hit rate, recall and result-set size, or fix a deterministic tie-break before
  computing rank metrics ([lean-tools/loogle](lean-tools/loogle.md)).
- **Result caps.** Engines that cap results (LeanSearch v2 returns at most 50)
  get "undefined" for metrics beyond the cap, not zero.
- **Unjudged results.** Report nDCG′ (unjudged results removed) as a
  sensitivity check. On NTCIR-12 formula search, Approach0 scored P@10 of
  0.285, 0.405 or 0.785 depending on how unjudged results were treated
  ([math-ir/ntcir-math](math-ir/ntcir-math.md)).

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
  - Sweep rerank depth from 10 to 1000, since reranking more candidates hurt
    in about half of the settings in one study (Drowning in Documents)
    ([reranker-evaluation/fixed-candidate-protocol](reranker-evaluation/fixed-candidate-protocol.md),
    [reranker-evaluation/proposed-protocol](reranker-evaluation/proposed-protocol.md)).
- **Component ablations:** retrieve-only vs retrieve+rerank, and removing each
  fusion component in turn ([ir-evaluation/hybrid-fusion-rrf](ir-evaluation/hybrid-fusion-rrf.md)).
- **Embedding model track:** exact search at full precision. Separately, report
  the loss from an approximate index against exact search, and how scores fall
  as vectors are truncated or quantized. Measure on retrieval, not sentence
  similarity; retrieval degrades much faster
  ([embedding-evaluation/efficiency-tradeoffs](embedding-evaluation/efficiency-tradeoffs.md)).
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
  ([premise-selection/leandojo-reprover](premise-selection/leandojo-reprover.md),
  [code-search/agent-retrieval-evals](code-search/agent-retrieval-evals.md)).
- **Cost columns:** p50/p95 latency with the hardware stated, index size, and
  LLM calls and tokens per query. Keep engines that put an LLM in the query
  loop (LeanDex rewriting, LeanSearch reasoning mode) in their own class
  ([ir-evaluation/industry-online-evaluation](ir-evaluation/industry-online-evaluation.md),
  [lean-engines/leandex](lean-engines/leandex.md)).

### 6a. Specialised tracks

- **Tip of the tongue ("I know it exists but not its name").** One gold
  declaration plus its accepted equivalents (aliases, deprecated names, the
  `iff`/`symm` twin), scored mainly by MRR@10 with Success@1/5/10. Collect real
  queries from Zulip threads where the asker confirmed the answer, and keep
  "partial name recall" queries as their own stratum
  ([test-collection-construction/known-item-tot-datasets-and-metrics](test-collection-construction/known-item-tot-datasets-and-metrics.md)).
- **No answer ("the lemma doesn't exist").** No Lean search benchmark tests
  this, yet invented names are 7.7% of proof failures in one study. Build
  queries from names agents actually invented, real lemmas altered so they
  become false, and results missing at the pinned commit, each with a recorded
  plausible wrong answer. Score by how well an engine's top-1 confidence
  separates answerable from unanswerable queries (AUROC, risk–coverage), and
  keep these queries out of the main nDCG/MRR averages, where they score 0 for
  everyone. Keep easy off-topic controls separate: pooled with natural cases
  they made abstention look useful
  ([test-collection-construction/no-answer-lean-formal-evidence](test-collection-construction/no-answer-lean-formal-evidence.md),
  [test-collection-construction/no-answer-retrieval-qpp-and-truncation](test-collection-construction/no-answer-retrieval-qpp-and-truncation.md)).
- **Type pattern (Loogle-style).** Give each query two labels: "matches the
  pattern" (Loogle is perfect on this by construction) and "is the lemma the
  user wanted". Group queries by the flexibility needed (reordered hypotheses,
  currying, generalisation, swapped sides). Mine queries from `exact foo` /
  `apply foo` steps in Mathlib proofs, and keep a regression tier of
  Hoogle-style assertions ("top hit", "in top k", "must not appear", "known
  failure") ([code-search/type-directed-api-search](code-search/type-directed-api-search.md),
  [code-search/type-directed-synthesis-user-studies](code-search/type-directed-synthesis-user-studies.md)).
- **Cross-formality (optional).** Informal theorem engines (TheoremSearch,
  Matlas) cannot be scored against Mathlib answers, except TheoremSearch's
  formal endpoint. A separate track with targets that exist both in Mathlib and
  informally (Stacks tags, 100/1000-theorems) could compare them, scoring
  coverage separately from ranking
  ([lean-engines/informal-theoremsearch](lean-engines/informal-theoremsearch.md),
  [lean-engines/informal-matlas](lean-engines/informal-matlas.md)).
- **Live services:** query one request at a time with retries (parallel runs
  gave spurious empty results on both informal engines), save every raw
  response with a timestamp, and score only from the saved copy
  ([lean-engines/informal-other-engines](lean-engines/informal-other-engines.md)).

### 7. Statistics

From [statistics/reporting-and-reproducibility](statistics/reporting-and-reproducibility.md)
and the other notes in `statistics/`:

1. **Pre-register** the query set (with a hash), the primary metric
   (nDCG@10), α = 0.05, and the smallest difference worth detecting
   (proposed: 0.05).
2. **Query count.** Run a pilot of about 50 judged queries to measure how much
   per-query differences between engines vary. No Lean benchmark reports this.
   The planning figure is about 300 queries, with 60–100 per query type.
   Results within a single query type are descriptive only. By our own power
   calculation (assumed variances, not a published result), Success@k needs
   about 3–7× more queries than graded nDCG to detect the same difference.
3. **Tests.** Use a paired t-test, confirmed by a paired permutation test with
   at least 10,000 permutations.
   - For all-pairs comparisons, use randomised Tukey HSD, implemented ourselves:
     ranx's `"tukey"` ignores that engines answer the same queries.
   - Use Holm correction when comparing only against one reference engine.
   - Avoid Wilcoxon and sign tests. Most studies advise against them for IR,
     though Parapar 2020 and Otero 2025 recommend Wilcoxon.
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
  ([reranker-evaluation/tooling](reranker-evaluation/tooling.md)).
- Self-host engines where possible. LeanExplore's hosted API allows 30
  requests/min ([lean-engines/leanexplore](lean-engines/leanexplore.md)),
  lean-lsp-mcp throttles its own Loogle calls to 3 per 30 s, and LeanStateSearch
  was unreachable on 2026-09-28 ([lean-tools/lean-lsp-mcp](lean-tools/lean-lsp-mcp.md),
  [lean-tools/loogle](lean-tools/loogle.md)).
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
([embedding-evaluation/benchmark-lessons](embedding-evaluation/benchmark-lessons.md)).

## Index

### Lean search benchmarks and leaderboards (`lean-benchmarks/`)

- [lean-benchmarks/lean-finder-eval](lean-benchmarks/lean-finder-eval.md): Lean Finder evaluation sets and user study
- [lean-benchmarks/leanexplore-llm-judge-eval](lean-benchmarks/leanexplore-llm-judge-eval.md): LeanExplore paper evaluation (LLM-as-judge, 300 queries)
- [lean-benchmarks/leansearch-v1-benchmark](lean-benchmarks/leansearch-v1-benchmark.md): Mathlib4 Semantic Search Benchmark (LeanSearch v1)
- [lean-benchmarks/legendre-leaderboard](lean-benchmarks/legendre-leaderboard.md): Legendre Leaderboard
- [lean-benchmarks/mathleap-meld-blueprints](lean-benchmarks/mathleap-meld-blueprints.md): MathLeap evaluation sets: MELD and the Blueprints retrieval set
- [lean-benchmarks/mathlibmpr](lean-benchmarks/mathlibmpr.md): MathlibMPR (global premise retrieval benchmark)
- [lean-benchmarks/mathlibqr](lean-benchmarks/mathlibqr.md): MathlibQR (LeanSearch v2 theorem-search benchmark)
- [lean-benchmarks/mirb](lean-benchmarks/mirb.md): MIRB: Mathematical Information Retrieval Benchmark

### Lean search engines (and informal theorem search engines) (`lean-engines/`)

- [lean-engines/informal-mathlas-mcp](lean-engines/informal-mathlas-mcp.md): mathlas (community MCP server, Krishi Attri), local informal theorem search plus a Loogle/LeanSearch proxy
- [lean-engines/informal-matlas](lean-engines/informal-matlas.md): Matlas (PKU BICMR AI4M / FrenzyMath), informal statement search over journals and textbooks
- [lean-engines/informal-other-engines](lean-engines/informal-other-engines.md): Other informal and cross-formality search services (zbMATH Open, Stacks/ProofWiki, formula engines, LLM web search), plus the protocols that evaluated them
- [lean-engines/informal-theoremsearch](lean-engines/informal-theoremsearch.md): TheoremSearch (UW Math AI Lab), informal theorem search with a formal side-index
- [lean-engines/lean-finder](lean-engines/lean-finder.md): Lean Finder
- [lean-engines/leandex](lean-engines/leandex.md): LeanDex (Project Numina)
- [lean-engines/leanexplore](lean-engines/leanexplore.md): LeanExplore
- [lean-engines/leansearch](lean-engines/leansearch.md): LeanSearch (v1, 2024; v2, 2026)
- [lean-engines/lightweight-llm-free-search](lean-engines/lightweight-llm-free-search.md): Towards Lightweight and LLM-Free Semantic Search for mathlib4 (Isaac Li)
- [lean-engines/octo-search](lean-engines/octo-search.md): Axiomatic Octo Search

### Name, pattern and in-editor tools (baselines) (`lean-tools/`)

- [lean-tools/exact-apply](lean-tools/exact-apply.md): `exact?` / `apply?` (library search tactics, formerly `library_search`)
- [lean-tools/lean-library-suggestions](lean-tools/lean-library-suggestions.md): Lean core library suggestions (`suggestions`, `set_library_suggestions`, `grind +suggestions`)
- [lean-tools/lean-lsp-mcp](lean-tools/lean-lsp-mcp.md): lean-lsp-mcp search tools (MCP bundle for agents)
- [lean-tools/lean-state-search](lean-tools/lean-state-search.md): LeanStateSearch (premise-search.com)
- [lean-tools/leansearchclient](lean-tools/leansearchclient.md): LeanSearchClient (`#search`, `#leansearch`, `#loogle`, `#statesearch` in Lean)
- [lean-tools/loogle](lean-tools/loogle.md): Loogle
- [lean-tools/symbolic-baselines](lean-tools/symbolic-baselines.md): Small symbolic baselines: `#check` and completion, doc-gen4 search, `#find`, `rw?`, `hint`

### Premise selection and retrieval-augmented proving (`premise-selection/`)

- [premise-selection/agents-with-search-tools](premise-selection/agents-with-search-tools.md): Do search tools help LLM agents write Lean? (cluster: Hilbert, Awakening the Sleeping Agent, Lean Finder RAG, Ax-Prover, Numina-Lean-Agent, Archon)
- [premise-selection/cslib-premise-bench](premise-selection/cslib-premise-bench.md): CSLibPremiseBench: Structure-Guided Premise Retrieval and Label Robustness for Lean 4 Computer-Science Theorems (Ji)
- [premise-selection/leandojo-reprover](premise-selection/leandojo-reprover.md): LeanDojo / ReProver (LeanDojo Benchmark, LeanDojo Benchmark 4)
- [premise-selection/leanhammer-leanpremise](premise-selection/leanhammer-leanpremise.md): Premise Selection for a Lean Hammer (LeanPremise + LeanHammer)
- [premise-selection/leansearch-v2](premise-selection/leansearch-v2.md): LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving (and LeanSearch v1 benchmark)
- [premise-selection/magnushammer](premise-selection/magnushammer.md): Magnushammer: A Transformer-Based Approach to Premise Selection
- [premise-selection/other-papers](premise-selection/other-papers.md): Other Lean premise-selection papers: Lean Copilot, LeanAgent, graph-augmented ReProver
- [premise-selection/piotrowski-ml-premise-selection-lean](premise-selection/piotrowski-ml-premise-selection-lean.md): Machine-Learned Premise Selection for Lean (Piotrowski, Fernández Mir, Ayers)
- [premise-selection/premise-retrieval-model-tao](premise-selection/premise-retrieval-model-tao.md): Learning an Effective Premise Retrieval Model for Efficient Mathematical Formalization (Tao, Liu, Wang, Xu)
- [premise-selection/rango-coq](premise-selection/rango-coq.md): Rango: Adaptive Retrieval-Augmented Proving (Coq) and the CoqStoq dataset
- [premise-selection/real-prover](premise-selection/real-prover.md): REAL-Prover: Retrieval Augmented Lean Prover (LeanSearch-PS)
- [premise-selection/retrieval-augmented-autoformalization](premise-selection/retrieval-augmented-autoformalization.md): Retrieval-augmented autoformalization (MS-RAG, RAutoformalizer, DRIFT, DDR)
- [premise-selection/theoremgraph](premise-selection/theoremgraph.md): TheoremGraph: Bridging Formal and Informal Mathematics (Kurgan, Wang, Leonen, et al.)

### Building test collections: queries, known-item search, synthetic data, no-answer queries (`test-collection-construction/`)

- [test-collection-construction/known-item-tot-datasets-and-metrics](test-collection-construction/known-item-tot-datasets-and-metrics.md): Tip-of-the-tongue query analysis, ToT datasets, and known-item metrics
- [test-collection-construction/known-item-tot-query-simulation](test-collection-construction/known-item-tot-query-simulation.md): Simulating known-item and tip-of-the-tongue queries, and validating the simulation
- [test-collection-construction/known-item-trec-tot](test-collection-construction/known-item-trec-tot.md): TREC Tip-of-the-Tongue (ToT) track, 2023–2025
- [test-collection-construction/no-answer-lean-formal-evidence](test-collection-construction/no-answer-lean-formal-evidence.md): "The lemma doesn't exist": evidence from Lean / formal-math work, and a proposed no-answer track
- [test-collection-construction/no-answer-qa-rag-abstention](test-collection-construction/no-answer-qa-rag-abstention.md): Unanswerable queries in QA and RAG evaluation (SQuAD 2.0, RGB, NoMIRACL, CRAG, UAEval4RAG, AbstentionBench, selective QA)
- [test-collection-construction/no-answer-retrieval-qpp-and-truncation](test-collection-construction/no-answer-retrieval-qpp-and-truncation.md): "Nothing relevant here" on the retrieval side: empty relevance sets, ranked-list truncation, and query performance prediction (QPP) evaluation
- [test-collection-construction/query-clustering-embeddings](test-collection-construction/query-clustering-embeddings.md): Clustering search queries in embedding space: short-text clustering, topic-model pipelines, intent discovery and rule-based query-form baselines
- [test-collection-construction/query-clustering-validation-and-visualization](test-collection-construction/query-clustering-validation-and-visualization.md): Validating query clusters without labels (internal indices, stability, intrusion tests, agreement) and visualising them safely
- [test-collection-construction/query-logs-agent-vs-human-queries](test-collection-construction/query-logs-agent-vs-human-queries.md): Agent-issued vs human-issued queries: what 2025–2026 log studies show (synthesis)
- [test-collection-construction/query-logs-characterisation-and-sampling](test-collection-construction/query-logs-characterisation-and-sampling.md): Query-log characterisation and how test collections sample queries from logs (synthesis)
- [test-collection-construction/query-logs-intent-taxonomies](test-collection-construction/query-logs-intent-taxonomies.md): Query intent taxonomies: web search, code search and math search (synthesis)
- [test-collection-construction/query-logs-llm-taxonomy-induction](test-collection-construction/query-logs-llm-taxonomy-induction.md): Inducing a query taxonomy from a log with LLMs and classifying the log at scale (TnT-LLM, Clio, GoalEx, TopicGPT)
- [test-collection-construction/query-logs-private-analysis-pipeline](test-collection-construction/query-logs-private-analysis-pipeline.md): Which artefacts of a query-log analysis can leak real queries (embeddings, labels, synthetic text, small counts) and how to gate them
- [test-collection-construction/query-logs-privacy-and-release](test-collection-construction/query-logs-privacy-and-release.md): Releasing query logs privately: AOL, k-anonymity thresholds, differential privacy, synthetic queries
- [test-collection-construction/synthetic-query-generation-and-simulation](test-collection-construction/synthetic-query-generation-and-simulation.md): Synthetic queries: training-time generators (InPars, Promptagator, GPL), query simulation, and LLM query variants
- [test-collection-construction/synthetic-test-collections](test-collection-construction/synthetic-test-collections.md): Synthetic test collections: LLM-written queries and LLM labels (Rahmani et al. SIGIR 2024, SynDL, and the bias evidence)
- [test-collection-construction/synthetic-validation-budget-and-protocol](test-collection-construction/synthetic-validation-budget-and-protocol.md): Validating synthetic queries and labels: how much human data, which checks, and a protocol for Lean search

### Math information retrieval outside Lean (`math-ir/`)

- [math-ir/arqmath](math-ir/arqmath.md): ARQMath (CLEF 2020-2022): Answer Retrieval for Questions on Math
- [math-ir/informal-formal-alignment](math-ir/informal-formal-alignment.md): Informal↔formal alignment resources (100 theorems, 1000+ theorems, Mathlib doc maps, Stacks tags, concept alignment, MMA)
- [math-ir/naturalproofs](math-ir/naturalproofs.md): NaturalProofs (and ProofWiki premise selection)
- [math-ir/ntcir-math](math-ir/ntcir-math.md): NTCIR Math tasks: NTCIR-10 Math Pilot, NTCIR-11 Math-2, NTCIR-12 MathIR
- [math-ir/other-proof-assistants](math-ir/other-proof-assistants.md): Search and premise selection in other proof assistants (Isabelle, Coq/Rocq, HOL Light/HOL4, Metamath, Mizar, Agda)
- [math-ir/saber-math](math-ir/saber-math.md): SABER-Math

### General IR evaluation (`ir-evaluation/`)

- [ir-evaluation/hybrid-fusion-rrf](ir-evaluation/hybrid-fusion-rrf.md): Hybrid lexical + semantic fusion: RRF and convex combination, and how they were evaluated
- [ir-evaluation/industry-online-evaluation](ir-evaluation/industry-online-evaluation.md): Industry search evaluation: offline vs online, A/B tests, interleaving, clicks, latency
- [ir-evaluation/msmarco-trecdl-beir-benchmarks](ir-evaluation/msmarco-trecdl-beir-benchmarks.md): MS MARCO, TREC Deep Learning, BEIR: how the standard IR benchmarks are constructed
- [ir-evaluation/offline-metrics-and-significance-testing](ir-evaluation/offline-metrics-and-significance-testing.md): Offline ranking metrics and significance testing for IR
- [ir-evaluation/trec-pooling-and-relevance-judgments](ir-evaluation/trec-pooling-and-relevance-judgments.md): TREC-style judged relevance sets: pooling, incompleteness, sparse labels, LLM assessors
- [ir-evaluation/twitter-the-algorithm](ir-evaluation/twitter-the-algorithm.md): Twitter/X open-sourced ranking and search code (the-algorithm, the-algorithm-ml, x-algorithm)

### Statistics of evaluation (`statistics/`)

- [statistics/effect-sizes-power-and-topic-set-size](statistics/effect-sizes-power-and-topic-set-size.md): Effect sizes, confidence intervals, statistical power and topic-set size in IR
- [statistics/judgment-reliability-and-llm-assessors](statistics/judgment-reliability-and-llm-assessors.md): Reliability of relevance judgments: assessor disagreement, incompleteness, LLM assessors
- [statistics/metric-scales-and-correlation](statistics/metric-scales-and-correlation.md): Metric properties: measurement scales, metric sensitivity, and ranking correlation
- [statistics/reporting-and-reproducibility](statistics/reporting-and-reproducibility.md): Reporting standards, reproducibility, and a statistical protocol for lean-explore-bench
- [statistics/significance-tests-and-multiple-comparisons](statistics/significance-tests-and-multiple-comparisons.md): Significance tests and multiple-comparison corrections for IR evaluation

### Embedding model evaluation (`embedding-evaluation/`)

- [embedding-evaluation/beir](embedding-evaluation/beir.md): BEIR (Benchmarking IR)
- [embedding-evaluation/benchmark-lessons](embedding-evaluation/benchmark-lessons.md): Embedding / reranker benchmarks: lessons for lean-explore-bench
- [embedding-evaluation/bright](embedding-evaluation/bright.md): BRIGHT (reasoning-intensive retrieval)
- [embedding-evaluation/critiques-and-robustness](embedding-evaluation/critiques-and-robustness.md): Critiques of embedding evaluation: leaderboard overfitting, static-benchmark saturation, instruction and paraphrase sensitivity, representational limits
- [embedding-evaluation/domain-benchmarks](embedding-evaluation/domain-benchmarks.md): Domain-specific embedding evaluations: how CoIR (code), BRIGHT (reasoning/math), LitSearch and SciRepEval (science) build queries and labels
- [embedding-evaluation/efficiency-tradeoffs](embedding-evaluation/efficiency-tradeoffs.md): Evaluating embeddings under efficiency constraints: Matryoshka truncation, quantization, exact vs ANN indexes
- [embedding-evaluation/first-stage-metrics](embedding-evaluation/first-stage-metrics.md): Metrics for the first-stage (embedding) retriever: Recall@K as a ceiling, nDCG@10, MRR@10
- [embedding-evaluation/mteb](embedding-evaluation/mteb.md): MTEB / MMTEB / RTEB (Massive Text Embedding Benchmark family)
- [embedding-evaluation/reporting-protocols](embedding-evaluation/reporting-protocols.md): How embedding-model papers report evaluation (E5, BGE, GTE, E5-mistral, NV-Embed, Gemini Embedding, Qwen3-Embedding)

### Reranker evaluation (`reranker-evaluation/`)

- [reranker-evaluation/fixed-candidate-protocol](reranker-evaluation/fixed-candidate-protocol.md): Reranker evaluation: the fixed-candidate protocol, first-stage dependence and rerank depth
- [reranker-evaluation/llm-order-cost-contamination](reranker-evaluation/llm-order-cost-contamination.md): LLM reranker evaluation: order sensitivity, nondeterminism, cost reporting and contamination
- [reranker-evaluation/proposed-protocol](reranker-evaluation/proposed-protocol.md): Proposed protocol: evaluating the reranking stage in lean-explore-bench
- [reranker-evaluation/tooling](reranker-evaluation/tooling.md): Reranker evaluation tooling: trec_eval, ir-measures, ranx, ir_datasets, Pyserini, RankLLM, rerankers

### Code search (`code-search/`)

- [code-search/agent-retrieval-evals](code-search/agent-retrieval-evals.md): Evaluating retrieval inside coding agents (SWE-Explore, Agent Retrieval Bench, semantic vs. deep agentic search on SWE-QA, RepoQA)
- [code-search/coderag-bench](code-search/coderag-bench.md): CodeRAG-Bench
- [code-search/codesearchnet](code-search/codesearchnet.md): CodeSearchNet (Corpus, Challenge) and CodeXGLUE AdvTest
- [code-search/coir](code-search/coir.md): CoIR (Code Information Retrieval Benchmark)
- [code-search/cosqa](code-search/cosqa.md): CoSQA, CodeXGLUE WebQueryTest, and CoSQA+
- [code-search/embedding-vs-grep-evidence](code-search/embedding-vs-grep-evidence.md): Embeddings vs. agentic grep in production coding tools: what vendors report and how they evaluated it
- [code-search/newer-retrieval-benchmarks](code-search/newer-retrieval-benchmarks.md): Newer (2025–2026) code retrieval benchmarks: ExecRetrieval, FreshStack, RepoAlign-Bench, MM-IssueLoc, AlgoSimBench
- [code-search/search-evaluation-methodology](code-search/search-evaluation-methodology.md): How code search is evaluated: query sources, relevance, metrics, leakage (cross-cutting synthesis)
- [code-search/swe-bench-localization](code-search/swe-bench-localization.md): SWE-bench-derived code localization evals (SWE-bench retrieval, Loc-Bench, SweRank/SweLoc, KA-LogicQuery)
- [code-search/type-directed-api-search](code-search/type-directed-api-search.md): Type-directed and signature-based API search outside Lean (and how it was evaluated)
- [code-search/type-directed-synthesis-user-studies](code-search/type-directed-synthesis-user-studies.md): Type-directed synthesis and composition search: benchmarks and user studies (Hoogle+, TyGAR, Hoogle⋆, Prospector, PARSEWeb, InSynth, Perelman et al.)
