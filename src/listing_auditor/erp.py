from __future__ import annotations

import csv
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from .models import ERPRecord


DEFAULT_GRAPHQL_URL = "https://hasura-cold-flower-6661.fly.dev/v1/graphql"

QUERY = """
query AuditProduct($where: ProductTableSchemaBoolExp, $limit: Int = 2) {
  productTableFilterable(args: {}, where: $where, limit: $limit) {
    createdAt id model name sku mpn thumbnail isSerialNumberRequired
    brand { name }
    category { name }
    specification {
      color ram cpu hdd os dvd graphicCard screenSize model touchable ssd ssd2
      fingerprint bluetooth resolution backlit refreshRate wifi powerSupply
      optaneMemory formFactor
    }
  }
}
"""


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _flatten(item: dict[str, Any]) -> dict[str, str]:
    fields = {key: _clean(value) for key, value in item.items() if key not in {"brand", "category", "specification"}}
    for key in ("brand", "category"):
        nested = item.get(key) or {}
        fields[key] = _clean(nested.get("name")) if isinstance(nested, dict) else _clean(nested)
    specification = item.get("specification") or {}
    if isinstance(specification, list):
        specification = specification[0] if specification else {}
    if isinstance(specification, dict):
        fields.update({key: _clean(value) for key, value in specification.items()})
    return {key: value for key, value in fields.items() if value}


def _from_export(internal_id: str, path: Path) -> ERPRecord:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = payload if isinstance(payload, list) else payload.get("products", payload.get("data", []))
    else:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    for row in rows:
        fields = _flatten(row)
        if fields.get("sku", "").casefold() == internal_id.casefold() or fields.get("internal_id", "").casefold() == internal_id.casefold():
            return ERPRecord(internal_id, fields, f"ERP export: {path.name}", True)
    return ERPRecord(internal_id, source=f"ERP export: {path.name}", error="Internal ID not found in ERP export")


def _from_graphql(internal_id: str, url: str) -> ERPRecord:
    headers = {"Content-Type": "application/json", "User-Agent": "amazon-listing-auditor/0.2"}
    if os.getenv("ERP_AUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['ERP_AUTH_TOKEN']}"
    if os.getenv("ERP_ADMIN_SECRET"):
        headers["x-hasura-admin-secret"] = os.environ["ERP_ADMIN_SECRET"]
    body = json.dumps({"query": QUERY, "variables": {"where": {"sku": {"_eq": internal_id}}, "limit": 2}}).encode()
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL query failed"))
    rows = payload.get("data", {}).get("productTableFilterable", [])
    if not rows:
        return ERPRecord(internal_id, source="ERP GraphQL", error="Internal ID not found in ERP")
    if len(rows) > 1:
        return ERPRecord(internal_id, source="ERP GraphQL", error="Multiple ERP products matched this internal ID")
    return ERPRecord(internal_id, _flatten(rows[0]), "ERP GraphQL", True)


def load_erp_record(internal_id: str, *, export_path: Path | None = None, graphql_url: str | None = None) -> ERPRecord:
    try:
        if export_path:
            return _from_export(internal_id, export_path)
        if graphql_url:
            return _from_graphql(internal_id, graphql_url)
        return ERPRecord(internal_id, source="ERP", error="ERP source not configured")
    except Exception as exc:
        return ERPRecord(internal_id, source="ERP", error=f"{type(exc).__name__}: {exc}")
