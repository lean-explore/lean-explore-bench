"""Rule checks that a written query has the form its bucket promises.

These checks are cheap and deterministic. They run before the judge, and
they catch the common failures of a language model: leaking the target's
name, writing in another form than the one asked for, or at another length.
"""

import re

from lean_explore_bench.mix.forms import classify
from lean_explore_bench.mix.style import NATURAL_LENGTH_FORMS, Style, length_problem

MAX_QUERY_CHARS = 600
MAX_GOAL_CHARS = 1500
MIN_LEAK_CHARS = 6

_HEADER = re.compile(r"^\s*(?:theorem|lemma|def|abbrev)\s+[^\s:({\[]+")
_NORMAL = re.compile(r"[^a-z0-9]+")
_HUMP = re.compile(r"[a-z0-9][A-Z]")


def leaks_name(query: str, name: str) -> bool:
    """Whether ``query`` contains the target's name or its distinctive part.

    The last component counts as distinctive when it is at least six
    characters long and is a compound (``sum_comm``, ``IsOverdamped``).
    Single words (``map``, ``measure``) are ordinary vocabulary.
    """
    lowered = query.lower()
    if name.lower() in lowered:
        return True
    last = name.rsplit(".", 1)[-1]
    compound = "_" in last or _HUMP.search(last) is not None
    return len(last) >= MIN_LEAK_CHARS and compound and last.lower() in lowered


def form_problem(query: str, query_type: str) -> str | None:
    """Return why ``query`` does not fit ``query_type``, or None if it does.

    The bucket of a query is its form, so the main test is that
    :func:`lean_explore_bench.mix.forms.classify` sorts the query into the
    bucket it was written for.
    """
    text = query.strip()
    if not text:
        return "empty"
    if len(text) > (MAX_GOAL_CHARS if query_type == "goal" else MAX_QUERY_CHARS):
        return "too long"
    if "\n" in text and query_type != "goal":
        return "more than one line"
    if query_type == "formal" and _HEADER.search(text):
        return "names a declaration"
    found = classify(text)
    if found != query_type:
        return f"reads as {found}, not {query_type}"
    return None


def copies(query: str, docstring: str | None) -> bool:
    """Whether ``query`` is the docstring, or the docstring contains it whole."""
    if not docstring:
        return False
    normal_query = _NORMAL.sub(" ", query.lower()).strip()
    normal_doc = _NORMAL.sub(" ", docstring.lower()).strip()
    return len(normal_query) >= 20 and normal_query in normal_doc


MAX_COPIED_WORDS = 5
"""Longest run of consecutive words a query may share with a source text."""


def copied_run(query: str, source: str) -> int:
    """Length in words of the longest run that ``query`` shares with ``source``.

    Case, punctuation and Markdown marks are ignored, so quoting a post
    with small edits still counts as copying it.
    """
    words = _NORMAL.sub(" ", query.lower()).split()
    text = " " + " ".join(_NORMAL.sub(" ", source.lower()).split()) + " "
    longest = 0
    for start in range(len(words)):
        end = start + longest + 1
        while end <= len(words) and f" {' '.join(words[start:end])} " in text:
            longest = end - start
            end += 1
    return longest


def problem(
    query: str,
    query_type: str,
    name: str,
    docstring: str | None = None,
    style: Style | None = None,
) -> str | None:
    """Return the first rule a query breaks, or None when it passes."""
    form = form_problem(query, query_type)
    if form is not None:
        return form
    if style is not None and query_type not in NATURAL_LENGTH_FORMS:
        length = length_problem(query, style)
        if length is not None:
            return length
    if leaks_name(query, name):
        return "contains the target name"
    if copies(query, docstring):
        return "copies the docstring"
    return None
