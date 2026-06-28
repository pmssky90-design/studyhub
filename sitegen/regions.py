import csv
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from config import CSV_REGION_SOURCE, REGION_SOURCE
from sitegen.utils import clean_text


@dataclass
class RegionNode:
    key: str
    region_key: str
    display_name: str
    title: str
    base_name: str
    parent: str | None
    depth: int
    level: str
    slug: str = ""
    children: list["RegionNode"] = field(default_factory=list)


LEVELS = ["sido", "sigungu", "eupmyeondong"]

REGION_NAME_ALIASES = {
    "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc": "\uc11c\uc6b8",
    "\ubd80\uc0b0\uad11\uc5ed\uc2dc": "\ubd80\uc0b0",
    "\ub300\uad6c\uad11\uc5ed\uc2dc": "\ub300\uad6c",
    "\uc778\ucc9c\uad11\uc5ed\uc2dc": "\uc778\ucc9c",
    "\uad11\uc8fc\uad11\uc5ed\uc2dc": "\uad11\uc8fc",
    "\ub300\uc804\uad11\uc5ed\uc2dc": "\ub300\uc804",
    "\uc6b8\uc0b0\uad11\uc5ed\uc2dc": "\uc6b8\uc0b0",
    "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc": "\uc138\uc885",
    "\uac15\uc6d0\ud2b9\ubcc4\uc790\uce58\ub3c4": "\uac15\uc6d0",
    "\uacbd\uae30\ub3c4": "\uacbd\uae30",
    "\ucda9\uccad\ubd81\ub3c4": "\ucda9\ubd81",
    "\ucda9\uccad\ub0a8\ub3c4": "\ucda9\ub0a8",
    "\uc804\ubd81\ud2b9\ubcc4\uc790\uce58\ub3c4": "\uc804\ubd81",
    "\uc804\ub77c\ub0a8\ub3c4": "\uc804\ub0a8",
    "\uacbd\uc0c1\ubd81\ub3c4": "\uacbd\ubd81",
    "\uacbd\uc0c1\ub0a8\ub3c4": "\uacbd\ub0a8",
    "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4": "\uc81c\uc8fc",
}


def strip_tutor_suffix(value: str) -> str:
    text = clean_text(value)
    suffix = "\uacfc\uc678"
    return text[: -len(suffix)] if text.endswith(suffix) else text


def normalize_region_name(value: str) -> str:
    text = strip_tutor_suffix(value)
    return REGION_NAME_ALIASES.get(text, text)


def page_title(value: str) -> str:
    base = normalize_region_name(value)
    return f"{base}\uacfc\uc678"


def display_name(value: str) -> str:
    return normalize_region_name(value)


def read_regions() -> tuple[list[RegionNode], dict[str, RegionNode]]:
    rows = _read_source_rows()
    return build_tree(rows)


def _read_source_rows() -> list[list[str]]:
    csv_rows: list[list[str]] = []
    if CSV_REGION_SOURCE.exists():
        with CSV_REGION_SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
            csv_rows = [[clean_text(cell) for cell in row] for row in csv.reader(handle)]
    if REGION_SOURCE.exists():
        xlsx_rows = read_xlsx_rows(REGION_SOURCE)
        if len(xlsx_rows) >= max(len(csv_rows), 2):
            return xlsx_rows
    if csv_rows:
        return csv_rows
    raise FileNotFoundError(f"지역 데이터 파일이 없습니다: {REGION_SOURCE} 또는 {CSV_REGION_SOURCE}")


def build_tree(rows: list[list[str]]) -> tuple[list[RegionNode], dict[str, RegionNode]]:
    if not rows:
        return [], {}

    header = [clean_text(cell).lower() for cell in rows[0]]
    data_rows = rows[1:] if _looks_like_header(header) else rows
    if "title" in header and "parent" in header:
        roots, nodes = _build_parent_rows(header, data_rows)
    else:
        roots, nodes = _build_column_rows(data_rows, header if _looks_like_header(header) else [])
    _assign_region_keys(nodes)
    return roots, nodes


def _looks_like_header(header: list[str]) -> bool:
    joined = ",".join(header)
    return any(
        token in joined
        for token in [
            "\uc2dc\ub3c4",
            "\uc2dc\uad70\uad6c",
            "\uc74d\uba74\ub3d9",
            "title",
            "parent",
            "sido",
            "sigungu",
            "eupmyeondong",
        ]
    )


