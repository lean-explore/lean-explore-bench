from pathlib import Path

import pytest

from lean_explore_bench.mix import profile as mix_profile
from lean_explore_bench.mix.profile import (
    binned_words,
    compare,
    divergence,
    name_position,
    profile,
    read_queries,
    render,
    word_bin,
    word_count,
)

QUERIES = (
    ["Nat.add_comm", "Finset.sum_comm", "List.map_id"]
    + ["even sum natural numbers", "prime divisor bound", "open set union"]
    + ["Finset.sum commute bijection", "reindex sum Finset.map", "x Finset.sum y"]
    + ["is the sum of two even numbers even?", "a sum of squares is not negative"]
    + ["a + b = b + a", ""]
)


def test_profile_counts_forms_and_styles() -> None:
    result = profile(QUERIES, min_count=1)
    assert result["distinct"] == 12 and result["searches"] == 12
    forms = result["forms"]
    assert set(forms) == {"name", "keywords", "names+keywords", "prose", "formal"}
    assert forms["name"]["share_of_distinct"] == 0.25
    assert forms["name"]["words"] == {"1": 1.0}
    assert forms["name"]["names"] == {"1": 1.0}
    assert forms["name"]["name_position"] == {}
    assert forms["keywords"]["marks"] == {"lower case": 1.0}
    assert forms["keywords"]["words"] == {"3": 0.6667, "4": 0.3333}
    assert forms["keywords"]["skeletons"] == {"W W W": 0.6667, "W W W W": 0.3333}
    mixed = forms["names+keywords"]
    assert mixed["name_position"] == {"first": 0.3333, "inside": 0.3333, "last": 0.3333}
    assert forms["prose"]["marks"]["question"] == 0.5
    assert forms["formal"]["distinct"] == 1


def test_weights_and_suppression() -> None:
    weighted = profile(["Nat.add_comm", "even sum natural numbers"], [9, 1], 1)
    assert weighted["searches"] == 10
    assert weighted["forms"]["name"]["share_of_searches"] == 0.9
    assert weighted["forms"]["name"]["share_of_distinct"] == 0.5
    suppressed = profile(QUERIES * 4, min_count=10)
    assert set(suppressed["forms"]) == {"name", "keywords", "names+keywords"}
    assert suppressed["forms"]["keywords"]["words"] == {}
    assert suppressed["forms"]["name"]["words"] == {"1": 1.0}
    with pytest.raises(ValueError):
        profile(["a", "b"], [1.0])


def test_marks_and_helpers() -> None:
    marks = profile(["solve $x^2$ for the `Nat` case of ∑"], min_count=1)["forms"]
    assert marks["prose+names"]["marks"] == {
        "backtick": 1.0,
        "latex": 1.0,
        "non-ASCII": 1.0,
    }
    assert word_count("a b  c") == 3
    assert word_count(" ".join(["w"] * 99)) == mix_profile.MAX_WORDS
    assert [word_bin(n) for n in (0, 1, 3, 5, 8, 16, 24, 40, 41, 60)] == [
        "1",
        "1",
        "2-3",
        "4-5",
        "6-8",
        "13-16",
        "17-24",
        "25-40",
        "41+",
        "41+",
    ]
    assert binned_words({"2": 0.25, "3": 0.25, "7": 0.5}) == {"2-3": 0.5, "6-8": 0.5}
    assert name_position("Finset.sum of terms Finset.map") == "both ends"


def test_divergence() -> None:
    assert divergence({"a": 0.5, "b": 0.5}, {"a": 1, "b": 1}) == 0.0
    assert divergence({"a": 1.0}, {"b": 1.0}) == 1.0
    assert 0 < divergence({"a": 0.9, "b": 0.1}, {"a": 0.5, "b": 0.5}) < 1
    assert divergence({}, {}) == 0.0


def test_compare_and_render() -> None:
    reference = profile(QUERIES, min_count=1)
    candidate = profile(
        ["Nat.succ_le", "prime", "long run plain keywords here now today", "x + y = z"],
        min_count=1,
    )
    result = compare(reference, candidate)
    assert 0 < result["form_divergence"] < 1
    assert set(result["forms"]) == {"name", "keywords", "formal"}
    name = result["forms"]["name"]
    assert name["words_divergence"] == 0.0 and name["median_words"] == [1, 1]
    assert name["reference_share"] == 0.25 and name["candidate_share"] == 0.25
    keywords = result["forms"]["keywords"]
    assert keywords["words_divergence"] == 1.0
    assert keywords["marks"]["lower case"] == [1.0, 1.0]
    text = render(result)
    assert "Divergence between the form distributions" in text
    assert "| name | 0.250 | 0.250 | 1 and 1 | 0.000 | 0.000 |" in text
    assert compare(reference, reference)["form_divergence"] == 0.0


def test_read_queries_accepts_several_layouts(tmp_path: Path) -> None:
    lines = tmp_path / "queries.jsonl"
    lines.write_text('{"query": "Nat.add_comm", "id": 1}\n\n{"query": " "}\n')
    assert read_queries(lines) == ["Nat.add_comm"]
    listed = tmp_path / "queries.json"
    listed.write_text('["a + b = b + a", {"query": "even sum"}, ""]')
    assert read_queries(listed) == ["a + b = b + a", "even sum"]
    plain = tmp_path / "queries.txt"
    plain.write_text("sum of squares\n\n[1, 2] is a list\n42\n")
    assert read_queries(plain) == ["sum of squares", "[1, 2] is a list", "42"]
