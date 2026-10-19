"""Normalize observed Customize choices; never infer them from title copy or platform limits."""
from __future__ import annotations

import re
from datetime import datetime
from .models import Evidence


def options(evidence: Evidence, kind: str) -> list[str]:
    capture = evidence.customization
    if not isinstance(capture, dict) or capture.get('available') is not True or not isinstance(capture.get('source'),str) or not capture.get('source') or not capture.get('captured_at'):
        return []
    try:
        datetime.fromisoformat(str(capture['captured_at']).replace('Z','+00:00'))
    except (ValueError,TypeError):
        return []
    asin = re.search(r'/dp/([A-Z0-9]{10})', evidence.url, re.I)
    if not asin or str(capture.get('asin', '')).upper() != asin[1].upper(): return []
    choices = capture.get('options', {})
    if not isinstance(choices, dict): return []
    values = choices.get(kind, [])
    if not isinstance(values, list) or not values: return []
    normalized = []
    for value in values:
        match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(GB|TB)\s*', str(value), re.I)
        if not match or float(match[1]) <= 0: return []
        number = float(match[1])
        # Storage capacity units are decimal; 0.5TB is 500GB, never silently 512GB.
        text = f'{number:g}{match[2].upper()}'
        if text not in normalized: normalized.append(text)
    return normalized


def capacity_values(text: str) -> set[tuple[float, str]]:
    return {(float(number), unit.upper()) for number, unit in re.findall(r'(\d+(?:\.\d+)?)\s*(GB|TB)\b', text, re.I)}


def option_groups(text: str) -> list[tuple[set[tuple[float, str]], str]]:
    token = r'\d+(?:\.\d+)?\s*(?:GB|TB)?'
    pattern = rf'\b{token}(?:\s*(?:/|,|\bor\b)\s*{token})+'
    groups = []
    for match in re.finditer(pattern, text, re.I):
        parts = re.findall(r'(\d+(?:\.\d+)?)\s*(GB|TB)?', match[0], re.I)
        last_unit = next((unit.upper() for _, unit in reversed(parts) if unit), '')
        if not last_unit: continue
        values = {(float(number), unit.upper() if unit else last_unit) for number, unit in parts}
        after = text[match.end():match.end()+35]
        before = text[max(0,match.start()-25):match.start()]
        kind = 'ram' if re.search(r'^(?:\s|DDR\d|LPDDR\d)*(?:RAM|memory)', after, re.I) else 'storage' if re.search(r'^\s*(?:SSD|NVMe|HDD|storage)', after, re.I) else ''
        if not kind:
            kind = 'ram' if re.search(r'(?:RAM|memory)\s*(?:options)?\s*:?\s*$',before,re.I) else 'storage' if re.search(r'(?:SSD|storage)\s*(?:options)?\s*:?\s*$',before,re.I) else ''
        groups.append((values, kind))
    return groups
