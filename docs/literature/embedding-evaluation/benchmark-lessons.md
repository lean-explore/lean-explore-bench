# Embedding / reranker benchmarks: lessons for lean-explore-bench

- **Kind:** synthesis (cross-cutting notes over [mteb.md](mteb.md), [beir.md](beir.md), [bright.md](bright.md), [../code-search/coir.md](../code-search/coir.md), [../lean-benchmarks/mirb.md](../lean-benchmarks/mirb.md))
- **Date:** 2026-09-28
- **Status:** working notes; the recommendations are ours, and every factual claim links to its source.

## What it is

This note compares how the embedding and reranking community builds retrieval benchmarks. It then draws out what lean-explore-bench should copy and what it should avoid. It deliberately leaves out model rankings. The last section explains how LeanExplore's current models would plug into such a benchmark.

## How the benchmarks are built (comparison)

| | BEIR | MTEB / MMTEB | BRIGHT | CoIR | MIRB |
|---|---|---|---|---|---|
| Queries from | existing IR/QA datasets | existing datasets (+ some LLM-generated) | real StackExchange posts, LeetCode, olympiad problems, GPT-4-rephrased TheoremQA | existing code datasets + 2 new | existing math/formal datasets + LeanSearch eval set |
| Relevance labels | inherited; mostly binary, some graded; pooled judging | inherited | human (unanimous, PhD-reviewed) or "shares the same theorem/skill"; GPT-4 verification with κ = 0.62 vs humans on TheoremQA-T | inherited; exactly one gold per query | inherited; binary or 3–4 level |
| Corpus | full original corpora (up to millions) | pooled top-250 from 3 systems per query, ≤1,000 queries, ≤250k docs | per-task corpora, 7.9k–414k docs | 816 to 1M | 2k–1.35M |
| Headline metric | nDCG@10 (+ capped R@100) | nDCG@10 for retrieval; Borda rank across tasks | nDCG@10; Recall@1 for long docs | nDCG@10 | nDCG@10 |
| Splits / leakage control | MS MARCO excluded from zero-shot avg | zero-shot score; eng v2 drops MS MARCO/NQ; RTEB private sets | `excluded_ids`; contamination probe | train/dev/test released | LeanDojo `novel_premises` split |
| Reporting | paper, then official leaderboard | PR-reviewed central results repo, pinned versions | self-reported by email | paper + package | paper |

