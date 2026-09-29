# Effect sizes, confidence intervals, statistical power and topic-set size in IR

- **Kind:** evaluation methodology (statistics)
- **Links:** see Sources
- **Authors / org, date:** Tague-Sutcliffe & Blustein (1995) to Sakai (2018)
- **Status:** mature theory. It is rarely applied in practice: many IR papers do not report the quantities needed for power analysis ([Sakai, SIGIR 2016](https://dl.acm.org/doi/10.1145/2911451.2911492)).

This note answers the open question left in `../ir-evaluation/offline-metrics-and-significance-testing.md`: *how many queries do we need?*

## What it is

- **Per-query variance dominates.**
  - Tague-Sutcliffe and Blustein's ANOVA of TREC-3 found that variation across topics is larger than variation across systems ([TREC-3 PDF](https://web.cs.dal.ca/~jamie/pubs/PDF/1995/TREC3/T-S+B_1995_TREC3%20(OCR).pdf); via search summary).
  - Banks, Over and Zhang's review of six analyses of TREC data likewise found that the topic factor is the largest effect, with a strong topic×system interaction ([NIST PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=151743); via search summary).
  - Consequences:
    - A mean over queries hides most of the signal.
    - Paired designs, where every engine runs on every query, matter a great deal.
    - The quantity that drives power is σ_d, the standard deviation of *per-query differences* between two systems. It is not the variance of either system's own scores.
- **Error rate vs. topic-set size.**
  - Voorhees & Buckley (SIGIR 2002) derived empirical "error rates" (swap rates): the likelihood "that a different set of topics of the same size would lead to a different conclusion". They computed them directly up to 25 topics and extrapolated beyond. "The error rates found are larger than anticipated" ([NIST abstract](https://www.nist.gov/publications/effect-topic-set-size-retrieval-experiment-error)).
  - Buckley & Voorhees (SIGIR 2000) found that P@30 has about twice the error rate of AP, so the choice of measure changes how many topics are needed ([ACM](https://dl.acm.org/doi/10.1145/345508.345543); via search summary).
  - Voorhees's "Topic set size redux" (SIGIR 2009) used real 50-topic sets and found that statistically significant differences "can be wrong, even when accompanied by moderately large (>10%) relative differences" ([ACM](https://dl.acm.org/doi/10.1145/1571941.1572138); via search summary).
- **Discriminative power.** Sakai (SIGIR 2006) defines it as the proportion of system pairs found significantly different at a given α, estimated with bootstrap tests. It is the standard way to compare how *sensitive* metrics are ([search summary of Sakai 2006](https://www.semanticscholar.org/paper/575a33aa00b7be4c63d5e6b455a6726e84d3f4d4); definition restated in [Sakai & Kando 2008](https://doi.org/10.1007/s10791-008-9059-7)).

## Power analysis: Webber, Moffat & Zobel (CIKM 2008)

Source: [PDF](https://people.eng.unimelb.edu.au/jzobel/fulltext/cikm08.pdf).

- **Definition.** Power is "the number of topics that are likely to be sufficient to detect a certain degree of superiority of one system over another". Estimating it requires "the variability ... of between-system score deltas".
- **Worked example (TREC Robust, AP).**
  - The standard deviation of per-topic AP deltas is about 0.15.
  - The target difference is 0.033, the gap between a typical top-quartile and a typical second-quartile system.
  - Detecting it with power 0.8 "requires 164 topics", so "the traditional 50-topic TREC collection is inadequate".
  - Using the 95th-percentile σ of 0.19 raises this to 262 topics.
- **Estimating σ.** Past experience and trial experiments both leave wide bounds. Designs ended up with "almost twice as many topics ... as will on average prove necessary".
- **Iterative designs are biased.** Adding topics until significance is reached "leads to a subtle bias towards overestimating both power and statistical significance". The authors propose a hybrid method and say what must be declared when reporting it.
- **Many shallow queries beat few deep ones.** "Greater statistical power is achieved for the same relevance assessment effort by evaluating a large number of topics shallowly than a small number deeply."
  - This qualifies the "few deeply judged queries" advice in `../ir-evaluation/trec-pooling-and-relevance-judgments.md`. Deep judging buys reusability and recall estimation. Many queries buy power.

## Topic-set-size design: Sakai (Information Retrieval Journal 2016; book 2018)

- **Approach.** Uses Nagata's sample-size design with three variants: the paired t-test, one-way ANOVA, and confidence-interval width. Inputs are α, β, a minimum detectable difference, and a variance estimate taken "from topic-by-run score matrices from past test collections" ([abstract via Semantic Scholar](https://doi.org/10.1007/s10791-015-9273-z)).
- **Measures differ a lot.** Because "different evaluation measures can have vastly different within-system variances, they require substantially different topic set sizes under the same set of statistical requirements". Pool depth can be traded against topic count in advance (same source).
- **Which variant to use.** The t-test-based results match ANOVA with m = 2, and the CI-based results match ANOVA with m = 10. Sakai therefore recommends the ANOVA-based tool in either case. Excel tools (`samplesizeTTEST.xlsx`, `samplesizeANOVA.xlsx`, `samplesizeCI.xlsx`) and R power-analysis case studies accompany the book ([Springer](https://springer.com/gp/book/9789811311987); tool names and recommendation via search summary).

## Effect sizes and confidence intervals

- **Fuhr (2017).** "Thou shalt not ignore effect sizes."
  - With enough data, almost any modification becomes significant.
  - Report differences in interpretable units: for P@10, 0.02 is "one more relevant document per five queries".
  - Standardize with Δ = (μ1 − μ2)/σ.
  - Fuhr also asks for confidence intervals rather than four-decimal point estimates. A 50-query P@10 of 0.7 has a binomial 95% CI of about [0.658, 0.739], and the true interval is wider because only 50 queries are independent. Bootstrap methods are suggested ([PDF](http://sigir.org/wp-content/uploads/2018/01/p032.pdf), §2.3 and §2.8).
- **Sakai (2020).**
  - Prefers standardized mean differences (Hedges' g, Glass's Δ) to relative improvements.
  - In multi-system settings, computes effect size as Δ/√V_E, where V_E is the two-way ANOVA residual variance. For example, nDCG vs. ERR agreement rates differ by 0.45 of a common standard deviation ([PDF](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf), Table 1 and §2.8).
- **Large samples.** Once samples reach thousands of queries, "most tests would have a 100% chance of finding statistically significant results. Therefore, the effect size should be used" ([Ihemelandu & Ekstrand 2023](https://arxiv.org/abs/2305.02461)).

## Illustrative sample sizes (computed here, not from the literature)

**Formula.** The normal approximation for a two-sided paired test at power 0.8 is n ≈ ((z₁₋α/₂ + z₀.₈)·σ_d/δ)².
- It reproduces Webber et al.'s example: σ_d = 0.15 and δ = 0.033 give 163 queries, against their 164.
- Bonferroni-style α/k is used as a worst case for k = 15 pairs (6 engines, all pairs).

**σ_d values are assumptions.** They must be replaced with estimates from a pilot.

| σ_d of per-query nDCG@10 diff | δ = 0.03 | δ = 0.05 | δ = 0.10 | δ = 0.05, α/15 |
|---|---|---|---|---|
| 0.20 | 349 | 126 | 32 | 229 |
| 0.25 | 546 | 197 | 50 | 357 |
| 0.30 | 785 | 283 | 71 | 514 |

**Binary metrics need far more queries.** For a binary per-query metric such as Success@k or Recall@1, each per-query difference is −1, 0 or +1. If a fraction p_disc of queries is discordant (exactly one engine succeeds), then σ_d = √(p_disc − δ²). With p_disc = 0.3 and δ = 0.05, σ_d ≈ 0.55 and n ≈ 935 (1,698 at α/15). With δ = 0.10, n ≈ 228.
- This is the arithmetic behind the advice to prefer graded metrics for discriminating engines. It is also why Sakai (2006) found graded one-relevant-document metrics more sensitive than RR (see `metric-scales-and-correlation.md`).

## Relevance to lean-explore-bench

- **Pilot first.** Judge about 50 queries across all engines. Estimate σ_d for each engine pair and each query type. Then fix N with Sakai's ANOVA-based design or the formula above. Do not grow N iteratively until results turn significant (Webber et al.'s bias).
- **Planning prior.** Assume σ_d ≈ 0.25–0.30 for nDCG@10 (unverified for Lean). Detecting a 0.05 difference then needs about 200–300 queries, or 350–500 under all-pairs correction. Differences of 0.10 or more between very different engines (for example Loogle vs. an embedding engine on NL queries) need under 100.
- **Breadth over depth.** Prefer many queries judged to depth 10–20 over few queries judged to depth 100, following Webber et al.
- **Report effect sizes.**
  - Absolute Δ with a 95% CI. Use a paired bootstrap over queries, or a t-interval on the differences.
  - A standardized effect size (Δ/σ_d, or Δ/√V_E for multi-system comparisons).
  - Never a relative "% improvement" alone.
- **Per query type.** Report per-query-type means and CIs. Power within a type is lower (a smaller n), so treat those results as descriptive unless the type has its own power budget.
- **LeanExplore's 300-query set** (`../lean-benchmarks/leanexplore-llm-judge-eval.md`) is in the right range for size. However, it was scored by relative placement, not per-query metric values, so it cannot directly supply σ_d.

## Open questions

- What are realistic σ_d values for Lean search engines? No published Lean benchmark reports per-query variance. We need to compute it from our pilot, or from per-query results if any engine's authors will share them.
- Can bootstrap CIs over queries be combined with judge-run variance when an LLM judge is used? A two-level (query, judge-sample) bootstrap is plausible, but I found no IR paper validating it.

## Sources

- Tague-Sutcliffe & Blustein, TREC-3: https://web.cs.dal.ca/~jamie/pubs/PDF/1995/TREC3/T-S+B_1995_TREC3%20(OCR).pdf (via search summary)
- Banks, Over, Zhang, "Blind Men and Elephants": https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=151743 (via search summary)
- Voorhees & Buckley, SIGIR 2002: https://www.nist.gov/publications/effect-topic-set-size-retrieval-experiment-error
- Buckley & Voorhees, SIGIR 2000: https://dl.acm.org/doi/10.1145/345508.345543 (via search summary)
- Voorhees, SIGIR 2009: https://dl.acm.org/doi/10.1145/1571941.1572138 (via search summary)
- Sakai, SIGIR 2006 (discriminative power): https://www.semanticscholar.org/paper/575a33aa00b7be4c63d5e6b455a6726e84d3f4d4
- Webber, Moffat, Zobel, CIKM 2008: https://people.eng.unimelb.edu.au/jzobel/fulltext/cikm08.pdf
- Sakai, Topic set size design, IRJ 2016: https://doi.org/10.1007/s10791-015-9273-z
- Sakai, Laboratory Experiments in IR (2018): https://springer.com/gp/book/9789811311987
- Sakai, SIGIR 2016 review: https://dl.acm.org/doi/10.1145/2911451.2911492
- Fuhr 2017: http://sigir.org/wp-content/uploads/2018/01/p032.pdf ; Sakai 2020: http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf
- Ihemelandu & Ekstrand 2023: https://arxiv.org/abs/2305.02461
- Sakai & Kando 2008: https://doi.org/10.1007/s10791-008-9059-7
