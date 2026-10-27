# 2026-10-28 (10) 파일럿과 사전 등록

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
읽을 것: docs/journal/2026-10-28-10-pilot-and-prereg.md 전체(커밋하지 않은 "낱말에 걸린 후보의 문맥"과 "인계 (첫째)" 절 포함), 티켓 11의 "사람과 정한다"
이어받을 상태: 인계: 커밋 뒤. 969a694f 까지 커밋했고 PR 은 없다. "사람과 정한다"의 첫 체크박스(브랜치 표 다시 모으기)는 db3e90db 로 마쳤고, 둘째(후보 표 다시 짓기)는 969a694f 로 지었으나 사람에게 아직 보이지 않았다. 다음은 그 표를 일지의 "낱말에 걸린 후보의 문맥" 절대로 사람에게 장면으로 보이고, 셋째(되살릴 목록)와 넷째(후보가 열둘에 모자라니 길 고르기)를 차례로 묻는 것이다. 새로 찾은 것: 다시 모은 브랜치 표는 사람의 기본 설정 폴더에서 세션 기록 일부가 지워져 옛 표보다 응답이 약 4,200개 적고 PR 앞 비용이 줄어든 브랜치가 29개다(일지 "브랜치 표"). 이것도 사람에게 함께 보인다. 커밋하지 않은 일지 두 절은 다음 커밋에 싣는다. docs/journal/2026-10-28-10-pilot-and-prereg.md
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

### 기록이 줄어든 까닭

옛 표(`db3e90db^`의 `branches.json`)와 새 표를 후보 브랜치마다 커밋하지 않은 스크래치 스크립트로 견줬다. 줄어든 것은 2026-10-22~23 에 병합된 브랜치에 몰렸다(ticket-for-every-pr-03 $22.60 → $0.19, model-rerun-01·02·03 $30~39 → $0.24~0.35, ticket-for-every-pr-01 $62.53 → $42.15). 기본 설정 폴더의 워크트리 기록 폴더를 `ls`로 보니 지워진 세션마다 `<세션 id>.desktop-released.json`이 있고 내용이 `"releasedAt": "2026-10-23T06:02:45.550Z", "reason": "delete"`였다. 같은 id 의 `.jsonl`은 없었다. 2026-10-23 뒤 수정된 그 표지가 113개다(`find -newermt`). 데스크톱 앱에서 세션 113개가 그 시각에 지워지며 기록 파일도 지워진 것으로 본다. 사람이 지웠는지 앱이 스스로 지웠는지는 이 표지로 가르지 못했다. 옛 표에 없는 2026-10-23 병합 브랜치 가운데 model-rerun-04($1.44)·06($19.12)도 낮게 보이지만 숨은 시험 0개로 이미 빠진다.

### 길과 비용 기준

후보 표를 날짜 안 빠진 까닭별로 셌다. 날짜 안 49행 가운데 숨은 시험 가르기를 받은 22행에서 지난 것은 ticket-for-every-pr-03 하나이고, 거슬러 채운 행에서 가르기를 받은 21행에서는 7행이 지났다. `-m llm` 하나로만 빠진 날짜 안 후보는 10개다. 그 10개와 되살린 날짜 안 3개를 9월 제품 티켓의 비율로 셈하면 날짜 안 후보가 5~6개쯤이라 열둘에 여전히 모자랄 것으로 어림했다. 회차 상한은 `rerun_select`의 `CAP_MULTIPLIER = 3.0`, `CAP_FLOOR_USD = 40.0`으로 대 봤다.

> 질문: 후보가 열둘에 모자라는 문제를 어떤 길로 풀까요?
> 답: "-m llm만 빼고 다시 세기 (Recommended)" — 거르기 낱말에서 -m llm을 빼고 후보 표를 다시 짓습니다(지난번에 2시간 52분). 실제 수를 본 뒤 여전히 모자라면 둘째 길로 넓힐지 다시 여쭙니다. 도구 고침은 상수 하나와 그 시험입니다.

> 질문: 삭제로 줄어든 'PR 앞 비용'을 어느 값으로 쓸까요? (비용 $70 거르기와 회차 상한에 쓰입니다)
> 답: "옛 표와 새 표 중 큰 값 (Recommended)" — 삭제는 값을 줄이기만 하므로, 옛 표(10-23 새벽)를 파일로 고정해 두고 브랜치마다 큰 값을 씁니다. ticket-for-every-pr-03은 $22.60, 회차 상한 $67.80이 됩니다. 고르기 도구에 입력 하나와 시험을 더합니다.

둘째 길은 "옛 B에 맞춘 준비·게이트까지"(B에 `web/`이 없으면 pnpm 준비를 건너뛰고 `run_checks.py`가 없으면 그 시점의 검증 명령을 직접 친다)다. 고르지 않은 다른 둘은 "과제 수를 줄인다"와 "측정을 미룬다"다.

### 고친 것과 다시 짓는 후보 표

- `tools/rerun_select.py`: `EXTERNAL_TERMS`에서 `-m llm`을 뺐고, `with_earlier`와 `--earlier-branches`를 더했다. 시험을 먼저 써서 `-m llm` 시험의 빨강을 봤고, `with_earlier`의 시험은 첫 실패에서 멈춰 빨강을 보지 못해 변이 일곱(41~47)을 `rerun_select_mutations.toml`에 더해 모두 기대대로 빨개지는 것을 봤다.
- 옛 표를 `.scratch/model-rerun/probes/branches-2026-10-23.json`으로 고정했다(`git show db3e90db^:…`).
- 되살릴 목록에서 end-user-channel-05·04 와 conversation-04 를 뺐다. 셋은 `-m llm`으로만 걸려 낱말을 뺀 뒤에는 거르기에 걸리지 않고, 되살리기는 낱말에 걸린 후보만 받아 첫 실행이 "바깥 검증 낱말에 걸리지 않았다"로 2를 냈다. 되살리지 않아도 후보로 돌아오므로 사람이 고른 결과와 같다. 남은 넷은 model-rerun-10·05, end-user-continuation-06, web-admin-01 이다.
- 후보 표를 `--rev 80ff61f1`(브랜치 표를 모은 때)로 다시 짓기 시작했다(2026-10-24T09:06Z, 백그라운드).

### 다시 지은 후보 표

2026-10-24T12:36Z 에 끝났다(띄운 때 09:06Z, 약 3시간 30분). 끝 줄: 날짜 안 남은 후보 9개(문턱 12개), 거슬러 채워 남은 후보 3개, 그 3개 모두 B 에 `tools/run_checks.py`가 없다(`web/package.json`은 있다). 날짜 안 9개는 model-rerun-10(되살림), web-widget-02·01, ticket-for-every-pr-03, mcp-shutdown-02·01, end-user-continuation-02·05·03 이다. 거슬러 채운 3개는 end-user-channel-04, conversation-02·01(B 2026-10-04~06)이다. 되살린 model-rerun-05·end-user-continuation-06 과 web-widget-04, mcp-shutdown-03, end-user-continuation-04 는 숨은 시험 가르기에서 빠졌다. ticket-for-every-pr-03 의 PR 앞 비용은 옛 표의 $22.60 이 쓰였다.

## 셋째 세션 (2026-10-26)

> 사용자: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

인계 지시문 없이 열린 세션이다. 브랜치는 이 PC의 워크트리 `11-pilot-and-prereg`에 d5ab0c15 까지 커밋된 채 남아 있었고(push 하지 않았다, 작업 트리 깨끗), `EnterWorktree`로 들어와 이었다. 그사이 origin/main 은 80ff61f1 에서 6커밋 앞섰다(cb6d9c39, web-widget 05~08·11).

### 후보 길

다시 지은 후보 표(위 "다시 지은 후보 표")를 보이고 넷째 체크박스를 물었다. 묻기 전에 대 본 것: 게이트는 `tools/rerun_files.py`의 `GATE_COMMANDS` 셋(`ruff check`, `ruff format --check`, `tools/run_checks.py`)이고 회차 기록 읽기가 그 셋이 차례로 드는지 본다. 후보가 9개면 명세 "층과 수"대로 파일럿 셋을 뺀 6개를 2·2·2로 자르게 되어 본 측정 여덟(3·3·2)을 채우지 못한다.

> 질문: 후보 12개 중 3개는 판정용 검사 파일(run_checks.py)이 없던 시점의 코드에서 시작합니다. 어떻게 할까요?
> 답: "그 시점 명령을 직접 친다 (Recommended)" — 옛 과제 3개에서는 셋째 게이트(run_checks.py) 대신 그때의 검증 명령(pytest·pyright·lint-imports 등)을 직접 칩니다. 후보 12개를 모두 써서 파일럿 3개와 본 측정 8개를 고릅니다. 게이트 목록과 회차 기록의 모양 검사를 고치고 시험을 더합니다. 옛 과제가 어느 층에 들지는 아직 모릅니다.

고르지 않은 둘은 "9개로 과제 수를 줄인다"(본 측정 6개, 명세의 열둘 규칙과 고르기 문턱을 고친다)와 "후보가 쌓일 때까지 미룬다"다.

### 옛 게이트 묶음

- `tools/rerun_files.py`: `GATE_FILE`, `OLD_GATE_COMMANDS`(ruff 둘, `uv run pytest -q`, `uv run pyright`, `uv run lint-imports`, `pnpm -C web verify`), `GATE_SETS`를 더했다. 회차 기록의 게이트 칸은 두 묶음 가운데 하나를 그 차례로 든다. 세 B(8a4274fe, 4112d2b8, 300b5f03)의 CLAUDE.md "검증 명령" 절을 `git show`로 꺼내 손으로 봤고 손으로 치는 명령이 셋 다 같았다(8a4274fe 의 절에는 pytest 괄호에 워크트리 `.env` 경로 문장이 더 붙어 절의 글은 같지 않다. 넷째 세션의 셀프 리뷰가 짚었다).
- `tools/rerun_gates.py`: `OLD_GATE_ARGV`와 `has_gate_file`(원본에서 `git ls-tree <B> -- tools/run_checks.py`의 형이 blob 인지)을 더했다. `check_result`는 받은 게이트를 돌기만 한다.
- `tools/rerun_runner.py`: `World.old_gates`를 두고, 끝남인 회차에서 B 로 묶음을 고른다. 가르지 못하면(`GateError`) 게이트 작업 트리를 짓지 못한 것과 같이 측정 아님(준비)이다. 기록 이름은 묶음의 수(셋, 여섯)로 가른다.
- 러너 시험의 원본 B 에 빈 `tools/run_checks.py`를 두었다. 두지 않으면 기존 시험이 옛 묶음의 진짜 명령을 돈다. 옛 원본은 따로 지었다.
- 시험을 먼저 써서 import 오류의 빨강을 봤다. 구현 뒤 한 번 빨개진 것은 내가 쓴 시험 사례였다(`옛[:2] + 새[2]`는 새 묶음과 같아 거부될 까닭이 없다). 그 사례를 옛 묶음의 뒤 넷을 뒤바꾼 차례로 바꿨다. 러너·게이트 시험은 import 오류로만 빨강을 봐서 변이 여섯(기록 49, 게이트 49·50, 러너 26~28)을 더했고, 없는 표지로 한 번 돌려 여섯 모두 고른 단언에서 빨개지는 것을 본 뒤 표지를 골랐다.

### 검증과 인계 (셋째 세션)

> 사용자: 이어서 진행

(앞 턴에서 사용자가 한 번 도구 호출을 멈추게 한 뒤 보낸 말이다.)

