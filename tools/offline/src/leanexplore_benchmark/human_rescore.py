"""Apply recorded human decisions and rescore immutable retrieval runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from leanexplore_benchmark.assisted import apply_human_corrections
from leanexplore_benchmark.corpus import fingerprint
from leanexplore_benchmark.evaluate import evaluate


def rescore(
    profile: dict[str, Any],
    decisions: list[dict[str, Any]],
    runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return a new label version and paired scores on identical stored rankings."""
    if profile.get("collection", {}).get("validation_profile") != "assisted-v1":
        raise ValueError("Expected an assisted-v1 collection")
    if not decisions or not runs:
        raise ValueError("Provide human decisions and at least one stored run")
    updated = apply_human_corrections(profile, decisions)
    comparison = {}
    for name, run in runs.items():
        before = evaluate(profile["collection"], run, (1, 5, 10, 50, 100))
        after = evaluate(updated["collection"], run, (1, 5, 10, 50, 100))
        comparison[name] = {
            "stored_run_sha256": fingerprint(run),
            "ranking_changed": False,
            "before": before,
            "after": after,
        }
    return {"profile": updated, "comparisons": comparison}


def main() -> None:
    """Read explicit human records; never infer acceptance from AI proposals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("Output exists; choose a new version directory")
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    runs = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(args.runs.glob("*.json"))
    }
    result = rescore(profile, decisions, runs)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, value in result.items():
        (args.out / (name + ".json")).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {"decisions": len(decisions), "runs": len(runs), "ranking_changed": False}
        )
    )


if __name__ == "__main__":
    main()
