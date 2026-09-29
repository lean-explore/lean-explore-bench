# TREC Tip-of-the-Tongue (ToT) track, 2023–2025

- **Kind:** benchmark / dataset (shared-task test collections)
- **Links:**
  - Track site: <https://trec-tot.github.io>
  - TREC 2023 overview: <https://trec.nist.gov/pubs/trec32/papers/Overview_tot.pdf>
  - TREC 2024 overview: <https://trec.nist.gov/pubs/trec33/papers/Overview_tot.pdf>
  - TREC 2025 overview: <https://arxiv.org/abs/2601.20671>
  - Baselines and runs: <https://github.com/TREC-ToT/bench/>
  - MS-ToT source dataset: <https://github.com/microsoft/Tip-of-the-Tongue-Known-Item-Retrieval-Dataset-for-Movie-Identification>
  - Follow-on NTCIR ToT task (multilingual): <https://ntcir-tot.github.io>, described in [arXiv:2604.21096](https://arxiv.org/abs/2604.21096)
- **Authors / org, date:** Arguello, Bhargav, Diaz, Kanoulas, Mitra (2023). He and T. E. Kim joined in 2024. Arguello, Diaz, Fröbe, Kim, Mitra (2025). Run at NIST TREC 2023, 2024 and 2025.
- **Status:** Three editions have finished. The queries, qrels, baselines and runs are public through the track site and the `TREC-ToT/bench` repo. The organizers moved on to a multilingual NTCIR ToT task ([arXiv:2604.21096](https://arxiv.org/abs/2604.21096)).

## What it is

A known-item ad hoc retrieval task. The searcher has encountered an item before but "does not reliably recall an identifier" [2025 abstract]. Every query has exactly one correct Wikipedia page, and systems return up to 1,000 page IDs "with the correct answer ranked as high as possible" [2023 §2; 2025 §2].

This matches the Lean case "I know a lemma like this exists but not its name". The notes below concentrate on how the organizers *built* and *validated* the query sets, because that is the part we can reuse.

## How it works (task and collection design by year)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Domains | movies (incl. TV) | movies, celebrities, landmarks | general, 53 entity types |
| Corpus | 231,618 Wikipedia pages in the "audiovisual works" category (Wikipedia dump of 2023-01-01) | 3,185,450 Wikipedia articles | 6,407,814 Wikipedia articles |
| Train / dev | 150 / 150 MS-ToT | 150 train + 2×150 dev, all MS-ToT | 143 train (MS-ToT) + 3 dev sets (2023 dev, 2023 test, 2024 test) |
| Test | 150 MS-ToT | 600: 150 MS-ToT + 450 LLM-synthetic (150 per domain) | 622: 172 MS-ToT + 150 human-elicited (NIST) + 300 LLM-synthetic (150 Llama-3.1-8B-Instruct, 150 GPT-4o) |
| Official metric | NDCG@1000 | NDCG@1000 | NDCG@1000 |
| Also reported | NDCG@10, MRR@1000, Recall@1000 | same | same |
| Participation | 11 groups, 33 runs | 6 groups, 18 runs | 9 groups, 32 runs |

Sources: [2023 §1–3], [2024 §1–3], [2025 §2–3].

**Query sources.**
- *Real CQA queries (MS-ToT).* MS-ToT has 1,000 query–answer pairs from the "I Remember This Movie…" forum [2023 §2]. In 2023 participants also received the sentence-level annotations from Arguello et al.'s qualitative coding and could use them in runs [2023 §3.2]. See `known-item-tot-datasets-and-metrics.md` for that coding scheme.
- *LLM-synthetic queries (2024 onward).* The method: sample a Wikipedia article, then prompt an LLM with the title plus the first paragraph (2024) or a GPT-4o summary (2025) to write a vague forum-style post that avoids the name [2024 §3.2; 2025 §3.3]. The 2025 prompt is printed in full and is domain-agnostic. It uses 7 "MUST" rules and 7 "COULD" rules, including "Include one or two plausible but incorrect details to reflect natural memory distortions" [2025 Fig. prompt].
- *Human-elicited queries (2025).* NIST assessors were shown an image of a celebrity, landmark or movie still. A query counted only if the assessor (1) recognised the entity, (2) could not recall its name, and (3) after writing the query, confirmed the entity's Wikipedia page. A progress bar pushed queries past 200 and then 300 characters. The final set was 53 celebrity, 47 landmark and 50 movie queries [2025 §3.2].

**How the synthetic prompts were validated (2024).** The organizers collected a small set of real ToT queries with known answers for each category: the TREC 2023 queries for movies, and r/tipofmytongue posts for celebrities and landmarks. They ran k retrieval systems on those real queries, then "iteratively designed category prompts to maximize Kendall's τ between the system ordering by synthetic and non-synthetic queries" for the same items [2024 §3.2]. The full procedure is in `known-item-tot-query-simulation.md`.

**Qrels.** One relevant page per query. It is not pooled or judged; the answer comes from the CQA "solved" answer, the sampled Wikipedia page, or the confirmed stimulus entity. Because there is a single relevant document, "NDCG@K is equivalent to DCG@K for all values of K (i.e., the ideal DCG@K is always one)" [2023 §2].

**Contamination controls.**
- Participants were told not to train or tune on MS-ToT or on data scraped from "I Remember This Movie…" [2024 §3.3; 2025 §3.4].
- Participants were asked to attest that test data had not been used for training.
  - 2023: 19 of 30 non-baseline runs attested; 11 were "uncertain" [2023 §4.1].
  - 2024: *no* participant attested. The organizers comment that "it is becoming increasingly difficult to attest to such a claim in the absence of transparency around the data used for pretraining different LLMs" [2024 §4.1].
  - 2025: two groups attested, covering 11 runs including two baselines [2025 §4.1].

## Evaluation (reported numbers)

**2023** [2023 Table 2, §4.3–4.4]:
- The best run (CMU-LTI `dpr-1000-rerank-robin`) scored NDCG@10 0.5169, NDCG@1000 0.5554, MRR@1000 0.5016 and R@1000 0.7933. The second-best run reached NDCG@1000 0.5070; the next was 0.3301.
- Baselines:
  - GPT-4 title-guessing: NDCG@1000 0.2624, R@1000 0.3733. It beat 26 runs on NDCG@1000, but with low recall.
  - DistilBERT dense: 0.1426.
  - BM25: 0.1388.
- **Floor effect.** The median NDCG@10 was zero for 129 of the 150 topics, and "the remaining 31 runs achieved a median NDCG@10 of 0". Sixteen runs had a median NDCG@1000 of 0.
- Query length (characters, sentences, number of annotations) correlated negatively with NDCG@1000 and Recall@1000. Verbosity and genre were "the only attributes correlated with retrieval performance".
- Topics that were easy across runs had high lexical overlap with the gold title and abstract. The hardest topics involved false memories or items the corpus described poorly.

**2024** [2024 Table 1, §4.2]:
- Best run (h2oloo `rg4o_t100_test`): NDCG@10 0.8042, NDCG@1000 0.8159, MRR 0.7910, R@1000 0.9250. Baselines: dense 0.2377 and BM25 0.1484 NDCG@1000.
- Systems "performed much better on synthetic queries for all three domains … compared to the MS-ToT movie queries". Even so, system performance on the different query types was "fairly well correlated", which the organizers read as support for synthetic queries.

**2025** [2025 Table "Summary of results", §4.2]:
- Best run (SRCB `scrb-tot-04`): NDCG@10 0.6576, MRR 0.6258, R@1000 0.9051, NDCG@1000 0.6824. PyTerrier BM25 scored 0.1700 NDCG@1000.
- Kendall's τ between the system rankings on each query source:
  - MS-ToT vs synthetic: **0.847**
  - MS-ToT vs NIST human-elicited: **0.703**
  - synthetic vs NIST: **0.737**
- The organizers conclude this "supports the use of diverse query generation approaches".
- On average the MS-ToT (real CQA) queries were the *hardest*. The NIST queries had "a larger proportion of 'easy' queries".
- NDCG@10, NDCG@1000 and MRR were strongly correlated across runs; Recall@1000 was less so.

## Relevance to lean-explore-bench

**What transfers directly:**
- **Task shape.** Each query has one gold item, the corpus is fixed and contains every answer, and systems return a ranked list. For a Lean ToT track this is: a query, one gold Mathlib declaration (plus equivalents; see the caveat below), a pinned Mathlib commit as the corpus, and ranked declaration names as runs.
- **Mixed query provenance with per-source reporting.** Real CQA, human-elicited and LLM-synthetic queries are kept as separately labelled strata. Scores are reported per source, and the τ between sources is itself a published result. We should do the same with Zulip-mined, elicited and synthetic Lean queries.
- **Validating synthetic queries by system-ranking agreement.** Tune the generator prompt until the system ordering on synthetic queries matches the ordering on a small real set for the *same targets*. This is the key methodological idea (details in `known-item-tot-query-simulation.md`).
- **The elicitation protocol's validity checks** (recognise, cannot recall, confirm) map cleanly onto Lean. Show a mathematician a statement, or an informal rendering of it. Ask whether they know it exists and whether they can name it. If they can't, have them write the query, then show them the declaration to confirm.
- **Contamination attestation.** It failed almost completely by 2024. Assume LLM-based engines may have seen Mathlib and Zulip. Prefer fresh or held-out targets, such as declarations added after a cutoff date, and hidden test answers.

**What to do differently:**
- **Single-answer qrels are too strict for Mathlib.** A ToT query can be satisfied by an `iff` form, a more general lemma, a `simp`-normal variant or a deprecated alias. The TREC setting has one Wikipedia page per entity, and Mathlib has no such structure. Keep a small set of accepted equivalents per query (see `../ir-evaluation/trec-pooling-and-relevance-judgments.md`).
- **The NDCG@1000 official metric** suits a 6M-page corpus where many systems miss entirely. Lean users rarely look past about 10 results. With one relevant item, NDCG@k reduces to 1/log2(rank+1) truncated at k. This is my derivation from the DCG definition and the organizers' "ideal DCG is one" remark. Report MRR@10 and Success@1/5/10 alongside it (see `known-item-tot-datasets-and-metrics.md`).
- **Floor effects.** The 2023 medians of zero show that a topic set that is too hard wastes queries statistically. Pilot the difficulty so that most queries fall within reach of *some* system.

## Open questions

- The 2024 overview says only that prompts were iterated to maximise τ, and gives neither the number of systems nor the final τ per domain. He et al. 2025 do report these (see the simulation note).
- The 2025 synthetic queries were validated against real queries only for the older domains. How reliable are they for the 50 new general domains? The overview does not report per-domain validation.
- Would the 2025 finding (real CQA queries hardest, NIST queries easiest) replicate for Lean? That would mean real Zulip questions are harder than elicited or synthetic ones.

## Sources

- TREC 2023 ToT overview: <https://trec.nist.gov/pubs/trec32/papers/Overview_tot.pdf>
- TREC 2024 ToT overview: <https://trec.nist.gov/pubs/trec33/papers/Overview_tot.pdf>
- TREC 2025 ToT overview: <https://arxiv.org/abs/2601.20671>
- Track site and baselines: <https://trec-tot.github.io>, <https://github.com/TREC-ToT/bench/>
- He et al., SIGIR 2025 (elicitation and validation): <https://arxiv.org/abs/2502.17776>
- He et al., SIGIR 2026 (multilingual, NTCIR): <https://arxiv.org/abs/2604.21096>
