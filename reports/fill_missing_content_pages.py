from dataclasses import replace
from pathlib import Path
import hashlib
import json

from config import CONTENT_SOURCE
from sitegen.builder import build_pages
from sitegen.content_loader import attach_content, load_content
from sitegen.regions import read_regions
from sitegen.render import render_page
from sitegen.urls import output_path


ROOT = Path.cwd()

PATTERNS = [
    "학생 사례형",
    "학부모 관찰형",
    "학습 습관형",
    "지역 환경형",
    "오답 분석형",
    "시험 준비형",
    "시간 관리형",
    "실제 수업형",
    "학습 변화형",
    "체크리스트형",
]

OPENINGS = [
    "학습 정보를 찾을 때 가장 먼저 확인할 부분은 학생이 실제로 공부하는 환경과 생활 리듬입니다.",
    "지역과 과목을 함께 살펴보면 학생에게 필요한 학습 방향을 조금 더 구체적으로 이해할 수 있습니다.",
    "같은 과목이라도 학년, 학교 일정, 가정에서의 학습 습관에 따라 필요한 준비는 달라집니다.",
    "학습 계획은 거창한 목표보다 현재 수준을 정확히 살피는 과정에서 안정적으로 시작됩니다.",
]

FOCUSES = [
    "개념 이해",
    "오답 정리",
    "수업 복습",
    "문제 독해",
    "서술형 대비",
    "학습 루틴",
    "시간 배분",
    "학교 진도 확인",
]


def seed_for(page) -> int:
    return int(hashlib.sha256(page.id.encode("utf-8")).hexdigest()[:12], 16)


def pick(items: list[str], seed: int, offset: int = 0) -> str:
    return items[(seed + offset) % len(items)]


def clean_subject(value: str) -> str:
    value = (value or "과외").strip()
    return value[:-2] if value.endswith("과외") and len(value) > 2 else value


def page_context(page):
    title = page.title
    region = page.display_name or title
    category = page.category or "과외"
    subject = clean_subject(category)
    if page.region_key is None and title != "전국과외":
        region = "전국"
    if title == "전국과외":
        subject = "과외"
        region = "전국"
    return title, region, subject


