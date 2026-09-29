# Validating and visualising query clusters without ground-truth labels (synthesis)

- **Kind:** evaluation methodology (synthesis)
- **Links:** see Sources
- **Authors / org, date:** this repo, Sept 2026; literature from Ben-Hur et al. (2002) to Simpson, Campello & Stojanovski (2025)
- **Status:** living note

## What it is

We plan to cluster de-identified LeanExplore queries in embedding space, optionally have an LLM name the clusters, and turn the result into benchmark categories with 60–100 synthetic queries each. There are no ground-truth labels. This note covers how to tell whether the clusters are real and useful, and how to look at them without fooling ourselves.

- The embedding and clustering pipeline is in [query-clustering-embeddings.md](query-clustering-embeddings.md).
- LLM taxonomy induction (TnT-LLM, Clio) and its human κ checks on category definitions are in [query-logs-llm-taxonomy-induction.md](query-logs-llm-taxonomy-induction.md). This note does not repeat them.
- Judge and assessor agreement in general is in [../statistics/judgment-reliability-and-llm-assessors.md](../statistics/judgment-reliability-and-llm-assessors.md). What may leave the server is in [query-logs-privacy-and-release.md](query-logs-privacy-and-release.md).

## How it works

There are four independent lines of evidence. None is enough alone.

### 1. Internal validity indices (geometry only)

