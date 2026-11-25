# TheoremSearch (UW Math AI Lab), informal theorem search with a formal side-index

- **Kind:** search engine (informal, with a Mathlib index added by the TheoremGraph follow-up)
- **Links:**
  - site: https://www.theoremsearch.com/
  - REST API: `POST https://api.theoremsearch.com/search`; OpenAPI at https://api.theoremsearch.com/openapi.json; Swagger UI at https://api.theoremsearch.com/docs
  - MCP: `https://api.theoremsearch.com/mcp`
  - paper: "Semantic Search over 9 Million Mathematical Theorems", https://arxiv.org/abs/2602.05216 (ICLR 2026 Workshop on Logical Reasoning of LLMs)
  - code: https://github.com/uw-math-ai/TheoremSearch
  - data: https://huggingface.co/datasets/uw-math-ai/theorem-search-dataset
  - follow-up (formal graph, Mathlib index): [../premise-selection/theoremgraph.md](../premise-selection/theoremgraph.md)
- **Authors / org, date:** Luke Alexander, Eric Leonen, Sophie Szeto, Artemii Remizov, Ignacio Tejeda, Jarod Alper, Giovanni Inchiostro, Vasily Ilin (University of Washington). arXiv v1 2026-02-05, v2 2026-03-07 ([arXiv](https://arxiv.org/abs/2602.05216)).
- **Status (checked 2026-09-28):**
  - **Live.** The site returned HTTP 200. `POST /search` answered a test query with HTTP 200 in about 21 s. `/graph/embedding` answered in about 20 s. MCP `tools/list` returned the single tool `theorem_search`. All checks were ours.
  - **No authentication.** No rate-limit headers were returned (the response came through an `envoy` proxy), and no rate limit is documented on the site or in the OpenAPI spec (checked by us). AViD also reports that the API has "no authentication" ([arXiv:2608.14669 §2](https://arxiv.org/abs/2608.14669)).
  - The TheoremSearch team's own head-to-head against Matlas saw transient empty responses (76 of 400) when running 8 parallel threads. Every request succeeded once re-run sequentially with retries ([matlas-comparison README](https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/matlas-comparison/README.md)). **Treat the service as low-concurrency.**
  - The repo was last pushed 2026-08-19 (GitHub API). The HF dataset was last modified 2026-02-20 and is licensed CC BY-SA 4.0.

## What it is

TheoremSearch retrieves **individual theorem-like statements** rather than papers. The site states "9+ million theorems across 7 sources" ([theoremsearch.com](https://www.theoremsearch.com/)). The paper breaks the corpus down as follows ([paper §3](https://arxiv.org/abs/2602.05216)):

- 9.2M statements from arXiv papers tagged math, stat, cs, physics, eess, econ, q-fin or q-bio;
- 23,871 from ProofWiki;
- 12,693 from the Stacks Project;
- small numbers from the Open Logic Project, the CRing Project, Stacks and Moduli, the HoTT Book and *An Infinitely Large Napkin*.

**Index snapshot.** The paper's datasheet says "Data was collected over five months, from September 2025 to January 2026." We found no per-deployment snapshot date on the live site.

**Formal side.** The TheoremGraph follow-up added Lean declarations to the same backend ([theoremgraph.md](../premise-selection/theoremgraph.md)). They are *not* reachable through `/search` or the MCP tool: a `sources: ["Lean Community"]` or `["Mathlib"]` filter on `/search` returned zero results in our checks. They are reachable through `GET /graph/embedding?formality=formal`, which returned Mathlib declarations, e.g. `ContinuousOn.exists_isMaxOn'`, with source `"Lean Repo"` and title `"Mathlib_v427"`. `/paper-search?q=Mathlib` lists **three Mathlib snapshots as separate "papers": `Mathlib_v427`, `Mathlib_v428` and `Mathlib_v429`** (checked by us). A Lean Zulip user independently reported the same split: `POST /search` and the MCP "only returns informal arXiv results, not lean declaration". The same user noted that there is no filter restricting `/graph/embedding` to Mathlib only, and no endpoint exposing the judged formal–informal matches ([Zulip, 2026-07-01](https://leanprover.zulipchat.com/#narrow/near/607697173)). Our `formality=formal` parameter did restrict results to formal statements. We did not check whether non-Mathlib Lean projects are also returned.

## How it works (brief)

- **Representation.** An LLM (DeepSeek V3) writes a "slogan" for each statement. The slogan prompt was given the body plus paper context, and the ablation favoured body plus introduction ([paper §3.3, §4.5](https://arxiv.org/abs/2602.05216)).
- **Embedding and index.** Qwen3-Embedding-8B, stored in pgvector with an HNSW index over binary-quantized vectors. The top candidates by Hamming distance are then reranked by cosine similarity ([paper §3.4](https://arxiv.org/abs/2602.05216)).
- **Live service** ([paper, "Search Tool" appendix](https://arxiv.org/abs/2602.05216)):
  - The candidate pool is `clamp(max(200, 12k), 200, 800)`.
  - Optional citation weighting: `score = cos + λ·log(max(citations,1))`.
  - Short queries are automatically duplicated ("Landau equation Landau equation") because slogan-trained embeddings handle keyword queries poorly.
  - The paper quotes a latency of about 3 s per query. We measured about 20 s on 2026-09-28.

## Evaluation

**1. Paper's validation set** ([paper §3.5, §4, Table "embedder-table"](https://arxiv.org/abs/2602.05216))
- **Queries.** 111 queries across 14 arXiv tags, mostly algebraic geometry, analysis and PDE. Three research mathematicians wrote them *blind*, from memory, about theorems by authors they know well.
- **Labels.** Each query has a single target (theorem number plus paper). The target was checked by an LLM for existence and semantic match, then by a second mathematician.
- **Metrics.** Hit@1, Hit@10, Hit@20 and MRR@20, at theorem level and at paper level.
- **Corpus for evaluation.** Restricted to arXiv papers.
- **Numbers** (theorem-level / paper-level):

  | System | Hit@1 | Hit@10 | Hit@20 | MRR@20 |
  |---|---|---|---|---|
  | Google `site:arxiv.org` (paper only) | – / 0.162 | – / 0.378 | – / 0.378 | – / 0.237 |
  | arXiv search (paper only) | – / 0.009 | – / 0.018 | – / 0.027 | – / 0.011 |
  | ChatGPT 5.2 w/ search | 0.117 | 0.180 | 0.198 | 0.139 |
  | Gemini 3 Pro | 0.171 | 0.252 | 0.270 | 0.196 |
  | Qwen3-Emb-8B | 0.171 / 0.243 | 0.387 / 0.505 | 0.450 / 0.568 | 0.243 / 0.328 |
  | Qwen3-Emb-8B + Qwen3-Reranker-0.6B (top-100) | 0.189 / 0.324 | 0.432 / 0.613 | 0.450 / 0.631 | 0.270 / 0.416 |

  - LLM answers with the correct result but a wrong theorem number count as theorem-level misses and paper-level hits.
  - The site advertises Hit@10 of 0.432 at theorem level and 0.505 at paper level ([theoremsearch.com](https://www.theoremsearch.com/)). Those two figures come from **different rows** of the table: the reranked theorem-level score and the non-reranked paper-level score.
  - Whether the live service uses the reranker is unverified. The paper's service description mentions only cosine reranking.
- **Ablations** (slogan context, LLM, embedder) were run on a 7,356-statement math.AG sub-corpus ([paper §4.5](https://arxiv.org/abs/2602.05216)).
- **Released test set.** The HF dataset's `theorem-test` config ships **110** of these queries with columns `query`, `theorem number`, `paper title` and `link to paper on arxiv` (we downloaded and inspected it). The dataset card reports the same Hit@20 figures on "110 test queries" ([HF card](https://huggingface.co/datasets/uw-math-ai/theorem-search-dataset)).
- **Released corpus.** Only about 15% of the corpus (1,341,083 statements, the arXiv papers under CC BY, CC BY-SA or CC0, plus the other sources) is released. The remaining 85% cannot be redistributed ([HF card](https://huggingface.co/datasets/uw-math-ai/theorem-search-dataset)). **The live index is therefore not reproducible offline.**

**2. Real-user-query RAG study (repo only, not in the paper)** ([experiments/user_queries/README.md](https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/user_queries/README.md))
- **Queries.** 748 production-log queries from January–February 2026, filtered to 302 research-level queries. GPT-5.4-mini split these into 148 "NICHE", 96 "FAMOUS" and 58 "VAGUE". The study uses 96 NICHE queries of 8–30 words.
- **Conditions and judge.** GPT-5.2 with web search is compared against the same model with the `theorem_search` tool added. A GPT-5.4 pairwise judge scores answers on a 1–5 scale.
- **Results.**
  - Overall, the tool *lowers* the mean score from 3.72 to 3.15, with a 36/96 win rate.
  - On the 36 queries where the baseline scored 3 or less, the tool wins 32/36 and raises the mean from 2.56 to 3.94.
  - Caveat (ours): stratifying by the baseline's own score invites regression-to-the-mean effects, and the judge is an LLM.
- **Finding relevant to a harness.** Keyword-style agent queries perform poorly, and "claim-style" queries (a full mathematical statement) work much better.

**3. Head-to-head vs Matlas (April 2026, repo only)**
- This comparison is summarized in [informal-matlas.md](informal-matlas.md).
- Theorem-level @10: 62% for TheoremSearch and 62% for Matlas.
- Theorem-level @1: 45% for TheoremSearch and 41% for Matlas.

**4. Formal retrieval (TheoremGraph)**
- The MathlibQR fair-810 comparison against LeanSearch v2 is covered in [../premise-selection/theoremgraph.md](../premise-selection/theoremgraph.md) and is not repeated here.
- Those numbers come from the TheoremGraph retrieval configuration, not from the informal `/search` endpoint.

**Third-party evidence**
- AViD Journal ([arXiv:2608.14669](https://arxiv.org/abs/2608.14669), 2026-08-02) used TheoremSearch plus Matlas as its informal corpus for novelty checking.
- Of 12 known pre-existing results ("duplicators") behind duplicate-withdrawn arXiv papers, **none was found by exact-name search in either engine**. The authors conclude that "the recall ceiling is imposed by the coverage of theorem indices, not by the similarity metric" (§ "Coverage of the Retrieval Corpora").

## Programmatic access (for a harness)

- **`POST /search`** accepts a JSON body with the following fields (from the OpenAPI spec):
  - `query`, `n_results` (default 10), `sources`, `authors`, `types`, `tags`, `paper_filter`;
  - `year_range`, `citation_range`, `citation_weight`, `include_unknown_citations`;
  - `prompt` (the embedding instruction) and `db_top_k` (the ANN pool).
- **`/search` response.** `{"theorems":[{theorem_id, slogan_id, name, body, slogan, theorem_type, paper{paper_id, source, title, authors, link, year, citations, ...}, similarity, score}]}`.
- **`GET /graph/embedding`** takes `query`, `n_results` (at most 100), `formality` (`informal`/`formal`/`both`), `sources`, `types`, `mode` (`full`/`minimal`) and others.
  - For formal hits, `name` is the placeholder `"Thm"`. The Lean declaration name is only the first token of `body` (the pretty-printed signature), so **a harness must parse it**.
  - Because three Mathlib versions are indexed, the same declaration can appear several times: **dedupe by declaration name**.
  - One of our results showed the same `statement_id` twice with different slogans, so **dedupe by `statement_id` as well**.
- **MCP.** One tool, `theorem_search`, with the same arguments as `/search`. It is informal only.

## Relevance to lean-explore-bench

- **Not a Lean engine on its main endpoint.** `/search` and the MCP can only be scored on *informal* targets, such as a paper or theorem number. They cannot be scored against Mathlib gold, so they cannot sit in the main Lean track.
- **The `/graph/embedding?formality=formal` endpoint** *can* be scored as a Lean engine on our query sets, but with care:
  - The index is Mathlib v4.27–v4.29 only. Record this snapshot, and use a fair-subset or "target absent" outcome as [theoremgraph.md](../premise-selection/theoremgraph.md) recommends.
  - The harness has to parse declaration names out of `body` and dedupe across versions.
  - Latency is about 20 s per query, so runs must be sequential with retries.
- **Reusable evaluation assets:**
  - The released 110-query mathematician-written test set, a blind-query protocol worth copying for our own human-written queries.
  - Theorem-level and paper-level (partial-credit) scoring.
  - The explicit rule that a right result with the wrong theorem number is a miss.
- **Cross-formality track input.** A Lean-side query set whose gold also carries an informal counterpart (Stacks tags, `100.yaml`; see [../math-ir/informal-formal-alignment.md](../math-ir/informal-formal-alignment.md)) would let TheoremSearch's informal endpoint and the Lean engines be scored on the *same* information need: "find this result, formal or informal".
- **Methodological warnings:**
  - The headline Hit@10 figures on the website mix configurations.
  - The live index cannot be rebuilt from released data (85% withheld), so results against the live service are tied to a date.
  - The claim-style versus keyword-style sensitivity means query-style stratification is mandatory.

## Open questions

- Does the live service apply the Qwen3 reranker? The paper's best row uses it, but the service description does not mention it.
- Which Lean projects besides Mathlib are indexed on the formal side, and which snapshot is served by default?
- The paper reports 111 queries while the release has 110. Which query was dropped, and does that change the published numbers?

## Sources

- Paper (LaTeX read via arXiv, including the methodology, experiments, search-tool appendix and datasheet): https://arxiv.org/abs/2602.05216
- Site (fetched 2026-09-28): https://www.theoremsearch.com/
- OpenAPI (fetched 2026-09-28): https://api.theoremsearch.com/openapi.json
- Live queries to `/search`, `/graph/embedding`, `/paper-search` and `/mcp` (run by us, 2026-09-28)
- HF dataset card and `theorems-test.parquet` (downloaded 2026-09-28): https://huggingface.co/datasets/uw-math-ai/theorem-search-dataset
- Repo experiments: https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/user_queries/README.md , https://github.com/uw-math-ai/TheoremSearch/blob/main/experiments/matlas-comparison/README.md
- Lean Zulip, TheoremGraph announcement thread: https://leanprover.zulipchat.com/#narrow/near/607529041 , https://leanprover.zulipchat.com/#narrow/near/607697173
- AViD Journal: https://arxiv.org/abs/2608.14669
