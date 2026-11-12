"""Validate proposed product and specification rows before backend integration.

Source IDs and reviewer fields record provenance; they do not prove that a value
is true. Verified numeric rows require a reviewed source page. Markdown-only
evidence stays pending until a locator contract is agreed with Backend/Security.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALIDATION_STATUSES = {"pending", "verified", "rejected"}
CATALOGUE_COLUMNS = (
    "product_id", "category", "manufacturer", "model", "spec_source_url",
    "manual_url", "license", "verified",
)
SPECIFICATION_COLUMNS = (
    "product_id", "field_key", "value_text", "canonical_unit", "source_id",
)

# Canonical units per specification field key.
# Keys not in this map require explicit unit in the source row.
CANONICAL_UNITS: dict[str, str] = {
    "rated_power_kw": "kW",
    "rated_power_kva": "kVA",
    "voltage_v": "V",
    "frequency_hz": "Hz",
    "flow_rate_l_min": "L/min",
    "flow_rate_m3_h": "m³/h",
    "head_m": "m",
    "mass_kg": "kg",
    "noise_db": "dB(A)",
    "efficiency_pct": "%",
    "fuel_consumption_l_h": "L/h",
    "warranty_months": "months",
    "dc_voltage_min_v": "V",
    "dc_voltage_max_v": "V",
    "mppt_voltage_min_v": "V",
    "mppt_voltage_max_v": "V",
    "ac_output_voltage_v": "V",
    "max_charge_current_a": "A",
    "ip_rating": "",
    "protection_rating": "",
    "mppt_trackers": "",
    "battery_voltage_v": "V",
    "dimensions_mm": "mm",
    "fuel_tank_l": "L",
}

# Categories and their expected field keys (subset; additional keys allowed).
CATEGORY_FIELDS: dict[str, set[str]] = {
    "industrial_pumps": {
        "rated_power_kw", "voltage_v", "frequency_hz",
        "flow_rate_l_min", "flow_rate_m3_h", "head_m",
        "mass_kg", "ip_rating", "protection_rating",
    },
    "power_generators": {
        "rated_power_kw", "rated_power_kva", "voltage_v", "frequency_hz",
        "fuel_consumption_l_h", "noise_db", "mass_kg",
        "fuel_tank_l", "dimensions_mm",
    },
    "solar_inverters": {
        "rated_power_kw", "efficiency_pct", "voltage_v",
        "dc_voltage_min_v", "dc_voltage_max_v",
        "mppt_voltage_min_v", "mppt_voltage_max_v",
        "ac_output_voltage_v", "mppt_trackers", "mass_kg",
        "ip_rating", "battery_voltage_v",
    },
}


@dataclass
class SpecValue:
    """A single specification value with provenance."""
    product_id: str
    field_key: str
    value_text: str
    value_num: float | None
    canonical_unit: str
    source_id: str
    page: int | None
    extraction_method: str = "manual_review"
    validation_status: str = "pending"
    reviewer: str = ""

    def validate(self, category: str) -> list[str]:
        """Return a list of validation errors."""
        errors: list[str] = []
        if not self.product_id:
            errors.append("product_id is required")
        if not self.field_key:
            errors.append("field_key is required")
        if not self.source_id:
            errors.append("source_id is required")
        if self.validation_status not in VALIDATION_STATUSES:
            errors.append("unknown specification validation_status")
        if self.page is not None and (type(self.page) is not int or self.page < 1):
            errors.append("page must be a positive integer")
        if self.validation_status == "verified":
            if not self.reviewer.strip():
                errors.append("verified specification requires a reviewer")
            if self.page is None:
                errors.append("verified specification requires a reviewed source page")
        if self.field_key in CANONICAL_UNITS:
            expected = CANONICAL_UNITS[self.field_key]
            if expected and self.canonical_unit != expected:
                errors.append(
                    f"unit mismatch for {self.field_key}: "
                    f"got '{self.canonical_unit}', expected '{expected}'"
                )
        if self.value_num is not None:
            if not isinstance(self.value_num, (int, float)) or isinstance(self.value_num, bool) or not math.isfinite(self.value_num):
                errors.append("numeric value must be finite")
                return errors
            if self.field_key.endswith("_kg") and self.value_num <= 0:
                errors.append(f"impossible {self.field_key} value: {self.value_num}")
            if self.field_key.endswith("_kw") and self.value_num <= 0:
                errors.append(f"impossible {self.field_key} value: {self.value_num}")
            if self.field_key == "efficiency_pct" and not (0 < self.value_num <= 100):
                errors.append(f"efficiency out of range: {self.value_num}")
        if category and category in CATEGORY_FIELDS:
            if self.field_key not in CATEGORY_FIELDS[category] and self.field_key not in CANONICAL_UNITS:
                errors.append(
                    f"field {self.field_key} not expected for category {category}; "
                    f"add to CATEGORY_FIELDS if valid"
                )
        return errors


@dataclass
class ProductRecord:
    """A product in the canonical catalogue with provenance."""
    product_id: str
    category_id: str
    manufacturer: str
    model_ref: str
    display_name: str
    source_ids: list[str] = field(default_factory=list)
    specs: list[SpecValue] = field(default_factory=list)
    validation_status: str = "pending"
    review_notes: str = ""

    def validate(self) -> list[str]:
        """Return a list of validation errors."""
        errors: list[str] = []
        if not self.product_id:
            errors.append("product_id is required")
        if not self.category_id:
            errors.append("category_id is required")
        if self.category_id not in CATEGORY_FIELDS:
            errors.append(f"unknown category: {self.category_id}")
        if not self.manufacturer:
            errors.append("manufacturer is required")
        if not self.model_ref:
            errors.append("model_ref is required")
        if not self.source_ids:
            errors.append("at least one source_id is required")
        if self.validation_status not in VALIDATION_STATUSES:
            errors.append("unknown product validation_status")
        seen_fields: set[tuple[str, str]] = set()
        for spec in self.specs:
            if spec.product_id != self.product_id:
                errors.append("specification belongs to a different product")
            if spec.source_id not in self.source_ids:
                errors.append("specification source is not declared by the product")
            if self.validation_status == "verified" and spec.validation_status != "verified":
                errors.append(f"verified product has unreviewed specification: {spec.field_key}")
            key = (spec.field_key, spec.source_id)
            if key in seen_fields:
                errors.append(f"duplicate spec: {spec.field_key} from {spec.source_id}")
            seen_fields.add(key)
            errors.extend(spec.validate(self.category_id))
        return errors


def validate_catalogue(
    products: list[ProductRecord],
) -> dict[str, Any]:
    """Validate a list of product records for completeness and consistency."""
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    seen_models: set[str] = set()
    categories: set[str] = set()
    verified_products: list[ProductRecord] = []

    for product in products:
        if product.product_id in seen_ids:
            errors.append(f"duplicate product_id: {product.product_id}")
        seen_ids.add(product.product_id)

        if product.model_ref in seen_models:
            errors.append(f"duplicate model_ref: {product.model_ref}")
        seen_models.add(product.model_ref)

        product_errors = product.validate()
        errors.extend(f"{product.product_id}: {e}" for e in product_errors)
        categories.add(product.category_id)

        if not product.specs:
            warnings.append(f"{product.product_id}: no specifications yet")
        if (
            not product_errors
            and product.validation_status == "verified"
            and product.specs
            and all(spec.validation_status == "verified" for spec in product.specs)
        ):
            verified_products.append(product)

    per_category = {}
    for cat in sorted(categories):
        count = sum(1 for p in products if p.category_id == cat)
        per_category[cat] = count

    verified_categories = {product.category_id for product in verified_products}
    return {
        "valid": not errors,
        "product_count": len(products),
        "category_count": len(categories),
        "per_category": per_category,
        "verified_product_count": len(verified_products),
        "verified_category_count": len(verified_categories),
        "coverage_ready": not errors and len(verified_products) >= 15 and len(verified_categories) >= 3,
        "errors": errors,
        "warnings": warnings,
        "minimums": {"products": 15, "categories": 3},
        "limitations": [
            "Counts depend on recorded reviews; this check does not establish technical truth or source rights.",
            "Source manifest checks and Backend/Security contract review are separate requirements.",
        ],
    }


def load_product_source_ids(manifest_path: Path) -> dict[str, list[str]]:
    """Return a mapping of product_id -> list of source_ids from the manifest."""
    mapping: dict[str, list[str]] = {}
    if not manifest_path.is_file():
        return mapping
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        for row in reader:
            pid = row.get("product_id", "").strip()
            sid = row.get("source_id", "").strip()
            if pid and sid:
                mapping.setdefault(pid, []).append(sid)
    return mapping


def load_specifications_csv(specs_path: Path) -> list[SpecValue]:
    """Load specification records from a CSV file."""
    specs: list[SpecValue] = []
    if not specs_path.is_file():
        return specs
    with specs_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        columns = reader.fieldnames or []
        required = set(SPECIFICATION_COLUMNS)
        if not required.issubset(columns):
            raise ValueError(f"Specifications CSV missing required columns: {required - set(columns)}")
        for number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"row {number}: wrong number of CSV cells")
            raw_num = row.get("value_num", "").strip()
            val_num: float | None = None
            if raw_num:
                try:
                    val_num = float(raw_num)
                except ValueError:
                    val_num = None
            raw_page = row.get("page", "").strip()
            page_val: int | None = None
            if raw_page:
                try:
                    page_val = int(raw_page)
                except ValueError:
                    page_val = None
            specs.append(SpecValue(
                product_id=row.get("product_id", "").strip(),
                field_key=row.get("field_key", "").strip(),
                value_text=row.get("value_text", "").strip(),
                value_num=val_num,
                canonical_unit=row.get("canonical_unit", "").strip(),
                source_id=row.get("source_id", "").strip(),
                page=page_val,
                extraction_method=row.get("extraction_method", "manual_review").strip() or "manual_review",
                validation_status=row.get("validation_status", "pending").strip() or "pending",
                reviewer=row.get("reviewer", "").strip(),
            ))
    return specs


def load_products_csv(
    csv_path: Path,
    manifest_path: Path | None = None,
    specs_path: Path | None = None,
) -> list[ProductRecord]:
    """Load products from the catalogue CSV and link available sources and specifications."""
    # Resolve optional source manifest and specification paths
    if manifest_path is None:
        sibling = csv_path.parent / "sources.csv"
        manifest_dir = csv_path.parent.parent / "manifests" / "sources.csv"
        if sibling.is_file():
            manifest_path = sibling
        elif manifest_dir.is_file():
            manifest_path = manifest_dir

    if specs_path is None:
        sibling_specs = csv_path.parent / "specifications.csv"
        if sibling_specs.is_file():
            specs_path = sibling_specs

    source_map: dict[str, list[str]] = {}
    if manifest_path and manifest_path.is_file():
        source_map = load_product_source_ids(manifest_path)

    spec_map: dict[str, list[SpecValue]] = {}
    if specs_path and specs_path.is_file():
        for spec in load_specifications_csv(specs_path):
            spec_map.setdefault(spec.product_id, []).append(spec)

    products: list[ProductRecord] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or not set(CATALOGUE_COLUMNS).issubset(columns):
            raise ValueError("Catalogue has missing or duplicate columns")
        for number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"row {number}: wrong number of CSV cells")
            flag = row["verified"].strip().casefold()
            if flag not in {"true", "false"}:
                raise ValueError(f"row {number}: verified must be true or false")
            product_id = row.get("product_id", "").strip()

            # Collect linked sources: explicitly from CSV column if present, plus from manifest
            linked_sources: list[str] = []
            if "source_ids" in row and row["source_ids"].strip():
                raw_sources = row["source_ids"].replace(",", ";").split(";")
                linked_sources.extend(s.strip() for s in raw_sources if s.strip())
            elif "source_id" in row and row["source_id"].strip():
                linked_sources.append(row["source_id"].strip())
            if product_id in source_map:
                for sid in source_map[product_id]:
                    if sid not in linked_sources:
                        linked_sources.append(sid)

            linked_specs = spec_map.get(product_id, [])

            products.append(ProductRecord(
                product_id=product_id,
                category_id=row.get("category", "").strip(),
                manufacturer=row.get("manufacturer", "").strip(),
                model_ref=row.get("model", "").strip(),
                display_name=row.get("model", "").strip(),
                source_ids=linked_sources,
                specs=linked_specs,
                validation_status="verified" if flag == "true" else "pending",
            ))
    return products


def write_catalogue_report(report: dict[str, Any], path: Path) -> None:
    """Write the validation report as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=Path("data/catalogue/products.csv"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--specs", type=Path, default=None)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--require-coverage", action="store_true")
    args = parser.parse_args(argv)
    if args.catalogue.resolve() == args.report.resolve():
        parser.error("Report must not overwrite the catalogue")
    try:
        products = load_products_csv(args.catalogue, manifest_path=args.manifest, specs_path=args.specs)
        report = validate_catalogue(products)
        write_catalogue_report(report, args.report)
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(1, f"Catalogue validation failed: {exc}\n")
    print(
        f"{report['product_count']} catalogue rows; {report['verified_product_count']} verified products; "
        f"coverage_ready={report['coverage_ready']}. Report: {args.report}"
    )
    return 0 if report["valid"] and (not args.require_coverage or report["coverage_ready"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
