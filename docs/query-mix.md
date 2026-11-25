# The query mix

The query mix is the benchmark's query set. It has clear buckets, one per kind of query that
people and agents send to LeanExplore, and the queries in each bucket are written to match the
length and style of real searches of that kind. The first build has 1,781 queries in equal
forms; [the balanced benchmark](#the-balanced-benchmark) built from it has 3,200 queries in four
buckets, all with answers in Mathlib, and one score.

It exists because the 50-query [pilot](pilot-report.md) was too small and too uniform to say how
an engine behaves on any particular kind of query, and because existing Lean search benchmarks
draw on one library and one or two query styles.

## Query forms

Every query has exactly one of eight forms. A form is decided by the surface of the query alone
(which tokens look like Lean names, how many function words such as "of" or "the" it has, how
much Lean syntax), never by its subject. The rules are in `lean_explore_bench.mix.forms`.

| Form | Definition | Example |
| --- | --- | --- |
| `name` | One Lean name and nothing else | `Polynomial.expand_eq_zero` |
| `names` | Several Lean names and nothing else | `Std.HashSet.contains Std.HashSet.union` |
| `names+keywords` | Lean names with other words, no function words | `Equiv.Perm.support integer power apply membership iff` |
| `keywords` | Words only, no function words | `secret sharing unauthorized coalition subset remains unauthorized` |
| `prose` | Natural language, no Lean names or code | `empty list encoded in SKI calculus reduces to its second argument` |
| `prose+names` | Natural language with Lean names or code | `How do I check if a ByteArray iterator still has bytes remaining?` |
| `formal` | A Lean statement, signature or pattern | `0 < -?a ↔ ?a < 0` |
| `goal` | A proof state | `⊢ a ∈ J.unop ↔ MulOpposite.op a ∈ J` |

The same rules sort real searches and benchmark queries, so the two can be compared directly.

## What real searches look like

**How the search log was used.** Only to count: how searches divide over the eight forms, how
long they are, how many Lean names they hold, and how often they are lower case or questions. No
search query is in the benchmark, none was shown to a language model, and none was used to train
or tune anything. The counts do not record what a search was about, and counts under ten are
left out.

The figures below come from LeanExplore's search log from 29 September to 11 November 2026:
about 50,000 searches, 42,000 of them distinct. The analysis runs on the server that holds the
log and returns shares only; cells with fewer than ten queries are left out.

Share of searches in each form, by where the search came from:

| Form | All | Web | API | MCP | Median words |
| --- | ---: | ---: | ---: | ---: | ---: |
| `name` | 5.5% | 6.4% | 4.2% | 27.8% | 1 |
| `names` | 1.5% | 0.4% | 1.7% | 4.2% | 2 |
| `names+keywords` | 22.7% | 9.6% | 26.4% | 15.7% | 5 |
| `keywords` | 26.2% | 21.0% | 28.0% | 16.2% | 6 |
| `prose` | 23.9% | 46.2% | 17.9% | 26.3% | 11 |
| `prose+names` | 17.0% | 13.9% | 18.2% | 8.3% | 10 |
| `formal` | 2.8% | 2.6% | 3.0% | 1.6% | 11 |
| `goal` | 0.4% | none seen | 0.5% | none seen | 12 |

The API accounts for 77% of searches, the website for 20% and MCP for 3%. Website use is growing
and was the largest source in the first eleven days of November.

Other facts that shape the mix:

- Real queries are short: half have seven words or fewer and nine in ten have at most sixteen.
- About half of the `keywords` and `prose` queries are entirely in lower case.
- Questions are rare: 4% of `prose` and 2% of `prose+names` queries.
- LaTeX and backticks each appear in fewer than 1% of queries.
- 76% of searches set a package filter, and almost all filters are Mathlib alone or Mathlib with
  Lean core. Filters that include CSLib, FLT, Physlib or Formal Conjectures are under 1%.

**Agreement with the statistical categories.** The method of
[search categories](search-categories.md), which fits Gaussian mixtures to the same topic-free
features without any hand-written rule, finds eight stable top-level categories in this log. They
line up with the forms:

| Statistical category | Share of searches | Closest form or forms | Share by the rules |
| --- | ---: | --- | ---: |
| 1. Prose without names | 28.2% | `prose` | 23.9% |
| 2. Prose with names | 17.7% | `prose+names` | 17.0% |
| 3. Word runs without names | 22.6% | `keywords` | 26.2% |
| 4, 5, 6. Names with words, and several names | 22.3% | `names+keywords`, `names` | 24.2% |
| 7. A single name | 5.5% | `name` | 5.5% |
| 8. Symbol-heavy | 3.7% | `formal`, `goal` | 3.2% |

The two disagree by a few points, mostly at the border between prose and keyword runs.

## Shape of the mix

There are nine buckets: one per form, written from sampled declarations, and one of real
questions from the Lean Zulip. Each holds 200 queries, except `names` (182) and `prose+names`
(199), where too few written queries passed the checks.

The eight written buckets share one spread over libraries, so that half of each bucket lies
outside Mathlib:

| Library | Queries per bucket |
| --- | ---: |
| Mathlib | 100 |
| Lean core (`Init`, `Std`, `Batteries`) | 20 |
| Physlib | 20 |
| CSLib | 20 |
| FLT | 15 |
| Formal Conjectures | 15 |
| QuantumInfo | 10 |

QuantumInfo was dropped after this build as not relevant; the spread is now 20 each for FLT and
Formal Conjectures, and the combined mix below does not include it.

Equal buckets make each form measurable, but they are not how traffic is distributed: `formal`
and `goal` are 22% of the mix and 3% of searches. Scores are therefore reported twice: per
bucket, and as one figure weighted by each form's share of real searches. The library spread is
likewise a choice, not a reflection of traffic, and scores are reported per library.

## How queries are made

**Corpus.** Queries are written against a pinned LeanExplore snapshot (`20260714_172516`, 408,970
declarations). A declaration can be a target only if its own source introduces it by name, which
excludes generated declarations such as structure fields and `simps` lemmas. Deprecated
declarations and tooling modules are excluded as well; 285,375 declarations remain.

**Sampling.** Within a library, an area (the second component of the module name, for example
`Mathlib.Topology`) is drawn with probability proportional to the square root of its size, and a
declaration uniformly within it. No declaration is used twice.

**Name queries** are produced by a program: the exact name, the name without its leading
namespaces, the name with spaces for dots and underscores, the name with one typing error, or the
name in lower case. When a shortened name matches several declarations (at most five), each of
them counts as a correct answer.

**The other seven forms** are written by a language model (`anthropic/claude-sonnet-5.5`) that
sees the target declaration, the form, and a style drawn from the real searches of that form: a
word count, a number of Lean names, and whether to use lower case or ask a question. A written
query must then pass two checks:

1. Rule checks: the form rules sort the query into its own bucket, its length is within two words
   or 35% of the drawn word count, it does not contain the target's name, and it does not copy
   the docstring.
2. A judge from a different model family (`openai/gpt-6.1-terra`) must grade the target 3 on the
   0 to 3 scale of the [evaluation protocol](evaluation-protocol.md) and find the query specific
   enough that unrelated declarations would not answer it equally well.

A rejected query is rewritten, with the reason for the rejection, up to twice. If it still fails,
the target is dropped and a reserve target from the same cell takes its place.

**Zulip questions** come from the public channel "Is there code for X?". For each thread whose
replies name a declaration of the corpus, a language model rewrites the opening request as one
search query, in the asker's vocabulary, and grades the declarations that the thread offers as
answers (3 confirmed, 2 a useful alternative, 1 related). The judge then checks the best answer
against the query. Of the 1,650 most recently active threads, 249 gave an accepted query, and the
200 most recent are in the mix. Only the rewritten query, the graded answers and a link to the
thread are stored; message text and author names are not.

**Splits.** A fifth of the targets in every (bucket, library) cell form the development split
(356 queries) and the rest the test split (1,425 queries). Tuning should use the development
split only.

## How well the mix matches real searches

`leb-mix compare` measures the distance between two sets of queries with the Jensen-Shannon
divergence, which is 0 for identical distributions and 1 for disjoint ones. For the written
queries against the log:

| Form | Median words, real | Median words, mix | Length divergence | Length divergence, first build |
| --- | ---: | ---: | ---: | ---: |
| `name` | 1 | 1 | 0.00 | 0.00 |
| `names` | 2 | 2 | 0.03 | 0.74 |
| `names+keywords` | 5 | 6 | 0.06 | 0.29 |
| `keywords` | 6 | 7 | 0.07 | 0.15 |
| `prose` | 11 | 14 | 0.05 | 0.20 |
| `prose+names` | 10 | 14 | 0.08 | 0.35 |
| `formal` | 11 | 12 | 0.03 | 0.15 |
| `goal` | 12 | 16 | 0.28 | 0.46 |

The first build was written without reference to the log: its informal queries had a median of
28 words, and the `names+keywords` form, 23% of real searches, was almost absent from it.

Known gaps in the current build:

- Written `prose` queries run about three words long, and `prose+names` four.
- Too many written queries are in lower case: 72% of `keywords` against 48% in the log, and 79%
  of `prose` against 47%.
- Zulip questions are longer than search queries (median 23 words) and nearly all fall under
  `prose` or `prose+names`. They are kept as a separate bucket for that reason.
- Only form and style are matched. Subject matter is not: the log's topics are not used, by
  design, so that the mix does not mirror any user's research.

## Building and scoring

```sh
leb-mix profile  --log --to log-profile.json                 # on the server that holds the log
leb-mix generate --corpus lean_explore.db --out data/mix --style log-profile.json
leb-mix zulip    --corpus lean_explore.db --out data/mix
leb-mix build    --corpus lean_explore.db --out data/mix
leb-mix profile  --queries data/mix/queries.jsonl --to mix-profile.json
leb-mix compare  --reference log-profile.json --candidate mix-profile.json
leb-mix run      --engine leanexplore --out data/mix --split development
leb-mix score    --engine leanexplore --out data/mix --split development --weights log-profile.json
```

`build` writes `queries.jsonl` (every query with its provenance), `collection.development.json`
and `collection.test.json` (the format scored by the [offline evaluator](../tools/offline/README.md)),
and `summary.md`. `run` supports `leanexplore`, `leansearch`, `loogle` and `leanfinder`, spaces its
requests to respect each service, and resumes an interrupted run. `score` uses the offline
evaluator's metrics and reports them by query type, by library and weighted by real traffic;
`--group web`, `api` or `mcp` weights by one source.

`profile --queries` and `compare` accept any file of queries (JSON Lines with a `query` field, a
JSON list, or one query per line), so another query set can be measured against the log in the
same way.

Both builds together cost about 27 US dollars in model calls. The data is in `data/mix-v2/`
(and the first build in `data/mix-v1/`), which is not committed; whether and where to publish it
is still to be decided. The log profile is in `data/log-profile.json`.

## Results

These are scores on the test split (1,425 queries), run on 11 November 2026 against the hosted
engines with ten results per query. Each cell shows Success@10, the share of queries with a known
answer in the first ten results, and in brackets Success@1. A bucket holds about 160 queries (80
with a Mathlib target), so a difference of less than about 0.1 between two cells is within noise.
Two LeanExplore requests failed and count as misses.

All libraries:

| Bucket | Queries | LeanExplore | LeanSearch | Lean Finder | Loogle |
| --- | ---: | ---: | ---: | ---: | ---: |
| `name` | 160 | 0.95 (0.69) | 0.38 (0.30) | 0.34 (0.22) | 0.17 (0.17) |
| `names` | 146 | 0.78 (0.25) | 0.40 (0.15) | 0.43 (0.21) | 0.06 (0.01) |
| `names+keywords` | 160 | 0.88 (0.39) | 0.43 (0.19) | 0.44 (0.31) | 0.00 (0.00) |
| `keywords` | 160 | 0.88 (0.44) | 0.42 (0.19) | 0.43 (0.26) | 0.00 (0.00) |
| `prose` | 160 | 0.76 (0.38) | 0.43 (0.23) | 0.43 (0.27) | 0.00 (0.00) |
| `prose+names` | 159 | 0.85 (0.40) | 0.40 (0.28) | 0.39 (0.28) | 0.00 (0.00) |
| `formal` | 160 | 0.50 (0.19) | 0.42 (0.24) | 0.39 (0.24) | 0.07 (0.06) |
| `goal` | 160 | 0.48 (0.08) | 0.42 (0.28) | 0.43 (0.34) | 0.02 (0.01) |
| `question` (Zulip) | 160 | 0.33 (0.17) | 0.49 (0.14) | 0.49 (0.26) | 0.00 (0.00) |
| All | 1,425 | 0.71 (0.33) | 0.42 (0.22) | 0.42 (0.27) | 0.04 (0.03) |

LeanSearch and Lean Finder return almost nothing outside Mathlib, which is consistent with their
indexing Mathlib only, and Loogle accepts names and patterns, not prose. LeanExplore scores higher
on the other libraries (0.77 to 0.83 in the first ten, 0.63 on core) than on Mathlib (0.67).
Restricted to the 774 queries whose target is in Mathlib (`score --library mathlib`):

| Bucket | Queries | LeanExplore | LeanSearch | Lean Finder | Loogle |
| --- | ---: | ---: | ---: | ---: | ---: |
| `name` | 80 | 0.94 (0.65) | 0.74 (0.59) | 0.68 (0.44) | 0.28 (0.28) |
| `names` | 78 | 0.77 (0.27) | 0.76 (0.28) | 0.79 (0.40) | 0.09 (0.00) |
| `names+keywords` | 80 | 0.85 (0.38) | 0.85 (0.38) | 0.89 (0.61) | 0.00 (0.00) |
| `keywords` | 80 | 0.90 (0.48) | 0.84 (0.39) | 0.86 (0.53) | 0.00 (0.00) |
| `prose` | 80 | 0.71 (0.35) | 0.85 (0.46) | 0.85 (0.54) | 0.00 (0.00) |
| `prose+names` | 80 | 0.83 (0.44) | 0.79 (0.55) | 0.78 (0.55) | 0.00 (0.00) |
| `formal` | 80 | 0.49 (0.16) | 0.84 (0.49) | 0.78 (0.48) | 0.10 (0.10) |
| `goal` | 80 | 0.39 (0.05) | 0.84 (0.56) | 0.85 (0.68) | 0.03 (0.01) |
| `question` (Zulip) | 136 | 0.35 (0.19) | 0.57 (0.16) | 0.57 (0.31) | 0.00 (0.00) |
| All | 774 | 0.67 (0.32) | 0.77 (0.41) | 0.77 (0.49) | 0.05 (0.04) |

Weighted by each form's share of real searches (written queries only; Zulip questions are left
out because they are not written like search queries):

