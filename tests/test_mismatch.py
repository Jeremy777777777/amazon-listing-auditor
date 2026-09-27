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


def test_url_only_cross_field_dell_lenovo_conflict_is_critical() -> None:
    record = ListingRecord(
        product_name="",
        sku="",
        seller="MegaPC",
        url="https://www.amazon.com/dp/B0HBDTJNJV",
        asin="B0HBDTJNJV",
        row_number=0,
    )
    evidence = collect_evidence(record, ROOT / "fixtures" / "listings")
    evidence = type(evidence)(
        url=evidence.url,
        title="MegaPC Dell 15 DC15250 Laptop, 15.6-inch FHD Display",
        bullets=evidence.bullets,
        description="Created Using Lenovo ThinkPad X1 Carbon Gen 13 with a 14-inch OLED display.",
        details={"Model Name": "Dell 15 DC15250"},
        image_urls=evidence.image_urls,
        source=evidence.source,
        captured_at=evidence.captured_at,
    )
    result = compare(record, evidence)
    identity = [finding for finding in result.findings if finding.rule_id == "IDENTITY-CROSS-FIELD-001"]
    assert result.status == "FAIL"
    assert len(identity) == 1
    assert identity[0].field == "product_description_identity"
    assert identity[0].severity == "CRITICAL"
    assert identity[0].expected.startswith("Dell")
    assert identity[0].observed.startswith("Lenovo — ThinkPad")


def test_incidental_software_brand_is_not_an_identity_conflict() -> None:
    record = ListingRecord("", "", "MegaPC", "https://www.amazon.com/dp/B0HBDTJNJV", "B0HBDTJNJV", 0)
    evidence = collect_evidence(record, ROOT / "fixtures" / "listings")
    evidence = type(evidence)(
        url=evidence.url,
        title="MegaPC Dell Inspiron 15 Laptop with Microsoft Windows 11 Pro",
        description="Includes Microsoft Windows 11 Pro and works with common productivity software.",
        details={"Brand": "Dell", "Model": "Inspiron 15"},
        source="test",
    )
    result = compare(record, evidence)
    assert not [finding for finding in result.findings if finding.rule_id == "IDENTITY-CROSS-FIELD-001"]


def test_same_brand_different_model_family_is_critical() -> None:
    record = ListingRecord("", "", "MegaPC", "https://www.amazon.com/dp/B0HBDTJNJV", "B0HBDTJNJV", 0)
    evidence = collect_evidence(record, ROOT / "fixtures" / "listings")
    evidence = type(evidence)(
        url=evidence.url,
        title="MegaPC Dell Inspiron 15 Laptop",
        description="Created using a Dell Latitude business laptop.",
        details={"Brand": "Dell"},
        source="test",
    )
    result = compare(record, evidence)
    identity = [finding for finding in result.findings if finding.rule_id == "IDENTITY-CROSS-FIELD-001"]
    assert len(identity) == 1
    assert identity[0].expected == "Dell — Inspiron"
    assert identity[0].observed == "Dell — Latitude"
    assert identity[0].severity == "CRITICAL"

