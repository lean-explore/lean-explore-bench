# LeanAgent: Lifelong Learning for Formal Theorem Proving

- **Kind:** paper
- **Links:** paper [arXiv:2410.06209](https://arxiv.org/abs/2410.06209) (v8, March 2025); code <https://github.com/lean-dojo/LeanAgent> (per paper Sec. 4.1)
- **Authors / org, date:** Adarsh Kumarappan, Mo Tiwari, Peiyang Song, Robert Joseph George, Chaowei Xiao, Anima Anandkumar (Caltech, Stanford, UW-Madison); first posted October 2024 ([arXiv](https://arxiv.org/abs/2410.06209)). ICLR 2025 venue (unverified; not stated in the text we read).
- **Status:** Code released per the paper. License not checked (unverified).

Caveat: the arXiv **LaTeX source** appears to be an older draft. It contains TODO markers and says "162 … sorry theorems across 22 repositories." The rendered **v8 HTML** and the abstract say 155 theorems across 23 repositories. Numbers below come from the v8 HTML ([arXiv HTML v8](https://arxiv.org/html/2410.06209v8)).

## What it is

A lifelong-learning framework that keeps a ReProver-style premise retriever up to date as it moves through a curriculum of GitHub Lean repositories, then tries to prove each repository's `sorry` theorems ([arXiv:2410.06209](https://arxiv.org/abs/2410.06209)).

## How it works

The ReProver retriever is trained for one extra epoch per new repository, in curriculum order. Premise embeddings over the growing corpus are recomputed after each round. Proving uses ReProver's tactic generator with 100 retrieved accessible premises per state, inside best-first search with a 10-minute budget ([paper, Sec. 3 and App. A.2](https://arxiv.org/html/2410.06209v8)).

## Evaluation

- **Repositories.** 23 Lean repos, among them PFR, Hairy Ball, Coxeter, MIL source, Formal Book, MiniF2F (Lean 4), SciLean, Carleson, and Lean4 PDL. The lifelong metrics use an initial curriculum of 14 repos ([paper, Sec. 4.1, 4.3](https://arxiv.org/html/2410.06209v8)).
- **Split.** Each repo is split with LeanDojo's **random** split. "We refrain from using the novel split from LeanDojo, as we would like LeanAgent to learn as much as possible from a repository." The starting retriever is also "ReProver's retriever trained on the random split" ([paper, App. A.1-A.2](https://arxiv.org/html/2410.06209v8)). On MiniF2F they "disregard its separation into validation and test splits" ([paper, Sec. 4.2](https://arxiv.org/html/2410.06209v8)).
- **Retrieval-only metrics.** Validation R@10 on the newest repo measures plasticity. Average test R@10 over all repos seen so far measures stability. Six lifelong-learning metrics are derived from these: WF5, FM, CFR, EBWT, WP5 and IP ([paper, Sec. 4.3, Table 3](https://arxiv.org/html/2410.06209v8)). We did not find absolute R@10 values in the main text; only derived metrics are tabulated.
- **Lifelong metrics, single-repository setting (Table 4)** ([source](https://arxiv.org/html/2410.06209v8)): LeanAgent WF5 0.18, FM 0.85, CFR 0.88, EBWT 1.21, WP5 2.47, IP 1.02. The best other single-repo setup has WF5 0.73 and FM 2.11 (Setup 3). The paper reports WF5 75.34% lower, FM 59.97% lower, and EBWT 16.25% higher than the next-best setup.
- **End-to-end metric.** `sorry`-theorem accuracy = proven / total `sorry`s per repo, compared with ReProver (frozen) and "ReProver+" (updated on all 23 repos at once). Examples from Table 2 ([source](https://arxiv.org/html/2410.06209v8)):

| Repo | #sorrys | LeanAgent total % | ReProver % | ReProver+ % |
|---|---|---|---|---|
| MIL | 29 | 72.4 | 48.3 | 55.2 |
| MiniF2F | 406 | 24.4 | 20.9 | 20.9 |
| SciLean | 294 | 9.2 | 8.2 | 8.5 |
| PFR | 37 | 2.7 | 0.0 | 0.0 |

- **Headline claim.** 155 `sorry` theorems proved across 23 repos, plus "7 system exploits" found on PFR. Five of these were `sorry` theorems with a `0=1` placeholder statement ([paper, Sec. 4.2](https://arxiv.org/html/2410.06209v8)).

## Relevance to lean-explore-bench

- **Cross-repository retrieval is the most realistic setting for a search tool.** New premises from projects outside Mathlib keep appearing, and an engine indexed on a fixed Mathlib snapshot degrades on them. LeanAgent's per-repo R@10 over time is a template for measuring index freshness or coverage.
- **Leakage warning.** It uses random splits throughout, a retriever pre-trained on the random split, and ignores MiniF2F's val/test separation. These results should not be read as leakage-controlled generalization numbers.
- **"Unproved `sorry`" targets have no ground truth, and some are degenerate.** Five had `0=1` placeholder statements, so "proofs" can exploit bad statements. Any end-to-end task we build must vet target statements.
- **The retrieval-to-proving link is weak here too.** Derived stability metrics are argued to "explain" proving gains, but no controlled ablation isolates the retriever's contribution to proof success.
- **Reusable items:**
  - A multi-repo test pool (PFR, Carleson, SciLean, Coxeter, and others) for an out-of-Mathlib retrieval track.
  - The "average test R@10 over all previously seen repos" protocol, for index-update or versioning studies.

## Open questions

- What are the absolute R@10 values per repo? These may be in the appendix or repo, which we did not read.
- How much of the proving gain comes from retriever updates versus changes to the corpus? The corpus is re-embedded each round.

## Sources

- Kumarappan et al., "LeanAgent: Lifelong Learning for Formal Theorem Proving", arXiv:2410.06209 (v8 HTML read for Sec. 1-4 and App. A.1-A.2; LaTeX source also read, which is an older draft): <https://arxiv.org/abs/2410.06209>, <https://arxiv.org/html/2410.06209v8>
- Code (as linked in the paper): <https://github.com/lean-dojo/LeanAgent>
