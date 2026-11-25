"""Describe a set of queries by form, and by style within each form.

A profile holds shares only: how searches divide over the forms of
:mod:`lean_explore_bench.forms`, and within each form how long queries
are, how many Lean names they hold and where, how often they are lower case
or phrased as questions, and which token patterns recur. Cells counted
fewer than ``min_count`` times are left out, so a profile of the real search
log can leave the server without showing what anyone searched for.

The same profile is computed for the benchmark mix. Comparing the two says
how well the mix reflects real searches, and the real profile is what the
generator samples from when it writes queries.
"""

import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from lean_explore_bench.features import skeleton
from lean_explore_bench.forms import FORMS, classify, is_question, token_kinds

MAX_WORDS = 60
TOP_SKELETONS = 15
WORD_BINS = (1, 2, 4, 6, 9, 13, 17, 25, 41)
"""Lower edges of the word-count bins used to compare length distributions."""

_LATEX = re.compile(r"\$|\\[A-Za-z]{2,}")


def read_queries(path: Path) -> list[str]:
    """Read query texts from a file, whatever its layout.

    Accepted layouts: JSON Lines whose objects have a ``query`` field, a
    JSON list of strings or of such objects, and plain text with one query
    per line. Blank entries are dropped.
    """
    text = path.read_text(encoding="utf-8")

    def pick(item: Any) -> str:
        return str(item["query"]) if isinstance(item, dict) else str(item)

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        loaded = None
    if isinstance(loaded, list):
        queries = [pick(item) for item in loaded]
    else:
        queries = []
        for line in text.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                item = line
            queries.append(pick(item) if isinstance(item, dict) else line)
    return [query for query in queries if query.strip()]


def word_count(text: str) -> int:
    """Number of whitespace-separated tokens, capped at :data:`MAX_WORDS`."""
    return min(len(text.split()), MAX_WORDS)


def word_bin(words: int) -> str:
    """Label of the word-count bin that holds ``words``."""
    lower = max(edge for edge in WORD_BINS if edge <= max(words, 1))
    position = WORD_BINS.index(lower)
    if position == len(WORD_BINS) - 1:
        return f"{lower}+"
    upper = WORD_BINS[position + 1] - 1
    return str(lower) if upper == lower else f"{lower}-{upper}"


def name_position(text: str) -> str:
    """Where the Lean names sit among the words: first, last, both or inside."""
    kinds = token_kinds(text)
    first, last = kinds[0] == "ID", kinds[-1] == "ID"
    if first and last:
        return "both ends"
    return "first" if first else "last" if last else "inside"


def _shares(counts: Counter[str], total: float, min_count: int) -> dict[str, float]:
    return {
        key: round(count / total, 4)
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= min_count
    }


def _form_profile(
    queries: Sequence[str], weights: Sequence[float], min_count: int
) -> dict[str, Any]:
    """Profile the distinct queries of one form."""
    total = len(queries)
    words: Counter[str] = Counter()
    names: Counter[str] = Counter()
    positions: Counter[str] = Counter()
    skeletons: Counter[str] = Counter()
    marks: Counter[str] = Counter()
    for query in queries:
        kinds = token_kinds(query)
        count = kinds.count("ID")
        words[str(word_count(query))] += 1
        names[str(count) if count < 4 else "4+"] += 1
        skeletons[skeleton(query)] += 1
        if count and len(kinds) > count:
            positions[name_position(query)] += 1
        letters = [char for char in query if char.isalpha()]
        flags = {
            "lower case": bool(letters) and query == query.lower(),
            "question": is_question(query),
            "latex": _LATEX.search(query) is not None,
            "backtick": "`" in query,
            "non-ASCII": any(ord(char) > 127 for char in query),
        }
        marks.update(name for name, present in flags.items() if present)
    located = sum(positions.values())
    return {
        "distinct": total,
        "searches": sum(weights),
        "words": _shares(words, total, min_count),
        "names": _shares(names, total, min_count),
        "name_position": _shares(positions, located, min_count) if located else {},
        "marks": _shares(marks, total, min_count),
        "skeletons": dict(
            list(_shares(skeletons, total, min_count).items())[:TOP_SKELETONS]
        ),
    }


