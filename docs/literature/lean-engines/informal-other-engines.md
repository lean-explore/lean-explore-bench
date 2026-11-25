# Other informal and cross-formality search services (zbMATH Open, Stacks/ProofWiki, formula engines, LLM web search), plus the protocols that evaluated them

- **Kind:** survey note (several services and two evaluation protocols)
- **Links:**
  - zbMATH Open https://zbmath.org/ and API https://api.zbmath.org/
  - Stacks Project https://stacks.math.columbia.edu/
  - ProofWiki https://proofwiki.org/
  - Re²Math https://arxiv.org/abs/2605.09012
  - AViD Journal https://arxiv.org/abs/2608.14669
- **Authors / org, date:** various, 2025–2026. See each section.
- **Status:** liveness was checked by us on 2026-09-28 and is given per section.

## What it is

This note covers the 2025–2026 informal math search services other than the statement-level engines, which have their own notes: [informal-theoremsearch.md](informal-theoremsearch.md), [informal-matlas.md](informal-matlas.md) and [informal-mathlas-mcp.md](informal-mathlas-mcp.md). It also records two recent papers whose *evaluation protocols* for informal theorem retrieval are useful to a Lean benchmark.

**Our search for other statement-level engines.** We searched arXiv, the web and Lean Zulip on 2026-09-28. We found **no other public statement-level informal theorem search engine** from 2025–2026 beyond TheoremSearch, Matlas (including its legacy arXiv engine at leansearch.net/thm) and the community mathlas MCP. We found no engine named "Real Math" or "RealMath" (web search returned nothing relevant). **Of these engines, only TheoremSearch indexes Lean**, and only on its `/graph/*` endpoints (see [informal-theoremsearch.md](informal-theoremsearch.md)). mathlas proxies Loogle and LeanSearch instead of indexing Lean itself.

## Services

### zbMATH Open (FIZ Karlsruhe): document-level, experimental natural-language front end

