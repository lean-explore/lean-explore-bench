# Do search tools help LLM agents write Lean? (cluster: Hilbert, Awakening the Sleeping Agent, Lean Finder RAG, Ax-Prover, Numina-Lean-Agent, Archon)

- **Kind:** paper (cluster)
- **Links:**
  - Hilbert: https://arxiv.org/abs/2509.22819 ; code https://github.com/Rose-STL-Lab/ml-hilbert
  - Awakening the Sleeping Agent (Goedel-Prover-V2 + LeanSearch tool): https://arxiv.org/abs/2604.08388
  - Lean Finder (prover-integration appendix): https://arxiv.org/abs/2510.15940
  - Ax-Prover: https://arxiv.org/abs/2510.12787
  - Numina-Lean-Agent: https://arxiv.org/abs/2601.14027 ; code https://github.com/project-numina/numina-lean-agent
  - Rethlas / Archon ("Automated Conjecture Resolution with Formal Verification"): https://arxiv.org/abs/2604.03789 ; code https://github.com/frenzymath/Archon
  - Related, covered separately: LeanSearch v2 Prove task (`leansearch-v2.md`), REAL-Prover retrieval ablation (`real-prover.md`).
- **Authors / org, date:** Hilbert: Varambally, Voice, Sun, Chen, Yu, Ye, Sep 2025 (ICLR 2026 template; affiliations not checked). Awakening: Chung, Lin, Jiang, Tang, Jin, Apr 2026 (COLM 2026 template). Lean Finder: Lu et al., Oct 2025. Ax-Prover: Breen et al., Oct 2025. Numina-Lean-Agent: Liu et al. (Project Numina et al.), Jan 2026. Archon: Ju, Gao et al., Apr 2026.
- **Status:** all on arXiv; code links as above (not fetched).

## What it is

The set of papers found (arXiv search, Sep 2026) that either (a) ablate a search/retrieval component inside a Lean proving agent and report end-to-end numbers, or (b) give an LLM agent a Mathlib search tool and report how it is used. Only (a) gives causal evidence.

## How it works

One sentence: in each system an LLM (specialized prover or general frontier model) calls a Mathlib search engine (LeanSearch, Loogle, a custom embedding index, Lean Finder, or LeanExplore-derived LeanDex) either at fixed pipeline points or autonomously as an MCP/tool call, and pastes results into its context.

## Evaluation

### Papers with an explicit with/without-retrieval ablation

