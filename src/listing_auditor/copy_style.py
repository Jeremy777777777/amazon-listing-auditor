from __future__ import annotations

import re
from html import escape

from .models import ERPRecord, Evidence, Finding, ListingRecord
from .catalog_policy import has_capacity_options, identify_oem, warranty


REFERENCE = "references/listing-copy-style.md"
SELLER_BRANDS = {"megapc": "MegaPC", "jtd": "J-Tech Digital"}


def _value(fields: dict[str, str], *keys: str) -> str:
    return next((fields.get(key, "").strip() for key in keys if fields.get(key, "").strip()), "")


def _base_capacity(value: str, fallback: str, placeholder: str) -> str:
    def single(text: str) -> bool:
        return len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:GB|TB)\b", text, re.I)) == 1 and not re.search(r"[/,]|\b(?:options?|or|up to|maximum)\b", text, re.I)
    if value:
        if not single(value): return placeholder
        def nominal(text):
            match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|TB)", text, re.I)
            return float(match[1]) * (1000 if match[2].upper() == 'TB' else 1)
        if fallback and nominal(value) != nominal(fallback): return placeholder
        return value
    return fallback if single(fallback) else placeholder


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
    category = _value(fields, "category")
    if not category:
        category = next((name for pattern, name in ((r"all-in-one|\baio\b", "All-in-One Desktop"), (r"\blaptop\b|\bnotebook\b", "Laptop"), (r"\bmini pc\b", "Mini PC"), (r"\bdesktop\b", "Desktop"), (r"\bworkstation\b", "Workstation")) if re.search(pattern, input_text, re.I)), "")
    cpu = _value(fields, "cpu") or (re.search(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", input_text, re.I).group(0) if re.search(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", input_text, re.I) else "")
    ram_match = re.search(r"\b\d+\s*GB\s*(?:DDR\d+\s*(?:RAM|Memory)?|RAM|Memory)\b", input_text, re.I)
    storage_match = re.search(r"\b\d+(?:\.\d+)?\s*(?:GB|TB)\s*(?:SSD|HDD|NVMe)\b", input_text, re.I)
    ram = _base_capacity(_value(fields, "ram", "memory"), ram_match.group(0) if ram_match else "", "[[VERIFY BASE RAM]]")
    storage = _base_capacity(_value(fields, "ssd", "hdd", "storage"), storage_match.group(0) if storage_match else "", "[[VERIFY BASE INTERNAL STORAGE]]")
    if has_capacity_options(input_text):
        ram, storage = "[[VERIFY BASE RAM]]", "[[VERIFY BASE INTERNAL STORAGE]]"
    if fields.get('ssd2'): storage = "[[VERIFY BASE INTERNAL STORAGE]]"
    os_name = "Windows 11 Pro" if record.seller.casefold() == "megapc" else _value(fields, "os")
    graphics = _value(fields, "graphicCard", "graphics")
    screen_parts = [_value(fields, "screenSize"), _value(fields, "resolution"), _value(fields, "refreshRate")]
    if not any(screen_parts):
        screen_parts = [m.group(0) for pattern in (r'\b\d{2}(?:\.\d)?\s*(?:"|inch(?:es)?)', r'\b\d{3,4}\s*[x×]\s*\d{3,4}\b', r'\b\d{2,3}\s*Hz\b') if (m := re.search(pattern, input_text, re.I))]
    screen = " ".join(screen_parts)
    connectivity = ", ".join(label for key, label in (("wifi", "Wi-Fi"), ("bluetooth", "Bluetooth"), ("fingerprint", "fingerprint reader"), ("backlit", "backlit keyboard")) if fields.get(key, "").casefold() in {"true", "yes", "1", "supported"} or (not fields.get(key) and re.search(r"\b" + (r"wi-?fi" if key == "wifi" else key) + r"\b", input_text, re.I)))
    return {
        "model": model or "[[VERIFY OEM MODEL]]",
        "type": category or "[[VERIFY PRODUCT TYPE]]",
        "cpu": cpu or "[[VERIFY CPU]]",
        "ram": ram,
        "storage": storage,
        "oem_brand": identify_oem(brand or model),
        "os": os_name or "[[VERIFY PREINSTALLED OS]]",
        "graphics": graphics,
        "screen": screen or "[[VERIFY DISPLAY OR DESIGN DIFFERENTIATOR]]",
        "connectivity": connectivity or "[[VERIFY CONNECTIVITY AND PORTS]]",
    }


