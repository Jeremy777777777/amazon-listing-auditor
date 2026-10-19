# Listing Copy Correction Style

Adapted for audit corrections from:

- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/listing-style-guide.md
- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/compliance-rules.md

Suggested corrections are drafts for human review, not permission to invent missing facts. The auditor uses canonical Input/ERP facts when available and prints `[[VERIFY ...]]` for unresolved required content.

## Title

Use this order: seller brand, `Customized`, product type, `Created Using` plus OEM model, relevant differentiator, CPU, actual RAM options, actual SSD options, and verified OS. Keep the result readable and at or below approximately 200 characters. Never present the OEM as the customized listing brand.

## Bullet points

Bullet 1 is the verified warranty disclosure. Remaining bullets follow product overview/customization identity, processor, memory and storage, display or design, connectivity/expansion, and complete-use setup. Each bullet uses a short heading followed by specific facts and buyer value. Remove an unsupported theme instead of fabricating content.

## Product description

User-confirmed output format (2026-10-19): save literal HTML text in the Product Description recommendation cell. Wrap the opening identity in `<p><strong>...</strong></p>`. Wrap every following section in `<p><strong>Heading</strong><br>Body</p>`, separating HTML paragraphs with a blank line for readability. Do not output Markdown `**`, heading backslashes, or plain newlines as a substitute for HTML tags. Excel stores the HTML as text; a compatible HTML renderer applies the bold headings and paragraph/line breaks.

Escape text content using HTML entities (`&amp;`, `&quot;`, `&lt;`, `&gt;`) without escaping the generated structural tags or treating source text as markup. Use 5–8 capability headings, cover only verified product facts, distinguish factory specifications from RAM/storage changes, treat the OS as fixed rather than customized, and place `Warranty` last. Title, bullets, description, attributes, and image copy must remain consistent. This is a formatting change, not authorization to invent or verify missing product facts. Captured Amazon content remains unchanged in the original Value/source cells; the recommendation row contains the generated HTML.

No suggestion containing `[[VERIFY ...]]` is publication-ready.
