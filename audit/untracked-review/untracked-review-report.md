# Untracked File Review

## Summary
- Git status untracked entries reviewed: 92
- Expanded untracked file paths captured before review: 12126
- Total size bytes across reviewed entries/directories: 477507071
- COMMIT_REUSABLE: 14
- KEEP_LOCAL_IGNORE: 4
- DELETE_CANDIDATE: 22
- NEEDS_REVIEW: 52

## Folder Counts
- audit: 44
- reports: 35
- DEPLOYMENT_CHECKS.md: 1
- cloudflare_build.py: 1
- deploy_guard.py: 1
- deployment_complete_report.md: 1
- favicon_fix_report.md: 1
- favicon_validation_report.md: 1
- final_platform_report.md: 1
- package.json: 1
- post_deploy_check.py: 1
- pre_deploy_check.py: 1
- scripts: 1
- seo_audit: 1
- verification: 1

## File Type Counts
- .csv: 31
- .png: 22
- .md: 12
- .py: 8
- .txt: 7
- directory: 6
- .json: 4
- .html: 1
- .xml: 1

## Sensitive Pattern Review
- Suspect entries: 4
- Secret values were not printed; CSV contains file names and pattern types only.

## Duplicate Review
- Duplicate groups among individual top-level files: 3
- Duplicate file entries: 6

## Script Review
- Script/helper entries reviewed: 10
- Entries with risky command patterns: 1

## COMMIT_REUSABLE
- `DEPLOYMENT_CHECKS.md`: human-readable final/operational report candidate
- `audit/final-root-cause-ranking.md`: human-readable final/operational report candidate
- `cloudflare_build.py`: reusable helper script candidate
- `deploy_guard.py`: reusable helper script candidate
- `deployment_complete_report.md`: human-readable final/operational report candidate
- `favicon_fix_report.md`: human-readable final/operational report candidate
- `favicon_validation_report.md`: human-readable final/operational report candidate
- `final_platform_report.md`: human-readable final/operational report candidate
- `post_deploy_check.py`: reusable helper script candidate
- `pre_deploy_check.py`: reusable helper script candidate
- `reports/build_naver_seo_fix_report.py`: reusable helper script candidate
- `reports/check_naver_seo_urls.py`: reusable helper script candidate
- `reports/fix_naver_seo_pages.py`: reusable helper script candidate
- `reports/naver_seo_fix_report.md`: human-readable final/operational report candidate

## KEEP_LOCAL_IGNORE
- `audit/regeneration-test-output`: temporary generated/backup artifact; preserve locally or ignore
- `audit/unstaged-review-backup`: temporary generated/backup artifact; preserve locally or ignore
- `reports/favicon-live-check`: local/generated verification artifact
- `verification`: local/generated verification artifact

## DELETE_CANDIDATE
- `reports/studyhub-final-qa-browser.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-fixed-images-browser-cdp.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-fixed-images-browser-full.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-fixed-images-vertical-complete.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-fixed-images-vertical-final.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-fixed-images-vertical.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-home-live-redesign-fresh.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-home-live-redesign.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-home-redesign-final.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-home-redesign-full.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-home-redesign.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-live-jeju.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-live-main.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-main-deployed-final.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-body-2.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-body-crop.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-body.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-content-crop.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-full-9000.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju-full.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-jeju.png`: reproducible screenshot candidate; not deleted
- `reports/studyhub-restored-main.png`: reproducible screenshot candidate; not deleted

