from __future__ import annotations

import re

from .models import AuditResult, Evidence, Finding, ListingRecord


BRANDS = ["Dell", "Lenovo", "HP", "LG", "Acer", "ASUS", "Microsoft", "Samsung", "Apple", "MegaPC"]
CPU_RE = re.compile(r"(?:Intel\s+)?(?:Core\s+)?(?:Ultra\s+\d+\s+\d+[A-Z]*|i[3579]-\d{4,5}[A-Z]*)", re.I)
RESOLUTION_RE = re.compile(r"\b(\d{3,4})\s*[x×]\s*(\d{3,4})\b", re.I)
SIZE_RE = re.compile(r"\b(\d{2}(?:\.\d)?)\s*(?:inch|inches|\")", re.I)
HZ_RE = re.compile(r"\b(\d{2,3})\s*Hz\b", re.I)


def _brand(text: str) -> str:
    for brand in BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", text, re.I):
            return brand
    return ""


def _model(expected: str) -> str:
    # Tracker convention: the first slash-delimited segment is Brand + model family.
    first = expected.split("/", 1)[0].strip()
    brand = _brand(first)
    return re.sub(rf"^{re.escape(brand)}\s+", "", first, flags=re.I).strip() if brand else first


def _first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    if len(match.groups()) > 1:
        return " x ".join(match.groups())
    if len(match.groups()) == 1:
        return match.group(1)
    return match.group(0)


def compare(record: ListingRecord, evidence: Evidence) -> AuditResult:
    if not evidence.available or not evidence.text:
        finding = Finding("evidence", "Readable listing page", evidence.error or "No text", "REVIEW", "Listing evidence is unavailable; manual review required.")
        return AuditResult(record, "REVIEW", [finding], evidence)

    expected = record.product_name
    observed = evidence.text
    findings: list[Finding] = []
    expected_brand, observed_brand = _brand(expected), _brand(observed)
    if expected_brand and observed_brand and expected_brand.lower() != observed_brand.lower():
        findings.append(Finding("brand", expected_brand, observed_brand, "CRITICAL", "The listing describes a different manufacturer."))

    expected_model = _model(expected)
    if expected_model and not re.search(re.escape(expected_model), observed, re.I):
        observed_identity = " ".join(observed.split()[:14])
        findings.append(Finding("model", expected_model, observed_identity, "CRITICAL", "The expected model/family is absent from listing evidence."))

    for field, pattern in [("cpu", CPU_RE), ("resolution", RESOLUTION_RE), ("display_size", SIZE_RE), ("refresh_rate", HZ_RE)]:
        expected_value = _first(pattern, expected)
        observed_value = _first(pattern, observed)
        if expected_value and observed_value and expected_value.lower().replace(" ", "") != observed_value.lower().replace(" ", ""):
            findings.append(Finding(field, expected_value, observed_value, "HIGH", f"Explicit {field} values conflict."))

    expected_touch = bool(re.search(r"\btouch(?:screen)?\b", expected, re.I))
    observed_touch = bool(re.search(r"\btouch(?:screen)?\b", observed, re.I))
    if expected_touch != observed_touch:
        findings.append(Finding("touchscreen", str(expected_touch), str(observed_touch), "HIGH", "Touch capability does not match."))

    status = "FAIL" if findings else "PASS"
    return AuditResult(record, status, findings, evidence)
