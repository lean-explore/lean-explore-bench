# Do frontier Lean provers use retrieval? (DeepSeek-Prover, Kimina, Goedel, Seed-Prover)

- **Kind:** paper (cluster survey of 7 prover papers)
- **Links:**
  - DeepSeek-Prover-V1.5 — [arXiv 2408.08152](https://arxiv.org/abs/2408.08152)
  - DeepSeek-Prover-V2 — [arXiv 2504.21801](https://arxiv.org/abs/2504.21801)
  - Kimina-Prover Preview — [arXiv 2504.11354](https://arxiv.org/abs/2504.11354), [code](https://github.com/MoonshotAI/Kimina-Prover-Preview)
  - Goedel-Prover — [arXiv 2502.07640](https://arxiv.org/abs/2502.07640)
  - Goedel-Prover-V2 — [arXiv 2508.03613](https://arxiv.org/abs/2508.03613), [code](https://github.com/Goedel-LM/Goedel-Prover-V2)
  - Seed-Prover (1.0) — [arXiv 2507.23726](https://arxiv.org/abs/2507.23726)
  - Seed-Prover 1.5 — [arXiv 2512.17260](https://arxiv.org/abs/2512.17260)
- **Authors / org, date:** DeepSeek (Aug 2024, Apr 2025); Moonshot/Numina (Apr 2025); Princeton Goedel team (Feb 2025, Aug 2025); ByteDance Seed (Jul 2025, Dec 2025).
- **Status:** DeepSeek, Kimina (distilled 1.5B/7B), Goedel models are open-weight; Seed-Prover is closed.

## What it is

A check of whether the strongest 2024–2025 whole-proof Lean provers include a premise-retrieval or library-search component, and what their papers say about benchmark contamination. Method: full LaTeX of each paper read via arXiv and searched (bibliography excluded) for `retriev|premise|search engine|LeanSearch|Loogle|Moogle|exact?|contaminat|leak|overlap|dedup|decontam|search tool|Mathlib search`, then the hits read in context.

## How it works

All seven are LLMs trained with SFT/expert iteration and/or RL on Lean proofs; only Seed-Prover 1.5 gives the model an explicit Mathlib search tool.

## Evaluation

### Retrieval usage, per paper

| Paper | Retrieval / search component? | What the paper actually says |
|---|---|---|
| DeepSeek-Prover-V1.5 | **None described** | Only premise mention: verification imports "Mathlib4 and Aesop to access predefined premises and tactics" (Sec. "Experiments"). "Retrieves" appears only for MCTS value estimates. Headline: miniF2F-test 63.5%, ProofNet 25.3% (abstract). |
| DeepSeek-Prover-V2 | **None described** | "Premises" appear only as preceding subgoals added as hypotheses in subgoal-decomposition lemmas (Fig. "conjecture-generation-example"). Headline: miniF2F-test 88.9% (Pass@8192), ProofNet-test 37.1% (Pass@1024), PutnamBench 47/658 (Intro). |
| Kimina-Prover Preview | **None described** | No retrieval/search hits beyond the decontamination paragraph. Headline: miniF2F 80.7% pass@8192 (abstract). |
| Goedel-Prover | **None described** for its own model | Mentions retrieval only in related work (Magnushammer, LeanDojo) and in the PutnamBench leaderboard table, where **"ReProver w/ retrieval" and "ReProver w/o retrieval" both solve 0/644** (Table "putnambench"). Headline: miniF2F 57.6% Pass@32 (SFT), PutnamBench 7/644 Pass@512 (abstract). |
| Goedel-Prover-V2 | **None described** | Retrieval appears only in related work ("[LeanDojo] employs retrieval-augmented generation (RAG) to retrieve relevant theorems"). Uses Lean-compiler feedback for self-correction instead. Headline: 8B 84.6% miniF2F pass@32; 32B 88.1% (90.4% with self-correction); PutnamBench 86 at pass@184 (abstract). |
| Seed-Prover 1.0 | **Retrieval over its own lemma pool, not Mathlib** | "The lemma pool is typically used to (1) retrieve the most relevant lemmas by name or formal statement; (2) sample the most difficult lemmas" (Sec. on heavy inference). No Mathlib search tool described. Headline: 78.1% of formalized past IMO problems, >50% PutnamBench, MiniCTX-v2 81.8% (abstract; results table). |
| Seed-Prover 1.5 | **Yes — agentic Mathlib search tool** | Tools = Lean verification, "Mathlib search", Python. "For Mathlib search, we use embedding-based retrieval to identify relevant theorems by semantic similarity, calibrated to a fixed Mathlib commit (i.e., v4.22.0)". Budget: 64K tokens, max 28 tool calls per trajectory. Observed behaviour: <3 search calls per trajectory during RL; at inference ~10 per trajectory on Fate-H vs 1–2 on Putnam, "given that Fate relies heavily on Mathlib search"; search calls decreased in later checkpoints while performance rose (Sec. "Adaptive Search Behavior"). **No with/without-search ablation reported** (searched for "w/o", "without", "ablat": no hits). Headline: PutnamBench 580 (87.9%), Fate-H 80%, Fate-X 33% (comparison table). |

### Contamination / leakage discussions relevant to benchmark design

- **Kimina:** "To prevent data contamination, we perform 13-gram decontamination and explicitly remove all AMC12, AIME, and IMO problems from the Numina Math 1.5 training set if their sources overlap with problems in the miniF2F test set." Also corrected eight unsolvable miniF2F statements (e.g., `mathd_numbertheory_618`, `aime_1994_p3`) ([arXiv 2504.11354](https://arxiv.org/abs/2504.11354), Sec. "Inference Setup").
- **Seed-Prover 1.0:** evaluates on MiniCTX-v2 whose problems "were written after Nov. 2024 to prevent data contamination" — i.e., a **temporal split** ([arXiv 2507.23726](https://arxiv.org/abs/2507.23726), Sec. "MiniCTX-v2").
- **DeepSeek-Prover-V2:** introduces ProverBench (325 problems) including 15 from AIME 2024–25 as recent, presumably-unseen items; for PutnamBench it excluded problems incompatible with Lean 4.9.0 (649 evaluated) and two more after maintainers flagged misformulated statements, dropping 49 -> 47 solved ([arXiv 2504.21801](https://arxiv.org/abs/2504.21801), Sec. "Experimental Results"). Shows scores move with benchmark-statement fixes and Lean version.
- **DeepSeek-Prover-V1.5, Goedel-Prover, Goedel-Prover-V2, Seed-Prover 1.5:** no explicit test-set decontamination procedure found by the keyword search above (absence of a hit is not proof of absence; Goedel's training statements are auto-formalized from Numina, which Kimina notes overlaps with miniF2F sources).

## Relevance to lean-explore-bench

- Through 2025 the headline provers win **without** Mathlib retrieval on competition benchmarks (miniF2F, PutnamBench), where few library lemmas are needed. The first to add search (Seed-Prover 1.5) reports that its model searches much more on Fate-H (abstract algebra, Mathlib-heavy) than on Putnam — evidence that **benchmark choice decides whether retrieval matters at all**. A search-engine benchmark should use library-heavy targets (Fate-style, research repos, MiniCTX) rather than olympiad problems.
- Nobody here reports a search-on/search-off ablation, so the value of retrieval for frontier provers is **unmeasured**; an end-to-end "same agent, swap search engine / no search" track would fill a real gap. The only paired datapoint is ReProver with vs. without retrieval on PutnamBench (0 vs 0 solved) — uninformative because of floor effects.
- Seed-Prover 1.5's pinned-commit design ("calibrated to a fixed Mathlib commit") is the right reproducibility practice; we should pin Mathlib/Lean versions per benchmark release.
- Related (other slice, abstract only): "Awakening the Sleeping Agent" reports Goedel-Prover-V2 lost tool-calling ability (89.4% -> ~0% function-calling accuracy) and 100 Lean search-tool traces restored it, with ProofNet pass@32 21.51% -> 25.81% ([arXiv 2604.08388](https://arxiv.org/abs/2604.08388)) (full text not verified here). Specialized provers may not be able to use a search tool at all without adaptation.
- **Concrete reusable items:**
  1. Kimina's decontamination recipe (13-gram overlap + source-based removal) for filtering any NL query set against training corpora.
  2. Temporal split à la MiniCTX-v2 (declarations/problems created after a cutoff) for leakage-resistant queries.
  3. Tool-call telemetry (search calls per trajectory, split by benchmark) as a secondary metric for agentic evaluations.
  4. Fixed budget spec for agentic runs (max tokens, max tool calls) as in Seed-Prover 1.5 (64K / 28 calls).
  5. Report Lean/Mathlib version and any statement fixes, since PutnamBench counts shifted after corrections.

## Open questions

- What embedding model/index does Seed-Prover 1.5's "Mathlib search" use, and how much of its Fate-H score depends on it? (not stated in the paper)
- Would DeepSeek-Prover-V2 / Goedel-Prover-V2 benefit from retrieved premises in-context, or does it act as a distractor (as DRIFT observed for Goedel-V2 on miniF2F autoformalization)? See `paper-retrieval-augmented-autoformalization.md`.

## Sources

- https://arxiv.org/abs/2408.08152 (full LaTeX searched)
- https://arxiv.org/abs/2504.21801 (full LaTeX searched; ProverBench and PutnamBench sections)
- https://arxiv.org/abs/2504.11354 (full LaTeX searched; decontamination paragraph)
- https://arxiv.org/abs/2502.07640 (full LaTeX searched; PutnamBench table)
- https://arxiv.org/abs/2508.03613 (full LaTeX searched; abstract numbers)
- https://arxiv.org/abs/2507.23726 (full LaTeX searched; lemma pool, MiniCTX-v2)
- https://arxiv.org/abs/2512.17260 (full LaTeX searched; Tools, Adaptive Search Behavior, comparison table)
- https://arxiv.org/abs/2604.08388 (abstract only)
