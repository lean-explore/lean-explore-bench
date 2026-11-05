# Lean Finder evaluation sets and user study

- **Kind:** benchmark / dataset (plus a human-preference protocol)
- **Links:**
  - Paper: https://arxiv.org/abs/2510.15940 (ICLR 2026; OpenReview https://openreview.net/forum?id=5SF4fFRw7u)
  - Test data: https://github.com/delta-lab-ai/lean-finder/tree/main/lean-finder-original/data/test
  - Service: https://leanfinder.github.io and https://huggingface.co/spaces/delta-lab-ai/Lean-Finder
- **Authors / org, date:** Lu et al., DELTA Lab. arXiv October 2025.

## What it is

The paper builds three evaluation resources:

## How it works

- **Metrics:** R@1/5/10 and MRR. A hit requires the full Lean code to match.
- **GPT-4o baseline:** GPT-4o with web search emits names only. It is scored by exact full-name match and by a looser "stem match" on the last name component.
- **Fairness constraints:**
  - Test targets must exist in Lean Search's database.
  - Test queries must not appear in Lean Search's database or in Lean Finder's training data.
  - For the LeanExplore comparison, a "cleaned" test set keeps only targets that exist in LeanExplore's database (Appendix J, Table 12).
- **User study metrics:**
  - counts of 1st, 2nd and 3rd place votes
  - Top-3 rate over valid ballots
  - normalized Borda score, (3·n1 + 2·n2 + n3) / 3N
- **Judge-validity check:** GPT-4o agreed with humans on 58 of 63 decisive arena votes (92%) but only 15 of 37 tie or both-bad votes (43%), because it tends to force a choice (Appendix H).

## Evaluation

**Table 2** (R@1 / R@10 / MRR):

| System | Informalized statement | Synthetic user query | Augmented statement |
|---|---|---|---|
| Lean Finder | 64.2 / 93.3 / 0.75 | 54.4 / 91.4 / 0.68 | 82.7 / 97.7 / 0.89 |
| Lean Search | 49.2 / 82.5 / 0.61 | 47.1 / 83.7 / 0.60 | 59.2 / 85.5 / 0.69 |
| GPT-4o (stem match) | 21.1 / 30.0 / — | 17.8 / 30.5 / — | 48.2 / 54.1 / — |

**Table 3** (R@10): proof states, augmented / raw.
- Lean Finder: 67.9 / 40.0
- Lean State Search: 39.6 / 32.1
- Real Prover Search: 39.2 / 34.3

**Table 12** (R@10 / MRR, cleaned set):

| System | Informalized | Synthetic user query | Augmented statement |
|---|---|---|---|
| Lean Finder | 93.2 / 0.76 | 91.2 / 0.69 | 98.0 / 0.91 |
| LeanExplore | 68.0 / 0.46 | 60.1 / 0.37 | 95.2 / 0.89 |

**User study (Table 4):**

| System | 1st | 2nd | 3rd | Top-3 | Borda |
|---|---|---|---|---|---|
| Lean Finder | 139 | 56 | 36 | 81.6% | 0.67 |
| Lean Search | 70 | 51 | 40 | 56.9% | 0.41 |
| GPT-4o | 71 | 46 | 36 | 54.1% | (not captured) |

## Relevance to lean-explore-bench

**What to reuse:**
- **Multiple input modalities.** Informal statement, noisy formal statement, and proof state are useful as separate tracks. Proof-state inputs are far harder (raw R@10 ≤ 40%).
- **The blind user-study protocol and the Borda metric.** The Arena idea is a model for collecting preference data from real queries.
- **The judge-validity finding.** Any LLM judge we use must be validated against humans on ties and "all bad" cases specifically.
- **The test JSONLs.** They are downloadable and could be re-scored against any engine by resolving the gold passage to a declaration name.

**Caveats:**
- **Synthetic and in-distribution.** The queries were produced by the same pipeline as Lean Finder's training data, so the test sets favour Lean Finder by construction.
- **Paraphrase, not search intent.** Informalized-statement queries are close paraphrases of LLM informalizations; they measure how well a system matches the informalization, not realistic search intent.
- **Hard to re-score.** Gold is keyed by full Lean source text and a docid, not by declaration name plus snapshot, so re-scoring other engines needs name extraction.
- **Opaque snapshot.** The mathlib snapshot of the test set is not stated in what I read; Lean Finder's served indexes are v4.19.0, v4.24.0 and v4.28.0.
- **Tiny, unreleased user study.** 5 participants, and the real queries are unreleased.

## Open questions

- Which Mathlib version do the test sets target? Can the `docid`s be mapped to names?
- Will the "updated model" evaluation, or the v2 evaluation, be published? Legendre scored Lean Finder v1 via its endpoint on MathlibQR: nDCG@10 0.591.

## Sources

- Paper (§3.1 query mining, §4.1 metrics and settings, Tables 2–4, App. G, H, J Table 12, N): https://arxiv.org/abs/2510.15940 and https://arxiv.org/html/2510.15940v2
- Test files: https://github.com/delta-lab-ai/lean-finder (tree listing and line counts via the GitHub API and raw downloads)
- v2 repo: https://github.com/delta-lab-ai/lean-finder-v2
- Model: https://huggingface.co/delta-lab-ai/lean-finder (license field via the Hugging Face API)
- Legendre's Lean Finder row: https://www.legendre-leaderboard.com/changelog
