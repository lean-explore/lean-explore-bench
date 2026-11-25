"""Prompts for writing and judging queries about a known declaration.

The writer is told the form of the query (see
:mod:`lean_explore_bench.forms`) and a style drawn from real searches
(see :mod:`lean_explore_bench.builder.style`): how many words, how many Lean
names, whether lower case, whether a question. Formal queries and proof
states also come in a few variants.
"""

import random

from openai.types.chat import ChatCompletionMessageParam

from lean_explore_bench.builder.corpus import Declaration
from lean_explore_bench.builder.style import NATURAL_LENGTH_FORMS, Style, word_range

PROMPT_VERSION = "2026-11-13"

MAX_SOURCE_CHARS = 1500

WRITER_SYSTEM = """\
You write search queries for a benchmark of Lean 4 declaration search engines.

You are shown one Lean declaration. Write the single query that a user would \
type into a search box when this declaration is what they are looking for. \
The user has never seen this declaration: they know the mathematics or the \
programming task, not the name, the docstring or the exact wording. Real \
queries are short and plain, so be brief and do not explain.

Rules for every query:
- This declaration must be a correct and direct answer to the query.
- The query must be specific enough that unrelated declarations on the same \
topic would not answer it equally well.
- Never include the declaration's own name or any part of it written as an \
identifier.
- Do not copy the docstring or the description; use your own words.
- Follow the requested form and length exactly.

Reply with JSON: {"query": "..."}."""

FORM_INSTRUCTIONS: dict[str, str] = {
    "names": (
        "Write only Lean identifiers separated by single spaces, and no other "
        "words: the constants this statement is about (types, functions, "
        "structures, or lemmas it relates). Each must look like a Lean name: "
        "it has a dot, an underscore or an inner capital letter, such as "
        "Finset.sum, add_comm or ContinuousLinearMap."
    ),
    "names+keywords": (
        "Write a run of search terms, not a sentence: Lean identifiers of the "
        "objects involved (such as Finset.sum or ContinuousLinearMap) together "
        "with plain keywords. No words such as 'the', 'of', 'is', 'for', 'a' or "
        "'that', no punctuation."
    ),
    "keywords": (
        "Write a run of keywords, not a sentence: plain mathematical or "
        "programming terms separated by single spaces. No words such as 'the', "
        "'of', 'is', 'for', 'a' or 'that', no punctuation and no Lean "
        "identifiers."
    ),
    "prose": (
        "Write natural language: a plain phrase or sentence in English, with "
        "ordinary connecting words such as 'of', 'the', 'is' or 'for'. No Lean "
        "identifiers, no code, no backticks and no LaTeX."
    ),
    "prose+names": (
        "Write natural language, a plain phrase or sentence in English with "
        "ordinary connecting words such as 'of', 'the', 'is' or 'for', that "
        "mentions Lean identifiers of the objects involved (types, functions "
        "or structures that appear in the statement, such as Finset.sum or "
        "ContinuousLinearMap)."
    ),
}
"""Instructions for the forms that have no variants."""

VARIANTS: dict[str, dict[str, str]] = {
    "formal": {
        "statement": (
            "Write the statement as Lean 4 code, as the user would write it "
            "from scratch, with different names for the bound variables. No "
            "declaration name, no proof, no comments, no English."
        ),
        "conclusion": (
            "Write only the conclusion of the statement as a Lean 4 expression, "
            "with free variables and no binders or hypotheses. For a definition, "
            "write its type signature instead. No English."
        ),
        "pattern": (
            "Write a pattern in the style of Loogle: the shape of the statement "
            "or of the type, with `_` for parts the user does not care about and "
            "`?a`, `?b` for parts that must agree. For example "
            "`_ * (_ + _) = _ * _ + _ * _` or `List ?a → ?a → Bool`. No English."
        ),
        "ascii": (
            "Write the statement or its conclusion as Lean 4 code typed on a "
            "plain keyboard: `forall`, `exists`, `->`, `<->`, `<=`, `fun x =>` "
            "and spelled-out names instead of Unicode symbols, with different "
            "names for the bound variables. No declaration name, no proof, no "
            "English."
        ),
    },
    "goal": {
        "state": (
            "Write a Lean 4 proof state as the infoview shows it: the local "
            "hypotheses, one per line as `name : type`, then a line starting "
            "with `⊢` and the goal. The goal must be one that this declaration "
            "closes directly with `exact` or `apply`. Use concrete variable "
            "names different from those in the source. Separate lines with "
            "newlines."
        ),
        "goal-only": (
            "Write only the goal line of a Lean 4 proof state, starting with "
            "`⊢`. The goal must be one that this declaration closes directly "
            "with `exact` or `apply`, and the goal alone must make clear which "
            "statement is needed. Use concrete variable names different from "
            "those in the source."
        ),
    },
}
"""Instructions for each variant of the forms that have variants."""

