# Significance tests and multiple-comparison corrections for IR evaluation

- **Kind:** evaluation methodology (statistics)
- **Links:** see Sources
- **Authors / org, date:** van Rijsbergen (1979) through Urbano (SIGIR 2026)
- **Status:** active and contested. The pairwise-test question is largely settled in favour of the paired t-test and the permutation test. The question of which correction to use when comparing many systems is still open.

This note extends `../ir-evaluation/offline-metrics-and-significance-testing.md`, which already summarises Smucker et al. 2007, Parapar et al. 2019 and Urbano 2026 in one line each. Here the focus is what each study measured, where the studies disagree, and what that means for an experiment comparing about 5 to 10 Lean search engines.

## What it is

In a Cranfield-style experiment, each system produces one score per query (topic). A paired significance test asks whether the mean per-query difference between two systems could plausibly be zero, given that the queries are a sample from a larger population of queries. The unit of analysis is the query, not the document ([Urbano et al. 2019 §1](https://arxiv.org/abs/1905.11096)).

## Pairwise tests: what the evidence says

The table orders the studies chronologically.

| Study | Method | Verdict |
|---|---|---|
| Smucker, Allan & Carterette, CIKM 2007 | Pairs of TREC runs. Measured agreement between tests, with the permutation test as reference. | Randomization, bootstrap and t-test agree closely. Wilcoxon and sign tests "should be discontinued" ([PDF](https://maroo.cs.umass.edu/getpdf.php?id=744)). |
| Smucker, Allan & Carterette, SIGIR 2009 (poster) | The same tests on topic subsets down to 10 topics. | The tests disagree more as the topic count shrinks ([ACM](https://dl.acm.org/doi/10.1145/1571941.1572050); via search summary). |
| Urbano, Lima & Hanjalic, SIGIR 2019 | Simulated TREC-like scores with a *known* null hypothesis, over 500 million p-values. | The t-test and the permutation test "maintain the Type I error rate at the α level across measures, topic set sizes and significance levels". The t-test is the "top recommendation" because it is "simpler and remarkably robust to sample size". The bootstrap-shift test is biased toward small p-values, and the authors "propose its discontinuation as well". Wilcoxon and sign tests should be discontinued. Type III errors (correct rejection, wrong direction) reach 2% for P@10 and RR, or for small topic sets ([arXiv:1905.11096](https://arxiv.org/abs/1905.11096), §1 and §5). |
| Parapar et al., JASIST 2020 | Simulation from score distributions. | Contrary result: sign and Wilcoxon tests had more power with acceptable Type I error ([arXiv:1901.10696](https://arxiv.org/abs/1901.10696)). |
| Ihemelandu & Ekstrand, SIGIR 2023 | Large search and recommendation experiments with thousands of queries or users. | Wilcoxon and sign tests show "significantly higher Type-1 error rates for large sample sizes". At that scale, most tests would find significance nearly 100% of the time, so "the effect size should be used to determine practical or scientific significance" ([arXiv:2305.02461](https://arxiv.org/abs/2305.02461)). |
| Urbano, SIGIR 2026 | Textbook review plus TREC demonstrations. | Wilcoxon tests the *median* of the per-query differences and assumes those differences are symmetric. IR score differences are skewed and heavy-tailed. Under asymmetry, the t-test holds 5% Type I error while Wilcoxon "fails catastrophically, and increasingly so" as the sample grows ([arXiv:2604.25349](https://arxiv.org/abs/2604.25349), §4). |

**Reading.** Four independent groups (Smucker, Urbano, Ihemelandu, and Urbano again) converge on two recommendations:
- Use the paired t-test for hypotheses about mean effectiveness.
- Use the paired permutation (randomization) test when you need a different statistic, such as a median or a trimmed mean.

Parapar et al. are the outlier. Urbano 2026 explains the mechanism behind the disagreement: Wilcoxon answers a different question (location under symmetry), and IR data break symmetry.

## Many systems: multiple comparisons

With m systems there are k = m(m−1)/2 pairwise tests. At α = 0.05 with 6 systems (15 tests), the family-wise error rate (FWER) is about 0.53 if the tests are treated as independent ([Otero et al., ECIR 2025 §2](https://arxiv.org/abs/2501.03930)).

- **Fuhr (SIGIR Forum 2017), "Thou shalt not test multiple hypotheses without correction".**
  - Bonferroni is presented as the simple, conservative option.
  - For evaluation campaigns, "the only reasonable method ... is the application of a post-hoc test such as e.g. Tukey's test", which "checks all pairwise differences between runs".
  - If several metrics are tested, "an additional correction is necessary".
  - Reusing a test collection is itself sequential multiple testing ([PDF](http://sigir.org/wp-content/uploads/2018/01/p032.pdf), §2.7).
- **Carterette (TOIS 2012).** Treats multiple testing in systems-based IR experiments at length ([ACM](https://dl.acm.org/doi/10.1145/2094072.2094076)). Sakai (2020) credits Carterette 2012 and Sakai 2018 with the *randomised Tukey HSD* test, which Sakai uses in his own meta-evaluation ([PDF](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf), Table 1). Carterette's specific procedure is (unverified) here beyond these citations.
- **Boytsov, Belova & Westfall (SIGIR 2013).**
  - Compared Holm–Bonferroni-adjusted permutation p-values, the MaxT permutation test, and permutation-based closed testing ([ACM](https://dl.acm.org/doi/10.1145/2484028.2484034)).
  - As summarised by Otero et al.: at 50 queries these procedures "seem to over-adjust ... and thus end up with ... low average power" ([arXiv:2501.03930](https://arxiv.org/abs/2501.03930) §1).
- **Ferro & Sanderson (SIGIR 2024).**
  - "Multiple testing corrections are critical for experimental work."
  - Ignoring the context of a test (which family it belongs to, what kinds of systems are compared) produces "substantial numbers of Type I errors" ([PDF](https://www.dei.unipd.it/~ferro/papers/2024/SIGIR2024-FS.pdf)).
  - Otero et al. summarise the paper as finding that 40–50% of uncorrected significance tests in IR research are likely Type I errors ([arXiv:2501.03930](https://arxiv.org/abs/2501.03930) §1).
- **Ihemelandu & Ekstrand (ECIR 2024).** In simulation, Benjamini–Yekutieli gave the lowest Type I error and good average power (as summarised in [arXiv:2501.03930](https://arxiv.org/abs/2501.03930)).
- **Otero, Parapar & Barreiro (ECIR 2025)** ([arXiv:2501.03930](https://arxiv.org/abs/2501.03930), §5). Tests compared: t-test, Wilcoxon, two-way ANOVA, and randomised Tukey HSD, each combined with Bonferroni, Holm, BH and BY corrections.
  - Unadjusted testing "drastically increases the Type I error rate".
  - "Only one procedure, the randomised TukeyHSD, behaved as expected, controlling the expected error rate for every topic set size."
  - The other corrections were *more* conservative than nominal, especially on t-test p-values.
  - Adjusted tests did not lose power relative to unadjusted ones in their setup.
  - They recommend Wilcoxon + Benjamini–Hochberg as the most powerful option. That recommendation conflicts with Urbano's SIGIR 2026 finding that Wilcoxon's error control breaks under asymmetry.

**Reading.**
- *If you want FWER control over all pairs:* randomised Tukey HSD is the one procedure empirically shown to hold its nominal error rate across topic-set sizes.
  - **Caution on ranx.** ranx's `stat_test="tukey"` calls `scipy.stats.tukey_hsd(*scores)` ([source](https://github.com/AmenRa/ranx/blob/master/ranx/statistical_tests/tukey_hsd_test.py)). That is the classical one-way, *unpaired* Tukey HSD. It ignores the query pairing, so it is not the randomised, query-blocked version evaluated above.
  - **Existing implementations.** Sakai's Discpower tool implements randomised Tukey HSD ([sakailab downloads](https://sakailab.com/download/); via search summary).
  - **How it works.** In each of B trials, shuffle the system labels independently within each query's row of the query×system score matrix. Record the largest pairwise mean difference. A pair's p-value is the fraction of trials whose largest difference is at least that pair's observed difference. It is about 20 lines of NumPy. (This algorithm is my paraphrase of the method as used by Carterette 2012 and Sakai 2018 (unverified) against their texts.)
- *If you only compare each engine against a single reference* (for example "is engine X better than LeanExplore?"): Holm over those m−1 tests is standard and uniformly more powerful than Bonferroni.
- *If controlling the false discovery rate is acceptable:* BH is supported, but pair it with the t-test or the permutation test, not Wilcoxon, given Urbano 2026.

## Critiques of common practice

- **Fuhr's ten "Thou shalt not"s (2017)** ([PDF](http://sigir.org/wp-content/uploads/2018/01/p032.pdf)):
  - Don't use MRR or ERR (discussed in `metric-scales-and-correlation.md`).
  - Don't use MAP.
  - Don't overstate precision: four decimal places imply false precision, so report CIs.
  - Don't report relative improvements of arithmetic means.
  - Don't rely on the simple holdout method.
  - Don't form hypotheses after the experiment.
  - Don't run uncorrected multiple tests.
  - Don't ignore effect sizes.
  - Don't forget reproducibility.
  - Don't claim proof by experimentation.
- **Sakai's reply (SIGIR Forum 2020)** ([PDF](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf)):
  - Agrees on overstated precision, post-hoc hypotheses, multiple-testing correction, effect sizes, reproducibility and proof-by-experiment.
  - Disagrees on banning MRR, ERR and MAP.
  - Prefers standardized effect sizes (Hedges' g, Glass's Δ) to relative improvements.
  - Warns that one researcher's guideline should not become an unchallenged venue policy.
- **Sakai's systematic review (SIGIR 2016).** Covered 840 SIGIR and 215 TOIS papers from 2006–2015.
  - Where a test was used, the paired t-test dominated (66% of SIGIR papers, 61% of TOIS papers), followed by Wilcoxon (20% and 23%).
  - Many papers did not report p-values or test statistics, which makes post-hoc power analysis impossible ([ACM](https://dl.acm.org/doi/10.1145/2911451.2911492); figures via search summary, (unverified) against the full text).

## Relevance to lean-explore-bench

- **Primary pairwise test.** Use the paired two-sided t-test on per-query metric values. Use the paired permutation test (≥10,000 permutations) as a robustness check, and for any non-mean statistic. Do not use Wilcoxon or sign tests.
- **Many engines.** Report a single all-pairs randomised Tukey HSD per primary metric (FWER 0.05). If the headline question is "engine X vs. each other engine", use Holm over those m−1 paired tests instead.
- **Multiple metrics.** Pre-declare one primary metric; the rest are descriptive only. If several metrics must be tested, correct across metrics as well (Fuhr §2.7).
- **Leaderboard over time.** Every new engine added to a frozen query set is another test on the same collection (Fuhr's "collection reuse" point). Adding fresh query batches over time keeps the benchmark from being overfit.
- **LeanExplore's LLM-judge evaluation.** It reported mean ± SE across 3 judge runs (`../lean-benchmarks/leanexplore-llm-judge-eval.md`). That SE measures judge stochasticity, not query-sampling variance. Query-level resampling (bootstrap over the 300 queries) is what supports claims that generalise to new queries.

## Open questions

- None of the multiple-comparison studies uses a heterogeneous query mix like ours (name lookup, natural-language concept, type pattern). Should query type be a blocking factor, for example through a two-way ANOVA or a mixed model with query-type strata?
- Tukey HSD answers "which pairs differ?" A leaderboard wants "which engine is best?" Multiple comparisons with the best (MCB) or a ranking with confidence sets may fit better. I found no IR literature on this.

## Sources

- Smucker, Allan, Carterette, CIKM 2007: https://maroo.cs.umass.edu/getpdf.php?id=744
- Smucker, Allan, Carterette, SIGIR 2009: https://dl.acm.org/doi/10.1145/1571941.1572050 (via search summary)
- Urbano, Lima, Hanjalic, SIGIR 2019: https://arxiv.org/abs/1905.11096 ; code: https://github.com/julian-urbano/sigir2019-statistical
- Parapar et al., JASIST 2020: https://arxiv.org/abs/1901.10696
- Ihemelandu & Ekstrand, SIGIR 2023: https://arxiv.org/abs/2305.02461
- Urbano, SIGIR 2026: https://arxiv.org/abs/2604.25349
- Carterette, TOIS 2012: https://dl.acm.org/doi/10.1145/2094072.2094076 (content known via citing papers)
- Boytsov, Belova, Westfall, SIGIR 2013: https://dl.acm.org/doi/10.1145/2484028.2484034 (findings via Otero et al.)
- Ferro & Sanderson, SIGIR 2024: https://www.dei.unipd.it/~ferro/papers/2024/SIGIR2024-FS.pdf
- Otero, Parapar, Barreiro, ECIR 2025: https://arxiv.org/abs/2501.03930
- Fuhr, SIGIR Forum 2017: http://sigir.org/wp-content/uploads/2018/01/p032.pdf
- Sakai, SIGIR Forum 2020: http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf
- Sakai, SIGIR 2016: https://dl.acm.org/doi/10.1145/2911451.2911492 (via search summary)
