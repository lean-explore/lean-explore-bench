# Human review of relevance labels

The pilot's labels were proposed by an AI assistant and have not been independently validated. This
guide explains how a mathematician can check and correct them, and records the calibration
decisions made so far. The grading scale is defined in the
[evaluation protocol](evaluation-protocol.md).

## What a reviewer does

The pending checks are listed in `human-checks.json`, which is part of the external data package
and not of this repository. Each check has an identifier beginning with `HC`: one per case
(`HC-D*` and `HC-T01` to `HC-T30`), plus a few release-wide checks.

For each query-document pair:

1. Read the query and its scope, and check that the recorded interpretation and assumptions are
   right. If the query is invalid or has to change, it becomes a new case version with a new
   retrieval run; the old response is not reused.
2. Read the candidate's complete statement, including implicit parameters and typeclass
   assumptions. A generated declaration needs its own exported type.
3. Assign grade 3, 2, 1 or 0, or leave the pair unresolved if the uncertainty is real.
4. Record your name, the decision, the reason and the active review time.

A review made after seeing the AI grade is an assisted review. Agreement statistics require a
separate assessor who has not seen that grade.

## Recording and rescoring a correction

Decisions go in a JSON list. Each entry has `case_id`, `document_id`, an integer `grade` from 0 to
3, `reviewer`, `assessor_type: human`, `status: accepted`, `uncertain: false` and a substantive
`reason`. The tool rejects assistant proposals presented as accepted decisions.

From `tools/offline`, with the package installed or `PYTHONPATH` pointing to `src`:

```text
python -m leanexplore_benchmark.human_rescore --profile PATH_TO_ASSISTED_JSON --decisions PATH_TO_HUMAN_DECISIONS_JSON --runs PATH_TO_EVALUATION_RUNS --out NEW_REVIEW_VERSION_DIRECTORY
```

The command refuses an existing output directory. It writes a new label profile and the scores
before and after the correction, computed on the stored rankings. The next correction starts from
the new `profile.json`. Rescoring does not mark the release as independently validated.

## Calibration decisions so far

Six of the ten calibration cases have been discussed (record dated 6 November 2026).

| ID | Question | Recorded response |
|---|---|---|
| Q01 | Include mathematical calibration alongside technical work? | Include both. |
| Q02 | Is `Ordinal.inductionOn` exact lookup or mathematical search? | Mathematical search; equivalent induction principles are acceptable. |
| Q03 | Is `InformationTheory.klDiv_eq_zero_iff` exact lookup or mathematical search? | Characterize when KL divergence is zero; other lemmas are allowed. |
| Q04 | Is `Maschke's theorem` specific enough to grade? | Clarify the field, characteristic and formulation first. |
| Q05 | Ordinal induction: on quotient representatives, or transfinite induction? | On representatives, including equivalent formulations. |
| Q06 | Grade 3 for `Ordinal.inductionOn` under that intent? | Accepted. |
| Q07 | Restrict the KL task to finite measures and give `InformationTheory.klDiv_eq_zero_iff` grade 3? | Finite measures; grade 3 accepted. |
| Q08 | Maschke: complete reducibility, semisimplicity of the group algebra, or unresolved? | Deferred to a specialist; no formulation or grade accepted. |
| Q09 | Natural-number addition: allow a general theorem that specializes to `ℕ`? | Only a lemma specific to `ℕ`. |
| Q10 | For `f : α → Set α`, require non-surjectivity with no extra assumptions on `α`? | Confirmed. |
| Q11 | Iterated derivatives and translation: one-variable, Fréchet, or unresolved? | Deferred to a specialist; no grade accepted. |
| Q12 | Grade 3 for `Nat.add_comm` on the `ℕ`-specific task? | Accepted. |
| Q13 | Grade 3 for `Function.cantor_surjective` on the non-surjectivity task? | Accepted. |

### The four accepted grade-3 pairs

Each decision followed a suggested grade and explanation, so these are assisted judgments and not
blind annotations. Other candidates in the same pools remain unjudged.

**Ordinal induction.** Query: `Ordinal.inductionOn`, read as induction on representatives of the
quotient defining ordinals. This reading was fixed after the candidate had been seen.

```lean
{motive : Ordinal → Prop} (o : Ordinal)
    (type : ∀ (α r) [IsWellOrder α r], motive (Ordinal.type r)) : motive o
```

**Zero KL divergence.** Query: `InformationTheory.klDiv_eq_zero_iff`, restricted to finite
measures. The restriction was also added after the candidate had been seen.

```lean
[IsFiniteMeasure μ] [IsFiniteMeasure ν] : klDiv μ ν = 0 ↔ μ = ν
```

**Natural-number addition.** Query:

```lean
∀ a b : ℕ, a + b = b + a
```

Accepted answer, `Nat.add_comm`:

```lean
∀ (n m : Nat), n + m = m + n
```

**Non-surjectivity onto a power set.** Query: `Given f : α → Set α, find a theorem showing that f
cannot be surjective.` Accepted answer, `Function.cantor_surjective`:

```lean
{α} (f : α → Set α) : ¬ Function.Surjective f
```

## Open questions for a specialist

The proposals below are the assistant's and have not been accepted.

### Unresolved: Maschke's theorem formulation

The query is `Maschke's theorem`. The proposed reading is the invariant-complement formulation,
with candidate `MonoidAlgebra.Submodule.exists_isCompl`: under `[Field k]`, `[Group G]`,
`[Finite G]`, `[NeZero (Nat.card G : k)]`, `[AddCommGroup V]` and `[Module k[G] V]`, every
`Submodule k[G] V` has a complement. The question is which formulation the task should mean, and
what grade this candidate then gets.

### Unresolved: iterated derivatives and translation

The query is `Iterated derivatives commute with translating the input by a constant`. The proposed
reading is one-variable and whole-domain, with candidates `iteratedDeriv_comp_const_add` and
`iteratedDeriv_comp_add_const`; a Fréchet version would be a separate variant. The question is
which reading to adopt, and whether a chain rule, which supports a derivation but does not state
the result for an arbitrary iteration count, counts as a direct answer.

### Calibration cases not yet done

| Case | Proposed candidates | Point to settle |
|---|---|---|
| Precomposition by a surjective linear map | `Function.Surjective.injective_comp_right` (proof component), `LinearMap.funLeft_injective_of_surjective`, `LinearMap.dualMap_injective_of_surjective` | `funLeft` acts on ordinary function spaces and `dualMap` covers only scalar-valued maps; what adaptation earns grade 2 or 3? |
| Maximal spectrum | `MaximalSpectrum` under `[CommSemiring R]`, `Ideal.IsMaximal` | Does the query ask for the type of maximal ideals, a predicate on an ideal, or a topology? |
| Multiplication through a finite supremum | `Finset.apply_sup_eq_sup_comp`, its deprecated alias `Finset.comp_sup_eq_sup_comp`, `NNReal.mul_finset_sup` | Does the statement hold over an arbitrary canonically ordered commutative semiring? `NNReal.mul_finset_sup` covers only nonnegative reals. |
| Polynomial equality from enough evaluations | `Polynomial.eq_of_natDegree_lt_card_of_eval_eq` and its finset variant | The query already contains a matching theorem name, so it is answer-exposed. Its proposed-target list was empty although the candidate is in the corpus. |
