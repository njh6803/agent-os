# wait_ci가 CodeRabbit의 체크 런 제목을 설명처럼 읽게 한다 (harness wait-ci-coderabbit-check-run)

세션 제목: `chore/wait-ci-coderabbit-check-run` (인계하며 `chore/wait-ci-coderabbit-check-run (인계함)`으로 바꾼다). 브랜치 `chore/wait-ci-coderabbit-check-run`, 워크트리 `C:\project\agent\.claude\worktrees\wait-ci-coderabbit-check-run`. 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

> 사용자: 대기열 499를 티켓 .scratch/harness/issues/wait-ci-coderabbit-check-run.md로 쓰고 한다

지시문의 이번 요청 범위는 PR과 병합까지다. 이어받을 상태는 없었다. 지시문은 나란히 여는 다섯 가운데 둘째이고, 첫 세션이 `tidy-checkouts`를 돈다.

## 한 것

- **티켓.** `.scratch/harness/issues/wait-ci-coderabbit-check-run.md`를 `in-progress`로 먼저 썼고 지금은 `done`이며 수용 기준을 모두 표시했다(마지막 줄 "검증 명령이 모두 초록이다"는 아래 검증 절의 남은 일을 끝낸 뒤에야 참이다). 브랜치는 워크트리를 만들 때 붙은 `worktree-…`를 `chore/wait-ci-coderabbit-check-run`으로 바꿨다.
- **CodeRabbit의 실제 모양.** `gh api repos/{owner}/{repo}/commits/<헤드>/check-runs`와 같은 헤드의 `/status`를 손으로 읽었다(2026-11-08). PR #489 헤드는 combined status가 비고 체크 런 하나가 `skipped`와 `Review skipped: manual review required for this OSS repository`였다. PR #401 헤드는 `neutral`과 `Review rate limited`, PR #405 헤드는 `success`와 `Finished`(요약 첫 줄은 `Result: Success - Review completed`)였다. `gh pr view --json statusCheckRollup`의 CheckRun 항목에는 `output`이 없다. 리뷰가 진행 중일 때의 체크 런 제목은 보지 못했다.
- **`tools/wait_ci.py`.** `fetch_pr`가 `…/commits/<헤드>/check-runs?per_page=100`도 읽어 `check_runs` 칸으로 붙인다. `parse_snapshot`은 `output.title`이 비지 않은 체크 런을 StatusContext처럼 읽는다. 제목은 `notes`로, 상태는 그 목록의 `status`와 `conclusion`으로 간다(롤업과 목록은 시각이 달라서다). 제목이 없는 체크 런(GitHub Actions)은 롤업의 것을 그대로 둔다. combined status 길은 그대로다. 독스트링에 CodeRabbit의 체크 런 모양을 적고, 못 보는 것 셋(진행 중 제목, 파일 수 한도의 체크 런 모양, 100개 넘는 목록)을 더했다.
- **시험.** `tests/tools/test_wait_ci.py`에 헬퍼 `coderabbit_run`을 더하고 `payload`가 `check_runs` 칸을 낸다. 시험 여덟을 더했다(건너뜀 제목이 요청 전으로 세어진다, 롤업이 건너뜀을 보는 사이 목록이 진행 중이면 끝나지 않았다, 제목 없는 체크 런을 설명으로 읽지 않는다, 한도·완료 제목이 통과 줄에 붙는다 둘, 건너뜀이면 요청 유예 뒤 종료 4, 건너뜀에서 진행을 거쳐 끝까지 기다린다, `fetch_pr`가 `check_runs`를 붙이고 시간 제한을 지킨다, 체크 런 조회 실패는 조회 실패다). 고치기 전에 첫 시험이 `notes`가 빈 채로 빨갛게 되는 것을 봤다.
- **변이.** `.scratch/harness/probes/wait_ci_mutations.toml`에 45~48번을 더했다(제목을 읽지 않는다, 상태를 롤업에서만 읽는다, 제목 없는 체크 런의 제목도 담는다, 목록을 붙이지 않는다). 표 전체를 돌려 48개가 기대대로(빨강 47, 초록 대조군 1)였고 새 넷은 `expect_output` 표지까지 맞았다. 이후 독스트링과 시험 형식만 바뀐 뒤 고른 `--check`(45~48)는 통과했다.
- **대기열.** `.scratch/retro-queue/0499.md`의 상태를 닫힘으로 바꿨다.

