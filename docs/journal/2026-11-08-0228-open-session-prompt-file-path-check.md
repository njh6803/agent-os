# 인계 열기 스크립트가 -PromptFile과 -Folder를 스스로 좁힌다 (open-session-prompt-file-path-check)

브랜치 `chore/open-session-prompt-file-path-check`, 티켓 `.scratch/harness/issues/open-session-prompt-file-path-check.md`, 대기열 498.

## 사용자 프롬프트

> 사용자: 대기열 498을 티켓 .scratch/harness/issues/open-session-prompt-file-path-check.md로 쓰고 한다 (next-session 지시문으로 열린 세션. 이번 요청 범위: PR과 병합까지)

## 이 세션이 한 것

- 세션 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌았다. 루트는 이미 `origin/main`과 같았다. 쉬는 세션이 쥔 병합된 워크트리 셋(`01-retro-threshold-five`, `02-retro-queue-one-file-per-item`, `public-demo-plan`)을 `end-holders`로 풀고 지웠다.
- 워크트리 `open-session-prompt-file-path-check`에 들어가 브랜치를 `chore/open-session-prompt-file-path-check`로 바꿨다.
- 티켓을 썼고(상태 `done`으로 올려 두었다), `tools/open_session.ps1`에 `Get-PromptRoot`·`Resolve-PromptFile`·`Test-RepoFolder`·`Get-RepoRoots`를 더했고 `Send-Prompt`가 읽기 전에 부르게 했다. 읽기는 `-LiteralPath`다.
  - `Resolve-PromptFile`: 경로를 정규화해 `<임시 폴더>\claude` 아래인지 보고(접두만 같은 형제 폴더는 아니다) 파일에서 그 폴더까지 올라가며 링크가 있으면 멈춘다.
  - `Test-RepoFolder`: `-Folder`가 스크립트가 든 저장소의 뿌리(워크트리면 그 주 체크아웃 포함)와 같을 때만 받는다. 뿌리는 `git -C $PSScriptRoot rev-parse --path-format=absolute --git-common-dir`의 부모와 `$PSScriptRoot`의 부모다.
- `tests/tools/test_open_session.py`에 시험을 더했다(처음 판은 파라미터를 풀어 열일곱 건이었고, 일지에 열아홉이라 적은 것은 셈이 틀렸다. 셀프 리뷰 뒤 대체 데이터 스트림 시험이 하나 늘어 열여덟 건이다. 스크래치패드 아래 통과, `.env` 같은 바깥 파일·`..` 탈출·접두만 같은 형제·링크·없는 파일 거부, 저장소 뿌리 허용·거부, `Send-Prompt`가 검사를 읽기 전에 부르는 순서, 허용 규칙과 스킬 호출 모양의 글자 대조).
- `.claude/settings.json`에 `permissions.allow`로 `PowerShell(pwsh -NoProfile -File tools/open_session.ps1 -Action send -Folder C:\project\agent -PromptFile *)`를 더했다.
- `.scratch/retro-queue/0498.md`의 상태를 닫힘으로 바꿨다(분류기가 다음 인계 열기를 거부하지 않는지는 병합 뒤 첫 인계에서 본다고 적었다). `uv run python tools/plan_table.py`를 돌렸고 출력이 없었다.

## 확인한 것(손으로)

