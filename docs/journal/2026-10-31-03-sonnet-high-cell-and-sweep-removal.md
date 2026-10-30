# 2026-10-31 (03) 구현·하네스 칸을 Sonnet 5.5 / high로 내리고 레벨 스윕을 걷는다

## 시작

> 사용자: (새 세션 지시문) ADR 0029 이력 2026-10-31의 "함께 고치는 것"을 티켓 .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md로 쓰고 한다

지시문의 모델 줄은 칸의 지금 값 `Opus 5.5 / xhigh`였다(사용자 결정. 칸을 바꾸는 이 chore가 병합될 때까지 칸은 그대로 둔다). 주
체크아웃 미갱신이라 `tidy-checkouts`를 먼저 돌았다. 병합된 워크트리 하나(`03-upload-plan-first-canonical`)의 `remove`가 다른
프로세스가 쥔 파일 때문에 WinError 5로 종료 1이었고, 지시문대로 보고만 하고 넘어갔다. 그 뒤 `EnterWorktree`로 이 워크트리에
들어가 브랜치를 바꾸고 티켓 031을 썼다.

## 범위를 정한 것

- 결정표: 구현 두 줄과 하네스 chore 배치 줄의 칸을 `Sonnet 5.5 / high`로, "같은 주제가 남았다" 줄은 새 세션이면 새 티켓이라
  `Sonnet 5.5 / high`로 바꿨다. 화면 디자인·티켓 줄(`Opus 5.5 / xhigh`)과 설계 인터뷰·명세 줄(`Fable 5.1 / xhigh`)은 그대로다.
- 같은 티켓을 잇는 지시문(끊는 줄, 인계 줄)의 모델은 `directive.md` 2 한 곳에 "이어 가기"와 "사다리"로 두고 끊는 줄과
  `handoff.md` 인계 줄이 가리킨다. 이어 가기는 "다음 단계" 칸으로 고른다(PR 반영·병합 `Sonnet 5.5 / high`, 설계 인터뷰나 명세
  `Fable 5.1 / xhigh`, 구현은 이 세션의 모델 줄을 그대로, 그 밖 `Opus 5.5 / xhigh`). 2026-10-31 이력의 "같은 모델로 잇는다"와
  harness 030의 "설계·명세를 이어받아도 Fable"을 함께 지키려고 "다음 단계"로 갈랐다. 사다리는 막혀서 넘길 때만 한 단계 올린다.
- 지운 것: `tools/model_sweep.py`, `tools/model_sweep_judge.py`, 그 시험 둘, 판정 변이 표, 스윕만 확인하던 카나리아 셋,
  아침 보고의 스윕 조각(서브에이전트가 걷었다). `rerun_judge.py`가 가져다 쓰던 `percentile_ci`는 그 파일로 옮겼다.
- 남긴 것: 스윕 프로브(`sweep.py`, 사전 등록 README)는 ADR 0029·0033이 인용하는 기록이라 두고, 지운 도구를 import하므로 지우기
  전 커밋 `f01ce1e9`에서 돈다고 README와 독스트링에 적었다. 소급 측정 창(`tools/session_cost_window.py`)은 `collect.py`가 쓰므로
  두고 독스트링만 과거형으로 바꿨다.
- ADR 0033의 스윕 문장 셋(24·55·139행, 다음 세션이 grep으로 셌다)은 PR #439가 이미 `(바뀜: ADR 0029 이력 2026-10-31 …)` 포인터를 달았다. ADR 0037의 "스윕의 종류가
  섞인다"는 결정이 아니라 결과 절의 고려라 포인터를 달지 않았다(코드 읽기).
- 지난 지시문을 옮긴 시험 입력(`test_rerun_continue.py`의 파일럿 E-2 인계 지시문, `test_session_cost_window.py`의 모델 줄)의
  "레벨 스윕의 갈래"는 그 기간의 실제 입력 모양이라 두었다.
