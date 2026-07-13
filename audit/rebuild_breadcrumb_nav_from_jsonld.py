from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
REPORT = ROOT / "audit" / "breadcrumb-nav-rebuild.csv"
JSONLD_RE = re.compile(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', re.I | re.S)
NAV_RE = re.compile(r'<nav\s+class=["\']breadcrumbs["\']\s+aria-label=["\']breadcrumb["\']>.*?</nav>', re.I | re.S)


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def breadcrumb_items(html: str) -> list[dict[str, str]]:
    match = JSONLD_RE.search(html)
    if not match:
        return []
    data = json.loads(match.group(1))
    graph = data.get("@graph", []) if isinstance(data, dict) else []
    for item in graph:
        if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
            elements = item.get("itemListElement", [])
            result = []
            for element in elements:
                if not isinstance(element, dict):
                    continue
                result.append({"name": str(element.get("name", "")), "url": str(element.get("item", ""))})
            return [item for item in result if item["name"]]
    return []


def render_nav(items: list[dict[str, str]]) -> str:
    rendered = []
    for index, item in enumerate(items):
        name = escape_html(item["name"])
        if index == len(items) - 1:
            rendered.append(f'<li><span aria-current="page">{name}</span></li>')
        else:
            rendered.append(f'<li><a href="{escape_html(item["url"])}">{name}</a></li>')
    return '<nav class="breadcrumbs" aria-label="breadcrumb"><ol>' + "".join(rendered) + "</ol></nav>"


def main() -> None:
    rows = []
    for path in OUTPUT.rglob("index.html"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        items = breadcrumb_items(html)
        if not items:
            continue
        nav = render_nav(items)
        new_html, count = NAV_RE.subn(nav, html, count=1)
        if count and new_html != html:
            path.write_text(new_html, encoding="utf-8")
            rows.append({"file": path.as_posix(), "breadcrumb_items": str(len(items))})
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "breadcrumb_items"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"changed_files={len(rows)}")


if __name__ == "__main__":
    main()
