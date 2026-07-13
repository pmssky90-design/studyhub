from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"


def main() -> int:
    changed: list[list[str]] = []

    with (AUDIT / "h1-candidates.csv").open(encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            path = ROOT / row["file"]
            html = path.read_text(encoding="utf-8", errors="replace")
            updated = html
            # Keep the page header h1 and demote content h1s only.
            updated = re.sub(r'(<section class="page-content">.*)<h1([^>]*)>', r"\1<h2\2>", updated, flags=re.IGNORECASE | re.DOTALL)
            updated = re.sub(r'(</h1>.*</section>)', lambda m: m.group(1).replace("</h1>", "</h2>"), updated, flags=re.IGNORECASE | re.DOTALL)
            if updated != html:
                path.write_text(updated, encoding="utf-8", newline="\n")
                changed.append([row["file"], "demote_content_h1"])

    for relative in ["output/계양구과외/index.html", "output/산월동고등수학과외/index.html"]:
        path = ROOT / relative
        html = path.read_text(encoding="utf-8", errors="replace")
        updated = re.sub(r'<div\b[^>]*style=["\'][^"\']*display\s*:\s*none[^"\']*["\'][^>]*>\s*placeholder\s*</div>', "", html, flags=re.IGNORECASE)
        if updated != html:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed.append([relative, "remove_hidden_placeholder"])

    with (AUDIT / "confirmed-html-fixes.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["file", "fix"])
        writer.writerows(changed)
    print(f"changed={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