def _build_column_rows(rows: list[list[str]], header: list[str]) -> tuple[list[RegionNode], dict[str, RegionNode]]:
    nodes: dict[str, RegionNode] = {}
    order: list[str] = []
    name_indexes = [
        _header_index(header, ["\uc2dc\ub3c4", "sido"], 0),
        _header_index(header, ["\uc2dc\uad70\uad6c", "sigungu"], 1),
        _header_index(header, ["\uc74d\uba74\ub3d9", "eupmyeondong", "dong"], 2),
    ]
    slug_indexes = [
        _header_index(header, ["\uc2dc\ub3c4_slug", "sido_slug"], -1),
        _header_index(header, ["\uc2dc\uad70\uad6c_slug", "sigungu_slug"], -1),
        _header_index(header, ["\uc74d\uba74\ub3d9_slug", "eupmyeondong_slug", "dong_slug"], -1),
    ]

    for row in rows:
        values = [_row_value(row, index) for index in name_indexes]
        slugs = [_row_value(row, index) for index in slug_indexes]
        if len(values) >= 4 and values[1] and values[2] and values[1] == values[2]:
            values = [values[0], values[2], values[3]]
        path: list[str] = []
        for index, value in enumerate(values[:3]):
            if not value:
                continue
            name = display_name(value)
            slug = display_name(slugs[index]) if index < len(slugs) and slugs[index] else name
            title = f"{name}\uacfc\uc678"
            path.append(title)
            key = "|".join(path)
            if key in nodes:
                continue
            parent_key = "|".join(path[:-1]) if len(path) > 1 else None
            node = RegionNode(
                key=key,
                region_key=key,
                display_name=name,
                title=title,
                base_name=name,
                parent=parent_key,
                depth=len(path) - 1,
                level=LEVELS[min(index, len(LEVELS) - 1)],
                slug=slug,
            )
            nodes[key] = node
            order.append(key)
            if parent_key in nodes:
                nodes[parent_key].children.append(node)

    roots = [nodes[key] for key in order if nodes[key].parent is None]
    return roots, nodes


def _build_parent_rows(header: list[str], rows: list[list[str]]) -> tuple[list[RegionNode], dict[str, RegionNode]]:
    title_index = header.index("title")
    parent_index = header.index("parent")
    slug_index = header.index("slug") if "slug" in header else -1
    nodes: dict[str, RegionNode] = {}
    title_to_key: dict[str, str] = {}

    for row in rows:
        name = display_name(row[title_index] if len(row) > title_index else "")
        if not name:
            continue
        slug = display_name(row[slug_index] if slug_index >= 0 and len(row) > slug_index else "") or name
        title = f"{name}\uacfc\uc678"
        parent_name = display_name(row[parent_index] if len(row) > parent_index else "")
        parent_title = f"{parent_name}\uacfc\uc678" if parent_name else ""
        parent_key = title_to_key.get(parent_title)
        key = f"{parent_key}|{title}" if parent_key else title
        if key in nodes:
            continue
        depth = nodes[parent_key].depth + 1 if parent_key else 0
        node = RegionNode(
            key=key,
            region_key=key,
            display_name=name,
            title=title,
            base_name=name,
            parent=parent_key,
            depth=depth,
            level=LEVELS[min(depth, len(LEVELS) - 1)],
            slug=slug,
        )
        nodes[key] = node
        title_to_key[title] = key
        if parent_key:
            nodes[parent_key].children.append(node)

    roots = [node for node in nodes.values() if node.parent is None]
    return roots, nodes


def _header_index(header: list[str], candidates: list[str], fallback: int) -> int:
    for candidate in candidates:
        if candidate in header:
            return header.index(candidate)
    return fallback


def _row_value(row: list[str], index: int) -> str:
    if index < 0 or len(row) <= index:
        return ""
    return clean_text(row[index])


def _assign_region_keys(nodes: dict[str, RegionNode]) -> None:
    for node in nodes.values():
        node.region_key = "|".join(item.slug for item in ancestors(node, nodes))


def ancestors(node: RegionNode, nodes: dict[str, RegionNode]) -> list[RegionNode]:
    result = [node]
    while result[0].parent:
        result.insert(0, nodes[result[0].parent])
    return result


def descendants(node: RegionNode) -> list[RegionNode]:
    result: list[RegionNode] = []
    stack = list(node.children)
    while stack:
        child = stack.pop(0)
        result.append(child)
        stack.extend(child.children)
    return result


def read_xlsx_rows(path: Path) -> list[list[str]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        strings = _shared_strings(archive, ns)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        first_sheet = workbook.find("a:sheets/a:sheet", ns)
        rel_id = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = ""
        for rel in rels:
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib["Target"]
                break
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else "xl/" + target
        sheet = ElementTree.fromstring(archive.read(sheet_path))

    rows: list[list[str]] = []
    for row in sheet.findall(".//a:sheetData/a:row", ns):
        cells: dict[int, str] = {}
        for cell in row.findall("a:c", ns):
            ref = cell.attrib.get("r", "A1")
            column = _column_index(ref)
            cells[column] = _cell_value(cell, strings, ns)
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


def _shared_strings(archive: zipfile.ZipFile, ns: dict[str, str]) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall("a:si", ns):
        texts = [node.text or "" for node in item.findall(".//a:t", ns)]
        values.append("".join(texts))
    return values


def _cell_value(cell: ElementTree.Element, strings: list[str], ns: dict[str, str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return clean_text("".join(node.text or "" for node in cell.findall(".//a:t", ns)))
    value = cell.find("a:v", ns)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        index = int(value.text)
        return clean_text(strings[index] if index < len(strings) else "")
    return clean_text(value.text)


def _column_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref.upper())
    index = 0
    for char in letters.group(0):
        index = index * 26 + (ord(char) - 64)
    return index - 1
