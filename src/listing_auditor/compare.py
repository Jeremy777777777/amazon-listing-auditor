from __future__ import annotations

import re

from .compliance import check_compliance
from .copy_style import style_correction_findings
from .models import AuditResult, ERPRecord, Evidence, Finding, ListingRecord


BRANDS = ["Dell", "Lenovo", "HP", "LG", "Acer", "ASUS", "Microsoft", "Samsung", "Apple", "MegaPC"]
SELLER_BRANDS = {"megapc", "jtd"}
MODEL_FAMILY_BRANDS = {
    "Lenovo": ["ThinkPad", "IdeaPad", "Yoga", "Legion"],
    "Dell": ["Latitude", "Inspiron", "XPS", "Vostro", "Precision"],
    "HP": ["EliteBook", "ProBook", "Pavilion", "Spectre", "Envy"],
    "Acer": ["Aspire", "Swift"],
    "ASUS": ["ZenBook", "VivoBook"],
    "Microsoft": ["Surface"],
    "Apple": ["MacBook"],
    "Samsung": ["Galaxy Book"],
    "LG": ["Gram"],
}
MODEL_FAMILIES = [family for families in MODEL_FAMILY_BRANDS.values() for family in families]
PATTERNS = {
    "cpu": re.compile(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", re.I),
    "resolution": re.compile(r"\b(\d{3,4})\s*[x×]\s*(\d{3,4})\b", re.I),
    "display_size": re.compile(r"\b(\d{2}(?:\.\d)?)\s*[-–]?\s*(?:inch|inches|\")", re.I),
    "refresh_rate": re.compile(r"\b(\d{2,3})\s*Hz\b", re.I),
    "memory": re.compile(r"\b(\d{1,3})\s*GB\s*(?:LPDDR\w*|DDR\w*|RAM|Memory)?", re.I),
    "storage": re.compile(r"\b(\d+(?:\.\d+)?)\s*(TB|GB)\s*(?:SSD|NVMe|M\.2|HDD)", re.I),
    "os": re.compile(r"\bWindows\s+1[01]\s+(?:Pro|Home)\b", re.I),
}
BOOLEAN_TERMS = {
    "touchscreen": r"\btouch(?:screen|able)?\b",
    "fingerprint": r"\bfingerprint\b",
    "bluetooth": r"\bbluetooth\b",
    "backlit": r"\bbacklit\b",
    "wifi": r"\b(?:wi-?fi|wireless)\b",
}
ERP_KEYS = {
    "cpu": "cpu", "resolution": "resolution", "display_size": "screenSize",
    "refresh_rate": "refreshRate", "memory": "ram", "storage": "ssd", "os": "os",
    "touchscreen": "touchable", "fingerprint": "fingerprint", "bluetooth": "bluetooth",
    "backlit": "backlit", "wifi": "wifi", "model": "model", "brand": "brand",
}


def _brand(text: str) -> str:
    for brand in BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", text, re.I):
            return brand
    return ""


def _brands(text: str) -> set[str]:
    """Return every product manufacturer named in one evidence field."""
    return {
        brand for brand in BRANDS
        if brand.casefold() not in SELLER_BRANDS and re.search(rf"\b{re.escape(brand)}\b", text, re.I)
    }


def _model_families(text: str) -> set[str]:
    return {
        family for family in MODEL_FAMILIES
        if re.search(rf"\b{re.escape(family)}\b", text, re.I)
    }


def _has_product_identity_claim(text: str, brand: str) -> bool:
    """Separate product identity from incidental software/compatibility mentions."""
    for match in re.finditer(rf"\b{re.escape(brand)}\b", text, re.I):
        window = text[max(0, match.start() - 100):min(len(text), match.end() + 100)]
        if any(
            re.search(rf"\b{re.escape(family)}\b", window, re.I)
            for family in MODEL_FAMILY_BRANDS.get(brand, [])
        ):
            return True
        if re.search(
            rf"(?:created\s+using|built\s+(?:using|from|by)|brand\s*:|manufacturer\s*:|model(?:\s+name)?\s*:)[^.;]{{0,60}}\b{re.escape(brand)}\b|"
            rf"\b{re.escape(brand)}\b[^.;]{{0,40}}\b(?:laptop|notebook|desktop|computer|workstation)\b",
            window,
            re.I,
        ):
            return True
    return False


def _cross_field_identity_findings(evidence: Evidence) -> list[Finding]:
    """Flag Amazon fields whose OEM identity conflicts with the title."""
    title_brand_matches = [
        (match.start(), brand)
        for brand in _brands(evidence.title)
        if (match := re.search(rf"\b{re.escape(brand)}\b", evidence.title, re.I))
    ]
    if not title_brand_matches:
        return []
    expected_brand = min(title_brand_matches)[1]
    sections = {
        "Bullet Points": " ".join(evidence.bullets),
        "Product Description": evidence.description,
        "Product information": " ".join(f"{key}: {value}" for key, value in evidence.details.items()),
    }
    title_models = _model_families(evidence.title)
    findings: list[Finding] = []
    for section, text in sections.items():
        conflicting_brands = sorted(
            brand for brand in (_brands(text) - {expected_brand})
            if _has_product_identity_claim(text, brand)
        )
        for observed_brand in conflicting_brands:
            expected_models = ", ".join(sorted(title_models)) or "title product family/model"
            observed_models = ", ".join(sorted(_model_families(text))) or "different manufacturer identity"
            findings.append(Finding(
                field=f"{section.lower().replace(' ', '_')}_identity",
                expected=f"{expected_brand} — {expected_models}",
                observed=f"{observed_brand} — {observed_models}",
                severity="CRITICAL",
                reason=f"{section} names {observed_brand}, but the Amazon title identifies the product as {expected_brand}. This is a cross-field brand/model identity conflict.",
                evidence_source=evidence.source,
                corrected_value=f"Replace the {observed_brand} product identity and specifications with verified {expected_brand} model information.",
                rule_id="IDENTITY-CROSS-FIELD-001",
                reference="README.md#cross-field-identity-gate",
            ))
        section_models = _model_families(text)
        if not conflicting_brands and title_models and section_models and title_models.isdisjoint(section_models):
            findings.append(Finding(
                field=f"{section.lower().replace(' ', '_')}_identity",
                expected=f"{expected_brand} — {', '.join(sorted(title_models))}",
                observed=f"{expected_brand} — {', '.join(sorted(section_models))}",
                severity="CRITICAL",
                reason=f"{section} names a different product family/model than the Amazon title.",
                evidence_source=evidence.source,
                corrected_value="Replace the conflicting product family/model with the verified title and catalog identity.",
                rule_id="IDENTITY-CROSS-FIELD-001",
                reference="README.md#cross-field-identity-gate",
            ))
    return findings


def _model(text: str) -> str:
    first = text.split("/", 1)[0].strip()
    brand = _brand(first)
    return re.sub(rf"^{re.escape(brand)}\s+", "", first, flags=re.I).strip() if brand else first


def _first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    if len(match.groups()) > 1:
        return " x ".join(match.groups())
    return match.group(1) if match.groups() else match.group(0)


def _facts(text: str) -> dict[str, str]:
    facts = {field: _first(pattern, text) for field, pattern in PATTERNS.items()}
    facts["brand"] = _brand(text)
    facts["model"] = _model(text)
    for field, term in BOOLEAN_TERMS.items():
        facts[field] = "true" if re.search(term, text, re.I) else ""
    return facts


def _norm(value: str) -> str:
    value = value.casefold().replace("×", "x")
    return re.sub(r"[^a-z0-9]+", "", value)


def _erp_facts(erp: ERPRecord | None) -> dict[str, str]:
    if not erp or not erp.available:
        return {}
    facts: dict[str, str] = {}
    for field, key in ERP_KEYS.items():
        raw = erp.fields.get(key, "")
        if field in PATTERNS and raw:
            facts[field] = _first(PATTERNS[field], raw)
        elif field in BOOLEAN_TERMS and raw.casefold() in {"true", "yes", "1", "supported"}:
            facts[field] = "true"
        else:
            facts[field] = raw
    return facts


def compare(record: ListingRecord, evidence: Evidence, erp: ERPRecord | None = None, additional_findings: list[Finding] | None = None) -> AuditResult:
    findings: list[Finding] = []
    if not record.sku or not record.product_name:
        findings.append(Finding(
            field="input_baseline",
            expected="Internal ID and canonical product specification for full mismatch checking",
            observed=f"URL-only input for ASIN {record.asin}",
            severity="REVIEW",
            reason="The page can be checked for internal consistency, compliance, and image issues, but product-to-ERP mismatch cannot be fully confirmed without a mapped baseline.",
            evidence_source=record.url,
            corrected_value="Map this ASIN to an internal ID/product record if full product mismatch confirmation is required.",
            rule_id="INPUT-BASELINE-001",
            reference="README.md#url-only-输入",
        ))
    if not evidence.available or not evidence.text:
        findings.append(Finding("evidence", "Readable listing page", evidence.error or "No text", "REVIEW", "Amazon listing evidence is unavailable.", evidence.source))
        findings.extend(additional_findings or [])
        status = "FAIL" if any(f.severity in {"CRITICAL", "HIGH"} for f in findings) else "REVIEW"
        return AuditResult(record, status, findings, evidence, erp)

    expected, observed, erp_facts = _facts(record.product_name), _facts(evidence.text), _erp_facts(erp)
    expected["model"] = _model(record.product_name)
    observed["model"] = expected["model"] if re.search(re.escape(expected["model"]), evidence.text, re.I) else evidence.title
    fields = ["brand", "model", "cpu", "resolution", "display_size", "refresh_rate", "memory", "storage", "os", *BOOLEAN_TERMS]
    for field in fields:
        exp, obs, erp_value = expected.get(field, ""), observed.get(field, ""), erp_facts.get(field, "")
        if exp and obs and _norm(exp) != _norm(obs):
            severity = "CRITICAL" if field in {"brand", "model"} else "HIGH"
            corrected = exp if not erp_value or _norm(erp_value) == _norm(exp) else "MANUAL REVIEW"
            findings.append(Finding(field, exp, obs, severity, f"Amazon {field} conflicts with the input record.", evidence.source, erp_value, corrected))
        if erp_value and exp and _norm(erp_value) != _norm(exp):
            findings.append(Finding(field, exp, obs, "REVIEW", f"ERP {field} conflicts with the input record.", erp.source if erp else "ERP", erp_value, "MANUAL REVIEW"))
        if erp_value and obs and _norm(erp_value) != _norm(obs) and not any(f.field == field and f.observed == obs for f in findings):
            findings.append(Finding(field, exp, obs, "HIGH", f"Amazon {field} conflicts with ERP.", evidence.source, erp_value, erp_value))

    if erp and not erp.available:
        findings.append(Finding("erp_evidence", "Matching ERP record", erp.error or "Unavailable", "REVIEW", "ERP could not confirm this internal ID.", erp.source))

    findings.extend(_cross_field_identity_findings(evidence))
    findings.extend(check_compliance(record, evidence))
    findings.extend(additional_findings or [])
    findings.extend(style_correction_findings(record, evidence, erp, findings))

    status = "FAIL" if any(f.severity in {"CRITICAL", "HIGH"} for f in findings) else ("REVIEW" if findings else "PASS")
    return AuditResult(record, status, findings, evidence, erp)
