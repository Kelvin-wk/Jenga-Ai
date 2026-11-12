# Real Equipment Catalogue Sourcing Research (Task A-01)

**Date:** 12 November 2026 (Africa/Nairobi)

**Author:** AGENT-A (KWAIX) — AI/Data/Evaluation Owner

**Repository Branch:** `feature/ai-catalogue-sources` (branched from `origin/main`)

**Status:** 15 candidates recorded; **0 approved products**; rights and human technical review pending

---

## 1. Scope and evidence standard

This report records candidate equipment models for the 15 slots in
`data/catalogue/products.csv`. It is research evidence, not a catalogue approval:

- All 15 rows keep `verified: false`.
- Every candidate keeps `validation_status: "pending"`.
- No candidate has been approved for processing, quotation or redistribution.
- Commercial manufacturer documents are **rights-unresolved**. Site availability is
  not a reuse licence, and no commercial document is stored in this repository.
- The Libre Solar BMS C1 sample is the only item with an explicit open licence
  (CC BY-SA 4.0). It does not count toward the three-category / 15-product minimums.

## 2. What was verified

For 13 of the 15 slots, the official document URL returned HTTP 200 and the
downloaded bytes were hashed with SHA-256. The inspected page or page range is
recorded where it was actually opened; two documents still lack a confirmed page
locator. Downloads were kept in a temporary private directory for hashing and
were not committed.

Two slots remain without a verified official document URL or hash:

- **JC-GEN-003 Kipor KDE6700TA** — no official exact document URL confirmed.
- **JC-GEN-005 Cummins C55D5** — no official exact document URL confirmed.

Verified product-page URLs are recorded separately from document URLs. A product
page is not treated as a datasheet citation.

## 3. Category 1: Industrial pumps (`industrial_pumps`)

Candidate specifications below are the values already recorded in
`data/manifests/source_candidates.json`; they still require human technical review.

