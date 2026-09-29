# Towards Lightweight and LLM-Free Semantic Search for mathlib4 (Isaac Li)

- **Kind:** search engine (research prototype) and paper
- **Links:** AITP 2025 abstract https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf ; code/demo https://github.com/IsaacLi74/Lightweight-and-LLM-Free-Semantic-Search-for-mathlib4 ; adapter https://huggingface.co/Isaac74/qwen3-0.6b-lightweight-semantic-mathlib-search-adapter
- **Authors / org, date:** Isaac (Rucheng) Li, University of Pittsburgh. AITP 2025.
- **Status:** Open source (Apache-2.0 according to the [repo](https://github.com/IsaacLi74/Lightweight-and-LLM-Free-Semantic-Search-for-mathlib4)). Distributed as a Colab notebook plus an HF adapter and FAISS index. There is no hosted service (unverified beyond the README).

## What it is

This is a laptop-scale (CPU) dense retriever over about 179k Mathlib theorems (Lean 4.20.1) that makes no LLM call at query time. It targets formula-style queries and the variable-naming bias of other engines ([abstract](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)).

## How it works (brief)

DeepSeek-Chat writes three queries per theorem (natural-language, formula and mixed) with variables masked. Qwen3-Embedding-0.6B gets a LoRA adapter trained with MNRL on query–query pairs, using clustered hard batches. The search anchors are those queries plus harvested "vague" queries, indexed in FAISS HNSW. At query time, symbols are normalized, the query is embedded, the top 50 are retrieved and results are deduplicated by theorem ([abstract §2](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf)). The corpus is theorems only.

## Evaluation ([abstract §3](https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf))

- **Queries:** 2,400 queries from 300 "commonly used and important" theorems chosen so that every engine's snapshot contains them (LeanSearch at Lean 4.16.0, LeanExplore at 4.19.0, this model at 4.20.1). The queries were regenerated independently by DeepSeek-Chat. They fall into four groups (detailed natural-language, detailed formula, short natural-language, short formula) with two paraphrase variants each; formula paraphrases mainly rename variables.
- **Metric:** Top-10 hit rate. Dropping the namespace counts as correct.
- **Overall:** this model 92.58%, LeanSearch 72.71%, LeanExplore 59.00%.
- **Short formula with renamed variables (variant 1):** 84.67% / 55.33% / 26.00% in the same order. This shows large drops in variable-renaming robustness for both LeanSearch (v1-era) and LeanExplore (v0.x).
- **Caveats:** The same LLM family generated both training anchors and test queries, so the setup favours the author's model. Only theorems are covered, and the evaluation was done by the author.
- **Release:** The README mentions example queries and zipped test results. Whether the full 2,400-query set is released is unverified.

## Programmatic access

Local only, through the notebook and HF assets (about 7.2 GB RAM, about 0.5 s per query on CPU, per the [README](https://github.com/IsaacLi74/Lightweight-and-LLM-Free-Semantic-Search-for-mathlib4)). There is no API or MCP.

## Relevance to lean-explore-bench

- Its **variable-renaming paraphrase slice** is a simple, high-signal robustness test (`a + -b = a - b` vs `m + -i = m - i`) that we should adopt.
- It is a strong, cheap baseline for "is fine-tuning a small embedder enough?"

## Open questions

- Is the 2,400-query evaluation set publicly available?
- How does it do on MathlibQR?

## Sources

- AITP 2025 abstract: https://aitp-conference.org/2025/abstract/AITP_2025_paper_12.pdf
- Repo: https://github.com/IsaacLi74/Lightweight-and-LLM-Free-Semantic-Search-for-mathlib4
- HF adapter: https://huggingface.co/Isaac74/qwen3-0.6b-lightweight-semantic-mathlib-search-adapter