def _warranty(brand: str, oem: str) -> str:
    if brand == "MegaPC":
        return warranty(oem)
    return f"WARRANTY: [[VERIFY OEM WARRANTY STATUS]]. {brand} provides [[VERIFY SELLER WARRANTY TERM AND COVERAGE]] for upgraded RAM and SSD components."


def _title(brand: str, facts: dict[str, str]) -> str:
    required = [
        f"{brand} Custom {facts['type']}",
        f"Created Using {facts['model']}",
        facts["ram"], facts["storage"],
    ]
    os_label = "Win 11 Pro" if brand == "MegaPC" else facts["os"]
    values = required[:2] + [facts["cpu"]] + required[2:] + [os_label]
    candidate = ", ".join(values)
    return candidate


def _bullets(brand: str, facts: dict[str, str]) -> str:
    bullets = [
        _warranty(brand, facts['oem_brand']),
        f"Custom Computer — Created Using {facts['model']}, this {facts['type']} is configured by {brand} for the purchased base specification.",
        f"Processor & Performance — Powered by {facts['cpu']} for everyday computing.",
        f"Memory & Storage — Installed base memory: {facts['ram']}. Internal storage: {facts['storage']}. Hardware customization is limited to RAM and storage; other hardware remains factory configured.",
        f"Display & Connectivity — {facts['screen']}. {facts['connectivity']}. {facts['os']} is the fixed preinstalled operating system.",
    ]
    return "\n\n".join(bullets)


def _description(brand: str, facts: dict[str, str]) -> str:
    def paragraph(heading: str, body: str = "") -> str:
        content = f"<strong>{escape(heading)}</strong>"
        if body:
            content += f"<br>\n{escape(body)}"
        return f"<p>{content}</p>"

    sections = [
        paragraph(f"{brand} Custom {facts['type']} — Created Using {facts['model']}"),
        paragraph("Display or Design", f"Display or form-factor configuration: {facts['screen']}."),
        paragraph("Processor & Performance", f"The {facts['cpu']} processor supports everyday computing."),
    ]
    if facts["graphics"]:
        sections.append(paragraph("Graphics Platform", f"Graphics configuration: {facts['graphics']}."))
    sections.extend([
        paragraph(f"Memory & Storage, Customized by {brand}", f"Installed base memory: {facts['ram']}. Internal storage: {facts['storage']}. Hardware customization is limited to RAM and storage; other hardware remains factory configured."),
        paragraph("Connectivity & System Features", f"{facts['connectivity']}."),
        paragraph(facts['os'], f"{facts['os']} is preinstalled for everyday work and business use."),
        paragraph("Warranty and Disclosure", _warranty(brand, facts['oem_brand'])),
    ])
    return "\n\n".join(sections)


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
    if brand == "MegaPC": facts['os'] = "Windows 11 Pro"
    shared = dict(severity="REVIEW", evidence_source=REFERENCE, reference=REFERENCE)
    return [
        Finding("copy_title", "Seller-brand-first base-configuration title using verified facts", evidence.title, reason="Uses the creation project's Custom prefix, base capacities and fixed OS ending. Resolve VERIFY markers and confirm the final title is at most 200 characters; do not silently drop CPU or identity to shorten it.", corrected_value=_title(brand, facts), rule_id="STYLE-TITLE-001", **shared),
        Finding("copy_bullet_points", "Warranty-first themed bullet set using verified facts", "\n".join(evidence.bullets) or "No readable bullets", reason="Suggested bullets follow the existing warranty-first and product-theme sequence; they are not publish-ready while VERIFY placeholders remain.", corrected_value=_bullets(brand, facts), rule_id="STYLE-BULLET-001", **shared),
        Finding("copy_product_description", "HTML description using the base sold configuration and fixed catalog warranty", evidence.description or "No readable description", reason="Follows the creation project's base-configuration, fixed Windows 11 Pro and exact Warranty and Disclosure rules, with the user's p/strong/br HTML format. VERIFY placeholders require review before publication.", corrected_value=_description(brand, facts), rule_id="STYLE-DESC-001", **shared),
    ]
