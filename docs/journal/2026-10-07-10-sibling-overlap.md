# 2026-10-07 (10) 커밋 직전의 번호 대조에 열린 PR의 head를 넣는다

일지 2026-10-07-09의 "다음"이 연 새 클라우드 세션이다. 지시문의 브랜치는 `chore/open-pr-number-check`였지만, 이
클라우드 세션에 지정된 브랜치 `claude/hopeful-hopper-2u9q1j`에서 했다. 일지 08·09의 클라우드 세션도 지정된 브랜치를 썼다.

## 계기

> 사용자: "다음 작업: 대기열 115. 커밋 직전의 번호 대조에 열린 PR의 head를 넣는다(5회차). 첫 턴에 SessionStart 훅부터
> 확인한다
> 다음 단계: 하네스 chore
> 어디서: 새 세션. 결정표는 "이 세션"이지만 병합한 SessionStart 훅(tools/hook_session_web_deps.py)이 새 클라우드 세션에서
> 실제로 도는지 보는 것이 첫 일이라 새 세션이다
> 시작 프롬프트: 대기열 115를 반영한다. 그 전에 첫 턴에서 web/node_modules가 있는지, 없으면 SessionStart 훅의 알림이
> 컨텍스트에 있는지 본다
> 브랜치: chore/open-pr-number-check
> 읽을 것: docs/journal/2026-10-07-09-session-web-deps-hook.md의 "번호를 옮겼다"와 "다음"
> 이어받을 상태: 없음
> 확인할 선행 조건: 클라우드 환경의 Setup script 칸이 .scratch/harness/cloud-setup.sh와 같은지(사용자 쪽 설정이라 이
> 세션에서 보지 못했다). 열린 PR #158과 README.md 클론 뒤 설치 문단, tools/hook_bash_gate_pipe.py 게이트 정규식에서 글자
> 충돌이 남았다
> 이번 요청 범위: PR과 병합까지"

## SessionStart 훅이 실제로 돌았다

일지 09가 "못 본 것"으로 남긴 자리다. 첫 턴에 `web/node_modules`가 있었고, 셋을 손으로 봤다.

- **트랜스크립트.** 세션의 jsonl에 `hookName: "SessionStart:startup"`, `command`가 등록과 같은
  `uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python "${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" hook_session_web_deps.py`,
  `exitCode: 0`, `durationMs: 23683`, `stdout`이 빈 `hook_success` 기록이 하나 있었다. 성공하면 아무것도 내지 않는 훅이라
  컨텍스트에 알림이 없는 것이 맞다. `stderr`는 세 줄이다. uv의 `UV_NATIVE_TLS` 경고, `Using CPython 3.12.3 interpreter at: /usr/bin/python3.12`,
  `Creating virtual environment at: .venv`.
- **시각.** 세션이 만들어진 것이 04:33:37(UTC, `get_session`의 `created_at`), 저장소의 클론이 04:33:41(`.git/HEAD`의 mtime),
  `web/node_modules`가 04:34:18, 위 기록의 `timestamp`도 04:34:18이었다. 설정 스크립트 원본에는 pnpm 설치가 없으므로 훅이 깔았다.
- **23.7초.** 일지 09의 세션이 그 컨테이너에서 본 값(스토어가 찬 채 등록 모양으로 훅을 부르면 약 3초, 빈 스토어에서 pnpm만
  4.8초)보다 길다. 새 VM이라 pnpm 스토어가 비었고(`/root/.local/share/pnpm/store`가 04:34에 생겼다), `--no-sync`의 uv가 빈
  `.venv`를 처음 만들었다. 몫을 갈라 재지는 않았다. 등록의 300초, 훅의 240초 안이다. 빈 `.venv`는 이 세션의 첫 `--no-sync`
  없는 `uv run`이 패키지 80개를 깔아 채웠다.

## 선행 조건

