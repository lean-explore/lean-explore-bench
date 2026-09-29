# Embeddings vs. agentic grep in production coding tools: what vendors report and how they evaluated it

- **Kind:** paper / tool cluster (industry evidence)
- **Links:**
  - Cursor https://cursor.com/blog/semsearch
  - Claude Code tools reference https://code.claude.com/docs/en/tools-reference.md
  - Boris Cherny post https://x.com/bcherny/status/2017824286489383315
  - Sourcegraph https://sourcegraph.com/blog/how-cody-understands-your-codebase ; https://sourcegraph.com/blog/anatomy-of-a-coding-assistant ; https://sourcegraph.com/blog/lessons-from-building-ai-coding-assistants-context-retrieval-and-evaluation ; https://arxiv.org/abs/2408.05344
  - GitHub Copilot https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/
  - Aider https://aider.chat/docs/repomap.html
- **Authors / org, date:** Feb 2024 to Nov 2025 (see per-item dates)
- **Status:** Vendor claims. **None release their evaluation sets**, so all numbers below are unreproducible.

## What it is

This note collects the published positions of coding-tool vendors on "does embedding (semantic) search help, or is grep plus an agent loop enough?", together with the evaluation evidence each gives. The academic side is in [code-agent-retrieval-evals.md](code-agent-retrieval-evals.md).

## How it works (per system)