## 번복하거나 고친 것

- **`next-session`의 `merge.md` 2 대기 문장.** 처음에는 완료 제목 `Finished`를 괄호에 더했다. `uv run python tools/sibling_overlap.py`가 그 파일이 카나리아 명세 아홉 개(`next_session_*.toml`)의 원천이라 새 `claude -p` 세션으로 다시 돌리고 `# 최신 결과:` 줄을 고치라고 알려, 되돌렸다. 끝 줄의 모양은 그대로여서 그 문장은 고치지 않았고, 까닭은 티켓의 수용 기준 여섯째 칸에 적었다. 체크 런 모양의 `Finished`는 `wait_ci.py` 독스트링에만 있다.
- **줄 길이와 형식.** 시험의 긴 줄과 `ruff format`이 줄 하나를 다시 감았다. pyright가 시험의 `body`를 `partially unknown`으로 냈고 `body: Json`으로 고쳤다.

## 검증

근거의 종류. 아래는 이 세션에서 그 명령을 직접 돌려 출력에서 읽은 것이다.

- `uv run python tools/run_checks.py`(백그라운드, 약 23분)에서 `check-ticket`·`zizmor`·`check-instructions`·`lint-imports`·`check-type-escapes`·`run-hooks`·`web-verify`가 통과였다. `pyright`는 `test_wait_ci.py`의 `body` 하나로 실패했고 고친 뒤 `uv run pyright`가 통과했다. `pytest`는 6585개 가운데 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 `assert 1 == 2`로 실패했다(동시 실행 수를 재는 시간 단언이다. 이 변경이 닿지 않는 파일이다). 그 파일만 홀로 돌리면 통과였다. 원인(다른 세션이 함께 돌아 느려졌다)은 재지 않았다.
- `uv run ruff check . && uv run ruff format --check .`와 `uv run pytest tests/tools/test_wait_ci.py -q`(67개)는 통과였다. 변이 표 전체는 위 한 것의 대로다.
- 고친 파일 넷(`tools/wait_ci.py`, `tests/tools/test_wait_ci.py`, 변이 표, 대기열 0499)과 새 파일 둘(티켓, 이 일지)이 아직 커밋되지 않았다. `uv run python tools/plan_table.py`는 변경 없이 끝났다(harness 티켓은 전체 계획에 들지 않는다).
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음. origin/main이 `cfc5ac0`으로 옮겨졌고(`git diff --name-only HEAD...origin/main`) 바뀐 파일(`.scratch/approval-rules/…`, 대기열 0457~0466, 일지 하나, `tests/test_main.py`)은 이 브랜치와 겹치지 않는다.

## 셀프 리뷰 (`/code-review`, 기준 `778db404`)

범위: 고친 파일 넷과 새 파일 둘, 커밋 0, 미추적 2. 표준 축 서브에이전트(sonnet·high)와 명세 축 서브에이전트가 돌았고 Critical·Major는 없었다.

