# Validating synthetic queries and labels: how much human data, which checks, and a protocol for Lean search

- **Kind:** evaluation methodology (synthesis + protocol)
- **Links:**
  - Oosterhuis, Jagerman, Qin, Wang, Bendersky, "Reliable Confidence Intervals for IR Evaluation Using Generative A.I.", KDD 2024: [arXiv:2407.02464](https://arxiv.org/abs/2407.02464)
  - Angelopoulos et al., "Prediction-Powered Inference", Science 2023: [arXiv:2301.09633](https://arxiv.org/abs/2301.09633), code [ppi_py](https://github.com/aangelopoulos/ppi_py)
  - Saad-Falcon, Khattab, Potts, Zaharia, "ARES", NAACL 2024: [arXiv:2311.09476](https://arxiv.org/abs/2311.09476)
  - Evidence notes this builds on: [synthetic-test-collections.md](synthetic-test-collections.md), [synthetic-query-generation-and-simulation.md](synthetic-query-generation-and-simulation.md)
- **Authors / org, date:** 2023–2024 (see links). The protocol section is this repo's proposal, not a published method.
- **Status:** the methods are published with code. The protocol is unvalidated.

## What it is

The practical question is how many human-labelled queries are needed before LLM-generated queries and labels can be trusted to rank Lean search engines. The literature gives three kinds of answer:

1. **Ranking-agreement studies.** These compare full system orderings between synthetic and human collections. They are informative but data-hungry, because τ needs many systems and many queries on both sides.
2. **Statistical correction.** PPI and conformal methods use a small human-labelled subset to put valid confidence intervals on LLM-label metrics.
3. **Judge-calibration budgets.** ARES reports a minimum human validation set below which its rankings stop being meaningful.

## How it works

### Prediction-powered inference and conformal risk control (Oosterhuis et al., KDD 2024)
- **PPI** combines LLM labels on all queries with a *rectifier*: the mean LLM-vs-human error on the n human-labelled queries. The result is a confidence interval that stays valid whatever the LLM's errors are ([arXiv:2301.09633](https://arxiv.org/abs/2301.09633), abstract). Oosterhuis et al. apply it to IR metrics. They also propose **CRC** (conformal risk control), which produces per-query and per-document intervals designed for ranking metrics ([arXiv:2407.02464](https://arxiv.org/abs/2407.02464), abstract).
- **Setup.** Flan-UL2 in scoring mode, no prompt engineering. TREC-DL 2019–2022 (stratified) and Robust04, each split 50:50 into calibration and test. The target is BM25's DCG@10 with 95% intervals over 500 runs (§7).
- **Results** (§8.1):
  - The empirical bootstrap on human labels alone needs at least 40 labelled queries for 95% coverage on TREC-DL, and still falls short with 100 on Robust04.
  - PPI needs fewer than 20 (TREC-DL) and fewer than 40 (Robust04). CRC needs fewer than 30 and fewer than 50, with the narrowest intervals.
  - The authors' summary: "both PPI and CRC require as few as 30 human-labeled queries to produce informative and reliable confidence intervals".
- **Robustness.** Coverage held under injected systematic LLM bias. Interval *width* grows as the LLM gets worse, so bad labels cost precision, not validity (§8).
- **Caveat for us.** The intervals are on *one system's* metric (BM25). Comparing engines needs intervals on *differences*, which PPI supports in principle (it covers means) but this paper does not test. The human set also has to be a random sample of the same query distribution, not hand-picked queries.

### ARES (NAACL 2024)
ARES uses PPI with a fine-tuned LM judge to rank RAG systems. Varying the human validation set from 25 to 400 datapoints, the authors found **about 150 is the minimum**: "below about 100–150 datapoints … ARES cannot meaningfully distinguish between the alternate RAG systems" ([arXiv:2311.09476](https://arxiv.org/abs/2311.09476) §5.1 and Table 3). A datapoint here is a labelled (query, passage, answer) item, not a query with full judgments. Their main experiments used 300 (§5.1).

### Ranking-agreement budgets seen in the synthetic-collection studies
| Study | Human reference used to validate | Systems | Reported agreement |
|---|---|---|---|
| Rahmani et al. 2024 | 51 real + 31 synthetic DL-23 queries, NIST-judged | 31 | τ = 0.8151 (syn. queries, human labels); 0.8568 (fully synthetic) ([synthetic-test-collections.md](synthetic-test-collections.md)) |
| SynDL 2025 | DL-19 human qrels (43 judged queries) | 37 | τ = 0.8571 nDCG@10 |
| AIR-Bench | Full MS MARCO dev vs generated G-MSMARCO | 17 | Spearman 0.8211; 2,000-query subsamples mean 0.8031 ([../embedding-evaluation/critiques-and-robustness.md](../embedding-evaluation/critiques-and-robustness.md)) |
| Balog et al. 2025 | DL-19/20 human qrels (43/54 queries) | 14 incl. 6 oracles | τ 0.03–0.14 all systems vs 0.60–0.87 oracles only ([synthetic-test-collections.md](synthetic-test-collections.md)) |

Two lessons:
- **The system set drives τ.** With the ~5–10 Lean engines that exist, a τ over engines alone is too coarse. Six engines give only 15 pairs, so one swap moves τ by about 0.13. Add controlled variants (ablations, oracles, degraded runs) and report *pairwise* agreement on significant differences, following Otero et al. and McKechnie et al. as summarised in [../statistics/judgment-reliability-and-llm-assessors.md](../statistics/judgment-reliability-and-llm-assessors.md).
- **Topic count still matters.** The synthetic set needs enough queries for the effect sizes of interest; see [../statistics/effect-sizes-power-and-topic-set-size.md](../statistics/effect-sizes-power-and-topic-set-size.md).

## Relevance to lean-explore-bench: a protocol for LLM-written Lean queries and labels

This is a proposal built from the evidence above. The numbers are starting points, not validated thresholds.

**0. Declare the LLM families up front.** For each engine, record which model families wrote its index text (e.g. Gemini informalizations for LeanExplore, Qwen3-32B for LeanSearch v2), its reranker, and its training queries (GPT-4o for Lean Finder). Sources: [../lean-engines/](../lean-engines/). Choose the query-generator family and the judge family so that neither matches any engine's families. If that is impossible, use two generators and two judges from different families and report results per family.

**1. Human anchor set (build first, freeze, keep private).**
- Draw ≥ 50 targets by *random* stratified sampling over Mathlib folders and declaration kinds. Random sampling is required for PPI to be valid.
- Have experts write queries without seeing any engine's output. MathlibQR's six-style scheme is a ready template ([../lean-benchmarks/mathlibqr.md](../lean-benchmarks/mathlibqr.md)). Also include ≥ 30 real questions from Zulip or GitHub as information-need seeds, since Lean Finder's real queries are unreleased.
- Pool the top 10 from every engine plus the oracle and baseline runs from step 4. Have humans grade the pool on a 3–4 level scale with written criteria, e.g. exact / more general / usable with glue / unrelated.
- This gives about 50–80 human-judged queries. That clears the ~20–50 queries PPI/CRC needed on TREC and gives a pairwise-label set in the low thousands, above ARES's ~150 datapoint floor.

**2. Generate queries.**
- Seed from both declarations (known-item) and real information needs (backstory-style, following Alaofi et al.). Write several variants per seed across styles.
- Prompt rules: no identifier names from the target, no copied hypothesis names, and state the need the way a user would.
- Filters that do not use any retriever:
  - A lexical-overlap cap against the target's name and docstring (LitSearch-style).
  - A dedup step.
  - An LLM or human answerability check: can the target plausibly serve this need?
- Do **not** use round-trip retrieval or reranker-score filtering (Promptagator / InPars-v2 style), because that selects for the filter's retriever family.
- Log the acceptance rate. TREC kept only 31 of 97 generated queries after expert review ([synthetic-test-collections.md](synthetic-test-collections.md)).

**3. Label by pooling, never by "source = only gold".**
- Pool the top 10 from all engines and runs. The judge (fixed model, prompt and temperature; one configuration for all systems) grades the whole pool.
- Seed-only labels collapsed to τ = 0.157 in Rahmani et al.
- Report Judged@10 per engine.

**4. Validation runs on the human anchor. The synthetic set is only reported if all checks pass.**
- **(a) Query realism** (Breuer / Kruff facets; [synthetic-query-generation-and-simulation.md](synthetic-query-generation-and-simulation.md)). For the same targets, compare synthetic and human queries on:
  - the per-query nDCG@10 distribution for each engine (KS test or RMSE)
  - SERP overlap (RBO) between human and synthetic queries
  - query-similarity and length statistics
  - variant diversity (pool growth per added variant)
- **(b) Label agreement.** Judge vs human on the anchor pools: weighted κ on graded labels and κ on binary labels, broken down per grade. This matters because GPT-4 matched humans on only 28% of "perfectly relevant" labels in Rahmani et al.
- **(c) Ranking agreement.** Kendall's τ and τ_AP between the engine-plus-variant orderings under human-query/human-label and synthetic-query/LLM-label conditions. Also report the fraction of human-significant pairs that are preserved, reversed or lost.
- **(d) Per-system bias test.** For each system s, compute Δs = score_syn(s) − score_human(s). A uniform shift is expected, since synthetic sets are easier. Regress Δ on family-overlap indicators (generator family = engine index family, judge family = engine reranker family). Flag any family effect whose 95% CI excludes 0.
- **(e) Oracle sanity.** Include a "gold-first" oracle run and swap-degraded oracles built from the human labels. If the LLM judge scores any LLM engine above the Perfect oracle, the judge has the Balog et al. bias. In that case use human labels or PPI-corrected scores for that comparison.

**5. Report.**
- Headline numbers come from the synthetic set with PPI-corrected CIs, using the human anchor as the rectifier. Show them as rankings plus CIs on differences, not as absolute scores.
- Publish the human anchor's own scores next to them.
- State the generator and judge models, prompts, acceptance rates, and the (a)–(e) results.

**6. Refresh.**
- Re-run step 4 on a small new human sample (≥ 20 queries) whenever the generator, judge, Mathlib snapshot or engine set changes.
- Rotate the private anchor so engines cannot tune on it.

## Open questions

- PPI intervals on *differences* between engines, under PPI's i.i.d. assumption, when the human anchor is small and stratified: needs a simulation on our own data.
- Is a ~50-query anchor enough to detect a family bias of a given size in step 4(d)? This needs a power analysis once the variance of Δs is known.
- Should a judge's access to Lean (type-checking, `#check`, dependency info) count as a different "family" for bias purposes?

## Sources

- Oosterhuis et al. 2024: https://arxiv.org/abs/2407.02464 (§§7–8)
- Angelopoulos et al. 2023: https://arxiv.org/abs/2301.09633 (abstract)
- ARES: https://arxiv.org/abs/2311.09476 (§5.1, Table 3)
- Figures in the budget table: see the sources of the two sibling notes and [../embedding-evaluation/critiques-and-robustness.md](../embedding-evaluation/critiques-and-robustness.md).
- The protocol is this repo's synthesis and is not a published or validated procedure.
