"""Measure topic-free surface features of queries.

Nothing here classifies queries. It only measures them, so that categories
can be found statistically (:mod:`lean_explore_bench.analysis.categories`).
Features are chosen to describe *how* someone searches, never *what about*:

- numeric shares (identifiers, prose, symbols) and lengths;
- a *skeleton* that keeps a query's structure but drops its content. Lean
  identifiers become ``ID``, other words ``W``, numbers ``NUM`` and
  placeholders (``_``, ``?x``) ``HOLE``; English function words and symbols
  are kept. For example ``Finset.sum_comm or a reindexing lemma`` becomes
  ``ID or W W W``, and ``_ + _ = _ + _`` becomes ``HOLE + HOLE = HOLE + HOLE``.

Because neither reveals subject matter, categories built from them can be
described in public without showing what users search for.
"""

import re
from dataclasses import asdict, dataclass

import pandas as pd

FUNCTION_WORDS = frozenset(
    """
    a an the of in on for to from with without by at as is are was be been
    that which who whose what when where how why if then than and or but not
    no nor so such this these those there it its any every each all some
    does do can could should would will we you my our me iff
    """.split()
)
"""English function words; a standard stop-word style list."""

_TOKEN = re.compile(
    r"\?[A-Za-z][\w']*|[^\W\d][\w'.₀-₉]*[\w'₀-₉]|[^\W\d]|\d+(?:\.\d+)?|[^\w\s]"
)
_IDENTIFIER = re.compile(
    r"[^\W\d_][\w']*(?:[._][\w']+)+|[a-z]+[A-Z][\w']*|[A-Z][a-z]+[A-Z][\w']*"
)
_LATEX = re.compile(r"\\[A-Za-z]+")


@dataclass(frozen=True)
class QueryFeatures:
    r"""Surface measurements of one query.

    Attributes:
        n_chars: Characters.
        n_words: Word tokens (identifiers, words and numbers).
        identifier_share: Share of word tokens that look like Lean names.
        function_word_share: Share of word tokens that are English function
            words (single letters excluded; in maths they are variables).
        symbol_share: Share of non-space characters that are neither
            alphanumeric nor part of a name.
        latex_commands: Number of LaTeX commands such as ``\sum``.
    """

    n_chars: int
    n_words: int
    identifier_share: float
    function_word_share: float
    symbol_share: float
    latex_commands: int


def _token_kind(token: str) -> str:
    if token == "_" or token.startswith("?"):
        return "HOLE"
    if token[0].isdigit():
        return "NUM"
    if not (token[0].isalpha() or token[0] == "_"):
        return token
    if _IDENTIFIER.fullmatch(token.strip(".")):
        return "ID"
    lowered = token.casefold()
    if len(lowered) > 1 and lowered in FUNCTION_WORDS:
        return lowered
    return "W"


def skeleton(text: str) -> str:
    """Replace a query's content with token kinds, keeping its structure.

    Args:
        text: The query text.

    Returns:
        Space-separated token kinds and symbols, e.g. ``"ID or W W W"``.
    """
    return " ".join(_token_kind(token) for token in _TOKEN.findall(text))


def measure(text: str) -> QueryFeatures:
    """Measure one query.

    Args:
        text: The query text.

    Returns:
        Its :class:`QueryFeatures`.
    """
    kinds = [_token_kind(token) for token in _TOKEN.findall(text)]
    words = [kind for kind in kinds if kind[0].isalpha()]
    visible = [char for char in text if not char.isspace()]
    symbols = sum(not (char.isalnum() or char in "_.'") for char in visible)
    n_words = len(words)
    return QueryFeatures(
        n_chars=len(text),
        n_words=n_words,
        identifier_share=words.count("ID") / n_words if n_words else 0.0,
        function_word_share=(
            sum(kind.islower() for kind in words) / n_words if n_words else 0.0
        ),
        symbol_share=symbols / len(visible) if visible else 0.0,
        latex_commands=len(_LATEX.findall(text)),
    )


FEATURE_COLUMNS: tuple[str, ...] = tuple(QueryFeatures.__dataclass_fields__)


def add_features(frame: pd.DataFrame, text_column: str = "query") -> pd.DataFrame:
    """Return a copy of ``frame`` with feature columns and a ``skeleton``.

    Args:
        frame: Any DataFrame with a text column.
        text_column: Column holding the query text.

    Returns:
        A new DataFrame.
    """
    texts = frame[text_column].tolist()
    measured = pd.DataFrame(
        [asdict(measure(text)) for text in texts],
        index=frame.index,
        columns=list(FEATURE_COLUMNS),
    )
    result = pd.concat([frame, measured], axis=1)
    result["skeleton"] = [skeleton(text) for text in texts]
    return result
