# 2026-10-13 (67) 훅 페이로드 러너의 조각 대조, Grep 생략 줄 훅, `.env` 훅의 래퍼, 매처 공개 함수

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 130·145·162·216이 모두 `tools/hook_payloads.toml`·
`tools/run_hooks.py` 둘레라 한 PR로 닫는다(일지 2026-10-13-47 "다음"이 묶었다). 세션은 주 체크아웃에서 열렸고,
지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=hook-payloads-batch)`로 들어가 `origin/main`(`97e1d5e`,
#230)에서 `chore/hook-payloads-batch`로 브랜치 이름을 바꿨다. 순번은 처음에 `tools/sibling_overlap.py`가 낸 63이었다. 일하는 사이 #233이
일지 64를 들고 먼저 병합되어 이 일지가 이름순에서 밀렸고, 병합 직전의 대조가 낸 대로 67로 옮겼다.

## 계기

> 사용자: "대기열 130·145·162·216을 한 PR로 반영한다(tools/hook_payloads.toml·tools/run_hooks.py 둘레의 훅과 러너). 각 행의 "어디로" 칸이 원천이다"

## 첫 턴의 tidy-checkouts

루트는 main이고 깨끗해 `c170046`에서 `97e1d5e`로 당겼다. 판정에서 `지운다` 줄은 없었다. 사람에게 넘긴 것은 분리 HEAD
셋(`agent-canary-2d593dd`, `elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`), prunable 등록 둘
(`05-admin-hides-decision-for-end-user`, `spec-pipeline-and-pytest-ids` — 옆 이름 `.tidy-probe`에 폴더가 남았다), 병합된
PR의 머리와 브랜치 끝이 다른 `skill-check-and-retro-section`이다. 지시문대로 답을 기다리지 않았다.

## 130 — 러너의 조각 대조

- `Case`에 선택 칸 `contains`를 두고, `run_case`가 훅이 낸 문장(`message_of`)에서 조각을 찾는다. 빠진 조각이 있으면
  판정이 같아도 어긋남이다. 문장은 JSON을 푼 `additionalContext`(두 자리)·`permissionDecisionReason`·`reason`·
  `systemMessage`이고, 종료 2면 stderr다. 날것 stdout에서 찾지 않는 것은 훅이 `json.dumps`의 기본값으로 한글을
  이스케이프해 내기 때문이다(시험이 그 전제를 단언한다).
- 침묵 사례에 `contains`가 있으면 표를 읽을 때 거절한다.
- 표에서는 미갱신 지시문의 첫 세션 사례에 조각 둘을 달고, 둘째 세션 사례를 새로 더해 조각 둘을 달았다. 일지
  2026-10-06-15가 "옛 훅에서도 지난다"고 적은 그 사례다. 새 Grep 훅의 발동 사례에도 조각 셋을 달았다.
- 저장소 상태 시험 하나(조각을 단 사례만 지금 훅으로 돌려 모두 찾는다, 사례가 없으면 실패)를 더해 변이가 겨눌 자리를
  두었다.

## 145 — Grep 생략 줄 훅

- 프로브 `.scratch/harness/probes/grep_omitted/run.py`를 먼저 지었다. A는 덤프 훅만 붙여 Grep의 PostToolUse 입력을
  받았다. `tool_response`의 키는 `mode`·`numFiles`·`filenames`·`content`·`numLines`·`totalLines`이고, 생략된 줄은
  `content`에 `<경로>:<줄 번호>:[Omitted long matching line]` 꼴로 실렸다. content 모드에서 `numFiles`는 0, `filenames`는
  빈 목록이었다.
- 문턱은 이 세션이 Grep 도구로 길이가 다른 줄을 훑어 손으로 찾았고(500자까지 그대로, 501자부터 표지), 손으로 본
  한글 500자 줄(1482바이트)도 그대로여서 바이트가 아니라 글자 수다. 프로브 A가 영문·한글(1488바이트) 500자와 501자
  줄로 같은 것을 다시 낸다. 한글은 UTF-16 단위로도 500이라 글자와 UTF-16 단위는 가르지 않았다.
- 문맥 줄(`-C`)은 다른 표지 `[Omitted long context line]`이고 `-n`이 없으면 `<경로>:[Omitted …]` 꼴이다(손으로 봤다).
  문맥 줄의 생략은 일치를 숨기지 않아 세지 않는다.
- 훅 `tools/hook_grep_omitted.py`는 생략된 일치 줄의 수와 자리를 들고(열 개까지, 나머지는 수로), 파일 하나를 훑어 줄
  번호만 있으면 입력의 경로를 붙이며, 어느 자리에도 줄 번호가 없으면 `-n`을 켜라고 덧붙인다. 막지 않고 알린다.
- B(실제 훅과 덤프 훅)에서 모델이 훅의 첫 문장을 옮겼고, 대조군 C(표지 없는 일치)에서는 "알림 없음"이었다.

## 162 — `.env` 훅의 읽기 명령과 래퍼

- `READERS`에 `column`·`rev`를 더했다.
- 행의 "래퍼 모양도 본다"를 따라 스크래치 스크립트로 지금 판정을 찍어 보니, `column`·`rev` 말고도 `nice -n5`·`nice -5`·
  `nice --adjustment=5`·`command -p`·`env -i`·`env -u`·`sudo -u`·`exec -a`·`time -p` 뒤의 `cat .env`가 지나갔다. 래퍼
  뒤의 옵션을 명령 이름으로 읽었기 때문이다. 래퍼 아홉을 표(값을 먹는 옵션)로 두고, 옵션과 그 값을 벗기게 고쳤다.
  `timeout`은 그 뒤의 시간 하나를 더 먹는다.
- 못 보는 것에 목록 밖의 래퍼(`stdbuf`)와 명령을 문자열 하나로 받는 `env -S`를 더하고 시험으로 고정했다.

## 216 — 매처 공개 함수

- `tools/run_hooks.py`에 `registered_matchers(hook, event)`를 두었다. 그 이벤트에서 훅이 든 묶음마다 매처(없으면 빈
  문자열)를 돌려준다. 세 시험의 `TypedDict` 사본을 걷었고 새 Grep 훅의 매처 시험도 이것을 쓴다. 이벤트를 받는 것은
  셀프 리뷰가 짚어서다(아래).

## 셀프 리뷰

`/code-review`(기준 `97e1d5e`, 수정 14·미추적 8, 커밋 0). 명세는 지시문과 네 행의 "어디로" 칸이고, 이 세션이 더한
것(프로브, 둘째 세션 사례, 래퍼 일반화, 문서)은 리뷰어 참고로 갈랐다. 표준 축은 Minor 5·Nit 여럿, 명세 축은 Minor 5·Nit
5였고 Critical·Major는 없었다.

- **고친 것.**
  - 두 축이 함께: 카나리아 명세가 옛 일지 번호 60을 가리켰다(60은 PR #233의 일지다). 63으로.
  - 두 축이 함께: 한글 500자 줄을 1482바이트라 적었는데, 프로브의 줄(`"PROBE "`+한글 494자)은 1488바이트다. 1482는 이
    세션이 손으로 본 줄(`"KMARK500 "`+491자)의 수였다. 프로브를 가리키는 세 곳(훅 독스트링, `run.py`, README)을 1488로
    고치고 일지의 손으로 본 줄은 그대로 두었다.
  - 두 축이 함께: 시간 문단의 "아래 기록"은 위에 있는 WebFetch 기록이라 "앞의 WebFetch 기록(202~342ms)"으로.
  - 명세 Minor: 래퍼 옵션을 벗기자 `command -v cat .env`가 새로 막혔다(옛 판은 지났다). `command -v`·`-V`는 명령을 찾기만
    해 막지 않게 고치고 시험으로 고정했다. 표의 침묵 사례도 그 모양(`command -v column .env`)으로 바꿔 note가 참이 됐다.
  - 표준 Minor·명세 Nit: `sudo --user root`·`sudo -iu root`가 지나갔다. 옵션 낱말을 getopt처럼 읽게 했다(`_option_width`
    — 묶음에서 값을 먹는 글자가 나오면 뒤의 글자가 값이고 비었으면 다음 낱말이 값이다). sudo의 긴 옵션을 표에 더했다.
  - 표준 Minor: 훅 독스트링의 못 보는 것 가운데 "표지 문구나 키가 바뀐 판"과 count 모드에 시험이 없었다. 더했다.
  - 명세 Minor: 파일 하나를 `-n` 없이 훑어 줄이 표지 그대로인 꼴에 시험이 없어 그 분기를 지우는 변이가 살아남았다. 시험과
    변이를 더했다.
  - 명세 Minor: 행이 든 침묵 사례(둘째 턴)는 조각을 달 수 없어 지금도 판정만으로 지난다. 러너 독스트링의 못 보는 것과
    대기열 닫힘 칸에 적었다.
  - 명세 Nit: `registered_matchers`가 이벤트를 가리지 않아, 옛 사본들이 대 보던 이벤트(PreToolUse·PostToolUse)를 더는
    보지 않았다. 이벤트를 받게 했다.
  - 표준 Nit: 근거의 종류. `hook_env_read` 독스트링과 대기열 162 닫힘 칸에, 래퍼 뒤 옵션이 지나간 것은 스크래치
    스크립트로 찍어 본 것이라고 적었다. pitfalls의 "잔존 0으로 셌고"는 원천(일지 2026-10-07-14)에 없어 "놓쳤고"로.
  - 표준 Nit: 문턱이 글자인지 UTF-16 단위인지는 한글로 가를 수 없다고 독스트링과 일지에 적었다. 훅 판정과는 무관하다.
  - 표준 Nit: 프로브 A가 모델이 지시한 패턴·경로로 불렀는지 보지 않았다. 측정의 표지에 더했다(`--judge`로 다시 판정해
    셋 다 측정이었다).
  - 명세 Nit: 일지가 일지 2026-10-06-15의 말이라며 따옴표로 든 "옛 훅에서도 지났다"는 대기열 행의 말이었다. 원문
    "옛 훅에서도 지난다"로.
  - 명세 Nit: 표 머리의 "옛 훅도 같은 종류를 내는 사례에 단다"가 새 Grep 훅 사례와 어긋났다. "사례가 재려는 동작이 판정의
    종류만으로 갈리지 않을 때 단다"로.
  - 표준 Nit(냄새): 러너 출력의 `found`를 `fragments`로, `run_notices`의 dict를 거친 목록을 반복문으로, 두 함수의
    settings 읽기를 `_read_settings`로 모았다. `_strip_prefix`는 표 밖 분기를 줄여 다시 썼다.
- **남긴 것.**
  - 명세 Nit: `message_of`가 계기 문장보다 넓게 deny 이유·종료 2의 stderr·`systemMessage`까지 본다. deny·block 사례에
    조각을 달면 그 문장이 거기 있어서 좁히면 그 사례의 조각이 늘 빠진다. 지금 표에는 그런 사례가 없다.
  - 명세 Nit: 표 머리 자리표시자 목록에 `${BEHIND_REPO}`·`${COMMIT_MSGS}`를 더한 것은 이 요청 밖이지만, 이 PR이 고치는
    머리 주석의 사실 오류라 두었다.
  - 표준 Nit(냄새): 프로브가 `MARKER`를 훅에서 가져오지 않는 것은 Claude Code의 표지를 재는 자리라서다(그 까닭을 주석으로
    적었다). `_launch`가 알림 길에서도 `message_of`를 계산하는 것은 값이 작아 두었다.
  - 표준 "확인 불가": 시간의 수와 A의 `numFiles`·`numLines`는 원본이 저장소 밖(세션 스크래치)에 있다. `time_hook.sh`와
    `run.py`가 다시 낸다.
- **리뷰 뒤에 들어온 규약.** 셀프 리뷰를 돈 사이 #231이 병합되어 `code-review`에 "갈래 밟기"(훅이 넣는 문구처럼 에이전트가
  따르는 절차를 바꾸면 중간으로 들어오는 갈래를 밟는다)와 "보고를 받은 턴에 일지로 옮긴다"가 들어왔다. 이 리뷰는 옛 사본으로
  돌아 두 브리프에 그 문단이 없었다. 새 훅의 알림이 시키는 길(Read 도구에 줄 번호를 offset으로 준다)을 손으로 밟아,
  대기열 파일의 5159자 줄을 Read가 자르지 않고 보여 주는 것을 봤다. 나머지 갈래는 PR 직전 리뷰의 브리프에 그 문단을 싣는다.

## PR 직전 리뷰

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 대체 둘을 첫 커밋(`a3b50ac`)과 origin/main 병합 뒤에
나란히 돌렸다. 범위는 `97e1d5e..a3b50ac`다.

- **보안(`/security-review`).** 식별 서브태스크의 발견이 0건이라 오탐 거르기는 띄우지 않았다. 막는 훅 `hook_env_read`의
  옛 판과 새 판에 같은 명령 약 71만 개를 넣어 대 봤고(스크래치 스크립트), 옛 판이 막고 새 판이 지나보낸 50개는 모두
  `timeout -vk <값> <읽기> .env` 꼴이었다. GNU timeout은 그 꼴에서 읽기 명령을 시간으로 읽어 끝나므로 옛 판의 오탐이
  풀린 것이라고 봤다. 범위 밖의 옛 틈 둘(긴 옵션 줄임 `sudo --us`, env의 `-a`)을 참고로 냈다.
- **버그·성능(`bug-perf-review`).** Critical·Major 없음, 유효 Minor 2·Nit 2, 보류 1(변이 표와 `claude -p` 프로브는 돌리지
  못했다). 브리프에 #231의 갈래 밟기 문단을 실었고, 서브에이전트·병렬 Grep·`head_limit`·같은 줄을 다시 Grep하는 갈래는
  어긋나지 않는다고 봤다. 옛 판이 막고 새 판이 지나보낸 것은 래퍼 아홉×옵션×읽기 명령 조합에서 0건이었다.
  - 고친 것(Minor): Grep 훅의 안내가 offset만 말해 글자 그대로 따르면 Read가 그 자리부터 기본 2000줄을 싣는다. "offset에
    그 줄 번호, limit에 1"로.
  - 고친 것(Minor): 래퍼를 낱말 그대로 찾아 `/usr/bin/env cat .env`·`/usr/bin/time -v cat .env`가 지나갔다(옛 판도
    같았다). 경로를 벗긴 이름으로 찾게 했다. env의 `-a`·`--argv0`(보안 리뷰의 참고와 같다)도 값 옵션에 더했다.
  - 고친 것(Nit): `tool_input`이 null이면 Grep 훅이 터졌다. 객체인지 본다.
  - 고친 것(Nit): 자리가 열 개를 넘으면 "외 N개"만 적었다. 나머지가 위 결과의 같은 표지 줄이라고 덧붙였다.
  - 적은 것: 긴 옵션 줄임(`sudo --us root cat .env`)은 고치지 않고 `hook_env_read`의 못 보는 것에 적고 시험으로 고정했다.
    표의 이름 그대로만 값 옵션으로 보는 판단을 그대로 두는 값이 작아서다.
  - 고친 넷과 적은 하나마다 시험을 더하고 변이 넷을 두 표에 더했다. 두 표는 열둘씩 모두 기대대로였고 러너는 그대로 94건
    어긋남 0이었다.

## PR 봇

PR #235(커밋 둘과 origin/main 병합 둘, 헤드 `4eb1d42`). 마지막 푸시 뒤 `@coderabbitai review`를 남기고 `tools/wait_ci.py`로
기다렸다. 검사 여섯(`python`, `web`, `verify`, `e2e`, `visual`, `claude-review`)이 모두 초록이었다.

- **claude-review.** 지적 없음. 경계(`src/`·`sdk/` 계약을 건드리지 않았다)와 유지보수성(새 훅의 질의와 문장 조립이 갈렸고,
  `registered_matchers`가 사본 셋을 대신한다)을 적었다.
- **CodeRabbit.** "Review rate limited"로 초록이고 리뷰는 없다. 보안·버그 축은 PR 체크리스트에 적은 PR 직전 리뷰 둘의
  결과가 대신한다(`operations.md` 리뷰 파이프라인의 초록 착시 목록).

두 번째 회차(origin/main의 #236을 합쳐 헤드 `bed38fe`로 푸시한 뒤 `@coderabbitai review`). 검사 일곱이 모두 초록이었고
CodeRabbit이 리뷰를 냈다.

- **CodeRabbit, Minor 하나(반영).** 프로브 `grep_omitted/run.py`의 B·C 판정이 A와 달리 기록된 `tool_input`(패턴·경로·모드)을
  보지 않아, 지시와 다른 Grep 호출의 결과로도 표지와 답의 조건이 맞으면 측정으로 셌다. `.claude/rules/probes.md` 첫 항목
  (재려는 상황이 실제로 났다는 표지까지 단언한다)이 요구하는 것이라 옳은 지적이었다. A의 검증을 `call_problem`으로 빼
  세 변형이 함께 쓰게 했다. 가짜 기록 여섯(B·C 각각 맞는 호출, 다른 패턴, 다른 경로)으로 판정이 기대대로 갈리는 것을 확인했다.
- **claude-review, Minor 하나와 Nit 둘.** Nit 둘은 반영했다. `ToolInput`이 훅이 읽지 않는 키를 든 것은 독스트링에 시험이
  실제 입력을 흉내 내려는 것이라고 적었고, 경로가 `:숫자`로 끝나는 파일을 `-n` 없이 훑으면 줄 번호로 읽는 거짓 음성은 "못 보는 것"에
  적고 시험 하나로 고정했다. Minor(`hook_env_read.py`의 `sudo` 옵션 집합이 `# fmt: skip`의 세로 나열)는 반영하지 않았다.
  같은 파일의 `READERS`·`_RG_VALUE_OPTIONS`도 같은 모양이라 파일 안에서는 일관되고, 상수를 둘로 쪼개는 일은 판정 로직을 건드릴
  위험에 비해 얻는 것이 없다.

