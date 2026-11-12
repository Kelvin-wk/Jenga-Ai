"""Validate source metadata, file hashes and product coverage.

Run from the repository root: python -m ai.ingestion.manifest --require-coverage
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED_COLUMNS = (
    "source_id", "category_id", "product_id", "material_type", "publisher",
    "title", "url", "accessed_on", "license", "redistribution_allowed",
    "license_evidence_url", "sha256", "revision", "page_count",
    "extraction_method", "cleaning_steps", "validation_status", "reviewer",
)
# Used by this checker; not part of the backend schema.
OPTIONAL_COLUMNS = ("local_path",)
DOCUMENT_TYPES = {"manual", "datasheet", "safety", "installation", "maintenance", "troubleshooting"}
MATERIAL_TYPES = DOCUMENT_TYPES | {"image", "audio"}
VALIDATION_STATUSES = {"pending", "verified", "rejected"}
UNRESOLVED_VALUES = {"", "tbd", "unknown", "unverified", "pending", "n/a", "none", "placeholder"}


def _is_http_url(value: str) -> bool:
    if any(character.isspace() or ord(character) < 32 for character in value):
        return False
    try:
        parsed = urlsplit(value)
        # urlsplit defers port validation until this attribute is read.
        port = parsed.port
        return (
            parsed.scheme in {"https", "http"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and (port is None or 1 <= port <= 65535)
        )
    except ValueError:
        return False


def validate_manifest(manifest_path: Path, asset_root: Path, *, today: date | None = None) -> dict[str, object]:
    """Check the review record and compare local files with their recorded hashes.

    Only verified rows without errors count toward coverage. A reviewer must
    establish usage rights and technical accuracy before marking a row verified.
    """
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    valid_sources: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    product_categories: dict[str, str] = {}
    rows: list[dict] = []
    try:
        with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            headers = reader.fieldnames or []
            missing = sorted(set(REQUIRED_COLUMNS) - set(headers))
            if missing:
                errors.append("Missing columns: " + ", ".join(missing))
            if len(headers) != len(set(headers)):
                errors.append("Duplicate column names")
            unknown = sorted(set(headers) - set(REQUIRED_COLUMNS) - set(OPTIONAL_COLUMNS))
            if unknown:
                errors.append("Unknown columns: " + ", ".join(unknown))
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"Cannot read manifest: {exc}")

    schema_valid = not errors
    for number, raw in enumerate(rows, start=2):
        label = f"row {number}"
        row_errors: list[str] = []
        if None in raw or any(value is None for value in raw.values()):
            errors.append(f"{label}: wrong number of CSV cells")
            continue
        row = {key: value.strip() for key, value in raw.items()}
        source_id = row.get("source_id", "")
        if not source_id:
            row_errors.append("source_id is required")
        elif source_id in seen_ids:
            row_errors.append(f"duplicate source_id {source_id}")
        seen_ids.add(source_id)
        status = row.get("validation_status", "")
        if status not in VALIDATION_STATUSES:
            row_errors.append("validation_status must be pending, verified or rejected")
        if row.get("material_type") not in MATERIAL_TYPES:
            row_errors.append("unsupported material_type")
        if status != "verified":
            warnings.append(f"{label}: {source_id or '(no ID)'} excluded from coverage ({status or 'no status'})")
        else:
            for field in REQUIRED_COLUMNS:
                value = row.get(field, "").casefold()
                if field == "cleaning_steps" and value == "none":
                    continue
                if value in UNRESOLVED_VALUES:
                    row_errors.append(f"{field} must be resolved for a verified source")
            for field in ("url", "license_evidence_url"):
                if not _is_http_url(row.get(field, "")):
                    row_errors.append(f"{field} must be an HTTP(S) URL without embedded credentials")
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("accessed_on", "")):
                    raise ValueError
                accessed = date.fromisoformat(row.get("accessed_on", ""))
                if accessed > today:
                    row_errors.append("accessed_on cannot be in the future")
            except ValueError:
                row_errors.append("accessed_on must be YYYY-MM-DD")
            if row.get("redistribution_allowed") not in {"true", "false"}:
                row_errors.append("redistribution_allowed must be true or false")
            if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
                row_errors.append("sha256 must be 64 lowercase hexadecimal characters")
            try:
                if int(row.get("page_count", "")) < 1:
                    raise ValueError
            except ValueError:
                row_errors.append("page_count must be a positive integer (use 1 for an image/audio asset)")
            local_path = row.get("local_path", "")
            if not local_path:
                row_errors.append("local_path is required to check the source file")
            else:
                try:
                    root = asset_root.resolve()
                    candidate = Path(local_path)
                    snapshot = (root / candidate).resolve()
                    if candidate.is_absolute() or not snapshot.is_relative_to(root):
                        row_errors.append("local_path must remain relative to asset_root")
                    elif not snapshot.is_file():
                        row_errors.append("local_path does not identify an existing file")
                    else:
                        with snapshot.open("rb") as stream:
                            digest = hashlib.file_digest(stream, "sha256").hexdigest()
                        if digest != row.get("sha256"):
                            row_errors.append("local snapshot sha256 mismatch")
                except (OSError, ValueError, RuntimeError) as exc:
                    row_errors.append(f"cannot resolve/read local snapshot: {exc}")
            if row.get("redistribution_allowed") == "false":
                warnings.append(f"{label}: keep this snapshot private; submit only permitted extracts/access instructions")
            if row.get("sha256") in seen_hashes:
                warnings.append(f"{label}: duplicate asset hash; audit shared-document mappings")
            seen_hashes.add(row.get("sha256", ""))
            product = row.get("product_id", "")
            category = row.get("category_id", "")
            if product in product_categories and product_categories[product] != category:
                row_errors.append("product_id is assigned to multiple categories")
        errors.extend(f"{label}: {message}" for message in row_errors)
        if schema_valid and status == "verified" and not row_errors:
            valid_sources.append(row)
            product_categories[row["product_id"]] = row["category_id"]

    document_sources = [row for row in valid_sources if row["material_type"] in DOCUMENT_TYPES]
    documented_products = {row["product_id"] for row in document_sources}
    documented_categories = {row["category_id"] for row in document_sources}
    coverage = {
        "documented_products": len(documented_products),
        "documented_categories": len(documented_categories),
    }
    manifest_valid = not errors
    return {
        "schema_version": 1,
        "manifest_valid": manifest_valid,
        "coverage_ready": manifest_valid and len(documented_products) >= 15 and len(documented_categories) >= 3,
        "rows": len(rows), "verified_assets": len(valid_sources),
        "coverage": coverage,
        "minimums": {"documented_products": 15, "documented_categories": 3},
        "errors": errors, "warnings": warnings,
        "limitations": ["Structural checks do not establish legal rights or technical correctness.",
                        "Image/audio labeling and benchmark minimums are not evaluated by this A-01 checker."],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/sources.csv"))
    parser.add_argument("--asset-root", type=Path, default=Path("."))
    parser.add_argument("--require-coverage", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.report and args.report.resolve() == args.manifest.resolve():
        parser.error("--report must not overwrite the source manifest")
    report = validate_manifest(args.manifest, args.asset_root)
    output = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["manifest_valid"] and (not args.require_coverage or report["coverage_ready"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
