# Listing audit rules — v0.8

Adapted from create-custom-pc-listing at the commit in `generation-policy-lock.json`; see `docs/generation-sync.md`. These are internal QA rules, not independently verified current Amazon policy. Publication eligibility requires applicable current account/category guidance.

| Rule | Check | Severity |
| --- | --- | --- |
| CPC-TITLE-001–006 | Seller identity, Custom disclosure, Created Using, installed RAM/storage, <=200 characters | CRITICAL/HIGH/REVIEW |
| CPC-WARRANTY-001–003 | Warranty first; OEM and seller coverage identified | HIGH |
| CPC-SCOPE-001 | Explicit CPU/GPU/display/battery/software customization claims or selectable software; fixed MegaPC Pro is distinct | CRITICAL |
| CPC-SCOPE-002 | RAM/storage scope documented | HIGH |
| CPC-CLAIM-001 | Absolute claim requires substantiation | REVIEW |
| CAT-TITLE-001 | MegaPC exact `MegaPC Custom ` prefix | HIGH |
| CAT-OS-001 | MegaPC title ends with `Win 11 Pro` | HIGH |
| CAT-BULLET-001 | MegaPC five bullets | REVIEW |
| CAT-BASE-001 | MegaPC sold base capacities; no selectable tiers | HIGH |
| CAT-WARRANTY-001 | Fixed paragraph at all three locations; verified OEM substituted | HIGH when contradictory; REVIEW when unavailable |
| CAT-PUBLICATION-001 | Seller manual coverage, seal/customization, licensing and Amazon eligibility check | REVIEW |
| IDENTITY-CROSS-FIELD-001 | Title versus each section OEM/family | CRITICAL |
| SPEC-CROSS-FIELD-001 | Title versus all CPU/display/RAM/storage values in bullets and description | HIGH |

CAT rules are MegaPC-only, including seller inferred from a URL-only title. Fixed warranty is USER_CONFIRMED_CATALOG_POLICY, not OEM approval. It must not be silently rewritten, or used to infer that a specific unit was actually upgraded. Missing warranty attributes remain REVIEW. The generic title capacity checks do not prove those capacities are actually installed.

Keep source conflicts visible. `osScope: factory` in an ERP export explicitly identifies factory OS and excludes it from sold-OS comparison; unscoped ERP OS is not silently overridden. Product names are input clues, not complete hardware ledgers. Duplicate exact internal IDs in ERP exports are ambiguous and cannot be resolved by taking the first row.

A correct title cannot hide conflicting section values. Numeric comparison is conservative and may require human clarification of factory/platform context. It is not a complete natural-language fact verifier. Model-family recognition and CPU patterns have finite coverage. No automatic FCC, license, serial or account eligibility assertion is made.
