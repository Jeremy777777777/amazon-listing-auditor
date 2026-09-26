import csv
from pathlib import Path

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
