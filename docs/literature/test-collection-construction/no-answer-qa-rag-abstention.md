# Unanswerable queries in QA and RAG evaluation (SQuAD 2.0, RGB, NoMIRACL, CRAG, UAEval4RAG, AbstentionBench, selective QA)

- **Kind:** paper cluster (benchmarks + evaluation methodology)
- **Links:**
  - SQuAD 2.0, "Know What You Don't Know" https://arxiv.org/abs/1806.03822
  - Selective QA under domain shift https://arxiv.org/abs/2006.09462
  - Selective classification for DNNs (risk–coverage) https://arxiv.org/abs/1705.08500
  - RGB (negative rejection) https://arxiv.org/abs/2309.01431
  - NoMIRACL https://arxiv.org/abs/2312.11361
  - CRAG https://arxiv.org/abs/2406.04744
  - UAEval4RAG https://arxiv.org/abs/2412.12300
  - AbstentionBench https://arxiv.org/abs/2506.09038
  - Abstention survey "Know Your Limits" https://arxiv.org/abs/2407.18418
  - FaithEval https://arxiv.org/abs/2410.03727, Trust-Score/Trust-Align https://arxiv.org/abs/2409.11242
- **Authors / org, date:** 2017 (Geifman & El-Yaniv) to June 2025 (AbstentionBench). Stanford (SQuAD 2.0, Kamath et al.), CAS (RGB), Waterloo/Huawei (NoMIRACL), Meta (CRAG), Salesforce (UAEval4RAG, FaithEval), Meta FAIR (AbstentionBench).
- **Status:** All datasets are public. NoMIRACL code/data at https://github.com/project-miracl/nomiracl; CRAG at https://github.com/facebookresearch/CRAG/ (per the abstracts).

## What it is

The QA community has treated "no correct answer exists" as a first-class test case since SQuAD 2.0 (2018). The RAG community rediscovered it in 2023–2025 as "negative rejection", "unanswerability" and "abstention". These are the most mature designs for our problem: an agent asks for a Mathlib lemma that does not exist, the engine returns something, and the agent misuses it. This note collects the design choices that transfer: how no-answer items are built, how abstention is detected, and how answerable and unanswerable performance are combined into one score.

## How it works

### Constructing no-answer items

