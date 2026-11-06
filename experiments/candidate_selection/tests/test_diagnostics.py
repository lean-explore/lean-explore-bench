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
