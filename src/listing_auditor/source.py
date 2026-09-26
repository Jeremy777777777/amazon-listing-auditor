from __future__ import annotations

import csv
import io
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .models import ListingRecord


ASIN_RE = re.compile(r"(?:/dp/|/gp/product/)([A-Z0-9]{10})", re.I)


def _sheet_export_url(url: str) -> str:
    match = re.search(r"/spreadsheets/d/([\w-]+)", url)
    if not match:
        raise ValueError("Could not find a Google spreadsheet ID in --sheet-url")
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    fragment = urllib.parse.parse_qs(parsed.fragment)
    gid = (params.get("gid") or fragment.get("gid") or ["0"])[0]
    return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv&gid={gid}"


def download_sheet_csv(url: str) -> str:
    request = urllib.request.Request(
        _sheet_export_url(url),
        headers={"User-Agent": "amazon-listing-auditor/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read().decode("utf-8-sig")
    if "text/html" in content_type.lower() or payload.lstrip().startswith("<!DOCTYPE html"):
        raise PermissionError(
            "The Sheet CSV export was not readable. Publish/share the sheet for this runner "
            "or use --input with an exported CSV."
        )
    return payload


def load_records(
    *, input_path: Path | None = None, sheet_url: str | None = None,
    internal_id: str | None = None, product_name: str | None = None,
    amazon_url: str | None = None, seller: str = "Manual",
) -> list[ListingRecord]:
    if sum([bool(input_path), bool(sheet_url), bool(amazon_url)]) != 1:
        raise ValueError("Provide exactly one source: --input, --sheet-url, or --amazon-url")
    if amazon_url:
        if bool(internal_id) != bool(product_name):
            raise ValueError("Provide both --internal-id and --product-name for full matching, or omit both for URL-only review")
        asin_match = ASIN_RE.search(amazon_url or "")
        if not asin_match:
            raise ValueError("--amazon-url must contain a valid 10-character ASIN")
        return [ListingRecord((product_name or "").strip(), (internal_id or "").strip(), seller.strip() or "Unknown", amazon_url.strip(), asin_match.group(1).upper(), 0)]
    text = input_path.read_text(encoding="utf-8-sig") if input_path else download_sheet_csv(sheet_url or "")
    rows = list(csv.reader(io.StringIO(text)))
    return select_completed(rows)


def _find_header(rows: list[list[str]]) -> int:
    for index, row in enumerate(rows):
        if "Product Name" in row and "MegaPC Customized Listing" in row:
            return index
    raise ValueError("Could not find the tracker header row")


def select_completed(rows: list[list[str]]) -> list[ListingRecord]:
    header_index = _find_header(rows)
    header = rows[header_index]
    product_col = header.index("Product Name")
    sku_col = header.index("VL-")
    seller_status_cols = {
        "MegaPC": header.index("MegaPC Customized Listing"),
        "JTD": header.index("JTD Customized Listing"),
    }
    records: list[ListingRecord] = []
    for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        padded = row + [""] * (len(header) - len(row))
        for seller, status_col in seller_status_cols.items():
            link_col = status_col + 2
            if padded[status_col].strip().lower() != "completed":
                continue
            url = padded[link_col].strip()
            asin_match = ASIN_RE.search(url)
            if not asin_match:
                continue
            records.append(
                ListingRecord(
                    product_name=padded[product_col].strip(),
                    sku=padded[sku_col].strip(),
                    seller=seller,
                    url=url,
                    asin=asin_match.group(1).upper(),
                    row_number=row_number,
                )
            )
    return records
