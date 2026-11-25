import pytest

from lean_explore_bench.builder.checks import (
    copied_run,
    copies,
    form_problem,
    leaks_name,
    problem,
)
from lean_explore_bench.builder.style import Style


@pytest.mark.parametrize(
    ("query", "query_type"),
    [
        ("the sum of two even numbers is even", "prose"),
        ("even sum natural numbers parity", "keywords"),
        ("a lemma that the Finset.sum of zeros is zero", "prose+names"),
        ("Finset.sum reindex bijection", "names+keywords"),
        ("Finset.sum Finset.map", "names"),
        ("∀ a b : ℕ, a + b = b + a", "formal"),
        ("_ * (_ + _) = _ * _ + _ * _", "formal"),
        ("h : a ≤ b\n⊢ a + c ≤ b + c", "goal"),
    ],
)
def test_well_formed_queries_pass(query: str, query_type: str) -> None:
    assert form_problem(query, query_type) is None


@pytest.mark.parametrize(
    ("query", "query_type", "reason"),
    [
        ("  ", "prose", "empty"),
        ("x" * 601, "prose", "too long"),
        ("two lines of\nthe text here", "prose", "more than one line"),
        ("even sums parity", "prose", "reads as keywords, not prose"),
        ("sum of squares", "keywords", "reads as prose, not keywords"),
        ("the sum of the terms is even", "keywords", "reads as prose, not keywords"),
        ("even sum numbers", "names+keywords", "reads as keywords"),
        ("theorem foo (a : Nat) : a = a", "formal", "names a declaration"),
        ("a + c ≤ b + c", "goal", "reads as formal, not goal"),
    ],
)
def test_malformed_queries_are_rejected(
    query: str, query_type: str, reason: str
) -> None:
    found = form_problem(query, query_type)
    assert found is not None and reason in found


def test_goal_states_may_be_long() -> None:
    assert form_problem("⊢ " + "x" * 1000, "goal") is None
    assert form_problem("⊢ " + "x" * 1600, "goal") == "too long"


def test_leaks_name() -> None:
    assert leaks_name("see Nat.add_comm please", "Nat.add_comm")
    assert leaks_name("something like add_comm_assoc", "Nat.add_comm_assoc")
    assert leaks_name("an isoverdamped oscillator", "Oscillator.IsOverdamped")
    assert not leaks_name("the measure of a set", "MeasureTheory.Measure")
    assert not leaks_name("map of a composition", "List.map")
    assert not leaks_name("commutativity of addition", "Nat.add_comm")


def test_copies_docstring() -> None:
    doc = "The sum of two even numbers is even, for natural numbers."
    assert copies("the sum of two even numbers is even", doc)
    assert not copies("adding even numbers gives an even number", doc)
    assert not copies("is even", doc)
    assert not copies("the sum of two even numbers is even", None)


def test_problem_reports_the_first_broken_rule() -> None:
    name = "Nat.even_add_even"
    good = "the sum of two even numbers is even"
    assert problem(good, "prose", name) is None
    assert problem(good, "prose", name, style=Style(words=8)) is None
    assert problem("even sums", "prose", name) == "reads as keywords, not prose"
    assert problem(good, "prose", name, style=Style(words=20)) == (
        "8 words where 13 to 27 were asked for"
    )
    assert (
        problem("is a lemma named even_add_even about the parity", "prose+names", name)
        == "contains the target name"
    )
    assert (
        problem(good, "prose", name, "The sum of two even numbers is even.")
        == "copies the docstring"
    )


def test_copied_run_ignores_case_and_punctuation() -> None:
    post = "Hi! Is there a *lemma* that the sum, is commutative in mathlib?"
    assert copied_run("is there a lemma that the sum is commutative", post) == 9
    assert copied_run("commutativity of sums", post) == 0
    assert copied_run("the sum", post) == 2
