import html
import re
import shutil
from pathlib import Path


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def slugify(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"\s+", "-", text)
    return text


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