| Weights | Targets | LeanExplore | LeanSearch | Lean Finder | Loogle |
| --- | --- | ---: | ---: | ---: | ---: |
| All searches | All libraries | 0.84 (0.43) | 0.41 (0.22) | 0.42 (0.27) | 0.02 (0.01) |
| All searches | Mathlib | 0.82 (0.43) | 0.83 (0.44) | 0.83 (0.54) | 0.02 (0.02) |
| Web searches | Mathlib | 0.80 (0.42) | 0.83 (0.46) | 0.82 (0.53) | 0.02 (0.02) |
| API searches | Mathlib | 0.83 (0.43) | 0.83 (0.44) | 0.84 (0.54) | 0.02 (0.02) |
| MCP searches | Mathlib | 0.84 (0.46) | 0.80 (0.48) | 0.79 (0.51) | 0.10 (0.09) |

What stands out:

- On Mathlib, weighted by real traffic, the three engines are level in the first ten results
  (0.82 to 0.83). Lean Finder ranks the answer first more often (0.54 against 0.43 and 0.44).
- LeanExplore is the only engine that covers the other libraries, and that is its whole lead in
  the all-libraries row.
- LeanExplore is best on single names (0.94 against 0.74 and 0.68 on Mathlib) and level on
  keyword forms.
