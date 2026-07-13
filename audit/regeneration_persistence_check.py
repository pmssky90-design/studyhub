from __future__ import annotations

import csv
import re
import shutil
import sys
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
import sitegen.urls as urls
from config import CONTENT_SOURCE, ROBOTS_TEXT, SITE_URL
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions
from sitegen.render import render_site


TEMP_OUTPUT = ROOT / "audit" / "regeneration-test-output"
REPORT = ROOT / "audit" / "regeneration-persistence-report.csv"
SUMMARY = ROOT / "audit" / "regeneration-persistence-summary.txt"
HREF_RE = re.compile(r'\bhref=["\']([^"\']+)["\']', re.I)


def normalize_path(value: str, base: str = "/") -> str | None:
    value = value.strip()
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    absolute = urldefrag(urljoin(SITE_URL.rstrip("/") + base, value))[0]
    parsed = urlparse(absolute)
    if parsed.netloc and parsed.netloc not in {"studyhub.co.kr", "www.studyhub.co.kr"}:
        return None
    path = unquote(parsed.path)
    if not path or path == "/":
        return "/"
    return "/" + path.strip("/") + ("/" if not path.endswith(".html") else "")


def page_url(path: Path) -> str:
    rel = path.relative_to(TEMP_OUTPUT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")].strip("/") + "/"
    return "/" + rel.strip("/")


def outgoing_links(path: Path, url: str, valid_urls: set[str]) -> set[str]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    links = set()
    for href in HREF_RE.findall(html):
        target = normalize_path(href, url)
        if target in valid_urls:
            links.add(target)
    return links


def write_rendered_temp() -> None:
    if TEMP_OUTPUT.exists():
        shutil.rmtree(TEMP_OUTPUT)
    TEMP_OUTPUT.mkdir(parents=True, exist_ok=True)

    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)
    files = render_site(pages)

    for rendered in files:
        parts = [part for part in rendered.url.strip("/").split("/") if part]
        if parts and "." in parts[-1]:
            target = TEMP_OUTPUT.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target = TEMP_OUTPUT.joinpath(*parts) / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered.content, encoding="utf-8", newline="\n")
    (TEMP_OUTPUT / "robots.txt").write_text(ROBOTS_TEXT, encoding="utf-8", newline="\n")


def scan_temp() -> dict[str, object]:
    files = list(TEMP_OUTPUT.rglob("index.html"))
    by_url = {page_url(path): path for path in files}
    valid_urls = set(by_url)
    graph: dict[str, set[str]] = {}
    incoming: dict[str, int] = defaultdict(int)
    for url, path in by_url.items():
        links = outgoing_links(path, url, valid_urls)
        graph[url] = links
        for target in links:
            incoming[target] += 1

    depths: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([("/", 0)])
    while queue:
        url, depth = queue.popleft()
        if url in depths:
            continue
        depths[url] = depth
        for target in sorted(graph.get(url, ())):
            if target not in depths:
                queue.append((target, depth + 1))

    orphan = sorted(valid_urls - set(depths))
    broken = []
    for url, links in graph.items():
        for target in links:
            if target not in valid_urls:
                broken.append((url, target))

    depth_counts: dict[int, int] = defaultdict(int)
    for depth in depths.values():
        depth_counts[depth] += 1

    parent_samples = [
        "/경기도과외/",
        "/서울과외/",
        "/강남구고등과외/",
        "/금천구고등수학과외/",
        "/가경동고등수학과외/",
    ]
    sample_rows = []
    for url in parent_samples:
        sample_rows.append(
            {
                "url": url,
                "exists": str(url in valid_urls),
                "depth": str(depths.get(url, "")),
                "outgoing_internal_links": str(len(graph.get(url, set()))),
                "incoming_links": str(incoming.get(url, 0)),
            }
        )

    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "exists", "depth", "outgoing_internal_links", "incoming_links"])
        writer.writeheader()
        writer.writerows(sample_rows)

    summary = {
        "total_html": len(files),
        "reachable_pages": len(depths),
        "orphan_pages": len(orphan),
        "max_depth": max(depths.values()) if depths else "",
        "broken_internal_links": len(broken),
        "depth_counts": dict(sorted(depth_counts.items())),
    }
    SUMMARY.write_text("\n".join(f"{key}: {value}" for key, value in summary.items()), encoding="utf-8")
    return summary


def main() -> None:
    write_rendered_temp()
    summary = scan_temp()
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
