"""Fetch public benchmark files at a fixed upstream commit; no private inputs."""

import hashlib
import json
import urllib.request
from datetime import date
from pathlib import Path

REPOSITORY = "frenzymath/LeanSearch-v2"
REVISION = "94f4888cbaf9f4322535755f86cbac690ec18080"
FILES = (
    "LICENSE",
    "README.md",
    "benchmark/MathlibQR.json",
    "benchmark/MathlibQR_shared171.json",
    "benchmark/MathlibMPR.json",
    "benchmark/MathlibMPR_Prop_ids.txt",
    "benchmark/FATE-H.jsonl",
    "benchmark/FATE-H.LICENSE",
)


def main() -> None:
    """Download verbatim source files and record SHA256 provenance."""
    destination = (
        Path(__file__).resolve().parents[1] / "data" / "public" / "leansearch-v2"
    )
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for name in FILES:
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{name}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files.append(
            {
                "path": name,
                "url": url,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "repository": REPOSITORY,
        "commit": REVISION,
        "retrieved_on": date.today().isoformat(),
        "repository_license": "Apache-2.0",
        "FATE-H_license": "CC-BY-4.0",
        "files": files,
        "note": (
            "Upstream benchmark assets, not LeanExplore user queries. "
            "No runs performed."
        ),
    }
    (destination / "provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Downloaded {len(files)} public files to {destination}")


if __name__ == "__main__":
    main()
