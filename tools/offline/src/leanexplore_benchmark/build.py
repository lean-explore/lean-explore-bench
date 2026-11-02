"""Build a reproducible offline report from a private export."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

from leanexplore_benchmark import __version__
from leanexplore_benchmark.insights import analyze
from leanexplore_benchmark.querylog import load_export


def build(input_path: Path, out: Path) -> None:
    """Write aggregate-only artifacts. No network, annotations or raw examples."""
    from leanexplore_benchmark.cli import _audit

    exported = load_export(input_path)
    summary = analyze(exported.rows)
    out.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).parent
    manifest = {
        "version": __version__,
        "python": platform.python_version(),
        "input_sha256": exported.sha256,
        "first_day": summary["first_day"],
        "last_day": summary["last_day"],
        "min_count": 10,
        "min_channel_section": 100,
        "rounding_base": 10,
        "retrieval_evaluated": False,
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source.iterdir())
            if p.suffix in {".py", ".html"}
        },
        "normalization": (
            "NFC_whitespace_case_preserving_with_unordered_package_filters"
        ),
    }
    for name, value in (("summary.json", summary), ("manifest.json", manifest)):
        (out / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    flat: list[dict[str, Any]] = []

    def flatten(value: Any, path: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                flatten(child, [*path, key])
        elif isinstance(value, int) or value is None:
            flat.append({"measure": "/".join(path), "count": value})

    flatten(summary, [])
    with (out / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["measure", "count"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(flat)
    payload = json.dumps(summary, ensure_ascii=True).replace("<", "\\u003c")
    template = (source / "overview.html").read_text(encoding="utf-8-sig")
    (out / "index.html").write_text(
        template.replace("__SUMMARY__", payload), encoding="utf-8", newline="\n"
    )
    for name, since in (
        ("full", None),
        (
            "without-first-day",
            dt.date.fromisoformat(summary["first_day"]) + dt.timedelta(days=1),
        ),
    ):
        if name != "full" and not summary["windows"]["later"]["all"]:
            continue
        _audit(
            argparse.Namespace(
                input=input_path, since=since, out=out / name, min_count=10
            )
        )
    print(f"Open {out / 'index.html'}")
