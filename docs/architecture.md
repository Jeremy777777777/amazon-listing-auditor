# Architecture

## Pipeline

```text
Google Sheet / CSV / Manual input / Amazon URL only
              |
              v
completed listing selector ----> internal ID + expected product + ASIN
              |                 |                         |
              v                 v                         v
Amazon text/spec fields   MAIN + PT01-PT08       ERP GraphQL or export
              |                 |                         |
              |         pixel checks + visual             |
              |          observation/OCR                  |
              +-----------------+-------------------------+
                                v
             identity, specification, compliance and
                    image-consistency rules
                           |
                           v
       style-aligned copy correction drafts when needed
                           |
                           v
        JSON + CSV + Markdown + Excel issue output
```

## Source priority

1. Internal input record and ERP product mapped by exact internal ID.
2. Amazon variation-specific title, bullets, description and Product information.
3. Manufacturer evidence and approved policy references when available.
4. Licensed image provenance plus OCR/vision or human visual observations.

Conflicts remain visible instead of being collapsed into one score. Missing evidence is never treated as a successful match.

URL-only inputs receive an explicit `INPUT-BASELINE-001` review finding. They can complete page consistency, compliance and image checks, but cannot receive a full product-match confirmation until an internal ID and canonical product record are mapped.

Before baseline/ERP comparison, `IDENTITY-CROSS-FIELD-001` independently compares the Title identity anchor with Bullet Points, Product Description, and Product information. A foreign OEM or conflicting recognized model family is `CRITICAL`, including in URL-only mode. Evidence remains field-separated so a correct title cannot mask an incorrect description during whole-page aggregation. Script/style/template content is excluded from Product Description evidence.

## Finding types

- `CRITICAL`: wrong manufacturer or model/product family.
- `HIGH`: explicit contradiction on a buying attribute or between Amazon and ERP.
- `REVIEW`: insufficient evidence, ERP lookup failure, source conflict, or compliance claim requiring substantiation.
- `PASS`: no mismatch found in the evidence that was available. PASS records are excluded from the Excel problem list.

## ERP adapter

The adapter queries `productTableFilterable` by exact `sku` and normalizes the product and specification fields. Authentication comes only from environment variables. A CSV / JSON export adapter provides a local and auditable fallback.

## Excel review workflow

The workbook loads the pinned `create-custom-pc-listing` XLSX from package resources. The first sheet, 可复制文案, stores complete title, five-paragraph bullet copy and HTML description in individual column-B cells without placeholders or editorial instructions. Its C column contains source/review notes. The 审核修改 reading view groups findings by field; links navigate to the original template. Product Details, Offer and Safety&Compliance retain row-1 labels and row-2 definitions. Row 3 holds captured content and turns red on mapped issues; rows 4/5 hold status/source; rows 6/7 hold complete recommendations/reasons. The source workbook is never overwritten.

Missing capture remains blank with NOT_CAPTURED. CAPTURED_NOT_FLAGGED means only that the current rules did not flag the captured value; it is not VERIFIED or PASS. Offer SKU is not inferred from the internal ID. Multiple ASINs retain separate full template groups. Unmapped findings remain visible, image findings have a separate review tab, and complete Bullet Points and unavailable-source states are preserved in Source Evidence. Long text is split only in the reading view; original template/evidence strings remain intact. Review status and final notes are editable. CSV/JSON retain the individual finding model; this workbook is not a marketplace upload artifact.

The report layer groups results by exact internal ID and writes one product package per `VL-XXXX` folder. Each package contains Excel, JSON, CSV, Markdown, and a dedicated source-evidence JSON file. Multiple seller listings mapped to the same internal ID remain together. An unmapped URL uses `UNMAPPED-<ASIN>` until an internal ID is supplied.

GitHub Actions always uploads the Excel workbook together with machine-readable JSON/CSV and a Markdown summary, even when the audit command returns a mismatch exit code.

## Copy correction boundary

Listings with actionable text/specification findings receive complete Title, Bullet Points and HTML Description replacements. Under the latest user instruction, supported base facts are combined with actual observed, ASIN-scoped Customize upgrade choices. Omit unknown optional facts/numbers; keep source gaps in separate COPY-SOURCE review findings rather than buyer-facing VERIFY placeholders. Core identity and warranty gaps withhold copy. This view does not mark the overall audit PASS.

`Evidence.customization` and `--customization-evidence` preserve timestamp/source, ASIN, unit-qualified options and distinct base/selected facts. Do not infer factory/default values from the first/unchecked option, the old title or a platform maximum. In the VA-215 capture, the storage label is exactly 0.5TB, not 512GB. Unmatched option lists are HIGH when they contradict captured controls and REVIEW when matching evidence is missing. The CLI and Actions accept scoped evidence; they do not silently interact with terms-bearing Customize dialogs.

## Image audit boundary

The deterministic layer checks file format, dimensions, aspect ratio, MAIN white border/framing and near-duplicates. Semantic observations cover product identity, visible ports/accessories, image text, prohibited badges or marketplace content, claims and licensed provenance. If semantic observations are unavailable, the result remains `REVIEW`; technical image checks alone cannot establish a full image pass.
