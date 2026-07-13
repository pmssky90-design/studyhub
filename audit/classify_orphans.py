from __future__ import annotations

import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
OUTPUT = ROOT / "output"


class CrumbParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_breadcrumbs = False
        self.crumbs: list[tuple[str, str]] = []
        self._href = ""
        self._text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v or "" for k, v in attrs}
        if tag == "nav" and data.get("class") == "breadcrumbs":
            self.in_breadcrumbs = True
        if self.in_breadcrumbs and tag == "a":
            self._href = data.get("href", "")
            self._text = ""

    def handle_endtag(self, tag: str) -> None:
        if self.in_breadcrumbs and tag == "a" and self._href:
            self.crumbs.append((self._text.strip(), path_from_url(self._href)))
            self._href = ""
            self._text = ""
        if tag == "nav" and self.in_breadcrumbs:
            self.in_breadcrumbs = False

    def handle_data(self, data: str) -> None:
        if self.in_breadcrumbs and self._href:
            self._text += data


def path_from_url(url: str) -> str:
    parsed = urlparse(url)
    return unquote(parsed.path or "/")


def output_file(path: str) -> Path:
    if path == "/":
        return OUTPUT / "index.html"
    return OUTPUT / path.strip("/") / "index.html"


def classify(path: str, crumbs: list[tuple[str, str]]) -> str:
    title = crumbs[-1][0] if crumbs else path.strip("/")
    depth = len([part for part in path.strip("/").split("/") if part])
    if depth >= 3:
        return "dong_hub"
    if re.search(r"(초등|중등|고등)(수학|영어)?과외$", title):
        return "grade_subject_page" if re.search(r"(수학|영어)과외$", title) else "grade_hub"
    if re.search(r"(수학|영어)과외$", title):
        return "subject_hub"
    if title.endswith("과외"):
        base = title[:-2]
        if base.endswith(("구", "군", "시")):
            return "sigungu_hub"
        if base.endswith(("동", "읍", "면", "리")):
            return "dong_hub"
        if base in {"서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"}:
            return "sido_hub"
    return "other"


def main() -> int:
    crawl_depth: dict[str, tuple[str, str]] = {}
    with (AUDIT / "crawl-depth.csv").open(encoding="utf-8") as file:
        for row in csv.DictReader(file):
            crawl_depth[row["url"]] = (row["depth"], row["incoming_links"])

    link_edges: set[tuple[str, str]] = set()
    with (AUDIT / "all-internal-links.csv").open(encoding="utf-8", errors="replace") as file:
        for row in csv.DictReader(file):
            normalized = row.get("normalized_url", "")
            parsed = urlparse(normalized)
            target = unquote(parsed.path or "/")
            if target and not "." in target.split("/")[-1] and not target.endswith("/"):
                target += "/"
            if target:
                link_edges.add((row.get("source_url", ""), target))

    rows = []
    with (AUDIT / "orphan-pages.csv").open(encoding="utf-8") as file:
        orphans = list(csv.DictReader(file))

    for row in orphans:
        path = row["url"]
        file_path = output_file(path)
        parser = CrumbParser()
        if file_path.exists():
            parser.feed(file_path.read_text(encoding="utf-8", errors="replace"))
        crumbs = parser.crumbs
        parent = crumbs[-2][1] if len(crumbs) >= 2 else ""
        parent_exists = bool(parent and output_file(parent).exists())
        parent_links = (parent, path) in link_edges if parent else False
        child_links = (path, parent) in link_edges if parent else False
        parent_depth = crawl_depth.get(parent, ("", ""))[0] if parent else ""
        page_type = classify(path, crumbs)
        if not parent:
            fix = "inspect_missing_breadcrumb_or_data_parent"
            regen = "yes_data_or_template"
            source = "sitegen.builder breadcrumb/page parent generation"
        elif not parent_exists:
            fix = "create_or_restore_parent_before_linking"
            regen = "yes_data_or_template"
            source = "region/content source"
        elif parent_depth == "":
            fix = "connect_reachable_ancestor_or_parent_hub"
            regen = "partial_hub_or_template"
            source = "sitegen.builder link sections"
        elif not parent_links:
            fix = "add_child_link_to_existing_parent_hub"
            regen = "partial_parent_hub"
            source = "sitegen.builder section links"
        else:
            fix = "bfs_cluster_disconnected_at_higher_ancestor"
            regen = "partial_ancestor_hub"
            source = "ancestor hub output/template"
        rows.append([
            path,
            page_type,
            parent,
            int(parent_exists),
            int(parent_links),
            int(child_links),
            row.get("incoming_links", ""),
            crawl_depth.get(path, ("", ""))[0],
            fix,
            regen,
            source,
        ])

    with (AUDIT / "orphan-classification.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "page_path",
            "page_type",
            "expected_parent",
            "parent_exists",
            "parent_links_to_child",
            "child_links_to_parent",
            "inbound_link_count",
            "crawl_depth",
            "recommended_fix",
            "requires_regeneration",
            "template_source",
        ])
        writer.writerows(rows)

    counts: dict[str, int] = {}
    fixes: dict[str, int] = {}
    for item in rows:
        counts[item[1]] = counts.get(item[1], 0) + 1
        fixes[item[8]] = fixes.get(item[8], 0) + 1
    print(json.dumps({"total": len(rows), "page_type_counts": counts, "fix_counts": fixes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
