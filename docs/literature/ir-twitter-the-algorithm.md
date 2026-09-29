# Twitter/X open-sourced ranking and search code (the-algorithm, the-algorithm-ml, x-algorithm)

- **Kind:** search engine / recommender (production code release)
- **Links:**
  - 2023 release: https://github.com/twitter/the-algorithm (AGPL-3.0) and https://github.com/twitter/the-algorithm-ml
  - 2026 release: https://github.com/xai-org/x-algorithm (Apache-2.0)
  - Earlybird search index: https://github.com/twitter/the-algorithm/tree/main/src/java/com/twitter/search
  - Earlybird paper (Busch et al., ICDE 2012), as linked from the repo: http://notes.stephenholiday.com/Earlybird.pdf
  - Engineering blog (2023): https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm (returned HTTP 403 to our fetcher; figures below come from secondary sources)
- **Authors / org, date:** Twitter (March 2023); xAI/X (first published January 2026, still being updated).
- **Status:** `twitter/the-algorithm` was last pushed 2025-09-08 and has about 74k stars. `xai-org/x-algorithm` was created 2026-01-19, was last pushed 2026-09-26 and has about 33k stars (checked with `gh api` on 2026-09-28). Neither repo ships a top-level build. The 2023 README says Bazel BUILD files exist "for most components, but not a top-level BUILD or WORKSPACE file".

## What it is

This is the serving and ranking code behind X's For You timeline, notifications and (2023 only) the Earlybird tweet search index. The 2023 code follows a classic funnel: candidate sources, then a light ranker, then a heavy ranker, then filters and mixing. Earlybird is a Lucene-based real-time inverted index, and it both answers text search and serves as the in-network candidate source ([search README](https://github.com/twitter/the-algorithm/blob/main/src/java/com/twitter/search/README.md)). The 2026 repo replaces this stack with Phoenix, a two-tower retrieval model plus a transformer ranker, and it contains no text-search component ([x-algorithm README](https://github.com/xai-org/x-algorithm)).

## How it works (context only)

