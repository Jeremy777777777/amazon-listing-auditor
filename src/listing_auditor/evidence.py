from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from .models import Evidence, ListingRecord


class _AmazonParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = ""
        self.title = ""
        self.description_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        identity = " ".join(filter(None, [attr.get("id"), attr.get("class")]))
        if tag == "title" or re.search(r"productTitle|feature-bullets|productDescription", identity):
            self._capture = identity or tag

    def handle_endtag(self, tag: str) -> None:
        if tag in {"title", "div", "ul", "span"}:
            self._capture = ""

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean or not self._capture:
            return
        if self._capture == "title" and not self.title:
            self.title = clean
        else:
            self.description_parts.append(clean)


def _from_fixture(path: Path) -> Evidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Evidence(
        url=data.get("url", ""),
        title=data.get("title", ""),
        bullets=data.get("bullets", []),
        description=data.get("description", ""),
        source=data.get("source", f"fixture:{path.name}"),
        captured_at=data.get("captured_at", ""),
    )


def collect_evidence(record: ListingRecord, fixtures: Path | None = None) -> Evidence:
    fixture = fixtures / f"{record.asin}.json" if fixtures else None
    if fixture and fixture.exists():
        return _from_fixture(fixture)
    try:
        request = urllib.request.Request(
            record.url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; amazon-listing-auditor/0.1; +https://github.com/)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = _AmazonParser()
        parser.feed(html)
        text = " ".join(parser.description_parts)
        if not parser.title or "captcha" in (parser.title + text).lower():
            raise RuntimeError("Amazon returned an incomplete or challenge page")
        return Evidence(url=record.url, title=parser.title, description=text, source="Amazon live page")
    except Exception as exc:  # network and challenge pages are review states, not passes
        return Evidence(
            url=record.url,
            source="Amazon live page",
            available=False,
            error=f"{type(exc).__name__}: {exc}",
        )

