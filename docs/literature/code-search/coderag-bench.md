# CodeRAG-Bench

- **Kind:** benchmark / dataset
- **Links:** paper https://arxiv.org/abs/2406.14497 ; project https://code-rag-bench.github.io (unverified URL)
- **Authors / org, date:** Wang, Asai, Yu et al. (CMU, UW et al.), June 2024
- **Status:** Public (NAACL 2025 Findings, unverified venue)

## What it is

CodeRAG-Bench tests whether retrieval helps code generation. It has about 9k coding tasks and about 25M retrieval documents ([paper §1](https://arxiv.org/abs/2406.14497)).

- **Tasks:**
  - basic programming (HumanEval, MBPP, LiveCodeBench)
  - open-domain library use (DS-1000, ODEX)
  - repository-level work (RepoEval, SWE-bench-Lite)
  - code retrieval (CodeSearchNet)
- **Document sources:** competition solutions, tutorials, library documentation, StackOverflow posts and GitHub files ([abstract](https://arxiv.org/abs/2406.14497)).

## How it works

- **Canonical documents:** gold retrieval targets were annotated per task ([paper §2.3](https://arxiv.org/abs/2406.14497)):
  - HumanEval/MBPP: the solution document.
  - DS-1000/ODEX: library-doc entries for the functions the solution calls. These were parsed automatically, then manually verified, giving 1.4 and 1.2 entries per task on average.
  - RepoEval: the 20-line gold snippet.
  - SWE-bench: the files edited by the gold patch.
- **Metrics:** NDCG@10 for retrieval (with precision and recall) and pass@k for generation. Results are reported in two settings: "canonical" retrieval (from the gold datastore only) and "open" retrieval (from all sources) ([paper §2.4](https://arxiv.org/abs/2406.14497)).

## Evaluation

- Gold context helps a lot. For example, GPT-4o gains 27.4% on SWE-bench and 6.9% on ODEX with canonical docs ([paper §1](https://arxiv.org/abs/2406.14497)).
- **Dense versus lexical:** unlike BEIR-era findings, "dense embedding models frequently surpass BM25". Code-trained retrievers beat general ones at similar size (Jina-v2-code beats GIST-base/BGE-base by 7.4/6.6 NDCG@10), and SFR-Mistral (7B) is the best open model ([paper §3.2](https://arxiv.org/abs/2406.14497)).
- **Remaining failure:** "current retrievers still struggle to fetch useful contexts especially with limited lexical overlap" ([abstract](https://arxiv.org/abs/2406.14497)).
- Chunking documents to 200–800 tokens often works best in open retrieval ([paper §1](https://arxiv.org/abs/2406.14497)).

## Known flaws

1. **Gold docs come from what the reference solution used** (for example, functions called in the canonical program). Alternative valid solutions that use other APIs get no credit, which creates a false-negative risk.
2. **Base tasks are heavily contaminated** (HumanEval, MBPP, SWE-bench are public and pre-2024). LiveCodeBench was included partly for freshness ([paper §2.1](https://arxiv.org/abs/2406.14497)).
3. **Retrieval scores and generation outcomes don't always agree:** some open-retrieval RAG setups beat canonical ones ([paper §1](https://arxiv.org/abs/2406.14497)). NDCG against gold docs is therefore an imperfect proxy for usefulness.

## Relevance to lean-explore-bench

- **Offers a two-level evaluation model.** Measure (a) retrieval against gold declarations and (b) downstream success when retrieved declarations are fed to a prover or LLM. For Lean, (b) can be "does the prover close the goal with top-k retrieved premises", which is closely analogous to premise-selection evaluations.
- **Gold-from-reference-proof mirrors the premise-selection convention** (gold = lemmas used in the human proof). CodeRAG-Bench shows the known weakness: valid alternatives go unrewarded.
- **The "limited lexical overlap" failure is exactly the NL→Mathlib-name gap.** Stratify queries by lexical overlap with the gold declaration's name and docstring, as SweRank does for issues.

## Open questions

- Is there a Lean analogue of "open retrieval from heterogeneous sources" (Mathlib docs, Zulip, blueprint text, textbooks) worth benchmarking, or should we restrict to declarations?

## Sources

- CodeRAG-Bench paper: https://arxiv.org/abs/2406.14497
