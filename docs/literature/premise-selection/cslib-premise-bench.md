# CSLibPremiseBench: Structure-Guided Premise Retrieval and Label Robustness for Lean 4 Computer-Science Theorems (Ji)

- **Kind:** paper (benchmark / dataset)
- **Links:**
  - paper: https://arxiv.org/abs/2605.14549
  - artifact: https://doi.org/10.5281/zenodo.20176641
  - code: https://github.com/JJYYY-JJY/CSLibPremiseBench (release tag `v0.1.0`)
- **Authors / org, date:** Junye Ji (Department of Mathematics, University of Washington). arXiv v1 2026-05-14.
- **Status:** Single-author benchmark and audit paper. Benchmark JSON/CSV, rankings, bootstrap outputs and table-regeneration scripts are archived on Zenodo and mirrored on GitHub ([paper §9, artifact checklist table](https://arxiv.org/abs/2605.14549)). The license was not checked (unverified).

## What it is

A reproducible benchmark for **statement-level premise retrieval** in CSLib, the Lean 4 computer-science library. The query is a target theorem or lemma statement. The gold set is the CSLib declarations its proof references. The paper explicitly does **not** claim proof-generation results. Its stated contributions are the benchmark construction, a label audit and candidate-policy analysis. ([paper abstract, §1](https://arxiv.org/abs/2605.14549))

## How it works

The paper uses only non-learned rankers: BM25, symbol/name overlap, namespace, import-graph and PageRank priors, and fixed hand-weighted hybrids. The hybrid called CSG-Rerank combines these signals and is not tuned on the test set ([paper §5](https://arxiv.org/abs/2605.14549)).

## Evaluation

**Benchmark construction**


- **Pinned corpus.** CSLib v4.29.0 at commit `0d37cc7fcc985cfc53b155e7eef2453f846c6da2`, built with Lean 4.29.0 ([paper §3.1](https://arxiv.org/abs/2605.14549)).
- **Tasks and candidates.** There are 801 theorem/lemma tasks over 1,875 candidate declarations. Five families are covered: Algorithms, Computability, Foundations, Languages and Logics. 414 declarations are excluded under the strict policy for having no proxy gold ([paper §3.2, Table 1](https://arxiv.org/abs/2605.14549)).
- **Candidate policy.** The candidate policy is treated as an experimental variable ([paper §3.3, Table 1](https://arxiv.org/abs/2605.14549)).
  - **Strict import/source-order** is the primary setting. Candidates are CSLib declarations reachable through the target module's imports, plus same-module declarations that come *before* the target in source order. The mean is 153.1 candidates per task.
  - **Family-local fallback** is a sensitivity check with a mean of 354.8 candidates.
  - **All-earlier-CSLib fallback** is a sensitivity check with a mean of 999.6 candidates.

  The strict policy is justified as "most closely approximat[ing] accessible CSLib declarations without future leakage" ([paper §8](https://arxiv.org/abs/2605.14549)).
- **Gold labels are proxies.** Gold labels are CSLib names resolved from the **source proof text**, not elaborated dependencies. There are 2,845 proxy links over the 801 tasks ([paper §4, Table 2](https://arxiv.org/abs/2605.14549)).
  - A stricter source-visible filter, which drops ambiguous short names, keeps 2,666 of 2,845 links (93.7%).
  - A 300-task **Lean environment expression audit** checks the elaborated value-level constants. It finds only 462 of 958 proxy links (48.2%), over 257 found declarations.
  - The labels therefore miss simp, typeclass, tactic-internal and non-CSLib dependencies, and they over-represent explicitly named premises.
- **Query leakage control.** Proof text is never used as retrieval input. BM25 tokenizes Lean identifiers by splitting on dots, snake case and camel case ([paper §5](https://arxiv.org/abs/2605.14549)).

**Protocol and results**

- **Metrics:**
  - Recall@5, @10, @20 and @50;
  - MRR;
  - nDCG@5, @10, @20 and @50;
  - candidate count and runtime;
  - per-family breakdowns.

  Significance is assessed with **task-level paired bootstrap** (5,000 resamples, seed 17). A comparison whose confidence interval crosses zero is not called a win ([paper §6](https://arxiv.org/abs/2605.14549)).
- **Main results** (strict policy, 801 tasks, [paper Table 3](https://arxiv.org/abs/2605.14549)):

| Method | R@10 | R@50 | MRR |
|---|---|---|---|
| BM25 | 0.5242 | 0.7945 | 0.5061 |
| BM25+symbol | **0.5282** | **0.8013** | 0.5199 |
| CSG-Rerank | 0.5215 | 0.7930 | **0.5236** |

- **Significance tests** ([paper Table 4](https://arxiv.org/abs/2605.14549)):
  - CSG-Rerank beats BM25 on MRR by +0.0175, 95% CI [+0.0016, +0.0335].
  - CSG-Rerank against BM25+symbol on MRR: +0.0037, CI [−0.0103, +0.0173]. This is not significant.
  - Neither comparison gives a significant R@10 gain.
- **Module-disjoint dev/test check.** Of the 801 tasks, 244 go to dev and 557 to test. The picture is mixed: CSG-Rerank has the higher test MRR (0.5618 against 0.5549) but the lower test R@10 ([paper Table 5](https://arxiv.org/abs/2605.14549)).
- **Candidate-pool size changes the conclusions.** On a fixed 781-task subset, BM25 MRR falls from 0.5116 (strict) to 0.4652 (all-earlier). The full hybrid's MRR gain over BM25 grows from +0.0136, with a CI that crosses zero, to +0.0487, CI [+0.0343, +0.0639] ([paper Table 7](https://arxiv.org/abs/2605.14549)).
- **Context-packet audit.** This is a downstream proxy that does not involve an LLM. For the top-10 and top-20 packets it measures:
  - proxy-gold coverage;
  - gold density;
  - approximate tokens;
  - gold links per 1,000 tokens;
  - same-module and same-family share.

  CSG-Rerank's packets are more module-local (same-module share 0.8140 against 0.7146 at top-10). They are not better on coverage or gold per token. BM25+symbol@10 reaches coverage 0.5282 at 250.31 tokens and 6.51 gold per 1,000 tokens ([paper Table 8–9](https://arxiv.org/abs/2605.14549)).

## Relevance to lean-explore-bench

- This is the most methodologically careful retrieval paper in this slice. It is a template for **honest reporting**: paired bootstrap confidence intervals, explicit negative results, per-family breakdowns, and a pinned commit and toolchain.
- **Candidate-pool definition is a first-class variable.** Widening the pool from about 150 to about 1,000 candidates changes both absolute scores and method rankings. Our benchmark must fix and publish the searchable corpus per query. Search engines index all of Mathlib, including declarations "after" the target, so we need a policy for excluding the target itself and anything that trivially restates it.
- **Label quality needs an audit.** Only 48.2% of proof-text proxy links show up as elaborated constants. If we derive gold from source text, from elaborated dependencies, or from LLM judgments, each choice should be audited against another.
- **Strong lexical baselines are hard to beat** in-library. We must include BM25 and BM25+name-token baselines. Any "semantic" engine claim should be relative to them.
- Reusable items:
  - The Lean-identifier tokenization for BM25: split on dots, snake case and camel case.
  - The paired-bootstrap protocol (5,000 resamples, a fixed seed, and no "win" when the CI crosses zero).
  - The context-packet metrics (gold coverage, tokens, gold per 1,000 tokens). These are a cheap proxy for agent utility that accounts for result verbosity, which matters when comparing engines that return long versus short snippets.
  - CSLib itself, as an out-of-Mathlib domain for generalization queries.

## Open questions

- How do learned or dense engines (LeanSearch, LeanExplore, Lean Finder) score on this benchmark? The paper evaluates only non-learned methods.
- Would elaborated-dependency gold labels (for example from LeanGraph-style extraction) change the rankings?

## Sources

- Paper (LaTeX source read in full via arXiv): https://arxiv.org/abs/2605.14549 (v1)
- Artifact DOI: https://doi.org/10.5281/zenodo.20176641 (from the paper; not opened)
- Code: https://github.com/JJYYY-JJY/CSLibPremiseBench (from the paper; not opened)