- **고친 것.** (1) 독스트링 "판정." 문단과 `parse_snapshot`·`Snapshot` 독스트링이 새 체크 런 조회를 빠뜨려 적었다(명세 축 a3, 표준 축 3). (2) `wait_ci.py` 독스트링의 "2026-11 무렵부터"를 "2026-10-26 무렵부터"로 고쳤다. `gh pr view 390 --json createdAt`이 `2026-10-26T11:18:33Z`(상태 설명 모양), `gh pr view 396`이 `2026-10-26T17:37:48Z`(체크 런 모양)였다(손으로 봤다). (3) "시험 일곱"을 "시험 여덟"로 고쳤다(`git diff 778db404 -- tests/tools/test_wait_ci.py | grep -c '^+def test_'`가 8). (4) 공백뿐인 제목 `"  "`이 설명으로 담기던 것을 `.strip()`으로 걸렀고, `test_제목이_없는_체크_런은_설명으로_읽지_않는다`에 공백 제목을 더했다. `.strip()`을 빼면 `Left contains 1 more item: {'lint': '  '}`로 빨갛다(손으로 돌렸다). (5) `.scratch/harness/probes/README.md`의 `wait_ci_mutations.toml` 행에 변이 넷과 결과를 더했다.
- **남긴 것.** 같은 이름의 체크 런이 둘일 때 뒤의 것이 이기는 것(체크 런 목록은 기본이 최신이라 어림으로 실해 가능성이 낮다), 같은 이름이 `statuses`에도 있으면 StatusContext가 덮는 것(티켓이 정하지 않았고 겹침을 본 적이 없다), `parse_snapshot`의 같은 모양 루프 둘과 시험 헬퍼의 닮음(smell 판단 항목이라 추출하지 않는다), 롤업 `FAILURE`와 목록 `success`가 어긋나는 시각 차(지금은 영향 없음, 티켓 범위 밖).
- **다시 돌린 명령.** `uv run pytest tests/tools/test_wait_ci.py -q` 67개 통과, `uv run ruff check`와 `ruff format --check` 통과. 전체 게이트는 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤 적는다.

## PR 직전 리뷰

CLI는 `coderabbit auth status`가 `Seat: not assigned`라 돌리지 않았고(손으로 봤다) 대체 둘을 돌렸다.

- **`/security-review`.** 지적 0건. 새 `gh api` 호출은 셸 없는 인자 목록이고 경로의 헤드는 GitHub이 준 SHA다. 체크 런 제목은 출력 줄에만 닿는다(코드를 읽었다).
- **`bug-perf-review`.** 유효 1건(Minor). 제목이 없는 체크 런이 `in_progress`이고 롤업에 `SKIPPED`가 남으면 `parse_snapshot`이 목록의 항목을 건너뛰어 `judge`가 `done=True`를 낸다(서브에이전트가 `uv run python`으로 불렀다). 독스트링의 못 보는 것 절이 진행 중을 `status`가 `completed`가 아닌 것으로 판정한다고 적은 것과도 어긋났다.
  - 고친 것: 제목이 없어도 `status`가 `completed`가 아니면 `checks[name] = None`으로 읽는다. 제목이 없고 끝난 체크 런만 건너뛴다. 독스트링 두 곳과 코드 주석을 맞췄고, 시험 `test_제목이_없는_진행_중_체크_런도_끝나지_않은_것으로_읽는다`와 변이 49번을 더했다. 변이 45·47의 원문은 새 코드 모양에 맞췄다. 번호로 45~49를 돌려 모두 기대대로였다(47의 표지는 `Left contains 3 more items`로 고침).
  - 판단 근거: 이 틈은 롤업과 목록의 시각 차가 겹쳐야 나서 흔하지 않을 수 있으나, 고치는 값이 작고 독스트링이 이미 그렇게 약속했다.
- **확인했고 문제 없는 길(서브에이전트가 입력으로 확인했다).** 완료인데 conclusion이 null이면 UNKNOWN으로 실패 취급, 새 호출도 `CALL_TIMEOUT`과 `FetchError`를 지난다, 100개 넘는 목록은 독스트링이 한계로 적었다.

남은 일: 고친 판의 커밋과 푸시, PR, 봇 회차와 병합까지다.

## 인계

컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 인계한다(`handoff.md`). 제목을 `chore/wait-ci-coderabbit-check-run (인계함)`으로 바꿨고 워크트리 잠금을 풀었다. 도는 백그라운드 작업은 없었다.

open-session을 부른다 2026-11-07T17:53Z

## 두 번째 세션 (`커밋 뒤`에서 인계)