JUDGE_SYSTEM = """\
You check items of a benchmark for Lean 4 declaration search engines. Each \
item is a search query and the declaration it was written for. Real search \
queries are short, so judge what a short query asks for, not its polish.

Grade how well the declaration answers the query:
- 3: a direct answer. Someone who searched with this query would be satisfied \
with this declaration as it stands.
- 2: useful, but the user must adapt it in a clear way.
- 1: related to the query but not sufficient.
- 0: not relevant, or incompatible with what the query asks.
For a query that is a proof state, grade 3 means the declaration closes the \
goal directly with `exact` or `apply`.

Also decide whether the query is specific: true when only this declaration, \
or near-identical variants of it, would be a direct answer; false when many \
unrelated declarations on the same topic would answer it equally well.

Reply with JSON: {"grade": 0, "specific": true}."""

WRITER_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
    "additionalProperties": False,
}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "grade": {"type": "integer", "enum": [0, 1, 2, 3]},
        "specific": {"type": "boolean"},
    },
    "required": ["grade", "specific"],
    "additionalProperties": False,
}


def choose_variant(query_type: str, rng: random.Random) -> str:
    """Pick a variant of ``query_type``; forms without variants return it."""
    variants = VARIANTS.get(query_type)
    return rng.choice(sorted(variants)) if variants else query_type


def style_instruction(query_type: str, variant: str, style: Style) -> str:
    """Render the form, variant and style as an instruction for the writer."""
    if query_type in VARIANTS:
        parts = [VARIANTS[query_type][variant]]
    else:
        parts = [FORM_INSTRUCTIONS[query_type]]
    if query_type == "names":
        parts.append(f"Give exactly {style.names} identifiers.")
    elif query_type in NATURAL_LENGTH_FORMS:
        parts.append(
            "Write it at its natural length, as it would appear in Lean: do not "
            "pad it, shorten it or remove spaces."
        )
    else:
        low, high = word_range(style)
        parts.append(
            f"Use about {style.words} words: no fewer than {low} and no more "
            f"than {high}, counting every space-separated token."
        )
        if style.names:
            parts.append(f"Mention {style.names} Lean identifier(s).")
    if style.question:
        parts.append("Phrase it as a question.")
    elif query_type.startswith("prose"):
        parts.append("Do not phrase it as a question.")
    if style.lower_case:
        parts.append("Write everything in lower case.")
    return " ".join(parts)


def describe(declaration: Declaration) -> str:
    """Render a declaration for a prompt."""
    lines = [
        f"Name: {declaration.name}",
        f"Module: {declaration.module}",
        "Source:",
        declaration.source_text[:MAX_SOURCE_CHARS].strip(),
    ]
    if declaration.informalization:
        lines += ["Description:", declaration.informalization.strip()]
    return "\n".join(lines)


def writer_messages(
    declaration: Declaration,
    query_type: str,
    variant: str,
    style: Style,
    rejected: tuple[str, str] | None = None,
) -> list[ChatCompletionMessageParam]:
    """Build the messages asking for a query.

    Args:
        declaration: The target declaration.
        query_type: The bucket the query belongs to.
        variant: The variant, as returned by :func:`choose_variant`.
        style: Length, name count, casing and phrasing to follow.
        rejected: An earlier query for this target and the reason it was
            rejected, so that the writer does not repeat it.
    """
    instruction = style_instruction(query_type, variant, style)
    user = f"{describe(declaration)}\n\nForm: {instruction}"
    if rejected is not None:
        user += (
            f"\n\nAn earlier attempt was rejected ({rejected[1]}):\n{rejected[0]}\n"
            "Write a different query that avoids this problem."
        )
    return [
        {"role": "system", "content": WRITER_SYSTEM},
        {"role": "user", "content": user},
    ]


def judge_messages(
    declaration: Declaration, query: str
) -> list[ChatCompletionMessageParam]:
    """Build the messages asking a judge to grade a query against its target."""
    user = f"Query:\n{query}\n\nDeclaration:\n{describe(declaration)}"
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ]
