"""Sort any query into one of eight forms by its surface alone.

The forms are the benchmark's data types. Each is defined by a rule on
topic-free features (token kinds, function words, Lean syntax), so the same
rule sorts real searches on the server and written queries in the mix, and
a form can be described in public without showing what anyone searched for.

- ``name``: one Lean name and nothing else.
- ``names``: several Lean names and nothing else.
- ``names+keywords``: Lean names with other words, not a sentence.
- ``keywords``: words only, not a sentence.
- ``prose``: natural language without Lean names or code.
- ``prose+names``: natural language with Lean names or code.
- ``formal``: a Lean statement, signature or pattern.
- ``goal``: a proof state.
"""

import re

from lean_explore_bench.features import FUNCTION_WORDS, measure, skeleton

FORMS = (
    "name",
    "names",
    "names+keywords",
    "keywords",
    "prose",
    "prose+names",
    "formal",
    "goal",
)

_SYNTAX = (
    r"[∀∃λ→↔≤≥≠∈∉⊆∣∘×∑∏⁻¹]|:=|<->|->|\bfun\b|\bforall\b"
    r"|\(\w+ : [^)]+\)|\{\w+ : [^}]+\}|\[\w+ [^\]]+\]"
)
_LEAN = re.compile(_SYNTAX)
"""Syntax that only Lean code uses."""
_LEAN_LOOSE = re.compile(_SYNTAX + r"|\([^()]*\)|=|[<>+*^]")
"""Lean syntax plus operators and bracketed groups, which prose also uses."""
_HOLE = re.compile(r"(?<![\w.])_(?![\w.])|\?[A-Za-z]")
"""A placeholder in a pattern: ``_`` on its own, or ``?a``."""
_QUESTION = re.compile(
    r"^(is there|are there|how|does|do we|what|where|which|why|can|is it|do)\b",
    re.IGNORECASE,
)


def is_question(text: str) -> bool:
    """Whether the query is phrased as a question."""
    stripped = text.strip()
    return stripped.endswith("?") or _QUESTION.search(stripped) is not None


def token_kinds(text: str) -> list[str]:
    """Return the kind of every word token: ``ID``, ``W``, ``NUM`` or ``F``.

    ``F`` marks an English function word. Symbols and holes are dropped.
    """
    kinds = []
    for kind in skeleton(text).split():
        if kind in {"ID", "W", "NUM"}:
            kinds.append(kind)
        elif kind in FUNCTION_WORDS:
            kinds.append("F")
    return kinds


def classify(text: str) -> str:
    """Return the form of a query.

    Rules, applied in order:

    1. A goal marker (``⊢`` or ``|-``) makes a ``goal``.
    2. Lean syntax without sentence structure makes a ``formal`` query: at
       least two pieces of Lean syntax (operators, binders, bracketed
       groups, holes), or a high share of symbols, and almost no function
       words.
    3. Function words making up at least 10% of the words, or a question,
       make natural language: ``prose+names`` when a Lean name or code
       appears, otherwise ``prose``. The statistical categories fitted to the
       search log split at the same place: their keyword categories hold
       no function words at all.
    4. What remains has no sentence structure: ``name`` (one name),
       ``names`` (only names), ``names+keywords`` or ``keywords``.
    """
    stripped = text.strip()
    if "⊢" in stripped or "|-" in stripped:
        return "goal"
    features = measure(stripped)
    kinds = token_kinds(stripped)
    names = kinds.count("ID")
    functions = kinds.count("F")
    holes = len(_HOLE.findall(stripped))
    loose = len(_LEAN_LOOSE.findall(stripped)) + holes
    if features.function_word_share < 0.08 and (
        loose >= 2 or features.symbol_share > 0.12
    ):
        return "formal"
    code = len(_LEAN.findall(stripped)) + holes
    sentence = functions >= 1 and features.function_word_share >= 0.1
    if sentence or is_question(stripped):
        coded = names > 0 or "`" in stripped or code > 0
        return "prose+names" if coded else "prose"
    if names == 0:
        return "keywords"
    if names == len(kinds):
        return "name" if names == 1 else "names"
    return "names+keywords"
