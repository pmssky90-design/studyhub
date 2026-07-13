from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"


CANONICAL_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.I)
BREADCRUMB_RE = re.compile(r'<nav\b[^>]*class=["\'][^"\']*breadcrumbs[^"\']*["\'][^>]*>(.*?)</nav>', re.I | re.S)
ANCHOR_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def normalize_url(value: str) -> str:
    parsed = urlparse(unescape(value).strip())
    path = parsed.path if parsed.scheme or parsed.netloc else value
    path = unquote(path).strip()
    if not path or path == "/":
        return "/"
    return "/" + path.strip("/") + "/"


def page_url_from_file(path: Path) -> str:
    rel = path.relative_to(OUTPUT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")].strip("/") + "/"
    return "/" + rel.strip("/") + "/"


def text_of(html: str) -> str:
    return unescape(TAG_RE.sub("", html)).strip()


def canonical_or_path(path: Path, html: str) -> str:
    match = CANONICAL_RE.search(html)
    if match:
        return normalize_url(match.group(1))
    return page_url_from_file(path)


def breadcrumb_items(html: str) -> list[tuple[str, str]]:
    match = BREADCRUMB_RE.search(html)
    if not match:
        return []
    return [(normalize_url(href), text_of(label)) for href, label in ANCHOR_RE.findall(match.group(1))]


def main() -> None:
    pages: dict[str, dict[str, str | list[tuple[str, str]]]] = {}
    for path in OUTPUT.rglob("index.html"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        url = canonical_or_path(path, html)
        pages[url] = {"file": path.as_posix(), "breadcrumbs": breadcrumb_items(html)}

    children: dict[str, set[str]] = defaultdict(set)
    missing_parent = []
    for url, page in pages.items():
        crumbs = page["breadcrumbs"]
        if not isinstance(crumbs, list) or len(crumbs) < 2:
            continue
        parent_url = crumbs[-2][0]
        if parent_url == url:
            continue
        if parent_url not in pages:
            missing_parent.append((url, parent_url))
            continue
        children[parent_url].add(url)

    counts = Counter(len(items) for items in children.values())
    largest = sorted(((len(items), parent) for parent, items in children.items()), reverse=True)[:30]

    report = ROOT / "audit" / "breadcrumb-child-counts.csv"
    with report.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parent_url", "child_count"])
        for count, parent in sorted(((len(items), parent) for parent, items in children.items()), reverse=True):
            writer.writerow([parent, count])

    print(f"pages={len(pages)} parents={len(children)} missing_parent={len(missing_parent)}")
    print("count_distribution", dict(sorted(counts.items())))
    print("largest")
    for count, parent in largest:
        print(count, parent)


if __name__ == "__main__":
    main()
