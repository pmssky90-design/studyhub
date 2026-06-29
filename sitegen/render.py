from datetime import datetime, timezone
import hashlib
import re

from config import FIXED_IMAGES, OG_IMAGES, SITE_NAME, SITE_URL
from sitegen.pages import Page, RenderedFile
from sitegen.seo import json_script, meta_tags, webpage_schema
from sitegen.utils import escape

STUDYNOTE_HERO_IMAGE = "ChatGPT Image 2026년 6월 26일 오전 09_21_47.png"
STUDYNOTE_OG_IMAGE = "ChatGPT Image 2026년 6월 5일 오후 07_49_40.png"
STUDYHUB_MAIN_HERO_IMAGE = "/assets/images/studyhub-main-hero.png"


def render_site(pages: list[Page]) -> list[RenderedFile]:
    files = [RenderedFile(page.url, render_page(page)) for page in pages]
    files.append(render_root_entry(pages[0]))
    files.append(render_sitemap(pages))
    return files


def render_page(page: Page, include_hero: bool = False, asset_url: str | None = None) -> str:
    representative_image = representative_image_for_page(page)
    schema = webpage_schema(page.title, page.meta_description, page.canonical, page.breadcrumb)
    schema[0]["primaryImageOfPage"]["url"] = absolute_image_url(representative_image)
    image_context_url = asset_url or page.url
    body_html = (
        f"{render_hero(page, image_context_url)}"
        f"{render_content(page)}"
        f"{render_fixed_image_stack(page.title, image_context_url)}"
        f'<section class="content-grid">{"".join(render_link_section(heading, links) for heading, links in page.sections if links)}</section>'
        if include_hero
        else render_detail_page_body(page, image_context_url)
    )
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {render_meta_tags(page, representative_image)}
  <link rel="stylesheet" href="/assets/css/style.css">
  {json_script(schema)}
</head>
<body>
  <a class="skip-link" href="#main">본문 바로가기</a>
  <header class="site-header">
    <a class="brand" href="/">{escape(SITE_NAME)}</a>
  </header>
  <main id="main">
    <nav class="breadcrumbs" aria-label="breadcrumb">{render_breadcrumbs(page.breadcrumb)}</nav>
    {body_html}
  </main>
  <footer class="site-footer">
    <p>{escape(SITE_NAME)}</p>
  </footer>
