# 2026-11-05 (09) plan.md 기능 행 상태를 티켓과 맞대는 시험 (harness 044)

세션 제목은 `chore/044-plan-status-matches-tickets-test`이다. 티켓은 `.scratch/harness/issues/044-plan-status-matches-tickets-test.md`이다. 일지 2026-11-05-07(harness 043)의 "다음" 첫 항목을 받아 새 세션이 열었다. 이 일지는 컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 넘기며 지금까지를 적은 것이고, 이어 받는 세션이 같은 파일을 이어 쓴다.

## 사용자 프롬프트

> 사용자: 대기열 546을 티켓 .scratch/harness/issues/044-plan-status-matches-tickets-test.md로 쓰고 한다 (일지 2026-11-05-07 "다음" 첫 항목을 받은 지시문의 시작 프롬프트이고 이번 요청 범위는 "PR과 병합까지"다.)

## 한 것

- 세션 제목을 브랜치 이름으로 바꾸고 Skill 도구로 `tidy-checkouts`를 돌았다. 주 체크아웃을 `050bb13b`에서 `403c9e96`으로 당겼고(`git merge --ff-only --no-overwrite-ignore origin/main`의 출력을 읽었다), 병합된 워크트리·브랜치는 `chore/042-tools-rule-hook-time-items-split`(워크트리와 브랜치)와 `chore/041-mutate-check-marker-quality`(브랜치)를 지웠다. `05-default-model-required-and-checked`는 다른 프로세스가 쥐어 남았고, 042의 `node_modules`가 휴지통에 남았다(도구의 출력을 읽었다).
- `EnterWorktree`로 `044-plan-status-matches-tickets-test` 워크트리에 들어가 `chore/044-plan-status-matches-tickets-test` 브랜치를 땄다. 기준은 origin/main `403c9e96`이다.
- `uv run python tools/sibling_overlap.py`로 티켓 044, 일지 09를 받고 티켓을 쓴 뒤 다시 쳐서 겹침이 없음을 봤다(출력을 읽었다).
- 티켓 044를 썼다(`Status: in-progress`, 수용 기준 여섯, 체크박스는 모두 비어 있다).
- `tests/test_plan_status.py`를 썼다. `plan.md` 표에서 `기능(slug)`와 `Status` 칸을 표 머리로 찾고, 행마다 `.scratch/<slug>/issues/*.md`의 첫 `**Status:**` 값을 읽는다. 규칙은 둘이다. 하나라도 `done`이면 행이 `todo`가 아니다. 티켓이 모두 닫혔고(`done`·`wontfix`) `done`이 하나 이상이면 행이 `done`이다. 열린 티켓이 있는 `done` 행은 보지 않는다(`docs/agents/issue-tracker.md`가 기능 밖 제품 코드 티켓을 더하면서 행을 `done` 그대로 두라고 한다). 티켓의 `Status:` 줄이 없거나 값이 모르는 것, 행 상태가 모르는 것, 칸 수가 표 머리와 다른 행, 표 머리가 없는 것은 문제로 센다. 시험은 열한 개이고 저장소 상태 하나, 읽은 범위가 비지 않는지 하나, 변이 아홉이다.
- 첫 시험에서 main의 지금 상태가 한 번 빨갛게 나왔다. 어긋난 행이 아니라 내 정규식이 줄 끝까지 맞추게 되어 있어서, `.scratch/design-refresh/issues/05-claude-design-upload.md`의 `**Status:** done (2026-10-14 사람이 …)`처럼 값 뒤에 괄호 설명이 붙은 티켓을 못 읽은 것이었다. 정규식을 첫 낱말만 읽도록 고치고 그 모양을 시험(`test_티켓의_첫_Status_줄만_읽는다`)에 더했다. 고친 뒤 main의 상태는 어긋남 0으로 지난다(`uv run pytest -q tests/test_plan_status.py`가 11 passed).
- 일부러 깨뜨려 손으로 봤다. `.scratch/plan.md` 25번 줄(skill-plugin)을 `sed`로 `in-progress`로 되돌리자 `skill-plugin(plan.md 25번 줄): 티켓이 모두 닫혔는데 행이 in-progress다`로 빨갰고, 23번 줄(design-card-build)을 `todo`로 되돌리자 `티켓 5/5개가 done인데 행이 todo다`로 빨갰다. 둘 다 `git checkout -- .scratch/plan.md`로 원복했다(`git status --short`가 새 파일 셋만 남았다).
- 대기열 546을 닫았다(`.scratch/retro-queue.md`의 행 545번 줄). 「무엇」·「어디로」에 취소선을 긋고 승인 칸 끝에 닫힘 표기를 붙였다. `queue_open_rows.py --search`가 열린 행 0, 닫힌 행 1로 읽었고 `check_md_tables.py`는 출력이 없었다.

