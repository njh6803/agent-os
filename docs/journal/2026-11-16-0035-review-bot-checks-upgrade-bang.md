# 리뷰 봇이 PR의 변경과 제목 접두의 느낌표가 맞는지 본다 (release-image 티켓 06)

브랜치 `feature/06-review-bot-checks-upgrade-bang`.

## 사용자 프롬프트 원문

이 세션의 첫 메시지는 앞 묶음이 낸 지시문이었고, 사용자의 다른 말은 없었다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (중략) 인자: .scratch/release-image/issues/06-review-bot-checks-upgrade-bang.md
>
> 다음 작업: .scratch/release-image/issues/06-review-bot-checks-upgrade-bang.md. 리뷰 봇(claude-review)이 PR의 변경과 제목 접두의 느낌표가 맞는지 보게 한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 1. (중략) EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 모델: Sonnet 5.5 / high
> 이번 요청 범위: PR과 병합까지

## 한 것

- `.github/workflows/claude-code-review.yml`의 프롬프트 3번에 문장을 더했다. 두 축(유지보수성, 경계)에 더해 PR 제목 접두의 느낌표가 변경과 맞는지 본다. 변경이 운영자가 판을 올릴 때 손댈 것을 만드는데 느낌표가 없거나, 만들지 않는데 있으면 짚는다. 기준은 프롬프트에 다시 적지 않고 `docs/constitution/operations.md`의 "릴리스 노트 조각" 절 "느낌표의 기준" 문단을 읽어 적용하라고 가리킨다. 그 문서는 82KB라 통째로 읽으면 한도에 걸리고 Grep은 그 긴 줄의 내용을 생략하므로, Grep으로 줄 번호만 찾고 Read의 offset·limit으로 그 줄만 읽게 적었다(명세 축 리뷰가 짚었다). 맞을 때도 요약에 "느낌표: 맞음"과 이유 한 줄을 적게 해서, 아래 "다음"에서 볼 줄이 안 나온 것이 "안 봤다"인지 "봤고 맞다"인지 가를 수 있게 했다. 느낌표와 `upgrade/` 파일의 짝은 노트 검사가 CI에서 보므로 봇이 보지 않는다고 적어 둘이 같은 것을 두 번 보지 않게 했다.
- 프롬프트 4번의 "범위는 위 두 축뿐이다"를 "위 두 축과 느낌표 맞춤뿐이다"로 고쳤다. 안 고치면 3번의 새 문장과 4번의 범위 제한이 서로 부딪친다.
- 티켓 `Status`를 `in-progress`로 바꿨다가 `done`으로 마친다.

## 확인

- 이 PR이 싣는 파일은 워크플로, 티켓 파일, 이 일지다. 대기열 항목 셋(`0348`·`0555`·`0556`의 상태 줄. 아래 회고의 만료)도 첫 커밋 `f2db3eb37`에는 실었지만, 같은 만료를 `#584`가 `dev`에 먼저 실어 `origin/dev`를 합친 뒤에는 이 PR의 diff에서 빠졌다(`git diff --name-only origin/dev...HEAD`는 파일 셋만 냈다. 손으로 봤다). 모두 워크플로 가드 스텝이 받는 기록 경로다(가드 스텝의 정규식을 읽었고 표준 축 리뷰가 같은 판정을 냈다).
- `uv run python tools/plan_table.py`를 티켓을 `in-progress`로 바꾼 뒤에 돌렸고 `.scratch/plan.md`는 바뀌지 않았다(`git status --short`에 나타나지 않았다). `done`으로 바꾼 뒤에도 같은지는 커밋 전에 다시 본다.
- 워크플로 감사: 이 파일만 `uv run zizmor .github/workflows/claude-code-review.yml`로 따로 돌려 "No findings to report"(억제 4건)를 손으로 봤다. 전체 감사(`--offline --strict-collection --config .github/zizmor.yml .`)는 `tools/run_checks.py`가 돌리며, 그 결과는 아래 "전체 검증"에 적는다.
- 가드 스텝 탐침 `.scratch/harness/probes/review_workflow.py`는 `uv run python`으로 돌려 "어긋남 0/33"을 손으로 봤다. 프롬프트 문장만 바꿨고 가드 스크립트는 건드리지 않았으므로 놀랄 결과는 아니다(어림).
- 프롬프트가 실제로 느낌표 줄을 내는지는 이 PR에서 확인할 수 없다. 이 PR에서는 액션이 리뷰를 건너뛴다(워크플로 검증). 셀프 리뷰와 PR 직전 리뷰가 이 변경의 유일한 리뷰다.

