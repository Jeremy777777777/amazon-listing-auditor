# Generation alignment — 2026-10-14

Auditor v0.8 adapts create-custom-pc-listing commit `ae2dc3933bd220daf1cb00e300396de27388eff9`. `references/generation-policy-lock.json` stores seven monitored source hashes. Old production receipts are not current policy.

Implemented: MegaPC fixed base/title/OS/warranty/five-bullet rules, HTML correction drafts, per-section specification conflicts, ambiguous ERP-export rejection, current per-slot image hash/coverage/visual-completion checks, non-square size policy, computer-only observations, physical-port review and canonical semantic overlap. JTD remains independently scoped. Reports retain existing product folders and reviewer columns; Source Evidence now includes bullets.

Efficiency: one ERP lookup per internal ID per run, shared across MegaPC/JTD listings. Actions Sheet-mode ERP no longer requires a separate manual internal ID; each row supplies its own ID.

## Future drift check

After required local preflight, fetch the generation repository separately, then run:

```powershell
& 'E:\Coding\envs\amazon-listing-auditor-py311\python.exe' scripts/check_policy_sync.py --generation-repo ../repo-live
```

This read-only command checks monitored contents at local `origin/main`. It does not fetch, install, update rules or establish remote freshness. Changed/missing files return exit 1. Review implications and regressions before refreshing the lock. Changes outside the seven files are not covered.

## Boundaries

Do not bulk-import product-facts.json as a complete hardware ledger: the inspected VL-1249 record explicitly contains only policy resolutions and retains a historical size default superseded by active references. Product-specific ledgers, FCC and serial-derived OEM BOMs need field-level provenance adapters before automatic reuse. This update does not implement those integrations.

Scraped descriptions may contain rendered text; check visible warranty content there. HTML structure applies to generated correction drafts, not reconstructed workbook markup.

CAT-PUBLICATION-001 intentionally keeps otherwise compliant MegaPC results in REVIEW. No input contract currently clears manual OEM coverage, actual seal/customization, licensing or Amazon account checks. Seller policy alone cannot clear those checks. All corrections remain human-review drafts.

Pixel checks and supplied observations do not replace actual visual inspection, schema-3 production logo QA, style approval, full-gallery production QA, remote delivery or Amazon eligibility. Offline regression results do not imply a live Amazon audit or current external-policy validation.
