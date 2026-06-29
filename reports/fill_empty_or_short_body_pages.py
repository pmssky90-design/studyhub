from __future__ import annotations

from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
import csv
import re

from config import CONTENT_SOURCE
from reports.fix_body_quality import supplement_content, supplement_faq
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions
from sitegen.render import render_page
from sitegen.urls import output_path


ROOT = Path.cwd()
REPORT = ROOT / "reports" / "empty_or_short_body_pages.csv"
MIN_BODY_LENGTH = 300


class ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_page_content = False
        self.page_depth = 0
        self.in_article = False
        self.article_depth = 0
        self.skip = 0
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {key: value or "" for key, value in attrs}
        cls = attrs_d.get("class", "")
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        if tag == "section" and "page-content" in cls:
            self.in_page_content = True
            self.page_depth = 1
            return
        if self.in_page_content and tag == "section":
            self.page_depth += 1
        if self.in_page_content and tag == "article" and "info-card" in cls:
            self.in_article = True
            self.article_depth = 1
            return
        if self.in_article:
            self.article_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1
        if self.in_article:
            self.article_depth -= 1
            if self.article_depth <= 0:
                self.in_article = False
        if self.in_page_content and tag == "section":
            self.page_depth -= 1
            if self.page_depth <= 0:
                self.in_page_content = False

    def handle_data(self, data: str) -> None:
        if self.in_article and not self.skip:
            value = re.sub(r"\s+", " ", data).strip()
            if value:
                self.text.append(value)


def body_text_length(html: str) -> int:
    parser = ArticleTextParser()
    parser.feed(html)
    text = re.sub(r"\s+", " ", " ".join(parser.text)).strip()
    return len(text)


def project_output_path(url: str) -> Path:
    parts = [part for part in url.strip("/").split("/") if part]
    if parts and "." in parts[-1]:
        target = ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    target = ROOT.joinpath(*parts)
    target.mkdir(parents=True, exist_ok=True)
    return target / "index.html"


def html_path_for_url(url: str, base: Path) -> Path:
    if url == "/":
        return base / "index.html"
    return base.joinpath(*[part for part in url.strip("/").split("/") if part], "index.html")


def plain_length(value: str) -> int:
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip())


def write_page(page) -> None:
    filled = replace(page, content=supplement_content(page), faq=supplement_faq(page))
    html = render_page(filled)
    output_path(filled.url).write_text(html, encoding="utf-8", newline="\n")
    project_output_path(filled.url).write_text(html, encoding="utf-8", newline="\n")


def scan_short_pages(pages) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_url = {page.url: page for page in pages}
    for page in pages:
        path = html_path_for_url(page.url, ROOT / "output")
        if not path.exists():
            continue
        length = body_text_length(path.read_text(encoding="utf-8", errors="ignore"))
        if length <= MIN_BODY_LENGTH:
            rows.append(
                {
                    "url": page.url,
                    "title": page.title,
                    "html_body_length": length,
                    "page_content_length": plain_length(page.content),
                    "will_generate": "yes" if plain_length(page.content) <= MIN_BODY_LENGTH else "no_existing_page_content",
                }
            )
    return rows


def main() -> None:
    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)
    page_by_url = {page.url: page for page in pages}

    total_generated = 0
    last_rows: list[dict[str, object]] = []
    for _ in range(5):
        rows = scan_short_pages(pages)
        last_rows = rows
        targets = [row for row in rows if row["will_generate"] == "yes"]
        if not targets:
            break
        for row in targets:
            write_page(page_by_url[row["url"]])
            total_generated += 1
    final_rows = scan_short_pages(pages)
    REPORT.parent.mkdir(exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["url", "title", "html_body_length", "page_content_length", "will_generate"])
        writer.writeheader()
        writer.writerows(final_rows)
    print(f"initial_short_or_empty={len(last_rows)}")
    print(f"generated={total_generated}")
    print(f"remaining_short_or_empty={len(final_rows)}")
    print(f"csv={REPORT}")


if __name__ == "__main__":
    main()
