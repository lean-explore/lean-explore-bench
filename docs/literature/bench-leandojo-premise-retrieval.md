# LeanDojo Benchmark 4: premise retrieval as a search eval

- **Kind:** benchmark / dataset
- **Links:**
  - Paper: https://arxiv.org/abs/2306.15626 (NeurIPS 2023 Datasets and Benchmarks)
  - LeanDojo Benchmark 4: https://doi.org/10.5281/zenodo.8040109
- **Authors / org, date:** Kaiyu Yang et al. (Caltech and others), June 2023. The Lean 4 version is extracted from mathlib4 commit `3ce43c18…` (21 Oct 2023).
- **Status:**
  - Downloadable from Zenodo under CC BY 2.0 (paper Appendix D).
  - Mathlib snapshots newer than the original release are extracted with the LeanDojo tooling (details are covered by the premise-selection notes).

## What it is

LeanDojo Benchmark 4 contains 102,514 theorems with proofs, 213,067 tactics, and 152,695 premises from mathlib4. The split is 2,000 validation theorems, 2,000 test theorems, and the rest for training. There are two splits:
- `random`
- `novel_premises`, where every test proof uses at least one premise never seen in training.

**The retrieval task:** the query is the proof state before a tactic, and the gold set is the premises that tactic uses. Only tactics with at least one premise are included.

## Evaluation

Metrics are R@1, R@10 and MRR over the top 100 retrieved premises.

**LeanDojo Benchmark 4, ReProver retriever** (Appendix D, Table B):

| Split | R@1 | R@10 | MRR |
|---|---|---|---|
| random | 12.8 | 34.7 | 0.29 |
| novel_premises | 9.8 | 32.1 | 0.24 |

**Lean 3 comparison** (Table 1), novel_premises:
- BM25: R@10 15.5
- ReProver: R@10 27.6

**MIRB's packaging.** MIRB repackages the `novel_premises` split as 4,109 queries over 180,944 documents. There, general embedders score nDCG@10 between 5 and 13; BM25 scores 6.9 and voyage-3-large 13.0 (see `bench-mirb.md`).

**Legendre.** Legendre's methodology lists a "LeanDojo B4" premise task, which it never aggregates with the tasks built on mathlib-4280.

## Relevance to lean-explore-bench

- **Size and provenance.** This is the largest *non-synthetic* query-to-declaration dataset for Lean. The gold comes from real proofs, extracted automatically by the elaborator.
- **Different query modality.** The queries are proof states, not what a human types into a search box. It suits a separate "proof-state / agent" track, and fits engines that accept goals, such as Lean State Search, Lean Finder, and Loogle-like tools. It does not measure natural-language search.
- **Gold is incomplete.** The premises a tactic used are only one valid set; other lemmas that would also work count as wrong. Recall is also dominated by very common premises, such as basic simp lemmas.
- **Stale snapshot.** The 2023 snapshot is old; declaration names have churned since. Re-extracting from a current Mathlib with LeanDojo, or with Lean's own premise-selection data (e.g. `chasenorman/premises-mathlib-v4.30.0` on Hugging Face, unverified provenance), would be needed to score engines on a current corpus.

## Open questions

- Is there a maintained, current-Mathlib re-extraction with a standard test split? The premise-selection literature notes may cover this.

## Sources

- Paper (§4 benchmark, §5 Table 1, App. B.3 licensing, App. D Lean 4 statistics and Table B): https://arxiv.org/abs/2306.15626 and https://arxiv.org/html/2306.15626
- MIRB packaging: https://arxiv.org/abs/2505.15585 (Table 1, Table 9)
- Legendre's task list: https://www.legendre-leaderboard.com/methodology
- Hugging Face dataset listing (existence only, not inspected): https://huggingface.co/datasets/chasenorman/premises-mathlib-v4.30.0