- 옛 카나리아 셋(`next_session_model_line`, `next_session_fable_cut_row`, `next_session_handoff_fable`)은 기대 글이 이번에 고쳐 쓴
  옛 칸 문장이라 지금 원천에 없다. 기록으로 두고 머리 주석에 그 사실과 새 명세를 적었다. `next_session_deferred_merge_running_scope`의
  기대 글 하나도 원천에 없지만 `f01ce1e9`에서도 없었다(스크래치 스크립트로 기대 글과 원천을 대 보고, 옛 사본을 `git show`로 꺼내
  Grep으로 손으로 봤다). 이 티켓과 무관해 두었다.

## 이 세션이 고친 것

- `handoff.md` 인계 줄의 모델 항목을 처음에 "사다리로 올리지 않는다"로 써서 `directive.md` 2와 어긋났다. "이 세션이 막혔을 때만
  사다리로 올린다"로 고쳤다.
- 아침 보고를 걷은 서브에이전트가 지시와 달리 `combo_costs`도 지웠다. 저장소 전체 grep에서 쓰는 곳이 스윕 몫(`top_combo`,
  `_sweep_piece`)뿐이라 그 판단을 받아들였다. 그 서브에이전트는 `_model_section`을 `_ticket_section`으로, 실험 보고 7절 제목을
  "모델 선택과 티켓 분할"에서 "티켓 분할"로 바꾸고, 병합 PR을 읽는 첫날을 `day - TICKET_DAYS`로 줄였다(스윕 시작일과의
  `min`을 걷었다).

## 확인

- `uv run pytest -q tests/tools/test_open_session.py tests/tools/test_rerun_prereg.py tests/tools/test_morning_collect.py
  tests/tools/test_session_cost_window.py`: 220 passed. 서브에이전트는 `test_morning_collect.py`·`test_morning_report.py`에서 140
  passed, ruff·pyright·`check_type_escapes`가 0이라고 보고했다.
- `uv run ruff check .`와 `uv run ruff format --check .`: 둘 다 초록.
- 카나리아 두 명세(`next_session_continue_ladder.toml`, `next_session_ladder_rows.toml`)를 `--control-commit f01ce1e9`로 돌려 둘 다
  통과 4, 실패 0(claude 2.1.312). 이어 가기 명세의 "없음" 섞임 셋은 1번 답이 옮긴 원문 구절의 `없음`이었다(원본 로그를 손으로
  봤다). 결과는 두 명세의 머리 주석에 적었다.
- `uv run python tools/run_checks.py`는 백그라운드로 띄웠다가 끝나기 전에 인계하며 멈췄다. 결과는 보지 못했다.

## 인계 (셀프 리뷰 직전)

`/code-review`를 부른 직후 인계 계기가 왔다(세션 컨텍스트 266,746 토큰). 받은 범위가 PR과 병합까지라 넘긴다. 이 세션의 지금
제목은 `chore/031-sonnet-high-cell-and-sweep-removal`이다.

