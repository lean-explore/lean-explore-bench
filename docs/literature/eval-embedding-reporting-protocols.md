# How embedding-model papers report evaluation (E5, BGE, GTE, E5-mistral, NV-Embed, Gemini Embedding, Qwen3-Embedding)

- **Kind:** methodology survey (the papers are case studies of *how* results are reported, not of which model is best)
- **Links:** E5 [arXiv:2212.03533](https://arxiv.org/abs/2212.03533); BGE / C-Pack [arXiv:2309.07597](https://arxiv.org/abs/2309.07597); GTE [arXiv:2308.03281](https://arxiv.org/abs/2308.03281); E5-mistral [arXiv:2401.00368](https://arxiv.org/abs/2401.00368); NV-Embed [arXiv:2405.17428](https://arxiv.org/abs/2405.17428); Gemini Embedding [arXiv:2503.07891](https://arxiv.org/abs/2503.07891); Qwen3 Embedding [arXiv:2506.05176](https://arxiv.org/abs/2506.05176)
- **Authors / org, date:** Microsoft (E5, Dec 2022; E5-mistral, Dec 2023), BAAI (BGE, Sep 2023), Alibaba (GTE, Aug 2023; Qwen3, Jun 2025), NVIDIA (NV-Embed, May 2024), Google (Gemini Embedding, Mar 2025)
- **Status:** All read from the arXiv LaTeX sources, except where a model card is cited.
- **Companion notes:** MTEB machinery, the zero-shot score and reproducibility are in [embed-mteb.md](embed-mteb.md). BEIR's metric choice and pooling bias are in [embed-beir.md](embed-beir.md). This note covers what the *model papers* do with those tools.

## What it is

Embedding-model papers share a reporting template: a headline MTEB (or MMTEB) average, a BEIR/MTEB-retrieval nDCG@10 average, and a few extra benchmarks chosen by the authors. Underneath, they differ a lot in five choices that decide how much a number means:

1. which averages they report;
2. where the baseline numbers come from;
3. whether training data overlaps the test sets, and whether they say so;
4. which prompts or instructions they used at evaluation;
5. whether they add an out-of-distribution check.

## How it works: protocol by protocol

### 1. Benchmarks and metric per task

- **Every paper uses MTEB's fixed metric per task type.** C-Pack spells the scheme out for C-MTEB: retrieval nDCG@10, reranking MAP, STS Spearman, classification and pair classification average precision, clustering V-measure. The overall score is "the average performance of all datasets in C-MTEB" ([C-Pack, C-MTEB section](https://arxiv.org/abs/2309.07597)). NV-Embed lists the MTEB(eng, v1) makeup as 15 retrieval, 4 reranking, 11 clustering, 3 pair classification, 12 classification, 10 STS and 1 summarization task (56 in total) ([NV-Embed](https://arxiv.org/abs/2405.17428)).
- **Retrieval-only claims use BEIR nDCG@10 over "15 datasets that provide public downloads"** (E5, GTE). This is the BEIR subset that MTEB carries.
- **Extra benchmarks are chosen by the authors, and each has its own metric.**
  - Gemini Embedding adds XOR-Retrieve (Recall@5kt) and XTREME-UP (MRR@10) ([Gemini Table 1 caption](https://arxiv.org/abs/2503.07891)).
  - NV-Embed adds AIR-Bench QA (nDCG@10) and Long-Doc (Recall@10) ([NV-Embed App. AIR-Bench](https://arxiv.org/abs/2405.17428)).
  - GTE uses a harder CodeSearchNet setting that searches "all codes from dev and test set" rather than 1k-candidate samples ([GTE](https://arxiv.org/abs/2308.03281)).

  So the headline retrieval metric can change from benchmark to benchmark inside one paper.

### 2. Aggregation: task mean vs task-type mean vs Borda

- **Task mean** weights each dataset equally. In MTEB(eng, v1) that gives retrieval 15/56 ≈ 27% of the average and summarization 1/56 ≈ 2% (our arithmetic from the task counts above).
- **Task-type mean** weights each category equally (1/7 each in eng v1). A single small category, such as MMTEB's "Instruction Retrieval" with a handful of FollowIR-style tasks, then gets the same weight as Retrieval.
- **Gemini Embedding and Qwen3 both report task mean and task-type mean side by side.** Gemini also reports **Borda rank**, "the official leaderboard ranking metric" ([Gemini, evaluation section](https://arxiv.org/abs/2503.07891); [Qwen3 Tables 1–2](https://arxiv.org/abs/2506.05176)).
- **Metric scales get mixed.** MMTEB's Instruction Retrieval column is FollowIR's p-MRR, which ranges from −100 to 100 ([FollowIR](https://arxiv.org/abs/2403.15246)). It sits next to nDCG@10 columns. In Qwen3's MMTEB table it is negative for several baselines: BGE-M3 −3.11, text-embedding-3-large −2.68 ([Qwen3 Table 1](https://arxiv.org/abs/2506.05176)). A type mean therefore averages quantities that do not share a scale.
- **Why this matters for us.** If lean-explore-bench has query categories of very different sizes (for example many natural-language queries and a few type-pattern queries), the choice between query-mean, category-mean and Borda can reorder systems. We should publish all of them, or fix one ahead of time and justify it.

### 3. Where comparison numbers come from

- **Qwen3 copies baselines from leaderboard snapshots.** Its baseline scores were "retrieved from MTEB online leaderboard on June 4th, 2025", with some taken from the MMTEB and Gemini papers (marked α/γ) ([Qwen3 Tables 1–2](https://arxiv.org/abs/2506.05176)).
- **Copied numbers drift.** Qwen3 lists Gemini Embedding at 68.37 task mean / 59.59 type mean on MTEB(Multilingual) and 73.30 on MTEB(eng, v2). Gemini's own paper reports 68.32 / 59.64 and 73.28 ([Gemini intro and Table 6](https://arxiv.org/abs/2503.07891)). The gaps are small, but the same model's score depends on the leaderboard snapshot date. A benchmark should re-run every system itself, or record where and when each number came from.
- **Reranker comparisons fix one first stage.** Qwen3 compares rerankers on "the retrieval top-100 results" of Qwen3-Embedding-0.6B, and says this "ensures a fair evaluation of the reranking models" ([Qwen3, main results and Table 3](https://arxiv.org/abs/2506.05176)). This is the standard way to separate reranker quality from first-stage recall.

### 4. Train/test overlap and "zero-shot" claims

The papers range from a precise per-dataset in-domain label to no statement at all.

| Paper | What it trains on that overlaps the evaluation | How it reports this |
|---|---|---|
| E5 | Fine-tunes on MS MARCO, NQ, NLI | "Since our fine-tuning datasets include MS-MARCO and NQ, the corresponding numbers are in-domain results. For other datasets, these are zero-shot transfer results." It also reports an unsupervised E5-PT row. CCPairs is decontaminated: "we remove text pairs that occur in the evaluation datasets based on exact string match" ([E5, supervised fine-tuning results and data appendix](https://arxiv.org/abs/2212.03533)) |
| GTE | MS MARCO, NQ, FEVER, Quora, MEDI and BERRI mixtures | Only "text pair exact-match" deduplication, which the authors call "an overly strict filter" and flag as a contamination concern ([GTE discussion and appendix](https://arxiv.org/abs/2308.03281)) |
| E5-mistral | 13 labeled sets including MS MARCO, NQ, HotpotQA, FEVER and Quora, all of which are BEIR/MTEB datasets | Has a dedicated "Test Set Contamination Analysis": a case- and space-insensitive string match finds 4 DBPedia test questions in TriviaQA train. Shared Wikipedia corpora are "standard evaluation practice ... we do not regard it as contamination." It also notes that the LLMs' pretraining data is "not publicly accessible" ([E5-mistral App.](https://arxiv.org/abs/2401.00368)) |
| NV-Embed | MS MARCO plus the **training splits of MTEB classification and STS datasets** (AmazonReviews, Banking77, STS12, STS22, STSBenchmark, …) | "certain datasets (e.g., MSMARCO) are training splits of the MTEB Benchmark, which we follow the existing practices established by leading generalist embedding models". It adds AIR-Bench as the zero-shot check ([NV-Embed, training-data section and appendices](https://arxiv.org/abs/2405.17428)) |
| Gemini Embedding | Gecko academic subset plus synthetic data | "we excluded many in-domain MTEB datasets, which improved the performance only on their own test split mainly due to train-test leakage or dataset bias" ([Gemini, training-data section](https://arxiv.org/abs/2503.07891)). There is no per-dataset list in the paper. |
| Qwen3 Embedding | About 150M synthetic pairs plus about 12M filtered pairs for SFT | We found no train/test overlap or decontamination statement in the paper ([Qwen3, training section](https://arxiv.org/abs/2506.05176); our reading of the full source) |
| BGE (C-Pack) | C-MTP (labeled part includes T2Ranking, mMARCO-zh, DuReader) | No explicit decontamination statement found (our reading) |

Takeaways:

- **"Zero-shot" means different things in different papers.** In E5 it is decided per dataset. In NV-Embed it means "on AIR-Bench". In Gemini it means "we removed many in-domain sets". MTEB's leaderboard zero-shot percentage ([embed-mteb.md](embed-mteb.md)) exists because papers do not use a common definition.
- **String-match decontamination is the norm and it is weak.** GTE says so itself. It cannot catch paraphrases, synthetic data generated from the test corpus, or overlap in the LLM's pretraining data.

### 5. Prompts and instructions at evaluation time

- **Query-side-only instructions are the convention**, because they let the document index be prebuilt:
  - E5-mistral: "We do not modify the document side with any instruction prefix. In this way, the document index can be prebuilt" ([E5-mistral](https://arxiv.org/abs/2401.00368)).
  - Qwen3's input format is `{Instruction} {Query}<|endoftext|>` with documents unchanged ([Qwen3 §2 Model Architecture](https://arxiv.org/abs/2506.05176)).
  - NV-Embed masks the instruction tokens out of pooling but notes that "they still impact the output due to self-attention" ([NV-Embed](https://arxiv.org/abs/2405.17428)).
- **Instruction choice changes scores.**
  - The E5-mistral ablation reports MTEB averages of 64.5 with natural-language task instructions and 60.3 for both the "w/o instruction" and "task type prefix" variants. The authors conclude that "the way of adding instructions has a considerable impact on the performance" ([E5-mistral Table 6](https://arxiv.org/abs/2401.00368)). This is a training-plus-evaluation configuration ablation, not an evaluation-only swap.
  - The Qwen3-Embedding-8B card says omitting the query instruction "can lead to a drop in retrieval performance by approximately 1% to 5%" ([model card](https://huggingface.co/Qwen/Qwen3-Embedding-8B)).
  - The BGE v1.5 card says "No instruction only has a slight degradation" and advises choosing "the setting that achieves better performance on your task" ([model card](https://huggingface.co/BAAI/bge-large-en-v1.5)). Taken literally, that invites tuning prompts on the test set.
- **Truncation is part of the protocol.** E5-mistral evaluates "only ... the first 512 tokens for efficiency" even though it supports longer inputs ([E5-mistral](https://arxiv.org/abs/2401.00368)). CoIR caps open models at 512 tokens, but limits API models to 256-token queries because of rate limits ([CoIR, implementation details](https://arxiv.org/abs/2407.02883)). That makes the conditions unequal across models.

### 6. Out-of-distribution sanity checks

- **NV-Embed uses AIR-Bench**, whose "ground truth is kept confidential", as a zero-shot check. It also points out that MTEB gains do not always transfer: SFR-Embedding-2R beats SFR-Embedding-Mistral on MTEB (70.31 vs 67.56) but loses on AIR-Bench QA (49.47 vs 51.58) and Long-Doc (67.45 vs 69.0) ([NV-Embed App. AIR-Bench](https://arxiv.org/abs/2405.17428)).
- **SciRepEval splits its tasks into in-train and out-of-train** and reports both ([SciRepEval](https://arxiv.org/abs/2211.13308)). This is the cleanest design we found for separating "learned this task" from "generalizes".

## Evaluation (what these protocols get right and wrong)

**Good practice worth copying:**
- E5's per-dataset in-domain label.
- E5-mistral's written contamination appendix.
- A fixed first stage for comparing rerankers (Qwen3).
- A held-out or out-of-train check (NV-Embed with AIR-Bench, SciRepEval).
- Reporting several aggregates (Gemini, Qwen3).

**Common gaps:**
- No confidence intervals or significance tests in the headline tables we inspected. Only point estimates are reported (unverified for every appendix).
- Baselines copied from leaderboard snapshots instead of re-run.
- No exact per-task instruction strings in the paper body, which MTEB maintainers found critical for reproduction ([embed-mteb.md](embed-mteb.md)).
- Efficiency (latency, index size, dimension) is seldom reported next to quality. Exceptions: CoIR reports embedding latency per sample, and NV-Embed has a compression appendix. See [eval-embedding-efficiency-tradeoffs.md](eval-embedding-efficiency-tradeoffs.md).

## Relevance to lean-explore-bench

- **Run every embedder ourselves** on the pinned corpus. Store the exact query instruction string, the document template, max tokens, pooling, normalization and model revision in the result file. Never import leaderboard numbers.
- **Each result needs a "training exposure" card** with three levels:
  1. (a) Was the model fine-tuned on Mathlib or Lean data? Examples: Lean Finder, the LeanSearch-style fine-tunes in [bench-mathleap-meld-blueprints.md](bench-mathleap-meld-blueprints.md).
  2. (b) Did that data include our queries, our gold declarations, or text generated from them, such as LLM informalizations of the same declarations?
  3. (c) Unknown (closed API).

  Report in-domain and out-of-domain results separately, the way E5 does.
- **Decontaminate beyond exact match.** Check near-duplicates (normalized text, n-gram overlap, embedding similarity) between benchmark queries and any released training sets for Lean retrievers.
- **Instruction protocol.** Pre-register one instruction per query category and evaluate each instruction-aware model with (i) its model-card instruction and (ii) no instruction. Report both. Prompts must not be tuned on the test split.
- **Aggregates.** Report the per-category score, the macro mean over categories, the micro mean over queries, and Borda. Keep metrics on different scales (for example an instruction-following delta) out of the same mean.
- **Rerankers.** Freeze the candidate list (top-K from one fixed first stage) when comparing them.

## Open questions

- How do we score closed API embedders (Gemini, OpenAI, Voyage) whose training data is unknown? One option is a separate "unknown exposure" tier rather than treating them as zero-shot.
- Do we need an out-of-train analogue of SciRepEval? For example, hold out whole Mathlib subject areas (such as the newest `Mathlib/` directories added after all model cutoffs) as a zero-shot split.

## Sources

- E5: https://arxiv.org/abs/2212.03533 (LaTeX: §5 "Results with Supervised Fine-tuning", decontamination line in the data appendix)
- C-Pack / BGE: https://arxiv.org/abs/2309.07597 (C-MTEB metric list; instruction ablation "w.o. Instruct")
- BGE v1.5 model card: https://huggingface.co/BAAI/bge-large-en-v1.5
- GTE: https://arxiv.org/abs/2308.03281 (sections/discussion.tex, sections/appendix.tex)
- E5-mistral: https://arxiv.org/abs/2401.00368 (Table 6 hyperparameter ablation; App. "Test Set Contamination Analysis")
- NV-Embed: https://arxiv.org/abs/2405.17428 (§4 training data, App. AIR-Bench, compression appendix)
- Gemini Embedding: https://arxiv.org/abs/2503.07891 (sections/data.tex, evaluation.tex, tables/main_table.tex)
- Qwen3 Embedding: https://arxiv.org/abs/2506.05176 (full LaTeX read; Tables 1–3)
- Qwen3-Embedding-8B model card: https://huggingface.co/Qwen/Qwen3-Embedding-8B
- FollowIR p-MRR range: https://arxiv.org/abs/2403.15246
- SciRepEval in-train/out-of-train: https://arxiv.org/abs/2211.13308
- CoIR truncation settings: https://arxiv.org/abs/2407.02883
