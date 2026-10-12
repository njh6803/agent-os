# 2026-10-12 (26) Git Bash 경로 변환 함정을 훅으로 경고한다

next-session 지시문으로 연 새 세션이다. 대기열 195를 `chore/msys-pathconv` 한 PR로 반영하고, 196·191을 묶을지는 이 세션이
정한다. 세션은 주 체크아웃에서 열려 `tidy-checkouts`로 루트를 당긴 뒤(`a8e349c`→`030c976`) `EnterWorktree`로 새 워크트리에
들어가 브랜치를 바꿨다.

> 사용자: (지시문의 시작 프롬프트) "대기열 195(Git Bash 경로 변환 함정, 5회차)를 chore/msys-pathconv 한 PR로 반영한다. 196·191(카나리아 문서)을 묶을지는 이 세션이 정한다"

## 체크아웃 정리

`tidy-checkouts` 판정에서 지운 것은 없다. 남긴 것은 잠금 pid가 살아 있는 열하나, 병합된 PR이 없는 다섯, 작업 디렉터리로 쥔
프로세스가 있는 둘(`review-workflow-guards`, `rewrap-and-separator-hook`), 다시 만들 수 없는 무시된 항목(`grep.exe.stackdump`)이
든 `canary-spec-pipeline-followup`, 병합된 PR이 없는 로컬 브랜치 스물셋이다. 넘긴 것은 분리 HEAD 넷, `prunable` 하나, 병합된
PR의 머리와 브랜치 끝이 다른 것 하나, 제목이 어느 브랜치와도 맞지 않는 실행 중 세션(`docs/admin-style-spec`) 때문에 넘긴
`spec-pipeline-and-pytest-ids`, 등록 없는 워크트리 폴더 여섯이다. 지시문대로 답을 기다리지 않았다.

## 196·191을 묶지 않았다

둘은 카나리아 문서(`operations.md` 카나리아 항목과 명세 머리 주석 열여덟)를 고치는 일이라 Bash 훅과 영역이 다르다. 196은
명세 열여덟의 머리 주석으로 결과를 옮기는 재배치라 diff를 차지해 이 PR의 리뷰 초점이 흐려진다. 둘은 같은 `operations.md`
카나리아 항목을 고치므로 서로 묶는 것이 맞다.

## 측정이 대기열 행의 조건을 뒤집었다

대기열 195와 일지 21은 "콜론 양쪽에 `/`가 든 인자"가 바뀐다고 적었다. 훅의 판정을 세우려고 프로브
`.scratch/harness/probes/msys_pathconv/run.sh`를 지어 쟀더니 `a/b:c/d`와 `origin/main:src/agent_os/main.py`는 그대로였고,
바뀐 것은 첫 콜론 오른쪽이 `.`·`/`로 시작하는 것뿐이었다. 이 저장소에서는 점으로 시작하는 경로(`.scratch/`·`.claude/`·
`.github/`)를 가리킨 `<rev>:<경로>`가 그렇다. 조건의 뼈대는 git-for-windows/msys2-runtime의 `msys2_path_conv.cc`
(`a362d1c`)에 있는 `find_path_start_and_type`을 `gh api`로 받아 읽고 세웠다. 소스와 이 PC의 런타임(3.1.7)이 다른
자리(`..:.x`)는 잰 것을 따랐다.

손으로 본 것이 셋이다. 사건의 명령 `git show origin/main:.scratch/retro-queue.md`는 종료 128과
`fatal: ambiguous argument 'origin\main;.scratch\retro-queue.md'`로 끝났다. 우회 `MSYS_NO_PATHCONV=1 git rev-parse --verify
origin/main:.scratch/retro-queue.md`는 워크트리 가드를 지나 SHA를 냈고, `git rev-parse --verify origin/main:./.scratch/retro-queue.md`도
그랬다.

## 바꾼 것

- **훅 `tools/hook_bash_msys_pathconv.py`(PreToolUse Bash).** 명령 위치의 git이 받을 인자 가운데 Git Bash가 바꿀 것이 있으면
  `additionalContext`로 알리고, git 바로 앞의 `MSYS_NO_PATHCONV=1`이나 저장소 루트의 `<rev>:./<경로>`를 안내한다. 막지 않는다.
  실패가 대개 `fatal:`로 드러나 조용하지 않고 지침으로 적은 적도 없어서다(`.claude/rules/tools.md`의 막는 훅 조건). 윈도이거나
  `MSYSTEM`이 있을 때만 알리고, 리눅스 CI의 훅 러너는 발동 사례에 `MSYSTEM`을 넣는다. 훅이 잡으므로 `CLAUDE.md` 환경 함정에는
  적지 않았다(교정 루프의 "린터가 잡는 것을 지침에 적지 않고").
- 새 훅의 넷: `.claude/settings.json` 등록(래퍼 모양), `tests/tools/test_hook_bash_msys_pathconv.py`(모양 표는 프로브 출력을
  옮겼다), `tools/hook_payloads.toml`의 발동 하나와 침묵 둘, 변이 표 `msys_pathconv_hook_mutations.toml`.
