"""Stratified local review: raw text stays in memory, only labels are saved."""

from __future__ import annotations

import html
import http.server
import json
import random
import secrets
from collections import defaultdict
from pathlib import Path
from typing import Any

from leanexplore_benchmark.profile import surface
from leanexplore_benchmark.querylog import Export, Query, request_key

LABELS = {
    "intent": (
        "known_item",
        "find_lemma",
        "next_proof_step",
        "premise_bundle",
        "definition_or_api",
        "usage_example",
        "explanation",
        "exploration",
        "formalization",
        "debugging",
        "multiple",
        "unknown",
    ),
    "actor": ("unknown", "human_confirmed", "agent_confirmed"),
    "certainty": ("clear", "ambiguous", "insufficient_context"),
    "evidence": ("annotator_inference", "user_self_report", "client_attestation"),
    "language": ("english", "other", "formal_only", "mixed", "unknown"),
    "expected_output": (
        "declaration",
        "premise_set",
        "proof_step",
        "proof",
        "explanation",
        "example",
        "multiple",
        "unknown",
    ),
}


def sample(exported: Export, size: int, seed: int) -> list[tuple[Query, int, int]]:
    """Sample distinct source/request pairs with balanced source/style strata.

    Return (query, stratum population, stratum sample size). Weight N/n is
    required for estimating distinct-request prevalence. This is not a
    traffic-weighted or user-weighted sample. Small strata may be exhausted.
    """
    if size < 1:
        raise ValueError("Sample size must be positive")
    strata: dict[tuple[str, str], list[Query]] = defaultdict(list)
    seen = set()
    for row in exported.rows:
        request = row.source, request_key(row)
        if request not in seen:
            seen.add(request)
            strata[row.source, surface(row.text)].append(row)
    keys = sorted(strata)
    quotas = dict.fromkeys(keys, 0)
    remaining = min(size, len(seen))
    while remaining:
        for key in keys:
            if remaining and quotas[key] < len(strata[key]):
                quotas[key] += 1
                remaining -= 1
    rng = random.Random(seed)
    selected = [
        (row, len(strata[key]), quotas[key])
        for key in keys
        for row in rng.sample(strata[key], quotas[key])
    ]
    rng.shuffle(selected)
    return selected


def make_server(
    exported: Export,
    output: Path,
    reviewer: str,
    size: int = 400,
    seed: int = 42,
    port: int = 8051,
) -> http.server.HTTPServer:
    """Create a loopback-only review server with explicit per-label provenance."""
    if not reviewer.strip():
        raise ValueError("A real reviewer label is required")
    selected = sample(exported, size, seed)
    token = secrets.token_urlsafe(32)
    metadata = {
        "input_sha256": exported.sha256,
        "reviewer": reviewer,
        "seed": seed,
        "requested_size": size,
        "schema_version": 1,
    }
    saved: dict[str, Any] = {"metadata": metadata, "annotations": {}}
    if output.exists():
        saved = json.loads(output.read_text(encoding="utf-8"))
        if saved.get("metadata") != metadata:
            raise ValueError("Annotation file belongs to a different review")
    positions = {
        str(row.position): (row, population, n) for row, population, n in selected
    }

    class Handler(http.server.BaseHTTPRequestHandler):
        def _reply(self, body: bytes, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/":
                self._reply(b"Not found", 404)
                return
            pending = [
                (k, v) for k, v in positions.items() if k not in saved["annotations"]
            ]
            if not pending:
                self._reply(
                    b"<h1>Review complete</h1><p>Only annotations were saved.</p>"
                )
                return
            position, (row, population, n) = pending[0]
            options = "".join(
                f'<label>{name}<select name="{name}" required>'
                '<option value="">Choose</option>'
                + "".join(f"<option>{value}</option>" for value in values)
                + "</select></label>"
                for name, values in LABELS.items()
            )
            page = (
                '<!doctype html><meta charset="utf-8"><title>Local query review</title>'
                "<style>body{max-width:850px;margin:40px auto;font:16px system-ui;"
                "padding:20px}pre{white-space:pre-wrap;background:#f3f5f7;padding:20px}"
                "label{display:block;margin:15px 0}select{margin-left:20px}</style>"
                f"<h1>Review {len(saved['annotations']) + 1}/{len(selected)}</h1>"
                "<p>Infer intent only when supported. Source does not establish actor. "
                "Confirmed actor requires self-report or client evidence. "
                "An annotator interpretation is not the user's reported goal.</p>"
                f"<p>Channel: {row.source}; stratum N={population}, n={n}.</p>"
                f"<pre>{html.escape(row.text)}</pre><form>{options}"
                "<button>Save label and continue</button></form>"
                '<script>document.querySelector("form").onsubmit=async e=>{'
                "e.preventDefault();"
                "let labels=Object.fromEntries(new FormData(e.target));"
                'let r=await fetch("/label",{method:"POST",'
                f'headers:{{"X-Review-Token":"{token}"}},'
                f'body:JSON.stringify({{position:"{position}",labels}})}});'
                "if(r.ok)location.reload();else alert(await r.text());};</script>"
            )
            self._reply(page.encode("utf-8"))

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/label" or self.headers.get("X-Review-Token") != token:
                self._reply(b"Forbidden", 403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    raise ValueError
                payload = json.loads(self.rfile.read(length))
                position, labels = payload["position"], payload["labels"]
                if position not in positions or set(labels) != set(LABELS):
                    raise ValueError
                if any(labels[k] not in values for k, values in LABELS.items()):
                    raise ValueError
                if (
                    labels["actor"] != "unknown"
                    and labels["evidence"] == "annotator_inference"
                ):
                    raise ValueError
                row, population, n = positions[position]
                saved["annotations"][position] = {
                    **labels,
                    "source": row.source,
                    "stratum_population": population,
                    "stratum_sample": n,
                }
                output.parent.mkdir(parents=True, exist_ok=True)
                temporary = output.with_suffix(output.suffix + ".tmp")
                temporary.write_text(json.dumps(saved, indent=2), encoding="utf-8")
                temporary.replace(output)
            except (ValueError, TypeError, KeyError):
                self._reply(b"Invalid labels or unsupported actor attribution", 400)
                return
            self._reply(b"Saved")

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    return http.server.HTTPServer(("127.0.0.1", port), Handler)
