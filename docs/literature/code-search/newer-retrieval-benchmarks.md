# Newer (2025–2026) code retrieval benchmarks: ExecRetrieval, FreshStack, RepoAlign-Bench, MM-IssueLoc, AlgoSimBench

- **Kind:** benchmark cluster
- **Links:**
  - ExecRetrieval https://arxiv.org/abs/2609.01865
  - FreshStack https://arxiv.org/abs/2504.13128
  - RepoAlign-Bench https://arxiv.org/abs/2510.24749
  - MM-IssueLoc https://arxiv.org/abs/2607.15205
  - AlgoSimBench https://arxiv.org/abs/2507.15378
- **Authors / org, date:** Apr 2025 to Sept 2026
- **Status:** Research artifacts. The details below come from abstracts unless a section is cited.

## What it is

Each benchmark targets a specific blind spot of CodeSearchNet-era evaluation:

- **ExecRetrieval (EMNLP 2026):** *functional* discrimination. It has 939 Python tasks. Each has one execution-verified canonical implementation plus up to four execution-verified *single-edit buggy* variants planted in the pool. The metric is exec@k: is a functionally correct result in the top k? 23 dense embedding configurations and BM25 are evaluated with paired McNemar tests and bootstrap intervals ([abstract](https://arxiv.org/abs/2609.01865)).
- **FreshStack:** uncontaminated technical-document retrieval.
  - Queries come from *recent, niche* Stack Overflow questions (for example LangChain).
  - The corpus comes from GitHub repositories and documentation.
  - Relevance is judged at the **nugget** level: GPT-4o extracts answer nuggets from accepted answers, then judges whether each document supports each nugget. Judge quality was checked with humans on one topic. Metrics are α-nDCG@10, Coverage@20 and Recall@50 ([abstract](https://arxiv.org/abs/2504.13128); paper §3–4).
- **RepoAlign-Bench (EMNLP 2025):** repository-level retrieval driven by *change requests*, with 52k annotated instances ([abstract](https://arxiv.org/abs/2510.24749)).
- **MM-IssueLoc:** 652 issue→PR instances in 23 languages with screenshots and other visual evidence. It uses paired text-only versus with-image evaluation and file/function gold labels ([abstract](https://arxiv.org/abs/2607.15205)).
- **AlgoSimBench:** 402 multiple-choice items. Each reference problem has one algorithmically similar problem and three distractors that are "semantically close but algorithmically dissimilar". It also probes retrieval ([abstract](https://arxiv.org/abs/2507.15378)).

## Evaluation (headline findings)

- **ExecRetrieval:** the top hosted system reaches exec@10 = 1.00 but only exec@1 = 0.331. Rank-1 misses are the paired buggy variants 91.5–99.4% of the time. The canonical implementation scores below at least one of its near-clone distractors in 67–78% of queries ([abstract](https://arxiv.org/abs/2609.01865)). **Embeddings see topic, not correctness.**
- **FreshStack:** off-the-shelf retrievers "significantly underperform oracle approaches on all five topics", and rerankers fail to improve first-stage retrieval on 2 of 5 topics ([abstract](https://arxiv.org/abs/2504.13128)).
- **MM-IssueLoc:** the best agent reaches 38.96 file Acc@5, and high SWE-bench localization scores "do not transfer cleanly" ([abstract](https://arxiv.org/abs/2607.15205)).
- **AlgoSimBench:** LLM-generated solution attempts combined with BM25 give an 11.8% gain over state-of-the-art embedding models ([abstract](https://arxiv.org/abs/2507.15378)).

## Known flaws

- **ExecRetrieval** uses mechanical single-edit mutations, which may be easier or harder than natural near-misses. It is Python only.
- **FreshStack's** labels depend on an LLM judge (GPT-4o), validated on only one topic (per paper).
- **RepoAlign-Bench's** annotation method is not verified here (unverified).

## Relevance to lean-explore-bench

- **ExecRetrieval is the closest analogue of a critical Lean failure mode.** Mathlib has many near-clone lemmas that differ in one hypothesis, argument order or direction (`le` vs `lt`, `add_comm` vs `add_left_comm`, `Nat` vs `Int` versions). Build a "near-clone distractor" stratum. In Lean the correctness oracle is free: does the lemma typecheck against the target goal?
- **Adopt their statistical protocol:** paired McNemar tests or bootstrap CIs per query, rather than bare averages. Lean benchmarks will be small (hundreds of queries), so significance testing matters.
- **FreshStack's recipe transfers directly:**
  - Queries: recent Zulip #mathlib or #new-members "does Mathlib have..." questions.
  - Nuggets: from the accepted answer, typically the declaration name(s) given.
  - Result: a fresh, community-sourced, contamination-resistant query set. Nugget-level relevance fits multi-lemma answers.
- **AlgoSimBench's** "generate a solution attempt, then BM25" corresponds to HyDE-style "draft a Lean statement, then search", which is worth including as a baseline pipeline.

## Open questions

- How many Zulip questions per month yield a clean (question, declaration) pair? This decides whether a rolling "fresh" split is feasible.

## Sources

- ExecRetrieval: https://arxiv.org/abs/2609.01865
- FreshStack: https://arxiv.org/abs/2504.13128
- RepoAlign-Bench / ReflectCode: https://arxiv.org/abs/2510.24749
- MM-IssueLoc: https://arxiv.org/abs/2607.15205
- AlgoSimBench: https://arxiv.org/abs/2507.15378
