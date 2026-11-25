"""Reject data files from the Git index.

The benchmark data is published as a dataset, not in this repository, and
the search log it was styled on is private. Only source, documentation and
the paper belong here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {".gitattributes", ".gitignore", "LICENSE", "README.md", "pyproject.toml"}
DATA_DIRECTORIES = {
    "annotations",
    "data",
    "models",
    "private",
    "reports",
    "results",
    "runs",
}
SUFFIXES = {
    "docs": {".md"},
    "experiments": {".md", ".py"},
    "paper": {".bib", ".gitignore", ".md", ".pdf", ".py", ".sty", ".tex"},
    "scripts": {".py"},
    "src": {".py"},
    "tests": {".py"},
}


def allowed_path(name: str) -> bool:
    """Allow source, documentation and paper files; data directories fail."""
    path = Path(name)
    if set(path.parts) & DATA_DIRECTORIES:
        return False
    if name in ROOT_FILES:
        return True
    if name.startswith(".github/workflows/"):
        return path.suffix == ".yml"
    return (path.suffix or path.name) in SUFFIXES.get(path.parts[0], set())


def main() -> None:
    """Check every path in the index."""
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
    names = subprocess.check_output([*command, "ls-files", "-z"]).decode().split("\0")
    failures = [name for name in filter(None, names) if not allowed_path(name)]
    if failures:
        raise SystemExit("\n".join(f"Unexpected path: {name}" for name in failures))
    print("No data file is committed.")


if __name__ == "__main__":
    main()
