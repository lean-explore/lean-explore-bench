"""Rebuild the local report with Python 3.10+, without installation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from leanexplore_benchmark.cli import main  # noqa: E402

if __name__ == "__main__":
    main(["build", *sys.argv[1:]])