| Slot | Model | Manufacturer | Candidate specifications | Verified document | Product page |
|---|---|---|---|---|---|
| **JC-PMP-001** | **DDP 60** | Dayliff (Davis & Shirtliff) | 0.37 kW; 240 V, 50 Hz; max head 35 m; max flow 3.0 m³/h; IP44; 5.3 kg | [ddp60.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/ddp60.pdf), p. 1 | Not verified |
| **JC-PMP-002** | **DSD 3/18** | Dayliff (Davis & Shirtliff) | 1.1 kW; 240 V, 50 Hz; nominal flow 3.0 m³/h; max head 129 m; IP68; outlet 1¼"; mass unknown | [dsd-datasheet.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/dsd-datasheet.pdf), p. 2 | [D&S DSD 3](https://www.davisandshirtliff.com/products-and-solutions/product/dsd-3) |
| **JC-PMP-003** | **DB 4/30** | Dayliff (Davis & Shirtliff) | 0.77–0.82 kW; 240 V, 50 Hz; max flow 4.0 m³/h; max head 30 m; 10 bar; IP54; 11.5 kg | [db_685346571.pdf](https://www.dayliff.com/media/com_hikashop/upload/safe/db_685346571.pdf), p. 4 | [D&S DB 4](https://www.davisandshirtliff.com/products-and-solutions/product/db-4) |
| **JC-PMP-004** | **DDJ 750** | Dayliff (Davis & Shirtliff) | 0.75 kW; 240 V, 50 Hz; max suction lift 9 m; IP44; 17 kg | [file_id-7339](https://www.dayliff.com/products/product/download/file_id-7339) (`ddj.pdf`); page locator not confirmed | Not verified |
| **JC-PMP-005** | **CP 158** | Pedrollo | 0.75 kW; 230 V, 50 Hz; flow 0.6–5.4 m³/h; head 25–36 m; IPX4; mass 12.4 kg (1-ph) / 12.3 kg (3-ph) | [CP_EN-datasheet_50Hz.pdf](https://www.pedrollo.com/wp-content/uploads/schede-tecniche/EN/CP_EN-datasheet_50Hz.pdf), pp. 2–3 | [Pedrollo CP](https://www.pedrollo.com/en/product/surface/single-and-double-impeller-centrifugal/single-impeller-centrifugal-pumps/cp/) |

The Dayliff `ddj.pdf` response was 126,883 bytes with the recorded SHA-256, but
the file has no PDF EOF marker. It is recorded as retrieved evidence only; a
complete document is required before ingestion.

## 4. Category 2: Power generators (`power_generators`)

| Slot | Model | Manufacturer | Candidate specifications | Verified document | Product page |
|---|---|---|---|---|---|
| **JC-GEN-001** | **EU22i** | Honda | 1.8 kW rated / 2.2 kW max; 230 V, 50 Hz; tank 3.6 L; 53–62 dB(A); 21.1 kg | [EU22i owner's manual](https://cf.hondappsv.com/files/OM/OM000567HME/00X36-Z44-G010_EU22iT_HME_en.pdf), pp. 55–56 | Not verified |
| **JC-GEN-002** | **EG6500CX** | Honda | 5.0 kVA rated / 5.5 kVA max; 220 V, 50 Hz; tank 24 L; 70–74 dB(A); 87 kg | [EG6500CX owner's manual](https://cf.hondappsv.com/files/OM/OM001285MEX/4MZ306031_web.pdf), pp. 42–43 | Not verified |
| **JC-GEN-003** | **KDE6700TA** | Kipor | 4.5 kVA rated / 5.0 kVA max; 230 V, 50 Hz; tank 15 L; 72 dB(A); 170 kg; fuel consumption pending | **Pending:** official document URL and hash not verified | Not verified |
| **JC-GEN-004** | **P22-1** | FG Wilson | 20 kVA prime / 22 kVA standby; 400 V, 50 Hz, 3-ph; 5.4 L/h; mass configuration-dependent | [P22-1.pdf](https://fgwilson.ie/wp-content/uploads/2022/11/P22-1.pdf), pp. 1–3 | Not verified |
| **JC-GEN-005** | **C55D5** | Cummins | 50 kVA prime / 55 kVA standby; 400 V, 50 Hz, 3-ph; 11.4 L/h; mass 922 kg open / 1,236 kg enclosed | **Pending:** official document URL and hash not verified | Not verified |

Honda's model-page response did not establish a stable exact product URL for
JC-GEN-002, so only the verified owner's manual is recorded.

## 5. Category 3: Solar inverters (`solar_inverters`)

| Slot | Model | Manufacturer | Candidate specifications | Verified document | Product page |
|---|---|---|---|---|---|
| **JC-INV-001** | **MultiPlus-II 48/3000/35-32** | Victron Energy | 2.4 kW / 3,000 VA; 38–66 V DC; 230 V AC; 95% efficiency; 35 A charger; IP22; 19 kg | [MultiPlus-II datasheet](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-inverter-charger-EN-.pdf), p. 2 | [Victron MultiPlus-II](https://www.victronenergy.com/inverters-chargers/multiplus-ii) |
| **JC-INV-002** | **MultiPlus-II 48/5000/70-50** | Victron Energy | 4.0 kW / 5,000 VA; 38–66 V DC; 230 V AC; 96% efficiency; 70 A charger; IP22; 30 kg | Same datasheet as JC-INV-001, p. 2 | [Victron MultiPlus-II](https://www.victronenergy.com/inverters-chargers/multiplus-ii) |
| **JC-INV-003** | **SPF 5000 ES** | Growatt | 5.0 kW; 120–430 V MPPT; 450 V max PV; 48 V battery; 93% efficiency; IP20; 12 kg | [SPF 3000-5000 ES datasheet](https://us.growatt.com/upload/file/SPF_3000-5000_ES_Datasheet_EN_202405.pdf), p. 2 | [Growatt SPF ES](https://en.growatt.com/products/spf-3000-5000-es-es-lite) |
| **JC-INV-004** | **SUN-5K-SG03LP1-EU** | Deye | 5.0 kW AC; 150–425 V MPPT; 2 MPPTs; 40–60 V battery; 97.6% efficiency; IP65; 20.5 kg | [SUN-3.6-6K-SG03LP1 datasheet](https://www.deyeinverter.com/deyeinverter/2024/10/21/datasheet_sun-3.6-6k-sg03lp1_241021_en.pdf); page locator not confirmed | Not verified |
| **JC-INV-005** | **SUN2000-10KTL-M1** | Huawei | 10.0 kW AC; 140–980 V DC; 470–850 V full-power MPPT; 2 MPPTs; 98.6% efficiency; IP65; 17 kg | [SUN2000-3-10KTL-M1 datasheet](https://solar.huawei.com/-/media/Solar/attachment/pdf/eu/datasheet/SUN2000-3-10KTL-M1.pdf), p. 2 | Not verified |

The Victron datasheet is a shared document for both MultiPlus-II slots. It is
recorded once per product link in `data/manifests/sources.csv`, with the same
hash, so the product relationship is explicit.

## 6. Verified document evidence

| Product | SHA-256 | HTTP Last-Modified | Page locator |
|---|---|---|---|
| JC-PMP-001 | `d9fb6b374f7d27ca1016a22bee3cdee83b6ef5dae43c0fca5a0d701a49b00d7f` | 2020-03-12 | p. 1 |
| JC-PMP-002 | `6ff00a372a7c1e79b974b4bf9fbf4f22f477bbd172c23bb6901e5266ac793849` | 2020-03-12 | p. 2 |
| JC-PMP-003 | `27fdf5fc0894948cacf12879ce6606c4f399577cc8f5fa730916a73fc2dadd2b` | 2020-03-12 | p. 4 |
| JC-PMP-004 | `1a8ba81a54a53a9ed2399b85a0e6da4f9bfe84cf23c6173df4497a2be0f5508c` | 2026-11-12 | Pending; file lacks EOF marker |
| JC-PMP-005 | `255dc51728056c6bfd5bdb5f9cb4649f7a2cb16d2d20aa4c17ec2747103aa55d` | 2026-09-03 | pp. 2–3 |
| JC-GEN-001 | `5efe831105b26e5c0c1b32872aa37c5e643aba74beb66e69d200084258c36841` | 2018-03-20 | pp. 55–56 |
| JC-GEN-002 | `aa96528f826cc112948a2df3f5bf0053af69ca457022494184d371f4aad02cc0` | 2021-07-28 | pp. 42–43 |
| JC-GEN-003 | Pending | Pending | Pending |
| JC-GEN-004 | `ccdcbc92743ea03be4435faa52bf61d41e8faef899f0037e3b714a2b115adadd` | 2022-11-30 | pp. 1–3 |
| JC-GEN-005 | Pending | Pending | Pending |
| JC-INV-001 | `04ccf7512949073346821267a760dcfa30927b73e349b9f2b9f7d566bec943df` | 2026-06-23 | p. 2 |
| JC-INV-002 | `04ccf7512949073346821267a760dcfa30927b73e349b9f2b9f7d566bec943df` | 2026-06-23 | p. 2 |
| JC-INV-003 | `b31cfa8409ebb539b64ded16353282da1548f70c55d2f4da0723386a5c9f7c8b` | 2024-05-27 | p. 2 |
| JC-INV-004 | `2a127ea8c77492b985a494b88155c57132ab853d663e83ff82b636721e5107e2` | 2024-10-21 | Pending |
| JC-INV-005 | `89aab23b7546e990ed09a0600d2c46390aefa7bb2c8026b6d371ff521129adda` | 2026-10-31 | p. 2 |

`HTTP Last-Modified` is a retrieval signal, not a document revision identifier.
No independent revision number was established for these PDFs.

## 7. Rights status

All commercial candidates use:

```json
{
  "processing": "pending_review",
  "quotation": "pending_review",
  "redistribution": "pending_review"
}
```

These are three separate questions:

- **Processing:** may the team parse, index and extract facts locally?
- **Quotation:** may Copilot display short excerpts and cite pages?
- **Redistribution:** may the team publish the full document or binary?

Public download access answers none of them. Human review must record the basis
for each permission before a source leaves `pending`. Until then:

- Full commercial PDFs stay outside Git.
- Only factual summaries and URL/hash metadata are committed.
- The repository does not grant a fair-dealing, fair-use or open-evaluation
  licence by assertion.

The Libre Solar BMS C1 sample remains the only explicitly licensed text sample
(CC BY-SA 4.0, commit `7c2dcc1c4f266ce2a977c386ddaa4319f1ed1095`).

## 8. Remaining work and dependencies

1. Verify official document URLs and hashes for Kipor KDE6700TA and Cummins C55D5.
2. Obtain a complete DDJ 750 document and confirm the Deye page locator.
3. Human review of processing, quotation and redistribution rights for all 15 slots.
4. Human technical review of the candidate specifications and safety content.
5. Backend agreement on product ID type, specification storage and pre-retrieval
   authorization before any catalogue or retrieval integration.