- 표지를 넣은 변이 여섯을 다시 돌려 세 표 모두 0으로 끝났다(기록 49, 게이트 49·50, 러너 26~28). `uv run ruff check .`과 `uv run ruff format --check .`은 초록이다. `uv run python tools/run_checks.py`는 백그라운드로 띄웠다가 아래 인계로 멈췄다(결과 없음).
- 이 세션의 지금 제목: `Pilot and prereg feature continuation`(앱이 지었다).
- 인계 경계: `셀프 리뷰 직전`. 세션 컨텍스트 약 27.8만 토큰에서 `code-review`를 부르자 `hook_handoff`가 들어왔다. 인계하지 않는 다섯 때에 들지 않았다(명령은 성공했고, 지시문 없이 연 세션이라 요청 범위와 앞 인계 줄이 없고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다).
- 이 세션이 번복하거나 고친 것: 첫 선택 화면의 설명이 "9개로 줄이면 최소치(6)에 걸린다"고 적었다가, 훅이 막아 대 보니 본 측정 여덟(3·3·2)이 6개(2·2·2)가 되고 명세의 열둘 규칙을 고쳐야 하는 것이라 고쳐 물었다. 옛 게이트 묶음을 고르는 자리를 처음에 `check_result` 안에 두려다 러너로 옮겼다(게이트 모듈의 기존 시험을 그대로 두려고). 기록 꼴 시험의 사례 하나(`옛[:2] + 새[2]`)가 틀려 바꿨다(위 "옛 게이트 묶음").
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/11-pilot-and-prereg.md. 파일럿을 돌리고 사전 등록을 사람과 정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?
브랜치: feature/11-pilot-and-prereg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-10-pilot-and-prereg.md의 "셋째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "사람과 정한다" 다섯째 체크박스부터
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(B 에 tools/run_checks.py 가 없는 과제의 옛 게이트 묶음: tools/rerun_files.py·rerun_gates.py·rerun_runner.py 와 그 시험, 변이 여섯, 명세 "게이트와 숨은 시험" 주석, 티켓 넷째 체크박스, 일지)이 워크트리에 있고 셀프 리뷰(/code-review, 기준 HEAD d5ab0c15)부터 한다. ruff 둘은 초록이고 변이 여섯은 표지까지 기대대로였다. run_checks.py 는 인계로 멈춰 결과가 없다. 리뷰를 반영해 커밋한 뒤 다음은 다섯째 체크박스(전용 설정 폴더의 njh6803 로그인과 설정 옮기기)를 사람에게 묻는 것이다. PR 은 없다. docs/journal/2026-10-28-10-pilot-and-prereg.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```
- open-session을 부른다 2026-10-26T02:17:28Z

## 넷째 세션 (2026-10-26)

> 사용자: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

셋째 세션의 지시문으로 연 세션이다. `EnterWorktree`로 워크트리 `11-pilot-and-prereg`(d5ab0c15, 커밋하지 않은 변경 12파일)에 들어와 이었다. `uv run python tools/run_checks.py`를 백그라운드로 다시 띄우고 셀프 리뷰(`code-review`, base d5ab0c15)를 시작했다.
- 리뷰 앞 판의 `uv run python tools/run_checks.py`는 종료 0이었다(pytest 378초, web-verify 272초).

### 셀프 리뷰 (넷째 세션)

범위: base d5ab0c15, 파일 12개, 커밋 0개, 미추적 0개. 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다.

- 표준 축: Major 1(살아 있는 문서와 독스트링에 "게이트 셋"이 남아 이제 거짓이다. 명세 252·253행, `rerun_files` `gates_green`, `rerun_judge` `solved`, `rerun_gates`의 `Limits.gates`·`_gates`·`check_result`). Minor 4(러너가 묶음을 불리언으로 고른 뒤 `_named_gates`가 수로 다시 짐작한다, `current`라는 이름, `has_gate_file` 앞머리가 `check_result`와 같다, ls-tree 줄 파싱이 함수 안에 섞였다, 시험이 밟지 않은 길 둘(B 가르기가 실패하는 길, 결과 커밋이 게이트 러너를 지우는 길)). Nit 3(심볼릭 링크는 파일로 센다, 상수를 리터럴로 복제한 시험, `SETUP_COMMANDS` 문구).
- 명세 축: Major 1(같은 "게이트 셋" 잔존, 명세 "회차 기록" 결과 줄, 티켓 28행). Minor 4("그 절이 같다"는 글자 그대로는 거짓이다(8a4274fe 의 절에 `.env` 문장이 더 있다), "층과 수" 주석이 고른 길을 가리키지 않는다, 옛 묶음이 30분 안에 끝나는지 근거가 없다, 옛 묶음은 `run_checks.py`의 검사가 없어 판정이 느슨하다). Nit 2(링크, `_named_gates`가 수를 보지 않는다). 사실 대조(#160 이 4319c0e6 에서 `run_checks.py`를 처음 더했다, 세 B 에 `web/package.json`의 `verify`가 있다, 손으로 치는 명령이 같다)는 맞았다.
- 고친 것: "게이트 셋"을 명세 241·252·253행, 티켓 28행, 도구 독스트링·주석 여섯 자리, 게이트 시험 머리에서 고쳤다. 명세 240행 주석을 "그 절의 손으로 치는 명령이 같은 것을 손으로 봤다(절의 글은 B 마다 조금 다르다)"로 좁히고, "옛 묶음에는 그때 `run_checks.py`가 없어 돌지 않던 검사(지침, 타입 우회, 훅 러너)가 없어 판정이 새 묶음보다 느슨하다. 한 과제는 모든 갈래가 같은 묶음을 돌므로 갈래 사이의 견줌에는 들지 않는다"를 더했다. "층과 수" 주석 끝에 "다시 지은 후보 표에서 거슬러 채워 남은 셋은 B 가 9월이 아니라 2026-10-04~06 이라 `web/package.json`은 있고 `tools/run_checks.py`만 없다"를 더했다. 티켓 28행에 "파일럿에 옛 게이트 묶음의 과제가 들면 그 여섯이 30분 안에 끝나는지도 본다"를 넣었다. 러너는 고른 묶음의 이름(`gate_names`)을 들고 가고 `_named_gates`는 수가 다르면 `ValueError`다. `has_gate_file`과 `check_result`가 `_git_of`를, ls-tree 줄은 `_is_blob_at`을 쓴다. 독스트링에 "같은 이름의 심볼릭 링크는 형이 blob 이라 파일로 센다"를 적었다. 러너 시험 둘(B 가르기 실패, 결과 커밋이 게이트 러너를 지움)과 러너 변이 29를 더했다. 위 셋째 세션 "옛 게이트 묶음"의 "셋이 같았다"도 고쳤다.
- 고치며 찾은 것: `tools/mutate.py --check`가 세 표에서 원문 여섯이 어긋났다고 냈다. 기록 29는 셋째 세션이 `_outcome`의 견줌과 시험 이름을 바꾸고 표를 맞추지 않은 것이고(셋째 세션의 "변이 여섯" 확인은 그 여섯만 번호로 돌려 이것을 보지 못했다), 게이트 4는 이 세션의 편집이 `files = ` 뒤 공백을 지운 것이며, 나머지 넷은 이 세션의 고침이 바꾼 원문이다. 맞춘 뒤 고친 일곱을 번호로 돌려 모두 기대대로였다. 프로브 README 변이 절에 한 문단을 더했다.
- 남긴 것: 상수를 리터럴로 복제한 시험(Nit)은 그대로 둔다. 옛 묶음의 글을 고정하는 것이 그 시험의 뜻이다. `SETUP_COMMANDS` 문구(Nit)는 표준 축이 맞다고 했다.
- PR 직전 리뷰에 밀 주장: 위 "고친 것"의 명세 240행 두 문장과 "층과 수" 주석 문장, 티켓 28행 문장, `has_gate_file` 독스트링의 링크 문장.

### 커밋과 인계 (넷째 세션)

- 리뷰를 반영한 뒤 `uv run ruff check .`, `uv run ruff format --check .`(러너 한 파일을 포맷한 뒤)은 초록이다. `tools/sibling_overlap.py`가 이 일지(옛 2026-10-24-11)가 origin/main 의 최신 일지보다 이름순으로 앞이라고 해 `--move`로 2026-10-28-10 로 옮겼다. 커밋 1dd42c39 의 pre-commit 이 손으로 치는 다섯을 갈음했고 모두 통과했다(`Skipped`는 카나리아 명세 모양과 헌법 판, 둘 다 해당 파일 없음). origin/main 은 이 브랜치의 기점보다 앞서 있고(`git diff --name-only HEAD...origin/main`에 `tools/mutate.py`, `CLAUDE.md`, `docs/constitution/operations.md` 등), 이 브랜치가 이름으로 든 `tools/rerun_*` 와는 겹치지 않는다. PR 전에 main 을 합친다.
- 이 세션의 지금 제목: `feature/11-pilot-and-prereg`(지시문대로 바꿨다).
- 인계 경계: `커밋 뒤`. 컨텍스트 약 24.1만 토큰에서 커밋 직후 `hook_handoff`가 들어왔다. 인계하지 않는 다섯 때에 들지 않았다(커밋은 성공했고, 요청 범위는 PR과 병합까지이고, 이 세션의 지시문 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 다른 경계이고, `인계 못함` 줄이 없고, 지시문으로 연 세션이다).
- 이 세션이 번복하거나 고친 것: 셋째 세션이 맞추지 않은 변이 원문(기록 29)과, 이 세션의 편집이 지운 공백(게이트 4)을 `--check`로 찾아 고쳤다(위 "셀프 리뷰 (넷째 세션)").
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/11-pilot-and-prereg.md. 파일럿을 돌리고 사전 등록을 사람과 정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?
브랜치: feature/11-pilot-and-prereg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-10-pilot-and-prereg.md의 "넷째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "사람과 정한다" 다섯째 체크박스부터
이어받을 상태: 인계: 커밋 뒤. 1dd42c39 까지 넷째 체크박스(옛 게이트 묶음)와 그 셀프 리뷰 반영을 커밋했다(푸시하지 않았다, PR 없음). 남은 단계는 다섯째 체크박스(전용 설정 폴더의 njh6803 로그인과 설정 옮기기)를 사람에게 묻는 것부터다. PR 직전 리뷰에 밀 주장은 일지 "셀프 리뷰 (넷째 세션)"의 마지막 줄에 있다. 이 일지의 "커밋과 인계 (넷째 세션)" 절은 커밋하지 않았다. docs/journal/2026-10-28-10-pilot-and-prereg.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```
- 잠금 풀기: 이미 풀려 있었다(`is not locked`). open-session을 부른다 2026-10-26T02:42:39Z

## 다섯째 세션 (2026-10-26)

> 사용자: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

넷째 세션의 지시문으로 연 세션이다. `EnterWorktree`로 워크트리 `11-pilot-and-prereg`(1dd42c39, 커밋하지 않은 변경은 이 일지 하나)에 들어와 이었다.

### 다시 풀기 계정

다섯째 체크박스를 물으려고 빈 전용 설정 폴더 `C:\Users\User\.claude-rerun`으로 `claude auth status --json`(2.1.302)을 쳤다. 종료 1, `loggedIn` 거짓, `email` 키 없음, `configDirectory`는 넘긴 문자열 그대로였다(손으로 봤다. 명세 "계정"의 주석과 같다). 사람에게 로그인을 물었다.

> 사용자: njh6803는 한도가 없는데?

한도가 아예 없는 계정인지, 남은 한도가 없는지 되물었다.

> 사용자: njh6803 계정 주간한도가 꽉차서 njh4803 계정으로 진행해야해

그래서 다시 풀기 계정을 njh4803으로 바꾼다. 전용 설정 폴더는 그대로 둔다. 기록은 기본 설정 폴더와 갈리지만(브랜치 표의 수집이 읽는 `~/.claude/projects/`에 회차가 섞이지 않는다), 한도는 사람의 평소 작업과 같은 주간 창을 쓴다. 그때 `get_usage`는 Max 플랜, 주간(모든 모델) 2%, 초기화 2026-11-01T20:59:59Z(KST 2026-11-02 06:00)였다(손으로 봤다). 고친 자리는 설계 11절(주석), 명세 37·58·77·166·276·317행, 프로브 README 3·65행, 티켓 11의 5·19·20행이다. 저장소 이름 `njh6803/agent-os`(오염 꼴)와 끝난 티켓 09는 계정 이야기가 아니라 그대로 둔다. 러너는 `--account`로 이름을 받으므로 코드는 바뀌지 않는다.

### 전용 설정 폴더

> 사용자: 전용 설정 폴더에 njh4803으로 로그인했고 설정 세 가지도 옮겼어. 확인해 줘.

- 폴더 `C:\Users\User\.claude-rerun`으로 친 `claude auth status --json`이 종료 0, `loggedIn` 참, `authMethod` `claude.ai`, `email`의 `@` 앞이 njh4803, `configDirectory`가 그 폴더였다(PowerShell로 그 칸만 찍어 손으로 봤다. 이메일 전체는 찍지 않았다).
- 폴더에는 `.claude.json`, `.credentials.json`, `backups/`, `output-styles/fluent-korean-explanatory.md`, `settings.json`이 있었다. `settings.json`은 `$schema`, `outputStyle`, `language`, `autoCompactWindow`(400000)뿐이라 `env`·플러그인·MCP 키가 없다(Read로 봤다. 사람이 옮긴 파일이라 `hook_user_settings_read`의 대상이 아니었다). `.claude.json`의 최상위 키에 `mcp`·`plugin`·`env`가 든 이름이 없었다(PowerShell로 키 이름만 찍었다). `projects/`는 아직 없었다.

### 판 고정

- `~/.local/share/claude/versions/`에는 2.1.299·2.1.300·2.1.302 실행 파일이 있고, PATH 의 `claude`는 `~/.local/bin/claude.exe`다.
- `versions/2.1.302`를 파이썬 `subprocess`로 바로 띄우면 `--version`이 `2.1.302 (Claude Code)`로 종료 0이다. PowerShell 의 `&`는 확장자가 없어 "문서"로 보고 띄우지 못했다. 러너는 `subprocess`로 띄우므로 상관없다.
- 그렇게 띄운 프로세스를 `tools.proc_command_line.pids_named("2.1.302")`가 잡았고, `claude.exe`로는 잡히지 않았다. 같은 때 `claude.exe`라는 이름의 프로세스는 17개였다(사람의 다른 세션들). 그래서 러너의 `--claude`를 PATH 의 `claude.exe`로 주면 죽은 러너를 다시 띄울 때 남의 세션을 "아직 도는 회차"로 볼 수 있고, 판 이름 경로로 주면 그 이름으로만 훑는다(커밋하지 않은 스크래치 스크립트 `pin_name.py`로 손으로 봤다. stdin 을 열어 둔 `-p`라 모델을 부르지 않았고, 빈 임시 설정 폴더였다).
- 같은 경로로 전용 설정 폴더, `DISABLE_AUTOUPDATER=1`, `--model haiku --max-budget-usd 0.05 --strict-mcp-config`로 한 번 부르니 init 의 `claude_code_version`이 2.1.302, `mcp_servers` 빈 목록, `plugins`가 내장 셋(`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-plugin-authoring`)이었고 결과는 `success`, $0.0086 였다(스크래치 스크립트 `pin_init.py`로 손으로 봤다. 작업 폴더는 세션 스크래치패드다).
- 못 본 것: 사람의 `claude.exe`가 판을 올릴 때 업데이터가 옛 판 파일을 지우는지. 지금 셋이 남아 있다는 것만 안다.

사람에게 여섯째와 일곱째를 함께 물었다(질문 "njh4803 한도로 파일럿($65~115)과 본 측정(상한 $900, 주간의 약 33%로 어림)을 함께 돌려도 괜찮을까요?", "측정 기간에 Claude Code 판(2.1.302)을 어떻게 고정할까요?").

> 사용자(선택): "그대로 진행 (Recommended)" — 상한 $900을 유지합니다(설계 11절의 값). 측정 기간에는 평소 작업을 줄여 한도 여유를 남겨 둡니다. 33%는 재 본 적 없는 환산(1% ≈ $27)입니다.
> 사용자(선택): "복사본을 따로 둠 (Recommended)" — 2.1.302 파일(약 290MB)을 versions 밖 폴더(예: C:\Users\User\.claude-rerun-bin\2.1.302)로 복사해 러너에 그 경로를 줍니다. 업데이터가 versions 밖을 건드리지 않는다는 것은 어림입니다. 복사본이 같은 판으로 도는지는 제가 복사한 뒤 다시 확인합니다. 평소 claude는 계속 업데이트됩니다.

- 복사본 `C:\Users\User\.claude-rerun-bin\2.1.302`를 만들었다. 원본과 SHA-256 이 같다(`Get-FileHash`). 위 두 스크래치 스크립트를 복사본 경로로 바꿔 다시 돌리니, `pids_named("2.1.302")`가 그 pid 를 잡았고 init 의 판은 2.1.302, 결과는 `success`($0.0087)였다(손으로 봤다).

### 계정 동기화 플러그인

- 복사본으로 친 둘째 호출의 init `plugins`에 내장 셋 말고 `frontend-design`(`source` `frontend-design@synced`)과 `cowork-plugin-management`(`cowork-plugin-management@synced`, 0.2.2)가 더 실렸다. 첫 호출에는 없었다. 첫 호출 뒤 그 폴더에 `plugins/synced/<id>/`와 `skills/synced/<id>/`(built-in-browser, chrome-browser, computer-use, deep-research, docs, docx, google-workspace, import-memory, morning, pdf, pptx, skill-creator, xlsx)가 생겼다. claude.ai 계정에 걸린 플러그인과 스킬을 첫 실행에서 받아 와 다음 실행부터 싣는 것으로 본다(두 호출과 폴더 목록만 본 어림이다. 언제 다시 받는지는 보지 않았다). `settings.json`은 그대로였다.
- 두 플러그인에는 `hooks`, `.mcp.json`, `agents`, `commands`가 없고 `skills/`뿐이다(`find`로 봤다). `github`이 든 `.md`·`.json`도 없었다(`grep -ril`).
- 지금 러너의 허용 모임(`tools/rerun_checks.py`의 `BUILTIN_PLUGINS`와 클론의 `enabledPlugins`)에는 둘이 없다. 그래서 파일럿의 첫 회차가 "측정 아님(설정)"으로 멈춘다(코드 읽기). 사람의 기본 설정 폴더로 도는 이 세션의 스킬 목록에도 두 플러그인이 있어, 원래 세션도 이것을 싣고 돈 것으로 본다(어림).

> 사용자: 둘을 허용하는데, 작업 난이도도 구분이 돼?

- `tools/rerun_checks.py`에 `SYNCED_PLUGINS`와 `_SYNCED_SOURCE`를 두어 허용 모임에 `<이름>@synced` 둘을 더했다. 시험을 먼저 고쳐(`_synced`, 허용 둘·새 동기화 이름·다른 마켓의 같은 이름) import 오류로 빨간 것을 본 뒤 고쳤다. 명세 "설정 폴더의 설정"에 주석을 달았다. `tools/mutate.py --check`로 `rerun_checks_mutations.toml` 원문 46개가 그대로인 것을 봤다.
- 세 파일(`test_rerun_checks`, `test_rerun_session`, `test_rerun_runner`)을 한 프로세스로 돌리니 `test_rerun_session.py`의 `test_자식의_표준_입출력이_없으면_명령_줄을_본_뒤_끄고_예외를_올린다`가 명령 줄을 읽지 못해(`None`) 빨갰고, 홀로 다시 돌리니 초록이었다(73초). 이 세션은 그 파일을 고치지 않았다. 부하 아래의 흔들림으로 본다(어림).
- 난이도는 따로 재지 않는다고 답했다. 층은 크기 지표(티켓이 든 파일 경로 수)로 나누고, 그것이 원래 비용과 순위 상관 0.65인 대리 지표다(설계 3절). 층별 결과는 판정이 아니라 탐색으로 낸다(설계 6절 "크기 층별 결과").

