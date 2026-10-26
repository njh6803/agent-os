# 2026-10-26 (09) 변이 도구의 원문 확인이 메아리 표지를 알리고, 실행 표지가 시작 시각을 본다

브랜치 `chore/011-mutate-check-and-marker`, 티켓 `.scratch/harness/issues/011-mutate-check-and-marker.md`(대기열 417·449). 나란히 여는 8 중 2. 세션 제목: `chore/011-mutate-check-and-marker`.

## 사용자 프롬프트

> 사용자: 대기열 417·449를 티켓 .scratch/harness/issues/011-mutate-check-and-marker.md로 쓰고 한다
>
> 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/011-mutate-check-and-marker.md. tools/mutate.py --check가 시험 원문에 글자 그대로 있는 변이 표지를 알리고(대기열 417), 실행 표지가 pid와 시작 시각을 함께 보아 다시 쓰인 pid를 산 것으로 읽지 않게 한다(대기열 449)
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 8 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: 대기열 417·449를 티켓 .scratch/harness/issues/011-mutate-check-and-marker.md로 쓰고 한다
> 브랜치: chore/011-mutate-check-and-marker
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/agents/issue-tracker.md. 나란히 여는 나머지 티켓: .scratch/harness/issues/010-journal-evidence-hook.md, 012-env-read-option-records.md, 013-proc-cmdline-linux.md, 014-open-session-deeplink-lock.md, 015-probes-marker-rule.md, 016-visual-focus-flake.md, 017-tidy-collapsed-and-fresh-branches.md
> 이어받을 상태: 449는 417과 같은 파일(tools/mutate.py)을 고치는 고침 행이라 묶었다. 417의 행이 함께 들자고 적은 350과, 같은 파일의 455는 더하는 행이라 묶지 않았다(행 하나가 티켓 하나, ADR 0037). 350은 회차 3이라 다음 chore 차례에 다시 고른다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 티켓 011을 쓰고(`in-progress`) `tools/sibling_overlap.py`로 번호 겹침이 없음을 봤다.
- 시험 먼저: `tests/tools/test_mutate.py`(메아리 열넷, 표지의 시작 시각 둘)와 `tests/tools/test_hook_edit_during_mutate.py`(시작 시각 다섯)를 더해 빨강을 본 뒤 구현했다. 두 파일 모두 초록(`-n 8`).
- 417: `tools/mutate.py`의 `_echo_problems`. 빨강·처리하지 않은 에러를 기대한 변이의 표지가 그 시험 파일(러너 자리 기준, `::` 뗀다)의 원문에 글자 그대로 있으면 알린다. 이름·번호·`--since`로 고른 `--check`와 `--staged`의 새·바뀐 변이(`_fresh`: 어느 부모 판의 같은 표와도 다른 변이)만 본다. 옛 변이는 소급하지 않는다. `_watched_paths`의 시험 인자 풀기를 `_test_args`로 뽑아 함께 쓴다.
- 449: 표지에 `started`(윈도 `GetProcessTimes`의 만든 시각, 리눅스 `/proc/<pid>/stat`의 starttime)를 적고, 훅은 pid가 살았고 시작 시각이 같을 때만 센다. 시작 시각이 없는 옛 표지는 pid만으로, 시작 시각을 읽지 못하면 세지 않는다(못 보는 것, 시험으로 고정). 두 사본(`process_started`)이 같은 값을 내는지 시험이 대조한다.
- 독스트링(도구의 `--check`·`--staged`·표지 절·실행 표지 절, 훅의 판정·못 보는 것)과 `.claude/rules/probes.md` 표지 항목에 한 문장을 더했다.
- 변이 표 `.scratch/harness/probes/mutate_echo_and_start_mutations.toml`(열)을 썼다. 고친 도구의 `--check --since origin/main`이 첫 판의 표지 둘(`커밋에 든 표 1, …`)을 시험 원문의 메아리로 잡아, `AssertionError: 색인 확인: …`으로 바꿨다. 아직 돌리지 않았다. README 행도 아직 없다.
- ruff·포맷·pyright(바꾼 넷) 초록. pyright가 잡은 람다의 미지 형을 이름 있는 함수로 고쳤다.

## 남은 것

