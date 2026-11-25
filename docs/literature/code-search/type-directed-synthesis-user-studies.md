# Type-directed synthesis and composition search: benchmarks and user studies (Hoogle+, TyGAR, Hoogle⋆, Prospector, PARSEWeb, InSynth, Perelman et al.)

- **Kind:** papers (tools whose query is a type or a `Source → Destination` type pair, and whose answer may be a *composition* of library functions)
- **Links:**
  - Hoogle+: James, Guo, Wang, Doshi, Peleg, Jhala, Polikarpova, "Digging for Fold: Synthesis-Aided API Discovery for Haskell", OOPSLA 2020 <https://dl.acm.org/doi/10.1145/3428273>, PDF <https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla20-hplus.pdf>
  - TyGAR / H+: Guo et al., "Program Synthesis by Type-Guided Abstraction Refinement", POPL 2020 <https://arxiv.org/abs/1911.04091>
  - Hoogle⋆: Guerra, Ferreira, Costa Seco, ECOOP 2023 <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2023.4>
  - Prospector: Mandelin, Xu, Bodík, Kimelman, "Jungloid mining", PLDI 2005 <https://doi.org/10.1145/1064978.1065018>
  - PARSEWeb: Thummalapenta & Xie, ASE 2007 <https://taoxie.cs.illinois.edu/publications/ase07-parseweb.pdf>
  - InSynth: Gvero, Kuncak, Kuraj, Piskac, "Complete completion using types and weights", PLDI 2013 <https://lara.epfl.ch/~kuncak/papers/GveroETAL13CompleteCompletionTypesWeights.pdf>
  - Perelman, Gulwani, Ball, Grossman, "Type-directed completion of partial expressions", PLDI 2012 <https://www.microsoft.com/en-us/research/publication/type-directed-completion-partial-expressions/>
