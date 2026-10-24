# 2026-10-24 (08) 파일럿과 사전 등록

> 사용자: /implement .scratch/model-rerun/issues/11-pilot-and-prereg.md (next-session 지시문 그대로, "이번 요청 범위: PR과 병합까지")

이 세션의 제목은 `feature/11-pilot-and-prereg`이다. 주 체크아웃에서 `tidy-checkouts`를 돌아 루트를 f1ed4be7 에서 80ff61f1(origin/main)로 당기고 로컬 브랜치 `worktree-05-widget-conversation`을 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 다른 프로세스(python.exe)가 쥐고 있어 남았다. 그 뒤 워크트리 `11-pilot-and-prereg`에 들어가 브랜치를 땄다.

## 사람과 정한다

### 브랜치 표

`collect.py --refresh --out .scratch/model-rerun/probes/branches.json`으로 다시 모았다(origin/main 80ff61f1 때). 브랜치 380개다.

새 표가 옛 표(2026-10-23, c3c2cfcf 때)보다 기록이 적다. 응답이 141,889개에서 137,691개로, 저장소 안 비용이 $14,952.53 에서 $14,639.25 로 줄었다. 그사이 하루치 세션이 더 쌓였는데도 줄었으니, 사람의 기본 설정 폴더(`~/.claude/projects/`)에서 세션 기록 일부가 지워진 것으로 본다(무엇이 지웠는지는 보지 않았다). 두 표에 함께 있는 브랜치 366개 가운데 29개의 PR 앞 비용이 $0.5 넘게 바뀌었고 모두 세션 수가 줄었다. 큰 것은 `chore/choice-facts-batch`($105.10 → $4.48, 세션 41 → 38), `docs/design-reverse-sync-tickets`($43.17 → $0.00), `feature/02-docs-and-skills-teach-tickets`($32.46 → $2.30)다(두 표의 `meta`와 브랜치마다의 `cost − cost_post_pr`를 커밋하지 않은 스크립트로 견줘 손으로 봤다). 수집 도구는 같은 판이다(`collect_sha256` 같음).

### 후보 표

`rerun_select table --rev 80ff61f1`로 다시 지었다(KST 17:03 에 끝났다. 띄운 시각은 적지 않았다). 끝 줄은 앞 판과 같다. 날짜 안의 남은 후보 1개(ticket-for-every-pr-03, 숨은 시험 3개), 거슬러 채워 남은 후보 7개(http-channel-04·03, admin-api-06·04, interrupts-05·04·03), 그 7개 모두 B에 `web/package.json`과 `tools/run_checks.py`가 없다. 05 뒤에 병합된 날짜 안 후보 14개(model-rerun-01~10, web-widget-01~04)는 모두 빠졌다. model-rerun 은 숨은 시험 0개(새 모듈을 짓는 티켓이라 B에 덮은 시험이 import 에서 실패한다)이거나 PR 앞 비용이 $70 을 넘거나 낱말에 걸렸고, web-widget 은 `-m llm`이나 사진 비교 낱말에 걸렸다.

PR 앞 비용이 줄어든 행이 있다. ticket-for-every-pr-03 은 $22.60 에서 $0.19 로, ticket-for-every-pr-04 는 $38.21 에서 $0.25 로 바뀌었다. 위 브랜치 표의 기록 손실 때문이다.
