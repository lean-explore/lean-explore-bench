# Formula search engines and how each was evaluated (Approach Zero, Tangent-S/-CFT, MathWebSearch, zbMATH Open, SearchOnMath)

- **Kind:** search engine (grouped note, focused on evaluation)
- **Links:**
  - Approach0 ECIR 2019 <https://www.cs.rit.edu/~dprl/assets/files/Approach0_ECIR2019.pdf>
  - Tangent-CFT <https://dl.acm.org/doi/10.1145/3341981.3344235>, code <https://github.com/BehroozMansouri/TangentCFT>
  - Tangent-S (Davila & Zanibbi, SIGIR 2017) <https://dblp.org/rec/conf/sigir/DavilaZ17.html>
  - MathWebSearch <https://kwarc.info/systems/mws/>
  - zbMATH Open formula search <https://zbmath.org/formulae/>
  - SearchOnMath <https://arxiv.org/abs/1711.04189>
- **Authors / org, date:** RIT DPRL (Zanibbi group) for Approach0 and Tangent; KWARC (Kohlhase) for MWS; FIZ Karlsruhe for zbMATH Open; Oliveira et al. (UFRJ) for SearchOnMath. 2006-2022.
- **Status:**
  - Tangent-S is the official ARQMath baseline and its code is public [ARQMath-3 §4.3](https://ceur-ws.org/Vol-3180/paper-01.pdf).
  - Tangent-CFT code is on GitHub.
  - MWS is open source and runs zbMATH Open's formula search [KWARC](https://kwarc.info/systems/mws/).
  - The zbMATH formula-search page returned 403 to our fetcher, so its current state is unverified.

This note deliberately keeps engine mechanics to one line each. The focus is on the evaluation evidence behind each engine. Related notes: `arqmath.md`, `ntcir-math.md`, and `saber-math.md` (an automated benchmark that also evaluates Approach Zero).

## What it is

- **Approach Zero (Approach0).** Structural search over operator-tree leaf-root paths, scored by the largest common subexpression(s) [Zhong & Zanibbi ECIR 2019 abstract](https://link.springer.com/chapter/10.1007/978-3-030-15712-8_8).
- **Tangent-S.** Combines Symbol Layout Tree and Operator Tree matching [ARQMath-3 §4.3].
- **Tangent-CFT.** fastText-style embeddings of linearized SLT/OPT tuples [Tangent-CFT abstract](https://pure.psu.edu/en/publications/tangent-cft-an-embedding-model-for-mathematical-formulas/).
- **MathWebSearch (MWS).** Exact and unification search over Content MathML using substitution-tree indexing, a technique borrowed from automated theorem provers [KWARC](https://kwarc.info/systems/mws/).
- **zbMATH Open formula search.** The MWS engine deployed over zbMATH [KWARC](https://kwarc.info/systems/mws/).
- **SearchOnMath.** A commercial or academic multi-database formula search engine. Its one arXiv paper studies distributed response time only [Oliveira et al. 2017](https://arxiv.org/abs/1711.04189).

## How it works

Out of scope here. See the one-liners above.

## Evaluation

**Approach0**
- *NTCIR-12 WFB, 20 concrete queries, bpref@1000.* Fully relevant: 0.6726, against MCAT 0.5678 and Tangent-S 0.6361. Partially relevant: 0.5950, against MCAT 0.5698 and Tangent-S 0.5872 [ECIR 2019 Table 1].
- It used bpref "because our system does not contribute to pooling". It also reports P@k three ways: standard, condensed (unjudged removed) and upper bound (unjudged counted as relevant). For the K=1 run, fully-relevant P@10 was 0.285 / 0.405 / 0.785 [ECIR 2019 Table 1].
- *ARQMath-3.* Best Task 1 run overall (manual; nDCG′ 0.508) and best Task 2 run overall (manual; nDCG′ 0.720). Approach0 runs were declared *manual*, so the organizers caution they "might not be fairly compared to automatic runs" [ARQMath-3 §4.2, Tables 3-4].

**Tangent-S**
- Official ARQMath baseline. ARQMath-3 Task 2 scores were nDCG′ 0.540, MAP′ 0.336, P′@10 0.511, with an average retrieval time of about 6 s per query [ARQMath-3 Table 4, §5.3].
- As a formula-only engine applied to Task 1 answer retrieval, it reached nDCG′ 0.159 [ARQMath-3 Table 3].

**Tangent-CFT**
- The authors claim state-of-the-art NTCIR-12 WFB results (bpref on the top 1,000) and further gains when combined with Approach0 [ICTIR 2019 abstract](https://pure.psu.edu/en/publications/tangent-cft-an-embedding-model-for-mathematical-formulas/); [README](https://github.com/BehroozMansouri/TangentCFT). The exact bpref numbers were not retrieved (unverified).
- The CFTED rerank variant was the best automatic ARQMath-3 Task 2 run, nDCG′ 0.694 [ARQMath-3 Table 4].
- Tangent-S, -CFT and -CFTED all score higher on NTCIR-12 WFB (nDCG′ 0.78-0.90) than on ARQMath-1/2 (0.49-0.69) [2111.10504 Table 5](https://arxiv.org/abs/2111.10504).

**MathWebSearch**
- *NTCIR-10 formula search (22 queries, 100k arXiv papers).* MWS returned only 434 hits in total. Precision was rated at "18.7% fully relevant, and 33% partially relevant", and the authors say it "topped the precision section". Query latency was 3-70 ms (mean 11 ms) on a 10 GB in-RAM index [MWS NTCIR-10 §4](https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings10/pdf/NTCIR/MATH/04-NTCIR10-MATH-KohlhaseM.pdf).
- Some queries returned zero hits because of Content MathML conversion errors. This recall failure comes from exact unification semantics. The pattern of high precision, brittle recall and a dependence on encoding correctness is directly analogous to Lean's `exact?`/`#find`/Loogle-style unification search.
- The KWARC run at NTCIR-11 Math-2 scored MAP 0.285 and P@5 0.500 on relevant hits [NTCIR-11 Table 8](http://research.nii.ac.jp/ntcir/workshop/OnlineProceedings11/pdf/NTCIR/OVERVIEW/01-NTCIR11-OV-MATH-AizawaA.pdf). That this run was MWS-based is (unverified).

**zbMATH Open**
- No formal IR evaluation of the production formula search was found. The zbMATH team's ARQMath-1 participation (manual runs, fuzzy string search, kNN, and "Mathematical Objects of Interest" search) reports that "neither our automated methods nor our manual runs archived good scores" [Scharpf et al., arXiv:2012.02413](https://arxiv.org/abs/2012.02413).

**SearchOnMath**
- No relevance evaluation was found. The arXiv paper measures response times for 120 query formulas across 38 distributed configurations [arXiv:1711.04189](https://arxiv.org/abs/1711.04189).

## Relevance to lean-explore-bench

- **Evaluate unification/pattern engines separately from ranked-similarity engines, or with set-based metrics too.** MWS-style engines return a small, precise, unranked set, and that set can be empty. P@k and nDCG punish them for returning few results, not for being wrong. Report success@k and "empty result rate" alongside nDCG. Loogle and `exact?` behave like MWS.
- **Declare manual versus automatic runs.** The strongest ARQMath numbers came from manually operated Approach0 runs. If we ever benchmark "human with tool X", label it and keep it out of the automatic leaderboard.
- **A system's score shifts across collections because of evaluation design, not only system quality** (NTCIR-12 versus ARQMath [2111.10504]). Prefer several query sets with different construction (known-item, human ad hoc, formal pattern) over one.
- **Measure and report latency.** MWS (ms) versus Tangent-S (about 6 s) matters for interactive Lean use.

## Open questions

- Tangent-CFT exact NTCIR-12 numbers (paper not retrieved).
- Whether zbMATH Open has published any internal query-log or click-based evaluation.

## Sources

- Zhong & Zanibbi, ECIR 2019 (PDF read): <https://www.cs.rit.edu/~dprl/assets/files/Approach0_ECIR2019.pdf>; Springer <https://link.springer.com/chapter/10.1007/978-3-030-15712-8_8>
- Mansouri et al., "Tangent-CFT," ICTIR 2019: <https://dl.acm.org/doi/10.1145/3341981.3344235>; abstract <https://pure.psu.edu/en/publications/tangent-cft-an-embedding-model-for-mathematical-formulas/>; code <https://github.com/BehroozMansouri/TangentCFT>
- Davila & Zanibbi, "Layout and Semantics," SIGIR 2017: <https://dblp.org/rec/conf/sigir/DavilaZ17.html>
- ARQMath-3 overview: <https://ceur-ws.org/Vol-3180/paper-01.pdf>
- Mansouri et al., arXiv:2111.10504: <https://arxiv.org/abs/2111.10504>
- MathWebSearch system page: <https://kwarc.info/systems/mws/>; MWS at NTCIR-10: <https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings10/pdf/NTCIR/MATH/04-NTCIR10-MATH-KohlhaseM.pdf>
- NTCIR-11 Math-2 overview: <http://research.nii.ac.jp/ntcir/workshop/OnlineProceedings11/pdf/NTCIR/OVERVIEW/01-NTCIR11-OV-MATH-AizawaA.pdf>
- Scharpf et al., "ARQMath Lab: An Incubator for Semantic Formula Search in zbMATH Open?", arXiv:2012.02413: <https://arxiv.org/abs/2012.02413>
- Oliveira et al., "A distributed system for SearchOnMath based on the Microsoft BizSpark program," arXiv:1711.04189: <https://arxiv.org/abs/1711.04189>
- zbMATH Open formula search page (not fetchable, 403): <https://zbmath.org/formulae/>
