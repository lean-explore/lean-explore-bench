import random

from lean_explore_bench.mix import prompts
from lean_explore_bench.mix.corpus import Declaration
from lean_explore_bench.mix.forms import FORMS
from lean_explore_bench.mix.style import Style

DECLARATION = Declaration(
    name="Nat.add_comm",
    module="Init.Core",
    library="core",
    area="Core",
    kind="theorem",
    docstring="Addition commutes.",
    source_text="theorem Nat.add_comm (a b : Nat) : a + b = b + a := by omega",
    informalization="Addition of natural numbers is commutative.",
)


def test_every_written_form_has_an_instruction() -> None:
    covered = set(prompts.FORM_INSTRUCTIONS) | set(prompts.VARIANTS)
    assert covered == set(FORMS) - {"name"}
    assert not set(prompts.FORM_INSTRUCTIONS) & set(prompts.VARIANTS)


def test_choose_variant() -> None:
    formal = {prompts.choose_variant("formal", random.Random(i)) for i in range(200)}
    assert formal == set(prompts.VARIANTS["formal"])
    assert prompts.choose_variant("prose", random.Random(1)) == "prose"


def test_style_instruction() -> None:
    prose = prompts.style_instruction(
        "prose", "prose", Style(words=10, lower_case=True, question=True)
    )
    assert prompts.FORM_INSTRUCTIONS["prose"] in prose
    assert "about 10 words: no fewer than 6 and no more than 14" in prose
    assert "Phrase it as a question." in prose
    assert "Write everything in lower case." in prose
    plain = prompts.style_instruction("prose+names", "prose+names", Style(12, 2))
    assert "Mention 2 Lean identifier(s)." in plain
    assert "Do not phrase it as a question." in plain
    names = prompts.style_instruction("names", "names", Style(words=3, names=3))
    assert "Give exactly 3 identifiers." in names and "Use about" not in names
    goal = prompts.style_instruction("goal", "state", Style(words=20))
    assert prompts.VARIANTS["goal"]["state"] in goal and "question" not in goal


def test_writer_messages_carry_the_declaration_and_the_form() -> None:
    system, user = prompts.writer_messages(
        DECLARATION, "formal", "statement", Style(words=9)
    )
    assert system["content"] == prompts.WRITER_SYSTEM
    text = str(user["content"])
    assert "Name: Nat.add_comm" in text
    assert "Description:\nAddition of natural numbers" in text
    assert "Form: " + prompts.VARIANTS["formal"]["statement"] in text
    assert "rejected" not in text
    again = prompts.writer_messages(
        DECLARATION, "keywords", "keywords", Style(6), ("too many words", "too long")
    )
    assert "rejected (too long)" in str(again[1]["content"])
    assert "too many words" in str(again[1]["content"])


def test_judge_messages_and_missing_description() -> None:
    bare = Declaration(**{**DECLARATION.__dict__, "informalization": None})
    system, user = prompts.judge_messages(bare, "a + b = b + a")
    assert system["content"] == prompts.JUDGE_SYSTEM
    assert str(user["content"]).startswith("Query:\na + b = b + a")
    assert "Description:" not in str(user["content"])
