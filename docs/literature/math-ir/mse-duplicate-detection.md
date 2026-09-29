# Math StackExchange duplicate / related-question retrieval

- **Kind:** benchmark / dataset (cluster: several uses of MSE duplicate links as relevance labels)
- **Links:**
  - MIRB MSE/MO duplicate datasets: <https://arxiv.org/abs/2505.15585>, data <https://huggingface.co/collections/hcju/mirb-6827001711765454f58c5a76>
  - ARQMath (duplicate-based topic selection and the "Linked MSE posts" oracle): <https://ceur-ws.org/Vol-3180/paper-01.pdf>
  - DPRL ARQMath-2 system (duplicate-link fine-tuning): <https://terpconnect.umd.edu/~oard/pdf/arqmath21-team.pdf>
  - CQADupStack (general StackExchange duplicate benchmark): <https://github.com/D1Doris/CQADupStack>
- **Authors / org, date:** Ju & Dong (MIRB, 2025); Mansouri, Oard, Zanibbi (ARQMath and DPRL, 2020-2022); Hoogeveen, Verspoor, Baldwin (CQADupStack, ADCS 2015).
- **Status:** MIRB data is public on Hugging Face. MSE data dumps are public on the Internet Archive.

We found no dedicated, peer-reviewed "MSE duplicate detection" benchmark paper beyond these (searches on arXiv and the web). This note therefore covers how MSE duplicate links have been *used as relevance signals*. MIRB itself has its own notes: `../lean-benchmarks/mirb.md` and `mirb.md`.

## What it is

Stack Exchange moderators and high-reputation users close new questions as duplicates of earlier ones. The resulting links are free, large-scale, question-to-question relevance labels. MSE also records weaker "related" links.

## How it works (evaluation design)

