from dataclasses import replace
from urllib.parse import unquote, urlparse

from config import (
    CATEGORY_ENGLISH,
    CATEGORY_ELEMENTARY,
    CATEGORY_HIGH,
    CATEGORY_MATH,
    CATEGORY_MIDDLE,
    CATEGORY_TUTOR,
    CATEGORIES,
    ENGLISH_CHILD_CATEGORIES,
    MATH_CHILD_CATEGORIES,
    PRIMARY_CATEGORIES,
    SITE_NAME,
    CONTENT_SOURCE,
)
from sitegen.content_loader import attach_content, load_content
from sitegen.pages import Page
from sitegen.region_master import MasterRegion, ancestors as master_ancestors, children as master_children, load_region_master, siblings as master_siblings
from sitegen.regions import RegionNode, ancestors, read_regions
from sitegen.render import render_site
from sitegen.urls import breadcrumb_item, canonical_url, category_page_title, category_url, national_category_url, region_url, slug_url
from sitegen.writer import write_site


SIDO_SORT_ORDER = {
    "\uc11c\uc6b8": 1,
    "\uacbd\uae30": 2,
    "\uc778\ucc9c": 3,
    "\ubd80\uc0b0": 4,
    "\ub300\uad6c": 5,
    "\uad11\uc8fc": 6,
    "\ub300\uc804": 7,
    "\uc6b8\uc0b0": 8,
    "\uc138\uc885": 9,
    "\uac15\uc6d0": 10,
    "\ucda9\ubd81": 11,
    "\ucda9\ub0a8": 12,
    "\uc804\ubd81": 13,
    "\uc804\ub0a8": 14,
    "\uacbd\ubd81": 15,
    "\uacbd\ub0a8": 16,
    "\uc81c\uc8fc": 17,
}

NATIONAL_CATEGORY_SORT_ORDER = {
    CATEGORY_MATH: 1,
    CATEGORY_ENGLISH: 2,
    CATEGORY_ELEMENTARY: 1,
    CATEGORY_MIDDLE: 2,
    CATEGORY_HIGH: 3,
}


def build_site() -> None:
    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)
    write_site(render_site(pages))

    print(f"{SITE_NAME} generation complete")
    print(f"region nodes: {len(regions)}")
    print(f"excel slugs: {len(content_by_slug)}")
    print(f"pages: {len(pages)}")
    print(f"sitemap urls: {len(pages)}")


def build_pages(
    roots: list[RegionNode],
    regions: dict[str, RegionNode],
    content_slugs: set[str] | None = None,
) -> list[Page]:
    content_slugs = content_slugs or set()
    pages: list[Page] = []
    pages.append(build_national_tutor_page(roots, regions))
    for category in CATEGORIES:
        if category != CATEGORY_TUTOR:
            pages.append(build_national_category_page(roots, regions, category))

    needed_category_page_ids = needed_region_category_page_ids(regions, content_slugs)
    for region in regions.values():
        pages.append(build_region_page(region, regions))
        for category in CATEGORIES:
            if category != CATEGORY_TUTOR and category_page_id(region, category) in needed_category_page_ids:
                pages.append(build_category_page(region, regions, category))

    page_keys = {page.url.strip("/").split("/")[-1] for page in pages}
    for slug in sorted(content_slugs):
        if slug not in page_keys:
            pages.append(build_excel_slug_page(slug))
    return connect_region_master(add_region_master_hubs(pages, content_slugs))


def build_national_tutor_page(roots: list[RegionNode], regions: dict[str, RegionNode]) -> Page:
    title = "\uc804\uad6d\uacfc\uc678"
    url = national_category_url(CATEGORY_TUTOR)
    return make_page(
        page_id="root:all",
        region_key=None,
        display_name="\uc804\uad6d",
        slug="\uc804\uad6d",
        title=title,
        page_type="root",
        category=CATEGORY_TUTOR,
        parent=None,
        children=[region_page_id(item) for item in roots] + [national_category_page_id(item) for item in PRIMARY_CATEGORIES if item != CATEGORY_TUTOR],
        siblings=[],
        url=url,
        breadcrumb=[breadcrumb_item(title, url)],
        sections=[
            ("\uc2dc\ub3c4", region_links(roots, regions)),
            ("\uacfc\uc678 \uc720\ud615", national_primary_category_links()),
        ],
    )


