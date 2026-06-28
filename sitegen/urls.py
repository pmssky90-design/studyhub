from pathlib import Path
from urllib.parse import quote

from config import OUTPUT_DIR, SITE_URL
from sitegen.regions import RegionNode, ancestors
from sitegen.utils import ensure_dir, slugify


def region_segments(node: RegionNode, nodes: dict[str, RegionNode]) -> list[str]:
    return [slugify(f"{item.slug}\uacfc\uc678") for item in ancestors(node, nodes)]


def region_url(node: RegionNode, nodes: dict[str, RegionNode]) -> str:
    return "/" + "/".join(region_segments(node, nodes)) + "/"


def category_url(node: RegionNode, nodes: dict[str, RegionNode], category: str) -> str:
    return "/" + slugify(category_page_slug(node, category)) + "/"


def national_category_url(category: str) -> str:
    title = "\uc804\uad6d\uacfc\uc678" if category == "\uacfc\uc678" else category
    return "/" + slugify(title) + "/"


def slug_url(slug: str) -> str:
    return "/" + slugify(slug) + "/"


def category_page_title(node: RegionNode, category: str) -> str:
    return node.display_name + category


def category_page_slug(node: RegionNode, category: str) -> str:
    return node.slug + category


def output_path(url: str) -> Path:
    parts = [part for part in url.strip("/").split("/") if part]
    if parts and "." in parts[-1]:
        target = OUTPUT_DIR.joinpath(*parts)
        ensure_dir(target.parent)
        return target
    target = OUTPUT_DIR.joinpath(*parts)
    ensure_dir(target)
    return target / "index.html"


def absolute_url(url: str) -> str:
    return SITE_URL.rstrip("/") + quote(url, safe="/-._~")


def canonical_url(url: str) -> str:
    return absolute_url(url)


def breadcrumb_item(name: str, url: str) -> dict[str, str]:
    return {"name": name, "url": absolute_url(url)}
