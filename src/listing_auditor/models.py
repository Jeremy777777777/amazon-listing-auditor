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
    source: str = ""
    captured_at: str = ""
    available: bool = True
    error: str = ""

    @property
    def text(self) -> str:
        return " ".join([self.title, *self.bullets, self.description]).strip()


@dataclass(frozen=True)
class Finding:
    field: str
    expected: str
    observed: str
    severity: str
    reason: str


@dataclass
class AuditResult:
    listing: ListingRecord
    status: str
    findings: list[Finding]
    evidence: Evidence

    def to_dict(self) -> dict:
        return asdict(self)

