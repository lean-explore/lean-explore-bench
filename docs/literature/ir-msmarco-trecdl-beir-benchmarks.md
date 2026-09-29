# MS MARCO, TREC Deep Learning, BEIR: how the standard IR benchmarks are constructed

- **Kind:** benchmark / dataset (cluster)
- **Links:**
  - MS MARCO: https://arxiv.org/abs/1611.09268
  - TREC DL 2019 and 2020: https://arxiv.org/abs/2003.07820 and https://arxiv.org/abs/2102.07662
  - BEIR: https://arxiv.org/abs/2104.08663, code at https://github.com/beir-cellar/beir
- **Authors / org, date:** MS MARCO from Microsoft (2016). TREC DL from NIST and Microsoft (2019–2023). BEIR from Thakur et al. at UKP (2021).
- **Status:** all three are public and widely used. BEIR ships a standard corpus/queries/qrels format.

## What it is

These are three complementary designs for the same problem:

- **MS MARCO**: large-scale sparse labels. It has 1,010,916 Bing queries and 8.8M passages ([arXiv:1611.09268](https://arxiv.org/abs/1611.09268)).
- **TREC DL**: few queries, deep NIST pooling and graded labels over the MS MARCO corpora.
- **BEIR**: 18 heterogeneous datasets for **zero-shot** generalisation.

## Evaluation design

| | MS MARCO | TREC DL | BEIR |
|---|---|---|---|
| Queries | ~1M training queries, large dev set | 43 test queries per task (2019) | varies per dataset |
| Labels | sparse; "often only one positive label per query", no negatives | NIST pooled, 4-level graded | inherited from source datasets |
| Headline metric | MRR@10 | NDCG@10 (+ NCG@100/1000) | nDCG@10 (+ Recall@100) |
| Protocol | leaderboard | blind, single-shot TREC submission; full-rank and top-1000-rerank subtasks | zero-shot: no training on target data |

Sources: the TREC DL overview ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)) and BEIR ([arXiv:2104.08663](https://arxiv.org/abs/2104.08663)).

Notable design choices:

- **Controlled rerank subtask.** TREC DL provides the same BM25 top-1000 to every reranking participant, so rerankers are compared on an identical candidate set, separately from full retrieval ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)).
- **Pooling across subtasks.** TREC DL pools across both subtasks plus classifier-selected documents, to make the collection reusable. The 2019 overview attributes deep models' strong showing partly to the fact that "we included deep models trained on such data in our judging pools, whereas some past studies did not" ([arXiv:2003.07820](https://arxiv.org/abs/2003.07820)).
- **BM25 as baseline.** BEIR's headline finding is that "BM25 is a robust baseline". Reranking and late-interaction models perform best zero-shot, "however, at high computational costs" ([arXiv:2104.08663](https://arxiv.org/abs/2104.08663)).
- **Lexical bias.** BEIR notes a "lexical bias" in many datasets whose annotations were built from lexical systems, and quantifies it with Hole@10 (see [ir-trec-pooling-and-relevance-judgments.md](ir-trec-pooling-and-relevance-judgments.md)).
- **Contamination checks for LLM rerankers.** RankGPT built **NovelEval**, a test set "based on the latest knowledge", to address the concern that LLMs had memorised benchmark data ([arXiv:2304.09542](https://arxiv.org/abs/2304.09542)). RankZephyr also reports on NovelEval ([arXiv:2312.02724](https://arxiv.org/abs/2312.02724)).

## Relevance to lean-explore-bench

- **Adopt the split structure.** Mirror TREC DL's two tracks:
  1. a **full-retrieval track**, in which each engine searches all of Mathlib;
  2. a **rerank track**, in which every reranker gets the same fixed candidate list, for example a pooled BM25 plus dense top-100.

  This separates the retrieval ceiling from ranking quality.
- **Zero-shot framing.** Borrow BEIR's framing: many Lean engines are trained on Mathlib-derived data such as informalisations. We should hold out queries written *after* the engines' training snapshots, or from sources the engines did not train on. This is the Lean analogue of NovelEval.
- **Heterogeneous query types.** Report per-subset scores for name lookup, informal NL, type pattern and proof-state (goal) queries, rather than one blended number. BEIR reports per-dataset scores for the same reason.
- **Use BEIR's corpus/queries/qrels format.** That lets standard IR baselines (Pyserini BM25, sentence-transformers, ColBERT) run on our corpus without glue code.
- **Lexical baseline.** Always include a well-tuned BM25 over declaration names, docstrings and statements. BEIR shows it is hard to beat out of domain.

## Open questions

- Should the "corpus" be declarations at a pinned Mathlib commit? Probably yes, for reproducibility. Engines index different Mathlib versions, so we need a policy for gold declarations that are missing from an engine's index.

## Sources

- MS MARCO: https://arxiv.org/abs/1611.09268
- TREC DL 2019: https://arxiv.org/abs/2003.07820 ; 2020: https://arxiv.org/abs/2102.07662
- BEIR: https://arxiv.org/abs/2104.08663
- RankGPT (NovelEval): https://arxiv.org/abs/2304.09542 ; RankZephyr: https://arxiv.org/abs/2312.02724
