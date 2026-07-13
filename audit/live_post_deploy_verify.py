from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
SITE = "https://studyhub.co.kr"
SITEMAP = f"{SITE}/sitemap.xml"
HOSTS = {"studyhub.co.kr", "www.studyhub.co.kr"}
SUMMARY = AUDIT / "live-post-deploy-summary.txt"
URL_CSV = AUDIT / "live-post-deploy-urls.csv"
ORPHAN_CSV = AUDIT / "live-orphan-pages-after.csv"
DEPTH_CSV = AUDIT / "live-crawl-depth-after.csv"

CANONICAL_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.I)
ROBOTS_RE = re.compile(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', re.I)
JSONLD_RE = re.compile(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', re.I | re.S)
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)


def fetch(url: str, timeout: int = 20) -> tuple[int, str, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "StudyHubPostDeployAudit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, response.geturl(), response.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, exc.geturl(), exc.headers.get("Content-Type", ""), body
    except Exception as exc:
        return 0, url, "", f"ERROR: {exc}"


def normalized_path(value: str) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    path = parsed.path if parsed.scheme or parsed.netloc else value.split("?", 1)[0].split("#", 1)[0]
    path = urllib.parse.unquote(path)
    if not path or path == "/":
        return "/"
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if path.endswith(".html"):
        return "/" + path.strip("/")
    return "/" + path.strip("/") + "/"


def internal_link_path(href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urllib.parse.urlparse(href)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc not in HOSTS:
            return None
        return normalized_path(href)
    if not href.startswith("/"):
        return None
    return normalized_path(href)


def parse_sitemap() -> list[str]:
    status, final_url, content_type, body = fetch(SITEMAP, timeout=30)
    if status != 200:
        raise RuntimeError(f"sitemap fetch failed: {status} {final_url} {content_type}")
    root = ET.fromstring(body)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall(".//sm:loc", ns) if loc.text and loc.text.strip()]


def check_url(url: str) -> dict[str, object]:
    status, final_url, content_type, body = fetch(url)
    canonical = ""
    noindex = False
    jsonld_error = ""
    links: list[str] = []
    if body and not body.startswith("ERROR:"):
        canonical_match = CANONICAL_RE.search(body)
        canonical = canonical_match.group(1) if canonical_match else ""
        robots_match = ROBOTS_RE.search(body)
        noindex = bool(robots_match and "noindex" in robots_match.group(1).lower())
        for block in JSONLD_RE.findall(body):
            try:
                json.loads(block)
            except Exception as exc:
                jsonld_error = str(exc)
                break
        links = [item for item in (internal_link_path(href) for href in A_HREF_RE.findall(body)) if item]
    return {
        "url": url,
        "path": normalized_path(url),
        "status": status,
        "final_url": final_url,
        "content_type": content_type,
        "canonical": canonical,
        "canonical_ok": canonical == url,
        "noindex": noindex,
        "jsonld_error": jsonld_error,
        "links": links,
        "error": body if body.startswith("ERROR:") else "",
    }


def main() -> None:
    urls = parse_sitemap()
    rows = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_url, url): url for url in urls}
        for index, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if index % 500 == 0:
                print(f"checked={index}/{len(urls)} elapsed={time.time() - start:.1f}s")

    valid_paths = {row["path"] for row in rows}
    graph = {row["path"]: sorted({link for link in row["links"] if link in valid_paths}) for row in rows}
    depths: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([("/", 0)])
    while queue:
        path, depth = queue.popleft()
        if path in depths:
            continue
        depths[path] = depth
        for target in graph.get(path, []):
            if target not in depths:
                queue.append((target, depth + 1))

    orphans = sorted(valid_paths - set(depths))
    depth_counts: dict[int, int] = defaultdict(int)
    for depth in depths.values():
        depth_counts[depth] += 1

    with URL_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "status", "final_url", "content_type", "canonical", "canonical_ok", "noindex", "jsonld_error", "error"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    with ORPHAN_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path"])
        writer.writerows([[path] for path in orphans])

    with DEPTH_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "depth"])
        for path, depth in sorted(depths.items(), key=lambda item: (item[1], item[0])):
            writer.writerow([path, depth])

    summary = {
        "sitemap_urls": len(urls),
        "http_200": sum(1 for row in rows if row["status"] == 200),
        "non_200": sum(1 for row in rows if row["status"] != 200),
        "canonical_conflicts": sum(1 for row in rows if not row["canonical_ok"]),
        "noindex": sum(1 for row in rows if row["noindex"]),
        "jsonld_errors": sum(1 for row in rows if row["jsonld_error"]),
        "orphan_pages": len(orphans),
        "reachable_pages": len(depths),
        "max_depth": max(depths.values()) if depths else "",
        "depth_counts": dict(sorted(depth_counts.items())),
        "elapsed_seconds": round(time.time() - start, 1),
    }
    SUMMARY.write_text("\n".join(f"{key}: {value}" for key, value in summary.items()), encoding="utf-8")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
