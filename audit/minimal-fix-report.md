# StudyHub 최소 수정 적용 보고서

작성일: 2026-07-13

## A. URL 정규화 판단

- 적용 전 문제: `/path/`와 `/path/index.html`이 둘 다 200으로 열릴 수 있어 동일 페이지 중복 URL이 생길 수 있었다.
- 적용 내용: `vercel.json`에 `/index.html` -> `/`, `/:path*/index.html` -> `/:path*/` 영구 리디렉션 규칙만 추가했다.
- 유지한 항목: `trailingSlash: true`, `cleanUrls: false`, 기존 `www.studyhub.co.kr` -> `https://studyhub.co.kr/$1` 영구 리디렉션, headers 설정은 유지했다.
- 적용하지 않은 항목: query string 강제 제거 또는 강제 리디렉션은 하지 않았다.
- 배포 주의: 로컬 설정 파일만 수정했으며 Vercel 배포는 하지 않았으므로 실제 운영 반영은 아직 아니다.

## B. 고아 페이지 원인 분류

- 분류 대상: 이전 로컬 전수조사 기준 고아 페이지 5,398개.
- 주요 유형:
  - `grade_subject_page`: 2,597개
  - `grade_hub`: 1,502개
  - `subject_hub`: 866개
  - `dong_hub`: 369개
  - `sigungu_hub`: 36개
  - `other`: 28개
- 원인 판단:
  - 다수 페이지가 sitemap에는 있으나 홈에서 출발한 내부 링크 그래프에 연결되지 않았다.
  - 전체를 메인에 직접 노출하는 방식은 피해야 하며, 기존 부모 허브에서 하위 샘플 또는 구조 링크를 확장하는 방식이 적합하다.
- 산출물: `audit/orphan-classification.csv`

## C. 내부 링크 샘플 수정 결과

- 적용 범위: 대표 20개 고아 URL만 기존 부모 허브 13개에 샘플 링크로 연결했다.
- 수정 파일 수: `output` HTML 13개.
- 결과:
  - 전체 내부 링크 수: 304,241 -> 304,261
  - 고아 페이지 수: 5,398 -> 4,998
  - 직접 추가한 링크는 20개지만, 연결된 중간 허브를 통해 하위 군집까지 노출되어 고아 페이지가 400개 감소했다.
  - 깨진 내부 링크: 0
- 산출물:
  - `audit/sample-link-hotfix.csv`
  - `audit/sample-link-verification.csv`

## D. H1 및 placeholder 수정 결과

- 적용 범위:
  - 콘텐츠 본문 안의 중복 `<h1>`을 `<h2>`로 낮춤: 37개 output HTML.
  - 숨김 placeholder div 제거: 2개 output HTML.
  - 생성기 소스에도 동일 예방 로직 추가: `sitegen/render.py`
- 검증 결과:
  - `multiple_h1` 오류: 37 -> 0
  - 실제 오류 페이지가 아닌 정상 문장 내 "오류 유형" 표현 1건은 수정하지 않았다.
- 산출물: `audit/confirmed-html-fixes.csv`

## E. 변경 파일 목록

설정/생성기:

- `vercel.json`
- `sitegen/render.py`

조사 및 적용 스크립트/보고서:

- `audit/classify_orphans.py`
- `audit/apply_sample_links.py`
- `audit/fix_confirmed_html_candidates.py`
- `audit/minimal-fix-report.md`

생성된 audit 산출물:

- `audit/orphan-classification.csv`
- `audit/sample-link-hotfix.csv`
- `audit/sample-link-verification.csv`
- `audit/confirmed-html-fixes.csv`
- 재검증 과정에서 기존 audit CSV/JSON 일부가 최신 로컬 결과로 갱신됨.

샘플 내부 링크가 들어간 output 파일:

- `output/서울과외/index.html`
- `output/서울과외/강남구과외/index.html`
- `output/서울과외/송파구과외/index.html`
- `output/서울수학과외/index.html`
- `output/서울영어과외/index.html`
- `output/서울초등과외/index.html`
- `output/서울중등과외/index.html`
- `output/서울고등과외/index.html`
- `output/서울고등수학과외/index.html`
- `output/서울고등영어과외/index.html`
- `output/서울중등수학과외/index.html`
- `output/서울중등영어과외/index.html`
- `output/경기도과외/index.html`

H1/placeholder 최소 수정이 적용된 output 파일 목록은 `audit/confirmed-html-fixes.csv`에 기록했다.

## F. 로컬 검증 결과

- 로컬 HTML 전체: 9,612개
- sitemap URL: 9,612개
- sitemap 중복 loc: 0
- sitemap에는 있으나 로컬 파일이 없는 URL: 0
- 로컬에는 있으나 sitemap에 없는 페이지: 0
- canonical 충돌: 0
- noindex: 0
- JSON-LD 오류: 0
- 깨진 내부 링크: 0
- 고아 페이지: 4,998개
- depth 5 이상 페이지: 1,844개

주의:

- `audit/full_scan.py --local`은 10분 제한으로 프로세스 종료 코드를 받기 전에 타임아웃되었지만, `audit/scan-progress.json` 기준 로컬 HTML 9,612개 처리는 완료되었다.
- 운영 배포는 하지 않았으므로 live 사이트의 `/index.html` 리디렉션 개선과 샘플 링크 개선은 아직 반영되지 않았다.

## G. 전체 적용 계획

1. 이번처럼 부모 허브에 샘플 링크만 추가하는 방식은 효과가 확인되었지만, 전체 5,398개를 메인에 직접 연결하면 안 된다.
2. 다음 단계는 `sitegen/pages.py` 또는 관련 허브 생성 로직에서 부모-자식 관계를 구조적으로 반영하는 것이다.
3. 특히 시도 허브 -> 시군구 허브 -> 동 허브 -> 과목/학년 허브 흐름을 생성기에서 일관되게 만들어야 한다.
4. 전체 재생성 전에도 선택된 부모 허브만 부분 갱신하는 방식이 가능하다.
5. 단, 생성기 로직을 고친 뒤 전체 사이트의 내부 링크 구조를 완전히 일관화하려면 최종적으로는 계획된 재생성 검증이 필요할 수 있다.

## H. 하지 않은 작업

- 전체 output 재생성 안 함.
- output 전체 삭제 안 함.
- 5,398개 고아 페이지를 메인에 직접 링크하지 않음.
- query string 강제 리디렉션 추가 안 함.
- canonical, sitemap, robots, 대표 도메인 설정 변경 안 함.
- 커밋 안 함.
- push 안 함.
- Vercel 배포 안 함.

URL 정규화와 내부 링크 구조의 샘플 수정 및 로컬 검증만 완료했으며 전체 재생성, 커밋, push, Vercel 배포는 진행하지 않았습니다.
