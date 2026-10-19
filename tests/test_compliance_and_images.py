import json
from pathlib import Path

from PIL import Image, ImageDraw

from listing_auditor.compliance import check_compliance
from listing_auditor.copy_style import style_correction_findings
from listing_auditor.evidence import _AmazonParser
from listing_auditor.image_audit import audit_images
from listing_auditor.models import Evidence, ListingRecord


def _record() -> ListingRecord:
    return ListingRecord(
        product_name='Dell 15 DC15250 / Laptop / 15.6" / Touchscreen / Black / Intel Core i7-1355U / Intel UHD Graphics / 1920x1080 / 60 Hz',
        sku="VL-1249",
        seller="MegaPC",
        url="https://www.amazon.com/dp/B0HBDTJNJV",
        asin="B0HBDTJNJV",
        row_number=34,
    )


def test_custom_pc_compliance_rules() -> None:
    evidence = Evidence(
        url="https://www.amazon.com/dp/B0HBDTJNJV",
        title="Lenovo ThinkPad X1 Carbon Gen 13",
        bullets=["Fast business performance"],
        description="Windows customized by MegaPC.",
        source="test fixture",
    )
    fields = {finding.field for finding in check_compliance(_record(), evidence)}
    assert {
        "compliance_title_brand",
        "compliance_title_custom",
        "compliance_title_ram",
        "compliance_title_storage",
        "compliance_bullet_1_warranty",
        "compliance_customization_scope",
    } <= fields


def test_image_technical_and_visual_rules(tmp_path: Path) -> None:
    main_path = tmp_path / "MAIN.png"
    main = Image.new("RGB", (2000, 2000), "white")
    ImageDraw.Draw(main).rectangle((150, 450, 1850, 1550), fill="#222222")
    main.save(main_path)
    pt_path = tmp_path / "PT01.png"
    Image.new("RGB", (400, 300), "navy").save(pt_path)
    observations_path = tmp_path / "observations.json"
    observations_path.write_text(json.dumps({"images": [{
        "slot": "MAIN",
        "url": str(main_path),
        "ocr_text": "LIMITED TIME PRICE",
        "main_has_overlay": True,
        "detected_brand": "Lenovo",
        "product_identity": "ThinkPad X1 Carbon Gen 13",
        "contains_price": True,
        "claims": {"cpu": "Intel Core Ultra 7 265U"},
        "licensed_provenance": ""
    }]}), encoding="utf-8")
    evidence = Evidence(
        url=_record().url,
        title="MegaPC Customized Laptop, Created Using Dell 15 DC15250",
        description="Verified listing text",
        image_urls=[str(main_path), str(pt_path)],
        source="image fixture",
    )
    fields = {finding.field for finding in audit_images(_record(), evidence, observations_path=observations_path)}
    assert {
        "image_gallery_count",
        "image_PT01_dimensions",
        "image_PT01_aspect_ratio",
        "image_MAIN_overlay",
        "image_MAIN_brand",
        "image_MAIN_identity",
        "image_MAIN_contains_price",
        "image_MAIN_cpu",
        "image_MAIN_provenance",
    } <= fields


def test_amazon_parser_captures_bullets_and_gallery_images() -> None:
    parser = _AmazonParser()
    parser.feed('''
      <span id="productTitle">MegaPC Customized Laptop</span>
      <div id="feature-bullets"><ul><li>OEM warranty remains valid.</li></ul></div>
      <img id="landingImage" class="a-dynamic-image"
        data-old-hires="https://m.media-amazon.com/images/I/MAIN.jpg"
        data-a-dynamic-image='{"https://m.media-amazon.com/images/I/PT01.jpg":[1500,1500]}' />
    ''')
    assert parser.title == "MegaPC Customized Laptop"
    assert parser.bullets == ["OEM warranty remains valid."]
    assert parser.image_urls == [
        "https://m.media-amazon.com/images/I/MAIN.jpg",
        "https://m.media-amazon.com/images/I/PT01.jpg",
    ]


def test_style_aligned_copy_corrections() -> None:
    evidence = Evidence(
        url=_record().url,
        title="Lenovo ThinkPad X1 Carbon Gen 13",
        bullets=["Fast business performance"],
        description="Generic description",
        source="test fixture",
    )
    findings = style_correction_findings(_record(), evidence, None, check_compliance(_record(), evidence))
    corrections = {finding.field: finding.corrected_value for finding in findings}
    assert corrections["copy_title"].startswith("MegaPC Customized Laptop, Created Using Dell 15 DC15250")
    assert corrections["copy_bullet_points"].startswith("1. WARRANTY:")
    description = corrections["copy_product_description"]
    assert "<p><strong>Memory &amp; Storage, Customized by MegaPC</strong><br>\n" in description
    assert description.split("\n\n")[-1].startswith("<p><strong>Warranty</strong><br>\n")
    assert description.endswith("</p>")
    assert "**" not in description and "\\" not in description


def test_description_escapes_text_and_preserves_paragraph_structure():
    from html import unescape
    from listing_auditor.copy_style import _canonical, _description

    facts = _canonical(_record(), None)
    facts["screen"] = '23.8" FHD <panel> & display'
    description = _description("MegaPC", facts)
    paragraphs = description.split("\n\n")
    assert all(p.startswith("<p><strong>") and p.endswith("</p>") for p in paragraphs)
    assert "<br>" not in paragraphs[0]
    assert all("</strong><br>\n" in p for p in paragraphs[1:])
    assert '23.8&quot; FHD &lt;panel&gt; &amp; display' in description
    assert facts["screen"] in unescape(description)
    assert "[[VERIFY RAM OPTIONS]]" in description