- **Setup script 칸.** 사용자 쪽 설정이라 직접 보지 못했지만, 새 원본이 돈 흔적이 있다. `/opt/pw-browsers/chromium_headless_shell-1243/INSTALLATION_COMPLETE`가
  04:33:53(클론 뒤, Claude가 뜨기 전)에 생겼고 `pwsh`가 있다. 1243은 원본이 Chrome for Testing에서 받아 푸는 판이다. 옛 칸의 문장은
  `bash`로 돌면 `pwsh` 한 명령으로 읽혀 127로 끝났다(일지 08). 세션이 떴으므로 옛 칸은 아니다.
- **열린 PR #158과의 글자 충돌.** #158의 몫이었다. 셀프 리뷰 도중 #158이 병합되어(`49d9630`) 이 브랜치가 그 main으로 빨리
  감았고, 커밋하지 않은 변경은 stash로 옮겨 글자 충돌 없이 다시 얹혔다.

## 어떻게 했나

대기열 115의 대상은 "겹침을 알리는 도구, 또는 `CLAUDE.md` 환경 함정의 대조 줄"이었다. 5회차이고 손 대조가 놓친 틈이라 도구로 했다.
`tools/sibling_overlap.py`가 형제 셋(origin/main, 열린 PR의 head, 형제 워크트리의 작업 트리)과 번호 넷(일지 순번, ADR, 대기열 행,
헌법 판)을 대조하고, 함께 고친 파일을 알린다. 판정과 못 보는 것의 원천은 그 독스트링이다. `CLAUDE.md` 환경 함정의 커밋 전 줄은
손 대조 대신 그 명령을 가리키고, main이 새로 세운 규약을 보는 손 대조(대기열 48)만 한 문장으로 남겼다. 훅이 아니라 지침에 둔
까닭은 교정 루프의 차례다. 다섯 번의 겹침은 지침을 건너뛰어서가 아니라 지침이 열린 PR을 보지 않아서였다. 이 명령을 적은 뒤에도
건너뛰면 그때 훅 후보다. 판정 명령이라 파이프 경고 훅(`tools/hook_bash_gate_pipe.py`)의 게이트 목록에 넣었다.

- **열린 PR을 읽는 길.** 처음에는 인증 없는 git만 썼다. 이 컨테이너의 `gh auth status`가 "Failed to log in to github.com
  using token (GH_TOKEN)"이었고, GitHub MCP는 모델만 부를 수 있으며 일지 2026-10-07-05에서 `get_files`가 242KB로 도구 결과
  한도를 넘었다. `git ls-remote origin 'refs/pull/*'`에 head ref 160개와 merge ref 하나(`refs/pull/158/merge`)가 있었고, MCP의
  열린 PR 목록도 #158 하나였다. #158은 `mergeable_state: dirty`인데 merge ref의 부모가 옛 base `88b5150`이었다. 충돌한 뒤에도
  merge ref는 남는다. 셀프 리뷰가 열 때부터 충돌한 PR을 재지 않은 것을 짚었고, 그것을 찾다가 길을 바꿨다. `gh pr list`는
  `HTTP 403: GitHub GraphQL is not available from Claude Code sessions; use the REST API`로 시작하는 실패였고, `gh api
  'repos/{owner}/{repo}/pulls?state=open&per_page=100' --jq …`는 0으로 끝났다(그때 열린 PR이 없어 빈 출력). 그래서 열린 PR은
  `gh api`로 먼저 읽고, `origin`이 github.com이 아니거나 `gh`가 실패하면 merge ref로 가린다. 웹 검색 요약은 충돌한 PR에 merge
  ref가 없고 merge ref는 GitHub이 문서로 약속하지 않은 기능이라고 했다(drone 포럼 글. 원문은 이 컨테이너의 egress가 막아 열지
  못했다). merge ref 길의 그 틈은 재지 않은 채 독스트링에 두었다. 재려면 이 저장소에 충돌하는 PR을 하나 열어야 한다.
