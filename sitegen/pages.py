from dataclasses import dataclass, field


@dataclass(frozen=True)
class Page:
    id: str
    region_key: str | None
    display_name: str
    slug: str
    title: str
    page_type: str
    category: str | None
    parent: str | None
    children: list[str]
    siblings: list[str]
    template: str
    canonical: str
    breadcrumb: list[dict[str, str]]
    schema_type: str
    meta_description: str
    seo: dict[str, str]
    url: str
    sort_order: int | None = None
    content: str = ""
    faq: str = ""
    image: str = ""
    sections: list[tuple[str, list[dict[str, str]]]] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedFile:
    url: str
    content: str
