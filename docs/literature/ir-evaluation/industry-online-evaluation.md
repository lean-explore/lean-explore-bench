# Industry search evaluation: offline vs online, A/B tests, interleaving, clicks, latency

- **Kind:** paper cluster (industry case studies + online evaluation methods)
- **Links:** see Sources
- **Authors / org, date:** Facebook (2020), Airbnb (2018, 2025), Amazon (2019), Google (2009), Cornell, Yahoo! and Microsoft (2005, 2012)
- **Status:** published papers and reports.

## What it is

This note covers how production search teams decide whether a change is better. The common pattern is fast **offline metrics** used as a filter, followed by **online controlled experiments** as the arbiter, with known gaps between the two.

## Evidence

- **Facebook embedding-based retrieval (EBR)** ([arXiv:2006.11632](https://arxiv.org/abs/2006.11632)).
  - The end goal is "quality improvement end to end through online A/B test". Offline metrics exist "to quickly evaluate model quality before online experiments and isolate problems from complicated online experiment setup".
  - Offline evaluation: **recall@K over 10,000 sampled search sessions**, where the targets are clicked results or human-rated relevant documents, using exact KNN over the whole index.
  - The authors also deployed "several configs of the ANN algorithms and parameters online" to measure the real performance impact.
  - Precision was controlled by a **human-rating feedback loop**: newly retrieved EBR results were sent to raters, and the ratings were used to retrain a relevance filter.
  - Offline gains did not always transfer online, as the quantisation example shows: a model with better exact-kNN recall lost that advantage after quantisation, so "the actual benefit diminished when serving it online" ([arXiv:2006.11632](https://arxiv.org/abs/2006.11632), §6).
- **Airbnb, deep learning for search** ([arXiv:1810.09591](https://arxiv.org/abs/1810.09591)).
  - The principal offline metric was NDCG. The online metric was bookings in A/B tests.
  - Several documented gaps between the two:
    - Hand-crafted feature noise gave "∼1% in offline NDCG. But we failed to get any statistically significant improvement in online performance".
    - A multi-task model "increased long views by a large margin. But bookings remained neutral".
    - Single-feature ablations produced differences that "resembled the typical noise in offline metrics observed anyway while retraining models".
- **Airbnb, interleaving and counterfactual evaluation (KDD 2025).** A/B tests on conversion metrics are slow to reach power. Offline evaluation "often lack[s] accuracy". Interleaving and counterfactual methods increased experiment sensitivity "by a factor of up to 100" and are used to pick candidates for A/B tests ([arXiv:2508.00751](https://arxiv.org/abs/2508.00751)).
- **Amazon semantic product search.** Offline: Recall@100 and MAP (+4.7% and +14.5% over baselines). Online: three "match set augmentation" A/B experiments, in which conversion rate and revenue "statistically significantly increased". Irrelevant semantic matches required added "guard rails" to meet the precision bar ([arXiv:1907.00937](https://arxiv.org/abs/1907.00937)).
- **Interleaving.** Chapelle, Joachims, Radlinski & Yue (TOIS 2012) validate interleaving against manual judgments and observational click metrics, estimate its statistical efficiency, and learn click credit-assignment functions that increase sensitivity ([ACM](https://dl.acm.org/doi/10.1145/2094072.2094078); [PDF](https://www.cs.cornell.edu/~tj/publications/chapelle_etal_12a.pdf)).
- **Clicks are biased.** Eye-tracking studies show clicks are "informative but biased" by position. Clicks do not work as absolute relevance judgments, but "relative preferences derived from clicks are reasonably accurate on average" ([Joachims et al., SIGIR 2005](https://www.cs.cornell.edu/people/tj/publications/joachims_etal_05a.pdf); claims via search summary).
- **Latency costs usage.** Google's injected-delay experiments found that raising latency from 100 to 400 ms "reduces the daily number of searches per user by 0.2% to 0.6%". The effect grew with exposure: 0.22% fewer searches in weeks 1–3 versus 0.36% in weeks 4–6 at 200 ms. It also persisted after the delay was removed ([Brutlag 2009, PDF](https://services.google.com/fh/files/blogs/google_delayexp.pdf); figures via search summary). ColBERT's introduction likewise frames 100 ms increases as costly ([arXiv:2004.12832](https://arxiv.org/abs/2004.12832)).
- **Online-only objective tuning.** Twitter/X set ranking weights and boost values by A/B tests on platform metrics (see [twitter-the-algorithm.md](twitter-the-algorithm.md)).

## Relevance to lean-explore-bench

- **The benchmark plays the offline-filter role.** Industry evidence (Airbnb, Facebook) says offline gains of around 1% are often noise. We should report **run-to-run variance**, for example across embedding re-indexing, LLM sampling seeds or API nondeterminism. We should treat differences within that noise band as ties.
- **Human-in-the-loop pool growth.** Borrow Facebook's loop: when a new engine is added, send its unjudged top-k results to Lean-expert raters, so the qrels grow with the engines evaluated.
- **Latency as a first-class metric.** Measure it end to end: client-observed p50/p95 from a fixed location for hosted APIs, and server-side time for self-hosted engines. Brutlag shows latency affects usage. For agent use via MCP, latency multiplies across many tool calls (reasoning, not from literature).
- **An online arm (optional, future).** LeanExplore has a website and MCP server, so interleaving (team-draft) between engine variants on logged traffic is the sensitive online method. Any click-derived labels must be debiased for position (Joachims 2005) before being folded into qrels.
- **Recall-oriented and precision-oriented metrics are both needed.** Amazon and Facebook show that semantic retrieval raises recall but introduces irrelevant matches. Report precision-oriented metrics (nDCG@10, P@5) alongside recall so that engines are not rewarded for spraying near-misses.

## Open questions


## Sources

- https://arxiv.org/abs/2006.11632 (Facebook EBR)
- https://arxiv.org/abs/1810.09591 (Airbnb DL) ; https://arxiv.org/abs/2508.00751 (Airbnb interleaving, KDD 2025)
- https://arxiv.org/abs/1907.00937 (Amazon)
- https://dl.acm.org/doi/10.1145/2094072.2094078 (Chapelle et al. 2012)
- https://www.cs.cornell.edu/people/tj/publications/joachims_etal_05a.pdf (Joachims et al. 2005)
- https://services.google.com/fh/files/blogs/google_delayexp.pdf (Brutlag 2009)
- https://arxiv.org/abs/2004.12832 (ColBERT)
