"""Check tracked publication paths and hashes of reviewed public artifacts."""

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_ARTIFACTS = dict(
    [
        (
            "tools/offline/migration.json",
            "701dc7ad7ddfa81f2efc9976f1497c1f62e5f436e27f441ad02518fce493a5bd",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/download-manifest.json",
            "336270665843fa27d6e2dfd923e6ba03cfd4ac864a1ed3a925c0c73e785b95a9",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/lexical-audit.json",
            "fa21afb0ad3f04605a67faa2954385601ac44f3c6cd667d690fbb6d55e46e102",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/LICENSE.MathlibQR",
            "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/model-manifest.json",
            "0645991b0d8d7a3c28c764735302d8134e38e7a3a36f5d2d8402da76bbbc44a0",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/pilot-10.json",
            "ad8b53a63265c2f1c51ecedef66441a201e40923874477ed21d96ebb0db2768d",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/pilot-5.json",
            "842ef03a98db3ddd74583599114ffe773693cbd5a3227e9738ea8f2d73a45acc",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/pilot-provenance.json",
            "430be46d1c73fa4b401ebff2e73246c0d24f42ddf794d84dd3922794bc900047",
        ),
        (
            "experiments/candidate_selection/results/2026-11-02/pilot-queries.json",
            "7ad76b64b22bdbad8c5db92c3fa020733e6597034ffaba09107c589fdcebfde9",
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


def main() -> None:
    """Reject unexpected data and verify the exact reviewed artifact bytes."""
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT)]
    names = subprocess.check_output([*command, "ls-files", "-z"]).decode().split("\0")
    failures = [
        f"Missing reviewed artifact: {name}"
        for name in REVIEWED_ARTIFACTS
        if name not in names
    ]
    for name in filter(None, names):
        path = Path(name)
        if name in REVIEWED_ARTIFACTS:
            content = subprocess.check_output([*command, "show", ":" + name])
            if hashlib.sha256(content).hexdigest() != REVIEWED_ARTIFACTS[name]:
                failures.append(f"Unreviewed artifact content: {name}")
            continue
        allowed = (
            name in ROOT_FILES
            or name == TEMPLATE
            or (path.name in {".gitignore", ".gitattributes", "pyproject.toml"})
            or (
                path.parts[0] in {"src", "tests", "scripts", "tools", "experiments"}
                and path.suffix in {".py", ".js", ".md"}
            )
            or (path.parts[0] == "docs" and path.suffix == ".md")
            or (name.startswith(".github/workflows/") and path.suffix == ".yml")
        )
        if not allowed:
            failures.append(f"Unexpected publication path: {name}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Publication paths and reviewed public artifact hashes passed.")


if __name__ == "__main__":
    main()
