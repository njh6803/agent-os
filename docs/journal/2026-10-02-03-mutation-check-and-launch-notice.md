# 2026-10-02 (03) 변이 표 원문 확인과 래퍼의 알림 — 대기열 92·93

하네스 chore다. 지시문은 일지 2026-10-02-02의 "다음"이 가리킨 next-session 지시문에서 왔다. 브랜치는
`chore/mutation-check-and-launch-notice`이다. 주 체크아웃(`aadf91d`, 작업 트리 깨끗함)에서 시작했고, `EnterWorktree`로
만든 워크트리에서 브랜치 이름을 바꿔 일했다. 세션 제목은 UserPromptSubmit 훅의 지시대로 브랜치 이름으로 바꿨다.

> 사용자: ".scratch/retro-queue.md의 92·93(변이 표 원문 확인 pre-commit, 래퍼가 지나간 훅 알리기)을 chore PR 하나로 반영한다"

앞 PR의 끝을 여기 남긴다. PR #121은 2회차(`39c80dc`)에서 CI 여섯이 초록이었고 `aadf91d`로 병합됐다. CodeRabbit은
2회차를 시간당 한도로 보지 않았다(1회차 지적을 그대로 반영한 커밋이다). 2회차 claude-review Nit 둘은 그 PR에서 고치지
않았다. `test_launch_hook`의 `direct.returncode == 2` 단언은 CPython의 동작을 재지만 래퍼가 생긴 전제라 이번에도 두었다.
래퍼의 stderr 문구가 인자 누락과 파일 없음을 가르지 않는다는 것은 93과 같은 자리라 이번에 고쳤다(아래).

선행 조건은 이렇게 봤다. 새 세션의 훅이 래퍼를 거쳐 도는지는 UserPromptSubmit 훅이 제목 지시를 넣은 것, PreToolUse
훅 둘이 이 세션에서 발동한 것(`hook_bash_gate_pipe`이 파이프 뒤의 판정 명령에 계기를 넣었고, `hook_env_read`가 Grep의
`!**/node_modules/**` glob을 막았다)으로 봤다. 트랜스크립트의 `stop_hook_summary`는 턴이 끝날 때 남아 이 턴 안에서는
볼 수 없었다. 대신 앞 세션(`477c3ffa`)의 04:00 UTC 기록에 `hook_stop_korean`의 command가 이미 `launch_hook.py`를
가리켰다(병합 뒤 당긴 설정을 그 세션이 다시 읽었다). Bash·PowerShell·Grep은 막히지 않았다.

## 자리를 정한 것

- **92: 인자 규칙.** `--check`의 첫 인자는 예전처럼 표이고, 그 뒤의 `.toml`로 끝나는 인자도 표로 읽는다. 표가 여럿이면
  이름을 섞지 않고, 표 여럿은 `--check`로만 받는다(변이는 표 하나씩 돌린다). 이름 없이 `--check`를 주면 줄마다 표의
  경로가 붙는다 — 첫 판은 표가 하나일 때 경로를 붙이지 않아, pre-commit이 표 하나를 넘기면 어느 표가 틀렸는지 출력에
  없었다(손으로 돌린 pre-commit에서 봤다).
- **92: 훅 자리와 범위.** `check-mutations`는 ruff 훅 뒤에 둔다. pre-commit은 훅을 차례로 돌리고 뒤 훅이 앞 훅이 고친
  파일을 본다. 커밋에 든 표만 보므로 옛 프로브의 원문은 썩어도 된다는 대기열 73의 결정과 맞는다. CI에는 넣지 않았다.
- **92: 출력 인코딩.** pre-commit 훅 환경에 `PYTHONUTF8`이 있다고 가정하지 않는다. 새 subprocess 테스트가
  `PYTHONUTF8` 없이 띄운 `mutate.py`의 출력이 cp949로 나오는 것을 처음에 빨강으로 보였다. 다른 검사처럼 `__main__`에서
  stdout을 UTF-8로 다시 연다.
- **93: 누구에게 무엇을.** 사용자에게는 `systemMessage`(공통 필드), 모델에게는 `additionalContext`를 낸다. 공식 hooks
  문서를 읽고 정했다. 종료 0의 stderr는 디버그 로그로만 가고 세션은 보지 못한다. Stop·SubagentStop도
  `additionalContext`를 받지만 대화를 잇게 하므로, 턴이 끝날 때마다 한 번 더 돌지 않게 사용자에게만 알린다. 모델에게
  가는 문구에는 할 일 문장(`MODEL_SUFFIX`)을 더해, 탐침이 `additionalContext`가 닿았는지 가를 수 있다. 지나간 훅이
  계기 훅일 수도 있어 그 문장은 막던 일과 알리던 일을 함께 말한다.
