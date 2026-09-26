# Product Image Audit Rules

Adapted for audit use from:

- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/image-spec.md
- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/amazon-product-image-workflow.md

The auditor separates deterministic file/pixel checks from semantic visual review. Pixel checks must not claim that an image shows the correct product, ports, accessories, claims, or licensed source.

## Deterministic checks

| Rule ID | Requirement |
| --- | --- |
| `IMG-GALLERY-001/002` | Capture the gallery; internal standard is `MAIN` plus `PT01`–`PT08`. |
| `IMG-TECH-001` | JPEG, TIFF, PNG, or non-animated GIF. |
| `IMG-TECH-002` | Longest side is 500–10,000 px. |
| `IMG-TECH-003` | At least 1,000 px on the longest side for zoom. |
| `IMG-TECH-004` | Internal production gallery uses a 1:1 square canvas. |
| `IMG-MAIN-001` | MAIN uses a pure-white background. |
| `IMG-MAIN-002` | Complete product fills approximately 85% of MAIN without cropping. |
| `IMG-GALLERY-003` | Gallery slots are not near-duplicates. |

## Semantic visual checks

`image-observations.json` supplies OCR/vision or human observations grouped under `listings.<ASIN>.images`. The auditor also accepts a single-listing top-level `images` array. The auditor checks:

- MAIN has no added text, graphics, border, badge, watermark, or logo overlay.
- Image OEM and product identity match the mapped input/ERP product.
- Image text claims are supported by the mapped product evidence.
- No reviews, star ratings, testimonials, prices, coupons, shipping claims, Amazon/Prime/Alexa marks, Amazon badges, or seller contact information.
- Ports and included accessories are shown only when verified for the exact shipped configuration.
- Images do not mix another size, color, generation, chassis, or model.
- Asset provenance documents authorized OEM media, seller-owned photography, or original infographics using licensed assets.
- Photorealistic people generated entirely by AI carry the required production metadata when applicable.

When no semantic observations are supplied, the auditor emits `IMG-VISUAL-001` as `REVIEW`; technical success alone is not a full image PASS.
