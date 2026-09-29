# doc-gen4 search (Mathlib docs search box and `/find`)

- **Kind:** search engine (name-only, client-side)
- **Links:** Mathlib docs <https://leanprover-community.github.io/mathlib4_docs/>; code <https://github.com/leanprover/doc-gen4>
- **Authors / org, date:** `leanprover` GitHub org; code examined at commit [`d555f83`](https://github.com/leanprover/doc-gen4/tree/d555f83e82831466ec101c9753450e8b4ec203b4) (2026-05-07).
- **Status:** Live on the Mathlib docs site; open source.

## What it is

The search box on every doc-gen4 page (including the Mathlib docs), the `search.html` results page, and the `/find` URL endpoint. The default lookup when a user roughly knows a declaration's name.

## How it works

- Matches on the **declaration name only** (no docstrings, types, or natural language): a subsequence ("fuzzy") match of the query against every full name, ranked by an error score. The source calls it "quite hacky" ([declaration-data.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/declaration-data.js)). You can filter by declaration kind. Autocomplete shows at most 30 hits ([search.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/search.js)).
- The index is one JSON file of all declarations, written by doc-gen4 at build time and downloaded by the browser.
- `/find?pattern=Nat.add#doc` resolves an exact name. Adding `strict=false` switches to fuzzy search ([find.js](https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/find/find.js)).

## Evaluation

No published evaluation found.

## Relevance to lean-explore-bench

- **Harness:** there is no server API. Search runs in the browser. It is easy to reproduce offline, though: load the doc-gen4 declaration JSON for a pinned Mathlib build and port the ~30-line `matchCaseSensitive`/`getMatches` scorer. That makes it deterministic, free, and version-pinnable. Scraping the live site gives you whatever Mathlib revision was last deployed.
- **Role:** the **lexical name baseline** every Mathlib user already has. It should do well on identifier-like queries (`add_comm`, `Finset.sum_comm`) and close to zero on natural-language or statement-shaped queries. Report results per query type so this shows.
- `/find?pattern=<name>#doc` URLs are a convenient canonical link format for gold declarations. Lean Finder already returns this format, as its lean-lsp-mcp wrapper shows ([server.py](https://github.com/project-numina/lean-lsp-mcp/blob/5c0eddf0a67881aae10589e9c399538f90f1eff6/src/lean_lsp_mcp/server.py#L997-L1046)).

## Open questions

- Does the deployed Mathlib docs site run this exact search code? (unverified)
- Are any docs-site query logs available to seed a query set? (unknown)

## Sources

- doc-gen4 at `d555f83`: <https://github.com/leanprover/doc-gen4/tree/d555f83e82831466ec101c9753450e8b4ec203b4>
- Matcher: <https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/declaration-data.js>
- Search page: <https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/search.js>
- `/find`: <https://github.com/leanprover/doc-gen4/blob/d555f83e82831466ec101c9753450e8b4ec203b4/static/find/find.js>
- Mathlib docs: <https://leanprover-community.github.io/mathlib4_docs/>
