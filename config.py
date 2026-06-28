from pathlib import Path

PROJECT_NAME = "StudyHub"
SITE_NAME = "StudyHub"
SITE_DOMAIN = "studyhub.co.kr"
SITE_URL = "https://studyhub.co.kr"

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
OUTPUT_DIR = ROOT_DIR / "output"

REGION_SOURCE = DATA_DIR / "regions.xlsx"
CSV_REGION_SOURCE = DATA_DIR / "regions.csv"
CONTENT_SOURCE = Path(r"c:\gptwp\자료\12개_메인허브글_스터디허브.xlsx")

CATEGORY_TUTOR = "\uacfc\uc678"
CATEGORY_MATH = "\uc218\ud559\uacfc\uc678"
CATEGORY_ENGLISH = "\uc601\uc5b4\uacfc\uc678"
CATEGORY_ELEMENTARY = "\ucd08\ub4f1\uacfc\uc678"
CATEGORY_MIDDLE = "\uc911\ub4f1\uacfc\uc678"
CATEGORY_HIGH = "\uace0\ub4f1\uacfc\uc678"
CATEGORY_ELEMENTARY_MATH = "\ucd08\ub4f1\uc218\ud559\uacfc\uc678"
CATEGORY_MIDDLE_MATH = "\uc911\ub4f1\uc218\ud559\uacfc\uc678"
CATEGORY_HIGH_MATH = "\uace0\ub4f1\uc218\ud559\uacfc\uc678"
CATEGORY_ELEMENTARY_ENGLISH = "\ucd08\ub4f1\uc601\uc5b4\uacfc\uc678"
CATEGORY_MIDDLE_ENGLISH = "\uc911\ub4f1\uc601\uc5b4\uacfc\uc678"
CATEGORY_HIGH_ENGLISH = "\uace0\ub4f1\uc601\uc5b4\uacfc\uc678"

PRIMARY_CATEGORIES = [
    CATEGORY_TUTOR,
    CATEGORY_MATH,
    CATEGORY_ENGLISH,
    CATEGORY_ELEMENTARY,
    CATEGORY_MIDDLE,
    CATEGORY_HIGH,
]

MATH_CHILD_CATEGORIES = [
    CATEGORY_ELEMENTARY_MATH,
    CATEGORY_MIDDLE_MATH,
    CATEGORY_HIGH_MATH,
]

ENGLISH_CHILD_CATEGORIES = [
    CATEGORY_ELEMENTARY_ENGLISH,
    CATEGORY_MIDDLE_ENGLISH,
    CATEGORY_HIGH_ENGLISH,
]

CATEGORIES = PRIMARY_CATEGORIES + MATH_CHILD_CATEGORIES + ENGLISH_CHILD_CATEGORIES

HERO_IMAGE = "/assets/images/studyhub-hero.svg"
HERO_IMAGE_WIDTH = 1200
HERO_IMAGE_HEIGHT = 630
CONTENT_IMAGE = "/assets/images/studyhub-content.webp"
CONTENT_IMAGE_WIDTH = 1200
CONTENT_IMAGE_HEIGHT = 630
FIXED_IMAGES = [
    f"/assets/images/studynote-source/fixed/{index:03d}.png"
    for index in range(1, 7)
]
LOGO_IMAGE = "/assets/images/studyhub-logo.png"
LOGO_IMAGE_WIDTH = 512
LOGO_IMAGE_HEIGHT = 512
OG_IMAGES = [
    f"/assets/images/og/image{index:02d}.webp"
    for index in range(1, 21)
]
DEFAULT_IMAGE = HERO_IMAGE
ROBOTS_TEXT = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
