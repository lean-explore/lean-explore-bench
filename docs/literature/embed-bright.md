# BRIGHT (reasoning-intensive retrieval)

- **Kind:** benchmark / dataset + leaderboard
- **Links:** paper [arXiv:2407.12883](https://arxiv.org/abs/2407.12883); site and leaderboard [brightbenchmark.github.io](https://brightbenchmark.github.io/); code [github.com/xlang-ai/BRIGHT](https://github.com/xlang-ai/BRIGHT); data [hf.co/datasets/xlangai/BRIGHT](https://huggingface.co/datasets/xlangai/BRIGHT); in MTEB as `BrightRetrieval` / `BrightLongRetrieval` ([mteb source](https://github.com/embeddings-benchmark/mteb/blob/main/mteb/tasks/retrieval/eng/bright_retrieval.py))
- **Authors / org, date:** Su, Yen, Xia et al. (HKU, Princeton, Stanford, UW, Google Cloud AI Research), Jul 2024 (ICLR 2025).
- **Status:** Live. Code repo licensed CC-BY-4.0 on GitHub, last push 2025-09-13 (checked via GitHub API, 2026-09-28). The leaderboard is still taking entries dated up to Apr 2026.

## What it is

BRIGHT is a retrieval benchmark in which "the relevance between queries and documents ... requires intensive reasoning to determine" rather than keyword or semantic overlap. The paper calls this "level 3" retrieval. It has 1,384 real-world queries over 12 datasets ([arXiv:2407.12883](https://arxiv.org/abs/2407.12883), §1):

| Group | Datasets | Query source | Corpus | Relevance definition |
|---|---|---|---|---|
| StackExchange (7) | Biology, Earth Sci., Economics, Psychology, Robotics, Stack Overflow, Sustainable Living | post title + body | passages from web pages linked in answers + Google-found topical negatives | cited in an accepted/upvoted answer and unanimously confirmed by annotator + 2 domain PhD reviewers |
| Coding (2) | LeetCode, Pony | problem statement | LeetCode Q&Sol + CodeSearchNet; Pony language manual | same algorithm / required syntax doc |
| Theorem-based (3) | AoPS, TheoremQA-Q, TheoremQA-T | olympiad problem; GPT-4-rephrased TheoremQA question | STEM problem+solution corpus (188,002 docs); ProofWiki theorems (23,839 docs) | document uses the same theorem / problem-solving skill as the query's solution |

Sizes (statistics table): AoPS has 111 queries and 4.7 positives per query on average. TheoremQA-Q has 194 queries and 3.2 positives. TheoremQA-T has 76 queries, 2.0 positives, and a ProofWiki theorem corpus. TheoremQA-T gold labels come from title matching against ProofWiki followed by GPT-4 verification. GPT-4 agreed with human annotators at Cohen's κ = 0.62 (§3.4).

## How it works

- **Metric:** nDCG@10, "following prior work" (BEIR, MS MARCO, TREC) (§4.1). The long-document variant uses **Recall@1**, because with only a few hundred full web pages per task, "nDCG@10 ... becomes more susceptible to randomness" (§5.3).
- **Data layout.** Each query row carries `gold_ids`, `gold_ids_long`, `excluded_ids` and `gold_answer`. Separate configs hold LLM-generated `reasoning` rewrites of each query: `gpt4_reason`, `llama3-70b_reason`, `claude-3-opus_reason`, `Gemini-1.0_reason`, `grit_reason` (HF datasets-server `/info`, checked 2026-09-28). `excluded_ids` removes documents that must not count, such as the query's own source problem in AoPS/LeetCode (purpose inferred from field name and paper; unverified in detail).
- **Harness:** `python run.py --task {task} --model {model}`, with per-model instruction configs, `--query_max_length` / `--doc_max_length`, and cached document embeddings. A custom model must return `{query_id: {doc_id: score}}` ([GitHub README](https://github.com/xlang-ai/BRIGHT)).
- **Reranking protocol:**
  - Rerank the top k ∈ {10, 100} from BM25 or from Google's embedder, using either an MS-MARCO cross-encoder (MiniLM) or listwise LLM reranking in the RankGPT style (§5.1).

## Evaluation

The numbers below are from the original paper (v4, 2025-03), main results table, nDCG@10. They show how *math* subsets behave compared with the rest:

| Model | Avg (12) | AoPS | TheoQ | TheoT | LeetCode |
|---|---|---|---|---|---|
| BM25 | 14.5 | 6.2 | 10.4 | 4.9 | 24.4 |
| BGE-large (335M) | 13.7 | 6.0 | 13.0 | 6.9 | 26.7 |
| E5-Mistral (7.1B) | 17.9 | 7.1 | 26.1 | 26.8 | 28.7 |
| gte-Qwen1.5 (7.7B) | 22.5 | 14.4 | 27.8 | 32.9 | 25.5 |
| OpenAI text-embedding-3-large | 17.9 | 8.5 | 23.5 | 11.7 | 23.6 |

Headline results from the paper:
- SFR-Embedding-Mistral scored 59.0 nDCG@10 on the MTEB retrieval subset (MTEB leaderboard, 2024-05-28) but only 18.3 on BRIGHT (abstract). **MTEB retrieval rank does not transfer to reasoning-heavy retrieval.**
- Using LLM reasoning traces as the query raises scores by "up to 12.2 points". "Surprisingly, BM25 achieves the best performance ... using reasoning steps written by GPT-4 as new queries" (§4.2 and its reasoning-query figure).
- Reranking the top 10 or 100 with an MS-MARCO cross-encoder *hurts*: from Google's retriever, 19.5 drops to 16.0 at k=10 and to 9.4 at k=100. GPT-4 listwise reranking helps: 19.5 rises to 22.6 at k=100. So "training rerankers on MS MARCO does not transfer well to BRIGHT" (§5.1 and its reranking table).
- Contamination probe: continued pretraining of GritLM on the StackExchange corpus (without query–document pairs) left the average unchanged (20.5 vs 20.4) (§5.2).

**Leaderboard caveats.** As of 2026-09-28 the short-document leaderboard top is Mira-Reasoning-Retrieval at 66.9 (2026-04-22), then INF-X-Retriever at 63.4 (2025-12-20) ([brightbenchmark.github.io](https://brightbenchmark.github.io/)). Entries are:
- **self-reported by email**;
- a mix of single embedders, agentic retrieval pipelines, query rewriting with frontier LLMs, and LLM rerankers, all ranked on one list;
- accompanied only by optional method descriptions ("whether LLMs like GPT-4 or reranking are used, etc.").

Scores are therefore not comparable across system classes without reading each entry.

## Relevance to lean-explore-bench

- **The closest analogue to Lean search.** BRIGHT's theorem subsets have the same structure as "find the Mathlib lemma I need for this goal": a query stated in applied or informal terms, and a corpus of theorem statements with little lexical overlap. TheoremQA-T (question to ProofWiki theorem) is nearly a natural-language-to-Mathlib task, just on an informal corpus.
- **Design choices to copy:**
  1. Define relevance operationally, e.g. "is used in the proof" or "is the lemma that closes the goal", instead of topical similarity.
  2. Validate LLM-assisted labels with a κ against humans.
  3. Keep `excluded_ids`-style masks. For Lean: exclude the declaration the query was derived from, plus its auto-generated aliases.
  4. Report query-rewriting variants as separate tracks.
- **Mistake to avoid:** a single leaderboard that mixes "embedder only", "engine + LLM rewriting" and "agentic" systems. We should report tracks by system class and require a cost/latency disclosure.
- **Reranker transfer is a real risk.** Rerankers trained on general-domain data can reduce nDCG on reasoning and math retrieval. MIRB found the same thing ([embed-mirb.md](embed-mirb.md)). Our benchmark should always report "retriever alone" next to "retriever + reranker".

## Open questions

- How much of BRIGHT's theorem difficulty comes from the query rephrasing (GPT-4 applied scenarios) versus the corpus? Should lean-explore-bench include deliberately "applied" rephrasings as a separate query category?

## Sources

- BRIGHT paper v4: https://arxiv.org/abs/2407.12883 (tables and sections read from the arXiv LaTeX source)
- Leaderboard: https://brightbenchmark.github.io/ (fetched 2026-09-28)
- Code: https://github.com/xlang-ai/BRIGHT
- Dataset schema: https://datasets-server.huggingface.co/info?dataset=xlangai/BRIGHT (queried 2026-09-28)
- MTEB integration: https://github.com/embeddings-benchmark/mteb/blob/main/mteb/tasks/retrieval/eng/bright_retrieval.py
