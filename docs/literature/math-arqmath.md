# ARQMath (CLEF 2020-2022): Answer Retrieval for Questions on Math

- **Kind:** benchmark / dataset (shared-task test collection)
- **Links:** lab site <https://www.cs.rit.edu/~dprl/ARQMath/>; overviews ARQMath-1 (CLEF 2020) <https://user.eng.umd.edu/~oard/pdf/clef2020overviewproc.pdf>, ARQMath-2 (CLEF 2021) <https://ceur-ws.org/Vol-2936/paper-01.pdf>, ARQMath-3 (CLEF 2022) <https://ceur-ws.org/Vol-3180/paper-01.pdf>; code <https://github.com/ARQMath/ARQMathCode>; methodology follow-up <https://arxiv.org/abs/2111.10504>
- **Authors / org, date:** Richard Zanibbi, Behrooz Mansouri, Anurag Agarwal (RIT), Douglas W. Oard (UMD); Vít Novotný (Masaryk) joined for ARQMath-3. 2020-2022.
- **Status:** Lab ended after ARQMath-3 ("the time has now come to end this lab at CLEF") [ARQMath-3 §7]. Collection, topics, qrels and runs are public (Google Drive / GitHub per [ARQMath-3 §3, §4.2]). Still used as a test set, e.g. inside MIRB (see `bench-mirb.md`).

## What it is

