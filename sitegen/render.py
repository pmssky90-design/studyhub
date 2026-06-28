from datetime import datetime, timezone
import re
from urllib.parse import quote

from config import FIXED_IMAGES, SITE_NAME, SITE_URL
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
    representative_image = studynote_og_image()
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
    <nav class="top-nav" aria-label="navigation">
      <a href="/sitemap.xml">Sitemap</a>
      <a href="/robots.txt">Robots</a>
    </nav>
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
    if not page.content and not page.faq and not sections:
        return ""
    content = enhance_content_html(page.content or "")
    faq = enhance_content_html(page.faq or "")
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
    return re.sub(
        r'(<meta property="og:image" content=")[^"]+(">)',
        rf'\1{absolute_image_url(representative_image)}\2',
        meta_tags(page.title, page.meta_description, page.canonical),
    )


def studynote_og_image() -> str:
    return "/images/thumbs/" + quote(STUDYNOTE_OG_IMAGE)


def absolute_image_url(path: str) -> str:
    return SITE_URL.rstrip("/") + path


def page_intro(page: Page) -> str:
    if page.category:
        return f"{page.display_name} 기준으로 지역, 과목, 학년 정보를 차분하게 살펴볼 수 있는 StudyHub 안내 페이지입니다."
    return page.meta_description


def natural_section_title(title: str) -> str:
    replacements = {
        "수학과외 허브": "지역별 수학과외",
        "영어과외 허브": "지역별 영어과외",
        "초등과외 허브": "지역별 초등과외",
        "중등과외 허브": "지역별 중등과외",
        "고등과외 허브": "지역별 고등과외",
        "수학과외 세부 구조": "수학과외 학년별 정보",
        "영어과외 세부 구조": "영어과외 학년별 정보",
        "상위 구조": "상위 정보",
    }
    return replacements.get(title, title.replace("허브", "정보"))


def link_description(title: str) -> str:
    if title.endswith("과외"):
        return f"{title[:-2]} 지역 학습 정보"
    return "관련 학습 정보"


def link_description(title: str, section_title: str = "") -> str:
    if "형제" in section_title or "인근" in section_title:
        return "인근 지역의 학습 정보도 함께 확인해 보세요."
    if "상위" in section_title:
        return "상위 지역의 학습 흐름을 함께 살펴보세요."
    if "같은 지역" in section_title:
        return "같은 지역의 다른 과외 정보도 함께 살펴보세요."
    if "학년" in section_title:
        return f"{title}에 맞는 학년별 학습 정보를 확인해 보세요."
    if "지역" in section_title:
        return f"{title} 지역의 학습 정보를 차분히 살펴보세요."
    if any(grade in title for grade in ("초등", "중등", "고등")):
        return f"{title} 학생을 위한 학습 정보를 확인해 보세요."
    return "관련 학습 정보를 함께 확인해 보세요."


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
