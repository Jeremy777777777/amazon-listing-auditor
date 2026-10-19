from __future__ import annotations

import re
from html import unescape

from .models import Evidence, Finding, ListingRecord
from .catalog_policy import identify_oem, warranty
from .customization import capacity_values, option_groups, options


REFERENCE = "references/compliance-audit-rules.md"
SELLER_BRANDS = {"megapc": "MegaPC", "jtd": "J-Tech Digital"}


def _finding(rule_id: str, field: str, expected: str, observed: str, severity: str, reason: str, source: str, correction: str) -> Finding:
    return Finding(field, expected, observed, severity, reason, source, "", correction, rule_id, REFERENCE)


def check_compliance(record: ListingRecord, evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    title = evidence.title.strip()
    seller_brand = SELLER_BRANDS.get(record.seller.casefold(), "" if record.seller.casefold() in {"", "manual", "unknown"} else record.seller.strip())
    if not seller_brand:
        if title.casefold().startswith("megapc"):
            seller_brand = "MegaPC"
        elif title.casefold().startswith(("j-tech digital", "jtd")):
            seller_brand = "J-Tech Digital"
    source = evidence.source or "Amazon listing"

    if seller_brand and not title.casefold().startswith(seller_brand.casefold()):
        findings.append(_finding("CPC-TITLE-001", "compliance_title_brand", f"Title starts with {seller_brand}", title, "CRITICAL", "Customized computers must be listed under the seller's own brand, not the OEM brand.", source, f"Start the title with {seller_brand} and reference the OEM only as the base model."))
    if not re.search(r"\bcustom(?:ized)?\b", title, re.I):
        findings.append(_finding("CPC-TITLE-002", "compliance_title_custom", "Custom or Customized in title", title, "HIGH", "The title does not disclose that this is a customized computer.", source, "Add Custom or Customized to the seller-brand-first title."))
    if seller_brand == "MegaPC":
        if not title.startswith("MegaPC Custom "):
            findings.append(_finding("CPC-TITLE-007", "compliance_title_catalog_prefix", "MegaPC Custom ", title, "HIGH", "The creation project's confirmed title prefix is MegaPC Custom.", source, "Use MegaPC Custom followed by the product type and Created Using OEM model."))
        if not title.endswith("Win 11 Pro"):
            findings.append(_finding("CPC-TITLE-008", "compliance_title_catalog_os", "Win 11 Pro title ending", title, "HIGH", "The confirmed sold OS is Windows 11 Pro; the title must use the catalog ending.", source, "End the title with Win 11 Pro; OEM factory Home does not override seller policy."))
    if not re.search(r"\bcreated\s+using\b", title, re.I):
        findings.append(_finding("CPC-TITLE-003", "compliance_title_oem_reference", "Created Using [OEM model]", title, "REVIEW", "The title does not clearly separate the seller brand from the OEM base model.", source, "Use a seller-brand-first title and identify the base model with Created Using."))
    if not re.search(r"\b\d{1,3}\s*GB\b[^\n,]{0,35}\b(?:DDR\w*|LPDDR\w*|RAM|Memory)\b", title, re.I):
        findings.append(_finding("CPC-TITLE-004", "compliance_title_ram", "Confirmed base RAM or observed Customize RAM choices in title", title, "HIGH", "The title does not state a supported RAM configuration.", source, "Use confirmed base RAM or the actual unit-qualified Customize choices; do not invent capacities."))
    if not re.search(r"\b\d+(?:\.\d+)?\s*(?:GB|TB)\b[^\n,]{0,25}\b(?:SSD|HDD|NVMe|Storage)\b", title, re.I):
        findings.append(_finding("CPC-TITLE-005", "compliance_title_storage", "Confirmed base storage or observed Customize storage choices in title", title, "HIGH", "The title does not state a supported internal storage configuration.", source, "Use confirmed base storage or actual unit-qualified Customize choices; preserve their exact labels."))
    if len(title) > 200:
        findings.append(_finding("CPC-TITLE-006", "compliance_title_length", "Title at or below approximately 200 characters", str(len(title)), "HIGH", "The title exceeds the internal Amazon Custom PC length limit.", source, "Shorten the title without removing seller brand, customization identity, OEM model, RAM, or storage."))

    first_bullet = evidence.bullets[0].strip() if evidence.bullets else ""
    if seller_brand == "MegaPC":
        oem = identify_oem(record.product_name or title)
        if oem:
            required_warranty = warranty(oem)
            collapse = lambda text: " ".join(unescape(re.sub(r"<[^>]*>", " ", text)).split())
            if collapse(first_bullet) != required_warranty:
                findings.append(_finding("CPC-WARRANTY-004", "compliance_bullet_warranty_exact", required_warranty, first_bullet, "HIGH", "Bullet 1 must exactly match the seller-confirmed full warranty paragraph, including the seal-opening sentence.", source, required_warranty))
            description = collapse(evidence.description)
            if not description.endswith("Warranty and Disclosure " + required_warranty):
                findings.append(_finding("CPC-WARRANTY-005", "compliance_description_warranty_exact", required_warranty, evidence.description, "HIGH", "Description must end with Warranty and Disclosure followed by the identical fixed warranty paragraph.", source, required_warranty))
            warranty_attribute = next((v for k, v in evidence.details.items() if k.casefold() == 'warranty description'), '')
            if collapse(warranty_attribute) != required_warranty:
                findings.append(_finding("CPC-WARRANTY-006", "compliance_attribute_warranty_exact", required_warranty, warranty_attribute or "Not captured", "HIGH" if warranty_attribute else "REVIEW", "Warranty Description must use the same fixed paragraph; missing capture is not a confirmed attribute error.", source, required_warranty))
        if len(evidence.bullets) != 5:
            findings.append(_finding("STYLE-BULLET-002", "compliance_bullet_count", "Five bullet paragraphs, warranty first", str(len(evidence.bullets)), "REVIEW", "The creation project's default copy structure contains five bullets.", source, "Use the fixed warranty as bullet 1 and four concise benefit-led bullets."))
    for section, content in [("Title", title), ("Bullet Points", " ".join(evidence.bullets)), ("Product Description", evidence.description)]:
        for values, kind in option_groups(content):
            offered = options(evidence, kind) if kind else options(evidence,'ram') + options(evidence,'storage')
            allowed = capacity_values(' '.join(offered))
            if not allowed or not values <= allowed:
                findings.append(_finding("CPC-BASE-001", "compliance_base_configuration", "Capacity choices match the observed, unit-qualified Customize controls", f"{section}: {content}", "HIGH" if allowed else "REVIEW", "Capacity lists may describe actual sold upgrades under the user's latest instruction. These choices conflict with captured controls or lack matching option evidence.", source, "Use only captured Customize option labels; keep factory/base values separate. Put source gaps in audit notes, not buyer-facing placeholders."))
                break
    if not first_bullet or not re.search(r"\bwarrant(?:y|ies)\b", first_bullet, re.I):
        findings.append(_finding("CPC-WARRANTY-001", "compliance_bullet_1_warranty", "Warranty disclosure in bullet point #1", first_bullet or "No readable first bullet", "HIGH", "Amazon Custom PC rules require the warranty disclosure in the first bullet.", source, "Make bullet point #1 a clear OEM-warranty and seller-upgrade-warranty disclosure."))
    else:
        if not re.search(r"\b(?:OEM|original|manufacturer)\b", first_bullet, re.I):
            findings.append(_finding("CPC-WARRANTY-002", "compliance_oem_warranty", "OEM warranty status", first_bullet, "HIGH", "The first bullet does not clearly state whether OEM warranty coverage still applies.", source, "State whether the original manufacturer warranty is valid or void after customization."))
        if seller_brand and not (re.search(re.escape(seller_brand), first_bullet, re.I) and re.search(r"\bwarrant(?:y|ies)\b", first_bullet, re.I)):
            findings.append(_finding("CPC-WARRANTY-003", "compliance_seller_warranty", f"{seller_brand} upgrade warranty", first_bullet, "HIGH", "The first bullet does not clearly state the seller warranty for upgraded components.", source, f"State the actual {seller_brand} warranty for upgraded RAM and/or storage."))

    text = evidence.text
    # Check explicit positive claims, not nearby keywords in "no software changes" disclosures.
    prohibited_customization = re.search(
        r"\b(?:customiz(?:ed|e)|upgrad(?:ed|e)|modif(?:ied|y))\s+(?:the\s+)?(?:CPU|processor|GPU|graphics|display|screen|battery)\b|"
        r"\b(?:CPU|processor|GPU|graphics|display|screen|battery)\s+(?:(?:is|was|are|were)\s+)?(?:customized|upgraded|modified)\b|"
        r"\b(?:Windows(?:\s+11\s+(?:Pro|Home))?|OS|software)\s+(?:(?:is|was)\s+)?customized\b|"
        r"\bcustomized\s+(?:Windows|OS|software)\b", text, re.I)
    if prohibited_customization:
        findings.append(_finding("CPC-SCOPE-001", "compliance_customization_scope", "Hardware customization is limited to RAM/storage; final Windows 11 Pro is fixed", prohibited_customization.group(0), "CRITICAL", "The claim conflicts with the creation project's hardware/customization scope.", source, "Correct the hardware claim. Describe Windows 11 Pro as the fixed sold OS, not buyer-selectable software customization."))
    if re.search(r"\bcustom(?:ized|ization)?\b", text, re.I) and not (re.search(r"\b(?:RAM|memory)\b", text, re.I) and re.search(r"\b(?:SSD|HDD|storage)\b", text, re.I)):
        findings.append(_finding("CPC-SCOPE-002", "compliance_customization_disclosure", "Documented supported RAM/storage customization scope", "RAM and/or storage disclosure is incomplete", "HIGH", "The listing does not clearly document both allowed hardware customization categories.", source, "Describe supported base hardware and observed upgrade choices separately; other hardware remains factory configured and Windows 11 Pro is fixed seller policy."))

    absolute = re.search(r"\b(?:guaranteed|100%\s+(?:safe|compatible|reliable)|best\s+(?:in|on)\s+the\s+market)\b", text, re.I)
    if absolute:
        findings.append(_finding("CPC-CLAIM-001", "compliance_absolute_claim", "Documented and supportable claim", absolute.group(0), "REVIEW", "An absolute or guaranteed claim requires substantiation and compliance review.", source, "Remove the claim or replace it with a qualified, verifiable factual statement."))
    return findings
