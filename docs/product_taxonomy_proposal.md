# Product taxonomy proposal — A-01

This is an AI-side review format, not an approved database, API or retrieval
contract. Existing `products.csv` and `sources.csv` columns remain unchanged.
The candidate is in `data/catalogue/product_taxonomy_proposal.json` and does not
occupy a catalogue slot or count towards coverage.

## Proposed product fields

| Field | Meaning |
|---|---|
| `manufacturer`, `model` | Exact source-supported manufacturer and model identity; retain existing CSV fields. |
| `common_name` | Human-readable equipment type, not a unique identity. |
| `category`, `subcategory`, `product_type` | Hierarchical slugs. Proposed path: `battery_energy_storage` / `battery_management_system` / `battery_management_board`. |
| `aliases` | Alternative names identifying the same product; never a distinct equipment type or a generic class name. |
| `related_systems` | Associated, distinct equipment concepts; no equivalence or compatibility implied. |
| `source_ids` | IDs in the existing source manifest. |
| `evidence` | Source ID, exact revision, one-based inclusive line range and optional page; each source ID must have a reference. |
| `status` | Candidate remains `pending_catalogue_approval`. |

Proposed source representation retains existing manifest fields including URL,
revision, license, hash and review status. A citation additionally carries a
locator: source ID, revision and Markdown line range, or a verified PDF page.
PDF source identity, byte hash, page numbering and revision equivalence must be
established before associating PDF pages with a Markdown snapshot. A source
reference is not itself evidence of technical review or redistribution rights.

`ai/ingestion/product_taxonomy.py` validates this one proposed taxonomy path and
resolves model names and explicitly listed aliases with case and whitespace
normalization. A common equipment name alone does not identify a product, and
shared names are rejected as ambiguous. It is a review utility, not deployed search; human review
must assess whether aliases describe the same concept. It does not implement
access control or verify semantic correctness of cited text.

## PDF investigation

The official [PDF](https://libre.solar/bms-c1/manual/manual.pdf) describes the
BMS in its printed page 3 and the board design on printed page 6; its contents
resemble the pinned Markdown, but no build provenance ties those PDF bytes to
commit `7c2dcc1c4f266ce2a977c386ddaa4319f1ed1095`. Similar text alone cannot
establish full revision equivalence. The PDF has not been pinned, hashed or
mapped; candidate page references remain null. The pinned Markdown introduction
and features chapters provide line-level references for this proposal.

The original snapshot, attribution and CC BY-SA 4.0 license notice are preserved.
Libre Solar's [product page](https://libre.solar/hardware/bms-c1.html) identifies
the C1 as a battery management system board. Catalogue suitability and technical
review remain pending; no specifications or catalogue approval are inferred.

## Review needed from AGENT-B

Agree identifier mapping, taxonomy and relation storage, source/citation
locators, versioning and ACL enforcement before a database migration or runtime
integration. AGENT-F should review citation display after B and A agree the
contract. This handoff is recorded locally and has not been sent.

## Review follow-up

The side-quest review confirmed the board classification on the official product
page and added a SHA-256 check before validating line references. Modified source
bytes are now rejected. PDF pages, catalogue suitability and B/F approval remain
pending. Current test and source findings are in `reports/catalogue_review.md`.
