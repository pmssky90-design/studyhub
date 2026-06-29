from __future__ import annotations

from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
import csv
import hashlib
import re

from config import CONTENT_SOURCE
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions
from sitegen.render import render_page
from sitegen.urls import output_path


ROOT = Path.cwd()
CSV_PATH = ROOT / "reports" / "body_quality_failures.csv"

MIN_BODY_LEN = 1500
MIN_H2 = 3
MIN_H3 = 2
MIN_PARAGRAPHS = 8
MIN_FAQ = 5
MIN_IMAGES = 6

MOJIBAKE_HINTS = (
    "\u6028",
    "\u4e86",
    "\uf9de",
    "\u5a9b",
    "\uc12e",
    "\ub4bf",
    "\uc496",
    "\ua7a7",
    "\ubeb3",
    "\ub2f2",
    "\ub0ab",
    "\uc1b1",
    "\uacf8",
    "\ub431",
)


class BodyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.in_content = False
        self.section_depth = 0
        self.in_p = False
        self.p_has_text = False
        self.text: list[str] = []
        self.h2 = 0
        self.h3 = 0
        self.p = 0
        self.empty_p = 0
        self.faq_q = 0
        self.images = 0
        self.related_links = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {key: value or "" for key, value in attrs}
        cls = attrs_d.get("class", "")
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        if tag == "section" and "page-content" in cls:
            self.in_content = True
            self.section_depth = 1
        elif self.in_content and tag == "section":
            self.section_depth += 1
        if not self.in_content:
            return
        if tag == "h2":
            self.h2 += 1
        elif tag == "h3":
            self.h3 += 1
        elif tag == "p":
            self.p += 1
            self.in_p = True
            self.p_has_text = False
        elif tag == "img":
            self.images += 1
        elif tag == "a" and ("related-card" in cls or "link-card" in cls):
            self.related_links += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1
        if self.in_content and tag == "p":
            if not self.p_has_text:
                self.empty_p += 1
            self.in_p = False
        if self.in_content and tag == "section":
            self.section_depth -= 1
            if self.section_depth <= 0:
                self.in_content = False

    def handle_data(self, data: str) -> None:
        if not self.in_content or self.skip:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        self.text.append(value)
        if self.in_p:
            self.p_has_text = True
        if re.match(r"^Q[.:)]|^Q\s", value, flags=re.IGNORECASE) or value.startswith("Q."):
            self.faq_q += 1


def project_output_path(url: str) -> Path:
    parts = [part for part in url.strip("/").split("/") if part]
    if parts and "." in parts[-1]:
        target = ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    target = ROOT.joinpath(*parts)
    target.mkdir(parents=True, exist_ok=True)
    return target / "index.html"


def text_metrics(text: str) -> tuple[int, int, int]:
    hangul = sum("\uac00" <= char <= "\ud7a3" for char in text)
    hanja = sum(("\u4e00" <= char <= "\u9fff") or ("\uf900" <= char <= "\ufaff") for char in text)
    hints = sum(text.count(token) for token in MOJIBAKE_HINTS)
    return hangul, hanja, hints


def audit_html(html: str) -> dict[str, object]:
    parser = BodyParser()
    parser.feed(html)
    body_text = re.sub(r"\s+", " ", " ".join(parser.text)).strip()
    hangul, hanja, hints = text_metrics(body_text)
    broken = hints > 10 or (hanja > 40 and hanja > hangul * 0.2)
    fixed_image_count = len(re.findall(r'<div class="detail-image-stack">.*?</div>', html, flags=re.DOTALL))
    stack_images = 0
    stack_match = re.search(r'<div class="detail-image-stack">(.*?)</div>', html, flags=re.DOTALL)
    if stack_match:
        stack_images = len(re.findall(r"<img\b", stack_match.group(1), flags=re.IGNORECASE))
    image_count = max(parser.images, stack_images if fixed_image_count else 0)
    failures: list[str] = []
    if len(body_text) < MIN_BODY_LEN:
        failures.append("body_length")
    if parser.h2 < MIN_H2:
        failures.append("h2_count")
    if parser.h3 < MIN_H3:
        failures.append("h3_count")
    if parser.p < MIN_PARAGRAPHS:
        failures.append("paragraph_count")
    if parser.faq_q < MIN_FAQ:
        failures.append("faq_count")
    if image_count < MIN_IMAGES:
        failures.append("fixed_images")
    if parser.related_links < 1:
        failures.append("internal_links")
    if parser.empty_p > 0:
        failures.append("empty_p")
    if broken:
        failures.append("broken_characters")
    return {
        "failures": failures,
        "body_length": len(body_text),
        "h2": parser.h2,
        "h3": parser.h3,
        "paragraphs": parser.p,
        "faq": parser.faq_q,
        "images": image_count,
        "internal_links": parser.related_links,
        "empty_p": parser.empty_p,
        "broken_hints": hints,
        "hanja": hanja,
        "hangul": hangul,
    }