- LeanExplore is behind on plain prose on Mathlib (0.71 against 0.85). Prose is 24% of all
  searches and 46% of web searches.
- Proof states and formal statements are LeanExplore's weak forms on Mathlib (0.39 and 0.49 in
  the first ten, against about 0.8 for the other two). They are 3% of searches.
- On real Zulip questions LeanExplore trails both (0.35 against 0.57 on Mathlib). These queries
  are the only ones not written from LeanExplore's own descriptions.

The development split (356 queries) had suggested a LeanExplore lead on Mathlib (0.85 against
0.76 and 0.78). With four times as many queries that lead is gone, so it was noise. The first
build, whose queries were two to three times longer than real ones, had put LeanExplore behind
on keyword queries; with real lengths it is level or ahead there.

## The balanced benchmark

The mix above has equal forms and no single score. The benchmark built on 13 November 2026 has
four buckets of 800 queries (3,200 in all), defined by what the searcher is doing:

| Bucket | Queries | Made of |
| --- | ---: | --- |
| Names and keywords | 800 | 160 `name`, 80 `names`, 240 `names+keywords`, 320 `keywords` |
| Natural language | 800 | 480 `prose`, 320 `prose+names` |
| Formal | 800 | 480 `formal`, 320 `goal` |
| Real questions | 800 | Queries from Lean Zulip threads |

