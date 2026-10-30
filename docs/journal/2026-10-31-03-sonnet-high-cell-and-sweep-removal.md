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

## PR 직전 리뷰

위 일지를 커밋 `0e716068`로 남겼다(pre-commit의 검사 모두 `Passed`, ruff 둘은 `.py`가 없어 `Skipped`이고 `af7a72ea`에서 통과).
`coderabbit auth status`가 `Seat: not assigned`라 CLI는 돌지 못해 대체 둘을 돌렸다. `origin/main`은 기점 `f01ce1e9`에서 움직이지
않아 합칠 것이 없었다.

- `/security-review`: 취약점 없음. 바뀐 파이썬에 새 하위 프로세스·역직렬화·경로·비밀 처리가 없고(`merged_prs`의 날짜는 셸 없는
  리스트 인자의 `gh` 호출로 간다), 나머지는 문서와 시험 입력이다. 걸러 낼 지적이 없어 거짓 양성 거르기는 돌지 않았다.
- `bug-perf-review`(기준 `f01ce1e9`, 35파일, 호출 40): 유효 2, 보류 1, 오탐 3. 확인으로 시험 269개 통과, 바뀐 카나리아 여덟의
  `--shape` 통과, 옮긴 `percentile_ci`가 옛 본문과 글자 그대로 같고 경계 입력 값이 같다, ADR 0037 포인터가 이력 제목과 같다.

판정:

- 고친다(Minor, 유효). 사다리가 잇는 값만 기준으로 올려, `Opus 5.5 / high`까지 오른 구현 세션이 PR을 연 뒤 리뷰 반영에서 막히면
  다음 단계가 PR 반영·병합이라 `Sonnet 5.5 / high`에서 한 단계 위인 `Opus 5.5 / medium`이 막힌 세션보다 낮게 받는다. ADR 0029 이력
  2026-10-31의 굵은 결정 "그 세션이 막혔다고 인계하면 다음 세션의 모델을 사다리 … 에서 한 단계 올리고"와 어긋난다. `directive.md` 2
  사다리의 기준을 잇는 값과 이 세션의 값 가운데 사다리에서 높은 쪽으로 고치고 "끝:"도 맞췄다. ADR은 고치지 않는다.
- 고친다(Minor, 유효). 구현을 이을 때 지시문 "모델" 줄이 없거나 `없음`이면 `get_session`의 `model`(`claude-opus-5-5`)을 옮기는데
  형식은 모델 메뉴의 이름이다. `Opus 5.5`로 바꿔 적고 `open-session` 4의 바꾸는 법을 거꾸로 한다고 더했다. 보류였던 "`self`가
  `model`과 `effort`를 내는가"는 이 세션에서 `get_session` `self`를 불러 `claude-opus-5-5`·`xhigh`를 봤다.
- 오탐(보류였다). `session_cost` README의 세 칸(`first_human_at`, `model_line`, `branch_line`)을 `analyze.py`가 읽을 수 있다는
  지적은 `analyze.py:371-372`의 `DIRECTIVE_KEYS`에 그 칸이 없다. 저장소 `*.py` grep에서 그 이름이 걸린 `tools/token_report.py`·
  `tools/rerun_continue.py`는 다른 함수(`_branch_lines`, `arm_model_line`)였다.
- 오탐 셋은 리뷰가 스스로 닫았다(`merged_prs` 창, `percentile_ci` 값, `.scratch/morning-report-split/design.md`의 설계 기록).
- 리뷰가 따라가지 못한 것: `morning_collect.collect()`를 끝까지 돌리지 않았고, pyright와 `f01ce1e9`에서의 `sweep.py`는 보지 않았다.
  pyright는 두 커밋의 pre-commit이 돌렸다.

