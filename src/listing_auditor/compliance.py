from __future__ import annotations

import re

from .models import Evidence, Finding, ListingRecord
from .policy import seller_brand as resolve_seller, oem_brand, visible_text, warranty


REFERENCE = "references/compliance-audit-rules.md"


def _finding(rule_id: str, field: str, expected: str, observed: str, severity: str, reason: str, source: str, correction: str) -> Finding:
    return Finding(field, expected, observed, severity, reason, source, "", correction, rule_id, REFERENCE)


def check_compliance(record: ListingRecord, evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    title = evidence.title.strip()
    seller_brand = resolve_seller(record, evidence)
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
    if not re.search(r"\bcreated\s+using\b", title, re.I):
        findings.append(_finding("CPC-TITLE-003", "compliance_title_oem_reference", "Created Using [OEM model]", title, "REVIEW", "The title does not clearly separate the seller brand from the OEM base model.", source, "Use a seller-brand-first title and identify the base model with Created Using."))
    if not re.search(r"\b\d{1,3}\s*GB\b[^\n,]{0,35}\b(?:DDR\w*|LPDDR\w*|RAM|Memory)\b", title, re.I):
        findings.append(_finding("CPC-TITLE-004", "compliance_title_ram", "Actual installed RAM in title", title, "HIGH", "The customized-computer title does not show installed RAM.", source, "Add the actual installed base RAM."))
    if not re.search(r"\b\d+(?:\.\d+)?\s*(?:GB|TB)\b[^\n,]{0,25}\b(?:SSD|HDD|NVMe|Storage)\b", title, re.I):
        findings.append(_finding("CPC-TITLE-005", "compliance_title_storage", "Actual installed internal storage in title", title, "HIGH", "The customized-computer title does not show installed storage.", source, "Add the actual installed base internal storage."))
    if len(title) > 200:
        findings.append(_finding("CPC-TITLE-006", "compliance_title_length", "Title at or below approximately 200 characters", str(len(title)), "HIGH", "The title exceeds the internal Amazon Custom PC length limit.", source, "Shorten the title without removing seller brand, customization identity, OEM model, RAM, or storage."))

    first_bullet = evidence.bullets[0].strip() if evidence.bullets else ""
    if not first_bullet or not re.search(r"\bwarrant(?:y|ies)\b", first_bullet, re.I):
        findings.append(_finding("CPC-WARRANTY-001", "compliance_bullet_1_warranty", "Warranty disclosure in bullet point #1", first_bullet or "No readable first bullet", "HIGH", "Amazon Custom PC rules require the warranty disclosure in the first bullet.", source, "Make bullet point #1 a clear OEM-warranty and seller-upgrade-warranty disclosure."))
    else:
        if not re.search(r"\b(?:OEM|original|manufacturer)\b", first_bullet, re.I):
            findings.append(_finding("CPC-WARRANTY-002", "compliance_oem_warranty", "OEM warranty status", first_bullet, "HIGH", "The first bullet does not clearly state whether OEM warranty coverage still applies.", source, "State whether the original manufacturer warranty is valid or void after customization."))
        if seller_brand and not (re.search(re.escape(seller_brand), first_bullet, re.I) and re.search(r"\bwarrant(?:y|ies)\b", first_bullet, re.I)):
            findings.append(_finding("CPC-WARRANTY-003", "compliance_seller_warranty", f"{seller_brand} upgrade warranty", first_bullet, "HIGH", "The first bullet does not clearly state the seller warranty for upgraded components.", source, f"State the actual {seller_brand} warranty for upgraded RAM and/or storage."))

    if seller_brand == "MegaPC":
        findings.extend(_catalog_checks(record, evidence))

    text = visible_text(evidence.text)
    # The fixed, confirmed Pro configuration is distinct from selectable software.
    scope_text = re.sub(r"(?:Windows|Win)\s*11\s*Pro", "FIXED_SYSTEM", text, flags=re.I) if seller_brand == "MegaPC" else text
    prohibited_customization = re.search(
        r"\b(?:customized|upgraded|modified)\s+(?:(?:the|your|its)\s+)?(?:CPU|processor|GPU|graphics|display|screen|battery|Windows|OS|software)\b|"
        r"\b(?:CPU|processor|GPU|graphics|display|screen|battery|Windows|OS|software)\s+(?:(?:is|was|has been)\s+)?(?:customized|upgraded|modified)\b",
        scope_text, re.I,
    )
    if prohibited_customization:
        findings.append(_finding("CPC-SCOPE-001", "compliance_customization_scope", "Only RAM and storage are customized", prohibited_customization.group(0), "CRITICAL", "Amazon's Custom Computer Policy prohibits customization of software and components other than RAM/storage.", source, "Remove the prohibited customization claim and verify the physical product/configuration before publishing."))
    if seller_brand == "MegaPC" and re.search(r"\b(?:selectable|choose|optional)\b[^.;]{0,40}\b(?:Windows|OS|software)\b", text, re.I):
        findings.append(_finding("CPC-SCOPE-001", "compliance_customization_scope", "Fixed sold Windows 11 Pro, no selectable software customization", text, "CRITICAL", "The fixed seller OS policy does not authorize selectable software customization.", source, "Remove selectable software options and confirm the sold system."))
    if re.search(r"\bcustom(?:ized|ization)?\b", text, re.I) and not (re.search(r"\b(?:RAM|memory)\b", text, re.I) and re.search(r"\b(?:SSD|HDD|storage)\b", text, re.I)):
        findings.append(_finding("CPC-SCOPE-002", "compliance_customization_disclosure", "Documented RAM and storage customization scope", "RAM and/or storage disclosure is incomplete", "HIGH", "The listing identifies a customized computer but does not clearly document both allowed customization categories.", source, "Document the actual RAM and storage options and clarify what remains factory configured."))

    absolute = re.search(r"\b(?:guaranteed|100%\s+(?:safe|compatible|reliable)|best\s+(?:in|on)\s+the\s+market)\b", text, re.I)
    if absolute:
        findings.append(_finding("CPC-CLAIM-001", "compliance_absolute_claim", "Documented and supportable claim", absolute.group(0), "REVIEW", "An absolute or guaranteed claim requires substantiation and compliance review.", source, "Remove the claim or replace it with a qualified, verifiable factual statement."))
    return findings


def _catalog_checks(record: ListingRecord, evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    def add(rule: str, field: str, expected: str, observed: str, reason: str, severity: str = "HIGH") -> None:
        findings.append(_finding(rule, "compliance_" + field, expected, observed, severity, reason, evidence.source, expected))

    if not evidence.title.startswith("MegaPC Custom "):
        add("CAT-TITLE-001", "catalog_title", "MegaPC Custom [Product Type], Created Using [OEM Model], …, Win 11 Pro", evidence.title, "Current seller catalog requires the exact MegaPC Custom prefix.")
    if not evidence.title.rstrip().endswith("Win 11 Pro"):
        add("CAT-OS-001", "catalog_os", "Title ends with Win 11 Pro", evidence.title, "The confirmed sold system is Windows 11 Pro; OEM factory Home is a separate configuration.")
    if len(evidence.bullets) != 5:
        add("CAT-BULLET-001", "bullet_count", "Exactly five bullets; fixed warranty first", str(len(evidence.bullets)), "The current generation style uses five bullets.", "REVIEW")
    for field, content in [("title", evidence.title), ("bullets", " ".join(evidence.bullets)), ("description", visible_text(evidence.description))]:
        if re.search(r"\b(?:choose|selectable|options?|up to)\b.{0,50}\b(?:RAM|memory|SSD|storage|GB|TB)\b|\b\d+\s*(?:GB|TB)\s*[/–-]\s*\d+\s*(?:GB|TB)\b", content, re.I):
            add("CAT-BASE-001", "base_" + field, "Actual installed base RAM/SSD only; no selectable tiers or platform maximums", content, "Selectable capacities must not replace the sold base configuration.")
    brand = oem_brand(record.product_name) or oem_brand(evidence.title)
    expected = warranty(brand)
    locations = {"bullet_1": evidence.bullets[0] if evidence.bullets else "", "description_warranty": visible_text(evidence.description)}
    warranty_detail = next((value for key, value in evidence.details.items() if re.sub(r"\W", "", key.casefold()) == "warrantydescription"), "")
    locations["warranty_description"] = visible_text(warranty_detail)
    for location, content in locations.items():
        valid = content == expected if location != "description_warranty" else content.endswith(expected) and "Warranty and Disclosure" in content
        if not brand or not valid:
            add("CAT-WARRANTY-001", location, expected, content or "Not captured", "Match the fixed seller paragraph in all three locations; missing page evidence requires review.", "REVIEW" if not content or not brand else "HIGH")
    add("CAT-PUBLICATION-001", "publication_check", "SELLER_MANUAL_PUBLICATION_CHECK: OEM coverage, actual seal-opening/customization, Windows licensing and current Amazon account eligibility", "USER_CONFIRMED_CATALOG_POLICY", "Exact seller wording is an internal policy assertion, not independent OEM or Amazon approval.", "REVIEW")
    return findings