**The benchmark score is the plain mean of the four bucket scores.** Weighting by LeanExplore's
own traffic would favour it: its traffic is heavy on names and keywords, where it does well, and
light on formal queries, where it does badly, because people learn what an engine handles and
send it that. Each bucket is a kind of search that exists apart from any one engine, so each
counts once. A fifth of every bucket is the development split (640 queries); the rest is the
test split (2,560).

**Mathlib only, and only established declarations.** The benchmark measures search, not
coverage. Every engine indexes Mathlib, and no other library is indexed by all of them, so every
answer is a Mathlib declaration. Engines also index Mathlib at different dates: on declarations
added after January 2026, LeanSearch and Lean Finder scored 0.00 where they scored above 0.9 on
older ones. A declaration is therefore a target only when it has the same name and module in a
January 2026 snapshot (`--established`); 88% of Mathlib declarations do.

**Real questions.** This bucket holds 590 queries that Pietro Pellegrino derived from Zulip
threads and 210 of the mix's own. A thread query is kept when the judge grades at least one
answer 2 or 3, and it must be in its own words: one that repeats more than five consecutive
words of a post is rejected. Of the 1,807 contributed queries, 767 were accepted; 648 had no
proposed answer that is an eligible declaration of the corpus, 349 had every proposed answer
rejected by the judge, 34 contained an answer's name, and 9 copied a post. Of the accepted ones,
177 are left out here because their answers lie outside Mathlib or are not established. 515
contributed queries could not be checked against their post; those accepted are included
unchecked.

