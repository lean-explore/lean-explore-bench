"""Prepare external benchmark cases and audit their split constraints."""

from __future__ import annotations

import copy
import unicodedata
from collections import defaultdict
from typing import Any

from leanexplore_benchmark.corpus import Corpus, fingerprint
from leanexplore_benchmark.evaluate import validate

Json = dict[str, Any]
SPLITS = {"train", "development", "test"}
FORMS = {"name", "keywords", "prose", "formula", "mixed"}


def _text(value: object, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(description)
    return value


def _identifiers(value: object, description: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(description)
    return value


def _review(value: Json) -> None:
    if value.get("assessor_type") not in {"human", "assistant"}:
        raise ValueError("Review requires its assessor type")
    if value.get("status") not in {"proposed", "accepted", "rejected"}:
        raise ValueError("Review requires an explicit status")
    _text(value.get("reviewer"), "Review requires an assessor identifier")
    _text(value.get("reason"), "Review requires evidence and reasoning")
    if type(value.get("uncertain")) is not bool:
        raise ValueError("Review requires explicit uncertainty")
    if value["status"] == "accepted" and (
        value["assessor_type"] != "human" or value["uncertain"]
    ):
        raise ValueError("Only an explicit, resolved human review may be accepted")


def _cases(dataset: Json, corpus: Corpus) -> list[Json]:
    if type(dataset.get("schema_version")) is not int or dataset["schema_version"] != 1:
        raise ValueError("Unsupported benchmark schema")
    if dataset.get("corpus_revision") != corpus.revision:
        raise ValueError("Dataset and corpus revisions differ")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset requires cases")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Case must be an object")
        identifier = _text(case.get("id"), "Case requires an identifier")
        if identifier in seen:
            raise ValueError("Duplicate case identifier")
        seen.add(identifier)
        _text(case.get("query"), "Case requires query text")
        if (
            _text(case.get("split"), "Missing split") not in SPLITS
            or _text(case.get("form"), "Missing form") not in FORMS
        ):
            raise ValueError("Invalid split or query form")
        if _text(case.get("track"), "Missing track") not in {
            "human",
            "agent",
            "unknown",
        }:
            raise ValueError("Invalid provenance track")
        links = _identifiers(case.get("links"), "Case requires grouping links")
        if not links:
            raise ValueError("Case requires at least one source or family link")
        _identifiers(case.get("targets", []), "Invalid proposed targets")
        if type(case.get("family_reviewed")) is not bool:
            raise ValueError("Case requires family review status")
        if type(case.get("test_exposed")) is not bool:
            raise ValueError("Case requires test exposure status")
        if case["split"] == "test" and (
            case["test_exposed"] or not case["family_reviewed"]
        ):
            raise ValueError("Test cases require reviewed families and no exposure")
        if not isinstance(case.get("reviews", []), list):
            raise ValueError("Reviews must be a list")
        if not isinstance(case.get("adjudications", []), list):
            raise ValueError("Adjudications must be a list")
    return cases


def audit_splits(dataset: Json, corpus: Corpus) -> Json:
    """Reject cross-split connected components, including indirect overlaps."""
    cases = _cases(dataset, corpus)
    parents = {case["id"]: case["id"] for case in cases}

    def root(identifier: str) -> str:
        while parents[identifier] != identifier:
            parents[identifier] = parents[parents[identifier]]
            identifier = parents[identifier]
        return identifier

    owners: dict[str, str] = {}
    for case in cases:
        text = " ".join(unicodedata.normalize("NFC", case["query"]).split())
        tokens = {"link:" + link for link in case["links"]}
        tokens.add("query:" + fingerprint(text))
        targets = list(case.get("targets", []))
        for review in case.get("reviews", []):
            if not isinstance(review, dict):
                raise ValueError("Invalid review")
            targets.append(
                _text(review.get("document_id"), "Review requires a document")
            )
        for target in targets:
            tokens.add("target:" + (corpus.resolve(target) or target))
        for token in tokens:
            if token in owners:
                a, b = root(case["id"]), root(owners[token])
                parents[max(a, b)] = min(a, b)
            else:
                owners[token] = case["id"]
    components: dict[str, list[Json]] = defaultdict(list)
    for case in cases:
        components[root(case["id"])].append(case)
    groups = []
    for members in components.values():
        if len({case["split"] for case in members}) != 1:
            raise ValueError("Linked benchmark cases cross split boundaries")
        ids = sorted(case["id"] for case in members)
        groups.append(
            {
                "group_id": "group-" + fingerprint(ids)[:24],
                "case_ids": ids,
                "split": members[0]["split"],
                "family_reviewed": all(c["family_reviewed"] for c in members),
            }
        )
    return {
        "dataset_sha256": fingerprint(dataset),
        "corpus_manifest_sha256": corpus.sha256,
        "groups": sorted(groups, key=lambda group: group["group_id"]),
        "note": "Connected components enforce supplied constraints; they do not "
        "discover unrecorded mathematical equivalences.",
    }


def _judgments(case: Json, corpus: Corpus) -> dict[str, int]:
    reviews = case.get("reviews", [])
    accepted: dict[str, list[Json]] = defaultdict(list)
    all_reviews: dict[str, Json] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("Invalid review")
        identifier = _text(review.get("id"), "Review requires an identifier")
        if identifier in all_reviews:
            raise ValueError("Duplicate review identifier")
        _review(review)
        document = _text(review.get("document_id"), "Review requires a document")
        grade = review.get("grade")
        if grade is not None and (type(grade) is not int or grade not in range(4)):
            raise ValueError("Review grade must be null or integer 0..3")
        if review["status"] == "accepted":
            if grade is None:
                raise ValueError("Accepted review requires a grade")
            canonical = corpus.require(document)
            if any(r["reviewer"] == review["reviewer"] for r in accepted[canonical]):
                raise ValueError("Repeated accepted review by one assessor")
            accepted[canonical].append(review)
        all_reviews[identifier] = review
    decisions: dict[str, int] = {}
    for decision in case.get("adjudications", []):
        if not isinstance(decision, dict):
            raise ValueError("Invalid adjudication")
        _review(decision)
        if decision["status"] != "accepted":
            continue
        canonical = corpus.require(
            _text(decision.get("document_id"), "Adjudication requires a document")
        )
        if canonical in decisions:
            raise ValueError("Duplicate adjudication for a document")
        referenced = _identifiers(
            decision.get("review_ids"), "Adjudication requires original reviews"
        )
        expected = {r["id"] for r in accepted[canonical]}
        if (
            not expected
            or set(referenced) != expected
            or len(referenced) != len(expected)
        ):
            raise ValueError(
                "Adjudication must reference all accepted original reviews"
            )
        grade = decision.get("grade")
        if type(grade) is not int or grade not in range(4):
            raise ValueError("Adjudication grade must be integer 0..3")
        decisions[canonical] = grade
    judgments = {}
    for canonical, records in accepted.items():
        grades = {r["grade"] for r in records}
        if canonical in decisions:
            judgments[canonical] = decisions[canonical]
        elif len(grades) == 1:
            judgments[canonical] = records[0]["grade"]
        else:
            raise ValueError("Conflicting reviews require recorded adjudication")
    return judgments


def prepare_collection(dataset: Json, corpus: Corpus, split: str) -> Json:
    """Build scorer inputs while retaining review and availability evidence."""
    if split not in SPLITS:
        raise ValueError("Invalid requested split")
    audit = audit_splits(dataset, corpus)
    group_ids = {
        identifier: group["group_id"]
        for group in audit["groups"]
        for identifier in group["case_ids"]
    }
    queries, sidecar = [], []
    for case in dataset["cases"]:
        if case["split"] != split:
            continue
        judgments = _judgments(case, corpus)
        answerability = case.get("answerability", "unknown")
        if answerability not in {"answerable", "unanswerable", "unknown"}:
            raise ValueError("Invalid answerability")
        if answerability == "unanswerable":
            evidence = case.get("answerability_review")
            if not isinstance(evidence, dict):
                raise ValueError("Unanswerability requires expert review")
            _review(evidence)
            if evidence["status"] != "accepted":
                raise ValueError("Unanswerability requires accepted expert review")
        queries.append(
            {
                "id": case["id"],
                "group_id": group_ids[case["id"]],
                "track": case["track"],
                "answerability": answerability,
                "judgments": judgments,
            }
        )
        record = copy.deepcopy(case)
        record["group_id"] = group_ids[case["id"]]
        record["availability"] = [
            corpus.availability(target) for target in case.get("targets", [])
        ]
        sidecar.append(record)
    collection = {"corpus_revision": corpus.revision, "queries": queries}
    validate(
        collection, {"corpus_revision": corpus.revision, "max_k": 1, "results": {}}
    )
    return {
        "collection": collection,
        "sidecar": sidecar,
        "split_audit": audit,
        "corpus_manifest_sha256": corpus.sha256,
        "dataset_sha256": fingerprint(dataset),
    }


def adapt_run(
    rows: list[Json], collection: Json, corpus: Corpus, name: str, max_k: int
) -> Json:
    """Adapt external observations, keeping failures and missing requests."""
    if collection["corpus_revision"] != corpus.revision:
        raise ValueError("Collection and corpus revisions differ")
    for query in collection["queries"]:
        for document in query["judgments"]:
            if corpus.require(document) != document:
                raise ValueError("Collection judgments must use canonical IDs")
    results: dict[str, Json] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Observation must be an object")
        identifier = _text(row.get("id"), "Observation requires a case identifier")
        if identifier in results:
            raise ValueError("Duplicate observation identifier")
        documents = _identifiers(row.get("documents"), "Invalid ranked documents")
        results[identifier] = {
            key: row[key]
            for key in ("status", "latency_ms", "cost_usd", "abstained")
            if key in row
        }
        results[identifier]["documents"] = [corpus.require(d) for d in documents]
    run = {
        "name": _text(name, "Run requires a name"),
        "corpus_revision": corpus.revision,
        "max_k": max_k,
        "results": results,
    }
    validate(collection, run)
    return run
