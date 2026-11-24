"""Content-addressed manual snapshots with effective-input invalidation.

This module does not watch repositories or run models. A caller supplies each
layer's builder. It publishes the current pointer only after a full snapshot.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

LAYERS = ("extraction", "normalization", "informalization", "embedding")
REQUIRED = {
    "extraction": {"toolchain", "dependency_lock", "extractor", "settings"},
    "normalization": {"schema", "transformer"},
    "informalization": {
        "model_revision",
        "prompt_revision",
        "generation_settings",
        "context_policy",
    },
    "embedding": {
        "model_revision",
        "tokenizer_revision",
        "rendering",
        "normalization",
        "truncation",
        "numerics",
    },
    "index": {"algorithm", "parameters"},
}


def encoded(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def module_order(modules: Mapping[str, dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    active: set[str] = set()
    done: set[str] = set()

    def visit(name: str) -> None:
        if name not in modules:
            raise ValueError(f"Missing imported module: {name}")
        if name in active:
            raise ValueError("Cyclic module imports")
        if name in done:
            return
        active.add(name)
        module = modules[name]
        if set(module) != {"source_sha256", "imports"} or not re.fullmatch(
            r"[0-9a-f]{64}", module["source_sha256"]
        ):
            raise ValueError("Require source digest and explicit imports")
        if len(module["imports"]) != len(set(module["imports"])):
            raise ValueError("Duplicate imports")
        for dependency in sorted(module["imports"]):
            visit(dependency)
        active.remove(name)
        done.add(name)
        ordered.append(name)

    for name in sorted(modules):
        visit(name)
    return ordered


class SnapshotCache:
    """Single-writer cache; callers must serialize concurrent publication."""

    def __init__(self, root: Path):
        self.root = root

    def _artifact(
        self,
        layer: str,
        inputs: dict[str, Any],
        builder: Callable[[str, dict[str, Any]], bytes],
    ) -> tuple[dict[str, str], bool]:
        key = digest(encoded({"cache_schema": 1, "layer": layer, "inputs": inputs}))
        entry = self.root / "keys" / f"{key}.json"
        if entry.exists():
            reference = json.loads(entry.read_text(encoding="utf-8"))
            if not re.fullmatch(r"[0-9a-f]{64}", reference.get("sha256", "")):
                raise ValueError("Invalid artifact digest")
            obj = self.root / "objects" / reference["sha256"]
            if (
                reference.get("key") != key
                or digest(obj.read_bytes()) != reference["sha256"]
            ):
                raise ValueError("Corrupt cache artifact")
            return reference, True
        content = builder(layer, inputs)
        if not isinstance(content, bytes):
            raise TypeError("Builders must return bytes")
        sha = digest(content)
        obj = self.root / "objects" / sha
        if obj.exists() and digest(obj.read_bytes()) != sha:
            raise ValueError("Corrupt content-addressed object")
        if not obj.exists():
            atomic_write(obj, content)
        reference = {"key": key, "sha256": sha}
        atomic_write(entry, encoded(reference))
        return reference, False

    def build(
        self,
        snapshot_id: str,
        modules: Mapping[str, dict[str, Any]],
        config: dict[str, dict[str, Any]],
        builder: Callable[[str, dict[str, Any]], bytes],
        *,
        renames: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", snapshot_id) or snapshot_id in {
            ".",
            "..",
        }:
            raise ValueError("Unsafe snapshot identifier")
        if set(config) != set(REQUIRED) or any(
            set(config[k]) != fields for k, fields in REQUIRED.items()
        ):
            raise ValueError("Incomplete effective configuration")
        order = module_order(modules)
        rename_history = dict(renames or {})
        if any(
            old in modules or new not in modules for old, new in rename_history.items()
        ):
            raise ValueError("Rename history must resolve to current membership")
        identity = {
            "snapshot": snapshot_id,
            "modules": modules,
            "config": config,
            "renames": rename_history,
        }
        target = self.root / "snapshots" / f"{snapshot_id}.json"
        if target.exists() and json.loads(target.read_text(encoding="utf-8"))[
            "input_sha256"
        ] != digest(encoded(identity)):
            raise ValueError("Snapshot identifiers are immutable")
        artifacts: dict[str, dict[str, dict[str, str]]] = {}
        hits = {layer: 0 for layer in (*LAYERS, "index")}
        misses = dict(hits)
        for name in order:
            artifacts[name] = {}
            previous: dict[str, str] | None = None
            for layer in LAYERS:
                inputs = {"module": name, "config": config[layer], "previous": previous}
                if layer == "extraction":
                    inputs.update(
                        source_sha256=modules[name]["source_sha256"],
                        imports={
                            dep: artifacts[dep][layer]
                            for dep in sorted(modules[name]["imports"])
                        },
                    )
                if layer == "informalization":
                    inputs["context"] = {
                        dep: artifacts[dep][layer]
                        for dep in sorted(modules[name]["imports"])
                    }
                reference, hit = self._artifact(layer, inputs, builder)
                artifacts[name][layer] = reference
                (hits if hit else misses)[layer] += 1
                previous = reference
        index, hit = self._artifact(
            "index",
            {
                "config": config["index"],
                "members": {
                    name: artifacts[name]["embedding"] for name in sorted(artifacts)
                },
            },
            builder,
        )
        (hits if hit else misses)["index"] += 1
        manifest = {
            "schema_version": 1,
            **identity,
            "input_sha256": digest(encoded(identity)),
            "artifacts": artifacts,
            "index": index,
        }
        content = encoded(manifest)
        if target.exists() and target.read_bytes() != content:
            raise ValueError("Nondeterministic snapshot reconstruction")
        if not target.exists():
            atomic_write(target, content)
        atomic_write(
            self.root / "current.json",
            encoded({"snapshot": snapshot_id, "manifest_sha256": digest(content)}),
        )
        return {"manifest": manifest, "hits": hits, "misses": misses}
