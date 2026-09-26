from __future__ import annotations

import re

from .compliance import check_compliance
from .copy_style import style_correction_findings
from .models import AuditResult, ERPRecord, Evidence, Finding, ListingRecord


BRANDS = ["Dell", "Lenovo", "HP", "LG", "Acer", "ASUS", "Microsoft", "Samsung", "Apple", "MegaPC"]
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

    findings.extend(check_compliance(record, evidence))
    findings.extend(additional_findings or [])
    findings.extend(style_correction_findings(record, evidence, erp, findings))

    status = "FAIL" if any(f.severity in {"CRITICAL", "HIGH"} for f in findings) else ("REVIEW" if findings else "PASS")
    return AuditResult(record, status, findings, evidence, erp)
