# Tip-of-the-tongue query analysis, ToT datasets, and known-item metrics

- **Kind:** paper / benchmark / dataset survey note
- **Links:**
  - Arguello et al., "Tip of the Tongue Known-Item Retrieval: A Case Study in Movie Identification", CHIIR 2021: <https://arxiv.org/abs/2101.07124> (MS-ToT data: <https://github.com/microsoft/Tip-of-the-Tongue-Known-Item-Retrieval-Dataset-for-Movie-Identification>)
  - Bhargav, Sidiropoulos, Kanoulas, "'It's on the tip of my tongue': A new dataset for known-item retrieval" (Reddit-TOMT), WSDM 2022: <https://doi.org/10.1145/3488560.3498421>, data <https://github.com/samarthbhargav/tomt-data>
  - Fröbe, Schmidt, Hagen, "A Large-Scale Dataset for Known-Item Question Performance Prediction" (TOMT-KIS), QPP++ @ ECIR 2023: <https://downloads-cf.webis.de/publications/papers/froebe_2023c.pdf>
  - Lin, Lo, Gonzalez, Klein, "Decomposing Complex Queries for Tip-of-the-tongue Retrieval" (WhatsThatBook), 2023: <https://arxiv.org/abs/2305.15053>, data <https://github.com/kl2806/whatsthatbook>
  - Bhargav, Schuth, Hauff, "When the Music Stops: Tip-of-the-Tongue Retrieval for Music", SIGIR 2023: <https://arxiv.org/abs/2305.14072>
  - CH-Wang et al., "Browsing Lost Unformed Recollections" (BLUR), 2025: <https://arxiv.org/abs/2503.19193>
  - Craswell & Hawking, "Overview of the TREC-2002 Web Track" (named-page finding): <https://trec.nist.gov/pubs/trec11/papers/WEB.OVER.pdf>
- **Authors / org, date:** see individual links, 2002–2025.
- **Status:** All datasets listed are public, except BLUR's private test split and some CQA text restrictions (unverified per dataset).

## What it is

Three strands, each of which shapes a Lean "I know a lemma like this exists" query track:
1. **What real ToT requests look like.** Arguello et al. coded 1,000 real requests.
2. **Datasets harvested from community Q&A (CQA) sites**, with the "solved" answer as the single gold item.
3. **Metrics and statistics for single-answer (known-item) evaluation**, going back to TREC named-page finding.

## How it works

### 1. Anatomy of ToT requests (Arguello et al. 2021)

- **Definition.** A ToT need is "an item identification task where the searcher has previously experienced or consumed the item but cannot recall a reliable identifier" [§1].
- **Data.**
  - 2,072 solved questions from "I Remember This Movie…" (2013–2018), restricted to solved questions "because we could not confirm that all questions in fact referred to real movies" [§3].
  - 1,000 of them were coded at sentence level: 8,030 sentences, 34 codes.
  - The codes were developed in three phases with Cohen's κ checks; codes with κ ≤ 0.20 were redefined or dropped. Final agreement: 2 codes fair, 5 moderate, 16 substantial, 9 almost perfect [§4.1].
- **Code frequencies** (share of sentences, not mutually exclusive) [Tables 1–3]:
  - Movie content: character 51.2%, scene 36.5%, object 26.7%, category 25.1%, plot summary 10.8%, release date 5.4%, quote/dialogue 1.5%.
  - Context (episodic memory): temporal context 8.6%, physical medium 5.4%.
  - Uncertainty/hedging: **35.4%**.
  - Social niceties: 10.8%.
  - Relative comparison ("looks like Kevin Bacon"): 3.0%.
  - Previous failed search: 1.5%.
- **Retrieval findings** [§1 summary]:
  - Conventional IR "can successfully leverage descriptions of the movie, but not descriptions of the context".
  - It is "surprisingly robust to expressions of uncertainty".
  - The previous-search sentences carry useful *negative* evidence ("nothing on her filmography page rings any bells") [§4.3].
- **Earlier false-memory evidence.** Hagen et al. 2015 found "false memories" in 240 of 2,755 Yahoo! Answers known-item questions (as summarised in [§2]).

### 2. CQA-derived ToT datasets