## 검사

- 셀프 리뷰 전에 손으로 친 것: `uv run pytest -q`는 2700 통과, 7 deselect(`llm` 마커)였다(674초). ruff check·format,
  pyright(0 errors), lint-imports(계약 다섯 유지), 지침 검사, 타입 우회 검사가 모두 통과했다. 셀프 리뷰를 반영한 뒤에는 바뀐
  시험 여섯 파일을 다시 돌렸고, 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.
- `tools/run_hooks.py`: 반영 전후 모두 훅 페이로드 94건 어긋남 0, 래퍼 알림 5건 어긋남 0, 빈자리 0이었다.
- 변이: `run_hooks_contains_mutations.toml`은 반영 전후 모두 일곱이 기대대로였다. `grep_omitted_hook_mutations.toml`과
  `env_read_wrappers_mutations.toml`의 결과는 README 행에 판마다 적었다(첫 판 아홉·일곱, 반영 뒤 열·열. grep 표는 반영 뒤
  첫 실행의 대조군이 빨강이라 고쳐 다시 돌렸다).
- 카나리아 `tools_rule_grep_hook.toml`: 통과 4(실험군 셋이 제목·훅 이름·시간을 옮겼고 대조군은 "없음"). 그 뒤 시간 문단의
  "아래 기록"만 고쳐 사전 확인(통과 1)으로 갈음했다.