- **Claude Code (Anthropic): no index, agentic search.**
  - The tools reference lists `Grep` (built on ripgrep), `Glob`, `Read`, `LSP` ("jump to definitions, find references, report type errors") and `Agent` (sub-agents, including an `Explore` type).
  - On macOS, Linux and WSL, Glob and Grep are left out of the default tool set, and "Claude searches with `find` and `grep` through the Bash tool instead", which run embedded `bfs` and `ugrep` ([tools reference](https://code.claude.com/docs/en/tools-reference.md)).
  - Boris Cherny (Claude Code lead) wrote that "Early versions of Claude Code used RAG + a local vector db, but we found pretty quickly that agentic search generally works better. It is also simpler and doesn't have the same issues around security, privacy, staleness, and reliability" ([X post](https://x.com/bcherny/status/2017824286489383315); quote taken from the search-result snippet; the page itself was not fetched, so the wording is unverified).
  - **No quantitative evaluation has been published.**
- **Cursor: grep plus a custom embedding model.** Blog post of Nov 6, 2025 ([cursor.com/blog/semsearch](https://cursor.com/blog/semsearch)):
  - *Offline:* on the internal "Cursor Context Bench" (codebase questions with known answers), adding semantic search gives on average 12.5% higher accuracy (6.5%–23.5% depending on the model), across frontier models and Cursor's Composer.
  - *Online A/B:* code retention +0.3% overall and +2.6% on codebases with 1,000+ files. Dissatisfied follow-up requests rise 2.2% when semantic search is unavailable.
  - *Training:* the embedding model is trained from agent session traces. An LLM ranks which content would have helped at each step, and embeddings are trained to match those rankings.
  - *Conclusion:* "Our agent makes heavy use of grep as well as semantic search, and the combination of these two leads to the best outcomes."
- **Sourcegraph Cody: embeddings → keyword → hybrid.**
  - *Feb 2024:* removed embeddings from Cody Enterprise and replaced them with Sourcegraph search using "an adapted form of the BM25 ranking function alongside other signals". Reasons given: sending code to a third-party embedding API, admin complexity of keeping embeddings fresh, and difficulty scaling vector search to more than 100k repositories. **No quality numbers were given** ([blog](https://sourcegraph.com/blog/how-cody-understands-your-codebase)).
  - *June 2024:* chat defaults to "a mix of both" keyword and embeddings, while autocomplete uses no embeddings, for speed. Evaluation used ~90 queries against open-source repositories plus internal leaderboards ([anatomy blog](https://sourcegraph.com/blog/anatomy-of-a-coding-assistant)).
  - *Feb 2025:* four retrievers (Zoekt keyword, embeddings, code graph, local editor/git context), followed by a transformer ranker that solves a token-budget knapsack. Stated evaluation problems: "the lack of ground truth data for relevant context", and online signals that reflect the LLM response rather than context quality ([lessons blog](https://sourcegraph.com/blog/lessons-from-building-ai-coding-assistants-context-retrieval-and-evaluation); RecSys'24 paper [arXiv 2408.05344](https://arxiv.org/abs/2408.05344)).
- **GitHub Copilot: new code embedding model (Sept 24, 2025).**
  - *Offline:* "+37.6% relative lift (average score improved from 0.362 to 0.498) on our multi-benchmark evaluation", covering NL→code, code→NL, code→code, and problem-description→fix.
  - *Online:* code acceptance ratio up 110.7% for C# and 113.1% for Java in VS Code.
  - *Training:* hard negatives mined from public and internal repositories with LLM help. The benchmarks are unnamed ([GitHub blog](https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/)).
- **Aider: repo map instead of retrieval.** Aider sends a compact map of "the most important classes and functions along with their types and call signatures", selected by graph ranking over a file-dependency graph, within a token budget (default `--map-tokens` 1,000) that adjusts dynamically ([Aider docs](https://aider.chat/docs/repomap.html)). Agent Retrieval Bench found RepoMap best on budgeted context yield at 8K tokens ([arXiv 2607.24882](https://arxiv.org/abs/2607.24882)).

## Evaluation (synthesis)

- **Vendors who kept embeddings** (Cursor, GitHub, Sourcegraph in 2025) all use them *alongside* lexical search and report gains mostly on large codebases.
- **The vendor who dropped embeddings** (Anthropic for Claude Code) cites operational factors (staleness, privacy, reliability) as much as quality. Sourcegraph's 2024 removal was likewise operational.
- **The academic evidence is split:**
  - SWE-Explore: agents ≫ BM25 and static embeddings ([2606.07297](https://arxiv.org/abs/2606.07297)).
  - SWE-QA study: vector search > delegated agentic search, 65.2% vs 46.2% ([2608.01507](https://arxiv.org/abs/2608.01507)).
  - Agent Retrieval Bench: no family dominates ([2607.24882](https://arxiv.org/abs/2607.24882)).
  - SweRank: a strong single-shot retriever ≥ an agent on SWE-bench-Lite function localization ([2505.07849](https://arxiv.org/abs/2505.07849)).

## Known flaws

1. **Evaluation sets are private** (Cursor Context Bench, GitHub's multi-benchmark, Sourcegraph internal sets), so claims cannot be reproduced.
2. **Outcome metrics are confounded.** Code retention and acceptance ratios mix retrieval with model and UI effects.
3. **Survivorship and marketing bias:** a vendor announcing a new model reports improvement.
4. **"Agentic search" is ill-defined.** Direct grep by the main agent, delegated sub-agent exploration and LSP navigation are different designs, and results differ between them ([2608.01507](https://arxiv.org/abs/2608.01507)).

## Relevance to lean-explore-bench

- The field lacks **a public, matched ablation**: the same agent and task with grep-only, semantic-only, and both. A Lean benchmark can supply one cheaply, because Lean's goal checker gives an objective success signal. That signal is unavailable for code QA and only partially available for SWE-bench.
- **Include Lean's equivalents of each tool family as baselines:**
  - grep/ripgrep over Mathlib source (lexical)
  - Loogle (structural/type pattern)
  - `exact?`/`apply?`/`rw?` (the type-directed "LSP" analogue)
  - LeanSearch/LeanExplore/Moogle (semantic)
  - a RepoMap-like module outline
- **Operational factors deserve reporting columns:** index staleness relative to Mathlib HEAD, latency, whether code leaves the machine, and cost per query. These, not only accuracy, drove the Claude Code and Sourcegraph decisions.

## Open questions

- Can we get Cursor-style "agent session trace" relevance signals from Lean users (for example, which search results were subsequently used in a proof)?

## Sources

- Cursor semantic search blog (Nov 6, 2025): https://cursor.com/blog/semsearch
- Claude Code tools reference: https://code.claude.com/docs/en/tools-reference.md
- Boris Cherny on X (quote unverified): https://x.com/bcherny/status/2017824286489383315
- Sourcegraph, How Cody understands your codebase (Feb 15, 2024): https://sourcegraph.com/blog/how-cody-understands-your-codebase
- Sourcegraph, Anatomy of a coding assistant (June 18, 2024): https://sourcegraph.com/blog/anatomy-of-a-coding-assistant
- Sourcegraph, Lessons from building AI coding assistants (Feb 20, 2025): https://sourcegraph.com/blog/lessons-from-building-ai-coding-assistants-context-retrieval-and-evaluation
- Hartman et al., RecSys'24: https://arxiv.org/abs/2408.05344
- GitHub Copilot embedding model (Sept 24, 2025): https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/
- Aider repo map: https://aider.chat/docs/repomap.html
- Agent Retrieval Bench: https://arxiv.org/abs/2607.24882
- SWE-Explore: https://arxiv.org/abs/2606.07297
- SWE-QA semantic vs deep agentic: https://arxiv.org/abs/2608.01507
- SweRank: https://arxiv.org/abs/2505.07849