**Writers.** Queries are written by a language model and accepted by a judge from another family
(`openai/gpt-6.1-terra`). Of the 2,400 written queries, 1,294 were written by Claude Opus agents
working from exported tasks (`leb-mix tasks`), 624 were written by
`anthropic/claude-sonnet-5.5`, reviewed by an Opus agent and kept, 322 are Opus rewrites of
Sonnet queries, and 160 bare-name queries are made by rule. Agent-written queries go through the
same rule checks and judge (`leb-mix submit`, `leb-mix zulip --queries`), and a rewrite replaces
an accepted query only when the judge accepts it (`leb-mix submit --revise`). Every record names
its writer.

**Formal queries at natural length.** Written queries normally follow a word count drawn from
real searches. For Lean statements and proof states that produced padding (redundant type
ascriptions, made-up subterms, irrelevant hypotheses) and squeezing (spaces removed, hypotheses
dropped). These two forms are written at the length of the statement.

**Pooled answers.** A written query starts with one labelled answer, the declaration it was
written from, although other declarations may answer it equally well. To correct this, the top
ten results of the four engines were pooled for each query, each engine's list cut at its first
labelled answer, and candidates outside Mathlib or not established removed. Claude Opus agents
graded the 20,141 remaining candidates of 2,669 queries, seeing them in name order with no
engine or rank. Candidates graded 2 or 3 were added as labels: 1,551 answers on 984 queries
(`leb-mix pool`). Because each list is cut at its first labelled answer, Success@k and
reciprocal rank are exact with respect to full pooling of the top ten; nDCG is not.

