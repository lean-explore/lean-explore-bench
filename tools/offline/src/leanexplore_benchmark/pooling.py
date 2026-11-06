"""Export blinded candidate evidence and preserve individual review records."""

from __future__ import annotations

import copy
import math
from typing import Any

from leanexplore_benchmark.collection import _review
from leanexplore_benchmark.corpus import Corpus, fingerprint
from leanexplore_benchmark.evaluate import validate

Json = dict[str, Any]


def export_pool(
    prepared: Json, corpus: Corpus, runs: list[Json], depth: int, seed: int
) -> Json:
    """Pool distinct candidates without showing engine identity, score or rank."""
    if type(depth) is not int or depth < 1:
        raise ValueError("Pool depth must be positive")
    collection = prepared["collection"]
    if (
        collection["corpus_revision"] != corpus.revision
        or prepared["corpus_manifest_sha256"] != corpus.sha256
    ):
        raise ValueError("Pool corpus differs from prepared collection")
    if not runs:
        raise ValueError("At least one run is required")
    for run in runs:
        validate(collection, run)
        if depth > run["max_k"]:
            raise ValueError("Requested pool depth exceeds run depth")
    cases, audit = [], []
    for case in prepared["sidecar"]:
        if case["split"] == "test":
            raise ValueError(
                "Development review export cannot expose reserved test cases"
            )
        documents = {
            corpus.require(target)
            for target in case.get("targets", [])
            if corpus.resolve(target) is not None
        }
        query = next(q for q in collection["queries"] if q["id"] == case["id"])
        documents.update(query["judgments"])
        observations = []
        for run_index, run in enumerate(runs):
            result = run["results"].get(
                case["id"], {"status": "missing", "documents": []}
            )
            canonical = [corpus.require(d) for d in result["documents"]]
            documents.update(canonical[:depth])
            observations.append(
                {
                    "run_index": run_index,
                    "status": result["status"],
                    "documents": canonical[:depth],
                }
            )
        ordered = sorted(
            documents,
            key=lambda document: fingerprint([seed, case["id"], document]),
        )
        candidates = []
        for document in ordered:
            evidence = corpus.documents[document]
            candidates.append(
                {
                    "document_id": document,
                    "evidence": {
                        key: evidence[key]
                        for key in ("name", "statement", "context", "module")
                        if key in evidence
                    },
                }
            )
        cases.append(
            {"id": case["id"], "query": case["query"], "candidates": candidates}
        )
        audit.append({"id": case["id"], "observations": observations})
    packet = {
        "schema_version": 1,
        "corpus_revision": corpus.revision,
        "cases": cases,
    }
    return {
        "packet": packet,
        "packet_sha256": fingerprint(packet),
        "audit": audit,
        "binding": {
            "dataset_sha256": prepared["dataset_sha256"],
            "corpus_manifest_sha256": corpus.sha256,
            "run_sha256": [fingerprint(run) for run in runs],
            "depth": depth,
            "seed": seed,
        },
    }


def validate_reviews(packet: Json, submission: Json) -> Json:
    """Validate an assessor's submission without accepting or averaging labels."""
    if submission.get("packet_sha256") != fingerprint(packet):
        raise ValueError("Review packet fingerprint differs")
    reviewer = submission.get("reviewer")
    assessor_type = submission.get("assessor_type")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Submission requires an assessor identifier")
    if assessor_type not in {"human", "assistant"}:
        raise ValueError("Submission requires assessor type")
    valid_pairs = {
        (case["id"], candidate["document_id"])
        for case in packet["cases"]
        for candidate in case["candidates"]
    }
    records = submission.get("records")
    if not isinstance(records, list):
        raise ValueError("Submission requires review records")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid review record")
        pair = (record.get("case_id"), record.get("document_id"))
        if not all(isinstance(key, str) for key in pair):
            raise ValueError("Review requires case and document identifiers")
        if pair not in valid_pairs or pair in seen:
            raise ValueError("Unknown or repeated review pair")
        seen.add(pair)
        _review(
            dict(
                record,
                reviewer=reviewer,
                assessor_type=assessor_type,
                status="proposed",
            )
        )
        grade = record.get("grade")
        if grade is not None and (type(grade) is not int or grade not in range(4)):
            raise ValueError("Review grade must be null or integer 0..3")
        if record["uncertain"] and grade is not None:
            raise ValueError("Uncertain reviews must leave the grade unresolved")
        minutes = record.get("minutes")
        if minutes is not None and (
            type(minutes) not in (int, float)
            or not math.isfinite(minutes)
            or minutes < 0
        ):
            raise ValueError("Review minutes must be nonnegative or null")
    return {
        "status": "proposed",
        "packet_sha256": fingerprint(packet),
        "submission_sha256": fingerprint(submission),
        "original_submission": copy.deepcopy(submission),
    }
