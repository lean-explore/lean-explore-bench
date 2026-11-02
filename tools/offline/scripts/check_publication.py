"""Reject data artifacts in the Git index. Review file contents separately."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "README.md",
    "benchmark.py",
    "pyproject.toml",
    "migration.json",
}
CODE_DIRS = {"src", "tests", "scripts"}
TEMPLATE = "src/leanexplore_benchmark/overview.html"


def main() -> None:
    """Allow source, method documentation and the empty HTML template only."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths = [p for p in result.stdout.decode("utf-8").split("\0") if p]
    rejected = []
    for name in paths:
        path = Path(name)
        allowed = (
            name in ROOT_FILES
            or name == TEMPLATE
            or (path.parts[0] in CODE_DIRS and path.suffix in {".py", ".js"})
            or (path.parts[0] == "docs" and path.suffix == ".md")
        )
        if not allowed:
            rejected.append(name)
    if rejected:
        raise SystemExit("Data or unexpected files staged:\n" + "\n".join(rejected))
    print(f"Publication paths passed: {len(paths)} code/documentation files.")


if __name__ == "__main__":
    main()