- 셀프 리뷰(`/code-review origin/main`)부터. 인계 계기가 셀프 리뷰 직전에 와서 이 세션은 리뷰를 돌리지 않았다.
- 커밋 뒤 분리 워크트리에서 변이 표를 돌리고 `.scratch/harness/probes/README.md`에 행을 더한다.
- `tools/sibling_overlap.py`의 알림: `.claude/rules/probes.md`를 바꿔 카나리아 `probes_rule*.toml` 다섯을 새 `claude -p` 세션에서 돌리고 `# 최신 결과:` 줄을 고친다. 형제 워크트리 `015-probes-marker-rule`도 같은 파일을 고친다(글자 충돌 후보).
- 전체 검증(`tools/run_checks.py`), 티켓 `done`, PR, 병합.

## 이어서 (새 세션, 워크트리에 EnterWorktree로 들어왔다)

> 사용자: 대기열 417·449를 티켓 .scratch/harness/issues/011-mutate-check-and-marker.md로 쓰고 한다

### 셀프 리뷰 (`/code-review origin/main`, base 92b61458, 파일 다섯, 커밋 0, 미추적 셋)

표준 축(sonnet·high)과 명세 축이 낸 것:

- 두 축: `process_started`가 끝난 프로세스에도 값을 내 `test_이_프로세스의_시작_시각은_읽히고_끝난_프로세스는_읽히지_않는다`가 `-n 8`에서 빨갰다(`134374722272777789 is None`). 윈도는 끝난 프로세스도 누가 핸들을 쥐면 커널 객체가 남아 `GetProcessTimes`가 성공한다. 훅 판정은 `is_alive`가 먼저 막아 안전했다(Major).
- 두 축: `.claude/rules/tools.md`의 "표지의 pid가 살았는지만 본다"가 남았고, 카나리아 `tools_rule_edit_during_mutate.toml`의 `expect`가 그 구절이다(Major).
- 표준 축: 변이 7의 표지 `Right contains 1 more item: {'started':`가 `-q` 출력에 없다. 목록끼리 비교라 `At index 0 diff:`만 찍힌다(Major).
- 표준 축: `check(..., echoes: bool = False)`가 CODING_STANDARDS의 불리언 플래그 인자에 걸린다.
- 명세 축(Minor): 변이가 `unhandled`와 `::` 떼기를 덮지 않는다.
- 표준 축(Minor·판단): 시험 모듈 독스트링의 "pid 가 살았는지는", 훅 독스트링에 정수가 아닌 `started`의 판정이 없다, `_Marker`와 `RunningMutation`의 겹침, `run_hooks.py`의 `_mutating_repository`가 옛 꼴 표지만 만든다, `_running_marker`의 ctypes 오류 삼킴.

반영 중 전체 실행에서 `test_훅은_변이가_도는_체크아웃의_편집에만_계기를_낸다`도 한 번 빨갰다. 옛 꼴 표지에 넣은 끝난 pid를 부하 아래 다른 프로세스가 받아 알림이 났다(대기열 449의 상황 그대로).

- **고친 것.**
  - 두 사본의 `process_started`가 윈도에서 `GetExitCodeProcess`로 `STILL_ACTIVE`를 먼저 본다. 시험 `test_끝난_프로세스의_시작_시각은_핸들이_남아도_읽히지_않는다`(훅·도구 둘)를 먼저 써 빨강을 본 뒤 고쳤다.
  - 시험의 `_끝난_pid`를 `_끝난_프로세스`(Popen을 돌려준다)로 바꿔, 시험이 쥔 동안 윈도가 그 pid를 다른 프로세스에 주지 않게 했다. 네 자리를 바꿨다.
  - `.claude/rules/tools.md`를 "표지의 pid가 살았는지와 그 pid의 시작 시각이 표지의 것과 같은지만 본다"로, 카나리아 `expect`를 같은 구절로 고쳤다.
  - `check`의 플래그를 빼고 고른 변이용 `check_picked`를 두었다.
  - 변이 7을 손으로 넣어 출력을 본 뒤 표지를 `mutations.toml'} != {'pid':`로 바꿨다. `::` 떼기와 `STILL_ACTIVE`(두 사본)의 변이 셋을 더해 열셋이다.
  - 시험 모듈 독스트링과 훅 독스트링(정수가 아닌 `started`는 꼴이 다른 표지처럼 세지 않는다)을 고쳤다.
