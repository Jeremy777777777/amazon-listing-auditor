# Listing correction style — v0.8

Adapted on 2026-10-14 from the commit and file hashes in `generation-policy-lock.json`.

## MegaPC

- Exact prefix `MegaPC Custom`, then product type, `Created Using` plus verified OEM model, CPU, installed base RAM/internal storage; end with `Win 11 Pro`. Target <=200 characters. Do not suggest selectable tiers, platform maximums or external storage as installed capacity.
- Exactly five paragraphs separated by one blank line. First paragraph is the complete fixed warranty, without a heading or numbering. Remaining paragraphs cover purchase reason, platform performance, installed memory/storage, and experience/connectivity.
- Description correction is a single literal HTML string: `<strong>` identity/headings, `<br/>` after headings, `<br/><br/>` between sections. End at the exact fixed paragraph in `Warranty and Disclosure`; no trailing breaks.
- Fixed sold Windows 11 Pro is seller policy, distinct from factory Home; do not claim all software remains factory configured. No Office/Microsoft 365/paid Copilot entitlement is implied.
- Verified OEM name is the only substitution in the warranty template in `src/listing_auditor/policy.py`. Preserve its wording in bullet 1, final description section and Warranty Description. Coverage, licensing and actual seal-opening remain manual publication checks.

## Evidence boundary

Suggestions are review drafts. Conflicting Input/ERP/page facts and ambiguous capacities retain `[[VERIFY ...]]`. A placeholder is never ready to publish. ERP data is a mapped internal source, not automatic exact-SKU OEM verification. Confirm actual modifications, including soldered memory, before using copy.

JTD retains its separate seller-brand-first correction style and unresolved warranty placeholders; MegaPC-specific catalog assertions do not apply to JTD. The stored HTML format applies to generated correction drafts, not an assumption that scraped Amazon content retains source HTML or that every channel renders it.
