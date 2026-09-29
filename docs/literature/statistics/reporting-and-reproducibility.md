# Reporting standards, reproducibility, and a statistical protocol for lean-explore-bench

- **Kind:** evaluation methodology (reporting) plus the synthesised protocol
- **Links:** see Sources
- **Authors / org, date:** Armstrong et al. (2009), Breuer et al. (2020), SIGIR reproducibility track (2022–), ranx and ir_measures (2022)
- **Status:** tooling is mature and maintained. ranx, ir_measures and repro_eval all had GitHub activity between 2025 and 2026, checked via the GitHub API on 2026-09-28.

## What goes wrong without reporting standards

- **Weak baselines.** Armstrong, Moffat, Webber & Zobel (CIKM 2009) found little evidence of real ad-hoc retrieval improvement since 1998. Baselines were "generally weak, often below the median original TREC system", and papers only compared against their own runs ([ACM](https://dl.acm.org/doi/10.1145/1645953.1646031); via search summary). Lin (SIGIR Forum 2019) revisited the same problem for neural models ([ACM](https://dl.acm.org/doi/pdf/10.1145/3308774.3308781); via search summary).
- **Missing statistics.** Many SIGIR and TOIS papers omit p-values or test statistics, so nobody can run a power analysis afterwards ([Sakai 2016](https://dl.acm.org/doi/10.1145/2911451.2911492)).
- **Unverifiable claims.** Fuhr's "Thou shalt not forget about reproducibility" covers the same ground as the ACM artifact badges and the SIGIR reproducibility track ([Fuhr 2017](http://sigir.org/wp-content/uploads/2018/01/p032.pdf)).

## Community mechanisms

- **SIGIR reproducibility track.**
  - It wants papers that "repeat, reproduce, generalize, and analyze prior work". It prefers reproducibility (different team, different setup) over replicability (different team, same setup).
  - Authors must state "the assumptions of the original work that they found to hold up, and the ones that could not be confirmed", and must provide "a comprehensive online appendix, with code, data, and clear instructions" ([SIGIR 2022 CFP](https://sigir.org/sigir2022/call-for-reproducibility-track-papers/)).
- **ACM artifact badges at SIGIR.** Three badges: Artifacts Available, Artifacts Evaluated and Results Reproduced ([SIGIR badging](https://sigir.org/general-information/acm-sigir-artifact-badging/); via search summary).
- **Measuring reproduction.** Breuer, Ferro, Fuhr, Maistro, Sakai, Schaer & Soboroff (SIGIR 2020) propose measures at several levels, from ranked-list overlap to comparison of "effects and significant differences". They also release a reproducibility dataset ([arXiv:2010.13447](https://arxiv.org/abs/2010.13447)). The measures are implemented in `repro_eval` ([GitHub](https://github.com/irgroup/repro_eval)).

## Tooling

- **ir_measures** (MacAvaney, Macdonald & Ounis, ECIR 2022).
  - A single interface over pytrec_eval, gdeval, trectools and other backends, with standardised measure names ([arXiv:2111.13466](https://arxiv.org/abs/2111.13466)).
  - `ir_measures.iter_calc(...)` yields per-query values, for example `Metric(query_id='1', measure=nDCG@10, value=0.51)` ([docs](https://ir-measur.es/en/latest/getting-started.html)).
  - It has no statistical testing.
- **ranx** (Bassani, ECIR 2022) ([paper](https://link.springer.com/chapter/10.1007/978-3-030-99739-7_30), [source](https://github.com/AmenRa/ranx/blob/master/ranx/meta/compare.py)).
  - Numba-based. `compare()` exports LaTeX tables.
  - `stat_test` accepts `"student"` (default, paired t-test), `"fisher"` (randomization test) or `"tukey"`.
  - Defaults are `max_p=0.01` and `n_permutations=1000`.
  - **Caveats:**
    - ranx's Tukey calls `scipy.stats.tukey_hsd`. That is the unpaired one-way test, not the query-blocked randomised Tukey HSD the IR literature validates ([source](https://github.com/AmenRa/ranx/blob/master/ranx/statistical_tests/tukey_hsd_test.py)).
    - ranx applies no multiple-comparison correction to pairwise t or Fisher tests.
    - 1,000 permutations is too coarse for Holm-adjusted thresholds. At α/15 ≈ 0.0033 the resolution is 0.001.
- **trec_eval / Pyserini.** Already covered in `../ir-evaluation/offline-metrics-and-significance-testing.md`.

## Relevance to lean-explore-bench: recommended statistical protocol

This protocol synthesises the other `eval-stats-*` notes. Items marked (design choice) are our recommendation, not a literature result.

1. **Pre-register** (Fuhr §2.6). Commit these to the repo before running any engine:
   - The query set, with a hash.
   - Query-type labels.
   - The primary metric: nDCG@10 on 4-grade qrels.
   - The primary comparisons.
   - α = 0.05.
   - The minimum effect of interest: δ = 0.05 nDCG@10 (design choice).
2. **Query count.**
   - Pilot about 50 queries and estimate σ_d per engine pair. Size the main set with Sakai's ANOVA-based design, or with n ≈ 7.85·(σ_d/δ)², inflated for the correction.
   - Planning prior: **about 300 queries** total, at least 60–100 per query type (design choice). Rationale: under σ_d ≈ 0.25–0.30, detecting δ = 0.05 needs about 200–280 queries unadjusted; Webber et al. needed 164 for a 0.033 AP gap. Per-type results are descriptive unless each type is powered on its own.
   - Do not add queries iteratively until significance (Webber et al.).
3. **Judgments.**
   - Pool the top 10–20 results from *every* engine, including simple BM25 and name-match baselines.
   - Use the 4-grade Lean-anchored scale, with a written intent note per query.
   - Double-judge at least 15–20% of pairs by humans. Report Cohen's κ (4-grade and binary) and inter-annotator τ.
   - An LLM judge may extend coverage only after validation against the double-judged set: label κ relative to human–human κ, run-level τ and top-k τ, and preserved significant pairs.
   - The judge must not share a model family with any engine's reranker.
   - Keep a human-only holdout for final claims.
   - Publish Judged@10 per engine, plus condensed-list nDCG′ as a sensitivity analysis.
4. **Tests.**
   - Engine vs. reference engine: paired two-sided t-test on per-query nDCG@10. Confirm with a paired permutation test (≥10,000 permutations).
   - All pairs: randomised Tukey HSD (B ≥ 10,000), implemented ourselves or taken from Discpower, not ranx's Tukey.
   - If only m−1 comparisons against one reference are planned, use Holm instead.
   - No Wilcoxon or sign tests.
   - Secondary metrics (MRR@10, Success@k, Recall@k) are descriptive only, or tested with an additional correction across metrics.
5. **Effect sizes and CIs.** For each engine and each pair, report:
   - The mean with a 95% CI (bootstrap over queries, 10,000 resamples, or a t-interval).
   - The absolute Δ with a 95% CI.
   - A standardized effect Δ/σ_d, or Δ/√V_E from the two-way ANOVA.
   - Report two or three decimals, never four (Fuhr §2.3). Never report relative percentage improvement alone.
6. **Per-query and per-type reporting.**
   - Publish runs in TREC format, qrels, and per-query scores from `ir_measures.iter_calc`.
   - Show a per-query-type table and a per-query difference plot for key pairs, so readers can see where an engine wins.
7. **LLM-judge variance** (if a judge is used for any headline number). Run the judge at least 3 times. Report query-bootstrap CIs, which carry the claim, separately from judge-run spread, which is a nuisance diagnostic.
8. **Reproducibility.**
   - Pin engine versions, API endpoints, index snapshot dates and Mathlib commit.
   - Cache raw engine responses, because live engines drift.
   - Version the qrels.
   - Provide a one-command re-evaluation script.
   - Add fresh query batches periodically, report old and new batches separately, and treat the frozen public set as a development set once engines have tuned on it (Parry et al. "shelf life"; Fuhr on collection reuse).

## Open questions

- Should remote engines be queried once and cached, or several times to measure nondeterminism? Some engines use LLM query rewriting, and run-to-run variance could exceed small effects. A small repeat-query study during the pilot would answer this.

## Sources

- Armstrong et al., CIKM 2009: https://dl.acm.org/doi/10.1145/1645953.1646031 (via search summary)
- Lin, SIGIR Forum 2019: https://dl.acm.org/doi/pdf/10.1145/3308774.3308781 (via search summary)
- Sakai, SIGIR 2016: https://dl.acm.org/doi/10.1145/2911451.2911492
- Fuhr 2017: http://sigir.org/wp-content/uploads/2018/01/p032.pdf
- SIGIR 2022 reproducibility CFP: https://sigir.org/sigir2022/call-for-reproducibility-track-papers/
- SIGIR artifact badging: https://sigir.org/general-information/acm-sigir-artifact-badging/
- Breuer et al., SIGIR 2020: https://arxiv.org/abs/2010.13447 ; repro_eval: https://github.com/irgroup/repro_eval
- ir_measures: https://arxiv.org/abs/2111.13466 ; https://ir-measur.es/en/latest/getting-started.html
- ranx: https://link.springer.com/chapter/10.1007/978-3-030-99739-7_30 ; https://github.com/AmenRa/ranx
- Webber, Moffat, Zobel 2008: https://people.eng.unimelb.edu.au/jzobel/fulltext/cikm08.pdf
- Parry et al. 2025: https://arxiv.org/abs/2502.20937
- Other claims: see the sibling notes `significance-tests-and-multiple-comparisons.md`, `effect-sizes-power-and-topic-set-size.md`, `judgment-reliability-and-llm-assessors.md` and `metric-scales-and-correlation.md`.