카나리아 `next_session_continue_ladder.toml`에 물음 9~10과 기대 글 둘(올리는 기준, `model` 꼴)을 더했다. `--preflight` 통과 1 뒤
`--control-commit f01ce1e9`(claude 2.1.312)로 돌려 통과 4·실패 0·"없음" 섞임 3이다. 섞임 셋은 모두 1번 답이고, 둘은 옮긴 원문 구절의
`없음`, 하나는 "없음."이라고 쓴 뒤 같은 구절을 옮겼다. 대조군은 열 물음 모두 "없음"이었다(러너 출력의 답을 손으로 봤다). 실험군
3회차가 2번("모델" 줄 끝에 적는 말)에 `2의 잇는 지시문`을 답했다. 26행은 줄 끝에 `2의 잇는 지시문`을, 27행은 줄 끝에 `막혀 한 단계
올렸다`를 적게 해 둘이 놓이는 자리가 모호했다. 27행을 "`2의 잇는 지시문` 뒤에 `막혀 한 단계 올렸다`를 더한다"로 고치고, 문구만
고친 것이라 `--preflight`(통과 1)로 갈음했다. 다른 카나리아 명세의 기대 글에는 바뀐 문구가 없다(grep).

이 반영의 첫 커밋은 pre-commit의 pytest에서 `test_사다리로_올린_값은_스크립트가_읽는다` 하나가 빨개 만들어지지 않았다(1 failed, 5916
passed). 그 시험은 사다리 항목 줄에서 백틱으로 감싼 `<모델> / <레벨>` 값을 뽑아 넷인지 보는데, 사다리에 없는 값의 예로 넣은
`` `Fable 5.1 / xhigh` ``가 다섯째로 잡혔다. 시험이 아니라 문장이 그 계약을 깬 것이라 예를 "설계 인터뷰·명세의 Fable 칸"으로 고쳤고,
`uv run pytest -q tests/tools/test_open_session.py`가 111 passed, 카나리아 `--preflight`가 통과 1이다.

PR 직전 리뷰에 밀 문장에 더할 것(이 반영으로 새로 쓴 사실 문장): `directive.md` 2 사다리의 "올리는 기준은 그 값과 이 세션의 값
(구현을 이을 때 읽는 그 자리) 가운데 사다리에서 높은 쪽", "PR을 연 뒤 리뷰 반영에서 막힌 `Opus 5.5 / high` 구현 세션은 잇는 값이
`Sonnet 5.5 / high`여도 `Opus 5.5 / xhigh`로 넘긴다", 잇는 지시문 괄호의 "`model`의 `claude-opus-5-5`는 모델 메뉴의 이름 `Opus 5.5`로
바꿔 적는다", "끝:"의 "2의 올리는 기준 … 의 한 단계 위이고, 기준이 꼭대기였으면 꼭대기다", 사다리의 "\"모델\" 줄 끝의 `2의 잇는 지시문` 뒤에
`막혀 한 단계 올렸다`를 더한다". PR 봇이 다음 층이다.

## PR과 봇 1회차

PR #440(https://github.com/njh6803/agent-os/pull/440)을 헤드 `4931531b`로 열었다. CI 아홉(python, web, verify, e2e, e2e-widget,
visual, ticket, CodeRabbit, claude-review)이 모두 통과했다(`tools/wait_ci.py` 끝 `모두 통과`). claude-review는 지적이 없었다.
CodeRabbit 1회차는 Minor 하나를 냈다.