- **93: 러너의 판정.** 표의 사례는 훅 파일이 있어야 하므로(`load_cases`) 래퍼가 지나가는 길을 돌지 않는다. 그래서
  러너가 등록된 이벤트마다 래퍼를 없는 훅 이름(`ABSENT_HOOK`)으로 띄우고 `context`나 `notice`(새 판정, `systemMessage`
  하나)면 맞다고 본다. 어느 이벤트가 어느 쪽인지는 래퍼의 `CONTEXT_EVENTS`가 정하고, 등록된 이벤트마다의 기대는
  `tests/tools/test_run_hooks.py`가 고정한다. 러너가 그 집합을 다시 적지 않게 둘 다 받는다.
- **93: 해시할 수 없는 이벤트.** `isinstance(event, str)`은 타입을 좁히는 것만이 아니다. 페이로드의 `hook_event_name`이
  목록이면 집합에 바로 물을 때 TypeError로 1이 되어 알림이 없다. 테스트의 첫 판은 그 자리에 `1`을 넣어 확인을 빼도
  초록이었고, 변이 표를 쓰다가 보고 목록으로 바꿨다.

## 잰 것

- **pre-commit 차례**(손으로, 스크래치 스크립트). 포맷 전 코드(`y = ( 1 )`)와 그 줄을 원문으로 둔 표를 함께 넘기고 느린
  훅을 `SKIP`으로 뺐다. 같은 실행에서 ruff가 코드를 `y = 1`로 고쳤고 `check-mutations`가 2로 끝나 그 표의 원문 0번을
  알렸다. 임시 파일이 추적되지 않아 ruff 훅은 "Passed"로 찍혔다(pre-commit은 고친 것을 `git diff`로 본다).
- **원문 확인이 곧바로 일했다.** `run_case`를 `_launch`로 떼어 내자 `launch_hook_mutations.toml`의 "러너가 래퍼를
  거치지 않고 훅을 바로 띄운다" 원문(`launch_argv(case.hook),`)이 사라졌고, 표 둘을 새 `--check`로 넘기자 그것을
  알렸다. 표 열일곱(추적된 열여섯과 이 PR의 새 표 하나)은 모두 원문이 한 번씩 있다.
- **`claude -p` 변형 셋**(`.scratch/harness/probes/hook_registration/run.sh`의 E·F·G, haiku, claude 2.1.286). E 없는
  PreToolUse 훅을 래퍼로 더하고 그 호출에 붙은 알림의 마지막 문장을 물었더니 답이 `MODEL_SUFFIX`의 마지막 문장이었고,
  stream-json에 `PreToolUse:Bash says: launch_hook: …`가 `informational` 이벤트로 왔다. F 없는 Stop 훅을 래퍼로 더하면
  `Stop says: …` 하나에 답이 하나였다. G는 셀프 리뷰 뒤에 더한 F의 대조군이다. Stop에 `additionalContext`를 한 번 내는
  훅을 더하자 답이 둘이 되었고, 그 훅이 받은 `stop_hook_active`는 거짓, 참 순이었다. A~D는 앞 판과 같았다. E는
  `MODEL_SUFFIX`를 고친 뒤 다시 돌려 새 마지막 문장을 옮겼다.
- **시간.** `time_launch.sh`를 93 반영 뒤에 두 번 다시 재 바로 205~218ms, 래퍼 212~220ms였다. 지나가는 길만 json을
  import하므로 훅이 있는 길은 그대로다.
- **러너.** `tools/run_hooks.py`가 52건 어긋남 0, 래퍼 알림 4건(PostToolUse·PreToolUse·UserPromptSubmit은 `context`,
  Stop은 `notice`) 어긋남 0이다.
- **변이.** `launch_hook_mutations.toml` 스물하나(91의 열에 93의 열하나)와 `mutation_check_mutations.toml` 일곱이 모두
  기대대로 빨갰다. 셀프 리뷰를 반영한 뒤 둘 다 다시 돌렸다. 리뷰 전에는 스물과 일곱이었고, 리뷰가 짚은 틈(PostToolUse를
  `CONTEXT_EVENTS`에서 빼도 초록)을 겨누는 변이를 하나 더했다. UTF-8로 다시 열지 않는 변이는 이 윈도우의 cp949
  파이프에서 빨갰고, 로캘이 UTF-8인 곳에서는 재지 않았다.
- **바꾼 규칙의 카나리아**(스크래치 스크립트, sonnet, `operations.md` 환경 규약 상세의 명령). 실험군은
  `tools/hook_env_read.py`를 Read한 세션이고 셋 모두 새 줄이 근거로 든 변형 글자 "G"를 답했다. 대조군은 `paths` 밖의
  `README.md`를 Read한 세션이고 셋 모두 "없음"이었다.

