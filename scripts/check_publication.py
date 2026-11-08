"""Reject benchmark artifacts from the index while retaining source metadata."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTIFACTS = dict(
    [
        (
            "tools/offline/migration.json",
            "701dc7ad7ddfa81f2efc9976f1497c1f62e5f436e27f441ad02518fce493a5bd",
        ),
        (
            "experiments/candidate_selection/patches/bases.json",
            "70e0953f6fbc3746cf1f6ffe87ce4f4bde678889a74d71cb66ec291f3fa47cd2",
        ),
        (
            "experiments/candidate_selection/patches/lean-explore.patch",
            "655c24d5f2d61a63d8440bd1ac9392e8997659a31da51aa34081bce862acf5dc",
        ),
        (
            "experiments/candidate_selection/LICENSE.LeanExplore",
            "97840bc35908bc43a3524b6698a9b877270ad44db8f50b36b360104d86cc5e96",
        ),
    ]
)
ROOT_FILES = {".gitignore", ".gitattributes", "README.md", "pyproject.toml"}
TEMPLATE = "tools/offline/src/leanexplore_benchmark/overview.html"
DATA_DIRECTORIES = {
    "data",
    "reports",
    "results",
    "private",
    "models",
    "annotations",
    "runs",
}


def allowed_path(name: str) -> bool:
    """Allow source and method files; benchmark directories always fail."""
    path = Path(name)
    if set(path.parts) & DATA_DIRECTORIES:
        return False
    return (
        name in SOURCE_ARTIFACTS
        or name == 'experiments/declaration_metadata/VerifiedNormalization.lean'
        or name in ROOT_FILES
        or name == TEMPLATE
        or path.name in {".gitignore", ".gitattributes", "pyproject.toml"}
        or (
            path.parts[0] in {"src", "tests", "scripts", "tools", "experiments"}
            and path.suffix in {".py", ".js", ".md"}
        )
        or (path.parts[0] == "docs" and path.suffix == ".md")
        or (name.startswith(".github/workflows/") and path.suffix == ".yml")
    )


def main() -> None:
    """Check index paths and exact hashes of the source-only exceptions."""
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
    names = subprocess.check_output([*command, "ls-files", "-z"]).decode().split("\0")
    failures = [
        f"Missing source artifact: {name}"
        for name in SOURCE_ARTIFACTS
        if name not in names
    ]
    for name in filter(None, names):
        if not allowed_path(name):
            failures.append(f"Unexpected publication path: {name}")
        elif name in SOURCE_ARTIFACTS:
            content = subprocess.check_output([*command, "show", ":" + name])
            if hashlib.sha256(content).hexdigest() != SOURCE_ARTIFACTS[name]:
                failures.append(f"Source artifact content changed: {name}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Source-only publication paths and artifact hashes passed.")


if __name__ == "__main__":
    main()