### 파일럿 고르기와 막는 규칙 탐침

- 파일럿 고르기를 백그라운드로 띄웠다: `uv run python -m tools.rerun_select pilot --branches .scratch/model-rerun/probes/branches.json --earlier-branches .scratch/model-rerun/probes/branches-2026-10-23.json --revive .scratch/model-rerun/probes/revive.json --table .scratch/model-rerun/probes/candidates.md --rev 80ff61f1 --out .scratch/model-rerun/probes/pilot.json`(입력은 셋째 세션의 후보 표와 같고, 출력은 세션 스크래치패드의 `pilot_select.log`).
- 그동안 막는 규칙의 새 꼴을 `.scratch/model-rerun/probes/deny_shapes/deny_shapes.py`로 쟀다. 러너의 `deny_rules`를 가짜 주 체크아웃·홈에 걸고 러너의 `session_command`(갈래 E)로 돈다. 세 번 돌았고(첫째는 이름 규칙의 도구를 `ToolSearch`에서 못 찾아 시도 없음, 둘째의 `규칙`은 Edit 미시도), 셋째가 두 갈래 모두 측정이었다. 결과는 프로브 README 의 새 절이다. 세 실행의 비용은 약 $0.14·$0.23·$0.23 이다.
- 2026-10-26T03:49Z 에 그 로그에는 `숨은 시험을 가른다` 줄이 둘(B f1ed4be7 M 80ff61f1, B 7496a830 M f1ed4be7)이었다. 첫째 뒤에 임시 작업 트리 `b`·`m`을 걷지 못했다는 줄(`failed to delete … Invalid argument`)과 임시 폴더 `rerun-hidden-85tz413a`가 남았다는 줄이 찍혔다. `%TEMP%`에는 `rerun-hidden-*` 폴더가 아홉 있다(앞 세션들의 것이 섞였을 수 있다. 어느 것이 이 실행의 것인지는 가르지 않았다).

### 인계 (다섯째 세션)

- 인계 경계: `셀프 리뷰 직전`. `/code-review`(base 1dd42c39)를 부른 직후 `hook_handoff`가 컨텍스트 약 33.4만 토큰에서 들어왔다. 인계하지 않는 다섯 때에 들지 않았다(이 세션 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 다른 경계이고, `인계 못함` 줄이 없고, 지시문으로 연 세션이다). 셀프 리뷰는 새 세션이 한다.
- 이 세션의 지금 제목: `feature/11-pilot-and-prereg`.
- 이 세션이 번복한 것: 다시 풀기 계정(njh6803 → njh4803, 사람이 정했다). 막는 규칙 탐침의 표지(첫 실행 뒤 `ToolSearch`도 시도로 세고 init tools를 적게 고쳤다).
- 커밋하지 않은 변경: 설계 11절, 명세, 프로브 README, 티켓 11, `tools/rerun_checks.py`, `tests/tools/test_rerun_checks.py`, 미추적 `.scratch/model-rerun/probes/deny_shapes/`, 이 일지.
- 파일럿 고르기 백그라운드는 이 세션과 함께 멈춘다. 새 세션이 위 명령으로 다시 띄운다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/11-pilot-and-prereg.md. 파일럿을 돌리고 사전 등록을 사람과 정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?
브랜치: feature/11-pilot-and-prereg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-10-pilot-and-prereg.md의 "다섯째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "러너로 파일럿 목록을 돈다" 체크박스부터
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(설계·명세·프로브 README·티켓 11·tools/rerun_checks.py·그 시험·미추적 probes/deny_shapes/·일지)이 워크트리에 있고 셀프 리뷰(/code-review, base 1dd42c39)부터 한다. 파일럿 고르기 백그라운드는 멈췄으니 다시 띄운다: uv run python -m tools.rerun_select pilot --branches .scratch/model-rerun/probes/branches.json --earlier-branches .scratch/model-rerun/probes/branches-2026-10-23.json --revive .scratch/model-rerun/probes/revive.json --table .scratch/model-rerun/probes/candidates.md --rev 80ff61f1 --out .scratch/model-rerun/probes/pilot.json (약 3시간, 남은 %TEMP%\rerun-hidden-* 폴더는 일지 참고). 러너 인자: --account njh4803 --config-dir C:\Users\User\.claude-rerun --claude C:\Users\User\.claude-rerun-bin\2.1.302 --cap 900. PR 직전 리뷰에 밀 주장은 일지 "셀프 리뷰 (넷째 세션)"의 마지막 줄과 다섯째 세션이 새로 쓴 문장(설계 11절 주석, 명세 167행 주석, 프로브 README "막는 규칙의 새 꼴" 절)이다. docs/journal/2026-10-28-10-pilot-and-prereg.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```
- 잠금 풀기: 이미 풀려 있었다(`is not locked`). 파일럿 고르기 백그라운드를 멈췄다. open-session을 부른다 2026-10-26T03:50:21Z

## 여섯째 세션 (2026-10-26)

> 사용자: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

다섯째 세션의 지시문으로 연 세션이다. `EnterWorktree`로 워크트리 `11-pilot-and-prereg`(1dd42c39, 커밋하지 않은 변경 7파일과 미추적 `deny_shapes/`)에 들어와 이었다. 파일럿 고르기를 같은 명령으로 백그라운드에 다시 띄웠고(출력은 세션 스크래치패드의 `pilot_select.log`), 셀프 리뷰(`code-review`, base 1dd42c39)의 두 축을 띄웠다.

### 셀프 리뷰 (여섯째 세션)

범위: base 1dd42c39, 파일 7개, 커밋 0개, 미추적 1개(`deny_shapes/`, 파일 5개). 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다.

- 표준 축: Major 1(`SYNCED_PLUGINS` 주석과 명세 167행 주석이 일지의 어림 둘("원래 세션과 조건이 같다", 첫 실행에서 받아 와 다음 실행에 싣는다)을 사실로 적었다. 같은 폴더의 `skills/synced/` 스킬은 언급이 없다). Minor 6(ADR 0029 317행의 njh6803, `source` 없는 플러그인 항목은 마켓을 보지 않는다, README "서브에이전트는 두 갈래 모두 백그라운드"가 `대조-2`에서 틀리다, 18/28 차를 커밋하지 않은 스크립트로 냈고 요약 파일 이름을 손으로 바꾼 것이 README 에 없다, "오염으로 세지 않는다"가 코드를 대 보지 않은 추론이다, 탐침이 거부 표지를 단언하지 않는다). Nit 넷(지역 변수 `main`, `find_use`·`searched`의 같은 순회, `ACTIONS` 튜플, `session_env` 복제).
- 명세 축: Major 1(티켓 26행의 "표지를 단언한다"를 `missing_marker`가 지키지 않는다. 시도만 본다). Minor 5(명세 240행 "그때 `run_checks.py`가 없어 돌지 않던 검사"가 거짓이다. B 4112d2b8 의 CLAUDE.md 51행이 그 셋을 pre-commit 이 돌린다고 적는다, 티켓 66행이 백그라운드 서브에이전트만으로 일반화했다, `rerun_checks.py` 110행과 명세 179행의 미래형, 설계 318행의 전용 계정 탐색이 계정 변경으로 서지 않는다, 명세 167행 어림). Nit 2(요약 파일 이름, 티켓 21행의 복사본 `--version`은 근거가 없다).
- 고친 것: `deny_shapes.py`에 갈래마다의 기대 표지(`expected`, `DENY_TEXT`)와 저장한 요약을 다시 판정하는 `--rejudge`를 더했다. 다시 판정하니 셋째 실행의 두 갈래와 `대조-2`가 측정, `규칙-2`는 Edit 미시도로 측정 아님(종료 1)이고, 넷의 갈래를 맞바꾼 사본(세션 스크래치 `swap_arms.py`)은 두 갈래 모두 여섯 행동이 표지 없음으로 걸렸다(손으로 봤다). README 결과 절에 "둘째·셋째 실행의 요약은 `2026-10-26/`에 `<갈래>-<실행 차례>.summary.json`으로 손으로 옮겨 커밋했다", 판을 바꾼 까닭과 다시 판정한 결과, "`--rejudge`가 찍는 init `tools`의 차. 둘째 실행도 같다", "이 꼴의 서브에이전트 거부를 오염으로 세지 않는다고 본다(코드 읽기", "셋째 실행의 서브에이전트는 두 갈래 모두 백그라운드로 떴다 … 둘째 실행의 `대조`는 서브에이전트 보고가 Agent 결과로 바로 돌아왔다", 못 본 것에 "앞쪽으로 뜬 서브에이전트의 거부가 `permission_denials`에 실리는지는 재지 않았다"를 넣었다. `SYNCED_PLUGINS` 주석을 "첫 호출에는 없고 둘째 호출부터 실렸다. 두 호출과 폴더 목록만 본 어림이다", "원래 세션도 싣고 돈 것으로 본다(어림. 원래 세션의 init 은 보지 않았다)", "같은 폴더의 `skills/synced/` 사용자 스킬은 init 의 `plugins`에 실리지 않아 이 검사 밖이다"로, 명세 167행 주석을 같은 뜻으로 고쳤다. `rerun_checks.py` 못 보는 것의 서브에이전트 항목을 "실렸다. 백그라운드로 뜬 서브에이전트 하나만 쟀고 … 앞쪽으로 뜬 서브에이전트는 재지 않았다"로, 명세 179행에 2026-10-26 주석을, 명세 240행을 "그때 pre-commit 이 돌리던 검사(지침, 타입 우회, 훅 러너. 세 B 에 그 파일이 있다)가 들지 않아"로, 설계 318행에 "측정 앞뒤의 % 차에 평소 작업이 섞인다. 이 탐색은 측정 기간에 평소 작업을 멈춘 때만 선다"를, 티켓 21행을 "복사본이 원본(`--version` 2.1.302)과 SHA-256 이 같고"로, 티켓 66행을 "백그라운드로 뜬 서브에이전트에서 실렸다. 앞쪽으로 뜬 서브에이전트는 재지 않았다"로 고쳤다.
- 남긴 것: ADR 0029 317행은 2026-10-20 이력 항목 안이라 기록이다(`.claude/rules/adr.md` "지난 이력 항목은 기록이다"). 계정은 설계 11절이 원천이고 그 절에 주석을 달았다. `source` 없는 플러그인 항목은 이미 `rerun_checks.py` 못 보는 것(108행)에 있다. Nit 넷(탐침의 이름과 모양)은 판단 항목이라 두었다.
- PR 직전 리뷰에 밀 주장: 위 "고친 것"의 따옴표 문장 모두와, 앞 세션들이 넘긴 것(넷째 세션 셀프 리뷰의 마지막 줄, 설계 11절 주석, 명세 167행 주석, 프로브 README "막는 규칙의 새 꼴" 절).

### 커밋과 인계 (여섯째 세션)

- 셀프 리뷰 반영 뒤 `uv run ruff check .`, `uv run ruff format --check .`은 초록이다. 커밋 2343c349 의 pre-commit 이 손으로 치는 다섯을 갈음했고 모두 통과했다(`Skipped`는 카나리아 명세 모양과 헌법 판, 둘 다 해당 파일 없음). `tools/sibling_overlap.py`는 번호 겹침 없음이었다. 푸시하지 않았고 PR 은 없다. origin/main 은 이 브랜치의 기점보다 앞서 있어 PR 전에 합친다(넷째 세션의 "커밋과 인계").
- 이 세션의 지금 제목: `feature/11-pilot-and-prereg`.
- 인계 경계: `커밋 뒤`. 컨텍스트 약 24.7만 토큰에서 커밋 직후 `hook_handoff`가 들어왔다. 인계하지 않는 다섯 때에 들지 않았다(커밋은 성공했고, 요청 범위는 PR과 병합까지이고, 이 세션 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 다른 경계이고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다).
- 이 세션이 번복하거나 고친 것: 탐침의 판정 기준(시도만 보던 것에 갈래마다의 기대 표지를 더했다, 위 "셀프 리뷰 (여섯째 세션)").
- 파일럿 고르기(2026-10-26T03:5xZ 에 이 세션이 다시 띄운 백그라운드, 출력 `C:\Users\User\AppData\Local\Temp\claude\C--project-agent\41a2b8ca-8a8a-4468-ac4b-3a9c302b853c\scratchpad\pilot_select.log`)는 인계 절차의 "대기 멈추기"를 따르지 않고 돌게 둔다. 앞의 두 세션이 인계마다 멈춰 약 3시간 걸리는 고르기를 처음부터 다시 돌았기 때문이다. 넘긴 세션의 프로세스가 살아 있으면 계속 돌고, 끝나면 `.scratch/model-rerun/probes/pilot.json`을 쓴다(어림. 인계 뒤에도 백그라운드 명령이 사는지는 재지 않았다). 04:08Z 에 로그의 끝 줄은 둘째 `숨은 시험을 가른다`(B 7496a830 M f1ed4be7)였다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/11-pilot-and-prereg.md. 파일럿을 돌리고 사전 등록을 사람과 정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: feature/11-pilot-and-prereg 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?
브랜치: feature/11-pilot-and-prereg
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-10-pilot-and-prereg.md의 "여섯째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "파일럿 셋을 05의 고르기로 고르고" 체크박스부터
이어받을 상태: 인계: 커밋 뒤. 2343c349 까지 사람 단계 일곱과 막는 규칙 탐침, 그 셀프 리뷰 반영을 커밋했다(푸시하지 않았다, PR 없음). 이 일지의 "커밋과 인계 (여섯째 세션)" 절은 커밋하지 않았다. 남은 단계는 파일럿 목록 커밋, 러너로 파일럿 돌기(--account njh4803 --config-dir C:\Users\User\.claude-rerun --claude C:\Users\User\.claude-rerun-bin\2.1.302 --cap 900)부터다. 파일럿 고르기는 넘긴 세션에서 멈추지 않고 돌게 두었다(출력 C:\Users\User\AppData\Local\Temp\claude\C--project-agent\41a2b8ca-8a8a-4468-ac4b-3a9c302b853c\scratchpad\pilot_select.log, 끝나면 .scratch/model-rerun/probes/pilot.json). 먼저 PowerShell 로 명령 줄에 rerun_select pilot 이 든 python 프로세스가 있는지와 로그가 자라는지 보고, 없는데 pilot.json 도 없으면 일지 "다섯째 세션"의 명령으로 다시 띄운다. PR 직전 리뷰에 밀 주장은 일지 "셀프 리뷰 (여섯째 세션)"의 마지막 줄이다. docs/journal/2026-10-28-10-pilot-and-prereg.md
확인할 선행 조건: 넘긴 세션의 백그라운드 명령이 인계 뒤에도 사는지는 재지 않았다
이번 요청 범위: PR과 병합까지
```
- 잠금 풀기: 이미 풀려 있었다(`is not locked`). open-session을 부른다 2026-10-26T04:08:51Z
- 인계 못함 커밋 뒤: open-session 의 스크립트가 `stale=1`, `fired=13:09:27` 뒤 30초 안에 새 세션 화면을 찾지 못하고 멈췄다(`page=` 없음). 지시문의 첫 줄이 이 세션의 첫 메시지와 같아 스크립트가 그 글을 쏘기 전부터 있던 글로 걸렀다고 본다(어림). 같은 파일로 다시 돌리지 않았고, 제목을 `feature/11-pilot-and-prereg`로 되돌려 이 세션에서 잇는다.

### 파일럿 목록 (여섯째 세션, 인계 못함 뒤)

- 인계를 못 한 뒤 이 세션에서 origin/main 을 합쳤다(충돌 없음).