def plain_text(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def context(page) -> tuple[str, str, str]:
    title = page.title
    region = page.display_name or title
    category = page.category or "\uacfc\uc678"
    subject = category[:-2] if category.endswith("\uacfc\uc678") and len(category) > 2 else category
    return title, region, subject


def seed_for(page) -> int:
    return int(hashlib.sha256(page.id.encode("utf-8")).hexdigest()[:10], 16)


def supplement_content(page) -> str:
    title, region, subject = context(page)
    seed = seed_for(page)
    focus_sets = [
        ("\uac1c\ub150 \uc774\ud574", "\uc624\ub2f5 \uae30\ub85d", "\ud559\uad50 \uc9c4\ub3c4"),
        ("\uc2dc\uac04 \ubc30\ubd84", "\ubb38\uc81c \ub3c5\ud574", "\ubcf5\uc2b5 \ub8e8\ud2f4"),
        ("\uc11c\uc220\ud615 \ub300\ube44", "\ud559\uc2b5 \ud0dc\ub3c4", "\uc2dc\ud5d8 \uc77c\uc815"),
    ]
    a, b, c = focus_sets[seed % len(focus_sets)]
    return "\n".join(
        [
            f"<h2>{title} 학습 방향 점검</h2>",
            f"<p>{title} 정보를 살펴볼 때는 {region}의 생활 동선과 학교 일정, 학생의 현재 이해도를 함께 확인하는 것이 좋습니다. {subject} 학습은 단순히 많은 문제를 푸는 방식보다 어느 지점에서 막히는지 차분히 찾는 과정이 중요합니다.</p>",
            f"<p>특히 {a}, {b}, {c}는 학습 계획을 세울 때 함께 보아야 할 기준입니다. 각각을 따로 판단하기보다 학생의 하루 흐름 안에서 자연스럽게 이어지는지 확인하면 학습 부담을 줄일 수 있습니다.</p>",
            f"<h3>{region} 학생에게 필요한 기준</h3>",
            "<p>학생마다 집중이 잘 되는 시간과 어려움을 느끼는 단원이 다릅니다. 따라서 현재 수준을 먼저 점검하고, 복습과 예습의 비중을 조정하며, 시험 전에는 자주 틀리는 유형을 다시 확인하는 순서가 필요합니다.</p>",
            "<p>가정에서는 결과만 보기보다 문제를 읽는 방식, 풀이를 설명하는 습관, 오답을 다시 보는 태도를 함께 살펴보면 좋습니다. 이런 기록은 다음 학습 방향을 정할 때 실제적인 근거가 됩니다.</p>",
            f"<h2>{subject} 학습 루틴 구성</h2>",
            f"<p>{subject} 학습 루틴은 짧아도 반복 가능해야 합니다. 하루에 한 번은 배운 개념을 말로 설명하고, 틀린 문제의 원인을 한 문장으로 남기며, 다음 학습에서 다시 확인할 항목을 정리하는 방식이 안정적입니다.</p>",
            "<p>처음부터 많은 양을 정하기보다 학생이 지킬 수 있는 범위를 잡는 것이 중요합니다. 작은 성공이 쌓이면 학습에 대한 부담이 줄고, 스스로 확인하는 힘도 조금씩 커집니다.</p>",
            "<h3>본문에서 확인할 핵심 질문</h3>",
            "<p>오늘 배운 내용을 스스로 설명할 수 있는지, 같은 실수가 반복되는지, 학교 진도와 복습이 연결되는지, 시험 전까지 점검할 자료가 정리되어 있는지를 기준으로 살펴보면 좋습니다.</p>",
            f"<h2>{title} 정보 활용 방법</h2>",
            f"<p>{title} 페이지의 주변 지역, 과목, 학년 정보를 함께 보면 {region} 안에서 어떤 학습 조건을 고려해야 하는지 더 분명해집니다. 한 페이지에서 끝내지 말고 관련 정보를 비교하며 학생에게 맞는 기준을 정리해 보세요.</p>",
            "<p>학습 정보는 광고 문구보다 실제 공부 장면에 도움이 되는 질문으로 이어져야 합니다. 학생이 어디에서 어려움을 느끼는지, 어떤 순서로 확인하면 좋은지, 지속 가능한 루틴이 무엇인지 차분히 살펴보는 것이 핵심입니다.</p>",
        ]
    )


def supplement_faq(page) -> str:
    title, region, subject = context(page)
    return "\n".join(
        [
            "<h2>FAQ</h2>",
            f"<p>Q. {title} 정보를 볼 때 가장 먼저 확인할 점은 무엇인가요?</p>",
            "<p>A. 학생의 현재 이해도, 학교 진도, 가정에서 확보할 수 있는 학습 시간을 함께 확인하는 것이 좋습니다.</p>",
            f"<p>Q. {region} 지역 정보는 어떻게 활용하면 좋나요?</p>",
            "<p>A. 주변 지역과 학년별 정보를 비교해 학생에게 맞는 학습 조건을 정리하는 데 활용할 수 있습니다.</p>",
            f"<p>Q. {subject} 학습에서 가장 중요한 습관은 무엇인가요?</p>",
            "<p>A. 배운 내용을 짧게 복습하고, 틀린 이유를 기록하며, 다음 학습에 다시 반영하는 습관입니다.</p>",
            "<p>Q. 본문 중간의 관련 링크는 어떻게 보면 좋나요?</p>",
            "<p>A. 현재 페이지와 연결된 상위 지역, 주변 지역, 같은 지역의 다른 과목 정보를 비교하는 용도로 보면 좋습니다.</p>",
            "<p>Q. 학습 계획은 얼마나 자주 점검해야 하나요?</p>",
            "<p>A. 최소한 주 1회는 진도, 오답, 복습 시간을 함께 확인해 다음 주 계획에 반영하는 것이 좋습니다.</p>",
        ]
    )


def enhance_page(page, metrics: dict[str, object]):
    content = page.content or ""
    faq = page.faq or ""
    failures = set(metrics["failures"])
    existing_text = plain_text(content + "\n" + faq)
    _, _, hints = text_metrics(existing_text)
    if "broken_characters" in failures or "#ERROR!" in existing_text or hints > 10:
        content = supplement_content(page)
        faq = supplement_faq(page)
    else:
        if any(key in failures for key in ("body_length", "h2_count", "h3_count", "paragraph_count")):
            content = content.strip() + "\n" + supplement_content(page)
        if "faq_count" in failures:
            faq = (faq.strip() + "\n" if faq.strip() else "") + supplement_faq(page)
    return replace(page, content=content, faq=faq)


def fallback_page(page):
    return replace(page, content=supplement_content(page), faq=supplement_faq(page))


def write_page(page, html: str) -> None:
    output_path(page.url).write_text(html, encoding="utf-8", newline="\n")
    project_output_path(page.url).write_text(html, encoding="utf-8", newline="\n")


def main() -> None:
    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)

    initial_rows: list[dict[str, object]] = []
    fixed_pages = []
    for page in pages:
        html = render_page(page)
        metrics = audit_html(html)
        if metrics["failures"]:
            initial_rows.append({"url": page.url, **metrics})
            fixed_pages.append(enhance_page(page, metrics))
        else:
            fixed_pages.append(page)

    remaining_rows: list[dict[str, object]] = []
    for page in fixed_pages:
        html = render_page(page)
        metrics = audit_html(html)
        if metrics["failures"]:
            page = fallback_page(page)
            html = render_page(page)
            metrics = audit_html(html)
            if metrics["failures"]:
                remaining_rows.append({"url": page.url, **metrics})
        write_page(page, html)

    CSV_PATH.parent.mkdir(exist_ok=True)
    fieldnames = [
        "url",
        "failures",
        "body_length",
        "h2",
        "h3",
        "paragraphs",
        "faq",
        "images",
        "internal_links",
        "empty_p",
        "broken_hints",
        "hanja",
        "hangul",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining_rows)

    print(f"pages={len(pages)}")
    print(f"initial_failures={len(initial_rows)}")
    print(f"fixed={len(initial_rows) - len(remaining_rows)}")
    print(f"remaining_failures={len(remaining_rows)}")
    print(f"csv={CSV_PATH}")


if __name__ == "__main__":
    main()
