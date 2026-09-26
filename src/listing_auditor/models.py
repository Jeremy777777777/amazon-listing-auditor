from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ListingRecord:
    product_name: str
    sku: str
    seller: str
    url: str
    asin: str
    row_number: int


@dataclass(frozen=True)
class Evidence:
    url: str
    title: str = ""
    bullets: list[str] = field(default_factory=list)
    description: str = ""
    details: dict[str, str] = field(default_factory=dict)
    source: str = ""
    captured_at: str = ""
    available: bool = True
    error: str = ""

    @property
    def text(self) -> str:
        detail_text = " ".join(f"{key}: {value}" for key, value in self.details.items())
        return " ".join([self.title, *self.bullets, self.description, detail_text]).strip()


@dataclass(frozen=True)
class ERPRecord:
    internal_id: str
    fields: dict[str, str] = field(default_factory=dict)
    source: str = ""
    available: bool = False
    error: str = ""


@dataclass(frozen=True)
class Finding:
    field: str
    expected: str
    observed: str
    severity: str
    reason: str
    evidence_source: str = ""
    erp_value: str = ""
    corrected_value: str = ""


@dataclass
class AuditResult:
    listing: ListingRecord
    status: str
    findings: list[Finding]
    evidence: Evidence
    erp: ERPRecord | None = None

    def to_dict(self) -> dict:
        return asdict(self)
