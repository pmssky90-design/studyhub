import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CONTENT_SOURCE
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions


def page_key(page):
    return page.url.strip("/").split("/")[-1]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    roots, regions = read_regions()
    content = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content)), content_by_slug=content)

    page_keys = [page_key(page) for page in pages]
    page_key_set = set(page_keys)
    excel_keys = set(content)

    excel_pages = [page for page in pages if page_key(page) in excel_keys]
    hub_pages = [page for page in pages if page_key(page) not in excel_keys]
    failed = sorted(excel_keys - page_key_set)
    parent_missing = sorted(page_key(page) for page in excel_pages if page.id.startswith("excel:"))
    duplicates = sorted(key for key, count in Counter(page_keys).items() if count > 1)
    connected = [page for page in excel_pages if page.content]
    missing_content = sorted(page_key(page) for page in excel_pages if not page.content)

    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    write_csv(report_dir / "failed_excel_slugs.csv", [{"slug": value} for value in failed], ["slug"])
    write_csv(report_dir / "parent_missing_excel_slugs.csv", [{"slug": value} for value in parent_missing], ["slug"])
    write_csv(report_dir / "duplicate_page_urls.csv", [{"slug": value} for value in duplicates], ["slug"])
    write_csv(report_dir / "excel_pages_missing_content.csv", [{"slug": value} for value in missing_content], ["slug"])

    print(f"excel_slug_count={len(excel_keys)}")
    print(f"total_pages={len(pages)}")
    print(f"excel_based_pages={len(excel_pages)}")
    print(f"auto_hub_pages={len(hub_pages)}")
    print(f"failed_slugs={len(failed)}")
    print(f"parent_missing_slugs={len(parent_missing)}")
    print(f"duplicate_urls={len(duplicates)}")
    print(f"content_connected_pages={len(connected)}")
    print(f"excel_pages_missing_content={len(missing_content)}")
    print(f"content_connection_success={len(connected) == len(excel_keys)}")
    print(f"hub_by_type={dict(Counter(page.page_type for page in hub_pages))}")
    print(f"parent_missing_examples={parent_missing[:20]}")


if __name__ == "__main__":
    main()