Sources are in the per-benchmark notes. The key citations: BEIR [arXiv:2104.08663](https://arxiv.org/abs/2104.08663); MMTEB [arXiv:2502.13595](https://arxiv.org/abs/2502.13595); Maintaining MTEB [arXiv:2506.21182](https://arxiv.org/abs/2506.21182); BRIGHT [arXiv:2407.12883](https://arxiv.org/abs/2407.12883); CoIR [arXiv:2407.02883](https://arxiv.org/abs/2407.02883); MIRB [arXiv:2505.15585](https://arxiv.org/abs/2505.15585).

## Lessons (each with its evidence)

1. **nDCG@10 is the common currency. Pair it with a recall metric at the reranker's input depth.** BEIR's argument: precision and recall ignore rank order, and MRR and MAP cannot use graded labels ([BEIR](https://arxiv.org/abs/2104.08663)). For a retrieve-then-rerank engine, first-stage recall at the rerank depth caps what the reranker can achieve.
2. **Pooled judgments penalize systems outside the pool.** On TREC-COVID, dense systems had Hole@10 up to 31.8%, against 6.4% for BM25. After the holes were judged, ANCE gained 8 nDCG points ([BEIR](https://arxiv.org/abs/2104.08663)). Report Hole@k for every engine, and judge the holes before publishing.
3. **Training on the benchmark's distribution inflates leaderboard rank.** "The highest ranking models achieve their scores by training on benchmark tasks" ([Maintaining MTEB](https://arxiv.org/abs/2506.21182)). CodeSearchNet scores run well above CoIR scores for most models ([CoIR §5.5](https://arxiv.org/abs/2407.02883)). The remedies are to disclose training data, compute a zero-shot score, and keep private or fresh held-out queries ([RTEB](https://huggingface.co/blog/rteb)).
4. **Private test sets need neutral custody.** RTEB's private column was pulled on 2026-01-14 because one vendor had co-developed the private data ([mteb#3934](https://github.com/embeddings-benchmark/mteb/issues/3934)).
5. **General leaderboards do not predict domain performance.**
   - SFR-Embedding-Mistral: 59.0 on MTEB retrieval, but 18.3 on BRIGHT ([BRIGHT](https://arxiv.org/abs/2407.12883)).
   - GTE-Base: 2nd on BEIR, 6th on CoIR ([CoIR](https://arxiv.org/abs/2407.02883)).
   - "MTEB [does] not reliably predict mathematical performance" ([SABER-Math](https://arxiv.org/abs/2606.29894)).

   A Lean-specific benchmark is justified. We should not choose models by MTEB rank.
6. **General-domain rerankers can *hurt* in math and reasoning domains.** On BRIGHT, an MS-MARCO cross-encoder dropped nDCG@10 from 19.5 to 9.4 when reranking the top 100 ([BRIGHT §5.1](https://arxiv.org/abs/2407.12883)). On MIRB, bge-reranker-v2-m3 lowered averages by about 5–6 points ([MIRB](https://arxiv.org/abs/2505.15585)). Every pipeline stage should be evaluated with ablations.
7. **Scores depend on prompt and prefix details.** Query and passage prefixes, per-task instructions, normalization and custom encode arguments all change results. MTEB could only reproduce BGE's reported numbers after adding prefix support ([Maintaining MTEB §5.2](https://arxiv.org/abs/2506.21182)). The benchmark must record instructions and truncation lengths as part of each system's configuration.
8. **Keep system classes apart on the leaderboard.** BRIGHT's single self-reported list mixes embedders, LLM query rewriting, and agentic pipelines ([BRIGHT leaderboard](https://brightbenchmark.github.io/)). We should use tracks, for example "offline/on-device", "engine + API LLM" and "agentic", and require cost/latency disclosure. CoIR's efficiency section is a template for the latter ([CoIR §5.2](https://arxiv.org/abs/2407.02883)).
9. **Report statistical uncertainty.** MTEB-BR adds per-task bootstrap CIs and paired-bootstrap tests, and finds the top six models "statistically too close to order" ([arXiv:2607.04581](https://arxiv.org/abs/2607.04581)). Lean query sets will be small; LeanSearch's informal set has 40 queries in MIRB. CIs are mandatory.
10. **Cheap evaluation that preserves the ranking is possible, but validate it.** MMTEB validated both hard-negative downsampling (≥100 negatives per query kept the ranking; they used 250) and correlation-based task pruning with Spearman ρ against the full benchmark ([MMTEB](https://arxiv.org/abs/2502.13595)). A Mathlib corpus is small enough to search exhaustively, so we only need this for expensive LLM rerankers.
11. **Define relevance operationally.** BRIGHT's theorem subsets define relevance as "the document uses the same theorem as the query's solution", and LeanDojo uses "premise used in the next tactic" ([BRIGHT](https://arxiv.org/abs/2407.12883), [MIRB](https://arxiv.org/abs/2505.15585)). Both are checkable, unlike "topically similar". Their weakness is false negatives: other premises may also work ([MIRB Limitations](https://arxiv.org/abs/2505.15585)). That is why graded labels plus hole judging are needed.
12. **Plan for harness reuse.** MTEB v2's `SearchProtocol` (`index` + `search`, optional `top_ranked`) can evaluate full non-embedding systems. Its `top_ranked` field turns any retrieval task into a reranking task ([MTEB v2 post](https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md)). If we publish in the BEIR/MTEB schema, the whole ecosystem can run our benchmark.

## How LeanExplore's current models plug in

The facts below are from local source at commit `17b9d6c` of [lean-explore](https://github.com/lean-explore/lean-explore) and from the Hugging Face model cards.

**Pipeline.** LeanExplore's first stage fuses two ranked lists with reciprocal rank fusion ([ranking.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/ranking.py)):
- BM25 over declaration names.
- FAISS IVF (`nprobe=64`) over **Qwen/Qwen3-Embedding-0.6B** embeddings of each declaration's LLM *informalization*. Queries are encoded with sentence-transformers `prompt_name="query"`, and documents with no prompt ([engine.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/engine.py), [embedding_client.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/util/embedding_client.py)).

The top 25 candidates are then scored by **Qwen/Qwen3-Reranker-0.6B** on the text `"{name}: {informalization}"`. Inputs are truncated to 256 tokens and the instruction is "Find relevant Lean 4 math declarations". The reranker score is then combined with informal-BM25, fuzzy-name and dependency-count signals (weights 1.0 / 0.4 / 1.0 / 0.2) ([reranker_client.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/util/reranker_client.py), [ranking.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/ranking.py)).

**Model facts from the cards.** Both models are 0.6B parameters, Apache-2.0, 32K context. The embedder outputs up to 1,024 dimensions, supports Matryoshka truncation, and is instruction-aware. Scores the Qwen team reports:
- Qwen3-Embedding-0.6B: MTEB(eng, v2) retrieval 61.83; MMTEB retrieval 64.64. Competitor scores in that table were taken from the MTEB leaderboard on 2025-05-24 ([card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)).
- Qwen3-Reranker-0.6B: MTEB-R 65.80, reranking the top 100 from Qwen3-Embedding-0.6B, whose own MTEB-R is 61.82 ([card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)).

These are the model authors' own runs on general benchmarks. Lessons 3 and 5 say not to expect them to transfer to Lean.

**Plugging in.** Wrap the whole engine as one MTEB `SearchProtocol` system. Also expose each stage separately:
- (a) BM25-name only
- (b) dense-informalization only
- (c) RRF-fused, before reranking
- (d) + reranker
- (e) + post-rerank signals

Swapping in other embedders and rerankers then becomes a config change. Report Recall@25 for stages (a)–(c), because 25 is the reranker's input depth, and nDCG@10 and MRR@10 for all stages.

**Configuration issues the benchmark should test.** These come from reading the code and have not been measured:
- *Generic query instruction.* The embedder's sentence-transformers `"query"` prompt is the model default, "Given a web search query, retrieve relevant passages that answer the query" ([config_sentence_transformers.json](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/main/config_sentence_transformers.json)). It is not a Lean-specific instruction, although the card recommends task-specific instructions, which it says typically give "1% to 5%" improvement.
- *Reranker prompt differs from the card.* The reranker's input construction differs from the official usage on the model card ([card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)):
  - The card wraps each pair in a system/chat template: `<|im_start|>system\nJudge whether the Document meets the requirements ... "yes" or "no".<|im_end|>` ... `<|im_start|>assistant\n<think>\n\n</think>\n\n`.
  - The card scores with the logits of the tokens `"yes"` / `"no"`.
  - `RerankerClient._format_pair` sends only `<Instruct>: ...\n<Query>: ...\n<Document>: ...`, with no prefix or suffix, and reads the logits of `"true"` / `"false"`.

  The effect on quality is **unverified**. Combined with lesson 6, this makes stage (c) vs (d), and official vs current prompt formatting, the first ablation to run.
- *Truncation and approximate search.* The 256-token reranker cap and the IVF approximate index are further variables to record, as in lesson 7.

## Open questions

- Which relevance-label source should we use for Lean queries? Options: (i) human-curated (costly, small), (ii) automatically derived (premise-used, docstring-to-declaration; risk of false negatives), (iii) LLM-judged over pooled candidates (needs a κ audit, as BRIGHT did).
- Should the informalizations that LeanExplore embeds count as "training data" for the zero-shot disclosure, if our queries are also LLM-written?

## Sources

- BEIR: https://arxiv.org/abs/2104.08663
- MMTEB: https://arxiv.org/abs/2502.13595
- Maintaining MTEB: https://arxiv.org/abs/2506.21182
- MTEB v2 release post: https://github.com/embeddings-benchmark/mteb/blob/main/docs/blog/posts/mteb-v2.md
- RTEB: https://huggingface.co/blog/rteb ; private column removal: https://github.com/embeddings-benchmark/mteb/issues/3934
- BRIGHT: https://arxiv.org/abs/2407.12883 ; leaderboard: https://brightbenchmark.github.io/
- CoIR: https://arxiv.org/abs/2407.02883
- MIRB: https://arxiv.org/abs/2505.15585
- SABER-Math: https://arxiv.org/abs/2606.29894
- MTEB-BR: https://arxiv.org/abs/2607.04581
- Qwen3-Embedding-0.6B card: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B (raw README and config_sentence_transformers.json fetched 2026-09-28)
- Qwen3-Reranker-0.6B card: https://huggingface.co/Qwen/Qwen3-Reranker-0.6B (raw README fetched 2026-09-28)
- Qwen3 Embedding paper: https://arxiv.org/abs/2506.05176
- LeanExplore source (local clone, commit 17b9d6c): `src/lean_explore/search/{engine,ranking,indexes}.py`, `src/lean_explore/util/{embedding_client,reranker_client}.py`
