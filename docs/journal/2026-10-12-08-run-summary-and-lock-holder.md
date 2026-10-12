# 2026-10-12 (08) 실행 로그 요약이 거부와 훅 오류를 보이고, 정리 도구가 폴더를 쥔 프로세스를 댄다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 176·177·178을 닫는다. 세션은 주 체크아웃에서 열렸고,
지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=run-summary-and-lock-holder)`로 들어가
`origin/main`(`c60f1b0`)에서 `chore/run-summary-and-lock-holder`를 땄다. 순번은 08이다. 처음에는 06으로 썼으나
그사이 PR #178이 병합되어 `tools/sibling_overlap.py`가 main의 `2026-10-12-06-canary-agent-arm`과 겹친다고 알려 그
도구가 고른 08로 옮겼다.

## 계기

> 사용자: "대기열 176·177·178을 한 chore PR로 반영한다. 177은 3회차이고, 178은 operations.md 한 줄이라 헌법 버전의 patch가 함께 간다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `67dbb4a`에서 `c60f1b0`으로 당겼다. 스킬 파일은 바뀌지 않았다.
- **지운 것.** 없다. `지운다` 판정이 하나도 나오지 않았다.
- **남긴 것.** 잠금 pid가 살아 있는 `admin-style-design`·`pr-template-review-guard`, 병합된 PR이 없는 넷,
  다시 만들 수 없는 `grep.exe.stackdump`가 든 `canary-spec-pipeline-followup`.
- **사람에게 넘긴 것.** 분리 HEAD 넷, prunable 하나, PR 머리가 다른 `skill-check-and-retro-section`, 등록 없는 폴더
  여섯, 그리고 실행 중인 세션 `docs/admin-style-spec`의 제목이 체크아웃된 어느 브랜치와도 맞지 않아 보류된 셋
  (`review-workflow-guards`, `rewrap-and-separator-hook`, `spec-pipeline-and-pytest-ids`). 지시문대로 답을 기다리지
  않았다.

## 177: 쥔 프로세스를 무엇이 대는가

대기열 행은 Restart Manager로 대라고 적었다. 들이기 전에 쟀고(`.scratch/harness/probes/lock_holder.py`), 결과가
방법을 바꿨다.

- Restart Manager는 폴더 경로를 받지 않는다(모든 갈래에서 오류 5). 파일 경로만 받으며, 파일을 연 프로세스(C)와
  하드링크로 같은 파일·DLL을 쥔 프로세스(D·E·G)는 댔지만 작업 디렉터리로 쥔 프로세스(B·H)는 대지 못했다.
- 실제로 남은 `review-workflow-guards`의 파일 43241개를 5000개 덩이로 등록하니 209초였고(커밋하기 전의 판으로는
  184초), 덩이 일부가 오류 29였으며, 이름 바꾸기를 막는 프로세스 대신 Python과 OpenJDK 프로세스를 댔다.
- 워크트리 넷을 DELETE 권한으로 열어 보니 셋이 공유 위반(32)이었다. 일지 04의 `WinError 32`와 같은 모양이고, 합성
  갈래에서는 폴더 자신을 작업 디렉터리로 쥔 H만 이 모양을 냈다(양성 대조). 아무도 쥐지 않은 A는 열렸다(음성 대조).
- 프로세스마다 PEB의 작업 디렉터리를 읽으니(프로브로 672개 중 493개를 0.12초에) 그 셋(`review-workflow-guards`,
  `rewrap-and-separator-hook`, `canary-spec-pipeline-followup`)을 모두 `claude.exe`가 그 루트를 작업 디렉터리로 쥐고
  있었고, 열린 하나는 쥔 것이 없었다. 여기부터는 프로브 밖에서 손으로 봤다(`Get-CimInstance Win32_Process`,
  `list_sessions`). 셋의 CLI 판은 2.1.286이고 부모는 데스크톱 앱(`Claude.exe` 2.19675.0.0)이었으며, 앱이 띄운 CLI
  프로세스는 24개였다. 셋 다 06:34에 `--resume`으로 다시 띄워졌고, 그 세션들은 `list_sessions`에서 `isRunning`이
  아니었다.

그래서 `tools/tidy_checkouts.py`는 점유 탐침이 막혔을 때만 작업 디렉터리를 훑어(윈도 PEB, 리눅스 `/proc`) 그 폴더나
그 아래를 쥔 프로세스의 이름과 pid를 남긴 이유에 붙인다. 지울지는 가르지 않는다. 행의 방법을 바꾼 것은 닫힘 메모에
적었다.

## 바꾼 것

- `tools/gh_run_summary.py`(176): 로그의 들여 쓴 JSON 객체를 통째로 읽는다. 결과 블록에서 `num_turns`·
  `total_cost_usd`·`is_error`·`terminal_reason`과 `permission_denials`의 수와 도구 이름을, 훅 응답 중 오류인 것을,
  알림(`stop-hook-error`)을 따로 찍는다. 신호는 JSON 밖 줄의 `##[warning]`·`##[error]`에서만 잡고, 러너가 다시
  보여 주는 스크립트 원문(`[36;1m` 머리)은 거른다. 거부 항목의 모양은 로컬 `claude -p`(2.1.296)로 Write를
  거부시켜 손으로 봤다(`tool_name`, `tool_use_id`, `tool_input`).
