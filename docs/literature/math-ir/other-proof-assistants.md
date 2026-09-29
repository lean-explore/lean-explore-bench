# Search and premise selection in other proof assistants (Isabelle, Coq/Rocq, HOL Light/HOL4, Metamath, Mizar, Agda)

- **Kind:** cluster note (tools and premise-selection benchmarks), focused on evaluation
- **Links:** see each section
- **Status:** mostly research artifacts; built-in search commands are live in each system

**Summary.** Outside Lean, search by user query has almost never been evaluated with relevance labels; the one exception found is Isabelle's SErAPIS (25 queries). What these ecosystems offer is **premise-selection evaluation practice**: chronological or dependency-ordered splits, "used in a proof" labels and their biases, and oracle ceilings. Magnushammer and Rango have their own notes ([../premise-selection/magnushammer.md](../premise-selection/magnushammer.md), [../premise-selection/rango-coq.md](../premise-selection/rango-coq.md)).

## Isabelle

- **MePo (Meng & Paulson 2009)** evaluated end to end on 285 ATP problems; keeping only axioms referenced by found proofs raised success from "about 60 percent to 80 percent" ([preprint](https://ceur-ws.org/Vol-192/paper04.pdf)).
- **MaSh (Kühlwein et al., ITP 2013)** ([paper](https://www21.in.tum.de/~blanchet/mash.pdf)):
  - Offline ranking in **chronological order** of the theory graph (only earlier lemmas are candidates, only earlier proofs are training data), against human Isar or Vampire ATP proofs, with **full recall** (smallest m such that the top m holds all proof facts) and AUC. On Probability (Isar): MePo full recall 742 / AUC 57.7%, MaSh 384 / 88.0%, MeSh 336 / 89.2%.
  - In vivo ATP success: peak MaSh 44.8% vs MePo 38.2%; Judgment Day 1268 goals: MePo 65.6%, MeSh 69.8%.
  - Caveats stated by the authors: ATP-proof ground truth favours MePo "because the ATP proofs were found with MePo's help", and MePo is tuned for Judgment Day. **Labels derived from proofs found with a tool are biased toward that tool.**
- **SErAPIS (Stathopoulos, Koutsoukou-Argyraki, Paulson, 2020)** — the only natural-language fact-search evaluation with pooled judgments found outside Lean ([paper](https://www.cl.cam.ac.uk/~lp15/papers/Alexandria/Serapis.pdf)): 25 hand-written queries, each starting from an information need and a target fact then deliberately paraphrased away from the fact's name; top-20 of 4 models pooled; binary relevance ("main notion" present); MAP with a paired permutation test. Best model MAP .775 vs word-only baseline .688. Direct comparison with `find_theorems` was called "infeasible" because its results depend on the loaded session.
- **FindFacts (Huch & Krauss 2020)** — Solr search over the AFP with no relevance evaluation; notes that ranking ties make order "appear arbitrary" ([arXiv:2204.14191](https://arxiv.org/abs/2204.14191)).

## Coq / Rocq

- No published relevance benchmark for lemma search. Retrieval appears only inside proof synthesis, scored by theorems proved.
- **CoqGym** splits **by project** so "no testing proof comes from a project that is used in training"; each step has on average 10,350 premises in scope ([arXiv:1905.09381](https://arxiv.org/abs/1905.09381)).
- **Graph2Tac** splits Opam packages in a **random topological order** of the dependency graph, so no test package depends on a training package; the authors avoided pretrained LMs partly because of test-data leakage risk ([arXiv:2401.02949](https://arxiv.org/abs/2401.02949)).
- **Rango/CoqStoq**: a random file-level split raised the no-retrieval baseline from 17.8% to 25.4%; BM25 32.0% ≈ TF-IDF 31.7% ≫ untuned CodeBERT 22.0% ([arXiv:2412.14063](https://arxiv.org/abs/2412.14063)).

## HOL Light and HOL4

- **HolStep** (balanced 50/50 "useful in proof" labels): a context-free logistic regression reaches 71% and conditioning on the conjecture adds nothing, so balanced binary labels mostly measure a statement's prior usefulness ([arXiv:1703.00426](https://arxiv.org/abs/1703.00426)). Include a **query-agnostic popularity baseline** to expose this.
- **HOList** uses a random 60:20:20 theorem split; its pairwise proxy error is about 1% while end-to-end proof rates sit in the 30s, so proxies with random negatives saturate ([arXiv:1904.03241](https://arxiv.org/abs/1904.03241)).
- **HOL(y)Hammer on Flyspeck** evaluates chronologically, "each time using only the previous theorems and proofs": 39% of 14,185 theorems ([arXiv:1211.7012](https://arxiv.org/abs/1211.7012)).
- **HOL4 hammer**: giving all loaded theories did *better* than reproving from the exact dependencies the proof used, because alternative proofs exist — evidence that "used" labels are incomplete ([arXiv:1509.03534](https://arxiv.org/abs/1509.03534)).

## Metamath, Mizar and Agda

- **MPTP2078 (Mizar)**: chronologically ordered "chainy" problems (≈1,977 premises each) vs "bushy" problems with only the human proof's premises (≈31.5). Vampire solves 26.4% chainy vs 53.2% bushy — the ceiling perfect premise selection could reach. Recall is measured against the full set of used premises as a curve over n ([arXiv:1108.3446](https://arxiv.org/abs/1108.3446)). MizAR 60 reports about 60% in the hammer setting vs 75% with human-proof premises ([arXiv:2303.06686](https://arxiv.org/abs/2303.06686)).
- **DeepMath (Mizar)** uses a random 10% hold-out and concedes it "may also lead to learning from future proofs" ([arXiv:1606.04442](https://arxiv.org/abs/1606.04442)).
- **Agda (Kogkalidis et al., NeurIPS 2024)** splits stdlib by file, adds OOD and zero-shot libraries (Unimath, TypeTopology), and reports AveP and R-precision as means over 4 runs with 95% CIs; scores fall two- to threefold out of distribution ([arXiv:2402.02104](https://arxiv.org/abs/2402.02104)).
- Built-in search commands (metamath.exe `SEARCH`, Mizar MML Query, Agda "Search About") have no published relevance evaluation.

## Lessons for lean-explore-bench

1. **Chronological or dependency-ordered candidate pools** are the standard leakage control (MaSh, Flyspeck, MPTP2078 chainy, Graph2Tac). For Mathlib: candidates restricted to what exists before the target, or queries whose targets were added after a snapshot.
2. **"Used in a proof" labels are incomplete and can be biased toward the tool that found the proof.** Use graded, multi-answer, pooled judgments for headline numbers.
3. **Report an oracle ceiling** (downstream success given the gold premises) next to the no-retrieval floor.
4. **Include a popularity baseline** and use full-corpus ranking with realistic imbalance, not balanced pairwise accuracy.
5. **SErAPIS's query recipe** (start from a target, paraphrase away from its name) is reusable; at 25 queries it is far too small.
