"""Source validation tests using temporary synthetic files."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ai.ingestion.manifest import REQUIRED_COLUMNS, validate_manifest


class SourceManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.asset_root = Path(self.temp_directory.name)
        self.manifest_path = self.asset_root / "sources.csv"
        self.source_bytes = b"SYNTHETIC TEST FIXTURE. Not manufacturer evidence."
        (self.asset_root / "manual.txt").write_bytes(self.source_bytes)

    def _source_row(self, **overrides):
        row = {
            "source_id": "MOCK-SRC-1",
            "category_id": "MOCK-CAT-1",
            "product_id": "MOCK-PROD-1",
            "material_type": "manual",
            "publisher": "Synthetic fixture publisher",
            "title": "Synthetic test manual",
            "url": "https://example.invalid/manual",
            "accessed_on": "2026-11-12",
            "license": "CC0-1.0",
            "redistribution_allowed": "true",
            "license_evidence_url": "https://example.invalid/license",
            "sha256": hashlib.sha256(self.source_bytes).hexdigest(),
            "revision": "mock-v1",
            "page_count": "1",
            "extraction_method": "plain_text",
            "cleaning_steps": "unchanged",
            "validation_status": "verified",
            "reviewer": "test-fixture-reviewer",
            "local_path": "manual.txt",
        }
        return row | overrides

    def _validate_rows(self, rows, fields=(*REQUIRED_COLUMNS, "local_path")):
        with self.manifest_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return validate_manifest(self.manifest_path, self.asset_root, today=date(2026, 11, 12))

    def test_empty_manifest_is_not_coverage_ready(self):
        report = self._validate_rows([])
        self.assertTrue(report["manifest_valid"])
        self.assertFalse(report["coverage_ready"])
        self.assertEqual(report["verified_assets"], 0)

    def test_shared_document_counts_product_once(self):
        report = self._validate_rows([self._source_row(), self._source_row(source_id="MOCK-SRC-2")])
        self.assertTrue(report["manifest_valid"], report["errors"])
        self.assertEqual(report["coverage"]["documented_products"], 1)
        self.assertTrue(any("duplicate asset" in item for item in report["warnings"]))

    def test_pending_and_rejected_never_count(self):
        for state in ("pending", "rejected"):
            with self.subTest(state=state):
                report = self._validate_rows([self._source_row(validation_status=state)])
                self.assertTrue(report["manifest_valid"])
                self.assertEqual(report["verified_assets"], 0)

    def test_tampered_snapshot_is_rejected(self):
        (self.asset_root / "manual.txt").write_text("modified")
        report = self._validate_rows([self._source_row()])
        self.assertFalse(report["manifest_valid"])
        self.assertIn("sha256 mismatch", " ".join(report["errors"]))

    def test_absolute_or_traversing_paths_are_rejected(self):
        for path in ("../private.txt", str(self.asset_root / "manual.txt")):
            with self.subTest(path=path):
                report = self._validate_rows([self._source_row(local_path=path)])
                self.assertFalse(report["manifest_valid"])
                self.assertIn("relative to asset_root", " ".join(report["errors"]))

    def test_unresolved_provenance_is_rejected(self):
        for field, value in (("reviewer", "TBD"), ("license", "unknown"),
                             ("url", "file:///private"), ("sha256", "bad"),
                             ("page_count", "0"), ("accessed_on", "2026-11-13"),
                             ("accessed_on", "20261112"),
                             ("local_path", ""), ("redistribution_allowed", "maybe")):
            with self.subTest(field=field):
                self.assertFalse(self._validate_rows([self._source_row(**{field: value})])["manifest_valid"])

    def test_missing_and_invalid_snapshot_paths_fail_closed(self):
        for path in ("missing.txt", "bad\x00path"):
            with self.subTest(path=path):
                self.assertFalse(self._validate_rows([self._source_row(local_path=path)])["manifest_valid"])

    def test_missing_manifest_fails_closed(self):
        report = validate_manifest(self.asset_root / "missing.csv", self.asset_root)
        self.assertFalse(report["manifest_valid"])
        self.assertFalse(report["coverage_ready"])

    def test_duplicate_headers_and_unclosed_quotes_fail_closed(self):
        for content in ("source_id,source_id\nA,B\n", 'source_id\n"unclosed\n'):
            with self.subTest(content=content):
                self.manifest_path.write_text(content, encoding="utf-8")
                self.assertFalse(validate_manifest(self.manifest_path, self.asset_root)["manifest_valid"])

    def test_duplicate_ids_and_category_conflicts_are_rejected(self):
        self.assertFalse(self._validate_rows([self._source_row(), self._source_row()])["manifest_valid"])
        self.assertFalse(self._validate_rows([self._source_row(), self._source_row(source_id="MOCK-SRC-2", category_id="OTHER")])["manifest_valid"])

    def test_missing_columns_and_malformed_rows_fail_closed(self):
        self.manifest_path.write_text("source_id\nMOCK-SRC-1,EXTRA\n", encoding="utf-8")
        report = validate_manifest(self.manifest_path, self.asset_root)
        self.assertFalse(report["manifest_valid"])
        self.assertEqual(report["verified_assets"], 0)

    def test_non_document_assets_do_not_inflate_product_coverage(self):
        report = self._validate_rows([self._source_row(material_type="image")])
        self.assertTrue(report["manifest_valid"])
        self.assertEqual(report["coverage"]["documented_products"], 0)

    def test_minimums_use_distinct_products_and_categories(self):
        rows = [self._source_row(source_id=f"MOCK-SRC-{i}", product_id=f"MOCK-PROD-{i}",
                         category_id=f"MOCK-CAT-{i % 3}") for i in range(15)]
        self.assertTrue(self._validate_rows(rows)["coverage_ready"])
        self.assertFalse(self._validate_rows(rows[:14])["coverage_ready"])

    def test_cli_requires_coverage_and_writes_report(self):
        self._validate_rows([])
        output = self.asset_root / "report.json"
        process = subprocess.run([
            sys.executable, "-m", "ai.ingestion.manifest", "--manifest", str(self.manifest_path),
            "--asset-root", str(self.asset_root), "--require-coverage", "--report", str(output),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertFalse(json.loads(output.read_text())["coverage_ready"])

    def test_no_cleaning_required_is_valid(self):
        report = self._validate_rows([self._source_row(cleaning_steps="none")])
        self.assertTrue(report["manifest_valid"], report["errors"])

    def test_invalid_row_does_not_assign_product_category(self):
        report = self._validate_rows([
            self._source_row(sha256="bad", category_id="INVALID"),
            self._source_row(source_id="MOCK-SRC-2"),
        ])
        self.assertFalse(report["manifest_valid"])
        self.assertFalse(any("multiple categories" in error for error in report["errors"]))
        self.assertEqual(report["verified_assets"], 1)

    def test_invalid_http_urls_are_rejected(self):
        for url in ("https://bad host/manual", "https://example.invalid:bad/manual", "https://example.invalid/\nmanual"):
            with self.subTest(url=url):
                self.assertFalse(self._validate_rows([self._source_row(url=url)])["manifest_valid"])

    def test_cli_does_not_overwrite_manifest(self):
        self._validate_rows([])
        original = self.manifest_path.read_bytes()
        process = subprocess.run([
            sys.executable, "-m", "ai.ingestion.manifest", "--manifest", str(self.manifest_path),
            "--asset-root", str(self.asset_root), "--report", str(self.manifest_path),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertEqual(self.manifest_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