- `tools/tidy_checkouts.py`(177): `Holder`, `cwd_holders`, `is_within`, `describe_holders`와 `Ops.holders`.
  독스트링의 판정 4와 "못 보는 것"에 근거와 한계를 적었다.
- `docs/constitution/operations.md`(178): 리뷰 파이프라인의 초록 착시 목록에 CI 리뷰의 훅이 127로 지나간다는 한 줄,
  그리고 `gh_run_summary.py`가 보여 주는 것에 거부 수와 훅·알림. 헌법 3.0.23.
- `.scratch/retro-queue.md`: 176·177·178을 닫았다. 178의 남은 판단(훅을 끌지, uv를 깔지)은 열린 행 163에 붙였다.
- 프로브 `lock_holder.py`, 변이 표 `gh_run_summary_mutations.toml`(새로), `tidy_checkouts_mutations.toml`(일곱 더하고
  `_probe` 호출이 바뀐 하나의 원문을 고쳤다), 프로브 README의 줄.

## 세 실행으로 본 새 요약

| 실행 | 결과 | 거부 | 훅·알림 | 신호 |
|---|---|---|---|---|
| PR #176 `38181949361` | 9턴, 완료 | 0건 | SessionStart 127, `stop-hook-error` | 워크플로 원문 없음 |
| PR #174 `38180949060` | 13턴, 완료 | 0건 | SessionStart 127, `stop-hook-error` | 워크플로 원문 없음 |
| PR #172 `38120400317` | 1턴, `is_error`, `api_error` | 0건 | SessionStart 127 | `##[error]` 세 줄(옛 도구가 놓쳤다) |

## 잔존 grep

`permission_denials_count`, `permission_denied 이벤트`, `다른 프로세스가 쥐고`, `Restart Manager`, `처음 12줄`,
`결과 블록·경고`, `gh_run_summary`를 md·py·yml·yaml·toml·json·ts·sh·ps1에서 찾았다. 살아 있는 문서의 옛 서술은
`operations.md` 33행(도구가 보여 주는 것) 하나였고 고쳤다. 나머지 적중은 일지, 닫힌 행, 새 프로브의 서술, 그리고
지금과 같은 `KICKOFF.md`·`README.md`·ADR 0006의 가리킴이다.

## 검사

- 검증 명령: 셀프 리뷰를 반영한 뒤 `uv run pytest -q` 1935 통과(7 deselected), `ruff check`·`ruff format --check`,
  `pyright`, `lint-imports`, `pnpm -C web verify`(28파일 356개)가 모두 초록이다. 이 워크트리에는 web 의존성이 없어
  `pnpm -C web install --frozen-lockfile`을 먼저 쳤다.
- 변이: 셀프 리뷰를 반영한 뒤 `gh_run_summary_mutations.toml` 열하나, `tidy_checkouts_mutations.toml` 예순둘 모두
  기대대로.
