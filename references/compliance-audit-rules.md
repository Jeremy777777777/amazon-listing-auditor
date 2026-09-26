# Customized Computer Compliance Audit Rules

Adapted for audit use from the public `create-custom-pc-listing` references:

- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/compliance-rules.md
- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/listing-style-guide.md

Amazon's current policy and Seller Central controls override this repository. A `REVIEW` result requests evidence or human judgment; it is not a legal conclusion.

## Automated listing rules

| Rule ID | Requirement | Default severity |
| --- | --- | --- |
| `CPC-TITLE-001` | Title starts with the seller's own brand, not the OEM brand. | CRITICAL |
| `CPC-TITLE-002` | Title contains `Custom` or `Customized`. | HIGH |
| `CPC-TITLE-003` | OEM model is separated from seller identity using `Created Using`. | REVIEW |
| `CPC-TITLE-004` | Title contains only the RAM tiers actually offered. | HIGH |
| `CPC-TITLE-005` | Title contains only the storage tiers actually offered. | HIGH |
| `CPC-TITLE-006` | Title remains at or below the internal approximately 200-character limit. | HIGH |
| `CPC-WARRANTY-001` | Bullet point #1 is the warranty disclosure. | HIGH |
| `CPC-WARRANTY-002` | Bullet #1 states whether OEM/original manufacturer coverage applies. | HIGH |
| `CPC-WARRANTY-003` | Bullet #1 states the seller warranty on upgraded RAM/storage. | HIGH |
| `CPC-SCOPE-001` | Only RAM and storage may be presented as seller customizations; software customization is prohibited. | CRITICAL |
| `CPC-SCOPE-002` | The actual RAM/storage customization scope is documented. | HIGH |
| `CPC-CLAIM-001` | Absolute or guaranteed claims require substantiation. | REVIEW |

## Required manual/source controls

The product page alone normally cannot prove that the ASIN was created through Amazon Custom, is MFN, uses a new ASIN/UPC, includes shipment documentation, or uses original/licensed copy and imagery. Keep these controls in human review until Seller Central or internal evidence is supplied.

Do not silently choose between Sheet, ERP, Amazon, image text, and OEM sources. Preserve conflicts field by field and require human confirmation when the sources cannot be reconciled.
