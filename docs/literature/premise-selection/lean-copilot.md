# Lean Copilot (`select_premises`)

- **Kind:** paper (tool)
- **Links:** paper [arXiv:2404.12534](https://arxiv.org/abs/2404.12534) (NeuS 2025); code <https://github.com/lean-dojo/LeanCopilot>; evaluation code and per-theorem results <https://github.com/Peiyang-Song/mathematics_in_lean/tree/full-scale-experiment>
- **Authors / org, date:** Peiyang Song, Kaiyu Yang, Anima Anandkumar (Caltech / LeanDojo); v1 April 2024, v3 May 2025 ([arXiv](https://arxiv.org/abs/2404.12534)).
- **Status:** Open source under the MIT license ([paper, artifacts section](https://arxiv.org/abs/2404.12534); [README](https://github.com/lean-dojo/LeanCopilot)).

## What it is

A framework for running LLM inference natively inside Lean 4. It provides three user-facing tactics: `suggest_tactics`, `search_proof`, and `select_premises` ([arXiv:2404.12534](https://arxiv.org/abs/2404.12534)). `select_premises` is the in-editor premise retriever that is relevant to our benchmark.

## How it works

`select_premises` encodes the current goal with ReProver's ByT5 encoder and scores it by dot product against precomputed ReProver premise embeddings, then annotates each hit as in scope (showing type and docstring) or out of scope (showing the module to import and the source) ([paper, Sec. 3-4](https://arxiv.org/abs/2404.12534)). The README says it retrieves "from a fixed snapshot of Lean and mathlib4"; the referenced mathlib4 commit is `3ce43c18…`, the same snapshot as LeanDojo Benchmark 4. It does not index the user's local project ([README](https://github.com/lean-dojo/LeanCopilot); commit per WebFetch summary of the repo, (unverified) against source files).

## Evaluation

- **Premise selection was not evaluated.** The paper states: "We focus on evaluating `suggest_tactics` and `search_proof`, as `select_premises` is mainly a helping tool, and it remains a challenge in the field to effectively evaluate premise selection due to the inherent lack of ground truths" ([paper, Sec. 5](https://arxiv.org/abs/2404.12534)). The paper reports no recall or ranking numbers for `select_premises`; the only retrieval numbers are ReProver's own on LeanDojo Benchmark 4 (see `leandojo-reprover.md`).
- **Dataset.** All 168 theorems with tactic-style proofs in *Mathematics in Lean* (MIL), totalling 983 tactics (5.85 per theorem). The authors argue MIL was not in ReProver's fine-tuning data and predates ByT5's cutoff ([paper, Sec. 5](https://arxiv.org/abs/2404.12534)).
- **Protocol (human-in-the-loop simulation).** Ground-truth tactics are entered one at a time. After each one, each tool is tried on the remaining goals, and the number of manually entered tactics before the tool succeeds is recorded ([paper, Sec. 5](https://arxiv.org/abs/2404.12534)).
- **Results (Table 1)** ([source](https://arxiv.org/abs/2404.12534)):

| Method | Avg. human-entered tactics (lower is better) | % theorems proved autonomously | Avg. % proof steps automated |
|---|---|---|---|
| `aesop` | 3.86 | 24.4% | 40.1% |
| `suggest_tactics` | 3.10 | 45.2% | 58.3% |
| `search_proof` | 2.08 | 63.7% (107/168) | 74.2% |

  The paper's prose gives slightly different numbers for `suggest_tactics` (3.11 and 58.4%) than its table ([source](https://arxiv.org/abs/2404.12534)).
- **Baselines.** `aesop` out of the box; no comparison against other premise selectors or search engines.

## Relevance to lean-explore-bench

- This is an explicit statement from the LeanDojo group that the lack of ground truth makes interactive premise selection hard to evaluate. Our benchmark should confront this directly, with graded or multi-answer relevance judgments rather than single gold labels.
- The "number of human steps saved" protocol on MIL is a reusable *assistive* end-to-end metric that measures utility rather than recall.
- A fixed-snapshot index (Oct 2023 mathlib4) is a staleness risk. Any evaluation of `select_premises` against current Mathlib will penalize it for renames and new lemmas, so snapshot alignment must be reported.
- **Reusable items:**
  - `select_premises` as a baseline "engine" (proof-state query, ReProver embeddings).
  - The MIL 168-theorem set and its step-by-step protocol for measuring human effort saved.
  - The in-scope/out-of-scope annotation idea, which suggests an "import-aware" metric: does the engine surface lemmas the current file can actually use?

## Open questions

- Can `select_premises` be pointed at a newer Mathlib by regenerating embeddings? The README suggests the snapshot is fixed; not checked in code.
- No numbers exist for `select_premises` itself. Would its MIL goal queries recover the premises used in MIL's ground-truth proofs?

## Sources

- Song, Yang, Anandkumar, "Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean", arXiv:2404.12534v3 (LaTeX source read): <https://arxiv.org/abs/2404.12534>
- LeanCopilot README: <https://github.com/lean-dojo/LeanCopilot>
- Evaluation artifacts: <https://github.com/Peiyang-Song/mathematics_in_lean/tree/full-scale-experiment>