## 셀프 리뷰

`/code-review`, base `aadf91d`, 수정 16, 미추적 3, 커밋 0. `tools/`와 `tests/`의 파이썬이 바뀌어 두 축 모두 기본 모델이다.
명세는 대기열 92·93 행(취소선 전 원문)과 지시문이고, 설계 선택과 이 세션이 더한 프로브 변형은 리뷰어 참고로 갈랐다. 두
축 모두 92·93과 지시문의 문구 가르기가 구현됐다고 봤다.

- **두 축이 같은 것을 따로 냈다: 헌법 버전.** `operations.md` 가드레일에 구절을 더했는데 3.0.6 그대로였다(표준 Major,
  명세 Minor). 문구 수정이라 patch이고 3.0.7로 올렸다.
- **두 축: 근거의 종류.** Stop의 `additionalContext`가 대화를 잇는다는 것을 E·F의 실측으로 적었는데, F는
  `systemMessage`만 낸 경우라 대조군이 없었다. 근거는 문서뿐이었다. 대조군 G를 더해 쟀고, 문장마다 문서와 실측을
  갈랐다. "Stop만은"이라는 닫힌 주장은 SubagentStop과 `CONTEXT_EVENTS` 밖의 이벤트로 넓혔다.
- **두 축: `systemMessage`를 모든 이벤트가 받는다고 적은 첫 판.** 문서는 Setup이 그 JSON 출력을 버리고 StopFailure가 출력을
  무시한다고 적는다. `kickoff/facts.md`와 `notice` 독스트링을 고치고 래퍼의 못 보는 것에 더했다.
- **명세 Minor: 이벤트별 고정이 절반.** 테스트가 Stop과 PreToolUse만 고정해, `CONTEXT_EVENTS`에서 PostToolUse를 빼도
  테스트·러너·변이가 모두 초록이었다. 러너는 `notice`도 받기 때문이다. 테스트가 등록된 이벤트마다 기대를 고정하게
  하고 그 변이를 표에 더했다.
- **표준 Minor: `MODEL_SUFFIX`.** "이 알림은 사용자에게도 보였다"는 독스트링이 재지 않았다고 한 화면 표시를 단정했고,
  "막던 일"은 계기 훅(`hook_journal_retro` 등)에 맞지 않았다. 둘 다 고쳤다.
- **표준 Minor 그 밖.** 프로브 README의 "변형 넷"이 여섯을 나열했다(이제 일곱). 바꾼 rules의 카나리아가 없었다(아래
  검사 절). 일지의 변이 결과 자리가 비어 있었다.
- **Nit, 고친 것.** 표 열일곱의 셈(추적된 열여섯과 새 표 하나), 리눅스의 파이프가 UTF-8이라던 첫 판을 재지 않은 짐작으로,
  "약 10ms"를 93 뒤에 다시 쟀다, 프로브 README에 B의 `echo` 결과, `mutate.main`이 `"--check" in argv`를 세 번 묻던
  것을 `checking` 하나로, 이름 `more`→`more_tables`, `_자기`→`_이_도구`, 테스트 이름의 "받히는"→"받아들이는".
- **남긴 것.** `CLAUDE.md`의 게이트 수(열하나)에 `check-mutations`를 세지 않았다. commit-msg·인용 대조처럼 커밋에 든
  것만 보는 pre-commit 전용 검사이고, 그 목록의 원천은 `operations.md` 가드레일의 첫 문장이다. `hook_path`와
  `skip_reason`이 `len(argv) != 2`를 둘 다 묻는 것은 훅이 있는 길에 일을 더하지 않으려고 두었다. `run_hooks.main`의 출력
  루프 둘은 형식이 달라 두었다. `_launch`의 튜플은 값이 둘뿐이라 두었다. `NoticeResult.ok`가 Stop의 `context`도
  받는 것은 테스트가 이벤트마다 고정하므로 두었다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 1234 passed(경고 3은 기존 pytest-asyncio 설정 경고), `uv run ruff check .`·`uv run ruff format --check .` 통과, `uv run pyright`
  0 errors, `uv run lint-imports` 통과, `tools/check_instructions.py`·`tools/check_type_escapes.py` 통과,
  `tools/run_hooks.py` 52건 어긋남 0과 래퍼 알림 4건 어긋남 0, 변이 표 열일곱의 `--check`. `pnpm -C web verify`는 반영
  전에 통과(Vitest 263 passed)했고 커밋의 pre-commit이 다시 돈다. 워크트리에 web 의존성이 없어 `pnpm -C web install
  --frozen-lockfile --offline`을 한 번 했다. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.