- **Adversarial, human-written, on-topic (SQuAD 2.0).** Crowdworkers wrote 53,775 unanswerable questions against SQuAD paragraphs, roughly one-to-one with answerable ones in dev/test ([arXiv 1806.03822](https://arxiv.org/abs/1806.03822), §4). Two desiderata are stated explicitly:
  - *Relevance:* the question must look on-topic, "otherwise, simple heuristics (e.g., based on word overlap) could distinguish answerable and unanswerable questions".
  - *Plausible answers:* a span of the right type must exist in the context, so that type matching cannot give the game away.
  - Crowdworkers also annotated the **plausible (wrong) answer**. "Roughly half of all wrong answers on unanswerable questions exactly matched the plausible answers", for both systems and humans (§5.4). Plausible distractors are a measurable failure mode, not just a construction aid.
  - Auto-generated negatives (TF-IDF retrieved paragraphs, rule-based entity/antonym swaps) were "much easier for existing models to detect": the best SQuAD 2.0 score was 15.4 F1 below the best score on either automatic variant (§5.3). Manual audit found 93% of sampled negatives truly unanswerable (§4).
- **All retrieved passages judged non-relevant (NoMIRACL).** The non-relevant subset holds queries whose top-k retrieved passages were all judged non-relevant by native-speaker annotators. The relevant subset holds queries with at least one relevant passage in the top k. It spans 18 languages, 56,000+ samples and 31 annotators ([arXiv 2312.11361](https://arxiv.org/abs/2312.11361), §1–2). Note that "no answer" here means *no answer in the retrieved top-k*, not *no answer in the corpus*.
- **Noise-only contexts (RGB).** The negative-rejection testbed supplies only negative (noisy) documents, and the model should output "insufficient information" ([arXiv 2309.01431](https://arxiv.org/abs/2309.01431), §2).
- **Taxonomy-driven synthesis (UAEval4RAG).** Six categories are synthesized automatically from any knowledge base: Underspecified, False-presupposition, Nonsensical, Modality-limited, Safety-concerned, and **Out-of-Database** ("highly relevant but do not have an answer in the knowledge base") ([arXiv 2412.12300](https://arxiv.org/abs/2412.12300), §3.1). Out-of-Database is the category that matches "the lemma doesn't exist".
- **False premises (CRAG).** False-premise questions are one of eight question types. The gold answer is the literal string "invalid question" ([arXiv 2406.04744](https://arxiv.org/abs/2406.04744), §3 and appendix prompts).
- **Perturbing answerable items (AbstentionBench).** GSM8K-Abstain, GPQA-Abstain and MMLU-Math-Abstain remove key information from answerable questions, giving a mix of answerable and unanswerable items. The Unanswerable Math Word Problems set (UMWP) is added. The benchmark covers 20 datasets in all, spanning unknown answers, underspecification, false premises, subjective and outdated questions ([arXiv 2506.09038](https://arxiv.org/abs/2506.09038), §3).

### Scoring

- **Folded into the main metric (SQuAD 2.0).** "For negative examples, abstaining receives a score of 1, and any other response gets 0, for both exact match and F1" ([arXiv 1806.03822](https://arxiv.org/abs/1806.03822), §5.2 fn. 3). Models abstain when P(unanswerable) exceeds a threshold that is tuned on dev and then fixed for test. An **always-abstain baseline** gets 48.9 test F1, against 66.3 for the best model and 89.5 for humans. Reporting that trivial baseline is essential whenever no-answer items are about half the set.
- **Binary contingency table (NoMIRACL).**
  - Hallucination rate = FP/(FP+TN) on the no-answer subset.
  - Error rate = FN/(FN+TP) on the answerable subset.
  - The two rates are reported *separately*, so over-abstention is visible.
  - LLAMA-2 and Orca-2 exceed 88% hallucination rate. Mistral and LLAMA-3 hallucinate less but reach up to a 74.9% error rate ([arXiv 2312.11361](https://arxiv.org/abs/2312.11361), abstract, §2.1).
- **Rejection rate (RGB).** Rejection is measured by exact match and also by ChatGPT judging whether the response contains any rejection. The best rejection rates were 45% (English) and 43.33% (Chinese). The gap between exact-match and judge-based rejection shows that models "fail to strictly follow instructions", which makes rejection hard to parse ([arXiv 2309.01431](https://arxiv.org/abs/2309.01431), Table 3).
- **Asymmetric utility (CRAG).**
  - Human grading scores perfect = 1, acceptable = 0.5, missing ("I don't know", *empty response*, clarification request) = 0, incorrect = −1.
  - "Truthfulness" is the mean of these scores. Auto-eval merges perfect and acceptable, giving accurate/missing/incorrect = 1/0/−1 ([arXiv 2406.04744](https://arxiv.org/abs/2406.04744), §4.1–4.2).
  - This is the simplest metric that *rewards* abstaining over being wrong.
- **Two ratios plus a joint score (UAEval4RAG).**
  - *Unanswered ratio* is objective: the response is answered, asks for clarification, or is rejected.
  - *Acceptable ratio* is category-specific and LLM-judged.
  - A *joint score* is a weighted combination of correctness on answerable queries and acceptable ratio on unanswerable ones ([arXiv 2412.12300](https://arxiv.org/abs/2412.12300), §3.3).
  - The paper reports "hidden trade-offs" when swapping retrievers, rerankers, LLMs and prompts. No single configuration wins across datasets (abstract).
- **Abstention recall, precision and F1 (AbstentionBench).**
  - A Llama-3.1-8B-Instruct judge decides whether a response abstains. It reached 88% accuracy on a manually annotated sample.
  - Recall is the headline metric, because models "generally exhibit high abstention precision". Precision and F1 capture over-abstention ([arXiv 2506.09038](https://arxiv.org/abs/2506.09038), §4).
  - Headline finding: reasoning fine-tuning degrades abstention by 24% on average, even on math.
- **Risk–coverage (selective prediction).**
  - A confidence threshold γ induces *coverage* (the fraction answered) and *risk* (the error on the answered fraction).
  - Report the area under the risk–coverage curve (AUC; lower is better) and **coverage at a fixed risk**, e.g. coverage at 80% accuracy ([arXiv 2006.09462](https://arxiv.org/abs/2006.09462), §3). Geifman & El-Yaniv give the deep-learning formulation with guaranteed risk ([arXiv 1705.08500](https://arxiv.org/abs/1705.08500)).
  - Kamath et al. test on a *mixture* of in-domain SQuAD and out-of-domain data, because softmax confidence is overconfident on OOD inputs. A trained calibrator answers 56.1% of questions at 80% accuracy versus 48.2% for MaxProb ([arXiv 2006.09462](https://arxiv.org/abs/2006.09462), §1).

## Evaluation

Cross-cutting findings with numbers:

| Benchmark | No-answer construction | Headline no-answer number |
|---|---|---|
| SQuAD 2.0 | Adversarial crowd-written, on-topic, with plausible distractor | Best model 66.3 F1; always-abstain 48.9; human 89.5 ([§5.2](https://arxiv.org/abs/1806.03822)) |
| RGB | Noise-only retrieved docs | Best rejection rate 45% EN / 43.33% ZH ([Table 3](https://arxiv.org/abs/2309.01431)) |
| NoMIRACL | Top-k judged all non-relevant | >88% hallucination rate (LLAMA-2, Orca-2) ([abstract](https://arxiv.org/abs/2312.11361)) |
| CRAG | False-premise type + missing-vs-wrong scoring | "SOTA industry RAG solutions only answer 63% of questions without any hallucination" ([abstract](https://arxiv.org/abs/2406.04744)) |
| AbstentionBench | 20 datasets incl. perturbed math | Reasoning fine-tuning −24% abstention on average ([abstract](https://arxiv.org/abs/2506.09038)) |
| Selective QA | Mixed ID/OOD pool, risk–coverage | 56.1% vs 48.2% coverage at 80% acc. ([§1](https://arxiv.org/abs/2006.09462)) |

The abstention survey organizes this literature by query, model and human-values perspectives. It is a starting point for further benchmarks ([arXiv 2407.18418](https://arxiv.org/abs/2407.18418)). FaithEval adds "unanswerable context" as one of three faithfulness tasks (4.9K problems) ([arXiv 2410.03727](https://arxiv.org/abs/2410.03727)). Trust-Score scores RAG LLMs partly on whether they "correctly refuse" ([arXiv 2409.11242](https://arxiv.org/abs/2409.11242)). The metric details of those two papers were not checked here (unverified).

## Relevance to lean-explore-bench

- **The analogue is Out-of-Database, and it must be adversarial.** A no-answer Lean query must look like a real Mathlib request: right namespace, naming style and types. There must also be a *plausible distractor* in the library, such as a lemma with one hypothesis more or a nearby type. SQuAD 2.0 shows that auto-generated negatives are far easier, and that half of wrong answers hit the distractor. We should record the distractor per query and report "distractor hit rate" separately.
- **Separate "no answer in top-k" from "no answer in the corpus".** NoMIRACL's negatives are defined only relative to a retriever's top-k. For Lean we can do better: non-existence can be checked against the whole library by name lookup, type search, or `exact?`. This is closer to SQuAD 2.0's paragraph-level guarantee.
- **Score with a missing-beats-wrong utility.** A CRAG-style 1/0/−1 score over engine outputs works: relevant = +1, explicit empty or low-confidence = 0, confident irrelevant = −1. It rewards engines that can say "nothing good here" without letting always-abstain win on the answerable half.
- **Always report both halves and the trivial baselines.** Report NoMIRACL's two error rates (hallucination rate on no-answer, error rate on answerable), plus SQuAD 2.0's always-abstain and never-abstain baselines.
- **Tune thresholds on dev and freeze them for test.** SQuAD 2.0 and Kamath et al. both do this. Engines that expose scores (e.g. LeanExplore's similarity threshold, see [../lean-engines/leanexplore.md](../lean-engines/leanexplore.md)) should get their abstention threshold chosen on a dev split.
- **Mix domains when calibrating.** Kamath et al.'s domain-shift setting maps to Mathlib versus other packages, or old versus new Mathlib snapshots.
- **Transferable weakness:** most of these benchmarks judge abstention with an LLM (RGB, UAEval4RAG, AbstentionBench) because free-text refusals are hard to parse. A search engine returns a list, not prose. So we can define abstention mechanically (empty list, or top score below threshold) and avoid judge error entirely at the engine level. Judges are needed only at the agent level.

## Open questions

- None of these benchmarks is a *retrieval* benchmark with an empty gold set scored by a ranking metric. They all score the reader or generator. See [no-answer-retrieval-qpp-and-truncation.md](no-answer-retrieval-qpp-and-truncation.md) for the retrieval side.
- What fraction of no-answer queries should the benchmark contain? SQuAD 2.0 used about 1:1 in dev/test. A realistic agent-traffic rate for nonexistent Mathlib lemmas is unknown and should be measured from logs.
- Should partial answers count? A query can ask for "X for all fields" when Mathlib has only the version for commutative rings. SQuAD 2.0 and CRAG have no graded "near-miss" class. UAEval4RAG's "acceptable ratio" is the closest.

## Sources

- Rajpurkar, Jia, Liang. "Know What You Don't Know: Unanswerable Questions for SQuAD", ACL 2018. https://arxiv.org/abs/1806.03822 (§2 desiderata, §4 dataset, §5.2 scoring and baselines, §5.3 automatic negatives, §5.4 plausible distractors)
- Kamath, Jia, Liang. "Selective Question Answering under Domain Shift", ACL 2020. https://arxiv.org/abs/2006.09462 (§1, §3 risk–coverage AUC and coverage at accuracy)
- Geifman, El-Yaniv. "Selective Classification for Deep Neural Networks", 2017. https://arxiv.org/abs/1705.08500
- Chen et al. "Benchmarking Large Language Models in Retrieval-Augmented Generation" (RGB), AAAI 2024. https://arxiv.org/abs/2309.01431 (§2 negative rejection, Table 3)
- Thakur et al. "Knowing When You Don't Know" (NoMIRACL), EMNLP Findings 2024. https://arxiv.org/abs/2312.11361 (§1–2.1 construction and metrics)
- Yang et al. "CRAG – Comprehensive RAG Benchmark", NeurIPS 2024 D&B. https://arxiv.org/abs/2406.04744 (§4.1–4.2 scoring, false-premise prompts in appendix)
- Peng et al. "Unanswerability Evaluation for Retrieval Augmented Generation" (UAEval4RAG), 2024. https://arxiv.org/abs/2412.12300 (§3.1 taxonomy, §3.3 metrics)
- Kirichenko et al. "AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions", 2025. https://arxiv.org/abs/2506.09038 (§3 datasets, §4 judge and metrics)
- Wen et al. "Know Your Limits: A Survey of Abstention in Large Language Models", TACL. https://arxiv.org/abs/2407.18418
- Ming et al. "FaithEval", ICLR 2025. https://arxiv.org/abs/2410.03727 (abstract only)
- Song et al. "Measuring and Enhancing Trustworthiness of LLMs in RAG..." (Trust-Score), ICLR 2025. https://arxiv.org/abs/2409.11242 (abstract only)
