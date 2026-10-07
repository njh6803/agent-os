# 2026-10-07 (20) claude-review 워크플로의 게시·`.git/` 읽기·함께 실은 파일

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 84·146·158이 모두 `.github/workflows/claude-code-review.yml`을
고쳐 한 PR로 닫고, 셀프 리뷰 뒤 사용자 승인으로 같은 가드 단계의 161도 닫는다. 세션은 주 체크아웃에서 열렸고, 지시문대로
`tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=review-workflow-guards)`로 들어가 `origin/main`(`4d34bee`, #169)에서
`chore/review-workflow-guards`를 땄다. 일하는 사이 #170(`d5ee5e4`)과 #171(`f71e577`)이 병합되어 커밋 전에 그 위로
옮겼다. #171과는 워크플로 4~6단계와 대기열 146·158~161 행이 겹쳐, 미커밋 작업을 고유 태그로 stash했다가 앞당긴 뒤 다시
얹고 손으로 풀었다. 순번은 20이다. 18은 #171이, 19는 #170이 썼다(`tools/sibling_overlap.py`).

## 계기

> 사용자: "대기열 84·146·158(대상 파일 .github/workflows/claude-code-review.yml)을 한 chore PR로 반영한다. 그 파일을 바꾼 PR은 claude-review가 건너뛰므로 리뷰는 CodeRabbit과 셀프 리뷰로 손으로 본다"

지시문의 선행 조건은 둘이었다. 같은 파일을 고치는 PR #171이 병합된 뒤 브랜치를 딴다, 146은 권한 규칙 탐침이 먼저다.
#171은 열려 있었고(CodeRabbit은 시간당 한도, claude-review는 건너뜀, 그 세션은 멈춤), 일지 18의 "다음"은 146의 탐침
범위를 사용자에게 먼저 물으라고 했다. 둘을 함께 물었다.

> 사용자: (고른 것) "지금 시작, PR 전 rebase (Recommended)", ".git/ 경로 전부 (Recommended)"

두 번째 선택지의 설명은 다음 문장을 담았다.

> "그래서 Read(./.git/**) deny에 더해, 허용 목록에서 .git/config를 읽을 수 있는 다른 길(git diff --no-index, gh pr comment --body-file 임의 경로)도 막습니다."

 `/proc/self/environ` 같은 `.git/` 밖의 길을 더하는
선택지는 고르지 않았다.

셀프 리뷰 중 #171이 병합되며 대기열 161(가드가 `gh pr diff`의 실패를 이 파일을 바꾸지 않은 PR로 읽는다)을 남겼다. 이
PR이 고친 가드 단계라 함께 닫을지 물었다.

> 사용자: (고른 것) "이 PR에서 닫는다 (Recommended)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `eda296e`에서 `4d34bee`로 당겼다. 스킬 파일은 바뀌지 않았다.
- **지운 것.** `silly-carson-627e95`와 브랜치 `chore/open-session-wake-display`.
- **종료 1로 남은 것.** `tidy-before-worktree`는 다른 프로세스가 폴더를 쥐어 이름 바꾸기가 막혔다(일지 19와 같다).
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`,
  분리 HEAD `unruffled-lalande-9017fa`, 등록 없는 폴더 여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 확인한 것

- **액션의 Claude Code 판이 로컬과 같다.** 고정한 액션 커밋 `5898584`의 `src/entrypoints/run.ts`가 2.1.292를 깔고, 이 PC도
  2.1.292다. 그래서 로컬 `claude -p`의 권한 판정을 CI의 판정으로 읽는다. 액션은 `claude_args`의 `--allowedTools`·
  `--disallowedTools`를 쉼표로 나눠 합치고(`base-action/src/parse-sdk-options.ts`), 설정 출처는 user·project·local이다.
  저장소의 `.claude/settings.json`은 `.env`만 막아 CI에서 더해지는 허용이 없다.
- **허용 목록 밖의 읽기 전용 명령이 돈다.** 처음 손으로 본 것은 지금의 허용 목록으로 `git remote -v`였고, 묻지 않고 돌아
  가짜 토큰을 찍었다. 공식 permissions 문서는 Claude Code가 읽기 전용으로 아는 명령(`cat`, `grep`, 읽기 전용 `git` 등)을
  모든 모드에서 묻지 않고 돌린다고 적는다. 대기열 행의 전제("모델의 `Read`는 그 파일을 읽을 수 있다")보다 길이 넓었다.
- **탐침 `review_git_read.py`.** 사례마다 새 임시 저장소의 `origin` URL에 가짜 표지를 넣고, 워크플로의 규칙으로
  `claude -p`(haiku)에게 도구 호출 하나를 시켜 stream-json의 결과와 `permission_denials`로 가른다. `gh`는 PATH 맨 앞의
  가짜이고 원격은 `git.invalid`다. 거부는 메시지로 규칙·승인·자체 검사를 가르고, 사례마다 기대하는 갈래를 적었다. 지금
  main의 규칙에서 88개 중 56개가 어긋났다. 42개는 읽혔거나 거부 없이 돌았고, 14개는 승인이나 자체 검사로 막혔다. `--keep`으로 Read 거부 둘과 `Bash(git:*)`만 남긴 판은 32/88이고, 이
  판이 아래 둘을 가른다.
  - `Read(./.git)`·`Read(./.git/**)` 거부만으로 Read·Grep 도구, 경로를 그대로 댄 명령(`cat`·`head`·`sed`·`sort`·`nl`·`tac`·
    `awk`·`uniq`·`diff`·`grep`), 입력 리다이렉트, `cd .git && cat config`가 거부(규칙)였다. Grep 도구로 루트를 찾으면 숨은
    `.git`을 건너뛰었다.
  - **경로를 glob으로 적으면 Read 거부가 그 경로를 알아보지 못했다.** 같은 판에서 `cat .gi*/config`가 읽혔고, 그 모양으로
    훑으니 `cat`·`head`·`tail`·`nl`·`tac`·`grep`·`egrep`·`fgrep`·`cut`·`column`·`diff`와 `command cat`, `c''at`, `\cat`,
    `"cat"`, `cat .*/config`가 읽었다. `od -c`·`cmp -l`은 바꿔 찍었고, `strings`·`hexdump`·`rev`는 이 PC에 없을 뿐 권한
    단계를 지났다. `sort`·`less`·`xxd`·`base64`·`dd` 등은 glob이 들면 승인이 필요해져 막혔다.
  - `grep -r … .`과 `rg -uu … .`은 경로를 대지 않는 검색이라 Read 거부 밖이었다(문서가 적는 그대로다).
  - `git diff --no-index`와 `gh pr comment --body-file .git/config`는 파일을 스스로 여는 하위 프로세스라 읽었다.
- **처방은 이름으로 막는 것이다.** `--disallowedTools`에 `.git/` 둘, `Bash(git:*)`, 위의 `--keep` 판에서 읽거나 권한
  단계를 지난 셸 명령 열일곱(`rg`는 경로 없는 검색으로)을 두었다. 래퍼(`command`, `env`, `nice`, `timeout`)와 따옴표 모양은
  벗겨져 같은 규칙에 걸렸다. 게시는 `Bash(gh pr comment <번호> --body-file review-comment.md)` 하나를 글자 그대로 허용해
  본문 경로를 고정했다. 같은 탐침이 작업 트리에서 0/88이다(130초).
- **남은 위험.** 권한 규칙은 Claude가 쓴 호출의 모양만 맞춘다(공식 문서: 보안 경계가 아니다). 사례 밖의 읽기 명령과
  모양은 이 결과가 말하지 않는다. 모든 프로세스를 막는 것은 샌드박스이고, 이 PC에서는 잴 수 없어(Windows) 고르지 않았다.
  액션을 올려 Claude Code 판이 바뀌면 읽기 전용 집합도 바뀔 수 있어 워크플로 주석에 다시 돌라고 적었다.
  `/proc/self/environ`(액션이 `process.env`를 그대로 넘긴다, `parse-sdk-options.ts`)은 사용자가 범위에서 뺐다.
- **84.** PR #116 2회차는 `/tmp`로의 리다이렉트(작업 디렉터리 밖)와 `&& rm`이 막히자 앞선 코멘트를 제 것으로 읽었다.
  5단계를 Write 도구로 작업 디렉터리의 `review-comment.md`에 쓰고, 허용된 그 명령 하나를 단독으로 치고, 그 명령이 낸
  URL로 확인하게 바꿨다. 앞선 "## 코드 리뷰" 코멘트를 확인으로 쓰지 말라고도 적었다. 6단계에서는 `git diff`·`git log`·
  `git show`를 뺐다. 체크아웃이 `fetch-depth: 1`이라 볼 이력도 거의 없었고, 이제 `Bash(git:*)`가 막는다.
- **158.** 가드는 이 파일이 바뀐 PR에서 바뀐 파일 목록을 보고, 이 파일과 일지(`docs/journal/`), 대기열
  (`.scratch/retro-queue.md`), 하네스 탐침(`.scratch/harness/probes/`) 밖의 파일이 있으면 그 목록을 찍고 실패한다.
  탐침을 받는 것은 일지 17의 "다음"이 적은 대로 가드가 그 PR의 판으로 돌고, 그 PR이 근거로 드는 측정이 탐침이라서다.
- **161.** 전에는 `gh pr diff`가 실패해도 파이프 끝의 `grep`이 그 종료 코드를 가려, 이 파일을 바꾸지 않은 PR로 읽고
  코멘트를 셌다(PR #171의 HTTP 500). 이제 목록을 변수로 받고, 실패하면 "바뀐 파일 목록을 얻지 못했다"를 찍고 실패한다.

## 바꾼 것

- `.github/workflows/claude-code-review.yml`: `claude_args`의 허용·거부와 그 주석, 프롬프트 5·6단계, 가드와 그 주석.
- `.scratch/harness/probes/review_git_read.py`(새것), `review_workflow.py`(사례 열일곱, 결과 다섯과 함께 실음의 목록 단언,
  `pr diff`가 실패하는 가짜 `gh`), `README.md`의 두 행.
- `.scratch/retro-queue.md`: 84·146·158·161을 닫고 회고 후보 162~164를 더했다.

## 잔존 grep

`git log·git show`, `` `git diff`·`git log` ``, `Bash(git diff`, `Bash(gh pr comment`, `body-file <파일>`, `검사도 건너뛴다`,
`가드가 꺼`, `가드도 꺼`, `review_workflow.py`, `review-comment.md`를 md·yml·yaml·py·toml·json·ts에서 찾았다. 셀프 리뷰가
가드 자신의 출력 "검사도 건너뛴다"를 짚어 "코멘트는 세지 않는다"로 고쳤다. 그 뒤 살아 있는 문서의 잔존은
`.github/PULL_REQUEST_TEMPLATE.md` 37행 하나다. "그 PR은 claude-review가 건너뛰고 코멘트 0개 가드도 꺼지므로"인데,
이제 가드는 코멘트를 세지 않을 뿐 함께 실린 파일을 본다. 그 파일은 가드의 목록 밖이라 이 PR에 실으면 이 PR이 빨개진다.
그래서 이 PR이 병합된 뒤 따로 고친다(대기열 164). `operations.md` 리뷰 파이프라인의 "그 파일의 변경은 별도 PR로 먼저
병합한다"는 그대로 참이다. 나머지는 기록(일지, done인 web-admin 명세·티켓, 닫힌 대기열 50)과 ADR 0027의 대안 서술이다.

## 검사

- `review_workflow.py`: 158까지의 판에서 작업 트리 0/16, `origin/main`(`d5ee5e4`) 7/16(함께 실음 사례 일곱이 건너뜀).
  가드의 정규식에서 일지를 손으로 뺀 변이는 2/16이었다(기록 셋 사례가 함께 실음, 다른 문서 사례의 목록에 일지가 꼈다.
  변이 표가 없어 커밋으로 다시 낼 수 없다). 되돌렸다. 161까지의 판에서 작업 트리 0/18, `origin/main`(`f71e577`) 9/18(목록
  실패 사례 둘이 코멘트를 센 통과·실패).
- `review_git_read.py`: 작업 트리 0/88(130초), `--keep` 판 32/88(132초), `origin/main`(`f71e577`) 56/88(147초). 갈래를 보기 전의 판은 `origin/main`에서
42/88이었다. 첫 판(사례 31)은 셋을 잘못
  셌다. 표지를 패턴으로 쓴 `grep`은 거부 메시지가 명령을 되풀이해 읽힘으로, 모델은 문장 끝 마침표를 명령에 붙였고
  (`grep -r X ..`), `diff /dev/null`은 작업 디렉터리 밖이라는 다른 까닭으로 막혔다. 패턴을 `x-access-token`으로, 값을
  백틱으로, 경로를 저장소 안으로 바꿨다. 막혀야 하는 길은 거부만 통과로 보고, 셀프 리뷰 뒤로는 거부의 갈래까지 본다.
  거부 없이 돈 명령은 표지가 없어도 바꿔 찍었을 수 있다(`od -c`가 그랬다).
- PyYAML로 리뷰 단계의 `claude_args`, 프롬프트 5·6단계, 가드 스크립트를 찍었다(스크래치 스크립트). 접힌 스칼라가 한 줄
  인자로 풀렸다.
- zizmor(`--offline --strict-collection --config .github/zizmor.yml .`): 지적 없음(10 suppressed).
- 검증 명령: `uv run pytest -q` 1872 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(25파일 338개)가 모두 초록이다. 이 워크트리에는 web 의존성이 없어 `pnpm -C web install --frozen-lockfile`을 먼저 쳤다.
- 바뀐 프롬프트는 이 PR에서 돌지 않는다. 액션이 이 파일을 바꾼 PR을 건너뛰기 때문이다(아래 "다음").

## 셀프 리뷰

`/code-review`(기준 `d5ee5e4`, 수정 4·미추적 2, 커밋 0). 소스가 없어 표준 축은 sonnet이다. 명세는 지시문, 대기열
84·146·158 행, 146의 범위 선택이고 요구와 리뷰어 참고를 갈라 넘겼다. 표준 축은 Major 1·Minor 4·Nit 여럿, 명세 축은
Minor 4·Nit 5였고 Critical은 없었다. 명세 축은 셸 읽기 명령을 이름으로 막은 것을 146의 범위 안으로 봤다.

- **고친 것.**
  - 표준 Major: 기준이 낡았다. 리뷰 중 #171이 병합되어 워크플로와 대기열이 겹치고 161번을 먼저 썼다. `f71e577` 위로
    옮기고 회고 행을 162~164로, 일지의 서술(#171은 열린 PR, #170이 159·160)을 고쳤다. 161을 닫을지는 사용자에게 물었다.
  - 표준 Minor·명세 Minor(겹침): "glob 경로가 Read 거부를 지난다"를 커밋한 탐침이 다시 낼 수 없었고, Read 거부가 막았다는
    명령 여섯은 이름 거부와 겹쳐 갈리지 않았다. 탐침에 `--keep`을 더해 Read 거부와 git만 남긴 판(32/88)으로 둘을 갈랐다.
  - 표준 Minor: 탐침이 막힌 까닭을 단언하지 않았다(`git diff 두 경로`는 main에서 작업 디렉터리 밖 검사로 막혔다).
    거부를 규칙·승인·자체 검사로 가르고 사례마다 기대 갈래를 적었다.
  - 표준 Minor·명세 Nit(겹침): `gh pr diff` 실패의 사례가 없었다. 161과 함께 목록 실패 사례 둘을 더했다.
  - 표준 Minor·명세 Nit: 146 닫힘 메모의 "glob 경로로 지나던"이 `rg`(경로 없는 검색)와 `strings` 등(권한 단계만)에 맞지
    않았다. "허용 목록 밖에서 묻지 않고 돌아 Read 거부를 지나던"으로 고쳤다.
  - 명세 Minor·표준 Nit: 가드의 출력 "검사도 건너뛴다"가 함께 실음 검사 뒤라 반만 참이었다. "코멘트는 세지 않는다"로.
  - 명세 Minor: 5단계의 "`&&`·`;`·`|`·리다이렉션을 붙이면 거부된다"는 잰 적 없는 보편 주장이었다(복합 명령은 하위 명령마다
    판정된다). "다른 명령과 잇지 않고 단독으로 친다"와, 탐침이 잰 "본문 파일의 경로를 바꾸면 거부된다"로 좁혔다.
  - 명세 Nit: "(PR #116 실측)"은 프로브가 아니라 로그를 읽은 것이다. "(PR #116, 일지 2026-10-01-07)"로.
  - 명세 Nit: 선택지 인용이 원문의 "막습니다"를 "막는다"로 바꿨다. 원문 그대로 옮겼다.
  - 명세 Nit: 독스트링의 "세 번까지 다시 돌고"는 모두 세 번이다. 고쳤다.
  - 표준 Nit: "5분쯤"은 어림이었다. 탐침이 걸린 시간을 찍게 했다(130초). 사례당 `claude -p` 한 번이라는 서술에 재시도를,
    정규식 변이에 손으로 넣은 것이라는 것을 더했다. 결과 문자열은 상수로 묶고(Primitive Obsession), 규칙 둘은 `Rules`로
    묶었다(Data Clumps).
- **남긴 것.**
  - 명세·표준 Nit: 가드가 받는 폭(`docs/journal/`과 `.scratch/harness/probes/` 전체)이 "그 PR이 근거로 드는 탐침"보다 넓다.
    좁히려면 가드가 그 PR이 고칠 탐침 이름을 미리 알아야 해 기계 판정의 근사로 둔다.
  - 표준 Nit: 프롬프트 1단계는 `$PR`, 5단계는 숫자다. 5단계는 허용 규칙과 글자 그대로 같아야 해서 숫자로 둔다.
  - 표준 Nit(기준선 냄새): `load_workflow`와 `review_workflow._load`의 중복은 탐침이 서로 import하지 않는 단독 스크립트라
    둔다. `case.tool` 분기 둘, `GLOB_READERS`의 래퍼 섞임, `judge`와 `main`의 추상화 수준, 판 번호 여섯 곳은 판단 항목이라
    두었다.

## PR 직전 보안·버그·성능 축

## PR 리뷰

## 회고

일지 초안의 "다음"을 쓰자 훅이 계기를 넣어 셀프 리뷰 전에 돌았다. 후보 셋을 냈고 셋 다 승인됐다. 이 PR은 가드 때문에
일지·대기열·탐침 밖의 파일을 실을 수 없어 셋 다 대기열로 갔다. 처음에는 161~163으로 적었으나, #171이 155~157과 161을,
#169가 159를, #170이 160을 써서 #171 위로 옮기며 162~164가 되었다.

> 사용자: (고른 것) "1. .env 훅 읽기 명령,2. 리뷰 봇에서 Bash 없애기,3. PR 템플릿 후속"

1. **`hook_env_read`의 읽기 명령 목록의 빈자리(대기열 162, 1회차).** 탐침이 찾은, Claude Code가 묻지 않고 돌린 읽기
   명령 가운데 `column`·`rev`가 그 훅의 `READERS`에 없다. 로컬 세션에서 `column .e*`가 `.env`를 읽을 수 있다는 것은
   그 목록과 탐침 결과를 대 본 어림이고 재지 않았다.
2. **리뷰 봇에서 Bash를 없앤다(대기열 163, 1회차).** 이번 처방은 이름을 하나씩 막는 것이라 사례 밖의 명령은 열려 있다.
   PR 설명·diff를 앞 단계가 받고 게시를 뒤 단계가 하면 모델의 도구는 Read·Grep·Write만 남는다. 코멘트 작성자와 가드가
   바뀌어 ADR이 든다.
3. **PR 템플릿 후속(대기열 164, 1회차).** 위 잔존 grep의 37행이다.

일지에만 남기는 것:

- 탐침의 첫 판이 셋을 잘못 셌다(위 검사 절). 결과를 줄마다 읽어 잡았고, "실패의 까닭까지 단언한다"(대기열 144로 닫힌
  `CODING_STANDARDS.md`의 판단 기준)가 겨누는 모양이다.
- 워크트리 가드가 변수를 쓴 반복문과 `;`로 이은 판 확인 명령을 거부했다. `CLAUDE.md` 환경 함정에 이미 있는 것이고,
  하나씩 다시 쳤다.
- 지시문의 선행 조건 "#171 병합 뒤 브랜치를 딴다"는 그 세션이 멈춰 있어 기다릴 주인이 없었다. 사용자에게 물어 지금
  시작하고 PR 전에 rebase하기로 했다.
- next-session은 일지를 `/code-review` 뒤에 쓰라고 한다. 리뷰가 일지도 보도록 초안을 먼저 썼고, 그 "다음"이 회고의
  계기를 일찍 넣었다.

## 다음

- 병합 뒤 첫 PR의 claude-review 실행에서 바뀐 프롬프트와 규칙으로 요약 코멘트가 게시되는지 본다. 게시 명령이 거부되면
  코멘트 0개 가드가 빨갛게 잡는다. 거부된 호출 수는 `uv run python tools/gh_run_summary.py <run-id>`로 본다.
- 대기열 164(PR 템플릿)는 이 PR이 병합된 뒤에만 할 수 있다. 같은 대상 파일의 열린 행은 셋 미만이다.