- 프로브 `grep_omitted/run.py`: A·B·C가 측정이었고 문제 0건. 반영 뒤 A의 표지(지시한 패턴·경로)를 더해 `--judge`로 다시
  판정했고 그대로 측정이었다.

## 바꾼 것

- `tools/run_hooks.py`: `Case.contains`, `message_of`·`missing_fragments`, `Result.missing`, 침묵 사례의 조각 거절,
  `registered_matchers`, 독스트링(조각 문단, 못 보는 것 둘).
- `tools/hook_payloads.toml`: 머리 주석(자리표시자 목록, 조각 칸), 지시문 사례 둘의 조각, 지시문 둘째 세션 사례, `.env` 훅
  사례 둘, Grep 훅 사례 둘.
- `tools/hook_grep_omitted.py`(새 파일), `.claude/settings.json`의 PostToolUse `Grep` 등록.
- `tools/hook_env_read.py`: `READERS`의 `column`·`rev`, 래퍼 표 `_WRAPPERS`와 `_option_width`, `_strip_prefix`, 독스트링.
- 시험: `tests/tools/test_hook_grep_omitted.py`(새 파일), `test_run_hooks.py`, `test_hook_env_read.py`, 매처 사본을 걷은 셋
  (`test_hook_pr_next_session.py`, `test_hook_bash_msys_pathconv.py`, `test_hook_webfetch_summary.py`).
