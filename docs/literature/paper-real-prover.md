# REAL-Prover: Retrieval Augmented Lean Prover (LeanSearch-PS)

- **Kind:** paper
- **Links:** paper https://arxiv.org/abs/2505.20613 ; code https://github.com/frenzymath/REAL-Prover
- **Authors / org, date:** Ziju Shen, Naohao Huang, Fanyi Yang, Yutong Wang, Guoxiong Gao, et al., Bin Dong (Peking University, Renmin University, Ubiquant), arXiv May 2025, v3 Nov 2025.
- **Status:** code repo linked from the paper; paper claims release of a 55k state-tactic dataset ([§1.2](https://arxiv.org/abs/2505.20613)). License not checked (unverified).

## What it is

A stepwise Lean 4 prover whose every tactic call is conditioned on premises retrieved from Mathlib by LeanSearch-PS, plus a new benchmark FATE-M (141 undergraduate abstract-algebra problems) ([abstract, §3.2](https://arxiv.org/abs/2505.20613)).

## How it works

One sentence: LeanSearch-PS is an E5-mistral-7b-instruct dense retriever (LoRA, InfoNCE, then hard negatives sampled from ranks 30-100) trained on (proof state, applied theorem) pairs extracted from Mathlib with Jixia, whose top-k results are pasted into the prompt of a Qwen2.5-Math-7B tactic generator running best-first search ([§2.2, §3.1](https://arxiv.org/abs/2505.20613)).

## Evaluation

- **Retrieval-only metrics:** none reported for LeanSearch-PS in this paper; it is evaluated only through end-to-end proving. (Lean Finder later reports "Real Prover Search" retrieval numbers on its own proof-state benchmark, e.g. 8.0 / 29.0 / 39.2 in its Table on proof-state input ([arXiv 2510.15940](https://arxiv.org/abs/2510.15940)); column semantics not re-verified here (unverified).)
- **Benchmarks:** ProofNet test (186), miniF2F test (244), FATE-M (141 problems from 12 algebra textbooks, formalized by students and checked by Mathlib contributors and algebra PhD students) ([§3.2](https://arxiv.org/abs/2505.20613)).
- **Budget:** 64 passes x 64 samples per step ([§3.1](https://arxiv.org/abs/2505.20613)).
- **Headline numbers:** ProofNet 23.7%, FATE-M 56.7%, miniF2F 54.1% ([Tables 1-3](https://arxiv.org/abs/2505.20613)). Baselines on FATE-M: Goedel-Prover 18.7% (128 samples), DeepSeek-Prover-V1.5-RL 31.2% (128), DeepSeek-Prover-V1.5-RL + RMaxTS 41.8% (64x64).
- **Retrieval ablation** ([Table 4](https://arxiv.org/abs/2505.20613)): a separate model REAL-Prover-v1-NoRet trained on the same data without retrieval context, run without LeanSearch-PS:

| System | ProofNet | FATE-M |
|---|---|---|
| NoRet model, no retrieval | 22.6% | 44.7% |
| REAL-Prover-v1 + LeanSearch-PS | 23.7% | 56.7% |

- Authors attribute the weak miniF2F result partly to competition problems not relying heavily on Mathlib theorems, so retrieval helps less there ([§4.3](https://arxiv.org/abs/2505.20613)).
- **Leakage/splits:** no explicit decontamination between the Mathlib-extracted training pairs / expert-iteration data and the test benchmarks is described; FATE-M is new and textbook-sourced. Not discussed further in the paper.
- **Independent replication of the retriever swap:** Lean Finder replaced LeanSearch-PS inside REAL-Prover at an 8x8 budget and got miniF2F 52.0 -> 52.0, ProofNet 23.7 -> 23.1, FATE-M 51.1 -> 49.6 (w/o -> w/ Lean Finder); the Lean Finder authors suggest the tactic generator is tuned to its native retriever's signal ([arXiv 2510.15940, App. "RAG for LLM Provers"](https://arxiv.org/abs/2510.15940)).

## Relevance to lean-explore-bench

- Shows the typical "retrieval ablation" in prover papers: retrain without retrieval and compare end-to-end. The effect is large on a Mathlib-heavy benchmark (FATE-M +12.0 points) and small on ProofNet (+1.1), and near-zero on competition math, so the choice of downstream benchmark decides whether retrieval looks useful.
- A prover trained with one retriever's output format is not a neutral harness for comparing retrievers (the Lean Finder swap shows no gain). Our downstream evaluation should use an untrained-for-retrieval agent (general LLM with a tool) or retrain per retriever.
- No intrinsic retrieval metric means there is no way to tell from this paper whether LeanSearch-PS retrieves well; our benchmark should always report retrieval-only metrics alongside downstream ones.

**Concrete reusable items:**
1. FATE-M (141 problems) as a Mathlib-heavy downstream set where retrieval measurably matters.
2. The (proof state, applied theorem) extraction via Jixia as a way to build proof-state -> premise gold labels.
3. The ablation pattern "with vs without retrieval, same budget" as a required row in any downstream table.

## Open questions

- The paper says both "Queries are formal statements" and that proof states are embedded at inference ([§3.1 vs §2.2](https://arxiv.org/abs/2505.20613)); the exact query at train vs test time is ambiguous.
- Value of k (number of retrieved premises) is not stated in the text; the prompt example shows IDs 0-5 ([App. A](https://arxiv.org/abs/2505.20613)) (unverified that k = 6).

## Sources

- REAL-Prover paper: https://arxiv.org/abs/2505.20613 (read in full, LaTeX source v3)
- Lean Finder paper (retriever-swap experiment): https://arxiv.org/abs/2510.15940
- Code: https://github.com/frenzymath/REAL-Prover (not fetched)
