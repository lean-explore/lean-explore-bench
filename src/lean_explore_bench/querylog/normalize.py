"""Normalise query text so that trivially different spellings compare equal.

Lean names are case-sensitive (``Nat.add_comm`` vs ``nat.add_comm`` can be
different declarations), so case is folded only when the caller asks for it.
"""

import re
import unicodedata

ASCII_TO_UNICODE: tuple[tuple[str, str], ...] = (
    ("<->", "↔"),
    ("->", "→"),
    ("<=", "≤"),
    (">=", "≥"),
    ("!=", "≠"),
)
"""ASCII spellings of Lean notation mapped to the symbols Mathlib prints.

``<-`` and ``|-`` are left alone because they also occur in ``x<-1`` and
``|-x|``.
"""

_WHITESPACE = re.compile(r"\s+")


def normalize_query(text: str, casefold: bool = False) -> str:
    """Return a canonical form of a query for grouping duplicates.

    Applies NFC (not NFKC, which would turn ``ℝ`` into ``R`` and ``x₁`` into
    ``x1``), maps ASCII notation to Lean's Unicode symbols, collapses
    whitespace and strips the ends.

    Args:
        text: Raw query text.
        casefold: Also fold case. Use for natural-language queries only.

    Returns:
        The normalised query.
    """
    text = unicodedata.normalize("NFC", text)
    for ascii_form, symbol in ASCII_TO_UNICODE:
        text = text.replace(ascii_form, symbol)
    text = _WHITESPACE.sub(" ", text).strip()
    return text.casefold() if casefold else text
