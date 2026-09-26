import csv
from pathlib import Path

from listing_auditor.compare import compare
from listing_auditor.models import Evidence
from listing_auditor.source import load_records


ROOT = Path(__file__).parents[1]


def test_selects_both_completed_seller_links() -> None:
    records = load_records(input_path=ROOT / "examples" / "completed-listings.csv")
    assert [(record.seller, record.asin) for record in records] == [
        ("MegaPC", "B0HBDTJNJV"),
        ("JTD", "B0HBG12FK2"),
    ]


def test_manual_input_mode() -> None:
    records = load_records(
        internal_id="VL-1249",
        product_name="Dell 15 DC15250",
        amazon_url="https://www.amazon.com/dp/B0HBDTJNJV",
        seller="MegaPC",
    )
    assert [(record.sku, record.asin, record.seller) for record in records] == [
        ("VL-1249", "B0HBDTJNJV", "MegaPC")
    ]


def test_url_only_input_mode() -> None:
    records = load_records(amazon_url="https://www.amazon.com/dp/B0HBDTJNJV")
    assert [(record.sku, record.product_name, record.asin) for record in records] == [
        ("", "", "B0HBDTJNJV")
    ]
    result = compare(records[0], Evidence(
        url=records[0].url,
        title="MegaPC Customized Laptop Created Using Dell 15 DC15250, 16GB DDR5, 1TB SSD",
        bullets=["Original manufacturer warranty status and MegaPC upgrade warranty are documented."],
        description="RAM and storage customized by MegaPC.",
        source="test",
    ))
    assert any(finding.field == "input_baseline" for finding in result.findings)
