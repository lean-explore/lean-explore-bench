import pytest

from lean_explore_bench.querylog.normalize import normalize_query


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("  ℝ  ->  x₁ <= y ", "ℝ → x₁ ≤ y"),
        ("a <-> b, c >= d, e != f", "a ↔ b, c ≥ d, e ≠ f"),
        ("|-x| <-1", "|-x| <-1"),  # ambiguous ASCII is left alone
        ("tab\tand\nnewline", "tab and newline"),
    ],
)
def test_normalize_query(text: str, expected: str) -> None:
    assert normalize_query(text) == expected


def test_nfc_keeps_lean_symbols_that_nfkc_would_change() -> None:
    assert normalize_query("ℕ x₁") == "ℕ x₁"


def test_casefold_is_opt_in() -> None:
    assert normalize_query("Nat.Prime") == "Nat.Prime"
    assert normalize_query("Nat.Prime", casefold=True) == "nat.prime"
