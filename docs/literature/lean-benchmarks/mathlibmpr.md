# MathlibMPR (global premise retrieval benchmark)

- **Kind:** benchmark / dataset
- **Links:**
  - Paper: https://arxiv.org/abs/2605.13137 (Sections 4.2 and 4.3, Appendix A.2)
  - Data: https://github.com/frenzymath/LeanSearch-v2/blob/main/benchmark/MathlibMPR.json and `MathlibMPR_Prop_ids.txt`
- **Authors / org, date:** the LeanSearch v2 team (Gao et al., PKU / FrenzyMath), May 2026.
- **Status:** Downloadable inside the Apache-2.0 LeanSearch-v2 repo. Legendre's methodology page lists it as a supported task with n = 69.

## What it is

MathlibMPR has 69 theorems taken from merged Mathlib pull requests. Each item comes with:
- a natural-language statement,
- a formal statement (Lean source with `sorry`),
- the name of the main result as merged,
- one or more premise groups, 1 to 8 per theorem with a mean of 2.96.

A premise group is a set of interchangeable lemmas for one proof step. Each group is tagged either `original`, meaning it was used in the merged proof, or `alternative`, meaning experts annotated it as an equally valid proof route. The task is "global premise retrieval": from the statement alone, recover the full set of lemmas the proof needs. This differs from per-tactic premise selection. Candidate PRs were filtered so that no theorem is a trivial restatement, special case, or notational rewrite.

## How it works

- **Record format** (from `MathlibMPR.json`): `id`, `pr` (the Mathlib PR number), `formal_main_result`, `NL_main_result`, `formal_statement`, and `premise_group`, a list of `{kind: original|alternative, docs: [full_name, ...]}`.
- **MathlibMPR-Prop:** a 50-problem subset used for downstream proving (§4.3).

## Evaluation

**Metrics:**
- **Recall@k (group):** the fraction of gold premise groups hit in the top k, macro-averaged.
- **Covered@k:** 1 only if some complete proof routing, original or alternative, has every group hit. Legendre adopts the same Covered@k definition.

**Selected paper Table 2 numbers** (percentages, k = 10):

| System | Recall@10 (group) | Covered@10 |
|---|---|---|
| LeanSearch v2 (reasoning mode) | 46.1 | 30.4 |
| DIVER (full pipeline) | 38.0 | 24.6 |
| ReasonIR | 26.9 | 18.8 |
| INF-X-Retriever | 28.2 | 18.8 |
| LeanStateSearch (proof-state query) | 9.3 | 2.9 |
| LeanPremise | 4.8 | 1.4 |
| ReProver | 5.5 | 1.4 |

**Downstream check:** with a fixed prover loop, LeanSearch v2 retrieval gives 20% proof success, against 16% for the next-best retriever and 4% with no retrieval (abstract, §4.3).

**Other results:** TheoremGraph reports group Recall@10 of 0.224 for its untuned baseline and 0.165 after the MathlibQR-tuned configuration (arXiv 2606.25363). Configurations tuned for concept search did not transfer to this task.

## Relevance to lean-explore-bench

- **Why it matters:** this is the only public Lean set where the query is a *statement to prove* and the gold is a *set* of premises with alternatives. That is close to how coding agents actually use search. It could be a secondary track for "agentic" search.
- **Main limitation:** n = 69 is very small. Legendre itself notes that at this sample size many differences are not significant.
- **Other caveats:**
  - Gold comes from what the merged proof used. Other valid routes are only partly captured through the expert-annotated `alternative` groups.
  - Retrieval engines built for short queries, such as LeanExplore, LeanSearch and Loogle, are not designed for this input, so the task compares different kinds of system.
- **Metric to reuse:** Covered@k and group recall are good designs for multi-premise gold.

## Open questions

- How many items have alternative routings? The paper says "a subset". I could count them from the JSON; not done here.
- The PRs are recent, so is there leakage? Engines indexed after the merge contain the target theorem itself, which may matter. The paper's handling of this is unverified.

## Sources

- Paper (abstract, §4.2 Table 2, §4.3, App. A.2): https://arxiv.org/abs/2605.13137 and https://arxiv.org/html/2605.13137v2
- Data: https://github.com/frenzymath/LeanSearch-v2/tree/main/benchmark (record format checked from the raw `MathlibMPR.json`: 69 records)
- Legendre's use of the benchmark: https://www.legendre-leaderboard.com/methodology
- TheoremGraph: https://arxiv.org/abs/2606.25363
