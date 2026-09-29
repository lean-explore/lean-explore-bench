# TheoremGraph: Bridging Formal and Informal Mathematics (Kurgan, Wang, Leonen, et al.)

- **Kind:** paper (dataset + retrieval system)
- **Links:**
  - paper: https://arxiv.org/abs/2606.25363
  - site, API and MCP: https://www.theoremsearch.com/
  - matches dataset: https://huggingface.co/datasets/uw-math-ai/theorem-matching
- **Authors / org, date:** Simon Kurgan, Evan Wang, Eric Leonen, Sophie Szeto, Luke Alexander, Artemii Remizov, Jarod Alper, Giovanni Inchiostro, Vasily Ilin (University of Washington Math AI Lab). arXiv v1 2026-06-24.
- **Status:**
  - The dataset, extractors, HTTP API and MCP interface are released at theoremsearch.com ([paper Limitations, "Data availability"](https://arxiv.org/abs/2606.25363)).
  - The public release of judged matches is limited to 23,399 openly licensed candidates, gated for non-commercial research. The authors' own contributions are under CC-BY-NC-SA-4.0 ([paper Limitations](https://arxiv.org/abs/2606.25363)).
  - Liveness of the site and MCP was not checked (unverified).

## What it is

A statement-level dependency graph that joins:

- **informal mathematics**: 11.7M theorem-like statements from arXiv, with 18.3M candidate dependency edges;
- **formal mathematics**: **LeanGraph**, a Lean 4 elaborator-level extractor producing 388,105 declaration nodes and about 11.3M typed edges across 25 Lean projects.

The two sides are linked through LLM-generated "slogans" embedded in a shared space. The paper also benchmarks the retrieval representation against LeanSearch v2. ([paper abstract, §1](https://arxiv.org/abs/2606.25363))

This note focuses on the evaluation methodology.

## How it works

LLM-written slogans and name-and-signature passages are embedded with Qwen3-Embedding-8B, then boosted by a name index, HyDE query rewriting and one-hop expansion over the LeanGraph dependency graph ([paper §5, §8](https://arxiv.org/abs/2606.25363)).

LeanGraph extracts typed edges from elaborated terms rather than source text, which makes it a candidate source of gold labels. The edge types are `sig`, `proof`, `def`, `extends`, `field` and `docref` ([paper §4](https://arxiv.org/abs/2606.25363)).

## Evaluation

- **Formal concept retrieval against LeanSearch v2** ([paper §8](https://arxiv.org/abs/2606.25363)).
  - **Benchmark.** MathlibQR is built by the LeanSearch v2 team. It pairs 200 Mathlib declarations with up to 6 query styles each: plain English, LaTeX, Lean-flavoured, slogan, nickname and special case.
  - The paper uses the **fair-810 subset**: 810 query rows covering 171 targets. Every target is guaranteed to exist in every compared system's corpus. This controls for Mathlib snapshot drift, where "a system can miss a query simply because the target declaration is absent."
  - TheoremGraph indexed the union of Mathlib v4.27 and v4.28 so that all 171 targets were present.
  - **Controlled comparison.** Both systems use the *same* embedder (Qwen3-Embedding-8B, not fine-tuned). Differences are therefore attributed to what is embedded, not to model strength.
  - **Metrics:** nDCG@1, @5 and @10, and Recall@10. The authors did not replicate LeanSearch v2's R@50, R@100 or LLM-judge ranking.
  - **Numbers:**

| Config | nDCG@10 | R@10 |
|---|---|---|
| Ours (A) slogan only | 0.380 | 0.586 |
| Ours (E) recall-optimized (slogan+name/sig+search+graph) | 0.548 | **0.775** |
| Ours (F) ranking-optimized (name/sig+search) | 0.558 | 0.733 |
| LSv2 retriever | 0.494 | 0.657 |
| LSv2 retriever + reranker | **0.623** | **0.780** |

  - Configuration E's R@10 bootstrap 95% CI is [0.746, 0.802]. The authors note that containing LSv2's 0.780 is "a failure to reject, not an equivalence test."
  - Graph expansion adds only +0.8pp R@10 and −0.2pp nDCG@10 once the name/signature passage is present.
  - Per-kind analysis: the gains concentrate on structures, classes, definitions and inductives, whose identity is mostly their name. Theorems and instances decline slightly.
- **Transfer failure to chained-premise retrieval** ([paper §8 "Transfer to MathlibMPR"](https://arxiv.org/abs/2606.25363)). On MathlibMPR, the LeanSearch v2 premise-retrieval benchmark, the configuration tuned for concept retrieval *lowers* group R@10 from 0.224 to 0.165. The authors conclude that concept retrieval and "which lemmas does a proof invoke" retrieval need different signals.
- **Retrieval-augmented autoformalization** ([paper §7, Table "Statement-only autoformalization"](https://arxiv.org/abs/2606.25363)).
  - **Time-split design.** The 24 targets are theorems *introduced in Mathlib v4.30*, and retrieval is only over v4.29.
  - Queries are qwen3-8b back-translations of the signature with the declaration name removed.
  - Four conditions, all using claude-sonnet-4-6 with at most 3 typecheck calls:
    - None;
    - RAG (top retrieved premises);
    - Library (a `grep` tool over the v4.29 declaration listing);
    - RAG+Library.
  - Evaluated-correct counts, judged by claude-opus-4-7 and checked by hand: None 5/24, RAG 8/24, Library 6/24, RAG+Library 8/24.
  - RAG used 14k output tokens and 68 tool calls, against 52k and 275 for Library.
  - Typechecking is a poor success proxy: the None condition typechecks 22/24 outputs but only 5/24 are judged correct.
  - Retrieval recall at top-15 on these 24 targets is only 0.161.
  - The query head trained on typed-dependency labels raises R@100 from 0.16 to 0.54 on "a held-out Mathlib premise benchmark." That benchmark is not further specified (unverified).
- **Cross-formality matching** ([paper §6](https://arxiv.org/abs/2606.25363)).
  - Blueprint `\lean{}` pairs (1,595 pairs) serve as ground truth: Hit@1 is 43.5% and Hit@10 is 69.9%.
  - A GPT-5.4 judge affirms 47,952 of 100,799 candidates at cosine similarity ≥ 0.8. The affirmation rate is 87% in the ≥ 0.9 tier.
  - Judge stability: 93.2% agreement between two runs, Cohen's κ = 0.86.

## Relevance to lean-explore-bench

- **Snapshot/corpus fairness is essential.** The fair-810 idea restricts scoring to targets present in every engine's index. We need the same, or a declared "target missing" outcome that is scored separately from a retrieval miss.
- **Hold the embedder fixed to attribute gains.** This is a useful ablation style when comparing engines that share components.
- **Query style matters a lot.** MathlibQR's 6 query styles expose engines that handle English well but fail on Lean syntax or bare names: a Lean-style query for a named structure had only 12.9% R@10 in the slogan-only baseline. Our query set should be stratified by style and by declaration kind, and results should be reported per stratum.
- **Concept retrieval and premise retrieval are different tasks**, and tuning for one can hurt the other. We should keep them as separate tracks.
- **A version time-split for agent evals** is a clean leakage control that we can copy: targets added in version N+1, with the index at version N. Comparing a RAG tool against a `grep`-the-library tool is a directly relevant baseline for "does a search engine help an agent."
- Reusable items:
  - MathlibQR fair-810, via the LeanSearch v2 release, as an external comparison set.
  - The version time-split protocol.
  - Token and tool-call cost as secondary end-to-end metrics.
  - LeanGraph typed edges, as an elaborated-dependency source for gold labels.
  - theoremsearch.com's MCP, as an engine to benchmark.

## Open questions

- Were configurations A–F tuned on fair-810 itself? The paper does not describe a separate dev set, so the E and F numbers may be optimistic (unverified).
- What exactly is the "held-out Mathlib premise benchmark" used for the query-head R@100 result?
- n = 24 is small for the autoformalization comparison, and no confidence intervals are given for it.

## Sources

- Paper (LaTeX source, main body and conclusion read via arXiv; appendices skimmed only in part): https://arxiv.org/abs/2606.25363 (v1)
- theoremsearch.com: https://www.theoremsearch.com/ (from the paper; not opened, unverified)
- Hugging Face dataset: https://huggingface.co/datasets/uw-math-ai/theorem-matching (from the paper; not opened)
- LeanSearch v2 (source of MathlibQR and MathlibMPR): https://arxiv.org/abs/2605.13137
