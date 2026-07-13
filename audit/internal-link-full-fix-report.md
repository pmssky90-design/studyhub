# StudyHub 내부 링크 전체 보강 보고서

작성일: 2026-07-13

## A. 한 줄 결론

breadcrumb 기반의 실제 부모-자식 계층을 현재 `output`에 확장 적용하여 sitemap 정상 URL 9,612개가 모두 홈 기준 내부 링크로 도달 가능해졌다.

## B. 수정 전후 비교

| 항목 | 수정 전 | 샘플 수정 후 | 전체 보강 후 |
|---|---:|---:|---:|
| 전체 HTML | 9,612 | 9,612 | 9,612 |
| 고아 페이지 | 5,398 | 4,998 | 0 |
| 도달 가능 페이지 | 4,214 | 4,614 | 9,612 |
| 최대 crawl depth | 7 | 7 | 5 |
| 깨진 내부 링크 | 0 | 0 | 0 |
| canonical 충돌 | 0 | 0 | 0 |
| noindex | 0 | 0 | 0 |
| JSON-LD 오류 | 0 | 0 | 0 |

전체 보강 후 depth 분포:

| depth | 페이지 수 |
|---:|---:|
| 0 | 1 |
| 1 | 36 |
| 2 | 306 |
| 3 | 1,612 |
| 4 | 4,124 |
| 5 | 3,533 |

## C. 수정한 생성기 파일

- `sitegen/render.py`
  - 관련 링크 섹션 출력 제한을 기존 5개에서 `MAX_RELATED_LINKS_PER_SECTION = 60`으로 확장했다.
  - 부모별 직접 자식 수 최대가 44개로 확인되어, 사용자가 지정한 20~60개 범위 안에서 전체 하위 링크를 노출할 수 있다.
  - 기존 canonical, sitemap, robots, 대표 도메인 설정은 변경하지 않았다.

## D. 수정한 output 파일 수

- 이번 전체 보강으로 수정한 output HTML: 732개
- 기존 샘플 링크와 H1/placeholder 최소 수정은 유지했다.
- 변경 목록: `audit/changed-output-files.csv`

## E. 추가한 내부 링크 수

- 이번 전체 보강에서 추가한 내부 링크: 3,481개
- 추가 링크는 모두 현재 `output`에 실제 존재하는 URL만 사용했다.
- 추가 링크 중 자기 자신 링크: 0개
- 추가 링크 중 동일 source-target 중복: 0개
- 추가 링크 목록: `audit/internal-links-added.csv`

## F. 페이지 유형별 고아 페이지 감소 결과

| 페이지 유형 | 수정 전 고아 | 수정 후 고아 | 감소 |
|---|---:|---:|---:|
| grade_subject_page | 2,597 | 0 | 2,597 |
| grade_hub | 1,502 | 0 | 1,502 |
| subject_hub | 866 | 0 | 866 |
| dong_hub | 369 | 0 | 369 |
| sigungu_hub | 36 | 0 | 36 |
| other | 28 | 0 | 28 |
| 합계 | 5,398 | 0 | 5,398 |

after 산출물:

- `audit/orphan-pages-after.csv`
- `audit/orphan-classification-after.csv`
- `audit/crawl-depth-after.csv`
- `audit/unresolved-pages.csv`

## G. URL 정규화 검사 결과

검사 파일: `audit/url-normalization-after.csv`

| 변형 | 운영 응답 | 판단 |
|---|---|---|
| `/` | 200 | 정상 |
| `/index.html` | 200 | 운영에는 아직 redirect 미반영 |
| `/서울과외/` | 200 | 정상 대표 URL |
| `/서울과외` | 308 -> 200 | trailing slash 정규화 정상 |
| `/서울과외/index.html` | 200 | 운영에는 아직 redirect 미반영 |
| `//서울과외//` | 308 -> 200 | double slash 정규화 정상 |
| `/서울과외/?test=1` | 200 | query string 유지 |
| `/서울과외/index.html?test=1` | 200 | query string 유지, 운영 redirect 미반영 |

주의:

- 로컬 `vercel.json`에는 `/index.html`과 `/:path*/index.html`을 대표 슬래시 URL로 보내는 영구 redirect 규칙이 이미 있다.
- 커밋, push, Vercel 배포를 하지 않았기 때문에 운영 사이트에서는 아직 `/index.html` 변형이 200으로 남아 있다.
- query string은 요청대로 강제 제거하지 않았다.

## H. 남은 미해결 페이지와 사유

- 미해결 고아 페이지: 0개
- unresolved 목록: `audit/unresolved-pages.csv`
- 정적 검증 기준으로 sitemap URL 9,612개는 모두 내부 링크 그래프에서 도달 가능하다.

## I. 하지 않은 작업

- output 전체 삭제: 하지 않음
- 전체 재생성: 하지 않음
- canonical 변경: 하지 않음
- sitemap 구조 임의 변경: 하지 않음
- robots.txt 변경: 하지 않음
- 대표 도메인 변경: 하지 않음
- 메인 페이지에 수천 개 링크 직접 추가: 하지 않음
- query string 강제 리디렉션: 하지 않음
- 커밋: 하지 않음
- push: 하지 않음
- Vercel 배포: 하지 않음

## 산출물

- `audit/internal-link-full-fix-report.md`
- `audit/orphan-pages-after.csv`
- `audit/orphan-classification-after.csv`
- `audit/crawl-depth-after.csv`
- `audit/internal-links-added.csv`
- `audit/url-normalization-after.csv`
- `audit/unresolved-pages.csv`
- `audit/changed-output-files.csv`

수정과 로컬 전체 검증까지만 완료했으며 output 전체 삭제, 전체 재생성, 커밋, push, Vercel 배포는 진행하지 않았습니다.
