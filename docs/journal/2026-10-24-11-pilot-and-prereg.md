# 2026-10-24 (11) 파일럿과 사전 등록

> 사용자: /implement .scratch/model-rerun/issues/11-pilot-and-prereg.md (next-session 지시문 그대로, "이번 요청 범위: PR과 병합까지")

이 세션의 제목은 `feature/11-pilot-and-prereg`이다. 주 체크아웃에서 `tidy-checkouts`를 돌아 루트를 f1ed4be7 에서 80ff61f1(origin/main)로 당기고 로컬 브랜치 `worktree-05-widget-conversation`을 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 다른 프로세스(python.exe)가 쥐고 있어 남았다. 그 뒤 워크트리 `11-pilot-and-prereg`에 들어가 브랜치를 땄다.

## 사람과 정한다

### 브랜치 표

`collect.py --refresh --out .scratch/model-rerun/probes/branches.json`으로 다시 모았다(origin/main 80ff61f1 때). 브랜치 380개다.

새 표가 옛 표(2026-10-23, c3c2cfcf 때)보다 기록이 적다. 응답이 141,889개에서 137,691개로, 저장소 안 비용이 $14,952.53 에서 $14,639.25 로 줄었다. 그사이 하루치 세션이 더 쌓였는데도 줄었으니, 사람의 기본 설정 폴더(`~/.claude/projects/`)에서 세션 기록 일부가 지워진 것으로 본다(무엇이 지웠는지는 보지 않았다). 두 표에 함께 있는 브랜치 366개 가운데 29개의 PR 앞 비용이 $0.5 넘게 바뀌었고 모두 세션 수가 줄었다. 큰 것은 `chore/choice-facts-batch`($105.10 → $4.48, 세션 41 → 38), `docs/design-reverse-sync-tickets`($43.17 → $0.00), `feature/02-docs-and-skills-teach-tickets`($32.46 → $2.30)다(두 표의 `meta`와 브랜치마다의 `cost − cost_post_pr`를 커밋하지 않은 스크립트로 견줘 손으로 봤다). 수집 도구는 같은 판이다(`collect_sha256` 같음).

### 후보 표

`rerun_select table --rev 80ff61f1`로 다시 지었다(KST 17:03 에 끝났다. 띄운 시각은 적지 않았다). 끝 줄은 앞 판과 같다. 날짜 안의 남은 후보 1개(ticket-for-every-pr-03, 숨은 시험 3개), 거슬러 채워 남은 후보 7개(http-channel-04·03, admin-api-06·04, interrupts-05·04·03), 그 7개 모두 B에 `web/package.json`과 `tools/run_checks.py`가 없다. 05 뒤에 병합된 날짜 안 후보 14개(model-rerun-01~10, web-widget-01~04)는 모두 빠졌다. model-rerun 은 숨은 시험 0개(새 모듈을 짓는 티켓이라 B에 덮은 시험이 import 에서 실패한다)이거나 PR 앞 비용이 $70 을 넘거나 낱말에 걸렸고, web-widget 은 `-m llm`이나 사진 비교 낱말에 걸렸다.

PR 앞 비용이 줄어든 행이 있다. ticket-for-every-pr-03 은 $22.60 에서 $0.19 로, ticket-for-every-pr-04 는 $38.21 에서 $0.25 로 바뀌었다. 위 브랜치 표의 기록 손실 때문이다.

### 낱말에 걸린 후보의 문맥

낱말로만 빠진 후보마다 B 의 티켓 글에서 맞은 줄을 커밋하지 않은 스크립트로 찍어 손으로 봤다(B 판을 `git show <B>:<티켓>`으로 꺼냈다). 거짓 양성 후보(부정문·인용·다른 뜻)로 보이는 것은 아래다. 되살린 뒤에도 숨은 시험 가르기를 지나야 남는다(`pilot`·`main` 명령이 표를 다시 지으며 가른다).

- 날짜 안: model-rerun-10(`사람이 확인`이 러너의 "사람이 확인 인자를 주면 잇는다"는 명령 줄 인자 이야기), model-rerun-05(낱말 목록 자체를 수용 기준에 인용), end-user-continuation-06(`사진 비교도 CI에 맡긴다`, 로컬에서 치지 않는다).
- 날짜 앞(거슬러 채우기가 닿을 때만 쓰인다): end-user-channel-05·04, conversation-04(`-m llm은 돌리지 않는다`), web-admin-01(`Playwright 실행`이 게이트 훅 모양의 예).
- 진짜 바깥 검증으로 보이는 것: web-widget-01·02·04, mcp-shutdown-01~03, end-user-continuation-02~05, end-user-channel-01~03, conversation-01~03(`-m llm`을 돌려 일지에 적는다), design-refresh-01~05·design-system-01~04·design-reverse-sync-01(사진 비교를 로컬에서 초록으로), token-usage-08(사용자 범위 MCP 를 지우는 바깥 상태 변경), web-admin-05·02, plugin-toggle-02, http-channel-05.

