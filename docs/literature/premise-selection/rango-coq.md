# Rango: Adaptive Retrieval-Augmented Proving (Coq) and the CoqStoq dataset

- **Kind:** paper
- **Links:** paper [arXiv:2412.14063](https://arxiv.org/abs/2412.14063) (ICSE 2025); code, data and models [github.com/rkthomps/coq-modeling](https://github.com/rkthomps/coq-modeling)
- **Authors / org, date:** Kyle Thompson, Nuno Saavedra, Pedro Carrott, Kevin Fisher, Alex Sanchez-Stern, Yuriy Brun, João F. Ferreira, Sorin Lerner, Emily First (UCSD, UMass Amherst, INESC-ID/Lisbon, Imperial, among others). Submitted December 2024 ([arXiv](https://arxiv.org/abs/2412.14063)).
- **Status:** Open source. The authors "release Rango, CoqStoq, all trained models ... and all of the code required to reproduce the experiments" ([arXiv §1](https://arxiv.org/abs/2412.14063)). **Proof assistant: Coq 8.18, not Lean.** Included here as a cross-assistant comparison point.

## What it is

A step-wise LLM proof synthesizer for Coq. At every proof step it retrieves two kinds of context from the *current project*: (a) similar **proofs** and (b) relevant **lemma statements**. Both go into a fine-tuned LLM's prompt. The paper calls this retrieval-augmented proving (RAP) ([arXiv §1, §3](https://arxiv.org/abs/2412.14063)).

## How it works

Step-wise fine-tuned LLM prover (DeepSeek-Coder 1.3B) that at every step retrieves in-project similar *proofs* (BM25 over proof states) and accessible *lemma statements* (TF-IDF) into its prompt ([arXiv §3](https://arxiv.org/abs/2412.14063)).

## Evaluation

- **Dataset, CoqStoq** ([arXiv §4, Table 1](https://arxiv.org/abs/2412.14063)): mined from every GitHub repo listing Coq as primary language as of 2023-11-05, then compiled and validated with Coq 8.18 via CoqPyt. Total: 2,226 repos, 196,929 theorems, 2,225,515 proof steps.

  | Split | Repos | Theorems | Steps |
  |---|---|---|---|
  | Train | 2,208 | 181,562 | 2,008,543 |
  | Benchmark | 12 | 10,396 | 162,989 |
  | Validation | 6 | 4,971 | 53,983 |

- **Leakage controls** ([arXiv §4, §5.2, §5.8](https://arxiv.org/abs/2412.14063)):
  1. **Project-level (inter-project) split.** The benchmark is the CoqGym projects that still compile, plus CompCert and Coq-Community long-term-maintained projects. Every other repo goes to training.
  2. **Exact-duplicate filter.** Training files are dropped if any theorem statement exactly matches a validation or benchmark statement (guards against copy-paste across repos).
  3. **Pretraining-contamination check.** The base LLM may have seen the benchmark on GitHub. Two post-cutoff projects, Coq-BB5 and PnVRocqLib (first commit after DeepSeek-Coder's pretraining cutoff, 1,171 theorems), form a separate "cutoff" evaluation.
  4. **Graph2Tac fairness.** Graph2Tac was trained on most benchmark projects, so the comparison is restricted to the 3 projects it did not see, and only to theorems whose statements match exactly across Coq versions.
- **Metric:** percentage of theorems proven (end-to-end, Coq-checked) under a fixed wall-clock budget. The paper reports no retrieval-only metric (recall@k etc.) ([arXiv §5](https://arxiv.org/abs/2412.14063)).
- **Headline numbers** ([arXiv Tables 2–3](https://arxiv.org/abs/2412.14063)):
  - **CoqStoq benchmark:** Rango 3,325/10,396 = **32.0%**. Tactician: 24.8%; Proverbot9001: 19.3%. That is "29% more than Tactician", "66% more than Proverbot".
  - **Graph2Tac subset:** Rango 55.6% vs Graph2Tac 53.4% (496 theorems).
  - **Post-cutoff projects:** Rango 30.1% vs Tactician 28.3% vs Proverbot 18.5%. **The margin over Tactician shrinks from 29% to 6% relative once contamination is controlled.**
- **Retrieval ablations** (500-theorem ablation set; [arXiv Table 4, §5.3](https://arxiv.org/abs/2412.14063)):

  | Variant | Proof rate |
  |---|---|
  | Full Rango | 30.0% |
  | Without lemma retrieval | 29.0% |
  | **Without proof retrieval** | **20.4%** |
  | Without any retrieval | 18.6% |

  - Proof retrieval gives "47% more theorems". Lemma (premise) retrieval alone adds about 3%.
- **Inter-project vs inter-file split** ([arXiv Table 5](https://arxiv.org/abs/2412.14063)): variants were retrained on a random *file-wise* split and compared on 500 theorems that are test items under both splits.
  - Full Rango: 32.0% → 36.8%.
  - No retrieval: 17.8% → 25.4%.
  - **A random file-level split inflates scores, most of all for non-retrieval models.** Retrieval captures much of the project knowledge that would otherwise leak into the weights.
- **Sparse vs dense** (full benchmark; [arXiv Table 6](https://arxiv.org/abs/2412.14063)): **BM25 32.0% ≈ TF-IDF 31.7% ≫ CodeBERT dense 22.0%.** The dense model here is an off-the-shelf 125M CodeBERT, not trained for the task.
- **Naive "prefix retrieval"** (lines preceding the theorem): 31.3%. A hybrid alternating with Rango reaches 33.5% ([arXiv Table 7](https://arxiv.org/abs/2412.14063)). Nearby context is a strong baseline.
- **Other findings** ([arXiv §5.7](https://arxiv.org/abs/2412.14063)): success correlates most strongly with the length of the human proof, and drops for files with ≥100 transitive dependencies.

## Relevance to lean-explore-bench

- **Split granularity matters and has been measured:** random file-wise splits inflate results by up to 43% relative. Our benchmark should hold out whole projects or modules, or use a time cutoff, not random declarations or files.
- **Post-cutoff evaluation sets are the contamination control that actually moved the numbers** (29% → 6% relative margin). For Lean search engines backed by LLM embeddings or informalizations, we should include queries whose targets entered Mathlib (or other libraries) after the engines' index snapshots or model cutoffs, and record index dates.
- **The retrieval target matters.** In Coq, retrieving *similar proofs* helped far more than retrieving *premises*. A Lean search benchmark that scores only "did you find the premise" misses a use case: finding analogous lemmas and proofs to imitate. We could add a "similar-declaration / analogue retrieval" task.
- **Sparse baselines can beat untuned dense models on formal text.** BM25 over identifiers must be a baseline in our suite.
- **Proximity baseline:** "prefix retrieval" (same-file preceding context) was nearly as good as Rango's retrieval. A cheap "same module / nearby declarations" baseline belongs in our suite.
- **Concrete reusable items:**
  - Exact-statement dedup between train and test.
  - Project-level split plus a separate post-cutoff split.
  - BM25-over-identifiers and "prefix/same-file" baselines.
  - Reporting end-to-end proof rate under a fixed wall-clock budget, with ablations that remove retrieval.

## Open questions

- The CoqStoq split is inter-project, but the benchmark and train share Coq's standard library and common dependencies. How much cross-project duplication survives beyond exact-statement matching (e.g., alpha-equivalent restatements) is not measured.
- Ablations use a 500-theorem subset and a single run. Variance is not reported.

## Sources

- Thompson et al., "Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification", ICSE 2025 — https://arxiv.org/abs/2412.14063 (full LaTeX read: §3 approach, §4 dataset + Table 1, §5 Tables 2–7, threats to validity)
- Code / data / models — https://github.com/rkthomps/coq-modeling