**MIRB MSE Dup. Question Retrieval** [MIRB §3.1](https://arxiv.org/abs/2505.15585):
- *Source.* MSE dump of 2024-09-30. Posts with figures, links or tables were removed.
- *Graph.* Duplicate links form an undirected graph, which is **transitively closed**. One question per connected component becomes the query; the rest go into the corpus.
- *Dynamic corpus against false negatives.* For each query Q, any candidate Q′ with tag overlap |T(Q)∩T(Q′)|/|T(Q)| ≥ 0.5 is removed from Q's corpus. This follows BRIGHT's LeetCode set. The intent is that, apart from the gold duplicates, few on-topic questions remain.
- *Size.* 25,116 queries, 1,350,505 documents, 1.78 relevant documents per query, binary relevance. A MathOverflow version built the same way has 225 queries and 108,301 documents [MIRB Table 1].
- *Metric.* nDCG@10.

**ARQMath** [ARQMath-3 §4.1, §4.3](https://ceur-ws.org/Vol-3180/paper-01.pdf):
- Uses duplicates for topic selection. Every ARQMath-3 topic has at least one known duplicate in the collection, so that relevant answers are likely to exist.
- The links themselves are hidden from participants.
- An oracle baseline returns the answers to the known duplicates, ranked by vote score.

**DPRL (ARQMath-2)** [DPRL 2021 §3.1](https://terpconnect.umd.edu/~oard/pdf/arqmath21-team.pdf):
- Fine-tuned a Quora-pretrained Sentence-BERT cross-encoder in two stages: first on duplicate *and* related MSE pairs (358,306 pairs), then on duplicates only (57,670 pairs). Both stages used 50% random negatives.
- Answers attached to the retrieved similar questions were then ranked.

**CQADupStack**:
- Twelve StackExchange subforums, with duplicate labels and "related" labels. Related questions address a similar topic but do not give a full answer.
- The evaluation script can treat related posts as "half relevant" in nDCG/MAP/MRR [GitHub README](https://github.com/D1Doris/CQADupStack).
- The subforums include Mathematica SE but *not* Math SE [CQADupStack ADCS 2015 paper](https://eltimster.github.io/www/pubs/adcs2015.pdf).
- A follow-up paper, "CQADupStack: Gold or Silver?", examines missing duplicate labels [ResearchGate](https://www.researchgate.net/publication/309386352_CQADupStack_Gold_or_Silver). Content not accessed (unverified).

## Evaluation (reported numbers)

**MIRB, nDCG@10** [MIRB Table 3]:

| Model | MSE Dup | MO Dup |
|---|---|---|
| BM25 | 22.85 | 44.01 |
| voyage-3-large (best) | 60.33 | 82.87 |
| SFR-Embedding-2_R | 58.52 | 81.32 |

- General-purpose cross-encoder rerankers applied to the top 10 *lowered* scores. For voyage-3-large on MSE Dup, the score fell from 60.33 to 52.93 with bge-reranker-v2-m3 and to 54.84 with jina-reranker-v2 [MIRB Table 4].

**ARQMath "Linked MSE posts" oracle, nDCG′** [ARQMath-3 Table 3]:
- 0.279 on ARQMath-1, 0.203 on ARQMath-2, and 0.106 on ARQMath-3.
- Its P′@10 (0.384 on ARQMath-1, 0.282 on ARQMath-2) is high relative to its nDCG′.
- Takeaway: duplicate-derived answers are *precise but far from complete*, because pooled human judgments find many more relevant answers.

## Relevance to lean-explore-bench

- **Community links as cheap silver labels.** The Lean analogues are:
  - Zulip "#new members" / "#mathlib" threads where someone replies "this is `Foo.bar`".
  - Mathlib `@[deprecated]` aliases and `alias` declarations.
  - "See also" references in docstrings.
  
  These give query→declaration pairs at scale, as MSE duplicates do.
- **Take transitive closure and use the "dynamic corpus" trick together.** Group declarations that are aliases or equivalent restatements into equivalence classes. When silver labels are incomplete, drop likely-unlabeled positives from each query's corpus. For us that means near neighbours in the same namespace or file. The alternative is to evaluate only with metrics that ignore unjudged items. A caution: dropping same-topic candidates also removes the hardest distractors and inflates scores, so report both variants.
- **Do not treat silver links as gold.** ARQMath shows that the duplicate oracle has good early precision but poor nDCG′ against pooled judgments. Use silver pairs for training and for large-scale known-item metrics (MRR, Recall@k). Use pooled graded human (or LLM-plus-human-audited) judgments for the headline metric.
- **Graded "related" versus "duplicate".** MSE and CQADupStack distinguish the two, and CQADupStack scores "related" as half relevant. That is a ready-made two-level silver scale: an exact-match declaration versus a related API.
- **Rerankers are not free wins.** MIRB's negative reranking result is a reason to benchmark retrieve-then-rerank pipelines per component.

## Open questions

- Is there any MSE dataset with *human-verified* non-duplicate hard negatives? None found.
- How many MSE duplicates are actually "same theorem, different notation"? That is the case most analogous to informal→Mathlib search. Not quantified in any source found.

## Sources

- Ju & Dong, "MIRB: Mathematical Information Retrieval Benchmark," arXiv:2505.15585 (LaTeX source read): <https://arxiv.org/abs/2505.15585>
- ARQMath-3 overview (CEUR Vol-3180): <https://ceur-ws.org/Vol-3180/paper-01.pdf>
- Mansouri, Oard, Zanibbi, "DPRL Systems in the CLEF 2021 ARQMath Lab": <https://terpconnect.umd.edu/~oard/pdf/arqmath21-team.pdf>
- Hoogeveen, Verspoor, Baldwin, "CQADupStack," ADCS 2015: <https://eltimster.github.io/www/pubs/adcs2015.pdf>; repo <https://github.com/D1Doris/CQADupStack>
- "CQADupStack: Gold or Silver?" (not accessed): <https://www.researchgate.net/publication/309386352_CQADupStack_Gold_or_Silver>
