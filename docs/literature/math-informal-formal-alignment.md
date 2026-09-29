# Informal↔formal alignment resources (100 theorems, 1000+ theorems, Mathlib doc maps, Stacks tags, concept alignment, MMA)

- **Kind:** dataset / resources cluster
- **Links:**
  - Freek Wiedijk, *Formalizing 100 Theorems*: https://www.cs.ru.nl/~freek/100/
  - *1000+ theorems*: https://1000-plus.github.io/ and https://github.com/1000-plus-theorems/1000-plus
  - Mathlib `docs/100.yaml`, `docs/1000.yaml`, `docs/overview.yaml`, `docs/undergrad.yaml`: https://github.com/leanprover-community/mathlib4/tree/master/docs
  - Gauthier & Kaliszyk, *Matching concepts across HOL libraries*: https://arxiv.org/abs/1405.3906
  - Müller, Gauthier, Kaliszyk, Kohlhase, Rabe, *Classification of Alignments Between Concepts of Formal Mathematical Systems* (CICM 2017): https://link.springer.com/chapter/10.1007/978-3-319-62075-6_7
  - Horowitz & de Paiva, *MathGloss*: https://arxiv.org/abs/2311.12649
  - Jiang, Li, Jamnik, *Multilingual Mathematical Autoformalization* (MMA): https://arxiv.org/abs/2311.03755
  - Wu et al., *Autoformalization with LLMs* (Isabelle): https://arxiv.org/abs/2205.12615
- **Status:** the 100 list is live (last update 2026-09-17 per page); 1000+ repo last pushed 2026-07-22; Mathlib files live (checked at mathlib4 commit `3f6737d`, 2026-09-28).

## What it is
These are hand-curated links from an **informal statement** (a theorem name, Wikipedia page, textbook concept or Stacks tag) to a **formal declaration** in one or more proof assistants. The pairs are ready-made query→gold pairs for a Lean search benchmark, and several also exist for Isabelle, HOL Light, Rocq, Metamath and Mizar, which allows cross-system comparison.

## How it works (per resource)
- **Freek's 100 theorems.** A fixed list of 100 famous theorems, with per-system status. Counts on the page (2026-09-17): HOL Light 95, Isabelle 95, Lean 83, Rocq 80, Metamath 74, Mizar 71, ACL2 48, ProofPower 43, PVS 26, Imandra 20, Megalodon 12, Naproche 10 ([page](https://www.cs.ru.nl/~freek/100/)). The Lean side is Mathlib `docs/100.yaml`, which has 100 entries; **78 carry a `decl`/`decls` field** naming Mathlib declarations, e.g. `1: The Irrationality of the Square Root of 2 → irrational_sqrt_two` (counted by parsing the file at `3f6737d`).
- **1000+ theorems.** The entries are exactly those of Wikipedia's *List of theorems*, keyed by Wikidata QID, with MSC class and per-assistant fields (`isabelle`, `hol_light`, `rocq`, `lean`, `metamath`, `mizar`). Each formalization records `status` (formalized / statement only), `library` (S standard, L main library, X external), `url`, and optional `identifiers` (declaration names) ([README](https://github.com/1000-plus-theorems/1000-plus)).
  - Counts from a clone on 2026-09-28: 1,200 entry files. The Lean field is present in 226, 200 of which list identifiers. Metamath is present in 38 (37 with identifiers). Rocq has 4, and Isabelle, HOL Light and Mizar have 1 each. Formalized-status records total 270.
  - The Lean data is synchronized with Mathlib `docs/1000.yaml` by `sync_mathlib_data.py`. That file has 1,199 entries, 214 with `decl(s)`.