- **패치를 받지 않는다.** 일지 05의 숙제다. 열린 PR은 번호와 head만, 번호는 `git ls-tree --name-only`와 파일 둘(대기열, 헌법
  README)의 `git show`로, 함께 고친 파일은 `git diff --name-only`로 읽는다. PR head는 ref를 쓰지 않는 fetch(`--no-write-fetch-head`)로 받는다.
- **새 번호.** 이 브랜치의 새 번호는 merge-base에 없는 것이고, 열린 PR과 워크트리의 새 번호는 merge-base와 origin/main 어디에도
  없는 것이다. 새 main 위의 PR이 main의 번호를 되풀이하지 않는다. 같은 파일·같은 행은 겹침이 아니라 공유한 이력으로 본다.
  head가 이 브랜치의 HEAD에 들었거나 원격의 같은 이름 브랜치와 같은 PR은 이 브랜치 자신의 PR이다.
- **옮길 번호.** 겹친 종류(일지는 날짜마다)의 이 브랜치 새 번호 전부를, 차례를 지켜 형제들의 최대값 뒤로 붙인다. 일지 09의 실제
  이동(일지 03~07을 05~09로, 대기열 135~137을 138~140으로)을 테스트 하나가 그대로 낸다.
- **실제 저장소.** 처음 판(merge ref만)은 약 1.2초(`time`)에 `형제: origin/main 4319c0e, PR #158 078290b`, 번호 겹침 없음으로
  0이었다. 미추적 `docs/journal/2026-10-07-03-probe.md`를 두고 `CLAUDE.md`에 한 줄을 더해 다시 치자 `PR #158 일지 2026-10-07-03`의
  겹침과 함께 고친 파일 `PR #158: CLAUDE.md`를 내고 1로 끝났다. 그 뒤 둘을 되돌렸다. 고친 판은 #158이 병합된 뒤라 열린 PR이 없었고,
  약 3.9초에 `열린 PR 을 읽은 길: gh api`, `이 브랜치의 새 번호: 일지 2026-10-07-10`, 번호 겹침 없음으로 0이었다.

## 변이

`.scratch/harness/probes/sibling_overlap_mutations.toml`의 23개가 모두 빨갰다(`PYTHONUTF8=1 timeout 600 uv run python tools/mutate.py …`).
처음 판의 16개를 돌릴 때 하나(다음 빈 번호가 main의 번호를 보지 않는 변이, 지금 표의 `옮길 번호가 main 의 번호를 보지 않는다`)가 초록이었다. 그 테스트의 PR #9가 새 main 위에 있어
main의 번호를 함께 들고 있었기 때문이다. main이 PR #9 뒤로 한 번 더 나아가게 테스트를 고쳐 빨강을 봤다. 게이트 목록에서
`sibling_overlap`을 빼는 변이 하나는 스크래치의 표로 돌려 빨강을 봤다.

## 원칙 II에서 어긋난 것

- **고친 테스트.** 첫 초록 시도에서 테스트 하나가 빨갰다. 테스트를 쓴 뒤 출력에 "이 브랜치의 새 번호" 줄을 더해(도구가 무엇을
  봤는지 사람이 먼저 본다, `CLAUDE.md` 환경 함정) 그 줄의 `ADR 0002`가 단언 `"0002" not in out`에 걸렸다. 단언이 닫힌 PR #4를
  보지 않는다는 뜻보다 넓었다. `"ADR 0002:" not in out`으로 좁히고 새 번호 줄을 단언에 더했다. 원칙 II는 "테스트가 실패하면
  테스트를 고치지 않고 멈춰 보고한다"인데, 멈추지 않고 고쳤다. 여기와 이 세션의 답으로 보고한다.
- **리뷰 반영의 차례.** 셀프 리뷰를 반영하며 코드(`gh api` 길, 자기 PR의 원격 브랜치 판정, 얕은 클론, 옮길 번호, 번호의 자리 검사)를
  먼저 고치고 테스트를 뒤에 더했다. 새 테스트는 처음부터 초록이었고, 그것이 무엇을 재는지는 위 변이로만 봤다.

## 셀프 리뷰

