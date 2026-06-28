import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CONTENT_SOURCE
from sitegen.builder import build_pages, category_from_slug, region_slug_from_page_key
from sitegen.content_loader import attach_content, load_content
from sitegen.region_master import load_region_master
from sitegen.regions import read_regions


def page_key(page):
    return page.url.strip("/").split("/")[-1]


def main():
    roots, regions = read_regions()
    content = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content)), content_by_slug=content)
    ids = {page.id for page in pages}
    master = load_region_master()

    parent_connected = [page for page in pages if page.parent and page.parent in ids]
    parent_missing = [page for page in pages if not page.parent or page.parent not in ids]
    breadcrumb_ok = [page for page in pages if page.breadcrumb and page.breadcrumb[-1]["url"] == page.canonical]
    internal_link_ok = [page for page in pages if any(links for _, links in page.sections)]

    region_master_not_found = []
    for page in pages:
        category = page.category or category_from_slug(page_key(page))
        region_slug = region_slug_from_page_key(page_key(page), category)
        if region_slug and region_slug not in master and not page.id.startswith("national:"):
            region_master_not_found.append(page)

    print(f"total_pages={len(pages)}")
    print(f"parent_connected={len(parent_connected)}")
    print(f"parent_missing={len(parent_missing)}")
    print(f"breadcrumb_ok={len(breadcrumb_ok)}")
    print(f"internal_link_ok={len(internal_link_ok)}")
    print(f"region_master_not_found={len(region_master_not_found)}")
    print(f"parent_missing_examples={[(page.title, page.id, page.parent) for page in parent_missing[:10]]}")
    print(f"region_master_not_found_examples={[(page.title, page_key(page)) for page in region_master_not_found[:10]]}")


if __name__ == "__main__":
    main()
