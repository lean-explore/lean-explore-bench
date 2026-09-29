# Isabelle search and premise selection: MePo, MaSh, SErAPIS, FindFacts, Magnushammer

- **Kind:** cluster note (tools + premise-selection benchmarks)
- **Links:** MePo [Meng & Paulson 2009](https://www.sciencedirect.com/science/article/pii/S1570868307000626) ([preprint](https://ceur-ws.org/Vol-192/paper04.pdf)); MaSh [ITP 2013 paper](https://www21.in.tum.de/~blanchet/mash.pdf) ([Springer](https://link.springer.com/chapter/10.1007/978-3-642-39634-2_6)); SErAPIS [paper](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf); FindFacts [arXiv 2204.14191](https://arxiv.org/abs/2204.14191); Magnushammer [arXiv 2303.04488](https://arxiv.org/abs/2303.04488), see also `../premise-selection/magnushammer.md`
- **Authors / org, date:** Meng & Paulson (Cambridge), 2009; Kühlwein, Blanchette, Kaliszyk, Urban, 2013; Stathopoulos, Koutsoukou-Argyraki, Paulson (Cambridge, ALEXANDRIA), 2020; Huch & Krauss (TUM / QAware), 2020; Mikuła et al. (Warsaw / IDEAS NCBR / Google), ICLR 2024
- **Status:** MePo and MaSh ship in Sledgehammer. FindFacts was at search.isabelle.in.tum.de per the [paper](https://arxiv.org/abs/2204.14191); its current status is not checked (unverified). SErAPIS was a prototype. Magnushammer's dataset is on [HF](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle), per [the paper](https://arxiv.org/abs/2303.04488).

## What it is

Isabelle has the longest record of evaluated premise selection among proof assistants. It also has one small, TREC-style evaluation of natural-language fact search (SErAPIS). Tool context, one line each:
- `find_theorems` / `find_consts` search only the loaded session, by name, term pattern or type pattern ([FindFacts §2](https://arxiv.org/abs/2204.14191)).
- MePo is Sledgehammer's symbol-overlap relevance filter ([Meng & Paulson](https://ceur-ws.org/Vol-192/paper04.pdf)). MaSh learns from dependencies in previous proofs, and MeSh combines the two ([MaSh](https://www21.in.tum.de/~blanchet/mash.pdf)).
- FindFacts is a Solr drill-down search over the whole AFP ([paper](https://arxiv.org/abs/2204.14191)).
- SErAPIS indexes facts through words and "concepts" taken from related Wikipedia articles ([paper](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf)).
- Magnushammer is a contrastive bi-encoder with a cross-encoder reranker ([paper](https://arxiv.org/abs/2303.04488)).

## How it works (evaluation protocols only)

**MePo (2009).** Evaluated end to end: the ATP success rate on a hand-collected set of 285 clause-form problems from the Isabelle–ATP link-up ([preprint p.2, §3](https://ceur-ws.org/Vol-192/paper04.pdf)). To get a reference, the authors kept only the "referenced axioms" (axioms used in any successful proof). The filter could then be checked without running ATPs, by reporting which reference axioms it missed ([§3](https://ceur-ws.org/Vol-192/paper04.pdf)). This is an early "ground truth = axioms used in found proofs" protocol.

**MaSh (2013).** Two evaluations ([§5](https://www21.in.tum.de/~blanchet/mash.pdf)):
1. **Offline ranking against a known proof.** The corpora are three formalizations: Auth (743 lemmas), Jinja (733) and Probability (1311). Each lemma is a query, processed in a *topological/linearized order* of the theory graph, so that only earlier lemmas are candidates and only earlier proofs are training data. Ground truth is the fact set of either the human Isar proof or a Vampire ATP proof. Each filter returns n = 1024 facts. Metrics:
   - **Full recall:** the smallest m such that the top-m contains all proof facts, or n+1 if none does.
   - **AUC:** the fraction of (proof fact, non-proof selected fact) pairs that are ordered correctly.

   The authors say this offline part "may seem artificial" because users want *any* proof, not the known one. They use it anyway because it takes seconds rather than hours.
2. **"In vivo".** For each goal, the authors generate problems with 16…1024 facts and run E, Vampire and Z3. A goal counts as solved if any prover solves it within 10 s. They also report the Judgment Day suite: 1268 goals from seven theories.

**SErAPIS (2020).** This is a small, conventional IR evaluation ([§4](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf)):
- **Queries:** 25 hand-written queries. Each started from an information need plus an example target fact, then was deliberately paraphrased away from the fact's name, e.g. "summability, zero, criterion" instead of `summable`, `null`, `test`.
- **Judging:** the top-20 of each of 4 models was pooled and judged with binary relevance. A result counts as relevant if it has the query's "main notion", even when a secondary notion is missing.
- **Scoring:** MAP, with a paired permutation test for significance.
- **Comparison with find_theorems:** the authors call a direct comparison "infeasible" because find_theorems' results depend on the libraries loaded in the session.

**FindFacts (2020).** The paper has no relevance evaluation. It gives only a worked example: a "prime" query narrowed from more than 2000 hits to 8 through facets, of which 6 were prime definitions. It also notes that ties in ranking make result order "appear arbitrary" ([§3.5, §4](https://arxiv.org/abs/2204.14191)).

**Magnushammer (2023/24).** The dataset has 4.4M (proof state, premise) pairs and 433K unique premises, mined from the AFP plus the Isabelle standard library. It combines premises from human proofs (HPL, 1.1M pairs) with alternative premises from Sledgehammer-found proofs (SH, 3.3M pairs). Adding the Sledgehammer proofs is explicitly meant to reduce false negatives. Evaluation uses **proof rate only**, not ranking metrics: tactic × top-2^i premises, 2 s timeouts, on PISA (1000 AFP problems) and miniF2F. AFP material that appears in PISA was removed from training ([§4–5](https://arxiv.org/abs/2303.04488)). Details are in `../premise-selection/magnushammer.md`.

## Evaluation

| System | Corpus / queries | Ground truth | Metric | Reported numbers |
|---|---|---|---|---|
| MePo | 285 ATP problems | ATP success; axioms referenced by found proofs | success rate | Keeping only referenced axioms raised success from "about 60 percent to 80 percent" ([preprint](https://ceur-ws.org/Vol-192/paper04.pdf)) |
| MaSh offline | Auth / Jinja / Probability, chronological | Isar-proof facts, or ATP-proof facts | full recall, AUC | Probability (Isar proofs): MePo full recall 742, AUC 57.7%; MaSh 384, 88.0%; MeSh 336, 89.2% ([Fig. 2](https://www21.in.tum.de/~blanchet/mash.pdf)) |
| MaSh in vivo | same | ATP success | % solved vs. number of facts | Peak MaSh 44.8% vs. MePo 38.2%. Union over all fact counts: MePo 46.3%, rising to 62.7% with MaSh and MeSh ([§5.1](https://www21.in.tum.de/~blanchet/mash.pdf)) |
| MaSh on Judgment Day | 1268 goals | ATP success | % solved | MePo 65.6%, MeSh 69.8% ([§5.2](https://www21.in.tum.de/~blanchet/mash.pdf)) |
| SErAPIS | 25 NL queries, Isabelle libraries | pooled top-20 per model, binary | MAP + permutation test | Best model MAP .775; the word-only baseline .688 ([Table 1](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf)) |
| Magnushammer | PISA (1000), miniF2F (244 + 244) | proof found in Isabelle | proof rate | PISA single-step: BM25 30.6, TF-IDF 31.8, OpenAI ada-002 embeddings 36.1, Sledgehammer 38.3, Magnushammer 59.5 ([Table 1](https://arxiv.org/abs/2303.04488)) |

Two caveats come from the MaSh authors themselves:
- **Ground-truth bias.** ATP-proof ground truth favours MePo, because "the ATP proofs were found with MePo's help" ([§5.1](https://www21.in.tum.de/~blanchet/mash.pdf)).
- **Tuning bias.** MePo's parameters "are tuned for Judgment Day" ([§5.2](https://www21.in.tum.de/~blanchet/mash.pdf)).

## Relevance to lean-explore-bench

- **Chronological evaluation is the correct leakage control for library-derived queries.** MaSh ranks only facts proved *before* the query lemma and trains only on earlier proofs ([§5.1](https://www21.in.tum.de/~blanchet/mash.pdf)). For us, the equivalent is to restrict candidates to Mathlib declarations that exist, or are imported, before the target, or to use a Mathlib snapshot taken before the queries were written.
- **"Used premises" labels are biased toward the tool that produced the proof.** The MePo/ATP-proof reversal is a clear case of qrels contaminated by one system ([§5.1](https://www21.in.tum.de/~blanchet/mash.pdf)). If we derive labels from proofs that were found with LeanSearch, exact? or similar tools, we inherit the same bias. Human-proof labels, or labels pooled across many systems, reduce it.
- **Premise-used labels are incomplete positives.** Magnushammer adds Sledgehammer alternatives precisely because unseen alternatives look like negatives ([§4](https://arxiv.org/abs/2303.04488)). A search benchmark should allow several relevant answers per query, graded where possible, rather than a single gold declaration.
- **SErAPIS is the closest prior work to our task.** It evaluates NL queries over formal facts with pooled binary judgments, MAP and a paired permutation test. Its query design (start from a target fact, then paraphrase away from its name) is a pattern we can reuse, and at 25 queries it is far too small. A stated weakness to avoid: relevance is judged on topic ("main notion present"), not on whether the fact is usable.
- **End-to-end proof rate is not a search metric.** Magnushammer and MaSh-in-vivo measure retrieval × prover × tactic budget, and the budget choices (2^i premise subsets, timeouts) dominate the results ([§5](https://arxiv.org/abs/2303.04488)). At most, we should report it as a secondary downstream metric.
- **Full recall (the rank at which all needed facts appear) is a useful metric for multi-premise queries.** It complements recall@k and nDCG when a "query" is a goal that needs a set of lemmas.
- **Generic dense embeddings are a meaningful baseline.** On PISA, off-the-shelf ada-002 (36.1) came close to Sledgehammer (38.3) and beat BM25 (30.6) ([Table 1](https://arxiv.org/abs/2303.04488)). We should include a generic-embedding baseline.

## Open questions

- Did the promised SErAPIS large-scale evaluation with user queries ever happen? Only the plan is stated ([§5](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf)) (unverified whether it was done).
- Is FindFacts still maintained, and does it have query logs we could mine for real queries? (unverified)
- The 2016 JAR follow-up, "A Learning-Based Fact Selector for Isabelle/HOL" ([Springer](https://link.springer.com/article/10.1007/s10817-016-9362-8)), was not read (paywalled here). It may have larger chronological evaluations (unverified).

## Sources

- Meng & Paulson, "Lightweight relevance filtering for machine-generated resolution problems", J. Applied Logic 7(1), 2009: https://www.sciencedirect.com/science/article/pii/S1570868307000626 ; preprint https://ceur-ws.org/Vol-192/paper04.pdf
- Kühlwein, Blanchette, Kaliszyk, Urban, "MaSh: Machine Learning for Sledgehammer", ITP 2013, LNCS 7998: https://www21.in.tum.de/~blanchet/mash.pdf ; https://link.springer.com/chapter/10.1007/978-3-642-39634-2_6
- Blanchette et al., "A Learning-Based Fact Selector for Isabelle/HOL", JAR 2016: https://link.springer.com/article/10.1007/s10817-016-9362-8 (not read)
- Stathopoulos, Koutsoukou-Argyraki, Paulson, "SErAPIS: A Concept-Oriented Search Engine for the Isabelle Libraries Based on Natural Language": https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf (venue/year 2020 per [ResearchGate listing](https://www.researchgate.net/publication/341655872_SErAPIS_A_Concept-Oriented_Search_Engine_for_the_Isabelle_Libraries_Based_on_Natural_Language); venue unverified)
- Huch & Krauss, "FindFacts: A Scalable Theorem Search", Isabelle Workshop 2020: https://arxiv.org/abs/2204.14191
- Mikuła et al., "Magnushammer: A Transformer-Based Approach to Premise Selection", ICLR 2024: https://arxiv.org/abs/2303.04488
- Desharnais & Blanchette, "Sledgehammering Without ATPs", ITP 2025: https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ITP.2025.38 (abstract only; recent Sledgehammer evaluation context)
