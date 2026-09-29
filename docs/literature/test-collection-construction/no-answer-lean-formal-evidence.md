# "The lemma doesn't exist": evidence from Lean / formal-math work, and a proposed no-answer track

- **Kind:** paper cluster + benchmark design proposal
- **Links:**
  - Klingner et al., "Evaluation of LLMs for Mathematical Formalization in Lean" https://arxiv.org/abs/2606.05632
  - MA-ProofBench https://arxiv.org/abs/2606.13782
  - DDR (dependency retrieval with hallucination rate) https://arxiv.org/abs/2511.11990 (main note: [../premise-selection/retrieval-augmented-autoformalization.md](../premise-selection/retrieval-augmented-autoformalization.md))
  - Related notes: [no-answer-qa-rag-abstention.md](no-answer-qa-rag-abstention.md), [no-answer-retrieval-qpp-and-truncation.md](no-answer-retrieval-qpp-and-truncation.md), [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md)
- **Authors / org, date:** 2025–2026
- **Status:** Papers only. No public Lean search benchmark with no-answer queries was found.

## What it is

This note records what Lean and formal-math work says about models asking for, or inventing, declarations that do not exist. It also records the gap: no Lean *search* benchmark tests queries whose correct answer is "no such lemma". The note ends with a concrete design for a no-answer track.

## How it works (what existing work measures)

