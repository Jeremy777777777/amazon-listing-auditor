from __future__ import annotations

import argparse
from pathlib import Path

from .compare import compare
from .erp import load_erp_record
from .evidence import collect_evidence
from .image_audit import audit_images
from .report import write_reports
from .source import load_records


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="listing-auditor")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Audit completed customized listings")
    source = audit.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Tracker CSV export")
    source.add_argument("--sheet-url", help="Google Sheet URL")
    source.add_argument("--amazon-url", help="Amazon URL; works alone or with an internal ID and expected product")
    audit.add_argument("--internal-id", help="Optional internal product ID; requires --product-name")
    audit.add_argument("--product-name", help="Manual expected product name/specification")
    audit.add_argument("--seller", default="Manual", help="Seller label for manual input")
    audit.add_argument("--erp-export", type=Path, help="ERP CSV or JSON export (safe fallback when API auth is unavailable)")
    audit.add_argument("--erp-graphql-url", help="Authenticated ERP GraphQL endpoint")
    audit.add_argument("--image-observations", type=Path, help="Optional slot-by-slot OCR/visual review JSON")
    audit.add_argument("--skip-image-audit", action="store_true", help="Skip image checks (not recommended for final QA)")
    audit.add_argument("--fixtures", type=Path, help="Directory with <ASIN>.json evidence files")
    audit.add_argument("--out", type=Path, default=Path("reports"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    records = load_records(
        input_path=args.input,
        sheet_url=args.sheet_url,
        internal_id=args.internal_id,
        product_name=args.product_name,
        amazon_url=args.amazon_url,
        seller=args.seller,
    )
    results = []
    for record in records:
        erp = load_erp_record(record.sku, export_path=args.erp_export, graphql_url=args.erp_graphql_url) if record.sku and (args.erp_export or args.erp_graphql_url) else None
        evidence = collect_evidence(record, args.fixtures)
        image_findings = [] if args.skip_image_audit else audit_images(record, evidence, erp, args.image_observations)
        results.append(compare(record, evidence, erp, image_findings))
    excel_path = write_reports(results, args.out)
    failed = sum(result.status == "FAIL" for result in results)
    review = sum(result.status == "REVIEW" for result in results)
    print(f"Audited {len(results)} listings: {failed} failed, {review} need review. Excel backup: {excel_path}")
    return 2 if failed else (1 if review else 0)


if __name__ == "__main__":
    raise SystemExit(main())