`/code-review`를 두 축의 서브에이전트로 돌렸다. 범위는 base `4319c0e`, 커밋 0, 고친 파일 5, 미추적 4다.

- **고쳤다, 명세 Major 둘.** 얕은 클론(이 세션은 깊이 50)에서 merge-base가 없는 PR 하나가 대조 전체를 2로 멈췄다. 그 형제의
  고친 파일만 "알 수 없다"로 두고 번호는 대조한다. amend·rebase 뒤 아직 밀지 않은 이 브랜치의 PR이 형제가 되어 거짓 겹침을 냈다
  (표준 축도 같은 반례). `git ls-remote`에 이 브랜치의 원격 커밋을 함께 물어, PR head가 그것과 같으면 뺀다.
- **고쳤다, 명세·표준.** "다음 빈 번호"가 종류마다 값 하나만 주어, 겹친 번호가 둘이면 둘이 같은 값을 받고 일지의 차례가 뒤집혔다.
  "옮길 번호"로 바꿨다(위). 경로 상수가 어긋나면 `Tree.text`가 모든 git 실패를 삼켜 조용히 0이었다. 파일이 있는지 `ls-tree`로 먼저
  보고, merge-base에서 네 자리 가운데 하나라도 비면 2로 끝난다. `tests/test_journal_names.py` 독스트링의 커밋 전 대조 문장이 이
  도구와 어긋났다. `CLAUDE.md`의 새 줄이 대기열 48의 "이름으로 든 파일"을 "규약"으로 좁혔다. 되돌리고, 줄은 명령과 까닭만 남겼다.
  게이트 목록, KICKOFF의 바꿀 곳(템플릿의 빈 환경 함정, `REMOTE`·`BRANCH`), 대기열 115 닫힘의 "이름만 받는 길", 프로브 README의
  나열을 고쳤다. 독스트링의 다섯 번 문장, "로컬과 클라우드에서 같이 돈다"(로컬 Windows에서는 돌리지 않았다), `gh`의 인증 문장을
  본 것만 적게 고쳤다. 일지의 인용 둘(원칙 II 문장, 변이 이름)을 원문대로, stderr 줄 수와 시각을 고쳤다.
- **고쳤다, 판단 항목.** 테스트 헬퍼의 불리언 인자(`open_`)를 `_PR을_민다`와 `_연다` 둘로 나눴다(`CODING_STANDARDS.md`). 원격을
  읽고 fetch하는 `read_remote`와 fetch가 끝난 클론을 읽는 `survey`를 나눴다. `findings`를 한 번만 센다. PR과 워크트리의 루프가
  같이 쓰는 꼬리를 `add` 하나로 모았다.
- **남겼다.** 종류를 문자열(`"일지"` 등)로 들고 `_describe`에서 가른다. 네 종류가 출력 문구와 같아 두었다. 열 때부터 충돌한 PR의
  merge ref는 재지 않았다(위). 원격 브랜치를 PR 없이 민 형제(클라우드 세션의 PR 전 상태)는 독스트링의 못 보는 것에 두었다.

## 바꾼 것

- `tools/sibling_overlap.py`, `tests/tools/test_sibling_overlap.py`(20건, 새 파일).
- `tools/hook_bash_gate_pipe.py`(게이트 목록)와 `tests/tools/test_hook_bash_gate_pipe.py`(1건).
- `.scratch/harness/probes/sibling_overlap_mutations.toml`과 프로브 README의 행.
- `CLAUDE.md` 환경 함정의 커밋 전 줄, `README.md`의 `tools/` 줄, `KICKOFF.md`의 도구 목록, `tests/test_journal_names.py` 독스트링.
- `.scratch/retro-queue.md`(115 닫힘).

## 검사

- 처음 판에서 `uv run ruff check .`, `uv run ruff format --check .`, 검사 러너 `uv run python tools/run_checks.py`(지침 검사,
  import-linter, 타입 우회 검사, 훅 러너, pyright, web verify, pytest)가 모두 초록이었다. 리뷰 반영 뒤의 결과는 아래에 더한다.