- 문서: `.claude/rules/tools.md` 시간 문단, `KICKOFF.md`(매처 목록, 훅 목록, 계기 훅 목록, `hook_env_read` 설명),
  `kickoff/pitfalls.md` 새 행.
- 프로브: `.scratch/harness/probes/grep_omitted/`(새 디렉터리), 변이 표 셋, 카나리아 명세 하나, README 행 넷.
- `.scratch/retro-queue.md`: 130·145·162·216을 닫았다. 회고의 새 행(처음 256)을 더하고 239에 회차를 붙였다. 형제의 254(일지 66)가 먼저 병합되어, 병합 때 256을 254에 합쳐 2회차로 적고 256을 지웠다.

## 회고

후보 여덟, 승인 하나(새 행), 기존 행에 회차 하나, 기각 여섯. 넘긴 것은 없어 사용자에게 묻지 않았다.

1. **승인, 대기열 256(병합 때 254에 합쳐 2회차).** 처음에는 254로 적었는데, 형제 워크트리(feature/04-human-verification-of-runner, 아직 병합되지
   않았다)가 같은 254에 같은 후보(짐작한 일지 번호를 `kickoff/runner.md`에 적은 사건, 일지 2026-10-13-66)를 먼저 적어 두었다.
   병합 직전 대조가 겹침을 알려 256으로 옮기고, 두 행이 서로를 가리키게 해 나중에 병합하는 쪽이 한 행으로 합쳐 2회차로 적게
   했다. 사건: 일지 번호를 `tools/sibling_overlap.py`로 받기 전에 짐작한 번호(60)를 카나리아 명세에
   인용했고, 그 번호는 없는 일지(뒤에 #233이 64로 썼다)를 가리킨 채 셀프 리뷰까지 갔다. 두 축이 잡았다. 층: 자동 검사(이
   브랜치가 더한 줄의 일지 인용이 디스크의 파일이나 형제의 번호를 가리키는지 경고). `sibling_overlap.py` 독스트링은 번호를
   가리키는 참조를 못 보는 것으로 적는다. 되돌림: PR 하나. 번호를 옮길 때의 인용을 다루는 249와 원인이 달라 새 행으로 두고
   서로 가리키게 적었다.
