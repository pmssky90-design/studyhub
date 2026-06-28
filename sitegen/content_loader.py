from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree
import zipfile

from config import CONTENT_SOURCE
from sitegen.pages import Page


CONTENT_FIELDS = {
    "title": "title",
    "content": "content",
    "body": "content",
    "본문": "content",
    "faq": "faq",
    "image": "image",
    "이미지": "image",
    "meta_description": "meta_description",
    "description": "meta_description",
    "메타설명": "meta_description",
}


def attach_content(
    pages: list[Page],
    source: Path = CONTENT_SOURCE,
    content_by_slug: dict[str, dict[str, str]] | None = None,
) -> list[Page]:
    if content_by_slug is None:
        if not source.exists():
            return pages
        content_by_slug = load_content(source)
    if not content_by_slug:
        return pages

    return [merge_page_content(page, content_by_slug.get(page_content_key(page))) for page in pages]


def load_content(source: Path) -> dict[str, dict[str, str]]:
    content: dict[str, dict[str, str]] = {}
    for rows in read_xlsx_sheets(source):
        if not rows:
            continue
        header = [normalize_header(cell) for cell in rows[0]]
        has_named_header = any(name in CONTENT_FIELDS or name in ("slug", "키워드", "keyword") for name in header)
        data_rows = rows[1:] if has_named_header else rows
        slug_index = find_index(header, ["slug", "키워드", "keyword"], 0)
        content_index = find_index(header, ["content", "body", "본문"], 1)
        field_indexes = {
            CONTENT_FIELDS[name]: index
            for index, name in enumerate(header)
            if name in CONTENT_FIELDS
        }
        field_indexes.setdefault("content", content_index)

        for row in data_rows:
            slug = cell(row, slug_index)
            if not slug:
                continue
            values = {field: cell(row, index) for field, index in field_indexes.items() if cell(row, index)}
            if values:
                content[slug] = values
    return content


def merge_page_content(page: Page, content: dict[str, str] | None) -> Page:
    if not content:
        return page

    title = content.get("title", page.title)
    meta_description = content.get("meta_description", page.meta_description)
    seo = dict(page.seo)
    seo["description"] = meta_description

    return replace(
        page,
        title=title,
        meta_description=meta_description,
        seo=seo,
        content=content.get("content", page.content),
        faq=content.get("faq", page.faq),
        image=content.get("image", page.image),
    )


def page_content_key(page: Page) -> str:
    return page.url.strip("/").split("/")[-1]


def normalize_header(value: str) -> str:
    return str(value or "").strip().lower()


def find_index(header: list[str], candidates: list[str], fallback: int) -> int:
    for candidate in candidates:
        if candidate in header:
            return header.index(candidate)
    return fallback


def cell(row: list[str], index: int) -> str:
    if index < 0 or len(row) <= index:
        return ""
    return str(row[index] or "").strip()


def read_xlsx_sheets(path: Path) -> list[list[list[str]]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheets: list[list[list[str]]] = []
    with zipfile.ZipFile(path) as archive:
        strings = shared_strings(archive, ns)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib.get("Id"): rel.attrib["Target"].lstrip("/") for rel in rels}
        for sheet in workbook.findall("a:sheets/a:sheet", ns):
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = relmap[rel_id]
            sheet_path = target if target.startswith("xl/") else "xl/" + target
            root = ElementTree.fromstring(archive.read(sheet_path))
            sheets.append(read_sheet_rows(root, strings, ns))
    return sheets


def read_sheet_rows(root: ElementTree.Element, strings: list[str], ns: dict[str, str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in root.findall(".//a:sheetData/a:row", ns):
        values: dict[int, str] = {}
        for cell_node in row.findall("a:c", ns):
            ref = cell_node.attrib.get("r", "A1")
            values[column_index(ref)] = cell_value(cell_node, strings, ns)
        if values:
            rows.append([values.get(index, "") for index in range(max(values) + 1)])
    return rows


def shared_strings(archive: zipfile.ZipFile, ns: dict[str, str]) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//a:t", ns)) for item in root.findall("a:si", ns)]


def cell_value(cell_node: ElementTree.Element, strings: list[str], ns: dict[str, str]) -> str:
    if cell_node.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell_node.findall(".//a:t", ns)).strip()
    value = cell_node.find("a:v", ns)
    if value is None or value.text is None:
        return ""
    if cell_node.attrib.get("t") == "s":
        index = int(value.text)
        return strings[index].strip() if index < len(strings) else ""
    return value.text.strip()


def column_index(ref: str) -> int:
    letters = ""
    for char in ref.upper():
        if not char.isalpha():
            break
        letters += char
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - 64)
    return index - 1
