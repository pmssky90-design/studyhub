from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
REPORT = ROOT / "audit" / "duplicate-anchor-links-removed.csv"
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)
HOSTS = {"studyhub.co.kr", "www.studyhub.co.kr"}


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


def remove_duplicate_link_items(html: str) -> tuple[str, int]:
    seen = set()
    removed = 0
    position = 0
    output = []
    for match in A_HREF_RE.finditer(html):
        target = normalize_href(match.group(1))
        if target is None:
            continue
        if target not in seen:
            seen.add(target)
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
        html = path.read_text(encoding="utf-8", errors="ignore")
        new_html, removed = remove_duplicate_link_items(html)
        if removed:
            path.write_text(new_html, encoding="utf-8")
            rows.append({"file": path.as_posix(), "removed_duplicate_links": str(removed)})
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "removed_duplicate_links"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"changed_files={len(rows)} removed_duplicate_links={sum(int(row['removed_duplicate_links']) for row in rows)}")


if __name__ == "__main__":
    main()