- **What is indexed.** Bibliographic records (reviews, keywords, MSC codes and references), not individual statements. The API document schema has `title`, `keywords`, `msc`, `references`, `source`, `year` and similar fields, with no statement field (live API call, 2026-09-28). A 2026 knowledge-graph paper describes 34M entities and 168M RDF triples ([arXiv:2609.00969](https://arxiv.org/abs/2609.00969)).
- **Natural-language search.**
  - An "experimental" option lets an LLM translate a natural-language query into zbMATH's one-line search syntax (web-search snippets of [Teschke, EMS Magazine 141 (2026) 41–43](https://euromathsoc.org/magazine/articles/325)). The article's web version was "not yet available" when we fetched it, so the mechanism and the model are unverified.
  - FIZ still describes a natural-language interface as a future goal ("In the future, there should be a natural language user interface…"; [FIZ page](https://www.fiz-karlsruhe.de/en/bereiche/mathematische-informationsinfrastruktur)).
- **Evaluation.** We found no published retrieval evaluation of the natural-language search. The zbMATH team's own ARQMath participation reported that "neither our automated methods nor our manual runs archived good scores" ([Scharpf et al., arXiv:2012.02413](https://arxiv.org/abs/2012.02413)); see also [../math-ir/arqmath.md](../math-ir/arqmath.md).
- **API and liveness.** `https://api.zbmath.org/v1/document/_search` returned HTTP 200 without a key, reporting 995 results for "extreme value theorem". No rate-limit headers were seen. The zbmath.org web front end returned 403 to our fetcher.
- **Lean content:** none.

### Stacks Project and ProofWiki native search: keyword and tag search over curated statements

- **Stacks.** `https://stacks.math.columbia.edu/search?query=…` and `/tag/XXXX` returned HTTP 200 (checked by us). Search is keyword-based.
  - **Lean link.** Mathlib carries `@[stacks XXXX]` tags, so Stacks tags are ready-made informal–formal pairs ([../math-ir/informal-formal-alignment.md](../math-ir/informal-formal-alignment.md)).
- **ProofWiki.** The MediaWiki search API returned 403 to our unauthenticated curl; its liveness for bots is unverified. The ProofWiki and Stacks corpora underlie NaturalProofs ([../math-ir/naturalproofs.md](../math-ir/naturalproofs.md)).
- **Evaluation.** Neither native search has a published retrieval evaluation that we know of. The TheoremSearch paper indexes both sources (23,871 and 12,693 statements) and reports ProofWiki/Stacks filters on its API ([informal-theoremsearch.md](informal-theoremsearch.md)).

### Formula search engines (Approach Zero, Tangent, MathWebSearch/zbMATH formulae, SearchOnMath)

- These retrieve formulas or Q&A posts, not theorem statements. Their evaluations come from the ARQMath and NTCIR campaigns ([../math-ir/arqmath.md](../math-ir/arqmath.md), [../math-ir/ntcir-math.md](../math-ir/ntcir-math.md)).
- Approach Zero also appears as a baseline in SABER-Math ([../math-ir/saber-math.md](../math-ir/saber-math.md)).
- We did not re-evaluate them. Approach Zero's search page (https://approach0.xyz/search/) timed out for us on 2026-09-28 (HTTP 000).

### General LLM web search as a baseline "engine"

- **TheoremSearch's baselines** ([arXiv:2602.05216 Table 2](https://arxiv.org/abs/2602.05216)):
  - Theorem Hit@20: ChatGPT 5.2 with search 0.198, Gemini 3 Pro 0.270.
  - Paper Hit@20: Google `site:arxiv.org` 0.378, arXiv search 0.027.
- **TheoremSearch's real-user RAG study.** GPT-5.2 with web search already answers the "FAMOUS" and most "NICHE" queries well. TheoremSearch helped mainly where web search failed ([informal-theoremsearch.md](informal-theoremsearch.md)).

## Evaluation protocols worth reusing

- **Re²Math** (Lyu, Yang, Zhang, Huang; [arXiv:2605.09012](https://arxiv.org/abs/2605.09012), 2026-05-09) benchmarks *tool-grounded theorem retrieval from partial proofs*.
  - **Task.** Given a proof prefix, an agent must find a theorem that closes the next step.
  - **Scoring is citation-agnostic.** Any admissible theorem sufficient for the proof step earns credit.
  - **Headline result.** The best "fixed-judge ToolAcc" is only 7.0% (abstract).
  - **Frozen retrieval artifact.** The retrieval engine is a **frozen Google Scholar query cache**, not a live engine. Each query is run once with a per-instance upper year bound (the citing paper's year), and the top-20 is cached along with the query, timestamp and settings. All numbers are computed only from that cache ([§ "Input Rendering and Retrieval Artifact"](https://arxiv.org/abs/2605.09012)).
  - **Useful for us.** It does not evaluate TheoremSearch or Matlas. But the frozen query–result cache is exactly how to make evaluations of *live, unversioned* services reproducible. Its separation of planning, query writing, retrieval, selection and extraction is a useful decomposition for an agent-level track.
- **AViD Journal** (Porto; [arXiv:2608.14669](https://arxiv.org/abs/2608.14669), 2026-08-02) is a novelty-checking pipeline. It queries Leandex for Mathlib, and TheoremSearch plus Matlas for the informal literature, with a temporal filter and an LLM judge.
  - **Coverage finding.** None of the 12 known duplicators behind duplicate-withdrawn arXiv papers is in either informal index, even by exact-name search.
  - **Score-less API caveat.** Leandex's API returned no scores, so AViD's "18/18" formal coverage cannot distinguish real coverage from an absent threshold. This is a caution for any harness that consumes a score-less API.

## Relevance to lean-explore-bench

- **Scope.** zbMATH, Stacks/ProofWiki native search and the formula engines are not candidates for the Lean benchmark itself. They are paper-level, keyword-level or formula-level, and index no Lean.
- **LLM web search** is a realistic "what users do today" baseline for a cross-formality track, as TheoremSearch used it. It needs a frozen-cache protocol like Re²Math's to be reproducible.
- **Borrow from Re²Math:**
  - Freeze and publish raw responses from every live engine, including query, timestamp, settings and the ranked list.
  - Score from the frozen artifact only.
  - Allow citation-agnostic credit where more than one target is valid.
- **Borrow from AViD and the Matlas comparison:** report index coverage separately from ranking quality.

## Open questions

- What does zbMATH's experimental natural-language search actually do? It needs the EMS Magazine full text.
- Are there Chinese-language or other non-English statement search engines, for example inside publisher platforms, that we missed?

## Sources

- zbMATH Open API live call (2026-09-28): https://api.zbmath.org/v1/document/_search
- Teschke, "Natural language search queries in zbMATH Open", EMS Magazine 141 (2026) (metadata page only; content from search snippets, unverified): https://euromathsoc.org/magazine/articles/325
- FIZ Karlsruhe mathematics infrastructure page: https://www.fiz-karlsruhe.de/en/bereiche/mathematische-informationsinfrastruktur
- zbMATH Open Knowledge Graph: https://arxiv.org/abs/2609.00969
- Scharpf et al., ARQMath Lab and zbMATH Open: https://arxiv.org/abs/2012.02413
- Stacks Project (live check): https://stacks.math.columbia.edu/
- Re²Math (task definition, retrieval-artifact appendix read): https://arxiv.org/abs/2605.09012
- AViD Journal (related work, pipeline and coverage sections read): https://arxiv.org/abs/2608.14669
- TheoremSearch paper: https://arxiv.org/abs/2602.05216
