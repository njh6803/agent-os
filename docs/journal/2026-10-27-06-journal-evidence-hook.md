# 2026-10-27 (06) 일지 근거 계기 훅과 Glob 무시 설정

## 사용자 프롬프트

> 사용자: 대기열 445·370을 티켓 .scratch/harness/issues/010-journal-evidence-hook.md로 쓰고 한다 (next-session 지시문. 나란히 여는 8 중 1, 브랜치 chore/010-journal-evidence-hook, 범위는 PR과 병합까지. 주 체크아웃 미갱신이라 tidy-checkouts를 먼저 돌고 워크트리에 들어간다)

사용자에게 물은 것은 없다.

## 결정

- **일지 계기는 프로브 README 계기에 얹지 않고 따로 둔다(`tools/hook_journal_evidence.py`).** 대기열 445가 반영할 때 정하라고 남긴 갈래다. 판정하는 경로와 알림 문장이 다르고(일지에는 양성 대조와 갈래를 짚을 까닭이 없다), `tools/hook_report.py`가 훅 파일마다 발동을 세며, 표지 폴더가 같으면 한 계기가 다른 계기를 끈다. 일지 경로의 판정은 `hook_journal_retro`의 `is_journal`과 같은 뜻으로 복사했다(훅은 서로 import하지 않는다).
- **Glob은 설정 `env`의 `CLAUDE_CODE_GLOB_NO_IGNORE=false`로 `.gitignore`를 따르게 한다(대기열 370).** 무시된 자리는 그 폴더를 `path`로 주면 찾으므로, `CLAUDE.md`의 Glob 줄은 그 길과 `**/` 함정만 남겼다.

## 한 것

- 새 훅과 시험(`tests/tools/test_hook_journal_evidence.py`, 21개), 첫 `Write|Edit` 묶음의 등록, 페이로드 표의 발동 하나와 침묵 둘, 변이 표(`.scratch/harness/probes/journal_evidence_hook_mutations.toml`)와 그 README 행.
- `.claude/rules/tools.md`의 Write·Edit 훅 목록, `docs/agents/issue-tracker.md` 근거 항목, `CLAUDE.md` 환경 함정의 Glob 줄을 맞췄다. 대기열 445·370을 티켓으로 닫았다.
- 시작할 때 주 체크아웃 세션에서 `tidy-checkouts`를 돌아 루트를 `8ad99ca6`에서 `92b61458`로 당기고, 임시 폴더의 분리 HEAD 워크트리 하나를 지웠다. 형제 012~015의 브랜치는 `judge`가 `지운다`로 냈지만 지우지 않았다. 그 형제 세션들이 막 워크트리를 만드는 중이라 등록 없는 폴더(`.git` 있음)로 보였고, 브랜치 끝이 `origin/main`과 같았다. 판정 3이 제목으로 거르려면 그 세션이 `list_sessions`에 보여야 하는데 그때는 보이지 않았다.

## 검사

- 시험이 먼저 빨갛게 끝났다(모듈 없음으로 수집 오류, `uv run pytest -q tests/tools/test_hook_journal_evidence.py`로 손으로 봤다). 구현 뒤 21개가 초록이었다(같은 명령).
- `uv run python tools/run_hooks.py`: 훅 페이로드 159건 어긋남 0건(러너가 찍었다).
- 변이 표는 열여섯 모두 기대대로였다(`mutate.py`가 찍었다). 3번 표지를 실패 출력을 본 뒤 좁힌 까닭과 표지의 양성 대조는 그 README 행에 적었다.
- Glob 설정은 `claude -p --model haiku --allowedTools Glob`(claude 2.1.302, 이 워크트리)으로 손으로 봤다. 루트에서 `**/_cffi_backend*.pyd`는 `--settings`로 그 값을 준 판과 프로젝트 설정만 실린 판에서 "No files found", 값을 주지 않은 판(이 브랜치의 설정을 고치기 전)에서 `.venv\Lib\site-packages\_cffi_backend.cp312-win_amd64.pyd`였다. 프로젝트 설정만 실린 판에서 `path`를 `.venv/Lib/site-packages`로 주자 그 파일이 나왔다. 앱 세션과, 주 체크아웃 루트의 20초 시간 초과가 풀리는지는 보지 않았다(주 체크아웃은 병합 뒤에야 이 설정을 싣는다).

## 회고

후보 넷, 승인 하나(회차로 세는 것), 기각 셋, 넘김 없음.

1. **승인(회차로 세는 것), 대기열에 더하지 않음.** `tidy_checkouts.py judge`가 나란히 막 연 형제 012~015의 브랜치(끝이 `origin/main`과 같다)를 `브랜치를 지운다`로 냈다. 열린 대기열 440이 처방한 사건(형제가 그사이에 딴 브랜치를 체크아웃되지 않은 브랜치로 본다)이라 그 행의 회차다. 다만 나란히 도는 harness 티켓 017이 그 행을 닫는 중이라, 같은 행을 이 브랜치에서도 고치면 두 PR이 같은 줄에서 부딪친다. 그래서 회차는 이 절에만 적고 행은 고치지 않는다. 이번에는 지우지 않고 넘어가 손상은 없었다(위 "한 것").
2. **기각.** 일지 번호를 `docs/journal/`과 앞선 도구 출력의 06으로 만들었다가 형제와 겹쳐 10으로 옮겼다. `hook_journal_retro`의 순번 대조가 그 자리에서 알렸다(이미 있는 훅이 알린 것).
3. **기각.** 변이 표 3번의 첫 표지 `AssertionError`가 어느 실패에도 맞았다. `.claude/rules/probes.md` 첫 항목을 따라 실패 출력을 본 뒤 좁혔고 리뷰가 잡은 것이 아니다(규칙이 그 자리에서 작동했다).
4. **기각.** 워크트리 가드가 `mkdir`·`cd`·heredoc을 묶은 Bash 명령을 거부했다. `CLAUDE.md` 환경 함정이 적은 그대로이고, 파일로 나눠 쓰는 길로 바로 갔다(앱 가드가 막은 것).

## 인계

- `셀프 리뷰 직전`에 인계 계기가 왔다(세션 컨텍스트 약 26만 토큰). 이 세션의 제목은 `chore/010-journal-evidence-hook`이었고 `(인계함)`으로 바꾼다. 변경은 모두 워크트리에 커밋하지 않은 채 남겼다. 셀프 리뷰(`/code-review`, 기점 `origin/main`)부터 새 세션이 한다. 전체 검증(`tools/run_checks.py`)은 인계하며 멈춰 결과가 없다. ruff 둘(`ruff check .`, `ruff format --check .`)은 0으로 끝났다.
- PR 직전 리뷰에 밀 주장: 독스트링의 "표지 폴더도 따로라, 같은 세션에서 한 계기가 뜬 것이 다른 계기를 끄지 않는다", `CLAUDE.md` Glob 줄의 "그 폴더를 `path`로 주면 찾는다".
- open-session을 부른다 2026-10-26T07:15:21Z
- 이어받은 세션(제목 `chore/010-journal-evidence-hook`)이 셀프 리뷰와 반영을 마치고, 부하를 기다린 뒤 커밋 `b724493f`를 pre-commit 통과로 들였다. 그 직전 `sibling_overlap.py --move`로 일지를 `2026-10-26-10`에서 `2026-10-27-06`으로 옮겼다(main에 2026-10-27 일지가 먼저 들어왔다).
- `커밋 뒤`에 인계 계기가 왔다(세션 컨텍스트 약 30만 토큰). 남은 단계: origin/main 합치기, PR 직전 리뷰, PR, 봇 회차, 병합. main이 그사이 `.claude/rules/tools.md`(훅 시간 긴 줄), `.scratch/harness/probes/README.md`, `.scratch/retro-queue.md`를 고쳐 합칠 때 충돌 후보다. main 판의 Write·Edit 훅 목록은 그대로라(`git show origin/main:./.claude/rules/tools.md`로 봤다) 합친 뒤에도 카나리아 순번(여섯째 일지, 일곱째 디자인)이 맞는지 다시 본다.
- PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장): `CLAUDE.md` Glob 줄의 "루트에서 `**/_cffi_backend*.pyd`도 `.venv/**/_cffi_backend*.pyd`도 "No files found"였고, `path`를 그 파일이 든 하위 폴더 `.venv/Lib/site-packages`로 주자 찾았다", "`path`를 `.venv`로 주면 "No files found"였다(그 안에 `*`만 든 `.gitignore`가 있어서라고 어림한다", "루트의 Glob이 시간 초과로 끝나면 `path`를 그 자리들을 품지 않는 하위 폴더(`.claude/skills`, `src`)로 좁힌다", 훅 독스트링의 "대소문자를 구별해, 글자가 같은 경로만 일지로 본다".
- 인계 지시문:

```
다음 작업: .scratch/harness/issues/010-journal-evidence-hook.md (대기열 445·370, 커밋 b724493f까지 했고 커밋하지 않은 것은 이 일지의 인계 줄뿐이다)
다음 단계: 구현
어디서: 새 세션. 같은 브랜치라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 445·370을 티켓 .scratch/harness/issues/010-journal-evidence-hook.md로 쓰고 한다
브랜치: chore/010-journal-evidence-hook
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md, 일지 docs/journal/2026-10-27-06-journal-evidence-hook.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영과 검증을 마친 커밋 b724493f가 pre-commit을 지났다. 남은 단계는 이 일지 인계 줄의 커밋, origin/main 합치기(sync_with_base_branch, 충돌 후보와 합친 뒤 볼 카나리아 순번은 일지 인계 절), PR 직전 리뷰(밀 주장은 일지 인계 절), PR, 봇 회차, 병합이다. 회고와 "다음"은 썼고, 이 세션의 회고 후보 하나가 인계 절에 있다. docs/journal/2026-10-27-06-journal-evidence-hook.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 잠금 풀기는 `is not locked`로 이미 풀려 있었다.
- open-session을 부른다 2026-10-27T02:54:04Z
- 인계 못함 커밋 뒤. `tools/open_session.ps1 -Action send`를 자동 모드의 권한 분류기가 거부했다(까닭은 알려 주지 않았다). 제목을 `chore/010-journal-evidence-hook`으로 되돌리고 이 세션에서 main 합치기부터 잇는다.
- origin/main(`5e04968`)을 합쳤다. `sync_with_base_branch`는 커밋하지 않은 일지가 있으면 거절하므로 `git merge --no-commit --no-ff origin/main`으로 직접 합치고 이 일지를 합치기 커밋에 실었다. 충돌 둘을 main 판 위에 이 브랜치의 변경만 다시 얹어 풀었다(스크래치 스크립트가 바꿀 글이 한 번씩만 있는지 단언했다). `.claude/rules/tools.md`는 훅 이름 끼우기, 여섯째 일지 문장, "넷 다" 세 군데이고, 대기열 445는 main이 더한 12회차(일지 2026-10-27-01)를 닫힌 행에 얹었다. 풀린 두 파일을 `git diff --word-diff=plain origin/main`으로 보니 이 브랜치의 변경만 남았다. main의 Write·Edit 훅 목록은 그대로라 카나리아 순번은 맞다. 대기열 370의 닫힘 문구도 `CLAUDE.md`와 같게 본 것만으로 좁혔다.
- 회고 후보(이 세션): 부하에서 `test_rerun_runner`의 오염 재시도 시험이 세 번 연달아 떨어져 커밋이 두 번 막혔다(아래 "다음"). 단계를 닫는 세션의 retro가 판정한다.

## 셀프 리뷰

기점 `92b61458`(origin/main), 커밋 0, 미커밋 변경 7파일, 미추적 5파일. 이어받은 세션이 돌렸다.

명세 축 보고(서브에이전트가 `claude -p --model haiku` 2.1.302로 손으로 본 것과 grep·함수 호출로 잰 것):

- Major: `CLAUDE.md` Glob 줄의 "그 폴더를 `path`로 주면 찾는다"가 `.venv`에서 거짓이다. `path` `.venv`는 "No files found", `.venv/Lib/site-packages`는 찾았다. 원인은 uv가 만든 `.venv/.gitignore`의 `*`로 본다(어림. 그 파일의 내용이 `*`인 것은 이 세션이 `cat`으로 봤다).
- Major: 같은 줄이 무시된 자리 넷을 "손으로 봤다" 하나로 묶었는데 본 것은 `.venv` 하나다.
- Minor: 표지가 머리 한 줄만 쓴 첫 Write에서 쓰여, 결과 줄을 쓰는 단계 끝·리뷰 반영·압축 뒤에는 알리지 않는다(독스트링의 못 보는 것에 있다).
- Minor: 대기열 370의 앱 세션 확인 없이 `CLAUDE.md`에서 `path`를 좁히라는 옛 안내를 지웠다.
- Nit: 못 보는 것 가운데 `design/README.md` 경로의 단위 시험이 없다.
- 밀 주장 둘: 표지 폴더 `agent-os-journal-evidence`는 `tools/*.py`의 `STATE_DIR` 가운데 유일하고, `is_journal`은 경계 입력 일곱에서 `hook_journal_retro`와 같았다.

표준 축 보고(sonnet·high):

- Major: 카나리아 `tools_rule_ui_design_hook.toml`이 "여섯째도"를 묻는데, 이 diff가 일지 훅을 여섯째로 끼워 디자인 훅은 일곱째가 됐다.
- Minor: `CLAUDE.md` Glob 줄이 잰 것보다 넓다(명세 축의 두 Major와 같은 자리). 무시된 폴더 이름이 든 패턴(`.venv/**`)은 재지 않았다.
- Minor: `claim_first`의 `os.open` 실패 갈래에 시험도 변이도 없고, 변이 14의 표지 `assert False`가 그 시험의 두 단언 어디서든 나온다.
- Nit: 표지 폴더 시험이 프로브 README 계기 하나와만 견준다. `is_journal`을 맞대는 시험이 없다. 독스트링의 "대소문자를 가린다"가 반대로 읽힌다. 시험 이름의 `main_`.

고친 것:

- 카나리아 질문을 "일곱째도"로 고쳤고, 새 여섯째 문장의 카나리아 `tools_rule_journal_evidence_hook.toml`을 더했다.
- `CLAUDE.md` Glob 줄을 본 것만으로 줄였다. 새로 쓴 문장(PR 직전 리뷰에 밀 주장): "루트에서 `**/_cffi_backend*.pyd`도 `.venv/**/_cffi_backend*.pyd`도 "No files found"였고, `path`를 그 파일이 든 하위 폴더 `.venv/Lib/site-packages`로 주자 찾았다. `.venv`는 안에 `*`만 든 `.gitignore`가 있어 `path`를 `.venv`로 줘도 "No files found"였다", "무시된 다른 자리(`node_modules`, `.claude/worktrees/`, `.scratch/token-report/`)와 앱 세션은 재지 않았다", "루트의 Glob이 시간 초과로 끝나면 `path`를 그 자리들을 품지 않는 하위 폴더(`.claude/skills`, `src`)로 좁힌다". 근거: `.venv/**` 패턴은 이 세션이 `echo … | claude -p --model haiku --allowedTools Glob`(claude 2.1.302, 이 워크트리)으로 손으로 봤고, `path` `.venv`는 명세 축 서브에이전트가 같은 꼴로 손으로 봤으며, `.venv/.gitignore`의 내용은 이 세션이 `cat`으로 봤다.
- `test_표지_파일을_만들지_못하면_알린다`와 변이 15를 더하고, 변이 14의 표지를 `where False = claim_first(`로 좁혔다. 변이 열일곱이 모두 기대대로였다(`mutate.py`가 찍었다). 시험 22개가 초록이었다(`uv run pytest -q tests/tools/test_hook_journal_evidence.py`).
- 독스트링의 "가린다"를 "구별해, 글자가 같은 경로만 일지로 본다"로 고쳤다.
- 티켓 수용 기준의 같은 넓은 문장도 하위 폴더로 좁혔고, `.venv`에서 찾지 않는 원인은 두 문서 모두 어림이라고 적었다.
- 다시 돌린 것: 반영 전 `tools/run_checks.py`는 종료 0이었다. 반영 뒤 같은 러너는 pytest만 실패했다(3 failed, 5609 passed, 22분. `test_probe_kit`의 배출 시간, `test_rerun_gates`의 작업 트리 걷기, `test_rerun_runner`의 오염 재시도로 이 브랜치가 건드리지 않은 시험이다). 셋만 `uv run pytest -q <세 노드>`로 다시 돌리자 통과했고 6분이 걸려, 이 PC에 다른 세션이 여럿 돌던 부하로 본다(어림). ruff 둘은 0으로 끝났다. 커밋의 pre-commit 결과로 다시 판정한다.
- 첫 커밋 시도는 pre-commit의 pytest만 실패해 막혔다(4 failed, 5608 passed, 19분. `test_probe_kit` 배출과 `test_rerun_runner` 오염 재시도가 두 번째로, `test_interrupt`의 Ctrl+C 둘이 새로 떨어졌다. 모두 이 브랜치가 건드리지 않은 시간 시험이다). 그때 CPU 부하 93%, claude 프로세스 35개, pytest 프로세스 4개였다(PowerShell `Get-Process`·`Win32_Processor`로 손으로 봤다). 나란히 연 형제 세션들의 부하로 보고(어림) 고치지 않고 다시 커밋했다. 같은 두 시험이 연달아 떨어진 것은 회고 후보다.
- 카나리아 둘이 모두 통과 4였다(`tools/canary.py`가 찍었다). `tools_rule_journal_evidence_hook.toml`은 대조군이 이 체크아웃의 `README.md`, `tools_rule_ui_design_hook.toml`은 `--control-commit aba71813`이다.

남긴 것:

- 첫 Write에서 표지를 쓰는 갈래(명세 Minor): 독스트링의 못 보는 것이고 티켓이 세션·에이전트마다 한 번을 요구했다. 결과가 든 편집에서만 표지를 쓰려면 결과 문장을 판정해야 해 계기 훅의 몫을 넘는다.
- 대기열 370의 앱 세션 확인(명세 Minor): 병합 전에는 주 체크아웃과 앱 세션이 이 설정을 싣지 않아 지금 볼 수 없다. 아래 "다음"이 받고, `CLAUDE.md`에 시간 초과가 나면 좁히라는 안내를 되살렸다.
- Nit 넷: 표지 폴더와 `is_journal`의 맞대기 시험은 사실이 맞아(두 축이 불러 봤다) 더하지 않았다. `main_` 이름은 선례 시험과 같은 꼴이다. `design/README.md` 단위 시험은 페이로드 표의 침묵 입력이 고정한다.

## 다음

- 둘째 커밋 시도도 pre-commit에서 막혔다. pytest는 `test_rerun_runner`의 오염 재시도 시험 하나(세 번째 연속), web-verify는 `WidgetApproval.test.tsx`의 "18,000 / 20,000" 찾기 하나가 떨어졌다. 그때 CPU 부하는 세 번 모두 100%였다(PowerShell `Win32_Processor`로 손으로 봤다). 훅을 건너뛰는 커밋은 사용자 승인 없이 하지 않아, 커밋 방법을 사용자에게 물었다.

> 사용자: 부하가 줄 때까지 기다렸다가 같은 커밋을 다시 시도해 줘. 훅은 건너뛰지 마.

> 사용자: 다른 세션들이 끝날 때까지 계속 기다렸다가 부하가 줄면 커밋해 줘.

- 스크래치의 PowerShell 대기 스크립트로 30초마다 부하와 pytest 프로세스 수를 찍으며 기다렸다. 4시간 반 동안 부하는 87~100%였고(떠 있던 pytest는 다른 워크트리 세션들이 새로 띄운 전체 검사였다), 2026-10-27 11:34에 다른 pytest 0개·부하 74%가 두 번 연달아 와서 다시 커밋했다.
- `test_rerun_runner`의 오염 재시도 시험이 부하에서 세 번 연달아 떨어진 원인을 diagnosing-bugs로 가르는 일은 이 티켓 밖이다. 회고에서 대기열 행으로 올린다(같은 때 흔들린 `test_probe_kit` 배출, `test_interrupt`의 Ctrl+C 둘, 위젯 승인 화면 시험도 함께 본다).

- 앱 세션에서 이 설정이 Glob에 닿는지와 주 체크아웃 루트의 Glob이 시간 안에 끝나는지는 병합 뒤 주 체크아웃의 새 세션이 한 번 불러 본다.