- 프로브 셋(`msys_pathconv/run.sh`·`argv.py`, `msys_pathconv/time_hook.sh`, 변이 표)과 README 행.
- `KICKOFF.md` 훅 줄과 계기 훅 목록, `kickoff/pitfalls.md`의 [Win] 행, 대기열 195 닫힘(조건과 회차를 바로잡았다).

테스트를 먼저 써서 모듈이 없는 빨강을 봤다. 첫 판은 71개가 한 번에 초록이었다.

## 셀프 리뷰

`/code-review`(base `79a0c19`, 수정 5·미추적 4·커밋 0). `.py`가 있어 두 축 모두 기본 모델이었다. 명세는 지시문, 대기열 195의
원래 글, 일지 21의 회고 1과 사용자 답의 라벨, `.claude/rules/tools.md`의 새 훅 규약을 요구로 넣었다. 두 축 모두 브리프에 소스
발췌(URL과 커밋)와 프로브 출력 전문을 실었다(대기열 156). Critical·Major는 없었고, 판정 모델의 틀림과 닫힌 주장이 대부분이었다.

- **고친 것.**
  - [표준] 판정이 소스보다 좁았다. 첫 콜론 뒤의 `=`(`a:b=origin/main:.x`), `-` 머리의 `:`·`,`(`-Lx:origin/main:.y`,
    `-x,origin/main:.y`)도 바뀐다. 프로브에 모양 일곱을 더해 재고(`` ` ``·`'`·`?`는 소스만 읽고 적었던 것이라 함께 쟀다),
    `converts`를 소스의 루프 차례대로 다시 썼다.
  - [명세] 못 보는 것이 덜 적혔다. 주석 뒤의 개행을 shlex가 먹어 다음 줄의 git을 놓쳤고(개행을 둘로 늘려 고쳤다), 리다이렉션이
    조각을 갈라 `git show 2>/dev/null origin/main:.x`를 놓쳤고(대상과 fd만 빼게 고쳤다. `2>/dev/null git …`도 잡게 됐다), 산술
    `$(( … << … ))`를 heredoc으로 읽었다(`hook_bash_cd_outside`의 판정을 옮겼다). 따옴표 안의 `<<`와 변수가 든 인자는 못 보는
    것으로 적고 테스트로 고정했다. PowerShell 항목은 settings.json의 매처를 읽는 테스트로 고정했다.
  - [두 축] 안내·대기열·`KICKOFF.md`가 조건을 예외 없이 닫았는데, 안내가 권하는 `<rev>:./<경로>`가 바로 그 예외였다. "대개"와
    예외를 적었다. 안내의 "명령 앞에"는 체인(`cd web && git …`)에서 대입이 `cd`에만 걸려 "git 바로 앞에"로 바꿨고,
    "이 때문이다"는 "이 때문일 수 있다"로 낮췄다.
  - [명세] 사건은 다섯 세션의 여섯이었다. 일지 2026-10-11-01이 "Windows 경로로 바꿔"라는 말로 적어 첫 grep에 걸리지 않았다.
  - [두 축] 페이로드 표의 침묵 사례 노트가 출처를 잘못 들었다. 재구성한 명령에 그렇다고 적고 이 세션이 친 명령은 이 일지를
    가리키게 했다.
  - [명세] `run.sh`를 `/c/…` 경로로 부르면 `MSYS_NO_PATHCONV=1` 아래의 파이썬이 `argv.py`를 못 찾아 열이 비었는데 0으로 끝났다.
    `pwd -W`로 윈도 경로를 쓰고 받은 줄 수를 대조해 1로 끝나게 했다. 머리 주석의 "우회 둘"도 셋으로 고쳤다.
  - [표준] `time_hook.sh`가 출력을 버려 알림 길이 돌았는지 보지 않았다. 알렸는지 찍고 기대와 다르면 1로 끝나게 했다.
  - [표준] "점 폴더"는 좁았다(`.gitignore`, `.env.example`). "점으로 시작하는 경로"로 고쳤다. `_DISABLED`는 `_PATHCONV_OFF`로,
    `_LEADING_WORDS`의 두 집합 쪼갬은 튜플 둘의 합으로 바꿨다.
  - [표준 판단] `kickoff/pitfalls.md`의 [Win] 표에 이 함정 행을 더했다.
- **남긴 것.**
  - [표준 smell, Shotgun Surgery] 모양 하나를 더하면 `run.sh`, 테스트 표, README의 수를 함께 고쳐야 한다. 프로브의 출력을 테스트
    표로 옮기는 구조의 값이다.
  - [표준] `time_hook.sh`의 값을 리뷰어는 222~348ms로 재 첫 판의 201~240ms를 재현하지 못했다. 반영 뒤 다시 재니 221~353ms였다.
    README에 두 판을 모두 적었다.

반영 뒤 새 테스트 85개가 통과했고 훅 러너는 78건 어긋남 0이었다. 변이는 서른여섯 모두 빨강이었다. 그중 "(옛 판정)" 넷과
"(옛 문구)" 하나는 반영 전의 행동으로 되돌린 것이라, 구현을 먼저 고쳐 보지 못한 새 테스트의 빨강을 그것으로 봤다.

## PR 직전 보안·버그·성능 축

CodeRabbit CLI는 이번에도 `Seat: not assigned`라 대체 둘을 나란히 돌렸다(커밋 `8a01533` 기준, 범위 `79a0c19...HEAD`).

- **보안(`/security-review`).** 발견 없음. 훅은 명령을 `shlex`로 나누기만 하고 실행·파일 쓰기·네트워크가 없으며, 출력은 고정
  키 둘을 `json.dumps`로 내므로 명령으로 판정 필드를 끼워 넣지 못한다. 안내하는 `MSYS_NO_PATHCONV=1` 접두를 붙여도
  `hook_env_read`가 대입을 벗기고 판정해 `.env` 차단은 그대로다.
- **버그·성능(`bug-perf-review`).** 유효 셋(모두 Minor), 오탐·수용 여섯이었다. 띄운 백그라운드 작업은 없었다고 보고했다.
  - 고쳤다: `converts`가 `=`마다 재귀해 천 개쯤에서 `RecursionError`로 경고가 사라졌다. 그 자리로 옮겨 다시 도는 루프로 바꾸고
    마지막 `=`의 위치를 한 번 구해 콜론마다 뒤를 다시 훑지 않게 했다. 재귀로 되돌린 변이로 새 테스트의 빨강을 봤다.
  - 고쳤다: 모든 Bash 명령을 `shlex`로 나눠, 큰 따옴표 문자열 하나에 제곱 시간(리뷰어가 손으로 본 값은 1MB에 약 20초, 훅의
    `timeout`과 같다)이 들었다. `:`나 `git`이 없는 명령은 나누기 전에 돌아간다.
  - 고쳤다: 프로브가 측정의 전제를 단언하지 않았다(대기열 197의 모양). `run.sh`는 첫 모양이 실제로 바뀌었는지 단언하고,
    `time_hook.sh`는 Git Bash에서만 돈다는 것을 머리 주석과 README에 적었다.
  - 수용으로 왔지만 고쳤다: `>|`를 리다이렉션으로 알아보게 했다. 프로세스 치환 `<( … )` 뒤의 인자는 못 보는 것으로,
    리뷰어가 인자 약 6만 개를 이 PC의 Git Bash로 손으로 대조해 찾은 거짓 양성 열하나의 모양(`+//:/`)은 독스트링에 적고 둘 다
    테스트로 고정했다(`.claude/rules/tools.md`의 "항목마다 테스트 하나"). 그 모양과 `@/a:.b`를 프로브에 더해 쟀다.
  - 오탐: 판정과 실제 변환의 거짓 음성 대부분은 `/`로 시작하거나 머리 글자 뒤에 `/`가 오는 것이고 `<rev>:<경로>` 꼴은 없었다.
    stress 입력 서른 가량은 `RecursionError` 말고 예외가 없었고, 리다이렉션이 엉뚱한 인자를 경고하는 경우도 없었다.
- 반영 뒤 새 테스트 90개가 통과했고 변이 서른아홉 모두 빨강이었다.

## 검사

- 검증 명령(셀프 리뷰 전): `uv run pytest -q` 2150 passed(7 deselected), `ruff check`·`ruff format --check`, `pyright` 0 errors,
  `lint-imports` 5 kept, `pnpm -C web verify` 테스트 357 통과. 타입 우회 검사와 지침 검사도 통과였다.
- 셀프 리뷰 반영 뒤에는 손으로 다시 치지 않고 커밋 `8a01533`의 pre-commit으로 갈음했다. ruff 둘과 검사 러너의 여덟(zizmor,
  지침 검사, lint-imports, 타입 우회 검사, pyright, 훅 러너, web-verify, pytest)이 모두 통과였고 가장 긴 pytest가 230.6초였다.
  표·줄 구분 문자·변이 표·인용·커밋 메시지 검사도 통과였다.
- 변이: 첫 판 스물여섯, 셀프 리뷰 반영 뒤 서른여섯, PR 직전 리뷰 반영 뒤 서른아홉 모두 기대대로(`tools/mutate.py`).
- 훅 비용: 래퍼를 거쳐 한 번에 첫 판 201~240ms, 셀프 리뷰 반영 뒤 221~353ms, PR 직전 리뷰 반영 뒤 261~641ms
  (`msys_pathconv/time_hook.sh`. 셋째 판은 다른 세션들이 돌던 때라 흔들렸다). `Bash` 매처의 PreToolUse
  훅이 다섯이 되고, `Bash|PowerShell`·`Bash|Grep`·매처 없는 것까지 Bash 호출 하나에 붙는 PreToolUse 훅은 아홉이다.