## 셀프 리뷰

`/code-review` 두 축, base `d80690da1`, 파일 여섯과 미추적 일지 하나, 커밋 0개. Critical·Major 없음, 표준 축 Minor 3·Nit 1, 명세 축 지적 7.

- 고친 것: 프롬프트 3번에 "operations.md는 82KB라 통째로 읽지 말고 Grep으로 줄 번호를 찾아 Read의 offset·limit으로 그 문단만 읽는다"를 더했다(명세 축 a3. `wc -c`로 81,847바이트를 손으로 쟀고 `grep -n`으로 기준 문단이 32행임을 봤다). 맞을 때도 요약에 "느낌표: 맞음"과 이유 한 줄을 적게 했다(a2). 워크플로 머리 주석 1행에 느낌표 맞춤을 더했다(표준 Minor 1). 일지의 싣는 파일 서술, 문장 수 서술, 0425 근거를 고쳤다(표준 Minor 2·3, 명세 b1·c1·c2). "다음"에 동작 서술 문서의 후속 수정을 넘겼다(a4).
- 남긴 것: operations.md 리뷰 파이프라인 3과 `CODING_STANDARDS.md` 32행의 낡은 담당 서술은 허용 경로 밖이라 이 PR에서 고치지 않고 병합 뒤 chore로 넘긴다(위 "다음").
- 다시 돌린 명령: 고친 뒤 `uv run zizmor`(지적 없음)와 `review_workflow.py`(어긋남 0/33)를 다시 손으로 쳤다. 전체는 아래.

## 전체 검증

`uv run ruff check . && uv run ruff format --check .`는 통과했다. `uv run python tools/run_checks.py`는 종료 0이었고 항목은 check-notes, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright(둘), run-hooks, pytest, web-verify 모두 Passed였다. 다만 이 러너는 마지막 편집(프롬프트의 Grep·Read 문장, 일지, 티켓 `done`) 전에 시작해 끝났으므로, 그 편집 뒤의 전체는 커밋의 pre-commit 결과로 갈음한다. 워크플로 감사와 지침 검사는 편집 뒤에 따로 손으로 다시 쳤다(zizmor만). `-m llm`·e2e·사진 비교는 워크플로 문장 하나를 바꾼 이 변경에 닿지 않아 치지 않았다(어림).

## 회고

후보 하나, 판정은 기각 하나, 승인과 넘김 없음.

