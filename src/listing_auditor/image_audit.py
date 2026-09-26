from __future__ import annotations

import io
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from .models import ERPRecord, Evidence, Finding, ListingRecord


REFERENCE = "references/image-audit-rules.md"
SUPPORTED_FORMATS = {"JPEG", "PNG", "TIFF", "GIF"}
PROHIBITED_FLAGS = {
    "contains_price": "price or promotion",
    "contains_rating": "rating, testimonial, or review excerpt",
    "contains_amazon_badge": "Amazon name, logo, badge, or confusingly similar graphic",
    "contains_contact_info": "seller/store contact information",
}


def _finding(rule_id: str, field: str, expected: str, observed: str, severity: str, reason: str, source: str, correction: str) -> Finding:
    return Finding(field, expected, observed, severity, reason, source, "", correction, rule_id, REFERENCE)


def _download(url_or_path: str) -> bytes:
    path = Path(url_or_path)
    if path.exists():
        return path.read_bytes()
    request = urllib.request.Request(url_or_path, headers={"User-Agent": "Mozilla/5.0 (compatible; amazon-listing-auditor/0.3)"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def _average_hash(image: Image.Image) -> int:
    pixels = list(image.convert("L").resize((8, 8)).getdata())
    average = sum(pixels) / len(pixels)
    value = 0
    for pixel in pixels:
        value = (value << 1) | int(pixel >= average)
    return value


def _white_border_ratio(image: Image.Image) -> float:
    rgb = image.convert("RGB")
    width, height = rgb.size
    step = max(1, min(width, height) // 200)
    samples = []
    for x in range(0, width, step):
        samples.extend([rgb.getpixel((x, 0)), rgb.getpixel((x, height - 1))])
    for y in range(0, height, step):
        samples.extend([rgb.getpixel((0, y)), rgb.getpixel((width - 1, y))])
    return sum(all(channel >= 248 for channel in pixel) for pixel in samples) / max(1, len(samples))


def _subject_extent(image: Image.Image) -> float:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, background).convert("L").point(lambda value: 255 if value > 12 else 0)
    bbox = difference.getbbox()
    if not bbox:
        return 0.0
    return max((bbox[2] - bbox[0]) / rgb.width, (bbox[3] - bbox[1]) / rgb.height)


def _expected_brand(record: ListingRecord) -> str:
    match = re.match(r"\s*([A-Za-z][A-Za-z -]+?)\s+(?=\w*[0-9]|ThinkPad|Latitude|EliteBook|Gram|Yoga|ROG|Victus)", record.product_name)
    return match.group(1).strip() if match else record.product_name.split()[0]


def _load_observations(path: Path | None, record: ListingRecord) -> list[dict[str, Any]]:
    if not path:
        return []
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        scoped = [item for item in payload if not item.get("asin") or str(item.get("asin")).casefold() == record.asin.casefold()]
        return scoped
    listings = payload.get("listings")
    if isinstance(listings, dict):
        listing = listings.get(record.asin) or listings.get(record.sku) or {}
        return listing if isinstance(listing, list) else listing.get("images", [])
    if payload.get("asin") and str(payload.get("asin")).casefold() != record.asin.casefold():
        return []
    if payload.get("internal_id") and str(payload.get("internal_id")).casefold() != record.sku.casefold():
        return []
    return payload.get("images", [])


def audit_images(
    record: ListingRecord,
    evidence: Evidence,
    erp: ERPRecord | None = None,
    observations_path: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    urls = evidence.image_urls[:9]
    if not urls:
        return [_finding(
            "IMG-GALLERY-001", "image_gallery", "MAIN plus PT01-PT08 available for review", "No gallery images were captured",
            "REVIEW", "Image compliance and product-image consistency could not be evaluated.", evidence.source,
            "Capture the live gallery or provide local image paths and a visual-observation file.",
        )]
    if len(urls) < 9:
        findings.append(_finding(
            "IMG-GALLERY-002", "image_gallery_count", "9 internal gallery slots", str(len(urls)),
            "REVIEW", "The captured gallery does not cover the internal MAIN plus PT01-PT08 standard.", evidence.source,
            "Confirm whether images are missing, hidden, or still need production.",
        ))

    hashes: list[tuple[int, str]] = []
    for index, source in enumerate(urls):
        slot = "MAIN" if index == 0 else f"PT{index:02d}"
        try:
            with Image.open(io.BytesIO(_download(source))) as image:
                width, height = image.size
                image_format = (image.format or "").upper()
                if image_format not in SUPPORTED_FORMATS:
                    findings.append(_finding("IMG-TECH-001", f"image_{slot}_format", "JPEG, PNG, TIFF, or non-animated GIF", image_format or "Unknown", "HIGH", "Unsupported image format.", source, "Export the image using a supported format."))
                longest = max(width, height)
                if longest < 500 or longest > 10000:
                    findings.append(_finding("IMG-TECH-002", f"image_{slot}_dimensions", "Longest side 500-10,000 px", f"{width}x{height}", "HIGH", "Image dimensions are outside Amazon's technical range.", source, "Replace with a correctly sized original; do not upscale a small source."))
                elif longest < 1000:
                    findings.append(_finding("IMG-TECH-003", f"image_{slot}_zoom", "At least 1,000 px on longest side", f"{width}x{height}", "REVIEW", "The image may not enable Amazon zoom.", source, "Use an original image at least 1,000 px on the longest side."))
                if abs(width - height) / max(width, height) > 0.02:
                    findings.append(_finding("IMG-TECH-004", f"image_{slot}_aspect_ratio", "1:1 internal gallery standard", f"{width}x{height}", "REVIEW", "The image is not square and may not match the internal gallery standard.", source, "Review composition and export a square version without distorting the product."))
                if slot == "MAIN":
                    border_ratio = _white_border_ratio(image)
                    if border_ratio < 0.92:
                        findings.append(_finding("IMG-MAIN-001", "image_MAIN_background", "Pure white RGB 255/255/255 background", f"White-border ratio {border_ratio:.1%}", "HIGH", "The main-image border is not predominantly pure white.", source, "Replace the background with pure white without changing the product."))
                    extent = _subject_extent(image)
                    if extent < 0.75 or extent > 0.95:
                        findings.append(_finding("IMG-MAIN-002", "image_MAIN_fill", "Product fills approximately 85% of frame", f"Detected extent {extent:.1%}", "REVIEW", "Main-image product framing may be too small or too tightly cropped.", source, "Reframe the complete product near the 85% internal target."))
                current_hash = _average_hash(image)
                for previous_hash, previous_slot in hashes:
                    if (current_hash ^ previous_hash).bit_count() <= 3:
                        findings.append(_finding("IMG-GALLERY-003", f"image_{slot}_duplicate", "Distinct gallery content", f"Near-duplicate of {previous_slot}", "REVIEW", "Two gallery slots appear visually duplicated.", source, "Confirm the intended slot role and replace duplicate content if needed."))
                        break
                hashes.append((current_hash, slot))
        except Exception as exc:
            findings.append(_finding("IMG-EVIDENCE-001", f"image_{slot}_evidence", "Readable image file", f"{type(exc).__name__}: {exc}", "REVIEW", "The image could not be downloaded or decoded.", source, "Provide a readable local image or refresh the captured gallery URL."))

    try:
        observations = _load_observations(observations_path, record)
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        findings.append(_finding(
            "IMG-EVIDENCE-002", "image_visual_observations", "Readable image-observations JSON",
            f"{type(exc).__name__}: {exc}", "REVIEW", "The semantic visual-review input could not be read.",
            str(observations_path), "Correct the JSON file and rerun the audit.",
        ))
        return findings
    if not observations:
        findings.append(_finding(
            "IMG-VISUAL-001", "image_visual_review", "Slot-by-slot visual/OCR observations", "No visual-observation file supplied",
            "REVIEW", "Pixel checks cannot reliably verify image text, OEM identity, ports, accessories, badges, or provenance.", evidence.source,
            "Review MAIN and PT images visually or provide image-observations JSON using the documented schema.",
        ))
        return findings

    expected_brand = _expected_brand(record)
    expected_corpus = " ".join([record.product_name, *list((erp.fields if erp and erp.available else {}).values())]).casefold()
    for index, observation in enumerate(observations):
        slot = str(observation.get("slot") or ("MAIN" if index == 0 else f"PT{index:02d}"))
        source = str(observation.get("url") or f"visual observation: {slot}")
        if slot == "MAIN" and (observation.get("main_has_overlay") or str(observation.get("ocr_text", "")).strip()):
            findings.append(_finding("IMG-MAIN-003", "image_MAIN_overlay", "No added text, graphics, badges, watermarks, or logo overlay", str(observation.get("ocr_text") or "Overlay detected"), "HIGH", "The MAIN image contains a prohibited overlay.", source, "Remove all added overlays from MAIN."))
        detected_brand = str(observation.get("detected_brand", "")).strip()
        if detected_brand and expected_brand.casefold() not in detected_brand.casefold():
            findings.append(_finding("IMG-IDENTITY-001", f"image_{slot}_brand", expected_brand, detected_brand, "CRITICAL", "The image appears to show a different OEM brand than the expected product.", source, "Replace with imagery of the exact verified base product."))
        identity = str(observation.get("product_identity", "")).strip()
        if identity and identity.casefold() not in expected_corpus:
            findings.append(_finding("IMG-IDENTITY-002", f"image_{slot}_identity", record.product_name, identity, "CRITICAL", "The observed product identity is not supported by the input or ERP record.", source, "Replace the image or correct the product mapping after manual verification."))
        for flag, label in PROHIBITED_FLAGS.items():
            if observation.get(flag):
                findings.append(_finding("IMG-CONTENT-001", f"image_{slot}_{flag}", f"No {label}", label, "HIGH", "The gallery image contains prohibited promotional or marketplace content.", source, "Remove the prohibited content and regenerate the image from licensed assets."))
        claims = observation.get("claims") or {}
        if isinstance(claims, dict):
            for field, value in claims.items():
                value_text = str(value).strip()
                if value_text and re.sub(r"\W+", "", value_text.casefold()) not in re.sub(r"\W+", "", expected_corpus):
                    findings.append(_finding("IMG-CLAIM-001", f"image_{slot}_{field}", "Claim supported by input/ERP evidence", value_text, "HIGH", "Image text contains a specification not supported by the mapped product evidence.", source, "Correct or remove the unsupported image claim."))
        if not observation.get("licensed_provenance"):
            findings.append(_finding("IMG-RIGHTS-001", f"image_{slot}_provenance", "Documented licensed asset provenance", "Missing", "REVIEW", "Commercial-use rights cannot be confirmed from the observation record.", source, "Record authorized OEM media, seller-owned photography, or original infographic provenance."))
    return findings
