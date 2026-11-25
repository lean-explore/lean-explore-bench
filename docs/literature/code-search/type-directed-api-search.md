# Type-directed and signature-based API search outside Lean (and how it was evaluated)

- **Kind:** search engine cluster + papers
- **Links:**
  - Hoogle <https://hoogle.haskell.org/>, code <https://github.com/ndmitchell/hoogle>
  - Hayoo <https://github.com/hunt-framework/hayoo>
  - rustdoc search <https://doc.rust-lang.org/stable/rustdoc/read-documentation/search.html>, tests <https://github.com/rust-lang/rust/tree/master/tests/rustdoc-js-std>
  - Sherlodoc (OCaml) <https://github.com/ocaml/odoc/tree/master/sherlodoc>; Dowsing (OCaml) <https://github.com/Drup/dowsing/>
  - Scaps (Scala) thesis <https://luegg.github.io/scaps/thesis.pdf>, paper <https://dl.acm.org/doi/10.1145/2998392.2998405>
  - TypeSearch (Java) <https://eprints.ost.ch/id/eprint/1196/>
  - Idris `:search` <https://docs.idris-lang.org/en/latest/reference/type-directed-search.html>
  - Coq SearchIsos <https://www.lirmm.fr/~delahaye/papers/type-isos%20(TYPES'99).pdf>; Agda Aegle <https://github.com/wasabi315/aegle>
  - Rittri, "Using types as search keys in function libraries", JFP 1(1), 1991 <https://www.cambridge.org/core/journals/journal-of-functional-programming/article/using-types-as-search-keys-in-function-libraries/BA56BB3061DB73396847E37048544E19>
  - Zaremski & Wing, "Signature matching", TOSEM 1995 <https://doi.org/10.1145/210134.210179>
- **Authors / org, date:** 1989–2026. Details per entry.
- **Status:** Hoogle, rustdoc search, Sherlodoc (inside odoc), Dowsing, and Aegle are open source and active. Hayoo's repo was last pushed 2018-02-19, and `hayoo.fh-wedel.de` did not answer on 2026-09-28 (`gh api`, curl).

The companion note [type-directed-synthesis-user-studies.md](type-directed-synthesis-user-studies.md) covers Hoogle+, TyGAR, Prospector, PARSEWeb, InSynth and other "search that composes" tools. Those tools carry most of this area's user studies and query-log analyses.

## What it is

These engines take a **type signature, possibly partial or approximate, as the query** and return library functions whose types "fit". Loogle's own author calls it "inspired by Haskell's Hoogle" (see [../lean-tools/loogle.md](../lean-tools/loogle.md)). The scope here is **how these engines were evaluated**, not how they work. Only the relevance notion is kept from the mechanism, because it determines what "correct" means.

## How it works (relevance notion only)

