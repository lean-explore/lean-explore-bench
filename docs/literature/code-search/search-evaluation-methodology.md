# How code search is evaluated: query sources, relevance, metrics, leakage (cross-cutting synthesis)

- **Kind:** paper (synthesis note)
- **Links:** see the per-benchmark notes: [codesearchnet.md](codesearchnet.md), [cosqa.md](cosqa.md), [coir.md](coir.md), [coderag-bench.md](coderag-bench.md), [swe-bench-localization.md](swe-bench-localization.md), [agent-retrieval-evals.md](agent-retrieval-evals.md), [newer-retrieval-benchmarks.md](newer-retrieval-benchmarks.md), [embedding-vs-grep-evidence.md](embedding-vs-grep-evidence.md)
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

A comparison table of evaluation design choices across the code-search literature, and what each implies for a Lean declaration-search benchmark.

## How it works (comparison)

| Benchmark | Query source | Relevance labels | Positives/query | Metric | Leakage handling |
|---|---|---|---|---|---|
| CodeSearchNet proxy | docstring first paragraph | implicit (own function) | 1 | MRR vs 999 distractors | none (2019 GitHub) |
| CodeSearchNet Challenge | 99 Bing queries with high code CTR plus StaQC rewrites; name-like queries removed | expert 0–3 graded, κ = 0.47, pooled top-10 | graded set | NDCG (within judged / all) | none |
| AdvTest | docstrings | implicit | 1 | MRR | identifiers masked in test |
| CoSQA | Bing logs, intent-filtered | binary, ≥3 annotators, α = 0.63, CodeBERT-prefiltered | 1 (for MRR) | MRR | none |
| CoSQA+ | CoSQA queries | LLM test-driven agent (93.9% acc) plus 1k human-verified | many | MAP@10, NDCG@10, MRR, Recall | none stated |
| CoIR | derived from 10 datasets | inherited | mostly 1 | NDCG@10 | overfitting to CSN noted |
| CodeRAG-Bench | task statements | canonical docs (auto-parsed plus manual) | ~1–2 | NDCG@10 plus pass@k | includes LiveCodeBench for freshness |
| SWE-bench localization | GitHub issues | files/functions in gold patch | several | Acc@k (all gold in top k) | SWE-Bench+: >94% pre-cutoff; solution leakage |
| Loc-Bench | issues after Oct 2024 | patch locations | several | Acc@k | temporal cutoff |
| SWE-Explore | issues | lines read by ≥2 successful agent trajectories | many (lines) | coverage/ranking/efficiency under line budget | not stated |
| Agent Retrieval Bench | real workflow signals (test↔code, traces, ripple edits) | "what the agent needs next" | several files | MRR, Recall@20, budgeted yield, abstention | frozen base commits |
| ExecRetrieval | task statements | execution-verified | 1 + buggy near-clones | exec@k, McNemar | not stated |
| FreshStack | recent Stack Overflow Q&A | GPT-4o nugget support | many | α-nDCG@10, Coverage@20, Recall@50 | recency by construction |

Sources for every row are in the linked notes.

## Evaluation (recurring lessons, each with a source)

1. **Proxy queries mislead.** Models that are best on docstring→code MRR were worse on real queries, and keyword matching was "a crucial facility" ([CodeSearchNet](https://arxiv.org/abs/1909.09436)). CoIR also found CSN scores inflated ([CoIR](https://arxiv.org/abs/2407.02883)).
2. **Single-gold MRR undercounts.** Many code units satisfy the same query ([CoSQA+](https://arxiv.org/abs/2406.11589)).
3. **Pooling and prefiltering bias.** Labels exist only for what the pooled baselines retrieved ([CSN](https://arxiv.org/abs/1909.09436), [CoSQA](https://arxiv.org/abs/2105.13239)).
4. **Human agreement is only moderate** (κ = 0.47 in CSN; α = 0.63 in CoSQA after dropping low-agreement pairs), so graded labels and guidelines matter.
5. **Keyword shortcuts inflate scores.** Over 50% of SWE-bench Lite issues name the gold location ([KA-LogicQuery](https://arxiv.org/abs/2604.16021)). Performance falls as lexical overlap falls ([SweRank](https://arxiv.org/abs/2505.07849)).
6. **Contamination:** public, pre-cutoff data dominates ([SWE-Bench+](https://arxiv.org/abs/2410.06992)). Mitigations include temporal cutoffs ([Loc-Bench](https://arxiv.org/abs/2503.09089), [CrossCodeEval](https://arxiv.org/abs/2310.11248)) and excluding eval repositories from training data ([SweLoc](https://arxiv.org/abs/2505.07849)).
7. **Topical similarity ≠ correctness** (exec@1 = 0.331 despite exec@10 = 1.00 in [ExecRetrieval](https://arxiv.org/abs/2609.01865)).
8. **Retrieval metrics ≠ downstream usefulness,** so pair IR metrics with task success ([CodeRAG-Bench](https://arxiv.org/abs/2406.14497), [SWE-Explore](https://arxiv.org/abs/2606.07297)).
9. **In agents, measure what was surfaced under a budget, and test abstention** ([Agent Retrieval Bench](https://arxiv.org/abs/2607.24882)).

## Relevance to lean-explore-bench (proposed design implications)

- **Query strata, each reported separately:**
  1. natural-language intent, from real logs or Zulip
  2. informal statement of a theorem
  3. exact/partial name
  4. type/pattern (Loogle-style)
  5. proof-state/goal
  6. "no naming hints" (lexical-overlap-controlled)
  7. near-clone distractor set
  8. no-gold (abstention)
- **Labels:** graded (exact / equivalent variant / generalization / specialization / related / irrelevant) with multiple positives. Pool from all engines under test plus BM25 and grep. Where the query is goal-shaped, auto-verify with Lean (`exact`/`apply`/`rw` succeeds). Report inter-annotator agreement.
- **Metrics:** nDCG@10 (graded), Recall@k and MAP@k (multi-positive), MRR only as a secondary metric, Acc@k-all for multi-premise queries, and bootstrap CIs with paired significance tests. For in-agent mode, add task success, tokens, tool calls and gold-surfaced rate.
- **Leakage:** pin the Mathlib commit. Keep a post-cutoff split of declarations added after the engines' index and model dates. Record whether any engine trained on Mathlib docstrings or informalizations that overlap with test queries. Keep a hidden test split.
- **Packaging:** BEIR/MTEB-compatible format so off-the-shelf embedders plug in ([CoIR](https://arxiv.org/abs/2407.02883)).

## Open questions

- How should equivalent-but-differently-named lemmas be credited when Mathlib deprecates one in favour of another between commits?

## Sources

All sources are cited inline and listed in the linked per-benchmark notes.
