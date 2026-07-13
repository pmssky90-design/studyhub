from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
REPORT = ROOT / "audit" / "self-anchor-links-removed.csv"
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)
HOSTS = {"studyhub.co.kr", "www.studyhub.co.kr"}


def page_url(path: Path) -> str:
    rel = path.relative_to(OUTPUT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")].strip("/") + "/"
    return "/" + rel.strip("/")


def normalize_href(href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc not in HOSTS:
            return None
        path = parsed.path
    else:
        path = href.split("?", 1)[0].split("#", 1)[0]
    path = unquote(path)
    if not path or path == "/":
        return "/"
    if not path.startswith("/"):
        return None
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if path.endswith(".html"):
        return "/" + path.strip("/")
    return "/" + path.strip("/") + "/"


def remove_self_link_items(html: str, current_url: str) -> tuple[str, int]:
    removed = 0
    position = 0
    output = []
    for match in A_HREF_RE.finditer(html):
        if normalize_href(match.group(1)) != current_url:
            continue
        li_start = html.rfind("<li", 0, match.start())
        li_end = html.find("</li>", match.end())
        if li_start < 0 or li_end < 0:
            continue
        li_end += len("</li>")
        if li_start < position:
            continue
        output.append(html[position:li_start])
        position = li_end
        removed += 1
    if not removed:
        return html, 0
    output.append(html[position:])
    return "".join(output), removed


def main() -> None:
    rows = []
    for path in OUTPUT.rglob("index.html"):
        url = page_url(path)
        html = path.read_text(encoding="utf-8", errors="ignore")
        new_html, removed = remove_self_link_items(html, url)
        if removed:
            path.write_text(new_html, encoding="utf-8")
            rows.append({"file": path.as_posix(), "url": url, "removed_self_links": str(removed)})
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "url", "removed_self_links"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"changed_files={len(rows)} removed_self_links={sum(int(row['removed_self_links']) for row in rows)}")


if __name__ == "__main__":
    main()
