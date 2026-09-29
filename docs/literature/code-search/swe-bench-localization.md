# SWE-bench-derived code localization evals (SWE-bench retrieval, Loc-Bench, SweRank/SweLoc, KA-LogicQuery)

- **Kind:** benchmark / dataset cluster
- **Links:**
  - SWE-bench https://arxiv.org/abs/2310.06770
  - Agentless https://arxiv.org/abs/2407.01489
  - LocAgent / Loc-Bench https://arxiv.org/abs/2503.09089 (code https://github.com/gersteinlab/LocAgent)
  - SweRank / SweLoc https://arxiv.org/abs/2505.07849
  - SweRank+ https://arxiv.org/abs/2512.20482
  - CoSIL https://arxiv.org/abs/2503.22424
  - KA-LogicQuery / LogicLoc https://arxiv.org/abs/2604.16021
  - SWE-Bench+ https://arxiv.org/abs/2410.06992
  - CodeScout https://arxiv.org/abs/2603.17829
- **Authors / org, date:** various, Oct 2023 to Apr 2026.
- **Status:** SWE-bench and its Lite/Verified subsets are the de facto standard. The localization-specific sets are research artifacts.

## What it is

"Code localization" (also called issue localization) means: given an issue description, rank the files, classes and functions that must be edited. There is no dedicated query set. Every eval in this cluster reuses SWE-bench-style (issue, gold patch) pairs, and **the gold targets are the locations touched by the merged patch** ([LocAgent §4.1](https://arxiv.org/abs/2503.09089)).

## How it works

- **SWE-bench's original retrieval setting:** BM25 over repository files, using the issue as the query, compared against an "oracle" setting that uses the files edited by the reference patch. At a 27k-token budget, BM25 retrieves a superset of the oracle files in about 40% of instances, and **none** of them in almost half ([SWE-bench §4](https://arxiv.org/abs/2310.06770)).
- **Metric convention (Acc@k, from Agentless):** a prediction succeeds only if **all** gold locations are within the top k. Loc-Bench reports file Acc@1/3/5 and function Acc@5/10, plus a relaxed module level ([LocAgent §5](https://arxiv.org/abs/2503.09089)). SWE-bench-Lite localization uses 274 of the 300 instances (those that modify existing functions) ([LocAgent §5](https://arxiv.org/abs/2503.09089)).
- **Loc-Bench (560 instances):** built to address two problems: contamination, and SWE-bench's skew toward bugs (85% bug reports, 14% feature requests, 1% security, 0% performance in Lite). Bug-report instances come from issues created after October 2024. Security and performance issues were found by GitHub keyword search. Patches touching more than 5 files or 10 functions are excluded ([LocAgent §4](https://arxiv.org/abs/2503.09089)).
- **SweLoc (training data for SweRank):** PRs from 3,387 repositories of top PyPI packages. It explicitly excludes repositories in SWE-bench and Loc-Bench "to prevent data leakage", and deduplicates near-identical repositories ([SweRank §3.1](https://arxiv.org/abs/2505.07849)).
- **KA-LogicQuery:** a diagnostic set whose queries require structural reasoning "without any naming hints" ([abstract](https://arxiv.org/abs/2604.16021)).

## Evaluation

SWE-bench-Lite function-level Acc@10, from SweRank Table 1 as extracted from PDF text. The column mapping (File@1/3/5, Module@5/10, Function@5/10) was inferred from the layout, so treat it as approximate ([arXiv 2505.07849](https://arxiv.org/abs/2505.07849)):

| System | File Acc@1 | Function Acc@10 |
|---|---|---|
| BM25 | 38.69 | 36.86 |
| CodeRankEmbed (137M) | 52.55 | 58.76 |
| LocAgent (Claude-3.5, agentic) | 77.74 | 77.37 |
| SweRankEmbed-Large (7B, single-shot retriever) | 72.63 | 82.12 |

Other reported results:

- **Lexical-overlap stratification (SweRank):** performance "generally degrades as lexical overlap decreases" between the issue and the gold function (Rouge-1 buckets). In the lowest-overlap bucket, SweRankEmbed-Large still beats LocAgent (65.2% vs 60.9%) ([SweRank App.](https://arxiv.org/abs/2505.07849)).
- **LocAgent:** up to 92.7% file-level accuracy with a fine-tuned Qwen2.5-Coder-32B ([abstract](https://arxiv.org/abs/2503.09089)).
- **CoSIL:** Top-1 function localization of 43.3% on Lite and 44.6% on Verified with Qwen2.5-Coder-32B ([abstract](https://arxiv.org/abs/2503.22424)).
- **CodeScout:** an RL-trained agent with **only a bash terminal** (no graph or embedding tools) is competitive with agents 2–18x larger that use specialized scaffolds, on SWE-Bench Verified, Pro and Lite. It is scored by file- and function-level F1 ([abstract](https://arxiv.org/abs/2603.17829)).

## Known flaws

1. **Keyword shortcut.** In over 50% of SWE-bench Lite instances, the issue text explicitly names the gold file, class or function. Such instances can be solved "via simple lexical matching (e.g. grep) or embedding-based retrieval, without requiring genuine understanding". State-of-the-art methods collapse on KA-LogicQuery, where names are withheld ([KA-LogicQuery §4](https://arxiv.org/abs/2604.16021)).
2. **Solution leakage and contamination.** SWE-Bench+ finds that 32.67% of "successful" SWE-Agent+GPT-4 patches had the solution in the issue or its comments, and that over 94% of issues predate LLM knowledge cutoffs ([abstract](https://arxiv.org/abs/2410.06992)). Agentless separately found issues with exact ground-truth patches or misleading descriptions and built SWE-bench Lite-S by removing them ([abstract](https://arxiv.org/abs/2407.01489)).
3. **Gold = the edited locations.** The locations a developer *read* to understand the bug are not credited. SWE-Explore addresses this with trajectory-derived line-level ground truth (see [agent-retrieval-evals.md](agent-retrieval-evals.md)).
4. **Task-type skew.** Lite is 85% bug reports ([LocAgent §4.1](https://arxiv.org/abs/2503.09089)).
5. **Acc@k "all locations" is strict and depends on k.** Results are not comparable to recall@k or NDCG numbers from IR benchmarks.

## Relevance to lean-explore-bench

- **The keyword-shortcut finding is the single most important transfer.** Lean queries built from theorem statements or docstrings will often contain the declaration's own identifiers (`Finset`, `card`, `sum`). Measure lexical overlap between each query and the gold name/docstring, report metrics per overlap bucket, and build a "no naming hints" stratum (as KA-LogicQuery did).
- **Freshness split:** following Loc-Bench, build a held-out set from Mathlib declarations added after the embedding models' and engines' index dates. Engines that index Mathlib at a fixed commit will simply miss them, so this also tests index freshness. Record the Mathlib commit per benchmark item.
- **Exclude eval targets from training data,** as SweLoc did. If any engine is fine-tuned on Mathlib docstring pairs, document the overlap.
- **Acc@k over "all gold premises"** is the premise-selection analogue: a query needing 3 lemmas succeeds only if all 3 are retrieved. Offer it alongside per-item recall.
- **CodeScout suggests** a strong baseline for "search inside an agent": a model with only `grep` over the Mathlib source tree.

## Open questions

- What fraction of existing Lean search benchmark queries contain the gold declaration's name tokens? This needs measuring.
- Is there a Lean analogue of "issue → edit location" (for example, a Mathlib PR description → declarations changed) that could provide naturally occurring queries?

## Sources

- SWE-bench: https://arxiv.org/abs/2310.06770
- Agentless: https://arxiv.org/abs/2407.01489
- LocAgent / Loc-Bench: https://arxiv.org/abs/2503.09089
- SweRank: https://arxiv.org/abs/2505.07849
- SweRank+: https://arxiv.org/abs/2512.20482
- CoSIL: https://arxiv.org/abs/2503.22424
- KA-LogicQuery / LogicLoc: https://arxiv.org/abs/2604.16021
- SWE-Bench+: https://arxiv.org/abs/2410.06992
- CodeScout: https://arxiv.org/abs/2603.17829
