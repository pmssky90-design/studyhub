import json

from config import (
    APPLE_TOUCH_ICON,
    CATEGORIES,
    DEFAULT_IMAGE,
    FAVICON_16,
    FAVICON_32,
    FAVICON_ICO,
    LOGO_IMAGE,
    LOGO_IMAGE_HEIGHT,
    LOGO_IMAGE_WIDTH,
    OG_IMAGE_HEIGHT,
    OG_IMAGE_TYPE,
    OG_IMAGE_WIDTH,
    SITE_NAME,
    SITE_URL,
    THEME_COLOR,
)
from sitegen.utils import escape


def json_script(data: dict | list) -> str:
    if isinstance(data, list):
        data = graph_schema(data)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">{payload}</script>'


def graph_schema(items: list[dict]) -> dict:
    order = {"Organization": 0, "WebSite": 1, "WebPage": 2, "Service": 3, "BreadcrumbList": 4}
    graph = sorted(items, key=lambda item: order.get(item.get("@type", ""), 99))
    for item in graph:
        item.pop("@context", None)
    return {"@context": "https://schema.org", "@graph": graph}


def organization_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{SITE_URL.rstrip('/')}/#organization",
        "name": SITE_NAME,
        "url": SITE_URL,
        "logo": {
            "@type": "ImageObject",
            "url": f"{SITE_URL.rstrip('/')}{LOGO_IMAGE}",
            "width": LOGO_IMAGE_WIDTH,
            "height": LOGO_IMAGE_HEIGHT,
        },
    }


def website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{SITE_URL.rstrip('/')}/#website",
        "name": SITE_NAME,
        "url": SITE_URL,
        "publisher": {"@id": f"{SITE_URL.rstrip('/')}/#organization"},
    }


def breadcrumb_schema(items: list[dict[str, str]]) -> dict:
    page_url = items[-1]["url"] if items else SITE_URL
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{page_url}#breadcrumb",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": item["name"],
                "item": item["url"],
            }
            for index, item in enumerate(items)
        ],
    }


def webpage_schema(title: str, description: str, canonical: str, breadcrumbs: list[dict[str, str]]) -> list[dict]:
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "name": title,
        "description": description,
        "url": canonical,
        "isPartOf": {"@id": f"{SITE_URL.rstrip('/')}/#website"},
        "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": SITE_URL.rstrip("/") + DEFAULT_IMAGE},
    }
    service = service_schema(title, canonical)
    if service:
        webpage["mainEntity"] = {"@id": service["@id"]}
    items = [
        webpage,
        organization_schema(),
        website_schema(),
        breadcrumb_schema(breadcrumbs),
    ]
    if service:
        items.append(service)
    return items


def service_schema(title: str, canonical: str) -> dict | None:
    if title == "\uc804\uad6d\uacfc\uc678":
        return None
    if title == "전국과외":
        return None
    service_type = service_type_from_title(title)
    if not service_type:
        return None
    area_served = title[: -len(service_type)]
    if not area_served:
        return None
    return {
        "name": title,
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": f"{canonical}#service",
        "serviceType": service_type,
        "areaServed": {"@type": "Place", "name": area_served},
        "provider": {"@id": f"{SITE_URL.rstrip('/')}/#organization"},
        "url": canonical,
    }


def service_type_from_title(title: str) -> str | None:
    for category in sorted(CATEGORIES, key=len, reverse=True):
        if title.endswith(category):
            return category
    return None


def meta_tags(title: str, description: str, canonical: str) -> str:
    image_url = f"{SITE_URL.rstrip('/')}{DEFAULT_IMAGE}"
    return "\n".join(
        [
            f"<title>{escape(title)}</title>",
            f'<meta name="description" content="{escape(description)}">',
            f'<link rel="canonical" href="{escape(canonical)}">',
            f'<link rel="icon" href="{FAVICON_ICO}" sizes="any">',
            f'<link rel="icon" type="image/png" sizes="16x16" href="{FAVICON_16}">',
            f'<link rel="icon" type="image/png" sizes="32x32" href="{FAVICON_32}">',
            f'<link rel="apple-touch-icon" href="{APPLE_TOUCH_ICON}">',
            f'<meta name="theme-color" content="{THEME_COLOR}">',
            f'<meta property="og:title" content="{escape(title)}">',
            f'<meta property="og:description" content="{escape(description)}">',
            f'<meta property="og:url" content="{escape(canonical)}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:image" content="{image_url}">',
            f'<meta property="og:image:width" content="{OG_IMAGE_WIDTH}">',
            f'<meta property="og:image:height" content="{OG_IMAGE_HEIGHT}">',
            f'<meta property="og:image:type" content="{OG_IMAGE_TYPE}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{escape(title)}">',
            f'<meta name="twitter:description" content="{escape(description)}">',
            f'<meta name="twitter:image" content="{image_url}">',
        ]
    )
