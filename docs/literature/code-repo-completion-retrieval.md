# Retrieval components of repo-level completion benchmarks (RepoBench-R, CrossCodeEval)

- **Kind:** benchmark / dataset
- **Links:** RepoBench https://arxiv.org/abs/2306.03091 (code https://github.com/Leolty/repobench) ; CrossCodeEval https://arxiv.org/abs/2310.11248
- **Authors / org, date:** RepoBench: Liu, Xu, McAuley (UCSD), June 2023 (ICLR 2024, unverified). CrossCodeEval: Ding, Wang, Ahmad et al. (AWS et al.), NeurIPS 2023 Datasets & Benchmarks ([arXiv comment](https://arxiv.org/abs/2310.11248)).
- **Status:** Public; widely used for repo-level completion.

## What it is

Both benchmarks evaluate next-line or statement completion where the needed context lives in *other files* of the repository. Each has a retrieval sub-evaluation:

- **RepoBench-R:** a pure retrieval task. Given the in-file context, pick the one "gold snippet" among cross-file candidates parsed from import statements ([RepoBench §3](https://arxiv.org/abs/2306.03091)).
- **CrossCodeEval:** completion in Python, Java, TypeScript and C#. Examples "strictly require cross-file context", identified by static analysis. Retrievers are compared by the downstream exact match (EM) and edit similarity (ES) they enable ([abstract](https://arxiv.org/abs/2310.11248)).

## How it works

- **RepoBench-R setup:**
  - Candidates are all snippets from imported modules.
  - Easy subset: 5–9 candidates. Hard subset: 10 or more.
  - Metrics: acc@1/acc@3 (easy) and acc@1/3/5 (hard).
  - Two masking settings: first use (XF-F) and random non-first use (XF-R) of the cross-file symbol ([RepoBench §3](https://arxiv.org/abs/2306.03091)).
- **Leakage mitigation:**
  - RepoBench adds "newly crawled" repositories created after Feb 9, 2023 ([RepoBench §3](https://arxiv.org/abs/2306.03091)).
  - CrossCodeEval uses repositories created between 2023-03-05 and 2023-06-15, and removes examples that StarCoderBase-1B can complete without cross-file context ([CrossCodeEval §2](https://arxiv.org/abs/2310.11248)).

## Evaluation

- CrossCodeEval compares BM25, UniXcoder and OpenAI ada as cross-file retrievers. For CodeGen2.5-7B on Python, EM with retrieval was 14.52 (BM25), 13.73 (UniXcoder) and 14.82 (ada), per the appendix table as extracted from PDF text ([arXiv 2310.11248](https://arxiv.org/abs/2310.11248)). The three retrievers are within about 1 EM point, and **BM25 is competitive**.
- RepoBench-R baselines include random, lexical (Jaccard, edit distance) and CodeBERT/UniXcoder embeddings ([RepoBench Table 2](https://arxiv.org/abs/2306.03091)). Exact values are not transcribed here.

## Known flaws

1. **Relevance is defined by a single gold snippet** that contains the masked symbol's definition. That is close to a *name-lookup* problem, which may explain why lexical retrieval does well.
2. **Downstream EM mixes retriever and generator quality.**
3. **Temporal cutoffs age quickly.** Repositories from 2023 are now inside most training corpora.

## Relevance to lean-explore-bench

- **RepoBench-R is structurally close to Lean premise retrieval:** given the local context (a proof state or file prefix), pick the definition or lemma that will be used next. The "candidates = things importable from here" restriction corresponds to "declarations available under the current imports".
- **Use candidate-set size to define difficulty strata** (easy/hard), and report acc@k.
- **Mask first-use versus later-use** of a lemma: later uses have in-file evidence, which is an easier regime.
- **Lesson:** when the target is a named symbol, BM25 and identifier matching are hard to beat. Name-query strata in Lean should expect the same.

## Open questions

- Should the benchmark include a "proof-context → next premise" task at all, or leave that to premise-selection benchmarks (LeanDojo and similar, covered by other notes)?

## Sources

- RepoBench: https://arxiv.org/abs/2306.03091
- CrossCodeEval: https://arxiv.org/abs/2310.11248
