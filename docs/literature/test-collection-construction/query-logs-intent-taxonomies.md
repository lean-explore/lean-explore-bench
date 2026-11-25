# Query intent taxonomies: web search, code search and math search (synthesis)

- **Kind:** paper (synthesis note)
- **Links:** Broder 2002 ([SIGIR Forum PDF](https://www.sigir.org/files/forum/F2002/broder.pdf)); Rose & Levinson 2004 ([ACM DL](https://dl.acm.org/doi/10.1145/988672.988675)); Jansen, Booth & Spink 2008 ([PDF](https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf)); Sadowski, Stolee & Elbaum 2015 ([PDF](https://research.google.com/pubs/archive/43835.pdf)); Stolee, Welp, Sadowski & Elbaum 2025 ([ACM DL](https://dl.acm.org/doi/10.1145/3715774), [NSF PAR PDF](https://par.nsf.gov/servlets/purl/10618890)); Rahman et al. 2018 ([arXiv 1803.08612](https://arxiv.org/abs/1803.08612)); Mansouri, Zanibbi & Oard 2019 ([PDF](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf))
- **Authors / org, date:** this repo, Sept 2026
- **Status:** living note

## What it is

This note covers how the IR and software-engineering literature sorts queries by *why* the user is searching, and how those intent mixes were measured. A benchmark is only representative if its intent mix matches real traffic. So the useful parts are the categories themselves and the measurement methods (survey vs. log coding vs. classifier), together with their known biases.

## How it works (the taxonomies)

### Web search: Broder → Rose & Levinson → Jansen et al.

- **Broder (2002)** defines three classes: *navigational* ("reach a particular site"), *informational* ("acquire some information assumed to be present on one or more web pages") and *transactional* ("perform some web-mediated activity"). He measured the mix two ways on AltaVista ([Broder 2002](https://www.sigir.org/files/forum/F2002/broder.pdf), §4):
  - **Pop-up user survey.** 3,190 valid returns, June–Nov 2001, about 10% response rate. Navigational 24.5%. Transactional "> 22%", estimated at about 36% after hand-reading 200 free-text explanations. Informational was inferred as the remainder (estimated 39%).
  - **Log coding.** He drew 1,000 random queries, removed non-English and sexual queries, and hand-coded the first 400: navigational 20%, informational 48%, transactional 30%.
  - **Self-selection bias, measured.** Sexual queries were under 1% of survey responses but about 12% of the log. Survey-derived query sets can therefore misrepresent the log badly.
- **Rose & Levinson (2004)** refined the classes into informational (directed/undirected, advice, locate, list), navigational, and *resource* (download, entertainment, interact, obtain). They reported about 62% informational, 13% navigational and 24% resource. Figures are as summarised by [Jansen et al. 2008](https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf), §2; the primary paper is at [ACM DL](https://dl.acm.org/doi/10.1145/988672.988675) and we did not read it directly (unverified beyond the secondary summary).
- **Jansen, Booth & Spink (2008)** built a three-level hierarchical taxonomy and a rule-based classifier. On a log of over 1.5M queries they found "more than 80%" informational and about 10% each navigational and transactional. Against 400 hand-coded queries the classifier was 74% accurate. About 25% of queries were "vague or multi-faceted", and the authors argue for *probabilistic* (multi-label) intent. After correcting for the misclassifications they estimate about 65/15/20 ([Jansen et al. 2008](https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf), abstract and §5).
- **Takeaway.** The measured share of the same three classes swings widely: navigational ranges from 10% to 26%. What drives it is the measurement method (survey vs. log, rules vs. humans) and the engine, not only real behaviour ([Jansen et al. 2008](https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf), §5 discusses this directly).

### Code search

- **Sadowski, Stolee & Elbaum (FSE 2015), Google internal Code Search.** 27 developers over two weeks. A browser extension asked "What question are you trying to answer?" before a search (394 survey responses), and the authors combined this with logs (1,929 sessions, 1,429 containing a search). Open card-sorting of 259 answers gave five question families ([Sadowski et al. 2015](https://research.google.com/pubs/archive/43835.pdf), Table 1, §4.1):
  - **How / example code needed:** 33.5%. Subtypes: API consumer needs help, discover the correct library, example to build off, how to do something.
  - **What / exploring or reading code:** 26%. Subtypes: browsing, check implementation details, **name completion** (the developer "could only remember part of the name"), check common style.
  - **Where / code localization:** 16%. Subtypes: reachability, show someone else, location in source control.
  - **Why / determine impact:** 16%. Subtypes: why is something failing, side effects of a change, dependencies.
  - **Who and when / metadata:** 8%.
- **Stolee, Welp, Sadowski & Elbaum (FSE 2025), ten-year replication.** Three surveys with 1,945 responses, plus usage logs for more than 100,000 users over 30 months. Search frequency "has not changed despite the introduction of AI-enhanced development support". Example-seeking still occurs but has *decreased*, and learning/exploring has *increased*. Example seekers mostly wanted "the most common way of using the API in production code" ([Stolee et al. 2025](https://par.nsf.gov/servlets/purl/10618890), abstract and §1).
- **Rahman et al. (MSR 2018), general web search used for code.** 310 developers, 14 months, 149,610 Google queries. A "codeness" classifier built from Stack Overflow tag tokens (P 87%, R 86%) labelled 59.21% of queries as code-related. Code queries were edited more often (34.9% vs 17.01%) and needed more effort per task ([Rahman et al. 2018](https://arxiv.org/abs/1803.08612), abstract, §1, RQ2).
- Bing-log code-intent filtering is also how [CoSQA](../code-search/cosqa.md) and the [CodeSearchNet Challenge](../code-search/codesearchnet.md) chose their queries.

### Math search

- **Mansouri, Zanibbi & Oard (JCDL 2019).** They found 392,586 queries with a distinctive math term in two years of Parsijoo (Persian web engine) logs, across 69,014 sessions. Findings ([Mansouri et al. 2019](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf), abstract, §1, §4.1):
  - Math sessions are "typically longer and less successful" than general sessions.
  - Mean math query length is 6.7 words vs 3.4 for general queries.
  - 18.4% of math query instances are phrased as questions, vs 1.8% reported for general Persian queries.
  - Copy-pasted text is common among the longest queries.
  - The distribution is "essentially headless": under 1% of instances come from frequently repeated queries, and about 90% of unique queries occur once.
- For Lean specifically, [Lean Finder](../lean-benchmarks/lean-finder-eval.md) mined 5 intent clusters from 693 real Zulip/GitHub questions. It then generated 1,000 synthetic queries from those clusters. The real queries were not released.

## Evaluation (how intent mixes were measured, and the pitfalls)

| Study | Method | Sample | Known bias |
|---|---|---|---|
| Broder 2002 | pop-up survey + hand-coding 400 log queries | 3,190 survey returns | self-selection (sexual queries <1% in survey vs ~12% in log) |
| Rose & Levinson 2004 | hand-coding with session context | (see paper) | secondary figures only here |
| Jansen et al. 2008 | rule classifier on 1.5M queries, 400 hand-coded | 74% accuracy | about 25% of queries are ambiguous or multi-intent |
| Sadowski et al. 2015 | pre-search survey + logs | 27 devs, 259 coded answers | participants were known to the authors; one company |
| Stolee et al. 2025 | 3 surveys + 30-month logs | 1,945 responses, >100k users | one company; intent is self-reported |
| Rahman et al. 2018 | lexicon classifier on 149k queries | P 87 / R 86 | Chrome-plugin population |
| Mansouri et al. 2019 | math-term filter on a 2-year log | 392k queries | term-list recall; Persian engine |

Sources: the per-study links above.

## Relevance to lean-explore-bench

- **An intent axis for Lean queries, adapted from Sadowski's families.** This mapping is our proposal; the category names come from the sources above.
  - *Navigational / name completion* ("I remember part of the name": `Finset.sum_comm`, `mul_le_mul_left'`). This is Broder's navigational class and Sadowski's "name completion".
  - *Existence / informational-statement* ("is there a lemma that says a continuous function on a compact set is bounded?").
  - *How-to / API usage* ("how do I state a bound on a Finset sum?"). This is Sadowski's "example code needed".
  - *Goal-driven / transactional* (a proof state or goal pasted in to find a closing lemma). It resembles Broder's transactional class because the user wants to *do* something.
  - *Definition / concept lookup* ("what is Mathlib's name for a uniform space?").
  - *Browsing / exploration* (list the API around a structure).
- **Label intent probabilistically or multi-label.** About 25% of web queries are ambiguous ([Jansen et al. 2008](https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf)). Record annotator disagreement rather than forcing one class.
- **Do not estimate the intent mix from a survey or from Zulip alone.** Broder's self-selection result shows a survey can distort the mix badly. Zulip questions over-represent hard cases that people ask about publicly. Where possible, estimate the mix from the engine's own logs, and use surveys only to *explain* log queries.
- **Expect headless, long, question-style queries** if Lean search resembles math web search ([Mansouri et al. 2019](https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf)). Frequency-based head/torso/tail strata may then be degenerate, and intent × query-form strata matter more (see [query-logs-characterisation-and-sampling.md](query-logs-characterisation-and-sampling.md)).
- **AI assistance shifts intent over time.** Example-seeking in code search fell over ten years ([Stolee et al. 2025](https://par.nsf.gov/servlets/purl/10618890)), so re-measure the intent mix periodically. Agent traffic has its own intent mix (see [query-logs-agent-vs-human-queries.md](query-logs-agent-vs-human-queries.md)).

## Open questions

- What is the actual navigational (name) vs informational (NL) vs goal (proof-state) split in Lean search traffic? No public numbers exist that we found.
- Can a cheap classifier (a "codeness"-style lexicon plus Lean syntax detection) label intent at 85%+ precision, as Rahman et al. achieved for code/non-code?
- Does the Lean user population (students, Mathlib maintainers, formalisation projects, agents) need to be a stratification variable in its own right?

## Sources

- Broder, "A taxonomy of web search", SIGIR Forum 36(2), 2002: https://www.sigir.org/files/forum/F2002/broder.pdf
- Rose & Levinson, "Understanding user goals in web search", WWW 2004: https://dl.acm.org/doi/10.1145/988672.988675 (figures via Jansen et al.; primary not read, so unverified)
- Jansen, Booth & Spink, "Determining the informational, navigational, and transactional intent of Web queries", IP&M 44, 2008: https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_user_intent.pdf
- Sadowski, Stolee & Elbaum, "How developers search for code: a case study", ESEC/FSE 2015: https://research.google.com/pubs/archive/43835.pdf
- Stolee, Welp, Sadowski & Elbaum, "10 Years Later: Revisiting How Developers Search for Code", PACMSE 2(FSE), 2025: https://dl.acm.org/doi/10.1145/3715774 ; PDF https://par.nsf.gov/servlets/purl/10618890
- Rahman et al., "Evaluating how developers use general-purpose web-search for code retrieval", MSR 2018: https://arxiv.org/abs/1803.08612
- Mansouri, Zanibbi & Oard, "Characterizing searches for mathematical concepts", JCDL 2019: https://www.cs.rit.edu/~rlaz/files/CharacterizingMathSearch-JCDL_Final.pdf
