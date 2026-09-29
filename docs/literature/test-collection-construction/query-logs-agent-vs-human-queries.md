# Agent-issued vs human-issued queries: what 2025–2026 log studies show (synthesis)

- **Kind:** paper (synthesis note)
- **Links:**
  - Ning et al., "Agentic Search in the Wild", SIGIR 2026 ([arXiv 2601.17617](https://arxiv.org/abs/2601.17617), [logs on HF](https://huggingface.co/datasets/cx-cmu/deepresearchgym-agentic-search-logs))
  - Pezzuti et al., "A Picture of Agentic Search", 2026 ([arXiv 2602.17518](https://arxiv.org/abs/2602.17518))
  - Amani et al., "Characterizing Web Search by Conversational LLM Agents", 2026 ([arXiv 2609.19244](https://arxiv.org/abs/2609.19244))
  - Schall et al., "Q2D-Web", 2026 ([arXiv 2609.08887](https://arxiv.org/abs/2609.08887))
  - Liu et al., "Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents", 2026 ([arXiv 2608.01913](https://arxiv.org/abs/2608.01913))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

Lean search engines are used both by humans (web UIs, editor commands) and by agents (MCP/API tools such as [lean-lsp-mcp](../lean-tools/lean-lsp-mcp.md)). A benchmark built from human-style queries may mis-rank systems for agent traffic, and the reverse also holds. This note collects the first log-based studies that compare the two populations. The scope is how their query distributions differ, not how agents should search.

## How it works (the studies)

- **Ning et al. (SIGIR 2026).** 14.44M search requests in 3.97M sessions from DeepResearchGym, a public search API used by external agent clients ([arXiv 2601.17617](https://arxiv.org/abs/2601.17617)).
  - **Sessions:**
    - 47.77% of sessions are single-query.
    - Among multi-turn sessions, 90% have ≤10 steps.
    - 89.21% of inter-step gaps are under one minute.
    - Human web logs they cite show 1.7 queries/session and 77.6% single-query sessions (§5).
  - **Intent** (LLM-labelled, 95.15% agreement on a check sample): Declarative/fact-seeking 88.64%, Reasoning 7.41%, Procedural 3.96%.
  - **Query length:** mean whitespace terms 7.59 (declarative), 10.58 (procedural) and 12.69 (reasoning). Agents "phrase queries as full constraint-bearing questions" (§6, Table 3).
  - **Repetition:** 38.38% of distinct queries are singletons. The top-100 queries account for only 1.51% of requests (§3).
  - **Retrieval depth** is effectively hard-coded: K ∈ {1, 5, 10} in all but 8.36% of sessions (§5).
  - **Evidence-driven reformulation:** on average 54% of newly introduced query terms appear in previously retrieved evidence (abstract).
  - **Benchmark-contamination check:** under 0.4% of 1M log queries had cosine ≥ 0.7 to GAIA, FRAMES, HLE or WebWalkerQA queries. So the traffic is not dominated by benchmark runs (Table 2).
- **Pezzuti et al. (2026), ASQ dataset.** They instrumented agentic RAG systems (3 agents, 2 retrieval pipelines) on HotpotQA, Researchy Questions and MS MARCO, and compared reformulation Markov chains with human ones from Pass et al. 2006 (the AOL-era "A picture of search") ([arXiv 2602.17518](https://arxiv.org/abs/2602.17518), §6).
  - Agents move to *CH* (substantial reformulation) and *DUP* (re-issuing an earlier query) more than humans do. They rarely do REP, which in humans is paging for more results.
  - A larger model issued up to +265% more search calls, and traces reached 186 steps. Humans typically abandon after 2–3 reformulations.
  - Reformulation behaviour was "independent from the effectiveness of the retrieval pipeline", i.e. governed by the agent rather than by the retriever.
  - The authors warn that caching, query pre-processing and standard satisfaction metrics built for humans may not transfer.
- **Amani et al. (2026).** Donated real traces: 171,264 conversations from 613 users on ChatGPT, Claude, Grok and DeepSeek, plus controlled API runs ([arXiv 2609.19244](https://arxiv.org/abs/2609.19244)).
  - Median web queries per prompt ranges from 2 (Claude) to 4 (Grok). ChatGPT, Grok and DeepSeek fan out queries in parallel; Claude issues one query per iteration and goes deeper.
  - Nearly 80% of user prompts have more than 20 terms, while "almost all" agent queries have fewer than 10–15 terms. That is still "substantially longer" than typical 2–4-term human queries.
  - First-iteration query terms come from conversation history (80%) and the latest prompt (30%). Later iterations draw increasingly on earlier search results.
- **Q2D-Web (Perplexity, 2026).** About 70k agent-reformulated queries from about 23k production searches over nine months ([arXiv 2609.08887](https://arxiv.org/abs/2609.08887), §1, §3.1).
  - Each search contains one *primary* query restating the user intent plus about 4 *support* queries: 17.7% primary vs 82.3% support.
  - The motivation is that first-stage retrievers "serve machine-written reformulations whose distribution differs from human search behavior".
  - Q2D-Web cites Penha et al. 2022: intent-preserving reformulations cut nDCG@10 by about 20% on average. That figure comes via Q2D-Web; the primary was not read here (unverified).
- **Liu et al. (2026).** Across six deep-search agents, answer accuracy tracks cumulative retrieval recall more than the number of searches. Agents produce "a long tail of low-yield retrieval steps", and the best agents issue "far fewer redundant queries" ([arXiv 2608.01913](https://arxiv.org/abs/2608.01913), abstract).

## Evaluation (human vs agent, side by side)

| Property | Human (source) | Agent (source) |
|---|---|---|
| Query length | 2.35 terms (AltaVista 1998, [Silverstein](https://sigir.org/files/forum/F99/Silverstein.pdf)); 1.85 keywords (Google Code Search, [Sadowski](https://research.google.com/pubs/archive/43835.pdf)); 6.7 words (math web queries, [Mansouri](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf)) | 7.6–12.7 terms by intent ([Ning](https://arxiv.org/abs/2601.17617)); mostly fewer than 10–15 terms ([Amani](https://arxiv.org/abs/2609.19244)) |
| Queries per need | 77.6% single-query sessions (as cited by [Ning](https://arxiv.org/abs/2601.17617)) | median 2–4 per prompt ([Amani](https://arxiv.org/abs/2609.19244)); 47.77% single-query sessions ([Ning](https://arxiv.org/abs/2601.17617)) |
| Reformulation style | expand, page for more, abandon after 2–3 | substantial rewrites and exact re-issues of old queries; loops ([Pezzuti](https://arxiv.org/abs/2602.17518)) |
| Pacing | minutes of dwell | 56% of steps within 10 s ([Ning](https://arxiv.org/abs/2601.17617)) |
| Term provenance | user's head | conversation, prior results, parametric knowledge ([Amani](https://arxiv.org/abs/2609.19244), [Ning](https://arxiv.org/abs/2601.17617)) |
| Result depth | only the first result screen for 85% of queries ([Silverstein](https://sigir.org/files/forum/F99/Silverstein.pdf)) | fixed K ∈ {1, 5, 10} ([Ning](https://arxiv.org/abs/2601.17617)) |

## Relevance to lean-explore-bench

- **Treat "client type" as a first-class stratum.** Label each logged query as human (web UI), agent (MCP / API with an agent user-agent or tool-call signature) or unknown, and report metrics per stratum. Both [Q2D-Web](https://arxiv.org/abs/2609.08887) and [Ning et al.](https://arxiv.org/abs/2601.17617) show agent traffic has a different form and intent mix. Size the strata from the actual traffic split rather than 50/50.
- **Expect agent queries to be longer and to carry context.** Agent queries will contain restated goals, Lean fragments and terms from earlier results. Human queries will be shorter name fragments and NL phrases. Lexical shortcuts (declaration names copied from earlier results) are more likely in agent traffic, so control lexical overlap as in [../code-search/search-evaluation-methodology.md](../code-search/search-evaluation-methodology.md).
- **Unit of evaluation for agents.** A single agent need produces a *burst* of 2–4+ queries, including exact duplicates. Sampling individual queries over-weights long loops. Consider sampling *searches/sessions* and evaluating either (a) the primary query alone, (b) each support query with its own labels (the Q2D-Web design), or (c) set-level recall over the burst. Set-level recall is the quantity Liu et al. found correlates with answer accuracy.
- **Fixed K.** Agents call with a fixed small K, often 5–10. Weight Recall@K and nDCG@K at the K values agents actually request, not only @10/@100.
- **Deduplicate agent loops before sampling.** Otherwise repeated DUP queries from a single stuck trace dominate the sample ([Pezzuti et al.](https://arxiv.org/abs/2602.17518)).
- **Check agent traffic for benchmark contamination.** Repeat Ning et al.'s check against MathlibQR, LeanSearch v1, Lean Finder and miniF2F/ProofNet statements. Automated evaluation runs of *other* benchmarks through the MCP would otherwise leak into a "real traffic" set.
- **Related notes:** [../code-search/agent-retrieval-evals.md](../code-search/agent-retrieval-evals.md) (agent-in-the-loop retrieval metrics) and [../lean-engines/leandex.md](../lean-engines/leandex.md) (an engine that itself LLM-rewrites queries, which adds a third query population).

## Open questions

- What fraction of Lean search traffic comes from agents? Can the client be identified reliably from the MCP vs HTTP path and user-agent strings?
- Do system rankings on human Lean queries agree with rankings on agent Lean queries? Q2D-Web found rankings robust to judgment-set choice but divergent across query types.
- Should a benchmark replay whole agent trajectories (the query depends on earlier results) or freeze individual queries? Frozen queries ignore the fact that agent query terms come from previous results (54% per Ning et al.).

## Sources

- Ning et al., "Agentic Search in the Wild: Intents and Trajectory Dynamics from 14M+ Real Search Requests", SIGIR 2026: https://arxiv.org/abs/2601.17617
- Pezzuti, Frieder, Silvestri, MacAvaney & Tonellotto, "A Picture of Agentic Search", 2026: https://arxiv.org/abs/2602.17518
- Amani et al., "Characterizing Web Search by Conversational LLM Agents: From Search Decisions and Strategies to Results and Responses", 2026: https://arxiv.org/abs/2609.19244
- Schall et al., "Q2D-Web: A Large-Scale Benchmark for Retrieval in Agentic RAG Systems", 2026: https://arxiv.org/abs/2609.08887
- Liu, Mao, Zhu & Chua, "Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents", 2026: https://arxiv.org/abs/2608.01913
- Human baselines: Silverstein et al. 1999 https://sigir.org/files/forum/F99/Silverstein.pdf ; Sadowski et al. 2015 https://research.google.com/pubs/archive/43835.pdf ; Mansouri et al. 2019 https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf
