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

## 세 번째 세션: PR 492 (푸시 뒤)

- 푸시 전에 origin/main(`dd1c0190`)을 합쳤다(`sibling_overlap` 번호·파일 겹침 없음). PR 492를 열고 `@coderabbitai review`를 남겼다. 앱에는 PR이 이미 묶여 있었다.
- 첫 CI에서 `python` 잡이 실패했다. CI 로그(`gh run view 42406534877 --log-failed`)에서 읽은 것: pytest는 `6646 passed, 1 skipped`이고 출력에 `skip 1건. skip된 테스트는 초록이 아니다`가 찍혔으며 종료 코드는 1이었다. 그 skip이 이 PR의 `test_대체_데이터_스트림이_붙은_경로는_멈춘다`에 단 윈도 전용 `skipif`라는 것은 코드를 읽은 추정이다(`skipif`는 그 시험 하나뿐이었다. 로그에는 시험 이름이 없다). `.claude/rules/tests.md`가 `tests/tools/`는 CI 리눅스에서도 돈다고 적은 규칙을 어긴 것이다. 스크립트의 `:` 검사는 경로 뿌리 뒤의 `:`만 보므로 리눅스에서도 같은 거부가 난다고 코드를 읽어 판단해 `skipif`를 뺐다. 리눅스에서 돌려 본 것은 아니다. 이 PC에서 `uv run pytest -q tests/tools/test_open_session.py -k "대체_데이터 or 점점으로 or 접두만 or 링크 or 저장소_뿌리"`로 14건이 통과한 것은 손으로 보았고, 리눅스 pwsh에서의 통과는 다음 CI가 보여 준다. `verify` 잡의 빨강은 로그의 `needs` 출력에 `python: failure`가 있어 그것을 옮긴 것이다.
- 자동 보안 알림이 허용 규칙을 두 건 짚었다(상대 경로 스크립트는 위 `/security-review`와 같은 건, 열린 `-PromptFile *`은 권한 규칙이 `;`·`|` 뒤의 명령까지 `*`로 받는지 재현하지 못한 미확인 위험). 둘 다 PR 코멘트에 남겼고 사용자 답을 기다린다.

- 두 번째 푸시(`5c96f304`)의 CI는 `python` 포함 모두 초록이었다(`wait_ci.py` 출력). `skipif` 제거가 리눅스 CI에서 통한 것이다. 커밋 pre-commit은 부하 때문으로 보이는 시간 시험 실패(`test_interrupt.py` 3건, `test_rerun_runner.py` 1건, `test_interrupt.py` 1건)로 세 번 막혔고 홀로 돌린 앞의 둘은 통과했다(6건, 63건. 셋째는 홀로 돌리지 않았다). 그 시각 이 PC의 CPU 사용률 100%와 다른 두 워크트리의 검사를 `Get-CimInstance Win32_Process`로 보았고, 그 검사가 끝난 뒤 네 번째 시도가 통과했다. 부하가 원인이라는 것은 이 관찰에서 나온 추정이다.
- CodeRabbit 첫 회차(헤드 `5c96f304`)가 인라인 3건(Major 1, Minor 2)과 Nitpick 1건을 냈다. 판정:
  - **고침(Major, `open_session.ps1` 반복문)**: `Resolve-PromptFile`의 링크 검사가 `claude` 루트에 닿기 전에 멈춰 루트 자체가 밖을 가리키는 링크이면 그 아래 파일이 통과했다. 코드를 읽어 유효하다고 판단했고, 새 시험 `test_폴더_뿌리_자체가_링크이면_멈춘다`가 고침 전에 빨간 것(`.env`를 받아 냈다)과 고침 뒤에 초록인 것을 손으로 보았다(`uv run pytest -q tests/tools/test_open_session.py -k …`, 링크 관련 아홉 건 통과). 이 PC의 실제 `claude` 폴더는 링크가 아니고(`Get-Item`의 `Attributes=Directory`) 실제 스크래치패드 파일은 받고 `C:\project\agent\.env`는 거부하는 것도 손으로 보았다.
  - **보류(Minor, `settings.json` 상대 경로)**: 위 사용자 판단 대기 건과 같다.
  - **보류(Minor, `Get-RepoRoots`가 `GIT_DIR`·`GIT_COMMON_DIR`을 벗기지 않는다)**: 공격이 되려면 `pwsh` 프로세스 환경에 그 변수를 먼저 넣어야 하는데, 허용 규칙은 명령 글자 전체가 맞아야 하고 PowerShell 도구는 호출 사이에 셸 상태를 잇지 않는다고 도구 설명이 적었다(읽은 것이고 재지 않았다). 시험하려면 `$PSScriptRoot`에 기대는 함수를 시험 서버에서 띄워야 한다. 아래 "뒤로 넘긴 일"에 둔다.
  - **보류(Nitpick, 검사 순서 시험이 소스 글자 위치를 본다)**: 앞서 일지에 적은 한계 그대로다. 실제 `Send-Prompt`를 돌리려면 UI 자동화가 필요하다.
  - claude-review의 Minor·Nit(`Test-RepoFolder`의 이름, 정규화 중복, `Get-RepoRoots` 시험 없음, 검사가 `Wake-Display` 뒤)는 앞의 셀프 리뷰에서 이미 판정한 것과 같다.
- **뒤로 넘긴 일**(병합 뒤 지시문이 읽도록 여기에 둔다. 단계를 닫는 세션이 "다음"에 옮긴다):
  1. `Get-RepoRoots`가 `git`을 부르기 전에 저장소 위치 환경 변수(`GIT_DIR`, `GIT_COMMON_DIR`, `GIT_WORK_TREE`)를 벗기고 그 입력을 시험으로 고정한다. `$PSScriptRoot` 의존을 인자로 빼야 시험할 수 있다(`tools/open_session.ps1`, `tests/tools/test_open_session.py`).
  2. `Send-Prompt`의 검사 부분을 UI와 떨어진 함수로 빼 호출 순서를 행동으로 시험한다(글자 위치 시험을 대체한다).
  3. 검사를 `Wake-Display`와 잠금 앞으로 옮기는 일은 2와 함께 한다.
  4. 주 체크아웃을 당기기 전에 `send`를 돌리면 옛 판(두 검사가 없는 스크립트)이 도는데, 출력에 옛 판임을 알리는 표지가 없다. 스크립트가 판을 찍게 하고 스킬 3단계가 그 표지를 확인하게 하는 일이다(`tools/open_session.ps1`, `.claude/skills/open-session/SKILL.md`). 사용자 결정(절대 경로)이 만든 창이다.

## 결정: 허용 규칙의 스크립트를 절대 경로로 (사용자 답, 2026-11-08)

보안 리뷰 셋(`/security-review`, CodeRabbit, claude-review)이 허용 규칙의 상대 경로를 짚었고, 이 세션이 병합 전에 사용자에게 물었다.

> 사용자: 절대 경로로 바꿈 (이 세션이 올린 선택 버튼 `절대 경로로 바꿈` 그대로. 그 전에 다른 세션이 "바꾼다"는 답을 전했으나 이 대화에서 확인할 수 없어 승인으로 세지 않았고, 사용자가 이 대화에서 직접 고른 것을 근거로 했다)
> 사용자: 병합 후 다음 지시는 하지마 (병합까지만 하고 `next-session`의 다음 지시문과 `open-session` 열기를 하지 않는다)

고친 것(파일 다섯):
- `.claude/settings.json`: 허용 규칙이 `C:\project\agent\tools\open_session.ps1`을 가리킨다.
- `.claude/skills/open-session/SKILL.md`: 3단계 호출을 같은 절대 경로로 바꾸고, 절대 경로로 적는 까닭과 병합 직후 주 체크아웃을 당기기 전의 주의를 3단계 코드 블록 뒤에 더했다. 4단계의 사본 논거 두 군데(`send`가 도는 스크립트와 새 세션의 훅이 둘 다 주 체크아웃 사본이다)를 맞췄다. `writing-for-agents`를 먼저 불렀다.
- `tests/tools/test_open_session.py`: `_ALLOW_PREFIX`를 절대 경로로 바꾸고, 허용 규칙의 스크립트가 드라이브 문자로 시작하는지 보는 `test_허용_규칙의_스크립트는_절대_경로다`를 더했다. 설정을 옛 상대 경로로 잠시 되돌려 두 시험이 모두 빨간 것을 손으로 보고 복원해 초록을 확인했다(`uv run pytest -q tests/tools/test_open_session.py -k 허용`).
- `.scratch/harness/issues/open-session-prompt-file-path-check.md`: What to build의 규칙 문구와 사용자 결정.