2. **기존 행 239에 회차(2회차).** 사건: `hook_env_read`가 래퍼를 "getopt처럼" 벗긴다고 적었는데, 하류(실제 래퍼)가 입력을
   다르게 읽는 길(`sudo --user`·`-iu`, `/usr/bin/env`, `env -a`, 긴 옵션 줄임)을 셀프 리뷰와 PR 직전 리뷰가 차례로 찾았다.
   239(하류 판정과 같은 입력에서만 막는다고 주장하는 훅은 하류가 입력을 바꾸는 길을 먼저 나열한다)와 같은 모양이고, 이번은
   거짓 양성이 아니라 거짓 음성 쪽이었다.
3. **기각.** 한글 줄의 바이트 수를 손으로 본 줄의 수(1482)로 적었다. 프로브의 줄은 1488바이트였다. 셀프 리뷰 두 축의 주장
   검증이 잡았다.
4. **기각.** 도구 호출 앞의 중간 문장을 영어로 쓴 것이 여섯 번이었다. `hook_midturn_korean`이 매번 바로 짚었고 다음 문장은
   한국어였다. 이미 있는 계기 훅이 잡는다.
5. **기각.** 변수와 git을 한 줄에 묶은 명령을 워크트리 가드가 거부했다. `CLAUDE.md` 환경 함정에 적힌 모양이고 가드가 막았다.
6. **기각.** 셀프 리뷰가 옛 `code-review` 사본으로 돌아 갈래 밟기 문단이 없었다. 규약이 리뷰 뒤에 병합됐고, 손으로 한 갈래를
   밟고 PR 직전 리뷰의 브리프에 그 문단을 실었다.