## NEEDS_REVIEW
- `audit/all-html-audit.csv`: purpose unclear or intermediate artifact
- `audit/all-internal-links.csv`: purpose unclear or intermediate artifact
- `audit/breadcrumb-child-counts.csv`: purpose unclear or intermediate artifact
- `audit/broken-internal-links.csv`: purpose unclear or intermediate artifact
- `audit/canonical-conflicts.csv`: purpose unclear or intermediate artifact
- `audit/commands-used-final.txt`: purpose unclear or intermediate artifact
- `audit/commands-used.txt`: purpose unclear or intermediate artifact
- `audit/confirmed-html-fixes.csv`: purpose unclear or intermediate artifact
- `audit/crawl-depth.csv`: purpose unclear or intermediate artifact
- `audit/domain-string-inventory.txt`: purpose unclear or intermediate artifact
- `audit/duplicate-exact.csv`: purpose unclear or intermediate artifact
- `audit/duplicate-page-report.csv`: purpose unclear or intermediate artifact
- `audit/duplicate-similar.csv`: purpose unclear or intermediate artifact
- `audit/final-full-site-audit.md`: possible sensitive pattern; do not stage before manual inspection
- `audit/full-site-audit.md`: purpose unclear or intermediate artifact
- `audit/full_scan.py`: possible sensitive pattern; do not stage before manual inspection
- `audit/git-change-analysis.md`: purpose unclear or intermediate artifact
- `audit/h1-candidates.csv`: purpose unclear or intermediate artifact
- `audit/html-audit.csv`: purpose unclear or intermediate artifact
- `audit/http-domain-matrix.csv`: purpose unclear or intermediate artifact
- `audit/indexability-audit.csv`: purpose unclear or intermediate artifact
- `audit/internal-link-errors.csv`: purpose unclear or intermediate artifact
- `audit/jsonld-errors.csv`: purpose unclear or intermediate artifact
- `audit/live-home.html`: purpose unclear or intermediate artifact
- `audit/live-local-comparison.csv`: purpose unclear or intermediate artifact
- `audit/live-local-comparison.md`: purpose unclear or intermediate artifact
- `audit/live-sitemap.xml`: purpose unclear or intermediate artifact
- `audit/orphan-classification.csv`: purpose unclear or intermediate artifact
- `audit/orphan-pages.csv`: purpose unclear or intermediate artifact
- `audit/sample-link-hotfix.csv`: purpose unclear or intermediate artifact
- `audit/sample-link-verification.csv`: purpose unclear or intermediate artifact
- `audit/scan-progress.json`: purpose unclear or intermediate artifact
- `audit/sitemap-audit.csv`: purpose unclear or intermediate artifact
- `audit/sitemap-full-audit.csv`: purpose unclear or intermediate artifact
- `audit/sitemap-live-status.csv`: purpose unclear or intermediate artifact
- `audit/structured-data-errors.csv`: purpose unclear or intermediate artifact
- `audit/summary.json`: purpose unclear or intermediate artifact
- `audit/unstaged-change-classification.csv`: purpose unclear or intermediate artifact
- `audit/unstaged-change-review.md`: purpose unclear or intermediate artifact
- `audit/url-normalization.csv`: purpose unclear or intermediate artifact
- `audit/user-agent-comparison.csv`: purpose unclear or intermediate artifact
- `package.json`: tooling manifest can affect build/dependency expectations
- `reports/all_slugs.txt`: purpose unclear or intermediate artifact
- `reports/browser_qa_50_results.json`: purpose unclear or intermediate artifact
- `reports/live_title_check_7_urls.csv`: purpose unclear or intermediate artifact
- `reports/naver_all_collection_urls.txt`: purpose unclear or intermediate artifact
- `reports/naver_collection_urls.txt`: purpose unclear or intermediate artifact
- `reports/naver_seo_after.csv`: purpose unclear or intermediate artifact
- `reports/naver_seo_before.csv`: purpose unclear or intermediate artifact
- `reports/title_duplicate_report.txt`: purpose unclear or intermediate artifact
- `scripts`: possible sensitive pattern; do not stage before manual inspection
- `seo_audit`: possible sensitive pattern; do not stage before manual inspection

## Safety Confirmation
- No untracked files were deleted.
- No files were moved.
- No files were staged or committed by this review.
- No push or deployment was performed.
