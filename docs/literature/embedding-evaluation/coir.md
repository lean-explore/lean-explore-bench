# CoIR (Code Information Retrieval benchmark)

- **Kind:** benchmark / dataset + evaluation library
- **Links:** paper [arXiv:2407.02883](https://arxiv.org/abs/2407.02883); code [github.com/CoIR-team/coir](https://github.com/CoIR-team/coir) (Apache-2.0; last push 2025-06-30, checked via GitHub API 2026-09-28); included in MTEB as a domain benchmark ([MMTEB §2.4](https://arxiv.org/abs/2502.13595))
- **Authors / org, date:** Li, Dong, Lee, Xia, Zhang, Dai, Wang, Tang (Huawei Noah's Ark Lab et al.), Jul 2024 (ACL 2025 Main).
- **Status:** Open source; available as an MTEB benchmark.

## What it is

CoIR is a code-retrieval benchmark: "ten meticulously curated code datasets, spanning eight distinctive retrieval tasks across seven diverse domains" and 14 programming languages. It has four main task families: Text-to-Code, Code-to-Text, Code-to-Code, and Hybrid (mixed text and code) ([arXiv:2407.02883](https://arxiv.org/abs/2407.02883), abstract and §3). Two of the ten datasets are new; the other eight are repurposed:

| Task | Dataset | #Query (train/dev/test) | #Corpus |
|---|---|---|---|
| Text→Code (contest) | APPS | 5k / – / 3.8K | 9K |
| Text→Code (web query) | CosQA | 19k / – / 500 | 21K |
| Text→SQL | Synthetic Text2SQL | 100k / – / 6K | 106K |
| Code→Text (summary) | CodeSearchNet | 905k / 41k / 53K | 1M |
| Code→Code (context) | CodeSearchNet-CCR (new) | 905k / 41k / 53K | 1M |
| Code→Code (similar) | CodeTrans Ocean-DL / -Contest | 564/72/180; 561/226/446 | 816; 1K |
| Hybrid single-turn QA | StackOverflow QA (new); CodeFeedBack-ST | 13k/3k/2K; 125k/–/31K | 20K; 156K |
| Hybrid multi-turn QA | CodeFeedBack-MT | 53k / – / 13K | 66K |

(From the dataset statistics table in the paper.)

## How it works

- **Schema:** the same corpus/queries/qrels layout as BEIR and MTEB, so results can be compared across benchmarks. The package is pip-installable and supports open-source and API models (§3.4).
- **Protocol:**
  - Open models are run with query and document length truncated to 512 tokens. For Voyage, queries were cut to 256 tokens because of API rate limits.
  - Pooling is last-token for E5-Mistral and mean for the other models.
  - Documents are ranked by cosine similarity (§4).
- **Metric:** "Following BEIR, we use NDCG@10". MAP, Recall and Precision are also produced (§4).
- **Splits:** CoIR ships train, dev and test splits where the sources have them. That makes both zero-shot and fine-tuned evaluation possible, but it also means training on the train splits is easy (and common).

## Evaluation

- The best mean score in the paper is Voyage-Code-002 at 56.26. It "does not universally surpass other models in every task". E5-Mistral, which is strong on text retrieval, is only middling on APPS and CosQA (§5.1).
- The authors motivate CoIR by saying existing code benchmarks "have been extensively overfitted", and that "many models overfit to benchmarks like CodeSearchNet, leading to inflated performance with limited generalization" (§1, §3).
- **Evidence of overfitting (§5.5):**
  - The paper plots CodeSearchNet score minus CoIR score for each model. "Most models score significantly higher on CodeSearchNet, indicating a strong overfitting tendency."
  - OpenAI-Ada-002 and Voyage-Code-002 have the largest gaps.
  - E5-Mistral has the smallest gap.
- **Rankings shift between BEIR and CoIR (§5.4).** GTE-Base "drops from 2nd in BEIR to 6th in CoIR", so "strong text retrieval does not ensure effective code retrieval".
- **Input length matters (§5.3).** The paper compares input caps of 512 and 4,096 tokens:
  - GTE improves: CodeFeedBack-MT goes from 38.20 to 51.32, and StackOverflow QA from 64.36 to 78.63.
  - BGE-M3 is mixed: CodeFeedBack-MT drops from 33.46 to 27.49.
- The authors list these limitations (Limitations section):
  - English only.
  - "each query corresponding to exactly one ground-truth corpus". There are no n-ary or listwise labels, so a query cannot have several correct answers.
  - No metadata-aware queries, such as library version.
- There is also an efficiency analysis of embedding latency, retrieval latency and index memory on CodeFeedBack-ST (156k corpus, 31k queries) (§5.2).

## Relevance to lean-explore-bench

- **Lean search is partly code search.** Queries can be natural language (like Text→Code), a goal or type signature (like Code→Code), or a mix (Hybrid). CoIR's split into task families is a good template for our query categories. Each category should be scored on its own and averaged per category, so that the largest category does not dominate.
- **Single-gold labels are CoIR's main weakness, and in Mathlib it would be fatal.** Mathlib has many correct answers per query: variants, generalizations, `iff` versus `mp`. We should use graded, multi-positive qrels.
- **Truncation is a hidden variable.** CoIR fixed 512 tokens. LeanExplore truncates embedding inputs at 512 tokens and reranker inputs at **256** tokens (`EMBEDDING_MAX_LENGTH=512`, `RERANKER_MAX_LENGTH=256` in [engine.py](https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/engine.py)). Long Lean statements and informalizations may be cut off. The benchmark should record truncation settings per system and could include a long-statement slice.
- **Efficiency reporting.** Adopt CoIR's latency and memory reporting (query embed time, search time, index size), especially because LeanExplore runs on-device.

## Open questions

- Should formal Lean source (the "code" view) and informalizations (the "text" view) be treated as separate corpora or tracks, like CoIR's Text→Code versus Code→Code?

## Sources

- CoIR paper: https://arxiv.org/abs/2407.02883 (table and protocol details read from the arXiv LaTeX source)
- CoIR code: https://github.com/CoIR-team/coir
- MMTEB (CoIR as MTEB domain benchmark): https://arxiv.org/abs/2502.13595
- LeanExplore truncation constants: https://github.com/lean-explore/lean-explore/blob/main/src/lean_explore/search/engine.py (read locally at commit 17b9d6c)
