# open-session-selects-repo-folder: 새 세션 화면의 폴더를 열기 스크립트가 고른다

브랜치 `chore/open-session-selects-repo-folder`, 티켓 `.scratch/harness/issues/open-session-selects-repo-folder.md`. 이 세션의 제목은 인계 전 `chore/open-session-selects-repo-folder`다.

## 사용자 프롬프트 원문

> 사용자: 사용자 요청을 티켓 .scratch/harness/issues/open-session-selects-repo-folder.md로 쓰고 한다

세션을 연 지시문의 "이어받을 상태"가 옮긴 사용자의 원 요청:

> 사용자: 새 세션 화면의 폴더가 자신의 저장소인지 확인하고 아닐 경우 폴더를 바꾸는 조작 스크립트를 추가해서 자신의 저장소로 바꾸는 작업을 티켓으로 만들어서 새 세션에서 바로 진행하자. 만든 후에는 rag-engine 저장소에도 동일하게 적용할 수 있게 해줄 수 있나.

이번 요청 범위는 "PR과 병합까지"다. 대기열 378의 "다르면 멈추고 사람이 고른다"를 "스크립트가 고른다"로 바꾸는 결정이고, 사용자가 직접 청했다.

## 한 것(커밋하지 않았다, 워크트리에 있다)

- 티켓 `.scratch/harness/issues/open-session-selects-repo-folder.md`: `done`, 수용 기준 가운데 "rag-engine 몫 보고"와 "검증 명령"만 안 닫았다.
- `tools/open_session.ps1`: `Get-FolderEnvName`, `Select-FolderEnvNames`, `Find-FolderEnvRadios`(순수 둘과 UIA 하나), `Select-ComposerFolder`, `Repair-ShownFolder`를 더하고, `Send-Prompt`가 화면의 폴더를 읽었는데 `-Folder`가 아니면 `Repair-ShownFolder`로 환경 버튼에서 `-Folder`의 환경(이름이 폴더의 마지막 토막)을 골라 다시 읽고, 같을 때만 `folder-fixed=<전> -> <후>` 뒤에 `folder=`를 찍고 이어 가게 했다. 읽지 못했거나 고르지 못했으면 지금의 멈춤 문구 끝에 까닭을 덧붙여 멈춘다. 고른 뒤 입력창은 다시 찾는다.
- `tests/tools/test_open_session.py`: 순수 판정 시험(환경 이름 뽑기 여섯, 항목 고르기 여섯과 같은 이름 둘), 소스 순서 시험 셋.
- `.scratch/harness/probes/composer_env_menu.ps1`(진단 프로브, `-Pick` 포함)과 `open_session_folder_fix_mutations.toml`(변이 여섯. 이어받은 세션의 셀프 리뷰 뒤 열이 되었다, 아래)과 `README.md` 행 둘, `composer_folder` 행의 어림을 닫는 말 한 줄.
- `.claude/skills/open-session/SKILL.md`: 서두 두 군데, 3단계의 폴더 문장과 오류 갈래, 6단계의 보고 칸에 `folder-fixed=`를 맞췄다. 카나리아(`open_session_folder_check.toml`)가 요구하는 `folder=<폴더>`와 `환경 버튼에서`는 그대로 있다.

## 손으로 본 것(2026-11-10, 모두 이 세션이 앱에서 돌렸다)

