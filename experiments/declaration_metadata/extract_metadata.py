"""Export full Lean declaration types from an explicitly pinned project."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path

LEAN_HELPER = r"""
open Lean Elab Command Meta in
def exportMetadata (requested : Array String) : CommandElabM Unit := do
  let env ← getEnv
  let declarations := env.constants.toList
  liftTermElabM do
    for requestedName in requested do
      let found := declarations.find? fun (n, _) => n.toString == requestedName
      let record ← match found with
        | none => pure <| Json.mkObj [
            ("name", toJson requestedName), ("status", toJson "missing")]
        | some (name, info) => do
          let rendered ← ppExpr info.type
          let readable ← withOptions (fun o =>
            ((o.setBool `pp.explicit false).setBool `pp.fullNames false).setBool
              `pp.universes false) (ppExpr info.type)
          let kind := match info with
            | .thmInfo _ => "theorem"
            | .defnInfo _ => "definition"
            | .axiomInfo _ => "axiom"
            | .opaqueInfo _ => "opaque"
            | .inductInfo _ => "inductive"
            | .ctorInfo _ => "constructor"
            | .recInfo _ => "recursor"
            | .quotInfo _ => "quotient"
          pure <| Json.mkObj [
            ("name", toJson name.toString),
            ("status", toJson "found"),
            ("kind", toJson kind),
            ("level_parameters", toJson (info.levelParams.map Name.toString)),
            ("rendered_type", toJson rendered.pretty),
            ("readable_type", toJson readable.pretty),
            ("type_expression", toJson (reprStr info.type)),
            ("has_metavariables", toJson info.type.hasMVar),
            ("has_loose_bound_variables", toJson info.type.hasLooseBVars)]
      (liftM : IO Unit → TermElabM Unit) <| IO.println ("META_JSON:" ++ record.compress)
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_records(records: list[dict], names: list[str]) -> list[dict]:
    """Reject mismatched, duplicate or semantically incomplete type records."""
    if len(set(names)) != len(names):
        raise ValueError("Duplicate requested identities")
    if len(records) != len(names) or {r.get("name") for r in records} != set(names):
        raise ValueError("Export identities differ from the request")
    for record in records:
        if record.get("status") != "found":
            raise ValueError("Missing declaration in imported environment")
        if (
            not isinstance(record.get("rendered_type"), str)
            or not record["rendered_type"]
            or not isinstance(record.get("type_expression"), str)
            or not record["type_expression"]
            or record.get("has_metavariables") is not False
            or record.get("has_loose_bound_variables") is not False
        ):
            raise ValueError("Incomplete elaborated declaration")
    return records


def extract(project: Path, request_path: Path, out: Path) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    revision = subprocess.check_output(
        ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
    ).strip()
    toolchain = (project / "lean-toolchain").read_text().strip()
    if revision != request["revision"] or toolchain != request["toolchain"]:
        raise ValueError("Project revision or toolchain mismatch")
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=project).returncode:
        raise ValueError("Pinned project has tracked modifications")
    runtime = subprocess.check_output(
        ["lake", "env", "lean", "--version"], cwd=project, text=True, encoding="utf-8"
    ).strip()
    expected_version = toolchain.rsplit(":v", 1)[-1]
    if (
        re.search(r"\bversion " + re.escape(expected_version) + r"[,)]", runtime)
        is None
    ):
        raise ValueError("Active Lean executable differs from the pinned toolchain")
    modules, names = request["modules"], request["names"]
    if not modules or any(
        not isinstance(m, str)
        or re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", m) is None
        for m in modules
    ):
        raise ValueError("Invalid import modules")
    if not names or any(not isinstance(n, str) or not n for n in names):
        raise ValueError("Invalid declaration names")
    if any((p / ".git").exists() for p in (out.resolve(), *out.resolve().parents)):
        raise ValueError("Store extracted data outside Git checkouts")
    out.mkdir(parents=True, exist_ok=False)
    source = "\n".join("import " + m for m in modules)
    source += "\nset_option pp.universes true\nset_option pp.explicit true\n"
    source += "set_option pp.fullNames true\n" + LEAN_HELPER
    source += "\nrun_cmd exportMetadata #["
    source += ", ".join(json.dumps(n, ensure_ascii=False) for n in names) + "]\n"
    script = out / "Extract.lean"
    script.write_text(source, encoding="utf-8")
    command = ["lake", "env", "lean", "-j2", "-M4096", str(script.resolve())]
    process = subprocess.run(
        command, cwd=project, capture_output=True, text=True, encoding="utf-8"
    )
    (out / "lean-output.txt").write_text(
        process.stdout + process.stderr, encoding="utf-8"
    )
    if process.returncode:
        raise RuntimeError("Lean extraction failed; inspect lean-output.txt")
    records = [
        json.loads(line.removeprefix("META_JSON:"))
        for line in process.stdout.splitlines()
        if line.startswith("META_JSON:")
    ]
    records = normalized_records(records, names)
    result = {
        "schema_version": 1,
        "environment": {
            "revision": revision,
            "toolchain": toolchain,
            "lean_version": runtime,
            "platform": platform.platform(),
            "tracked_project_clean": True,
            "dependency_lock_sha256": digest(project / "lake-manifest.json"),
            "modules": modules,
            "extractor_sha256": digest(Path(__file__)),
            "lean_source_sha256": digest(script),
            "lean_exit_code": process.returncode,
        },
        "request_sha256": digest(request_path),
        "declarations": records,
        "trusted_boundary": "Lean import/elaboration, environment and pretty printer.",
        "proof_status": (
            "Executable extraction and validation; no normalization theorem proved."
        ),
    }
    (out / "metadata.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("project", "request", "out"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    result = extract(args.project, args.request, args.out)
    print(json.dumps({"declarations": len(result["declarations"])}))
