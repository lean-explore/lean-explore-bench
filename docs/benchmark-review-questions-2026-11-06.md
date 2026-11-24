# Calibration decisions

Use this record to review the initial development calibration before freezing relevance labels. Apply grade 3 to a direct answer or an equally usable equivalent result. Keep proposed interpretations separate from accepted query-document judgments.

Read the [benchmark status](benchmark-status.md) for experimental coverage and the [evaluation protocol](evaluation-protocol.md) for the draft scoring rules. Treat the responses below as normalized English decision records. Preserve the original query even when its intended scope is clarified.

## Review prompts and responses

| ID | Review prompt | Recorded response |
| --- | --- | --- |
| Q01 | Include mathematical calibration alongside technical work? | Include both. |
| Q02 | Interpret `Ordinal.inductionOn` as exact lookup or mathematical search? | Use mathematical search; accept equivalent induction principles. |
| Q03 | Interpret `InformationTheory.klDiv_eq_zero_iff` as exact lookup or mathematical search? | Characterize when KL divergence is zero; allow other lemmas. |
| Q04 | Is `Maschke's theorem` specific enough to grade? | Clarify the field, characteristic and theorem formulation before grading. |
| Q05 | For ordinal induction, require the principle on quotient representatives or transfinite induction? | Require the principle on representatives, including equivalent formulations. |
| Q06 | Assign grade 3 to `Ordinal.inductionOn` for that clarified intent? | Accept grade 3. |
| Q07 | Restrict the KL task to finite measures and assign grade 3 to `InformationTheory.klDiv_eq_zero_iff`? | Use finite measures; accept grade 3. |
| Q08 | Choose complete reducibility, semisimplicity of the group algebra, or leave the Maschke formulation unresolved? | Defer the choice for specialist assessment; no formulation or grade accepted. |
| Q09 | For natural-number addition, allow a general theorem directly specializable to `ℕ`? | Accept only a lemma specific to `ℕ`. |
| Q10 | For `f : α → Set α`, require a proof of non-surjectivity without additional assumptions on `α`? | Confirm this intent. |
| Q11 | For iterated derivatives and translation, choose a one-variable derivative, a Fréchet derivative, or leave the interpretation unresolved? | Defer the choice for specialist assessment; no candidate grade accepted. |
| Q12 | Assign grade 3 to `Nat.add_comm` for the Nat-specific task? | Accept grade 3. |
| Q13 | Assign grade 3 to `Function.cantor_surjective` for the non-surjectivity task? | Accept grade 3. |

## Apply the accepted decisions

### Ordinal induction

Retain the query `Ordinal.inductionOn`. Interpret it as induction on representatives of the quotient defining ordinals, allowing equivalent formulations. Use the following candidate statement as the basis for the accepted grade of 3:

```lean
{motive : Ordinal → Prop} (o : Ordinal)
    (type : ∀ (α r) [IsWellOrder α r], motive (Ordinal.type r)) : motive o
```

Record that the distinction from well-founded induction was clarified after candidate exposure. Mark any explicit rewritten query as an answer-informed development variant. Review alternative principles separately; do not infer their grades from this accepted pair.

### Zero KL divergence

Retain the query `InformationTheory.klDiv_eq_zero_iff`. Restrict the intended task to finite measures and accept grade 3 for:

```lean
[IsFiniteMeasure μ] [IsFiniteMeasure ν] : klDiv μ ν = 0 ↔ μ = ν
```

Record that the finite-measure restriction followed candidate exposure. Do not claim that the original bare-name query independently specified those assumptions. Leave one-direction lemmas and special cases unjudged until reviewed.

### Natural-number addition

Retain the query:

```lean
∀ a b : ℕ, a + b = b + a
```

Apply the recorded preference for a Nat-specific lemma and accept grade 3 for `Nat.add_comm`:

```lean
∀ (n m : Nat), n + m = m + n
```

Treat the Nat-specific restriction as a task preference. Do not classify a general theorem as mathematically false merely because it requires specialization. Resolve the grading policy for such alternatives before freezing the rubric.

### Non-surjectivity onto a power set

Retain the query `Given f : α → Set α, find a theorem showing that f cannot be surjective.` Accept grade 3 for `Function.cantor_surjective`:

```lean
{α} (f : α → Set α) : ¬ Function.Surjective f
```

Keep the task free of additional assumptions on `α`. Grade definitions and supporting results separately.

## Resolve the proposed interpretations

For `Maschke's theorem`, review the invariant-complement formulation: every submodule of a group-algebra module has a complement under the appropriate field and finite-group assumptions. Check `MonoidAlgebra.Submodule.exists_isCompl` against its full context. Keep this formulation and its candidate grade proposed until specialist review is complete.

For `Iterated derivatives commute with translating the input by a constant`, review the one-variable, whole-domain interpretation first. Treat a Fréchet formulation as a separately specified variant. Check domain, scalar field, codomain and the exact derivative operator before accepting a grade.

## Preserve review limits

Count four explicitly accepted positive pairs and two unresolved specialist cases among the six cases discussed. Complete the remaining calibration cases on linear-map precomposition, maximal spectra, finite suprema and polynomial evaluations. Grade alternatives and negatives in the discussed pools as well.

Treat the four positive decisions as assisted calibration judgments: each followed a suggested grade and explanation. Do not count them as independently elicited blind annotations or use them to report inter-rater agreement. Keep unjudged pairs unjudged.

Record the absence of measured active review time. Do not convert elapsed conversation time into an annotation-rate estimate. Distinguish source inspection from fresh Lean compilation of a candidate in its pinned environment.

Bind each accepted pair to its original review packet when integrating it into the evaluator. Preserve the different identity of the expanded candidate pool. Report judgment coverage with any partial-label diagnostic; do not describe four accepted positive pairs as a frozen benchmark.