- pyright를 `--pythonplatform Linux`·`Darwin`으로도 돌렸다. CI는 리눅스라 윈도 분기를 보지 않고 리눅스 분기를 본다.
  첫 판에서 리눅스에서만 나는 `reportUnnecessaryComparison` 하나가 나와, 플랫폼 분기를 반환 형을 선언한 함수
  하나(`_process_cwds`)로 옮겼다.

## 셀프 리뷰

`/code-review`(기준 `c60f1b0`, 수정 9·미추적 3, 커밋 0). 명세는 대기열 176~178 행(닫기 전 원문)과 지시문이고, 177의
방법 변경과 동반물(일지, 프로브, 변이 표)은 리뷰어 참고로 갈라 넘겼다. 표준 축은 Minor 7·Nit 9, 명세 축은 Major
1·Minor 2·Nit 1이었다.

- **고친 것.**
  - 명세 Major·표준 Minor(겹침): `operations.md`와 헌법 README가 리뷰의 권한을 `claude_args`만 쥔다고 적었다.
    실행 로그의 init `settingSources`에 `project`가 있어 설정 파일이 실리고 그 권한 규칙도 걸린다. 그 문장을 빼고
    "설정은 실리고 훅만 돌지 못한다"로 고쳤다. "훅이 모두 127"도 로그에 응답이 남은 SessionStart로 좁혔다.
  - 표준 Minor(출력 인자·CQS, 문서화된 표준): `gh_run_summary.py`의 `_blocks`와 읽기 함수 셋이 `summary`를 고쳤다.
    `_blocks`는 읽지 못한 객체를 None으로 내고, 읽기 함수는 값을 돌려주며, `summarize`만 `Summary`를 채운다.
    변이 표의 원문 다섯을 새 코드에 맞췄다.
  - 표준·명세 Minor(근거의 종류): 독스트링·닫힘 메모·테스트가 "남은 세 워크트리는 모두 쉬는 세션마다 띄워 둔
    `claude.exe`"를 측정처럼 적었다. 프로브의 `--folder`가 여러 폴더와 읽은 프로세스 수를 찍게 고쳐 세 폴더를
    프로브가 다시 내게 했고, 부모 앱·CLI 판·`isRunning`은 손으로 봤다고 적었다. "쉬는 세션마다"의 일반화는 뺐다.
  - 표준 Minor·명세 Nit: "32비트는 읽지 못한다"가 코드와 달랐다(건너뛰지 않고 64비트 사본을 읽는다). 낡은 경로로
    이름을 댈 수 있다는 어림으로 고쳤다. 열 수 없는 프로세스는 프로브가 잰 수(672개 중 493개)를 적었다.
  - 표준·명세 Minor: `gh_run_summary_mutations.toml`의 README 줄이 없었다. 더했다.
  - 표준 Nit: 튜플 `(pid, 실행 파일 이름, 작업 디렉터리)`에 별칭 `ProcessCwd`, 테스트의 `Json` 중복 정의를 도구에서
    가져오기, 프로브의 불리언 플래그 인자를 함수 둘로, 프로브 독스트링의 갈래 서술(F를 빼고 G·H를 더했다), README의
    184초 서술과 `tidy_checkouts_mutations.toml` 결과 칸, `gh_run_summary.py` 독스트링의 손으로 센 표기.
- **남긴 것.**
  - 표준 Minor(Divergent Change, 판단 항목): Win32 PEB를 읽는 ctypes 코드가 판정 모듈에 들어왔다. 이 도구는 스크립트로
    돌고(`uv run python tools/tidy_checkouts.py`) `tools/`의 도구는 서로 import하지 않는다(`.claude/rules/tools.md`의
    훅 단독 실행과 같은 결). 나누면 실행 경로와 테스트 경로의 import가 갈린다.
  - 표준 Nit(Speculative Generality): 리눅스 `/proc` 갈래는 CI 테스트에서만 쓰인다. 윈도 갈래는 CI(우분투)에서 돌지
    않아, 실제 프로세스를 훑는 테스트가 CI에서 도는 유일한 길이라 둔다.

## PR 직전 보안·버그·성능 축

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 CLI는 돌지 않았다. 커밋(`b334852`)과 main 병합
(`3990f81`) 뒤에 대체 둘을 나란히 돌렸다.

