# Releasing query logs privately: AOL, k-anonymity thresholds, differential privacy, synthetic queries

- **Kind:** paper (synthesis note)
- **Links:** AOL release ([Wikipedia summary](https://en.wikipedia.org/wiki/AOL_search_log_release), [TechCrunch 2006](https://www.techcrunch.com/2006/08/09/first-person-identified-from-aol-data-thelma-arnold)); Korolova et al. WWW 2009 ([ACM DL](https://dl.acm.org/doi/10.1145/1526709.1526733), [talk slides PDF](https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf)); Götz et al. TKDE 2012 ([arXiv 0904.0682](https://arxiv.org/abs/0904.0682)); ORCAS ([arXiv 2006.05324](https://arxiv.org/abs/2006.05324)); TREC 2009 Web ([overview](https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf)); Carranza et al. NAACL 2024 ([arXiv 2305.05973](https://arxiv.org/abs/2305.05973)); Q2D-Web ([arXiv 2609.08887](https://arxiv.org/abs/2609.08887)); DeepResearchGym logs ([arXiv 2601.17617](https://arxiv.org/abs/2601.17617))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

This note covers what can safely be published from a query log, and how the privacy mechanism changes which queries end up in a benchmark. For a benchmark the question is: if real query logs feed a public query set, which queries can be released, and what bias does the release rule introduce?

## How it works

### The AOL incident (2006)

- On 4 Aug 2006 AOL Research released about 20M queries from over 650,000 users covering three months. Users were replaced by numeric IDs, but queries contained PII ([Wikipedia](https://en.wikipedia.org/wiki/AOL_search_log_release)).
- The New York Times identified user 4417749 as Thelma Arnold of Lilburn, Georgia, from her queries alone ([TechCrunch](https://www.techcrunch.com/2006/08/09/first-person-identified-from-aol-data-thelma-arnold)).
- According to Korolova et al.'s talk, "CTO resigned, 2 employees fired" and a class action followed ([slides](https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf)).
- **The lesson.** Pseudonymous user IDs plus full per-user query histories re-identify people. Removing names, numbers and locations, or token-hashing the queries, does not fix this. Korolova et al. cite Kumar et al. (WWW 2007) showing token-based hashing fails ([slides](https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf); the Kumar et al. primary was not read, so unverified).

### Frequency thresholds (k-anonymity-style)

- **ORCAS (Bing, 2020)** keeps only queries "typed by k different users, for a high value of k", so the dataset "cannot contain a query with information that is only known to fewer than k users". It also drops user and session IDs, drops rank positions, records presence rather than counts for query–URL pairs, and removes offensive queries ([ORCAS](https://arxiv.org/abs/2006.05324), §3). The value of k is not published.
- **TREC 2009 Web** avoided "very rare queries [that] may contain personally identifiable information" by sampling torso queries only ([overview](https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf), §2).
- **Natural Questions** used only queries issued "by multiple users in a short period of time" ([NQ](https://aclanthology.org/Q19-1026.pdf), §3.1).
- **Weaknesses.**
  - Plain thresholds are attackable. An attacker can submit a guessed secret threshold − 1 times to push it over the line ([Korolova slides](https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf)).
  - Götz et al. show k-anonymity methods for search logs "are vulnerable to active attacks" ([Götz et al.](https://arxiv.org/abs/0904.0682), abstract).

### Differential privacy for query release

- **Korolova, Kenthapadi, Mishra & Ntoulas (WWW 2009).** The mechanism has three steps:
  1. Cap each user's contribution at *d* queries and *d_c* clicks.
  2. Add Laplace noise to each query's count.
  3. Release a query only if its noisy count exceeds a threshold.
- The result is an (ε, δ) guarantee, and "a non-negligible fraction of queries and clicks can indeed be safely published" ([ACM DL](https://dl.acm.org/doi/10.1145/1526709.1526733); mechanism as described in the [slides](https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf)).
- **Götz, Machanavajjhala, Wang, Xiao & Gehrke (TKDE 2012)** compare guarantees for publishing frequent keywords, queries and clicks. They found pure ε-DP gives no useful utility for this task, and proposed ZEALOUS, a two-phase noisy-threshold algorithm with (ε, δ)-probabilistic privacy. Its utility is comparable to k-anonymity methods with much stronger guarantees ([arXiv 0904.0682](https://arxiv.org/abs/0904.0682), abstract).
- **Consequence for benchmarks.** Every threshold-based release, DP or not, keeps *frequent* queries and drops the tail. Since tail queries are where systems do worst (see [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md)), a released query set is systematically easier than the traffic.

### Synthetic queries as a privacy route

- **Carranza et al. (NAACL 2024).** They train a DP language model on real queries and generate "private synthetic queries representative of the original data" with query-level DP guarantees. This beats DP-training the retriever directly ([arXiv 2305.05973](https://arxiv.org/abs/2305.05973), abstract). It was evaluated for *training*; its fidelity as an *evaluation* set is not established there.
- **Lean Finder** did not release its 693 real Zulip/GitHub queries, "for privacy reasons", and published GPT-4o-generated queries from mined intent clusters instead ([lean-finder-eval.md](../lean-benchmarks/lean-finder-eval.md)).

### Recent practice with agent logs

- **Q2D-Web (2026):** PII detection on each query, with any query containing PII dropped. Queries with operators such as `site:` are also discarded ([Q2D-Web](https://arxiv.org/abs/2609.08887), §3.1).
- **DeepResearchGym logs (SIGIR 2026):** released as "anonymized logs" with anonymized client IPs ([Ning et al.](https://arxiv.org/abs/2601.17617), §3 and abstract).
- **Agent queries can still leak.** Local research agents' network traces let an observer recover over 73% of the "functional and domain knowledge" of user prompts ([Jeong et al., arXiv 2508.20282](https://arxiv.org/abs/2508.20282)). Agent query strings are derived from user prompts, so they need the same care as human queries.

## Evaluation

| Mechanism | Guarantee | What it drops | Used by |
|---|---|---|---|
| Pseudonymous IDs, full histories | none (AOL re-identified) | nothing | AOL 2006 |
| Frequency floor (k users) | heuristic; active attacks possible | tail below k | ORCAS, NQ ("multiple users") |
| Frequency band (torso) | heuristic | head and tail | TREC Web 2009 |
| Per-user cap + noisy threshold | (ε, δ)-DP | tail below the threshold; some near-threshold queries | Korolova 2009, ZEALOUS |
| DP synthetic generation | (ε, δ)-DP on queries | exact strings (distribution only) | Carranza 2024 |
| Per-query PII filter | heuristic | PII-bearing queries | Q2D-Web 2026 |

Sources: rows as cited above.

## Relevance to lean-explore-bench

- **Lean queries are low-risk, but not zero-risk.** Most are mathematical (`sum of geometric series`, `Finset.card_le_card`). However, queries can contain unpublished research ideas, declaration names from private projects, or goals copied from private repositories, and agent queries are derived from user prompts, so they can embed private context ([Jeong et al.](https://arxiv.org/abs/2508.20282)).
- **Released query sets are easier than real traffic.** Every threshold-based release rule (k distinct users, a noisy DP threshold, a torso-only band) removes the rare tail, which is where systems do worst. Any log-derived public set should therefore be paired with results on a held-out set that keeps the tail, and the gap between the two reported.
- **Prefer aggregation or synthetic queries where manual review cannot scale**, as ORCAS and Carranza et al. do, and label synthetic queries clearly as synthetic.

## Open questions

- Is a k-distinct-user threshold feasible for Lean search at all, given the near-headless distribution seen in math search, or would it remove nearly everything?
- Can DP synthetic Lean queries preserve the syntactic forms (goals, partial names) that matter for evaluation?

## Sources

- AOL search log release (summary): https://en.wikipedia.org/wiki/AOL_search_log_release ; TechCrunch, "First person identified from AOL data: Thelma Arnold", 2006: https://www.techcrunch.com/2006/08/09/first-person-identified-from-aol-data-thelma-arnold
- Korolova, Kenthapadi, Mishra & Ntoulas, "Releasing search queries and clicks privately", WWW 2009: https://dl.acm.org/doi/10.1145/1526709.1526733 ; talk slides: https://pdfs.semanticscholar.org/960f/a86904befc486a7aa94c04bbaf7589c3096f.pdf
- Götz, Machanavajjhala, Wang, Xiao & Gehrke, "Publishing Search Logs – A Comparative Study of Privacy Guarantees", IEEE TKDE 24(3), 2012: https://arxiv.org/abs/0904.0682
- Craswell et al., ORCAS, 2020: https://arxiv.org/abs/2006.05324
- Clarke, Craswell & Soboroff, TREC 2009 Web Track overview: https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf
- Kwiatkowski et al., Natural Questions, TACL 2019: https://aclanthology.org/Q19-1026.pdf
- Carranza et al., "Synthetic Query Generation for Privacy-Preserving Deep Retrieval Systems using Differentially Private Language Models", NAACL 2024: https://arxiv.org/abs/2305.05973
- Schall et al., Q2D-Web, 2026: https://arxiv.org/abs/2609.08887
- Ning et al., "Agentic Search in the Wild", SIGIR 2026: https://arxiv.org/abs/2601.17617
- Jeong et al., "Network-Level Prompt and Trait Leakage in Local Research Agents", 2025: https://arxiv.org/abs/2508.20282