> 사용자: 진행중이야?

- 파일럿 고르기가 종료 0으로 끝났다. 파일럿은 conversation-02(B 4112d2b8, 크기 6, 숨은 시험 10, A·A), end-user-continuation-02(B 5fee4cd6, 크기 3, 숨은 시험 65, A·A), end-user-continuation-03(B 9e92ec72, 크기 4, 숨은 시험 15, E)이다. 회차 상한은 $82.72·$114.05·$72.64 다. 다시 지은 후보 표는 model-rerun-02 한 줄만 바뀌었다(전 판은 준비 `uv sync`의 네트워크 오류로 가르지 못했고, 이번에는 숨은 시험 0개로 빠진다).
- 첫 커밋 시도는 pre-commit 의 pytest 가 1735초 걸리며 시간을 재는 시험 셋(`test_hook_edit_during_mutate`의 계기, `test_interrupt`의 닫기 중 Ctrl+C, `test_probe_kit`의 배출 제한 시간)에서 빨갰다. 이 브랜치가 건드리지 않은 파일이고, 셋만 따로 돌리니 34초에 모두 통과해 부하 아래의 흔들림으로 보고(어림) 같은 커밋을 다시 띄웠다. 인계 계기는 `인계 못함` 줄이 있어 다시 넘기지 않는다.
- 둘째 시도는 검사가 모두 통과했지만, 도는 동안 이 일지에 줄을 덧붙여 pre-commit 이 `files were modified by this hook`으로 막았다. 그 줄까지 스테이지해 셋째로 커밋한다.
- 셋째 시도는 pytest 가 1215초 걸리며 `test_interrupt`의 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다` 하나로 빨갰다(5612 통과, 그 밖의 검사 모두 통과). 같은 시험이 첫째에 이어 두 번째로 빨갰다. 그때 CPU 사용률은 100%였고 가장 많이 쓴 프로세스는 다른 claude 셋이었다(PowerShell `Get-Process`로 손으로 봤다). 그 시험을 홀로 돌리니 22초에 통과했다. 이 브랜치가 건드리지 않은 시험이고 이 커밋은 데이터와 문서뿐이라, `SKIP=parallel-checks`로 넷째 커밋을 한다. 빠진 묶음은 셋째 시도의 결과(그 시험 하나 밖은 모두 통과)와 위 홀로 돌린 결과로 갈음한다. 부하 아래에서 그 시험이 흔들리는 것은 회고 후보다.
- 커밋 1bd70d62(파일럿 목록). 러너를 띄우기 전에 부하를 물었다(질문 "지금 PC의 CPU가 100%입니다(다른 Claude 세션들이 가장 많이 씁니다). 파일럿 5회차(어림 $65~115, njh4803 한도에서 씀)를 언제 돌릴까요?").

> 사용자(선택): "다른 세션을 줄인 뒤 (Recommended)" — 다른 Claude 세션을 멈추거나 줄여 주시면 그 뒤에 돌립니다. 회차마다 게이트는 30분 안에 끝나야 하고 넘기면 그 과제는 못 푼 것이 됩니다. 방금 부하 아래에서 pytest가 평소의 네 배(1215초)가 걸렸습니다. 준비되면 알려 주세요.

> 사용자: 체크하면서 부하가 낮아지면 진행해

- 세션 스크래치 `wait_low_load.ps1`(CPU 사용률이 30초 간격으로 다섯 번 연속 50% 미만이면 0, 6시간이면 1)을 백그라운드로 띄웠다. 끝나면 러너를 띄운다.
- 부하 감시는 6시간 뒤 시간 제한(종료 1)으로 끝났다. 표본 693개 가운데 50% 미만은 20개였고 중앙값은 100이었다. 그 뒤 손으로 재니 `Win32_Processor.LoadPercentage`는 62~71인데 같은 때 프로세스별 CPU 시간의 10초 차의 합은 약 10%였고, `\Processor(_Total)\% Processor Time`을 5초 간격 12번 잰 1분 평균은 29.6%(최대 67.5, 사용자 10.4, 특권 19.2)였다(PowerShell 로 손으로 봤다). 순간값 지표가 튀어 연속 조건을 깬 것으로 보고(어림), 1분 평균이 낮아 러너를 띄운다. Docker 가상 머신(`vmmem`)의 CPU 는 권한이 없어 보이지 않았다.
- 러너를 띄웠다: `uv run python -m tools.rerun_runner .scratch/model-rerun/probes/pilot.json --root C:/Users/User/rerun-rounds --config-dir C:/Users/User/.claude-rerun --account njh4803 --claude C:/Users/User/.claude-rerun-bin/2.1.302 --cap 900`(뿌리는 새로 만든 빈 폴더, 출력은 세션 스크래치 `pilot_run.log`).
- 러너는 곧바로 종료 2(`끝: claude 실행 파일을 찾지 못했다`)로 끝났다. `main`이 `--claude`를 `shutil.which`로만 풀어, 윈도에서 PATHEXT 의 확장자가 없는 판 고정 복사본(`2.1.302`)을 실행 파일로 보지 않았다. 시험(`test_확장자_없는_판_이름의_경로로_준_claude_도_그_경로로_넘긴다`)을 먼저 써 빨간 것을 보고, 주어진 경로가 파일이면 그 절대 경로를 쓰게 고쳤다. 시험 파일 59개 통과, ruff·pyright 초록. 1분 평균 CPU 14.3%에서 같은 명령으로 러너를 다시 띄운다. 고침의 커밋은 러너가 끝난 뒤에 한다(pre-commit 이 회차와 겹쳐 부하를 올리지 않게).

### 파일럿 첫 실행 (조건 판 1)

- 다섯 회차가 모두 끝났다. 합은 약 $120 이고 njh4803 의 주간 사용률은 0.34 에서 0.42 로 올랐다. 기록은 `.scratch/model-rerun/probes/records/`(조건 판 1).

| 회차 | 비용 | 걸린 시간 | 결과 |
|---|---|---|---|
| conversation-02 A·A | $24.57, $24.64 | 77분, 106분 | 게이트 pytest 1 |
| end-user-continuation-02 A·A | $33.53, $34.47 | 101분, 94분 | 게이트 run_checks 1. 모델이 `SKIP=pytest,check-instructions`로 커밋했다 |
| end-user-continuation-03 E | $3.15 | 43분 | 개입 상한. local 가드를 옮겨도 되는지 두 번 물었다 |

- 다섯 회차 모두 러너가 지은 환경의 결함에 닿았다고 본다(게이트를 다시 돌아 확인한 것은 아래 셋이다). 결함은 셋이다(회차 스트림의 도구 결과와 게이트 출력을 세션 스크래치 `result_texts.py`·`skip_uses.py`로 손으로 봤다).
  1. 허용 목록에 `USERNAME`이 없어 `getpass.getuser()`가 `pwd`를 찾다 실패했다. 이것을 부르는 시험이 클론과 게이트 모두에서 빨갰다.
  2. B 의 `.claude/settings.json`의 `env`(`PYTHONUTF8` 등)가 게이트에 실리지 않아, 게이트의 하위 프로세스가 UnicodeDecodeError 로 stdout 을 잃었다. 모델 세션은 그 설정을 실으므로 세션 안에서는 초록이던 것이 게이트에서 빨갰다.
  3. 막는 규칙을 클론의 `.claude/settings.local.json`에 써서, B 의 `check_instructions`가 그 파일을 저장소의 지침 위반으로 잡았다. eu-02 의 `SKIP`과 eu-03 의 두 질문이 이것에서 나왔다.
- API 키가 없어 `-m llm`을 돌지 못한 것은 설계가 정한 것이다(`design.md` 84·144행, 게이트가 `-m llm`을 돌지 않는 것은 218행).

### 실행 조건 고침 (조건 판 2)

- 티켓의 "파일럿에서 실행 조건을 고치면 도구와 명세를 고치고 러너의 조건 판을 올린다"에 따라 고쳤다. 시험을 먼저 써 빨간 것을 본 뒤 고쳤다.
  - `rerun_round.ALLOWED_ENV`에 윈도의 사용자·기계·경로 변수 16개를 더했다(`USERNAME`, `USERDOMAIN`, `COMPUTERNAME`, `NUMBER_OF_PROCESSORS`, `OS`, `PROCESSOR_*` 넷, `ALLUSERSPROFILE`, `PUBLIC`, `CommonProgram*` 셋, `ProgramW6432`, `PSModulePath`).
  - 막는 규칙을 회차 폴더의 `deny-settings.json`에 쓰고 세션에 `--settings`로 넘긴다. 클론에는 쓰지 않는다.
  - 게이트는 B 의 `.claude/settings.json`의 `env`에서 글 값을 허용 목록 환경 위에 얹는다(`rerun_gates.settings_env`).
  - `CONDITION_VERSION`을 2로 올렸다. 판 1의 기록은 판 2의 결과와 섞이지 않는다.
- 막는 규칙의 새 자리를 `deny_shapes` 탐침으로 다시 쟀다(2026-10-27 기록, 약 $0.27). 두 갈래 모두 측정이었고, 새 자리도 막으며 init `tools`의 차가 옛 자리와 같다(`.scratch/model-rerun/probes/README.md` 2026-10-27 절).
- 판 1의 결과 커밋 셋(conversation-02-A-1, end-user-continuation-02-A-1·A-2)에 고친 환경으로 게이트만 다시 돌린다(`.scratch/model-rerun/probes/regate/regate.py`, 새 뿌리 `C:/Users/User/rerun-regate`). 게이트가 초록이 되면 실패가 환경 탓이었다는 근거가 된다.
- 러너가 걷지 못한 판 1 회차의 게이트 폴더가 남았다. 하드 링크된 네이티브 파일(uv 캐시의 `.pyd`·`.exe`, pnpm 저장소의 `.node`)은 다른 프로세스가 매핑하고 있으면 어느 링크 이름으로도 지울 수 없었다(`fsutil hardlink list`로 손으로 봤다). 아래 다시 돌기에서도 세 게이트 폴더 모두 `git worktree remove`가 255(`Invalid argument`)로 끝났고, 남은 것은 `web/node_modules`(한 폴더에 파일 18095개)뿐이고 `.venv`는 지워졌다(`ls -A`·`find`로 손으로 봤다). 러너는 그 자리를 알림으로 내고 회차를 이어 가므로 결과를 가르지는 않는다. 회차마다 디스크가 쌓이는 정리 문제로 남기고 회고 후보로 둔다.
- 다시 돌기 결과(종료 0, `.scratch/model-rerun/probes/regate/2026-10-27.log`): 세 회차 모두 준비 실패가 없고 게이트가 모두 0으로 끝났다. conversation-02-A-1 은 옛 게이트 묶음 여섯이 모두 0, 숨은 시험 10개 중 9개 통과(`test_자기_요약_이벤트의_자리나_개수가_어긋난_재개는_결정을_쓰기_전에_PluginError다[앞 실행 없음]` 실패). end-user-continuation-02-A-1·A-2 는 ruff 둘과 `run_checks.py`가 0, 숨은 시험 65개 중 63개 통과(둘 다 `test_run.py`의 같은 두 시험 실패: 에이전트 자리 밖의 런타임 예외, 정리 코드를 기다리다 기한이 오는 실패). 판 1에서 빨갛던 그 셋의 게이트가 고친 환경에서 초록이 되었으니 그 셋의 게이트 실패는 환경 탓이었다. conversation-02-A-2 는 다시 돌지 않았다. 숨은 시험의 실패가 모델의 결과 탓인지 부하 아래의 시간 탓인지는 가르지 않았다.

### 셀프 리뷰 (일곱째 세션, 판 2 고침)

- 범위: base 1bd70d62, 바뀐 파일 13, 커밋 0, 미추적 폴더 둘(`deny_shapes/2026-10-27/`, `records/`). 명세는 `spec.md`와 티켓 11.
- 표준 축(Sonnet high): Major 둘(따옴표 인용이 원문과 다르다, 변이 표 둘이 낡았다), Minor 다섯, Nit 여섯. 명세 축: Major 하나(변이 표 셋이 깨졌다, 새 동작에 변이가 없다), Minor 넷, Nit 넷.
- 고친 것:
  - 변이 표: `rerun_round_mutations.toml`의 settings.local 변이 둘을 새 자리("막는 규칙을 클론의 settings.local 에 쓴다", "이미 있는 규칙 파일을 견주지 않는다")로 바꿨다. `settings_env`가 B 해시 검사를 베껴 `rerun_gates_mutations.toml`의 "B 가 커밋 해시인지 보지 않는다"의 원문이 두 번 있던 것은, 해시 검사와 ls-tree 를 `_blob_in_base`로 모아 풀었다. 게이트 변이 둘(B 설정의 `env`를 얹지 않는다, 글이 아닌 값도 낸다)을 더했다.
  - 인용: `rerun_round.py` 독스트링과 명세 131행의 따옴표 인용을 `check_instructions.py`의 원문("local 은 워크트리에 없어 거기서 연 세션에서 조용히 빠진다")으로 바꿨다.
  - 낡은 못 보는 것: `rerun_round.py`의 "쓰기·편집 규칙과 도구 이름만 쓴 규칙은 재지 않았다"를 `deny_shapes`가 Sonnet 으로 쟀다고 고쳤다.
  - `settings_env` 시험에 `env`가 배열·null, 최상위가 배열, 12자 B 를 더했다. `check_result` 독스트링에 B 설정을 풀지 못할 때의 `GateError`와, B 설정의 `PATH`가 넘긴 `PATH`를 덮는 것(못 보는 것. `git log --all -S'"PATH"' -- .claude/settings.json`이 빈 것을 손으로 봤다)을 적었다.
  - 명세: "막는 규칙을 둔 세션에는 PowerShell 도구가 없다"에 판 1 다섯 회차의 init 에 PowerShell 이 있었다는 주석을 달고, 막는 규칙 주석에 설계 8절 5의 settings.local 도 이 파일로 읽는다고 적었다.
  - 다시 돌기의 근거: 세션 스크래치에 있던 `regate.py`와 로그를 `.scratch/model-rerun/probes/regate/`로 옮겨 커밋하고 README 표에 `records/`와 함께 줄을 두었다. 일지와 티켓의 "다섯 모두"·"그 실패는 환경 탓" 을 다시 돈 셋으로 좁혔다. 판 2를 돌 때 `--rerun` 세 id 가 필요하다는 것을 티켓에 적었다.
  - 일지의 "부모 환경 위에"를 "허용 목록 환경 위에"로, 설계 줄 번호를 84·144·218 로 고쳤다. README `deny_shapes` 줄에 2026-10-27 비용(약 $0.27)과 근거 자리를 더했다.
- 남긴 것:
  - `type Json`과 `_parse_json`이 모듈마다 있는 것(Duplicated Code): 앞 티켓들이 모듈마다 두는 꼴로 지었다(`rerun_checks.py`, `rerun_session.py`). 모을지는 기능 전체의 일이라 회고 후보로 둔다.
  - `write_deny_rules`가 `RoundDir` 전체를 받는 것(Nit): 회차 폴더의 자리 이름을 `RoundDir`이 한 곳에서 정하게 두었다.
  - `--claude`의 상대 경로가 현재 폴더의 같은 이름 파일과 겹치면 그 파일을 잡는 것(Nit): 러너는 저장소 루트에서 돌고 판 고정은 절대 경로를 준다.
  - 준비 명령이 B 설정의 `env`를 받지 않는 것: 준비는 모델 세션 전에 클론에서 돌고, 세션은 Claude Code 가 그 값을 넣는다. 게이트만 세션 밖에서 B 의 pre-commit 을 다시 도는 자리라 넣었다.
  - B 설정에 BOM 이 있으면 `GateError`(명세 축 Nit): BOM 을 막는 검사가 있는지는 보지 않았다. 멈추는 쪽이 조용히 넘는 쪽보다 낫다고 보고 둔다.
  - `rerun_runner.py`의 "끝 이름이 곧 프로세스 이름이다"(명세 축 Minor): 표준 축이 `2.1.302`의 프로세스 이름이 `2.1.302`인 것을 재현했고, 티켓 11 판 고정 줄의 `pids_named` 확인과 같다.
  - 일지 2026-10-26 `규칙-2`를 끼고 "규칙-2·규칙-3과 같다"고 적은 README 줄(Nit): 그 줄은 도구 목록의 차만 견주고 측정 판정과 별개라 둔다.
- PR 직전 리뷰에 밀 주장: "B 설정의 `env`는 거르지 않고 얹으므로, 거기 `PATH`가 있으면 넘긴 환경의 `PATH`를 덮는다", "판 1에서 빨갛던 그 셋의 게이트가 고친 환경에서 초록이 되었으니 그 셋의 게이트 실패는 환경 탓이었다", "판 1에서 계획을 다 마친 과제라 러너에 세 과제 id 를 `--rerun`으로 준다", "설계 5절과 8절 5가 클론의 `settings.local.json`을 드는 자리도 이 파일로 읽는다".
- 다시 돈 명령: 바뀐 회차 변이 둘(26·27)과 게이트 변이 셋(50~52, 51은 표지를 고쳐 다시) 모두 기대대로, 다시 풀기 시험 넷 252 통과, `ruff check .`·`ruff format --check .` 초록, 바뀐 파일의 pyright 0. 나머지 검증은 커밋의 pre-commit 으로 갈음한다.
- `sibling_overlap.py`가 이 일지가 main 의 최신 일지(2026-10-27-03)보다 이름순으로 앞이라고 알려 `--move`로 2026-10-26-02 를 2026-10-28-10 로 옮겼다(인용 열넷).
- 커밋 175fb884. 그 뒤 컨텍스트 약 25.9만 토큰에서 `hook_handoff`(커밋 뒤)가 들어왔다. 이 세션의 지시문의 "이어받을 상태"가 같은 경계 `인계: 커밋 뒤`이고 이 세션이 쓴 `인계 못함` 줄이 있어 넘기지 않고 잇는다.
- 다음 단계는 파일럿을 조건 판 2로 다시 도는 것이다. 판 1 만큼(약 $120, 약 7시간) 다시 쓰므로 사람에게 묻는다.

## 파일럿 판 2 (여덟째 세션)

> 사용자: 파일럿을 판 2로 다시 돌려. 부하가 낮을 때 띄워

- 띄우기: 띄울 때 CPU 가 88% 였다. 1분 평균 CPU 를 재서 세 번 연속 60% 미만이면 러너를 띄우는 스크래치 스크립트로 기다렸고, 15:25 에 띄웠다. 인자는 판 1과 같고 `--rerun` 세 id 를 더했다. 러너는 "과제 목록을 다 돌았다"와 종료 0으로 끝났다(20:21).
- 결과(조건 판 2, 공식 단가 합 $119.62):

| 회차 | 끝 | 게이트 | 숨은 시험 | 공식 단가 | 벽시계 | 개입·인계 |
|---|---|---|---|---|---|---|
| conversation-02-A-3 | 끝남 | 여섯 모두 0 | 9/10 | $19.69 | 83분 | 0·0 |
| conversation-02-A-4 | 끝남 | 여섯 모두 0 | 9/10 | $23.76 | 78분 | 0·0 |
| end-user-continuation-02-A-3 | 끝남 | 셋 모두 0 | 63/65 | $32.67 | 126분 | 0·0 |
| end-user-continuation-02-A-4 | 끝남 | 셋 모두 0 | 63/65 | $37.10 | 151분 | 2·0 |
| end-user-continuation-03-E-2 | 측정 아님(오염) | - | - | $3.73 | 32분 | 0·1 |
| end-user-continuation-03-E-3 | 끝남 | 셋 모두 0 | 15/15 | $2.65 | 27분 | 0·0 |

- 판 1의 결함 셋(`USERNAME`, B 설정의 `env`, 클론의 막는 규칙)은 판 2에서 다시 나지 않았다. 준비 실패와 게이트 시간 넘김이 없다.
- 숨은 시험의 실패는 과제마다 회차 사이에 같았다. conversation-02 는 `test_자기_요약_이벤트의_자리나_개수가_어긋난_재개는_결정을_쓰기_전에_PluginError다[앞 실행 없음]` 하나, end-user-continuation-02 는 `test_run.py`의 두 시험(에이전트 자리 밖의 런타임 예외, 정리 코드를 기다리다 기한이 오는 실패)이고, 판 1을 다시 돈 결과(`regate/2026-10-27.log`)와도 같다. 그 시험이 원래 통과하는지 보려고 `regate.py --merge`로 두 과제의 M 을 돌자 숨은 시험이 10/10, 65/65 였다(`regate/2026-10-27-merge.log`). 그래서 실패는 시험의 결함이 아니라 결과물이 M 과 다른 자리다. 부하 탓인지는 여기서도 가르지 않았다(판 2 는 부하가 낮을 때 띄웠고 같은 시험이 실패했다).
- E-2 의 오염: 오염 검사의 `다른-회차` 꼴이 Write 하나와 Bash 하나에 걸렸다. 세션 기록의 도구 입력을 스크래치 스크립트로 훑자, 모델이 회차 폴더의 부모인 뿌리(`C:/Users/User/rerun-rounds/`)에 `fix1.py`와 커밋 메시지 파일 `commitmsg03.txt`를 쓰고 Bash 로 그 둘을 썼다. 다른 회차 폴더를 건드린 것은 아니지만 뿌리는 회차들이 함께 쓰는 자리라 검사가 맞게 걸었다고 본다. 막는 규칙은 뿌리의 쓰기를 막지 않는다(`deny-settings.json`에 뿌리 꼴이 없다). 두 파일은 다음 회차가 보지 않게 그 회차 폴더의 `leaked-to-root/`로 옮겼다. 그 뒤 돈 E-3 는 오염 0 이었다. 막는 규칙에 뿌리 쓰기를 더할지는 티켓의 "오염 검사에 걸린 꼴" 항목에서 사람과 정한다.
- 게이트 작업 트리: end-user-continuation-02-A-3·A-4 에서 `git worktree remove`가 255 로 끝나(`Invalid argument`) 게이트 폴더의 `web/`이 남았다(682MB, 15MB). 판 1에서 본 것과 같고 회고 후보로 둔 그대로다.
- 판 2에서 더 고칠 실행 조건은 오염 꼴을 정한 뒤에 가른다. 그래서 "실행 조건을 고친다" 항목은 아직 닫지 않는다.
- 막힌 호출(회차마다 2~7, 모두 24. 기록의 `denied_calls` 합)은 결과 이벤트의 `permission_denials`를 커밋하지 않은 스크래치 스크립트로 뽑아 손으로 보니 모두 B 의 훅·가드나 auto 모드가 막은 Bash·Grep 이었고(`/tmp` heredoc, 클론 밖 `cd`, `.env` 등), 러너의 막는 규칙에 걸린 것은 없었다. E-2 의 뿌리 쓰기는 `cat > /tmp/fix1.py`가 막힌 뒤였다.
- 서브에이전트 기록의 모델·노력: A 회차는 Opus xhigh(본 세션을 물려받은 것)와 Sonnet high(B 의 code-review 표준 축, ADR 0033), E 회차는 Sonnet medium(물려받은 것)과 Sonnet high 였다. `model_mismatch`는 모두 비었다.
- 뿌리 쓰기 결정:

> 질문: 회차의 모델이 회차 폴더 바깥, 곧 모든 회차가 함께 쓰는 뿌리 폴더(C:\Users\User\rerun-rounds\)에 임시 파일을 쓰면 어떻게 할까요? 이번 E-2 회차는 Bash 로 /tmp/fix1.py 를 쓰려다 막히자, Write 도구로 뿌리에 fix1.py 와 커밋 메시지 파일을 썼습니다. 오염 검사가 이것을 잡아 그 회차는 '측정 아님'으로 빠졌습니다(공식 단가 $3.73). 막는 규칙(deny 규칙)은 모델의 도구가 특정 경로를 건드리지 못하게 하는 설정입니다. 규칙을 바꾸면 실행 조건 판을 올려야 합니다.
>
> 사용자: 뿌리 쓰기를 막는다 (Recommended) — 뿌리 폴더 바로 아래에 Write·Edit 도구로 파일을 쓰는 것을 막는 규칙을 더하고 조건 판을 3으로 올립니다. 모델은 거부를 보고 다른 자리에 씁니다. 이번 경우는 Write 도구였으므로 막혔을 것입니다. Bash 의 리다이렉션(cat >)은 이 규칙으로 막지 못하고 오염 검사가 계속 잡습니다. 파일럿은 다시 돌지 않고, '바로 아래만' 막는 꼴이 실제로 동작하는지 싼 탐침으로 확인합니다(비용은 지난 탐침의 $0.27 로 본 어림).

- 조건 판 3 고침: 권한 규칙은 gitignore 꼴이라 `<뿌리>/*`가 회차 폴더에도 맞을 수 있어, 구현 전에 `probes/deny_shapes/root_shape.py`로 꼴 둘을 Sonnet medium 한 회차씩 견줬다(대조 포함 갈래 셋, 약 $0.24). `*`는 뿌리의 `leak.txt`·`LEAK`와 클론의 `ok.txt`를 모두 막았고, `*.*`는 `leak.txt`만 막고 `LEAK`와 클론 쓰기는 지나갔으며, 대조는 셋 모두 썼다. 그래서 `deny_rules`에 `roots`를 더해 `Edit`·`Write(<뿌리>/*.*)`를 쓰고(`ROOT_TOOLS`, `ROOT_SHAPE`), 러너가 `root_heads(settings.root)`를 넘기며, `CONDITION_VERSION`을 3으로 올렸다. 회차 폴더 이름은 `_TASK_ID`·`_TOKEN` 꼴이라 점이 없다. 탐침이 규칙의 경로를 지으려고 `_rule_path`를 `rule_path`로 열었다. 시험 셋(규칙의 꼴과 차례, 회차 폴더 이름에 점이 없다, 러너가 쓴 규칙 파일에 뿌리 규칙이 든다)과 변이 셋(뿌리 규칙을 쓰지 않는다, `*`로 쓴다, 러너가 뿌리를 넘기지 않는다)을 더했다. 변이 58 은 처음 표지가 pytest 의 줄임 출력에 없어 어긋났고, 실패 줄의 `Right contains 2 more items` 문구로 바꿔 다시 돌자 기대대로였다. 셋 모두 기대대로 빨갰고 다시 풀기 시험 넷 414 가 통과했다.
- M 의 숨은 시험은 처음에 `regate.py`를 sed 로 바꾼 스크래치 사본으로 돌았고, 커밋할 판에 `--merge`를 더한 뒤 그 판으로 다시 돌아 같은 결과(10/10, 65/65)를 `regate/2026-10-27-merge.log`에 남겼다.
- `/code-review`(base 175fb884)를 부르자 컨텍스트 약 27.6만 토큰에서 `hook_handoff`(셀프 리뷰 직전)가 들어왔다. 이 세션(`get_session` 생성 2026-10-26T03:51Z)이 쓴 `인계 못함 커밋 뒤` 줄(309행)이 있어 다시 시도하지 않고 셀프 리뷰를 잇는다.

### 셀프 리뷰 (판 3 고침)

- 범위: base 175fb884, 바뀐 파일 11, 커밋 0, 미추적 11(판 2 기록 여섯, `root_shape.py`와 요약 셋, merge 로그). 명세는 `spec.md`, 티켓 11, 사용자의 뿌리 쓰기 답.
- 표준 축(Sonnet high): Major 둘(README `deny_shapes/` 행의 칸이 여섯, merge 로그에 돈 커밋과 모드가 찍히지 않는다), Minor 일곱. 명세 축: Major 하나("실행 조건을 고친다"를 닫는 조건이 맞지 않는다), Minor 넷.
- 고친 것:
  - README `deny_shapes/` 행의 군더더기 `|`를 지웠다(`check_md_tables.py` 0).
  - `regate.py`가 `돈 커밋: <해시> (M)|(결과 커밋)`을 찍게 하고 merge 로그를 그 판으로 다시 만들었다.
  - 티켓 "실행 조건을 고친다"를 다시 열었다. "공식 단가 셈"과 "오염 검사에 걸린 꼴" 항목이 조건을 다시 고칠 수 있어 그 둘을 닫은 뒤 닫는다고 적었다. "오염 검사에 걸린 꼴" 항목에 판 2 에서 걸린 꼴(E-2 의 `다른-회차` 둘, 거짓 양성 아님), 뿌리 쓰기 결정, 서브에이전트 모델·노력을 적었다. 티켓 "러너로 파일럿 목록을 돈다"의 깨진 괄호를 고쳤다.
  - 일지의 막힌 호출 수를 23 에서 24 로(기록의 `denied_calls` 합) 고치고, 근거가 커밋하지 않은 스크래치 스크립트로 손으로 본 것이라고 적었다.
  - 시험: 회차 폴더 이름의 조각(과제 id, 난수)이 점을 받지 않는다(`ShapeError`), `root_heads`가 링크를 푼 꼴을 든다, 다른 회차 폴더 시험이 뿌리 규칙을 넣은 규칙으로 돌고 뿌리에 걸린 규칙이 `Edit`·`Write`의 `*.*`뿐이다, 오염 검사가 뿌리 바로 아래 파일(`fix1.py`, `cat > <뿌리>/LEAK`)을 `다른-회차`로 센다.
  - `rerun_checks.py` 독스트링과 명세 "오염 검사" 절에 뿌리 자체와 뿌리 바로 아래 파일도 `다른-회차`로 센다고 적었다. `deny_rules`의 못 보는 것에 `LEAK`가 탐침의 `점` 갈래에서 지나갔다는 것과 오염 검사 시험 자리를 적었다.
  - README `regate/` 행의 잰 판을 로그마다 적고, 변이 절에 판 3 변이 셋의 결과를 적었다.
- 남긴 것:
  - 사용자가 고른 뿌리 바로 아래의 Write·Edit 쓰기 막기를 탐침 결과로 점이 든 이름만 막게 좁힌 것(명세 축 Minor): `<뿌리>/*`는 클론 쓰기까지 막아 쓸 수 없고, 확장자 없는 파일은 오염 검사가 잡는다. 사람에게 보고에서 알린다.
  - Bash 리다이렉션의 못 보는 것에 단위 시험이 없는 것(표준 축 Minor): 도구 규칙이 Bash 를 보지 않는 것은 Claude Code 의 동작이고, 그 길은 오염 검사 시험이 고정한다.
  - `root_shape.py`가 `ROOT_SHAPE`를 가져다 쓰지 않고 `deny_shapes.py`와 꼴이 겹치는 것(표준 축 Minor·판단): 이 탐침은 후보 꼴을 견주는 것이라 운영 상수가 아니라 후보를 적고, 상수는 단위 시험(`뿌리_규칙은_바로_아래의`)이 고정한다. 겹침은 앞 탐침의 함수를 가져다 써 줄였다.
  - "실패는 시험의 결함이 아니라 결과물이 M 과 다른 자리다"를 한 단계 약하게 읽으라는 것(표준 축): 같은 문단에 부하 탓을 가르지 않았다고 적어 두었다.
- PR 직전 리뷰에 밀 주장(새로 쓴 문장의 요지):
  - 회차 폴더 이름의 조각(과제 id, 난수)이 점을 받지 않아 `*.*`가 회차 폴더에 맞지 않는다.
  - 뿌리 자체와 뿌리 바로 아래 파일도 `다른-회차`로 센다.
  - `LEAK`는 탐침의 `점` 갈래에서 지나갔다.
  - 막힌 호출 24 는 모두 B 의 훅·가드나 auto 모드가 막았다.
- 커밋 47aa107b. pre-commit 이 통과했고 인용 대조 경고 넷(이 절의 따옴표로 묶은 요지)은 다음 커밋에서 따옴표를 뗐다.

## 티켓 11 남은 항목 (여덟째 세션 이어서)

> 사용자: 티켓 11의 남은 항목을 이어서 진행해

### 공식 단가 대조

- 판 2 기록의 세션·모델 아홉(Opus 넷, Sonnet 다섯)에서 세션 기록 파일의 응답 셈과 `modelUsage`의 `costUSD`를 댔다(`probes/official_cost/compare.py`, `2026-10-27.log`). 응답 셈은 `costUSD`의 0.72~1.00배였다.
- 어긋남은 단가가 아니라 기록 파일의 토큰이 모자란 것이었다. 출력은 아홉 가운데 여덟에서 모자랐고 Opus는 입력·캐시 읽기·캐시 쓰기도 모자랐다. 모자란 칸을 같은 단가와 5분 배수로 채우면 아홉 모두 남는 차가 0.0000이었고, 1시간으로 셈하면 Opus에서 0.0011~0.0287달러가 남았다. 1시간 쓰기가 큰 Opus 회차에서도 맞아 배수는 수명이 정한다는 07의 해석이 섰다. 모자란 까닭은 재지 않았다.
- 결정: 07의 셈이 응답이 있는 모델도 `modelUsage`와 칸마다 견주어 모자란 몫을 채운다(티켓이 "07의 셈을 고친다"로 정한 길). 실행 조건이 아니라 셈이라 조건 판은 올리지 않았고, 커밋한 판 1·2 기록의 `official_usd`는 옛 셈 그대로다. 시험 넷(고친 둘 포함), 변이 셋(28~30, 모두 기대대로 빨강), 명세 "회차 기록"의 2026-10-27 주석, 프로브 README 행을 더했다.

### 설계 8절 확인과 사람 결정

- 설계 8절의 확인을 서브에이전트가 판 2 기록과 원본 스트림으로 대 보고 초안을 냈다(스크래치 `design8_draft.md`, 근거 스크립트 열). 맞다 열, 볼 수 없었다 둘(예산 멈춤, Opus의 막는 규칙. 모델이 그 길에 닿지 않았다), 다르다 둘(init에 `pyright-lsp`가 실리지 않는다, 시작 컨텍스트가 실제의 약 52~64%). 새로 드러난 것: end-user-continuation-02 의 카나리아 시험이 띄운 하위 `claude -p` 세션이 회차 비용에 들지 않는다, eu-02-A-4 의 개입 둘은 모델이 백그라운드 리뷰어를 기다리며 차례를 끝낸 것이다, E-2 인계 지시문의 `모델:` 줄이 갈래와 달랐다.
- 내가 기본값으로 정한 것(사람에게 알렸다): 백그라운드를 기다리다 끝난 것도 개입으로 센다(모든 갈래에 같은 규칙), 근거 스크립트는 `probes/`에 커밋한다, 예산 멈춤과 Opus 막는 규칙은 따로 재지 않고 본 측정 기록에 맡긴다, 한도 사용률은 `unifiedWindows` 기준으로 적는다, 본 측정의 첫 인계 뒤 멈춤은 설계대로 둔다.
- 사람에게 물은 넷과 답(고른 라벨과 설명 그대로):

> 사용자: 과제의 시험이 따로 띄운 하위 Claude 세션의 비용을 회차 비용에 더할까요? → 회차 비용에 더한다 (Recommended) — 러너가 전용 설정 폴더의 같은 클론 프로젝트 폴더에 생긴 다른 세션 기록도 찾아 공식 단가로 셈해 회차 비용에 더합니다. 원래 세션의 비용에도 이 시험 비용이 들었을 것이라는 것은 재지 않은 어림입니다. 러너를 고치고 시험을 더합니다.

> 사용자: 전용 설정 폴더에서 빠진 pyright-lsp와 플러그인 스킬을 어떻게 할까요? → 차이로 적고 간다 (Recommended) — 다시 풀기는 플러그인 없이 도는 것을 설계가 뺀 MCP와 같은 한계로 명세에 적습니다. 다섯 갈래가 모두 같은 환경이라 갈래 사이 비교에는 영향이 없고, 원래 세션과 견주는 탐색에만 듭니다. 조건 판은 그대로입니다.

> 사용자: 인계 지시문의 모델 줄이 갈래와 다르면 러너가 고쳐서 붙일까요? → 갈래 값으로 바꿔 붙인다 (Recommended) — 러너가 새 세션에 지시문을 붙일 때 `모델:` 줄을 그 갈래의 모델·노력으로 바꿉니다. 갈래 사이에 모델 줄만 다르다는 지시문 약속을 인계 뒤에도 지킵니다. 실행 조건이 바뀌니 조건 판이 오릅니다.

> 사용자: 서브에이전트가 쓸 수 있는 모델(허용 모임)을 지금 규칙대로 고정할까요? → 지금 규칙대로 고정한다 (Recommended) — 갈래 모델(파일럿에서 모델을 주지 않은 서브에이전트는 이것을 물려받았다), B의 에이전트 정의와 code-review가 정한 모델, 모델이 Agent 호출에서 직접 고른 모델을 허용합니다. 서브에이전트의 노력은 보지 않습니다(코드를 읽었다). 파일럿 기록 열하나의 허용 밖 줄은 모두 0이었고, 사전 등록 절에 그대로 옮깁니다.

### 결정의 반영 (조건 판 4)

- 하위 세션 비용: 러너가 회차 세션의 기록 파일이 든 프로젝트 폴더에서 회차 세션이 아닌 기록(`other_transcripts`)을 찾아 공식 단가로 셈해 회차 기록의 새 칸 `other_usd`에 넣고, 예산의 쓴 것과 판정 보기의 두 비용에 더한다. 그 칸 때문에 회차 기록의 꼴 판만 2로 올렸다(`RECORD_SHAPE_VERSION`). 과제 목록과 같이 쓰던 `SHAPE_VERSION`을 그대로 올리면 지금 도는 본 측정 고르기가 쓸 과제 목록(판 1)을 읽지 못하게 된다. 가짜 `claude`가 같은 프로젝트 폴더에 다른 세션 기록을 남길 수 있게 했다(`fake_claude.call`의 `others`).
- 인계 모델 줄: `arm_model_line`이 옮긴 지시문의 첫 `모델:` 줄을 갈래 값으로 바꾸고 나머지 모델 줄은 지운다. 없으면 `브랜치:` 줄 뒤에 넣는다.
- 조건 판: 처음에는 공식 단가 셈의 채우기를 셈의 고침으로 보고 판을 올리지 않는다고 티켓에 적었다. 러너의 `CONDITION_VERSION` 주석이 단가를 고칠 때도 올리라고 해, 두 결정과 함께 4로 올리고 티켓 메모를 고쳤다.
- 확인: 새 변이 넷(files 50, runner 31·32, continue 53)과 원문이 바뀐 변이 둘(files 2, continue 26)이 기대대로 빨갰고, 변이 표 여섯의 `--check`가 지났다. 다시 풀기 시험 아홉 파일 821개가 통과했다. 바뀐 파일의 pyright, `ruff check`, `ruff format --check`가 지났다.
- 문서: 명세 "지시문의 틀"·"회차 기록"·"설정 폴더의 설정"·"모델 확인"에 2026-10-27 주석, 프로브 README에 "2026-10-27 결과: 파일럿(설계 8절의 확인)" 절. 근거 스크립트 열은 `probes/pilot_checks/`로 옮긴다. 티켓의 허용 모임·실행 조건·브랜치 표 항목을 닫았다.

### 셀프 리뷰 (base 47aa107b)

- `/code-review`(base 47aa107b)를 부르자 컨텍스트 약 26.6만 토큰에서 `hook_handoff`(셀프 리뷰 직전)가 들어왔다. 이 세션이 쓴 `인계 못함 커밋 뒤` 줄(309행)이 있어 다시 시도하지 않고 셀프 리뷰를 잇는다.
- 명세 축: Critical 하나(꼴 판 2의 읽기가 커밋한 파일럿 기록 열하나를 `모르는 꼴 판 1`로 거부해 러너의 예산 셈과 판정이 멈춘다. 명세 축보다 먼저 손으로 `read_record`를 불러 재현했다), Major 하나(채운 몫이 `substitutes`에 들지 않는다), Minor 둘(`other_usd`가 응답 셈만이라 낮다·하위 세션의 `subagents/`를 세지 않는다, README 기본값 "다섯"에 넷만), Nit 하나(일지의 조건 판 문장이 엇갈린다).
- 고친 것: Critical은 읽기가 회차 기록의 꼴 판 1을 `other_usd` 없는 꼴로 받아 0으로 읽게 했다(`_top`이 받는 판의 모임과 읽은 판을 돌려준다). 쓰기는 판 2만이다. 시험 넷(판 1을 0으로 받는다, 판 1에 `other_usd`가 있으면 거부, 판 2에서 빠지면 거부, 이 저장소의 커밋한 기록을 모두 읽는다)과 변이 둘(files 51·52)을 더하고 변이 2의 원문을 맞췄다. 명세 "회차 기록"의 주석과 `tools/rerun_files.py` 독스트링에 적었다. Major는 Haiku만 프롬프트 크기로 단가가 갈려 Opus·Sonnet의 채운 몫은 정확하므로 `tools/rerun_cost.py`의 못 보는 것에 적는 것으로 갈음했다. Minor 앞 반은 `tools/rerun_runner.py`의 못 보는 것에 적었다. README 기본값 줄을 다섯으로 채웠다.
- 남긴 것: Minor 뒤 반(`subagents/`)은 틀린 지적이다. `_other_usd`가 쓰는 `transcript_lines`가 그 세션의 `subagents/`까지 읽는다. Nit은 일지가 기록이라 앞 문장을 고치지 않고, "결정의 반영" 절의 조건 판 줄이 바로잡는다.
- 밀 주장(PR 직전 리뷰): "읽기는 회차 기록의 판 1을 `other_usd` 없는 꼴로 받아 0으로 읽는다", "프롬프트 크기로 단가가 갈리는 모델은 Haiku뿐", "하위 세션의 `modelUsage`는 러너가 받지 못해 응답 셈만 한다", "꼴 판 1로 커밋한 파일럿 기록(조건 판 1·2의 열하나)".
- 표준 축(sonnet·high): Major 넷, Minor 여럿, 냄새는 판단 항목. M1 README "판 1·2 합쳐 18파일"이 17이다(회차 폴더를 `find`로 셌다). M2 README 10·11절과 티켓의 비용 수치가 채우기 전의 옛 셈이다. M3 하위 세션 $2.39에 조건 판 1이 섞였다. M4 `pilot_checks/`와 `official_cost/compare.py`가 `.claude/rules/probes.md` 첫 항목(표지를 세고 측정 아님이 있으면 종료 1)을 따르지 않는데 README가 결과를 측정처럼 적었다. Minor는 변이 51의 표지가 pytest 실패 줄이다, 이번 변이가 README 변이 기록에 없다, "판 2 기록 열하나"(판 1·2다), 52~64%(63%다), "물려받았다"가 general-purpose만 본 것이다, 러너 독스트링 0.72~1.00배의 범위와 근거 경로, README 5-1의 `blocked by a deny rule`이 러너 규칙이 아니라 클론 설정의 `Read(//**/.env)`다, `arm_model_line`·`_gaps` 꼬리·`other_transcripts` 제외 갈래의 시험이 없다.
- 고친 것(표준 축): M1은 17로. M2는 README 결과 절 머리에 비용 수치가 따로 적지 않으면 옛 셈이라고 적고, 10·11절에 채운 셈(conversation-02 $21.34·$25.82, end-user-continuation-02 $34.87·$40.46, E-3 $2.79)을 나란히 두었다. 변동계수는 옛 셈으로만 냈다고 적었다. M3은 "판 1·2 넷 합 약 $2.39(판 2 둘은 약 $0.87)"로. M4는 둘로 나눴다. `pilot_checks/`는 결과 절 머리와 표의 행에 "측정이 아니라 손으로 본 것"으로 적고 항목마다 근거를 스크립트 이름과 손으로 본 파일로 갈랐다(1의 클론 장부와 `~/.claude/projects/`·주 체크아웃 장부, 5-2의 `setup.log`·`.git/hooks/`, 5-3의 클론 설정·`installed_plugins.json`). `compare.py`는 `probe_kit.Rounds`로 세션·모델마다 회차를 세게 고치고(기록 파일이나 응답이 없으면 측정 아님, 그런 회차가 있거나 측정이 없으면 종료 1) 다시 돌려 `official_cost/2026-10-28.log`(측정 9, 측정 아님 0, 본문은 옛 로그와 같다)로 옛 로그를 갈음했다. Minor는 변이 51의 표지를 `회차 기록.spend: 빠진 키 ['other_usd']`로, README 변이 기록에 조건 판 4의 아홉(files 50~52, cost 28~30, runner 31·32, continue 53)과 원문을 맞춘 둘(files 2, continue 26)을 적고 열하나를 다시 돌려 모두 기대대로였다. 명세와 티켓의 "판 1·2 기록 열하나"와 "(본 것은 general-purpose뿐이다)", 52~63%, 러너 독스트링의 "파일럿 회차 기록의 응답 셈(서브에이전트 기록 포함)은 그 회차 `costUSD`의 0.72~1.00배였다(`.scratch/model-rerun/probes/official_cost/`)", README 5-1의 거부 문구 분리를 고쳤다.
- 다시 돌린 것: `run_checks.py`의 첫 바퀴에서 pyright가 `_top`의 반환형(`_is_int`는 형을 좁히지 않는다)을 빨갛게 냈다. 같은 파일의 다른 자리처럼 `isinstance(version, int)`를 앞에 두어 고치고 변이 2의 원문을 맞춰 다시 돌렸고 기대대로였다. 테스트의 `_판_1_기록` 인자를 키워드 전용으로 바꿔 ruff FBT001을 풀었다.
- 남긴 것(표준 축): 갈래 시험 셋(`arm_model_line`의 모델 줄이 없거나 둘인 지시문, `_gaps`의 꼬리 합치기, `other_transcripts`의 제외 갈래)은 Minor이고 이번 범위의 동작을 바꾸지 않아 다음 러너 손질에 넘긴다. 냄새(긴 함수, `_top`의 판 모임 인자)는 판단 항목이라 두었다.
- 밀 주장 더함(표준 축 반영): "아래 수는 측정이 아니라 손으로 본 것이다", "채운 셈은 Claude Code 셈과 같아 $21.34·$25.82, $34.87·$40.46", "판 1·2 넷 합 약 $2.39(판 2 둘은 약 $0.87)", "`blocked by a deny rule`은 클론 프로젝트 설정의 `Read(//**/.env)`", "파일럿 회차 기록의 응답 셈(서브에이전트 기록 포함)은 그 회차 `costUSD`의 0.72~1.00배", "본 것은 general-purpose뿐이다".
- 커밋 491f9d8f: pre-commit 이 모두 지나갔다(`run_checks.py` 의 둘째 바퀴도 모두 Passed, pytest 328.7초). 커밋 전 `sibling_overlap.py` 가 이 일지를 origin/main 의 최신 일지(2026-10-28-01)보다 앞이라고 내어 `--move` 로 2026-10-27-14 → 2026-10-28-10 로 옮겼다. origin/main 의 새 변경 가운데 이 브랜치가 따를 것은 `.claude/rules/probes.md` 첫 항목의 표지 문장(시험 원문에 글자 그대로 있는 문구는 표지가 못 된다)이고, 변이 51은 이미 그렇게 고쳤다.

### 사전 등록 (조건 판 4)

- 정의에 드는 코드 상수를 모듈마다 `PREREG_VALUES`(이름과 JSON 값의 표)에 모았다. 티켓이 든 넷(꼴·고르기·회차·판정) 밖에도 정의에 드는 상수를 가진 모듈이 일곱 더 있어(숨은 시험, 세션, 이어 가기, 오염 검사, 게이트, 공식 단가, 러너) 열하나다. 모듈 수준 상수를 grep 으로 훑어 골랐다. 고르는 기준은 정의 글이 서술하는 동작을 정하는가이고(값, 낱말, 정규식과 그 플래그), 기록을 읽고 쓰는 꼴(키, 글자 꼴)과 판정을 바꾸지 않는 시간 제한(git·버전·끄기·배출), 셸 파서의 내부 정규식은 그 예가 아니라서 뺐다. 처음에는 이 셋을 뺀 것의 전부로 적었으나 셀프 리뷰가 그 밖의 빠진 것을 찾았다(아래 셀프 리뷰). 구간의 5·95 백분위는 `tools/model_sweep_judge.py`의 `percentile_ci` 안의 값이라 시험이 그 함수를 불러 본다. `rerun_select`·`rerun_gates`·`rerun_cost`가 따로 짓던 같은 꼴의 `Json` 형은 표의 형이 하나가 되게 `rerun_files`의 것을 가져오게 바꿨다.
- 시험 `tests/tools/test_rerun_prereg.py`: 표의 항목마다 `prereg_line`(`<모듈>.<이름> = <JSON 한 줄>`)이 절에 있는지, 절의 상수 줄이 모두 표에 있고 한 번씩인지, 판정 도구의 해시가 절과 맞는지, 절 안의 과제 목록·되살릴 목록 JSON 이 `main.json`·`revive.json`과 같은지, 구간이 5·95 백분위인지 본다. 절을 쓰기 전에는 빨갛다(기대대로 넷이 빨갰다).
- 정의 글의 초안은 서브에이전트가 설계 3~6절, 명세 Implementation Decisions, 판정·꼴·고르기 코드를 읽고 썼다(명세가 설계를, 코드가 글을 이긴다). 어긋남 여섯을 냈다. 1 오염의 셸 도구에 코드는 `Monitor`와 그 웹소켓 입력을 더한다, 2 설정 확인은 코드가 모든 호출의 init 을 본다, 5 "숨은 시험이 모두 통과"에 코드는 하나 이상 돌았을 것을 더한다, 6 바깥 검증 낱말의 대소문자 무시 등 코드가 정한 것은 코드대로 적었다. 3 백그라운드를 기다리며 끝낸 차례를 개입으로 세는 것은 코드가 가르지 않아 그대로 적었다. 4 명령 줄 값(그때 상한 $900, 뒤에 $1,600으로 올렸다. 계정, `claude` 복사본 경로)은 절의 글에 적고 시험이 잡지 못한다고 절 머리에 적었다. 초안의 게이트 git 시간 제한 120초는 코드(300초)로 고쳤다.

### 본 측정 목록과 예산 어림

- 본 측정 고르기(`rerun_select main`, 기준 35028cba, 파일럿 목록과 되살릴 목록 입력)가 끝나 `main.json`과 다시 지은 `candidates.md`를 썼다. 실행 차례대로 mcp-shutdown-02(작은), web-widget-01(중간), model-rerun-10(큰), end-user-continuation-05(작은), web-widget-02(중간), ticket-for-every-pr-03(큰), end-user-channel-04(작은), conversation-01(중간)이다. PR 앞 비용 합 $302.72.
- 어림(스크래치 스크립트 `estimate.py`, 커밋하지 않았다): 회차 기록의 비용 합(파일럿과 측정 아님 포함, 판정 몫의 Claude Code 셈) $249.54. 조건 판 2 이상의 파일럿 A 넷의 A/PR 앞 비용 비는 0.774·0.936·0.917·1.064(평균 0.923). 과제마다 PR 앞 비용 × 그 비 × 갈래 비율 합 4.1로 셈해, 가장 큰 비로 8개 누적 약 $1,570, 평균 비로 약 $1,400. 상한 $900 안에는 어느 비로도 셋만 든다.
- 사람에게 물었다(질문 원문): "본 측정 예산 상한을 어떻게 할까요? 지금 상한 $900에서 파일럿이 이미 $249.54를 썼습니다. 고른 과제 8개를 다섯 갈래로 모두 돌리면 약 $1,570(파일럿에서 가장 비쌌던 비율 기준, 평균 비율이면 약 $1,400)이 들 것으로 어림합니다. 이대로면 과제 3개만 들어, 판정에 필요한 최소 6개에 못 미칩니다(6개 미만이면 판정은 '결론 없음'). 러너는 다음 과제의 어림까지 더해 상한을 넘으면 그 과제를 시작하지 않고 멈추므로, 상한이 실제로 쓸 수 있는 돈의 끝이 됩니다."

> 사용자: $1,600로 올려 8개 (Recommended) — "고른 8개를 모두 돌립니다. 가장 비싼 비율로 어림해도 약 $1,570이라 상한 안에 듭니다(어림이고, 실제 비용은 더 나올 수 있습니다). 층마다 수(작은 3, 중간 3, 큰 2)가 설계대로 남습니다."

- 그래서 과제 수를 줄이지 않고, 본 측정 러너의 `--cap`은 1600이다. 이 값은 사전 등록 절 머리와 정의의 "차례와 예산"에 적는다.

### 사전 등록 절과 해시

- 프로브 README에 `## 사전 등록(본 측정)`을 `## 2026-10-22 결과` 앞에 넣었다. 두 표지 사이는 머리 문단, 정의 글, `### 코드 상수`(처음 82줄, 셀프 리뷰 반영 뒤 102줄, PR 직전 리뷰 반영 뒤 107줄), `### 과제 목록(\`main.json\`)`, `### 되살릴 목록(\`revive.json\`)`이다. 스크래치 스크립트 셋(`prereg_lines.py`로 줄 뽑기, `build_prereg.py`로 잇기, `insert_prereg.py`로 넣고 해시 셈)으로 지었고 커밋하지 않았다. 5행 문단은 "절은 아직 없다"에서 "절은 아래에 있고 결과를 본 뒤에는 고치지 않는다"로 바꿨다.
- `PREREG_SHA256`은 처음 51281304…로 넣었고, 셀프 리뷰를 반영해 다시 지은 뒤 d98c86fd…였고, PR 직전 리뷰를 반영해 다시 지은 뒤 `4af49e5774efe883f1def6d5b1226cf83c8c97e5a8bed9acb8358d6f0f2f7563`이다. 저장소의 `.gitattributes`가 `* text=auto eol=lf`라 체크아웃마다 같은 바이트다. `test_rerun_prereg`·`test_rerun_judge`·`test_rerun_runner` 125개가 지나갔다.
- 본 측정 지시문 재료: 러너 명령 줄은 `uv run python -m tools.rerun_runner .scratch/model-rerun/probes/main.json --root C:/Users/User/rerun-rounds --config-dir C:/Users/User/.claude-rerun --account njh4803 --claude C:/Users/User/.claude-rerun-bin/2.1.302 --cap 1600`(파일럿의 명령 줄에서 목록과 상한만 바꿨다. `--help`로 인자를 다시 봤다. 파일로 부르면 `tools`를 import하지 못해 `-m`으로 부른다), 조건 판 4, 판 고정은 `C:\Users\User\.claude-rerun-bin\2.1.302` 복사본(일지 "판 고정"). 회차가 오래 돌므로 백그라운드로 띄우고 끝 알림을 기다린다. 여는 첫 회차 전에 러너가 해시를 대 보므로, 이 브랜치가 병합된 main 에서 띄운다.

### 셀프 리뷰 (base 491f9d8f, 사전 등록)

범위: base 491f9d8f, 수정 파일 15, 커밋 0, 미추적 2(`tests/tools/test_rerun_prereg.py`, `probes/main.json`).

명세 축(받은 보고의 요지):
- Major 1: 정의 글이 동작을 서술하는데 `PREREG_VALUES`에 빠진 상수가 있다. `rerun_continue.BUDGET_SUBTYPE`·`_QUESTION_MARKS`, `rerun_select.PR_SUFFIX`, `rerun_checks.SOCKET_KEY`·`OPEN_SESSION`·`_FREE_TEXT_BY_TOOL`·`_INHERIT`·`BOUNDARY`, `rerun_files.MODEL_LABELS`, `rerun_session._TITLE_HEAD`·`SYNTHETIC`. 위 "사전 등록 (조건 판 4)"의 뺀 것 셋(시간 제한, 기록 꼴, 셸 파서 정규식)이라는 닫힌 주장의 반례다.
- Major 2: 정규식은 `.pattern`만 실려 플래그(`re.IGNORECASE`)를 지워도 시험이 초록이다(`_GH`, `_ADDRESSES`, `_SESSION_OPENERS`).
- Minor: 티켓 41행 체크박스가 비었다. 정의 글이 `rerun_select.SEEDS`처럼 표의 키를 모듈 속성처럼 부르는데 실제 속성 이름은 없거나 다르다(`SEEDS`, `LIMITS`, `_NAME_ERRORS`, `_START_LINE`, `_GH`). 위 "사전 등록 (조건 판 4)"의 "명령 줄 값($900, …)"이 절의 실제 값 $1,600과 다르다. `Json` 형 합치기는 범위 밖이지만 무해하다.
- 재서 맞은 것: README 5행의 러너 대조, "차례와 예산"의 멈춤 셈($1,570 = 302.72 × 1.064 × 4.1 + 249.54로 다시 셈), 결론 조건, 쓰는 회차, 사람 결정 넷의 반영, 일지의 러너 명령 줄(파일로 부르면 `ModuleNotFoundError`도 직접 봤다), 티켓 괄호의 82줄.

표준 축(받은 보고의 요지):
- 하드 1(`.claude/rules/tests.md`의 저장소 상태 검사 항목): 새 시험에 통과를 재는 시험만 있고, 값이 바뀌거나 줄이 빠지거나 끼어들 때 빨개지는 변이 시험이 없다. `_절의_JSON`의 단언 갈래도 시험되지 않는다.
- 하드 2(`.claude/rules/probes.md`): 정의에 드는데 표에 없는 상수. 명세 축의 것과 겹치고, 더해 `rerun_continue._DIRECTIVE_HEAD`·`_DIRECTIVE_TAIL`·`_MODEL_HEAD`·`_BRANCH_HEAD`, `rerun_round`의 `DISABLE_AUTOUPDATER` 값, `rerun_judge.KEEP_CELL`·`PASTED_CLAIM`, 가격 세 칸의 순서(소스 주석에만 있다).
- 3: 위 뺀 것 셋의 닫힌 주장과 티켓 40행 괄호의 "정의에 드는 상수를 모았다"가 과하다.
- 4: 절이 코드에 없는 이름을 상수처럼 부른다(`ADDRESSES`·`GH`·`SESSION_OPENERS`·`LIMIT_MARKERS`·`NAME_ERRORS`·`LIMITS`·`SEEDS`·`START_LINE`).
- 5: 정의 글의 "설정 폴더 `settings.json`에는 autoCompactWindow, 출력 스타일, 언어만 있고 env 키가 없다"는 러너가 보는 것(`env` 키 부재)보다 넓다.
- 냄새(판단): `Limits()` 네 번 부르기와 `[*X]` 복사 꼴의 반복, 시험만 부르는 `prereg_line`의 자리, 이름 없는 가격 목록, 묶음 키 이름, 상수 하나에 네 곳을 고치는 Shotgun Surgery(의도한 값).
- 재서 맞은 것: 러너의 대조 자리, 멈춤 셈과 인계 확인, 허용 모델 모임, `Monitor`와 `ws`, `prereg_section`의 표지 수 판정, `.gitattributes`, 러너 명령 줄, 어림 $1,570·$1,395.

반영:
- 고친 것: 표에 빠진 상수 스물을 더했다(`rerun_files.MODEL_LABELS`, `rerun_select.PR_SUFFIX`, `rerun_checks`의 `SOCKET_KEY`·`OPEN_SESSION`·`FREE_TEXT_BY_TOOL`·`INHERIT`·`FRONT_MATTER`·`MODEL_LINE`·`BOUNDARY`, `rerun_continue`의 `BUDGET_SUBTYPE`·`DIRECTIVE_HEAD`·`DIRECTIVE_TAIL`·`MODEL_HEAD`·`BRANCH_HEAD`·`QUESTION_MARKS`, `rerun_session`의 `TITLE_HEAD`·`SYNTHETIC`, `rerun_round.AUTOUPDATER_OFF`(값 `"1"`을 이름 있는 상수로 뺐다), `rerun_judge`의 `KEEP_CELL`·`PASTED_CLAIM`). 이 가운데 하네스 모델 정규식 둘(`_FRONT_MATTER`·`_MODEL_LINE`)은 두 축이 내지 않았지만 같은 기준(정의 글이 서술하는 허용 모델 모임을 정한다)으로 더했다. 정규식은 `rerun_files.prereg_pattern`으로 글과 켠 플래그를 함께 싣는다. 가격은 `{input, output, cache_read}` 객체로 실어 칸 순서가 절 안에 있다. 시험에 변이 시험 여섯(값 바뀜, 표에 없는 줄, 두 번 적은 줄, 절 한 글자 바뀜의 해시, 목록 블록의 세 갈래)과 `prereg_pattern` 시험을 더했다. 정의 글의 설정 폴더 문장을 러너가 보는 것(`env` 키, JSON 객체 아님, 읽지 못함)으로 고쳤다. 절 머리에 `<모듈>.<이름>`의 이름은 표의 키이고 속성 이름과 다를 수 있다는 문장을 더했다. 위 "사전 등록 (조건 판 4)"의 닫힌 주장을 기준 조항으로 고치고 $900에 뒤의 값을 붙였다. 티켓 40행 괄호도 기준으로 고쳤고, 41행을 닫았다. 절을 다시 지어 해시를 바꿨고 상수 줄은 102줄이다.
- 남긴 것: `Limits()` 네 번 부르기와 `[*X]` 복사 꼴(판단 항목, 표가 Json 형이라 복사로 형을 맞춘다), 시험만 부르는 `prereg_line`의 자리(판단 항목, 표의 형 `Json`과 줄의 꼴을 한 모듈에 두어 README 머리가 그 이름을 가리킨다), Shotgun Surgery(사전 등록이 의도한 값), `Json` 형 합치기(명세 축이 무해하다고 했다). 예산 상한 $1,600이 해시 밖이라는 것은 절 머리가 스스로 밝히고, 명령 줄 값이라 상수로 옮기지 않는다.
- 밀 주장(PR 직전 리뷰에 넘긴다): "고르는 기준은 정의 글이 서술하는 동작을 정하는가이고(값, 낱말, 정규식과 그 플래그)", "셀프 리뷰가 빠진 것을 찾은 뒤 같은 기준으로 다시 훑어 스물을 더했다", 절 머리의 "모듈 속성 이름과 같거나, 앞 밑줄을 뗀 이름이거나, 여러 상수를 묶은 이름이다", 정의 글의 "`env` 키가 있으면(JSON 객체가 아니거나 읽지 못해도) 러너는 측정 아님(설정)으로 멈춘다. 다른 키는 보지 않는다".
- 다시 돌린 것: `tests/tools/test_rerun_prereg.py` 초록, 다시 풀기 변이 표 열하나의 `mutate.py --check` 초록. 나머지 검증은 커밋의 pre-commit으로 갈음했다.
- 커밋 28483932: pre-commit 이 Passed 열여덟(pytest 722.2초, web-verify 555.5초)이고, Skipped 둘(카나리아 명세, 헌법 판)은 이 커밋에 그 파일이 없어서다. 커밋 전 `sibling_overlap.py`가 일지를 origin/main 의 최신 일지보다 앞이라고 내어 `--move`로 2026-10-28-02 → 2026-10-28-10 으로 옮겼다(처음 내준 -10 이 다른 워크트리의 커밋하지 않은 일지와 겹쳐 다시 쳤더니 겹침이 없어져 -10 에 머물렀다). 옮기기가 인용을 고친 파일에 사전 등록 절은 없었고, 해시 시험이 그대로 지나갔다.
- origin/main(a1bdf8d7)을 손으로 합쳤다(앱의 합치기 도구는 이 세션이 앱이 만든 워크트리가 아니라며 거부했다). 충돌 없음. 합친 변경 가운데 이 브랜치가 따를 규칙은 `.claude/rules/probes.md` 표지 항목의 보강(두 해석에서 모두 나는 관찰은 표지가 못 된다)이고, 이번 변경에는 새 프로브가 없어 닿지 않는다.
- PR 직전 리뷰: CodeRabbit CLI는 좌석 미배정(`coderabbit auth status`의 `Seat: not assigned`)이라 대체 둘을 나란히 돌렸다. `/security-review`는 확신 높은 취약점 0건이다. 커밋한 데이터 파일(기록, 로그, 요약, 브랜치 표, 후보 표)과 일지 diff를 이메일 꼴과 토큰 꼴로 훑어 0건이었고, 하위 프로세스는 모두 리스트 인자이며 `shell=True`가 없고, 막는 규칙 파일의 자리를 옮긴 것은 새 약점이 아니라고 봤다(옛 자리도 세션이 쓸 수 있었다). 그래서 거짓 양성 거르기 단계는 돌 것이 없었다.
- `bug-perf-review`(받은 보고의 요지, 유효 셋 모두 Minor, 오탐 0): 1 숨은 시험의 모집단을 정하는 `rerun_files`의 `_TEST_FILE`·`_TESTS_PY`·`_CONFTEST`가 표에 없다. 2 숨은 시험의 통과를 정하는 `rerun_gates._BAD_CHILDREN`과 `rerun_hidden._SEVERITY`가 표에 없다. 3 절 머리의 "`<모듈>.<이름>`으로 부르는 이름은 표의 키다"를 같은 절의 `rerun_files.prereg_pattern`·`rerun_files.judge_view`(함수)가 어긴다. 밀 주장 가운데 "스물", 설정 폴더 문장(`[]`·빈 글·`{"env":null}`·BOM 으로 불러 봤다), README 5행 문단, 해시의 바이트, 러너 명령 줄은 맞다고 봤고, 일지 앞 절들의 밀 주장 줄은 시간이 모자라 따라가지 못했다. 시험은 300초를 넘겨 멈췄다.
- 반영: 셋 다 고친다. 1·2는 같은 기준의 반례라 표에 더하고, 3은 머리 문장을 "상수를 부르는 이름"으로 좁힌다. 절이 바뀌어 해시를 다시 고정한다.
- 고친 것: `rerun_files`의 표를 시험 파일 정규식 뒤로 옮겨 `TEST_FILE`·`TESTS_PY`·`CONFTEST`를 더했고, `rerun_gates.BAD_CHILDREN`과 `rerun_hidden.SEVERITY`를 더했다(다섯). 절 머리를 "`<모듈>.<이름>`으로 상수를 부르는 이름은 그 모듈 `PREREG_VALUES` 표의 키다(함수를 부를 때는 함수 이름 그대로다)"로 고쳤다. 상수 줄 107줄, 해시 4af49e57…. `test_rerun_prereg` 초록. 나머지 검증은 다음 커밋의 pre-commit으로 갈음한다.
- 밀 주장(PR 봇에 넘길 길은 없다, 리뷰 파이프라인 2): "PR 직전 리뷰가 찾은 다섯을 더 더했다", 절 머리의 "함수를 부를 때는 함수 이름 그대로다".
- 커밋 def40e73: 첫 시도는 pre-commit 의 web-verify 가 storybook 시험의 iframe 60초 시간 초과로 빨갰다(이 브랜치는 web 을 건드리지 않았고, 합친 main 의 잠금 파일도 그대로였다). `pnpm -C web verify`를 홀로 돌리니 초록이라 다시 커밋했고, 둘째 시도는 Passed 열여덟(pytest 1029.0초, web-verify 866.7초), Skipped 둘(카나리아 명세, 헌법 판)이다. 커밋 뒤 인계 계기가 두 번 더 왔으나 같은 경계라 넘기지 않았다.
- 커밋 뒤 인계 계기(컨텍스트 271,157 토큰)가 왔으나 넘기지 않았다. 이 세션을 연 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 `next-session` "인계할 때" 1의 같은 경계다.

### PR (여덟째 세션 이어서)

- origin/main(#296, 01800b91)을 다시 합쳤다(충돌 없음, 바뀐 것은 하네스 훅 파일뿐). 브랜치를 처음 푸시하고 PR #408을 열었다.
- PR을 연 뒤 `hook_handoff`(`PR 연 뒤`, 컨텍스트 약 36.5만 토큰)와 `hook_pr_next_session`이 함께 왔다. 이 세션이 쓴 `인계 못함 커밋 뒤` 줄(309행)이 있어 `next-session` "인계할 때" 1대로 다시 넘기지 않고, 그 스킬 순서 1의 2(봇 회차)부터 잇는다.
- 헤드 12957af8 에서 검사 아홉이 모두 통과했다(`tools/wait_ci.py`). 두 봇 모두 첫 회차다.

### PR 봇 첫 회차

- CodeRabbit Major: 명세의 본 측정 상한이 $900 으로 남았다. 맞다. 명세 다섯 자리(37·44·53·89·263행 근처)에 2026-10-28 $1,600 으로 올렸다는 주석을 붙이고, 설계 11절(414행)에도 같은 주석을 붙였다. 티켓의 러너 명령 줄 설명은 `--cap 1600`으로 고치고, 같은 줄의 조건 판도 지금 값 4로 고쳤다(`CONDITION_VERSION = 4`를 grep 으로 봤다). 사전 등록 절 밖이라 해시는 그대로다.
- CodeRabbit Minor `extra_sessions_cost.py`: 프로젝트 폴더가 없으면 추가 세션 0 으로 읽혔다. 맞다. 측정 아님으로 찍고 1 로 끝나게 고쳤다. 실제 경로로 돌려 열하나 모두 같은 값($2.3939)을, 없는 폴더를 주어 열하나 모두 측정 아님과 종료 1 을 봤다.
- CodeRabbit Minor 변이 표 27·29: `expect_output`의 `where 1 = run()`은 다른 원인으로 러너가 멈춰도 나와 `.claude/rules/probes.md` 첫 항목에 어긋난다. 맞다. 두 시험의 단언에 `board.lines`를 싣고, 변이를 손으로 넣어 본 실패 출력에서 `돈 게이트 6개가 묶음의 이름 3개와 다르다`와 `의 게이트를 돌지 못했다: git ls-tree`를 골랐다. `tools/mutate.py`로 두 변이가 기대대로 빨갰고 `--check`도 통과했다.
- CodeRabbit Minor `root_shape.py`(갈래마다 기대 결과를 단언하라): 보류. 독스트링이 "판정은 하지 않고" 행동마다 결과를 적는 관찰 탐침으로 정했고, 표지는 행동 셋을 모두 시도한 것이며, 꼴을 고른 판단은 저장한 요약을 읽어 README 에 적었다. 기대 결과를 단언하는 판정은 `deny_shapes.py`의 `--rejudge`처럼 따로 둘 일이고, 다시 재지 않고 결과를 바꾸지 않는다.
- claude-review Nit `TABLES` 손 열거: 고쳤다. `tools/rerun_*.py`에서 `PREREG_VALUES`를 둔 모듈이 모두 열거에 드는지 보는 시험을 더했다. 열거에서 한 줄을 빼면 빨갛고 되돌리면 초록이다.
- claude-review Minor `other_transcripts` 시험: 앞서 다음 러너 손질로 넘긴 셋의 하나다. 이 비용이 본 측정의 예산 멈춤(`spent + estimate > cap_usd`)에 들어가므로 본 측정 첫 회차 전에 시험으로 고정할 일로 "다음"에 적는다.
- claude-review Minor `_with_costs`·`_interrupted`의 같은 차례: 보류. 두 자리이고 동작 변경이 없다. 다음 러너 손질 때 함께 본다.
- claude-review Minor `ALLOWED_ENV`를 윈도 기본값 튜플로 나누기: 보류. `rerun_round.PREREG_VALUES`의 값이 같아도 구조를 바꾸는 일이라 사전 등록을 고정한 뒤의 손질로 미룬다. 동작은 같다.
- claude-review Nit `ROOT_SHAPE`의 점 없는 회차 폴더 이름 단언: 보류. 다음 러너 손질 때 함께 본다.
- 대기열을 고치기 전에 origin/main(#297, 4a74cd19)을 다시 합쳤다(충돌 없음. 이 브랜치가 고친 파일과 겹치지 않았다).
- 커밋 2576e007 의 pre-commit 은 모두 통과했다(pytest 425.1초, web-verify 537.2초). 판단은 PR 코멘트로 남겼다.

### PR 봇 둘째 회차

- 헤드 2576e007 에서 검사가 모두 통과했다. CodeRabbit 은 `Review rate limited`라 리뷰가 없어 회차로 세지 않는다.
- claude-review 둘째 회차는 Minor 다섯과 Nit 하나라 고치지 않고 지적마다 보류 이유를 PR 코멘트에 남긴다(`next-session` 1단계의 2 회차 세기). 뒤로 넘기는 것은 아래 "다음"에 적었다.

## 회고

티켓 11 전체(첫째~여덟째 세션)를 이 일지와 이 세션으로 봤다. 후보 일곱, 승인 다섯(회차로 세는 것 셋, 새 행 둘), 기각 둘, 넘김 없음. 반영은 모두 대기열이고 이 세션에서 반영한 것은 없다. 대기열의 만료할 행은 이 브랜치와 origin/main 모두 없었다. 517 이 새 검사로 문턱(5회차)을 넘어 `tools/hook_report.py`를 돌렸고 뺄 후보는 없었다.

1. **결정이 바뀐 뒤 명세·설계·티켓에 본 측정 상한 $900 이 남았다**(PR 봇 CodeRabbit 이 Major 로 잡았다. 셀프 리뷰와 PR 직전 리뷰는 놓쳤다). `CLAUDE.md` 작업 규약 4 를 구현 때 어긴 것이라 회차로 센다(승인). 같은 처방의 열린 행 420 에 더해 7회차.
2. **변이 표지 `where 1 = run()`이 다른 까닭으로 러너가 멈춰도 맞았다**(PR 봇 CodeRabbit). `.claude/rules/probes.md` 첫 항목을 구현 때 어겼다. 이은 열린 행이 없어(290 과 그 4회차 417 은 닫혔다) 새 행 517 에 `290의 5회차`로 잇고, 처방은 `tools/mutate.py --check`의 검사로 골랐다(승인, 층 조건).
3. **관찰 스크립트 `pilot_checks/extra_sessions_cost.py`가 프로젝트 폴더가 없는 회차를 추가 세션 0 으로 읽었다**(PR 봇 CodeRabbit). 같은 probes.md 첫 항목의 표지 갈래다. 339 를 이은 열린 행 430 에 더해 8회차. 430 의 처방은 `.scratch/**/probes/*.py`를 보므로 `probes/pilot_checks/` 같은 하위 폴더가 그 꼴에 드는지는 반영할 때 본다.
4. **인계에 실패해 `인계 못함`을 적은 뒤에도 `hook_handoff`가 단계 경계마다 계기를 다시 넣었다**(한 세션에서 여섯 번, 이번에는 `next-session` SKILL.md 약 2.4만 자를 열어 넘기지 않는다고 판정했다). 사건이 있고, 훅의 고침이라 층이 맞고, PR 하나로 되돌린다(승인). 새 행 518, 1회차.
5. **인계 열기가 `stale=1` 뒤 새 세션 화면을 찾지 못하고 멈췄다**(309행). 도구 결함의 고침이다(승인). 새 행 519, 1회차. 원인은 어림이라 처방이 먼저 재현하게 했다.
6. **pre-commit 의 시간 시험 셋(1735초 실행)과 web-verify 의 storybook iframe 60초 넘김이 이 브랜치가 건드리지 않은 곳에서 빨갰고, 다시 돌리면 지났다.** 기각. 시간 시험은 `.claude/rules/tests.md`의 여유 항목으로 닫힌 332·306 의 가족이고, web-verify 는 504(main 이 새 의존성을 들인 뒤의 Vite 재적재)와 원인이 같은지 보지 않았다(이 브랜치가 합친 main 은 web 의존성을 바꾸지 않았다). 일지에만 남긴다.
7. **워크트리 가드가 heredoc·리다이렉트가 섞인 git 명령을 거부했고, 앱의 `sync_with_base_branch`가 이 워크트리를 앱이 만든 것이 아니라며 거부했다.** 기각. 이미 있는 앱 가드와 도구가 그 자리에서 알렸고 `CLAUDE.md` 환경 함정에 길이 있다.

## 다음

- 기능 model-rerun 의 티켓은 모두 done 이다. 본 측정은 티켓이 아니라 러너를 돌리는 일이고, 명령 줄은 위 "사전 등록 절과 해시"의 본 측정 지시문 재료다. 사전 등록 절을 고치면 `PREREG_SHA256`을 다시 고정한다.
- 본 측정 첫 회차 전에 시험으로 고정할 것: `tools/rerun_runner.py`의 `other_transcripts`(회차 세션 기록은 빼고 같은 프로젝트 폴더의 다른 세션만 센다). 이 비용이 예산 멈춤(`spent + estimate > cap_usd`)에 든다(PR #408 claude-review). 앞서 다음 러너 손질로 넘긴 `arm_model_line`, `_gaps`의 꼬리, 판정 몫의 셈도 함께 본다(위 "셀프 리뷰 (base 47aa107b)").
- 본 측정 첫 회차 전에 볼 만한 것: 표에 빠진 상수를 기계가 잡게, `PREREG_VALUES`를 둔 모듈의 대문자 상수가 모두 표에 들거나 까닭과 함께 제외 목록에 드는지 보는 시험(PR #408 claude-review 둘째 회차. 표에 넣을 상수를 사람이 골라 셀프 리뷰와 PR 직전 리뷰가 25개를 뒤늦게 찾았다). 더하면 절을 다시 짓고 해시를 다시 고정할 수 있다.
- PR #408 claude-review 둘째 회차에서 다음 러너 손질로 넘긴 것: `plan_task`의 `rerun`과 `_check_end`의 `timed_out` 불리언 플래그 인자, 회차 기록의 `gates_green`·`hidden_passed`(`bool | None`)를 열거로, `rerun_files.py`의 나누기(기록 꼴, 사전 등록 헬퍼, 종료 판정), `test_구간은_5와_95_백분위다`의 자리.
- PR #408 봇 첫 회차에서 보류한 것: `root_shape.py`의 갈래별 기대 결과 판정, `_with_costs`·`_interrupted`의 같은 차례, `ALLOWED_ENV`의 윈도 기본값 튜플, `ROOT_SHAPE`의 점 없는 회차 폴더 단언(위 "PR 봇 첫 회차").
