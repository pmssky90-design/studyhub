from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
AUDIT = ROOT / "audit"


TARGETS: list[tuple[str, str, str]] = [
    ("/서울과외/", "/금천구과외/", "금천구과외"),
    ("/서울과외/", "/노원구과외/", "노원구과외"),
    ("/서울과외/", "/마포구과외/", "마포구과외"),
    ("/서울과외/강남구과외/", "/서울과외/강남구과외/역삼동과외/", "역삼동과외"),
    ("/서울과외/송파구과외/", "/서울과외/송파구과외/잠실동과외/", "잠실동과외"),
    ("/서울과외/송파구과외/", "/송파동과외/", "송파동과외"),
    ("/서울과외/강남구과외/", "/압구정동과외/", "압구정동과외"),
    ("/서울수학과외/", "/금천구수학과외/", "금천구수학과외"),
    ("/서울영어과외/", "/금천구영어과외/", "금천구영어과외"),
    ("/서울수학과외/", "/노원구수학과외/", "노원구수학과외"),
    ("/서울초등과외/", "/금천구초등과외/", "금천구초등과외"),
    ("/서울중등과외/", "/금천구중등과외/", "금천구중등과외"),
    ("/서울고등과외/", "/금천구고등과외/", "금천구고등과외"),
    ("/서울고등수학과외/", "/금천구고등수학과외/", "금천구고등수학과외"),
    ("/서울고등영어과외/", "/금천구고등영어과외/", "금천구고등영어과외"),
    ("/서울중등수학과외/", "/금천구중등수학과외/", "금천구중등수학과외"),
    ("/서울중등영어과외/", "/금천구중등영어과외/", "금천구중등영어과외"),
    ("/경기도과외/", "/김포과외/", "김포과외"),
    ("/경기도과외/", "/남양주과외/", "남양주과외"),
    ("/경기도과외/", "/부천과외/", "부천과외"),
]


def output_file(url_path: str) -> Path:
    if url_path == "/":
        return OUTPUT / "index.html"
    return OUTPUT / url_path.strip("/") / "index.html"


def render_band(parent: str, items: list[tuple[str, str]]) -> str:
    links = "".join(
        f'<li><a class="related-card" href="{url}"><strong>{title}</strong>'
        f"<span>{title}와 연결된 하위 학습 정보를 함께 살펴보세요.</span></a></li>"
        for url, title in items
    )
    return (
        '<aside class="related-link-band discovery-sample-links">'
        '<h2 id="연결-페이지-보강">연결 페이지 보강</h2>'
        f"<ul>{links}</ul>"
        "</aside>"
    )


def main() -> int:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for parent, child, title in TARGETS:
        grouped.setdefault(parent, []).append((child, title))

    report_rows = []
    for parent, items in grouped.items():
        file = output_file(parent)
        if not file.exists():
            raise FileNotFoundError(file)
        html = file.read_text(encoding="utf-8", errors="replace")
        added = []
        for child, title in items:
            if f'href="{child}"' not in html:
                added.append((child, title))
        if added:
            band = render_band(parent, added)
            marker = "  </main>"
            if marker not in html:
                raise ValueError(f"main close marker not found: {file}")
            html = html.replace(marker, f"    {band}\n{marker}", 1)
            file.write_text(html, encoding="utf-8", newline="\n")
        for child, title in items:
            report_rows.append([parent, child, title, file.relative_to(ROOT).as_posix(), int((child, title) in added)])

    with (AUDIT / "sample-link-hotfix.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["parent_path", "child_path", "child_title", "modified_file", "link_added"])
        writer.writerows(report_rows)
    print(f"parents_touched={len(grouped)} sample_children={len(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