- **보안(`/security-review`).** 식별 단계의 지적이 0건이라 오탐 거르기는 띄우지 않았다. 쥔 프로세스의 이름과 작업
  디렉터리는 `remove`가 멈출 때의 이유 줄에만 찍히고, 에이전트가 치는 명령(`judge`의 `→` 뒤)은 그것을 쓰지 않는다.
  프로세스는 `PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ`로만 열고 권한을 올리지 않는다.
- **버그·성능(`bug-perf-review`).** 턴 한도(60)에서 보고 없이 멈춰, 이어 붙여 보고만 받았다(대기열 169와 같은 일).
  유효 4, 보류 1, 오탐 9였고 Critical·Major는 없었다. 유효한 넷을 모두 고쳤고 테스트와 변이를 더했다.
  - Minor: `_blocks`가 잘린 객체(닫는 따옴표 없이 끊긴 도구 결과 줄) 뒤의 멀쩡한 객체까지 삼켰다. 서브에이전트가
    실행 38182830347·38189417612의 로그에서 손으로 봤다. 맨 앞의 `{`가 오면 앞 버퍼를 읽지 못한 것으로 세고 새로 연다.
  - Minor: `fetch_log`의 `splitlines()`가 JSON이 이스케이프하지 않는 U+2028 등에서도 줄을 나눴다. `split_log`가
    개행에서만 나눈다. 테스트 도우미 `event()`도 같은 `splitlines()`를 써서, 새 테스트가 도우미에서 먼저 깨졌다.
  - Minor: 읽지 못한 프로세스(이 PC에서 약 27%)가 있는데 빈 목록에서 "쥔 프로세스는 없다"고 단정했다. 읽을 수
    있는 프로세스 가운데에서만 없다고 적는다.
  - Nit: `\\?\` 머리째 작업 디렉터리를 옮긴 프로세스를 놓쳤다(서브에이전트가 손으로 재현했다). 비교 전에 머리를 뗀다.
  - 보류, Nit: `cwd_holders`가 OSError 밖의 예외를 내면 이유 문구 없이 트레이스백으로 끝난다. 그런 예외의 구체적인
    출처를 찾지 못했다. PR 리뷰에서 claude-review가 같은 자리를 짚어 고쳤다(아래).

## PR 리뷰

PR [#182](https://github.com/njh6803/agent-os/pull/182)(커밋 `7c61b2b`까지). CI 일곱이 모두 초록이었다.

- **CodeRabbit.** `@coderabbitai review`를 남겼으나 "Review limit reached"(한도)로 리뷰가 없었다. 회차에 세지 않는다.
  보안·버그 축은 위 PR 직전 대체 둘이 맡았다.
- **claude-review 1회차.** Minor 3·Nit 1, Critical·Major 없음. 첫 회차라 지적마다 판단했다.
  - 고친 것, Minor: `summarize`가 턴수·비용은 결과 블록마다 모으면서 거부는 마지막 블록이 덮어, 키 없는 뒤 블록이
    앞 블록의 거부를 "키 없음"으로 바꿀 수 있었다. 거부도 모은다. 테스트와 변이를 더했다.
  - 고친 것, Minor: `cwd_holders`가 OSError만 잡아 ctypes 쪽 예외(AttributeError, ValueError, `ctypes.ArgumentError`)
    가 판정 4의 1의 이유 줄을 지웠다. 버그 리뷰가 보류했던 것을 두 번째 리뷰어가 짚었다. `CODING_STANDARDS.md`의
    "부재는 `X | None`, 실패의 형태는 층마다 하나"대로 볼 수 없는 것(None)으로 돌려주고, None의 문구를 "찾지
    못했다(이 OS에서 볼 수 없거나 읽다 실패했다)"로 넓혔다. 넷을 매개변수로 둔 테스트와 변이를 더했다.
  - 보류, Minor(Divergent Change): 셀프 리뷰에서 보류한 것과 같다. 봇도 차단 사유가 아니라고 적었다.
  - 보류, Nit(`ProcessCwd` 튜플과 `Holder`): `Holder`는 이유 줄에 붙는 출력의 모양이고 작업 디렉터리를 싣지 않는다.
    튜플은 플랫폼 갈래 셋이 내는 안쪽 값이다. 봇도 작성자 재량이라 적었다.
