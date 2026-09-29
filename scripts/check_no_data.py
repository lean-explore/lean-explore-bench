"""Fail if any tracked file could hold real query data.

Run in CI and before committing: ``python scripts/check_no_data.py``.
Checks every file git tracks (or would commit, with ``--staged``) for data
file extensions, notebooks (which can hold outputs) and large files.
"""

import argparse
import subprocess
import sys
from pathlib import Path

FORBIDDEN_SUFFIXES = frozenset(
    {
        ".arrow",
        ".db",
        ".feather",
        ".ipynb",
        ".jsonl",
        ".npy",
        ".npz",
        ".parquet",
        ".pickle",
        ".pkl",
        ".sqlite",
        ".sqlite3",
    }
)
MAX_BYTES = 1_000_000


def tracked_files(staged: bool) -> list[Path]:
    """List files git tracks, or files staged for commit.

    Args:
        staged: List staged files instead of tracked ones.

    Returns:
        Paths relative to the repository root.
    """
    command = (
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
        if staged
        else ["git", "ls-files"]
    )
    output = subprocess.run(command, check=True, capture_output=True, text=True)
    return [Path(line) for line in output.stdout.splitlines() if line]


def problems(paths: list[Path]) -> list[str]:
    """Describe every path that must not be committed.

    Args:
        paths: Paths to check.

    Returns:
        One message per offending path.
    """
    found = []
    for path in paths:
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            found.append(f"{path}: data or notebook file type")
        elif ".env" in path.name and path.name != ".env.example":
            found.append(f"{path}: environment file")
        elif path.is_file() and path.stat().st_size > MAX_BYTES:
            found.append(f"{path}: larger than {MAX_BYTES:,} bytes")
    return found


def main() -> int:
    """Run the check.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    found = problems(tracked_files(parser.parse_args().staged))
    for message in found:
        print(message, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
