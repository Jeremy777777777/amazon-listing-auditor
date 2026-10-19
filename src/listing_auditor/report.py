from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from .models import AuditResult


HEADERS = [
    "严重程度", "问题类型", "Rule ID / Reference", "产品名称", "内部编号", "Seller", "ASIN",
    "影响位置 / 字段", "错误或歧义内容", "已核实 / 预期内容",
    "建议修改内容", "问题说明", "Amazon Reference", "Input / ERP Reference",
    "证据摘录", "人工审核状态", "人工最终修改 / 备注", "审核人", "审核日期",
]


def _issue_type(field: str, severity: str) -> str:
    if field.startswith("compliance"):
        return "合规风险"
    if field.startswith("image_"):
        return "图片问题"
    if field.startswith("copy_"):
        return "文案修改建议"
    if field in {"brand", "model"}:
        return "上下文不对应"
    if field in {"evidence", "erp_evidence"} or severity == "REVIEW":
        return "证据不足 / 有歧义"
    return "具体规格错误"


def _rows(results: list[AuditResult]) -> list[list[str]]:
    rows: list[list[str]] = []
    for result in results:
        for finding in result.findings:
            rows.append([
                finding.severity,
                _issue_type(finding.field, finding.severity),
                " — ".join(value for value in [finding.rule_id, finding.reference] if value),
                result.listing.product_name or result.evidence.title or f"Amazon ASIN {result.listing.asin}",
                result.listing.sku,
                result.listing.seller,
                result.listing.asin,
                finding.field,
                finding.observed,
                finding.erp_value or finding.expected,
                finding.corrected_value,
                finding.reason,
                result.listing.url,
                f"Input: {finding.expected}; ERP: {finding.erp_value or 'not confirmed'}",
                f"{finding.evidence_source}: {finding.observed}",
                "待审核",
                "",
                "",
                "",
            ])
    return rows


def _write_excel(results: list[AuditResult], path: Path) -> None:
    from .template_report import write_template_workbook

    write_template_workbook(results, path)


def write_reports(results: list[AuditResult], out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "source-evidence.json").write_text(json.dumps([
        {
            "internal_id": result.listing.sku,
            "asin": result.listing.asin,
            "seller": result.listing.seller,
            "amazon_url": result.listing.url,
            "amazon_evidence": result.evidence.__dict__,
            "erp_evidence": result.erp.__dict__ if result.erp else None,
        }
        for result in results
    ], indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(_rows(results))

    lines = ["# Amazon Listing Audit Report", "", f"Listings checked: {len(results)}", ""]
    for result in results:
        lines.extend([f"## {result.status}: {result.listing.asin} ({result.listing.seller})", "", f"- Expected: {result.listing.product_name}", f"- Internal ID: {result.listing.sku}", f"- URL: {result.listing.url}"])
        if not result.findings:
            lines.append("- No mismatch found in available evidence.")
        for finding in result.findings:
            lines.append(f"- **{finding.severity} / {finding.field}** — input `{finding.expected}`, Amazon `{finding.observed}`, ERP `{finding.erp_value}`. {finding.reason}")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    excel_path = out / "listing-audit-review.xlsx"
    _write_excel(results, excel_path)
    return excel_path


def _product_folder(result: AuditResult) -> str:
    raw = result.listing.sku.strip() or f"UNMAPPED-{result.listing.asin}"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    return safe or f"UNMAPPED-{result.listing.asin}"


def write_product_packages(results: list[AuditResult], output_root: Path) -> list[Path]:
    grouped: dict[str, list[AuditResult]] = defaultdict(list)
    for result in results:
        grouped[_product_folder(result)].append(result)
    return [write_reports(group, output_root / folder) for folder, group in sorted(grouped.items())]
