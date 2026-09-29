# Query-log characterisation and how test collections sample queries from logs (synthesis)

- **Kind:** paper (synthesis note)
- **Links:**
  - Log characterisation: Silverstein et al. 1999 ([PDF](https://sigir.org/files/forum/F99/Silverstein.pdf)); Downey, Dumais & Horvitz 2007 ([PDF](http://susandumais.com/SIGIR2007-pp225-downeyEtAl.pdf)); Sadowski et al. 2015 ([PDF](https://research.google.com/pubs/archive/43835.pdf)); Mansouri et al. 2019 ([PDF](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf))
  - Collections that sampled from logs: TREC 2009 Web ([overview](https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf)); TREC 2008 Million Query ([overview](https://trec.nist.gov/pubs/trec17/papers/MQ.OVERVIEW.pdf)); MS MARCO ([arXiv 1611.09268](https://arxiv.org/abs/1611.09268)); TREC DL 2019 ([arXiv 2003.07820](https://arxiv.org/abs/2003.07820)); Natural Questions ([TACL](https://aclanthology.org/Q19-1026.pdf)); ORCAS ([arXiv 2006.05324](https://arxiv.org/abs/2006.05324)); Baidu-ULTR ([arXiv 2207.03051](https://arxiv.org/abs/2207.03051)); Q2D-Web ([arXiv 2609.08887](https://arxiv.org/abs/2609.08887))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

This note covers two things:

1. What real query logs look like: length, repetition and head/tail shape, sessions and reformulation.
2. The concrete selection rules that well-known test collections used to turn a log into a query set.

The point is that every published collection applied filters: difficulty, frequency band, length, question-form, privacy. Each filter moves the query set away from the traffic distribution. We should choose our filters deliberately and report them.

## How it works

### What logs look like

| Log | Size | Query length | Repetition / tail | Sessions |
|---|---|---|---|---|
| AltaVista, 43 days, 1998 | ~1B requests, ~285M sessions | mean 2.35 terms | top-25 queries = 1.5% of volume; "almost two-thirds" of queries asked only once | 63.7% of sessions are a single request |
| Windows Live Toolbar opt-in, 3 weeks | ~10M query events, >250k users | n/a | singleton share still near its asymptote after 22 days | tail queries: click 49.5% vs 58.0% non-tail; re-query 44.8% vs 33.4% |
| Google internal Code Search, 2 weeks | 3,870 queries, 27 devs | mean 1.85 keywords (median 1) | 26.5% use `file:`, 5.4% use `lang:` | 2.64 queries/session (mean); 76% of no-click query pairs differ by 1 word |
| Parsijoo math queries, 2 years | 392,586 queries | mean 6.7 words vs 3.4 general | "headless": about 90% of unique queries occur once | math sessions longer and less successful |

Sources:
- AltaVista: [Silverstein et al. 1999](https://sigir.org/files/forum/F99/Silverstein.pdf), §3.1–3.3.
- Windows Live Toolbar: [Downey et al. 2007](http://susandumais.com/SIGIR2007-pp225-downeyEtAl.pdf), Fig. 1 and Table 1. "Tail" there means a query not seen in the previous week.
- Google Code Search: [Sadowski et al. 2015](https://research.google.com/pubs/archive/43835.pdf), §4.3–4.4.
- Parsijoo: [Mansouri et al. 2019](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf), §1, §4.1.

Further points:
- **Robots are already in the logs.** Silverstein et al. traced the surprisingly frequent term "applet" to "almost all" being submitted by a robot ([Silverstein et al. 1999](https://sigir.org/files/forum/F99/Silverstein.pdf), §3.2). Separating automated traffic is an old problem, now sharpened by agents (see [query-logs-agent-vs-human-queries.md](query-logs-agent-vs-human-queries.md)).
- **Query frequency differs from need frequency.** Users often reformulate *non-tail* queries into *tail* queries while pursuing the same goal (49.9% of reformulations from non-tail queries go to tail). A rare string is therefore not a rare need ([Downey et al. 2007](http://susandumais.com/SIGIR2007-pp225-downeyEtAl.pdf), Table 2).

### How collections sampled their queries

| Collection | Source log | Selection rule | Effect on representativeness |
|---|---|---|---|
| TREC 2009 Web Track | commercial engine, Jan 2009 | 200 sampled **preferring medium popularity** ("torso"); head avoided as "too navigational", tail avoided as possible PII; adult filter; NIST used 50 | deliberately excludes head and tail |
| TREC 2008 Million Query | large engine; queries with a click on a GOV2 page | 10,000 queries **stratified 2×2**: ≤6 vs >6 words × ≤3 vs >3 .gov clicks, equal cells (2,434 each); assessors **chose** 1 of 10 displayed queries to judge | equal allocation over-weights rare cells; assessor choice adds selection bias |
| MS MARCO | Bing | sampled, then **non-question queries removed** by a trained classifier; "navigational and other intents" excluded | question-intent only |
| TREC DL 2019 | MS MARCO held-out | 200 test queries; NIST judged those whose runs had **median MRR in (0, 0.5]** (52 candidates → 43 final) | difficulty-filtered, not traffic-representative |
| Natural Questions | Google | **≥8 words**, issued "by multiple users in a short period of time", question-form heuristics, Wikipedia page in top 5 | long, repeated, question-form only |
| ORCAS | Bing, 26 months | query–URL pairs to TREC DL docs; **k-anonymity** (query typed by k distinct users, "a high value of k"); offensive queries removed; counts dropped | removes the tail entirely |
| Baidu-ULTR | Baidu, 2022 | **token-level** random sampling (a repeated query is sampled repeatedly), "so the query distribution … follows the same distribution as that in the online system"; expert set tagged with 10 monthly-frequency buckets (0–2 high, 3–6 mid, 7–9 tail) | representative, with per-stratum reporting |
| Q2D-Web (2026) | Perplexity-style production agent searches | **stratified by month**, then matched to production distribution over domain and language; dedup; drop `site:`-style operators and PII | representative of agent traffic, minus operators and PII |

Sources:
- TREC 2009 Web: [overview](https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf), §2 "Topic Development Procedure".
- TREC 2008 MQ: [overview](https://trec.nist.gov/pubs/trec17/papers/MQ.OVERVIEW.pdf), §1.2 and the judging procedure.
- MS MARCO: [Bajaj et al.](https://arxiv.org/abs/1611.09268), §3.
- TREC DL 2019: [Craswell et al.](https://arxiv.org/abs/2003.07820), §2 and §5.
- NQ: [Kwiatkowski et al.](https://aclanthology.org/Q19-1026.pdf), §3.1.
- ORCAS: [Craswell et al.](https://arxiv.org/abs/2006.05324), §3.
- Baidu-ULTR: [Zou et al.](https://arxiv.org/abs/2207.03051), §3.1–3.2.
- Q2D-Web: [Schall et al.](https://arxiv.org/abs/2609.08887), §3.1.

### Two sampling units: types vs tokens

- **Token (traffic) sampling** draws log *events*, so a query asked 1,000 times is 1,000× as likely to be drawn. The mean metric then estimates the user-experienced average (Baidu-ULTR).
- **Type (unique-query) sampling** draws *distinct strings*. In a heavy-tailed log it is dominated by singletons: two-thirds of AltaVista queries and about 90% of unique math queries occurred once. The mean metric then estimates quality over the space of distinct needs.
- These two answer different questions. Stratified designs (TREC MQ, Baidu-ULTR buckets) let you report both, provided each stratum's traffic weight is known. The weighting arithmetic is standard stratified estimation; the sources above do not spell it out.

## Evaluation (lessons, each with a source)

1. **Every filter is a bias; document it.** TREC DL chose moderately hard queries. NQ chose long, repeated question queries. ORCAS removed everything under the k-user threshold. Their scores therefore do not describe the traffic mean ([TREC DL 2019](https://arxiv.org/abs/2003.07820), [NQ](https://aclanthology.org/Q19-1026.pdf), [ORCAS](https://arxiv.org/abs/2006.05324)).
2. **Tail queries are where systems are weakest.** Users click less and re-query more after tail queries ([Downey et al. 2007](http://susandumais.com/SIGIR2007-pp225-downeyEtAl.pdf)). All ULTR algorithms "perform poorly on those tail queries" ([Baidu-ULTR](https://arxiv.org/abs/2207.03051), §3.3). Dropping the tail for privacy therefore inflates scores.
3. **Stratify, then report per stratum.** Baidu-ULTR's frequency buckets and TREC MQ's length × click cells make per-stratum comparisons possible. Per-stratum rankings of systems can differ from the aggregate: Q2D-Web found rankings "diverging substantially across topical domains, query languages, and query types" ([Q2D-Web](https://arxiv.org/abs/2609.08887), abstract).
4. **Freeze the time window and stratify by time.** TREC Web 2009 sampled from a log contemporaneous with the crawl ([overview](https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf)). Q2D-Web stratified uniformly by month ([Q2D-Web](https://arxiv.org/abs/2609.08887), §3.1).
5. **Do not let assessors pick queries silently.** In TREC MQ 2008 assessors chose which of 10 displayed queries to judge ([overview](https://trec.nist.gov/pubs/trec17/papers/MQ.OVERVIEW.pdf)), which skews toward understandable queries. Log any skipped queries and the reason.
6. **How many topics?** See [../statistics/effect-sizes-power-and-topic-set-size.md](../statistics/effect-sizes-power-and-topic-set-size.md) and [../ir-evaluation/trec-pooling-and-relevance-judgments.md](../ir-evaluation/trec-pooling-and-relevance-judgments.md).

## Relevance to lean-explore-bench

- **Characterise before sampling.** Where query logs are available (web UI, API, MCP), compute:
  - query length distribution
  - type/token ratio and singleton share
  - top-k volume share
  - share of queries that look like Lean identifiers, Lean syntax or goals, LaTeX, and natural language
  - session length and reformulation rate (edit distance 1, as in Sadowski)
  - share from each client (web / API / MCP / agent)
- **Expect a near-headless distribution.** Math search was about 90% singletons ([Mansouri et al.](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf)). Frequency buckets may then collapse to "repeated" vs "singleton". Stratify primarily on *query form × intent × client*, and use frequency as a secondary axis.
- **Use a Baidu-ULTR-style dual design.** Draw a token-level random sample, so the headline number is traffic-weighted. Add over-sampled strata for rare but important forms (goal-state queries, name fragments), and reweight them for the headline.
- **Don't copy TREC DL's difficulty filter into the main split.** A "hard" split is fine, but label it as such.
- **Normalise near-duplicates before counting frequency.** Normalise whitespace, case and Unicode vs ASCII notation (`≤` vs `<=`). Sadowski's 1-word reformulations suggest that session-level de-duplication also matters. Keep one query per session per need, or weight by session.
- **Keep a log-derived split separate from a curated split** ([MathlibQR](../lean-benchmarks/mathlibqr.md), [LeanSearch v1](../lean-benchmarks/leansearch-v1-benchmark.md)), and report both.

## Open questions

- Are Lean search logs large enough for frequency strata to mean anything, or is essentially every query a singleton?
- Which unit best represents "a need" in Lean search: query string, session, or (session, target declaration)?
- How much does an in-editor source (`exact?`, [lean-lsp-mcp](../lean-tools/lean-lsp-mcp.md) tool calls) change the length and form distribution relative to the web UI?

## Sources

- Silverstein, Henzinger, Marais & Moricz, "Analysis of a very large web search engine query log", SIGIR Forum 33(1), 1999: https://sigir.org/files/forum/F99/Silverstein.pdf
- Downey, Dumais & Horvitz, "Heads and tails: studies of web search with common and rare queries", SIGIR 2007 poster: http://susandumais.com/SIGIR2007-pp225-downeyEtAl.pdf
- Sadowski, Stolee & Elbaum, FSE 2015: https://research.google.com/pubs/archive/43835.pdf
- Mansouri, Zanibbi & Oard, JCDL 2019: https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf
- Clarke, Craswell & Soboroff, "Overview of the TREC 2009 Web Track": https://trec.nist.gov/pubs/trec18/papers/WEB09.OVERVIEW.pdf
- "Million Query Track 2008 Overview": https://trec.nist.gov/pubs/trec17/papers/MQ.OVERVIEW.pdf ; 2007 track data page: https://trec.nist.gov/data/million.query07.html
- Bajaj et al., "MS MARCO", arXiv 1611.09268: https://arxiv.org/abs/1611.09268
- Craswell et al., "Overview of the TREC 2019 deep learning track", arXiv 2003.07820: https://arxiv.org/abs/2003.07820
- Kwiatkowski et al., "Natural Questions", TACL 2019: https://aclanthology.org/Q19-1026.pdf
- Craswell et al., "ORCAS: 18 Million Clicked Query-Document Pairs", arXiv 2006.05324: https://arxiv.org/abs/2006.05324
- Zou et al., "A Large Scale Search Dataset for Unbiased Learning to Rank" (Baidu-ULTR), arXiv 2207.03051: https://arxiv.org/abs/2207.03051
- Schall et al., "Q2D-Web", arXiv 2609.08887: https://arxiv.org/abs/2609.08887
