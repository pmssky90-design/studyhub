from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
REPORT = ROOT / "audit" / "self-link-output-fixes.csv"
def fix_breadcrumb(html: str) -> tuple[str, int]:
    nav_start = html.find('<nav class="breadcrumbs"')
    if nav_start < 0:
        return html, 0
    nav_end = html.find("</nav>", nav_start)
    if nav_end < 0:
        return html, 0
    nav_end += len("</nav>")
    nav = html[nav_start:nav_end]
    li_start = nav.rfind("<li><a ")
    if li_start < 0:
        return html, 0
    label_start = nav.find(">", li_start)
    label_end = nav.find("</a></li>", label_start)
    if label_start < 0 or label_end < 0:
        return html, 0
    label = nav[label_start + 1 : label_end]
    replacement = f'<li><span aria-current="page">{label}</span></li>'
    new_nav = nav[:li_start] + replacement + nav[label_end + len("</a></li>") :]
    if new_nav == nav:
        return html, 0
    return html[:nav_start] + new_nav + html[nav_end:], 1


def main() -> None:
    rows = []
    for path in OUTPUT.rglob("index.html"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        new_html, breadcrumb_changes = fix_breadcrumb(html)
        brand_changes = 0
        if path == OUTPUT / "index.html":
            updated = new_html.replace('<a class="brand" href="/">StudyHub</a>', '<span class="brand" aria-current="page">StudyHub</span>', 1)
            if updated != new_html:
                brand_changes = 1
            new_html = updated
        if new_html != html:
            path.write_text(new_html, encoding="utf-8")
            rows.append(
                {
                    "file": path.as_posix(),
                    "breadcrumb_current_item_fixed": str(breadcrumb_changes),
                    "root_brand_fixed": str(brand_changes),
                }
            )

    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "breadcrumb_current_item_fixed", "root_brand_fixed"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"changed_files={len(rows)}")


if __name__ == "__main__":
    main()
