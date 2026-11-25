# Paper

Draft preprint: "DeclSearch: A Benchmark for Lean 4 Declaration Search". The name is a
placeholder, set by `\bench` at the top of the source. Earlier drafts are in `versions/`.

| File | Content |
| --- | --- |
| `lean-search-bench.tex` | The working draft, in the format of the Lean Census and Fuse papers (`neurips_2025.sty`, preprint). Compile with `latexmk -pdf lean-search-bench.tex`. |
| `references.bib` | Bibliography. |
| `figures.py` | Scores the engine runs of a built benchmark and draws `figures/forms.pdf`. |
| `scores.json` | Success@1 and Success@10 on the test split by form, bucket and engine. |

To refresh the numbers from a benchmark directory (queries and engine runs), run from the
repository root:

```sh
python3 paper/figures.py data/mix-v6
cd paper && latexmk -pdf lean-search-bench.tex
```

The BM25 column comes from `leb run DIR --engine bm25 --corpus lean_explore.db`. The numbers in the tables of the paper are typed in by hand from `leb score` and
`scores.json`; update them when the benchmark changes.