- 기각: `operations.md`의 긴 줄을 Grep으로 찾자 `[Omitted long matching line]`만 나와 줄을 따로 Read로 열어야 했다. 이미 있는 훅이 그 자리에서 알렸다(PostToolUse 알림이 줄 번호를 짚었고, 닫힌 대기열 `0145`가 낸 알림이다). 대기열 `0425`(닫힘, retro 5단계의 행 찾기를 `queue_open_rows.py --search`로 옮겼다)는 대기열 행 찾기의 처방이라 이 사건(코드 문서를 Grep한 것)과 면이 다르다. 훅이 알린 것은 4단계의 기각이다.
- 만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/dev` 두 출력에 모두 든 `0348`·`0555`·`0556`을 만료로 닫았다(상태 줄을 `만료 2026-11-16 (ADR 0036)`로 고쳤다. 닫은 뒤 첫 명령이 만료할 항목 `(없음)`을 찍었다).
- 이 세션에서 반영한 것은 없다.

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 이 세션의 제목은 `feature/06-review-bot-checks-upgrade-bang`이었고 `feature/06-review-bot-checks-upgrade-bang (인계함)`으로 바꿨다. 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없었다). 커밋 `f2db3eb37`까지 했다. pre-commit의 전체 러너가 통과했다(손으로 봤다. 종료 0). 아직 푸시하지 않았고 PR도 없다. 남은 일: `origin/dev`를 합치기(이 세션이 본 `origin/dev`는 `6cc6784`로 앞서 있었다), 푸시, PR(`dev`로), `@coderabbitai review`, 봇 회차, 병합(`merge.md`의 "워크트리에서 병합할 때"). 이 PR은 `claude-code-review.yml`을 고쳐 claude-review가 건너뛰므로 봇 회차는 CodeRabbit만 돈다. 티켓 06은 `done`이고 체크박스는 모두 채웠다.
open-session을 부른다 2026-11-15T16:32Z

## 두 번째 세션: 병합 커밋과 PR 열기

이 세션이 이어받아 PR #589를 `dev`로 열었다. 근거 종류는 문장마다 적는다.

- 인계 줄 커밋 `c1d0d24e5`는 pre-commit 전체 러너가 네 번째 시도에서 통과했다(손으로 봤다. 백그라운드 명령의 종료 코드 0).
- `origin/dev`를 합친 병합 커밋 `aa7258507`은 여덟 번째 시도에서 통과했다(손으로 봤다. 종료 코드 0). 앞의 일곱 번은 매번 다른 시간에 기대는 시험 한두 개가 빨갰다: `tests/channel/cli/test_interrupt.py`의 Ctrl+C 자식 프로세스 30초 제한, `tests/tools/test_rerun_runner.py`(실제 시간 `hang=3.0`을 쓰는 시험), `tests/tools/test_rerun_gates.py`, 첫 시도에서는 `tests/tools/test_probe_kit.py`와 `apps/portal/tools/start.spawn.test.ts`(시작 로그 30초 제한). 모두 `uv run pytest -q <그 파일>`이나 `pnpm -C web exec vitest run <그 파일>`로 단독으로 쳐서 통과했다(손으로 봤다). 그때 기계의 CPU는 88%였고 다른 Claude 세션의 프로세스들이 쥐고 있었다(`Get-CimInstance Win32_Processor`로 손으로 봤다. 이 세션이 띄운 프로세스가 아니었다는 것은 프로세스 목록에서 읽은 어림이다). 한 번에 20~30분이 걸렸다. 사용자가 "계속 재시도"를 골랐고 훅은 건너뛰지 않았다.
- 푸시하려 하자 `hook_push_behind`가 `origin/dev`가 5커밋 앞섰다고 막았다. 기다린 사이에 `#583`·`#584`·`#586`, 출시 PR `#587`과 되돌려 합치기 `#588`이 들어갔다. `git merge origin/dev`로 다시 합쳤고 충돌이 없었으며 pre-commit은 커밋 메시지 검사만 돌았다(손으로 봤다. 출력의 `Passed` 한 줄). 그 뒤 `sibling_overlap.py`는 번호 겹침 없음, `plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았다(둘 다 손으로 봤다). 이 마지막 병합 커밋 `origin/dev` 5커밋의 전체 검사는 CI가 본다.
- PR #589를 열었다. 제목은 `chore: 리뷰 봇이 PR의 변경과 제목 접두의 느낌표가 맞는지 보게 한다 (06-review-bot-checks-upgrade-bang)`이고 느낌표는 없다(이 변경은 운영자가 올릴 때 손댈 것을 만들지 않는다. 판단이다).
- PR 직전 리뷰: `coderabbit-review` 서브에이전트가 CodeRabbit CLI 0.7.5로 `--base origin/dev`를 붙여 돌렸고 지적 0건으로 끝났다(보고를 받았다. `Plan: Free`, `Seat: not assigned`에서도 리뷰는 정상 완료). 서브에이전트가 손으로 본 것은 Minor 2·Nit 2였고 모두 비차단이다. 하나는 위 "확인"의 대기열 항목 서술이라 고쳤다. 또 하나는 프롬프트가 Grep은 긴 줄의 내용을 생략하고 번호만 준다고 적은 것이 도구의 현재 출력 방식에 기댄 가정이라는 것이다. 지금 모양을 유지하고 아래 "다음"의 후속(병합 뒤 느낌표 줄이 실제로 나오는지 보기)이 덮는다.
- 회고 후보 하나(이 세션은 판정하지 않는다): 시간에 기대는 시험(Ctrl+C 30초 제한, 러너 재시도 시험들)이 다른 세션이 CPU를 쓰는 기계에서 병합 커밋의 pre-commit을 일곱 번 연달아 빨갛게 했다. 회차를 세는 대기열 항목은 만들지 않았다. 이 세션이 한 사건이고 같은 실수의 다섯 번째인지는 `uv run python tools/queue_open_rows.py --search`로 보지 못했다.

