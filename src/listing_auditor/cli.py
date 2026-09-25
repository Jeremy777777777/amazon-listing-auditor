from __future__ import annotations

import argparse
from pathlib import Path

from .compare import compare
from .evidence import collect_evidence
from .report import write_reports
from .source import load_records


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="listing-auditor")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Audit completed customized listings")
    source = audit.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Tracker CSV export")
    source.add_argument("--sheet-url", help="Google Sheet URL")
    audit.add_argument("--fixtures", type=Path, help="Directory with <ASIN>.json evidence files")
    audit.add_argument("--out", type=Path, default=Path("reports"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    records = load_records(input_path=args.input, sheet_url=args.sheet_url)
    results = [compare(record, collect_evidence(record, args.fixtures)) for record in records]
    write_reports(results, args.out)
    failed = sum(result.status == "FAIL" for result in results)
    review = sum(result.status == "REVIEW" for result in results)
    print(f"Audited {len(results)} listings: {failed} failed, {review} need review. Report: {args.out / 'report.md'}")
    return 2 if failed else (1 if review else 0)


if __name__ == "__main__":
    raise SystemExit(main())