def profile(
    queries: Iterable[str],
    weights: Iterable[float] | None = None,
    min_count: int = 10,
) -> dict[str, Any]:
    """Profile a set of distinct queries.

    Args:
        queries: Distinct query texts.
        weights: Number of searches for each query; one each when omitted.
        min_count: Cells counted fewer times than this are left out.

    Returns:
        Totals, the share of each form among searches and among distinct
        queries, and a style profile of each form.
    """
    texts = [query.strip() for query in queries]
    counts = list(weights) if weights is not None else [1.0] * len(texts)
    by_form: dict[str, tuple[list[str], list[float]]] = defaultdict(lambda: ([], []))
    for text, weight in zip(texts, counts, strict=True):
        if text:
            members = by_form[classify(text)]
            members[0].append(text)
            members[1].append(weight)
    distinct = sum(len(members[0]) for members in by_form.values())
    searches = sum(sum(members[1]) for members in by_form.values())
    forms = {
        form: {
            "share_of_searches": round(sum(by_form[form][1]) / searches, 4),
            "share_of_distinct": round(len(by_form[form][0]) / distinct, 4),
            **_form_profile(by_form[form][0], by_form[form][1], min_count),
        }
        for form in FORMS
        if len(by_form[form][0]) >= min_count
    }
    return {"searches": searches, "distinct": distinct, "forms": forms}


def binned_words(words: dict[str, float]) -> dict[str, float]:
    """Collapse a word-count distribution into :data:`WORD_BINS`."""
    binned: dict[str, float] = defaultdict(float)
    for count, share in words.items():
        binned[word_bin(int(count))] += share
    return dict(binned)


def divergence(first: dict[str, float], second: dict[str, float]) -> float:
    """Jensen-Shannon divergence of two distributions, between 0 and 1.

    Each distribution is normalised first, so shares with suppressed cells
    can be compared. Zero means identical; one means disjoint.
    """
    keys = set(first) | set(second)
    total_first = sum(first.values()) or 1.0
    total_second = sum(second.values()) or 1.0
    result = 0.0
    for key in keys:
        p = first.get(key, 0.0) / total_first
        q = second.get(key, 0.0) / total_second
        mean = (p + q) / 2
        for value in (p, q):
            if value > 0:
                result += 0.5 * value * math.log2(value / mean)
    return round(result, 4)


def compare(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare a candidate profile with a reference profile.

    Returns:
        The divergence between the two form distributions (by searches),
        and for each form present in both: its share in each profile, the
        divergence of the word-count and name-count distributions, the
        median word counts, and the difference in each mark's rate.
    """

    def form_shares(value: dict[str, Any]) -> dict[str, float]:
        return {
            form: entry["share_of_searches"] for form, entry in value["forms"].items()
        }

    def median(words: dict[str, float]) -> int:
        running, half = 0.0, sum(words.values()) / 2
        for count in sorted(words, key=int):
            running += words[count]
            if running >= half:
                return int(count)
        return 0

    forms = {}
    for form in FORMS:
        if form not in reference["forms"] or form not in candidate["forms"]:
            continue
        ref, cand = reference["forms"][form], candidate["forms"][form]
        marks = sorted(set(ref["marks"]) | set(cand["marks"]))
        forms[form] = {
            "reference_share": ref["share_of_searches"],
            "candidate_share": cand["share_of_searches"],
            "words_divergence": divergence(
                binned_words(ref["words"]), binned_words(cand["words"])
            ),
            "names_divergence": divergence(ref["names"], cand["names"]),
            "median_words": [median(ref["words"]), median(cand["words"])],
            "marks": {
                mark: [ref["marks"].get(mark, 0.0), cand["marks"].get(mark, 0.0)]
                for mark in marks
            },
        }
    return {
        "form_divergence": divergence(form_shares(reference), form_shares(candidate)),
        "forms": forms,
    }


def render(comparison: dict[str, Any]) -> str:
    """Render a comparison from :func:`compare` as a Markdown table."""
    lines = [
        f"Divergence between the form distributions: "
        f"{comparison['form_divergence']:.3f} (0 identical, 1 disjoint)",
        "",
        "| Form | Reference share | Candidate share | Median words | "
        "Length divergence | Name-count divergence |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for form, entry in comparison["forms"].items():
        reference, candidate = entry["median_words"]
        lines.append(
            f"| {form} | {entry['reference_share']:.3f} | "
            f"{entry['candidate_share']:.3f} | {reference} and {candidate} | "
            f"{entry['words_divergence']:.3f} | {entry['names_divergence']:.3f} |"
        )
    return "\n".join(lines) + "\n"
