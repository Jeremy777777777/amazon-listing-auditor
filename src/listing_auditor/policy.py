"""Seller assertions adapted from the pinned generation policy, not Amazon approval."""
from __future__ import annotations

import re
from html import unescape

from .models import Evidence, ListingRecord

WARRANTY_TEMPLATE = (
    "MegaPC provides a 1-year limited warranty on the upgraded RAM and SSD components. "
    "The original [OEM brand] manufacturer warranty remains valid on all remaining factory "
    "components, so you are covered on both the base machine and our upgrades. "
    "The original seal has been opened solely for upgrading purposes."
)
OEM_BRANDS = ("Dell", "Lenovo", "HP", "LG", "Acer", "ASUS", "Microsoft", "Samsung", "Apple")


def seller_brand(record: ListingRecord, evidence: Evidence) -> str:
    label = record.seller.strip().casefold()
    if label in {"megapc", "jtd", "j-tech digital"}:
        return "MegaPC" if label == "megapc" else "J-Tech Digital"
    if label not in {"", "manual", "unknown"}:
        return record.seller.strip()
    if re.match(r"MegaPC\b", evidence.title, re.I):
        return "MegaPC"
    if re.match(r"(?:J-Tech Digital|JTD)\b", evidence.title, re.I):
        return "J-Tech Digital"
    return ""


def oem_brand(text: str) -> str:
    matches = [(m.start(), brand) for brand in OEM_BRANDS
               if (m := re.search(rf"\b{brand}\b", text, re.I))]
    return min(matches)[1] if matches else ""


def visible_text(text: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]*>", " ", text)).split())


def warranty(brand: str) -> str:
    return WARRANTY_TEMPLATE.replace("[OEM brand]", brand or "[[VERIFY OEM BRAND]]")