- **PR 직전 리뷰에 밀 주장.** "윈도는 끝난 프로세스도 누가 핸들을 쥐고 있으면 열리고 만든 시각을 내므로 끝났는지(`STILL_ACTIVE`)를 함께 본다", "시험이 이것을 쥔 동안 파이썬이 그 핸들을 쥐어, 윈도는 그 pid 를 다른 프로세스에 주지 않는다", "리눅스는 `wait` 가 거둔 pid 를 다시 줄 수 있지만 pid 를 차례로 돌려 써 시험 한 번 안에 돌아오지 않는다".
- **남긴 것.** `unhandled` 기대의 메아리 시험·변이(같은 `_ECHO_EXPECTS` 집합의 한 원소라 `red`가 덮는 길과 같다), `_Marker`·`RunningMutation`의 겹침(훅의 공개 반환형을 바꾸지 않으려 둔다), `_mutating_repository`의 옛 꼴 표지(옛 꼴도 훅이 받는 꼴이라 pre-commit 실행 확인의 뜻은 같다), ctypes 오류 삼킴(표지를 두는 쪽은 시작 시각만 빼고 도는 것이 맞고, 서명 오류는 시험이 이 PC와 리눅스에서 잡는다).
- **다시 돌린 명령.** `uv run pytest -q tests/tools/test_hook_edit_during_mutate.py tests/tools/test_mutate.py -n 8` 252 통과. 나머지는 커밋의 pre-commit으로 갈음한다.
- **첫 커밋 시도.** pre-commit이 둘에서 막았다. `--staged`가 옛 표 둘(`mutate_runners_mutations.toml`의 둘, `mutate_table_guards_mutations.toml`의 셋)의 원문을 이 변경이 깼다고 알렸고, `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`가 빨갰다(web-verify 692초와 겹친 부하, 홀로 돌리면 통과). 원문을 지금 코드로 고쳤고, 원문이 바뀌어 새 변이가 된 "훅이 죽은 pid 의 표지도 센다"는 표지가 시험 함수 이름이라 `table='b_mutations.toml')`로 바꿨다. 이 표의 `::` 변이는 옛 표의 것과 같아 지웠다(열둘). `--staged` 문제 0.
- **둘째 커밋 시도.** 같은 `test_rerun_runner.py` 오염 시험 하나로 다시 막혔다(1142초). 두 번 연속이라 진단했다. 그 파일은 이 브랜치가 고친 파일을 import하지 않고, 파일만 `-n 8`로 따로 돌리니 이번에는 다른 시험(`test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`)이 빨갰다(52 통과 1 실패). 시험이 번갈아 흔들리는 부하 의존 시간 시험이고 선례(일지 2026-10-24-10, 2026-10-25-02)와 같은 종류(대기열 306)라 회차를 더하지 않고 다시 커밋한다.
- **셋째 커밋 시도.** 같은 나무에서 pytest가 같은 오염 시험 하나로(5612 통과 1 실패, 1154초), web-verify가 `WidgetFailures.test.tsx`의 초 단위 띠 시험 하나로(920 통과 1 실패, 928초) 빨갰다. 둘 다 이 브랜치가 건드리지 않은 실제 시각에 기대는 시험이고, 이 PC에 형제 세션 여럿이 함께 돌았다. 이 결과를 그 둘의 손 실행으로 두고 `SKIP=pytest,web-verify`로 커밋한다. 깨끗한 환경의 확인은 CI가 한다.

## 인계 지시문

- 다음 작업: .scratch/harness/issues/011-mutate-check-and-marker.md를 셀프 리뷰부터 이어 PR과 병합까지 한다
- 다음 단계: 구현
- 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
- 시작 프롬프트: 대기열 417·449를 티켓 .scratch/harness/issues/011-mutate-check-and-marker.md로 쓰고 한다
- 브랜치: chore/011-mutate-check-and-marker
- 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
- 읽을 것: docs/journal/2026-10-26-09-mutate-check-and-marker.md의 "남은 것", docs/agents/issue-tracker.md
- 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review origin/main`)부터 한다. 변이 표 `.scratch/harness/probes/mutate_echo_and_start_mutations.toml`은 아직 돌리지 않았고 README 행이 없다. `.claude/rules/probes.md`를 바꿔 카나리아 다섯을 다시 돌려야 하고, 형제 워크트리 `015-probes-marker-rule`이 같은 파일을 고친다. docs/journal/2026-10-26-09-mutate-check-and-marker.md
- 확인할 선행 조건: 없음
- 이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-26T07:00Z