사용자 프롬프트는 같다: `> 사용자: 대기열 499를 티켓 .scratch/harness/issues/wait-ci-coderabbit-check-run.md로 쓰고 한다`. 이번 세션 제목은 `chore/wait-ci-coderabbit-check-run`, 모델 Sonnet 5.5 / high.

- **한 것.** 셀프 리뷰(`/code-review`, 기준 `778db404`)를 돌려 반영했고(위 절), `origin/main`(`cfc5ac01`)을 직접 `git merge origin/main`으로 합쳤고(충돌 없음, 앱의 `sync_with_base_branch`는 "앱이 만든 워크트리가 아니다"로 거절했다), PR 직전 리뷰(위 절)를 돌려 반영했다. 커밋은 셋이다: `7ba03c83`(본체), `933500e2`(병합), `c4ff0b0e`(PR 직전 리뷰 반영).
- **검증.** 첫 커밋(`7ba03c83`)의 pre-commit은 pytest 6585개 포함 모두 통과였다. 둘째 커밋을 처음 시도했을 때 `tests/channel/cli/test_interrupt.py::test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다`가 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"로 실패했다(pre-commit 출력에서 읽었다). 이 변경이 닿지 않는 파일이고, 그 파일만 홀로 돌리면 6개가 34초에 통과였다(손으로 돌렸다). 원인(다른 세션이 함께 돌아 느려졌는지)은 재지 않았다. 같은 커밋을 다시 시도해 통과했다. 이 시험이 두 번 실패한 것이 아니라 한 번이다.
- **푸시하지 않은 것.** 아직 푸시하지 않았다. `git push`가 `hook_push_behind_main`에 막혀 `origin/main`을 합친 뒤에 하려던 참이었고, 합친 뒤 `c4ff0b0e`가 더해졌다. PR도 열지 않았다.
- **남은 일.** `origin/main`이 또 움직였는지 `git fetch`로 본 뒤 푸시, PR 열기(제목 꼬리 `(harness wait-ci-coderabbit-check-run)`, 본문은 `#489`처럼 변경사항·왜·남긴 위험·체크리스트, 체크리스트의 PR 직전 리뷰 줄에는 위 "PR 직전 리뷰" 절을 옮긴다), `@coderabbitai review` 코멘트, `merge.md` 2의 봇 회차와 병합까지다.
- **PR 본문에 옮길 남긴 위험.** 같은 이름 체크 런이 둘일 때 뒤의 것이 이기는 것, statuses가 체크 런을 덮는 것, 롤업 FAILURE와 목록 success의 시각 차(위 "셀프 리뷰"의 남긴 것). 파일 수 한도(대기열 374)의 체크 런 모양과 진행 중 제목은 보지 못했다(독스트링의 못 보는 것).
- **셀프 리뷰·PR 직전 리뷰로 새로 쓴 사실 문장(다음 리뷰층에 밀 주장).** `wait_ci.py` 독스트링의 "2026-10-26 무렵부터"(`gh pr view 390`의 `createdAt`이 `2026-10-26T11:18:33Z`, 396이 `2026-10-26T17:37:48Z`, 손으로 봤다), "제목이 없어도 `status`가 `completed`가 아니면 진행 중으로 읽는다", probes README 행의 "마흔아홉"과 "45~49를 번호로 돌려 모두 기대대로".

open-session을 부른다 2026-11-07T19:33Z
인계 못함 커밋 뒤: `tools/open_session.ps1`을 부르는 PowerShell 호출을 자동 모드 분류기가 "dangerous"로 거부했다(까닭 설명 없음). 제목을 되돌렸고 이 세션이 푸시, PR, 병합을 잇는다.

이어 한 것: `origin/main`(`dd1c0190`, PR #491)을 `git merge origin/main`으로 한 번 더 합쳤다(겹치는 파일 없음, 커밋 `3c0ec54e`). 푸시하고 PR [#493](https://github.com/njh6803/agent-os/pull/493)을 열었다. 앱이 PR을 이미 이 세션에 묶었다(`get_status`가 `bound: true`). 일지의 미커밋 줄은 이 커밋에 싣는다.