def build_national_category_page(roots: list[RegionNode], regions: dict[str, RegionNode], category: str) -> Page:
    title = category
    url = national_category_url(category)
    sections = [
        ("\uc2dc\ub3c4", category_links(roots, regions, category)),
        ("\uc0c1\uc704 \uad6c\uc870", [link("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR))]),
    ]
    sections.extend(category_family_sections(None, regions, category))
    return make_page(
        page_id=national_category_page_id(category),
        region_key=None,
        display_name=category,
        slug=category,
        title=title,
        page_type=category_page_type(category),
        category=category,
        parent="root:all",
        children=[category_page_id(item, category) for item in roots],
        siblings=[national_category_page_id(item) for item in CATEGORIES if item != CATEGORY_TUTOR and item != category],
        url=url,
        breadcrumb=[breadcrumb_item("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR)), breadcrumb_item(title, url)],
        sections=sections,
    )


def build_region_page(region: RegionNode, regions: dict[str, RegionNode]) -> Page:
    url = region_url(region, regions)
    sections = [
        ("\uc0c1\uc704 \uc9c0\uc5ed", parent_region_links(region, regions)),
        ("\ud558\uc704 \uc9c0\uc5ed", region_links(region.children, regions)),
        ("\ud615\uc81c \uc9c0\uc5ed", sibling_region_links(region, regions)),
        ("\uacfc\uc678 \uc720\ud615", region_primary_category_links(region, regions)),
    ]
    return make_page(
        page_id=region_page_id(region),
        region_key=region.region_key,
        display_name=region.display_name,
        slug=region.slug,
        title=region.title,
        page_type=region_page_type(region),
        category=CATEGORY_TUTOR,
        parent=region_page_id(regions[region.parent]) if region.parent else "root:all",
        children=[region_page_id(item) for item in region.children],
        siblings=[region_page_id(item) for item in sibling_regions(region, regions)],
        url=url,
        breadcrumb=region_breadcrumbs(region, regions),
        sections=sections,
    )


def build_category_page(region: RegionNode, regions: dict[str, RegionNode], category: str) -> Page:
    title = category_page_title(region, category)
    url = category_url(region, regions, category)
    sections = [
        ("\uc0c1\uc704 \uc9c0\uc5ed", parent_category_links(region, regions, category)),
        ("\ud558\uc704 \uc9c0\uc5ed", category_links(region.children, regions, category)),
        ("\ud615\uc81c \uc9c0\uc5ed", sibling_category_links(region, regions, category)),
        ("\uac19\uc740 \uc9c0\uc5ed \uacfc\uc678", region_primary_category_links(region, regions)),
        ("\uc9c0\uc5ed \uba54\uc778", [link(region.title, region_url(region, regions))]),
    ]
    sections.extend(category_family_sections(region, regions, category))
    return make_page(
        page_id=category_page_id(region, category),
        region_key=region.region_key,
        display_name=region.display_name,
        slug=region.slug,
        title=title,
        page_type=category_page_type(category),
        category=category,
        parent=category_page_id(regions[region.parent], category) if region.parent else national_category_page_id(category),
        children=[category_page_id(item, category) for item in region.children],
        siblings=[category_page_id(item, category) for item in sibling_regions(region, regions)],
        url=url,
        breadcrumb=category_breadcrumbs(region, regions, category),
        sections=sections,
    )


def build_excel_slug_page(slug: str) -> Page:
    category = category_from_slug(slug)
    display_name = slug[: -len(category)] if category and slug.endswith(category) else slug
    title = slug
    url = slug_url(slug)
    breadcrumb = [breadcrumb_item("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR))]
    if category and category != CATEGORY_TUTOR:
        breadcrumb.append(breadcrumb_item(category, national_category_url(category)))
    breadcrumb.append(breadcrumb_item(title, url))
    parent = national_category_page_id(category) if category and category != CATEGORY_TUTOR else "root:all"
    sections = [("\uc0c1\uc704 \uad6c\uc870", [link(breadcrumb[-2]["name"], breadcrumb[-2]["url"])])] if len(breadcrumb) > 1 else []
    return make_page(
        page_id=f"excel:{slug}",
        region_key=None,
        display_name=display_name,
        slug=slug,
        title=title,
        page_type=category_page_type(category) if category else "service",
        category=category,
        parent=parent,
        children=[],
        siblings=[],
        url=url,
        breadcrumb=breadcrumb,
        sections=sections,
    )


def make_page(
    page_id: str,
    region_key: str | None,
    display_name: str,
    slug: str,
    title: str,
    page_type: str,
    category: str | None,
    parent: str | None,
    children: list[str],
    siblings: list[str],
    url: str,
    breadcrumb: list[dict[str, str]],
    sections: list[tuple[str, list[dict[str, str]]]],
) -> Page:
    return Page(
        id=page_id,
        region_key=region_key,
        display_name=display_name,
        slug=slug,
        title=title,
        page_type=page_type,
        category=category,
        parent=parent,
        children=children,
        siblings=siblings,
        template=template_for(page_type),
        canonical=canonical_url(url),
        breadcrumb=breadcrumb,
        schema_type="WebPage",
        meta_description=meta_description(title),
        seo={"description": meta_description(title)},
        url=url,
        sort_order=sort_order_for(region_key, display_name, category),
        sections=sections,
    )


def region_page_id(region: RegionNode) -> str:
    return f"region:{region.region_key}"


def category_page_id(region: RegionNode, category: str) -> str:
    return f"category:{region.region_key}:{category}"


def national_category_page_id(category: str) -> str:
    return f"national:{category}"


def region_page_type(region: RegionNode) -> str:
    if region.level == "sido":
        return "city"
    if region.level == "sigungu":
        return "district"
    return "dong"


def category_page_type(category: str) -> str:
    if category in (CATEGORY_MATH, CATEGORY_ENGLISH):
        return "subject"
    if category in MATH_CHILD_CATEGORIES or category in ENGLISH_CHILD_CATEGORIES:
        return "subject_grade"
    return "grade"


def template_for(page_type: str) -> str:
    return f"{page_type}.html"


def category_from_slug(slug: str) -> str | None:
    for category in sorted(CATEGORIES, key=len, reverse=True):
        if slug.endswith(category):
            return category
    return None


def needed_region_category_page_ids(regions: dict[str, RegionNode], content_slugs: set[str]) -> set[str]:
    needed: set[str] = set()
    for region in regions.values():
        for category in CATEGORIES:
            if category == CATEGORY_TUTOR:
                continue
            if category_page_title(region, category) not in content_slugs:
                continue
            current: RegionNode | None = region
            while current is not None:
                needed.add(category_page_id(current, category))
                current = regions[current.parent] if current.parent else None
    return needed


def category_family_sections(
    region: RegionNode | None,
    regions: dict[str, RegionNode],
    category: str,
) -> list[tuple[str, list[dict[str, str]]]]:
    if category == CATEGORY_MATH:
        return [("\uc218\ud559\uacfc\uc678 \uc138\ubd80 \uad6c\uc870", scoped_category_links(region, regions, MATH_CHILD_CATEGORIES))]
    if category == CATEGORY_ENGLISH:
        return [("\uc601\uc5b4\uacfc\uc678 \uc138\ubd80 \uad6c\uc870", scoped_category_links(region, regions, ENGLISH_CHILD_CATEGORIES))]
    if category in MATH_CHILD_CATEGORIES:
        return [("\uc0c1\uc704 \uacfc\ubaa9", scoped_category_links(region, regions, [CATEGORY_MATH]))]
    if category in ENGLISH_CHILD_CATEGORIES:
        return [("\uc0c1\uc704 \uacfc\ubaa9", scoped_category_links(region, regions, [CATEGORY_ENGLISH]))]
    return []


def region_breadcrumbs(region: RegionNode, regions: dict[str, RegionNode]) -> list[dict[str, str]]:
    items = [breadcrumb_item("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR))]
    items.extend(breadcrumb_item(item.title, region_url(item, regions)) for item in ancestors(region, regions))
    return items


def category_breadcrumbs(region: RegionNode, regions: dict[str, RegionNode], category: str) -> list[dict[str, str]]:
    items = [breadcrumb_item("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR))]
    items.append(breadcrumb_item(category, national_category_url(category)))
    items.extend(
        breadcrumb_item(category_page_title(item, category), category_url(item, regions, category))
        for item in ancestors(region, regions)
    )
    return items


def parent_region_links(region: RegionNode, regions: dict[str, RegionNode]) -> list[dict[str, str]]:
    if not region.parent:
        return [link("\uc804\uad6d\uacfc\uc678", national_category_url(CATEGORY_TUTOR))]
    parent = regions[region.parent]
    return [link(parent.title, region_url(parent, regions))]


def parent_category_links(region: RegionNode, regions: dict[str, RegionNode], category: str) -> list[dict[str, str]]:
    if not region.parent:
        return [link(category, national_category_url(category))]
    parent = regions[region.parent]
    return [link(category_page_title(parent, category), category_url(parent, regions, category))]


def sibling_regions(region: RegionNode, regions: dict[str, RegionNode]) -> list[RegionNode]:
    if region.parent:
        return [item for item in regions[region.parent].children if item.key != region.key]
    return [item for item in regions.values() if item.parent is None and item.key != region.key]


def sibling_region_links(region: RegionNode, regions: dict[str, RegionNode]) -> list[dict[str, str]]:
    return region_links(sibling_regions(region, regions), regions)


def sibling_category_links(region: RegionNode, regions: dict[str, RegionNode], category: str) -> list[dict[str, str]]:
    return category_links(sibling_regions(region, regions), regions, category)


def region_links(items: list[RegionNode], regions: dict[str, RegionNode]) -> list[dict[str, str]]:
    return [link(item.title, region_url(item, regions)) for item in items]


def category_links(items: list[RegionNode], regions: dict[str, RegionNode], category: str) -> list[dict[str, str]]:
    return [link(category_page_title(item, category), category_url(item, regions, category)) for item in items]


def region_primary_category_links(region: RegionNode, regions: dict[str, RegionNode]) -> list[dict[str, str]]:
    links = [link(region.title, region_url(region, regions))]
    links.extend(link(category_page_title(region, item), category_url(region, regions, item)) for item in PRIMARY_CATEGORIES if item != CATEGORY_TUTOR)
    return links


def national_primary_category_links() -> list[dict[str, str]]:
    return [link(item, national_category_url(item)) for item in PRIMARY_CATEGORIES if item != CATEGORY_TUTOR]


def scoped_category_links(
    region: RegionNode | None,
    regions: dict[str, RegionNode],
    categories: list[str],
) -> list[dict[str, str]]:
    if region is None:
        return [link(item, national_category_url(item)) for item in categories]
    return [link(category_page_title(region, item), category_url(region, regions, item)) for item in categories]


def link(title: str, url: str) -> dict[str, str]:
    return {"title": title, "url": url}


def meta_description(title: str) -> str:
    return f"{title} | {SITE_NAME}"


def add_region_master_hubs(pages: list[Page], content_slugs: set[str]) -> list[Page]:
    master = load_region_master()
    if not master:
        return pages

    result = list(pages)
    by_key = {page_key(page): page for page in result}
    for slug in sorted(content_slugs):
        category = category_from_slug(slug)
        region_slug = region_slug_from_page_key(slug, category)
        if not category or region_slug not in master:
            continue
        for region in master_ancestors(master[region_slug], master):
            for needed_category in {CATEGORY_TUTOR, category}:
                if needed_category != CATEGORY_TUTOR and region.region_type == "root":
                    continue
                key = region_category_key(region.slug, needed_category)
                if key in by_key:
                    continue
                page = build_region_master_hub_page(region, needed_category)
                result.append(page)
                by_key[key] = page
    return result


def build_region_master_hub_page(region: MasterRegion, category: str) -> Page:
    title = region_category_key(region.slug, category)
    url = slug_url(title)
    page_type = master_region_page_type(region) if category == CATEGORY_TUTOR else category_page_type(category)
    return make_page(
        page_id=master_page_id(region.slug, category),
        region_key=region.slug,
        display_name=region.display_name,
        slug=region.slug,
        title=title,
        page_type=page_type,
        category=category,
        parent=None,
        children=[],
        siblings=[],
        url=url,
        breadcrumb=[breadcrumb_item(title, url)],
        sections=[],
    )


def connect_region_master(pages: list[Page]) -> list[Page]:
    master = load_region_master()
    if not master:
        return remove_missing_page_links(pages)

    by_key = {page_key(page): page for page in pages}
    connected: list[Page] = []
    for page in pages:
        category = page.category or category_from_slug(page_key(page))
        region_slug = region_slug_from_page_key(page_key(page), category)
        if not category or region_slug not in master:
            connected.append(page)
            continue

        region = master[region_slug]
        parent_page = parent_for_master_page(region, category, by_key, master)
        child_pages = pages_for_master_regions(master_children(region, master), category, by_key)
        sibling_pages = pages_for_master_regions(master_siblings(region, master), category, by_key)
        breadcrumb = breadcrumb_for_master_page(region, category, page, by_key, master)
        sections = sections_for_master_page(page, region, category, parent_page, child_pages, sibling_pages, by_key)

        connected.append(
            replace(
                page,
                region_key=region.slug,
                display_name=region.display_name,
                slug=region.slug,
                parent=parent_page.id if parent_page else page.parent,
                children=[child.id for child in child_pages],
                siblings=[sibling.id for sibling in sibling_pages],
                breadcrumb=breadcrumb,
                sections=sections,
            )
        )
    connected = connect_national_category_pages(connected, master)
    connected = connect_main_page_sections(connected)
    return remove_missing_page_links(connected)


def remove_missing_page_links(pages: list[Page]) -> list[Page]:
    valid_ids = {page.id for page in pages}
    valid_urls = {normalized_url_path(page.url) for page in pages}
    return [
        replace(
            page,
            children=[child for child in page.children if child in valid_ids],
            siblings=[sibling for sibling in page.siblings if sibling in valid_ids],
            sections=[
                (title, [item for item in links if normalized_url_path(item["url"]) in valid_urls])
                for title, links in page.sections
            ],
        )
        for page in pages
    ]


def normalized_url_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path if parsed.scheme or parsed.netloc else url
    return (unquote(path).strip() or "/").rstrip("/") + "/"


def parent_for_master_page(
    region: MasterRegion,
    category: str,
    pages: dict[str, Page],
    master: dict[str, MasterRegion],
) -> Page | None:
    if region.parent_slug:
        parent_region = master.get(region.parent_slug)
        if category != CATEGORY_TUTOR and parent_region and parent_region.region_type == "root":
            return pages.get(category)
        return pages.get(region_category_key(region.parent_slug, category))
    if category == CATEGORY_TUTOR:
        return None
    return pages.get(category)


def pages_for_master_regions(regions: list[MasterRegion], category: str, pages: dict[str, Page]) -> list[Page]:
    result = []
    for region in regions:
        page = pages.get(region_category_key(region.slug, category))
        if page:
            result.append(page)
    return result


def breadcrumb_for_master_page(
    region: MasterRegion,
    category: str,
    page: Page,
    pages: dict[str, Page],
    master: dict[str, MasterRegion],
) -> list[dict[str, str]]:
    items = []
    root = pages.get("\uc804\uad6d\uacfc\uc678")
    if root:
        append_breadcrumb(items, root.title, root.url)
    if category != CATEGORY_TUTOR:
        national = pages.get(category)
        if national:
            append_breadcrumb(items, national.title, national.url)
    for ancestor in master_ancestors(region, master):
        if category != CATEGORY_TUTOR and ancestor.region_type == "root":
            continue
        key = region_category_key(ancestor.slug, category)
        ancestor_page = pages.get(key)
        if ancestor_page:
            append_breadcrumb(items, ancestor_page.title, ancestor_page.url)
    if not items or items[-1]["url"] != page.canonical:
        append_breadcrumb(items, page.title, page.url)
    return items


def append_breadcrumb(items: list[dict[str, str]], title: str, url: str) -> None:
    item = breadcrumb_item(title, url)
    if items and items[-1]["url"] == item["url"]:
        return
    items.append(item)


def sections_for_master_page(
    page: Page,
    region: MasterRegion,
    category: str,
    parent_page: Page | None,
    child_pages: list[Page],
    sibling_pages: list[Page],
    pages: dict[str, Page],
) -> list[tuple[str, list[dict[str, str]]]]:
    sections = [
        ("\uc0c1\uc704 \uc9c0\uc5ed", page_links([parent_page] if parent_page else [])),
        ("\ud558\uc704 \uc9c0\uc5ed", page_links(child_pages)),
        ("\ud615\uc81c \uc9c0\uc5ed", page_links(sibling_pages)),
        ("\uac19\uc740 \uc9c0\uc5ed \uacfc\uc678", same_region_links(region, pages)),
    ]
    sections.extend(master_category_family_sections(region, category, pages))
    if category != CATEGORY_TUTOR:
        region_main = pages.get(region_category_key(region.slug, CATEGORY_TUTOR))
        sections.append(("\uc9c0\uc5ed \uba54\uc778", page_links([region_main] if region_main else [])))
    return sections


def connect_national_category_pages(pages: list[Page], master: dict[str, MasterRegion]) -> list[Page]:
    root_region = next((region for region in master.values() if region.region_type == "root"), None)
    if not root_region:
        return pages

    by_key = {page_key(page): page for page in pages}
    result = []
    for page in pages:
        if not page.category or page.category == CATEGORY_TUTOR or not page.id.startswith("national:"):
            result.append(page)
            continue

        child_pages = pages_for_master_regions(master_children(root_region, master), page.category, by_key)
        result.append(
            replace(
                page,
                children=[child.id for child in child_pages],
                sections=replace_national_child_section(page.sections, child_pages),
            )
        )
    return result


def replace_national_child_section(
    sections: list[tuple[str, list[dict[str, str]]]],
    child_pages: list[Page],
) -> list[tuple[str, list[dict[str, str]]]]:
    child_links = page_links(child_pages)
    result = []
    replaced = False
    for title, links in sections:
        if title == "\uc2dc\ub3c4":
            result.append((title, child_links))
            replaced = True
        else:
            result.append((title, links))
    if not replaced:
        result.insert(0, ("\uc2dc\ub3c4", child_links))
    return result


def connect_main_page_sections(pages: list[Page]) -> list[Page]:
    by_id = {page.id: page for page in pages}
    root = by_id.get("root:all")
    if not root:
        return pages

    direct_children = [page for page in pages if page.parent == root.id]
    region_pages = sort_pages_for_output(
        [page for page in direct_children if page.category == CATEGORY_TUTOR and page.page_type != "root"]
    )
    subject_pages = sort_pages_for_output(
        [page for page in direct_children if page.category != CATEGORY_TUTOR and page.page_type == "subject"]
    )
    grade_pages = sort_pages_for_output(
        [page for page in direct_children if page.category != CATEGORY_TUTOR and page.page_type == "grade"]
    )
    school_pages = sort_pages_for_output(
        [
            page
            for page in direct_children
            if page.page_type == "school" or "\ud559\uad50" in page.title or "\ud559\uad50" in page.slug
        ]
    )
    popular_pages = popular_region_pages(pages)

    sections = [
        ("\uc9c0\uc5ed", page_links(region_pages)),
        ("\uacfc\ubaa9", page_links(subject_pages)),
        ("\ud559\ub144", page_links(grade_pages)),
        ("\ud559\uad50", page_links(school_pages)),
        ("\uc778\uae30\uc9c0\uc5ed", page_links(popular_pages)),
    ]
    root_child_ids = unique_page_ids(region_pages + subject_pages + grade_pages + school_pages)

    return [replace(page, children=root_child_ids, sections=sections) if page.id == root.id else page for page in pages]


def popular_region_pages(pages: list[Page], limit: int = 30) -> list[Page]:
    candidates = [
        page
        for page in pages
        if page.category == CATEGORY_TUTOR and page.page_type in {"city", "district", "dong"} and page.children
    ]
    return sorted(candidates, key=lambda page: (-len(page.children), page.title))[:limit]


def unique_page_ids(pages: list[Page]) -> list[str]:
    result = []
    seen = set()
    for page in pages:
        if page.id in seen:
            continue
        seen.add(page.id)
        result.append(page.id)
    return result


def same_region_links(region: MasterRegion, pages: dict[str, Page]) -> list[dict[str, str]]:
    result = []
    for category in PRIMARY_CATEGORIES:
        page = pages.get(region_category_key(region.slug, category))
        if page:
            result.append(link(page.title, page.url))
    return result


def master_category_family_sections(region: MasterRegion, category: str, pages: dict[str, Page]) -> list[tuple[str, list[dict[str, str]]]]:
    if category == CATEGORY_MATH:
        return [("\uc218\ud559\uacfc\uc678 \uc138\ubd80 \uad6c\uc870", category_page_links(region, MATH_CHILD_CATEGORIES, pages))]
    if category == CATEGORY_ENGLISH:
        return [("\uc601\uc5b4\uacfc\uc678 \uc138\ubd80 \uad6c\uc870", category_page_links(region, ENGLISH_CHILD_CATEGORIES, pages))]
    if category in MATH_CHILD_CATEGORIES:
        return [("\uc0c1\uc704 \uacfc\ubaa9", category_page_links(region, [CATEGORY_MATH], pages))]
    if category in ENGLISH_CHILD_CATEGORIES:
        return [("\uc0c1\uc704 \uacfc\ubaa9", category_page_links(region, [CATEGORY_ENGLISH], pages))]
    return []


def category_page_links(region: MasterRegion, categories: list[str], pages: dict[str, Page]) -> list[dict[str, str]]:
    return page_links([pages.get(region_category_key(region.slug, category)) for category in categories])


def page_links(pages: list[Page | None]) -> list[dict[str, str]]:
    return [link(page.title, page.url) for page in sort_pages_for_output([page for page in pages if page])]


def sort_pages_for_output(pages: list[Page]) -> list[Page]:
    if not any(page.sort_order is not None for page in pages):
        return pages
    return [
        page
        for _, page in sorted(
            enumerate(pages),
            key=lambda item: sort_page_key(item[0], item[1]),
        )
    ]


def sort_page_key(index: int, page: Page) -> tuple[int, int, str, int]:
    if page.sort_order is None:
        return (1, 0, "", index)
    return (0, page.sort_order, page.display_name, index)


def sort_order_for(region_key: str | None, display_name: str, category: str | None) -> int | None:
    if region_key and "|" not in region_key:
        return SIDO_SORT_ORDER.get(display_name)
    if region_key is None and category:
        return NATIONAL_CATEGORY_SORT_ORDER.get(category)
    return None


def page_key(page: Page) -> str:
    return page.url.strip("/").split("/")[-1]


def region_slug_from_page_key(key: str, category: str | None) -> str:
    if category and key.endswith(category):
        return key[: -len(category)]
    return key


def region_category_key(region_slug: str, category: str) -> str:
    return f"{region_slug}{category}"


def master_page_id(region_slug: str, category: str) -> str:
    return f"master:{region_slug}:{category}"


def master_region_page_type(region: MasterRegion) -> str:
    if region.region_type == "sido":
        return "city"
    if region.region_type == "sigungu":
        return "district"
    if region.region_type == "root":
        return "root"
    return "dong"
