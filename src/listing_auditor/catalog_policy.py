"""Seller-confirmed content policy shared by copy generation and audit checks.

Source: create-custom-pc-listing e2910c8fa93370105d53bcb49d3fc17f12b0ee1a.
Seller declarations are not independent OEM coverage or marketplace eligibility evidence.
"""
import re


POLICY_SOURCE = "https://github.com/Jeremy777777777/create-custom-pc-listing/blob/e2910c8fa93370105d53bcb49d3fc17f12b0ee1a/references/confirmed-catalog-defaults.md"
WARRANTY_TEMPLATE = (
    "MegaPC provides a 1-year limited warranty on the upgraded RAM and SSD components. "
    "The original {oem} manufacturer warranty remains valid on all remaining factory components, "
    "so you are covered on both the base machine and our upgrades. "
    "The original seal has been opened solely for upgrading purposes."
)


def identify_oem(text: str) -> str:
    matches = [(m.start(), brand) for brand in ("Dell", "Lenovo", "HP", "LG", "Acer", "ASUS", "Microsoft", "Samsung", "Apple") if (m := re.search(rf"\b{brand}\b", text, re.I))]
    return min(matches)[1] if matches else ""


def warranty(oem: str) -> str:
    return WARRANTY_TEMPLATE.format(oem=oem or "[[VERIFY OEM BRAND]]")


def has_capacity_options(text: str) -> bool:
    from .customization import option_groups
    return bool(option_groups(text))
