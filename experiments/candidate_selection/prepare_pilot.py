"""Fetch the pinned public pilot inputs into an external directory."""

import argparse
import hashlib
import json
import shlex
import shutil
import urllib.request
from pathlib import Path


def digest(path: Path) -> str:
    """Hash a potentially large corpus file in bounded memory."""
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def download(entry: dict, directory: Path) -> None:
    """Verify existing assets or download a file and check its recorded hash."""
    path = directory / entry["file"]
    if path.exists():
        if digest(path) != entry["sha256"]:
            raise ValueError(f"Existing file has the wrong checksum: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    request = urllib.request.Request(
        entry["url"], headers={"User-Agent": "lean-explore/1.3.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        with partial.open("xb") as target:
            shutil.copyfileobj(response, target)
    if partial.stat().st_size != entry["bytes"] or digest(partial) != entry["sha256"]:
        raise ValueError(f"Downloaded asset failed verification: {partial}")
    partial.rename(path)
    print(f"Verified {entry['file']}")


def prepare(output: Path) -> None:
    """Fetch public corpus/models and print commands using immutable model paths."""
    source = Path(__file__).resolve().parent / "results/2026-11-02"
    repository = Path(__file__).resolve().parents[2]
    output = output.resolve()
    if output == repository or repository in output.parents:
        raise ValueError("Choose an output directory outside the repository.")
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / "download-manifest.json").read_text())
    directory = output / "data" / manifest["snapshot"]
    for entry in manifest["files"]:
        download(entry, directory)
    from huggingface_hub import snapshot_download

    models = json.loads((source / "model-manifest.json").read_text())
    paths = {}
    for name, model in models.items():
        paths[name] = snapshot_download(
            name,
            revision=model["revision"],
            cache_dir=output / "models",
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"],
        )
    query_file = output / "pilot-queries.json"
    if (
        query_file.exists()
        and query_file.read_bytes() != (source / query_file.name).read_bytes()
    ):
        raise FileExistsError(query_file)
    shutil.copyfile(source / query_file.name, query_file)
    for limit in (5, 10):
        print(
            shlex.join(
                [
                    "python",
                    "-m",
                    "scripts.candidate_selection",
                    "--data-directory",
                    str(directory),
                    "--queries",
                    str(query_file),
                    "--embedding-model",
                    paths["Qwen/Qwen3-Embedding-0.6B"],
                    "--reranker-model",
                    paths["Qwen/Qwen3-Reranker-0.6B"],
                    "--limit",
                    str(limit),
                    "--repetitions",
                    "1",
                    "--seed",
                    "42",
                    "--output",
                    str(output / f"pilot-{limit}.json"),
                ]
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    prepare(parser.parse_args().out)
