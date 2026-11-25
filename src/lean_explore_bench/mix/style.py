"""Draw the style of each written query from a profile of real searches.

A style fixes what the writer is told beyond the form: how many words to
use, how many Lean names to mention, and whether to write in lower case or
as a question. Each value is sampled from the distribution that real
searches of the same form follow, taken from a profile made by
:mod:`lean_explore_bench.mix.profile`. Without a profile, typical values
are used.
"""

import random
from dataclasses import asdict, dataclass
from typing import Any

FALLBACK_WORDS = {
    "names": 2,
    "names+keywords": 6,
    "keywords": 6,
    "prose": 12,
    "prose+names": 13,
    "formal": 11,
    "goal": 12,
}
"""Median word counts of real searches, used when no profile is given."""

MIN_WORDS = {
    "names": 2,
    "names+keywords": 3,
    "keywords": 2,
    "prose": 4,
    "prose+names": 5,
    "formal": 3,
    "goal": 3,
}
"""Shortest query of each form that can still identify one declaration."""


LOWER_CASE_FORMS = frozenset({"keywords", "prose"})
"""Forms that can be written in lower case without damaging Lean names."""


NATURAL_LENGTH_FORMS = frozenset({"formal", "goal"})
"""Forms written at the length of the statement itself. A Lean statement or
proof state cannot be stretched or cut to a drawn word count without
padding it or removing its spaces, and too few real searches have these
forms for their lengths to be worth matching."""


@dataclass(frozen=True)
class Style:
    """How one query should be written.

    Attributes:
        words: Target number of whitespace-separated words.
        names: Number of Lean names to mention, for forms that mention any.
        lower_case: Write everything in lower case.
        question: Phrase the query as a question.
    """

    words: int
    names: int = 0
    lower_case: bool = False
    question: bool = False

    def to_json(self) -> dict[str, Any]:
        """Return the style as a JSON object."""
        return asdict(self)


def _draw(distribution: dict[str, float], rng: random.Random) -> str | None:
    """Draw a key in proportion to its share; None for an empty distribution."""
    if not distribution:
        return None
    keys = sorted(distribution)
    return rng.choices(keys, weights=[distribution[key] for key in keys])[0]


def draw_style(form: str, profile: dict[str, Any] | None, rng: random.Random) -> Style:
    """Draw a style for one query of ``form``.

    Args:
        form: The query's form; not ``name``, which needs no style.
        profile: A profile of real searches, or None for typical values.
        rng: Random source.

    Returns:
        The style. Word counts below the form's minimum are raised to it,
        because a shorter query could not single out one declaration.
    """
    entry = (profile or {}).get("forms", {}).get(form, {})
    marks = entry.get("marks", {})
    drawn_words = _draw(entry.get("words", {}), rng)
    words = int(drawn_words) if drawn_words is not None else FALLBACK_WORDS[form]
    words = max(words, MIN_WORDS[form])
    names = 0
    if form in {"names", "names+keywords", "prose+names"}:
        drawn = _draw(
            {key: share for key, share in entry.get("names", {}).items() if key != "0"},
            rng,
        )
        names = int((drawn or "1").rstrip("+"))
        names = min(names, words if form == "names" else max(1, words // 2))
        if form == "names":
            names = words = max(2, names)
    return Style(
        words=words,
        names=names,
        lower_case=form in LOWER_CASE_FORMS
        and rng.random() < marks.get("lower case", 0.0),
        question=form.startswith("prose") and rng.random() < marks.get("question", 0.0),
    )


def word_range(style: Style) -> tuple[int, int]:
    """Return the fewest and most words a query of this style may have.

    A query may differ from the target by two words or by 35%, whichever
    is larger.
    """
    allowed = max(2, round(style.words * 0.35))
    return max(1, style.words - allowed), style.words + allowed


def length_problem(query: str, style: Style) -> str | None:
    """Return a complaint when a query's length is outside its range."""
    words = len(query.split())
    low, high = word_range(style)
    if not low <= words <= high:
        return f"{words} words where {low} to {high} were asked for"
    return None