- **What they measure.** Silhouette, Davies–Bouldin (DB) and Calinski–Harabasz (CH) score compactness against separation. scikit-learn warns that silhouette and CH are "generally higher for convex clusters than other concepts of clusters, such as density based clusters like those obtained through DBSCAN" ([scikit-learn](https://scikit-learn.org/stable/modules/clustering.html)).
- **Arbelaitz et al. (2013)** compared 30 indices ([DOI 10.1016/j.patcog.2012.07.021](https://doi.org/10.1016/j.patcog.2012.07.021), §5–6):
  - No small set was significantly best. A top group of about 10 had "Silhouette, Davies–Bouldin* and Calinski–Harabasz ... in the top", and silhouette "obtained the best results in many" settings.
  - "Noise and cluster overlap had the greatest impact". Adding 10% random noise cut the average success score "to a third", and heavy overlap did about the same. Our log has both: automated traffic and many near-duplicate phrasings.
  - Some indices did *better* with higher dimensionality, so high dimension alone is not the main risk.
- **Simpson, Campello & Stojanovski (2025)** benchmarked 26 indices on 16,177 datasets and 8 algorithms, including HDBSCAN* ([arXiv:2511.05983](https://arxiv.org/abs/2511.05983), §6, Table 10):
  - Silhouette, WB, VRC (= CH), Wemmert–Gancarski, DBCV and Point-Biserial were the best overall. DB was "intermediate to low" everywhere.
  - For HDBSCAN* partitions, the top-3 recommended indices were Silhouette, Point-Biserial and Wemmert–Gancarski. DBCV was recommended for noise and high-dimensional data, but it dropped on spectral-clustering partitions.
  - Their main finding: the choice of clustering algorithm affected index performance more than dataset properties, so "an index should not be recommended over others without considering the nature of the clustering problem".
- **DBCV (Moulavi et al., SDM 2014)** scores density-connected, arbitrarily shaped clusters on a scale from −1 to +1 ([DOI 10.1137/1.9781611973440.96](https://doi.org/10.1137/1.9781611973440.96)).
  - The `hdbscan` library's `relative_validity_` is a faster approximation that uses a different spanning tree. The docs say it "may only be used to compare results across different choices of hyper-parameters" ([hdbscan API](https://hdbscan.readthedocs.io/en/latest/api.html)). `validity_index()` computes the full index.
- **Noise points.** HDBSCAN leaves some points unassigned. Scoring only the assigned points rewards a run that discards its hard cases. Report the noise share next to every index. *(Our inference; we found no paper that quantifies this for text queries.)*
- **High dimensions.** As dimensionality grows, nearest and farthest distances can converge under broad conditions ([Beyer et al. 1999, DOI 10.1007/3-540-49257-7_15](https://doi.org/10.1007/3-540-49257-7_15)). This is one reason to compute indices with cosine distance on the embedding actually clustered, not on a 2-D projection. How much our embeddings suffer from this is *(unverified)*.

### 2. Stability (does the partition reproduce?)

- **Ben-Hur, Elisseeff & Guyon (PSB 2002)** perturb the data by subsampling, re-cluster, and look at the *distribution* of pairwise similarities between the resulting clusterings. The method works with any algorithm and "can also detect the lack of structure in data" ([PubMed 11928511](https://pubmed.ncbi.nlm.nih.gov/11928511/), [PDF](https://psb.stanford.edu/psb-online/proceedings/psb02/benhur.pdf)).
- **Lange, Roth, Braun & Buhmann (2004)** treat stability as the risk of a classifier, trained on one sample's cluster labels, disagreeing with clustering on a second sample. They pick k by minimising that risk ([DOI 10.1162/089976604773717621](https://doi.org/10.1162/089976604773717621)).
- **von Luxburg (2010)** is the caution ([arXiv:1007.1075](https://arxiv.org/abs/1007.1075)):
  - "Solutions that are completely instable should not be considered at all." But when several solutions are stable, the most stable is not necessarily the best.
  - For k-means, too many clusters tends to be unstable. Too few can be either stable or unstable.
  - Stability-based selection "breaks down" when the clusters do not fit the algorithm's shape assumptions (§5).
- **Per-cluster stability (Hennig 2007, `fpc::clusterboot`).** Each original cluster is matched to its most similar cluster in each bootstrap run, and the mean Jaccard is its stability ([Hennig PDF](https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf), [clusterboot docs](https://rdrr.io/cran/fpc/man/clusterboot.html)). The docs' reading of the mean Jaccard:
  - ≤ 0.5: "dissolved".
  - Below 0.6: do not trust.
  - 0.6–0.75: a pattern, but membership doubtful.
  - ≥ 0.75: valid and stable.
  - ≥ 0.85: highly stable.
  - The docs also warn that "clusters obtained by very inflexible clustering methods may be stable but not valid."
- **Comparing two partitions.** Use chance-adjusted scores. NMI "will tend to increase as the number of different labels (clusters) increases". AMI is near 0 for random labels, and ARI is advised "for smaller sample sizes or larger number of clusters" ([scikit-learn](https://scikit-learn.org/stable/modules/clustering.html); [Vinh, Epps & Bailey, JMLR 2010](https://www.jmlr.org/papers/volume11/vinh10a/vinh10a.pdf)).
- **Across time windows.** MONIC tracks whether a cluster survives, splits, is absorbed, disappears or newly emerges between time periods ([Spiliopoulou et al., KDD 2006](https://dl.acm.org/doi/10.1145/1150402.1150491), [PDF](https://kbs.uni-hannover.de/~ntoutsi/papers/06.KDD.pdf)). A category that only exists in one week, for example one agent's burst, is not a stable category.

### 3. Human and LLM judgement

- **Intrusion tests.** Chang et al. (NeurIPS 2009) introduced word intrusion and topic intrusion. They found "topic models which perform better on held-out likelihood may infer less semantically meaningful topics" ([NeurIPS](https://papers.nips.cc/paper/3700-reading-tea-leaves-how-humans-interpret-topic-models)). For clusters of queries, the analogue is to show k queries from one cluster plus one from another and ask which is the odd one out *(our adaptation)*.
- **Automated coherence is not a human proxy.** Hoyle et al. (NeurIPS 2021) compared NPMI-style coherence with human ratings and word intrusion on classical and neural topic models. "Automated evaluations declare a winning model when corresponding human evaluations do not" ([arXiv:2107.02173](https://arxiv.org/abs/2107.02173)). Coherence metrics are also built on word co-occurrence, which fits our short, symbol-heavy queries poorly *(our inference)*.
- **LLM as judge.** Stammbach et al. (EMNLP 2023) found LLM ratings correlate with human judgements more strongly than existing automated metrics. But "LLMs correlate better with coherence ratings of word sets than on a word intrusion task" ([arXiv:2305.12152](https://arxiv.org/abs/2305.12152)). They also found that coherent topic words "do not necessarily imply an optimal categorization", and picked the number of topics by the purity of LLM-assigned labels instead.
  - An LLM that both names the clusters and judges them is grading its own work. Validate it against humans first, as in [../statistics/judgment-reliability-and-llm-assessors.md](../statistics/judgment-reliability-and-llm-assessors.md).
- **Agreement on assignment.** Cohen's κ (2 raters), Fleiss' κ (more) or Krippendorff's α (any number of raters, missing data). Krippendorff's convention: rely on α ≥ 0.800, draw tentative conclusions from 0.667–0.800, and discard below 0.667 ([Krippendorff 2004, PDF](http://faculty.washington.edu/jwilker/559/Krippendorf.pdf); thresholds via [Wikipedia](https://en.wikipedia.org/wiki/Krippendorff's_alpha); exact page *(unverified)*).

### 4. Usefulness (do categories behave differently?)

- A category is worth a separate benchmark track only if engines behave differently on it. The README already requires per-track reporting because query types rank systems differently ([../README.md](../README.md) §2; [../lean-benchmarks/legendre-leaderboard.md](../lean-benchmarks/legendre-leaderboard.md)).
- **Kang & Kim (SIGIR 2003)** classified queries as topic-relevance vs. homepage-finding and used different retrieval evidence for each ([ACM DL](https://dl.acm.org/doi/10.1145/860435.860449)). Details are from search summaries only *(unverified)*.
- **The RIA workshop (Harman & Buckley 2009)** ran a cross-system failure analysis on 45 TREC topics. Systems retrieved different documents but tended to fail for the *same* reasons, such as wrong query understanding and missed synonyms ([DOI 10.1007/s10791-009-9101-4](https://doi.org/10.1007/s10791-009-9101-4); via search summary, *(unverified)* against the full text). Grouping queries by failure cause therefore separates systems less than one might hope. We should test whether our categories actually separate the engines.

## Evaluation

This is a synthesis note, so it reports no new experiments. The key numbers from the literature:

- **Noise and overlap.** In Arbelaitz et al., 10% noise cut index success to about a third.
- **Per-cluster stability.** clusterboot reads a mean Jaccard of 0.75 or more as stable.
- **Label agreement.** Krippendorff's convention puts the tentative floor at α ≥ 0.667.
- **2-D embeddings distort neighbourhoods.** Chari & Pachter found an average neighbour Jaccard distance "consistently above 0.7" between 2-D t-SNE/UMAP and the ambient space ([PLOS Comp Bio 2023](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1011288)).

## Relevance to lean-explore-bench

The thresholds below are **our design choices**, anchored where possible to the sources above.

**A. Internal indices, used for choosing between runs, not for pass/fail.**
- For every candidate run (embedding × UMAP-before-clustering on/off × `min_cluster_size`), report:
  - the noise share and the number of clusters;
  - silhouette (cosine, assigned points only);
  - DBCV via `validity_index()`;
  - CH as a secondary index.
- Skip DB, since Simpson et al. rank it low.
- Reject any run whose noise share exceeds 40%, however good its indices look (our cap).
- Null check: rerun on embeddings with each dimension permuted independently across queries. The real silhouette and DBCV must clearly beat the null, in the spirit of Ben-Hur's lack-of-structure test.

**B. Stability.**
- Run 50 bootstrap resamples (or 80% subsamples) × 5 seeds.
- Report median ARI and AMI between runs, computed on points assigned in both.
- Report per-cluster Hennig Jaccard. A cluster can become a category only if its Jaccard is ≥ 0.75. Clusters between 0.6 and 0.75 go to human review; clusters below 0.6 are merged or dropped.
- Time split: fit on the earlier half of the log and assign the later half. Report MONIC-style survive, split, absorb and emerge counts.
- A category must appear in at least 2 disjoint weeks. This matches the "≥ 2 UTC days" floor in the taxonomy note; the stricter rule is ours.
- Report stability separately for human and agent traffic ([query-logs-agent-vs-human-queries.md](query-logs-agent-vs-human-queries.md)).

**C. Human checks (all on the server, 2 Lean-literate annotators).**
- **Intrusion.** For each candidate category, run 10 items of 5 in-cluster queries plus 1 intruder from the nearest other cluster. Target at least 70% detection per category (ours). Chance is 1/6.
- **Assignment agreement.** Both annotators independently assign a stratified sample of 15 queries per category (for example, about 300 queries for 20 categories), including an "Other/none" option.
  - Report Krippendorff α overall and per category, with bootstrap CIs.
  - The overall α must be ≥ 0.667. A category whose own agreement is below 0.6 is redefined or merged.
- **LLM labeller.** Score it on the same set against each human. Use it at scale only if its agreement is within about 0.1 of the human–human α (our margin).

**D. Usefulness.**
- On a pilot of about 30 real or synthetic queries per category, compare across categories:
  - the zero-result rate and median result count from logs;
  - each engine's nDCG@10.
- Report Kendall τ between per-category engine rankings. Merge two categories if they show the same engine ranking (τ ≥ 0.9, the convention noted in the judgment note) and similar log behaviour.
- Also report AMI between clusters and the rule-based strata (query form: NL / name / type pattern / proof state). An AMI near 1 means the clusters only rediscover the rules. An AMI near 0 needs an explanation.

**E. Plots.** Internal plots may show query text. Public plots show aggregates only.
- **Internal only:**
  - UMAP at 3 settings of `n_neighbors` × 3 seeds, to reflect Wattenberg et al.'s warnings: "hyperparameters really matter", cluster sizes and between-cluster distances "might not mean anything", and noise can look clustered ([Distill 2016](https://distill.pub/2016/misread-tsne/)). The UMAP docs add "false tears" and imperfect density preservation ([UMAP docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)).
  - Never select clusters or read distances from the 2-D plot.
- **Public, aggregates only, subject to the minimum counts in [query-logs-privacy-and-release.md](query-logs-privacy-and-release.md):**
  - a cluster-size bar chart with the noise share;
  - a heatmap of per-cluster stability (Jaccard);
  - a contingency table of rule strata × clusters;
  - per-cluster distributions of query length, token class and agent share;
  - a dendrogram of cluster centroids;
  - per-category engine metrics.
  - No scatter plots of individual queries, and no example queries unless they are synthetic.

## Open questions

- Do the index rankings in Simpson et al. transfer to very short, mixed-script text embeddings? None of the studies above used query logs.
- How should one near-duplicate agent loop be weighted? It can create a very dense, very stable, but meaningless cluster. Deduplicate before computing stability?
- Is 15 queries per category enough for per-category α to be informative? The CIs will be wide; check them after the first round.

## Sources

- Arbelaitz et al. 2013, Pattern Recognition 46: [DOI 10.1016/j.patcog.2012.07.021](https://doi.org/10.1016/j.patcog.2012.07.021) (full text read)
- Simpson, Campello & Stojanovski 2025: [arXiv:2511.05983](https://arxiv.org/abs/2511.05983), DOI 10.1002/sam.70061
- Moulavi et al. 2014 (DBCV): [DOI 10.1137/1.9781611973440.96](https://doi.org/10.1137/1.9781611973440.96); [hdbscan API docs](https://hdbscan.readthedocs.io/en/latest/api.html)
- scikit-learn clustering evaluation: [docs](https://scikit-learn.org/stable/modules/clustering.html); Vinh, Epps & Bailey 2010: [JMLR](https://www.jmlr.org/papers/volume11/vinh10a/vinh10a.pdf)
- Beyer et al. 1999: [DOI 10.1007/3-540-49257-7_15](https://doi.org/10.1007/3-540-49257-7_15) (not re-read; general claim)
- Ben-Hur, Elisseeff & Guyon 2002: [PSB PDF](https://psb.stanford.edu/psb-online/proceedings/psb02/benhur.pdf) (abstract only)
- Lange et al. 2004: [DOI 10.1162/089976604773717621](https://doi.org/10.1162/089976604773717621) (abstract only)
- von Luxburg 2010: [arXiv:1007.1075](https://arxiv.org/abs/1007.1075), DOI 10.1561/2200000008
- Hennig 2007: [PDF](https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf); [clusterboot docs](https://rdrr.io/cran/fpc/man/clusterboot.html)
- Spiliopoulou et al. 2006 (MONIC): [DOI 10.1145/1150402.1150491](https://dl.acm.org/doi/10.1145/1150402.1150491)
- Chang et al. 2009: [NeurIPS](https://papers.nips.cc/paper/3700-reading-tea-leaves-how-humans-interpret-topic-models)
- Hoyle et al. 2021: [arXiv:2107.02173](https://arxiv.org/abs/2107.02173); Stammbach et al. 2023: [arXiv:2305.12152](https://arxiv.org/abs/2305.12152)
- Krippendorff 2004: [PDF](http://faculty.washington.edu/jwilker/559/Krippendorf.pdf) (thresholds via secondary source)
- Kang & Kim 2003: [DOI 10.1145/860435.860449](https://dl.acm.org/doi/10.1145/860435.860449) (unverified); Harman & Buckley 2009: [DOI 10.1007/s10791-009-9101-4](https://doi.org/10.1007/s10791-009-9101-4) (via summary)
- Wattenberg, Viégas & Johnson 2016: [Distill](https://distill.pub/2016/misread-tsne/); Chari & Pachter 2023: [DOI 10.1371/journal.pcbi.1011288](https://doi.org/10.1371/journal.pcbi.1011288); [UMAP clustering docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)
