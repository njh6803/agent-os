# 2026-10-13 (63) 훅 페이로드 러너의 조각 대조, Grep 생략 줄 훅, `.env` 훅의 래퍼, 매처 공개 함수

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 130·145·162·216이 모두 `tools/hook_payloads.toml`·
`tools/run_hooks.py` 둘레라 한 PR로 닫는다(일지 2026-10-13-47 "다음"이 묶었다). 세션은 주 체크아웃에서 열렸고,
지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=hook-payloads-batch)`로 들어가 `origin/main`(`97e1d5e`,
#230)에서 `chore/hook-payloads-batch`로 브랜치 이름을 바꿨다. 순번 63은 `tools/sibling_overlap.py`가 형제(열린 PR #231·#233,
병합된 #232의 일지 59)를 보고 낸 다음 빈 번호다.

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
- `.scratch/retro-queue.md`: 130·145·162·216을 닫았다.