Three yearly test collections built from Math Stack Exchange (MSE). The searched collection is MSE questions and answers from 2010-2018, taken from the 1 March 2020 Internet Archive snapshot: about 1M questions and 28M formulae, each formula with LaTeX, Presentation MathML (SLT) and Content MathML (OPT) versions [ARQMath-3 §3]. Topics are later MSE questions: 2019 for ARQMath-1, 2020 for ARQMath-2 and 2021 for ARQMath-3 [ARQMath-1 §4.1; MIRB §3.2](https://arxiv.org/abs/2505.15585).

Tasks [ARQMath-3 §1]:
- **Task 1, answer retrieval.** Given an MSE question, rank up to 1,000 answer posts from the collection.
- **Task 2, formula retrieval.** Given one formula from a Task 1 question, plus that question as context, rank up to 1,000 formula instances from any post.
- **Task 3, open-domain QA (ARQMath-3 pilot).** Return one answer of at most 1,200 Unicode characters. It can be extracted from anywhere or generated.

## How it works (evaluation design)

This section describes the evaluation protocol, not the systems.

**Topic construction (Task 1).**
- ARQMath-1 required that a candidate question have text, at least one formula, and at least one duplicate or related post. The organizers then drew 101 questions by stratified manual sampling over formula count, Flesch reading ease, asker reputation and tags. 77 of these were evaluated [ARQMath-1 §4.1].
- ARQMath-3 used stricter rules: at least one formula and at least one known *duplicate* (flagged by MSE moderators) in the 2010-2018 collection. 3,313 questions qualified. Soft criteria narrowed these to 139, and 100 were picked by hand for diversity [ARQMath-3 §4.1].
- The reason for the duplicate requirement: in ARQMath-2, 11 topics without known duplicates were included experimentally, and 9 of them ended up with no relevant answers from any system [ARQMath-3 §4.1].
- Topics were stratified by type (ARQMath-3: 49 proof, 28 computation, 23 concept), difficulty (24 hard, 55 medium, 21 easy) and dependence (12 text, 28 formula, 60 both). 14 topics had multiple parts, and a highly relevant answer to one of those had to address every part [ARQMath-3 §4.1].
- Links to duplicates were withheld from participants [ARQMath-3 §4.1].

**Topic construction (Task 2).**
- One formula was chosen per Task 1 topic, preferring the title. Selection was a heuristic stratified sample over complexity (low/medium/high, labelled by a mathematician) and over "elements" such as integrals, limits and matrices [ARQMath-3 §5, §5.1].

**Pooling.**
- *Task 1.* ARQMath-1 pooled to depth 50 for baselines, primary and manual runs, and to depth 20 for alternate runs. That gave about 500 answers per topic [ARQMath-1 Fig. 2, §4.3]. ARQMath-2 pooled to depth 45 for primary runs and 15 for alternates, about 448 answers per topic [ARQMath-2 §4.4]. ARQMath-3 pooled to depth 45 for primary runs and 20 for alternates. Task 3 answers joined the same pools, which averaged 464 posts per topic. Pools were deduplicated and shown to assessors in random order [ARQMath-3 §4.4].
- *Task 2.* Pools are counted in **visually distinct formulae** (clusters of identical SLT, or of identical LaTeX with whitespace removed), not in instances. Each run was walked down until k distinct formulae had been seen. ARQMath-1 used k=25 for primary runs and k=10 for others. ARQMath-2 used 20 and 10. ARQMath-3 used 25 and 15 [ARQMath-1 §5.4; ARQMath-2 §5; ARQMath-3 §5.4].
- At most 5 instances per visual cluster were judged. ARQMath-3 chose which ones by reciprocal-rank voting across runs [ARQMath-3 §5.4].
- Manual runs were invited explicitly "to increase the quality and diversity of the pool" [ARQMath-3 §4.2].

**Relevance scale (0-3)** [ARQMath-3 Table 2]:
- *Task 1:* 3 = sufficient to answer the complete question on its own; 2 = provides some path towards the solution; 1 = could be useful for finding or interpreting an answer; 0 = no pertinent information. A post that only restates the question counts as 0.
- *Task 2:* 3 = just as good as finding an exact match; 2 = useful but not as good; 1 = some chance of finding something useful; 0 = not expected to be useful.
- Assessors judge from the viewpoint of an expert (modelled as a math professor) and may not use links outside the collection [ARQMath-3 §4.4].
- Besides the four grades there are two extra options, "System failure" and "Do not know". Both are treated as unjudged [ARQMath-3 §4.5-4.6].
- Task 2 relevance is contextual. From ARQMath-2 on, a formula visually identical to the query can be judged non-relevant if its post gives it a different meaning. In ARQMath-1, exact matches were always judged highly relevant [ARQMath-3 §5.6; Mansouri et al. 2021](https://arxiv.org/abs/2111.10504).

**Assessors and agreement.**
- ARQMath-3 recruited 44 interested students, invited 11 to a trial, and selected 9 math/CS students after an expert mathematician reviewed their trial judgments. Assessors went through several Zoom training rounds using earlier-year qrels, with a math professor present [ARQMath-3 §4.5].
- Tool: Turkle, a self-hosted Mechanical Turk clone. Assessors could open "thread" links for background but were told to judge only the post itself [ARQMath-3 §4.5].
- Average judging time per item: 63.1 s per answer in ARQMath-1 Task 1 and 44.1 s in ARQMath-3 Task 1; 26.6 s per formula instance in ARQMath-3 Task 2 [ARQMath-1 §4.4; ARQMath-3 §4.5, §5.4].
- Post-hoc Cohen's κ, Task 1:
  - ARQMath-1: 0.34 four-way at the end of training [ARQMath-1 §4.4].
  - ARQMath-3: 0.24 four-way and 0.25 binary (H+M) [ARQMath-3 §4.5].
- Post-hoc Cohen's κ, Task 2:
  - ARQMath-1: 0.83 on two jointly discussed pools, then 0.47 on dual-assessed topics [ARQMath-1 §5.4].
  - ARQMath-2: 0.329 four-way and 0.694 H+M after assessment. During training rounds the figures were 0.281/0.417, rising to 0.467/0.565 [ARQMath-2 §5].
  - ARQMath-3: 0.44 four-way and 0.51 H+M [ARQMath-3 §5.4].
- Mansouri et al. report formula κ of 0.48 (ARQMath-1) and 0.69 (ARQMath-2) [2111.10504 §3]. The ARQMath-2 figure matches the H+M post-assessment value above.

**Topic filtering.** Topics with zero or one H+M relevant item were dropped because single-relevant topics make MAP′ coarsely quantized. The result was 77 of 80 topics kept in ARQMath-1 and 78 of 80 in ARQMath-3 Task 1 [ARQMath-1 §4.4; ARQMath-3 §4.5]. Task 2 dropped topics with fewer than two relevant formulae [ARQMath-1 §5.4].

**Metrics.**
- The primary metric is **nDCG′**: nDCG@1000 computed after removing unjudged items from the run (Sakai & Kando).
- Secondary metrics are **MAP′** and **P′@10**, both binarized H+M (grades 2-3 count as relevant, the TREC convention) [ARQMath-3 §4.6].
- The organizers' stated reason for the prime variants: to be fair to "future systems that may find different documents". They cite better discriminative power and ranking stability than bpref, and note that nDCG′ can use graded relevance directly [ARQMath-1 §4.5; ARQMath-3 §4.6].
- Task 2 scoring maps each instance to its visual ID, dedupes from the top, and gives each cluster the max grade over its judged instances [ARQMath-3 §5.6].
- Task 3 is scored by Average Relevance (0-3) and P@1. There are also two automatic measures: lexical overlap (token F1 with MathBERTa tokens) and contextual similarity (BERTScore) against known relevant answers, excluding each team's own pool contributions. Against manual AR, lexical overlap had Pearson r = 0.837 and Kendall τ = 0.736; contextual similarity had r = 0.839 and τ = 0.670 [ARQMath-3 §6.4-6.5].

**Progress testing.** ARQMath-3 teams also re-ran on the ARQMath-1 and -2 topics (158 topics in all). The organizers caution that these topics were available for training [ARQMath-3 §4.7].

## Evaluation (reported numbers)

**ARQMath-3 Task 1 (78 topics)** [ARQMath-3 Table 3]:
- Best manual run: approach0 `fusion_alpha05`, nDCG′ 0.508, MAP′ 0.216, P′@10 0.345.
- Best automatic run: MSM `Ensemble_RRF`, nDCG′ 0.504.
- Baselines (nDCG′ / MAP′ / P′@10):
  - Terrier TF-IDF: 0.272 / 0.064 / 0.124
  - Tangent-S: 0.159 / 0.039 / 0.086
  - "Linked MSE posts" oracle (answers to moderator-flagged duplicates, ranked by votes): 0.106 / 0.051 / 0.168. The same oracle scored 0.279 nDCG′ on ARQMath-1.
- Because some topics have fewer than 10 H+M relevant answers, the highest achievable P′@10 is 0.95.

**ARQMath-3 Task 2 (76 topics)** [ARQMath-3 Table 4]:
- Best manual run: approach0 `fusion_alph05`, nDCG′ 0.720, MAP′ 0.568, P′@10 0.688.
- Best automatic run: DPRL `TangentCFT2ED`, nDCG′ 0.694.
- Tangent-S baseline: 0.540 / 0.336 / 0.511.
- Highest achievable P′@10: 0.93.

**ARQMath-3 Task 3 (78 topics)** [ARQMath-3 §6.5]:
- The GPT-3 (text-davinci-002) baseline had the best Average Relevance, 1.346 on the 0-3 scale.
- Best manual extractive run: approach0, AR 1.282.
- Best automatic extractive run: DPRL, AR 0.462.

**Scale.** Pools averaged 446.8 judged answers per Task 1 topic and 152.3 visually distinct formulae per Task 2 topic. Relevant items (H+M+L) averaged 100.8 answers and 63.2 formulae per topic [ARQMath-3 §4.5, §5.4].

## Relevance to lean-explore-bench

**What to reuse:**
- *A 0-3 graded scale anchored on task utility.* "Sufficient on its own" / "a path to it" / "could help" / "no". This maps well onto declaration search. For example: 3 = exactly the lemma needed (or a trivial restatement); 2 = a more general or special form that gets you there with little work; 1 = a related API that helps you locate the right one; 0 = unrelated.
- *Judge from a fixed persona* (ARQMath used an expert, a "math professor"), not from a guess about the asker. Give judges background links but tell them to judge the item itself.
- *Report prime metrics (nDCG′, P′@k) alongside standard ones.* We will evaluate engines that did not contribute to our pools, and new Mathlib versions will add declarations. Prime metrics keep scores comparable when unjudged items appear.
- *Deduplicate by equivalence class before pooling and scoring.* ARQMath clustered "visually distinct formulae" [2111.10504]. Our analogue: collapse aliases, `@[deprecated]` redirects, `_root_` versus namespaced duplicates, and `iff`/`mp` variants that a user would treat as one hit. Pool by class, then score each class by the max grade of its judged members.
- *Pool at mixed depths* (deep for primary runs, shallow for alternates). *Add manual or interactive runs* to diversify the pool.
- *Drop topics with fewer than two relevant items.* *Stratify topics* by type and difficulty, and record the labels so results can be broken down per stratum.
- *Report per-year assessor κ, both graded and binarized.* ARQMath shows four-way κ can be low (0.24-0.34 for Task 1) while system rankings still hold up. A low κ is not by itself a reason to throw out graded judgments.
- *Keep training and test topics separate.* Progress-test sets are contaminated once released.

**What it gets wrong or leaves out:**
- Topics are sampled only from questions that already have a moderator-flagged duplicate. That biases toward easier, more common questions, and the organizers acknowledge it [ARQMath-3 §4.1]. The analogue for us: sampling queries only from Mathlib declarations that already have docstrings, or that appear in Zulip threads, would bias toward well-documented API.
- The duplicate-link oracle is a weak relevance signal. It scored nDCG′ 0.106 on ARQMath-3. Silver labels from community links should not replace pooled judgments.
- MIRB's reuse of ARQMath rescores only within each topic's judged pool (a "dynamic corpus" of annotated documents) [MIRB §3.2](https://arxiv.org/abs/2505.15585). That turns full retrieval into reranking and inflates scores relative to the original task.

## Open questions

- Should we adopt a Task 3-style track (generated answers)? If LLM agents return synthesized Lean terms rather than declaration names, the lexical-overlap trick might extend to comparing returned names against the judged-relevant set.

## Sources

- ARQMath-1 overview (Zanibbi, Oard, Agarwal, Mansouri, CLEF 2020 LNCS): <https://user.eng.umd.edu/~oard/pdf/clef2020overviewproc.pdf>; Springer <https://link.springer.com/chapter/10.1007/978-3-030-58219-7_15>
- ARQMath-2 overview working notes (CEUR Vol-2936): <https://ceur-ws.org/Vol-2936/paper-01.pdf>; Springer <https://link.springer.com/chapter/10.1007/978-3-030-85251-1_17>
- ARQMath-3 overview working notes (CEUR Vol-3180): <https://ceur-ws.org/Vol-3180/paper-01.pdf>; LNCS version <https://link.springer.com/chapter/10.1007/978-3-031-13643-6_20>
- Mansouri, Oard, Agarwal, Zanibbi, "Effects of context, complexity, and clustering on evaluation for math formula retrieval," arXiv:2111.10504: <https://arxiv.org/abs/2111.10504>
- MIRB (Ju & Dong 2025), for how ARQMath is re-packaged: <https://arxiv.org/abs/2505.15585>
- Section and table references in brackets point to the overview PDFs above, which were read directly (pdftotext).