def pattern_blocks(pattern: str, title: str, region: str, subject: str, focus_a: str, focus_b: str, focus_c: str) -> list[str]:
    if pattern == "학생 사례형":
        return [
            f"<h2>{title}를 살펴볼 때 중요한 기준</h2>",
            f"<p>한 학생은 문제를 풀 때 정답 여부만 확인하고 넘어가면서 비슷한 실수를 반복했습니다. {region} 학습 환경 안에서 {subject} 학습을 준비한다면 단원별 이해도와 오답의 이유를 함께 적어 두는 방식이 도움이 됩니다. 처음에는 문제를 많이 푸는 것보다 왜 틀렸는지 설명하는 시간이 더 중요할 수 있습니다.</p>",
            "<h3>학생에게 맞는 확인 질문</h3>",
            "<ul><li>오늘 배운 개념을 스스로 설명할 수 있는가</li><li>틀린 문제의 원인을 문장으로 정리했는가</li><li>학교 진도와 복습 일정이 연결되어 있는가</li><li>시험 전까지 반복할 자료가 정리되어 있는가</li></ul>",
        ]
    if pattern == "학부모 관찰형":
        return [
            f"<h2>가정에서 관찰할 수 있는 {subject} 학습 흐름</h2>",
            f"<p>학부모가 확인할 부분은 공부 시간이 길었는지보다 그 시간이 어떻게 쓰였는지입니다. {title} 정보를 볼 때도 단순한 양보다 집중이 유지되는 시간, 질문이 생기는 지점, 복습 후 남는 내용을 함께 살펴보는 편이 좋습니다.</p>",
            f"<h3>{region} 학습 생활에서 살펴볼 점</h3>",
            "<ul><li>숙제 후 다시 확인하는 시간이 있는가</li><li>어려운 단원을 미루지 않고 표시해 두는가</li><li>틀린 과정을 말로 설명하는 습관이 있는가</li><li>주말 복습이 다음 주 학습으로 이어지는가</li></ul>",
        ]
    if pattern == "학습 습관형":
        return [
            f"<h2>{region} 학생을 위한 학습 습관 정리</h2>",
            f"<p>{subject} 학습은 하루에 몰아서 해결하기보다 짧은 확인을 꾸준히 이어갈 때 이해가 깊어집니다. {title}와 관련된 정보를 찾는다면 먼저 학생의 주간 생활표를 살펴보고 어느 시간대에 집중이 잘 되는지 확인하는 것이 좋습니다.</p>",
            "<h3>작게 시작하는 루틴</h3>",
            f"<p>복습은 긴 시간이 아니어도 괜찮습니다. 핵심은 {focus_a}를 확인하고, 이어서 {focus_b}를 정리한 뒤, 마지막으로 {focus_c}를 점검하는 순서를 꾸준히 유지하는 것입니다.</p>",
        ]
    if pattern == "지역 환경형":
        return [
            f"<h2>{region} 지역 학습 환경과 {subject}</h2>",
            f"<p>{region}의 학습 환경은 학생의 이동 시간, 학교 일정, 주변 학습 분위기와 연결됩니다. {title}를 살펴볼 때는 특정 방식이 모두에게 맞는다고 보기보다 학생이 실제로 생활하는 공간 안에서 지속 가능한 흐름을 찾는 것이 중요합니다.</p>",
            "<h3>지역 정보를 볼 때의 기준</h3>",
            "<ul><li>학교 수업과 복습 시간이 충돌하지 않는가</li><li>학생의 질문을 정리할 시간이 충분한가</li><li>시험 기간과 평상시 계획이 구분되어 있는가</li><li>가정에서 확인 가능한 학습 기록이 있는가</li></ul>",
        ]
    if pattern == "오답 분석형":
        return [
            f"<h2>{subject} 오답을 바라보는 방법</h2>",
            f"<p>오답은 부족함을 확인하는 표시가 아니라 다음 학습의 방향을 알려 주는 자료입니다. {title} 정보를 활용할 때는 맞고 틀림보다 어떤 유형에서 시간이 오래 걸리는지, 어떤 개념이 흔들리는지 확인하는 과정이 필요합니다.</p>",
            "<h3>오답 기록에 남기면 좋은 내용</h3>",
            "<ul><li>틀린 이유를 계산, 개념, 독해, 시간으로 구분하기</li><li>비슷한 문제를 다시 볼 날짜 정하기</li><li>해설을 보기 전 스스로 시도한 풀이 남기기</li><li>반복되는 실수를 짧은 문장으로 정리하기</li></ul>",
        ]
    if pattern == "시험 준비형":
        return [
            f"<h2>{title}와 시험 준비 흐름</h2>",
            f"<p>시험 준비는 마지막 기간에만 시작되는 일이 아닙니다. {region}에서 {subject} 학습을 준비하는 학생이라면 평소 수업 복습, 단원별 확인, 시험 범위 정리, 실전 연습이 자연스럽게 이어져야 합니다.</p>",
            "<h3>시험 전 점검 순서</h3>",
            "<ul><li>학교 프린트와 교과서 개념 확인</li><li>자주 틀리는 유형 다시 풀기</li><li>서술형 답안의 표현 점검</li><li>남은 기간에 맞춘 반복 계획 세우기</li></ul>",
        ]
    if pattern == "시간 관리형":
        return [
            f"<h2>{subject} 학습 시간 관리</h2>",
            f"<p>시간 관리는 단순히 오래 앉아 있는 문제가 아닙니다. {title}를 기준으로 정보를 살펴볼 때는 학생이 어느 단계에서 시간이 지연되는지, 복습과 문제 풀이의 균형이 맞는지 확인해야 합니다.</p>",
            "<h3>시간을 나누는 방법</h3>",
            f"<p>처음에는 {focus_a}에 시간을 두고, 중간에는 {focus_b}를 정리하며, 마무리에는 {focus_c}를 확인하는 방식이 안정적입니다. 이 흐름은 학생의 학년과 시험 일정에 따라 조금씩 조정할 수 있습니다.</p>",
        ]
    if pattern == "실제 수업형":
        return [
            f"<h2>실제 학습 장면에서 보는 {title}</h2>",
            f"<p>실제 학습에서는 학생이 어떤 질문을 하는지가 중요합니다. {region}에서 {subject} 정보를 살펴보는 과정에서도 문제 풀이 결과뿐 아니라 질문의 질, 설명의 순서, 복습 기록을 함께 보는 것이 좋습니다.</p>",
            "<h3>수업 흐름을 평가하는 질문</h3>",
            "<ul><li>개념 설명 뒤 바로 적용 문제가 이어지는가</li><li>학생이 자신의 풀이를 말로 설명하는가</li><li>오답을 다음 학습에서 다시 확인하는가</li><li>숙제량이 학생의 생활 리듬과 맞는가</li></ul>",
        ]
    if pattern == "학습 변화형":
        return [
            f"<h2>{region} 학생의 학습 변화 만들기</h2>",
            f"<p>학습 변화는 갑자기 나타나기보다 작은 루틴이 쌓이면서 드러납니다. {title} 정보를 확인할 때는 현재 부족한 부분만 보지 말고 앞으로 어떤 방식으로 개선할 수 있는지 함께 생각해 보는 것이 좋습니다.</p>",
            "<h3>변화를 확인하는 신호</h3>",
            "<ul><li>틀린 문제를 다시 보는 시간이 짧아진다</li><li>문제를 읽을 때 조건 표시가 늘어난다</li><li>풀이 과정을 건너뛰지 않는다</li><li>시험 전 불안보다 준비 목록이 먼저 보인다</li></ul>",
        ]
    return [
        f"<h2>{title} 확인 체크리스트</h2>",
        f"<p>{title}를 살펴보는 목적은 정보를 많이 보는 데서 끝나지 않습니다. 학생에게 필요한 항목을 골라 실제 학습 계획으로 옮길 수 있는가가 더 중요합니다.</p>",
        "<h3>확인할 항목</h3>",
        f"<ul><li>{focus_a}를 충분히 점검했는가</li><li>{focus_b}를 기록하는 방식이 있는가</li><li>{focus_c}를 시험 전까지 반복할 수 있는가</li><li>학생이 스스로 이해한 부분과 어려운 부분을 구분하는가</li></ul>",
    ]


