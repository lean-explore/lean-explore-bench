"""Aggregate observations and explicitly unvalidated query-intent cues."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import TypeAlias

from leanexplore_benchmark.querylog import Query, normalize, request_key

Cell: TypeAlias = dict[str, str | int | None]
MIN_COUNT = 10
_NAME = re.compile(r"[A-Za-z][\w']*(?:[._][\w']+)+")
_PROOF = re.compile(r"⊢|\b(?:theorem|lemma|example)\b.*?:|:=\s*by\b", re.S)
_QUESTION = re.compile(r"\b(?:how|why|what|which|where|is there|does|can i)\b", re.I)
_LATEX = re.compile(r"\\[A-Za-z]+")

# These rules are deliberately exposed: their precision has not been validated.
_INTENT_PATTERNS = {
    "proof_support": r"⊢|\b(?:prove|proof|proving|rewrite|simp|goal)\b",
    "usage_or_example": r"\b(?:how to use|example|syntax|tactic)\b",
    "explanation": r"\b(?:explain|why|meaning|definition of)\b",
    "discovery": r"\b(?:find|search|is there|looking for|lemma for)\b",
    "enumeration": r"\b(?:list all|all lemmas|all theorems|enumerate)\b",
}
_INTENTS = {k: re.compile(v, re.I) for k, v in _INTENT_PATTERNS.items()}
_DOMAIN_WORDS = {
    "algebra": "group ring field module ideal polynomial algebra homomorphism",
    "analysis": "continuous continuity derivative integral limit convergence norm",
    "topology": "topology topological compact hausdorff neighborhood",
    "number_theory": "prime coprime divisibility divisor congruence modular",
    "combinatorics": "finset graph cardinality permutation combinatorics",
    "probability_measure": "probability random expectation measure measurable",
    "order_logic_sets": "order monotone lattice subset set union intersection logic",
    "linear_algebra": "matrix vector determinant eigenvalue linear",
    "category_theory": "category functor naturaltransformation morphism adjunction",
    "programming": "list array string parser monad io recursion recursive",
}
_DOMAINS = {k: set(v.split()) for k, v in _DOMAIN_WORDS.items()}


def bucket(n: int, bounds: tuple[int, ...]) -> str:
    """Bin counts using a fixed vocabulary, including a separate zero bucket."""
    lower = 0
    for upper in bounds:
        if n <= upper:
            return str(lower) if lower == upper else f"{lower}-{upper}"
        lower = upper + 1
    return f"{lower}+"


def intent_cue(text: str) -> str:
    """Return a hypothesis from English/Lean cues, not a verified user goal."""
    if _NAME.fullmatch(text.strip()):
        return "known_item_candidate"
    matches = [label for label, pattern in _INTENTS.items() if pattern.search(text)]
    if len(matches) > 1:
        return "multiple_cues"
    return matches[0] if matches else "unknown"


def surface(text: str) -> str:
    """Assign a surface label with explicit precedence, independent of intent."""
    if not text.strip():
        return "empty"
    if _PROOF.search(text):
        return "proof_state_or_statement"
    if _NAME.fullmatch(text.strip()):
        return "identifier_only"
    if _LATEX.search(text):
        return "latex_present"
    if _QUESTION.search(text) or "?" in text:
        return "question_like"
    if _NAME.search(text):
        return "mixed_identifier_text"
    if any(c in text for c in "∀∃→↔≤≥∈∑∏=<>⊆"):
        return "symbolic_expression"
    return "other_text"


def features(row: Query) -> dict[str, str]:
    """Measure surface facts and fixed-vocabulary hypotheses in memory."""
    text = row.text
    # ASCII word/namespace splitting gives domain cues, not language detection.
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    domain_hits = [name for name, words in _DOMAINS.items() if words & tokens]
    visible = [c for c in text if not c.isspace()]
    symbols = sum(not (c.isalnum() or c in "_.'") for c in visible)
    percent = round(100 * symbols / len(visible)) if visible else 0
    return {
        "surface": surface(text),
        "intent_cue": intent_cue(text),
        "domain_cue": (
            domain_hits[0]
            if len(domain_hits) == 1
            else "multiple_domains"
            if domain_hits
            else "unknown"
        ),
        "words": bucket(len(text.split()), (0, 2, 4, 8, 16, 32, 64, 128)),
        "characters": bucket(len(text), (0, 32, 64, 128, 256, 512, 1024)),
        "symbol_percent": bucket(percent, (0, 10, 25, 50, 75, 100)),
        "filtered": "yes" if row.packages else "no",
        "filter_count": bucket(len(set(row.packages)), (0, 1, 3)),
        "multiline": "yes" if "\n" in text else "no",
        "non_ascii": "yes" if not text.isascii() else "no",
        "latex": "yes" if _LATEX.search(text) else "no",
        "proof_marker": "yes" if _PROOF.search(text) else "no",
        "identifier_present": "yes" if _NAME.search(text) else "no",
    }


def rounded(n: int) -> int:
    """Round half up to a multiple of ten."""
    return (n + 5) // 10 * 10


def release(counter: Counter[tuple[str, str]], min_count: int) -> list[Cell]:
    """Suppress small cells and a complementary cell, then round counts.

    Fixed labels are the only inputs. This is output minimization, not a
    guarantee against reconstruction across many reports or user anonymity.
    """
    if min_count < MIN_COUNT:
        raise ValueError(f"min_count must be at least {MIN_COUNT}")
    ordered = sorted(counter.items(), key=lambda item: item[1])
    small = [item for item in ordered if item[1] < min_count]
    kept = [item for item in ordered if item[1] >= min_count]
    if len(small) == 1 and kept:
        small.append(kept.pop(0))
    cells: list[Cell] = [
        {"source": source, "category": label, "count": rounded(n)}
        for (source, label), n in sorted(kept)
    ]
    if small:
        total = sum(n for _, n in small)
        cells.append(
            {
                "source": "suppressed",
                "category": "suppressed",
                "count": rounded(total) if total >= min_count else None,
            }
        )
    return cells


def profile(rows: tuple[Query, ...], min_count: int = MIN_COUNT) -> list[Cell]:
    """Produce event-weighted and distinct-request tables without raw query data.

    Repeat counts are computed within source using normalized text and filters.
    Distinct views omit result count/day: these vary across repeated requests.
    """
    if not rows:
        raise ValueError("No queries selected")
    repeats = Counter((row.source, request_key(row)) for row in rows)
    seen: set[tuple[str, tuple[str, tuple[str, ...]]]] = set()
    counters: dict[tuple[str, str], Counter[tuple[str, str]]] = defaultdict(Counter)
    for row in rows:
        key = row.source, request_key(row)
        dims = features(row)
        dims["repeats"] = bucket(repeats[key], (0, 1, 2, 5, 10, 20, 50, 100))
        dims["source"] = "requests"
        for view in ("events", "distinct_requests"):
            if view == "distinct_requests" and key in seen:
                continue
            for dimension, label in dims.items():
                counters[view, dimension][row.source, label] += 1
        seen.add(key)
        count = row.result_count
        result = (
            "missing" if count is None else bucket(count, (0, 1, 5, 10, 25, 50, 100))
        )
        for dimension, label in {
            "results": result,
            "day": row.day.isoformat(),
            "weekday": row.day.strftime("%A"),
            "surface_results": dims["surface"] + " / " + result,
            "intent_results": dims["intent_cue"] + " / " + result,
        }.items():
            counters["events", dimension][row.source, label] += 1
    counters["global", "distinct_texts"]["all", "distinct_texts"] = len(
        {normalize(row.text) for row in rows}
    )
    counters["global", "distinct_requests"]["all", "distinct_requests"] = len(
        {request_key(row) for row in rows}
    )
    cells: list[Cell] = []
    for (view, dimension), counter in sorted(counters.items()):
        cells.extend(
            {"view": view, "dimension": dimension, **cell}
            for cell in release(counter, min_count)
        )
    return cells
