import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from ai.ingestion.product_taxonomy import resolve_product, validate_product
from ai.ingestion.source_preview import build_preview


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/manifests/sources.csv"
SNAPSHOT = ROOT / "data/manifests/bms_c1_snapshot.json"
PROPOSAL = ROOT / "data/catalogue/product_taxonomy_proposal.json"


class ProductTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.product = json.loads(PROPOSAL.read_text(encoding="utf-8"))

    def test_classification_and_provenance(self):
        validate_product(self.product, MANIFEST, ROOT)
        self.assertEqual(self.product["status"], "pending_catalogue_approval")
        self.assertEqual(self.product["product_type"], "battery_management_board")
        self.assertEqual(build_preview(SNAPSHOT, ROOT)["review_status"], "pending")

    def test_reject_inconsistent_taxonomy_and_related_alias(self):
        self.product["product_type"] = "battery_pack"
        with self.assertRaises(ValueError):
            validate_product(self.product, MANIFEST, ROOT)
        self.product["product_type"] = "battery_management_board"
        self.product["aliases"].append("battery pack")
        with self.assertRaises(ValueError):
            validate_product(self.product, MANIFEST, ROOT)

    def test_exact_name_and_alias(self):
        for query in ("Libre Solar BMS C1", "bms c1", "BMS C1 board"):
            self.assertEqual(resolve_product(query, [self.product])["model"], "BMS C1")
        for query in ("battery pack", "solar inverter", "battery management board", "C1", "Libre Solar BMS C2"):
            with self.assertRaises(ValueError):
                resolve_product(query, [self.product])

    def test_ambiguous_names_rejected(self):
        other = copy.deepcopy(self.product)
        other["model"] = "BMS C2"
        other["aliases"] = ["BMS C1 board"]
        with self.assertRaises(ValueError):
            resolve_product("BMS C1 board", [self.product, other])
        self.assertEqual(resolve_product("Libre Solar BMS C1", [self.product, other])["model"], "BMS C1")

    def test_bad_provenance_rejected(self):
        for field, value in (("source_id", "missing"), ("revision", "other"),
                             ("start_line", 0), ("end_line", 99999), ("page", 3)):
            product = copy.deepcopy(self.product)
            product["evidence"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_product(product, MANIFEST, ROOT)

    def test_changed_source_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with MANIFEST.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                fields = reader.fieldnames
                sources = [row for row in reader if row["source_id"] in self.product["source_ids"]]
            for source in sources:
                target = root / source["local_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                content = (ROOT / source["local_path"]).read_bytes()
                target.write_bytes(content + b"\nChanged test content.\n")
            manifest = root / "sources.csv"
            with manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(sources)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate_product(self.product, manifest, root)


if __name__ == "__main__":
    unittest.main()
