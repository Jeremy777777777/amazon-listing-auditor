# Listing Copy Correction Style

## Content-policy sync — 2026-10-19

The user explicitly requested consistency with `create-custom-pc-listing` commit `e2910c8fa93370105d53bcb49d3fc17f12b0ee1a`: [confirmed seller policy](https://github.com/Jeremy777777777/create-custom-pc-listing/blob/e2910c8fa93370105d53bcb49d3fc17f12b0ee1a/references/confirmed-catalog-defaults.md) and [writing guide](https://github.com/Jeremy777777777/create-custom-pc-listing/blob/e2910c8fa93370105d53bcb49d3fc17f12b0ee1a/references/listing-style-guide.md). The same day's explicit `<p>/<strong>/<br>` format overrides the source project's older break-tag layout for this auditor; the content policy stays consistent.

Describe one installed base configuration. Never list selectable capacities, treat platform maximums as installed, or invent optional camera/stand/ports/accessories. Missing or conflicting capacities stay `[[VERIFY BASE RAM]]` / `[[VERIFY BASE INTERNAL STORAGE]]` in automatic drafts. Do not select the first value from an option list. Final MegaPC sold OS is Windows 11 Pro (`USER_CONFIRMED_CATALOG_POLICY`); OEM factory Home does not override it. Do not imply included Office, Microsoft 365 or paid Copilot subscriptions. Hardware customization is limited to RAM/storage; other hardware remains factory configured. Do not claim all software remains factory configured.

Use this identical warranty paragraph in Bullet 1, the final Description section headed **Warranty and Disclosure**, and Warranty Description. Replace only `[OEM brand]` with the mapped OEM; preserve all other words and punctuation:

> MegaPC provides a 1-year limited warranty on the upgraded RAM and SSD components. The original [OEM brand] manufacturer warranty remains valid on all remaining factory components, so you are covered on both the base machine and our upgrades. The original seal has been opened solely for upgrading purposes.

This declaration is seller-confirmed policy, not independent OEM coverage or Amazon approval. Do not reopen per-product wording approval; keep manual checks for actual coverage, seal-opening accuracy, license/activation and marketplace eligibility. Unknown OEM stays an explicit VERIFY marker. Do not rename JTD-branded listings or assume a MegaPC warranty for them.

Adapted for audit corrections from:

- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/listing-style-guide.md
- https://github.com/Jeremy777777777/create-custom-pc-listing/blob/main/references/compliance-rules.md

Suggested corrections are drafts for human review, not permission to invent missing facts. The auditor uses canonical Input/ERP facts when available and prints `[[VERIFY ...]]` for unresolved required content.

## Title

Use `MegaPC Custom [Product Type], Created Using [OEM Model], [verified useful differentiator], [CPU], [installed base RAM], [installed base internal storage], Win 11 Pro`. Target at most 200 characters. Remove secondary features before identity, base capacities or the OS ending. Never list selectable tiers or present the OEM as the customized listing brand.

## Bullet points

Store exactly five paragraphs in the single Bullet Point cell, separated by one blank line. Bullet 1 is the exact fixed paragraph above, with no heading or numbering. The other four use concise benefit headings covering product overview, processor/platform, installed base memory/storage, and display/connectivity/fixed OS. Omit unsupported themes rather than inventing them.

## Product description

User-confirmed output format (2026-10-19): save literal HTML text in the Product Description recommendation cell. Wrap the opening identity in `<p><strong>...</strong></p>`. Wrap every following section in `<p><strong>Heading</strong><br>Body</p>`, separating HTML paragraphs with a blank line for readability. Do not output Markdown `**`, heading backslashes, or plain newlines as a substitute for HTML tags. Excel stores the HTML as text; a compatible HTML renderer applies the bold headings and paragraph/line breaks.

Escape text content using HTML entities (`&amp;`, `&quot;`, `&lt;`, `&gt;`) without escaping structural tags or treating source text as trusted markup. Use 5–8 relevant capability headings, keep only supported base facts, and put **Warranty and Disclosure** last with the exact complete fixed paragraph and nothing after it. Opening identity uses `MegaPC Custom`. Keep title, bullets, description, attributes and image copy consistent. Captured Amazon content remains unchanged in original Value/source cells; the recommendation row contains generated HTML.

No suggestion containing `[[VERIFY ...]]` is publication-ready.

The copyable [VA-215 example](../examples/VA-215-product-description.html) deliberately omits unconfirmed installed capacity numbers and optional hardware. It uses the supplied model/display/CPU/graphics/color/wireless baseline and confirmed seller policy; it does not establish missing inventory-level facts.
