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
        self._capture_depth = 0
        self._depth = 0
        self._in_title = False
        self._product_title_depth = 0
        self._product_title_parts: list[str] = []
        self._feature_depth = 0
        self._bullet_depth = 0
        self._bullet_parts: list[str] = []
        self.title = ""
        self.bullets: list[str] = []
        self.description_parts: list[str] = []
        self.details: dict[str, str] = {}
        self.image_urls: list[str] = []
        self._row: list[str] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._depth += 1
        attr = dict(attrs)
        identity = " ".join(filter(None, [attr.get("id"), attr.get("class")]))
        if tag == "title":
            self._in_title = True
        if re.search(r"productTitle", identity, re.I):
            self._product_title_depth = self._depth
        if re.search(r"feature-bullets", identity, re.I):
            self._feature_depth = self._depth
        if self._feature_depth and tag == "li":
            self._bullet_depth = self._depth
            self._bullet_parts = []
        if not self._capture_depth and (tag == "title" or re.search(r"productTitle|feature-bullets|productDescription|productOverview|productDetails|detailBullets|techSpec|prodDetails|product-information", identity, re.I)):
            self._capture_depth = self._depth
        if self._capture_depth and tag in {"th", "td", "dt", "dd"}:
            self._in_cell = True
            self._cell_parts = []
        if tag == "img":
            candidates = [attr.get("data-old-hires", "")]
            dynamic = attr.get("data-a-dynamic-image", "")
            if dynamic:
                try:
                    candidates.extend(json.loads(dynamic).keys())
                except (json.JSONDecodeError, AttributeError):
                    pass
            if re.search(r"landingImage|a-dynamic-image", identity, re.I):
                candidates.append(attr.get("src", ""))
            for candidate in candidates:
                if candidate and "media-amazon.com/images/I/" in candidate and candidate not in self.image_urls:
                    self.image_urls.append(candidate)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if self._bullet_depth == self._depth:
            bullet = " ".join(self._bullet_parts).strip()
            if bullet and bullet not in self.bullets:
                self.bullets.append(bullet)
            self._bullet_depth = 0
            self._bullet_parts = []
        if self._product_title_depth == self._depth:
            product_title = " ".join(self._product_title_parts).strip()
            if product_title:
                self.title = product_title
            self._product_title_depth = 0
        if self._feature_depth == self._depth:
            self._feature_depth = 0
        if self._capture_depth and tag in {"th", "td", "dt", "dd"} and self._in_cell:
            cell = " ".join(self._cell_parts).strip()
            if cell:
                self._row.append(cell)
            self._in_cell = False
        if self._capture_depth and tag in {"tr", "dl"}:
            if len(self._row) >= 2:
                self.details[self._row[0]] = " ".join(self._row[1:])
            self._row = []
        if self._capture_depth == self._depth:
            self._capture_depth = 0
        self._depth = max(0, self._depth - 1)

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean or not self._capture_depth:
            return
        if self._product_title_depth:
            self._product_title_parts.append(clean)
        elif not self.title and self._in_title:
            self.title = clean
        else:
            self.description_parts.append(clean)
        if self._bullet_depth:
            self._bullet_parts.append(clean)
        if self._in_cell:
            self._cell_parts.append(clean)


def _from_fixture(path: Path) -> Evidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Evidence(
        url=data.get("url", ""),
        title=data.get("title", ""),
        bullets=data.get("bullets", []),
        description=data.get("description", ""),
        details={str(k): str(v) for k, v in data.get("details", {}).items()},
        image_urls=[str(value) for value in data.get("images", [])],
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
        return Evidence(url=record.url, title=parser.title, bullets=parser.bullets, description=text, details=parser.details, image_urls=parser.image_urls[:12], source="Amazon live page")
    except Exception as exc:  # network and challenge pages are review states, not passes
        return Evidence(
            url=record.url,
            source="Amazon live page",
            available=False,
            error=f"{type(exc).__name__}: {exc}",
        )
