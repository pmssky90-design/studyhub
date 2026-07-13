from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import CONTENT_SOURCE, ROBOTS_TEXT
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions
from sitegen.render import render_site


TEMP_OUTPUT = ROOT / "audit" / "regeneration-test-output"


def main() -> None:
    if TEMP_OUTPUT.exists():
        shutil.rmtree(TEMP_OUTPUT)
    TEMP_OUTPUT.mkdir(parents=True, exist_ok=True)

    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)
    files = render_site(pages)

    for rendered in files:
        parts = [part for part in rendered.url.strip("/").split("/") if part]
        if parts and "." in parts[-1]:
            target = TEMP_OUTPUT.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target = TEMP_OUTPUT.joinpath(*parts) / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered.content, encoding="utf-8", newline="\n")
    (TEMP_OUTPUT / "robots.txt").write_text(ROBOTS_TEXT, encoding="utf-8", newline="\n")
    print(f"rendered_files={len(files)}")


if __name__ == "__main__":
    main()