| System | What counts as a match | Ranked? |
|---|---|---|
| Rittri 1989/1991 (Lazy ML) | Types equal **modulo CCC isomorphism** (argument order, currying), or matching modulo isomorphism so library types more general than the query are found ([JFP paper](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/BA56BB3061DB73396847E37048544E19/S095679680000006Xa.pdf/using-types-as-search-keys-in-function-libraries.pdf)) | No, it returns a set |
| Runciman & Toyn 1989 (as summarized by Rittri) | Types **unifiable** with the query, plus a generality order where a library function may take extra arguments (Rittri §6.1, same PDF) | Partial order |
| Zaremski & Wing 1995 (SML) | "Exact match but also various flavors of relaxed match", for functions and modules ([abstract via Crossref](https://api.crossref.org/works/10.1145/210134.210179)) | Not checked (unverified) |
| Coq SearchIsos (Delahaye, TYPES'99) | Isomorphism for dependent types (an extension of the λ-calculus axiomatization to ECC), decided for Coq ([PDF](https://www.lirmm.fr/~delahaye/papers/type-isos%20(TYPES'99).pdf)) | No |
| Hoogle | "Approximate type signature" ([README](https://github.com/ndmitchell/hoogle)). A cheap fingerprint scan keeps the top 100, then a costlier full-type comparison ranks them ([Mitchell 2020](http://neilmitchell.blogspot.com/2020/06/hoogle-searching-overview.html)) | Yes, heuristic cost |
| Idris 1 `:search` | Shortest path of edits (argument transposition, symmetry of equality, argument application, type-class application/introduction), each with a score. Results are "listed in order of ascending score" ([docs](https://docs.idris-lang.org/en/latest/reference/type-directed-search.html)) | Yes, edit cost |
| rustdoc | Order-agnostic parameters; parameters may be omitted; wrappers (references, `Box`, `Rc`, `Arc`, `Option`, `Result`, `Future`, …) may be omitted; type parameters never match concrete types; supertraits, aliases and `Deref` are ignored. "Closer" matches rank higher, split into *In Names / In Parameters / In Return Types* tabs ([rustdoc book](https://doc.rust-lang.org/stable/rustdoc/read-documentation/search.html)) | Yes |
| Sherlodoc | Polarity decomposition (positive vs. negative positions) plus arity. Static score (short names, short types, has docs) is adjusted by a dynamic name and type tree-diff similarity. Self-described "very limited support for polymorphic variables, type aliases and true type isomorphisms" ([README](https://github.com/art-w/sherlodoc)) | Yes |
| Dowsing | Types more general than the query **up to isomorphisms** (currying, argument reordering), "sound and complete"; unification modulo isomorphism is NP-complete ([repo](https://github.com/Drup/dowsing/); paper "Light-speed type unification modulo isomorphisms", Arrighi & Radanne, [HAL](https://inria.hal.science/hal-04794390v1), not read because HAL blocked automated access) | Not checked (unverified) |
| Scaps (Scala) | Vector-space "fingerprint" model over type terms, with subtyping and implicit-conversion "type views" ([thesis](https://luegg.github.io/scaps/thesis.pdf) ch. 3) | Yes |
| Aegle (Agda) / TyDe 2025 | Unification modulo Π-swap, Σ-swap, Σ-assoc and currying, plus generalisation and alias expansion ([README](https://github.com/wasabi315/aegle)). The paper argues that SearchIsos and Loogle each support "only a subset" of these flexibilities ([Takimoto, Moriguchi, Watanabe, TyDe 2025](https://dl.acm.org/doi/10.1145/3759538.3759651), via search-result abstract) | Not checked (unverified) |

There are two schools. **Formal relevance** (Rittri, SearchIsos, Dowsing, Aegle, and Loogle itself) treats a hit as correct iff it satisfies a decidable relation (isomorphism, unification, instance), so the result is a set. **Heuristic ranking** (Hoogle, Idris, rustdoc, Sherlodoc, Scaps) returns a ranked list, and "correct" means *the function the user wanted* ranks high.

## Evaluation

**Summary: almost none of these tools has an IR-style evaluation.** The evaluation modes found, from weakest to strongest:

### 1. Worked examples plus timing (the formal-relevance papers)

- **Rittri:** the whole evaluation is performance. "For the type-files of the Lazy ML standard library, with 194 identifiers, a search takes typically 3–6 cpu seconds, 1–5 of which are due to the parsing". The matching-modulo-isomorphism prototype takes "usually around 2 CPU seconds" (JFP §5, §6.2). Correctness is by theorem, and usefulness is argued with examples.
- **Runciman & Toyn:** support their approach "with a statistical investigation of some typical functional libraries" (per Rittri §6.1). The details were not read (unverified).
- **SearchIsos:** four example queries with timings, e.g. `(A:Prop)A\/~A` → `classic` in about 1 s on a DEC Alpha (§6 of the PDF). No query set and no relevance metric.
- **Idris `:search`, Dowsing, Aegle, Hayoo:** no retrieval-quality evaluation was found. The TyDe 2025 abstract only claims a prototype that demonstrates "feasibility" (unverified beyond the abstract).

### 2. Regression suites of rank assertions (Hoogle, rustdoc, Sherlodoc)

These are the most transferable artifacts: **hand-curated "query → expected hit at rank ≤ k" test cases run in CI.**

- **Hoogle** (`src/Action/Search.hs`, commit [`df554c4`](https://github.com/ndmitchell/hoogle/blob/df554c496c676874a889cc6526e154c2d8b5bc7d/src/Action/Search.hs#L201-L330), 2026-07-04):
  - About 40 top-hit checks, mostly by name (`"map" === …#v:map`) and three by type (`"(a -> b) -> [a] -> [b]" === …#v:map`), plus **21 type queries carrying about 50 rank assertions**.
  - The assertion vocabulary: `TopHit`, `InTop k`, `RanksBelow k`, `DoesNotFind`, `AppearsBefore a b`, `NoHits`, and **`KnownFailure reason`**, which wraps an assertion expected to fail, usually with a GitHub issue number.
  - Examples: `"(a -> [a]) -> [a] -> [a]"` → `TopHit concatMap`, `InTop 10 (=<<)`, and `KnownFailure $ InTop 50 (>>=)`. `"a -> b"` → `TopHit unsafeCoerce`, `DoesNotFind id`. `"[a] -> a"` → `InTop 10 head`, `DoesNotFind repeat`.
  - 19 of the assertions are `KnownFailure`, so the suite doubles as a **public list of known ranking bugs** (issues #127, #180, #266–#269).
  - Earlier history: "a log of all the searches performed was used to determine where Hoogle didn't match the users expectations", and v3 shipped a separate "regression testing" executable ([Mitchell, "Hoogle Overview", Monad.Reader 12, 2008](https://ndmitchell.com/downloads/paper-hoogle_overview-19_nov_2008.pdf), pp. 30, 33).
  - No aggregate metric is reported. On the second ranking phase: "For a long time (a few years) I hadn't even bothered doing the second phase … and it still gave reasonable results" ([blog 2020](http://neilmitchell.blogspot.com/2020/06/hoogle-searching-overview.html)).
- **rustdoc:**
  - `tests/rustdoc-js-std/` has 68 files run against the real `std`/`core` index, including `option-type-signatures.js`, `iterator-type-signatures.js`, `vec-type-signatures.js`, and `return-based-sort.js`. `tests/rustdoc-js/` has 159 fixture crates (counts via GitHub API at `c1070d6`, 2026-09-28).
  - Each file lists `EXPECTED = [{query, others|in_args|returned: [items…]}]`. The tester ([`src/tools/rustdoc-js/tester.js`](https://github.com/rust-lang/rust/blob/master/src/tools/rustdoc-js/tester.js)) checks that every expected item is present and **in the listed relative order** (a subsequence, not necessarily contiguous).
  - Directives change the check: `// ignore-order` drops the order check, `// exact-check` requires exactly those results in exactly that order, and `// should-fail` expects failure. `correction` fields test "did you mean" type-name corrections.
  - Per-tab expectations (names vs. parameters vs. return types) are a clean way to score one query against several relevance notions.
- **Sherlodoc:** cram (golden-output) tests under `sherlodoc/test/cram/` (`query_syntax.t`, `cli_poly.t`, `size_bound.t`, `prefix_favouritism.t`, …) and a `base_benchmark.t` that "is not deterministic. Please just check that the values are not crazy" ([odoc `6dc5826`](https://github.com/ocaml/odoc/tree/master/sherlodoc/test/cram)). This is snapshot testing, with no relevance metric.

### 3. A small IR test collection (Scaps, 2015/2016)

This is **the only classic Cranfield-style evaluation found for a type-search engine** ([thesis](https://luegg.github.io/scaps/thesis.pdf) ch. 5).

- **Corpus:** Scala standard library + Scalaz + Scala Refactoring, over 100,000 entities. Scalaz is included mainly to "add noise".
- **Queries:** **52 information needs**, partly "derived from" Q&A questions about the standard library, each with ≥1 relevant identifier.
- **Relevance:** binary, and "a result is only relevant if it answers the information need and not if it just has the identical type signature as the query". This is **task relevance, not type relevance**.
- **Query taxonomy:** navigational vs. informational (after Broder), generic vs. concrete query types (a user may type `List[Int] => Int` for a generic `sum`), and textual vs. type-directed.
- **Metrics:** MAP and Recall@10.
- **Results:**
  - A text-matching baseline got MAP 0.57 / R@10 0.69, and Baseline+All (depth boost, type frequencies, fractions) got 0.62 / 0.74.
  - The full model (FEM+All) got **MAP 0.70 / R@10 0.85**.
  - Ablations: removing type-frequency weighting dropped MAP to 0.55, and removing distance boost dropped it to 0.61 (Table 5.2, Fig. 5.2).
  - Per-query results (Table 5.3) show the type-aware model losing on some simple queries, e.g. `List[A] => (List[A], List[A])`: AP 0.63 vs. 0.81.
- **The author's own list of flaws (§5.7):**
  1. the baseline is too close to the system, with no comparison to a real tool like Hoogle;
  2. **"we use the same test collection to find a good parametrization … and to assess the score"**, since parameters were tuned by random search over 50–500 configurations per variant;
  3. the collection "is biased towards our retrieval model", since queries were chosen to be answerable and there was "no data on the actual usage patterns of real user interactions".

### 4. Self-retrieval with generated queries (TypeSearch, Java, 2024)

- **Protocol:** sample 1,000 JDK 21 functions, use each function's **own exact signature as the query**, and record the rank of that function in the results (41,208 "relevant" JDK functions, index of 40,000) ([TypeSearch report](https://eprints.ost.ch/id/eprint/1196/1/MA_TypeSearch_TechnicalReport.pdf) ch. 7).
- **Latency:** mean 1,212 ms, median 239 ms, p90 2,078 ms, p99 24,127 ms (Table 7.1), with scaling by index size.
- **Quality:** a histogram of the sample's rank, with misses beyond 100 clamped to 100 (Fig. 7.3). No summary number is reported.
- **Logging for the future:** all queries are logged, *including syntactically invalid ones*, plus per-result like/dislike buttons, "to eventually get real feedback" (§7.3).

### 5. Surveys, logs, and user studies

- The only **quantitative Hoogle usage data** found comes from the Hoogle+ authors: **3.8M Hoogle queries (Jan 2015 – Feb 2019), 71K syntactically unique, about 60K not exactly solved by Hoogle**, of which many were ill-formed or unrealizable ([Guo et al., POPL 2020, §6](https://arxiv.org/abs/1911.04091)).
- The same group surveyed **151 Haskell programmers**. 84 named Hoogle as their first-choice engine; among those listing Hoogle, 121 search by type and 107 by name ([James et al., OOPSLA 2020, §7](https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla20-hplus.pdf)).
- The same paper's controlled user study used **Hoogle as the control condition**. See [type-directed-synthesis-user-studies.md](type-directed-synthesis-user-studies.md).
- No Rust, OCaml, Scala, Idris, or Agda type-search user study or log analysis was found (unverified; searched, not exhaustive).

## Relevance to lean-explore-bench

Loogle and `exact?` are Lean's members of the formal-relevance school ([../lean-tools/loogle.md](../lean-tools/loogle.md), [../lean-tools/exact-apply.md](../lean-tools/exact-apply.md), [../lean-tools/symbolic-baselines.md](../lean-tools/symbolic-baselines.md)). The literature above transfers as follows.

1. **Keep two relevance labels per query.**
   - **(a) Formal:** "the declaration matches the pattern", decidable and computed by Loogle or `isDefEq`.
   - **(b) Task:** "the declaration is what the user wanted", i.e. the gold lemma, as in Scaps's rule that an identical signature is not enough.
   - Loogle is perfect on (a) by construction, so it can only be *compared* on (b). A semantic engine can be scored on both, with (a) giving precision-of-set and (b) giving MRR/Recall@k.
2. **Adopt Hoogle's and rustdoc's assertion vocabulary as a regression tier** next to the aggregate metrics: `TopHit`, `InTop k`, `DoesNotFind` (hard negatives, e.g. a lemma with the right head symbol but the wrong direction), `AppearsBefore`, and **`KnownFailure` with a reason**. It is cheap to write, readable in diffs, and records known ranking bugs without failing CI. rustdoc's per-tab expectations map onto Lean as *matches in hypotheses vs. matches in conclusion*, i.e. Loogle's `⊢` filter.
3. **Stratify pattern queries by the flexibility they require:**
   - exact form;
   - argument or hypothesis reordering (Π-swap);
   - currying/uncurrying (`∧` vs. `→ →`, `∃` vs. Σ);
   - generalisation (query about `ℝ`, lemma about a `LinearOrderedField`);
   - extra hypotheses in the lemma;
   - symmetry (`a = b` vs. `b = a`), which is Idris's rule; how Loogle handles it was not checked (unverified);
   - alias/notation unfolding.

   These are exactly the axes Rittri, Runciman & Toyn, Idris, rustdoc, and Aegle each chose different subsets of. Per-stratum recall shows *which* flexibility each Lean engine lacks. Aegle's claim that Loogle covers only a subset makes this a direct test.
4. **Query sources, in order of realism:**
   1. **Logs:** real Loogle queries if obtainable, e.g. Zulip `@loogle` bot messages are public. TyGAR's filtering pipeline shows the cost: 3.8M → 1,750 popular → 180 valid → 24 usable.
   2. **Q&A-derived needs** (Scaps; Zulip "is there a lemma…" threads).
   3. **Generated patterns** from gold statements by abstracting subterms. This is TypeSearch's self-retrieval protocol, which is easy to scale but only tests exact-form recall. **Perturb** the pattern (reorder, generalise, swap sides) to reach the harder strata.
5. **Avoid Scaps's two named mistakes:** keep a **held-out split** for any tuning, and do not select queries by "our engine can answer it". Include unanswerable or zero-result queries: TyGAR found many Hoogle queries unrealizable, and a good engine should return nothing or say so.
6. **Report latency percentiles** (TypeSearch's p50/p90/p99). Type search has heavy tails: TypeSearch's p99 was 20× its median, and unification modulo isomorphism is NP-complete. Loogle's `heartbeats` field is a natural cost column.
7. **Treat set-returning engines honestly.** Formal engines return unranked sets, so report set size and hit/recall, or impose a documented deterministic order before computing MRR. The same caveat appears in the Loogle note.

## Open questions

- Do Hoogle's raw query logs remain available to researchers? The Hoogle+ group had 2015–2019 logs, but the access terms are unknown (unverified).
- Is there any retrieval-quality evaluation of Dowsing, or in the TyDe 2025 Aegle paper? Neither PDF could be read here.
- Is there a Loogle query log, or can one be reconstructed from Zulip `@loogle` messages?

## Sources

- Rittri JFP 1991 PDF: <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/BA56BB3061DB73396847E37048544E19/S095679680000006Xa.pdf/using-types-as-search-keys-in-function-libraries.pdf>
- Zaremski & Wing abstract: <https://api.crossref.org/works/10.1145/210134.210179>
- Delahaye, SearchIsos: <https://www.lirmm.fr/~delahaye/papers/type-isos%20(TYPES'99).pdf>
- Hoogle README and tests: <https://github.com/ndmitchell/hoogle>, <https://github.com/ndmitchell/hoogle/blob/df554c496c676874a889cc6526e154c2d8b5bc7d/src/Action/Search.hs>
- Hoogle Overview (Monad.Reader 12): <https://ndmitchell.com/downloads/paper-hoogle_overview-19_nov_2008.pdf>
- Hoogle searching overview blog: <http://neilmitchell.blogspot.com/2020/06/hoogle-searching-overview.html>
- Hayoo repo: <https://github.com/hunt-framework/hayoo>
- rustdoc search docs: <https://doc.rust-lang.org/stable/rustdoc/read-documentation/search.html>; tests: <https://github.com/rust-lang/rust/tree/master/tests/rustdoc-js-std>; tester: <https://github.com/rust-lang/rust/blob/master/src/tools/rustdoc-js/tester.js>; original feature request: <https://github.com/rust-lang/rust/issues/12866>
- Sherlodoc: <https://github.com/art-w/sherlodoc>, <https://github.com/ocaml/odoc/tree/master/sherlodoc>
- Dowsing: <https://github.com/Drup/dowsing/>; Arrighi & Radanne: <https://inria.hal.science/hal-04794390v1>
- Scaps thesis: <https://luegg.github.io/scaps/thesis.pdf>; SCALA 2016 paper: <https://dl.acm.org/doi/10.1145/2998392.2998405>
- TypeSearch report: <https://eprints.ost.ch/id/eprint/1196/1/MA_TypeSearch_TechnicalReport.pdf>; TyDe 2024 paper: <https://dl.acm.org/doi/abs/10.1145/3678000.3678207>
- Idris type-directed search: <https://docs.idris-lang.org/en/latest/reference/type-directed-search.html>
- Aegle: <https://github.com/wasabi315/aegle>; TyDe 2025 paper: <https://dl.acm.org/doi/10.1145/3759538.3759651>
- Hoogle logs and survey: <https://arxiv.org/abs/1911.04091>, <https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla20-hplus.pdf>
