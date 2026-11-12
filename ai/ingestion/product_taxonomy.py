"""Proposed catalogue validation and conservative exact-name lookup.

This is a review adapter, not the backend catalogue or an authorization layer.
"""

import csv
import hashlib
from pathlib import Path


TAXONOMY = {
    "battery_energy_storage": {
        "battery_management_system": {"battery_management_board"},
    },
}


def normalize_name(value: str) -> str:
    return " ".join(value.casefold().split())


def validate_product(product: dict, manifest_path: Path, asset_root: Path) -> None:
    for key in ("manufacturer", "model", "common_name", "category", "subcategory", "product_type"):
        if not isinstance(product.get(key), str) or not product[key].strip():
            raise ValueError(f"Missing {key}")
    for key in ("aliases", "related_systems", "source_ids", "evidence"):
        if not isinstance(product.get(key), list) or not product[key]:
            raise ValueError(f"Missing {key}")
    types = TAXONOMY.get(product["category"], {}).get(product["subcategory"], set())
    if product["product_type"] not in types:
        raise ValueError("Inconsistent product classification")
    if any(not isinstance(item, str) or not item.strip() for key in ("aliases", "related_systems", "source_ids") for item in product[key]):
        raise ValueError("Empty or invalid list entry")
    names = {normalize_name(x) for x in [product["common_name"], *product["aliases"]]}
    if names & {normalize_name(x) for x in product["related_systems"]}:
        raise ValueError("Related systems cannot be aliases")
    with manifest_path.open(encoding="utf-8", newline="") as stream:
        sources = {row["source_id"]: row for row in csv.DictReader(stream)}
    if len(set(product["source_ids"])) != len(product["source_ids"]):
        raise ValueError("Duplicate source ID")
    for reference in product["evidence"]:
        source_id = reference.get("source_id")
        if source_id not in product["source_ids"] or source_id not in sources:
            raise ValueError("Unknown evidence source")
        source = sources[source_id]
        if reference.get("revision") != source["revision"]:
            raise ValueError("Evidence revision mismatch")
        start, end = reference.get("start_line"), reference.get("end_line")
        path = (asset_root / source["local_path"]).resolve()
        if not path.is_relative_to(asset_root.resolve()):
            raise ValueError("Source path escapes asset root")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError("Source hash mismatch")
        lines = content.decode("utf-8").splitlines()
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
            raise ValueError("Invalid evidence line range")
        if reference.get("page") is not None:
            raise ValueError("PDF mapping has not been verified")
    if set(product["source_ids"]) != {ref["source_id"] for ref in product["evidence"]}:
        raise ValueError("Every source must have evidence")


def resolve_product(query: str, products: list[dict]) -> dict:
    """Resolve whole names only; ambiguous and absent names are errors."""
    needle = normalize_name(query)
    matches = []
    for product in products:
        names = [product["model"], f'{product["manufacturer"]} {product["model"]}',
                 *product["aliases"]]
        if needle and needle in {normalize_name(name) for name in names}:
            matches.append(product)
    if len(matches) != 1:
        raise ValueError("Ambiguous or unknown product name")
    return matches[0]