- **Authors / org, date:** 2005–2023 (above).
- **Status:** research prototypes. Hoogle+ has an artifact ([Zenodo DOI](https://dl.acm.org/do/10.5281/zenodo.3544697/full/)).

Companion note: [type-directed-api-search.md](type-directed-api-search.md) covers single-declaration type search (Hoogle, rustdoc, Scaps, …).

## What it is

These tools go one step past Hoogle. The query is a type, or a type plus examples, and the answer is a **program built from library functions**. They are included because they hold the **only controlled user studies and the only published Hoogle query-log analysis** found for type-directed search. Their benchmarks are also the closest analogue to a Lean "which lemma(s) close this goal" track (`exact?`/`apply?`, see [../lean-tools/exact-apply.md](../lean-tools/exact-apply.md)).

## How it works (relevance notion only)

- **Hoogle+ / TyGAR / Hoogle⋆:** a candidate is correct if it type-checks against the query and (Hoogle+) passes the user's input-output tests. Usefulness is then judged separately.
- **Prospector:** a "jungloid query" is a pair `(Tin, Tout)`, and the answer is a unary chain of calls from `Tin` to `Tout` ([abstract](https://api.crossref.org/works/10.1145/1064978.1065018)).
- **PARSEWeb:** the same `Source → Destination` query form, answered by method-invocation sequences mined from code-search-engine results ([PDF](https://taoxie.cs.illinois.edu/publications/ase07-parseweb.pdf) §4).
- **InSynth, Perelman et al.:** the query is a program point with an expected type or a partial expression with holes. Candidates are ranked by weights or type-similarity features.

In every case a **type-correct answer is not automatically the right answer**. All of these papers found that type-only queries yield many meaningless or trivial candidates, and they had to add a second, human-grounded relevance judgement.

## Evaluation

### TyGAR (POPL 2020): benchmark from Hoogle logs

- **Query mining** ([§6](https://arxiv.org/abs/1911.04091)):
  - "We started with all queries made to Hoogle between 1/2015 and 2/2019. Among the **3.8M raw queries, 71K were syntactically unique**, and only **60K could not be exactly solved by Hoogle**."
  - Many of these were ill-formed or unrealizable (e.g. `a → b`). Unrealizable ones could not be detected automatically.
  - They kept popular queries (asked ≥5 times, **1,750**), pruned invalid ones by hand (**180**), and kept those realizable with their 291-component library (**24**).
  - They added **6** from the top-500 most-viewed Haskell StackOverflow questions and **17** curated "from our own experience". Total: **44**.
  - Stated reason for curating: "Hoogle queries do not come with expected solutions and also tend to be easy."
- **Relevance:** "ground truth solutions are not available for Hoogle benchmarks; we judge usefulness by manual inspection" (§2 footnote). Each synthesized solution among the first five was labeled *interesting* or not.
- **Metrics:** time to first solution (60 s timeout, median of 3 runs) and the fraction of the first-5 solutions that were interesting.
- **Result:** "Overall, 66/179 solutions produced by H+ were interesting (37%), compared with 65/189 for H-D (34%) and 26/199 for H-R (13%)". H-D and H-R are ablations without demand analysis and without relevant typing.

### Hoogle+ (OOPSLA 2020): benchmark, log-derived queries, survey, controlled user study

All numbers from [the PDF](https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla20-hplus.pdf).

- **Benchmark:** TyGAR's type-only queries, minus one (`ByteString`), plus the 5 user-study tasks: **45 benchmarks**.
- **Type inference from tests, real users:** **76** test-only queries were taken from user-study logs after removing ill-formed ones. The correct type ranked 1st in 39, 2nd in 4, and 3rd in 1; median rank 1; for 5 of 76 it was outside the top 10 (§6.1).
- **Type inference from tests, synthetic:** QuickCheck-generated tests (1–3 per benchmark, 6 runs), with rank of the true type stratified by **number of type variables (0–4) × number of tests**. Median rank was 1 or 2 in 12 of 15 cells, and no correct answer was in the top 10 for (3 vars, 1 test) and (4 vars, 1 test) (Fig. 9).
- **Elimination of meaningless and duplicate candidates:** the authors *manually labeled all meaningless results* of the baseline run and partitioned the rest into semantic equivalence classes. They then counted true positives, true negatives, and false negatives, split into "loss due to misclassification" vs. "loss due to testing overhead" (180 s vs. 360 s runs) (§6.2, Fig. 10).
- **Pre-study survey:** **151** Haskell programmers. 84 listed Hoogle as their first engine choice and 27 as second; among Hoogle users, 121 search by type and 107 by name. Google was first choice for only 37 (§7).
- **Controlled user study** (§7.1–7.2):
  - *Participants:* **30** (12 new to Haskell, 10 intermediate, 8 expert; 22 academic, 8 industry), recruited remotely and paid.
  - *Tasks:* 4 plus a training task, each with an English description and one example, e.g. `firstJust :: a → [Maybe a] → a`, `dedup :: Eq a => [a] → [a]`, `applyNTimes`, `inverseMap`. Limit: **8 minutes** per task.
  - *Design:* within-subjects, with control always first and task groups rotated (A/C vs. B/D), balanced by experience.
  - *Control condition:* **Hoogle plus a restricted GHCi** (no `:t`/`:i`/`:browse`, no extra imports, no open web search).
  - *Outcomes:* completion, time, correctness, query modality, and a feature-usefulness questionnaire. Statistical tests were Fisher's exact test (completion) and Mann-Whitney U (time), **with p < 0.1 as the significance threshold**.
  - *Completion:* out of 60 task attempts per tool, **29 were completed with Hoogle and 44 with Hoogle+** (+51%, p = .009). The gain was significant for tasks A (p = .003) and D (p = .080), not for C (p = .5) or B (p = .715).
  - *Time:* average time to complete improved by **35 s** overall (p = .004). Counting only non-timeouts the gain was 15 s, and for task D the direction reversed.
  - *Correctness:* 1 incorrect solution out of 73 completions.
  - *Query modality:* 115 Hoogle+ searches, only **22 type-only**. "Despite our pre-study survey discovering that searching Hoogle by type was the most popular way to query …, searching by type-only in our synthesis setting was uniformly the least popular mode."
  - *Barriers:* participants did not know the **intermediate types** (about half, per the authors). Hoogle results "often contain cruft from domain specific libraries". Users vaguely remembered a function but "Hoogle doesn't permit searches by documentation" (§7.3).

### Hoogle⋆ (ECOOP 2023)

- Reuses TyGAR's **44** benchmarks (RQ1) and adds **26** new ones needing constants or λ-abstractions, mostly adapted from StackOverflow ([PDF](https://drops.dagstuhl.de/storage/00lipics/lipics-vol263-ecoop2023/LIPIcs.ECOOP.2023.4/LIPIcs.ECOOP.2023.4.pdf) §6).
- Metrics are solved count, time to first solution, and number of solutions. On the new set, "Hoogle⋆ solves 22 out of 26 benchmarks, whereas Hoogle+ solves only 3".
- This is an example of benchmark drift. A new benchmark was built to exercise the new capability, the same bias Scaps admitted (see [companion note](type-directed-api-search.md)).

### Java / Scala / C# composition search

- **Prospector (PLDI 2005):** "found the desired solution for **18 of 20** problems". A user study found "programmers solved programming problems more quickly and with more reuse" ([abstract](https://api.crossref.org/works/10.1145/1064978.1065018)). The full paper was not read, so the study size and metrics are unverified. It shows only its first 12 results (per [PARSEWeb §6.2](https://taoxie.cs.illinois.edu/publications/ase07-parseweb.pdf)).
- **PARSEWeb (ASE 2007),** [PDF](https://taoxie.cs.illinois.edu/publications/ase07-parseweb.pdf) §6:
  - *Four evaluations:* (1) forum problems; (2) **queries extracted from a real project**, the first 10 maximal `Source → Destination` queries in the largest file of Eclipse GEF's Logic example, compared with Prospector, Strathcona, and raw Google Code Search; (3) **12 tasks reused from the XSnippet evaluation**; (4) ablations of internal techniques.
  - *Success criterion:* "the final code can be compiled and executed, and the required functionality is enabled with at least one suggested solution".
  - *Results:* PARSEWeb failed 1 of the 12 tasks and Prospector failed 5. The authors quote Bajracharya et al. that there is a "need (but lack) of a benchmark for open source code search".
- **InSynth (PLDI 2013),** [PDF](https://lara.epfl.ch/~kuncak/papers/GveroETAL13CompleteCompletionTypesWeights.pdf) §7:
  - *Benchmark:* "no standardized set of benchmarks … so we constructed our own": **50** examples, mostly from java2s.com, translated to Scala.
  - *Protocol:* **remove an expression from existing code and ask the tool to reconstruct it** at that program point. Imports were widened to enlarge the search space.
  - *Results:* the expected expression was in the **top 10 in 48/50 (96%)** and **rank 1 in 32/50 (64%)**, averaging about 145 ms. The weight corpus was derived from code disjoint from the benchmarks.
- **Perelman et al. (PLDI 2012):** "In an automated experiment on mature C# projects, we show our algorithm can place the intended expression in the **top 10 choices over 80%** of the time" ([MSR abstract](https://www.microsoft.com/en-us/research/publication/type-directed-completion-partial-expressions/)). The same hole-from-real-code protocol; details not read (unverified).

## Relevance to lean-explore-bench

1. **Hole-from-real-code is the right automated protocol for a goal/type track.** InSynth and Perelman delete an expression from mature code and score the rank of the original. For Lean: take a Mathlib proof step `exact foo …` or `apply foo`, pose its goal (or the Loogle pattern of `foo`'s statement) as the query, and score the rank of `foo`. This is the same as the proof-state track in [../lean-tools/exact-apply.md](../lean-tools/exact-apply.md), and it gives free, unambiguous gold labels at scale.
   - **Caveat from TyGAR and Hoogle+:** type-correct alternatives exist. Other lemmas may also close the goal, so accept "any verified closer" as a secondary label, which is checkable by `exact`, rather than penalizing them.
2. **Log-mined queries need heavy filtering, and they skew easy.** TyGAR went 3.8M → 24 usable, and the authors say log queries "tend to be easy" and lack gold answers. A Loogle-log or Zulip-`@loogle` query set will need (a) validity filtering, (b) gold labeling, and (c) supplementation with curated hard queries. Report the funnel.
3. **Budget for a small human study later, and copy Hoogle+'s design:**
   - within-subjects, 30 participants, 4 timed tasks (8 min), rotated task groups, experience-balanced;
   - baseline = the tool people actually use (Loogle + `#check`/`exact?`, analogous to Hoogle + GHCi);
   - outcomes = completion, time, and query modality.

   Its key finding transfers: **users who say they search by type mostly didn't when offered alternatives**, and they struggled to write intermediate types. Pattern queries have a hidden authoring cost that offline recall numbers miss. An "LLM writes the Loogle query" condition would measure this cheaply.
   - *Statistics caveat:* p < 0.1 and n = 30 with 2 tasks per condition is weak. Pre-register tests and report effect sizes (see [../statistics/effect-sizes-power-and-topic-set-size.md](../statistics/effect-sizes-power-and-topic-set-size.md)).
4. **Stratify by difficulty knobs the way Hoogle+ did.** It reports by number of type variables × number of examples. For Lean patterns, the analogous knobs are: number of metavariables `?a`; number of `_` wildcards; whether the conclusion is anchored with `⊢`; and how many constants are named.
5. **Separate "found something type-correct" from "found something useful".** TyGAR's first-5 "interesting" rate (37%) is essentially Precision@5 under a human usefulness judgement. For Lean, the analogue is a trivial-lemma filter (e.g. `rfl`-level, `id`-like, or `Iff.rfl` hits) when scoring `exact?`-style or pattern-based engines.

## Open questions

- Is the Hoogle 2015–2019 log, or TyGAR's 180 validated queries, available? That could calibrate how realistic generated Lean patterns look (unverified).
- Prospector's user-study size and metrics (full paper not read).

## Sources

- Hoogle+ OOPSLA 2020: <https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla20-hplus.pdf>, <https://dl.acm.org/doi/10.1145/3428273>
- TyGAR POPL 2020: <https://arxiv.org/abs/1911.04091>
- Hoogle⋆ ECOOP 2023: <https://drops.dagstuhl.de/storage/00lipics/lipics-vol263-ecoop2023/LIPIcs.ECOOP.2023.4/LIPIcs.ECOOP.2023.4.pdf>
- Prospector abstract (Crossref): <https://api.crossref.org/works/10.1145/1064978.1065018>
- PARSEWeb: <https://taoxie.cs.illinois.edu/publications/ase07-parseweb.pdf>
- InSynth: <https://lara.epfl.ch/~kuncak/papers/GveroETAL13CompleteCompletionTypesWeights.pdf>
- Perelman et al.: <https://www.microsoft.com/en-us/research/publication/type-directed-completion-partial-expressions/>
