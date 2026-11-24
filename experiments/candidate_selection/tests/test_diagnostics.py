"""Check request accounting and experiment boundaries with invented inputs."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import diagnostic_replay
import representation_probe


def inputs(tmp_path, split="development"):
    data = tmp_path / "data"
    data.mkdir()
    database = data / "lean_explore.db"
    database.write_bytes(b"invented corpus")
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "corpus_revision": "sha256:"
                + hashlib.sha256(database.read_bytes()).hexdigest(),
                "cases": [
                    {"id": "failure", "query": "fail", "split": split},
                    {"id": "success", "query": "succeed", "split": split},
                ],
            }
        )
    )
    models = tmp_path / "models.json"
    models.write_text(
        json.dumps(
            {
                key: {"path": str(data), "revision": "invented"}
                for key in ("Qwen/Qwen3-Embedding-0.6B", "Qwen/Qwen3-Reranker-0.6B")
            }
        )
    )
    return SimpleNamespace(
        cases=cases, data=data, models=models, out=tmp_path / "output"
    )


@pytest.mark.asyncio
async def test_failed_request_remains_and_later_request_runs(tmp_path, monkeypatch):
    import torch

    from lean_explore.search import engine as engine_module

    args = inputs(tmp_path)

    class Model:
        max_seq_length = 512
        prompts = {"query": "invented prompt"}

        def parameters(self):
            yield torch.tensor([1.0])

    class Engine:
        def __init__(self, **kwargs):
            self.engine = self
            self.embedding_client = SimpleNamespace(model=Model())
            self.reranker_client = SimpleNamespace(model=Model(), max_length=256)
            self.indexes = SimpleNamespace(faiss_index=SimpleNamespace(nprobe=64))

        async def search(self, query, **kwargs):
            if query == "fail":
                raise RuntimeError("invented failure")
            if kwargs.get("trace") is not None:
                kwargs["trace"].record("results", [1])
            return [
                SimpleNamespace(model_dump=lambda: {"id": 1, "name": "Example.result"})
            ]

        async def get_by_name(self, query):
            return None

        async def dispose(self):
            pass

    monkeypatch.setattr(engine_module, "SearchEngine", Engine)
    await diagnostic_replay.run(args)
    result = json.loads((args.out / "replay.json").read_text())
    assert result["scheduled_ids"] == ["failure", "success"]
    assert [r["status"] for r in result["records"]] == ["error", "ok"]
    assert result["records"][0]["results"] == []
    assert result["records"][0]["error"]["type"] == "RuntimeError"
    assert result["records"][1]["results"][0]["name"] == "Example.result"
    assert result["state"] == "complete"
    with pytest.raises(FileExistsError):
        await diagnostic_replay.run(args)


@pytest.mark.asyncio
async def test_reserved_test_cases_are_rejected_before_output(tmp_path):
    args = inputs(tmp_path, split="test")
    with pytest.raises(ValueError, match="development-only"):
        await diagnostic_replay.run(args)
    assert not args.out.exists()


@pytest.mark.asyncio
async def test_outputs_in_checkout_are_rejected(tmp_path):
    args = inputs(tmp_path)
    (tmp_path / ".git").mkdir()
    with pytest.raises(ValueError, match="outside Git"):
        await diagnostic_replay.run(args)
    assert not args.out.exists()


@pytest.mark.asyncio
async def test_formal_failure_prevents_model_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(
        representation_probe.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="invented proof failure"
        ),
    )
    monkeypatch.setattr(
        representation_probe.subprocess,
        "check_output",
        lambda *a, **k: "invented Lean version",
    )
    args = SimpleNamespace(
        out=tmp_path / "probe",
        lean=Path("unused"),
        models=tmp_path / "nonexistent-model-manifest.json",
    )
    with pytest.raises(RuntimeError, match="Lean verification failed"):
        await representation_probe.run(args)
    assert (args.out / "lean-check.txt").exists()
    assert not (args.out / "scores.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["query", "settings", "profile"])
async def test_frozen_test_binding_rejects_changes(tmp_path, damage):
    args = inputs(tmp_path, split="test")
    dataset = json.loads(args.cases.read_text())
    dataset["validation_profile"] = "assisted-v1"
    args.cases.write_text(json.dumps(dataset))
    freeze = {
        "phase": "before_test_retrieval",
        "cases_sha256": diagnostic_replay.file_hash(args.cases),
        "settings": {
            "bm25_k": 1000,
            "faiss_k": 1000,
            "rerank_top": 10,
            "limit": 10,
            "dependency_boost": True,
            "exclude_zero_bm25": False,
            "seed": 42,
        },
    }
    if damage == "query":
        dataset["cases"][0]["query"] = "changed after freeze"
        args.cases.write_text(json.dumps(dataset))
    elif damage == "settings":
        freeze["settings"]["rerank_top"] = 100
    else:
        dataset["validation_profile"] = "human"
        args.cases.write_text(json.dumps(dataset))
        freeze["cases_sha256"] = diagnostic_replay.file_hash(args.cases)
    args.frozen_evaluation = tmp_path / "freeze.json"
    args.frozen_evaluation.write_text(json.dumps(freeze))
    with pytest.raises(ValueError):
        await diagnostic_replay.run(args)
    assert not args.out.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["digest", "settings", "profile", "both"])
async def test_external_reference_contract_rejected_before_output(tmp_path, fault):
    args = inputs(tmp_path)
    dataset = json.loads(args.cases.read_text())
    dataset["validation_profile"] = "mathlibqr-remapped-v1"
    args.cases.write_text(json.dumps(dataset))
    contract = {
        "phase": "before_reference_retrieval",
        "cases_sha256": diagnostic_replay.file_hash(args.cases),
        "settings": {
            "bm25_k": 1000,
            "faiss_k": 1000,
            "rerank_top": 100,
            "limit": 100,
            "dependency_boost": True,
            "exclude_zero_bm25": False,
            "seed": 42,
        },
    }
    if fault == "digest":
        contract["cases_sha256"] = "wrong"
    elif fault == "settings":
        contract["settings"]["rerank_top"] = 10
    elif fault == "profile":
        dataset["validation_profile"] = "assisted-v1"
        args.cases.write_text(json.dumps(dataset))
        contract["cases_sha256"] = diagnostic_replay.file_hash(args.cases)
    else:
        args.frozen_evaluation = tmp_path / "test-freeze.json"
    args.external_reference = tmp_path / "reference-contract.json"
    args.external_reference.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="reference|Reference"):
        await diagnostic_replay.run(args)
    assert not args.out.exists()


@pytest.mark.parametrize(
    "fault", [None, "cases", "settings", "engine", "order", "duplicate", "unfinished"]
)
def test_resume_requires_identical_inputs_and_completed_prefix(fault):
    import copy

    current = {
        "evaluation_profile": "mathlibqr-remapped-v1",
        "reference_contract_sha256": "contract",
        "corpus_revision": "corpus",
        "cases_sha256": "cases",
        "models": {"model": "revision"},
        "source_files_sha256": {"engine.py": "code"},
        "data_files_sha256": {"index": "index"},
        "settings": {"limit": 100},
        "scheduled_ids": ["a", "b", "c"],
    }
    previous = copy.deepcopy(current)
    previous["records"] = [{"query_id": "a", "status": "ok"}]
    if fault == "cases":
        previous["cases_sha256"] = "changed"
    elif fault == "settings":
        previous["settings"]["limit"] = 10
    elif fault == "engine":
        previous["source_files_sha256"]["engine.py"] = "changed"
    elif fault == "order":
        previous["records"][0]["query_id"] = "b"
    elif fault == "duplicate":
        previous["records"] *= 2
    elif fault == "unfinished":
        previous["records"][0]["status"] = "running"
    if fault:
        with pytest.raises(ValueError, match="Resume"):
            diagnostic_replay.resumed_records(previous, current)
    else:
        assert (
            diagnostic_replay.resumed_records(previous, current) == previous["records"]
        )
