from __future__ import annotations

import re

from .models import ERPRecord, Evidence, Finding, ListingRecord


REFERENCE = "references/listing-copy-style.md"
SELLER_BRANDS = {"megapc": "MegaPC", "jtd": "J-Tech Digital"}


def _value(fields: dict[str, str], *keys: str) -> str:
    return next((fields.get(key, "").strip() for key in keys if fields.get(key, "").strip()), "")


def _seller_brand(record: ListingRecord, evidence: Evidence) -> str:
    mapped = SELLER_BRANDS.get(record.seller.casefold())
    if mapped:
        return mapped
    if evidence.title.casefold().startswith("megapc"):
        return "MegaPC"
    if evidence.title.casefold().startswith(("j-tech digital", "jtd")):
        return "J-Tech Digital"
    return "[[VERIFY SELLER BRAND]]"


def _canonical(record: ListingRecord, erp: ERPRecord | None) -> dict[str, str]:
    fields = erp.fields if erp and erp.available else {}
    parts = [part.strip() for part in record.product_name.split("/") if part.strip()]
    input_text = " / ".join(parts)
    brand = _value(fields, "brand")
    model = _value(fields, "model", "name")
    if not model and parts:
        model = parts[0]
    elif brand and model and not model.casefold().startswith(brand.casefold()):
        model = f"{brand} {model}"
    category = _value(fields, "category") or next((part for part in parts if re.search(r"\b(?:laptop|desktop|all-in-one|aio|mini pc|workstation)\b", part, re.I)), "")
    cpu = _value(fields, "cpu") or (re.search(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", input_text, re.I).group(0) if re.search(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", input_text, re.I) else "")
    ram = _value(fields, "ram", "memory")
    storage = _value(fields, "ssd", "ssd2", "hdd", "storage")
    os_name = _value(fields, "os")
    graphics = _value(fields, "graphicCard", "graphics")
    screen = " ".join(value for value in [_value(fields, "screenSize"), _value(fields, "resolution"), _value(fields, "refreshRate")] if value)
    connectivity = ", ".join(label for key, label in (("wifi", "Wi-Fi"), ("bluetooth", "Bluetooth"), ("fingerprint", "fingerprint reader"), ("backlit", "backlit keyboard")) if fields.get(key, "").casefold() in {"true", "yes", "1", "supported"})
    return {
        "model": model or "[[VERIFY OEM MODEL]]",
        "type": category or "[[VERIFY PRODUCT TYPE]]",
        "cpu": cpu or "[[VERIFY CPU]]",
        "ram": ram or "[[VERIFY RAM OPTIONS]]",
        "storage": storage or "[[VERIFY SSD OPTIONS]]",
        "os": os_name or "[[VERIFY PREINSTALLED OS]]",
        "graphics": graphics,
        "screen": screen or "[[VERIFY DISPLAY OR DESIGN DIFFERENTIATOR]]",
        "connectivity": connectivity or "[[VERIFY CONNECTIVITY AND PORTS]]",
    }


def _warranty(brand: str) -> str:
    if brand == "MegaPC":
        return "WARRANTY: The original manufacturer warranty remains valid on factory components. MegaPC provides a 1-year limited warranty on upgraded RAM and SSD components."
    return f"WARRANTY: [[VERIFY OEM WARRANTY STATUS]]. {brand} provides [[VERIFY SELLER WARRANTY TERM AND COVERAGE]] for upgraded RAM and SSD components."


def _title(brand: str, facts: dict[str, str]) -> str:
    required = [
        f"{brand} Customized {facts['type']}",
        f"Created Using {facts['model']}",
        facts["ram"], facts["storage"],
    ]
    values = required[:2] + [facts["cpu"]] + required[2:]
    candidate = ", ".join(values)
    if len(candidate) + len(facts["os"]) + 2 <= 200:
        candidate = f"{candidate}, {facts['os']}"
    if len(candidate) > 200:
        candidate = ", ".join(required)
    return candidate


