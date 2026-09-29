# Production code search engines: GitHub Blackbird, Zoekt, Google Code Search, Kythe (and how they were evaluated)

- **Kind:** search engine cluster
- **Links:**
  - GitHub Blackbird https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/
  - Zoekt https://github.com/sourcegraph/zoekt (design doc https://github.com/sourcegraph/zoekt/blob/main/doc/design.md)
  - Google Code Search / trigram index https://swtch.com/~rsc/regexp/regexp4.html (code https://github.com/google/codesearch)
  - Kythe https://kythe.io/
- **Authors / org, date:** Russ Cox (Jan 2012); Zoekt (Google origin, maintained by Sourcegraph since 2017); Timothy Clem, GitHub (Feb 6, 2023)
- **Status:** Blackbird is proprietary and live. Zoekt is Apache-2.0 and active (last push Sept 2026, per `gh repo view`). google/codesearch is open source. Kythe is open source.

## What it is

These are large-scale **lexical / regex** code search engines. They share one design: an n-gram inverted index narrows candidates, a real regex or substring match confirms them, and ranking uses code-specific signals. Scope per the request: record only how they evaluate their search.

## How it works

- **Google Code Search (2006–2011):**
  - A trigram inverted index. Each regex is converted to an AND/OR trigram query, and the candidate files are then scanned with the full regex.
  - The index was about 20% of corpus size in the example (Linux 3.1.3: 420 MB source → 77 MB index), with about 100x speedup on sample queries ([Cox 2012](https://swtch.com/~rsc/regexp/regexp4.html)).
- **Zoekt:**
  - *Positional* trigrams: offsets are stored, so a substring query intersects just two posting lists. The index is about 3x corpus size, and memory use is about 1.2x corpus size.
  - Goal: "sub-50ms results on large codebases, such as Android (~2G text) or Chrome" on one machine ([design.md](https://github.com/sourcegraph/zoekt/blob/main/doc/design.md)).
  - Ranking uses "code-related signals like whether the match is on a symbol". ctags symbol information is "a key signal in ranking" ([README](https://github.com/sourcegraph/zoekt)).
- **GitHub Blackbird (Rust):**
  - *Why not existing tools:* general text-search products gave "poor" UX for code. Brute-force ripgrep over 115 TB would need 2,048 cores for 96 s per query (0.01 QPS).
  - *Index:* n-gram indices with variable-length "sparse grams" instead of fixed trigrams, sharded by Git blob object ID for even load and deduplication.
  - *Scale:* 45M repositories, 115 TB, 15.5B documents, 28 TB unique content, 25 TB index.
  - *Performance:* 120k docs/s ingest, about 18 h full reindex, about 100 ms p99 per shard, about 640 QPS per 64-core host ([GitHub blog](https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/)).
- **Kythe:** "a pluggable, (mostly) language-agnostic ecosystem for building tools that work with code". It has a graph schema, per-language indexers and a cross-reference service ([kythe.io](https://kythe.io/)). This is the "semantic cross-reference" layer (go-to-definition, find-references) rather than text search.

## Evaluation

- **Published evaluations are almost entirely systems metrics:** latency (p99), throughput (QPS, ingest rate), index size and reindex time ([Blackbird](https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/), [Zoekt design](https://github.com/sourcegraph/zoekt/blob/main/doc/design.md), [Cox](https://swtch.com/~rsc/regexp/regexp4.html)).
- **Recall is not evaluated, because it is exact by construction.** Regex/substring search returns every match, so relevance evaluation reduces to *ranking* the matches. No public ranking-quality evaluation (NDCG, query sets, judgments) was found for Blackbird, Zoekt or Google Code Search (searched; none found).
- Sourcegraph's later AI-context evaluations used ~90 queries and internal annotated sets (see [code-embedding-vs-grep-evidence.md](code-embedding-vs-grep-evidence.md)).

## Known flaws

- For benchmark purposes, the lack of published relevance evaluation means these systems give no reusable qrels or query sets.
- Exact-match engines cannot answer NL intent queries. They are only as good as the user's (or agent's) guess of the identifier.

## Relevance to lean-explore-bench

- **Name and regex queries are a distinct regime:** recall is trivially 100% and ranking is everything. For Lean name-style queries, evaluate *ranking among exact/partial-name matches* (for example, `sum_comm` matches dozens of namespaces). Symbol-aware ranking, as Zoekt ranks declaration matches above body matches, is the relevant analogue.
- **A trigram or ripgrep index over Mathlib source is the natural lexical baseline.** Blackbird's numbers show it scales to far bigger corpora, and Mathlib is small (on the order of 10^5 declarations; unverified count).
- **Kythe-style cross-reference is the analogue of Lean's environment:** `#find`, find-usages and the dependency graph. That supports "decl → related decl" evaluation.
- **Report systems metrics too** (latency, index build time, index staleness relative to Mathlib), since production engines are chosen on them.

## Open questions

- Does GitHub publish any code-search relevance evaluation (for example, in "A brief history of code search at GitHub")? (not checked)

## Sources

- GitHub, The technology behind GitHub's new code search (Feb 6, 2023): https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/
- Zoekt README and design doc: https://github.com/sourcegraph/zoekt ; https://github.com/sourcegraph/zoekt/blob/main/doc/design.md
- Russ Cox, Regular Expression Matching with a Trigram Index (2012): https://swtch.com/~rsc/regexp/regexp4.html
- google/codesearch: https://github.com/google/codesearch
- Kythe: https://kythe.io/
