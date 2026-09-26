from __future__ import annotations

import re

from .models import Evidence, Finding


RULES = [
    (
        "compliance_warranty_claim",
        re.compile(r"(?:original|manufacturer(?:'s)?)\s+\w*\s*warranty\s+(?:remains?\s+valid|is\s+valid|will\s+remain)", re.I),
        "A manufacturer-warranty validity claim needs manufacturer or authorized-reseller evidence after customization.",
    ),
    (
        "compliance_absolute_claim",
        re.compile(r"\b(?:guaranteed|100%\s+(?:safe|compatible|reliable)|best\s+(?:in|on)\s+the\s+market)\b", re.I),
        "An absolute or guaranteed claim requires substantiation and compliance review.",
    ),
]


def check_compliance(evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    for field, pattern, reason in RULES:
        match = pattern.search(evidence.text)
        if match:
            findings.append(
                Finding(
                    field=field,
                    expected="Documented and supportable claim",
                    observed=match.group(0),
                    severity="REVIEW",
                    reason=reason,
                    evidence_source=evidence.source,
                    corrected_value="Remove the claim or add an approved, verifiable qualification.",
                )
            )
    return findings
