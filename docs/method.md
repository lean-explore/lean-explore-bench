# Method

How the benchmark was made: the forms of a query, what real searches look like, how
queries and answers were produced, and what the benchmark does not yet do.

## Query forms

Every written query has one of eight forms. A form is decided by the surface of the
query alone (which tokens look like Lean names, how many function words such as "of"
or "the" it has, how much Lean syntax), never by its subject. The rules are in
`lean_explore_bench.mix.forms`.

| Form | Definition | Example |
| --- | --- | --- |
| `name` | One Lean name and nothing else | `Stonean fully Faithful To Comp Haus` |
| `names` | Several Lean names and nothing else | `Dynamics.coverMincard IsCompact` |
| `names+keywords` | Lean names with other words, no function words | `IsLocallyConstructible intersection closed` |
| `keywords` | Words only, no function words | `annihilator span singleton membership` |
| `prose` | Natural language, no Lean names or code | `tail of interleaving two infinite streams` |
| `prose+names` | Natural language with Lean names or code | `the MulAction.orbit of any point under a monoid action is Set.Nonempty` |
| `formal` | A Lean statement, signature or pattern | `ManyOneEquiv u v → (ManyOneEquiv u w ↔ ManyOneEquiv v w)` |
| `goal` | A proof state | `⊢ WithBot.succ x = ⊥ ↔ x = ⊥` |

## Buckets

The forms are grouped into four buckets of 800 queries, defined by what the searcher
is doing.

| Bucket | Queries | Made of |
| --- | ---: | --- |
| Names and keywords | 800 | 160 `name`, 80 `names`, 240 `names+keywords`, 320 `keywords` |
| Natural language | 800 | 480 `prose`, 320 `prose+names` |
| Formal | 800 | 480 `formal`, 320 `goal` |
| Real questions | 800 | Queries derived from Lean Zulip threads (form `question`) |

The benchmark score is the plain mean of the four bucket scores. Weighting by
LeanExplore's own traffic would favour LeanExplore: its traffic is heavy on names and
keywords and light on formal queries, because people learn what an engine handles
and send it that.

## What real searches look like

The forms and their typical lengths come from LeanExplore's search log from
29 September to 11 November 2026: about 50,000 searches, 42,000 of them distinct.

**How the log was used.** Only to count: how searches divide over the forms, how long
they are, how many Lean names they hold, and how often they are lower case or
questions. No search query is in the benchmark, none was shown to a language model,
and none was used to train or tune anything. The counts do not record what a search
was about, they are computed on the server that holds the log, and counts under ten
are left out.

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

The API accounts for 77% of searches, the website for 20% and MCP for 3%. Half of
all searches have seven words or fewer, and nine in ten have at most sixteen. About
half of the `keywords` and `prose` searches are entirely in lower case, and questions
are rare (4% of `prose`).

## Answers are established Mathlib declarations

The benchmark measures search, not coverage. Every engine indexes Mathlib, and no
other library is indexed by all of them, so every answer is a Mathlib declaration.

Engines also index Mathlib at different dates. In an earlier build, on declarations
added after January 2026, LeanSearch and Lean Finder scored 0.00 where they scored
above 0.9 on older ones. A declaration can therefore be an answer only when it has
the same name and module in a January 2026 snapshot; 88% of the Mathlib declarations
in the corpus do.

The corpus is the LeanExplore snapshot `20260714_172516` (408,970 declarations). A
declaration can be a target only if its own source introduces it by name, which
excludes generated declarations such as structure fields and `simps` lemmas.
Deprecated declarations and tooling modules are excluded as well.

## Written queries

The first three buckets (2,400 queries) are written from a target declaration.

**Sampling.** An area of Mathlib (the second component of the module name, for
example `Mathlib.Topology`) is drawn with probability proportional to the square
root of its size, and a declaration uniformly within it. No declaration is used
twice.

**Name queries** (160) are made by a program: the exact name, the name without its
leading namespaces, the name with spaces for dots and underscores, the name with one
typing error, or the name in lower case. The `variant` field records which.