- **Hallucinated names are a measured failure class in Lean proving.**
  - Klingner et al. define a *hallucination* error as "Unknown identifier, constant, or tactic — the model referenced a name that does not exist in scope". Overall, hallucination is 4,366 failure entries, or 7.7% of failures. On miniCTX it is 3,017 (9.3%), and on miniF2F 1,349 (5.6%) ([arXiv 2606.05632](https://arxiv.org/abs/2606.05632), error taxonomy and Table A.2).
  - They attribute the higher miniCTX rate to context. Models "make up plausible sounding lemmas (such as 'Padic.valuation_nonneg' and 'Int.toNat_add_of_nonneg', both of which are not real Mathlib Lemmas) based off of the context that miniCTX provides" (§3.2).
  - The per-model breakdown (e.g. GPT-OSS about 15%) was reported by a WebFetch summary and not checked against the table (unverified).
- **Two kinds of "unknown identifier" (MA-ProofBench).** "Mathlib Hallucinations" trigger Unknown Constant / Unknown Identifier errors and split into:
  - **Namespace omission:** "the referenced theorem exists in Mathlib but the model fails to open the corresponding namespace".
  - **Name fabrication:** "the model 'guesses' and fabricates non-existent theorem names based on Mathlib's naming conventions".
  Mathlib hallucinations and incomplete proofs are "the primary sources of error" in sampled failures of DeepSeek-Prover-V2-671B, DeepSeek-V3.2-Thinking and Gemini 3.1 Pro ([arXiv 2606.13782](https://arxiv.org/abs/2606.13782), §error analysis, Fig. 4).
- **Hallucination rate for generative dependency retrieval (DDR).**
  - DDR defines `Hall` as the fraction of output dependency names that do not exist in the library. If a model outputs (Real.div, Real.max, Nat.succ) and only Nat.succ exists, Hall = 2/3.
  - Prompted in-context LLM retrievers have mean Hall of about 0.30. DDR's mean is below 0.02 ([arXiv 2511.11990](https://arxiv.org/abs/2511.11990), "Hallucination Study", Table 2).
  - Select-based retrievers (top-k from the library) are "inherently free from hallucination by design".
  - Precision and recall are then computed *after filtering hallucinated items* (Table 3).
- **What is missing.** In all three works, "does not exist" is a property of the *model's output*, never of the *query*. Every evaluated query has a real gold dependency set. A select-based search engine can never score badly on DDR's `Hall`, even though it always returns real-but-wrong names. That is exactly the failure we care about: an agent asks for a lemma that doesn't exist, receives real neighbours, and misuses them.
- **Lean search benchmarks in this repo.** A grep over `docs/literature/` (2026-09-28) for abstain / unanswerable / nonexistent / hallucination found no Lean search benchmark with no-gold queries. The only mention is our own recommendation in [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md).
- **Tools already hint at existence checks.** lean-lsp-mcp advertises `lean_local_search` to agents as "Confirm declarations exist ... to prevent hallucinating APIs" ([../lean-tools/lean-lsp-mcp.md](../lean-tools/lean-lsp-mcp.md)). LeanExplore v0.x drops candidates below a 0.525 similarity threshold, so it *can* return fewer results ([../lean-engines/leanexplore.md](../lean-engines/leanexplore.md)). Neither behaviour has been evaluated as abstention.

## Evaluation

| Work | Unit | "Doesn't exist" metric | Number |
|---|---|---|---|
| Klingner et al. 2026 | failed proof attempts | share of failures that are unknown identifier/constant/tactic | 7.7% overall; 9.3% miniCTX; 5.6% miniF2F ([2606.05632](https://arxiv.org/abs/2606.05632)) |
| MA-ProofBench 2026 | sampled failures | counts of namespace-omission + fabrication | "primary sources of error" with incomplete proofs ([2606.13782](https://arxiv.org/abs/2606.13782)) |
| DDR 2025 | generated dependency sets | Hall = fraction of non-existent names | ~0.30 prompted LLMs; <0.02 DDR ([2511.11990](https://arxiv.org/abs/2511.11990)) |

## Relevance to lean-explore-bench: proposed no-answer track

**Constructing no-answer queries.** Each query gets a stratum label. Strata are reported separately, following the Agent Retrieval Bench lesson in [no-answer-retrieval-qpp-and-truncation.md](no-answer-retrieval-qpp-and-truncation.md).

1. **Harvested fabrications (natural, hardest).** Collect names that agents actually invented. Sources are unknown-identifier errors in agent/prover logs (as in Klingner et al. and MA-ProofBench), and our own agent traces. Keep a name if it does not resolve in the pinned Mathlib *and* the intended statement is not provable by `exact?`/`apply?` or found by Loogle type search. Convert each name into the engine's query styles: the bare name, a natural-language paraphrase, and a type-pattern. MA-ProofBench's split matters here. *Namespace omissions* are **answerable** queries (the lemma exists under a qualified name) and belong in the normal track. Only *fabrications* go here.
2. **Perturbed real lemmas (synthetic, SQuAD 2.0 / AbstentionBench style).** Take a real declaration and drop a hypothesis, strengthen the conclusion, or generalize the type class so that the statement is false or absent. The original lemma becomes the recorded **plausible distractor** (SQuAD 2.0's device, [no-answer-qa-rag-abstention.md](no-answer-qa-rag-abstention.md)). Verify absence mechanically: a counterexample or disproof where possible; otherwise failed `exact?` plus a manual check. Record the verification method per item.
3. **True-but-missing statements (natural).** Take statements that are true but not in Mathlib at the pinned commit, for example results added in later Mathlib versions. A later-added lemma is a natural "didn't exist yet" query with a known future gold. MathlibQR's `missing_in_*` lists already track declarations absent from specific snapshots ([../lean-benchmarks/mathlibqr.md](../lean-benchmarks/mathlibqr.md)). Deprecated and renamed names are *answerable* (they redirect) and must not be used here.
4. **Out-of-scope controls (easy).** Concepts from other libraries or off-domain requests. Use them only as a sanity stratum and never pool them into the headline number.

Mix no-answer items with answerable ones drawn from the same query distribution. Report the ratio. Keep a frozen dev split for threshold tuning.

**Scoring engines.**
- **Primary, scale-free: AUROC** of the engine's confidence (its top-1 score, or its own abstain signal) for separating answerable queries (where gold is in the top-k) from no-answer queries. Also report **risk–coverage AUC** and **coverage at a fixed risk**. These work even for engines that never return an empty list.
- **Operating point:** tune a per-engine threshold on dev, freeze it, then report on test:
  - abstention recall on no-answer queries (NoMIRACL's 1 − hallucination rate);
  - false-abstention rate on answerable queries;
  - **distractor hit rate** (the recorded near-miss appears in the top-k).
- **Utility score (CRAG-style):** +1 for a relevant hit in the top-k on answerable queries, 0 for abstaining, −1 for a confident non-empty result on a no-answer query or a confident miss on an answerable one. Report always-abstain and never-abstain baselines alongside (SQuAD 2.0).
- **Padding cost:** penalized DCG (non-relevant gain −1; Choppy) over the returned list, which rewards engines that truncate.
- **Keep it out of the main nDCG/MRR averages.** Empty-gold queries score 0 for every engine under trec_eval-style metrics.
- **Agent-level (extrinsic):** in the in-agent protocol of [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md), measure how often the agent (a) correctly concludes "not in Mathlib" and proves or states the result itself, versus (b) invokes a returned neighbour incorrectly. Count unknown-identifier and type-mismatch errors attributable to search results.

## Open questions

- How often do real agent queries target nonexistent lemmas? This fixes the realistic no-answer ratio and needs log data.
- Can non-existence be certified cheaply at scale? `exact?` failure is not a proof of absence: the lemma may exist in a form that needs rewriting. Perturbed-false statements are cleanly certifiable. True-but-missing ones need human review.
- Should a near-miss be graded as partially correct, e.g. the commutative-ring version when the query asks for general rings? That is arguably the *most useful* output for an agent, which suggests a graded no-answer track: "closest real lemma + explicit mismatch flag".

## Sources

- Klingner et al. "Evaluation of LLMs for Mathematical Formalization in Lean", arXiv 2606.05632 (June 2026). https://arxiv.org/abs/2606.05632 (error taxonomy table, Table A.2, §3.2; PDF text checked for the overall/miniCTX/miniF2F counts)
- Pu et al. "MA-ProofBench: A Two-Tiered Evaluation of LLMs for Theorem Proving in Mathematical Analysis", arXiv 2606.13782 (June 2026). https://arxiv.org/abs/2606.13782 (error attribution section, Fig. 4)
- DDR, arXiv 2511.11990. https://arxiv.org/abs/2511.11990 ("Hallucination Study", Tables 2–3)
- In-repo notes: [../premise-selection/retrieval-augmented-autoformalization.md](../premise-selection/retrieval-augmented-autoformalization.md), [../lean-tools/lean-lsp-mcp.md](../lean-tools/lean-lsp-mcp.md), [../lean-engines/leanexplore.md](../lean-engines/leanexplore.md), [../lean-benchmarks/mathlibqr.md](../lean-benchmarks/mathlibqr.md), [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md)
- Design devices borrowed from SQuAD 2.0 (https://arxiv.org/abs/1806.03822), CRAG (https://arxiv.org/abs/2406.04744), NoMIRACL (https://arxiv.org/abs/2312.11361), Choppy (https://arxiv.org/abs/2004.13012), Kamath et al. (https://arxiv.org/abs/2006.09462), Agent Retrieval Bench (https://arxiv.org/abs/2607.24882). The track design itself is our proposal, not a published protocol.
