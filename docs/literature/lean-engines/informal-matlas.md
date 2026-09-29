# Matlas (PKU BICMR AI4M / FrenzyMath), informal statement search over journals and textbooks

- **Kind:** search engine (informal only)
- **Links:**
  - site: https://matlas.ai/
  - API docs (Swagger): https://matlas.ai/docs; OpenAPI at https://matlas.ai/openapi.json
  - paper: "Matlas: A Semantic Search Engine for Mathematics", https://arxiv.org/abs/2604.17484
  - blog: https://frenzymath.com/blog/matlas/
  - legacy arXiv engine (the "preliminary Matlas" used by Rethlas): https://leansearch.net/thm/
  - consumer: Rethlas/Archon, https://arxiv.org/abs/2604.03789; see [../premise-selection/agents-with-search-tools.md](../premise-selection/agents-with-search-tools.md)
- **Authors / org, date:** Haocheng Ju, Leheng Chen, Peihao Wu, Bryan Dai, Bin Dong (Peking University BICMR / IQuest Research). arXiv 2026-04-19 ([arXiv](https://arxiv.org/abs/2604.17484)).
- **Status (checked 2026-09-28):**
  - **Live.** `GET /api/health` returned `{"ok":true}`. `POST /api/search` returned 10 results in about 0.7 s, served through Cloudflare. No authentication was needed and no rate-limit headers were returned (checked by us). AViD likewise reports "public APIs without authentication" ([arXiv:2608.14669](https://arxiv.org/abs/2608.14669)).
  - No MCP server was found.
  - **Code and data.** The paper lists `https://huggingface.co/FrenzyMath/matlas` as a data link, but the HF API returned an auth error for both the dataset and model paths (checked by us). We treat the corpus as **unreleased** (unverified: it may be private).
  - The legacy arXiv engine at `leansearch.net/thm/search` still answered in about 0.4 s. Rethlas says it "will be deprecated in the near future" ([arXiv:2604.03789 footnote in §3](https://arxiv.org/abs/2604.03789)).

## What it is

Matlas is a dense retriever over **mathematical statements** (definitions, theorems, lemmas and so on) taken from **published** papers and textbooks rather than from arXiv. The stated motivations are reliability (peer review) and self-containedness ([paper §1](https://arxiv.org/abs/2604.17484)).

- **Corpus:**
  - 8.07M statements from 435K papers (1826–2025) in 180 journals. A journal was kept if its 2007–2021 papers received more than 50 citations from ICM proceedings and it published at least 100 papers in that period.
  - Plus 1.9K textbooks from Springer, Princeton, Cambridge, Oxford and AMS.
  - PDFs were obtained from MathSciNet metadata and processed with OCR ([paper §3.1](https://arxiv.org/abs/2604.17484)).
- **Conflicting corpus sizes.** Three figures circulate:
  - **13.6M** arXiv statements: the preliminary system used in Rethlas, at leansearch.net/thm. This is the figure quoted in our [agents-with-search-tools.md](../premise-selection/agents-with-search-tools.md).
  - **8.07M**: the Matlas paper.
  - **8.51M**: the "latest Matlas" according to the Rethlas v2 footnote ([arXiv:2604.03789](https://arxiv.org/abs/2604.03789)).

  Which one the live matlas.ai serves is unverified. Our test query returned textbook hits (e.g. *Understanding Analysis* Thm 4.4.2), consistent with the journal and textbook corpus.
- **Formal content: none.** The paper cites LeanSearch, LeanExplore, Lean Finder and LeanDex only as related work ([paper §2](https://arxiv.org/abs/2604.17484)). The API result schema has `type ∈ {book, paper}` only. In Rethlas/Archon the Lean-side search is **LeanSearch**, used by Archon, not Matlas ([arXiv:2604.03789](https://arxiv.org/abs/2604.03789)).

## How it works (brief)

- **Extraction.** DeepSeek-V3.2 writes a regular expression for each document to locate statements. An LLM "structurer" then extracts each statement's type, content and local dependencies ([paper §3.2](https://arxiv.org/abs/2604.17484)).
- **Unfolding.** Statements are recursively *unfolded* layer by layer over each document's dependency DAG, so that each indexed statement is self-contained ([paper §3.3](https://arxiv.org/abs/2604.17484)).
- **Retrieval.** Qwen3-Embedding-8B embeds the statement with an instruction prefix and ranks by cosine similarity. There is no reranker and no LLM summary; the unfolded statement itself is embedded ([paper §3.3](https://arxiv.org/abs/2604.17484)).

## Evaluation

- **The Matlas paper reports no retrieval evaluation**: no queries, labels, metrics or numbers (full LaTeX read). The blog is likewise qualitative ([FrenzyMath blog](https://frenzymath.com/blog/matlas/)).
- **Rethlas case study** ([arXiv:2604.03789 §4](https://arxiv.org/abs/2604.03789)):
  - The preliminary arXiv Matlas surfaced Jensen (2006), a key ingredient in the counterexample to Anderson's Problem 8a.
  - The Rethlas agent is instructed to query Matlas *first*, then web search.
  - This is anecdotal evidence only; the paper has no search ablation (see [agents-with-search-tools.md](../premise-selection/agents-with-search-tools.md)).
- **Third-party head-to-head vs TheoremSearch (April 2026)**, run by the TheoremSearch team ([matlas-comparison README](https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/matlas-comparison/README.md)):
  - **Overlap set.** Built from 748 arXiv papers whose `journal-ref` is one of 17+ Matlas-covered journals (2010–2021). Presence in each engine was verified *by metadata only*: an arXiv-id lookup for TheoremSearch, and a title in the Matlas top-50 for a title query. **Only 258 of the 748 (35%) were in both.** The authors say Matlas coverage "thins out post-2020 and is patchier than the '180 journals × 1826-2025' description suggests."
  - **Sample.** 50 papers and 200 non-headline theorems: the first two theorem environments were skipped, then four were sampled per paper.
  - **Queries.** Each theorem got a *precise* and a *vague* paraphrase from gpt-5.2 via the Codex CLI, giving 400 queries.
  - **Grading:**
    - Paper level uses a strict normalized-title match.
    - Theorem level requires the paper match *and* at least 2 shared normalized word-4-grams with the target body. This was hand-checked on about 30 cases.
  - **Results:**

    | | TheoremSearch | Matlas |
    |---|---|---|
    | Paper @1 / @10 | 51% / 68% | 51% / 73% |
    | Theorem @1 / @10 | 45% / 62% | 41% / 62% |
    | Theorem @10, precise / vague | 78% / 45% | 76% / 48% |

  - **Caveats (the authors' own):** selection bias toward papers Matlas already indexes, a single LLM paraphraser, a heuristic theorem match, and a single API snapshot.
  - **Harness lesson.** Running with 8 parallel threads produced 29 of 400 empty Matlas responses from transient failures. All were recovered by re-running sequentially with retries.
- **AViD Journal** ([arXiv:2608.14669](https://arxiv.org/abs/2608.14669)) queried Matlas and TheoremSearch for prior versions of duplicate-withdrawn arXiv papers. None of the 12 named duplicators was found in either index, even by exact-name search. Most were pre-1991 journal results, which is exactly Matlas's claimed niche.
  - AViD also notes that Matlas candidates carry a DOI and year rather than an arXiv id. **Temporal filtering is therefore only year-level.**

## Programmatic access (for a harness)

- **`POST https://matlas.ai/api/search`** takes `{"query": str, "num_results": int}`, where `num_results` must be between 10 and 200 (default 10).
  - It returns a list of `{type: "book"|"paper", entity_name (e.g. "Theorem 4.4.2 (Extreme Value Theorem)"), doi, title, authors, journal, year, statement, candidate_id}` (from the OpenAPI spec; confirmed by a live call).
  - There are no filters (source, year, type) and no scores.
- **`POST /api/feedback`** takes `{query, candidate_id, label: relevant|irrelevant}`. A benchmark harness must **not** call it, to avoid polluting their logs.
- **Legacy arXiv engine.** `POST https://leansearch.net/thm/search` takes `{"query", "task", "num_results"}`, where `task` is an instruction string sent by the web UI. It returns `[{theorem, theorem_id, arxiv_id, title}]` (read from the page's `main.js`; confirmed by a live call).

## Relevance to lean-explore-bench

- **Not a Lean engine.** Matlas cannot be scored on Mathlib gold. It belongs, if anywhere, in a **cross-formality/informal comparison track**, where the information need is "does this result exist, and where?".
- **Coverage is the dominant variable.** The 35% overlap finding and AViD's zero-recall result both say that informal engines differ mainly in *what they index*. Any comparison must therefore:
  - report the index snapshot;
  - restrict scoring to targets verified present *by metadata, not by the engine's semantic search* (TheoremSearch's overlap protocol is a good template);
  - separate out "target not indexed" as its own outcome, just as for Lean engines ([theoremgraph.md](../premise-selection/theoremgraph.md)).
- **Reusable protocol pieces from the head-to-head:**
  - Skip headline theorems, so that we test deep lemmas.
  - Use paired precise and vague queries per target. This stratification exposes a 30-point gap and maps directly onto our query-style strata.
  - Score at two granularities: paper (module/file for Lean) and statement.
- **Engineering.** The service is fast (under 1 s) but has no documented rate limit. Run sequentially with retries, and cache raw responses: there is no versioned index, so results are tied to the query date.

## Open questions

- Which corpus (8.07M or 8.51M) and which extraction version does matlas.ai serve today? Is there any public changelog?
- Will the corpus or the unfolded statements be released? The HF link in the paper is not publicly readable.
- Does Matlas plan an MCP endpoint, or any formal (Lean) index?

## Sources

- Matlas paper (full LaTeX read): https://arxiv.org/abs/2604.17484
- Rethlas/Archon paper (full text searched for Matlas passages, including the footnote giving the 13.6M and 8.51M figures): https://arxiv.org/abs/2604.03789
- FrenzyMath blog: https://frenzymath.com/blog/matlas/
- matlas.ai OpenAPI and live `/api/health` and `/api/search` calls (run by us, 2026-09-28): https://matlas.ai/openapi.json
- leansearch.net/thm page, `main.js` and live `/thm/search` call (run by us, 2026-09-28): https://leansearch.net/thm/
- TheoremSearch vs MATLAS benchmark: https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/matlas-comparison/README.md
- AViD Journal: https://arxiv.org/abs/2608.14669
- Lean Zulip Rethlas+Archon announcement: https://leanprover.zulipchat.com/#narrow/near/583591174
