import csv
import re
import unicodedata
import urllib.parse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CONTENT_SOURCE
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions


def page_key(page):
    return page.url.strip("/").split("/")[-1]


def normalize(value):
    return unicodedata.normalize("NFKC", urllib.parse.unquote(str(value or ""))).strip().lower()


def compact(value):
    return re.sub(r"\s+", "", normalize(value))


def main():
    roots, nodes = read_regions()
    base_pages = build_pages(roots, nodes)
    content = load_content(CONTENT_SOURCE)
    pages = attach_content(base_pages)

    content_keys = set(content)
    norm_map = {}
    compact_map = {}
    for key in content_keys:
        norm_map.setdefault(normalize(key), []).append(key)
        compact_map.setdefault(compact(key), []).append(key)

    rows = []
    matched = 0
    normalized_hits = []
    for page in pages:
        key = page_key(page)
        has_content = bool(page.content)
        if has_content:
            matched += 1
            reason = "matched"
            candidate = ""
        elif page.region_key is None or page.page_type in ("root", "city", "district"):
            reason = "hub_page_no_content"
            candidate = ""
        elif key not in content_keys and normalize(key) in norm_map:
            reason = "case_or_unicode_normalization_mismatch"
            candidate = "|".join(norm_map[normalize(key)][:5])
            normalized_hits.append(key)
        elif key not in content_keys and compact(key) in compact_map:
            reason = "whitespace_mismatch"
            candidate = "|".join(compact_map[compact(key)][:5])
            normalized_hits.append(key)
        else:
            reason = "excel_slug_missing"
            candidate = ""

        rows.append(
            {
                "page_id": page.id,
                "page_type": page.page_type,
                "category": page.category or "",
                "display_name": page.display_name,
                "slug": page.slug,
                "url": page.url,
                "content_key": key,
                "reason": reason,
                "candidate_excel_slug": candidate,
            }
        )

    unmatched_rows = [row for row in rows if row["reason"] != "matched"]
    output = Path("reports/unmatched_content_slugs.csv")
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(unmatched_rows)

    page_keys = {page_key(page) for page in pages}
    norm_page = {normalize(key): key for key in page_keys}
    compact_page = {compact(key): key for key in page_keys}
    unconnected_content = []
    for excel_slug in sorted(content_keys):
        if excel_slug in page_keys:
            continue
        reason = "no_generated_page_for_excel_slug"
        candidate = ""
        if normalize(excel_slug) in norm_page:
            reason = "case_or_unicode_normalization_mismatch"
            candidate = norm_page[normalize(excel_slug)]
        elif compact(excel_slug) in compact_page:
            reason = "whitespace_mismatch"
            candidate = compact_page[compact(excel_slug)]
        unconnected_content.append(
            {
                "excel_slug": excel_slug,
                "reason": reason,
                "candidate_page_slug": candidate,
            }
        )

    output2 = Path("reports/unconnected_excel_content_slugs.csv")
    with output2.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["excel_slug", "reason", "candidate_page_slug"])
        writer.writeheader()
        writer.writerows(unconnected_content)

    page_reasons = Counter(row["reason"] for row in unmatched_rows)
    content_reasons = Counter(row["reason"] for row in unconnected_content)
    print(f"pages={len(pages)}")
    print(f"matched={matched}")
    print(f"unmatched={len(unmatched_rows)}")
    print(f"match_rate={matched / len(pages) * 100:.2f}%")
    print(f"content_keys={len(content_keys)}")
    print(f"unconnected_content_keys={len(unconnected_content)}")
    print(f"page_reason_counts={dict(page_reasons)}")
    print(f"content_reason_counts={dict(content_reasons)}")
    print(f"normalized_or_spacing_page_misses={len(normalized_hits)}")
    print(f"unmatched_csv={output.resolve()}")
    print(f"unconnected_csv={output2.resolve()}")


if __name__ == "__main__":
    main()
