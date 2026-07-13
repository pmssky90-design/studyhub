from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
OUT = ROOT / "audit" / "self-links-current.csv"
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
    path = parsed.path if parsed.scheme or parsed.netloc else href.split("?", 1)[0].split("#", 1)[0]
    if parsed.netloc and parsed.netloc not in HOSTS:
        return None
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


def main() -> None:
    rows = []
    for path in OUTPUT.rglob("index.html"):
        url = page_url(path)
        html = path.read_text(encoding="utf-8", errors="ignore")
        for match in A_HREF_RE.finditer(html):
            if normalize_href(match.group(1)) == url:
                rows.append({"url": url, "file": path.as_posix(), "href": match.group(1)})
                break
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "file", "href"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"pages_with_self_link={len(rows)}")
    for row in rows[:20]:
        print(row)


if __name__ == "__main__":
    main()