</body>
</html>
"""
    return add_missing_heading_ids(html)


def render_detail_page_body(page: Page, image_context_url: str) -> str:
    return (
        f"{render_page_header(page)}"
        f"{render_fixed_image_stack(page.title, image_context_url, class_name='detail-image-stack')}"
        f"{render_content(page, page.sections)}"
    )


def render_breadcrumbs(items: list[dict[str, str]]) -> str:
    return "<ol>" + "".join(f'<li><a href="{escape(item["url"])}">{escape(item["name"])}</a></li>' for item in items) + "</ol>"


def render_link_section(title: str, links: list[dict[str, str]]) -> str:
    display_title = natural_section_title(title)
    items = "".join(
        f'<li><a class="link-card" href="{escape(link["url"])}">'
        f'<span class="link-card-title">{escape(link["title"])}</span>'
        f'<span class="link-card-meta">{escape(link_description(link["title"], display_title))}</span>'
        f'<span class="link-card-arrow">→</span>'
        "</a></li>"
        for link in links
    )
    return f'<article class="link-panel"><h2 id="{heading_id(display_title)}">{escape(display_title)}</h2><ul>{items}</ul></article>'


def fixed_image_src_prefix(current_url: str) -> str:
    return "/assets/images/studynote-source/fixed/"


def thumb_image_src_prefix(current_url: str) -> str:
    depth = len([part for part in current_url.strip("/").split("/") if part])
    return "../" * depth + "images/thumbs/"


def render_hero(page: Page, current_url: str) -> str:
    return f"""<section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">{escape(SITE_NAME)}</p>
        <h1>{escape(page.title)}</h1>
      </div>
      {render_studynote_hero_image(page, current_url)}
    </section>"""


def render_page_header(page: Page) -> str:
    return f"""<section class="page-heading">
      <p class="eyebrow">{escape(SITE_NAME)}</p>
      <h1>{escape(page.title)}</h1>
      <p>{escape(page_intro(page))}</p>
    </section>"""


def render_studynote_hero_image(page: Page, current_url: str) -> str:
    return (
        f'<img class="hero-image" src="{STUDYHUB_MAIN_HERO_IMAGE}" alt="{escape(page.title)} StudyHub 교육 정보 이미지" '
        'width="1536" height="1024" loading="lazy" decoding="async">'
    )


def render_fixed_image_legacy(title: str, current_url: str, index: int, class_name: str = "flow-image") -> str:
    prefix = fixed_image_src_prefix(current_url)
    return (
        f'<figure class="{class_name}">'
        f'<img src="{prefix}{index:03d}.png" alt="{escape(title)} 맞춤 과외 안내 이미지 {index:03d}" '
        f'width="1200" height="630" loading="eager" decoding="async">'
        "</figure>"
    )


def render_fixed_image_stack_legacy(title: str, current_url: str, count: int = 6, class_name: str = "fixed-image-stack") -> str:
    blocks = [render_fixed_image_legacy(title, current_url, 1, "representative-image")]
    blocks.extend(render_fixed_image_legacy(title, current_url, index) for index in range(2, count + 1))
    return f'<div class="{class_name}">\n' + "\n".join(blocks) + "\n</div>"


def render_fixed_image(title: str, src: str, index: int, class_name: str = "flow-image") -> str:
    return (
        f'<figure class="{class_name}">'
        f'<img src="{escape(src)}" alt="{escape(title)} 맞춤 과외 안내 이미지 {index:03d}" '
        f'width="1200" height="630" loading="eager" decoding="async">'
        "</figure>"
    )


def render_fixed_image_stack(title: str, current_url: str, class_name: str = "fixed-image-stack") -> str:
    blocks = [
        render_fixed_image(title, src, index, "representative-image" if index == 1 else "flow-image")
        for index, src in enumerate(FIXED_IMAGES, start=1)
    ]
    return f'<div class="{class_name}">\n' + "\n".join(blocks) + "\n</div>"


def render_content(page: Page, sections: list[tuple[str, list[dict[str, str]]]] | None = None) -> str:
    sections = sections or []
    content_source = page.content or ""
    faq_source = page.faq or ""
    if not content_source and sections:
        content_source = fallback_content(page)
        faq_source = fallback_faq(page)
    if not content_source and not faq_source and not sections:
        return ""
    content = enhance_content_html(content_source)
    faq = enhance_content_html(faq_source)
    body = interleave_content_and_links(content, sections)
    return f'<section class="page-content">{body}{render_faq_content(faq)}</section>'


def cardize_content(html: str) -> str:
    html = html.strip()
    if not html:
        return ""
    parts = re.split(r"(?=<(?:h2|h3)\b)", html, flags=re.IGNORECASE)
    cards = [part.strip() for part in parts if part.strip()]
    return "".join(f'<article class="info-card">{part}</article>' for part in cards)


def split_content_cards(html: str) -> list[str]:
    html = html.strip()
    if not html:
        return []
    parts = re.split(r"(?=<(?:h2|h3)\b)", html, flags=re.IGNORECASE)
    return [f'<article class="info-card">{part.strip()}</article>' for part in parts if part.strip()]


def interleave_content_and_links(html: str, sections: list[tuple[str, list[dict[str, str]]]]) -> str:
    cards = split_content_cards(html)
    link_bands = [render_related_link_band(heading, links[:5]) for heading, links in sections if links]
    if not cards:
        return "".join(link_bands)

    output: list[str] = []
    for index, card in enumerate(cards):
        output.append(card)
        if index < len(link_bands):
            output.append(link_bands[index])
    if len(link_bands) > len(cards):
        output.extend(link_bands[len(cards):])
    return "".join(output)


def render_related_link_band(title: str, links: list[dict[str, str]]) -> str:
    if not links:
        return ""
    display_title = natural_section_title(title)
    items = "".join(
        f'<li><a class="related-card" href="{escape(link["url"])}">'
        f'<strong>{escape(link["title"])}</strong>'
        f'<span>{escape(link_description(link["title"], display_title))}</span>'
        "</a></li>"
        for link in links
    )
    return f'<aside class="related-link-band"><h2 id="{heading_id(display_title)}">{escape(display_title)}</h2><ul>{items}</ul></aside>'


def render_faq_content(html: str) -> str:
    html = html.strip()
    if not html:
        return ""
    return f'<section class="faq-card">{cardize_content(html)}</section>'


def enhance_content_html(html: str) -> str:
    html = add_heading_ids(html)
    return add_image_attributes(html)


def add_heading_ids(html: str) -> str:
    used: set[str] = set()

    def add_id(match: re.Match[str]) -> str:
        tag = match.group(1)
        attrs = match.group(2) or ""
        text = match.group(3)
        if re.search(r"\sid=", attrs):
            return match.group(0)
        value = unique_heading_id(heading_id(strip_tags(text)), used)
        return f"<{tag}{attrs} id=\"{value}\">{text}</{tag}>"

    return re.sub(r"<(h[23])([^>]*)>(.*?)</\1>", add_id, html, flags=re.IGNORECASE | re.DOTALL)


def add_missing_heading_ids(html: str) -> str:
    used = set(re.findall(r'\sid="([^"]+)"', html, flags=re.IGNORECASE))
    index = 1

    def add_id(match: re.Match[str]) -> str:
        nonlocal index
        tag = match.group(1)
        attrs = match.group(2) or ""
        if re.search(r"\sid=", attrs):
            return match.group(0)
        value = unique_heading_id(f"section-{index}", used)
        index += 1
        return f'<{tag}{attrs} id="{value}">'

    return re.sub(r"<(h[23])([^>]*)>", add_id, html, flags=re.IGNORECASE)


def add_image_attributes(html: str) -> str:
    def add_attrs(match: re.Match[str]) -> str:
        tag = match.group(0)
        tag = ensure_img_attr(tag, "loading", "lazy")
        tag = ensure_img_attr(tag, "width", "1200")
        tag = ensure_img_attr(tag, "height", "630")
        return ensure_img_attr(tag, "decoding", "async")

    return re.sub(r"<img\b[^>]*>", add_attrs, html, flags=re.IGNORECASE)


def ensure_img_attr(tag: str, name: str, value: str) -> str:
    if re.search(rf"\s{name}\s*=", tag, flags=re.IGNORECASE):
        return tag
    return tag[:-1] + f' {name}="{value}">'


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def heading_id(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "-", value.strip().lower()).strip("-")
    return slug or "section"


def unique_heading_id(value: str, used: set[str]) -> str:
    base = value
    index = 2
    while value in used:
        value = f"{base}-{index}"
        index += 1
    used.add(value)
    return value


def render_meta_tags(page: Page, representative_image: str) -> str:
    html = re.sub(
        r'(<meta property="og:image" content=")[^"]+(">)',
        rf'\1{absolute_image_url(representative_image)}\2',
        meta_tags(page.title, page.meta_description, page.canonical),
    )
    return re.sub(
        r'(<meta name="twitter:image" content=")[^"]+(">)',
        rf'\1{absolute_image_url(representative_image)}\2',
        html,
    )


def representative_image_for_page(page: Page) -> str:
    seed = page.slug or page.title
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return OG_IMAGES[int(digest, 16) % len(OG_IMAGES)]


def absolute_image_url(path: str) -> str:
    return SITE_URL.rstrip("/") + path


def page_intro(page: Page) -> str:
    if page.category:
        return f"{page.display_name} 기준으로 지역, 과목, 학년 정보를 차분하게 살펴볼 수 있는 StudyHub 안내 페이지입니다."
    return page.meta_description


def fallback_content(page: Page) -> str:
    title = page.title
    region = page.display_name or title.replace(page.category or "", "")
    category = page.category or "과외"
    focus_sets = [
        ("개념 이해", "오답 기록", "학교 진도"),
        ("시간 배분", "문제 독해", "복습 루틴"),
        ("서술형 대비", "학습 태도", "시험 일정"),
    ]
    seed = sum(ord(char) for char in page.id)
    first, second, third = focus_sets[seed % len(focus_sets)]
    return "\n".join(
        [
            f"<h2>{title} 학습 방향 점검</h2>",
            f"<p>{title} 정보를 살펴볼 때는 {region}의 생활 동선과 학교 일정, 학생의 현재 이해도를 함께 확인하는 것이 좋습니다. {category} 학습은 단순히 많은 문제를 푸는 방식보다 어느 지점에서 막히는지 차분히 찾는 과정이 중요합니다.</p>",
            f"<p>특히 {first}, {second}, {third}는 학습 계획을 세울 때 함께 보아야 할 기준입니다. 각각을 따로 판단하기보다 학생의 하루 흐름 안에서 자연스럽게 이어지는지 확인하면 학습 부담을 줄일 수 있습니다.</p>",
            f"<h3>{region} 학생에게 필요한 기준</h3>",
            "<p>학생마다 집중이 잘 되는 시간과 어려움을 느끼는 단원이 다릅니다. 따라서 현재 수준을 먼저 점검하고, 복습과 예습의 비중을 조정하며, 시험 전에는 자주 틀리는 유형을 다시 확인하는 순서가 필요합니다.</p>",
            "<p>가정에서는 결과만 보기보다 문제를 읽는 방식, 풀이를 설명하는 습관, 오답을 다시 보는 태도를 함께 살펴보면 좋습니다. 이런 기록은 다음 학습 방향을 정할 때 실제적인 근거가 됩니다.</p>",
            f"<h2>{category} 학습 루틴 구성</h2>",
            f"<p>{category} 학습 루틴은 짧아도 반복 가능해야 합니다. 하루에 한 번은 배운 개념을 말로 설명하고, 틀린 문제의 원인을 한 문장으로 남기며, 다음 학습에서 다시 확인할 항목을 정리하는 방식이 안정적입니다.</p>",
            "<p>처음부터 많은 양을 정하기보다 학생이 지킬 수 있는 범위를 잡는 것이 중요합니다. 작은 성공이 쌓이면 학습에 대한 부담이 줄고, 스스로 확인하는 힘도 조금씩 커집니다.</p>",
            "<h3>본문에서 확인할 핵심 질문</h3>",
            "<p>오늘 배운 내용을 스스로 설명할 수 있는지, 같은 실수가 반복되는지, 학교 진도와 복습이 연결되는지, 시험 전까지 점검할 자료가 정리되어 있는지를 기준으로 살펴보면 좋습니다.</p>",
            f"<h2>{title} 정보 활용 방법</h2>",
            f"<p>{title} 페이지의 주변 지역, 과목, 학년 정보를 함께 보면 {region} 안에서 어떤 학습 조건을 고려해야 하는지 더 분명해집니다. 한 페이지에서 끝내지 말고 관련 정보를 비교하며 학생에게 맞는 기준을 정리해 보세요.</p>",
            "<p>학습 정보는 광고 문구보다 실제 공부 장면에 도움이 되는 질문으로 이어져야 합니다. 학생이 어디에서 어려움을 느끼는지, 어떤 순서로 확인하면 좋은지, 지속 가능한 루틴이 무엇인지 차분히 살펴보는 것이 핵심입니다.</p>",
        ]
    )


def fallback_faq(page: Page) -> str:
    title = page.title
    region = page.display_name or title.replace(page.category or "", "")
    return "\n".join(
        [
            "<h2>FAQ</h2>",
            f"<p>Q. {title} 정보를 볼 때 가장 먼저 확인할 점은 무엇인가요?</p>",
            "<p>A. 학생의 현재 이해도, 학교 진도, 가정에서 확보할 수 있는 학습 시간을 함께 확인하는 것이 좋습니다.</p>",
            f"<p>Q. {region} 지역 정보는 어떻게 활용하면 좋나요?</p>",
            "<p>A. 주변 지역과 학년별 정보를 비교해 학생에게 맞는 학습 조건을 정리하는 데 활용할 수 있습니다.</p>",
            "<p>Q. 과외 학습에서 가장 중요한 습관은 무엇인가요?</p>",
            "<p>A. 배운 내용을 짧게 복습하고, 틀린 이유를 기록하며, 다음 학습에 다시 반영하는 습관입니다.</p>",
            "<p>Q. 본문 중간의 관련 링크는 어떻게 보면 좋나요?</p>",
            "<p>A. 현재 페이지와 연결된 상위 지역, 주변 지역, 같은 지역의 다른 과목 정보를 비교하는 용도로 보면 좋습니다.</p>",
            "<p>Q. 학습 계획은 얼마나 자주 점검해야 하나요?</p>",
            "<p>A. 최소한 주 1회는 진도, 오답, 복습 시간을 함께 확인해 다음 주 계획에 반영하는 것이 좋습니다.</p>",
        ]
    )


def natural_section_title(title: str) -> str:
    replacements = {
        "상위 구조": "함께 살펴보는 상위 지역",
        "상위 지역": "함께 살펴보는 상위 지역",
        "하위 지역": "인근 지역",
        "시도": "지역별로 찾기",
        "형제 지역": "주변 지역",
        "같은 지역 과외": "함께 보면 좋은 지역 정보",
        "지역 메인": "관련 지역 정보",
        "과외 유형": "과외 유형별 정보",
        "수학과외 허브": "지역별 수학과외",
        "영어과외 허브": "지역별 영어과외",
        "초등과외 허브": "지역별 초등과외",
        "중등과외 허브": "지역별 중등과외",
        "고등과외 허브": "지역별 고등과외",
        "수학과외 세부 구조": "수학과외 학년별 안내",
        "영어과외 세부 구조": "영어과외 학년별 안내",
    }
    return replacements.get(title, title.replace("허브", "정보"))


def link_description(title: str) -> str:
    if title.endswith("과외"):
        return f"{title[:-2]} 지역 학습 정보"
    return "관련 학습 정보"


def link_description(title: str, section_title: str = "") -> str:
    seed = sum(ord(char) for char in f"{section_title}:{title}")
    nearby = [
        f"{title}의 학습 분위기를 함께 비교해 보세요.",
        f"{title}에서 이어지는 학습 흐름도 차분히 살펴보세요.",
        f"{title} 주변의 교육 정보를 함께 정리해 볼 수 있습니다.",
        f"인접한 {title} 정보를 비교하며 학습 방향을 정리해 보세요.",
        f"{title} 학생들이 살펴볼 만한 교육 정보를 함께 확인해 보세요.",
    ]
    parent = [
        f"{title} 범위에서 연결되는 지역 정보를 먼저 살펴보세요.",
        f"{title}의 학습 환경을 보면 현재 지역 정보를 더 넓게 이해할 수 있습니다.",
        f"{title}와 함께 보면 지역 계층을 쉽게 파악할 수 있습니다.",
    ]
    same_region = [
        f"{title}의 다른 과외 정보를 함께 살펴보세요.",
        f"같은 지역에서 연결되는 {title} 정보도 확인할 수 있습니다.",
        f"{title}를 통해 과목과 학년 흐름을 함께 비교해 보세요.",
    ]
    grade = [
        f"{title}에 맞는 학년별 학습 흐름을 확인해 보세요.",
        f"{title}의 준비 포인트를 학년 단계와 함께 정리해 보세요.",
        f"{title} 정보를 보면 학년에 따른 학습 방향을 세우기 좋습니다.",
    ]
    general = [
        f"{title}의 학습 환경과 교육 정보를 함께 확인해 보세요.",
        f"{title}와 연결된 지역, 과목, 학년 정보를 차분히 비교해 보세요.",
        f"{title} 정보를 바탕으로 학습 선택지를 더 넓게 살펴보세요.",
        f"{title} 학생들이 참고할 만한 학습 정보를 함께 정리했습니다.",
    ]
    if "주변" in section_title or "인근" in section_title:
        choices = nearby
    elif "상위" in section_title:
        choices = parent
    elif "같은 지역" in section_title or "함께 보면" in section_title or "관련 지역" in section_title:
        choices = same_region
    elif "학년" in section_title or any(word in title for word in ("초등", "중등", "고등")):
        choices = grade
    else:
        choices = general
    return choices[seed % len(choices)]


def render_root_entry(root_page: Page) -> RenderedFile:
    return RenderedFile("/", render_page(root_page, include_hero=True, asset_url="/"))


def render_sitemap(pages: list[Page]) -> RenderedFile:
    lastmod = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{page.canonical}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return RenderedFile("/sitemap.xml", "\n".join(lines))
