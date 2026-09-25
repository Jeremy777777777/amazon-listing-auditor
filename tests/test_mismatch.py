from pathlib import Path

from listing_auditor.compare import compare
from listing_auditor.evidence import collect_evidence
from listing_auditor.models import ListingRecord


ROOT = Path(__file__).parents[1]


def test_wrong_product_identity_is_critical() -> None:
    record = ListingRecord(
        product_name='Dell 15 DC15250 / Laptop / 15.6" / Touchscreen / Black / Intel Core i7-1355U / Intel UHD Graphics / 1920x1080 / 60 Hz',
        sku="VL-1249",
        seller="MegaPC",
        url="https://www.amazon.com/dp/B0HBDTJNJV",
        asin="B0HBDTJNJV",
        row_number=34,
    )
    evidence = collect_evidence(record, ROOT / "fixtures" / "listings")
    result = compare(record, evidence)
    assert result.status == "FAIL"
    assert {finding.field for finding in result.findings} >= {"brand", "model"}
    assert all(
        finding.severity == "CRITICAL"
        for finding in result.findings
        if finding.field in {"brand", "model"}
    )

