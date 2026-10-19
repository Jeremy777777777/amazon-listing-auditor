from __future__ import annotations

import re
from html import escape

from .models import ERPRecord, Evidence, Finding, ListingRecord
from .catalog_policy import has_capacity_options, identify_oem, warranty
from .customization import options


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


def _known(value: str) -> str:
    return "" if "[[VERIFY" in str(value) else str(value or "")


def _publication_facts(record: ListingRecord, evidence: Evidence, erp: ERPRecord | None) -> dict:
    facts = {key: _known(value) for key, value in _canonical(record, erp).items()}
    facts['ram_options'] = options(evidence, 'ram')
    facts['storage_options'] = options(evidence, 'storage')
    ram_type = next((str(value) for key, value in evidence.details.items() if key.casefold() in {'ram memory technology','ram type'} and re.fullmatch(r'(?:LP)?DDR\d+(?: RAM)?', str(value), re.I)), '')
    facts['ram_type'] = ram_type.replace(' RAM', '')
    if not facts['graphics'] and re.search(r'Intel\s+Integrated', record.product_name, re.I):
        facts['graphics'] = 'integrated Intel graphics'
    facts['cpu'] = re.sub(r'\bIntel\s+(i[3579]-)', r'Intel Core \1', facts['cpu'])
    return facts


def _capacity_copy(facts: dict, kind: str, title: bool = False) -> str:
    choices = facts.get(kind + '_options', [])
    if choices:
        text = '/'.join(choices) if title else ', '.join(choices[:-1]) + (' or ' + choices[-1] if len(choices) > 1 else choices[-1])
        suffix = (facts.get('ram_type', '') + ' RAM').strip() if kind == 'ram' else 'SSD'
        return f'{text} {suffix}' if title else f"Choose {text} {suffix}."
    value = _known(facts.get('ram' if kind == 'ram' else 'storage', ''))
    if not value: return ''
    return value if title else f"{'Base memory' if kind == 'ram' else 'Base internal storage'}: {value}."


def _memory_paragraph(brand: str, facts: dict) -> str:
    capacities = ' '.join(filter(None, [_capacity_copy(facts, 'ram'), _capacity_copy(facts, 'storage')]))
    customization = f"{brand} prepares the selected memory and storage configuration before shipment. Hardware customization is limited to supported RAM and storage changes; other hardware remains factory configured."
    return ' '.join(filter(None, [capacities, customization]))


def _display_paragraph(facts: dict) -> str:
    screen = _known(facts.get('screen', ''))
    if not screen: return ''
    size = re.search(r'(\d{2}(?:\.\d)?)\s*(?:"|inch(?:es)?)', screen, re.I)
    resolution = re.search(r'(\d{3,4})\s*[x×]\s*(\d{3,4})', screen)
    refresh = re.search(r'(\d{2,3})\s*Hz', screen, re.I)
    if not size: return screen + '.'
    spec = f"The {size[1]}-inch display"
    if resolution: spec += f" features {resolution[1]} x {resolution[2]} resolution"
    if refresh: spec += f" and a {refresh[1]} Hz refresh rate"
    return spec + ' for documents, spreadsheets, browsing and everyday applications.'


def _wireless_paragraph(facts: dict) -> str:
    text = _known(facts.get('connectivity',''))
    wifi, bluetooth = 'Wi-Fi' in text, 'Bluetooth' in text
    if wifi and bluetooth: return 'Wi-Fi supports wireless network access, while Bluetooth connects compatible wireless peripherals.'
    if wifi: return 'Wi-Fi supports wireless network access.'
    if bluetooth: return 'Bluetooth connects compatible wireless peripherals.'
    return ''


def _title(brand: str, facts: dict) -> str:
    required = [
        f"{brand} Custom {facts['type']}",
        f"Created Using {facts['model']}",
        _capacity_copy(facts, 'ram', title=True), _capacity_copy(facts, 'storage', title=True),
    ]
    os_label = "Win 11 Pro" if brand == "MegaPC" else facts["os"]
    values = required[:2] + [_known(facts["cpu"])] + required[2:] + [os_label]
    candidate = ", ".join(filter(None, values))
    return candidate