**Hilbert** ([§4.3, Table "Ablation with/without retrieval"](https://arxiv.org/abs/2509.22819)). Retriever: all-mpnet-base-v2 + FAISS over informal descriptions from the `mathlib_informal` dataset (from LeanSearch v1); the reasoner writes 5 queries, top-5 each, then filters ([§3.1](https://arxiv.org/abs/2509.22819)). Verifier: Lean/Mathlib v4.15.0. Ablation on miniF2F test (244), Gemini 2.5 Pro reasoner:

| Prover | Retrieval | Pass rate | Reasoner calls | Prover calls | Reasoner tokens |
|---|---|---|---|---|---|
| DeepSeek-Prover-V2-7B | yes | 98.4% | 420 | 205 | 1.9M |
| DeepSeek-Prover-V2-7B | no | 97.1% | 426 | 290 | 2.1M |
| Goedel-Prover-V2-32B | yes | 99.2% | 548 | 391 | 2.3M |
| Goedel-Prover-V2-32B | no | 97.9% | 862 | 449 | 4.0M |

Calls/tokens are averages over samples needing decomposition. Takeaway: on a saturated competition benchmark, retrieval moves pass rate about 1.3 points (about 3 problems) but cuts reasoner compute substantially; no PutnamBench retrieval ablation.

**Awakening the Sleeping Agent** ([§4, Table 1](https://arxiv.org/abs/2604.08388)). Goedel-Prover-V2 loses tool calling (BFCL 89.4% base -> near 0). SFT on 100 / 1K / 18K Lean agentic traces that call a LeanSearch-style tool (e5-mistral-7b-instruct over informalized Mathlib in ChromaDB) restores it. ProofNet (186) pass@32, SFT checkpoint: 21.51 -> 25.81 (+100 traces) -> 27.96 (+1K and +18K); miniF2F pass@32: 84.02 -> 81.97 / 82.79 / 85.25. Post-RL checkpoint ProofNet pass@32: 22.58 -> 26.88 for all three sizes. After SFT, 99.1-99.9% of generations call the tool and 93.8% of solved ProofNet proofs (+100 run) use a retrieved identifier. About 45-50% of retrieved-and-used theorem occurrences are "out-of-model" (never emitted by the base model in any sample) ([§4.3](https://arxiv.org/abs/2604.08388)). Caveat: the comparison changes weights and tool access together; the paper does not report the fine-tuned model with the tool disabled, so the gain is not cleanly attributable to search.

**Lean Finder prover integration** ([App. "RAG for LLM Provers"](https://arxiv.org/abs/2510.15940)). 6-10 statements retrieved from the initial proof state, prepended to the prompt. Whole-proof provers, w/o -> w/ Lean Finder: Goedel-Prover-SFT ProofNet 6.6 -> 7.2 (pass@1), 13.2 -> 14.4 (pass@32), 17.6 -> 17.6 (pass@128); DeepSeek-Prover-V1.5-RL ProofNet 4.3 -> 6.5 (pass@1), 14.5 -> 18.3 (pass@32), 17.7 -> 19.4 (pass@128); miniF2F changes at most 1.3 points; PutnamBench counts move by at most 1 in either direction. Swapping it into REAL-Prover gives no gain (see `real-prover.md`). Authors describe benefits as "marginal".

**LeanSearch v2 Prove task** (see `leansearch-v2.md`): Sonnet 4.5 reflection loop on FATE-H, no retrieval 4/100 vs 12-20/100 with various retrievers. This is the largest retrieval effect in the cluster, on a Mathlib-heavy graduate algebra set.

### Papers that give agents search tools but do not isolate search

**Ax-Prover** ([§4, §4.3 "Analysis of Tool Usage"](https://arxiv.org/abs/2510.12787)). Claude Sonnet 4 agent with lean-lsp-mcp tools, including `lean_leansearch` and `lean_loogle`. On 100 NuminaMath-LEAN "Unsolved" problems the prover averages 100.76 tool calls per run, of which `lean_loogle` 5.88 and `lean_leansearch` 4.32. Baseline is Sonnet with no tools at all, so search is not separated from compilation/goal feedback.

**Numina-Lean-Agent** ([§2-3](https://arxiv.org/abs/2601.14027)). Claude Code + MCP tools: lean-lsp-mcp (incl. `lean_loogle`, `lean_local_search`) and LeanDex, an agentic semantic search tool "built on top of LeanExplore". Solves 12/12 Putnam 2025; ablations cover the informal prover and a subagent, not search.

**Rethlas / Archon** ([§3-4](https://arxiv.org/abs/2604.03789)). Archon uses an improved LeanSearch; Rethlas uses Matlas (arXiv theorem search, about 13.6M statements). Evidence for search is a case study (Matlas located a key result of Jensen); the only controlled ablation is a human-blueprint fork, not a search ablation.

## Relevance to lean-explore-bench

- Evidence that search helps agents exists but is thin and benchmark-dependent: large on Mathlib-heavy graduate sets (FATE-H, FATE-M), small on ProofNet, near zero on saturated miniF2F. An end-to-end track must use Mathlib-heavy, post-cutoff problems or it will not discriminate between engines.
- Compute is a second outcome: Hilbert's biggest effect is fewer reasoner calls/tokens. We should record calls, tokens and wall-clock alongside pass rate.
- Most agent papers only report tool-call counts or "with all tools vs no tools". A clean design is: same agent, same budget, tool set identical except the search backend (including a "no search" arm and a "grep/Loogle only" arm).
- Retrieved-and-used rate and the "out-of-model" analysis (retrieved identifiers the model never produces unaided) are cheap, retrieval-specific process metrics we can compute from traces.
- Agents built on LeanExplore (LeanDex) and MCP search tools are already in use, so an MCP-level harness matches real usage.

**Concrete reusable items:**
1. Ablation table layout from Hilbert: pass rate plus reasoner/prover calls and tokens, with and without retrieval.
2. Metrics from Awakening: tool-call compliance, fraction of solved proofs using at least one retrieved identifier, and out-of-model share of used theorems.
3. Lean Finder's minimal RAG protocol (retrieve 6-10 from initial proof state, prepend) as a cheap, model-agnostic downstream baseline.
4. Ax-Prover's per-tool call counts as a trace statistic to log.

## Open questions

- No paper found compares multiple search engines as agent tools under an identical agent loop except LeanSearch v2's Prove task (which excludes LeanExplore). This is the gap our benchmark can fill.
- None report variance across seeds for the retrieval ablation; with 244 or 186 problems, 1-4 point differences may be noise.
- Other 2025-2026 agent papers (e.g., Seed-Prover 1.5, APOLLO) were not checked for a search ablation here (unverified).

## Sources

- Hilbert: https://arxiv.org/abs/2509.22819 (read methods, results, retrieval ablation table from LaTeX source)
- Awakening the Sleeping Agent: https://arxiv.org/abs/2604.08388 (read §1-4 and limitations from LaTeX source)
- Lean Finder: https://arxiv.org/abs/2510.15940 (read prover-integration section and appendix)
- Ax-Prover: https://arxiv.org/abs/2510.12787 (read tool list, baselines, tool-usage analysis)
- Numina-Lean-Agent: https://arxiv.org/abs/2601.14027 (read full text)
- Rethlas/Archon: https://arxiv.org/abs/2604.03789 (searched full text for LeanSearch/Matlas/ablation passages)
