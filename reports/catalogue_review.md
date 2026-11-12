# Catalogue and Taxonomy Review

**Date:** 12 November 2026 (Africa/Nairobi)

**Task:** A-01 Source Review and A-02 Ingestion Preparation

**Author:** AGENT-A (KWAIX) — AI/Data/Evaluation Owner

**Branch:** `feature/ai-catalogue-sources` (branched from `origin/main@c6ed220`)

---

## 1. Current status

- **15 catalogue candidates, 0 approved products.** All rows in
  `data/catalogue/products.csv` keep `verified: false`; all manifest candidates
  keep `validation_status: "pending"`.
- **13 of 15 slots now link to a verified official document.** Each linked
  document returned HTTP 200 on 12 November 2026 and has a recorded SHA-256.
  Kipor KDE6700TA and Cummins C55D5 remain without a verified official document
  URL or hash.
- **Rights remain unresolved.** Every commercial candidate records
  `processing`, `quotation` and `redistribution` as `pending_review`. No
  fair-dealing, fair-use or open-evaluation permission is asserted.
- **No commercial PDFs were committed.** Downloads used for hashing were kept in
  a temporary private directory. `data/manifests/sources.csv` records URLs,
  hashes, page counts and HTTP Last-Modified dates only.
- **Hardware documentation corrected.** The observed GPU is an NVIDIA GeForce
  RTX 3050 Laptop GPU with 6 GB VRAM and the host has about 8 GB OS-visible RAM.
  The exposed host has not been independently confirmed as Athena; no
  model-capacity claim is made from this observation.
- **Ingestion linkage exercised.** `load_products_csv` links source IDs from
  `data/manifests/sources.csv`. The current run links 13 of 15 products and
  reports the two missing Kipor/Cummins source rows. No catalogue
  `specifications.csv` exists yet, so specification loading remains covered by
  unit fixtures rather than production rows.
- **Libre Solar BMS C1** remains a pending ingestion sample under CC BY-SA 4.0
  (commit `7c2dcc1c4f266ce2a977c386ddaa4319f1ed1095`). It does not count toward
  the three-category / 15-product minimums.

## 2. Candidate slots

| Slot | Category | Manufacturer | Model | Verified document | Page locator | Rights |
|---|---|---|---|---|---|---|
| **JC-PMP-001** | industrial_pumps | Dayliff | DDP 60 | [ddp60.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/ddp60.pdf) | p. 1 | `pending_review` |
| **JC-PMP-002** | industrial_pumps | Dayliff | DSD 3/18 | [dsd-datasheet.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/dsd-datasheet.pdf) | p. 2 | `pending_review` |
| **JC-PMP-003** | industrial_pumps | Dayliff | DB 4/30 | [db_685346571.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/db_685346571.pdf) | p. 4 | `pending_review` |
| **JC-PMP-004** | industrial_pumps | Dayliff | DDJ 750 | [file_id-7339](https://www.dayliff.com/products/product/download/file_id-7339) | Pending | `pending_review` |
| **JC-PMP-005** | industrial_pumps | Pedrollo | CP 158 | [CP_EN-datasheet_50Hz.pdf](https://www.pedrollo.com/wp-content/uploads/schede-tecniche/EN/CP_EN-datasheet_50Hz.pdf) | pp. 2–3 | `pending_review` |
| **JC-GEN-001** | power_generators | Honda | EU22i | [EU22i owner's manual](https://cf.hondappsv.com/files/OM/OM000567HME/00X36-Z44-G010_EU22iT_HME_en.pdf) | pp. 55–56 | `pending_review` |
| **JC-GEN-002** | power_generators | Honda | EG6500CX | [EG6500CX owner's manual](https://cf.hondappsv.com/files/OM/OM001285MEX/4MZ306031_web.pdf) | pp. 42–43 | `pending_review` |
| **JC-GEN-003** | power_generators | Kipor | KDE6700TA | Pending | Pending | `pending_review` |
| **JC-GEN-004** | power_generators | FG Wilson | P22-1 | [P22-1.pdf](https://fgwilson.ie/wp-content/uploads/2022/11/P22-1.pdf) | pp. 1–3 | `pending_review` |
| **JC-GEN-005** | power_generators | Cummins | C55D5 | Pending | Pending | `pending_review` |
| **JC-INV-001** | solar_inverters | Victron Energy | MultiPlus-II 48/3000/35-32 | [MultiPlus-II datasheet](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-inverter-charger-EN-.pdf) | p. 2 | `pending_review` |
| **JC-INV-002** | solar_inverters | Victron Energy | MultiPlus-II 48/5000/70-50 | Same datasheet | p. 2 | `pending_review` |
| **JC-INV-003** | solar_inverters | Growatt | SPF 5000 ES | [SPF 3000-5000 ES datasheet](https://us.growatt.com/upload/file/SPF_3000-5000_ES_Datasheet_EN_202405.pdf) | p. 2 | `pending_review` |
| **JC-INV-004** | solar_inverters | Deye | SUN-5K-SG03LP1-EU | [SUN-3.6-6K-SG03LP1 datasheet](https://www.deyeinverter.com/deyeinverter/2024/10/21/datasheet_sun-3.6-6k-sg03lp1_241021_en.pdf) | Pending | `pending_review` |
| **JC-INV-005** | solar_inverters | Huawei | SUN2000-10KTL-M1 | [SUN2000-3-10KTL-M1 datasheet](https://solar.huawei.com/-/media/Solar/attachment/pdf/eu/datasheet/SUN2000-3-10KTL-M1.pdf) | p. 2 | `pending_review` |

Detailed specifications, SHA-256 values and remaining technical blockers are in
`reports/catalogue_sourcing_research.md` and
`data/manifests/source_candidates.json`.

## 3. Test evidence

Executed with Python 3.14.7:

```powershell
python -B -m unittest discover -s ai/tests -v
```

**Result:** **43 passed in 3.641 s** (18 manifest tests, 11 normalize_specs
tests, 6 product_taxonomy tests, 8 source_preview tests).

```powershell
python -B -m ai.ingestion.manifest --require-coverage --report reports/source_validation.json
```

**Result:** exit 1 (expected). Manifest valid; **19 pending rows** (6 BMS
chapters plus 13 commercial document links); **0 verified assets, 0 verified
products, 0 verified categories**.

```powershell
python -B -m ai.ingestion.normalize_specs --catalogue data/catalogue/products.csv --require-coverage --report reports/catalogue_validation.json
```

**Result:** exit 1 (expected). **15 catalogue rows across 3 categories; 0
verified products.** 13 products link to recorded source rows; JC-GEN-003 and
JC-GEN-005 report `at least one source_id is required`. All 15 report
`no specifications yet` because no production `specifications.csv` has been
approved.

## 4. Backend/Security dependencies

1. **Product ID type:** Backend currently uses integer IDs (`ProductDB.id: int`);
   AI ingestion uses string identifiers (`JC-PMP-001`, `JC-GEN-001`,
   `JC-INV-001`).
2. **Specification representation:** Agree whether specifications are stored as a
   JSON string in `ProductDB.specifications` or as normalized `spec_values`
   rows. The candidate manifest uses richer field names than the ingestion
   schema; mapping must be agreed before a production `specifications.csv`.
3. **Pre-retrieval authorization:** Provide a server-derived `AuthContext` so
   retrieval can filter candidates before similarity scoring or full-text
   execution.
4. **Rights review:** Human review must resolve processing, quotation and
   redistribution separately; a public download is not a reuse licence.

No backend, frontend, database or API contract was changed in this review.
