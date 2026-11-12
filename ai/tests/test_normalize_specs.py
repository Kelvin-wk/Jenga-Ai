"""Catalogue validation tests use synthetic products and source references."""

import copy
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ai.ingestion.normalize_specs import ProductRecord, SpecValue, load_products_csv, validate_catalogue


class CatalogueValidationTests(unittest.TestCase):
    def _product(self, index=1, category="industrial_pumps"):
        return ProductRecord(
            product_id=f"MOCK-{index}", category_id=category,
            manufacturer="Synthetic test manufacturer", model_ref=f"MOCK-MODEL-{index}",
            display_name="Synthetic test equipment", source_ids=[f"MOCK-SOURCE-{index}"],
            specs=[SpecValue(
                product_id=f"MOCK-{index}", field_key="rated_power_kw", value_text="1 kW",
                value_num=1.0, canonical_unit="kW", source_id=f"MOCK-SOURCE-{index}", page=1,
                validation_status="verified", reviewer="synthetic-test-reviewer",
            )], validation_status="verified",
        )

    def _products(self):
        categories = ("industrial_pumps", "power_generators", "solar_inverters")
        return [self._product(index, categories[index % 3]) for index in range(15)]

    def test_placeholders_do_not_satisfy_coverage(self):
        categories = ("industrial_pumps", "power_generators", "solar_inverters")
        products = [ProductRecord(
            product_id=f"MOCK-{index}", category_id=categories[index % 3],
            manufacturer="", model_ref="", display_name="",
        ) for index in range(15)]
        report = validate_catalogue(products)
        self.assertFalse(report["coverage_ready"])
        self.assertEqual(report["verified_product_count"], 0)

    def test_pending_products_do_not_satisfy_coverage(self):
        products = self._products()
        for product in products:
            product.validation_status = "pending"
        self.assertFalse(validate_catalogue(products)["coverage_ready"])

    def test_valid_verified_fixture_meets_count_minimums(self):
        report = validate_catalogue(self._products())
        self.assertTrue(report["coverage_ready"], report["errors"])
        self.assertEqual(report["verified_product_count"], 15)

    def test_duplicate_models_prevent_coverage(self):
        products = self._products()
        products[1].model_ref = products[0].model_ref
        self.assertFalse(validate_catalogue(products)["coverage_ready"])

    def test_nonfinite_values_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                product = self._product()
                product.specs[0].value_num = value
                self.assertTrue(product.validate())

    def test_spec_must_belong_to_product_and_declared_source(self):
        product = self._product()
        product.specs[0].product_id = "OTHER"
        self.assertTrue(product.validate())
        product = self._product()
        product.specs[0].source_id = "UNDECLARED"
        self.assertTrue(product.validate())

    def test_verified_spec_requires_review_and_page(self):
        original = self._product()
        for field, value in (("reviewer", ""), ("page", None), ("page", 0), ("validation_status", "made_up")):
            with self.subTest(field=field):
                product = copy.deepcopy(original)
                setattr(product.specs[0], field, value)
                self.assertTrue(product.validate())

    def test_csv_verification_flag_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.csv"
            fields = ["product_id", "category", "manufacturer", "model", "spec_source_url", "manual_url", "license", "verified"]
            for flag in ("false", "FALSE", " false ", "unknown"):
                with self.subTest(flag=flag):
                    with path.open("w", encoding="utf-8", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=fields)
                        writer.writeheader()
                        writer.writerow({"product_id": "MOCK-1", "verified": flag})
                    if flag == "unknown":
                        with self.assertRaises(ValueError):
                            load_products_csv(path)
                    else:
                        self.assertEqual(load_products_csv(path)[0].validation_status, "pending")

    def test_cli_writes_report_without_overwriting_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.csv"
            path.write_text(
                "product_id,category,manufacturer,model,spec_source_url,manual_url,license,verified\n"
                "MOCK-1,industrial_pumps,,,,,,false\n", encoding="utf-8",
            )
            original = path.read_bytes()
            command = [sys.executable, "-B", "-m", "ai.ingestion.normalize_specs", "--catalogue", str(path)]
            result = subprocess.run(command + ["--report", str(path)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(path.read_bytes(), original)
            report_path = Path(directory) / "validation.json"
            result = subprocess.run(command + ["--report", str(report_path), "--require-coverage"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(json.loads(report_path.read_text())["coverage_ready"])
            self.assertEqual(path.read_bytes(), original)

    def test_load_products_with_linked_sources_and_specs(self):
        with tempfile.TemporaryDirectory() as directory:
            dir_path = Path(directory)
            prod_path = dir_path / "products.csv"
            prod_path.write_text(
                "product_id,category,manufacturer,model,spec_source_url,manual_url,license,verified\n"
                "PROD-01,industrial_pumps,TestMaker,TP-100,https://example.invalid/spec,https://example.invalid/man,CC-BY-4.0,true\n",
                encoding="utf-8",
            )
            sources_path = dir_path / "sources.csv"
            sources_path.write_text(
                "source_id,category_id,product_id,material_type\n"
                "SRC-01,industrial_pumps,PROD-01,manual\n",
                encoding="utf-8",
            )
            specs_path = dir_path / "specifications.csv"
            specs_path.write_text(
                "product_id,field_key,value_text,value_num,canonical_unit,source_id,page,extraction_method,validation_status,reviewer\n"
                "PROD-01,rated_power_kw,1.5,1.5,kW,SRC-01,4,manual_review,verified,rev-1\n",
                encoding="utf-8",
            )
            products = load_products_csv(prod_path, manifest_path=sources_path, specs_path=specs_path)
            self.assertEqual(len(products), 1)
            product = products[0]
            self.assertEqual(product.source_ids, ["SRC-01"])
            self.assertEqual(len(product.specs), 1)
            self.assertEqual(product.specs[0].field_key, "rated_power_kw")
            self.assertEqual(product.specs[0].value_num, 1.5)
            self.assertEqual(product.specs[0].canonical_unit, "kW")
            self.assertEqual(product.validate(), [])

    def test_rejection_of_missing_or_unreviewed_evidence(self):
        product = ProductRecord(
            product_id="PROD-01", category_id="industrial_pumps",
            manufacturer="TestMaker", model_ref="TP-100", display_name="Test Pump",
            source_ids=[], specs=[], validation_status="verified",
        )
        # Missing source IDs
        errors = product.validate()
        self.assertIn("at least one source_id is required", errors)

        # Mismatched spec product_id and source_id
        product.source_ids = ["SRC-01"]
        mismatched_spec = SpecValue(
            product_id="OTHER-PROD", field_key="rated_power_kw", value_text="1.0",
            value_num=1.0, canonical_unit="kW", source_id="OTHER-SRC", page=1,
            validation_status="verified", reviewer="rev-1",
        )
        product.specs = [mismatched_spec]
        errors = product.validate()
        self.assertIn("specification belongs to a different product", errors)
        self.assertIn("specification source is not declared by the product", errors)

        # Verified product cannot have unreviewed (pending) specification
        pending_spec = SpecValue(
            product_id="PROD-01", field_key="rated_power_kw", value_text="1.0",
            value_num=1.0, canonical_unit="kW", source_id="SRC-01", page=1,
            validation_status="pending", reviewer="",
        )
        product.specs = [pending_spec]
        errors = product.validate()
        self.assertIn("verified product has unreviewed specification: rated_power_kw", errors)


if __name__ == "__main__":
    unittest.main()
