import pytest

from lean_explore_bench.forms import FORMS, classify, is_question, token_kinds


@pytest.mark.parametrize(
    ("query", "form"),
    [
        ("Nat.add_comm", "name"),
        ("add_comm", "name"),
        ("Finset.sum Finset.map", "names"),
        ("Finset.sum commute bijection", "names+keywords"),
        ("contDiff ℝ n smooth iterated", "names+keywords"),
        ("even sum natural numbers", "keywords"),
        ("continuity", "keywords"),
        ("sum of two even numbers is even", "prose"),
        ("is there a lemma about sums?", "prose"),
        ("a lemma that the Finset.sum of zeros is zero", "prose+names"),
        ("how do I rewrite `a ∣ b` for integers", "prose+names"),
        ("is there a lemma for Finset.sum over range?", "prose+names"),
        ("a + b = b + a", "formal"),
        ("List ?a → Nat", "formal"),
        ("_ * (_ + _) = _ * _ + _ * _", "formal"),
        ("forall (x : Nat), x <= x * x", "formal"),
        ("Functor.map (f x) = g (η k)", "formal"),
        ("h : a ≤ b\n⊢ a + c ≤ b + c", "goal"),
        ("|- a = b", "goal"),
    ],
)
def test_classify(query: str, form: str) -> None:
    assert classify(query) == form
    assert form in FORMS


def test_every_query_has_a_form() -> None:
    for query in ("", "   ", "?", "12 34", "∑"):
        assert classify(query) in FORMS


def test_is_question_and_token_kinds() -> None:
    assert is_question("Is there a lemma for this")
    assert is_question("commutativity of addition?")
    assert not is_question("commutativity of addition")
    assert token_kinds("the Finset.sum of 2 terms ≤ x") == [
        "F",
        "ID",
        "F",
        "NUM",
        "W",
        "W",
    ]