def _bullets(brand: str, facts: dict) -> str:
    processor = f"Processor & Performance — The {facts['cpu']} processor" + (f" with {facts['graphics']}" if facts.get('graphics') else '') + ' supports everyday office applications, browsing and multitasking.' if _known(facts.get('cpu','')) else 'Factory Hardware — Other hardware remains factory configured; seller hardware customization is limited to RAM and storage.'
    experience = ' '.join(filter(None, [_display_paragraph(facts), _wireless_paragraph(facts), f"{facts['os']} is preinstalled for everyday work and business use." if _known(facts.get('os','')) else '']))
    bullets = [
        _warranty(brand, facts['oem_brand']),
        f"Custom Computer — Created Using {facts['model']}, this {facts['type']} is configured by {brand} for your selected memory and storage specification.",
        processor,
        f"Memory & Storage — {_memory_paragraph(brand, facts)}",
        f"Display & Connectivity — {experience}",
    ]
    return "\n\n".join(bullets)


def _description(brand: str, facts: dict) -> str:
    if not _known(facts.get('model','')) or not _known(facts.get('oem_brand','')): return ''
    def paragraph(heading: str, body: str = "") -> str:
        content = f"<strong>{escape(heading)}</strong>"
        if body:
            content += f"<br>\n{escape(body)}"
        return f"<p>{content}</p>"

    sections = [
        paragraph(f"{brand} Custom {facts['type']} — Created Using {facts['model']}"),
    ]
    display = _display_paragraph(facts)
    if display: sections.append(paragraph("Display & Design", display))
    if _known(facts.get('cpu','')): sections.append(paragraph("Processor & Performance", f"The {facts['cpu']} processor supports everyday office applications, web browsing and multitasking."))
    if _known(facts.get('graphics','')):
        sections.append(paragraph("Graphics Platform", f"Graphics configuration: {facts['graphics']}."))
    sections.extend([
        paragraph(f"Memory & Storage, Customized by {brand}", _memory_paragraph(brand, facts)),
    ])
    wireless = _wireless_paragraph(facts)
    if wireless: sections.append(paragraph("Connectivity", wireless))
    if _known(facts.get('os','')): sections.append(paragraph(facts['os'], f"{facts['os']} is preinstalled for everyday work and business use."))
    sections.append(paragraph("Warranty and Disclosure", _warranty(brand, facts['oem_brand'])))
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
    facts = _publication_facts(record, evidence, erp)
    if brand == "MegaPC": facts['os'] = "Windows 11 Pro"
    if not facts['model'] or not facts['type'] or not facts['oem_brand'] or brand != 'MegaPC':
        return [Finding('copy_source_review', 'Mapped model, product type, OEM and seller warranty policy', 'Insufficient identity/warranty evidence', 'REVIEW', 'Buyer-facing copy is withheld until core identity and warranty policy are mapped; placeholders are not exported as copy.', REFERENCE, rule_id='COPY-SOURCE-001', reference=REFERENCE)]
    shared = dict(severity="REVIEW", evidence_source=REFERENCE, reference=REFERENCE)
    recommendations = [
        Finding("copy_title", "Copyable title using supported base facts and observed Customize options", evidence.title, reason="Only observed, unit-qualified Customize options enter the offered capacity list. Unconfirmed optional facts are omitted, not emitted as VERIFY placeholders. Confirm the title is at most 200 characters.", corrected_value=_title(brand, facts), rule_id="STYLE-TITLE-001", **shared),
        Finding("copy_bullet_points", "Five complete buyer-facing paragraphs, warranty first", "\n\n".join(evidence.bullets) or "No readable bullets", reason="Full copyable replacement; missing-source explanations remain in audit notes instead of buyer-facing text.", corrected_value=_bullets(brand, facts), rule_id="STYLE-BULLET-001", **shared),
        Finding("copy_product_description", "Copyable HTML with observed Customize choices and fixed catalog warranty", evidence.description or "No readable description", reason="The latest user instruction permits actual offered upgrades in audit copy, overriding the prior base-only restriction. Factory values, offered options and page attributes remain distinct evidence.", corrected_value=_description(brand, facts), rule_id="STYLE-DESC-001", **shared),
    ]
    missing = [label for kind,label in [('ram','RAM'),('storage','internal storage')] if not facts.get(kind + '_options') and not facts.get('ram' if kind == 'ram' else 'storage')]
    if missing:
        recommendations.append(Finding('copy_capacity_source', 'Observed Customize options or confirmed installed base capacity', ', '.join(missing), 'REVIEW', 'Capacity numbers are omitted from buyer-facing copy because their source is unavailable. Capture the choices and units or provide confirmed base facts.', REFERENCE, rule_id='COPY-SOURCE-002', reference=REFERENCE))
    return recommendations