```
다음 작업: .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md. 결정표 구현·하네스 줄의 모델 칸을 Sonnet 5.5 / high로 바꾸고 레벨 스윕 도구와 임시 문장을 걷는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: ADR 0029 이력 2026-10-31의 "함께 고치는 것"을 티켓 .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md로 쓰고 한다
브랜치: chore/031-sonnet-high-cell-and-sweep-removal
모델: Opus 5.5 / xhigh. 2의 이어 가기(구현이라 이 세션의 모델 줄을 잇는다. 칸을 바꾸는 이 chore가 병합될 때까지 칸을 Opus 5.5 / xhigh로 두는 것은 사용자 결정)
읽을 것: docs/journal/2026-10-31-03-sonnet-high-cell-and-sweep-removal.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세는 티켓 031)부터 한다. docs/journal/2026-10-31-03-sonnet-high-cell-and-sweep-removal.md. 전체 검증 러너(tools/run_checks.py)는 끝나기 전에 멈췄으니 리뷰 반영 뒤 커밋의 pre-commit으로 본다. 카나리아 두 명세는 통과했다. 티켓은 in-progress이고 수용 기준 체크박스는 아직 비었다
확인할 선행 조건: 이 chore가 next-session을 고쳐 주 체크아웃의 사본은 옛것이다. 병합과 다음 지시문은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"와 directive.md를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `chore/031-sonnet-high-cell-and-sweep-removal (인계함)`으로 바꾸고, 전체 검증 러너를 멈추고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-30T19:52:05Z

## 이어받은 세션: 셀프 리뷰

> 사용자: (인계 지시문) ADR 0029 이력 2026-10-31의 "함께 고치는 것"을 티켓 .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md로 쓰고 한다

지시문대로 `EnterWorktree(path)`로 이 워크트리에 들어와 `/code-review`를 돌렸다. 범위는 base `f01ce1e9`, 파일 32개(바뀜 20,
지움 8, 미추적 4), 커밋 0이다. 표준 축(sonnet·high)은 Major 1·Minor 3·Nit 3, 명세 축은 Major 1·Minor 7·Nit 4를 냈다.

판정:

- 고친다(두 축 Major, 명세 Minor 5). 끊는 줄의 모델이 "다음 단계"로 고르는데, 결정표의 그 줄 "다음 단계" 칸은 `이어서`라
  글자대로면 "그 밖"(`Opus 5.5 / xhigh`)으로 떨어져 끊긴 설계·명세가 Fable로 열리지 않는다. 옛 줄의 "끊는 세션의 지시문의
  '다음 단계'"와 "남은 것이 PR 반영·병합뿐이면"이 빠졌다. `directive.md` 2가 내는 지시문의 "다음 단계" 줄로 고르고, 그 값은
  끊기든 인계든 `handoff.md` 인계 줄의 "다음 단계" 항목대로 정하게 고친다.
- 고친다(표준 Minor 3, 명세 Minor 6·Nit). 사다리로 올린 값이 그대로 가는 범위(구현을 이을 때뿐), 잇는 값의 줄 끝 표지(앞 지시문의
  `막혀 한 단계 올렸다`를 옮기지 않는다), 꼭대기에서 막혔을 때의 `막힘:`, `directive.md` "끝:"의 "한 단계 위"를 적는다.
- 고친다(명세 Minor 4). 구현을 이을 때 이 세션의 지시문 "모델" 줄이 없거나 `없음`이면 `Sonnet 5.5 / high`로 내려 막힌 모델보다
  낮아질 수 있다. 그때는 이 세션이 도는 모델과 레벨(`get_session`의 `self`)을 잇는다. `get_session` `self`가 `model`과 `effort`를
  내는 것은 이 세션에서 손으로 봤다(`claude-opus-5-5`, `xhigh`).
- 고친다(명세 Nit). 규칙 이름 "이어 가기"는 `CONTEXT.md`의 제품 용어(Continuation)이고 인계 항목이 `_Avoid_`로 든다. "잇는
  지시문"으로 바꾼다.
- 고친다(두 축 Minor). ADR 0037 결과 절 66행에 포인터를 단다. `.claude/rules/adr.md`가 ADR 본문을 살아 있는 문서로 보고 Consequences
  문장을 사례로 든다. 위 "범위를 정한 것"의 "포인터를 달지 않았다"를 번복한다.
- 고친다(두 축 Minor, 명세 Minor 7·Nit). `docs/model-selection.md` 1절의 "앞 세션의 모델을 잇고"(구현일 때만 맞다), 4절 6의
  "레벨과 계열을 바꾸는 측정은 다시 풀기"(하네스 칸은 재지 않았다), 새 규칙이 된 231~233행과 270행, 기점을 날짜로 잡은 191·233행.
- 고친다(명세 Minor 3). `.scratch/harness/probes/session_cost/README.md`의 "이 세 칸은 레벨 스윕의 판정이 쓴다"를 과거형으로.
- 고친다(명세 Minor 2). 새 카나리아가 PR 반영·병합과 설계·명세의 값, `handoff.md` 인계 줄을 보지 않고, 지운 `next_session_model_sweep.toml`이
  보던 `directive.md` 1의 "티켓 파일은 이 세션이 쓰지 않는다"도 빠졌다. 이어 가기 명세에 물음을 더하고 인계 줄 명세를 새로 둔다.
- 고친다(Nit). 스윕 프로브 README의 판정 문장 시제, `rerun_judge.py` `percentile_ci` 독스트링의 이력, `docs/model-selection.md`
  "멈춘 스윕"의 `f01ce1e9` 되풀이(README를 가리킨다), 위 "범위를 정한 것"의 "ADR 0033의 스윕 문장 둘"(셋이다. 24·55·139행).
- 남긴다(표준 Nit). "같은 주제가 남았다" 줄이 앞 세션이 화면 디자인·티켓이었어도 `Sonnet 5.5 / high`다. ADR 0029 이력 2026-10-31의
  굵은 결정이 그 줄을 하네스 티켓을 여는 줄로 들어 그 칸으로 정했다.
- 남긴다(표준 Nit). `f01ce1e9`에서 돈다는 문장 가운데 `sweep.py` 독스트링, 그 README, 프로브 README 행의 "돌리는 법" 칸은 둔다.
  셋 다 그 프로브를 돌리려는 사람이 여는 자리다.
- 남긴다(명세 Major 1의 받는 쪽). 14일 뒤 지표 문서 4절 8을 도는 계기는 그 4절 계기 목록이 받고 "자동으로 알리는 훅은 없고, 알아챈
  세션이나 사람이 시작한다"고 정했다. harness 030도 같은 길이다(ADR 0029 이력 2026-10-31 Fable 칸의 결과 절). 정해진 날에 돌게 하는
  예약 작업은 지속 설정이라 사람에게 묻는다. 기점을 날짜로 적은 문장은 위에서 고친다.
- 남긴다(명세 Minor 8). 이 브랜치가 결정표를 고쳐, 병합 뒤 이 세션이 Skill 도구로 싣는 next-session은 옛 사본이다. 다음 지시문은
  워크트리 사본의 `SKILL.md` 결정표까지 Read로 열어 낸다(`CLAUDE.md` 환경 함정의 "바뀐 스킬은 Read로 디스크의 `SKILL.md`를 열어
  따른다"). 파일은 고치지 않는다.
- 남긴다(명세 Minor 2의 셋째). `directive.md` 1의 "티켓 파일은 이 세션이 쓰지 않는다"는 이 브랜치가 고치지 않았고 대조군
  `f01ce1e9`에도 있어 카나리아가 될 수 없다(`tools/canary.py` 독스트링의 돌리기 전 확인: 대조군 사본의 원천에 카나리아가 하나도
  없어야 한다). 지운 명세가 그 글을 본 것은 harness 027이 본문을 옮긴 때의 확인이었다(그 명세의 머리 주석).

반영 뒤 다시 돌린 것:

- 카나리아 사전 확인 `uv run python tools/canary.py --preflight --control-commit f01ce1e9`에 세 명세(`next_session_continue_ladder`,
  `next_session_handoff_model`, `next_session_ladder_rows`): 통과 3. 결정표 명세는 끊는 줄의 규칙 이름만 바뀌어 이것으로
  갈음했다(`docs/constitution/operations.md` 카나리아 항목의 "한 번 통과한 뒤 문구만 고쳤으면").
- 카나리아 `--control-commit f01ce1e9`(claude 2.1.312): 잇는 지시문 명세(물음 여덟) 통과 4·"없음" 섞임 3, 새 인계 줄 명세 통과 4·
  섞임 0. 섞임 셋은 모두 1번 답이다. 둘은 옮긴 원문 구절의 `없음`이고 하나는 "없음."이라고 쓴 뒤 같은 구절을 옮겼다(러너 출력의
  답을 손으로 봤다). 대조군은 두 명세 모두 카나리아가 없었다.
- 수용 기준 4의 grep(`model_sweep`·`레벨 스윕의 갈래`·`스윕 밖`, 살아 있는 문서·하네스·시험): 남은 줄은 지운 도구를 지웠다고
  적는 문장(`docs/model-selection.md` 멈춘 스윕, `tools/session_cost_window.py`, `tools/rerun_judge.py`), 레벨 스윕에 둔 옛 규칙을
  적는 문장(`docs/model-selection.md` 3절), 지난 지시문을 옮긴 시험 입력(`test_rerun_continue.py`, `test_session_cost_window.py`)이다.

커밋 직전 `uv run python tools/sibling_overlap.py`가 종료 1로, `.claude/skills/open-session/SKILL.md`를 고쳤는데 그 파일을 원천으로 드는
카나리아 명세를 이 브랜치가 고치지 않았다고 알렸다. 위 "범위를 정한 것"에서 지운 셋 가운데 `open_session_model_source.toml`은
스윕만 본 명세가 아니었다. "모델" 줄의 출처 괄호를 보는 명세이고, 그 괄호는 이 브랜치가 고쳐 썼지만 남아 있다. 그래서
`git restore --source=HEAD`로 되살려 카나리아를 새 괄호의 `잇는 지시문·사다리`로 바꾸고 대조군을 `f01ce1e9`로 했다. 사전 확인은
통과 1이고, `--control-commit f01ce1e9`로 돌린 카나리아(claude 2.1.312)는 통과 4·"없음" 섞임 0이다. 지운 카나리아는
둘(`next_session_model_sweep`, `next_session_sweep_stopped`)이 된다.

PR 직전 리뷰에 밀 문장(반영으로 새로 쓴 사실 문장, 셀프 리뷰 6의 1):

- `directive.md` 2 잇는 지시문: "그 값은 끊든 인계하든 `handoff.md` 인계 줄의 \"다음 단계\" 항목대로 정한다(결정표의 \"다음 단계\" 칸
  `이어서`는 형식의 값이 아니다. 그 칸의 줄로 낸 지시문도 다섯 값 가운데 하나를 적는다)", "그 줄이 없거나 `없음`이면 이 세션이
  도는 모델과 레벨. `get_session`의 `self`가 `model`과 `effort`로 보인다", "앞 세션이 사다리로 올린 값이 그대로 가는 것은 구현을
  이을 때뿐이다", "줄 끝에는 `2의 잇는 지시문`을 적고, 앞 지시문의 `막혀 한 단계 올렸다`는 옮기지 않는다".
- `directive.md` 2 사다리: "잇는 지시문의 값이 사다리 … 에 있고 꼭대기가 아니면 한 단계 올려", "사다리에 없거나 꼭대기면 값을 그대로
  둔다"와 "끝:"의 "잇는 값이 사다리의 꼭대기 아래였으면 그 한 단계 위다".
- `docs/model-selection.md`: 1절 표의 "넘기는 지시문의 \"다음 단계\"로 고르고(구현이면 앞 세션의 모델을 잇는다)", 3절의 "harness
  031의 병합부터"(둘)와 "ADR 0029 이력 2026-10-13은 레벨 스윕의 갈래에 Sonnet 5.5가 들면 공식 가격표로 셈한 판정을 함께 적게 했고",
  4절 6의 "레벨과 계열을 바꾸는 측정은 구현 칸을 재는 다시 풀기 … 이고, 하네스 칸은 다시 풀기가 재지 않는다".
- `.scratch/harness/probes/session_cost/README.md`: "이 세 칸은 레벨 스윕의 판정(`../model_sweep/`)에 쓰려고 더했고". 세 칸을 읽는
  코드가 `sweep.py`뿐인 것은 `tools/`·`tests/tools/`·프로브 파이썬을 grep해 봤다(`analyze.py`의 `DIRECTIVE_KEYS`에는 없다).
- ADR 0037 결과 절 66행의 포인터.

## 인계 (커밋 뒤)

반영을 커밋 `af7a72ea`로 남겼다. pre-commit의 검사는 모두 `Passed`이고 헌법 판 검사만 헌법 파일을 고치지 않아 `Skipped`였다(커밋
출력). 손으로 치는 다섯(pytest, ruff 둘, pyright, lint-imports)은 이 pre-commit 결과로 갈음한다. 티켓 031은 done이고 수용 기준을
모두 채웠다. 커밋을 띄우자 인계 계기가 왔다(세션 컨텍스트 343,883 토큰, 경계 `커밋 뒤`). 받은 범위가 PR과 병합까지라 넘긴다.
이 세션의 지금 제목은 `chore/031-sonnet-high-cell-and-sweep-removal`이다. 이 절은 커밋하지 않았다.

```
다음 작업: .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md. 결정표 구현·하네스 줄의 모델 칸을 Sonnet 5.5 / high로 바꾸고 레벨 스윕 도구와 임시 문장을 걷는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: ADR 0029 이력 2026-10-31의 "함께 고치는 것"을 티켓 .scratch/harness/issues/031-sonnet-high-cell-and-sweep-removal.md로 쓰고 한다
브랜치: chore/031-sonnet-high-cell-and-sweep-removal
모델: Opus 5.5 / xhigh. 2의 잇는 지시문(구현이라 이 세션의 지시문 모델 줄을 잇는다. 칸을 바꾸는 이 chore가 병합될 때까지 칸을 Opus 5.5 / xhigh로 두는 것은 사용자 결정)
읽을 것: docs/journal/2026-10-31-03-sonnet-high-cell-and-sweep-removal.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영을 커밋 af7a72ea로 남겼고(pre-commit 통과) 티켓 031은 done이다. 남은 단계는 일지의 "인계 (커밋 뒤)" 절(커밋하지 않음)을 다음 커밋에 싣기, PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. CodeRabbit CLI가 돌지 못하면 origin/main을 합친 뒤 /security-review와 bug-perf-review를 나란히, 브리프에 일지의 "PR 직전 리뷰에 밀 문장"을 나열), PR 열기, merge.md 2의 봇 회차, 병합이다. 14일 뒤 docs/model-selection.md 4절 8을 정해진 날에 돌게 하는 예약 작업은 지속 설정이라 사람에게 물을 것으로 남겼다(일지의 셀프 리뷰 판정). docs/journal/2026-10-31-03-sonnet-high-cell-and-sweep-removal.md
확인할 선행 조건: 이 chore가 next-session을 고쳐 주 체크아웃의 사본은 옛것이다. 병합과 다음 지시문은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때", directive.md, SKILL.md 결정표를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `chore/031-sonnet-high-cell-and-sweep-removal (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었고, 워크트리 잠금은 이미
풀려 있었다(`git worktree unlock`이 `is not locked`).

open-session을 부른다 2026-10-30T20:35:28Z

인계 못함 커밋 뒤

`tools/open_session.ps1 -Action send`를 자동 모드 분류기가 거부했다(설명 없음). 스크립트가 돌지 않아 `fired=`가 없고 세션은
생기지 않았다. `handoff.md` 4 열기의 막힘 갈래대로 제목을 `chore/031-sonnet-high-cell-and-sweep-removal`로 되돌리고, 이
세션에서 다음 단계(일지 커밋, PR 직전 리뷰, PR, 봇 회차, 병합)를 잇는다. 멈춘 대기는 없었다.
