# LeanExplore paper evaluation (LLM-as-judge, 300 queries)

- **Kind:** benchmark / evaluation protocol
- **Links:**
  - Paper: https://arxiv.org/abs/2506.11085 (Section 6, Appendix B for the prompt, Appendix C for the query list)
  - Code: https://github.com/justincasher/lean-explore
- **Authors / org, date:** Justin Asher, June 2025.
- **Status:** The query list is published in full in the paper's appendix. I did not find a machine-readable release of the queries or the judge outputs (unverified).

## What it is

A comparative evaluation of LeanExplore, LeanSearch (v1) and Moogle:
- **Queries:** 300 short natural-language queries, AI-generated. Examples: "group definition", "Heine-Borel theorem", "snake lemma", "Yoneda lemma".
- **Gold labels:** none. Instead, an LLM judge ranks the three engines' top-5 result sets per query.

## How it works

- **What the judge sees:** each engine's top 5 results. For each result: the Lean code, the docstring, and any informal statement.
- **Judge:** Gemini 2.5 Flash. Engine identities are blinded and the presentation order is permuted per query.
- **Output:** the judge assigns 1st, 2nd and 3rd place, and ties are allowed.
- **Repetitions:** 3 runs over all 300 queries, 900 trials in total. Results are reported as mean ± SE across runs.

## Evaluation

**Table 1, place rates (%):**

| Engine | 1st | 2nd | 3rd |
|---|---|---|---|
| LeanExplore | 55.4 ± 0.7 | 33.8 ± 0.6 | 10.8 ± 0.5 |
| LeanSearch | 46.3 ± 1.4 | 34.1 ± 0.7 | 19.6 ± 1.1 |
| Moogle | 12.0 ± 0.6 | 24.8 ± 0.2 | 63.2 ± 0.4 |

**Table 2, head-to-head:**
- LeanExplore vs. LeanSearch: LeanExplore wins 50.0 ± 1.8%, LeanSearch wins 39.4 ± 1.4%, ties 10.6%.
- LeanExplore vs. Moogle: 79.2% to 15.9%.
- LeanSearch vs. Moogle: 72.0% to 23.2%.

**Caveat the paper itself notes:** Moogle sometimes lacked natural-language statements, which were shown to the judge as N/A. That may have hurt Moogle.

**Later use:** LeanSearch v2 adopted this judge protocol for MathlibQR (Claude Sonnet 4.5, 4 systems, strict orderings, 3 permutations per query). It found a primacy bias of about 0.4 to 0.6 rank positions. On that setup LeanExplore's mean rank was 3.32 of 4, last among the four systems. See `mathlibqr.md`.

## Relevance to lean-explore-bench

- **Why it matters:** the protocol is the origin of the "LLM judge ranks blinded result sets" approach that later Lean search papers reuse. It needs no gold labels and suits short, underspecified queries.
- **Lessons for our benchmark:**
  - **Self-evaluation.** An author evaluating their own engine on queries they generated themselves is exactly what an independent benchmark should avoid. The conflicting results are evidence: LeanExplore ranks first here, but last or near last in LeanSearch v2's judge study and on Legendre's gold-label metrics.
  - **Judge ranks depend on the setup.** The result depends on which judge model is used, which fields the judge sees, and how each engine's results are hydrated. LeanSearch v2 hydrated all engines from one shared metadata source to control for this. Here, each engine's own display fields were used, so presentation quality is confounded with retrieval quality.
  - **Bias checks.** Position-bias and tie-handling checks should be mandatory (compare the Lean Finder finding that GPT-4o handles ties badly).
  - **Query style.** The query set, short topic names mostly targeting famous definitions and theorems, is a useful "concept lookup" style that MathlibQR's nickname style only partly covers.

## Open questions

- Are the raw judge outputs or per-query rankings available? They would allow re-analysis with a different aggregation.
- Could the 300 queries be given gold labels, via pooling across engines plus human judging, to turn them into a graded gold set?

## Sources

- Paper (§6, Tables 1–2, App. B, App. C): https://arxiv.org/abs/2506.11085 and https://arxiv.org/html/2506.11085
- LeanSearch v2's reuse of the protocol and its bias diagnostics: https://arxiv.org/html/2605.13137v2 (§4.1, App. B.2)
- Legendre's gold-label scores: https://www.legendre-leaderboard.com/leaderboard
