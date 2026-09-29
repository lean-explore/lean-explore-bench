# Retrieval-augmented autoformalization (MS-RAG, RAutoformalizer, DRIFT, DDR)

- **Kind:** paper (cluster of four)
- **Links:**
  - MS-RAG: Zhang, Quan, Freitas, "Consistent Autoformalization for Constructing Mathematical Libraries", EMNLP 2024 — [arXiv 2410.04194](https://arxiv.org/abs/2410.04194), [code](https://github.com/lanzhang128/retrieval_augmented_autoformalization)
  - RAutoformalizer: Liu et al., "Rethinking and Improving Autoformalization: Towards a Faithful Metric and a Dependency Retrieval-based Approach", ICLR 2025 (spotlight per repo README) — [proceedings PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), [OpenReview](https://openreview.net/forum?id=hUb2At2DsQ), [code](https://github.com/Purewhite2019/rethinking_autoformalization), [retriever weights](https://huggingface.co/purewhite42/dependency_retriever_f). No arXiv version found (arXiv title search returned nothing).
  - DRIFT: Zhang, Borchert, Gritta, Lampouras, "DRIFT: Decompose, Retrieve, Illustrate, then Formalize Theorems", ICLR 2026 — [arXiv 2510.10815](https://arxiv.org/abs/2510.10815), [code](https://github.com/Formal-Math-Reasoning/DRIFT)
  - DDR: Wang et al., "Improving Autoformalization Using Direct Dependency Retrieval" — [arXiv 2511.11990](https://arxiv.org/abs/2511.11990), [dataset](https://huggingface.co/datasets/Palca/FineLeanCorpus_DDR)
- **Authors / org, date:** see above; Oct 2024 – Jan 2026.
- **Status:** all four release code and/or data (links above). RAutoformalizer pins Lean `4.7.0-rc2` and Mathlib commit `59fdb6b0…` (ICLR PDF, Table 9).

## What it is

A line of work where the retrieval target is **the set of library declarations a formal statement depends on** ("dependency retrieval"), with the query being an *informal* (natural-language) statement. This is the closest academic analogue to "natural-language query -> Mathlib declarations", which is exactly what a Lean search engine is asked to do. Each paper evaluates retrieval intrinsically (precision/recall against gold dependencies) and extrinsically (does the formalizer produce a correct statement).

## How it works

One sentence each: MS-RAG retrieves top-3 BM25-similar (informal, formal) exemplar pairs from the same library as few-shot context; RAutoformalizer fine-tunes a BGE-M3 dense retriever on informalized Mathlib to map informal statements to dependency declarations; DRIFT has an LLM decompose the statement into sub-queries and takes top-1 per sub-query from that same retriever, plus illustrative theorems; DDR has a fine-tuned LLM (Qwen3-32B) *generate* dependency names and then checks their existence with a suffix array.

## Evaluation

### Task definitions and gold labels

| Paper | Query | Retrieval target | How gold is labeled |
|---|---|---|---|
| MS-RAG | informal statement | most-similar (informal, formal) exemplars from a knowledge base; no dependency gold | n/a — retrieval is not scored intrinsically ([arXiv 2410.04194](https://arxiv.org/abs/2410.04194), Sec. 4) |
| RAutoformalizer | informal statement | set of formal objects `D_P` that the ground-truth formal statement depends on | Parsed from declarations: "parsing the declarations of all formal objects and linking identifiers with accessible formal objects in the corresponding context"; 243,797 Mathlib objects (139,933 theorems) ([ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), Sec. 4.1) |
| DRIFT | informal statement (decomposed) | same as RAutoformalizer ("oracle*" dependencies as defined by Liu et al.) | Reuses RAutoformalizer labels; authors explicitly call the oracle "imperfect ... not necessarily optimal or exhaustive" ([arXiv 2510.10815](https://arxiv.org/abs/2510.10815), Sec. 4.2) |
| DDR | informal statement | Mathlib identifiers used in the formal statement | Extracted from source strings of FineLeanCorpus formal statements; matching uses a suffix/sublist rule because "source code often contains unqualified or partially qualified names" ([arXiv 2511.11990](https://arxiv.org/abs/2511.11990), App. "SAC Details") |

### Benchmarks and splits

- **ProofNet** (374 theorems, Mathlib-based): "in-distribution"; average 3.39 dependencies from >243k objects ([DRIFT](https://arxiv.org/abs/2510.10815), Sec. 4.1). RAutoformalizer notes that "ProofNet participates in the data synthesis process of Lean-Workbook" — i.e., a known contamination path for one of its baselines ([ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), Sec. 4.2).
- **Con-NF** (introduced by RAutoformalizer): 961 theorems from the Lean 4 `con-nf` library (consistency of New Foundations), with its own library of 1,348 formal objects, deduplicated against Mathlib; built to test **out-of-distribution** retrieval where neither retriever nor formalizer has seen the target library ([ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), Sec. 4.1; [DRIFT](https://arxiv.org/abs/2510.10815), Sec. 4.1 — avg 3.92 premises). DRIFT adds a caveat: "We found no indication of contamination from our zero-shot results on ConNF; however, without access to the underlying training data, this cannot be conclusively validated."
- **miniF2F-test** (DRIFT only): 224 theorems after removing 20 duplicated/non-compiling ones; only 0.43 Mathlib dependencies on average, used as a "boundary condition" where retrieval should not help ([DRIFT](https://arxiv.org/abs/2510.10815), Sec. 4.1).
- **MathLibForm** (MS-RAG): 2,744 IsarMathLib items (Isabelle/ZF, **not Lean**) randomly split 90/10 into 2,470 train / 274 test; the train split is the retrieval knowledge base ([arXiv 2410.04194](https://arxiv.org/abs/2410.04194), Sec. 4). A random split within one library means near-neighbour items can be retrieved — no leakage control is described.
- **FineLeanCorpus Diff01…Diff89** (DDR): 100 statements randomly sampled per LLM-graded difficulty level, adjacent levels merged into five 200-item test sets; "All remaining samples in the dataset were used to fine-tune the DDR model" ([arXiv 2511.11990](https://arxiv.org/abs/2511.11990), Sec. 4.1). This is a random in-distribution split of the same corpus; no near-duplicate filtering is described (searched for dedup/leak/contamination; none found). An out-of-domain check on Omni-math is reported with an LLM judge (App. "Out of Domain Study").

### Metrics

- Retrieval: Recall@k and Precision@k for k ∈ {5, 10, 100} (RAutoformalizer, Table 2); set-level Precision/Recall/F1 against oracle dependencies (DRIFT, Table 1 — retrieved-set size varies per query); Precision/Recall after **removing hallucinated names** plus a hallucination rate `Hall` (DDR).
- Downstream: Typecheck@k and **BEq@k** (bidirectional extended definitional equivalence, proposed by RAutoformalizer; 100% precision / 90.50% accuracy vs. human labels on their equivalence benchmark) ([ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), Sec. 3, Table 1); DRIFT uses BEq+ (Poiroux et al.) at pass@1/pass@10; MS-RAG uses BLEU-2, ChrF, RUBY, CodeBERTScore and Isabelle syntax "Pass".

### Headline numbers (verified against the papers)

**RAutoformalizer** ([ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf), Tables 2–3):

| Bench | Retriever | R@5 | R@10 | R@100 | P@5 |
|---|---|---|---|---|---|
| ProofNet | BM25 | 0.16% | 0.16% | 1.00% | 0.11% |
| ProofNet | BGE-M3 pretrained | 1.93% | 2.13% | 7.14% | 1.02% |
| ProofNet | fine-tuned DR (topological) | 35.52% | 43.63% | 67.71% | 22.89% |
| Con-NF | BM25 | 4.41% | 7.31% | 31.13% | 2.37% |
| Con-NF | BGE-M3 pretrained | 5.66% | 9.10% | 34.50% | 3.73% |
| Con-NF | fine-tuned DR (topological) | 24.32% | 37.44% | 88.86% | 14.05% |

(Formal-declaration embedding format "F"; the F+IF rows differ.) Downstream BEq@8: ProofNet 16.58% (no retrieval) -> 18.18% (retrieval) -> 31.28% (oracle deps); Con-NF 4.58% -> 16.86% -> 55.36%. The paper's summary: "semantic similarity"-based baselines fail because "dependency retrieval is a novel retrieval task, which relies more on logical dependency" (Sec. 4.2).

**DRIFT** ([arXiv 2510.10815](https://arxiv.org/abs/2510.10815), Tables 1–2): retrieval F1 (no-decomposition baseline -> best decomposer): ProofNet 13.77 -> 27.68 (Claude-Opus-4), miniF2F 0.66 -> 3.83, Con-NF 28.17 -> 36.88 (DeepSeek-V3.1). Downstream BEq+@10 with GPT-4.1: ProofNet 13.37 (zero-shot) / 19.25 (DPR-RAuto) / 21.93 (DRIFT) / 27.54 (oracle*); Con-NF 6.76 / 20.08 / 62.33 / 58.90 — DRIFT beats the "oracle" because it also supplies usage examples. On miniF2F, retrieval can hurt: Goedel-Prover-V2-8B BEq+@10 drops from 93.33 (zero-shot) to 26.67 with DPR (RAuto) context.

**DDR** ([arXiv 2511.11990](https://arxiv.org/abs/2511.11990), Table "dependency-retrieval-icl"): filtered precision/recall ~0.82–0.92 for DDR vs. 0.02–0.09 precision for the RAutoformalizer retriever at k=5/10 and ~0.15–0.54 for prompted LLMs; prompted LLMs hallucinate ~30% of dependency names (Sec. 5.2). Downstream BEq@8 with DeepSeek-R1 on Diff89: 0.13 (none) / 0.135 (prompted retrieval) / 0.20 (DDR) (Table "results-icl"). Note precision is computed *after* dropping hallucinated items.

**MS-RAG** ([arXiv 2410.04194](https://arxiv.org/abs/2410.04194), Table 1): Mistral Isabelle "Pass" 5.47% (3-shot fixed exemplars) -> 21.53% (BM25 top-3 retrieved exemplars, query=text, index=text); GPT-3.5 38.69% -> 64.60%. Indexing auto-informalizations did not help ("does not lead to better retrieval").

## Relevance to lean-explore-bench

- This is the only academic line that evaluates **informal-query -> Mathlib declaration retrieval against machine-extracted gold**, which is the core of our benchmark. Its gold-labeling recipe (dependencies of a reference formal statement) gives us cheap, large-scale relevance labels.
- Warnings it surfaces:
  - Gold = "dependencies of one reference formalization" is incomplete and non-unique; DRIFT beats the oracle on Con-NF. Treat dependency labels as a *lower bound* on relevance and consider graded/human-adjudicated judgments for a subset.
  - Name matching is fragile (DDR needs suffix/sublist matching for unqualified names). We must canonicalize to fully qualified names and pin a Mathlib commit.
  - Low-dependency queries (miniF2F, 0.43 deps) make retrieval metrics degenerate and can make retrieval harmful downstream; stratify by number of gold dependencies.
  - Random within-corpus splits (MS-RAG, DDR) and known pipeline contamination (ProofNet -> Lean-Workbook) inflate numbers; the Con-NF idea (a separate library, deduplicated against Mathlib) is the cleanest OOD design here.
  - Retrieval-only and end-to-end rankings diverge (DRIFT's Goedel results; RAutoformalizer's large oracle gap), so report both.
- **Concrete reusable items:**
  1. Con-NF benchmark (961 theorems, 1,348-object library) as an OOD retrieval split — from the RAutoformalizer repo.
  2. RAutoformalizer's Mathlib dependency-graph extraction and its topological informalizations as a source of gold labels and NL queries (repo above).
  3. Metric set: R@{5,10,100}, P@k, set-F1 for variable-size outputs, plus a hallucination rate for generative retrievers (DDR's `Hall`).
  4. Oracle-dependency upper bound as a standard extrinsic baseline alongside no-retrieval.
  5. FineLeanCorpus_DDR (HF) as a large pool of (informal statement, Mathlib identifiers) pairs — but needs our own dedup against any test set.

## Open questions

- How much do BEq/BEq+ outcomes depend on the Lean/Mathlib version used? RAutoformalizer pins Lean 4.7.0-rc2; DRIFT used Lean v4.18.0 for miniF2F filtering — cross-paper numbers are not directly comparable.
- Is Con-NF truly unseen by current frontier LLMs? DRIFT says it cannot be conclusively validated.
- The DDR paper does not report whether FineLeanCorpus test items have near-duplicates in its training remainder (unverified either way).

## Sources

- https://arxiv.org/abs/2410.04194 (MS-RAG; full LaTeX read: Sec. 4 dataset, Table 1)
- https://proceedings.iclr.cc/paper_files/paper/2025/file/d630537fc4402cfa3ebbc7450a0cac91-Paper-Conference.pdf (RAutoformalizer; Sec. 3–4, Tables 1–3, Table 9)
- https://openreview.net/forum?id=hUb2At2DsQ ; https://github.com/Purewhite2019/rethinking_autoformalization
- https://arxiv.org/abs/2510.10815 (DRIFT; Sec. 4–5, Tables 1–3) ; https://github.com/Formal-Math-Reasoning/DRIFT
- https://arxiv.org/abs/2511.11990 (DDR; Sec. 3–5, appendices) ; https://huggingface.co/datasets/Palca/FineLeanCorpus_DDR
