"""Exercise dependency invalidation and transactional publication."""

import copy
import json

import pytest

from incremental_cache import REQUIRED, SnapshotCache, digest, encoded


def fixture():
    modules = {
        "A": {"source_sha256": digest(b"A"), "imports": []},
        "B": {"source_sha256": digest(b"B"), "imports": ["A"]},
    }
    config = {
        layer: dict.fromkeys(sorted(fields), "fixture-v1")
        for layer, fields in REQUIRED.items()
    }
    return modules, config


def builder(layer, inputs):
    return encoded({"layer": layer, "effective_inputs": inputs})


def test_no_change_and_dependency_only(tmp_path):
    modules, config = fixture()
    cache = SnapshotCache(tmp_path)
    first = cache.build("one", modules, config, builder)
    repeat = cache.build("one", modules, config, builder)
    assert sum(repeat["misses"].values()) == 0
    assert sum(repeat["hits"].values()) == 9
    modules["A"]["source_sha256"] = digest(b"A changed")
    second = cache.build("two", modules, config, builder)
    assert sum(second["misses"].values()) == 9
    assert first["manifest"]["modules"]["B"] == second["manifest"]["modules"]["B"]
    assert (tmp_path / "snapshots/one.json").exists()


@pytest.mark.parametrize(
    "layer,field",
    [(layer, field) for layer, fields in REQUIRED.items() for field in sorted(fields)],
)
def test_configuration_invalidates_its_layer(tmp_path, layer, field):
    modules, config = fixture()
    cache = SnapshotCache(tmp_path)
    cache.build("one", modules, config, builder)
    config[layer][field] = "fixture-v2"
    changed = cache.build("two", modules, config, builder)
    assert changed["misses"][layer] == (1 if layer == "index" else 2)
    if layer != "extraction":
        assert changed["hits"]["extraction"] == 2


def test_delete_rename_and_old_snapshot(tmp_path):
    modules, config = fixture()
    cache = SnapshotCache(tmp_path)
    cache.build("one", modules, config, builder)
    old = (tmp_path / "snapshots/one.json").read_bytes()
    modules["C"] = modules.pop("B")
    result = cache.build("two", modules, config, builder, renames={"B": "C"})
    assert set(result["manifest"]["artifacts"]) == {"A", "C"}
    assert result["manifest"]["renames"] == {"B": "C"}
    assert (tmp_path / "snapshots/one.json").read_bytes() == old
    del modules["C"]
    result = cache.build("three", modules, config, builder)
    assert set(result["manifest"]["artifacts"]) == {"A"}


def test_failed_build_keeps_published_snapshot(tmp_path):
    modules, config = fixture()
    cache = SnapshotCache(tmp_path)
    cache.build("one", modules, config, builder)
    old = (tmp_path / "current.json").read_bytes()
    modules["A"]["source_sha256"] = digest(b"new")

    def fail(layer, inputs):
        if layer == "embedding":
            raise RuntimeError("interrupted build")
        return builder(layer, inputs)

    with pytest.raises(RuntimeError, match="interrupted"):
        cache.build("two", modules, config, fail)
    assert (tmp_path / "current.json").read_bytes() == old
    assert not (tmp_path / "snapshots/two.json").exists()
    cache.build("two", modules, config, builder)
    assert json.loads((tmp_path / "current.json").read_text())["snapshot"] == "two"


def test_corruption_and_snapshot_reuse_are_rejected(tmp_path):
    modules, config = fixture()
    cache = SnapshotCache(tmp_path)
    first = cache.build("one", modules, config, builder)
    changed = copy.deepcopy(modules)
    changed["A"]["source_sha256"] = digest(b"different")
    with pytest.raises(ValueError, match="immutable"):
        cache.build("one", changed, config, builder)
    sha = first["manifest"]["artifacts"]["A"]["extraction"]["sha256"]
    (tmp_path / "objects" / sha).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="Corrupt"):
        cache.build("one", modules, config, builder)


@pytest.mark.parametrize("fault", ["missing", "cycle", "config", "rename"])
def test_invalid_inputs_do_not_publish(tmp_path, fault):
    modules, config = fixture()
    renames = None
    if fault == "missing":
        del modules["A"]
    elif fault == "cycle":
        modules["A"]["imports"] = ["B"]
    elif fault == "config":
        del config["embedding"]["tokenizer_revision"]
    else:
        renames = {"old": "missing"}
    with pytest.raises(ValueError):
        SnapshotCache(tmp_path).build("one", modules, config, builder, renames=renames)
    assert not (tmp_path / "current.json").exists()