## 인계 (PR 연 뒤)

컨텍스트가 인계 문턱(200,000)을 넘은 채 `PR 연 뒤` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 이 세션의 제목은 `feature/06-review-bot-checks-upgrade-bang`이었고 `feature/06-review-bot-checks-upgrade-bang (인계함)`으로 바꾼다. 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없었다. 손으로 봤다). PR #589는 열렸고, 이 일지의 두 번째 세션 절은 아직 커밋하지 않았다. 남은 일: 일지 커밋과 푸시, 첫 `@coderabbitai review` 코멘트, 봇 회차(claude-review는 이 PR이 워크플로를 고쳐 건너뛰므로 CodeRabbit만), 병합(`merge.md`의 "워크트리에서 병합할 때"). 지금 기계가 느려 pre-commit이 시간에 기대는 시험으로 빨갈 수 있다. 사용자가 이 일의 재시도를 골랐으므로 훅을 건너뛰지 않고 다시 시도한다.
open-session을 부른다 2026-11-16T03:53Z

## 세 번째 세션: 일지 커밋

이 세션이 인계를 받아 일지 커밋을 시도했다. 근거 종류는 문장마다 적는다.

- 첫 시도의 pre-commit은 전체 러너가 모두 통과했다(백그라운드 출력 파일의 `Passed` 줄을 손으로 봤다. pytest 1211.9초, web-verify 1242.4초). 마지막 `commit-msg` 검사가 제목 74자가 72자를 넘는다며 막았다(같은 출력의 `제목 74자 > 72자`를 손으로 봤다). 제목을 줄여 다시 커밋했다(두 번째 시도의 결과는 이 커밋이 들었다는 사실이 갈음한다).
- 인용 대조 경고가 일지 64행의 따옴표 인용 하나에 났다(같은 출력을 손으로 봤다. 막는 검사는 아니다). 따옴표를 떼고 문장으로 풀어 고쳤다.

## 다음

이 PR은 동작을 서술하는 문서를 고치지 못한다(PR 서식이 허용 경로 밖의 문서는 병합 뒤 따로 고치라고 정했다). 병합 뒤 따로 고칠 자리는 `docs/constitution/operations.md` 리뷰 파이프라인 3(claude-review 담당을 "유지보수성과 경계"로만 적었다)과 `CODING_STANDARDS.md` 32행("이 넷과 경계는 PR의 Claude Code Review가 본다")이다. 느낌표 맞춤을 한 구절씩 더한다. 작은 문서 고침이라 병합한 세션이 다음 티켓 PR에 싣지 않고 따로 chore로 연다.

병합한 세션은 이 변경이 dev에 오른 뒤 처음 열리는 티켓 PR(07·08·09 가운데 먼저 열리는 것)에서 claude-review의 요약 코멘트가 느낌표를 판정하는 줄("느낌표" 또는 "접두"를 말하는 지적이나 확인 한 줄)을 내는지, 그 PR의 세션이 일지에 적게 한다. 줄이 없으면 프롬프트 문장이 약한 것이므로 `claude-code-review.yml`을 고치는 새 PR을 따로 연다. 그 PR도 다른 파일과 함께 싣지 않는다.
