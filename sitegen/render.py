from datetime import datetime, timezone
import hashlib
import re

from config import FIXED_IMAGES, OG_IMAGES, SITE_NAME, SITE_URL
from sitegen.pages import Page, RenderedFile
from sitegen.seo import json_script, meta_tags, webpage_schema
from sitegen.utils import escape

STUDYNOTE_HERO_IMAGE = "ChatGPT Image 2026??6??26???ㅼ쟾 09_21_47.png"
STUDYNOTE_OG_IMAGE = "ChatGPT Image 2026??6??5???ㅽ썑 07_49_40.png"
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
  <a class="skip-link" href="#main">Skip to content</a>
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
        f'<span class="link-card-arrow">??/span>'
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
        f'<img class="hero-image" src="{STUDYHUB_MAIN_HERO_IMAGE}" alt="{escape(page.title)} StudyHub 援먯쑁 ?뺣낫 ?대?吏" '
        'width="1536" height="1024" loading="lazy" decoding="async">'
    )


def render_fixed_image_legacy(title: str, current_url: str, index: int, class_name: str = "flow-image") -> str:
    prefix = fixed_image_src_prefix(current_url)
    return (
        f'<figure class="{class_name}">'
        f'<img src="{prefix}{index:03d}.png" alt="{escape(title)} 留욎땄 怨쇱쇅 ?덈궡 ?대?吏 {index:03d}" '
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
        f'<img src="{escape(src)}" alt="{escape(title)} 留욎땄 怨쇱쇅 ?덈궡 ?대?吏 {index:03d}" '
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
    html = repair_malformed_closing_tags(html)
    html = demote_content_h1(html)
    html = add_heading_ids(html)
    return add_image_attributes(html)


def repair_malformed_closing_tags(html: str) -> str:
    for tag in ("h1", "h2", "h3", "p", "strong", "a", "li", "ul", "ol"):
        html = re.sub(rf"(</{tag}>)(?:/{tag}>)+", rf"</{tag}>", html, flags=re.IGNORECASE)
        html = re.sub(rf"(?<!<)/{tag}>", "", html, flags=re.IGNORECASE)
    return html


def demote_content_h1(html: str) -> str:
    html = re.sub(r"<h1(\b[^>]*)>", r"<h2\1>", html, flags=re.IGNORECASE)
    return re.sub(r"</h1>", "</h2>", html, flags=re.IGNORECASE)


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
    text = strip_tags(value).strip().lower()
    slug = re.sub(r"[^0-9a-z]+", "-", text).strip("-")
    if slug:
        return slug
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"section-{digest}"


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
        return f"{page.display_name} 湲곗??쇰줈 吏?? 怨쇰ぉ, ?숇뀈 ?뺣낫瑜?李⑤텇?섍쾶 ?댄렣蹂????덈뒗 StudyHub ?덈궡 ?섏씠吏?낅땲??"
    return page.meta_description




def natural_section_title(title: str) -> str:
    replacements = {
        "\uc0c1\uc704 \uad6c\uc870": "\ud568\uaed8 \uc0b4\ud3b4\ubcf4\ub294 \uc0c1\uc704 \uc9c0\uc5ed",
        "\uc0c1\uc704 \uc9c0\uc5ed": "\ud568\uaed8 \uc0b4\ud3b4\ubcf4\ub294 \uc0c1\uc704 \uc9c0\uc5ed",
        "\ud558\uc704 \uc9c0\uc5ed": "\uc778\uadfc \uc9c0\uc5ed",
        "\uc2dc\ub3c4": "\uc9c0\uc5ed\ubcc4\ub85c \ucc3e\uae30",
        "\ud615\uc81c \uc9c0\uc5ed": "\uc8fc\ubcc0 \uc9c0\uc5ed",
        "\uac19\uc740 \uc9c0\uc5ed \uacfc\uc678": "\ud568\uaed8 \ubcf4\uba74 \uc88b\uc740 \uc9c0\uc5ed \uc815\ubcf4",
        "\uc9c0\uc5ed \uba54\uc778": "\uad00\ub828 \uc9c0\uc5ed \uc815\ubcf4",
        "\uacfc\uc678 \uc720\ud615": "\uacfc\uc678 \uc720\ud615\ubcc4 \uc815\ubcf4",
        "\uc218\ud559\uacfc\uc678 \ud559\ub144\ubcc4 \uc815\ubcf4": "\uc218\ud559\uacfc\uc678 \ud559\ub144\ubcc4 \uc548\ub0b4",
        "\uc601\uc5b4\uacfc\uc678 \ud559\ub144\ubcc4 \uc815\ubcf4": "\uc601\uc5b4\uacfc\uc678 \ud559\ub144\ubcc4 \uc548\ub0b4",
    }
    return replacements.get(title.replace("\ud5c8\ube0c", "\uc815\ubcf4"), title.replace("\ud5c8\ube0c", "\uc815\ubcf4"))


def link_description(title: str, section_title: str = "") -> str:
    variants = [
        f"{title}\uc758 \ud559\uc2b5 \ud658\uacbd\uacfc \uad50\uc721 \uc815\ubcf4\ub97c \ud568\uaed8 \ud655\uc778\ud574 \ubcf4\uc138\uc694.",
        f"{title} \ud559\uc0dd\ub4e4\uc774 \uc790\uc8fc \uc0b4\ud3b4\ubcf4\ub294 \ud559\uc2b5 \uc815\ubcf4\ub97c \uc815\ub9ac\ud588\uc2b5\ub2c8\ub2e4.",
        f"{title}\uc640 \uc5f0\uacb0\ub41c \uc9c0\uc5ed, \uacfc\ubaa9, \ud559\ub144 \uc815\ubcf4\ub97c \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
        "\uc778\uadfc \uc9c0\uc5ed\uc758 \ud559\uc2b5 \uc815\ubcf4\ub3c4 \ud568\uaed8 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
        "\uac19\uc740 \uacfc\ubaa9\uc758 \ub2e4\ub978 \uc9c0\uc5ed \uc815\ubcf4\ub3c4 \uc790\uc5f0\uc2a4\ub7fd\uac8c \uc774\uc5b4\uc11c \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    ]
    if "\uc8fc\ubcc0" in section_title or "\uc778\uadfc" in section_title:
        return variants[3]
    if "\uc0c1\uc704" in section_title:
        return f"{title} \uc548\uc5d0\uc11c \uc774\uc5b4\uc9c0\ub294 \ud559\uc2b5 \ud750\ub984\uc744 \ud568\uaed8 \uc0b4\ud3b4\ubcf4\uc138\uc694."
    if "\uac19\uc740 \uc9c0\uc5ed" in section_title or "\ud568\uaed8 \ubcf4\uba74" in section_title:
        return "\uac19\uc740 \uc9c0\uc5ed\uc758 \ub2e4\ub978 \uacfc\uc678 \uc815\ubcf4\ub3c4 \ud568\uaed8 \uc0b4\ud3b4\ubcf4\uc138\uc694."
    if "\ud559\ub144" in section_title:
        return f"{title}\uc5d0 \ub9de\ub294 \ud559\ub144\ubcc4 \ud559\uc2b5 \ubc29\ud5a5\uc744 \ud655\uc778\ud574 \ubcf4\uc138\uc694."
    if "\uc9c0\uc5ed" in section_title:
        return variants[sum(ord(char) for char in title) % 3]
    return variants[sum(ord(char) for char in title) % len(variants)]


def link_description(title: str, section_title: str = "") -> str:
    seed = sum(ord(char) for char in f"{section_title}:{title}")
    nearby = [
        f"{title}\uc758 \ud559\uc2b5 \ubd84\uc704\uae30\ub97c \ud568\uaed8 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
        f"{title}\uc5d0\uc11c \uc774\uc5b4\uc9c0\ub294 \ud559\uc2b5 \ud750\ub984\ub3c4 \ucc28\ubd84\ud788 \uc0b4\ud3b4\ubcf4\uc138\uc694.",
        f"{title} \uc8fc\ubcc0\uc758 \uad50\uc721 \uc815\ubcf4\ub97c \ud568\uaed8 \uc815\ub9ac\ud574 \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        f"\uc778\uc811\ud55c {title} \uc815\ubcf4\ub97c \ube44\uad50\ud558\uba70 \ud559\uc2b5 \ubc29\ud5a5\uc744 \uc815\ub9ac\ud574 \ubcf4\uc138\uc694.",
        f"{title} \ud559\uc0dd\ub4e4\uc774 \uc0b4\ud3b4\ubcfc \ub9cc\ud55c \uad50\uc721 \uc815\ubcf4\ub97c \ud568\uaed8 \ud655\uc778\ud574 \ubcf4\uc138\uc694.",
    ]
    parent = [
        f"{title} \ubc94\uc704\uc5d0\uc11c \uc5f0\uacb0\ub418\ub294 \uc9c0\uc5ed \uc815\ubcf4\ub97c \uba3c\uc800 \uc0b4\ud3b4\ubcf4\uc138\uc694.",
        f"{title}\uc758 \ud559\uc2b5 \ud658\uacbd\uc744 \ubcf4\uba74 \ud604\uc7ac \uc9c0\uc5ed \uc815\ubcf4\ub97c \ub354 \ub113\uac8c \uc774\ud574\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        f"{title}\uc640 \ud568\uaed8 \ubcf4\uba74 \uc9c0\uc5ed \uacc4\uce35\uc744 \uc27d\uac8c \ud30c\uc545\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
    ]
    same_region = [
        f"{title}\uc758 \ub2e4\ub978 \uacfc\uc678 \uc815\ubcf4\ub97c \ud568\uaed8 \uc0b4\ud3b4\ubcf4\uc138\uc694.",
        f"\uac19\uc740 \uc9c0\uc5ed\uc5d0\uc11c \uc5f0\uacb0\ub418\ub294 {title} \uc815\ubcf4\ub3c4 \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        f"{title}\ub97c \ud1b5\ud574 \uacfc\ubaa9\uacfc \ud559\ub144 \ud750\ub984\uc744 \ud568\uaed8 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
    ]
    grade = [
        f"{title}\uc5d0 \ub9de\ub294 \ud559\ub144\ubcc4 \ud559\uc2b5 \ud750\ub984\uc744 \ud655\uc778\ud574 \ubcf4\uc138\uc694.",
        f"{title}\uc758 \uc900\ube44 \ud3ec\uc778\ud2b8\ub97c \ud559\ub144 \ub2e8\uacc4\uc640 \ud568\uaed8 \uc815\ub9ac\ud574 \ubcf4\uc138\uc694.",
        f"{title} \uc815\ubcf4\ub97c \ubcf4\uba74 \ud559\ub144\uc5d0 \ub530\ub978 \ud559\uc2b5 \ubc29\ud5a5\uc744 \uc138\uc6b0\uae30 \uc88b\uc2b5\ub2c8\ub2e4.",
    ]
    general = [
        f"{title}\uc758 \ud559\uc2b5 \ud658\uacbd\uacfc \uad50\uc721 \uc815\ubcf4\ub97c \ud568\uaed8 \ud655\uc778\ud574 \ubcf4\uc138\uc694.",
        f"{title}\uc640 \uc5f0\uacb0\ub41c \uc9c0\uc5ed, \uacfc\ubaa9, \ud559\ub144 \uc815\ubcf4\ub97c \ucc28\ubd84\ud788 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
        f"{title} \uc815\ubcf4\ub97c \ubc14\ud0d5\uc73c\ub85c \ud559\uc2b5 \uc120\ud0dd\uc9c0\ub97c \ub354 \ub113\uac8c \uc0b4\ud3b4\ubcf4\uc138\uc694.",
        f"{title} \ud559\uc0dd\ub4e4\uc774 \ucc38\uace0\ud560 \ub9cc\ud55c \ud559\uc2b5 \uc815\ubcf4\ub97c \ud568\uaed8 \uc815\ub9ac\ud588\uc2b5\ub2c8\ub2e4.",
    ]
    if "\uc8fc\ubcc0" in section_title or "\uc778\uadfc" in section_title:
        choices = nearby
    elif "\uc0c1\uc704" in section_title:
        choices = parent
    elif "\uac19\uc740 \uc9c0\uc5ed" in section_title or "\ud568\uaed8 \ubcf4\uba74" in section_title or "\uad00\ub828 \uc9c0\uc5ed" in section_title:
        choices = same_region
    elif "\ud559\ub144" in section_title or any(word in title for word in ("\ucd08\ub4f1", "\uc911\ub4f1", "\uace0\ub4f1")):
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
