"""Figures and score data of the paper.

  scores.json       Success@1 and Success@10 on the test split
  figures/forms.pdf      the same by form, for the three semantic engines

Run from the repository root, with the benchmark in data/mix-v6:
    python3 paper/figures.py [MIX_DIRECTORY]
The second run needs only scores.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ENGINES = {
    "leanexplore": ("LeanExplore", "#BB480B"),
    "leansearch": ("LeanSearch", "#2a78d6"),
    "leanfinder": ("Lean Finder", "#1baf7a"),
    "loogle": ("Loogle", "#a3a39e"),
}
FORMS = [
    "name",
    "names",
    "names+keywords",
    "keywords",
    "prose",
    "prose+names",
    "formal",
    "goal",
    "question",
]
BUCKET = {
    "name": "names and keywords",
    "names": "names and keywords",
    "names+keywords": "names and keywords",
    "keywords": "names and keywords",
    "prose": "natural language",
    "prose+names": "natural language",
    "formal": "formal",
    "goal": "formal",
    "question": "real questions",
}
INK, MUTED, GRID = "#222222", "#6B5B4A", "#EDE6DA"


def first_answer(record: dict, result: dict) -> int | None:
    """Rank of the first result graded 2 or 3, among the first ten."""
    for position, name in enumerate(result.get("documents", [])[:10], start=1):
        if record["judgments"].get(name, 0) >= 2:
            return position
    return None


def compute(mix: Path) -> dict:
    """Score every engine on the test split, by form and by bucket."""
    lines = (mix / "queries.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    test = [record for record in records if record["split"] == "test"]
    scores: dict = {"queries": {}, "forms": {}, "buckets": {}}
    for form in FORMS:
        scores["queries"][form] = sum(r["query_type"] == form for r in test)
    for engine in ENGINES:
        run = {}
        for line in (mix / "runs" / f"{engine}.jsonl").read_text().splitlines():
            row = json.loads(line)
            run[row["id"]] = row
        ranks = {r["id"]: first_answer(r, run[r["id"]]) for r in test}

        def share(group: list[dict], depth: int) -> float:
            hits = sum((ranks[r["id"]] or 99) <= depth for r in group)
            return hits / len(group)

        scores["forms"][engine] = {
            form: [
                share([r for r in test if r["query_type"] == form], k) for k in (1, 10)
            ]
            for form in FORMS
        }
        scores["buckets"][engine] = {
            bucket: [
                share([r for r in test if BUCKET[r["query_type"]] == bucket], k)
                for k in (1, 10)
            ]
            for bucket in dict.fromkeys(BUCKET.values())
        }
    return scores


def draw(scores: dict) -> None:
    """Draw the scores by form for the three semantic engines."""
    shown = [engine for engine in ENGINES if engine != "loogle"]
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for axis, index, title in zip(
        axes, (1, 0), ("Answer in the first ten", "Answer first")
    ):
        for offset, engine in enumerate(shown):
            label, colour = ENGINES[engine]
            values = [scores["forms"][engine][form][index] for form in FORMS]
            places = [row + (offset - 1) * 0.26 for row in range(len(FORMS))]
            axis.barh(places, values, height=0.22, color=colour, label=label)
        axis.set_title(title, fontsize=9, color=INK, loc="left")
        axis.set_xlim(0, 1)
        axis.set_yticks(range(len(FORMS)))
        axis.set_yticklabels(FORMS, fontsize=8, color=INK)
        axis.tick_params(axis="x", labelsize=8, colors=MUTED)
        axis.tick_params(axis="y", length=0)
        axis.grid(True, axis="x", color=GRID, linewidth=0.6)
        axis.set_axisbelow(True)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)
    axes[0].invert_yaxis()
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles, labels, fontsize=8, frameon=False, ncol=3, loc="lower center"
    )
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    figure.savefig(HERE / "figures" / "forms.pdf")


def main() -> None:
    """Recompute the scores when a mix directory is given, then draw."""
    path = HERE / "scores.json"
    if len(sys.argv) > 1:
        path.write_text(json.dumps(compute(Path(sys.argv[1])), indent=2) + "\n")
    draw(json.loads(path.read_text()))


if __name__ == "__main__":
    main()