- 고친다(Minor, 유효). `tools/morning_collect.py:2329`의 "병합 PR 조회 기간과 남은 워크트리 판정을 분리하세요". 이 브랜치가 병합 PR
  조회의 아래 경계를 `min(보고일 - TICKET_DAYS, SWEEP_START_AT)`에서 `보고일 - TICKET_DAYS`로 바꿨고, `_gather_worktrees`가 같은
  목록으로 병합 여부를 가르므로 28일보다 오래전에 병합한 PR의 워크트리가 남은 수에서 빠진다. 옛 경계도 2026-10-13 전에 병합한
  PR은 못 봤고, 좁아지는 것은 보고일이 2026-11-10 뒤일 때부터다. PR 직전 `bug-perf-review`는 같은 자리를 오탐으로 닫았다(위 절의
  "`merged_prs` 창"). 워크트리 판정만 기간 없는 병합 PR(`merged_prs(None, root)`, `PR_LIMIT`개까지)로 하고, 그 조회만 실패하면 창 안의
  병합 PR로 가른다. 티켓·날·주의 소비자는 그대로 창 목록을 받는다. 시험 `test_기간_없는_병합_PR_목록은_창보다_오래전에_병합한_PR도_받는다`를
  더했고(고치기 전에는 `None - timedelta`로 끝난다), 모듈 독스트링의 못 보는 것에 `PR_LIMIT`과 그 조회의 실패를 적었다.

확인: `uv run python -m tools.morning_collect --day 2026-10-30`을 스크래치 폴더로 세 번 돌렸다. 첫 회는 기간 없는 조회가 실패해(까닭은
못 봤다) 워크트리 표의 PR 칸이 `PR (수집 안 됨)`, 남은 워크트리가 0이었다. 둘째 회는 남은 워크트리 6이고, 스크래치 스크립트로
`gh pr list --state merged`와 `git worktree list`를 대 본 병합된 브랜치 여섯(03, 05, 06, 08, 13-main-run-judge, 030)과 같다(손으로
봤다). 첫 회 뒤 창 목록으로 되돌아가는 길을 더했고, 셋째 회도 6이다. 같은 스크립트로 한 번씩 잰 시간은 기간 없는 조회 2.6~2.7초,
창 조회 3.2초다(손으로 봤다). `uv run pytest -q tests/tools/test_morning_collect.py`는 66 passed다.

따로 본 것: `--day 2026-10-31`(아직 진행 중인 오늘)로 돌리자 `_summary_piece`의 `statistics.median(before)`(1151행)가
`StatisticsError: no median for empty data`로 끝났다. 이 PR이 건드리지 않은 줄이고, 그 기간에 자동 압축의 컨텍스트 기록(`before`)이
없으면 난다(트레이스백과 코드를 읽었다). 바로 아래 줄의 `headless`도 같은 꼴이다. 이 PR의 범위 밖이라 따로 넘긴다.

반영 커밋 `ffddb555`의 pre-commit은 모두 `Passed`다(pytest 350.1초, web-verify 472.0초. 인용 대조 경고 1건은 위의 CodeRabbit 지적
제목이라 저장소에 원문이 없다). 이 커밋 뒤에도 인계 계기가 왔으나 위의 `인계 못함 커밋 뒤` 줄이 있어 `handoff.md` 1의 인계하지
않는 때대로 넘기지 않았다.

## 회고

후보 아홉, 승인 3(회차로 세는 것 2, 고침 1), 기각 6, 넘김 0.

1. **승인(회차로 세는 것, 대기열 498 → 3회차).** 커밋 뒤 인계 열기(`tools/open_session.ps1 -Action send`)를 자동 모드 분류기가 거부해
   인계를 못 하고 이 세션이 압축으로 이었다(위 "인계 (커밋 뒤)"). 열린 498이 같은 사건을 처방한 행이라 회차를 더했다.
2. **승인(회차로 세는 것, 대기열 552 새 행, 1회차).** 레벨 스윕을 걷으며 함께 받는 병합 PR 조회의 범위를 티켓 창으로 좁혔는데, 창 없이
   같은 목록을 받던 남은 워크트리 판정을 보지 않았다. 셀프 리뷰 두 축을 지나고 PR 직전 `bug-perf-review`는 오탐으로 닫았으며
   CodeRabbit이 잡았다. `CODING_STANDARDS.md`와 `code-review`의 두 브리프에 그 기준이 없어(Grep으로 `소비자`·`받는 쪽`·`범위를`을
   봤다) 리뷰가 잡도록 둔 기준을 어긴 사건이 아니다. 검사가 글자로 가를 수 없는 새 판단 기준이고 더하는 것이라 세 번째까지 센다.
   `--search 소비자 --search tools/morning_collect.py --search merged_prs`에 맞은 380·446은 다른 일이다.
