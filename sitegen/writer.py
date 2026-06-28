import shutil

from config import ASSETS_DIR, OUTPUT_DIR, ROBOTS_TEXT
from sitegen.pages import RenderedFile
from sitegen.urls import output_path
from sitegen.utils import reset_dir


def write_site(files: list[RenderedFile]) -> None:
    reset_dir(OUTPUT_DIR)
    copy_assets()
    for file in files:
        write_file(file)
    remove_empty_dirs()
    (OUTPUT_DIR / "robots.txt").write_text(ROBOTS_TEXT, encoding="utf-8", newline="\n")


def copy_assets() -> None:
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, OUTPUT_DIR / "assets", dirs_exist_ok=True)


def write_file(file: RenderedFile) -> None:
    output_path(file.url).write_text(file.content, encoding="utf-8", newline="\n")


def remove_empty_dirs() -> None:
    directories = sorted(
        [item for item in OUTPUT_DIR.rglob("*") if item.is_dir()],
        key=lambda item: len(item.parts),
        reverse=True,
    )
    for path in directories:
        try:
            path.rmdir()
        except OSError:
            pass

