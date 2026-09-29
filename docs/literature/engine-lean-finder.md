# Lean Finder

- **Kind:** search engine (plus test sets)
- **Links:** web https://leanfinder.github.io ; HF Space https://huggingface.co/spaces/delta-lab-ai/Lean-Finder ; model https://huggingface.co/delta-lab-ai/lean-finder (and `lean-finder-v2-preview`) ; code https://github.com/delta-lab-ai/lean-finder ; paper [arXiv:2510.15940](https://arxiv.org/abs/2510.15940) (ICLR 2026, according to the [model card](https://huggingface.co/delta-lab-ai/lean-finder))
- **Authors / org, date:** Jialin Lu, Kye Emond, Kaiyu Yang, Swarat Chaudhuri, Weiran Sun, Wuyang Chen (DeLTA Lab, SFU, and collaborators). Paper posted October 2025 and revised February 2026 ([arXiv](https://arxiv.org/abs/2510.15940)).
- **Status:** Live. The web page, HF Space and the HF inference endpoint used by lean-lsp-mcp all responded on 2026-09-28 (checked by us). Code and model are Apache-2.0 ([repo](https://github.com/delta-lab-ai/lean-finder)). The deployed model has been updated since the paper: the `main` revision is "significantly stronger", the paper model sits at the `old-model` revision, and "full evaluation details for the updated model will be released soon" ([repo README](https://github.com/delta-lab-ai/lean-finder)). A `lean-finder-v2-preview` model was last modified 2026-09-03 ([HF API](https://huggingface.co/api/models/delta-lab-ai/lean-finder-v2-preview)).

## What it is

Lean Finder is a dense retriever fine-tuned to match how real users ask questions rather than informalizations of Mathlib statements. It covers four input kinds: synthetic user questions, informalized statements, proof states with a note on where the proof should go, and noisy formal statements ([paper §3](https://arxiv.org/abs/2510.15940)).

## How it works (brief)

The base model is DeepSeek-Prover-V1.5-RL 7B. It is trained with a contrastive loss on about 1.4M query–code pairs. The synthetic user queries are generated from clusters of intents mined from Zulip and GitHub questions. The model is then aligned with DPO on 1,154 preference triplets, which come from user votes and "Arena" comparisons against LeanSearch in the web UI, plus GPT-4o judgments ([paper §3 "Preference Alignment"](https://arxiv.org/abs/2510.15940); [model card](https://huggingface.co/delta-lab-ai/lean-finder)). The corpus includes Mathlib plus SciLean, some research repositories and their dependencies ([paper, "Data Source Details" appendix](https://arxiv.org/abs/2510.15940)). Results carry the formal statement plus an informal name and description.

## Evaluation ([arXiv:2510.15940 §4 and "Evaluation Settings" / "Additional Experiments" appendices](https://arxiv.org/abs/2510.15940))

- **Test sets:**
  - 1,000 informalized statements, re-informalized from LeanSearch database entries with a simplified prompt
  - 1,000 synthetic user queries
  - 1,000 formal statements with 20% of tokens randomly replaced ("augmented statement")
  - 2,224 proof states, both raw and augmented
- **Fairness filter:** Every gold statement must exist in LeanSearch's database, and the query must not appear in LeanSearch's database or in Lean Finder's training data.
- **Relevance and metrics:** One gold statement per query, and a hit requires an exact match on the full Lean code. Metrics are R@1/5/10 and MRR. GPT-4o with web search is a baseline scored by full-name and by stem match.
- **Main results, R@1 / R@10 / MRR (main modality table):**
  - Informalized statements: Lean Finder 64.2 / 93.3 / 0.75 vs LeanSearch 49.2 / 82.5 / 0.61
  - Synthetic user queries: Lean Finder 54.4 / 91.4 / 0.68 vs LeanSearch 47.1 / 83.7 / 0.60
  - Noisy formal statements: Lean Finder 82.7 / 97.7 / 0.89 vs LeanSearch 59.2 / 85.5 / 0.69
  - GPT-4o with full-name match reached only 14.8 / 22.6 R@1 / R@10 on informalized statements.
- **Proof states, R@1 / R@10 / MRR (proof-state table):**
  - Augmented: Lean Finder 24.6 / 67.9 / 0.40 vs LeanStateSearch 4.99 / 39.6 / 0.16 vs REAL-Prover search 8.0 / 39.2 / 0.18
  - Raw: Lean Finder 8.3 / 40.0 / 0.19
- **Extra baselines ("Additional Experiments" appendix):**
  - LeanSearch with its own augmentation turned on did *worse* at R@1: 31.9 on informalized statements.
  - Qwen3-Embedding-8B zero-shot scored 57.7 / 89.2 / 0.69 on informalized statements, fairly close to Lean Finder.
  - LeanExplore (v0.x): see [engine-leanexplore.md](engine-leanexplore.md).
- **User study:** 5 participants judged 128 queries taken from GitHub, looking at the top 3 results from each system. Top-3 rate / normalized Borda: Lean Finder 81.6% / 0.67, LeanSearch 56.9% / 0.41, GPT-4o 54.1% / 0.40 (user-study table).
- **Downstream:** Used as RAG for provers on MiniF2F, ProofNet, PutnamBench and FATE-M, it made results "mostly consistent with the non-integrated setting, with modest improvements" (§4, "Compatible with LLM Provers").
- **Third-party:** On MathlibQR fair (LeanSearch v2 paper), LeanFinder scored nDCG@10 0.533, R@10 0.698, R@100 0.875 (best of all systems at R@100), and LLM-judge rank 2.87 ([arXiv:2605.13137 Table 1](https://arxiv.org/abs/2605.13137)).
- **Data release:** The five test files (`informalized_statement`, `synthetic_user_query`, `augmented_statement`, `augmented_proof_state` and `raw_proof_state` `.jsonl`) and `eval.py` are in `lean-finder-original/` ([repo tree](https://github.com/delta-lab-ai/lean-finder)). Real Zulip queries are *not* released, for privacy ([paper, "Privacy and Data Release" appendix](https://arxiv.org/abs/2510.15940)).
- **Caveats for us:** Three of the four test sets are LLM-generated from the gold statement, so they are close to the training distribution. The "fair" filter is defined relative to LeanSearch's database. The numbers describe the paper model, not the model deployed now.

## Programmatic access (for a harness)

- **Hosted:** lean-lsp-mcp calls an HF Inference Endpoint (`POST {"inputs": query, "top_k": k}`, default URL in [config.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/config.py), overridable with `LEAN_FINDER_URL`). It keeps only results whose URL points to mathlib4_docs and throttles itself to 10 requests per 30 s ([search.py](https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py)). The LeanSearch v2 authors used the HF Space's gradio `/retrieve` endpoint instead ([arXiv:2605.13137, "Prove: per-system input handling" appendix](https://arxiv.org/abs/2605.13137)). Neither endpoint documents a rate limit. The README advises self-hosting for heavy workloads.
- **Self-hosted (recommended for benchmarks):** `server.py` needs one GPU with at least 16 GB. It exposes `POST /search {"inputs", "top_k", "version"}`, `GET /versions` and `GET /health`, and ships prebuilt FAISS indices for **Mathlib v4.19.0, v4.24.0 and v4.28.0**, which can be pinned per request ([README](https://github.com/delta-lab-ai/lean-finder)). This is the only engine that lets a harness pick the Mathlib snapshot per query.
- **MCP:** No first-party MCP server. It is reachable through lean-lsp-mcp `lean_leanfinder`.

## Relevance to lean-explore-bench

- Its intent-based query taxonomy (clusters of real user questions) and the "question" query style (for example, "Does y being a root of minpoly(x) imply…?") are underrepresented in MathlibQR.
- Its released test sets can be reused, but they are synthetic. They are best used as a "paraphrase robustness" slice, not as a headline number.
- Letting the harness pin a snapshot (v4.28.0) makes it easy to line Lean Finder up with LeanSearch v2 (v4.28.0-rc1).
- The finding that zero-shot Qwen3-Embedding-8B nearly matches Lean Finder is a useful baseline. Our benchmark should include a plain-embedder control.

## Open questions

- How does the current `main` model perform? No numbers have been published yet.
- What is the rate limit or availability guarantee for the HF endpoint and Space?
- Will real Zulip queries be released in any anonymized form?

## Sources

- Paper: https://arxiv.org/abs/2510.15940
- Code, test data: https://github.com/delta-lab-ai/lean-finder
- Model card: https://huggingface.co/delta-lab-ai/lean-finder ; v2 preview metadata: https://huggingface.co/api/models/delta-lab-ai/lean-finder-v2-preview
- Web: https://leanfinder.github.io ; Space: https://huggingface.co/spaces/delta-lab-ai/Lean-Finder
- lean-lsp-mcp integration: https://github.com/oOo0oOo/lean-lsp-mcp/blob/main/src/lean_lsp_mcp/tools/search.py
- LeanSearch v2 comparison: https://arxiv.org/abs/2605.13137
