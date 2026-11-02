"""Apply the experiment to a clean checkout at the recorded LeanExplore commit."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def prepare(checkout: Path) -> None:
    """Check the base and working tree before applying the engine patch."""
    checkout = checkout.resolve(strict=True)
    source = Path(__file__).resolve().parent
    base = json.loads((source / "patches/bases.json").read_text())["lean-explore"][
        "commit"
    ]
    command = [
        "git",
        "-c",
        f"safe.directory={checkout.as_posix()}",
        "-C",
        str(checkout),
    ]
    head = subprocess.check_output([*command, "rev-parse", "HEAD"], text=True).strip()
    if head != base:
        raise ValueError(f"Expected LeanExplore {base}, got {head}.")
    if subprocess.check_output([*command, "status", "--porcelain"], text=True).strip():
        raise ValueError("The LeanExplore checkout must be clean.")
    target = checkout / "scripts/candidate_selection.py"
    if target.exists():
        raise FileExistsError(target)
    patch = source / "patches/lean-explore.patch"
    subprocess.run([*command, "apply", "--check", str(patch)], check=True)
    subprocess.run([*command, "apply", str(patch)], check=True)
    shutil.copyfile(source / "runner.py", target)
    print(
        f"Prepared {checkout}. Install its local dependencies before running the pilot."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    prepare(parser.parse_args().checkout)
