# Which artefacts of a private query-log analysis pipeline leak real queries, and how to stop them (synthesis)

- **Kind:** evaluation methodology (synthesis)
- **Links:**
  - Embedding inversion: Morris et al., "Vec2Text", EMNLP 2023 ([arXiv 2310.06816](https://arxiv.org/abs/2310.06816)); Song & Raghunathan, CCS 2020 ([arXiv 2004.00053](https://arxiv.org/abs/2004.00053)); Huang et al., transfer inversion, ACL 2024 ([arXiv 2406.10280](https://arxiv.org/abs/2406.10280)); Zhang, Morris & Shmatikov, "ZSInvert", 2025 ([arXiv 2504.00147](https://arxiv.org/abs/2504.00147))
  - Cluster summaries: Tamkin et al., "Clio", Anthropic, 2024 ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678))
  - Synthetic text leakage and DP generation: Carlini et al. 2021 ([arXiv 2012.07805](https://arxiv.org/abs/2012.07805)); Carlini et al. 2023 ([arXiv 2202.07646](https://arxiv.org/abs/2202.07646)); Meeus et al., "The Canary's Echo", ICML 2025 ([arXiv 2502.14921](https://arxiv.org/abs/2502.14921)); Yue et al., ACL 2023 ([arXiv 2210.14348](https://arxiv.org/abs/2210.14348)); Lin et al., Private Evolution, ICLR 2024 ([arXiv 2305.15560](https://arxiv.org/abs/2305.15560)); Xie et al., Aug-PE, ICML 2024 ([arXiv 2403.01749](https://arxiv.org/abs/2403.01749)); Tang et al., DP few-shot generation, ICLR 2024 ([arXiv 2309.11765](https://arxiv.org/abs/2309.11765)); Lee et al., deduplication, ACL 2022 ([arXiv 2107.06499](https://arxiv.org/abs/2107.06499))
  - Disclosure control: Griffiths et al., *Handbook on SDC for Outputs* v2.0, 2024 ([PDF](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf)); Hundepool et al., *Handbook on SDC*, 2nd ed. ([PDF](https://sdctools.github.io/HandbookSDC/Handbook-on-Statistical-Disclosure-Control.pdf)); Desai, Ritchie & Welpton, "Five Safes", 2016 ([PDF](https://www2.uwe.ac.uk/faculties/bbs/Documents/1601.pdf)); Wilson et al., DP SQL, 2019 ([arXiv 1909.01917](https://arxiv.org/abs/1909.01917)); Preen et al., SACRO/ACRO, 2025 ([arXiv 2212.02935](https://arxiv.org/abs/2212.02935)); OpenSAFELY ([docs](https://docs.opensafely.org/))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

The planned pipeline runs public code on the production server, next to the de-identified log. The steps are: dedup → rule-based features → local embeddings → clustering → local-LLM cluster labels → human review → category descriptions → LLM-generated synthetic queries per category → a published benchmark plus aggregate statistics. The Privacy Policy allows us to publish only synthetic-query benchmarks and aggregates that "cannot identify anyone or reproduce any individual query". It also rules out sending search data to external LLM APIs.

This note goes through each intermediate artefact and asks whether it can leak a real query, and what the literature says about stopping that. Release mechanisms for the queries themselves (AOL, k-user thresholds, DP query release, DP synthetic queries for training) are in [query-logs-privacy-and-release.md](query-logs-privacy-and-release.md) and are not repeated here. The taxonomy method is in [query-logs-llm-taxonomy-induction.md](query-logs-llm-taxonomy-induction.md). Embedding and clustering choices are in [query-clustering-embeddings.md](query-clustering-embeddings.md) and [query-clustering-validation-and-visualization.md](query-clustering-validation-and-visualization.md).

## How it works

### 1. Embeddings are (almost) the text

- **Vec2Text** inverts GTR and OpenAI ada-002 embeddings by repeatedly correcting a guess and re-embedding it. It recovers 92% of 32-token inputs exactly (BLEU 97.3), and 89% of full names from embedded clinical notes. The authors conclude embeddings "should be treated with the same precautions as raw data" ([arXiv 2310.06816](https://arxiv.org/abs/2310.06816), §1, §5).
- **Earlier and weaker.** Song & Raghunathan recover 50–70% of input words (F1 0.5–0.7) from sentence embeddings. They also infer attributes such as authorship from "a handful" of labelled vectors, and show membership leakage for infrequent inputs ([arXiv 2004.00053](https://arxiv.org/abs/2004.00053), abstract).
- **The attacker needs less over time.**
  - A transfer attack uses a surrogate model and needs no queries to the victim encoder ([arXiv 2406.10280](https://arxiv.org/abs/2406.10280), abstract).
  - ZSInvert needs no embedding-specific training. It exceeds 80% leakage of sensitive content on Enron for every encoder tested, and still works with σ = 0.01 Gaussian noise ([arXiv 2504.00147](https://arxiv.org/abs/2504.00147), §1).
- **Noise is not a fix.** In Vec2Text, noise at λ = 0.01 cut reconstruction to 13% of the original BLEU with a 2% retrieval loss ([arXiv 2310.06816](https://arxiv.org/abs/2310.06816), §6). ZSInvert defeats that same noise level ([arXiv 2504.00147](https://arxiv.org/abs/2504.00147), §1).
- **Our encoder is a known, local, open model**, and the pipeline code is public. That is exactly the threat model these papers assume: the attacker can query the encoder ([arXiv 2504.00147](https://arxiv.org/abs/2504.00147), §3).
- **Centroids.** No paper read here tests inversion of cluster *means*. But a centroid of a 1–3 member cluster is close to a member embedding, so we treat small-cluster centroids as per-query embeddings *(our inference, unverified)*.

### 2. Cluster labels and summaries can quote queries

- **Clio's four privacy layers** ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678), privacy-design section and App. D):
  1. per-conversation summaries told to omit private information;
  2. clusters kept only above minimum counts of *unique accounts* and conversations;
  3. cluster summaries again told to omit private details;
  4. an LLM auditor that removes any cluster with private information.
- **Measured leakage** (5,000 conversations, App. D):
  - About 10% of raw conversations contained private information (rated 1–2 on a 5-point scale).
  - After summarisation this fell to about 1.5%.
  - After cluster summarisation, "almost all clusters were rated 5, with a few instances rated 4, and none rated 3 or below".
  - The auditor scored 98% accuracy on a curated test set of 1,237 examples (App. D.1).
- **Clio does not publish its thresholds.** It explains that formal DP and k-anonymity are hard to apply to rich text, so it relies on "defense in depth". It lists two remaining risks: correlated failures across layers, and group-privacy harms ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678), privacy-design and limitations sections).
- **Access.** Only aggregate clusters leave Clio's "secure private environment", and a small number of authorised staff can see the individual records (App. F).

### 3. Synthetic queries can copy real ones

- **Memorisation is real and grows with scale.** Carlini et al. extracted hundreds of verbatim training sequences from GPT-2, including sequences that appeared in only one document ([arXiv 2012.07805](https://arxiv.org/abs/2012.07805), abstract). Memorisation grows with model capacity, duplication count and prompt context length ([arXiv 2202.07646](https://arxiv.org/abs/2202.07646), abstract).
- **Few-shot prompts leak.** LLMs "may leak or regurgitate the private examples demonstrated in the prompt" ([Tang et al.](https://arxiv.org/abs/2309.11765), abstract). This is the risk if real queries ever go into the generation prompt.
- **Synthetic data supports membership inference.** Membership inference attacks that see *only* the synthetic output still succeed against the fine-tuning data, and ordinary canaries understate the risk ([Meeus et al.](https://arxiv.org/abs/2502.14921), abstract).
- **DP routes:**
  - DP fine-tuning of the generator gives utility "competitive" with non-private generation ([Yue et al.](https://arxiv.org/abs/2210.14348), abstract).
  - Private Evolution / Aug-PE need no training. The model sees only synthetic samples; private data enters only through DP-noised nearest-neighbour votes ([Lin et al.](https://arxiv.org/abs/2305.15560); [Xie et al.](https://arxiv.org/abs/2403.01749), abstracts).
  - DP few-shot generation makes DP synthetic demonstrations for prompts ([Tang et al.](https://arxiv.org/abs/2309.11765)).
- **Overlap checks.** Lee et al. find near-duplicate and repeated substrings in LM corpora and release exact-substring and near-duplicate (MinHash) tools ([arXiv 2107.06499](https://arxiv.org/abs/2107.06499), abstract; MinHash detail *unverified*). The same tools can flag synthetic queries that match a real query.

### 4. Aggregate tables: SDC rules

- **Five Safes** (Safe Data, People, Projects, Settings, Outputs) is the standard framing for trusted research environments ([Desai et al.](https://www2.uwe.ac.uk/faculties/bbs/Documents/1601.pdf); [SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), p. 6).
- **Threshold.**
  - Statistically the minimum is 3 observations. Data owners use anywhere from 3 to 30. The UK handbook assumes N = 10, the ONS value ([SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), pp. 16, 23–24).
  - The Eurostat handbook "normally" uses a minimum frequency of 3 ([Hundepool et al.](https://sdctools.github.io/HandbookSDC/Handbook-on-Statistical-Disclosure-Control.pdf), §4.2).
- **Secondary disclosure.** Two tables that each pass the threshold can still be differenced to isolate one unit ([SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), p. 23). Cells removed to stop this are "secondary" cell suppression ([Hundepool et al.](https://sdctools.github.io/HandbookSDC/Handbook-on-Statistical-Disclosure-Control.pdf), §4.2.2, §4.4).
- **Dominance.** Dominance and p% rules guard against one contributor making up most of a cell ([SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), p. 24). Hundepool et al. recommend the p% rule and keeping its parameters confidential (§4.2).
- **Scatter plots** "are considered disclosive" because each point is one data subject. They fall under the same N rule as tables ([SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), "Scatter plots").
- **Rules versus judgement.** The UK handbook prefers principles-based checking, where each output is assessed, over rigid rules ([SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf), pp. 24–26). SACRO/ACRO automates the common checks and hands a report to a human checker ([arXiv 2212.02935](https://arxiv.org/abs/2212.02935)).
- **DP counts.** Google's DP SQL bounds each user's contribution and thresholds noisy counts before releasing a group whose key comes from the data ([arXiv 1909.01917](https://arxiv.org/abs/1909.01917), abstract; thresholding detail *unverified*). Our category names come from the data, so this "partition selection" problem applies.

### 5. Code to data

- **OpenSAFELY:** researchers write code against generated dummy data, "without access to the real data". The code then runs inside the secure environment, and outputs are reviewed before release ([dummy-data docs](https://docs.opensafely.org/ehrql/tutorials/dummy-data/what-is-dummy-data/); [docs](https://docs.opensafely.org/)).
- Clio follows the same split: raw data stays in a restricted environment and only aggregates leave it ([arXiv 2412.13678](https://arxiv.org/abs/2412.13678), App. F).

## Evaluation

| Artefact type | Attack or failure shown | Reported number | Source |
|---|---|---|---|
| Per-text embedding | full inversion | 92% exact (32 tokens); 89% of full names | [2310.06816](https://arxiv.org/abs/2310.06816) |
| Noisy embedding (σ = 0.01) | zero-shot inversion | > 80% leakage (Enron) | [2504.00147](https://arxiv.org/abs/2504.00147) |
| LLM summary | private info survives | ~10% raw → ~1.5% after summary | [2412.13678](https://arxiv.org/abs/2412.13678) |
| LLM cluster summary + auditor | private info survives | none rated ≤ 3; auditor accuracy 98% | [2412.13678](https://arxiv.org/abs/2412.13678) |
| Synthetic text | membership inference | attack succeeds (see paper) | [2502.14921](https://arxiv.org/abs/2502.14921) |
| Frequency table | small cells, differencing | threshold 3–30; UK N = 10 | [SDC Handbook](https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf) |

## Relevance to lean-explore-bench

Three facts shape everything below. The log has **no user or session ID**. It is **tiny**: about 6,700 rows so far, about 99% API, probably from one or two clients ([query-logs-llm-taxonomy-induction.md](query-logs-llm-taxonomy-induction.md)). And the **encoder is local and public**. As a result, "N queries" is not "N people". One client can fill a whole cluster (a dominance failure), and Clio-style *unique-account* thresholds cannot be computed. DP guarantees would be per query, not per person. The rules below are **our design choices**.

| Artefact | Rule |
|---|---|
| Raw rows (decrypted text) | Stay on the server. Decrypt only in memory inside the pipeline process, and write no plaintext to disk outside the server's data directory. |
| Deduplicated set, rule-based features | Stay on the server. Feature *counts* may leave only through the aggregate-table gate. |
| Per-query embeddings | Stay on the server and are never published: treat them as raw text (§1). Delete them after clustering if they are not needed. |
| Cluster assignments (query → cluster) | Stay on the server; they are row-level data. |
| Centroids | Stay on the server. Publishing centroids adds no benchmark value, and small-cluster centroids approximate single queries (§1, unverified). |
| Keyword / top-term lists (c-TF-IDF etc.) | Stay on the server by default. A term may leave only if it appears in ≥ N distinct queries *and* passes human review for identifiers (declaration names from private projects, file paths, names). |
| Local-LLM cluster labels | Human review on the server. They may leave only as rewritten category *descriptions* with no verbatim query and no example queries, and only for clusters that pass the size gate. Consider a Clio-style audit prompt (local model) as a second check. |
| Plots (UMAP/t-SNE scatter) | Per-query scatter plots stay on the server (§4). Only binned or cluster-level plots with cells ≥ N may leave. |
| Synthetic queries | Generate from the reviewed descriptions only, never with real queries in the prompt (Tang et al.). Before release, run on the server: exact and normalised match, character/word n-gram overlap, and nearest-neighbour embedding similarity against every real query. Drop any synthetic query over the thresholds. Publish the pass/drop counts, not the matches. |
| Aggregate tables (category shares, source mix, filter use) | May leave after an output gate: minimum cell N (start at 10, as ONS does), suppress or merge smaller cells, add secondary suppression across related tables, round counts, and flag any cell dominated by one source or one day. DP noise (per-query ε) is optional on top. |
| Code, configs, prompts | Public. Develop against a generated dummy log (OpenSAFELY pattern). The decryption key lives only in the server's secret store, never in the repo or CI. |

Operational guards (ours):

- Pipeline outputs go to one directory with an allow-listed schema (JSON/CSV of named aggregate fields). Anything else is treated as non-exportable.
- Add a CI and pre-commit check that fails on committed files over a size limit, on non-allow-listed data extensions (`.parquet`, `.npy`, `.jsonl`, `.db`), and on any line matching a hash of a real query. The hash list is kept on the server and checked there.
- Log every export with the reviewer's name, in the spirit of an auditable output check (SACRO).

What the thresholds cost on a small log. With N = 10 and a few thousand deduplicated queries, rare but distinct categories may fall below N. They then have to be merged into a parent or dropped from published stats. Their *description* can still seed synthetic queries if it passes review. This is the same tail loss described in [query-logs-privacy-and-release.md](query-logs-privacy-and-release.md).

## Open questions

- How well can a centroid of k queries be inverted as k grows? Is there a safe k for publishing centroids, or should they never be published?
- Which overlap thresholds (n-gram length, cosine) separate "same query" from "same Lean idiom", given that many real queries are short declaration names that synthetic queries will legitimately repeat?
- With one or two API clients dominating, should the minimum cell size count distinct `source` × day combinations instead of rows?
- Is Aug-PE practical with a local model at our size, and is a per-query ε meaningful without user IDs?

## Sources

- Morris, Kuleshov, Shmatikov & Rush, "Text Embeddings Reveal (Almost) As Much As Text", EMNLP 2023: https://arxiv.org/abs/2310.06816
- Song & Raghunathan, "Information Leakage in Embedding Models", 2020: https://arxiv.org/abs/2004.00053
- Huang et al., "Transferable Embedding Inversion Attack", ACL 2024: https://arxiv.org/abs/2406.10280
- Zhang, Morris & Shmatikov, "Universal Zero-shot Embedding Inversion", 2025: https://arxiv.org/abs/2504.00147
- Tamkin et al., "Clio: Privacy-Preserving Insights into Real-World AI Use", 2024: https://arxiv.org/abs/2412.13678
- Carlini et al., "Extracting Training Data from Large Language Models", USENIX Security 2021: https://arxiv.org/abs/2012.07805
- Carlini et al., "Quantifying Memorization Across Neural Language Models", ICLR 2023: https://arxiv.org/abs/2202.07646
- Meeus et al., "The Canary's Echo", ICML 2025: https://arxiv.org/abs/2502.14921
- Yue et al., "Synthetic Text Generation with Differential Privacy", ACL 2023: https://arxiv.org/abs/2210.14348
- Lin et al., "DP Synthetic Data via Foundation Model APIs 1: Images", ICLR 2024: https://arxiv.org/abs/2305.15560
- Xie et al., "DP Synthetic Data via Foundation Model APIs 2: Text" (Aug-PE), ICML 2024: https://arxiv.org/abs/2403.01749
- Tang et al., "Privacy-Preserving In-Context Learning with DP Few-Shot Generation", ICLR 2024: https://arxiv.org/abs/2309.11765
- Lee et al., "Deduplicating Training Data Makes Language Models Better", ACL 2022: https://arxiv.org/abs/2107.06499
- Griffiths et al., *Handbook on Statistical Disclosure Control for Outputs*, v2.0, SDAP, July 2024: https://ukdataservice.ac.uk/app/uploads/sdc-handbook-v2.0.pdf
- Hundepool et al., *Handbook on Statistical Disclosure Control*, 2nd ed., CoE on SDC: https://sdctools.github.io/HandbookSDC/Handbook-on-Statistical-Disclosure-Control.pdf
- Desai, Ritchie & Welpton, "Five Safes: designing data access for research", UWE Working Paper 1601, 2016: https://www2.uwe.ac.uk/faculties/bbs/Documents/1601.pdf
- Wilson et al., "Differentially Private SQL with Bounded User Contribution", 2019: https://arxiv.org/abs/1909.01917
- Preen et al., "A multi-language toolkit for the semi-automated checking of research outputs", IEEE Trans. Privacy 2025: https://arxiv.org/abs/2212.02935
- OpenSAFELY documentation: https://docs.opensafely.org/ ; dummy data: https://docs.opensafely.org/ehrql/tutorials/dummy-data/what-is-dummy-data/
