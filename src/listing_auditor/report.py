from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import AuditResult


def write_reports(results: list[AuditResult], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["status", "severity", "seller", "sku", "asin", "field", "expected", "observed", "url", "reason"])
        for result in results:
            if not result.findings:
                writer.writerow([result.status, "", result.listing.seller, result.listing.sku, result.listing.asin, "", "", "", result.listing.url, ""])
            for finding in result.findings:
                writer.writerow([result.status, finding.severity, result.listing.seller, result.listing.sku, result.listing.asin, finding.field, finding.expected, finding.observed, result.listing.url, finding.reason])

    lines = ["# Amazon Listing Audit Report", "", f"Listings checked: {len(results)}", ""]
    for result in results:
        lines.extend([f"## {result.status}: {result.listing.asin} ({result.listing.seller})", "", f"- Expected: {result.listing.product_name}", f"- URL: {result.listing.url}", f"- Sheet row: {result.listing.row_number}"])
        if not result.findings:
            lines.append("- No mismatch found in available evidence.")
        for finding in result.findings:
            lines.append(f"- **{finding.severity} / {finding.field}** — expected `{finding.expected}`, observed `{finding.observed}`. {finding.reason}")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")

