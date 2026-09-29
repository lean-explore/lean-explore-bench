# Inducing a query taxonomy from logs with LLMs, then classifying the log at scale (synthesis)

- **Kind:** evaluation methodology (synthesis)
- **Links:**
  - Wan et al., "TnT-LLM", Microsoft, 2024 ([arXiv 2403.12173](https://arxiv.org/abs/2403.12173))
  - Shah et al., "Using LLMs to Generate, Validate, and Apply User Intent Taxonomies", Microsoft, 2023 ([arXiv 2309.13063](https://arxiv.org/abs/2309.13063))
  - Tamkin et al., "Clio", Anthropic, 2024 ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678))
  - Wang, Shang & Zhong, "Goal-Driven Explainable Clustering" (GoalEx), EMNLP 2023 ([arXiv 2305.13749](https://arxiv.org/abs/2305.13749))
  - Pham et al., "TopicGPT", NAACL 2024 ([arXiv 2311.01449](https://arxiv.org/abs/2311.01449))
  - De Raedt et al., "IDAS", 2023 ([arXiv 2305.19783](https://arxiv.org/abs/2305.19783)); Zhang, Wang & Shang, "ClusterLLM", EMNLP 2023 ([arXiv 2305.14871](https://arxiv.org/abs/2305.14871)); Grootendorst, "BERTopic", 2022 ([arXiv 2203.05794](https://arxiv.org/abs/2203.05794), [docs](https://maartengr.github.io/BERTopic/))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

LeanExplore now logs de-identified queries (encrypted text, package filters, result count, source ∈ {web, web_account, api, mcp}, UTC day; no user, session, IP or client ID). The first ~6,700 rows are ~99% API traffic, probably from one or two automated clients. The plan is to use the log to *discover* query categories, then build a balanced benchmark with 60–100 synthetic queries per category, reported per category.

This note covers step 1: how to induce a category taxonomy from a log with LLMs, validate it with humans, and label the whole log, so that rare but distinct query types come out as their own categories. Existing intent taxonomies are in [query-logs-intent-taxonomies.md](query-logs-intent-taxonomies.md). Log shape and sampling are in [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md), and the agent/human split is in [query-logs-agent-vs-human-queries.md](query-logs-agent-vs-human-queries.md). Generating the per-category queries is covered in [synthetic-query-generation-and-simulation.md](synthetic-query-generation-and-simulation.md).

## How it works

### LLM-first: the LLM writes the taxonomy, then labels

- **TnT-LLM (Wan et al. 2024), Bing Copilot logs.** Two phases ([arXiv 2403.12173](https://arxiv.org/abs/2403.12173), §3):
  - *Phase 1, taxonomy generation.* An LLM first summarises each conversation for the use case (e.g. "intent detection", about 20 words). Then an initial-generation prompt drafts a taxonomy from one minibatch of summaries, an update prompt revises it on each later minibatch ("evaluate, identify issues, modify"), and a review prompt checks the final format. The authors frame this as SGD over a prompt-based mixture model. Rerunning Stage 2 inside each category gives a hierarchy.
  - *Phase 2, classification at scale.* GPT-4 labels a larger sample with a primary label and all applicable labels. These pseudo-labels train cheap classifiers (logistic regression, LightGBM, MLP on ada2 or Instructor-XL embeddings), which then label the full corpus.
  - *Data and settings* (§5.1–5.2): 10 weeks of conversations (6 Aug – 14 Oct 2023), 1k/week for Phase 1 and 5k/week for Phase 2, split 60/20/20. After privacy and content filters, 9,592 and 48,160 conversations remained. Targets were 10 intent and 25 domain categories, with a minibatch of 200. They ran 10 trials and picked the best on a validation split with an LLM "model selection" prompt.
- **Shah et al. (2023), Bing search and chat logs.** A human-in-the-loop method built around five taxonomy criteria: *comprehensiveness, consistency, clarity, accuracy, conciseness* ([arXiv 2309.13063](https://arxiv.org/abs/2309.13063), §3.2). GPT-4 drafts the taxonomy. Two annotators then code samples and argue out their disagreements, and GPT-4 adds definitions plus positive and negative examples. After that the taxonomy is frozen and applied (§3.4–3.5, §5).
- **GoalEx (Wang, Shang & Zhong 2023).** Propose–Assign–Select ([arXiv 2305.13749](https://arxiv.org/abs/2305.13749), §3):
  - *Propose.* An LLM reads corpus subsets plus a free-text *goal* ("cluster by X") and proposes about 30–50 candidate cluster explanations, each a natural-language predicate.
  - *Assign.* An LLM checks every (sample, predicate) pair.
  - *Select.* Integer linear programming picks K predicates so that each sample is covered about once. Applying it recursively gives a taxonomy (§5.2).
- **TopicGPT (Pham et al. 2024).** The LLM walks a document sample and either assigns each document to an existing topic or adds a new "label: one-sentence description" topic. A refinement pass merges topic pairs whose embedding cosine is ≥ 0.5 and removes topics below a frequency "removal threshold" (10 and 5 in their runs). A second LLM assigns topics, quoting supporting text, and hallucinated labels are self-corrected ([arXiv 2311.01449](https://arxiv.org/abs/2311.01449), §3, §4).

### Embed-first: cluster, then have an LLM name the clusters

- **Clio (Tamkin et al. 2024), Claude.ai usage.** Pipeline ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678), §2.2 and the system-architecture appendices):
  - *Facets.* Each conversation gets several facets, some computed (turns, language) and some LLM-extracted summaries (task, topic). Clustering uses one facet at a time.
  - *Base clusters.* The chosen facet is embedded with all-mpnet-base-v2 and clustered with k-means. k "can be quite large, including many thousands"; exact values are withheld.
  - *Naming.* Claude names each cluster from 50 in-cluster summaries plus 50 summaries that sit *nearest the centroid but outside the cluster*, as contrastive negatives.
  - *Hierarchy.* Clusters are grouped into neighbourhoods averaging 40 clusters. Claude proposes parents per neighbourhood, deduplicates them across neighbourhoods, assigns children with shuffled option order, and renames the parents. They found HDBSCAN and agglomerative clustering "inferior" to this.
  - *Privacy layers.* Summaries are told to omit private information. Clusters are kept only above minimum counts of *unique accounts* and conversations. Cluster summaries again omit private details, and an LLM auditor removes any cluster that still contains them (§2.3).
  - *Cost.* About $48.81 for 100,000 conversations (§2.2).
- **IDAS (De Raedt et al. 2023).** An LLM writes a short abstractive "label" for each utterance, bootstrapped in-context from prototypical seeds. The utterance and its label are encoded and clustered. Up to +7.42% on standard cluster metrics on Banking, StackOverflow and Transport ([arXiv 2305.19783](https://arxiv.org/abs/2305.19783), abstract).
- **ClusterLLM (Zhang et al. 2023).** It asks an LLM hard triplet questions ("does A match B better than C?") to fine-tune a small embedder. It then asks pairwise "same category?" questions to choose the *granularity* cut in a cluster hierarchy. Tested on 14 datasets at about $0.6 per dataset ([arXiv 2305.14871](https://arxiv.org/abs/2305.14871), abstract).
- **BERTopic.** Embed, reduce, then HDBSCAN. `min_cluster_size` defaults to 10, and "outliers are to be expected" (topic −1) ([parameter docs](https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html)). An optional LLM step labels each topic from keywords and, by default, its 4 most representative documents; it names clusters but does not form them ([LLM docs](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html); [arXiv 2203.05794](https://arxiv.org/abs/2203.05794)).

## Evaluation (how taxonomy quality was measured)

| Study | Taxonomy check | Human agreement | LLM vs human | Other results |
|---|---|---|---|---|
| TnT-LLM | coverage (share sent to "Other"); pairwise label accuracy (true label vs random other label); use-case relevance; 3 author-raters, 200 conversations | taxonomy rating: Fleiss κ 0.476 (intent accuracy), 0.466 (intent relevance), 0.379 (domain relevance). Primary label on 400 conversations: 0.553 intent, 0.624 domain | GPT-4 primary label κ 0.572 intent, 0.695 domain; all-labels exact match only 0.271 / 0.102 | coverage > 99.5%; ada2+logistic regression 0.658 intent accuracy vs GPT-4's 0.655 against human labels |
| Shah et al. | 5 criteria; "Other" rate; 100-item manual spot check (95 correct) | 3/10 exact agreement at first; after revision κ 0.762 on 124 conversations | κ 0.7212 vs human majority; Fleiss κ 0.8516 across 5 GPT-4 runs | no category under 2% in 16,987 test items |
| Clio | manual review of each stage; reconstruction of a synthetic corpus with known categories | n/a | summaries 96% accurate; base cluster titles 99% accurate on random traffic; about 3% of members per cluster "did not clearly belong"; hierarchy titles 97% | 94% reconstruction accuracy over 20 top-level categories (19,476 synthetic chats, 15 languages; random 5%); 84% on 18 "concerning" categories |
| GoalEx | coverage/overlap; explanation accuracy (pick the right explanation vs a distractor); goal relevance | 3 Turkers per item, majority vote | n/a | explanations picked correctly 80% of the time (LDA 56%, Instructor 71%); only 66% of samples covered, 60% exactly once |
| TopicGPT | harmonic purity, ARI and NMI against human labels; stability under reruns | n/a | n/a | purity 0.74 vs 0.64 for LDA (Wiki); the same run twice gives purity 0.95, a different sample 0.67 |

Sources: TnT-LLM Tables 1–3, §5.2–5.3 ([arXiv 2403.12173](https://arxiv.org/abs/2403.12173)); Shah §3.4–3.5, §5 ([arXiv 2309.13063](https://arxiv.org/abs/2309.13063)); Clio "Validation" appendix ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678)); GoalEx §5.3 ([arXiv 2305.13749](https://arxiv.org/abs/2305.13749)); TopicGPT main results and stability tables ([arXiv 2311.01449](https://arxiv.org/abs/2311.01449)).

Lessons that bear on our setting:

1. **Intent needs an LLM; topic does not.** Embedding + k-means baselines produced accurate *domain* labels but "fail to capture the user intent". The authors attribute this to intent needing reasoning beyond surface semantics ([TnT-LLM](https://arxiv.org/abs/2403.12173), §5.2.3). Instructor + k-means also collapsed on non-topic goals: macro-F1 25 vs 97 for GoalEx when clustering by language ([GoalEx](https://arxiv.org/abs/2305.13749), non-topic results table). A Lean query's *form* (name, syntax, NL) and *need* are not topic.
2. **LLMs over-assign secondary labels.** GPT-4 was "more liberal than humans", with high recall and low precision on all-applicable labels ([TnT-LLM](https://arxiv.org/abs/2403.12173), §5.3.2). Validate primary labels and secondary labels separately.
3. **Rare types are the weak spot of every method.** Clio notes that k-means is suboptimal "for rare, outlier topics" (§5.1). GoalEx merged Animal and Plant into "Biology" and lists "discovering minority clusters" as future work (§4.4, §7). Both frequency-pruning rules delete them on purpose: Shah's conciseness check flags categories under 2%, and TopicGPT drops topics under its removal threshold.
4. **Granularity is unstable.** Different samples or prompts moved TopicGPT from k=73 to k=147 at similar purity (stability table). Shah found level-1 categories stable across LLMs but level-2 "more variance", improved "substantially by holding the level-1 categories constant" (§4.2). New topics plateaued after about 600 documents; TopicGPT suggests stopping once 200 documents yield nothing new (§4).
5. **Validate end-to-end on data with known answers.** Clio's reconstruction test and GoalEx's synthetic corpus with three crossed attributes (64 combinations × 16 texts) are the only checks here with a ground truth ([Clio](https://arxiv.org/abs/2412.13678), "End-to-end evaluation with synthetic data" appendix; [GoalEx](https://arxiv.org/abs/2305.13749), §4.1).
6. **The sampling unit sets the weights.** Clio's two strategies either weight long conversations more (sample outputs, then dedupe by conversation) or weight all conversations equally ("Input & Sampling" appendix). The same choice arises between raw rows and distinct queries.

## Relevance to lean-explore-bench

The recipe below is our proposal, assembled from the sources above. **Categories come from the log; benchmark weights do not.** Each category gets equal weight (60–100 synthetic queries). Log shares are reported only as description, because 99% of the current log is one or two API clients.

**Every LLM step below that reads real queries must run on a local model on the server** (for example a Qwen3 model). Our Privacy Policy forbids sending de-identified queries to third-party AI services. External APIs may only see text that has passed the release gates in [query-logs-private-analysis-pipeline.md](query-logs-private-analysis-pipeline.md), such as reviewed category descriptions.

1. **Deduplicate before anything else.**
   - Normalise whitespace, case and Unicode vs ASCII notation (as in [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md)).
   - Collapse exact duplicates, then near-duplicates (embedding cosine or small edit distance) *within the same source and UTC day*. This absorbs agent bursts and loops ([query-logs-agent-vs-human-queries.md](query-logs-agent-vs-human-queries.md)).
   - Keep, per distinct query, its raw count, number of distinct days, sources and package filters. Induce the taxonomy on *distinct queries* (types), not rows.
2. **Stop the API client from defining the taxonomy.** Build the induction sample stratified by source: all distinct web, web_account and mcp queries, plus a random draw of API queries capped at the same size. Label the full API set afterwards.
3. **Extract facets per query (Clio/TnT Stage 1).** An LLM writes (a) query form (Lean name / fragment, Lean or type pattern, goal state, LaTeX, NL, mixed), (b) a one-sentence need ("find the lemma that…"), and (c) the math area. Package filter and result count come straight from the log. Cluster on the need facet and cross it with form afterwards, rather than inducing one tangled taxonomy. Summaries also keep decrypted text out of later prompts ([query-logs-privacy-and-release.md](query-logs-privacy-and-release.md)).
4. **Induce two ways and compare.**
   - (a) A TnT-style minibatch LLM taxonomy (target about 8–15 categories), with the instruction that a distinct type with a handful of examples should keep its own category.
   - (b) A Clio-style embedding + k-means over the need facet with a deliberately large k. Name clusters with contrastive nearest-outside examples, then build the hierarchy with an LLM.
   - Run each at least 3 times on different samples or seeds (Shah's bootstrapping). Keep the categories that recur across runs and methods.
5. **Human review.** Two annotators label about 100–150 held-out distinct queries with the draft taxonomy plus "Other". Record a primary label and optional secondary labels.
   - Revise definitions and add positive and negative examples until Cohen's κ on primary labels is at least about 0.6 (our target; Shah reached 0.762) and "Other" is at most about 5% (Shah's rule of thumb).
   - Optionally run TnT's pairwise label-accuracy test.
   - Freeze the level-1 categories before refining level 2.
6. **Classify the full log.** The log is thousands of distinct queries, so an LLM can label all of them directly; TnT-style distillation is unnecessary at this size.
   - Report LLM-vs-human κ on the step-5 set.
   - Relabel twice and report self-agreement (Shah: Fleiss κ 0.8516 across 5 runs).
   - Flag categories whose support comes almost entirely from one source and one or two days. Those may be one bot's quirk.
7. **Merge rule for small categories.**
   - A category needs enough *distinct real* seeds to anchor generation and validation. Since we generate 60–100 queries anyway, raw frequency is not the test.
   - Proposed floor: at least 5 distinct post-dedup queries spread over at least 2 UTC days, and humans can tell it apart (per-category κ not markedly below the overall κ).
   - Below the floor, merge the category into its nearest sibling (chosen by LLM proposal and human decision). Or park it on a "candidate" list and re-check it in the next window.
   - Do **not** apply share-based pruning (Shah's < 2%, TopicGPT's removal threshold). Those rules remove exactly the rare-but-distinct types we want.
8. **Fix the granularity used for weighting before scoring any engine.** Under equal weighting, splitting one category into two doubles its weight in the macro average. Report the headline at the frozen top level, and put finer sub-categories in per-category tables only.
9. **Check stability over time.** Rerun steps 1–6 on each new log window. Report the "Other" rate on new data, the new and vanished categories, and the ARI/NMI of the old taxonomy's labels against a fresh induction (TopicGPT's stability check). Version the taxonomy alongside the benchmark.
10. **Validate the pipeline itself.** Before trusting it on real logs, seed a synthetic log with known Lean query types, including a few rare ones at 0.5–1% share. Check that the pipeline recovers them, as Clio and GoalEx did.

## Open questions

- With no user or session ID, what stands in for Clio's "unique accounts" threshold? Distinct days × sources is a weak proxy when one client dominates.
- Does inducing on the need facet alone find types defined by *form* (goal-state pastes, partial names), or should form be a fixed axis that is not induced?
- How many distinct non-API queries are needed before new categories stop appearing? TopicGPT's plateau was about 600 documents, but on a different kind of corpus.
- Should the categories found only in agent (API/MCP) traffic be reported as a separate track rather than merged with human-origin categories?

## Sources

- Wan et al., "TnT-LLM: Text Mining at Scale with Large Language Models", 2024: https://arxiv.org/abs/2403.12173
- Shah et al., "Using Large Language Models to Generate, Validate, and Apply User Intent Taxonomies", 2023: https://arxiv.org/abs/2309.13063
- Tamkin et al., "Clio: Privacy-Preserving Insights into Real-World AI Use", 2024: https://arxiv.org/abs/2412.13678
- Wang, Shang & Zhong, "Goal-Driven Explainable Clustering via Language Descriptions", EMNLP 2023: https://arxiv.org/abs/2305.13749
- Pham et al., "TopicGPT: A Prompt-based Topic Modeling Framework", NAACL 2024: https://arxiv.org/abs/2311.01449
- De Raedt et al., "IDAS: Intent Discovery with Abstractive Summarization", NLP4ConvAI 2023: https://arxiv.org/abs/2305.19783 (abstract only read)
- Zhang, Wang & Shang, "ClusterLLM: Large Language Models as a Guide for Text Clustering", EMNLP 2023: https://arxiv.org/abs/2305.14871 (abstract only read)
- Grootendorst, "BERTopic", 2022: https://arxiv.org/abs/2203.05794 ; docs https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html and https://maartengr.github.io/BERTopic/getting_started/representation/llm.html
