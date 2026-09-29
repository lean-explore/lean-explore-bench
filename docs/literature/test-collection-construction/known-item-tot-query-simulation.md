# Simulating known-item and tip-of-the-tongue queries, and validating the simulation

- **Kind:** paper (methodology line: classic known-item query simulation → LLM/human ToT elicitation)
- **Links:**
  - Azzopardi, de Rijke, Balog, "Building simulated queries for known-item topics: an analysis using six European languages", SIGIR 2007: <https://dl.acm.org/doi/10.1145/1277741.1277820>. Author PDF: <https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/azzopardi-building-2007.pdf>
  - He, Kim, Diaz, Arguello, Mitra, "Tip of the Tongue Query Elicitation for Simulated Evaluation", SIGIR 2025: <https://arxiv.org/abs/2502.17776>. Code: <https://github.com/kimdanny/llm-tot-query-elicitation>, <https://github.com/kimdanny/human-tot-query-elicitation-mturk>
  - He, Kim, Fröbe, Arguello, Mitra, Diaz, "Multilingual and Domain-Agnostic Tip-of-the-Tongue Query Generation for Simulated Evaluation", SIGIR 2026: <https://arxiv.org/abs/2604.21096>. Data: <https://github.com/kimdanny/ntcir-19-tot>
- **Authors / org, date:** Glasgow and Amsterdam (2007); CMU, UNC and Microsoft/independent (2025–2026).
- **Status:** The 2025 and 2026 code and data are public. The 2025 synthetic queries became TREC 2024 ToT test queries, and the human-elicited ones became TREC 2025 test queries (see `known-item-trec-tot.md`).

## What it is

Collecting real known-item queries with verified answers is expensive and skewed by domain. Community Q&A (CQA) sites are mostly about movies, books and music. This line of work builds queries from the *target item*: pick the answer first, then produce a query that a searcher who half-remembers it might write. It also asks the key question of *how to show that the simulated queries evaluate systems the same way real ones do*.

For Lean this is the obvious route. Sample a Mathlib declaration, generate a vague "I know there's a lemma that…" query, and score retrieval of that declaration.

## How it works

### Classic term-sampling simulation (Azzopardi et al. 2007)

- **Generative model** [§3]. For each query:
  1. Pick a known item d with probability p(d).
  2. Pick a query length s with probability p(s).
  3. Draw s terms from a "user's language model" of d that mixes document terms with collection noise: p(t|θ) = (1−λ)·p(t|d) + λ·p(t).
