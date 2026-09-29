# NTCIR Math tasks: NTCIR-10 Math Pilot, NTCIR-11 Math-2, NTCIR-12 MathIR

- **Kind:** benchmark / dataset (shared-task test collections)
- **Links:**
  - NTCIR-12 MathIR overview: <https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings12/pdf/ntcir/OVERVIEW/01-NTCIR12-OV-MathIR-ZanibbiR.pdf>
  - NTCIR-11 Math-2 overview: <http://research.nii.ac.jp/ntcir/workshop/OnlineProceedings11/pdf/NTCIR/OVERVIEW/01-NTCIR11-OV-MATH-AizawaA.pdf>
  - NTCIR-11 Wikipedia subtask paper (SIGIR 2015): <https://dl.acm.org/doi/10.1145/2766462.2767787> (PDF: <https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=918116>)
  - NTCIR-10 Math Pilot overview: Semantic Scholar record <https://www.semanticscholar.org/paper/NTCIR-10-Math-Pilot-Task-Overview-Aizawa-Kohlhase/162a0a79472fc92560d6be663921f979967d2500>. The NII PDF URL tried returned 404, so NTCIR-10 details below come from secondary sources.
  - Cross-collection re-analysis: <https://arxiv.org/abs/2111.10504>
- **Authors / org, date:**
  - NTCIR-10 (2013): Aizawa, Kohlhase, Ounis.
  - NTCIR-11 (2014): Aizawa, Kohlhase, Ounis, Schubotz.
  - NTCIR-12 (2016): Zanibbi, Aizawa, Kohlhase, Ounis, Topić, Davila.
- **Status:** Finished. NTCIR-12 corpora were released and "topics and assessment ratings will be released later in 2016" [NTCIR-12 §5]. NTCIR-12 WFB is still used as a formula-retrieval test set, e.g. inside MIRB (see `../lean-benchmarks/mirb.md`).

## What it is

The first three Math IR shared tasks, and the direct predecessors of ARQMath (see `arqmath.md`).