def _bullets(brand: str, facts: dict[str, str]) -> str:
    bullets = [
        _warranty(brand),
        f"CUSTOMIZED PRODUCT OVERVIEW: Created using {facts['model']}, this {facts['type']} is customized by {brand} only for the selected RAM and storage configuration; other hardware and software remain factory configured.",
        f"PROCESSOR & EVERYDAY PERFORMANCE: Powered by {facts['cpu']} for [[VERIFY APPROPRIATE WORKLOADS AND PRACTICAL VALUE]].",
        f"MEMORY & STORAGE: Choose {facts['ram']} memory and {facts['storage']} storage options to match [[VERIFY SUPPORTED BUYER NEEDS]]. The selected configuration is installed before shipment.",
        f"DISPLAY OR DESIGN: {facts['screen']} supports [[VERIFY DISPLAY OR DESIGN BENEFIT]].",
        f"CONNECTIVITY & EXPANSION: {facts['connectivity']} supports [[VERIFY CONNECTIVITY USE CASES]].",
        f"COMPLETE USE SETUP: {facts['os']} is preinstalled as a fixed system specification for [[VERIFY SUITABLE USE CASES]]; it is not a {brand} software customization. Included accessories: [[VERIFY INCLUDED ACCESSORIES]].",
    ]
    return "\n".join(f"{index}. {text}" for index, text in enumerate(bullets, 1))


def _description(brand: str, facts: dict[str, str]) -> str:
    sections = [
        f"**{brand} Customized {facts['type']} — Created Using {facts['model']}**",
        f"**Display or Design**\\\n{facts['screen']} supports [[VERIFY DISPLAY OR DESIGN BENEFIT]].",
        f"**Processor & Performance**\\\nPowered by {facts['cpu']}, this system is suited to [[VERIFY APPROPRIATE WORKLOADS]].",
    ]
    if facts["graphics"]:
        sections.append(f"**Graphics Platform**\\\n{facts['graphics']} supports [[VERIFY MANUFACTURER-SUPPORTED GRAPHICS CAPABILITIES AND USE CASES]].")
    sections.extend([
        f"**Memory & Storage, Customized by {brand}**\\\nAvailable memory: {facts['ram']}. Available storage: {facts['storage']}. {brand} changes only the selected RAM and storage; other hardware and software remain factory configured.",
        f"**Connectivity & System Features**\\\n{facts['connectivity']} supports [[VERIFY CONNECTIVITY USE CASES]]. Included accessories: [[VERIFY INCLUDED ACCESSORIES]].",
        f"**{facts['os']}**\\\nThe operating system is preinstalled as a fixed system specification for [[VERIFY SUITABLE USE CASES]] and is not a {brand} software customization.",
        f"**Warranty**\\\n{_warranty(brand)}",
    ])
    return "\n".join(sections)


def style_correction_findings(record: ListingRecord, evidence: Evidence, erp: ERPRecord | None, existing: list[Finding]) -> list[Finding]:
    actionable = any(
        not finding.field.startswith("image_")
        and finding.field != "input_baseline"
        and (finding.severity in {"CRITICAL", "HIGH"} or finding.field.startswith("compliance"))
        for finding in existing
    )
    if not actionable:
        return []
    brand = _seller_brand(record, evidence)
    facts = _canonical(record, erp)
    shared = dict(severity="REVIEW", evidence_source=REFERENCE, reference=REFERENCE)
    return [
        Finding("copy_title", "Seller-brand-first style-compliant title using verified facts", evidence.title, reason="Suggested title follows the existing customized-PC title order; every VERIFY placeholder must be resolved before use.", corrected_value=_title(brand, facts), rule_id="STYLE-TITLE-001", **shared),
        Finding("copy_bullet_points", "Warranty-first themed bullet set using verified facts", "\n".join(evidence.bullets) or "No readable bullets", reason="Suggested bullets follow the existing warranty-first and product-theme sequence; they are not publish-ready while VERIFY placeholders remain.", corrected_value=_bullets(brand, facts), rule_id="STYLE-BULLET-001", **shared),
        Finding("copy_product_description", "Sectioned Markdown description using verified facts", evidence.description or "No readable description", reason="Suggested description follows the existing sectioned style and keeps Warranty last; it must be fact-checked before publication.", corrected_value=_description(brand, facts), rule_id="STYLE-DESC-001", **shared),
    ]