7. **기각.** Grep 변이 표의 대조군이 시험을 더한 뒤 빨개졌다. `tools/mutate.py` 독스트링이 적은 동작이고 전체 실행이 잡았다.
8. **기각.** 새 훅의 Read 안내에 `limit`이 없었다. 갈래 밟기 문단을 실은 PR 직전 리뷰가 잡았다(새 규약이 그대로 돌았다).

일지에만 남기는 것: Edit 도구가 한 번 원자적 쓰기에 실패(EPERM)했다. 도구가 오류를 냈고 그 편집만 빠져 다시 적용했다.

## 다음

- **이 PR 뒤의 다음 작업은 대기열 128·141·239다.** 셋 다 "어디로"가 `.claude/rules/tools.md`라 결정표의 chore 배치 조건(대상
  파일이 같은 항목 셋 이상)을 채운다. 141은 클라우드 세션의 `gh` 사실이라 그 세션이 잴 수 있는지부터 본다. 246
  (`hook_bash_commit_msg`의 보안 고침)은 대상 파일이 달라 조건에 들지 않지만 239와 같은 훅 둘레라 그 세션이 함께 볼지 정한다.
  `tools/mutate.py` 묶음(203·231·253)과 `tools/sibling_overlap.py` 묶음(235·249·251)은 다른 세션이 돌고 있어 뺐다. 254(256을 합친
  행)는 `sibling_overlap.py` 묶음을 연 세션이 함께 볼 수 있다.
- **새 훅 `hook_grep_omitted`는 주 체크아웃을 당긴 뒤의 세션에서 처음 돈다.** 잔존 grep에서 생략 표지가 나오면 그 알림을
  따라 Read로 연 자리가 맞는지 처음 볼 수 있다. 어긋나면 그 Grep 호출과 알림을 일지에 남긴다.