## 대기열 546 3회차 셈의 재판정

PR #468의 claude-review 둘째 회차가 짚은 Minor("546의 3회차 셈이 느슨하다")를 이 PR이 판정했다. 근거는 대기열 104·399·546의 첫 문구를 `git show <커밋> -- .scratch/retro-queue.md`로 읽은 것이다(커밋 `300b5f03`, `ed5618cb`, `d312a806`).

- 104와 399는 나란히 도는 마지막 티켓이 서로의 `Status`를 어느 시점에 보고 행을 `done`으로 바꾸는지의 설계 시점 틈이다. 실제로 행이 어긋난 사건이 아니다.
- 이 세션이 처음에 센 결과는 546 자체와 043 둘뿐이라 같은 종류의 회차는 2라는 것이었다. 셀프 리뷰 명세 축이 반례를 냈고 `git log -- .scratch/plan.md`와 `git show --format= 5b255a18 -- .scratch/plan.md`로 확인했다. skill-plugin 01(PR #462)과 02(PR #461)가 병합됐을 때 `plan.md`는 그대로였고 셋째 티켓 PR #463에서야 `todo`가 `in-progress`로 바뀌었다. 그래서 병합 뒤 행 상태가 따라오지 않은 실제 사건은 셋이다. design-card-build 첫 티켓(PR #430, PR #433이 고침), skill-plugin 첫 티켓 둘(PR #463이 고침), skill-plugin 마지막 티켓(PR #465, 043이 고침).
- 같은 종류의 회차가 3이라 행의 3회차 표기는 그대로 서고 바꾸지 않았다. 104·399는 설계 시점 틈이라 회차에 더하지 않는 판정은 그대로이고, 닫힘 칸이 그 사건 셋으로 근거를 다시 쓴다. 기준이 된 문장은 `CLAUDE.md` 교정 루프의 "지침으로 적은 뒤에도 어겨지면 막는 훅 후보다"이다.
- 처방의 범위는 "티켓이 모두 done이면 행도 done"까지 그대로이고, `done` 행의 열린 티켓은 정상이라 보지 않는다. 독스트링·티켓의 "두 번 어겨졌다"도 "세 번"으로 고쳤다.

## 셀프 리뷰

인계받은 세션이 돌렸다. base는 origin/main `403c9e96`이고 범위는 커밋 전 작업 트리(수정 1: `.scratch/retro-queue.md`, 미추적 3: 티켓·일지·`tests/test_plan_status.py`, 커밋 0)다. 표준 축(sonnet·high)과 명세 축(기본)을 나란히 돌렸다.

- **Major, 명세 축·표준 축 공통: 닫힘 칸의 "3회차 셈 재판정"이 티켓 수용 기준 5와 어긋난다.** 표준 축은 한 행에 "3회차"와 "회차는 2다"가 같이 있다고, 명세 축은 같은 지적에 더해 "둘뿐"의 반례(skill-plugin 01·02)를 냈다. 반례를 `git log`로 직접 확인했고 사실이었다. 고쳤다. 닫힘 칸을 실제 사건 셋으로 다시 쓰고 3회차를 그대로 세웠으며, 독스트링·티켓의 "두 번 어겨졌다"를 "세 번"으로 고쳤다(위 재판정 절).
- **Minor, 표준 축: 변이 시험 이름이 `test_…을_잡는다` 꼴이 아니다.** 규약(`.claude/rules/tests.md`)에 맞춰 잡는 시험의 이름을 `…을_잡는다` 꼴로 고쳤다. 정상으로 지나는 꼴을 다룬 시험은 이름을 그대로 뒀다.
- **Minor, 명세 축: 독스트링의 "`in-progress` 행에 `done` 티켓이 없는 것도 보지 않는다"에 까닭이 없고 시험이 없다.** 까닭(세 사건이 모두 행이 뒤처진 쪽이고 행을 먼저 올리는 순서까지 막지 않는다)을 독스트링에 더하고, 정상 꼴 시험에 `ready-for-agent` 티켓만 있는 `in-progress` 행을 더했다.
- **Nit, 두 축: 칸이 모두 빈 행(`| | | | | |`)을 구분선으로 보고 말없이 건너뛴다.** 임시 입력으로 `[]`가 나오는 것을 두 축이 각자 보고했다(서브에이전트 보고이고 이 세션이 다시 재지는 않았다). 구분선 판정에 "빈 칸이 아니다"를 더하고 시험(`test_칸이_모두_빈_행을_구분선으로_넘기지_않고_잡는다`)을 더했다. 고침만 `sed`로 되돌려 시험이 `[] == [...]`로 빨개지는 것을 손으로 봤고 원복했다(`grep -n 'if all('`로 77번 줄을 다시 읽었다). 시험은 열두 개가 됐다(`uv run pytest -q tests/test_plan_status.py`가 12 passed).
- **남긴 것.** 표준 축의 `PlanTable` 튜플(Primitive Obsession)과 메시지 틀의 반복(Duplicated Code), 판정 논리와 시험 도우미가 한 파일에 섞인 것(Divergent Change)은 baseline의 판단 항목이고, 같은 꼴의 선례(`tests/test_plugins_boundary.py`)가 있고 호출 자리가 한 파일 안에 닫혀 있어 뒀다.
- **확인하지 못했다고 보고된 것.** PR 번호 #430·#433·#465와 PR #468의 claude-review 인용은 표준 축이 `gh` 복합 명령 가드에 막혀 못 댔다. 명세 축은 #468의 Minor를 확인했다고 보고했다. #463·#462·#461은 이 세션이 `git log`로 확인했다.

## 인계

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 왔다. 이 세션의 제목은 `chore/044-plan-status-matches-tickets-test`이고 넘기기 전에 `chore/044-plan-status-matches-tickets-test (인계함)`으로 바꾼다. 남은 일: 셀프 리뷰와 반영, 티켓 수용 기준의 체크박스를 검증 뒤에 닫기, 이 일지의 검증·회고·`## 다음`, 검증 명령(`uv run python tools/run_checks.py`와 ruff 둘), 커밋, PR, 봇 회차, 병합.

open-session을 부른다 2026-11-05T09:01Z

## 검증 (인계받은 세션)

- `uv run python tools/run_checks.py`를 셀프 리뷰 반영 뒤의 작업 트리로 돌렸다. 종료 코드 0이고 끝 줄이 `pytest Passed (463.4s)`, `web-verify Passed (514.3s)`, 앞의 검사(`check-ticket`·`lint-imports`·`zizmor`·`check-instructions`·`check-type-escapes`·`pyright`·`pyright-linux`·`run-hooks`)도 `Passed`였다(출력의 마지막 25줄을 읽었다). 같은 명령을 반영 전에도 한 번 돌렸고 그것도 종료 코드 0이었으나, 반영 뒤에 다시 돌렸으므로 이 줄이 근거다.
- 손으로 친 ruff 둘: `uv run ruff check .`가 `All checks passed!`, `uv run ruff format --check .`가 `1265 files already formatted`였다.
- `uv run pytest -q tests/test_plan_status.py`가 12 passed였다.
- `-m llm`·`-m llm_widget`·e2e·사진 비교는 돌리지 않았다. `.py` 하나(시험 파일)와 마크다운만 바뀌어 그 갈래를 건드리지 않는다.

## 회고

후보 하나, 승인 0, 기각 1, 넘김 0.

- **기각: 대기열 행의 3회차를 닫힘 칸에서 재판정하며 행의 인용 문구(104·399의 첫 문구, 546의 앞 세션 근거)로만 세어 "둘뿐"이라고 썼다.** 사건: 이 세션 앞쪽이 `git log`로 사건을 세지 않고 문구를 읽어 셌고, 셀프 리뷰 명세 축이 skill-plugin 첫 티켓 둘의 반례를 내 `git log -- .scratch/plan.md`로 확인하고 고쳤다. 리뷰가 제 몫을 한 첫 사건이고, 같은 꼴의 앞 사건은 PR #468의 claude-review가 "셈이 느슨하다"고 짚은 것이라 둘이다. 그래도 둘 다 리뷰가 커밋 전에 잡았고 손상이 없어 새 지침이나 검사를 더하지 않는다. 같은 꼴이 병합까지 간 채 나오면 그때 센다.
- 만료·반영 확인(`tools/queue_open_rows.py`)은 이 세션에서 돌리지 않았다.

## 다음

- 프론티어는 `approval-rules` 하나이고 설계 인터뷰부터다. `docs/approval-rules-design` 세션이 이미 돌고 있으면 그 세션의 몫이다.
- 일지 2026-11-05-04의 "다음"에 적은 `tools/mutate.py`의 `where ` 줄 머리 거짓 양성(독스트링 한 문장과 시험)은 새 harness 티켓이 필요하다(일지 2026-11-05-07의 "다음"에서 이어 받았고 이 일은 건드리지 않았다).
- 이 일(044)이 병합되면 `plan.md`의 기능 행을 바꾸는 PR이 상태와 티켓을 같이 안 맞추면 CI가 빨갛다. 새 기능 행을 열 때 티켓의 `Status:` 줄이 없거나 값이 `ready-for-agent`·`in-progress`·`done`·`wontfix` 밖이면 같은 시험이 잡는다.

## 첫 커밋 시도의 pre-commit (인계받은 세션)

- 첫 `git commit`의 pre-commit에서 `pytest`가 1 failed, 6316 passed로 빨갰다. 실패는 `tests/tools/test_rerun_runner.py::test_본_측정에서_첫_인계_뒤_멈추고_확인_인자를_주면_잇는다`의 `any("인계" in line for line in board.lines)`였다(출력을 읽었다). 이 변경은 그 파일도 `tools/rerun`도 건드리지 않았다(`git diff --stat`의 파일 목록). 그 시험만 홀로 돌리자 통과했다(`uv run pytest -q tests/tools/test_rerun_runner.py -k 첫_인계_뒤_멈추고`, 1 passed, 47.69초). 반영 전후로 돌린 `run_checks.py` 둘은 같은 시험이 통과했다. 원인은 이 PC에서 확인하지 못했고, 한 프로세스에서만 통과하고 xdist에서 빨간 시험의 가능성은 어림이다. 같은 커밋을 다시 시도한다.

## PR 직전 리뷰

- `coderabbit-review` 서브에이전트: `coderabbit auth status`는 `Plan: Free`, `Seat: not assigned`였지만 `coderabbit review --agent --base origin/main`(0.7.5)이 오류 없이 `review_completed`, `findings: 0`으로 끝났다(서브에이전트 보고이고 이 세션이 CLI를 다시 돌리지는 않았다). 그래서 CLI 축이 찼고 대체 둘(`/security-review`, `bug-perf-review`)은 돌리지 않았다. 훑은 파일은 네 개다.
- 밀게 한 주장 셋을 서브에이전트가 직접 댔다. 닫힘 칸의 사건 셋은 `git log`로 맞았고, 독스트링의 "뒤처진 쪽"과 "못 보는 것" 서술은 코드를 읽어 맞았으며, 구분선 수정은 정상 구분선(`['---','---']`, `[':--','--:']`)을 여전히 넘기고 빈 행(`['','','']`)을 행으로 읽는다고 조건을 실제로 돌려 보고했다.
- 보류 판정 하나(Minor, 문체): 독스트링 끝 두 문장이 서술어 없이 명사구로 끝났다. 고치는 값이 작아 고쳤다("도 보지 않는다"를 더했다). 독스트링만 바뀌어 동작은 그대로다.

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `커밋 뒤` 경계에 왔다. 커밋 둘(`e7b6bdf5` 시험·티켓·일지·대기열, `9363f6e5` 독스트링 끝 문장과 PR 직전 리뷰 기록)이 브랜치에 있고 pre-commit이 모두 통과했다. 푸시도 PR도 아직 없다(`gh pr view chore/044-plan-status-matches-tickets-test`가 `no pull requests found`). 이 세션의 제목은 `chore/044-plan-status-matches-tickets-test`이고 넘기기 전에 `chore/044-plan-status-matches-tickets-test (인계함)`으로 바꾼다.

남은 일: 푸시, PR 열기(`/git-pr`. 본문의 자체 점검과 리뷰 결과는 위 "셀프 리뷰"와 "PR 직전 리뷰"를 가리킨다), 첫 `@coderabbitai review` 코멘트, `merge.md` 2의 봇 회차, 병합(워크트리에서 병합하는 길), `tidy-checkouts`. 일지 회고 절과 `## 다음`은 이미 썼으므로 봇 회차 결과만 이 일지에 덧붙인다. PR 직전 리뷰에서 고친 것은 독스트링 문장 하나뿐이라 PR 봇에 밀어 둘 새 사실 문장은 없다.

open-session을 부른다 2026-11-05T09:56Z

## 봇 회차 (PR #470)

- 첫 푸시(`a32a99d`)의 검사는 모두 통과했다(`tools/wait_ci.py` 출력: python·verify·web·e2e·e2e-widget·visual·ticket SUCCESS).
- claude-review 첫 회차: 지적 없음. Nit 하나(판정 논리와 시험 도우미가 한 파일에 섞임)는 PR 본문 "남긴 위험"에 이미 밝힌 것이라 작성자 재량으로 뒀다.
- CodeRabbit: `@coderabbitai review`에 `Review rate limited`로 답해 리뷰가 없었다(무료 OSS 한도). PR 직전 CLI 리뷰가 지적 0건이었다는 것은 위 "PR 직전 리뷰"의 서브에이전트 보고를 옮긴 것이다. 이 세션은 CLI를 돌리지 않았다.
- 푸시 뒤 main이 앞섰다(`b77f158f`, PR #469, ADR 0044). `.scratch/plan.md`를 바꿨으므로 `origin/main`을 합치고 `uv run pytest -q tests/test_plan_status.py`를 다시 돌려 12 passed를 봤다. 앱의 `sync_with_base_branch`는 앱이 만든 워크트리가 아니라는 까닭으로 거부해 `git merge --no-edit origin/main`으로 직접 합쳤다.