남긴 위험(코드를 읽어 판단한 것이고 재지 않았다): 이 호출이 도는 사본은 주 체크아웃의 것이라, 이 PR을 병합한 뒤 주 체크아웃을 당기기 전에는 그 사본이 두 검사가 없는 옛 판이다. 주 체크아웃의 `settings.json`은 같은 당기기로 규칙과 스크립트가 함께 들어오지만, 병합된 `origin/main`에서 딴 다른 워크트리 세션은 당기기 전에도 규칙을 읽을 수 있다. 그래서 SKILL.md 3단계에 당기기(`tidy-checkouts`)를 마친 뒤에 열라고 적었다. 병합 뒤 첫 인계에서 분류기가 거부하지 않는지와 함께 이 창을 본다.

바뀐 스킬을 새 세션에서 불러 보는 검증(`operations.md` 환경 규약 상세)은 새 컨텍스트의 에이전트가 스킬 파일을 읽고 3단계 호출을 말하게 하는 길로 했다. 실제 `Skill` 도구로 새 세션에서 부른 것은 아니다. 새 세션을 여는 일이 사용자가 하지 말라고 한 다음 지시문의 열기와 겹쳐 하지 않았다.

그 에이전트(결론을 알려 주지 않고 파일 경로만 준 Sonnet 서브에이전트, 읽기만 했다)의 보고: 3단계 호출을 절대 경로 그대로 말했고, 도는 사본이 주 체크아웃이며, 당기기 전에는 열면 안 된다고 읽었고, 4단계의 사본 설명이 "보통 같은 판"으로 읽혔다. 짚은 빈 자리 넷 가운데 둘을 SKILL.md에 한 문장씩 메웠다(5단계 `split`·`focus`가 허용 규칙에 없어 상대 경로로 남은 까닭, 당기기는 주 체크아웃 세션이 하고 워크트리 세션은 사람에게 `/tidy-checkouts`를 부탁한다는 것). 둘은 두었다. 막히면 절의 프로브 명령이 상대 경로인 것은 허용 규칙 밖이라 이번 변경과 무관하다. 당기지 않고 돌렸을 때 출력의 어떤 표지로 옛 판을 알아챌지는 지금 표지가 없다. 이 둘은 이번 범위 밖이고, 뒤로 넘긴 일 4로 둔다.

### 카나리아 여섯을 새 세션에서 다시 돌렸다 (2026-11-08)

SKILL.md 본문이 바뀌어 `open_session_*` 카나리아 명세 여섯의 `source`가 움직였고, `tools/sibling_overlap.py`가 그 의무를 알렸다. 실험군 `9f942870`(이 브랜치), `claude 2.1.318`(`claude --version`), 이 PC에서 `uv run python tools/canary.py --control-commit <대조군> <명세> <출력 디렉터리>`로 명세마다 한 번씩 돌렸다.

| 명세 | 대조군 | 결과 |
|---|---|---|
| `open_session_effort_errors` | `df705c17` | 통과 4, 실패 0 |
| `open_session_folder_check` | `bea74a07` | 통과 4, 실패 0 |
| `open_session_lock` | `71433a0d` | 통과 4, 실패 0 |
| `open_session_model_pick` | `80445cff^`(`f0b3379a`) | 통과 4, 실패 0, "없음" 섞임 2 |
| `open_session_model_source` | `f01ce1e9` | 통과 4, 실패 0 |
| `open_session_parallel_cap` | `06a8f85b` | 통과 4, 실패 0 |

`model_pick`의 "없음" 섞임 2는 거짓 표지다. 찍힌 답을 읽어 보니 두 답 모두 카나리아 둘(`restored=<모델> / <레벨>`, `같거나 싼 모델`)을 그대로 옮겼고, 본문 문구 `restored=바뀐 것 없음`을 인용하다 "없음"이 센 것이었다. 여섯 명세의 `# 최신 결과:` 줄에 이 실행을 쓰고 옛 결과는 `# 그 전:`으로 남겼다.

## 이 세션의 제목

`chore/open-session-prompt-file-path-check` (인계하며 `chore/open-session-prompt-file-path-check (인계함)`으로 바꿨다)

open-session을 부른다 2026-11-07T17:30:01Z

## 두 번째 인계 (커밋 뒤)

두 번째 세션(`local_ad86f5d4-ec79-4513-b14c-21a10bbfbaa2`)이 위 셀프 리뷰·전체 검증·커밋 둘·main 합치기·PR 직전 리뷰를 하고, 컨텍스트가 문턱(20만 토큰)을 넘은 `커밋 뒤` 경계에서 `handoff.md`대로 넘긴다. 이 세션의 제목은 인계하며 `chore/open-session-prompt-file-path-check (인계함)`으로 바꾼다. 위 "남은 일"이 새 세션의 순서다.

open-session을 부른다 2026-11-07T19:07:50Z
