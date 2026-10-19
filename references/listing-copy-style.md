# Listing Copy Correction Style

## Content-policy sync — 2026-10-19

The user requested consistency with `create-custom-pc-listing` commit `e2910c8fa93370105d53bcb49d3fc17f12b0ee1a`: [confirmed seller policy](https://github.com/Jeremy777777777/create-custom-pc-listing/blob/e2910c8fa93370105d53bcb49d3fc17f12b0ee1a/references/confirmed-catalog-defaults.md) and [writing guide](https://github.com/Jeremy777777777/create-custom-pc-listing/blob/e2910c8fa93370105d53bcb49d3fc17f12b0ee1a/references/listing-style-guide.md). Later explicit instructions in this chat override two points for the auditor: use `<p>/<strong>/<br>` HTML and describe the actual purchasable Customize capacities alongside supported base hardware facts. Keep the rest of the shared wording and warranty policy consistent.

Keep OEM factory facts, page/base attributes, available upgrade options and a customer's selected configuration separate. Allowed option lists come from an ASIN-matched, dated capture of the actual Customize controls with explicit units. Title/description lists and platform maximums cannot establish available choices. Never treat the first/lowest choice or an unchecked radio option as a factory/default configuration. Preserve labels: **0.5TB is not 512GB**. Do not invent camera/stand/ports/accessories. Final MegaPC sold OS is Windows 11 Pro (`USER_CONFIRMED_CATALOG_POLICY`); OEM factory Home does not override it. Do not imply included Office, Microsoft 365 or paid Copilot subscriptions. Hardware changes are limited to supported RAM/storage changes; other hardware remains factory configured. Do not claim all software remains factory configured.

Use this identical warranty paragraph in Bullet 1, the final Description section headed **Warranty and Disclosure**, and Warranty Description. Replace only `[OEM brand]` with the mapped OEM; preserve all other words and punctuation:

> MegaPC provides a 1-year limited warranty on the upgraded RAM and SSD components. The original [OEM brand] manufacturer warranty remains valid on all remaining factory components, so you are covered on both the base machine and our upgrades. The original seal has been opened solely for upgrading purposes.

This declaration is seller-confirmed policy, not independent OEM coverage or Amazon approval. Do not reopen per-product wording approval; keep manual checks for actual coverage, seal-opening accuracy, license/activation and marketplace eligibility. Unknown OEM/seller warranty policy withholds copy until mapped; do not output placeholders as a finished replacement. Do not rename JTD-branded listings or assume a MegaPC warranty for them.

Adapted for audit corrections from:

- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/listing-style-guide.md
- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/compliance-rules.md

Copy recommendations must be complete buyer-facing text. Omit unconfirmed optional facts or capacity numbers and record source gaps separately as COPY-SOURCE review findings. Never put `[[VERIFY ...]]`, editorial instructions, missing-source commentary or bracketed TODOs inside finished copy. Missing data is not PASS. Internal canonical fact processing may retain diagnostics, but those markers must not appear in the copy-ready view or native recommended copy cells.

## Title

Use `MegaPC Custom [Product Type], Created Using [OEM Model], [CPU], [observed RAM choices or confirmed base RAM], [observed SSD choices or confirmed base storage], Win 11 Pro`. Target at most 200 characters. Prefer actual purchasable option labels when captured; unknown capacities are omitted, not guessed. Never present the OEM as the customized listing brand.

## Bullet points

Store exactly five paragraphs in one complete Bullet Point cell, separated by one blank line. Bullet 1 is the exact fixed paragraph above, without a heading/number. Other paragraphs cover product overview, supported processor/platform, actual Customize choices (or confirmed base capacities), and supported display/connectivity/fixed OS. Offer capacity choices as choices, not installed/factory claims. Omit unsupported facts rather than filling the cell with review instructions.

## Product description

User-confirmed output format (2026-10-19): save literal HTML text in the Product Description recommendation cell. Wrap the opening identity in `<p><strong>...</strong></p>`. Wrap every following section in `<p><strong>Heading</strong><br>Body</p>`, separating HTML paragraphs with a blank line for readability. Do not output Markdown `**`, heading backslashes, or plain newlines as a substitute for HTML tags. Excel stores the HTML as text; a compatible HTML renderer applies the bold headings and paragraph/line breaks.

Escape text (`&amp;`, `&quot;`, `&lt;`, `&gt;`) without escaping structural tags or treating source text as trusted markup. Use relevant supported capability headings and actual observed upgrade choices; put **Warranty and Disclosure** last with the complete fixed paragraph and nothing after it. Opening identity uses `MegaPC Custom`. Keep capacity labels consistent across title, bullets and description. Captured Amazon content remains unchanged; the recommendation row and 可复制文案 view contain complete HTML in a single cell, never split across continuation rows for copying.

The copy-ready view contains no VERIFY placeholders; unresolved audit/eligibility items remain separate from buyer-facing text. This view does not mark the overall product audit PASS.

The [VA-215 Customize snapshot](../examples/VA-215-customization.json) records observed RAM **16GB/32GB/64GB** and SSD **0.5TB/1TB/2TB/4TB**. The product page's separate 8GB attribute is not a purchasable radio choice. No option was selected; factory RAM/SSD remain independently unverified. The snapshot is dated evidence, not an automatically fresh capture. The copyable [HTML example](../examples/VA-215-product-description.html) uses these actual choices and omits unsupported optional hardware.
