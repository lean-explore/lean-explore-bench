# Metric properties: measurement scales, metric sensitivity, and ranking correlation

- **Kind:** evaluation methodology (metrics)
- **Links:** see Sources
- **Authors / org, date:** Fuhr (2017), Ferrante/Ferro/Fuhr (2021), Moffat (2022, 2023), Sakai (2006, 2020)
- **Status:** the scale debate is unresolved and both camps are active. The practical guidance on metric sensitivity is stable.

`ir-offline-metrics-and-significance-testing.md` covers which metrics benchmarks use. This note covers whether averaging and testing those metrics is meaningful, how sensitive they are, and how to compare the rankings they induce.

## The interval-scale debate

- **Fuhr (2017)** ([PDF](http://sigir.org/wp-content/uploads/2018/01/p032.pdf), §2.1):
  - "Thou shalt not compute MRR nor ERR."
  - Under reciprocal rank (RR), the step from rank 1 to 2 equals the step from rank 2 to ∞, so "RR is not an interval scale, it is only an ordinal scale", and "one cannot compute the mean for an ordinal scale".
  - His example: system A finds the first relevant result at ranks 1, 2 and 4 (MRR 0.58, mean rank 2.33). System B finds it at rank 2 every time (MRR 0.50, mean rank 2). MRR and mean rank disagree.
  - He proposes Mean First Relevant (MFR), the mean rank of the first relevant result, which he calls a ratio scale.
- **Ferrante, Ferro & Fuhr (2021).** Built on representational measurement theory ([arXiv:2101.02668](https://arxiv.org/abs/2101.02668)).
  - The recall base and run length can make comparison across topics problematic.
  - They propose mapping each measure to an interval scale.
  - Across P, R, AP, nDCG, RBP and RR, interval-scaling changed both the order of mean scores and significance outcomes. On average "a 25% change in the decision about which systems are significantly different and which are not".
- **Sakai (2020) disagrees** ([PDF](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf), §2.1–2.2):
  - Averaging ordinal data is contested in statistics, not forbidden.
  - RR's equal steps reflect its user model, just as DCG's log discount makes ranks 15 → 31 equal to ranks 31 → 100.
  - RR and ERR suit navigational (single-answer) search.
  - On 1,127 SERP pairs, each judged by 15 assessors, agreement with user preferences was: nDCG 0.742, ERR 0.681, AP 0.705. Graded measures beat AP significantly under randomised Tukey HSD.
- **Moffat (2022, 2023)** ([arXiv:2207.03103](https://arxiv.org/abs/2207.03103), [arXiv:2312.12672](https://arxiv.org/abs/2312.12672)):
  - Rankings are categorical data. A metric maps each category to a usefulness value on a ratio scale.
  - Such mappings are valid "provided there is an external reason for each target point to have been selected".
  - Current metrics "are more meaningful in their current form than in the proposed 'intervalized' versions."

**Practical reading.** Nobody disputes the *empirical* part: the choice of metric transformation can flip significance for about a quarter of system pairs. The debate is only about which version is "right". So:
- Pre-register the metric, and do not shop among metrics.
- Report a second, differently-scaled metric as a robustness check. For a single-answer task, MRR and Success@k, or MRR and mean first-relevant rank, are natural pairs.
- If conclusions differ between them, say so.

## Metrics for one-correct-answer (known-item) tasks

- **Sensitivity ranking.** Sakai (AIRS 2006) compared metrics for "finding one relevant document" using bootstrap tests. Sensitivity generally ranks "P(+)-measure ≥ O-measure ≥ NWRR ≥ RR", so plain RR is the least sensitive of the group ([Springer](https://link.springer.com/chapter/10.1007/11880592_29); via search summary). The more sensitive metrics exploit graded relevance or relevant documents beyond the first.
- **Type III errors.** Urbano et al. (2019) found the highest rates of direction errors for P@10 and RR ([arXiv:1905.11096](https://arxiv.org/abs/1905.11096)).
- **Binary Success@k.** Per-query differences take only the values −1, 0 or +1, so it needs several times more queries than a graded metric for the same δ. See the computation in `eval-stats-effect-sizes-power-and-topic-set-size.md`.
- **Sparse labels.** A single gold answer under-credits engines that return equally good alternatives. This is MS MARCO's "better than perfect" problem ([arXiv:2109.00062](https://arxiv.org/abs/2109.00062); see `ir-trec-pooling-and-relevance-judgments.md`).

## Comparing system rankings (metric correlation, judge validation)

- **Kendall's τ** between the system orderings induced by two metrics, or two qrel sets, is the standard tool. Its threshold conventions (0.9 / 0.8) are unreliable because τ depends on the spread of system scores ([Sanderson & Soboroff 2007](https://www.nist.gov/publications/problems-kendalls-tau)).
- **τ_AP.** Yilmaz, Aslam & Robertson (SIGIR 2008) proposed τ_AP, a rank correlation that penalises disagreements near the top more heavily ([ACM](https://dl.acm.org/doi/10.1145/1390334.1390435); the weighting description is from general knowledge, (unverified) against the text). It is useful because leaderboards care about the top.
- **Significance-aware comparison.** Compare whether two setups make the same *significant* pairwise decisions, not just whether they order systems the same way ([Otero et al. 2023](https://arxiv.org/abs/2308.09340)). Soboroff describes a τ variant in which swaps count only if they are significant ([arXiv:2409.15133](https://arxiv.org/abs/2409.15133), §2).
- **Redundant metrics.** Highly correlated metrics add no evidence and add multiple-testing burden. Fuhr: "if the measures are strongly correlated, then there is no need to test each of them" (§2.7). Webber, Moffat, Zobel & Sakai's "Precision-at-ten considered redundant" (SIGIR 2008) is a case study (title and venue from [Sakai 2020's references](http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf); content (unverified)).
- **Stability of metric families.** Chen & Sakai (2023) compared aggregation choices within the C/W/L/A framework. Precision, DCG, RBP, INST and AP with their canonical aggregation "all have favourable performances in system ranking consistency and discriminative power" ([arXiv:2307.02936](https://arxiv.org/abs/2307.02936)).

## Relevance to lean-explore-bench

- **Primary metric.** Graded nDCG@10 on the pooled judgments. It is the most discriminative family and has the best agreement with user preference in Sakai's data. Pre-register it.
- **Known-item sub-task** (queries with one canonical target declaration):
  - Report MRR@10 *and* Success@1/5/10 *and* the mean or median first-relevant rank (capped at a cutoff).
  - Treat all of them as secondary. Budget for many more queries if any is to be tested for significance.
  - Credit equivalent declarations (aliases, `iff` versions) using the graded qrels, not a single string match.
- **Diagnostic metric.** Recall@k at the candidate depth. Descriptive only.
- **Robustness check.** If a headline pairwise conclusion under nDCG@10 flips under a second metric (nDCG@20, or binarised P@10), report it as fragile.
- **Judge validation.** Use τ, τ_AP (or top-k τ), and the preserved significant-pair fraction. Never τ alone.

## Open questions

- Is there a Lean-appropriate *effort-based* metric, for example "expected number of results inspected before a usable lemma", in the spirit of Fuhr's MFR? That would give an interpretable ratio-scale effect size ("users inspect 1.3 fewer results").

## Sources

- Fuhr 2017: http://sigir.org/wp-content/uploads/2018/01/p032.pdf
- Ferrante, Ferro, Fuhr 2021: https://arxiv.org/abs/2101.02668
- Sakai 2020: http://www.sigir.org/wp-content/uploads/2020/06/p14.pdf
- Moffat 2022: https://arxiv.org/abs/2207.03103 ; Moffat 2023: https://arxiv.org/abs/2312.12672
- Sakai, AIRS 2006: https://link.springer.com/chapter/10.1007/11880592_29 (via search summary)
- Urbano et al. 2019: https://arxiv.org/abs/1905.11096
- Sanderson & Soboroff 2007: https://www.nist.gov/publications/problems-kendalls-tau
- Yilmaz, Aslam, Robertson 2008: https://dl.acm.org/doi/10.1145/1390334.1390435
- Otero, Parapar, Ferro 2023: https://arxiv.org/abs/2308.09340 ; Soboroff 2025: https://arxiv.org/abs/2409.15133
- Chen & Sakai 2023: https://arxiv.org/abs/2307.02936
- Arabzadeh et al. (shallow pooling): https://arxiv.org/abs/2109.00062
