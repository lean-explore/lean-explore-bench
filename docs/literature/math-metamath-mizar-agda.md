# Metamath, Mizar and Agda: search commands and premise-selection benchmarks

- **Kind:** cluster note (tools + premise-selection datasets / benchmarks)
- **Links:** Metamath: [metamath-exe help source](https://github.com/metamath/metamath-exe), Holophrasm [arXiv 1608.02644](https://arxiv.org/abs/1608.02644), GPT-f [arXiv 2009.03393](https://arxiv.org/abs/2009.03393). Mizar: MML Query [Springer](https://link.springer.com/chapter/10.1007/11812289_21), MPTP2078 [arXiv 1108.3446](https://arxiv.org/abs/1108.3446), DeepMath [arXiv 1606.04442](https://arxiv.org/abs/1606.04442), MizAR 40 [JAR](https://link.springer.com/article/10.1007/s10817-015-9330-8), MizAR 60 [arXiv 2303.06686](https://arxiv.org/abs/2303.06686). Agda: [Emacs mode docs](https://agda.readthedocs.io/en/latest/tools/emacs-mode.html), Kogkalidis et al. [arXiv 2402.02104](https://arxiv.org/abs/2402.02104) ([code](https://github.com/konstantinosKokos/quill))
- **Authors / org, date:** Whalen 2016; Polu & Sutskever (OpenAI) 2020; Bancerek et al. (MML Query, 2001 onward, per [search summary](https://link.springer.com/chapter/10.1007/11812289_21); unverified); Alama, Heskes, Kühlwein, Tsivtsivadze, Urban, JAR 2014; Alemi, Chollet, Een, Irving, Szegedy, Urban, NeurIPS 2016 (venue unverified); Kaliszyk & Urban, JAR 2015; Jakubův et al., ITP 2023; Kogkalidis, Melkonian, Bernardy, NeurIPS 2024
- **Status:** Tools are live in their respective systems. The datasets are public as described in each paper.

## What it is

Tool context, one line each:
- metamath.exe `SEARCH <label-match> "<symbol-match>"` wildcard-matches labels and math-symbol strings, and `/COMMENTS` searches the preceding comments. `IMPROVE` in the proof assistant searches for statements that close fully known steps ([help text, mmhlpb.c](https://github.com/metamath/metamath-exe)).
- Mizar's MML Query is a semantics- and pattern-based search over the MML with its own query language ([Springer](https://link.springer.com/chapter/10.1007/11812289_21); [overview via web platform paper](https://ceur-ws.org/Vol-3377/fmm10.pdf)).
- Agda's Emacs mode has "Search About" (`C-c C-z`) ([docs](https://agda.readthedocs.io/en/latest/tools/emacs-mode.html)).

None of these has a published relevance evaluation that we found. The benchmarking content below is premise selection.

## How it works (evaluation protocols only)

**Mizar, MPTP2078 (Alama et al.).**
- **Problems:** 2078 problems from 33 MML articles, each in two versions. *Chainy* problems contain all previous MML content, **ordered chronologically** (on average 1976.5 premises). *Bushy* problems keep only the minimal fine-grained dependencies of the human proof (on average 31.5 premises) ([§5](https://arxiv.org/abs/1108.3446)).
- **Learning setup:** incremental. There are 2078 training steps, and each problem learns only from the dependencies of earlier problems.
- **Metric:** `recall(c,n) = |usedPremises ∩ top-n| / |usedPremises|` against the premises of the MML proof, plus ATP success ([§6.2](https://arxiv.org/abs/1108.3446)).

**DeepMath (Mizar).**
- **Data:** 32,524 of 57,917 MML theorems that some ATP could prove given the right premises. 10% was held out **at random**. The authors concede this "may also lead to learning from future proofs", and cite earlier k-NN experiments where cross-validation and chronological evaluation gave similar results ([§6.1](https://arxiv.org/abs/1606.04442)).
- **Primary metric:** theorems proved by E from the top-k premises, for k = 16…1024 (the proved set counts the cumulative union over cutoffs).
- **Proxy metric:** average max relative rank (aMRR) of the true premises among the true dependencies plus 128 random false ones ([§6.2](https://arxiv.org/abs/1606.04442)).
- **Test-set size:** the text says 2,724 test conjectures and the Table 1 caption says 2,742, an internal inconsistency ([§6.1, Table 1](https://arxiv.org/abs/1606.04442)).

**MizAR 40 / 60.** Whole-MML hammer evaluations: % of MML theorems proved automatically ([MizAR 40](https://link.springer.com/article/10.1007/s10817-015-9330-8), [MizAR 60](https://arxiv.org/abs/2303.06686)).

**Metamath, Holophrasm.** set.mm propositions split 21,786 / 2,711 / 2,720 (train / valid / test); how the split was drawn is not stated in the text read (unverified). The "relevance network" ranks which theorem is applied next and is scored by top-k accuracy over "all viable propositions" ([§5](https://arxiv.org/abs/1608.02644)).

**Metamath, GPT-f.** About 38k theorems, with valid and test sets of about 1k proofs each, "sampled randomly". The metric is the % of held-out theorems proved ([§3–4](https://arxiv.org/abs/2009.03393)). Premise choice is implicit in generation, so there is no separate retrieval metric.

**Agda (Kogkalidis et al.).**
- **Data:** Agda stdlib files split 85/15 by **file** (481 train / 92 eval files). The 5 outlier-size eval files form an OOD set. Zero-shot sets come from Unimath (137 files, 5,247 holes) and TypeTopology (28 files, 1,983 holes) ([§5.1, App. B](https://arxiv.org/abs/2402.02104)).
- **Query and candidates:** the query is a hole's type; the candidates are the file's scope entries (imports plus local definitions).
- **Labels:** gold labels are the lemmas that occur in the term that filled the hole ([App. A](https://arxiv.org/abs/2402.02104)).
- **Metrics:** average precision (AveP) and R-precision, as means over 4 training runs with 95% CIs ([§5.2](https://arxiv.org/abs/2402.02104)).

## Evaluation

| Benchmark | Numbers |
|---|---|
| MPTP2078, ATP only | Vampire (10 s) solves 548 (26.4%) chainy vs. 1105 (53.2%) bushy: the gap that perfect premise selection could close ([Table 3](https://arxiv.org/abs/1108.3446)) |
| MPTP2078, recall | About 88% of used premises in the MOR-ranked top-50 vs. about 80% for SNoW naive Bayes ([§6.2](https://arxiv.org/abs/1108.3446)). Combined system: 50% improvement over Vampire/SInE ([abstract](https://arxiv.org/abs/1108.3446)) |
| DeepMath | Cumulative proved up to cutoff 1024: k-NN 1786 (65.1%); def-CNN 1822 (66.4%); def+char-CNN 1862 (67.9%). Union of all methods 80.9% ([Table 1](https://arxiv.org/abs/1606.04442)) |
| MizAR 40 / 60 | 40% of MML theorems in 30 s on 14 CPUs ([JAR abstract](https://link.springer.com/article/10.1007/s10817-015-9330-8)); about 60% in the hammer setting, and 75% when given the human-proof premises ([abstract](https://arxiv.org/abs/2303.06686)) |
| Holophrasm | Relevance top-1 / top-5 / top-20 accuracy 55.3% / 72.8% / 87.4%; 14% of test theorems proved ([§5.3, abstract](https://arxiv.org/abs/1608.02644)) |
| GPT-f | 56.22% of the held-out test set proved, vs. 21.16% for the prior state of the art ([§1](https://arxiv.org/abs/2009.03393)) |
| Agda (QUILL) | stdlib in-distribution: AveP 50.2, R-Prec 40.3. OOD: 38.7 / 31.1. Unimath: 27.0 / 17.4. TypeTopology: 22.5 / 15.4. Vanilla Transformer on in-distribution: 10.9 / 3.7 ([Table 1](https://arxiv.org/abs/2402.02104)) |

## Relevance to lean-explore-bench

- **The recall@n definition in MPTP2078 is the natural form for multi-premise targets.** It is recall against the full set of premises the proof used, reported as a curve over n ([§6.2](https://arxiv.org/abs/1108.3446)). The authors note that high recall (about 90%) can still be insufficient for a proof, which is why they also report ATP success. We can report recall@k curves and treat downstream success as a separate, optional axis.
- **Use a chronological or dependency-order candidate pool.** Chainy MPTP2078 and incremental learning are the cleanest leakage control. DeepMath's random split is a documented weakness ([§6.1](https://arxiv.org/abs/1606.04442)).
- **The chainy/bushy gap bounds what retrieval can buy.** It doubles ATP success ([Table 3](https://arxiv.org/abs/1108.3446)), and MizAR 60's 60% vs. 75% shows the same pattern ([abstract](https://arxiv.org/abs/2303.06686)). An analogous "oracle retrieval" row (downstream success given the gold premises) would give our benchmark a ceiling.
- **Agda's AveP and R-precision with 95% CIs over runs is a good reporting template.** Its OOD and cross-library zero-shot sets show a two- to threefold drop out of distribution ([Table 1](https://arxiv.org/abs/2402.02104)). For Mathlib, we could hold out queries from areas that appear rarely in the training data or in the query-writing examples.
- **Labels exist but candidate pools are small in Agda.** Candidates are one file's scope, where positives are under 1.5% in-distribution and about 2‰ for OOD. That is far smaller than whole-Mathlib search, so the scores are not comparable to corpus-wide retrieval.
- **Holophrasm-style top-k accuracy over "viable" candidates pre-filters by unification.** It is closer to Lean's `exact?`/`apply?` suggestion than to NL search, so we should keep that task separate from NL search.

## Open questions

- Did MML Query or the newer Mizar web platform ([CEUR 3377](https://ceur-ws.org/Vol-3377/fmm10.pdf)) ever publish a user-query evaluation? None was found (unverified).
- Is there a Metamath NL search tool (e.g. over set.mm comments) with evaluation? None was found (unverified).

## Sources

- metamath-exe source (help text in `src/mmhlpb.c`): https://github.com/metamath/metamath-exe
- Whalen, "Holophrasm", 2016: https://arxiv.org/abs/1608.02644
- Polu & Sutskever, "Generative Language Modeling for Automated Theorem Proving", 2020: https://arxiv.org/abs/2009.03393
- Bancerek & Rudnicki et al., "Information Retrieval and Rendering with MML Query": https://link.springer.com/chapter/10.1007/11812289_21 (not read in full)
- "A Web Platform for Hosting the Mizar Mathematical Library": https://ceur-ws.org/Vol-3377/fmm10.pdf (not read in full)
- Alama et al., "Premise Selection for Mathematics by Corpus Analysis and Kernel Methods", JAR 2014: https://arxiv.org/abs/1108.3446
- Alemi et al., "DeepMath – Deep Sequence Models for Premise Selection", 2016: https://arxiv.org/abs/1606.04442
- Kaliszyk & Urban, "MizAR 40 for Mizar 40", JAR 55, 2015: https://link.springer.com/article/10.1007/s10817-015-9330-8
- Jakubův et al., "MizAR 60 for Mizar 50", ITP 2023: https://arxiv.org/abs/2303.06686
- Agda Emacs mode docs: https://agda.readthedocs.io/en/latest/tools/emacs-mode.html
- Kogkalidis, Melkonian, Bernardy, "Learning Structure-Aware Representations of Dependent Types", NeurIPS 2024: https://arxiv.org/abs/2402.02104
