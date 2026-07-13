from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
TEMP_OUTPUT = ROOT / "audit" / "regeneration-test-output"
SUMMARY = ROOT / "audit" / "regeneration-persistence-summary.txt"
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)
HOSTS = {"studyhub.co.kr", "www.studyhub.co.kr"}


def page_url(path: Path) -> str:
    rel = path.relative_to(TEMP_OUTPUT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")].strip("/") + "/"
    return "/" + rel.strip("/")


def normalize_href(href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
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


def main() -> None:
    files = list(TEMP_OUTPUT.rglob("index.html"))
    by_url = {page_url(path): path for path in files}
    valid = set(by_url)
    graph: dict[str, set[str]] = {}
    broken = 0
    self_links = 0
    duplicate_pairs = 0
    total_links = 0

    for url, path in by_url.items():
        html = path.read_text(encoding="utf-8", errors="ignore")
        links = []
        for href in A_HREF_RE.findall(html):
            target = normalize_href(href)
            if target is None:
                continue
            if target in valid:
                links.append(target)
            elif target.startswith("/"):
                broken += 1
        total_links += len(links)
        self_links += sum(1 for target in links if target == url)
        duplicate_pairs += len(links) - len(set(links))
        graph[url] = set(links)

    depths: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([("/", 0)])
    while queue:
        url, depth = queue.popleft()
        if url in depths:
            continue
        depths[url] = depth
        for target in sorted(graph.get(url, set())):
            if target not in depths:
                queue.append((target, depth + 1))

    depth_counts: dict[int, int] = defaultdict(int)
    for depth in depths.values():
        depth_counts[depth] += 1

    summary = {
        "total_html": len(files),
        "total_internal_links": total_links,
        "reachable_pages": len(depths),
        "orphan_pages": len(valid - set(depths)),
        "max_depth": max(depths.values()) if depths else "",
        "broken_internal_links": broken,
        "self_links": self_links,
        "duplicate_source_target_links": duplicate_pairs,
        "depth_counts": dict(sorted(depth_counts.items())),
    }
    SUMMARY.write_text("\n".join(f"{key}: {value}" for key, value in summary.items()), encoding="utf-8")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
