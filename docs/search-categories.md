# Search categories and query distribution

How people and agents search LeanExplore, found statistically from the query
log.

**Data:** about 9,000 searches (about 8,580 distinct queries) logged on
2026-09-29. Over 99% came from one API client, most likely an agent, so these
categories describe that client more than human searchers.

**Disclosure control:** counts are rounded to the nearest 10 and every share
is computed from rounded counts; groups under 10 are suppressed.

**Method:** each distinct query is measured on topic-free features only:
length, share of Lean identifiers, share of English function words (prose),
share of symbols, and a *skeleton* that keeps its structure but drops its
content (`ID` for a Lean name, `W` for any other word). Gaussian mixtures are
fitted to these features, and the largest number of categories whose
categories all reproduce on subsamples (Jaccard at least 0.75) is kept. The
same rule is then applied inside each category. Code:
`lean_explore_bench.analysis.categories`.

Because no feature encodes subject matter, the categories describe *how*
people search, not *what about*.

## Top-level categories

| Category | Share of searches | Median words | Identifier share | Prose share | Stability (Jaccard) |
|---|---|---|---|---|---|
| 1. Prose | 48.00% | 13 | 0.09 | 0.20 | 0.96 |
| 2. Keyword runs | 33.67% | 6 | 0.13 | 0.00 | 0.89 |
| 3. Identifier-heavy | 18.22% | 4 | 0.56 | 0.00 | 0.81 |

Three is the largest number of top-level categories that are all stable. With
four or more, at least one category fails to reproduce on subsamples.

## Subcategories

Prose queries have no stable split. The other two split by length and by
where Lean names appear.

| Category | Share of searches | Median words | Identifier share | Most common skeletons |
|---|---|---|---|---|
| 2.1 Long word runs | 10.67% | 7 | 0.00 | `W W W W W W W` · `W W W W W W` |
| 2.2 Name, then many words | 5.67% | 7 | 0.14 | `ID W W W W W` · `ID W W W W W W` |
| 2.3 Name, then a few words | 4.44% | 5 | 0.22 | `ID W W W W` · `ID W W W` |
| 2.4 Short word runs | 4.11% | 5 | 0.00 | `W W W W W` · `W W W W` |
| 2.5 Two names, then words | 3.11% | 5 | 0.38 | `ID ID W W` · `ID ID W W W` |
| 2.6 Word, name, words | 2.00% | 5 | 0.19 | `W ID W W` · `W ID W W W` |
| 2.7 Words, then a name | 2.00% | 5 | 0.20 | `W W W W ID` · `W W W ID` |
| 2.8 Name and two words | 1.78% | 3 | 0.33 | `ID W W` |
| 3.1 Names mixed with words | 8.33% | 5 | 0.34 | `ID W W ID` · `ID W ID` · `W ID` |
| 3.2 Names, then a word | 4.56% | 5 | 0.56 | `ID ID W` · `ID ID ID W` |
| 3.3 Names only | 3.33% | 3 | 0.94 | `ID ID` · `ID ID ID` |
| 3.4 Single name | 2.00% | 1 | 0.85 | `ID` · `ID W` |

Every subcategory has a Jaccard of at least 0.75 over subsamples. The names
in the first column describe each category's measurements; they were added
after fitting and play no part in it.

## Sources

| Source | Share of searches |
|---|---|
| API | 99.33% |
| MCP and web | suppressed (web is under 10 searches, so MCP is suppressed with it) |

## Query length

Words per distinct query (median 8).

| Words | Share of distinct queries |
|---|---|
| 1–2 | 4.31% |
| 3–8 | 48.48% |
| 9–16 | 34.50% |
| 17+ | 12.82% |

## Other distributions

| Measure | Share of searches |
|---|---|
| With a package filter (almost all `Mathlib`) | 99.22% |
| Repeating an earlier query | 4.67% |
