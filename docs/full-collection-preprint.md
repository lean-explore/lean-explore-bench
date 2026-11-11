# LeanExplore retrieval: full-collection evaluation and reranker correction

Working preprint, 11 November 2026. Retrospective local evaluation. Independent relevance review remains pending.

## Abstract

We evaluate Lean declaration search on all prepared query collections available for this campaign: 38,566 source records corresponding to 33,075 distinct query-and-package requests. The collection combines usage logs, public discussion-derived requests, expert-written reference queries, premise-retrieval problems and earlier synthetic development material. Every distinct request received a final execution record, with 0 request errors. On MathlibQR, the frozen engine obtains Success@10 57.29% and nDCG@10 0.3961. Its 25-candidate pool imposes a known-target Success@10 ceiling of 62.68% even with perfect ordering. A code audit also finds that the pinned reranker adapter differs from the model card in its answer tokens and conversation format. We test compatible chat-based yes/no scoring at two context limits on all 3,215 target-bearing requests, using unchanged candidate pools. We also replay the corrected production client at its unchanged 256-token limit on all 33,075 distinct requests. Its unchanged score mixture reaches MathlibQR Success@10 60.57% and nDCG@10 0.4214; corrected neural-only ranking reaches nDCG@10 0.4799. The results support separate work on candidate selection, model integration and annotation quality. They do not provide a single accuracy estimate for unlabelled usage traffic.

## What we found

The reranker integration had a scoring-contract error. It read true/false answer logits from a flat input, while the model card specifies yes/no scoring with conversation wrapping. On MathlibQR, correcting that integration improves recorded target recovery on the same candidate pools. This supports fixing and testing the model interface before judging the model's usefulness. Because the experiment changes the answer tokens and wrapper together, it does not tell us which change contributes how much.

Candidate coverage is a separate bottleneck. Even perfect ordering of the original 25-candidate pools could recover only 62.68% of MathlibQR targets in the top ten. The corrected neural ranking already approaches that ceiling. A stronger reranker cannot retrieve a declaration that never reaches its input; further gains at that cutoff require better candidates, larger pools or both. The experiment identifies this constraint but does not yet establish which selection change works best.

The final score mixture needs new calibration after the integration fix. The corrected neural ranking recovers more first-position MathlibQR targets than the unchanged mixture on five of the six query styles, while nickname queries benefit from the mixture. The extra signals are therefore worth testing individually. These results support a new calibration study with a fresh test split; they do not justify removing every supporting signal or choosing new serving weights from this exposed collection.

A longer input budget has task-dependent effects. Moving the corrected adapter from 256 to 512 tokens changes MathlibQR recovery only slightly. The premise and discussion tasks show different responses, and their labels and uncertainty need separate interpretation. Truncation counts identify where content is lost, but they do not show that every truncated pair would improve with more context. Longer inputs should be evaluated together with candidate representation and uncontended runtime costs.

Broader execution gives us better coverage of system behavior, while relevance confidence still depends on the labels. Reference targets support target-recovery claims. Reply-link targets are useful proxies that still need review. Usage logs show what was executed and how rankings changed, but cannot establish whether users received useful answers. Completing the full collection resolves the coverage gap; expert judgments and a fresh evaluation split are the next requirements for stronger relevance claims.

Sections 2 through 4 explain the inputs and method. Section 5 gives the evidence for these findings, and section 7 turns them into proposed experiments. The linked aggregate reports retain the detailed category tables.

## 1. Objective and scope

The earlier work established a diagnostic pilot and the evaluation tooling. That was insufficient for the intended coverage across hundreds or thousands of queries. This campaign expands execution to every prepared query collection and every available query form. It asks four questions: how much material is covered; where recorded targets disappear; how final ranking changes a fixed pool; and how these effects vary across tasks and query forms.

The task is retrieval of ranked Lean declarations. Proof completion, generated explanations, user satisfaction and production serving latency are different outcomes. FATE-H and MathlibMPR therefore remain separate diagnostic tasks. No search result is treated as a verified proof.

