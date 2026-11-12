import csv
from pathlib import Path

base = Path("data")

for directory in [
    "sources/manuals",
    "sources/images",
    "sources/audio",
    "catalogue",
    "synthetic",
    "validated",
    "evaluation",
]:
    (base / directory).mkdir(parents=True, exist_ok=True)

categories = {
    "PMP": "industrial_pumps",
    "GEN": "power_generators",
    "INV": "solar_inverters",
}

fields = [
    "product_id",
    "category",
    "manufacturer",
    "model",
    "spec_source_url",
    "manual_url",
    "license",
    "verified",
]

path = base / "catalogue" / "products.csv"

if path.exists():
    raise SystemExit(
        f"{path} already exists. Refusing to overwrite."
    )

with path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for code, category in categories.items():
        for i in range(1, 6):
            writer.writerow({
                "product_id": f"JC-{code}-{i:03d}",
                "category": category,
                "manufacturer": "",
                "model": "",
                "spec_source_url": "",
                "manual_url": "",
                "license": "",
                "verified": "false",
            })

print("Created 15 catalogue slots across 3 categories.")
print(f"File: {path}")
print("All products remain unverified.")
