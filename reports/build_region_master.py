import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CATEGORIES, CONTENT_SOURCE
from sitegen.content_loader import load_content, read_xlsx_sheets
from sitegen.regions import read_regions
REGION_SOURCE = Path(r"C:\gptwp\자료\지역구조(메인지역).xlsx")
REGION_MASTER = Path("data/region_master.csv")
UNRESOLVED = Path("reports/region_master_unresolved.csv")


def strip_category(slug: str) -> str:
    for category in sorted(CATEGORIES, key=len, reverse=True):
        if slug.endswith(category):
            return slug[: -len(category)]
    return slug


def clean(value: str) -> str:
    return str(value or "").strip()


def short_sigungu(value: str) -> str:
    text = clean(value)
    return text[:-1] if text.endswith(("시", "군", "구")) else text


def url_slug(value: str) -> str:
    return "-".join(clean(value).split())


def add_region(regions: dict[str, dict[str, str]], display_name: str, slug: str, parent_slug: str, region_type: str) -> None:
    if not slug:
        return
    regions.setdefault(
        slug,
        {
            "display_name": display_name,
            "slug": slug,
            "parent_slug": parent_slug,
            "region_type": region_type,
        },
    )


def load_region_index() -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    rows = read_xlsx_sheets(REGION_SOURCE)[0]
    regions: dict[str, dict[str, str]] = {}
    by_slug: dict[str, list[dict[str, str]]] = {}

    add_region(regions, "전국", "전국", "", "root")

    for row in rows[1:]:
        values = [clean(cell) for cell in row[:4] if clean(cell)]
        if not values:
            continue
        if values and values[0] in ("A", "시도"):
            continue
        sido = values[0] if len(values) > 0 else ""
        middle = ""
        if len(values) >= 4:
            middle = values[1]
            sigungu = values[-2]
            dong = values[-1]
        elif len(values) == 3:
            sigungu = values[1]
            dong = values[2]
        elif len(values) == 2:
            sigungu = values[1]
            dong = ""
        else:
            sigungu = ""
            dong = ""

        if sido:
            add_region(regions, sido, sido, "전국", "sido")
        if middle:
            add_region(regions, middle, middle, sido, "sigungu")
        if sigungu:
            add_region(regions, sigungu, sigungu, sido, "sigungu")
            add_region(regions, short_sigungu(sigungu), short_sigungu(sigungu), sido, "sigungu")
        if dong:
            add_region(regions, dong, dong, sigungu, "eupmyeondong")
            add_region(regions, dong, f"{short_sigungu(sigungu)}{dong}", sigungu, "eupmyeondong")

    for item in regions.values():
        by_slug.setdefault(item["slug"], []).append(item)
    return regions, by_slug


def main() -> None:
    content = load_content(CONTENT_SOURCE)
    content_regions = sorted({strip_category(slug) for slug in content})
    regions, by_slug = load_region_index()

    master: dict[str, dict[str, str]] = {slug: dict(row) for slug, row in regions.items() if row["region_type"] in ("root", "sido")}
    unresolved = []

    for region_slug in content_regions:
        matches = by_slug.get(region_slug, [])
        if matches:
            chosen = matches[0]
            master[chosen["slug"]] = dict(chosen)
            parent_slug = chosen["parent_slug"]
            while parent_slug and parent_slug in regions:
                parent = regions[parent_slug]
                master[parent["slug"]] = dict(parent)
                parent_slug = parent["parent_slug"]
        else:
            unresolved.append({"slug": region_slug, "reason": "region_not_found_in_region_source"})

    _, engine_regions = read_regions()
    for node in engine_regions.values():
        parent_slug = "전국"
        if node.parent and node.parent in engine_regions:
            parent_slug = url_slug(engine_regions[node.parent].slug)
        region_type = {
            "sido": "sido",
            "sigungu": "sigungu",
            "eupmyeondong": "eupmyeondong",
        }.get(node.level, "eupmyeondong")
        master.setdefault(
            url_slug(node.slug),
            {
                "display_name": node.display_name,
                "slug": url_slug(node.slug),
                "parent_slug": parent_slug,
                "region_type": region_type,
            },
        )

    REGION_MASTER.parent.mkdir(exist_ok=True)
    with REGION_MASTER.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["display_name", "slug", "parent_slug", "region_type"])
        writer.writeheader()
        writer.writerows(sorted(master.values(), key=lambda row: (row["region_type"], row["parent_slug"], row["slug"])))

    UNRESOLVED.parent.mkdir(exist_ok=True)
    with UNRESOLVED.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["slug", "reason"])
        writer.writeheader()
        writer.writerows(unresolved)

    counts = {}
    for row in master.values():
        counts[row["region_type"]] = counts.get(row["region_type"], 0) + 1
    print(f"region_master={REGION_MASTER.resolve()}")
    print(f"unresolved_csv={UNRESOLVED.resolve()}")
    print(f"total_regions={len(master)}")
    print(f"sido_count={counts.get('sido', 0)}")
    print(f"sigungu_count={counts.get('sigungu', 0)}")
    print(f"eupmyeondong_count={counts.get('eupmyeondong', 0)}")
    print(f"unresolved_count={len(unresolved)}")


if __name__ == "__main__":
    main()