| Dataset | Source | Size | Answer extraction | Notes |
|---|---|---|---|---|
| MS-ToT | irememberthismovie.com | 1,000 coded pairs (from 2,072 solved) | asker-marked solved | source of TREC ToT movie queries [Arguello 2021 §3–4] |
| Reddit-TOMT | r/tipofmytongue, movies + books | about 15K query–item pairs | asker replied exactly "Solved!" and the answer had exactly one Wikipedia, IMDb or GoodReads link (as described by [TOMT-KIS §2](https://downloads-cf.webis.de/publications/papers/froebe_2023c.pdf)) | TREC 2023 suggested training data |
| TOMT-KIS | all of r/tipofmytongue | **1.28M questions, 47% with an identified answer** | moderator "solved" flag plus lexical patterns ("solved", "thank", "yes", "amazing") | built for query-performance prediction; "performance" = time until solved. None of 7 pre-retrieval predictors worked [TOMT-KIS abstract, §2] |
| WhatsThatBook | GoodReads "What's the name of that book?" group | 14,441 query–book pairs, split 11,552 / 1,444 / 1,445 | thread tagged SOLVED with a pinned link | document collection = the 14,441 gold books only [Lin 2023 §3] |
| ToT-Music | r/tipofmytongue | 2,278 information needs | not checked | multi-modal needs (lyrics, audio, text); LLM reformulations were *worse* than using the full need as the query [abstract](https://arxiv.org/abs/2305.14072) |
| BLUR | human-validated, multi-modal, multilingual | 573 questions; 350 released on a leaderboard (answers withheld for 250); the rest private | not checked | humans average 98%, best system about 56% [abstract](https://arxiv.org/abs/2503.19193) |

**How ToT queries differ from ordinary queries** [Lin 2023 Table 1]:

| Dataset | Mean BPE tokens | Lexical overlap with gold |
|---|---|---|
| MS MARCO | 7.7 | 0.55 |
| TOMT | 136.5 | 0.25 |
| WhatsThatBook | 156.2 | 0.19 |

On WhatsThatBook the Recall@5 scores were: BM25 8.3, DPR 13.8, Contriever 26.5, Contriever plus query decomposition into cover/title/date "clues" 28.4 [Lin 2023 Table 3].
- Lin et al. "use Recall@K metric as our primary metric since each query has exactly one correct item" [§4.2]. With one gold item, this is Success@K.

**Caution.** WhatsThatBook's corpus contains only gold items, so it has no distractor documents. Scores are therefore not comparable with open-corpus settings such as TREC ToT's 6.4M-page Wikipedia corpus.

### 3. Known-item metrics, from TREC named-page finding onward

- **TREC-2002 named-page finding** [Craswell & Hawking §2.4, §2.8, Table 3]:
  - Task: 150 topics over the 1.25M-page .GOV crawl, each a query naming one specific page.
  - Main measure: "the reciprocal rank of the first correct answer". Success@10 was also reported.
  - Qrels: the only assessment was finding *duplicate URLs* of the named page. Most topics had one correct answer, 16 had two and 2 had three.
  - Results: 70 runs from 18 groups; the best MRR was 0.719.
  - This is the template for "one gold item plus its duplicates" qrels. It maps onto Mathlib aliases and `@[deprecated]` synonyms.
- **NTCIR-11 Math Wikipedia known-item subtask.** Automatically generated formula queries, scored by MRR and success at any rank. It is covered in `../math-ir/ntcir-math.md` and not repeated here.
- **TREC ToT.** Official NDCG@1000, plus NDCG@10, MRR@1000 and R@1000 (`known-item-trec-tot.md`).
  - With one relevant item, NDCG@k = DCG@k [TREC 2023 §2]. That equals 1/log2(r+1) if the item is at rank r ≤ k and 0 otherwise. This is my derivation from the standard DCG formula.
  - So NDCG@k and RR differ only in the discount: 1/log2(r+1) vs 1/r. NDCG penalises deep ranks less.
  - Empirically the two metrics were strongly correlated across TREC 2025 runs [TREC 2025 §4.2].

## Evaluation

The numbers are quoted inline above.

**Statistical implications of single-answer metrics.** These draw on the repository's statistics notes.
- **RR is among the least sensitive one-answer metrics.**
  - Sakai's ordering is P(+) ≥ O-measure ≥ NWRR ≥ RR.
  - RR has high Type III (wrong-direction) error rates.
  - See `../statistics/metric-scales-and-correlation.md`.
- **Success@k is binary per query.** Its per-query differences are in {−1, 0, +1}. With 30% discordant queries, detecting a 0.05 difference needs roughly 935 queries, and a 0.10 difference about 228 (`../statistics/effect-sizes-power-and-topic-set-size.md`).
- **Floor effects waste queries.**
  - TREC 2023 had a median NDCG@10 of 0 on 129 of 150 topics ([TREC 2023 §4.3](https://trec.nist.gov/pubs/trec32/papers/Overview_tot.pdf)).
  - Queries that no system solves add no discriminative power, which is standard paired-test reasoning.
- **MRR-based validation was noisier.** When synthetic queries were validated by system-ranking agreement, MRR-based Kendall τ was usually below NDCG-based τ in the multilingual study (for example 0.639 vs 0.788 for Chinese), though not always in the movie study ([arXiv:2604.21096](https://arxiv.org/abs/2604.21096); [arXiv:2502.17776](https://arxiv.org/abs/2502.17776) Table 1). See `known-item-tot-query-simulation.md`.
- **A single gold item under-credits good alternatives.** This is the MS MARCO "better than perfect" problem (`../ir-evaluation/trec-pooling-and-relevance-judgments.md`). TREC 2002's duplicate-URL qrels are the minimal fix.

## Relevance to lean-explore-bench

**Query analysis to replicate for Lean.**
- Code about 200–300 real Lean "is there a lemma…" requests with a scheme adapted from Arguello's. Candidate codes:
  - statement content (objects, hypotheses, conclusion shape);
  - algebraic/typeclass context;
  - *proof context* (the goal the user is stuck on), which plays the role of episodic memory;
  - hedging;
  - relative comparison ("the `Finset` version of `List.sum_le_sum`");
  - previous search ("`exact?` times out", "Loogle found nothing");
  - partial name recall ("something like `..._of_le`").
- The last code, partial name recall, is Lean-specific and probably common. It deserves its own stratum, because it favours name-matching engines.
- Measure inter-annotator κ per code as Arguello did. Use the code distribution both to describe the benchmark and to validate synthetic queries (EMD, as in He et al. 2025).

**Harvesting real ToT queries for Lean.**
- The Lean analogue of CQA "solved" threads is a Zulip `#new members` / `#mathlib4` / `#Is there code for X?` (channel names (unverified)) thread where a reply names a declaration and the asker confirms it.
- Use the TOMT-KIS approach: a precision-oriented heuristic for the confirmation (asker replies "thanks" or "that's it" to a post containing a backticked declaration name), then manual verification.
- Expect a low solved rate. TOMT-KIS found answers for only 47%. Unsolved questions are still useful: they show where search fails, and they can seed "no known answer" negatives.
- Resolve every answer to a declaration at a pinned Mathlib commit, and record renames. This is Mathlib's version of Reddit-TOMT's "exactly one link" filter.

**Metrics for a Lean ToT track:**
- Primary: **MRR@10**.
- Always also report **Success@1 / @5 / @10**, and **NDCG@10** for comparability with TREC ToT.
- Report the **median first-relevant rank** (capped) as the effort-interpretable number.
- Use qrels in the TREC 2002 style: the gold declaration plus its *accepted equivalents* (aliases, deprecated synonyms, the `iff` or `symm` twin), each counted as correct. Keep a separate graded ad hoc track for "useful but not the one" results.
- Size the query set for the binary metrics, not for MRR alone. That means several hundred queries per stratum if pairwise engine differences of about 0.05–0.10 are to be tested.

## Open questions

- How often do Lean users arrive with *partial name recall* rather than pure description? Real Zulip data is needed to answer this.
- Should queries that were solved on Zulip only through discussion (clarifying questions) count as single-shot queries? Arguello and TOMT-KIS take only the initial post. BLUR and DETOUR ([arXiv:2602.00352](https://arxiv.org/abs/2602.00352)) move toward multi-turn evaluation, which fits agentic Lean search.
- For the most common "does Mathlib have X?" requests, what share of real answers is "no, it doesn't exist"? A pure known-item benchmark cannot score the correct abstention (see `no-answer-qa-rag-abstention.md`).

## Sources

- Arguello et al. 2021: <https://arxiv.org/abs/2101.07124>
- Bhargav et al. 2022 (Reddit-TOMT): <https://doi.org/10.1145/3488560.3498421>; <https://github.com/samarthbhargav/tomt-data>
- Fröbe et al. 2023 (TOMT-KIS): <https://downloads-cf.webis.de/publications/papers/froebe_2023c.pdf>
- Lin et al. 2023 (WhatsThatBook): <https://arxiv.org/abs/2305.15053>
- Bhargav et al. 2023 (ToT-Music): <https://arxiv.org/abs/2305.14072>
- CH-Wang et al. 2025 (BLUR): <https://arxiv.org/abs/2503.19193>
- DETOUR 2026: <https://arxiv.org/abs/2602.00352>
- Craswell & Hawking, TREC-2002 Web Track overview: <https://trec.nist.gov/pubs/trec11/papers/WEB.OVER.pdf>
- TREC 2023 / 2025 ToT overviews: <https://trec.nist.gov/pubs/trec32/papers/Overview_tot.pdf>, <https://arxiv.org/abs/2601.20671>
- He et al. 2025 / 2026: <https://arxiv.org/abs/2502.17776>, <https://arxiv.org/abs/2604.21096>
