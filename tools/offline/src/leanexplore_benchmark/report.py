"""Self-contained local HTML from released aggregate cells only."""

from __future__ import annotations

import html
from collections import defaultdict

from leanexplore_benchmark.profile import Cell

_STYLE = """
:root{color-scheme:light;font-family:system-ui,sans-serif;color:#17283a;background:#f5f7fa}
body{max-width:1140px;margin:40px auto;padding:0 24px;line-height:1.55}
h1{font-size:2.2rem;line-height:1.15}h2{font-size:1.25rem;margin-top:0}
.eyebrow{color:#216486;font-size:.85rem;letter-spacing:.1em;text-transform:uppercase}
.intro{max-width:850px}
.note{border-left:4px solid #cf8b27;padding:12px 18px;background:#fff8e9}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}
.card,section{background:white;border:1px solid #dce3eb;border-radius:10px;
padding:22px;margin:18px 0}
.big{display:block;font-size:2rem;font-weight:650;color:#165c7c}
.toolbar{position:sticky;top:0;background:#f5f7faed;padding:15px 0;z-index:2}
select{font:inherit;border:1px solid #bcc9d7;padding:8px;border-radius:6px;
margin-right:20px}
table{border-collapse:collapse;width:100%;font-size:.9rem}
td,th{text-align:left;padding:8px;border-bottom:1px solid #edf0f4}
th{color:#456078}td:last-child{font-variant-numeric:tabular-nums;text-align:right}
summary{cursor:pointer;font-weight:650}
.bar{height:9px;background:#3788ad;border-radius:4px;margin:5px 0}
small{color:#52677a}a{color:#126185}.hidden{display:none!important}
@media print{.toolbar{position:static}section{break-inside:avoid}}
"""


def render(cells: list[Cell], title: str, sha256: str) -> str:
    """Build a report that needs no network, external scripts, or query samples."""
    tables: dict[tuple[str, str], list[Cell]] = defaultdict(list)
    for cell in cells:
        tables[str(cell["view"]), str(cell["dimension"])].append(cell)
    cards = []
    for cell in tables["events", "source"]:
        count = cell["count"]
        shown = f"{count:,}" if isinstance(count, int) else "suppressed"
        cards.append(
            '<div class="card"><small>'
            + html.escape(str(cell["source"]))
            + f'</small><span class="big">{shown}</span>'
            "<small>requests, rounded</small></div>"
        )
    sections = []
    for (view, dimension), rows in tables.items():
        maximum = max((int(r["count"] or 0) for r in rows), default=1) or 1
        body = []
        for row in rows:
            n = row["count"]
            count = f"{n:,}" if isinstance(n, int) else "suppressed"
            width = 100 * int(n or 0) / maximum
            source = html.escape(str(row["source"]), quote=True)
            label = html.escape(str(row["category"]))
            body.append(
                f'<tr data-source="{source}"><td>{source}</td><td>{label}'
                f'<div class="bar" style="width:{width:.1f}%"></div>'
                f"</td><td>{count}</td></tr>"
            )
        opened = (
            " open"
            if dimension in {"source", "intent_cue", "surface", "results"}
            else ""
        )
        sections.append(
            f'<section data-view="{view}"><details{opened}><summary>'
            f"{html.escape(view)} / {html.escape(dimension)}</summary>"
            "<table><thead><tr><th>Channel</th><th>Category</th><th>Count</th></tr></thead>"
            "<tbody>" + "".join(body) + "</tbody></table></details></section>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head><body>"
        '<p class="eyebrow">LeanExplore · query benchmark · local audit</p>'
        f"<h1>{html.escape(title)}</h1>"
        '<p class="intro">What search requests reveal, which hypotheses they '
        "support, and what evidence is still missing to evaluate the engine.</p>"
        '<p class="note">Channels do not establish human or agent identity. '
        "<code>intent_cue</code> and <code>domain_cue</code> are experimental "
        "English/Lean rules without human validation. "
        "They are not reliable estimates of actual user goals or topics.</p>"
        '<div class="grid">' + "".join(cards) + "</div>"
        "<p>Small cells are suppressed; visible counts are rounded to tens. "
        "Totals may differ. <code>events</code> weights every request; "
        "<code>distinct_requests</code> counts normalized text with filters once "
        "per channel. Neither counts people or sessions. "
        "<code>words</code> counts whitespace-separated items, not LLM tokens.</p>"
        "<p>The export lacks clicks, impressions, returned documents, timing, "
        "relevance judgments, and confirmed success. Zero results do not prove "
        "that no answer exists; nonempty results do not establish success.</p>"
        '<div class="toolbar"><label>Channel <select id="source">'
        '<option value="all">All</option><option>api</option><option>mcp</option>'
        "<option>web</option><option>web_account</option></select></label>"
        '<label>View <select id="view"><option value="all">All</option>'
        "<option>events</option><option>distinct_requests</option><option>global</option>"
        '</select></label><button id="expand">Expand all tables</button></div>'
        + "".join(sections)
        + f"<p><small>SHA256 export: {html.escape(sha256)}</small></p>"
        + '<script>const src=document.getElementById("source"),'
        'vw=document.getElementById("view");'
        'function filter(){document.querySelectorAll("tr[data-source]").forEach(r=>'
        'r.classList.toggle("hidden",src.value!=="all"&&r.dataset.source!==src.value));'
        'document.querySelectorAll("section[data-view]").forEach(s=>'
        's.classList.toggle("hidden",vw.value!=="all"&&s.dataset.view!==vw.value));}'
        'src.addEventListener("change",filter);vw.addEventListener("change",filter);'
        'document.getElementById("expand").addEventListener("click",()=>'
        'document.querySelectorAll("details").forEach(d=>d.open=true));</script>'
        "</body></html>"
    )
