import random

from lean_explore_bench.builder.style import (
    FALLBACK_WORDS,
    Style,
    draw_style,
    length_problem,
    word_range,
)

PROFILE = {
    "forms": {
        "keywords": {
            "words": {"5": 0.5, "6": 0.5, "1": 0.2},
            "marks": {"lower case": 1.0, "question": 1.0},
        },
        "prose": {"words": {"12": 1.0}, "marks": {"question": 1.0}},
        "prose+names": {"words": {"6": 1.0}, "names": {"0": 0.5, "4+": 0.5}},
        "names": {"words": {"3": 1.0}, "names": {"3": 1.0}},
        "names+keywords": {"words": {"7": 1.0}, "names": {"2": 1.0}},
        "formal": {"words": {"9": 1.0}, "marks": {"lower case": 1.0}},
    }
}


def test_styles_follow_the_profile() -> None:
    rng = random.Random(0)
    drawn = [draw_style("keywords", PROFILE, rng) for _ in range(200)]
    assert {style.words for style in drawn} == {2, 5, 6}
    assert all(style.lower_case and not style.question for style in drawn)
    assert all(style.names == 0 for style in drawn)

    prose = draw_style("prose", PROFILE, rng)
    assert prose == Style(words=12, names=0, lower_case=False, question=True)
    assert draw_style("prose+names", PROFILE, rng).names == 3
    assert draw_style("names", PROFILE, rng) == Style(words=3, names=3)
    assert draw_style("names+keywords", PROFILE, rng) == Style(words=7, names=2)
    formal = draw_style("formal", PROFILE, rng)
    assert formal.words == 9 and not formal.lower_case


def test_fallback_without_a_profile() -> None:
    rng = random.Random(1)
    for form, words in FALLBACK_WORDS.items():
        style = draw_style(form, None, rng)
        assert style.words == words and not style.lower_case and not style.question
    assert draw_style("names", {"forms": {}}, rng) == Style(words=2, names=2)
    assert draw_style("prose+names", None, rng).names == 1
    assert draw_style("goal", PROFILE, rng).to_json() == {
        "words": 12,
        "names": 0,
        "lower_case": False,
        "question": False,
    }


def test_length_range() -> None:
    assert word_range(Style(words=6)) == (4, 8)
    assert word_range(Style(words=20)) == (13, 27)
    assert word_range(Style(words=2)) == (1, 4)
    assert length_problem("one two three four", Style(words=6)) is None
    assert length_problem("one two three", Style(words=6)) == (
        "3 words where 4 to 8 were asked for"
    )
    assert length_problem(" ".join(["w"] * 9), Style(words=6)) is not None