- **Mathlib concept maps.** `docs/overview.yaml` (about 512 non-empty concept→declaration leaves) and `docs/undergrad.yaml` (about 436). The latter's topic list comes from the French *agrégation* syllabus, per the file header. Both map informal concept names such as "quotient space" or "Yoneda embedding" to declarations (counted by parsing at `3f6737d`).
- **Stacks/Kerodon tags in Mathlib.** At `3f6737d`, Mathlib source has 576 `stacks XXXX` attribute occurrences covering 368 distinct Stacks tags, plus 16 `kerodon` occurrences (grep count). Each tag resolves to an informal Stacks statement, which yields *textbook-quality informal statement → Mathlib declaration* pairs. The same Stacks project is a NaturalProofs source (`math-naturalproofs.md`).
- **Cross-library concept alignment.** Gauthier & Kaliszyk normalise properties of constants and types, then use similarity measures to discover **398 pairs of isomorphic constants/types** across HOL4, HOL Light and Isabelle/HOL ([abstract](https://arxiv.org/abs/1405.3906)). Müller et al. classify kinds of alignment and propose a shared format and infrastructure ([Springer](https://link.springer.com/chapter/10.1007/978-3-319-62075-6_7)).
- **MathGloss.** A knowledge graph linking undergraduate concepts across Wikidata, UChicago course terms, the French undergraduate curriculum (which hyperlinks to Lean 4), MuLiMa and nLab ([abstract](https://arxiv.org/abs/2311.12649)).
- **Autoformalization data (non-Lean-specific).** MMA builds informal–formal pairs by *informalising* Isabelle and Lean statements with an LLM. Fine-tuning on it gives 16–18% of statements "acceptable with minimal corrections" on miniF2F/ProofNet, against 0% for the base model ([abstract](https://arxiv.org/abs/2311.03755)). Wu et al. report 25.3% of competition problems perfectly formalised into Isabelle/HOL by an LLM ([abstract](https://arxiv.org/abs/2205.12615)). Neither is a retrieval benchmark, but both are sources of paired statements.

## Evaluation
None of the curated lists is itself a benchmark; there are no metrics. Gauthier & Kaliszyk evaluate by the number of discovered matches (398) ([arXiv](https://arxiv.org/abs/1405.3906)). MMA is evaluated by manual acceptability of autoformalisations ([arXiv](https://arxiv.org/abs/2311.03755)).

## Relevance to lean-explore-bench
- **Free, expert-curated gold for "famous theorem by name" queries.** The combined 100.yaml and 1000.yaml give roughly 290 Wikipedia-theorem → Mathlib-declaration pairs. overview/undergrad add about 950 concept → declaration pairs, and Stacks adds about 370 tag → declaration pairs. Together that is a four-figure seed set with essentially zero annotation cost.
- **Query construction:** a raw theorem *name* makes a very easy, name-matching query. For each pair we should generate several query forms: the name; the Wikipedia or Stacks statement text; a paraphrase with the name removed (as BRIGHT's rewriting does); and a LaTeX-formula form. Then stratify results by form.
- **Graded relevance is needed.** These maps give *one* canonical declaration. Mathlib usually has several acceptable ones (general versus specialised forms, iff versus implication, `Nat` versus general-ring versions). Treat the listed declaration as grade 3 and pool the other engines' results for grading.
- **Freshness risk:** declaration names in the YAML are checked by `scripts/yaml_check.py` in Mathlib (file header), so they should resolve at a given commit. Pin the Mathlib commit in the benchmark.
- **Cross-system extension:** the 1000+ schema already has Isabelle, HOL Light, Rocq, Metamath and Mizar slots, but outside Lean and Metamath these are almost empty in the repo today. Freek's 100 page has dense cross-system coverage. It could support a later "same query, different library" comparison.

## Open questions
- Many 1000+ Lean URLs point to the rendered 1000-theorems page, not to a declaration; the `identifiers` field is the thing to use.
- Licensing: Wikipedia statement text is CC BY-SA; Stacks is GFDL (per NaturalProofs footnote).

## Sources
- https://www.cs.ru.nl/~freek/100/ (fetched 2026-09-28)
- https://1000-plus.github.io/ and repo README https://github.com/1000-plus-theorems/1000-plus (cloned 2026-09-28; counts computed locally)
- Mathlib4 docs YAML and source, commit 3f6737de4761ec7bf368491fe9faccc991ebd6ca (sparse clone; counts computed locally): https://github.com/leanprover-community/mathlib4
- https://arxiv.org/abs/1405.3906 · https://link.springer.com/chapter/10.1007/978-3-319-62075-6_7 · https://arxiv.org/abs/2311.12649 · https://arxiv.org/abs/2311.03755 · https://arxiv.org/abs/2205.12615
