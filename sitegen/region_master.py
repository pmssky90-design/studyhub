import csv
from dataclasses import dataclass
from pathlib import Path


REGION_MASTER_PATH = Path("data/region_master.csv")


@dataclass(frozen=True)
class MasterRegion:
    display_name: str
    slug: str
    parent_slug: str
    region_type: str


def load_region_master(path: Path = REGION_MASTER_PATH) -> dict[str, MasterRegion]:
    if not path.exists():
        return {}

    regions: dict[str, MasterRegion] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            slug = clean(row.get("slug"))
            if not slug:
                continue
            regions[slug] = MasterRegion(
                display_name=clean(row.get("display_name")) or slug,
                slug=slug,
                parent_slug=clean(row.get("parent_slug")),
                region_type=clean(row.get("region_type")),
            )
    return regions


def clean(value: object) -> str:
    return str(value or "").strip()


def ancestors(region: MasterRegion, regions: dict[str, MasterRegion]) -> list[MasterRegion]:
    result = [region]
    current = region
    while current.parent_slug and current.parent_slug in regions:
        current = regions[current.parent_slug]
        result.insert(0, current)
    return result


def children(region: MasterRegion, regions: dict[str, MasterRegion]) -> list[MasterRegion]:
    return [item for item in regions.values() if item.parent_slug == region.slug]


def siblings(region: MasterRegion, regions: dict[str, MasterRegion]) -> list[MasterRegion]:
    if not region.parent_slug:
        return []
    return [item for item in regions.values() if item.parent_slug == region.parent_slug and item.slug != region.slug]
