# 다시 풀기 후보 표

`tools/rerun_select.py` 가 지었다. main 은 `80ff61f1d831`(`80ff61f1`), 브랜치 표는 `.scratch/model-rerun/probes/branches.json`(SHA-256 앞 12자리 `847604d8400a`), 되살릴 목록은 없다.
조건은 그 모듈의 상수다. 날짜 바닥 2026-10-12T00:00:00+09:00(B 의 커밋 시각), 후보 문턱 12개, 숨은 시험 3개 이상, PR 앞 비용 $70 이하, 원래 브랜치 `feature/`. 바깥 검증 낱말은 `-m llm`, `playwright`, `pnpm -C web visual`, `사진 비교`, `Claude Design`, `사람이 확인`(대소문자를 가리지 않는다)과 파일 이름의 `human-verification`이다.
행은 M 이 늦은 차례다. 자리의 `거슬러 채움`은 남은 후보가 모자라 B 가 날짜 바닥 앞인 후보를 늦은 것부터 더해 본 행이고, `닿지 않음`은 채운 뒤라 보지 않은 행이다. 빠진 노드는 숨은 시험 가르기(`tools/rerun_hidden.py`)가 뺀 노드를 조건과 까닭으로 묶어 센 것이다.

| 과제 id | PR | B | M | B 시각 | 원래 브랜치 | 자리 | 남음 | 빠진 까닭 | 바깥 검증 낱말 | PR 앞 비용 | 크기 | 숨은 시험 | 빠진 노드 | B 의 `web/package.json` | B 의 `tools/run_checks.py` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model-rerun-10 | #380 | f1ed4be7 | 80ff61f1 | 2026-10-24T13:47+09:00 | feature/10-schedule-and-budget | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(사람이 확인) | 사람이 확인 | $30.05 | 27 | — | — | 있음 | 있음 |
| web-widget-04 | #379 | 7496a830 | f1ed4be7 | 2026-10-24T02:26+09:00 | feature/04-site-file-feeds-widget-build | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $61.85 | 5 | — | — | 있음 | 있음 |
| model-rerun-09 | #377 | eec99a51 | 7496a830 | 2026-10-24T01:53+09:00 | feature/09-not-measured-checks | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $55.83 | 20 | 0 | 조건 2 결과 없음(모음 실패) ×222; 조건 2 TypeError ×1; 조건 2 통과 ×1 | 있음 | 있음 |
| web-widget-02 | #378 | 51a0417e | eec99a51 | 2026-10-24T00:36+09:00 | feature/02-runtime-relays-call-events-live | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $27.30 | 16 | — | — | 있음 | 있음 |
| web-widget-03 | #376 | 96d3e1df | 51a0417e | 2026-10-23T23:51+09:00 | feature/03-widget-app-skeleton | 날짜 안 | 빠짐 | PR 앞 비용 $73.22 가 $70 를 넘는다; 바깥 검증 낱말에 걸렸다(pnpm -C web visual, 사진 비교) | pnpm -C web visual, 사진 비교 | $73.22 | 6 | — | — | 있음 | 있음 |
| web-widget-01 | #375 | 07c890c5 | 96d3e1df | 2026-10-23T22:11+09:00 | feature/01-contract-calling-item-and-limit-kind | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $65.49 | 11 | — | — | 있음 | 있음 |
| model-rerun-08 | #374 | 15e7b59b | 07c890c5 | 2026-10-23T21:42+09:00 | feature/08-continue-and-caps | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $57.55 | 10 | 0 | 조건 2 결과 없음(모음 실패) ×63; 조건 2 AttributeError ×1 | 있음 | 있음 |
| model-rerun-07 | #372 | 062e9734 | 15e7b59b | 2026-10-23T20:01+09:00 | feature/07-gates-and-official-cost | 날짜 안 | 빠짐 | PR 앞 비용 $82.99 가 $70 를 넘는다 | — | $82.99 | 11 | — | — | 있음 | 있음 |
| model-rerun-05 | #371 | 8a026f3c | 062e9734 | 2026-10-23T19:31+09:00 | feature/05-task-selection | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm, playwright, pnpm -C web visual, 사진 비교, Claude Design, 사람이 확인) | -m llm, playwright, pnpm -C web visual, 사진 비교, Claude Design, 사람이 확인 | $52.53 | 13 | — | — | 있음 | 있음 |
| model-rerun-06 | #370 | db92d68a | 893e0fe8 | 2026-10-23T13:35+09:00 | feature/06-round-drive-record | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $19.12 | 15 | 0 | 조건 2 결과 없음(모음 실패) ×46 | 있음 | 있음 |
| model-rerun-04 | #369 | 934f8dfa | c2c03eae | 2026-10-23T12:18+09:00 | feature/04-round-clone | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $1.44 | 9 | 0 | 조건 2 결과 없음(모음 실패) ×81 | 있음 | 있음 |
| model-rerun-03 | #364 | 750761b9 | 9b4952f6 | 2026-10-23T10:35+09:00 | feature/03-rerun-judge | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $0.35 | 7 | 0 | 조건 2 결과 없음(모음 실패) ×55 | 있음 | 있음 |
| model-rerun-02 | #363 | d0e696c9 | c3c2cfcf | 2026-10-23T06:15+09:00 | feature/02-hidden-test-filter | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $0.31 | 7 | 0 | 조건 2 결과 없음(모음 실패) ×98; 조건 3 문자열 '번호(따옴표 없이' ×1 | 있음 | 있음 |
| model-rerun-01 | #361 | 04ea401d | d0e696c9 | 2026-10-23T05:28+09:00 | feature/01-rerun-file-shapes | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $0.24 | 4 | 0 | 조건 2 결과 없음(모음 실패) ×131 | 있음 | 있음 |
| ticket-for-every-pr-04 | #355 | 9999e83e | 975bf04c | 2026-10-23T01:47+09:00 | feature/04-ci-checks-ticket-done | 날짜 안 | 빠짐 | 숨은 시험이 1개라 3개보다 적다 | — | $0.25 | 9 | 1 | 조건 2 통과 ×1; 조건 3 이름 '_CI가_막았다' ×12; 조건 3 이름 '_CI가_지났다' ×6; 조건 3 이름 '_CI로_친다' ×4; 조건 3 이름 'PR값' ×2 | 있음 | 있음 |
| ticket-for-every-pr-05 | #354 | 19bbfa06 | ebaed667 | 2026-10-22T23:44+09:00 | feature/05-first-turn-ticket-notice | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $1.85 | 17 | 0 | 조건 2 결과 없음(모음 실패) ×13 | 있음 | 있음 |
| design-reverse-sync-01 | #353 | b104f8fa | 19bbfa06 | 2026-10-22T22:32+09:00 | feature/01-contrast-module | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(pnpm -C web visual, 사진 비교) | pnpm -C web visual, 사진 비교 | $0.18 | 10 | — | — | 있음 | 있음 |
| ticket-for-every-pr-03 | #350 | 96fbe241 | e62eb052 | 2026-10-22T19:30+09:00 | feature/03-commit-check-blocks-ticketless | 날짜 안 | 남음 | — | — | $0.19 | 20 | 3 | 조건 3 이름 '_막혔다' ×24; 조건 3 이름 '_지났다' ×16 | 있음 | 있음 |
| ticket-for-every-pr-02 | #348 | b2f5c61d | 8f8c54f8 | 2026-10-22T17:06+09:00 | feature/02-docs-and-skills-teach-tickets | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $2.30 | 19 | 0 | — | 있음 | 있음 |
| ticket-for-every-pr-01 | #345 | 98272c4f | caaa062b | 2026-10-22T14:39+09:00 | feature/01-harness-ticket-numbers | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $42.15 | 4 | 0 | 조건 2 결과 없음(모음 실패) ×39; 조건 2 통과 ×3 | 있음 | 있음 |
| ticket-for-every-pr-06 | #343 | 6bd52b06 | 82ba6866 | 2026-10-22T12:54+09:00 | feature/06-hook-blocks-own-cards | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $23.84 | 15 | 0 | 조건 2 결과 없음(모음 실패) ×12 | 있음 | 있음 |
| ticket-for-every-pr-07 | #342 | c1e05e96 | 6bd52b06 | 2026-10-22T12:46+09:00 | feature/07-morning-report-harness-branches | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $11.87 | 7 | 0 | 조건 2 결과 없음(모음 실패) ×1 | 있음 | 있음 |
| mcp-shutdown-03 | #338 | 14efe41d | c1e05e96 | 2026-10-21T21:53+09:00 | feature/03-posix-launcher | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $5.33 | 16 | — | — | 있음 | 있음 |
| mcp-shutdown-02 | #340 | 303e8fb5 | f1e6516b | 2026-10-21T20:19+09:00 | feature/02-boundary-exceptions | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $19.99 | 7 | — | — | 있음 | 있음 |
| mcp-shutdown-01 | #337 | c2c2105f | 5040230c | 2026-10-21T16:15+09:00 | feature/01-mcp-2-and-cli-interrupt | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $56.97 | 20 | — | — | 있음 | 있음 |
| end-user-continuation-02 | #325 | 5fee4cd6 | 77ecd319 | 2026-10-20T17:50+09:00 | feature/02-runtime-names-the-failure-cause | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $38.02 | 3 | — | — | 있음 | 있음 |
| end-user-continuation-04 | #323 | b78317fe | 0262841b | 2026-10-20T17:13+09:00 | feature/04-exchange-count-read-cap-and-thread | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $52.67 | 12 | — | — | 있음 | 있음 |
| end-user-continuation-05 | #321 | 0a6e0b0d | ed111753 | 2026-10-20T15:26+09:00 | feature/05-only-pre-owner-damage-is-404 | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $67.33 | 8 | — | — | 있음 | 있음 |
| end-user-continuation-06 | #319 | e70d6722 | 2d460f6b | 2026-10-20T13:06+09:00 | feature/06-admin-shows-cause-and-shortcut-links | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교) | 사진 비교 | $26.61 | 4 | — | — | 있음 | 있음 |
| end-user-continuation-03 | #318 | 9e92ec72 | e70d6722 | 2026-10-20T12:48+09:00 | feature/03-shortcuts-walk-only-that-agent | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $24.21 | 4 | — | — | 있음 | 있음 |
| token-usage-09 | #299 | a89ec15c | a0c79b61 | 2026-10-19T13:31+09:00 | feature/09-human-verification-close | 날짜 안 | 빠짐 | 파일 이름에 human-verification 가 든다 | — | $29.37 | 7 | — | — | 있음 | 있음 |
| token-usage-08 | #282 | df1238cf | d0f5bdef | 2026-10-16T20:59+09:00 | feature/08-apply-outside-settings | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(playwright) | playwright | $8.81 | 3 | — | — | 있음 | 있음 |
| token-usage-03 | #280 | 17e80b32 | a751d589 | 2026-10-16T18:29+09:00 | feature/03-remaining-metrics-and-weekly-reports | 날짜 안 | 빠짐 | PR 앞 비용 $84.80 가 $70 를 넘는다 | — | $84.80 | 10 | — | — | 있음 | 있음 |
| token-usage-06 | #278 | 5437432a | 424f119c | 2026-10-16T17:52+09:00 | feature/06-large-result-hook | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $26.36 | 9 | 0 | 조건 2 결과 없음(모음 실패) ×24 | 있음 | 있음 |
| token-usage-04 | #277 | 42820083 | 5437432a | 2026-10-16T16:55+09:00 | feature/04-session-start-hook | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $49.54 | 17 | 0 | 조건 2 결과 없음(모음 실패) ×38 | 있음 | 있음 |
| token-usage-05 | #276 | 89b560de | 42820083 | 2026-10-16T15:51+09:00 | feature/05-handoff-hooks-and-sentences | 날짜 안 | 빠짐 | 숨은 시험이 1개라 3개보다 적다 | — | $37.20 | 18 | 1 | 조건 2 결과 없음(모음 실패) ×45 | 있음 | 있음 |
| end-user-continuation-01 | #274 | c689c9ce | 89b560de | 2026-10-16T15:01+09:00 | feature/01-contract-end-user-continuation-and-cause-slots | 날짜 안 | 빠짐 | PR 앞 비용 $75.04 가 $70 를 넘는다; 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $75.04 | 20 | — | — | 있음 | 있음 |
| token-usage-07 | #273 | 9be7bdeb | a0890053 | 2026-10-16T14:28+09:00 | — | 날짜 안 | 빠짐 | 원래 브랜치 chore/token-usage-07-status 가 feature/ 로 시작하지 않는다 | — | — | 7 | — | — | 있음 | 있음 |
| token-usage-02 | #270 | 74fd4375 | feb64be1 | 2026-10-16T14:03+09:00 | feature/02-ledger-and-daily-report | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $21.25 | 13 | 0 | 조건 2 결과 없음(모음 실패) ×44 | 있음 | 있음 |
| token-usage-01 | #271 | d71d8c96 | e52e8da3 | 2026-10-16T12:24+09:00 | feature/01-runner-notice-expectation | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $20.68 | 7 | 0 | 조건 2 통과 ×4; 조건 2 TypeError ×3; 조건 3 문자열 'hook_notice_and_silent.py' ×1 | 있음 | 있음 |
| kickoff-auto-flow-04 | #236 | e445a3dc | 5f72cdbb | 2026-10-13T22:59+09:00 | feature/04-human-verification-of-runner | 날짜 안 | 빠짐 | 파일 이름에 human-verification 가 든다 | — | $15.17 | 7 | — | — | 있음 | 있음 |
| design-refresh-05 | #234 | 55ba299c | e7ca8193 | 2026-10-13T22:05+09:00 | feature/05-claude-design-upload | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교, Claude Design) | 사진 비교, Claude Design | $28.37 | 15 | — | — | 있음 | 있음 |
| design-refresh-04 | #221 | 2d593dd7 | 25fe55e1 | 2026-10-13T20:13+09:00 | feature/04-density-and-common-sizes | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교) | 사진 비교 | $48.82 | 9 | — | — | 있음 | 있음 |
| kickoff-auto-flow-03 | #218 | 8871a15e | e6eb8dfe | 2026-10-13T19:19+09:00 | feature/03-runner-and-templates | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $26.40 | 12 | 0 | — | 있음 | 있음 |
| design-refresh-03 | #216 | cd4f92d7 | 628a0f65 | 2026-10-13T12:23+09:00 | feature/03-four-themes-and-colors | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교) | 사진 비교 | $61.07 | 13 | — | — | 있음 | 있음 |
| kickoff-auto-flow-02 | #214 | c342d150 | cd4f92d7 | 2026-10-13T11:11+09:00 | feature/02-human-share-lines-and-prep-section | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $35.96 | 16 | 0 | 조건 2 결과 없음(모음 실패) ×41 | 있음 | 있음 |
| design-refresh-02 | #205 | 84893a87 | 3e9e5442 | 2026-10-13T09:33+09:00 | feature/02-icon-stroke-and-removed-props | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(pnpm -C web visual, 사진 비교) | pnpm -C web visual, 사진 비교 | $31.75 | 10 | — | — | 있음 | 있음 |
| kickoff-auto-flow-01 | #210 | 132da916 | 84893a87 | 2026-10-13T09:01+09:00 | feature/01-main-commit-hook-allows-first-commit | 날짜 안 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $26.29 | 8 | 0 | 조건 2 결과 없음(모음 실패) ×8; 조건 3 문자열 'EMPTY_MAIN_REPO' ×1 | 있음 | 있음 |
| design-refresh-01 | #204 | 80445cff | a33d681c | 2026-10-12T23:51+09:00 | feature/01-noto-sans-mono | 날짜 안 | 빠짐 | 바깥 검증 낱말에 걸렸다(pnpm -C web visual, 사진 비교) | pnpm -C web visual, 사진 비교 | $21.73 | 12 | — | — | 있음 | 있음 |
| design-system-03 | #166 | f71e5772 | 58969f7e | 2026-10-07T22:07+09:00 | feature/03-status-badge-progress-card | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교) | 사진 비교 | $15.12 | 4 | — | — | 있음 | 있음 |
| design-system-04 | #165 | 61884df3 | 5c069d43 | 2026-10-07T16:51+09:00 | feature/04-text-field-switch-alert | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(사진 비교) | 사진 비교 | $3.85 | 4 | — | — | 있음 | 있음 |
| design-system-02 | #158 | 4319c0e6 | 49d9630c | 2026-10-07T13:31+09:00 | feature/02-visual-comparison-gate | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(playwright, 사진 비교) | playwright, 사진 비교 | $36.42 | 21 | — | — | 있음 | 있음 |
| design-system-01 | #156 | cbb6a6c8 | 162ae54e | 2026-10-07T09:10+09:00 | feature/01-tokens-story-seam-and-buttons | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(playwright, 사진 비교) | playwright, 사진 비교 | $53.25 | 25 | — | — | 있음 | 없음 |
| end-user-channel-02 | #151 | 88badb18 | e7e17d81 | 2026-10-06T17:18+09:00 | feature/02-limits-and-backlog | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $51.12 | 12 | — | — | 있음 | 없음 |
| end-user-channel-05 | #146 | 9b31a2b2 | ef3f43bc | 2026-10-06T16:45+09:00 | feature/05-admin-hides-decision-for-end-user | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $13.31 | 3 | — | — | 있음 | 없음 |
| end-user-channel-04 | #147 | 8a4274fe | 5a371082 | 2026-10-06T15:42+09:00 | feature/04-cors-on-prefix | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $20.48 | 4 | — | — | 있음 | 없음 |
| end-user-channel-03 | #148 | 1d039759 | 8a4274fe | 2026-10-06T14:43+09:00 | feature/03-run-timeout | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $39.28 | 6 | — | — | 있음 | 없음 |
| end-user-channel-01 | #137 | 821e50db | 8df4d87a | 2026-10-06T13:18+09:00 | feature/01-contract-signed-token-prefix-and-subscription | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $68.53 | 23 | — | — | 있음 | 없음 |
| conversation-04 | #134 | 7bba2b6a | b7d13821 | 2026-10-05T04:11+09:00 | feature/04-admin-links-previous-and-covered | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $15.86 | 2 | — | — | 있음 | 없음 |
| conversation-03 | #133 | b393cac9 | 7bba2b6a | 2026-10-05T01:37+09:00 | feature/03-cli-continue-and-calc-weaves | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $27.02 | 10 | — | — | 있음 | 없음 |
| conversation-02 | #132 | 4112d2b8 | b393cac9 | 2026-10-04T22:47+09:00 | feature/02-runtime-summarizes-over-limit | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $27.57 | 6 | — | — | 있음 | 없음 |
| conversation-01 | #131 | 300b5f03 | 4112d2b8 | 2026-10-04T19:19+09:00 | feature/01-contract-continue-run-and-own-exchanges | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $49.48 | 10 | — | — | 있음 | 없음 |
| web-admin-08 | #106 | bbf58628 | 447c0686 | 2026-09-30T17:03+09:00 | feature/08-channel-token-and-decision | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $39.77 | 19 | 0 | — | 있음 | 없음 |
| web-admin-07 | #105 | ff9c48de | bbf58628 | 2026-09-30T14:20+09:00 | feature/07-runs-list-and-trace | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $29.45 | 9 | 0 | — | 있음 | 없음 |
| web-admin-06 | #104 | 770d26ec | ff9c48de | 2026-09-30T11:44+09:00 | feature/06-plugin-detail-and-toggle | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $25.52 | 9 | 0 | — | 있음 | 없음 |
| web-admin-05 | #103 | c7dff2e3 | 770d26ec | 2026-09-30T09:00+09:00 | feature/05-admin-token-plugin-list-first-e2e | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm, playwright) | -m llm, playwright | $43.48 | 22 | — | — | 있음 | 없음 |
| web-admin-04 | #102 | a7a90a50 | c7dff2e3 | 2026-09-30T00:02+09:00 | feature/04-admin-app-loopback-relay | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $38.43 | 11 | 0 | — | 있음 | 없음 |
| web-admin-03 | #101 | 57727852 | a7a90a50 | 2026-09-29T20:49+09:00 | feature/03-generated-api-client | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $26.70 | 16 | 0 | — | 있음 | 없음 |
| web-admin-01 | #99 | c6a0ca67 | a7602233 | 2026-09-29T14:43+09:00 | feature/01-constitution-harness-web-skeleton | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(playwright) | playwright | $24.91 | 34 | — | — | 없음 | 없음 |
| web-admin-02 | #98 | acb38688 | c6a0ca67 | 2026-09-29T13:07+09:00 | feature/02-contract-decision-names-its-pause | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $23.90 | 16 | — | — | 없음 | 없음 |
| plugin-toggle-02 | #87 | 3a87ac88 | c5417b1a | 2026-09-28T09:59+09:00 | feature/02-runtime-refuses-disabled | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $16.54 | 6 | — | — | 없음 | 없음 |
| plugin-toggle-01 | #85 | 28a46ca6 | 8b136231 | 2026-09-27T13:58+09:00 | feature/01-contract-switch-and-wrapped-rows | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $42.96 | 12 | 0 | 조건 2 결과 없음(모음 실패) ×79 | 없음 | 없음 |
| http-channel-05 | #80 | 38d1692f | 2056e7b2 | 2026-09-26T16:16+09:00 | feature/05-real-serve-pauses-and-approves | 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(-m llm) | -m llm | $10.45 | 2 | — | — | 없음 | 없음 |
| http-channel-04 | #78 | 01b89fad | 3aad4920 | 2026-09-26T08:37+09:00 | feature/04-approval-resumes-over-http | 거슬러 채움 | 남음 | — | — | $21.61 | 1 | 33 | 조건 3 문자열 '#/components/schemas/Approve' ×1; 조건 3 문자열 '#/components/schemas/Decision' ×1 | 없음 | 없음 |
| http-channel-03 | #75 | 42a2d3a6 | 6cf2595d | 2026-09-26T06:37+09:00 | feature/03-start-run-streams-events | 거슬러 채움 | 남음 | — | — | $30.63 | 7 | 6 | 조건 2 TypeError ×34; 조건 2 결과 없음(모음 실패) ×5; 조건 2 통과 ×2 | 없음 | 없음 |
| http-channel-02 | #73 | be757ab6 | 260affd0 | 2026-09-26T03:16+09:00 | feature/02-channel-token | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $10.86 | 0 | 0 | 조건 2 결과 없음(모음 실패) ×14; 조건 2 오류 ×5; 조건 2 TypeError ×3 | 없음 | 없음 |
| http-channel-01 | #70 | edc7ecd8 | ead03573 | 2026-09-25T11:02+09:00 | feature/01-contract-shared-http-layer-and-pre-run-failures | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $21.99 | 15 | 0 | 조건 2 결과 없음(모음 실패) ×20; 조건 2 통과 ×1; 조건 3 문자열 'python -m agent_os.main' ×1 | 없음 | 없음 |
| admin-api-06 | #63 | f9b85e10 | 19bcc2f7 | 2026-09-23T23:38+09:00 | feature/06-trace-detail | 거슬러 채움 | 남음 | — | — | $12.01 | 1 | 9 | 조건 2 AttributeError ×1; 조건 2 통과 ×1; 조건 3 문자열 'TraceEvent' ×3; 조건 3 문자열 '#/components/schemas/TraceEvent' ×1 | 없음 | 없음 |
| admin-api-05 | #56 | 007aa22c | 09cb2981 | 2026-09-23T12:24+09:00 | feature/05-traces-list | 거슬러 채움 | 빠짐 | 숨은 시험이 1개라 3개보다 적다 | — | $14.74 | 1 | 1 | 조건 2 결과 없음(모음 실패) ×26; 조건 2 통과 ×4 | 없음 | 없음 |
| admin-api-04 | #51 | 526ad97b | 6442f95d | 2026-09-23T11:39+09:00 | feature/04-plugins | 거슬러 채움 | 남음 | — | — | $27.23 | 1 | 9 | 조건 2 TypeError ×3; 조건 2 통과 ×2; 조건 2 AttributeError ×1; 조건 3 문자열 '#/components/schemas/PluginManifest' ×1; 조건 3 문자열 'HTTPValidationError' ×1 | 없음 | 없음 |
| admin-api-03 | #48 | 29e00fa0 | c6e1ffa2 | 2026-09-23T10:03+09:00 | — | 거슬러 채움 | 빠짐 | 원래 브랜치 docs/ticket-03-bookkeeping 가 feature/ 로 시작하지 않는다 | — | — | 2 | — | — | 없음 | 없음 |
| admin-api-02 | #44 | ea7c2562 | 7ff73ff5 | 2026-09-22T22:55+09:00 | feature/02-server-stands-fail-closed | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $21.34 | 4 | 0 | 조건 2 결과 없음(모음 실패) ×29 | 없음 | 없음 |
| admin-api-01 | #42 | 41b12aed | 0442f884 | 2026-09-22T19:06+09:00 | feature/01-contract-list-ports-and-run-summary | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $33.73 | 8 | 0 | 조건 2 결과 없음(모음 실패) ×34 | 없음 | 없음 |
| interrupts-06 | #37 | e11f8c7d | 8c77344d | 2026-09-22T11:10+09:00 | feature/06-prove-it-outlives-the-process | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $10.71 | 0 | 0 | 조건 1 M 첫째 실행: 결과 없음 ×2 | 없음 | 없음 |
| interrupts-05 | #36 | 52e11fae | e11f8c7d | 2026-09-22T09:31+09:00 | feature/05-deny | 거슬러 채움 | 남음 | — | — | $20.68 | 0 | 5 | 조건 2 결과 없음(모음 실패) ×18; 조건 2 통과 ×1 | 없음 | 없음 |
| interrupts-04 | #35 | f01d8ae2 | 52e11fae | 2026-09-22T08:36+09:00 | feature/04-approve-and-resume | 거슬러 채움 | 남음 | — | — | $23.12 | 0 | 7 | 조건 1 M 첫째 실행: 결과 없음 ×1; 조건 2 결과 없음(모음 실패) ×32; 조건 2 AttributeError ×1 | 없음 | 없음 |
| interrupts-03 | #32 | 7585bae1 | cb08e24e | 2026-09-21T23:26+09:00 | feature/03-pause-at-the-gate | 거슬러 채움 | 남음 | — | — | $17.12 | 0 | 6 | 조건 1 M 첫째 실행: 결과 없음 ×1; 조건 2 통과 ×6; 조건 2 TypeError ×1; 조건 2 결과 없음(모음 실패) ×1; 조건 3 이름 'FlakyCloseTools' ×1; 조건 3 이름 'SwallowingAgent' ×1; 외 1가지 | 없음 | 없음 |
| interrupts-02 | #31 | 70d5186e | 7585bae1 | 2026-09-21T22:53+09:00 | feature/02-read-the-trace | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $10.29 | 0 | 0 | 조건 1 M 첫째 실행: 결과 없음 ×1; 조건 2 결과 없음(모음 실패) ×11 | 없음 | 없음 |
| interrupts-01 | #29 | ed4d429e | 528c3df1 | 2026-09-21T16:23+09:00 | feature/01-contract-events-and-manifest | 거슬러 채움 | 빠짐 | 숨은 시험이 0개라 3개보다 적다 | — | $28.29 | 1 | 0 | 조건 1 M 첫째 실행: 결과 없음 ×1; 조건 2 결과 없음(모음 실패) ×40 | 없음 | 없음 |

- B 가 2026-10-12 이후인 남은 후보: 1개(문턱 12개)
- 거슬러 채워 남은 후보: 7개
- 거슬러 채워 남은 후보 가운데 B 에 준비·게이트 파일(`web/package.json`, `tools/run_checks.py`) 가운데 하나라도 없는 것: 7개
- 푼 티켓 파일이 둘 이상이라 후보가 아닌 병합 커밋: #23