모두 되살려도 날짜 안의 남은 후보는 많아야 4개라 열둘에 모자란다. 그래서 사람이 길을 골라야 한다. 길을 고를 때 넣을 사실은 셋이다. 거슬러 채워 남은 7개는 B가 2026-09-21~26 이라 `web/`이 없어 준비 명령 `pnpm -C web install --frozen-lockfile`이 실패하고(러너는 "측정 아님(준비)"로 멈춘다), 게이트의 `tools/run_checks.py`도 없다. 날짜 안 후보 가운데 `-m llm`만으로 빠진 것이 10개(web-widget-01·02·04, mcp-shutdown-01~03, end-user-continuation-02~05)라, 그 낱말을 목록에서 빼는 "조건 고치기"가 열둘에 가장 가까운 길이다(숨은 시험 가르기는 아직 돌지 않았다). 대신 클론에는 `.env`가 없어 그 세션은 `-m llm` 체크박스를 지킬 수 없다. 그리고 위 "브랜치 표"의 기록 손실로 PR 앞 비용이 줄어든 브랜치가 있어, 비용 문턱 $70 과 회차 상한(세 배와 $40 가운데 큰 값)을 옛 표의 값으로 볼지도 정해야 한다.

## 인계 (첫째)

- 이 세션의 지금 제목: `feature/11-pilot-and-prereg`.
- 인계 경계: `커밋 뒤`. 세션 컨텍스트 약 26.2만 토큰에서 969a694f 커밋 직후 `hook_handoff`가 들어왔다. 인계하지 않는 다섯 때에 들지 않았다(커밋은 성공했고, 요청 범위는 PR과 병합까지이고, 이 세션의 지시문은 인계 줄이 아니고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다).
- 이 세션이 번복하거나 고친 것: 일지에 후보 표를 짓는 데 걸린 시간을 어림으로 적었다가 지웠다(띄운 시각을 적지 않았다).
- 이 절과 위 "낱말에 걸린 후보의 문맥" 절은 커밋하지 않은 채 워크트리에 있다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/11-pilot-and-prereg.md. 파일럿을 돌리고 사전 등록을 사람과 정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/11-pilot-and-prereg.md
브랜치: feature/11-pilot-and-prereg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-11-pilot-and-prereg.md 전체(커밋하지 않은 "낱말에 걸린 후보의 문맥"과 "인계 (첫째)" 절 포함), 티켓 11의 "사람과 정한다"
이어받을 상태: 인계: 커밋 뒤. 969a694f 까지 커밋했고 PR 은 없다. "사람과 정한다"의 첫 체크박스(브랜치 표 다시 모으기)는 db3e90db 로 마쳤고, 둘째(후보 표 다시 짓기)는 969a694f 로 지었으나 사람에게 아직 보이지 않았다. 다음은 그 표를 일지의 "낱말에 걸린 후보의 문맥" 절대로 사람에게 장면으로 보이고, 셋째(되살릴 목록)와 넷째(후보가 열둘에 모자라니 길 고르기)를 차례로 묻는 것이다. 새로 찾은 것: 다시 모은 브랜치 표는 사람의 기본 설정 폴더에서 세션 기록 일부가 지워져 옛 표보다 응답이 약 4,200개 적고 PR 앞 비용이 줄어든 브랜치가 29개다(일지 "브랜치 표"). 이것도 사람에게 함께 보인다. 커밋하지 않은 일지 두 절은 다음 커밋에 싣는다. docs/journal/2026-10-24-11-pilot-and-prereg.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/11-pilot-and-prereg (인계함)`으로 바꿨다. 백그라운드 작업은 모두 끝나 있었다. 워크트리 잠금을 풀었다.
- open-session을 부른다 2026-10-24T08:12:27Z

## 둘째 세션

### 되살릴 목록

> 사용자: /implement .scratch/model-rerun/issues/11-pilot-and-prereg.md (인계 지시문 그대로)

후보 표(위 "후보 표")와 브랜치 표의 기록 손실을 장면으로 보이고 셋째 체크박스를 물었다. 묻기 전에 후보 일곱의 B 판 티켓에서 걸린 줄과 B의 `web/package.json`·`tools/run_checks.py`를 커밋하지 않은 스크래치 스크립트로 다시 찍어 손으로 봤다. 위 문맥 절의 줄과 같았다. 고친 것 하나는 날짜 앞 넷의 B가 2026-09-29~10-06 이라는 것이다(9월 21~26일의 거슬러 채운 일곱과 다르다). end-user-channel-05·04 와 conversation-04 는 B에 `web/package.json`이 있고 `tools/run_checks.py`가 없으며, web-admin-01 은 둘 다 없다.

첫 화면(네 선택지 다중 선택)에는 고르지 않고 말로 답했다.

> 사용자: 추천해줘

모두 되살리기를 추천했다. 까닭은 셋이다. 일곱 모두 원문이 부정문·인용·다른 뜻이고, 되살리기는 후보 자격만 돌려줄 뿐 숨은 시험·비용·준비 거르기는 그대로 받으며, 사전 등록에 고정할 정의라 "거짓 양성이면 모두"라는 한 기준이 일부만 고르는 것보다 설명이 필요 없다.

> 질문: 추천대로 거짓 양성 후보 7개(model-rerun-10, model-rerun-05, end-user-continuation-06, end-user-channel-05·04, conversation-04, web-admin-01)를 모두 되살릴까요?
> 답: "7개 모두 되살린다 (Recommended)" — "걸린 줄이 부정문·인용·다른 뜻이면 되살린다"는 하나의 기준으로 일곱을 모두 입력 파일에 넣습니다. 나머지 거르기(숨은 시험·비용·준비 명령)는 그대로 받습니다.

입력 파일은 `.scratch/model-rerun/probes/revive.json`이다(과제 id → 까닭). `rerun_select.parse_revive`가 일곱으로 푸는 것을 손으로 봤다. `revive`의 검사(낱말로만 빠진 후보인가)는 표를 다시 짓는 `pilot`·`main` 명령에서 처음 돈다.