**The other seven forms** are written by a language model that sees the target, the
form, and a style drawn from the real searches of that form: a word count, a number
of Lean names, and whether to use lower case or ask a question. `formal` and `goal`
queries are written at the length of the statement instead, because a drawn word
count led to padded or squeezed Lean.

A written query must pass two checks:

1. Rule checks: the form rules sort the query into its own form, its length is close
   to the drawn word count, it does not contain the target's name, and it does not
   copy the docstring.
2. A judge from another model family (`openai/gpt-6.1-terra`) must grade the target
   3 and find the query specific enough that unrelated declarations would not answer
   it equally well.

A rejected query is rewritten, with the reason, up to twice. If it still fails, the
target is dropped and a reserve target takes its place.

**Writers.** Claude Opus wrote 1,294 of the queries. Claude Sonnet 5.5 wrote 946;
Claude Opus reviewed them, kept 624 and rewrote 322, and a rewrite replaced a query
only when the judge accepted it. The `writer_model` and `rewritten` fields record
this for every query.

## Real questions

The fourth bucket (800 queries) comes from Lean Zulip threads in which someone asks
for a result and a reply names a declaration.

- **210 queries** come from the channel "Is there code for X?". A language model
  rewrites the opening request as one search query, in the asker's vocabulary and
  without seeing the replies. The declarations that the replies name are proposed
  answers.
- **590 queries** were contributed by Pietro Pellegrino from an earlier collection of
  discussion-derived queries, made the same way. For 38 of them the writer had seen
  the replies; `writer_saw_answers` records this.

A thread query is kept when the judge grades at least one proposed answer 2 or 3.
Of the 1,807 contributed queries, 767 were accepted, and 177 of those are left out
because their answers lie outside Mathlib or are not established.

The benchmark contains no text of any post and no author name: a thread query that
repeats more than five consecutive words of a post is rejected. Only the rewritten
query, its graded answers and, where recorded, a link to the thread are stored.

## Pooled answers

A written query starts with one labelled answer, the declaration it was written
from, although other declarations may answer it equally well. To correct this, the
first ten results of four engines (LeanExplore, LeanSearch, Lean Finder and Loogle)
were pooled for each query. Each engine's list was cut at its first labelled answer,
and candidates outside Mathlib or not established were removed.

Claude Opus graded the 20,141 remaining candidates of 2,669 queries, seeing them in
name order with no engine and no rank. Candidates graded 2 or 3 were added as
labels: 1,551 answers on 984 queries. They are marked `pooled` in the data.

Pooling raised the benchmark score of the three semantic engines by 5 to 8 points
and changed no ranking.

## Limits

- **No human review.** Queries, acceptance and grades all come from language models.
  Writer and judge are from different model families, but neither is a mathematician.
- **Pooled labels cover only what four engines returned.** A new engine can return a
  correct answer that is not labelled, and it counts as a miss until it is graded.
  The BM25 baseline is in this position.
- **The writer sees LeanExplore's descriptions.** The model that writes a query is
  shown LeanExplore's natural-language description of the target, and LeanExplore
  searches over those descriptions, so written queries may share wording with its
  index. The real questions bucket does not have this bias.
- **One library at one date.** Every answer is a Mathlib declaration that existed in
  January 2026.
- **Every query has an answer.** There are no queries that nothing answers.
- **Style, not subject, matches real searches.** Written queries follow the lengths
  and forms of real searches. Their subjects come from sampling Mathlib, not from
  what people search for.

## Building

Building from scratch needs the corpus snapshot (`lean_explore.db`), the January 2026
snapshot, an `OPENROUTER_API_KEY`, and for `zulip` a `~/.zuliprc`. `generate`,
`zulip` and `contribute` stop at a spending limit (`--budget`) and resume where they
stopped.

```sh
leb-mix profile    --log --to log-profile.json           # on the server that holds the log
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
leb-mix export     --out data/mix --to release --card docs/dataset-card.md \
                   --engine leanexplore leansearch leanfinder loogle bm25
```

`leb-mix tasks` and `leb-mix submit` export writing tasks for an agent and take its
queries back through the same checks. `leb-mix profile --queries` and
`leb-mix compare` measure how far any set of queries is from the real searches.
