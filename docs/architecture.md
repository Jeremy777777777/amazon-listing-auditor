# Architecture

## Pipeline

```text
Google Sheet / CSV
        |
        v
completed listing selector ----> one record per seller + ASIN
        |
        v
expected fact extractor <------- official manufacturer evidence (planned)
        |
        +-------------------+
                            v
Amazon evidence ------> deterministic comparison engine
                            |
                            v
                 JSON + CSV + Markdown report
```

## Guardrails

- Product identity (`brand`, `model`) is checked before detailed specs.
- Missing evidence is never treated as a successful match.
- Conflicting facts are reported individually instead of collapsed into one AI score.
- A future LLM/research layer may extract candidate facts, but deterministic rules and cited evidence make the final decision reviewable.
- Seller-customizable fields such as RAM and SSD should be checked against the selected variation, not only the base manufacturer configuration.

## Sheet mapping

The current tracker uses row 3 as headers. For each row, the selector emits:

- `MegaPC Customized Listing` when its status is `Completed`, using the adjacent `Link` column.
- `JTD Customized Listing` when its status is `Completed`, using its adjacent `Link` column.

Duplicate header names are resolved by position, not by dictionary key.

## Risk levels

- `CRITICAL`: wrong brand or model/product family.
- `HIGH`: explicit contradiction on a key buying attribute.
- `REVIEW`: page unavailable, evidence missing, or a fact cannot be resolved safely.
- `PASS`: evidence supports all facts that were available for comparison.