- 환경 메뉴: `환경: agent` 버튼(펼치기 패턴)을 펼치면 `agent , 환경 편집, 오른쪽 화살표`(고름)·`rag-engine , …`·`Default , …` 라디오 버튼이 `SelectionItem`으로 생긴다. 항목 이름은 환경 이름이지 경로가 아니다(`composer_env_menu.ps1`이 찍었다).
- `-Pick rag-engine`: 화면 폴더 `C:\project\agent`→`C:\project\rag-engine`, 메뉴가 스스로 닫혔고 입력창의 값과 요소가 그대로였다. 이어 연 표지 화면이 `rag-engine`으로 열렸다. 곧 고른 폴더가 앱의 마지막 폴더가 된다. `-Pick agent`로 되돌렸다. 대기열 387이 기다리던 양성 대조다.
- `send` 실제 실행: 앱의 마지막 폴더를 `rag-engine`으로 돌려 놓고 첫 줄이 옮길 수 없는 슬래시 명령인 프롬프트로 `pwsh -NoProfile -File tools/open_session.ps1 -Action send -Folder C:\project\agent -PromptFile <스크래치>\held-prompt.md`를 쳤다. `folder-fixed=C:\project\rag-engine -> C:\project\agent`, `folder=C:\project\agent`, `held=` 순으로 나왔다(세션이 생기지 않는다).
- 음성: 환경 목록에 없는 이름(`no-such-env`)이면 `5초 안에 환경 메뉴의 'no-such-env' 항목 을(를) 찾지 못했다.`를 던지고 메뉴가 접히며 화면 폴더는 그대로였다(커밋하지 않은 스크래치 스크립트로 봤다).
- 단위 시험: `uv run pytest -q tests/tools/test_open_session.py` 종료 코드 0. 변이: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/open_session_folder_fix_mutations.toml` 여섯 모두 기대대로 빨강, 표지도 맞았다(첫 판의 첫 변이 `old`가 실제 코드와 한 글자 달라 한 번 고쳤다).
- `uv run ruff check .`, `uv run ruff format --check .` 통과.
- `uv run python tools/run_checks.py`는 check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux까지 통과하고 pytest와 web이 남은 상태에서, 인계하며 멈췄다. 새 세션이 다시 돌린다.

## 결정과 이 세션이 고친 것

- 고르는 값은 `Test-RepoFolder`를 지난 `-Folder`의 마지막 토막뿐이고, 항목이 정확히 하나일 때만 고른다. 앞부분만 같은 이름(`agent2`)은 다른 환경이다. 대소문자는 가리지 않는다.
- 폴더를 화면에서 읽지 못했으면(앱이 모양을 바꿨다) 무엇이 선택돼 있는지 모르므로 고르지 않고 멈춘다.
- 대기열 378(닫힘)과 387(만료)의 상태 줄은 고치지 않았다. 닫힌 기록은 바꾸지 않는 규약이다. 티켓의 대기열 줄은 `378, 387`이다(처음 적은 498은 이 일과 관계가 없어 뺐다).
- 첫 시험이 `Repair-ShownFolder`의 첫 등장(주석)을 호출 위치로 잘못 잡아 빨갰고, 호출 줄(`= Repair-ShownFolder $win $box $needle $Folder`)로 고쳤다.

## 아직 안 한 것(새 세션이 이어서)

1. 셀프 리뷰(`/code-review`). 인계 계기가 그 직전에 와서 밟지 않았다.
2. `uv run python tools/run_checks.py`(600초 상한이라 백그라운드로, 끝 알림을 기다린다. 다시 치지 않는다)와 `pnpm`은 워크트리에 `web/node_modules`가 없을 수 있다. 린트 둘은 이미 초록이다.
3. 카나리아 `uv run python tools/canary.py .scratch/harness/probes/canary/open_session_folder_check.toml <출력 디렉터리>`는 스킬을 고쳤으므로 다시 돌린다(선택이 아니라 스킬을 바꾼 일의 확인이다. 헤더 주석에 결과 줄을 갱신한다).
4. PR 직전 리뷰(`coderabbit-review`, 안 돌면 `/security-review`와 `bug-perf-review`), 커밋(`git branch --show-current` 확인, `uv run python tools/sibling_overlap.py`), PR, 봇 회차, 병합(워크트리에서 병합하는 길).
5. 병합 뒤 마지막 보고에 rag-engine 세션에 붙여 넣을 글을 코드 블록으로 싣는다. 내용: 옮길 파일 `tools/open_session.ps1`(이 저장소와 `C:\project\rag-engine`의 것이 2026-11-10에 SHA-256이 같았다. `Get-FileHash`로 손으로 봤다), 그쪽 `open-session` 스킬에서 고칠 문장(스킬은 두 저장소가 달라서 통째로 옮기지 말고 서두의 폴더 문장, 3단계의 폴더 문장과 오류 갈래, 6단계 보고 칸만 맞춘다), 확인 방법(앱의 마지막 폴더가 이 저장소로 돌려 놓은 뒤 옮길 수 없는 슬래시 명령 프롬프트로 `send`를 쳐 `folder-fixed=`와 `held=`를 본다). 쓰기 전에 그 저장소의 두 파일을 다시 대 본다(해시 비교). 그 저장소는 고치지 않는다.
6. 병합 뒤 첫 인계 열기에서 새 세션의 `cwd`가 저장소 뿌리인지(`list_sessions`)와 `folder-fixed=`가 찍혔는지를 일지 "다음"이나 보고에 적는다.

## 확인하지 못한 것

- 워크트리 폴더가 환경 목록에 항목으로 나오는지는 보지 못했다. 나오지 않아도 `-Folder`는 저장소 뿌리라 영향이 없고, 마지막 폴더가 워크트리면 뿌리 항목을 고른다.
- 스크립트가 폴더를 바꾸면 앱의 마지막 폴더가 바뀌어, 잠금(`Invoke-SendLocked`)을 모르는 다른 저장소의 열기가 같은 때 그 폴더로 열릴 수 있다. 같은 때 도는 열기와 겹치는 것은 재지 않았다.
- 환경 이름이 폴더의 마지막 토막과 다른 저장소에서는 항목을 찾지 못해 멈춘다(rag-engine은 `rag-engine` 환경이 있어 같았다. 손으로 봤다).

## 인계

제목을 `chore/open-session-selects-repo-folder (인계함)`으로 바꿨고, 백그라운드 `run_checks`(b1oagyybj)를 멈췄고, 워크트리 잠금을 풀었다.
open-session을 부른다 2026-11-10T13:09Z

## 이어받은 세션의 셀프 리뷰(2026-11-10)

범위: 기준 `2a8bd35d`(main), 수정 파일 4개, 미추적 4개, 커밋 0개. 표준 축과 명세 축을 병렬로 돌렸다(표준 축은 sonnet·high).

고친 것(지적마다 근거를 코드에서 열어 맞는 것만 고쳤다):

- 프로브 `composer_env_menu.ps1`의 머리 주석이 「expand=ok·closed= 중 하나라도 없으면 1」이라 적었는데 코드는 그것을 보지 않았다(두 축 모두 지적). 코드가 `expand`가 `ok`가 아니거나 `-Pick` 항목이 없으면 `측정 아님:` 줄을 찍고 1로 끝나게 하고, 주석과 README 행을 맞췄다. `closed=`는 관찰이라 판정하지 않는다고 적었다. 머리 2행의 "아무것도 고르지 않는다"는 `-Pick`이 없을 때만이라고 고쳤다. 프로브를 다시 돌려 `-Pick rag-engine -Leaf zzz`가 `pick=ok`이고 종료 코드 2인 것을 봤다(손으로 돌렸다). `expand` 실패 갈래와 `pick=항목 없음`의 종료 코드 1은 돌려 보지 않았고 코드를 읽은 것이다.
- `Select-ShownFolders` 앞 주석의 "양성 대조가 없다"를 같은 변경이 내놓은 양성(2026-11-10 `-Pick`)으로 바꿨다(대기열 387 "어디로"가 이름으로 든 두 자리 가운데 README만 닫혀 있었다).
- `Get-FolderMismatch`의 멈춤 문구와 스킬 3단계의 사람 부탁이 환경 항목을 경로로 고르라고 했다. 항목 이름은 환경 이름이므로 "폴더가 `<-Folder>`인 환경을 고르고"로 고쳤다.
- `Select-ComposerFolder`가 펼치기 결과 확인(`$opened -ne 'ok'`)을 접는 `try` 밖에 두어, 펼치기가 멈춤·오류로 돌아온 뒤 뒤늦게 열린 메뉴를 접지 않았다. `try` 안으로 옮겼다.
- `Repair-ShownFolder`가 골랐는데 6초 안에 폴더가 안 바뀌면 열린 메뉴를 접지 않고 던졌다. 던지기 전에 환경 버튼이 펼쳐져 있으면 접는다.
- `Send-Prompt`가 읽은 경로 여럿 가운데 `-Folder`가 이미 있어도 환경을 골랐다(낯선 글이 함께 읽히면 견줌이 영영 같아지지 않아 앱의 마지막 폴더만 바뀐다). 그 경우는 고르지 않고 멈춘다.
- 시험이 소스 글자의 있고 없음만 봐서 견줌 결과를 뒤집어도 초록이던 자리: `Repair-ShownFolder`의 조건 전체 글자(`$shown.Count -gt 0 -and -not (Get-FolderMismatch $shown $folder)`), 위 새 가드, 접기의 자리(try 안의 확인, 던지기 앞의 접기)를 시험으로 고정했다. 변이 셋을 더해 아홉이 되었고 아홉 모두 기대대로 빨강이다(`tools/mutate.py`, 손으로 돌렸다). 마지막 옛 변이의 `old`가 바뀐 줄과 달라져 새 줄에 맞췄다.
- 티켓: "다른 폴더를 고르지 않는다"를 「고르는 환경 이름은 `-Folder`의 마지막 토막뿐이고, 같은 이름의 환경이 다른 폴더를 가리키면 고른 뒤에야 알아 마지막 폴더가 바뀐 채 멈춘다」로, 음성 갈래 서술을 손으로 본 것은 항목 없음 하나뿐이라고, 대기열 378 인용을 글자 그대로 있는 말이 아니라 풀어 쓴 말로, "`-Folder`는 저장소 뿌리"를 조건이 붙은 말로 고쳤다. 스킬 3단계에 「환경을 고른 뒤 멈췄으면 앱의 마지막 폴더는 이미 바뀌어 있다」는 뜻의 괄호를 더했다.
- 실제 앱 다시 돌림(변경 뒤): `-Pick rag-engine`으로 앱의 마지막 폴더를 `rag-engine`으로 돌린 뒤 `-Action send -Folder C:\project\agent`를 첫 줄이 옮길 수 없는 슬래시 명령인 프롬프트로 쳤다. `folder-fixed=C:\project\rag-engine -> C:\project\agent`, `folder=C:\project\agent`, `held=` 순으로 나왔고 앱의 마지막 폴더는 `agent`다.

남긴 것과 이유:

- 정상 흐름(`$mismatch = $null`, `folder-fixed=` 출력)이 `try` 안에 섞인 것, `Select-ComposerFolder`·`Repair-ShownFolder`가 명령이면서 값을 돌려주는 것(CQS), `Select-` 동사가 순수 필터와 UI 클릭에 같이 쓰인 것, `($win,$box,$needle,$folder)` 덩어리, 기존 `Select-ComposerModelItem` 뼈대와의 닮음: 모두 냄새 기준선의 판단 항목이고 이 파일의 기존 모양(같은 `try`/`catch` 문구 덧붙이기, 이웃 함수의 인자 모양)과 같아 이 PR에서 구조를 바꾸지 않았다. 구조를 바꾸려면 기존 모델 고르기까지 함께 손대야 한다.
- 프로브 `-Pick`이 앱의 마지막 폴더를 바꾸고 되돌리지 않는 것은 머리 주석에 적었다(진단 전용).
- 신뢰 대화상자가 환경을 고른 뒤 뜨는지는 보지 못했다(명세 축 3). 떠도 6초 뒤 폴더 불일치로 멈추는 갈래라 위험이 작다고 보고, 확인은 병합 뒤 첫 인계 열기가 한다.

## 첫 커밋 시도(2026-11-10)

pre-commit의 pytest 한 프로세스가 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`(동시에 두 회차가 도는 것을 시간으로 재는 시험)에서 `max(running) == 2`가 1이어서 커밋을 막았다. 이 변경과 닿지 않는 파일이다. 같은 시험을 단독으로 돌리니 통과했다(87초, 이 PC에 다른 세션이 여럿 돌던 때. 손으로 돌렸다). `.claude/rules/tests.md`가 말하는 시간 의존 시험의 부하 취약성으로 보고 다시 커밋한다. 6884개 통과 1개 실패였고 그 밖의 검사(web-verify 등)는 통과했다. 둘째 시도도 이 변경과 닿지 않는 시간 의존 시험 둘(`tests/channel/cli/test_interrupt.py`의 Ctrl+C 뒤 30초 안에 끝나는지 재는 두 시험)에서 막혔다. 러너가 1169초 걸렸고, 그 시험 파일을 단독으로 돌려도 6개 통과에 149초가 걸렸다(이 PC에 claude 45, node 149, python 34 프로세스가 떠 있던 때, 손으로 셌다). 부하 때문으로 보고 다시 커밋했고, 셋째 시도도 시간 의존 시험 둘(`test_interrupt.py`의 도구 호출 도중 Ctrl+C와 `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`)에서 6883개 통과 2개 실패로 막혔다. 셋째 시도의 두 시험도 단독으로 통과했다(손으로 돌렸다).

사용자에게 물었다(`AskUserQuestion`, 질문 「커밋이 PC 부하 때문에 시간 의존 시험에서 세 번 막혔습니다. 어떻게 할까요?」). 사용자 답: 「pytest 훅만 건너뛰고 커밋」. 그 선택지의 설명(글자 그대로): 「pre-commit의 pytest 검사 하나만 `SKIP=pytest`로 빼고 커밋합니다. 나머지 검사(린트, 타입, web 등)는 그대로 돕니다. 세 번의 시도에서 실패한 시험은 다섯 개였고(세 번 모두 시간 의존 시험 1~2개, 이 변경과 다른 파일), 단독으로 돌리면 모두 통과했습니다. 셀프 리뷰를 마친 변경의 시험 149개는 따로 초록입니다. 전체 pytest는 PR의 CI가 다시 돌려 최종 판정합니다. 건너뛴 사실은 일지와 PR 본문에 적습니다.」

그래서 이 커밋은 `SKIP=pytest`로 pytest 훅을 뺐다. 나머지 훅은 돌았다. 전체 pytest는 CI가 판정한다.

## PR 직전 리뷰(2026-11-10, `coderabbit-review`)

CodeRabbit CLI 0.7.5가 끝까지 돌았고(`review_completed`, 파일 8개) 지적은 0건이었다(좌석 `Seat: not assigned`, `Plan: Free`). 에이전트가 직접 읽고 민 결과:

- Major: `Repair-ShownFolder` 끝의 접기가 `Find-ComposerButton $win '환경:'`로 부르는데 그 함수의 첫 인자는 입력창 요소라, 창을 주면 버튼을 못 찾거나 던지고 `catch { }`가 삼켜 접기가 조용히 빠진다. 이 세션이 보고를 받기 전에 같은 오류를 `Find-PromptBox`가 돌려준 입력창 요소(`$lastBox`)를 넘기게 고쳤고(밀 주장 2에 그것을 넣었더니 에이전트가 같은 자리를 짚었다), 그 인자를 시험 한 줄과 변이 하나(열 번째)로 고정했다. 소스 글자만 보는 시험이라 첫 판의 시험은 이 오류를 못 잡았다.
- Minor(고침): 프로브 `-Pick`에서 `select`가 `ok`가 아니어도 `pick=` 줄만 찍고 0이나 2로 끝났다. `ok`가 아니면 `측정 아님`을 찍고 1로 끝나게 하고 머리 주석과 README를 맞췄다(돌려 보지 않았고 코드를 읽은 것이다).
- Minor(고침): 일지 앞쪽의 변이 여섯이 뒤의 아홉·열과 갈려 읽혀 앞 문장에 "나중에 열이 되었다"를 붙였다.
- Minor(남김): `Select-ComposerFolder`의 `catch`에서 `Test-Expanded $button`이 시간 제한 없이 UIA를 직접 부른다. 펼치기가 `expand-hung`일 때 앱의 UIA가 멈춘 중이면 이 호출도 멈출 수 있다. `Test-Expanded`가 시간 제한 없이 부르는 것은 기존 코드의 모양이고(이 변경이 만든 것이 아니다) 이어서 멈추는지는 재지 못했다. 이 PR이 `Test-Expanded` 자체를 바꾸지 않는다. 고치려면 그 함수를 쓰는 기존 모든 자리를 함께 봐야 한다.
- 맞은 것: 가드 조건식은 문장대로(경로 하나만 읽혀 다르면 고치기로 들어간다), 펼치기 확인이 `try` 안이라 hung도 `catch`로 간다, 프로브 종료 코드 규칙이 주석·README·코드와 맞는다, 일지·티켓의 사실 문장이 코드와 맞는다. 보안: `Test-RepoFolder`를 지난 `-Folder`의 마지막 토막만 쓰이고 항목이 정확히 하나일 때만 고른다.

밀 주장(셀프 리뷰 반영이 새로 쓴 사실 문장, PR 직전 리뷰에 넘긴 목록):

1. `Send-Prompt` 주석(풀어 쓴 요지): 읽은 경로 가운데 -Folder 와 같은 것이 이미 있으면 환경을 골라도 견줌이 같아지지 않으므로 고르지 않고 멈춘다.
2. `Repair-ShownFolder` 주석: "골랐는데 폴더가 바뀌지 않았다면 메뉴가 스스로 닫히지 않았을 수 있다. 열려 있으면 접는다".
3. `Select-ShownFolders` 주석: "2026-11-10 composer_env_menu.ps1 의 -Pick 이 양성으로 대 봤다(환경을 고르자 이 Text 가 C:\project\rag-engine 으로 바뀌었다, 손으로 돌렸다)".
4. 프로브 머리(풀어 쓴 요지): 앞의 둘이 없으면 그 자리에서, expand 가 ok 가 아니거나 -Pick 항목을 찾지 못했거나 고르기가 ok 가 아닐 때는 끝에서 `측정 아님` 줄을 찍고 1로 끝난다.
5. 티켓과 스킬의 "고른 뒤 멈췄으면 앱의 마지막 폴더는 이미 바뀌어 있다".