3. **승인(고침, 대기열 553 새 행, 1회차).** `_summary_piece`가 빈 목록의 중앙값으로 끝나는 버그(위 "따로 본 것"). 고침이라 사건
   하나로 반영할 수 있으나 이 PR의 범위 밖이고 봇 2회차의 범위를 넓히지 않으려고 이 세션에서는 반영하지 않는다. 같은 일을 다룬 행은
   `--search _summary_piece --search median --search StatisticsError`에 없었다.
4. **기각.** `4931531b`의 첫 pre-commit에서 사다리 시험이 빨갰다. 이미 있는 시험이 그 자리에서 막았다.
5. **기각.** 카나리아 3회차가 "모델" 줄 끝 두 표지의 자리를 모호하게 읽었다. 카나리아가 그 자리에서 드러냈고 문구를 고쳤다.
6. **기각.** PR 직전 `bug-perf-review`의 유효 Minor 둘(사다리의 올리는 기준, `model` 이름의 꼴). 구현이 ADR의 결정을 잘못 옮긴 것은
   셀프 리뷰 명세 축의 브리프가 보는 자리라 리뷰가 제 몫을 한 사건이고, 검사로 옮길 수 없으며 표준에 더할 새 기준도 아니다.
7. **기각.** 수집 도구 첫 회에서 기간 없는 조회가 실패했다. 도구의 실패 갈래(`수집 안 됨`)가 그 자리에서 알렸고, 되돌아가는 길을 이
   PR에 넣었다.
8. **기각.** 대기열 만료에 쓴 스크래치 스크립트의 `write_text`가 줄 끝을 CRLF로 바꿨다. git이 경고했고 LF로 되돌렸다(2026-10-30-12
   회고 5와 같은 판정).
9. **기각.** `인계 못함` 줄을 쓴 뒤에도 단계 경계마다 인계 계기가 다시 왔다. `handoff.md` 1의 인계하지 않는 때가 받았고 비용은 Read
   한 번씩이다.

만료: 작업 폴더와 `git fetch origin` 뒤 `--ref origin/main`의 두 출력에 모두 든 열둘(289, 295, 297, 298, 301, 304, 314, 315, 322, 324,
325, 329)을 취소선과 `만료 2026-10-31`로 닫았다. 날짜를 찾지 못한 행은 없었다.

## 다음

harness 031이 ADR 0029 이력 2026-10-31의 "함께 고치는 것"을 마쳐 그 주제가 남지 않았다. next-session 결정표의 harness 티켓 PR 줄이
프론티어로 보내는데, `plan.md`의 프론티어에 남은 기능이 없다(design-card-build가 2026-10-30에 닫혔고, model-rerun의 티켓 01~13도
모두 `done`이다). 그래서 다음은 새 기능을 고르는 설계 인터뷰(`/grill-with-docs`, 새 세션, `Fable 5.1 / xhigh`)다. 대기열의 회차 3
이상인 열린 행은 27개라 chore 조건은 차 있지만, 그 줄은 harness PR 뒤에 chore를 잇지 않는다.

- 대기열 553(아침 보고 `_summary_piece`의 빈 목록)은 고침이라, 다음 chore 차례에 `tools/morning_collect.py`를 대상으로 하는 행과 묶는다.
- `docs/model-selection.md` 4절 8의 14일 뒤 다시 보기는 4절 계기 목록대로 알아챈 세션이나 사람이 시작한다. 정해진 날에 돌게 하는
  예약 작업은 지속 설정이라 만들지 않았다.
- 워크트리에서 병합하므로 주 체크아웃은 당기지 않는다. 주 체크아웃 미갱신: 루트는 main. 새 세션이 워크트리에 들어가기 전에
  `tidy-checkouts`로 당긴다.
