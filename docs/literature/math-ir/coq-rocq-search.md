# Coq/Rocq search and retrieval: Search, CoqGym, Tactician/Graph2Tac, Rango/CoqStoq, CoqPilot

- **Kind:** cluster note (tools + proof-synthesis benchmarks with retrieval components)
- **Links:** [Rocq `Search` refman](https://rocq-prover.org/doc/master/refman/proof-engine/vernacular-commands.html); CoqGym [arXiv 1905.09381](https://arxiv.org/abs/1905.09381); Tactician [arXiv 2008.00120](https://arxiv.org/abs/2008.00120); Graph2Tac [arXiv 2401.02949](https://arxiv.org/abs/2401.02949); Rango [arXiv 2412.14063](https://arxiv.org/abs/2412.14063) (see `../premise-selection/rango-coq.md`); CoqPilot [arXiv 2410.19605](https://arxiv.org/abs/2410.19605); CoqHammer [JAR 2018](https://link.springer.com/article/10.1007/s10817-018-9458-4)
- **Authors / org, date:** Yang & Deng (Princeton), ICML 2019; Blaauwbroek, Urban, Geuvers, CICM 2020; Blaauwbroek, Olšák, Rute et al., 2024; Thompson, Saavedra, …, First (UCSD et al.), ICSE 2025; Kozyrev et al. (JetBrains Research), ASE 2024 tool demo; Czajka & Kaliszyk, JAR 2018
- **Status:** `Search` is built into Rocq. The others are research code on GitHub, e.g. [CoqGym](https://github.com/princeton-vl/CoqGym) and [CoqPilot](https://github.com/JetBrains-Research/coqpilot).

## What it is

The Coq ecosystem has **no published relevance benchmark for lemma search** that we found. Retrieval appears only as a component inside proof-synthesis systems, and it is evaluated by theorems proved. Tool context: Rocq's `Search` filters the loaded environment by patterns, constants, name substrings, `concl:`/`hyp:`/`head:` positions, `is:` kind and module scope. `SearchPattern` and `SearchRewrite` are deprecated in favour of `Search` ([refman](https://rocq-prover.org/doc/master/refman/proof-engine/vernacular-commands.html)).

## How it works (evaluation protocols only)

- **CoqGym (2019).** 70,856 human proofs from 123 projects. The split is **by project** (43,844 train / 13,875 valid / 13,137 test proofs), so that "no testing proof comes from a project that is used in training". Each step has on average 10,350.3 premises in its environment. ASTactic encodes only the local context plus up to 10 environment premises; selecting premises from the full environment is "left for future research" ([§4–5](https://arxiv.org/abs/1905.09381)). There is no retrieval metric; the metric is % of test theorems proved.
- **Tactician / Graph2Tac (2020/2024).** Tactician's k-NN learns online from earlier proofs ([paper](https://arxiv.org/abs/2008.00120)). Graph2Tac's evaluation splits Opam **packages** using a random topological order of the dependency graph. The paper states that "no test package depends on a training package"; training holds 91.3% of theorems. Results are on 2000 randomly chosen test theorems ([Graph2Tac §3, App.](https://arxiv.org/abs/2401.02949)). The authors avoided pretrained LMs partly because of the "strong risk that our test data will be leaked into the pretraining data" ([Graph2Tac](https://arxiv.org/abs/2401.02949)).
- **Rango / CoqStoq (2025).** 196,929 theorems from 2,226 GitHub repos. The benchmark is 10,396 theorems from 12 repos, including CoqGym projects that compile under Coq 8.18 plus CompCert. Training files whose theorem statement exactly matches a test or validation statement were removed. Two post-cutoff projects check for contamination ([§III–V](https://arxiv.org/abs/2412.14063)). Lemma retrieval uses TF-IDF over identifiers, and proof retrieval uses BM25 over proof states. Full summary: `../premise-selection/rango-coq.md`.
- **CoqPilot (2024).** A VS Code plugin that fills `admit` holes by combining LLMs and non-ML methods. It includes a benchmarking harness for generation methods ([abstract](https://arxiv.org/abs/2410.19605)). It publishes no retrieval evaluation (the abstract mentions none).
- **CoqHammer (2018).** A hammer with learned premise selection. The evaluation details were not read here (unverified). Paper: [JAR](https://link.springer.com/article/10.1007/s10817-018-9458-4).

## Evaluation

| System | Split | Metric | Retrieval-relevant numbers |
|---|---|---|---|
| CoqGym / ASTactic | by project | % test theorems proved | ASTactic alone and with ATPs, up to 30.0% ([§1](https://arxiv.org/abs/1905.09381)) |
| Graph2Tac + k-NN | by package, dependency-ordered | % of 2000 test theorems proved | Online k-NN 1.72× over offline; Graph2Tac online definitions 17.4% → 26.1%; combined 33.2% ([abstract, §1](https://arxiv.org/abs/2401.02949)) |
| Rango | by repo (+ post-cutoff projects) | % theorems proved | 32.0% on CoqStoq. Proof-retrieval ablation: BM25 32.0%, TF-IDF 31.7%, CodeBERT dense 22.0% ([Table VI](https://arxiv.org/abs/2412.14063)) |
| Rango, split ablation | inter-file vs. inter-project | % of 500 theorems proved | Without retrieval: 17.8% (project split) vs. 25.4% (file split) ([Table V](https://arxiv.org/abs/2412.14063)) |

## Relevance to lean-explore-bench

- **The split granularity changes results a lot, and it interacts with retrieval.** In Rango, a random file-wise split inflated the no-retrieval variant by 43% relative. The full retrieval system gained less (15%), because retrieval supplies the project knowledge that the weights would otherwise memorise ([§V-C](https://arxiv.org/abs/2412.14063)). If we evaluate learned retrievers on queries derived from Mathlib, we should split by module or by time, not randomly by declaration.
- **Dependency-respecting splits.** Graph2Tac's topological package split and CoqGym's project split both avoid testing on material that the training set depends on ([Graph2Tac App.](https://arxiv.org/abs/2401.02949), [CoqGym §4](https://arxiv.org/abs/1905.09381)). For a fixed corpus like Mathlib, the analogue is to hold out queries whose targets are recent additions.
- **Contamination checks.** Rango's two post-cutoff projects and its exact-duplicate statement filter are cheap controls we can copy: add queries about declarations created after the embedding or LLM cutoff, and deduplicate near-identical statements ([§III and threats-to-validity](https://arxiv.org/abs/2412.14063)).
- **Sparse retrieval beat a small dense encoder over formal states.** Rango's BM25 > CodeBERT result ([Table VI](https://arxiv.org/abs/2412.14063)) argues for always including BM25 over declaration names and statements as a baseline.
- **Gap.** Nothing in Coq evaluates a *user query → declaration* ranking with relevance labels. The Coq literature offers splitting and contamination practice, not qrels.

## Open questions

- Does CoqHammer's JAR paper report premise-selection recall or only reproving rates? (unverified; paper not read)
- Is there an NL lemma-search tool for Coq/Rocq comparable to LeanSearch? None was found in this pass (unverified absence).

## Sources

- Rocq reference manual, Search commands: https://rocq-prover.org/doc/master/refman/proof-engine/vernacular-commands.html
- Yang & Deng, "Learning to Prove Theorems via Interacting with Proof Assistants" (CoqGym), ICML 2019: https://arxiv.org/abs/1905.09381
- Blaauwbroek, Urban, Geuvers, "The Tactician", CICM 2020: https://arxiv.org/abs/2008.00120
- Blaauwbroek et al., "Graph2Tac: Online Representation Learning of Formal Math Concepts", 2024: https://arxiv.org/abs/2401.02949
- Thompson et al., "Rango: Adaptive Retrieval-Augmented Proving for Automated Software Verification", ICSE 2025: https://arxiv.org/abs/2412.14063
- Kozyrev et al., "CoqPilot, a plugin for LLM-based generation of proofs", ASE 2024: https://arxiv.org/abs/2410.19605
- Czajka & Kaliszyk, "Hammer for Coq: Automation for Dependent Type Theory", JAR 2018: https://link.springer.com/article/10.1007/s10817-018-9458-4 (abstract only)
