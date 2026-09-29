# Reliability of relevance judgments: assessor disagreement, incompleteness, LLM assessors

- **Kind:** evaluation methodology (judgments)
- **Links:** see Sources
- **Authors / org, date:** Voorhees (2000) to Clarke & Dietz (2024–2026) and Parry et al. (SIGIR 2025)
- **Status:** the classic finding (rankings stable despite disagreement) was reproduced on neural-era data in 2025. The validity of LLM assessors is actively disputed.

This note goes deeper than `../ir-evaluation/trec-pooling-and-relevance-judgments.md`, which covers pooling, bpref, BEIR's Hole@10 and a first pass on UMBRELA. The focus here is quantitative: how much assessors disagree, how much that matters, and how to validate a judge.

## Assessor disagreement

- **Voorhees (IP&M 2000).**
  - TREC-4 and TREC-6 pools were re-judged by different assessors. The study found "very high correlations ... among the rankings of systems produced using different relevance judgment sets", so "comparative evaluation ... is stable despite substantial differences in relevance judgments" ([NIST](https://www.nist.gov/publications/variations-relevance-judgments-and-measurement-retrieval-effectiveness)).
  - Pairwise agreement was measured as *overlap* (common relevant / union relevant), at around 0.4 ([Parry et al. 2025](https://arxiv.org/abs/2502.20937) §2, summarising Voorhees).
- **Parry et al. (SIGIR 2025).** Reproduced the study on TREC DL 2019, with 4-grade labels and no topic narratives ([arXiv:2502.20937](https://arxiv.org/abs/2502.20937)).
  - Under 4-grade relevance all agreement values dropped. Fleiss' κ "indicates near-random agreement", and improved by about 10 points after binarising. Secondary assessors tended to *lower* grades.
  - System orderings nonetheless remained "highly correlated with the original DL'19 annotations even under 4-grade relevance".
  - But "some models substantially degrade with our new relevance judgments, and some have already reached the effectiveness of humans as rankers". The authors take this as evidence that heavily reused collections can "expire".
- **Kendall's τ thresholds.** The convention traced to Voorhees treats τ ≥ 0.9 between two system rankings as "equivalent" and τ < 0.8 as noticeably different (via search summary; the attribution is (unverified)). Sanderson & Soboroff (SIGIR 2007) showed that "basing decisions on threshold values for the coefficient is not as reliable as has been assumed", because τ depends on how spread out the system scores are ([NIST](https://www.nist.gov/publications/problems-kendalls-tau)).

**Takeaway.** Label-level agreement between humans is low (overlap ≈ 0.4). Run-level rankings are robust to it *on average*. Individual pairwise comparisons, especially among close systems, can still flip. Graded scales without written intent descriptions make agreement worse.

## Incomplete judgments

Recap from the pooling note: pools miss relevant documents, bpref was designed for this, and BEIR showed dense retrievers penalised by BM25-built pools. Additional results:

- **Condensed lists.** Sakai (SIGIR 2007) and Sakai & Kando (IRJ 2008) take a different route: remove unjudged documents from each ranked list and then compute a standard metric (AP′, Q′, nDCG′).
  - On TREC Robust and NTCIR data with artificially reduced qrels, "Q′, nDCG′ and AP′ ... are superior to bpref ... and to Rank-Biased Precision" in discriminative power and in Kendall's τ against the full-qrels ranking ([Sakai & Kando 2008](https://doi.org/10.1007/s10791-008-9059-7)).
  - Graded relevance further improves robustness to incompleteness ([Sakai 2007](https://dl.acm.org/doi/abs/10.1145/1277741.1277756); via search summary).
- **infAP (Yilmaz & Aslam, CIKM 2006).** Estimates AP from a *uniform random sample* of the pool, and is more robust than bpref to incomplete or imperfect judgments. The follow-up infNDCG/xinfAP (Yilmaz, Kanoulas & Aslam, SIGIR 2008) uses stratified sampling ([ACM](https://dl.acm.org/doi/10.1145/1390334.1390437); both via search summary).
- **Unjudged treated as non-relevant.** This is the trec_eval default. It systematically penalises a system that retrieves documents outside the pool, which is exactly the BEIR TREC-COVID pattern. Mitigations:
  - Pool from every system evaluated.
  - Report Judged@k (the fraction of the top k that is judged) next to each score.
  - Report condensed-list nDCG′ as a sensitivity check.
- **Discriminative power of cheap qrels.** Otero, Parapar & Ferro (CIKM 2023) argue that cheaper adjudication methods should be judged by whether they preserve *significant* pairwise differences, not only by Kendall's τ. They found "the best methods in terms of ranking of systems correlation do not always match those preserving statistical significance" ([arXiv:2308.09340](https://arxiv.org/abs/2308.09340)). McKechnie et al. (2025) add Type II errors, summarised as balanced accuracy, to that analysis ([arXiv:2507.07924](https://arxiv.org/abs/2507.07924)).

## LLM assessors: evidence and validation

- **Thomas et al. (Bing; arXiv 2023, rev. 2024).**
  - The prompt was tuned against first-party searcher feedback. LLM labels had "accuracy as good as human labellers" and picked the best runs and groups.
  - "Systematic changes to the prompts make a difference in accuracy, but so too do simple paraphrases."
  - Against gold labels, the LLM beat third-party workers at a fraction of the cost ([arXiv:2309.10621](https://arxiv.org/abs/2309.10621)).
- **UMBRELA (Upadhyay et al. 2024).** GPT-4o, temperature 0, TREC DL 2019–2023, nDCG@10 ([arXiv:2406.06519](https://arxiv.org/abs/2406.06519), Table 2 and §4). The numbers show clearly why run-level correlation is not label accuracy:
  - **Label-level Cohen's κ** against NIST labels was only 0.31–0.37 on the 4-point scale and 0.42–0.50 binarised.
  - **Per-grade accuracy** was roughly 75% for non-relevant, but about 50%, 30% and 45% for grades 1, 2 and 3.
  - **System-ranking correlation** was nonetheless high: Kendall's τ of 0.87–0.94, Spearman's ρ of 0.97–0.99.
- **TREC 2024 RAG large-scale study (Upadhyay, …, Soboroff, Dang, Lin).** 77 runs from 19 teams.
  - UMBRELA vs. fully manual gave run-level τ ≈ 0.89 on nDCG@20. The average per-topic τ was lower.
  - LLM *assistance* to humans (filtering, post-editing) did not raise correlation with fully manual labels.
  - "Human assessors appear to be stricter than UMBRELA" ([arXiv:2411.08275](https://arxiv.org/abs/2411.08275), §4 and Table 2).
- **Counter-evidence.**
  - *Soboroff (IRRJ 2025)* ([arXiv:2409.15133](https://arxiv.org/abs/2409.15133)):
    - "Don't use LLMs to create relevance judgments for TREC-style evaluations."
    - When the judge has the same information as the systems, evaluation "reduces to comparing the performance of the system to the model".
    - Retrieval and relevance assessment "are the same problem".
    - He cites Alaofi et al. (2024): LLM false positives correlate with query-term presence in non-relevant passages.
  - *Clarke & Dietz (2024, rev. 2026)* ([arXiv:2412.17156](https://arxiv.org/abs/2412.17156), §4):
    - Scenario: every system uses UMBRELA as a final re-ranker and is then evaluated by UMBRELA.
    - τ with human-judged rankings falls to 0.63 overall, 0.38 among the top 10 systems, and −0.40 among the top 5.
    - Twelve systems exceed 0.95 nDCG under UMBRELA while scoring 0.68–0.72 under human judgments.
  - *Faggioli et al. (ICTIR 2023)* propose a human–machine collaboration spectrum and a compromise position rather than full automation ([arXiv:2304.09161](https://arxiv.org/abs/2304.09161)).
- **Comparing judging methods.** Arabzadeh & Clarke (SIGIR 2025) compare binary, graded, pairwise-preference and nugget-based LLM assessment on TREC DL 2019–2021 and ANTIQUE. They release judgments from Llama 3.2 and GPT-4o ([arXiv:2504.12558](https://arxiv.org/abs/2504.12558)). The LLMJudge challenge (SIGIR 2024) released a shared dataset for studying LLM labelers ([arXiv:2408.08896](https://arxiv.org/abs/2408.08896)).

**Takeaway.** LLM judges can reproduce *run-level* rankings (τ ≈ 0.9) while agreeing only moderately with humans *per label* (κ ≈ 0.3–0.5). They are least reliable exactly where a leaderboard matters, at the top among close systems. They also fail badly when systems under test use the judge, or a close relative of it.

## Relevance to lean-explore-bench

- **Written intent per query.** Give each query a one-to-two-sentence intent note (what the user wants, and what counts as an acceptable declaration). Parry et al. attribute the collapse in agreement partly to missing narratives.
- **Grading scale.**
  - Use 4 grades with Lean-specific anchors:
    - 3: exact declaration.
    - 2: usable with trivial glue (an `iff` direction, `.symm`, a coercion variant).
    - 1: related but needs real work.
    - 0: irrelevant.
  - Also report binarised (≥2) versions, since binarising raises agreement.
- **Human agreement study.** Have 2 Lean-literate annotators double-judge at least about 15–20% of pooled pairs. Report Cohen's κ (4-grade and binary), overlap, and τ between the system rankings each annotator induces. Adjudicate disagreements.
- **LLM judge validation.** If an LLM judge is used:
  - Validate it on the double-judged subset. Report label κ vs. each human *and* human–human κ, so the judge is compared to the human ceiling.
  - Report run-level τ, top-k τ (or τ_AP), and the fraction of significant pairwise decisions preserved (Otero et al. 2023).
  - Do not rely on τ alone.
- **Circularity.** Circularity is a live risk here: LeanExplore and other engines use LLM rerankers or LLM-generated descriptions. Choose a judge from a different model family than any engine's reranker. Disclose any overlap. Keep a human-only-judged holdout for the final leaderboard.
- **Incompleteness.** Pool from all engines. Report Judged@10 per engine. Report nDCG′ (condensed) as a sensitivity analysis alongside nDCG with unjudged treated as non-relevant.
- **Rotating queries.** Add fresh queries periodically so that engines tuned on the public set can be detected. This is the "shelf life" concern raised by Parry et al.

## Open questions

- Is Lean relevance *less* subjective than web relevance? Partial ground truth might come from type-checking (for example "does `exact X` close the goal?"). If so, human κ may be much higher than 0.4, and LLM validation easier. This needs measuring.
- Should pairwise preference judgments (as in LeanExplore's own judge protocol) be combined with graded labels? The statistics of preference-based evaluation are not covered by the tests above.

## Sources

- Voorhees 2000: https://www.nist.gov/publications/variations-relevance-judgments-and-measurement-retrieval-effectiveness
- Parry et al., SIGIR 2025: https://arxiv.org/abs/2502.20937
- Sanderson & Soboroff 2007: https://www.nist.gov/publications/problems-kendalls-tau
- Sakai 2007: https://dl.acm.org/doi/abs/10.1145/1277741.1277756 ; Sakai & Kando 2008: https://doi.org/10.1007/s10791-008-9059-7
- Yilmaz & Aslam 2006: https://dl.acm.org/doi/10.1145/1183614.1183633 ; Yilmaz, Kanoulas, Aslam 2008: https://dl.acm.org/doi/10.1145/1390334.1390437 (via search summary)
- Otero, Parapar, Ferro, CIKM 2023: https://arxiv.org/abs/2308.09340 ; McKechnie et al. 2025: https://arxiv.org/abs/2507.07924
- Thomas et al.: https://arxiv.org/abs/2309.10621 ; UMBRELA: https://arxiv.org/abs/2406.06519 ; TREC 2024 RAG study: https://arxiv.org/abs/2411.08275
- Soboroff 2025: https://arxiv.org/abs/2409.15133 ; Clarke & Dietz: https://arxiv.org/abs/2412.17156 ; Faggioli et al.: https://arxiv.org/abs/2304.09161
- Arabzadeh & Clarke 2025: https://arxiv.org/abs/2504.12558 ; LLMJudge: https://arxiv.org/abs/2408.08896
