# 2026-10-26 (02) 파일럿과 사전 등록

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
읽을 것: docs/journal/2026-10-26-02-pilot-and-prereg.md 전체(커밋하지 않은 "낱말에 걸린 후보의 문맥"과 "인계 (첫째)" 절 포함), 티켓 11의 "사람과 정한다"
이어받을 상태: 인계: 커밋 뒤. 969a694f 까지 커밋했고 PR 은 없다. "사람과 정한다"의 첫 체크박스(브랜치 표 다시 모으기)는 db3e90db 로 마쳤고, 둘째(후보 표 다시 짓기)는 969a694f 로 지었으나 사람에게 아직 보이지 않았다. 다음은 그 표를 일지의 "낱말에 걸린 후보의 문맥" 절대로 사람에게 장면으로 보이고, 셋째(되살릴 목록)와 넷째(후보가 열둘에 모자라니 길 고르기)를 차례로 묻는 것이다. 새로 찾은 것: 다시 모은 브랜치 표는 사람의 기본 설정 폴더에서 세션 기록 일부가 지워져 옛 표보다 응답이 약 4,200개 적고 PR 앞 비용이 줄어든 브랜치가 29개다(일지 "브랜치 표"). 이것도 사람에게 함께 보인다. 커밋하지 않은 일지 두 절은 다음 커밋에 싣는다. docs/journal/2026-10-26-02-pilot-and-prereg.md
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
읽을 것: docs/journal/2026-10-26-02-pilot-and-prereg.md의 "셋째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "사람과 정한다" 다섯째 체크박스부터
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(B 에 tools/run_checks.py 가 없는 과제의 옛 게이트 묶음: tools/rerun_files.py·rerun_gates.py·rerun_runner.py 와 그 시험, 변이 여섯, 명세 "게이트와 숨은 시험" 주석, 티켓 넷째 체크박스, 일지)이 워크트리에 있고 셀프 리뷰(/code-review, 기준 HEAD d5ab0c15)부터 한다. ruff 둘은 초록이고 변이 여섯은 표지까지 기대대로였다. run_checks.py 는 인계로 멈춰 결과가 없다. 리뷰를 반영해 커밋한 뒤 다음은 다섯째 체크박스(전용 설정 폴더의 njh6803 로그인과 설정 옮기기)를 사람에게 묻는 것이다. PR 은 없다. docs/journal/2026-10-26-02-pilot-and-prereg.md
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

- 리뷰를 반영한 뒤 `uv run ruff check .`, `uv run ruff format --check .`(러너 한 파일을 포맷한 뒤)은 초록이다. `tools/sibling_overlap.py`가 이 일지(옛 2026-10-24-11)가 origin/main 의 최신 일지보다 이름순으로 앞이라고 해 `--move`로 2026-10-26-02 로 옮겼다. 커밋 1dd42c39 의 pre-commit 이 손으로 치는 다섯을 갈음했고 모두 통과했다(`Skipped`는 카나리아 명세 모양과 헌법 판, 둘 다 해당 파일 없음). origin/main 은 이 브랜치의 기점보다 앞서 있고(`git diff --name-only HEAD...origin/main`에 `tools/mutate.py`, `CLAUDE.md`, `docs/constitution/operations.md` 등), 이 브랜치가 이름으로 든 `tools/rerun_*` 와는 겹치지 않는다. PR 전에 main 을 합친다.
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
읽을 것: docs/journal/2026-10-26-02-pilot-and-prereg.md의 "넷째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "사람과 정한다" 다섯째 체크박스부터
이어받을 상태: 인계: 커밋 뒤. 1dd42c39 까지 넷째 체크박스(옛 게이트 묶음)와 그 셀프 리뷰 반영을 커밋했다(푸시하지 않았다, PR 없음). 남은 단계는 다섯째 체크박스(전용 설정 폴더의 njh6803 로그인과 설정 옮기기)를 사람에게 묻는 것부터다. PR 직전 리뷰에 밀 주장은 일지 "셀프 리뷰 (넷째 세션)"의 마지막 줄에 있다. 이 일지의 "커밋과 인계 (넷째 세션)" 절은 커밋하지 않았다. docs/journal/2026-10-26-02-pilot-and-prereg.md
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
읽을 것: docs/journal/2026-10-26-02-pilot-and-prereg.md의 "다섯째 세션" 이후 전체(커밋하지 않은 절 포함), 티켓 11의 "러너로 파일럿 목록을 돈다" 체크박스부터
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(설계·명세·프로브 README·티켓 11·tools/rerun_checks.py·그 시험·미추적 probes/deny_shapes/·일지)이 워크트리에 있고 셀프 리뷰(/code-review, base 1dd42c39)부터 한다. 파일럿 고르기 백그라운드는 멈췄으니 다시 띄운다: uv run python -m tools.rerun_select pilot --branches .scratch/model-rerun/probes/branches.json --earlier-branches .scratch/model-rerun/probes/branches-2026-10-23.json --revive .scratch/model-rerun/probes/revive.json --table .scratch/model-rerun/probes/candidates.md --rev 80ff61f1 --out .scratch/model-rerun/probes/pilot.json (약 3시간, 남은 %TEMP%\rerun-hidden-* 폴더는 일지 참고). 러너 인자: --account njh4803 --config-dir C:\Users\User\.claude-rerun --claude C:\Users\User\.claude-rerun-bin\2.1.302 --cap 900. PR 직전 리뷰에 밀 주장은 일지 "셀프 리뷰 (넷째 세션)"의 마지막 줄과 다섯째 세션이 새로 쓴 문장(설계 11절 주석, 명세 167행 주석, 프로브 README "막는 규칙의 새 꼴" 절)이다. docs/journal/2026-10-26-02-pilot-and-prereg.md
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
