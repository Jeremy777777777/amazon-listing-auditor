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

