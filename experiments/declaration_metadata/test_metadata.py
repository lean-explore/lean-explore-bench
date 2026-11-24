"""Reject source snippets and wrong identities as semantic metadata."""

import copy
import unittest

from extract_metadata import normalized_records


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.record = dict(
            name="Invented.result",
            status="found",
            rendered_type="True",
            type_expression="Expr.const True []",
            has_metavariables=False,
            has_loose_bound_variables=False,
        )

    def test_complete_record_is_preserved(self):
        records = [self.record]
        self.assertEqual(normalized_records(records, ["Invented.result"]), records)

    def test_missing_or_duplicate_identity_fails(self):
        for names, records in [
            (["Invented.other"], [self.record]),
            (["Invented.result", "Invented.result"], [self.record, self.record]),
        ]:
            with self.assertRaises(ValueError):
                normalized_records(records, names)

    def test_source_span_and_open_terms_fail(self):
        for field, value in [
            ("type_expression", ""),
            ("has_metavariables", True),
            ("has_loose_bound_variables", True),
            ("status", "missing"),
        ]:
            record = copy.deepcopy(self.record)
            record[field] = value
            with self.assertRaises(ValueError):
                normalized_records([record], ["Invented.result"])

    def test_wrong_active_toolchain_is_rejected_before_output(self):
        import json
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch

        from extract_metadata import extract

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "lean-toolchain").write_text("leanprover/lean4:v4.32.0")
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    dict(revision="pinned", toolchain="leanprover/lean4:v4.32.0")
                )
            )
            with (
                patch(
                    "extract_metadata.subprocess.check_output",
                    side_effect=["pinned", "Lean (version 4.35.0, Release)"],
                ),
                patch(
                    "extract_metadata.subprocess.run",
                    return_value=SimpleNamespace(returncode=0),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "Active Lean executable"):
                    extract(project, request, root / "output")
            self.assertFalse((root / "output").exists())

    def test_modified_pinned_project_is_rejected(self):
        import json
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch

        from extract_metadata import extract

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "lean-toolchain").write_text("leanprover/lean4:v4.32.0")
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    dict(revision="pinned", toolchain="leanprover/lean4:v4.32.0")
                )
            )
            with (
                patch(
                    "extract_metadata.subprocess.check_output", return_value="pinned"
                ),
                patch(
                    "extract_metadata.subprocess.run",
                    return_value=SimpleNamespace(returncode=1),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "tracked modifications"):
                    extract(project, request, root / "output")
            self.assertFalse((root / "output").exists())
