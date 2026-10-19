from html import unescape
from pathlib import Path

from listing_auditor.catalog_policy import has_capacity_options, warranty
from listing_auditor.compliance import check_compliance
from listing_auditor.copy_style import _canonical, _description, style_correction_findings
from listing_auditor.models import AuditResult, ERPRecord, Evidence, Finding, ListingRecord
from listing_auditor.report import write_reports
from openpyxl import load_workbook


def record(product='Dell QC24251 / All-in-One / 23.8" / Intel Core i5-14500T / 16GB DDR5 RAM / 512GB SSD / WiFi / Bluetooth / 1920x1080 / 60 Hz'):
    return ListingRecord(product, 'VA-215', 'MegaPC', 'https://www.amazon.com/dp/B0H9V9BKXS', 'B0H9V9BKXS', 1)


def test_creation_style_uses_one_base_configuration_and_identical_warranty(tmp_path):
    r = record()
    evidence = Evidence(r.url, title='Incorrect title', source='test')
    trigger = [Finding('model', r.product_name, 'Wrong', 'CRITICAL', 'Identity mismatch')]
    corrections = {f.field: f.corrected_value for f in style_correction_findings(r, evidence, None, trigger)}
    title, bullets, description = (corrections[k] for k in ('copy_title','copy_bullet_points','copy_product_description'))
    assert title.startswith('MegaPC Custom ') and title.endswith('Win 11 Pro')
    assert len(title) <= 200
    assert '16GB DDR5 RAM' in title and '512GB SSD' in title
    assert not has_capacity_options(title + bullets + description)
    assert len(bullets.split('\n\n')) == 5
    assert bullets.split('\n\n')[0] == warranty('Dell')
    assert unescape(description).endswith(warranty('Dell') + '</p>')
    assert 'software remain factory' not in description
    assert '[[VERIFY PREINSTALLED OS]]' not in description
    updated = Evidence(r.url, title=title, bullets=bullets.split('\n\n'), description=description, details={'Warranty Description':warranty('Dell')}, source='test')
    findings = check_compliance(r, updated)
    assert not any(f.rule_id.startswith(('CPC-WARRANTY','CPC-SCOPE','CPC-BASE','CPC-TITLE')) for f in findings)
    original = Evidence(r.url, title='Old title', bullets=['Old warranty'], description='Old description', details={'Warranty Description':'1 Year Manufacturer'}, source='test')
    checks = check_compliance(r, original)
    suggestions = style_correction_findings(r, original, None, checks)
    path = write_reports([AuditResult(r,'FAIL',checks + suggestions,original)], tmp_path)
    wb = load_workbook(path)
    assert wb['Safety&Compliance']['C6'].value == warranty('Dell')
    assert wb['Product Details']['L6'].value.startswith('<p><strong>MegaPC Custom ')
    assert wb['Product Details']['L3'].value == 'Old description'


def test_missing_conflicting_and_option_capacities_are_not_invented():
    for ram in ('8GB / 16GB / 32GB', '8 / 16 / 32GB', 'up to 64GB'):
        facts = _canonical(record(), ERPRecord('VA-215', {'ram':ram}, available=True))
        assert facts['ram'] == '[[VERIFY BASE RAM]]'
    conflict = _canonical(record(), ERPRecord('VA-215', {'ram':'32GB'}, available=True))
    assert conflict['ram'] == '[[VERIFY BASE RAM]]'
    missing = _canonical(record('Dell QC24251 / All-in-One / Intel Core i5-14500T'), None)
    assert missing['ram'] == '[[VERIFY BASE RAM]]'
    assert missing['storage'] == '[[VERIFY BASE INTERNAL STORAGE]]'
    assert missing['os'] == 'Windows 11 Pro'
    unknown_oem = _canonical(record('Unknown computer / All-in-One'), None)
    assert _description('MegaPC', unknown_oem) == ''


def test_copy_checks_find_capacity_lists_and_warranty_drift_without_negation_false_positive():
    r = record()
    evidence = Evidence(r.url, title='MegaPC Customized AIO, Created Using Dell QC24251, 8GB / 16GB / 32GB DDR5 RAM, 512GB / 1TB SSD, Windows 11 Pro', bullets=['Warranty applies'], description='Only RAM and storage are modified, with no software changes. Other hardware remains factory configured.', details={'Warranty Description':'1 Year Manufacturer'})
    rules = {f.rule_id for f in check_compliance(r,evidence)}
    assert {'CPC-BASE-001','CPC-TITLE-007','CPC-TITLE-008','CPC-WARRANTY-004','CPC-WARRANTY-005','CPC-WARRANTY-006'} <= rules
    assert 'CPC-SCOPE-001' not in rules
    for text in ('MegaPC upgraded the GPU.', 'The screen was modified.', 'Windows customized by MegaPC.'):
        assert any(f.rule_id == 'CPC-SCOPE-001' for f in check_compliance(r, Evidence(r.url,description=text)))


def test_va215_copyable_example_has_no_optional_or_unverified_specs():
    example = (Path(__file__).parents[1]/'examples/VA-215-product-description.html').read_text(encoding='utf-8').strip()
    assert '[[VERIFY' not in example
    assert '0.5TB' in example and '4TB' in example
    assert '512GB' not in example and '256GB' not in example
    assert 'IR webcam' not in example and 'Wi-Fi 6E' not in example
    assert example.startswith('<p><strong>MegaPC Custom ')
    assert unescape(example).endswith(warranty('Dell')+'</p>')