- **NTCIR-10 Math Pilot (2013).**
  - Four subtasks: formula search, full-text search, open MIR, and math text understanding.
  - Corpus: 100,000 arXiv papers converted to XHTML+MathML by LaTeXML, 63 GB [MathWebSearch at NTCIR-10](https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings10/pdf/NTCIR/MATH/04-NTCIR10-MATH-KohlhaseM.pdf).
  - Formula search had 22 queries according to the MWS paper and the ARQMath-3 overview [ARQMath-3 §2](https://ceur-ws.org/Vol-3180/paper-01.pdf). Mansouri et al. count 21, of which 18 contain wildcards [2111.10504 §2]. The discrepancy is unresolved (unverified).
  - 15 teams registered and 6 submitted formula-search runs [MWS NTCIR-10 §1].
- **NTCIR-11 Math-2 (2014).**
  - Main task: ad hoc retrieval of arXiv *paragraphs*. The corpus was 105,120 arXiv articles split into 8,301,578 search units with about 60M formulae.
  - 50 topics, each combining keywords and formulae.
  - 8 teams submitted 20 runs [NTCIR-11 §3-5; NTCIR-12 §2.1].
  - An optional Wikipedia subtask was a *known-item* formula search, described below.
- **NTCIR-12 MathIR (2016).** Four subtasks [NTCIR-12 §1-2]:
  - *arXiv-main*: 29 topics, keywords + formulae, over the NTCIR-11 arXiv paragraphs.
  - *arXiv-simto*: 8 experimental topics using a "similar-to" region operator.
  - *Wiki-main*: 30 topics over a new corpus of 319,689 English Wikipedia articles with over 590k formulae. Only about 10% of the articles contain math; the rest are distractors.
  - *Wiki-formula* (Wikipedia Formula Browsing, WFB): 40 isolated-formula queries, 20 concrete and 20 wildcard variants of them.
  - 6 teams submitted 47 runs.

## How it works (evaluation design)

**Query format.**
- Topics are formula(e) plus keywords, with **query variables** (wildcards) that unify with arbitrary subexpressions. arXiv topics write them as `?x`; Wikipedia topics as `*1*`. A repeated variable must match the same subexpression [NTCIR-12 §2.2].
- Formulae are supplied as LaTeX, Presentation MathML and Content MathML.
- Participants get only the topic ID and the query. The *narrative* (user situation, information need, relevance criteria) goes only to assessors, "to avoid participants biasing their system design towards the specific information needs" [NTCIR-12 §2.2; NTCIR-11 §3].
- Runs return up to 1,000 results, each with "hit justifications" (matched formula ID, substitutions). The judging interface highlights these for assessors [NTCIR-12 §2.3].

**Pooling.**
- *NTCIR-10 formula search.* Runs were sampled one rank at a time until the pool reached at least 100 unique formula *instances* [2111.10504 §3].
- *NTCIR-11 main task.* Round-robin sampling took the current top-ranked unit from every run until the pool held 50 units per topic, with the sampling order prioritised by how much each group had been assessed so far [NTCIR-11 §4.2].
- *NTCIR-12.* Top-20 from each run [NTCIR-12 §4].
- Instance-level pooling can produce degenerate pools. For the NTCIR-12 WFB query β, "every formula instance in the judgement pool was β" [2111.10504 §3]. This is what motivated ARQMath's visual-ID clustering.

**Assessors and relevance levels.**
- Each item was rated Relevant (2), Partially relevant (1) or Not relevant (0) by **two** assessors, and the two scores were summed to 0-4. For binary trec_eval, a sum of 3-4 counts as "relevant" and 1-4 as "partially relevant" [NTCIR-12 Table 6; NTCIR-11 Table 4].
- NTCIR-12 arXiv tasks used three evaluators drawn from third-year and graduate pure-math students.
- NTCIR-12 Wikipedia tasks used 10 evaluators, 5 undergraduates and 5 MSc students. Each hit was judged by one undergraduate and one graduate, with the pairings rotated to reduce bias [NTCIR-12 §4].
- NTCIR-11 assessors were given no guidelines beyond the narrative. They "self-reported being relatively lenient with formula hits", marking hits partially relevant when many symbols overlapped [NTCIR-11 §4.3].
- NTCIR-12 WFB assessors were shown the formula in context but told to judge the formula itself against the scenario [2111.10504 §3].

**Agreement.**
- NTCIR-11 main task: Fleiss' κ 0.544 (relevant) and 0.578 (partially relevant); Pearson 0.548 and 0.591 [NTCIR-11 Table 6].
- NTCIR-12, Fleiss' κ per subtask [NTCIR-12 Table 7]: arXiv-main 0.5615, arXiv-simto 0.5380, Wiki-main 0.3546, Wiki-formula 0.2619. The organizers note that some evaluators judged by semantics and others mainly by visual similarity.

**Metrics.**
- NTCIR-11: MAP, P@5, P@10 and bpref from trec_eval 9.0 [NTCIR-11 §4.4].
- NTCIR-12: P@5/10/15/20 only, chosen because they are "simple to understand" [NTCIR-12 §2.4].
- Unjudged items were counted as non-relevant for P@hit and MAP [2111.10504 §4]. Later papers on NTCIR-12 WFB report **bpref on the top 1,000** precisely because their systems did not contribute to the pools [Approach0 ECIR 2019 §5](https://www.cs.rit.edu/~dprl/assets/files/Approach0_ECIR2019.pdf).

**NTCIR-11 Wikipedia subtask: automatically generated known-item queries** [Schubotz et al. SIGIR 2015 §3-4]:
- *Generation.* Pick a random formula (the "seed") from a random math-bearing Wikipedia article, then randomly replace variables with query variables named `x0, x1, …` so the names leak nothing. The relevant answer is the seed itself.
- *Stratification.* Topics are classed by f (how often the seed occurs exactly) and q (number of query variables): 41 easy, 27 variable, 24 frequent, 8 hard (100 total).
- *Metrics.* MRR and "success" (found at any rank). Scoring is either *page-centric* (the seed page was retrieved) or *formula-centric* (the exact TeX was retrieved).
- *Live leaderboard.* Only aggregate scores were shown, "to avoid over-fitting". Teams resubmitted 3-5 times, and some improved MRR by 50% or more.
- *Results.* 7 teams submitted 56 runs. Best page-centric success was 97% (TUW and NII), with MRR 82% for TUW and 74.5% for NII. Best formula-centric was NII at 94% success and 82% MRR. The "any fraction" query (99) was found by only one team, at rank 8,983.
- *Design principles.* The paper lists lessons carried over from NTCIR-10: every query needs at least one relevant hit in the collection; wildcard semantics must be well defined; participants should see only what a system would see; relevance criteria should not depend on the topic author or assessor.

## Evaluation (reported numbers)

**NTCIR-11 main task, 50 topics, "Relevant" = combined score ≥ 3** [NTCIR-11 Table 8]:
- Best run: MIRMU `cmath`, MAP 0.363, P@5 0.568, P@10 0.352, bpref 0.513.
- KWARC default: MAP 0.285, P@5 0.500, bpref 0.380.
- Best partially-relevant P@5: RIT `mte`, 0.924.

**NTCIR-12, P@5 / P@10 on "Relevant"** [NTCIR-12 Table 8]:

| Subtask | Best run | P@5 | P@10 | "Pool" upper bound (P@5 / P@10) |
|---|---|---|---|---|
| arXiv-main | MCAT `af-nw-u` | 0.2828 | 0.2379 | 0.6966 / 0.5586 |
| Wiki-main | ICST | 0.4733 | 0.3767 | 0.8400 / 0.6967 |
| Wiki-formula (WFB) | MCAT `f-af-nw-u` | 0.4900 | 0.3900 | 0.7900 / 0.6400 |

The "Pool" row sorts all pooled hits by relevance, giving an ideal-ranking upper bound. The organizers stress the "substantial gap" between it and the best runs.

**Follow-up work on NTCIR-12 WFB, 20 concrete queries, bpref@1000, fully relevant** [Approach0 ECIR 2019, Table 1]:
- Approach0 (3 subtrees): 0.6726
- Tangent-S: 0.6361
- MCAT: 0.5678

The same paper also reports P@k three ways: "standard" (unjudged counted as non-relevant), "condensed" (unjudged removed) and "upper bound" (unjudged counted as relevant). For Approach0 (K=1 run), fully-relevant P@10 was 0.285, 0.405 and 0.785 respectively. That spread shows how much a non-contributing system is penalised by incomplete pools.

**Re-analysis** [2111.10504]:
- The same three systems (Tangent-S, -CFT, -CFTED) all score higher nDCG′ on NTCIR-12 WFB concrete queries (0.78-0.89 aggregate) than on ARQMath-1/2 (0.49-0.69).
- Kendall τ between system rankings on low- versus high-complexity query subsets drops to 0.59 (ARQMath-2), and to 0.37 for medium versus high.
- The authors conclude that topic complexity, contextual relevance and clustering choices all change system ordering.

## Relevance to lean-explore-bench

**What to reuse:**
- *Give assessors a hidden narrative.* Each topic carries a short scenario plus relevance criteria that engines never see. This separates the "query string" from the "information need", which matters for us because the same Lean query (e.g. `add_comm`) can come from very different needs.
- *Use two independent judges per item and sum their scores* (0-2 each, giving 0-4). This yields a finer graded label, and binarization thresholds (≥3 strict, ≥1 lenient) can be reported side by side.
- *Report an ideal-from-pool upper bound next to system scores.* It shows how much headroom exists.
- *Evaluate non-pooled systems with bpref or prime metrics, and publish the standard / condensed / upper-bound triple for P@k.* When a new engine surfaces unjudged Mathlib declarations, the triple makes pool incompleteness visible instead of hiding it.
- *Build an automatically generated known-item track*, following the NTCIR-11 Wikipedia recipe:
  - Sample a random Mathlib declaration.
  - Build a query from its statement with some identifiers or subterms replaced by wildcards (for `#find`/`exact?`-style formal queries), or from an informalized paraphrase.
  - Score MRR / success@k against the seed.
  - Stratify by how many near-duplicates of the seed exist (their f) and by how many wildcards were inserted (their q).
  - This is cheap, unbounded, and needs no assessors. It complements a smaller human-judged ad hoc track.
- *Keep the test set hidden and show only aggregate scores* on any public leaderboard. This limits overfitting, which the organizers observed directly (MRR gains of 50% or more across resubmissions).

**What NTCIR gets wrong or leaves out:**
- Precision-only metrics.
- Unjudged items treated as non-relevant.
- Instance-level pooling that fills with duplicates.
- Small topic sets (20-50).
- Low agreement on formula-only relevance (κ about 0.26), when assessors had no context to decide *why* a formula was wanted.

## Open questions

- Is the NTCIR-12 topic-and-qrels release still downloadable? Not checked.
- The NTCIR-10 overview PDF could not be retrieved; its pooling and metric details come only from secondary sources [2111.10504; MWS NTCIR-10].

## Sources

- NTCIR-12 MathIR Task Overview (Zanibbi et al., 2016): <https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings12/pdf/ntcir/OVERVIEW/01-NTCIR12-OV-MathIR-ZanibbiR.pdf>
- NTCIR-11 Math-2 Task Overview (Aizawa et al., 2014): <http://research.nii.ac.jp/ntcir/workshop/OnlineProceedings11/pdf/NTCIR/OVERVIEW/01-NTCIR11-OV-MATH-AizawaA.pdf>
- Schubotz, Youssef, Markl, Cohl, "Challenges of Mathematical Information Retrieval in the NTCIR-11 Math Wikipedia Task," SIGIR 2015: <https://dl.acm.org/doi/10.1145/2766462.2767787>, PDF <https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=918116>
- Kohlhase et al., "MathWebSearch at NTCIR-10": <https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings10/pdf/NTCIR/MATH/04-NTCIR10-MATH-KohlhaseM.pdf>
- NTCIR-10 Math Pilot Task Overview (Aizawa, Kohlhase, Ounis 2013), metadata only: <https://www.semanticscholar.org/paper/NTCIR-10-Math-Pilot-Task-Overview-Aizawa-Kohlhase/162a0a79472fc92560d6be663921f979967d2500>
- Mansouri, Oard, Agarwal, Zanibbi, arXiv:2111.10504: <https://arxiv.org/abs/2111.10504>
- Zhong & Zanibbi, "Structural Similarity Search for Formulas Using Leaf-Root Paths in Operator Subtrees," ECIR 2019: <https://www.cs.rit.edu/~dprl/assets/files/Approach0_ECIR2019.pdf>
- ARQMath-3 overview §2 (related work on NTCIR): <https://ceur-ws.org/Vol-3180/paper-01.pdf>