- 새 시험(처음 판은 17건, 셀프 리뷰 뒤 18건이다. 이 줄에 처음 적힌 19는 셈이 틀렸다)을 `uv run pytest -q tests/tools/test_open_session.py -k …`로 돌려 통과했다. 변이(`Resolve-PromptFile`의 폴더 아래 검사와 링크 검사를 꺼 둠)에서 네 시험이 빨개졌고 되돌렸다.
- 실제 환경에서 `Get-PromptRoot`가 `C:\Users\User\AppData\Local\Temp\claude`를 내고 스크래치패드의 파일을 받는 것을 PowerShell 도구로 손으로 봤다. `git rev-parse --path-format=absolute --git-common-dir`는 워크트리에서 `C:/project/agent/.git`을 냈다.
- `uv run ruff check .`와 `uv run ruff format --check .`는 초록이다. 전체 `uv run python tools/run_checks.py`는 이 세션이 백그라운드로 띄웠으나 인계로 멈추므로 끝나지 않았다. 새 세션이 다시 돌린다.
- `uv run python tools/sibling_overlap.py`는 번호·파일 겹침 없음이었다. 그 뒤 origin/main이 `cfc5ac0`으로 움직였고 바뀐 파일은 이 브랜치의 파일과 겹치지 않았다(승인 규칙 티켓 06, 대기열 0457~0466, 일지 하나, `tests/test_main.py`).

## 셀프 리뷰 (인계받은 세션, 기준 778db404, 파일 넷 수정 + 미추적 둘, 커밋 0)

표준 축과 명세 축 서브에이전트를 병렬로 돌렸다. 두 축 모두 함수를 `pwsh -NoProfile`로 직접 불러 경계 입력으로 쟀다(서브에이전트 보고).

- 고친 것
  - 대체 데이터 스트림(`파일:스트림`)이 `Resolve-PromptFile`을 지났다(명세 축이 실제 스크립트로 재현, 아래 사고 참고). 폴더 밖 탈출은 아니라 `.env` 우회는 못 되지만 "폴더 아래의 파일만"보다 넓었다. 드라이브 뿌리 뒤에 `:`가 있으면 거부하게 했고 시험 하나를 더했다(윈도 전용 `skipif`).
  - 사용 줄과 거부 메시지가 "스크래치패드의 파일만"이라 적었으나 실제로 받는 곳은 `<임시 폴더>\claude` 전체다. 사용 줄과 메시지를 그 폴더로 맞췄다.
  - `Get-RepoRoots`의 `git` 호출이 `git`이 없을 때 `Stop`으로 스크립트를 죽일 수 있어 `try/catch`로 감쌌다(사본의 뿌리만 남는다. 더 좁은 쪽이다).
  - 하드링크는 링크 표지가 없어 통과한다. 만들려면 별도 셸 호출이 필요해 위협은 낮다고 보고, `Resolve-PromptFile` 주석의 "못 보는 것"에 적었다.
  - pyright가 시험의 `given` 딕셔너리 형을 거부해(`dict[str, object]` 주석) 고쳤다.
  - 일지의 시험 수(열아홉)가 틀렸다. 위에서 고쳤다.
  - 티켓의 수용 기준 체크박스를 채웠고 첫 항목에 대체 데이터 스트림을 더했다.
- 남긴 것(근거)
  - `Wake-Display`와 잠금이 검사보다 먼저라 잘못된 입력도 화면을 깨운다. 효율 문제일 뿐이고 읽기 전에 검사하는 수용 기준은 충족해 둔다.
  - `Test-RepoFolder`가 `Test-` 이름인데 throw로 알리는 점(Mysterious Name), 정규화가 두 함수에 따로 있는 점(Duplicated Code)은 판단 항목이다. 이름이 티켓·시험·주석에 퍼져 있어 이번에는 두었다.
  - `Send-Prompt`가 검사를 부르는 순서 시험은 소스 글자 위치로 판정해 `if ($false) { … }`로 감싼 변이에는 약하다. 실제 `Send-Prompt`를 돌리는 시험은 UI 자동화가 필요해 이 PR 범위 밖이다.
  - `Get-RepoRoots`는 시험이 없다(`$PSScriptRoot`에 기대 시험 서버에서 재현하기 어렵다). 실제 환경에서는 손으로 봤다(위 "확인한 것").
  - 스킬 `open-session` 3단계에 두 거부(파일 밖, 뿌리 아닌 폴더)의 안내가 없다. 이번 변경이 스킬을 건드리지 않아 두었다.