```sh
leb-mix zulip      --corpus lean_explore.db --out data/mix
leb-mix contribute --corpus lean_explore.db --out data/mix --queries contributed.jsonl
leb-mix generate   --corpus lean_explore.db --out data/mix --style log-profile.json \
                   --shape balanced --established january.db
leb-mix build      --corpus lean_explore.db --out data/mix --shape balanced --established january.db
leb-mix run        --engine leanexplore --out data/mix
leb-mix pool       --corpus lean_explore.db --out data/mix --shape balanced --established january.db \
                   --until-answer --to tasks.jsonl
leb-mix pool       --corpus lean_explore.db --out data/mix --grades grades.jsonl --judge NAME
leb-mix score      --engine leanexplore --out data/mix --split test
```

**Results** on the test split (640 queries per bucket), run on 11 to 13 November 2026:
Success@10, with Success@1 in brackets.

| Bucket | LeanExplore | LeanSearch | Lean Finder | Loogle |
| --- | ---: | ---: | ---: | ---: |
| Names and keywords | 0.91 (0.52) | 0.93 (0.62) | 0.94 (0.75) | 0.07 (0.07) |
| Natural language | 0.86 (0.48) | 0.98 (0.72) | 0.98 (0.88) | 0.00 (0.00) |
| Formal | 0.54 (0.14) | 0.95 (0.68) | 0.96 (0.89) | 0.10 (0.10) |
| Real questions | 0.50 (0.27) | 0.77 (0.46) | 0.80 (0.56) | 0.00 (0.00) |
| **Benchmark score** | **0.70 (0.35)** | **0.91 (0.62)** | **0.92 (0.77)** | **0.04 (0.04)** |

Before pooling the benchmark scores were 0.63 (0.28), 0.85 (0.49), 0.87 (0.64) and 0.04 (0.04).
Pooling raised every engine and changed no ranking. Loogle searches by name and pattern, so only
bare names and some formal statements suit it.

## Limits

- **Pooled labels cover only what was returned.** Extra answers were found among the results of
  four engines. A new engine may return a valid answer that none of them did, and it will count
  as a miss until that result is judged. Pooled grades come from one model family, and LeanExplore
  results outside Mathlib or newer than January 2026 were not judged.
- **No human validation yet.** Queries and the acceptance decision both come from language
  models. The two models are from different families, but neither is a mathematician.
- **Hosted engines are not pinned.** Each engine indexes its own snapshot of the libraries, and
  some index Mathlib only. A target that an engine does not index counts as a miss.
- **The writer sees LeanExplore's descriptions.** The writer model is shown LeanExplore's own
  natural-language description of each target, and LeanExplore searches over those descriptions,
  so written queries may share wording with its index. The Zulip bucket is free of this bias.
- **Every query has an answer.** There is no track yet for requests that no indexed declaration
  answers, nor for declarations added after the snapshot.
