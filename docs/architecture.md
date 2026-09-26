# Architecture

## Pipeline

```text
Google Sheet / CSV / Manual input
              |
              v
completed listing selector ----> internal ID + expected product + ASIN
              |                                  |
              v                                  v
Amazon title, description,              ERP GraphQL or export
bullets and Product information                  |
              |                                  |
              +------------+---------------------+
                           v
          deterministic identity, specification
                 and compliance review rules
                           |
                           v
        JSON + CSV + Markdown + Excel issue output
```

## Source priority

1. Internal input record and ERP product mapped by exact internal ID.
2. Amazon variation-specific title, bullets, description and Product information.
3. Manufacturer evidence and approved policy references when available.

Conflicts remain visible instead of being collapsed into one score. Missing evidence is never treated as a successful match.

## Finding types

- `CRITICAL`: wrong manufacturer or model/product family.
- `HIGH`: explicit contradiction on a buying attribute or between Amazon and ERP.
- `REVIEW`: insufficient evidence, ERP lookup failure, source conflict, or compliance claim requiring substantiation.
- `PASS`: no mismatch found in the evidence that was available. PASS records are excluded from the Excel problem list.

## ERP adapter

The adapter queries `productTableFilterable` by exact `sku` and normalizes the product and specification fields. Authentication comes only from environment variables. A CSV / JSON export adapter provides a local and auditable fallback.

## Excel review workflow

The first worksheet is the action list and contains findings only. Each row is one issue, so one product can have several rows. The editable review fields are highlighted and include a status dropdown. A second worksheet preserves source evidence for the products that have findings.

GitHub Actions always uploads the Excel workbook together with machine-readable JSON/CSV and a Markdown summary, even when the audit command returns a mismatch exit code.