- 사고: 명세 축 서브에이전트가 대체 데이터 스트림 탐침을 실제 스크립트로 돌려 사용자 앱에 제목 `S`인 새 세션(`local_e462dbe9-59fd-4fc1-a6e4-91808ea732d5`, 폴더 `C:\project\agent`)이 열렸다. 탐침 파일은 지웠다고 보고했다. 세션은 이 세션이 지우지 않고 사용자에게 알린다.

## PR 직전 리뷰 (main 합치기 뒤, 기준 cfc5ac01)

- CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`(Plan: Free)였고 `coderabbit-review` 서브에이전트가 돌지 못한다고 보고했다. 규약 대로 대체 둘을 나란히 돌렸다: 내장 `/security-review`(식별 서브에이전트, 코드를 읽어 판정)와 `bug-perf-review`(함수를 `pwsh -NoProfile`로 직접 불러 재현).
- `bug-perf-review` 보고(서브에이전트가 `pwsh`로 잰 결과): `.env` 읽기 금지를 돌아가는 입력은 하나도 통과하지 못했다. 통과한 것은 하드링크뿐이고 주석이 이미 적었다. 끝의 점·공백, 예약 장치 이름, `\\.\`·`\\?\`, 8.3 이름, 와일드카드는 거부되거나 폴더 안에 머물렀다. `Get-RepoRoots`는 git이 없거나 `GIT_DIR`이 틀리면 사본의 뿌리만 남겼다(fail-closed). 허용 규칙과 스킬 3단계의 호출 모양은 글자가 같았다.
  - 고친 것: 일지 22행의 시험 수 19(낡은 숫자). 공통 git 폴더가 `.git`이 아닌 배치에서 그 부모를 뿌리로 보는 점을 `Test-RepoFolder` 주석의 "못 보는 것"에 적었다(코드를 읽은 것이고 재현하지 않았다).
  - 남긴 것: `Wake-Display`와 잠금이 검사보다 앞이라 잘못된 입력도 화면을 깨우고 잠금을 기다린다(Minor. 읽기 전에 검사하는 수용 기준은 충족한다. 검사를 `switch` 앞으로 옮기면 고치지만 시험이 가리키는 `Send-Prompt` 안의 자리를 옮겨야 해 이번에는 두었다).
- `/security-review` 식별 서브에이전트 보고(코드를 읽어 판정, 확신도 7/10, 스킬의 거르는 기준 8 미만): 허용 규칙이 스크립트를 상대 경로 `tools/open_session.ps1`로 적어, 모델이 PowerShell 도구의 작업 폴더를 스크래치패드로 옮기고(`Set-Location`, `hook_bash_cd_outside`는 Bash만 본다) 거기에 같은 상대 경로의 가짜 스크립트를 써서 규칙과 같은 글자로 부르면 이 PR의 두 검사가 통째로 빠진 채 확인 없이 돈다는 지적이다. 제안은 규칙과 스킬 3단계 호출을 절대 경로(`C:\project\agent\tools\open_session.ps1`)로 고정하는 것이다.
  - 판정: 보류(사용자 판단). 유효한 구멍으로 보이나 고침이 이 PR이 허용 규칙으로 받은 승인(대기열 0498, 사용자 승인 2026-10-27)의 꼴과 스킬 호출 모양을 바꾸고, 어느 사본(워크트리 것/주 체크아웃 것)의 스크립트가 도는지가 바뀌어 `open-session` 4단계의 훅·스크립트 사본 논거와 얽힌다. 확신도도 기준 미만이다. 이 세션은 상대 경로 꼴 그대로 두고 판정과 값을 PR 체크리스트에 적고, 사용자에게 묻는다.
  - 값: 규칙·스킬 3단계 호출·시험의 `_ALLOW_PREFIX` 세 곳과 티켓 문구를 고친다. 새 세션이 읽는 스킬이라 새 세션에서 불러 보는 검증이 따른다.

## 남은 일

(두 번째 세션이 갱신, 커밋 뒤 인계 직전. 앞 세션의 "남은 일" 1~3은 끝났다.)

끝난 것: 셀프 리뷰(위), 전체 검증(`pre-commit`이 두 커밋 모두 통과, 첫 `run_checks`의 pyright 2건은 고쳤고 시간 의존 시험 둘은 홀로 돌려 통과), 티켓 수용 기준 체크, 커밋 둘(`f39c0fb3`, `5a6d8826`)과 origin/main 합치기(`ff67406d`), PR 직전 리뷰(위). 푸시와 PR은 아직 없다.

남은 일:

1. 푸시하고 PR을 연다(제목은 컨벤셔널 커밋 형식, 본문은 PR 템플릿). PR 체크리스트에 PR 직전 리뷰를 적는다: CodeRabbit CLI는 좌석 미배정이라 못 돌았고 `/security-review`와 `bug-perf-review`로 갈음했다. 보류한 지적 둘(검사가 `Wake-Display`·잠금보다 뒤인 Minor, 아래 절대 경로 건)과 값은 위 "PR 직전 리뷰"에 있다.
2. 앱 PR 도구 `get_status`로 PR이 묶였는지 보고 안 묶였으면 `bind_pr`. `@coderabbitai review` 코멘트를 남기고 `merge.md` 2의 봇 회차로 간다.
3. **병합 전에 사용자에게 물을 것.** `/security-review`가 짚은 지적(확신도 7/10, 보류): 허용 규칙이 스크립트를 상대 경로로 적어, 작업 폴더를 스크래치패드로 옮긴 호출이 가짜 `tools/open_session.ps1`을 확인 없이 돌릴 수 있다. 절대 경로(`C:\project\agent\tools\open_session.ps1`)로 규칙과 스킬 3단계 호출을 바꾸면 막히지만, 승인받은 규칙의 꼴이 바뀌고 도는 사본이 워크트리 것에서 주 체크아웃 것으로 바뀐다(스킬 `open-session` 4단계의 사본 논거도 고쳐야 한다). 사용자의 답이 오기 전에는 병합하지 않는다. 답이 "바꾼다"면 settings.json, `.claude/skills/open-session/SKILL.md` 3·4단계, 시험의 `_ALLOW_PREFIX`, 티켓 문구를 고치고(스킬은 `writing-for-agents`를 먼저 부른다) 새 세션에서 불러 본다.
4. 병합은 워크트리 세션이라 `merge.md`의 "워크트리에서 병합할 때"를 따른다.
5. 병합 뒤 일지의 "다음"에 `분류기가 다음 인계 열기를 거부하지 않는지`를 남긴다(티켓 What to build의 마지막 항목).
6. 사고: 명세 축 서브에이전트가 연 새 세션 `local_e462dbe9-59fd-4fc1-a6e4-91808ea732d5`(제목 `S`)가 사용자 앱에 남아 있다(실행 중은 아니다). 사용자에게 알리고 보관할지 묻는다.

## 이 세션의 제목

`chore/open-session-prompt-file-path-check` (인계하며 `chore/open-session-prompt-file-path-check (인계함)`으로 바꿨다)

open-session을 부른다 2026-11-07T17:30:01Z

## 두 번째 인계 (커밋 뒤)

두 번째 세션(`local_ad86f5d4-ec79-4513-b14c-21a10bbfbaa2`)이 위 셀프 리뷰·전체 검증·커밋 둘·main 합치기·PR 직전 리뷰를 하고, 컨텍스트가 문턱(20만 토큰)을 넘은 `커밋 뒤` 경계에서 `handoff.md`대로 넘긴다. 이 세션의 제목은 인계하며 `chore/open-session-prompt-file-path-check (인계함)`으로 바꾼다. 위 "남은 일"이 새 세션의 순서다.

open-session을 부른다 2026-11-07T19:07:50Z
