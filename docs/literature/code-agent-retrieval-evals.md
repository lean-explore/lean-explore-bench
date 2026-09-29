# Evaluating retrieval inside coding agents (SWE-Explore, Agent Retrieval Bench, semantic vs. deep agentic search on SWE-QA, RepoQA)

- **Kind:** benchmark / paper cluster
- **Links:**
  - SWE-Explore https://arxiv.org/abs/2606.07297
  - Agent Retrieval Bench https://arxiv.org/abs/2607.24882
  - "Deep Agentic Search for Repository-Level Code QA: An Empirical Study" https://arxiv.org/abs/2608.01507
  - RepoQA https://arxiv.org/abs/2406.06025
  - CodeScout https://arxiv.org/abs/2603.17829
- **Authors / org, date:** June 2024 (RepoQA) to Aug 2026
- **Status:** All are recent research artifacts. Code/data availability was not verified for SWE-Explore, Agent Retrieval Bench or the SWE-QA study (unverified).

## What it is

These papers stop scoring agents only by final task success (resolved or not). Instead they isolate the **context-acquisition** step: what the agent or retriever surfaced, and whether it was what was needed. This is the closest published methodology to "benchmark search engines as tools inside a coding agent".

## How it works

- **SWE-Explore** ([arXiv 2606.07297](https://arxiv.org/abs/2606.07297)):
  - Task: given (repository, issue), an "explorer" returns a ranked list of code regions under a **fixed line budget**.
  - Scale: 848 issues, 10 languages, 203 repositories.
  - **Ground truth is trajectory-grounded.** Line regions are those actually *read* (view/cat/sed/grep hits) by independent agent trajectories that successfully solved the issue. Instances need two successful trajectories (from GPT-5.4, Gemini-3-Pro, Sonnet-4.6, GLM-5.1, Kimi-K2.6).
  - Metrics cover coverage (file hit, line recall), ranking (nDCG) and context efficiency.
  - Validation: a restricted-context protocol, in which a fixed coding agent sees *only* the explorer's output, is used to show that the metrics track downstream repair.
- **Agent Retrieval Bench** ([arXiv 2607.24882](https://arxiv.org/abs/2607.24882)):
  - A file-level benchmark in which relevance is "defined by what an agent needs next rather than direct query-file semantic similarity".
  - Four positive tasks: code2test, comment2context, trace2code and edit2ripple.
  - A **selective-retrieval** subset has no-gold cases and counterfactual wrong-repository controls, testing abstention.
  - Scale: 427 samples across 25 repositories and 308 frozen base-commit snapshots, with 7.9M chunks.
  - Systems evaluated: lexical retrieval, Aider-style RepoMap, open embeddings, and logged agent context selection.
- **Semantic vs. deep agentic search on SWE-QA** ([arXiv 2608.01507](https://arxiv.org/abs/2608.01507)):
  - Compares (a) an agent retrieving chunks from a pre-built vector index against (b) "Deep Agentic Search", where a planner delegates grep/read exploration to a sub-agent with its own context window, the pattern used by Claude Code-style Explore sub-agents.
  - Setup: 15 Python repositories (12 from SWE-bench, 3 from SWE-bench-Live), 48 questions each (720 per condition), and 4 LLMs.
  - Grading: an LLM judge (Claude Sonnet 4.6), validated against a blind human panel on 800 answers.
- **RepoQA "Searching Needle Function"** ([arXiv 2406.06025](https://arxiv.org/abs/2406.06025)): 500 tasks from 50 repositories in 5 languages. A long-context LLM must find a function from its NL description inside a large code context. This is code search done by the LLM itself, with no retriever.

## Evaluation

- **SWE-Explore:** "agentic explorers form a clear tier above classical retrieval". BM25, TF-IDF and a lightweight static-embedding RAG retriever "remain close to Random on most metrics". General coding agents (Claude Code, Codex, OpenHands, Mini-SWE-Agent, AweAgent) "have closely matched profiles", with high file hit but **low line-level recall**, so "Low F1 is mostly a recall problem" ([§5](https://arxiv.org/abs/2606.07297)). Caveat: the dense baseline was a small static-embedding model, not a strong code embedder.
- **Agent Retrieval Bench:** "No single retrieval family dominates":
  - Qwen3-Embedding-4B has the best MRR, and Qwen3-Embedding-8B the best Recall@20.
  - **RepoMap is best at budgeted context yield at 8K tokens.**
  - Logged agent trajectories "miss every gold file on 27–35 percent of samples".
  - Thresholds calibrated on counterfactual controls do not help on natural no-gold cases.
  - Seeding an agent with retrieved context gives higher file F1 with less exploration than random context ([abstract](https://arxiv.org/abs/2607.24882)).
- **SWE-QA study:** semantic (vector-index) search answered 65.2% correctly versus 46.2% for deep agentic search, at "less than half the cost" per correct answer. 41.8% of deep-agentic failures happened at the planner→sub-agent hand-off and were usually silent ([abstract](https://arxiv.org/abs/2608.01507)). Caveat: this compares against *delegated* agentic search, not a single agent grepping directly.
- **CodeScout:** a bash-only agent trained with RL is competitive on SWE-bench localization ([abstract](https://arxiv.org/abs/2603.17829)). Tool simplicity is not the bottleneck; the policy is.

## Known flaws

1. **Trajectory-derived gold** (SWE-Explore) inherits the tool biases of the agents that produced it. If those agents grep, grep-reachable regions become "relevant", which is a circularity risk.
2. **LLM-judged answer correctness** (SWE-QA study) depends on judge validity. That paper did validate against humans ([§4](https://arxiv.org/abs/2608.01507)).
3. **The conclusions conflict** depending on task (issue repair vs. read-only QA), baseline strength (static embeddings vs. Qwen3-Embedding) and agent design (direct grep vs. delegated sub-agent). No study yet runs a matched comparison of the same agent with {grep only, embeddings only, both} across several task types. This is **a gap lean-explore-bench could fill for Lean**.

## Relevance to lean-explore-bench

- **Offer two evaluation modes:**
  1. *Engine mode:* a ranked list against qrels (standard IR).
  2. *In-agent mode:* a fixed agent (for example Claude Code or a minimal ReAct loop) solves Lean tasks with tool ablations: `grep`/`rg` over Mathlib source only; + `exact?`/`apply?`/Loogle; + a semantic engine (LeanSearch/LeanExplore MCP); + all. Measure task success, tokens, tool calls, and whether the gold declaration was ever surfaced.
- **Budgeted metrics matter:** score by recall within a token budget, not just rank, as SWE-Explore and Agent Retrieval Bench do with "context yield at 8K".
- **Include no-gold queries** (the lemma doesn't exist in Mathlib) to test abstention. Lean engines always return *something*, and agents then hallucinate uses of it.
- **Trajectory-grounded relevance transfers:** from successful agent proofs, the declarations the agent looked up *and used* become graded-relevant items. Watch the circularity noted above.
- **Record whether the gold was surfaced but ignored,** to separate retrieval failure from agent failure (compare the "hand-off" failure class).

## Open questions

- Which agent harness should be fixed for in-agent evaluation, and should we freeze the model version to keep results comparable over time?
- How can grep over Mathlib source be made a fair baseline (for example, include `.lean` sources, not just compiled `.olean` files)?

## Sources

- SWE-Explore: https://arxiv.org/abs/2606.07297
- Agent Retrieval Bench: https://arxiv.org/abs/2607.24882
- Deep Agentic Search empirical study: https://arxiv.org/abs/2608.01507
- RepoQA: https://arxiv.org/abs/2406.06025
- CodeScout: https://arxiv.org/abs/2603.17829
