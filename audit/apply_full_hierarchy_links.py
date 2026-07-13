from __future__ import annotations

import csv
import re
from collections import defaultdict
from html import escape, unescape
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
ADDED_LINKS_CSV = ROOT / "audit" / "internal-links-added.csv"
CHANGED_FILES_CSV = ROOT / "audit" / "changed-output-files.csv"
START = "<!-- hierarchy-links:start -->"
END = "<!-- hierarchy-links:end -->"

CANONICAL_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.I)
BREADCRUMB_RE = re.compile(r'<nav\b[^>]*class=["\'][^"\']*breadcrumbs[^"\']*["\'][^>]*>(.*?)</nav>', re.I | re.S)
ANCHOR_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
HREF_RE = re.compile(r'\bhref=["\']([^"\']+)["\']', re.I)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
OLD_BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def normalize_url(value: str) -> str:
    parsed = urlparse(unescape(value).strip())
    path = parsed.path if parsed.scheme or parsed.netloc else value
    path = unquote(path).strip()
    if not path or path == "/":
        return "/"
    return "/" + path.strip("/") + "/"


def text_of(html: str) -> str:
    return " ".join(unescape(TAG_RE.sub("", html)).split())


def canonical_or_path(path: Path, html: str) -> str:
    match = CANONICAL_RE.search(html)
    if match:
        return normalize_url(match.group(1))
    rel = path.relative_to(OUTPUT).as_posix()
    if rel == "index.html":
        return "/"
    return "/" + rel[: -len("/index.html")].strip("/") + "/" if rel.endswith("/index.html") else "/" + rel.strip("/") + "/"


def breadcrumb_items(html: str) -> list[tuple[str, str]]:
    match = BREADCRUMB_RE.search(html)
    if not match:
        return []
    return [(normalize_url(href), text_of(label)) for href, label in ANCHOR_RE.findall(match.group(1))]


def title_from_html(html: str, breadcrumbs: list[tuple[str, str]]) -> str:
    if breadcrumbs:
        return breadcrumbs[-1][1]
    match = H1_RE.search(html) or TITLE_RE.search(html)
    if match:
        return text_of(match.group(1)).replace(" | StudyHub", "")
    return ""


def existing_hrefs(html: str) -> set[str]:
    return {normalize_url(href) for href in HREF_RE.findall(html) if href and not href.startswith("#")}


def link_description(title: str) -> str:
    return f"{title}와 연결된 하위 학습 정보를 함께 살펴보세요."


def render_block(links: list[dict[str, str]]) -> str:
    items = "".join(
        '<li><a class="related-card" href="{url}"><strong>{title}</strong><span>{desc}</span></a></li>'.format(
            url=escape(item["url"], quote=True),
            title=escape(item["title"]),
            desc=escape(link_description(item["title"])),
        )
        for item in links
    )
    return (
        f"{START}"
        '<aside class="related-link-band hierarchy-link-band">'
        '<h2 id="하위-페이지-더-보기">하위 페이지 더 보기</h2>'
        f"<ul>{items}</ul>"
        "</aside>"
        f"{END}"
    )


def insert_block(html: str, block: str) -> str:
    html = OLD_BLOCK_RE.sub("", html)
    if "</main>" in html:
        return html.replace("</main>", f"{block}</main>", 1)
    return html + block


def main() -> None:
    pages: dict[str, dict[str, object]] = {}
    for path in OUTPUT.rglob("index.html"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        crumbs = breadcrumb_items(html)
        url = canonical_or_path(path, html)
        pages[url] = {
            "file": path,
            "html": html,
            "title": title_from_html(html, crumbs),
            "breadcrumbs": crumbs,
            "hrefs": existing_hrefs(html),
        }

    children_by_parent: dict[str, list[dict[str, str]]] = defaultdict(list)
    for url, page in pages.items():
        crumbs = page["breadcrumbs"]
        if not isinstance(crumbs, list) or len(crumbs) < 2:
            continue
        parent_url = crumbs[-2][0]
        if parent_url == url or parent_url not in pages:
            continue
        title = str(page["title"] or crumbs[-1][1] or url.strip("/"))
        children_by_parent[parent_url].append({"url": url, "title": title})

    added_rows: list[dict[str, str]] = []
    changed_rows: list[dict[str, str]] = []
    for parent_url, children in sorted(children_by_parent.items()):
        page = pages[parent_url]
        html = str(page["html"])
        hrefs = page["hrefs"]
        if not isinstance(hrefs, set):
            hrefs = set()
        unique_children = []
        seen = set()
        for child in sorted(children, key=lambda item: item["title"]):
            child_url = child["url"]
            if child_url == parent_url or child_url in seen or child_url in hrefs:
                continue
            seen.add(child_url)
            unique_children.append(child)
        if not unique_children:
            cleaned = OLD_BLOCK_RE.sub("", html)
            if cleaned != html:
                path = page["file"]
                assert isinstance(path, Path)
                path.write_text(cleaned, encoding="utf-8")
                changed_rows.append({"file": path.as_posix(), "url": parent_url, "links_added": "0", "action": "removed_empty_hierarchy_block"})
            continue

        block = render_block(unique_children)
        new_html = insert_block(html, block)
        if new_html == html:
            continue
        path = page["file"]
        assert isinstance(path, Path)
        path.write_text(new_html, encoding="utf-8")
        changed_rows.append({"file": path.as_posix(), "url": parent_url, "links_added": str(len(unique_children)), "action": "added_hierarchy_child_links"})
        for child in unique_children:
            added_rows.append(
                {
                    "source_url": parent_url,
                    "target_url": child["url"],
                    "target_title": child["title"],
                    "source_file": path.as_posix(),
                    "section": "하위 페이지 더 보기",
                }
            )

    with ADDED_LINKS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_url", "target_url", "target_title", "source_file", "section"])
        writer.writeheader()
        writer.writerows(added_rows)

    with CHANGED_FILES_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "url", "links_added", "action"])
        writer.writeheader()
        writer.writerows(changed_rows)

    print(f"pages={len(pages)} parents={len(children_by_parent)} changed_files={len(changed_rows)} links_added={len(added_rows)}")


if __name__ == "__main__":
    main()