- **Term selection**: *popular* (proportional to term frequency in d), *random* (uniform over d's terms) or *discriminative* (weighted by inverse collection frequency).
- **Setting** [§4]. Noise λ = 0.2, "which reflects the amount of noise on average within the manual queries". The reference queries were the manual known-item topics from WebCLEF 2005/2006, in six languages over the EuroGOV crawl.
- **Validation by *replicative validity*** [§4]. For three retrieval models (TF.IDF, BM25, Dirichlet LM), compare the distribution of per-query reciprocal rank (RR) on simulated vs manual queries with a two-sample **Kolmogorov–Smirnov test** at 5%. "If the two distributions of MRRs are not significantly different, we can say that the query model produces known-item topics which are comparable to manual queries."
- **Findings** [§1, §7–8]:
  - Earlier WebCLEF 2006 simulated topics "resulted in substantially poorer performance than manual topics for many of the languages".
  - Two refinements made the generated topics replicatively valid: an improved term-selection method, and a **document prior based on inlink counts**. Users "prefer to retrieve known items which tend to be more important", and "retrieving a random document in the collection is substantially more difficult".
  - Different languages needed different models.

Other classic work cited by He et al. (2025) §2.1 (not read here, (unverified) beyond the citation):
- Kim & Croft (2009) applied the approach to desktop search.
- Elsweiler et al. (2011) applied it to email re-finding.
- Validation methods in that literature include system-ranking correlation (WebCLEF 2006 overview), score-distribution comparison (Azzopardi 2007) and human-resemblance checks (Kim & Croft).
- Hagen et al. (2015) collected 2,755 known-item questions from Yahoo! Answers; 240 of them contained "false memories" ([Arguello et al. 2021 §2](https://arxiv.org/abs/2101.07124)).
- According to Lin et al., Hagen et al. also "injected query inaccuracies via hired annotators to simulate … false memories" ([arXiv:2305.15053 §5](https://arxiv.org/abs/2305.15053)).

### LLM-elicited ToT queries (He et al. 2025, §3–4)

- **Pipeline** [§4.1]:
  1. Sample a target entity.
  2. GPT-4o summarises its Wikipedia page into two paragraphs (for movies, the Plot section is always included).
  3. Build a role-play prompt from the summary.
  4. GPT-4o generates the query.
  5. **Name-leak check.** If the entity name appears in the query, regenerate, up to 3 retries, then discard.
- **Validation 1: system-rank correlation** [§3.2.1].
  - Run the *same target entities* through both real CQA queries (MS-ToT) and elicited queries, over **40 retrieval systems**.
  - The systems span BM25 and Dirichlet LMs with varied parameters, MiniLM-family dense retrievers, dense models "with intentionally degraded performance by reinitializing the weights of certain layers" (to spread the system scores), GPT-3.5-Turbo-Instruct as a ranker, and the top TREC 2023 run.
  - Rank the systems by MRR@1000 and by NDCG@1000 on each query set, then report Kendall's τ and Pearson's r.
- **Validation 2: linguistic similarity** [§3.2.2].
  - Annotate queries at sentence level with Arguello et al.'s ToT codes (movie, context, previous-search, social, uncertainty, opinion, emotion, relative-comparison) using GPT-4o-mini at temperature 0.
  - The annotator was first validated against MS-ToT gold annotations (precision, recall and Earth Mover's Distance, EMD).
  - Compare the code distributions of real and elicited queries by EMD.
- **Prompt search** [Table 1]. Thirteen configurations were compared on a movie set.

  | Config | MRR-based τ / r | NDCG-based τ / r | EMD |
  |---|---|---|---|
  | V0: "writing assistant", no Wikipedia summary | 0.264 / 0.610 | 0.309 / 0.425 | 0.090 |
  | Few-shot (V2) | about 0.45 | about 0.43–0.44 | about 0.03 |
  | Role-play without summary (V3) | 0.144–0.152 | | |
  | 14 flat rules, T=0.5 | 0.701 / 0.954 | 0.713 / 0.950 | |
  | **Final V6: 7 MUST + 7 COULD rules, T=0.3** | **0.757 / 0.917** | 0.719 / 0.897 | **0.026** |

  Lessons the authors draw [§4.2]:
  - Role-playing as the searcher beats "writing assistant".
  - Explicit rules beat few-shot examples.
  - Including the Wikipedia summary "substantially increased system rank correlation".
  - Lower temperature (0.3/0.5) beat 0.7, "contrary to our initial hypothesis that increased randomness would better simulate the stochastic nature of memory retrieval".
  - Splitting rules into MUST and COULD raised τ and lowered EMD, relative to the same 14 rules presented flat.
- **Other domains** [Table 2]. The authors hand-collected 22 landmark and 70 person queries from r/tipofmytongue. Correlations were lower than for movies:
  - Landmark: MRR τ 0.598, NDCG τ 0.697.
  - Person: MRR τ 0.636, NDCG τ 0.569.
  - All p < 0.01.

### Human-elicited ToT queries (He et al. 2025, §5)

- **Stimuli** [§5.1].
  - Wikipedia entities selected by infobox type and filtered to the top 20% by page views, "as less popular entities were deemed unlikely to be recognized".
  - The images were filtered so the name does not leak (no posters with titles, no visible station names) and are unambiguous (one person per image).
  - Images are drawn from 20 popularity buckets in turn.
- **Four-phase interface** [§5.2]: recognise → cannot recall the name → write the query → confirm the Wikipedia page. The queries were written by seven contracted participants.
- **Yield** [Table 3–4]:
  - 14,933 image presentations → 2,182 recognised → 884 "can't recall" → 777 queries written → **584 confirmed-valid queries**.
  - Recognisability was 0.10–0.20 across domains.
  - The funnel is expensive: most time goes on unrecognised stimuli.
- **Validation** [Table 5, §5.3]. Against 303 movie queries filtered from TOMT-KIS: MRR τ 0.611, NDCG τ 0.644. The EMD of 0.029 is comparable to the best LLM prompt.
  - Human-elicited queries had more opinion statements. The authors attribute this to the absence of an audience expecting to answer.
  - Landmark and Person could not be validated because the CQA data had almost no matching entities.

### Multilingual extension (He et al. 2026)

- **Real reference sets.** About 150 real CQA ToT queries per language (Chinese, Japanese, Korean, English). Where too few existed, they were topped up with machine-translated English queries.
- **Systems.** A pool of 27 systems per CJK language: 7 lexical, 1 GPT-4o ranker, 14 multilingual dense and 5 language-specific dense [§3.3].
- **Metric choice.** The authors report Kendall's τ as primary, "as linear relationship-based measures such as Pearson's r are more sensitive to outliers" [§4.1].
- **Results.**
  - The best mean τ is language-dependent: roughly 0.75 for Chinese, 0.55 for Japanese and 0.74 for Korean [Tables 1–3].
  - **MRR-based τ was usually lower than NDCG-based τ.** Examples:
    - Chinese full set: MRR 0.639 vs NDCG@1000 0.788.
    - Japanese full set, translated prompt: MRR 0.375 vs 0.518.
- **Released collections.** 5,000 queries per language, split train/dev/test 80/10/10.
- **Sampling.** Stratified sampling over 20 popularity buckets, with a domain mix of 80% general, 10% movies, 10% people [§3.1, Table 4].

## Evaluation

For general (non-ToT) LLM query generation and synthetic test collections, see the sibling notes `synthetic-query-generation-and-simulation.md` and `synthetic-test-collections.md`.

The numbers are the validation results above. There is no system leaderboard in these papers.

## Relevance to lean-explore-bench

**How to build a Lean ToT query simulator, following this recipe:**
1. **Target sampling.**
   - Sample Mathlib declarations with a *popularity prior*: for example, the number of uses in Mathlib or in downstream projects, which plays the role of inlinks or page views.
   - Stratify into popularity buckets. Azzopardi found that uniform sampling produces unrealistically hard topics, and He et al. use 20 popularity buckets.
   - Exclude auto-generated and private declarations.
2. **Generator input.**
   - Give the LLM the declaration's statement, docstring and an informal summary: the equivalent of the Wikipedia summary, which was the single biggest improvement.
   - Do *not* give the name.
3. **Role-play prompt with MUST/COULD rules.**
   - MUST: never state the name or distinctive name fragments; describe the mathematical content, not the Lean syntax; hedge.
   - COULD:
     - mention the context ("I was proving X and needed…");
     - include one plausibly wrong detail, such as a wrong typeclass, `≤` instead of `<`, or swapped argument order;
     - mention a failed prior search ("`exact?` didn't find it");
     - compare to a similar lemma.
4. **Leak check.**
   - Reject queries containing the declaration name or its last component.
   - For Lean this should also reject queries that contain the full formal statement, since that reduces the task to `exact?` or Loogle.
5. **Validate before use.**
   - Collect about 100–150 *real* ToT-style Lean questions with known answers, for example Zulip "is there a lemma…" threads with an accepted answer (README "real human queries"; `../lean-benchmarks/lean-finder-eval.md` notes that Lean Finder's 693 real questions were not released).
   - Run the real and synthetic queries *for the same target declarations* through a deliberately diverse pool of engines. The pool should include BM25 on names and docstrings, several embedding models, LeanSearch, Lean Finder, LeanExplore, Moogle-style engines, and deliberately degraded variants to spread the scores.
   - Tune the prompt to maximise Kendall's τ between the two system orderings. Report τ on NDCG and on MRR. Also report a top-weighted or significance-aware agreement measure (see `../statistics/metric-scales-and-correlation.md`).
6. **Optional: linguistic-code check.**
   - Define a small Lean-specific code set: statement content, typeclass/context, proof context, previous search, hedging, relative comparison ("like `mul_le_mul` but for…").
   - Compare the code distributions of real and synthetic queries by EMD, as He et al. did with Arguello's codes.

**Human elicitation for Lean.**
- Show an expert a *rendered informal statement*, not the Lean name, and ask whether they believe Mathlib has it and whether they can name it. If they can't, have them write the query, then reveal the declaration to confirm.
- Overall yield was 584 valid queries from 14,933 stimuli shown (about 4%; movies about 3%). To avoid wasting expert time, pre-filter stimuli to lemmas that users of the target community are likely to have used.

**Caveats:**
- τ ≈ 0.6–0.75 is "reasonably high" by the authors' standard, but conventional thresholds for "equivalent" rankings are 0.8–0.9. Those thresholds are themselves unreliable (`../statistics/metric-scales-and-correlation.md`). Report τ with a confidence interval, for example by bootstrapping over queries.
- Validation needs *paired* real and synthetic queries for the same targets. The real set therefore bounds which declarations can be validated. This is the same problem He et al. hit in the Landmark and Person domains.
- An LLM-written query can carry the generator's vocabulary. An engine built on the same LLM family may be favoured, which is the circularity that `../lean-benchmarks/lean-finder-eval.md` flags for Lean Finder. Use at least two generator LLMs, as TREC 2025 did with Llama and GPT-4o, and report scores per generator.

## Open questions

- How large does the real reference set need to be for τ to be stable? He et al. used 150 movie queries and only 22 landmark queries, and neither paper reports a confidence interval on τ.
- Azzopardi validated distributions of per-query scores (KS test on RR), while He et al. validated system orderings. Which matters more for a leaderboard? Probably both: the ordering for rankings, and the score distribution for absolute difficulty.
- Should synthetic Lean queries imitate forum prose (long, polite, anecdotal) or search-box queries? TREC ToT imitates forum posts. Lean users typing into a search engine may be terser.

## Sources

- Azzopardi, de Rijke, Balog 2007, SIGIR: <https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/azzopardi-building-2007.pdf> (DOI <https://doi.org/10.1145/1277741.1277820>)
- He et al. 2025, SIGIR: <https://arxiv.org/abs/2502.17776>
- He et al. 2026, SIGIR: <https://arxiv.org/abs/2604.21096>
- Arguello et al. 2021, CHIIR (Hagen et al. 2015 summary): <https://arxiv.org/abs/2101.07124>
- Lin et al. 2023 (Hagen et al. 2015 summary): <https://arxiv.org/abs/2305.15053>
- TREC 2024 ToT overview (prompt tuning by τ): <https://trec.nist.gov/pubs/trec33/papers/Overview_tot.pdf>
