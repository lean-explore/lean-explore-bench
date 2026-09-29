# Discovering query categories by embedding and clustering (non-LLM pipeline, synthesis)

- **Kind:** evaluation methodology (synthesis)
- **Links:**
  - Embeddings: MTEB ([arXiv 2210.07316](https://arxiv.org/abs/2210.07316)); Instructor ([arXiv 2212.09741](https://arxiv.org/abs/2212.09741)); Qwen3 Embedding ([arXiv 2506.05176](https://arxiv.org/abs/2506.05176), [model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B))
  - Topic-model pipelines: BERTopic ([arXiv 2203.05794](https://arxiv.org/abs/2203.05794), [docs](https://maartengr.github.io/BERTopic/)); Top2Vec ([arXiv 2008.09470](https://arxiv.org/abs/2008.09470)); short-text topic model survey incl. GSDMM ([arXiv 1904.07695](https://arxiv.org/abs/1904.07695)); UMAP ([arXiv 1802.03426](https://arxiv.org/abs/1802.03426), [clustering docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)); HDBSCAN ([parameter docs](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html))
  - Short-text clustering and intent discovery: SCCL ([arXiv 2103.12953](https://arxiv.org/abs/2103.12953)); DeepAligned ([arXiv 2012.08987](https://arxiv.org/abs/2012.08987)); MTP-CLNN ([arXiv 2205.12914](https://arxiv.org/abs/2205.12914)); USNID ([arXiv 2304.07699](https://arxiv.org/abs/2304.07699))
  - Near-duplicates: Lee et al. 2021 ([arXiv 2107.06499](https://arxiv.org/abs/2107.06499)). Rule/feature query classification: Kang & Kim 2003 ([PDF](https://www.cs.cmu.edu/~ihkang97/papers/query_type.pdf)); Lee, Liu & Cho 2005 ([ACM DL](https://dl.acm.org/doi/10.1145/1060745.1060804)). Formula embeddings: Tangent-CFT ([ACM DL](https://dl.acm.org/doi/10.1145/3341981.3344235))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

LeanExplore logs de-identified queries (text, package filters, result count, source ∈ web/api/mcp, UTC day; no user, session or client ID). We want to *discover* query categories from that log, then write 60–100 synthetic queries per category. Real queries may only go to local models such as Qwen3-Embedding-0.6B, which the engine already runs.

This note covers the classic route: turn each query into a vector (plus surface features), cluster, and read the clusters. LLM-driven taxonomy induction (TnT-LLM, Clio, GoalEx, TopicGPT) is in [query-logs-llm-taxonomy-induction.md](query-logs-llm-taxonomy-induction.md). Existing intent taxonomies are in [query-logs-intent-taxonomies.md](query-logs-intent-taxonomies.md), and log shape and sampling in [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md).

## How it works

### Why short queries are hard to cluster

- Short texts give "only very limited word co-occurrence information", so LDA-style models do poorly on them ([Qiang et al. 2019](https://arxiv.org/abs/1904.07695), abstract).
- Sparse bag-of-words fails badly, but TF-IDF can be strong on technical text. On StackOverflow titles (20 classes, mean 8 words), BoW + k-means reached ACC 18.5, TF-IDF 58.4 and SCCL 75.5 ([SCCL](https://arxiv.org/abs/2103.12953), Tables 1–2). Lexical signal matters when queries contain identifiers.
- Imbalance hurts. On Tweet (89 clusters, largest/smallest size ratio 249), SCCL's ACC (78.2) was below the hierarchical baseline HAC-SD (89.6) ([SCCL](https://arxiv.org/abs/2103.12953), Tables 1–2). Real query logs are more imbalanced than benchmark sets.

### Choosing the embedding

- **MTEB clustering is a topic benchmark.** It runs mini-batch k-means (batch 32, k = number of gold labels) and scores V-measure ([MTEB](https://arxiv.org/abs/2210.07316), §3 "Tasks and Evaluation"). The 11 English sets are arXiv/bioRxiv/medRxiv, Reddit, StackExchange and 20 Newsgroups, so the labels are subject areas ([MTEB](https://arxiv.org/abs/2210.07316), dataset list). A good score says little about separating *query form* or *intent*. The sibling note records that embedding + k-means captured domain but not intent in TnT-LLM.
- **Qwen3-Embedding-0.6B** scores 52.33 on MMTEB clustering, vs 57.65 for the 8B model and 50.75 for multilingual-e5-large-instruct. It scores 75.41 on MTEB (Code), which is a retrieval benchmark ([Qwen3 Embedding](https://arxiv.org/abs/2506.05176), MMTEB and MTEB-Code tables). It supports 32–1024 output dimensions (MRL) ([model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)).
- **The instruction changes the space.** Qwen3 puts `{Instruction} {Query}` in the input ([Qwen3 Embedding](https://arxiv.org/abs/2506.05176), §2). The model card says instructions "typically" give 1–5% and should be written in English ([model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)). Instructor found that more detailed instructions help consistently (none < dataset tag < simple < detailed) and that paraphrased instructions still move scores ([Instructor](https://arxiv.org/abs/2212.09741), §4.2–4.3, Figs. 4–5). So an instruction naming the axis we want ("classify by the kind of search request") is a free lever, but it must be fixed and reported.
- **Hybrid representations.** BERTopic keeps embedding (for clustering) and bag-of-words (for c-TF-IDF labels) separate, so preprocessing can differ between them ([BERTopic](https://arxiv.org/abs/2203.05794), §7.1). No source here tests concatenating dense and lexical vectors for query clustering; the SCCL StackOverflow result above is indirect evidence that lexical features carry signal.

### Pipeline components and their pitfalls

- **Normalise and deduplicate first.** Duplicates inflate density, so bot bursts become "clusters". Lee et al. use MinHash over 5-grams (signature 9,000; b = 20, r = 450), then call a pair a duplicate if edit similarity > 0.8 ([Lee et al. 2021](https://arxiv.org/abs/2107.06499), §4.2). Those settings are for documents; queries of 2–10 tokens need character n-grams (our assumption).
- **Dimensionality reduction.** BERTopic reduces with UMAP because distances concentrate in high dimensions ([BERTopic](https://arxiv.org/abs/2203.05794), §3.2). The UMAP docs warn that it "does not completely preserve density" and can "create false tears in clusters, resulting in a finer clustering than is necessarily present". For clustering they suggest n_neighbors ≈ 30, min_dist = 0 and ≥ 10 dimensions ([UMAP docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)). Top2Vec instead chose n_neighbors = 15 and 5 dimensions ([Top2Vec](https://arxiv.org/abs/2008.09470), §2.2.1). UMAP is stochastic, so fix and vary the seed *(unverified: not stated in the pages read)*. PCA is linear and deterministic; in the UMAP docs' MNIST example, HDBSCAN on 50-D PCA clustered only 17.1% of points (ARI 0.054), vs 99.2% (ARI 0.924) after UMAP ([UMAP docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)).
- **k-means / mini-batch k-means.** Fast, needs k, assigns every point (no noise), and favours round clusters of similar size. BERTopic's argument against centroid-based topic words is that "a cluster will not always lie within a sphere around a cluster centroid" ([BERTopic](https://arxiv.org/abs/2203.05794), §1). Clio still chose k-means with very large k over HDBSCAN and agglomerative clustering (see sibling note).
- **HDBSCAN.** Finds clusters of varying density and labels the rest noise (−1). Pitfalls ([HDBSCAN docs](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html)):
  - `min_cluster_size` is "the smallest size grouping that you wish to consider a cluster".
  - Larger `min_samples` makes it "more conservative", so more points become noise. It defaults to `min_cluster_size`, so raising one raises both.
  - Default `eom` selection "has a tendency to pick one or two large clusters and then a number of small extra clusters"; `leaf` gives "many small homogeneous clusters".
  - BERTopic defaults `min_cluster_size` to 10 and says "outliers are to be expected" ([BERTopic docs](https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html)). Top2Vec used 15, because larger values "have a higher chance of merging unrelated document clusters" ([Top2Vec](https://arxiv.org/abs/2008.09470), §2.2.2). `reduce_outliers` can reassign noise, but may cause errors if topics are merged afterwards ([docs](https://maartengr.github.io/BERTopic/getting_started/outlier_reduction/outlier_reduction.html)). For us, a rare query type may sit in the noise set, so noise must be read, not discarded.
- **Agglomerative / hierarchical.** Gives a dendrogram, which suits a multi-level taxonomy. BERTopic's `hierarchical_topics` builds one with Ward linkage over cosine distances between topic c-TF-IDF vectors ([docs](https://maartengr.github.io/BERTopic/getting_started/hierarchicaltopics/hierarchicaltopics.html)). HAC-SD (agglomerative clustering on a sparsified similarity matrix) was the strongest SCCL baseline on imbalanced sets ([SCCL](https://arxiv.org/abs/2103.12953), Table 1).
- **Spectral and GMM.** Spectral clustering handles non-convex shapes but needs k and an affinity graph. A GMM gives soft memberships. Neither was evaluated on queries in the sources read *(general knowledge, unverified here)*.
- **Choosing k.** Intent-discovery work over-clusters and prunes. DeepAligned sets K′ to about twice the true count, runs k-means, and keeps only clusters of at least N/K′ points ([DeepAligned](https://arxiv.org/abs/2012.08987), §3). USNID initialises at 2× (154, 300 and 40 for BANKING, CLINC150 and StackOverflow) and reports estimation error ([USNID](https://arxiv.org/abs/2304.07699), §6.3). Most unsupervised baselines were "not sensitive" to k from 1× to 4× on BANKING and CLINC150, but MTP-CLNN was "extremely sensitive" (§6.4). Silhouette or gap statistics are the textbook options *(not evaluated in the sources read)*.

### Topic-model pipelines for short text

- **BERTopic:** SBERT embed → UMAP → HDBSCAN → c-TF-IDF, with W(t,c) = tf(t,c) · log(1 + A / tf(t)), where A is the average number of words per class ([BERTopic](https://arxiv.org/abs/2203.05794), §3). Its stated weakness is that each document gets a single topic (§7.2). It had the best topic coherence on the short Trump tweets (0.066 vs 0.009 for NMF and CTM) (Table 1). Coherence measures topic words, not agreement with gold categories.
- **Top2Vec:** Doc2Vec or SBERT → UMAP → HDBSCAN; topic vectors are dense-area centroids and the number of topics is found automatically ([Top2Vec](https://arxiv.org/abs/2008.09470), §2). In BERTopic's comparison, Top2Vec with MPNet embeddings lost coherence and diversity on every dataset ([BERTopic](https://arxiv.org/abs/2203.05794), §6.2).
- **GSDMM and short-text topic models:** GSDMM is a Gibbs-sampled Dirichlet multinomial mixture that assumes one topic per text ([Qiang et al.](https://arxiv.org/abs/1904.07695), §3.3.1). In the survey's 20-run comparison, BTM and GSDMM "always outperform" LDA, and other models were "highly data set dependent" (§7.1–7.2). These are bag-of-words models: `List.map` and "map a function over a list" share no tokens.

### Intent discovery in dialogue systems

- **Task.** Cluster user utterances into intents, unsupervised or with some known intents. Benchmarks: BANKING (77 intents, mean 11.9 tokens), CLINC150 (150 intents, 8.3), StackOverflow (20 classes, 9.2) ([USNID](https://arxiv.org/abs/2304.07699), Table 1).
- **Metrics.** NMI, ARI, and ACC under the best one-to-one label mapping found by the Hungarian algorithm ([USNID](https://arxiv.org/abs/2304.07699), §5.3). ACC needs k close to the gold count; NMI is more forgiving when k is too large.
- **Methods.** DeepAligned pre-trains on known intents and aligns k-means pseudo-labels across epochs with the Hungarian algorithm ([arXiv 2012.08987](https://arxiv.org/abs/2012.08987)). MTP-CLNN combines multi-task pre-training (external labelled intents plus in-domain masked LM) with contrastive learning over top-K nearest neighbours ([arXiv 2205.12914](https://arxiv.org/abs/2205.12914), §3). USNID adds centroid-guided clustering and cluster- plus instance-level objectives ([arXiv 2304.07699](https://arxiv.org/abs/2304.07699)).

## Evaluation

Fully unsupervised intent discovery (0% known intents), from [USNID](https://arxiv.org/abs/2304.07699) Table 2:

| Method | BANKING NMI / ARI / ACC | CLINC150 NMI / ARI / ACC | StackOverflow NMI / ARI / ACC |
|---|---|---|---|
| k-means on averaged GloVe | 49.30 / 13.04 / 28.62 | 71.05 / 27.72 / 45.76 | 19.87 / 5.23 / 23.72 |
| Agglomerative on GloVe | 53.28 / 14.64 / 31.62 | 72.21 / 27.05 / 44.13 | 25.54 / 7.12 / 28.50 |
| SCCL (sentence-transformer) | 63.89 / 26.98 / 40.54 | 79.35 / 38.14 / 50.44 | 69.11 / 34.81 / 68.15 |
| USNID | 75.30 / 43.33 / 54.83 | 91.00 / 68.54 / 75.87 | 72.00 / 52.25 / 69.28 |

Lessons:

1. **Even the best unsupervised method gets about half of BANKING wrong** (ACC 54.83) with the *true* k. Clusters are candidates for humans to name, not a finished taxonomy.
2. **ARI is much lower than NMI** across rows; report both, plus Hungarian ACC when there are gold labels.
3. **All these benchmarks are single-domain, fairly balanced and natural-language only.** None contains identifiers, formulas or proof states, so no result above transfers directly to mixed-form Lean queries.
4. **Classic feature classifiers are precise but miss a lot.** Kang & Kim classified queries into topic relevance, homepage finding and service finding from term-distribution differences, mutual information, anchor-text usage rate and POS tags. All four features together gave 91.7% precision and 61.5% recall ([Kang & Kim 2003](https://www.cs.cmu.edu/~ihkang97/papers/query_type.pdf), abstract, Table 2 test set). Lee, Liu & Cho predicted navigational vs informational goals from click and anchor-link distributions ([ACM DL](https://dl.acm.org/doi/10.1145/1060745.1060804); accuracy figures not read, *unverified*). Jansen et al.'s rule classifier reached 74% (see [query-logs-intent-taxonomies.md](query-logs-intent-taxonomies.md)).
5. **Mixed-form inputs need structure.** Formula retrieval systems embed formula *structure*. Tangent-CFT embeds symbol-layout-tree and operator-tree path tuples with fastText rather than raw text ([ACM DL](https://dl.acm.org/doi/10.1145/3341981.3344235); see [../math-ir/ntcir-math.md](../math-ir/ntcir-math.md)). A "codeness" lexicon classifier separated code from non-code web queries at P 87 / R 86 (Rahman et al., in [query-logs-intent-taxonomies.md](query-logs-intent-taxonomies.md)). We found no study that clusters a pool mixing identifiers, formulas and prose with one text embedder.

## Relevance to lean-explore-bench

Recommended pipeline. Every default below is **our design choice** unless it carries a link.

1. **Normalise, then dedup on distinct queries.**
   - Apply NFKC, collapse whitespace and map ASCII/Unicode pairs (`<=`/`≤`, `->`/`→`), as in [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md). Case-fold only queries detected as natural language, because Lean names are case-sensitive.
   - Remove exact duplicates, then near-duplicates with MinHash over character 4-grams plus edit similarity > 0.8 (threshold from [Lee et al.](https://arxiv.org/abs/2107.06499)), within the same source and UTC day. Keep count, number of days and sources per distinct query.
2. **Stratify by form with rules before any clustering.** Form is a surface property that regexes detect cheaply, while embeddings are tuned for topic (MTEB). Strata, in precedence order:
   - proof state: contains `⊢`, or `name : type` hypothesis lines;
   - type pattern: `_` or `?x` placeholders with operators or arrows;
   - exact declaration name: one token, dotted or snake/camel case, no spaces;
   - fuzzy name: 2–4 lowercase tokens that are all Mathlib name components;
   - LaTeX / Unicode math: `\`, `$`, or math symbols in otherwise short text;
   - natural language: everything else; mixed queries get a "mixed" flag.
   Hand-label 200 distinct queries and report per-stratum precision and recall. Kang & Kim's 91.7 / 61.5 shows the usual pattern: precise but incomplete rules.
3. **Embed locally with Qwen3-Embedding-0.6B.** Use the full 1024 dimensions and an English instruction naming the axis, e.g. `Instruct: Identify what kind of Lean/Mathlib search request this is` ([model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) format). Try two instructions and none, and keep the one with the most stable clusters (step 5). Optionally append a down-weighted (×0.3) SVD of character-n-gram TF-IDF, motivated by the StackOverflow TF-IDF result ([SCCL](https://arxiv.org/abs/2103.12953)).
4. **Cluster within each stratum, two ways.**
   - (a) UMAP (cosine, n_neighbors 15–30, min_dist 0, 10 dimensions; [UMAP docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)) → HDBSCAN (min_cluster_size 5, matching the sibling note's 5-distinct-query floor; min_samples 2; `leaf` selection so small groups survive).
   - (b) Agglomerative clustering (Ward on L2-normalised full embeddings), cut at several heights, for the level-1/level-2 hierarchy.
   - Over-cluster rather than under-cluster (DeepAligned/USNID start at 2× the expected k). Merging is a cheap human step; splitting is not.
   - Read every HDBSCAN noise point in the human-origin (web/mcp) strata, and a sample in the API stratum.
   - Global clustering across strata is a *check*. Clusters that straddle strata point to a need that appears in several forms (e.g. "continuity on compact sets" asked in NL and as a type pattern). Record that as a need × form cross-tab, not as one category.
5. **Check stability.** Rerun over 5 UMAP seeds and 80% bootstrap samples, and report pairwise ARI and NMI. Keep a cluster only if it is stable by the rule in [query-clustering-validation-and-visualization.md](query-clustering-validation-and-visualization.md) (Hennig Jaccard ≥ 0.75; 0.6–0.75 goes to human review). Flag clusters whose support is one source on one or two days (likely one bot).
6. **Describe clusters without external LLMs.** List c-TF-IDF keywords ([BERTopic](https://arxiv.org/abs/2203.05794)), the 10 queries nearest the centroid, and 5 random members. Humans or a *local* LLM (see the sibling note) name clusters and merge them into categories.
7. **Validate on data with known answers.** Plant synthetic queries from known categories, including 2–3 rare ones at about 1%, run steps 1–6, and report NMI, ARI and Hungarian ACC ([USNID](https://arxiv.org/abs/2304.07699) §5.3) plus recovery of the rare categories.

## Open questions

- Does the instruction prefix move Qwen3 embeddings toward form/intent enough to matter, or does topic (math area) still dominate?
- How many distinct non-API queries per stratum exist? HDBSCAN with min_cluster_size 5 is meaningless for a stratum of 30 queries; those may need hand coding only.
- Should fuzzy-name detection use the engine's own declaration-name index (a lexicon, as in Rahman's codeness classifier)?
- Is embedding + clustering worth running at all next to the LLM route? Compare the two taxonomies with ARI on a shared labelled sample.

## Sources

- Muennighoff et al., "MTEB", 2022: https://arxiv.org/abs/2210.07316
- Su et al., "One Embedder, Any Task: Instruction-Finetuned Text Embeddings" (Instructor), 2022: https://arxiv.org/abs/2212.09741
- Zhang et al., "Qwen3 Embedding", 2025: https://arxiv.org/abs/2506.05176 ; model card https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- Grootendorst, "BERTopic", 2022: https://arxiv.org/abs/2203.05794 ; docs (parameter tuning, outlier reduction, hierarchical topics): https://maartengr.github.io/BERTopic/
- Angelov, "Top2Vec", 2020: https://arxiv.org/abs/2008.09470
- Qiang et al., "Short Text Topic Modeling Techniques, Applications, and Performance: A Survey", 2019: https://arxiv.org/abs/1904.07695
- McInnes, Healy & Melville, "UMAP", 2018: https://arxiv.org/abs/1802.03426 ; "Using UMAP for Clustering": https://umap-learn.readthedocs.io/en/latest/clustering.html
- HDBSCAN docs, "Parameter Selection for HDBSCAN": https://hdbscan.readthedocs.io/en/latest/parameter_selection.html
- Zhang et al., "Supporting Clustering with Contrastive Learning" (SCCL), NAACL 2021: https://arxiv.org/abs/2103.12953
- Zhang et al., "Discovering New Intents with Deep Aligned Clustering", AAAI 2021: https://arxiv.org/abs/2012.08987
- Zhang et al., "New Intent Discovery with Pre-training and Contrastive Learning" (MTP-CLNN), ACL 2022: https://arxiv.org/abs/2205.12914
- Zhang et al., "A Clustering Framework for Unsupervised and Semi-supervised New Intent Discovery" (USNID), TKDE 2023: https://arxiv.org/abs/2304.07699
- Lee et al., "Deduplicating Training Data Makes Language Models Better", ACL 2022: https://arxiv.org/abs/2107.06499
- Kang & Kim, "Query Type Classification for Web Document Retrieval", SIGIR 2003: https://www.cs.cmu.edu/~ihkang97/papers/query_type.pdf
- Lee, Liu & Cho, "Automatic Identification of User Goals in Web Search", WWW 2005: https://dl.acm.org/doi/10.1145/1060745.1060804 (full text not read; unverified)
- Mansouri et al., "Tangent-CFT: An Embedding Model for Mathematical Formulas", ICTIR 2019: https://dl.acm.org/doi/10.1145/3341981.3344235 (description via abstract/search summary; unverified beyond that)