## 2. Data and provenance

| Collection | Source records or variants | Distinct requests |
|---|---|---|
| Discussion-derived queries | 2,079 | 2,078 |
| MathlibQR | 946 | 945 |
| MathlibMPR | 138 | 138 |
| FATE-H | 200 | 200 |
| Synthetic discussion queries | 28 | 28 |
| Development pilot | 20 | 20 |
| Historical test requests | 30 | 30 |
| Candidate-selection pilot | 12 | 12 |
| Earlier calibration queries | 10 | 10 |
| Usage logs | 35,103 | 29,628 |

MathlibQR supplies 200 target declarations and up to six query styles. MathlibMPR supplies 69 problems with alternative sets of premises; we evaluate both natural and formal statements. FATE-H supplies 100 problems, also evaluated in informal and formal form. These inputs come from the pinned [LeanSearch-v2 benchmark repository](https://github.com/frenzymath/LeanSearch-v2/tree/94f4888cbaf9f4322535755f86cbac690ec18080/benchmark). Their original task definitions and label types remain separate.

The discussion collection contains all 2,079 previously extracted candidate topics. The extraction selected short threads with a later declaration link from another author. The opening message is the query; a reply link is a proposed target. This selects for answered, link-bearing discussions and does not represent all discussion requests. The underlying archive contains much more conversation material, but raw messages are not counted as additional benchmark queries. Existing synthetic reformulations are included separately with their provenance.

The usage export contains 35,103 logged events across API, MCP and web channels. It has no returned-document lists or accepted relevance judgments. We replay each distinct request and retain its event memberships, so both unique-request and event-weighted views are recoverable. We make no inference about human versus agent identity from a channel label.

### 2.1 Deduplication and categories

Deduplication uses exact query text and sorted unique package filters. It does not collapse paraphrases, mathematical equivalences, code whitespace or distinct filter settings. MathlibQR fields have surrounding whitespace stripped during import; internal whitespace remains intact. A shared execution retains all source IDs and each source's own target list. Source-record totals therefore overlap and must not be interpreted as independent observations.

| Primary form | Distinct requests |
|---|---|
| formula | 1,567 |
| keywords | 12,829 |
| mixed | 6,914 |
| name | 1,242 |
| prose | 10,523 |

Forms use explicit surface rules: identifiers, formal statements, mixed identifier/text requests, formulas and prose/keyword distinctions based on English function-word share. The original seven surface labels, intent and domain cues, source query styles and difficulty tags remain available. Unknown intent and domain are preserved. These labels are unvalidated rules, not mathematical expert annotations or the earlier first-day Gaussian-mixture cluster assignments. The complete rules and all category tables accompany the aggregate report.

### 2.2 Label types

We keep four evidence classes separate. MathlibQR has an upstream single target; MathlibMPR has upstream alternative premise sets; discussion reply links and earlier proposed targets are weak target evidence; usage logs and FATE-H have no declaration-relevance judgments in these inputs. The earlier pilot's graded AI proposals and historical human decisions remain in its own versioned package. This larger replay does not promote those proposals or discussion links into accepted human labels.

The frozen historical test request file has no target lists. Its requests are all replayed, but its separately versioned graded annotations are reported only in the assisted-v2 pilot. The full-collection report states this distinction explicitly.

## 3. Experimental pipeline

```mermaid
flowchart LR
 A[All prepared sources] --> B[Exact request deduplication]
 B --> C[Frozen schedule and input identities]
 C --> D[Lexical and dense retrieval]
 D --> E[Fusion and selection]
 E --> F[Fixed candidate pool and reranking]
 F --> G[Source-specific scoring and loss analysis]
 G --> H[Aggregate reports and review queue]
```

### 3.1 Frozen environment

The local corpus contains 408,970 canonical declaration names in the existing index bundle. Code, database and index files are hashed in an external manifest. The original corpus build history is incomplete; later Lean metadata and type-checking experiments must not be mistaken for a reconstruction of that build. Usage queries were collected after the index snapshot, so this is retrospective replay against a fixed corpus, not a reconstruction of what users saw at the time.

The recorded environment uses Python 3.12.13, PyTorch 2.9.1+cu130, Transformers 5.22.1, FAISS 1.15.1 and BM25s 0.3.16 under WSL2. The GPU is an NVIDIA GeForce RTX 5080 Laptop GPU with 16 GB of memory and driver 621.01. Reranker inference uses float16. The full installed-package snapshot is retained with the external artifacts.

The embedding and reranking models are Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B at the previously pinned local revisions. The engine uses the embedding model's query prompt, a 512-token embedding limit, a 256-token baseline reranking limit and FAISS nprobe 64. The [embedding model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) describes instruction-aware query encoding. No model weights or ranking weights were trained or tuned on this collection. The adapter protocol was corrected after an implementation audit; both context conditions are reported as exploratory comparisons.

### 3.2 Retrieval and ranking

BM25 searches raw and spaced declaration-name indexes with depth 1,000; dense retrieval searches informalizations at depth 1,000. The engine combines ranks with the sum of reciprocal lexical and dense ranks. A missing candidate receives the rank immediately after that channel's list. Selection operates on the top 500 fused candidates and adds a dependency signal. Original package filters are applied before the final 25-candidate pool.

The reranker sees a declaration name and its informalization, falling back to the name alone. The final score combines normalized neural scores, informal-text BM25, dependency counts and fuzzy name similarity. The respective weights are 1.0, 0.4, 0.2 and 1.0; the fuzzy term is gated at similarity 0.7. We retain eight diagnostic rankings: lexical, dense, fusion, selection, the pool before reranking, the current mixture, neural-only ranking and the mixture without its final dependency term. The last four use the same pool and final output filter. Earlier raw stages precede package filtering and should be read as retrieval diagnostics.

### 3.3 Execution and integrity

Each request has a stable ID and an append-only result record. The runner preserves errors and allows resume only when the input identities, settings and completed schedule prefix match. Scoring refuses incomplete schedules and changed journals. Independent checks cover source counts, category totals, filters, finite scores and retained source memberships. Raw queries, per-request scores and run manifests remain outside Git; only code and aggregate Markdown are published.

The corrected replay's original journal retained baseline timing diagnostics and an old result-order trace alongside its actual new results. A derived journal synchronizes that diagnostic result trace and labels the copied timings as baseline timings. The transformation verifies that inference scores, returned result order and per-request latency are unchanged; both the original journal and its executed source are preserved. Evaluation uses the returned results and scores.

The earlier blinded-pooling, accepted-review, metadata-normalization and cache workflows remain useful supporting tools. Their previous checks are not evidence of retrieval accuracy, a general verified Lean parser or production cache speedups. They were not used to manufacture labels for this replay.

### 3.4 Annotation, metadata and cache components

The annotation workflow pools candidates from different rankings, removes duplicate declaration IDs and hides the originating method during review. Proposed grades retain their assessor and provenance. Accepted human decisions are stored separately and can supersede a proposal without changing the recorded search output. The earlier pilot contains 759 AI proposals and four accepted human decisions; these counts do not establish human validation of the enlarged collection.

The metadata workflow normalizes already decoded declaration records at a defined boundary. Its existing checks include seven Lean theorems, 37 pinned declaration records and twelve executable fixtures. These checks concern record preservation and validation, not a proof of search correctness or a general Lean parser. The cache experiment uses two snapshots over 351 modules to check invalidation rules. Its recording builders do not measure saved model inference in production. The [earlier manuscript](preprint.md) retains those experiments and their limits.

## 4. Metrics and uncertainty

Success@k is the share of requests with at least one known target among the first k results. Success@1 therefore asks whether the first result is a recorded answer; Success@10 allows the user to inspect ten results. Recall@k measures the fraction of recorded targets recovered. nDCG@k is a score from zero to one that rewards putting recorded targets nearer the top; higher is better. It uses binary target relevance and divides the rank-discounted gain by the best possible gain for the recorded answer set. MRR records the inverse rank of the first target. For premise retrieval, recall and nDCG use the union of recorded premises, while complete-route success requires one whole recorded alternative premise set. It is not proof success. Absent target names and failed labelled requests remain in the denominator.

Unlabelled queries have unavailable relevance metrics. We report their completion, empty results, result counts and ranking changes, without equating nonempty output with usefulness. No global relevance average combines different sources or label classes. Variant-weighted estimates are accompanied by exploratory paired bootstrap intervals with 2,000 draws, grouped by upstream target/problem or source topic. These intervals are conditional on recorded labels; they do not quantify annotation error, source bias or all mathematical dependencies, and are not multiplicity-adjusted confirmatory tests.

## 5. Results

All 33,075 distinct requests finished. There were 0 request errors and 2 empty result lists. The original reranking mixture changed the first result relative to the selected pool's incoming order on 28,131 requests. The mean instrumented request time was 517.8 ms. The GPU was shared with the adapter experiment and corrected-client replay during parts of the baseline run. Timings include diagnostics, depend on query order and contention, and are unsuitable for production latency claims.

Per-request timings exclude startup, warmup and journal writes. Wall-clock throughput also includes that overhead; it is a different measurement from the reported mean request time.

| Source and label type | Success@1 | Success@10 | Recall@10 | nDCG@10 |
|---|---|---|---|---|
| MathlibQR: upstream target | 24.31% | 57.29% | 57.29% | 0.3961 |
| MathlibMPR: recorded premises | 0.00% | 26.81% | 7.65% | 0.0426 |
| Discussion queries: reply-link proxies | 6.01% | 21.07% | 15.42% | 0.1012 |

The large differences between sources are not a ranking of their difficulty on a shared scale. They differ in task, query construction, answer completeness and corpus compatibility.

### 5.1 Candidate loss limits the reranker

| First observed outcome for a MathlibQR target-query record | Count |
|---|---|
| Target name absent from the corpus | 19 |
| Target missing from lexical and dense retrieval | 93 |
| Target excluded from the 500-candidate selection | 49 |
| Target dropped before the 25-candidate reranker pool | 192 |
| Target returned below the top ten | 51 |
| Target recovered in the top ten | 542 |

The current mixture retrieves 542 recorded MathlibQR targets in the top ten. Another 51 targets are in its pool but below that cutoff. Even perfect reranking of this pool could therefore reach only 62.68% Success@10. The larger loss of 192 targets before the 25-candidate pool makes candidate selection a separate priority. Increasing the strength of the reranker alone cannot recover candidates it never receives.

### 5.2 Reranking effects depend on the task

| MathlibQR ranking | Success@1 | Success@10 | nDCG@10 |
|---|---|---|---|
| Dense retrieval | 25.37% | 54.44% | 0.3925 |
| Rank fusion | 18.50% | 51.90% | 0.3468 |
| Selected pool, before reranking | 15.01% | 52.96% | 0.3217 |
| Final score mixture | 24.31% | 57.29% | 0.3961 |
| Neural score only | 15.22% | 52.01% | 0.3186 |
| Mixture without final dependency term | 21.99% | 54.44% | 0.3678 |

The source-specific tables expose tradeoffs that a single aggregate would hide. In the frozen implementation, improvements over the selected pool do not imply uniform improvement over dense retrieval or over other task types. The premise task needs several useful declarations; returning a declaration similar to the main statement is not sufficient.

### 5.3 Model integration and context

The pinned baseline adapter reads true/false logits from a flat instruction/query/document input. The [Qwen reranker model card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) instead documents yes/no scoring after a conversation prefix and assistant suffix. The same discrepancy exists in the inspected local development checkout; production was not inspected in this campaign.

We evaluate all 3,215 target-bearing requests on their unchanged pools. The alternative adapter uses yes/no tokens and compatible chat wrapping with a custom short system instruction. Its 256-token condition changes both the answer head and wrapper, so it does not identify their separate effects. The wrapper also consumes part of that unchanged total budget. The 512-token condition changes only the total token budget relative to that alternative. Both preserve the assistant suffix during truncation. These are exploratory local conditions, not a replication of Qwen's published benchmark protocol.

#### MathlibQR: fixed-pool adapter comparison

| Condition | Success@1 | Success@10 | nDCG@10 |
|---|---|---|---|
| Original final mixture | 24.31% | 57.29% | 0.3961 |
| Original neural score only | 15.22% | 52.01% | 0.3186 |
| Selected pool, before reranking | 15.01% | 52.96% | 0.3217 |
| Corrected adapter, 256 tokens, neural only | 34.78% | 61.52% | 0.4799 |
| Corrected adapter, 256 tokens, final mixture | 26.00% | 60.57% | 0.4214 |
| Corrected adapter, 512 tokens, neural only | 35.10% | 61.73% | 0.4830 |
| Corrected adapter, 512 tokens, final mixture | 26.00% | 60.68% | 0.4220 |

#### MathlibMPR: fixed-pool adapter comparison

| Condition | Success@1 | Success@10 | nDCG@10 |
|---|---|---|---|
| Original final mixture | 0.00% | 26.81% | 0.0426 |
| Original neural score only | 4.35% | 27.54% | 0.0594 |
| Selected pool, before reranking | 2.17% | 21.74% | 0.0395 |
| Corrected adapter, 256 tokens, neural only | 2.90% | 30.43% | 0.0588 |
| Corrected adapter, 256 tokens, final mixture | 0.00% | 28.26% | 0.0447 |
| Corrected adapter, 512 tokens, neural only | 2.17% | 32.61% | 0.0695 |
| Corrected adapter, 512 tokens, final mixture | 0.00% | 29.71% | 0.0490 |

#### Discussion-derived queries: fixed-pool adapter comparison

| Condition | Success@1 | Success@10 | nDCG@10 |
|---|---|---|---|
| Original final mixture | 6.01% | 21.07% | 0.1012 |
| Original neural score only | 4.67% | 20.01% | 0.0921 |
| Selected pool, before reranking | 4.62% | 18.28% | 0.0831 |
| Corrected adapter, 256 tokens, neural only | 6.97% | 22.27% | 0.1123 |
| Corrected adapter, 256 tokens, final mixture | 6.88% | 22.51% | 0.1111 |
| Corrected adapter, 512 tokens, neural only | 8.51% | 23.62% | 0.1233 |
| Corrected adapter, 512 tokens, final mixture | 6.88% | 23.62% | 0.1159 |

On MathlibQR, correcting the adapter raises neural-only Success@1 from 15.22% to 34.78%. With the existing score mixture, Success@1 moves from 24.31% to 26.00%. The supporting score weights were kept unchanged. Their behavior under the corrected neural signal is a separate calibration problem; the old mixture does not preserve the full observed neural ranking gain.

The corrected 256-token neural ranking reaches MathlibQR Success@10 61.52%, close to this fixed pool's known-target ceiling of 62.68%. This makes candidate coverage the next constraint on that cutoff. The premise task has weaker and less certain mixture gains; the source-specific intervals below should be read separately.

Paired changes in nDCG@10 relative to the frozen current mixture:

| Source | Condition | Change | Exploratory grouped 95% interval |
|---|---|---|---|
| MathlibQR | Corrected adapter, 256 tokens, final mixture | +0.0253 | [+0.0102, +0.0414] |
| MathlibQR | Corrected adapter, 512 tokens, final mixture | +0.0259 | [+0.0108, +0.0420] |
| MathlibQR | Corrected adapter, 256 tokens, neural only | +0.0838 | [+0.0623, +0.1050] |
| MathlibQR | Corrected adapter, 512 tokens, neural only | +0.0869 | [+0.0649, +0.1092] |
| MathlibMPR | Corrected adapter, 256 tokens, final mixture | +0.0021 | [-0.0094, +0.0138] |
| MathlibMPR | Corrected adapter, 512 tokens, final mixture | +0.0064 | [-0.0048, +0.0187] |
| MathlibMPR | Corrected adapter, 256 tokens, neural only | +0.0162 | [-0.0004, +0.0337] |
| MathlibMPR | Corrected adapter, 512 tokens, neural only | +0.0269 | [+0.0089, +0.0490] |
| Discussion-derived queries | Corrected adapter, 256 tokens, final mixture | +0.0099 | [+0.0048, +0.0148] |
| Discussion-derived queries | Corrected adapter, 512 tokens, final mixture | +0.0147 | [+0.0092, +0.0199] |
| Discussion-derived queries | Corrected adapter, 256 tokens, neural only | +0.0110 | [+0.0035, +0.0187] |
| Discussion-derived queries | Corrected adapter, 512 tokens, neural only | +0.0221 | [+0.0145, +0.0299] |

The baseline truncated 33,269 of 825,391 query-document pairs (4.03%). This measures exposure to truncation, not its causal effect on correctness. Longer context can retain assumptions and candidate information, but must be tested on fixed pools with separate latency and memory measurements.

### 5.4 Corrected production client on the full collection

The isolated engine change implements yes/no scoring and chat wrapping, reserves the assistant suffix before truncation, and computes logits only for the final token. We replayed it on all 33,075 distinct requests with the engine's existing 256-token limit, candidate pools and score weights. The replay has 0 request errors and 2 empty result lists. Retrieval was reused from the frozen baseline. Its timings therefore exclude retrieval and cannot be compared with the baseline's end-to-end timings.

| Source | Baseline S@1 | Corrected S@1 | Baseline nDCG@10 | Corrected nDCG@10 |
|---|---|---|---|---|
| MathlibQR | 24.31% | 26.00% | 0.3961 | 0.4214 |
| MathlibMPR | 0.00% | 0.00% | 0.0426 | 0.0447 |
| Discussion-derived queries | 6.01% | 6.88% | 0.1012 | 0.1111 |

The change is an engine implementation fix, with regression tests for answer tokens, batching and truncation. The last-token projection is supported by the [Qwen3 implementation in Transformers](https://github.com/huggingface/transformers/blob/v4.51.3/src/transformers/models/qwen3/modeling_qwen3.py). A cached real-model CPU check found maximum absolute logit difference below 0.00001 between final-token-only and full-logit calculations on the checked inputs. The full replay evaluates the actual corrected client. It does not assume that GPU floating-point results are bit-identical to the earlier prototype. Deployment and a new independent relevance test remain separate steps.

Across all 3,215 target-bearing requests, the CUDA float16 comparison with the full-logit prototype has maximum absolute score difference 0.0078125. The first result changes on 0 neural rankings and 0 mixture rankings. Some later positions change on 44 neural rankings and 22 mixture rankings. The production-client tables and paired comparisons use its own recorded scores and rankings.

Compared with the frozen baseline, the corrected mixture changes the first result on 15,859 requests and changes some part of the order on 32,549. The visible result sets and retrieval stages are identical. A changed ranking is not itself evidence of improved relevance.

| Source | Corrected nDCG@10 change | Exploratory grouped 95% interval |
|---|---|---|
| MathlibMPR | +0.0021 | [-0.0094, +0.0138] |
| MathlibQR | +0.0253 | [+0.0102, +0.0414] |
| Discussion-derived queries | +0.0099 | [+0.0048, +0.0148] |

### 5.5 Effects by query style

| MathlibQR style | Variants | Original mixture S@1 | Corrected mixture S@1 | Corrected neural S@1 |
|---|---|---|---|---|
| Lean statement | 199 | 16.08% | 17.09% | 30.15% |
| LaTeX statement | 200 | 26.00% | 24.50% | 39.50% |
| Natural-language statement | 199 | 28.14% | 27.14% | 38.19% |
| Short description | 197 | 22.34% | 25.38% | 28.93% |
| Nickname | 128 | 35.16% | 44.53% | 41.41% |
| Special case | 23 | 4.35% | 8.70% | 17.39% |

The corrected neural ranking leads the corrected mixture on five of the six recorded styles. Nickname queries retain a higher first-result recovery under the mixture. The supporting signals should therefore be tested individually by query style before changing their weights. These descriptive slices do not identify which term causes each difference.

The styles have different target coverage: the special-case slice has only 23 variants, while the main statement styles have about 200. Absolute differences between styles can reflect their different targets as well as query form. The aggregate reports contain every available form, surface category, intent/domain cue and source-supplied category. Unlabelled slices retain operational statistics and unavailable relevance scores.

## 6. Limitations

Coverage is complete for the supplied query collections, not for all possible Lean tasks or all raw discussion messages. Exact deduplication does not remove semantic dependence. The material is already exposed and is not a fresh held-out test. Source selection, client bursts, temporal corpus mismatch and incomplete labels constrain interpretation.

Discussion links can be supporting or unsuitable answers. Missing target names do not prove that no equivalent result exists in the corpus. A result outside the recorded answer set is unjudged, not necessarily irrelevant. The rules used for category labels need human review, especially for non-English, context-dependent and mixed code/prose requests.

The adapter audit concerns the pinned local implementation. The alternative uses a custom system instruction and changes several protocol details together. Observed gains cannot be attributed to answer-token choice alone, generalized to production or used to justify training on this exposed collection.

## 7. Improvement programme

| Priority | Intervention | Evidence and next controlled check |
|---|---|---|
| 1 | Review the corrected reranker integration | The isolated engine fix and full fixed-pool replay are complete. Review serving compatibility before deployment; separate head-only and wrapper-only effects before attributing the cause. |
| 2 | Recalibrate the final score mixture | The corrected neural ranking outperforms the unchanged mixture on MathlibQR. Compare signal contributions using a new development split, preserve source-specific results and reserve a fresh test before changing serving defaults. |
| 3 | Improve candidate selection | Compare fused, dependency-boosted and channel-balanced pools at equal sizes; test 25, 50 and 100 candidates. Report targets recovered and lost, not only final ranking averages. |
| 4 | Protect mathematical context | Compare 256/512/1024-token inputs and representations containing canonical types or relevant assumptions. Keep retrieval fixed and measure memory and latency in an uncontended run. |
| 5 | Build reliable category-level judgments | Blind pooled candidates from different methods; obtain expert judgments, record uncertainty and adjudicate disagreements. Validate the reply-link proxies and audit unlabelled usage strata before claiming relevance gains. |
| 6 | Treat premise retrieval as its own task | Preserve alternative premise routes, test decomposition and iterative retrieval, then verify downstream proofs in Lean. Do not substitute single-target retrieval scores. |
| 7 | Create a fresh evaluation split | Group related mathematical families and paraphrases, check exposure, tune only on development material and reserve newly collected sources for final evaluation. |

## 8. Reproduction and supporting material

The [baseline aggregate report](benchmark-full-collection.md) and [corrected-client aggregate report](benchmark-reranker-corrected.md) contain all source/category tables. The [engine correction](https://github.com/lean-explore/lean-explore/commit/255ffc91caef71c7b77039e203ecd0a8db710c19) contains the client change and its regression tests. The [full-collection tools](../experiments/full_collection/README.md) prepare the schedule, run the local engine, reconstruct scores, locate losses and evaluate the adapter conditions. External artifacts retain raw inputs, membership maps, frozen contracts, journals and per-request scores. Publication checks reject raw data paths. The historical pilot, annotation workflow and metadata experiments remain separately versioned.

Primary reference inputs and implementation documentation: [LeanSearch-v2, pinned benchmark files](https://github.com/frenzymath/LeanSearch-v2/tree/94f4888cbaf9f4322535755f86cbac690ec18080/benchmark); [Qwen3-Reranker-0.6B model card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B); [Qwen3-Embedding-0.6B model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
