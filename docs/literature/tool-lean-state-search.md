# LeanStateSearch (premise-search.com)

- **Kind:** search engine (proof-state → premise retrieval)
- **Links:** web/API <https://premise-search.com/>; engine code <https://github.com/ruc-ai4math/LeanStateSearch>; model code <https://github.com/ruc-ai4math/Premise-Retrieval>; paper [arXiv 2501.13959](https://arxiv.org/abs/2501.13959)
- **Authors / org, date:** Yicheng Tao, Haotian Liu, Shanwen Wang, Hongteng Xu (Renmin University AI4Math). Paper v1 2025-01-21, v3 2025-07-16 ([arXiv](https://arxiv.org/abs/2501.13959)).
- **Status:** Public service, but on 2026-09-28 `https://premise-search.com/` did not respond from our machine: `curl` got no HTTP response within 40 s, and a second check reported connection refused (47.129.51.178:443). The service may be down or may block our network. The code went public 2025-03-05 and has been self-hostable since 2025-04-05 (per the repo, as reported by a sub-agent). Loogle answered normally from the same machine at the same time. lean-lsp-mcp (fork at `5c0eddf`, 2026-01-28) queries it with `rev=v4.22.0` ([server.py](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py#L1049-L1101)). That suggests an index for the Mathlib that goes with Lean v4.22.0 was being served then (unverified). It can be self-hosted.

## What it is

A search engine where **the query is a Lean proof state** (goal plus hypotheses), not text. It returns Mathlib lemmas likely to be used at that step. It is the backend of `#statesearch` and of `#search` with no string in LeanSearchClient, which Mathlib depends on.

## How it works

- A contrastively trained dense retriever with a tokenizer trained on formal text, a fine-grained similarity, and a re-ranker ([arXiv 2501.13959](https://arxiv.org/abs/2501.13959)).
- It indexes Mathlib premises. The corpus is extracted with ntp-toolkit, stored in PostgreSQL plus a vector index ([LeanStateSearch README](https://github.com/ruc-ai4math/LeanStateSearch)).
- **Strength against name/type tools:** it tolerates inexact matches, unlike Loogle and `exact?`.
- **Weakness against NL search:** the user must already have a formal goal.

## Evaluation

From [arXiv 2501.13959](https://arxiv.org/abs/2501.13959), as extracted from the LaTeX source by a sub-agent:

- **Data:** state–premise pairs from Mathlib tag v4.10.0, extracted with LeanDojo scripts. The corpus has 149,549 premises. There are four splits (Random, Reference-Isolated, Proof-Length, Premise-Frequency), each with 65,567 train theorems and 2,000 val/test theorems.
- **Metrics:** Precision, Recall, F1, and nDCG @1/5/10. nDCG uses graded relevance: 1 for the used premise, 0.3 for a premise in the same module, 0 otherwise.
- **Random split:**
  - Their model: R@1/5/10 = 15.17 / 38.20 / 46.53, nDCG@10 = 0.5163.
  - ReProver retrained: 11.79 / 28.78 / 36.69, nDCG@10 0.4617.
  - Fine-tuned general embedders (UniXcoder, E5-large-v2, BGE-m3): about 25–27 R@10.
- **Downstream:** miniF2F pass@1 30.74% vs. 28.28% for ReProver.
- **Loogle:** mentioned only in related work, as "strict matching criteria, which often leads to failures". It is not a baseline.

Independent evaluations:

- **Lean Finder** ([arXiv 2510.15940](https://arxiv.org/abs/2510.15940)), 2,224 raw proof states. Lean State Search gets R@1/5/10 = 3.3 / 23.1 / 32.1 (MRR 0.13), against Lean Finder's 8.3 / 30.1 / 40.0 (MRR 0.19).
- **LeanSearch v2** ([arXiv 2605.13137](https://arxiv.org/abs/2605.13137)). On MathlibMPR, LeanStateSearch recovers 9.3% of premise groups at Recall@10, against 46.1% for LeanSearch v2 reasoning mode. As a retriever in a prover loop it gives 7% on FATE-H and 6% on MathlibMPR-Prop, against 4% with no retrieval.

## Relevance to lean-explore-bench

- **Harness:**
  - Call `GET {base}/api/search?query=<url-encoded goal>&results=<k>&rev=<revision>`. The response is JSON with `name`, `formal_type`, `module`, and `rev` ([lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py#L1049-L1101); [LeanStateSearch README](https://github.com/ruc-ai4math/LeanStateSearch)).
  - The `rev` parameter selects the indexed Mathlib/Lean revision, which helps version pinning.
  - lean-lsp-mcp throttles it to 3 requests per 30 s client-side. The service's own limits are unknown.
  - For large runs, self-host it from the repo (Docker, Nix, and a model downloaded from Hugging Face).
- **Role:** the canonical **proof-state track** engine. The paper's split design (Random vs. Reference-Isolated) and graded-relevance nDCG are worth copying.
- **Caution:** its training data comes from Mathlib proof steps, so Mathlib-derived test goals may overlap its training set. Use held-out or post-cutoff goals.

## Open questions

- Which `rev` values the live service currently accepts, and its rate limits (unverified).
- Whether the live model matches the paper's checkpoint.

## Sources

- Paper: <https://arxiv.org/abs/2501.13959>
- Engine repo: <https://github.com/ruc-ai4math/LeanStateSearch>
- Model repo: <https://github.com/ruc-ai4math/Premise-Retrieval>
- Service: <https://premise-search.com/>
- Lean Finder comparison: <https://arxiv.org/abs/2510.15940>
- LeanSearch v2 comparison: <https://arxiv.org/abs/2605.13137>
- lean-lsp-mcp client code: <https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py>