def make_content(page):
    seed = seed_for(page)
    pattern = PATTERNS[seed % len(PATTERNS)]
    title, region, subject = page_context(page)
    focus_a = pick(FOCUSES, seed, 1)
    focus_b = pick(FOCUSES, seed, 3)
    focus_c = pick(FOCUSES, seed, 5)
    opening = pick(OPENINGS, seed, 2)
    intro = [
        f"<p>{opening} {title} 페이지는 {region}을 기준으로 {subject} 정보를 찾는 사용자가 학습 환경, 과목 특성, 학년별 준비 흐름을 차분히 살펴볼 수 있도록 구성했습니다. 단순히 키워드만 나열하기보다 학생이 실제로 공부하는 장면을 떠올리며 필요한 정보를 정리하는 데 초점을 둡니다.</p>",
        f"<p>{region}에서 {subject} 정보를 살펴볼 때는 학교 진도, 과제량, 시험 일정, 이동 시간 같은 현실적인 조건을 함께 보는 것이 좋습니다. 학생마다 출발점이 다르기 때문에 한 가지 방식으로 판단하기보다 현재의 이해도와 생활 패턴을 기준으로 학습 방향을 정리해야 합니다.</p>",
        f"<p>특히 {focus_a}, {focus_b}, {focus_c}는 {title} 정보를 확인할 때 자주 함께 고려되는 요소입니다. 이 세 가지를 분리해서 보기보다 서로 연결된 흐름으로 살피면 학습 계획이 더 안정적으로 잡힙니다.</p>",
    ]
    mid = pattern_blocks(pattern, title, region, subject, focus_a, focus_b, focus_c)
    order = seed % 4
    if order == 1:
        body = [intro[0], mid[0], mid[1], intro[1], *mid[2:], intro[2]]
    elif order == 2:
        body = [mid[0], intro[0], mid[1], intro[1], *mid[2:], intro[2]]
    elif order == 3:
        body = [intro[0], intro[1], mid[0], mid[1], *mid[2:], intro[2]]
    else:
        body = [intro[0], *mid, intro[1], intro[2]]
    body.extend(
        [
            f"<h2>{title} 정보를 활용하는 방법</h2>",
            f"<p>페이지에 연결된 주변 지역, 과목, 학년 정보를 함께 살펴보면 {region} 안에서 {subject} 학습을 어떻게 바라볼지 더 분명해집니다. 한 페이지에서 끝내기보다 관련 정보를 비교하며 학생에게 맞는 기준을 정리해 보세요.</p>",
            "<h3>마무리 점검</h3>",
            f"<p>{title}의 핵심은 학생의 현재 상태를 차분히 확인하고 무리하지 않는 순서로 학습을 이어 가는 데 있습니다. 지역명이나 과목명을 반복해서 외우는 것보다 실제 공부 장면에서 필요한 자료와 질문을 정리하는 것이 더 중요합니다.</p>",
        ]
    )
    faq = "\n".join(
        [
            "<h2>FAQ</h2>",
            f"<p>Q. {title} 정보를 볼 때 가장 먼저 확인할 점은 무엇인가요?</p>",
            "<p>A. 학생의 현재 이해도, 학교 진도, 가정에서 확보할 수 있는 학습 시간을 함께 보는 것이 좋습니다.</p>",
            f"<p>Q. {region} 지역 정보는 어떻게 활용하면 좋나요?</p>",
            "<p>A. 주변 지역과 학년별 정보를 비교해 학생에게 맞는 학습 조건을 정리하는 데 활용할 수 있습니다.</p>",
            f"<p>Q. {subject} 학습에서 가장 중요한 습관은 무엇인가요?</p>",
            "<p>A. 배운 내용을 짧게 복습하고, 틀린 이유를 기록하며, 다음 학습에 다시 반영하는 습관입니다.</p>",
        ]
    )
    return "\n".join(body), faq, pattern


def project_output_path(url: str) -> Path:
    parts = [part for part in url.strip("/").split("/") if part]
    if parts and "." in parts[-1]:
        target = ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    target = ROOT.joinpath(*parts)
    target.mkdir(parents=True, exist_ok=True)
    return target / "index.html"


def main() -> None:
    roots, regions = read_regions()
    content_by_slug = load_content(CONTENT_SOURCE)
    pages = attach_content(build_pages(roots, regions, set(content_by_slug)), content_by_slug=content_by_slug)
    missing = [page for page in pages if not (page.content or "").strip()]
    patterns_used = []
    for page in missing:
        content, faq, pattern = make_content(page)
        patterns_used.append(pattern)
        filled = replace(page, content=content, faq=faq)
        html = render_page(filled)
        output_path(filled.url).write_text(html, encoding="utf-8", newline="\n")
        project_output_path(filled.url).write_text(html, encoding="utf-8", newline="\n")
    summary = {
        "missing_before": len(missing),
        "generated": len(missing),
        "not_generated": 0,
        "patterns_used": sorted(set(patterns_used)),
    }
    Path("reports/missing_content_fill_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