- **Earlybird search.** The index is split into realtime (about 7 days), protected and archive clusters. Each cluster is partitioned, and root services scatter/gather requests across partitions. The superroot queries the archive only "if realtime and protected clusters don't return enough results" ([earlybird_root README](https://github.com/twitter/the-algorithm/blob/main/src/java/com/twitter/search/earlybird_root/README.md)).
- **Earlybird relevance scoring.** `LinearScoringFunction.java` computes a weighted linear sum of the Lucene text score and static and realtime features. Examples are reputation, a text-quality score, log2 retweet/fav/reply counts, `hasUrl` and `isReply`. Weights come from request parameters, and the function emits a per-feature *explanation* of the score ([source](https://github.com/twitter/the-algorithm/blob/main/src/java/com/twitter/search/earlybird/search/relevance/scoring/LinearScoringFunction.java)).
- **Heavy ranker (2023).** A parallel MaskNet predicts about 10 engagement probabilities. The final score is `sum_i w_i * p_i`, and the README lists the weights as of 2023-04-05 (for example reply 13.5, report -369.0) ([recap README](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)).

## Evaluation and experimentation infrastructure the code reveals

The repos contain **no offline relevance benchmark for search**: no judged query sets, no nDCG/MRR harness and no reported search-quality numbers. What they do show:

1. **Cascade-fidelity metrics for the light ranker (notifications).** `pushservice/.../libs/light_ranking_metrics.py` scores the light ranker *against the heavy ranker's output*, not against human labels ([source](https://github.com/twitter/the-algorithm/blob/main/pushservice/src/main/python/models/libs/light_ranking_metrics.py)):
   - `recall_at_nk(labels, predictions, n, k)`: the fraction of the heavy ranker's top-K that appears in the light ranker's top-N. It can be weighted, and it is logged as `group_recall_unweighted_at_L{n}_at_H{k}`.
   - `cgr_at_nk`: the cumulative gain ratio of the light ranker's top-N compared with the ideal ordering.
   - `score_loss_at_n`: the heavy-ranker label of the best item overall minus the best item within the light top-N.

   This is the standard way to evaluate an early stage of a multi-stage pipeline: measure how much of what the later stage would pick survives the cut.
2. **Calibration-style metrics for engagement models.** `the-algorithm-ml/metrics/rce.py` implements **RCE (relative cross entropy)**. RCE is the model's binary cross-entropy relative to a "straw man" baseline, alongside AUROC. It also implements NRCE, where predictions are normalised to the label mean ([source](https://github.com/twitter/the-algorithm-ml/blob/main/metrics/rce.py)). These metrics evaluate pCTR-style predictors, not rankings.
3. **ANN recall-vs-latency harness.** `ann/src/main/scala/com/twitter/ann/experimental/Runner.scala` builds a brute-force index as ground truth. It then sweeps HNSW `efSearch` (with `efConstruction = 200`) and Annoy search-node counts, recording `(time, recall)` per setting, where recall = |ANN top-k ∩ exact top-k| / k ([source](https://github.com/twitter/the-algorithm/blob/main/ann/src/main/scala/com/twitter/ann/experimental/Runner.scala)).
4. **Online experimentation hooks.** Examples:
   - The product-mixer framework ships an `experiments/metrics` package that templates metric definitions for experiments ([MetricTemplates.scala](https://github.com/twitter/the-algorithm/blob/main/product-mixer/component-library/src/main/scala/com/twitter/product_mixer/component_library/experiments/metrics/MetricTemplates.scala)).
   - cr-mixer has `TopLevelDdgMetricsMetadata.scala`. That DDG is Twitter's A/B framework is our inference (unverified).
   - Pushservice has `MlModelsHoldbackExperimentPredicate.scala`, which holds users back from ML models.
   - Earlybird has a `EarlybirdDarkProxy` that sends *dark* (shadow) traffic with its own 800 ms timeouts ([source](https://github.com/twitter/the-algorithm/blob/main/src/java/com/twitter/search/earlybird/EarlybirdDarkProxy.java)).
   - Earlybird root has `ScatterGatherWithExperimentRedirectsService` for routing experiment traffic (file listing only).
5. **x-algorithm (2026) experimentation disclosures.** The README says experiments run "on a small percentage of timeline traffic". Experiments at 10% or more of traffic are meant to be visible in the repo, and cron scripts sync production parameter defaults into `home-mixer/params/param.rs`. An `InventoryHoldoutFilter` removes "a configured percentage of posts, chosen deterministically per post and viewer", which is a holdout for measurement ([README](https://github.com/xai-org/x-algorithm)). [`docs/BIDIRECTIONAL_BOOST_CHANGE.md`](https://github.com/xai-org/x-algorithm/blob/main/docs/BIDIRECTIONAL_BOOST_CHANGE.md) walks through a real multi-arm A/B test:
   - Boost values 0/5/10/15/20 were assigned at random.
   - A broad launch at 20 followed three days later.
   - Weeks later the value was reset to 15 after experiment results and qualitative user feedback.
6. **Training metrics only for Phoenix.** The Phoenix trainer writes per-step `metrics.jsonl` including loss, and the shipped path is described as "an offline verification harness" ([TRAINING.md](https://github.com/xai-org/x-algorithm/blob/main/phoenix/TRAINING.md)). No retrieval-quality benchmark is published.
7. **Latency and scale (secondary source).** The 2023 blog reportedly states about 1,500 candidates per request, a ~48M-parameter heavy ranker, about 1.5 s for the full pipeline and 5 billion runs per day (quoted via search-result summaries of the blog; the primary page returned 403) (unverified against primary).
8. **Objective tuning is online.** The heavy-ranker weights were "originally set so that ... each weighted engagement probability contributes a near-equal amount", then "periodically adjusted ... to optimize for platform metrics" ([recap README](https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md)). In other words, the final ranking objective is chosen by online metrics, not by an offline relevance set.

## Relevance to lean-explore-bench

- **Cascade recall@N-vs-K.** If LeanExplore (or any engine we test) has a candidate stage (BM25 top-N plus vector top-N) followed by a reranker, we should report the retrieval stage's recall of the final top-K and of gold items at the candidate depth, separately from end-to-end nDCG. This localises failures to "never retrieved" versus "retrieved but misranked".
- **Exact-vs-ANN recall.** The ANN harness pattern applies to engines backed by FAISS or HNSW: report ANN recall against brute-force at the operating point, so approximate-search loss is not confused with embedding quality.
- **Score explanations.** Earlybird's per-feature score explanation is a useful requirement for benchmark diagnostics. If an engine can emit component scores (lexical, semantic, PageRank), we can run per-component ablations.
- **What it leaves out.** Twitter's evaluation is engagement-driven, with online A/B tests, holdouts and dark traffic, and it has no public judged relevance set. A Lean search benchmark has no click logs, so this repo is a source of *pipeline-stage* metrics and experimentation hygiene, not of relevance-judgment methodology.

## Open questions

- Did Twitter search (Top/Latest) ever have an offline judged set? Nothing in the repo shows one.
- The primary blog text could not be fetched, so its numbers are unverified.

## Sources

- https://github.com/twitter/the-algorithm (README, `src/java/com/twitter/search/**`, `pushservice/src/main/python/models/libs/light_ranking_metrics.py`, `ann/.../experimental/Runner.scala`, `product-mixer/.../experiments/metrics/`)
- https://github.com/twitter/the-algorithm/blob/main/src/python/twitter/deepbird/projects/timelines/scripts/models/earlybird/README.md (the light ranker is logistic regression and "last trained several years ago")
- https://github.com/twitter/the-algorithm-ml (`projects/home/recap/README.md`, `metrics/rce.py`)
- https://github.com/xai-org/x-algorithm (README, `phoenix/README.md`, `phoenix/TRAINING.md`, `docs/BIDIRECTIONAL_BOOST_CHANGE.md`)
- Blog figures via search summary: https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm (unverified; 403)
