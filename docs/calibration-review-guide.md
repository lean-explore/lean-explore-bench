# Calibration review guide

Review these cases against the [calibration decisions](benchmark-review-questions-2026-11-06.md) and the [evaluation protocol](evaluation-protocol.md). Treat the following analysis as proposals, not additional accepted human labels. Preserve source and corpus evidence in the external review records.

## Verify complete assumptions

For the invariant-complement interpretation of Maschke's theorem, inspect `MonoidAlgebra.Submodule.exists_isCompl` with `[Field k]`, `[Group G]`, `[Finite G]`, `[NeZero (Nat.card G : k)]`, `[AddCommGroup V]` and `[Module k[G] V]`. Require a complement for every `Submodule k[G] V`. Avoid adding a finite-dimensional hypothesis that the inspected declaration does not require. Keep the proposed scope pending independent review.

For one-variable translation of iterated derivatives, inspect `iteratedDeriv_comp_const_add` and `iteratedDeriv_comp_add_const`. Include a nontrivially normed scalar field and the normed additive group/normed-space assumptions on the codomain. Distinguish whole-domain derivatives from derivatives within a set. Do not infer an extra smoothness hypothesis from the informal phrase alone; check the actual total derivative operator and declaration type.

Replace the assumption that a proposed chain-rule target is a direct answer with an explicit relevance check. A chain rule can support a derivation without directly stating translation invariance for an arbitrary iteration count. Keep target corrections proposed until accepted.

## Distinguish related function spaces

For precomposition by a surjective linear map, specify the domain and codomain of the induced map on linear-map spaces. Treat `Function.Surjective.injective_comp_right` as a possible proof component, with coercion and extensionality steps made explicit.

Do not treat `LinearMap.funLeft_injective_of_surjective` as a direct theorem about spaces of linear maps: its displayed construction acts on ordinary function spaces equipped with pointwise module structure. Treat `LinearMap.dualMap_injective_of_surjective` as a specialization to scalar-valued linear maps unless the query explicitly requests dual spaces. Review the necessary adaptation before assigning grade 2 or 3.

## Clarify definition-search tasks

For the maximal-spectrum query, specify whether the request is for the type of maximal ideals, a predicate on an ideal, or a topology. Propose `MaximalSpectrum` for the type-of-maximal-ideals interpretation under `[CommSemiring R]`. Review `Ideal.IsMaximal` and the equivalence to a subtype as distinct candidates. Do not treat a local ring's distinguished maximal ideal as the same task without a scope change.

## Check order compatibility

For multiplication through a finite supremum, inspect `Finset.apply_sup_eq_sup_comp` and its deprecated alias `Finset.comp_sup_eq_sup_comp`. Instantiate the map with left multiplication only after proving preservation of binary suprema and bottom. Reverse the equality when needed to match the query.

Treat `NNReal.mul_finset_sup` as a result for nonnegative reals, not a proof of the query over an arbitrary canonically ordered commutative semiring. Check the compatibility of multiplication with the chosen order structure before accepting a generalization. Leave the original hypotheses unresolved until that check is complete; do not invent a missing assumption or assert the statement false without evidence.

## Record missing proposals and exposed answers

For polynomial equality from sufficiently many distinct evaluations, inspect `Polynomial.eq_of_natDegree_lt_card_of_eval_eq`. Match the commutative-domain assumptions, injectivity of the evaluation points and strict bound on the maximum degree. Review the finset variant separately and document any conversion between indexed and finset evaluations.

Record that this calibration query already contains a theorem name matching the result. Classify it as answer-exposed development material. Do not use it to claim name-free formula retrieval. Also record that the original proposed-target list was empty, although a matching candidate is present in the corpus. Distinguish this label-construction issue from corpus absence or retrieval failure.

## Complete the review

Retain the four accepted positive pairs without extending them to the rest of their pools. Review equivalents, one-direction results, restricted specializations and unrelated candidates separately. Keep every new proposal out of accepted metrics until reviewed. Record independent judgments before adjudication, and measure active query, pair and adjudication time separately.