"""Verify source integrity and preserve line references in review excerpts."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ai.ingestion.source_preview import build_preview, split_sections

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SourcePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.asset_root = Path(self.temp_directory.name)
        self.source_path = self.asset_root / "manual.md"
        self.source_bytes = b"# Synthetic manual\n\nTest fixture.\n\n## Details\n\nNo equipment facts.\n"
        self.source_path.write_bytes(self.source_bytes)
        self.snapshot_path = self.asset_root / "snapshot.json"
        self.snapshot = {
            "source_id": "MOCK-SOURCE", "title": "Synthetic test manual",
            "source_version": "mock-v1", "license": "CC0-1.0",
            "license_url": "https://example.invalid/license", "review_status": "pending",
            "files": [{
                "path": "manual.md", "url": "https://example.invalid/manual",
                "size_bytes": len(self.source_bytes),
                "sha256": hashlib.sha256(self.source_bytes).hexdigest(),
                "git_blob_sha1": hashlib.sha1(b"blob " + str(len(self.source_bytes)).encode() + b"\0" + self.source_bytes).hexdigest(),
            }],
        }
        self._write_snapshot()

    def _write_snapshot(self):
        self.snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")

    def test_sections_preserve_text_and_line_ranges(self):
        text = "Preface\r\n# Heading\r\nBody\r\n## Child\r\nDetails\r\n"
        sections = split_sections(text)
        self.assertEqual("".join(section["text"] for section in sections), text)
        self.assertEqual([(section["start_line"], section["end_line"]) for section in sections], [(1, 1), (2, 3), (4, 5)])
        self.assertEqual(sections[-1]["heading_path"], ["Heading", "Child"])

    def test_headings_inside_fenced_code_are_preserved_as_code(self):
        text = "# Heading\n```python\n# Code comment\n```\n## Next\n"
        sections = split_sections(text)
        self.assertEqual(len(sections), 2)
        self.assertIn("# Code comment", sections[0]["text"])

    def test_pending_source_stays_pending_without_pdf_pages(self):
        preview = build_preview(self.snapshot_path, self.asset_root)
        self.assertEqual(preview["review_status"], "pending")
        self.assertEqual(preview["purpose"], "source_review")
        self.assertTrue(all(section["page"] is None for section in preview["sections"]))

    def test_changed_source_bytes_are_rejected(self):
        self.source_path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            build_preview(self.snapshot_path, self.asset_root)

    def test_outside_paths_and_duplicate_paths_are_rejected(self):
        self.snapshot["files"][0]["path"] = "../private.md"
        self._write_snapshot()
        with self.assertRaisesRegex(ValueError, "relative to asset_root"):
            build_preview(self.snapshot_path, self.asset_root)
        self.snapshot["files"][0]["path"] = "manual.md"
        self.snapshot["files"].append(self.snapshot["files"][0].copy())
        self._write_snapshot()
        with self.assertRaisesRegex(ValueError, "Duplicate source path"):
            build_preview(self.snapshot_path, self.asset_root)

    def test_cli_cannot_overwrite_source_or_snapshot(self):
        for output in (self.source_path, self.snapshot_path):
            with self.subTest(output=output.name):
                original = output.read_bytes()
                result = subprocess.run([
                    sys.executable, "-m", "ai.ingestion.source_preview",
                    "--snapshot", str(self.snapshot_path), "--asset-root", str(self.asset_root),
                    "--output", str(output),
                ], capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(output.read_bytes(), original)

    def test_cli_writes_review_output(self):
        output = self.asset_root / "preview.json"
        result = subprocess.run([
            sys.executable, "-m", "ai.ingestion.source_preview",
            "--snapshot", str(self.snapshot_path), "--asset-root", str(self.asset_root),
            "--output", str(output),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(output.read_text())["sections"]), 2)

    def test_real_snapshot_preserves_source_license_and_all_text(self):
        preview = build_preview(PROJECT_ROOT / "data/manifests/bms_c1_snapshot.json", PROJECT_ROOT)
        self.assertEqual(preview["attribution"]["license"], "CC-BY-SA-4.0")
        self.assertEqual(len(preview["files"]), 7)
        for source in preview["files"]:
            path = PROJECT_ROOT / source["path"]
            if path.suffix == ".md":
                reconstructed = "".join(section["text"] for section in preview["sections"] if section["source_path"] == source["path"])
                self.assertEqual(reconstructed.encode("utf-8"), path.read_bytes())


if __name__ == "__main__":
    unittest.main()
