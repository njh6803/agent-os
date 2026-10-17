# 2026-10-17 (08) ruff PLW0717 켜기 (대기열 337)

next-session 지시문으로 연 새 세션의 하네스 chore다. `CODING_STANDARDS.md`의 "에러 처리와 정상 흐름을 분리한다" 가운데
`try` 몸통의 길이를 린터 층(ruff preview 규칙 PLW0717)으로 옮기는 열린 대기열 행 337을 한 PR로 닫는다. 나란히 연 세 세션 가운데
셋째다.

> 사용자: "대기열 337(ruff의 PLW0717로 try 블록의 문장 수를 재는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이고, 켜기 전에 지금 위반 13곳을 하나씩 판정한다" (지시문의 시작 프롬프트. 범위는 PR과 병합까지)

## 시작

- **워크트리.** 묶음의 첫 세션이 아니라 `tidy-checkouts`는 돌지 않았다. `EnterWorktree`(이름 `ruff-try-statements`)로 들어가
  지시문의 브랜치 `chore/ruff-try-statements`로 이름을 바꿨다. 기점은 origin/main `544d59ac`다.
- **번호.** `tools/sibling_overlap.py`가 준 다음 빈 번호 08로 이 일지를 만들었다.

## 규칙이 세는 것

ruff 0.16.8에서 문턱을 0으로 두고(`--preview --select PLW0717 --config lint.pylint.max-statements-in-try=0`) 스크래치의
표본 파일로 손으로 봤다. 표본은 커밋하지 않았다. 같은 표본의 일부를 서브에이전트도 따로 봤다.

- `except`가 붙은 `try`만 보고, 그런 `try`마다 따로 잰다. `except` 없는 `try/finally`는 몸통이 여섯 문장이어도 지나간다. 그래서
  행이 걱정한 정리 꼴(`try/finally`)의 거짓 양성은 생기지 않는다. `with suppress(OSError):`처럼 예외를 삼키는 `with`의 몸통도
  여섯 문장이어도 지나간다.
- 재는 `try`의 `except`·`else`·`finally` 몸통은 세지 않는다.
- 몸통의 중첩 블록 안까지 센다. `if`·`with`·`while` 머리와 `if`의 `elif`·`else` 절이 하나씩이다. 몸통 안의 안쪽 `try`는 머리와
  몸통에 더해 `except`·`else` 절을 하나씩, `finally` 절을 둘로 세고 그 절들의 몸통도 센다. 안쪽 `try/finally`의 몸통과 `finally`가
  한 문장씩이면 5이고, 안쪽 `try/except`의 몸통이 하나에 `except` 몸통이 셋이면 6이다. `for` 머리, `for`·`while`의 `else` 절,
  `return`은 세지 않는다(`return`은 서브에이전트가, 나머지는 내가 봤다). 그래서 `try: return f()`는 0이다.

## 위반 13곳의 판정

켜기 전 `uv run ruff check --preview --select PLW0717 .`는 13곳(`src/` 2, `tools/` 7, `.scratch/**/probes/` 4)이었다. 판정의
기준은 그 줄의 뜻이다. `try`가 잡는 예외의 원천이 아닌 로직을 품었으면 참 양성, 몸통 전부가 그 예외의 원천이거나 일부러 넓게
감싼 것이면 거짓 양성으로 본다.

| 자리 | 수 | 꼴 | 판정 | 고친 법 |
|---|---|---|---|---|
| `src/agent_os/adapters/jsonl.py` `read` | 9 | 읽기·디코딩·파싱에 실행 식별자 대조 루프까지 `try` 안 | 참 양성 | 목록의 `_row`처럼 `_read_trace`로 빼고 `try`는 그 호출 하나 |
| `src/agent_os/core/run.py` `execute` | 10 | 에이전트 이벤트 중계(재생 대조, 런타임 전용 거부)가 일시정지를 받는 `try` 안 | 참 양성 | 중계를 비동기 제너레이터 `_Body._relay`로 빼고 `aclosing`으로 연다 |
| `tools/canary.py` `read_facts` | 48 | 줄 종류별 분해 전부가 `ValidationError`의 `try` 안 | 참 양성 | 종류마다 메서드를 둔 `_Reading`으로 옮기고 `try`는 머리 검증과 `add` 둘 |
| `tools/hook_bash_msys_pathconv.py` `_segments` | 10 | `shlex` 순회와 조각 가르기가 `ValueError`의 `try` 안 | 참 양성 | `try`는 `list(lexer)` 하나 |
| `tools/hook_edit_during_commit.py` `_linux_processes` | 8 | `/proc` 파일 넷 읽기에 `stat`의 파싱(`parent_from_stat`)이 섞였다. `with` 머리 셋도 수를 부풀렸다 | 참 양성 | 파싱을 `try` 밖으로 빼고 `Path.read_text`·`read_bytes`로 `with`를 걷어 5 |
| `tools/hook_session_usage.py` `append` | 8 | 다시 덧붙이는 루프가 `OSError`의 `try` 안 | 참 양성 | 루프를 `_append_until_seen`으로 |
| `tools/mutate.py` `main` | 7 | `--since` 출력·고르기·갈래. 8회차 사건의 자리이고 리뷰가 12에서 7로 반쯤 줄였다 | 참 양성 | `_run_table`로 |
| `tools/tidy_checkouts.py` `main` | 6 | 하위 명령 디스패치. 갈래마다 호출 하나 | 경계(분기만 있다) | `_dispatch`로 |
| `tools/token_report.py` `main` | 6 | 잠금 안의 ingest·report 갈래 | 참 양성 | `_run`으로. 잠금의 `with`는 `try`에 남겼다 |
| `.scratch/end-user-channel/probes/run_timeout.py` `run_case` | 8 | 새는 예외를 보려고 시나리오 전체를 감쌌다 | 거짓 양성(의도한 넓이) | 안쪽 함수 `consume`으로. 관찰 범위는 같다 |
| `.scratch/http-channel/probes/probe_uvicorn_shutdown.py` `main` | 6 | 스트림이 끊기는 자리를 보려고 소비 전체를 감쌌다 | 거짓 양성(의도한 넓이) | `consume`으로 |
| `.scratch/web-widget/probes/nginx_relay/measure.py` `h2` | 7 | 읽기 루프 전체가 `TimeoutError`의 `try` 안 | 참 양성 | `try`를 `client.read` 한 줄로 좁혔다. 바깥 `try/finally`의 정리는 그대로 |
| 같은 파일 `abort_case` | 6 | 같은 꼴 | 참 양성 | `wait_for` 한 줄로 좁혔다 |

참 양성 10, 거짓 양성 2, 경계 1이다. 행의 조건 "거짓 양성이 적을 때만 켠다"는 찼다고 판정했다. 참 양성이 아닌 셋은 일부러
넓게 감싼 관찰 탐침 둘과 분기만 있는 디스패치 하나이고, 행이 걱정한 정리 꼴(`try/finally`)은 0곳이며, 셋 모두 함수 하나를 빼서
풀렸다. 그래서 판정에서 뺀 자리(`per-file-ignores`, `noqa`) 없이 모두 고쳤다. 선례 FBT(대기열 285)와 같다. 고친 것은 모두 동작을
바꾸지 않는 옮기기다.

`core/run.py`는 따로 따졌다. 중계를 제너레이터 한 층으로 빼면 닫는 차례가 바뀔 수 있다. `_closing`은 순회를 나올 때 에이전트의
제너레이터를 닫는다. 예외로 빠지면 정리 코드의 `Exception`을 버리며 닫은 뒤 다시 올리고, 정상으로 나오면(순회 끝, `break`) 그대로
닫는다. 옛 `break`를 `_relay` 안의 `return`으로 바꿨고, 둘 다 `async with`를 정상으로 나오므로 같은 길을 지난다. 소비자가 몸통을
닫으면(`GeneratorExit`) `aclosing`이 `_relay`를, `_relay`의 `_closing`이 에이전트를 같은 태스크에서 차례로 닫아 옛 차례와 같다.
일시정지 신호와 취소는 에이전트에서 올라와 두 제너레이터를 끝낸 채 지나가고, 끝난 제너레이터의 `aclose`는 기다리지 않는다.
에이전트의 `run()` 호출도 `_relay`의 첫 순회에서 나므로 옛 자리처럼 같은 `except`가 받는다.

## 문턱

기본값 5를 그대로 적었다.

- **문턱 4.** 지금 코드에서 8곳을 더 낸다. 참 양성은 `nginx_relay/measure.py` `abort_h2`의 읽기 루프 하나다. 나머지는
  `tail_lines` 셋(`hook_handoff`, `hook_handoff_notice`, `hook_midturn_korean`. `with` 하나에 `seek`·`read` 셋과 그 사이에서 다음
  `seek`의 자리를 정하는 계산 한 줄), 위에서 5로 줄인 `/proc` 읽기(읽기 넷과 이름 거르기), 일부러 넓게 감싼 관찰 탐침
  셋(`probe_mw_sse`, `probe_scope`, `probe_scope_cancel`)이다.
- **문턱 6.** 지금 코드에서 값이 6인 넷을 덜 낸다. 참 양성 둘(`token_report` `main`, `measure.py` `abort_case`)을 놓치고 아닌 것
  둘(`probe_uvicorn_shutdown`, `tidy_checkouts` 디스패치)을 덜 낸다. 아래 과거 사건은 5와 같이 둘을 잡는다. 놓치는 참 양성은 리뷰
  한 회차의 값이고 덜 내는 것은 함수 하나를 빼는 값이라 기본값을 바꿀 까닭이 없었다.
- **과거 사건.** 서브에이전트가 행의 여덟 사건을 고치기 전 판으로 다시 지어 ruff로 손으로 봤다(지은 판과
  스크립트는 스크래치에 있고 커밋하지 않았다). 셀프 리뷰가 커밋 전에 고친 다섯은 세션 기록의
  Edit 호출로 지었고, 같은 방법으로 지은 고친 뒤 판이 커밋된 파일과 같은지 견줬다.

| 사건(일지) | 자리 | 고치기 전 | 규칙이 보는 자리인가 |
|---|---|---|---|
| 2026-09-21-first-slice | `channel/cli/main.py` `run_command` | 10 | 예 |
| 2026-09-26-03 | `channel/http/runs.py` `Runs._drive` | 2 | 아니오. 지적은 `except` 안의 분기와 출력 인자 |
| 2026-09-26-05 | `tests/test_main.py` `_serving` | 1 | 아니오. `finally` 안의 로직 |
| 2026-09-28-01 | `adapters/filesystem.py` `_replace_operator_file` | 3 | 예. 다만 3이라 문턱 2에서야 잡힌다 |
| 2026-10-01-06 | `tools/mutate.py` `_run_mutated` | 5 | 아니오. `finally` 안의 로직(그 안의 중첩 `try`가 5) |
| 2026-10-04-04 | `core/run.py` `run()`의 요약 | 1 | 아니오. `except` 안의 조립 |
| 2026-10-12-05 | `tools/rewrap_comments.py` `main` | 2 | 아니오. 실패 분기 되풀이 |
| 2026-10-12-29 | `tools/mutate.py` `main` | 12 | 예. 고친 뒤에도 7이라 이번에 고쳤다 |

문턱 5는 둘, 문턱 4는 셋을 잡는다. 2026-10-01-06의 PR에서 claude-review가 한 층 아래로 옮긴 같은 위반(값 5)을 다시 짚은 일이
하나 더 있고, 그것도 문턱 4에서만 잡힌다. 문턱 4가 더 잡는 사건 하나에 견줘 지금 코드의 거짓 양성 일곱이 커서 5로 두었다.
여덟 사건 가운데 다섯(표의 "아니오")은 지적이 `try` 몸통이 아니라 `finally`·`except` 안의 로직이나 실패 분기 되풀이를
가리켜, 문턱을 내려도 그 지적 자체는 잡히지 않는다. 2026-10-01-06은 `finally` 안의 중첩 `try`가 5라 문턱 4에서 함께 걸릴
뿐이다. 남은 2026-09-28-01은 규칙이 보는 자리지만 3이라 문턱 2에서야 잡힌다. 몸통 밖의 몫은 `CODING_STANDARDS.md`의 그 줄에
리뷰가 볼 것으로 남겼다.

## 설정과 표준 줄

- `pyproject.toml`의 `[tool.ruff.lint]`에 `preview = true`·`explicit-preview-rules = true`를 두고 `select`에 `PLW0717`을, 새
  `[tool.ruff.lint.pylint]`에 `max-statements-in-try = 5`를 적었다. `preview`를 `[tool.ruff]`에 두면 포매터도 preview 서식이 된다.
  lint의 preview만 켜도 지금 코드에 새 위반은 0이었다(explicit을 끈 채로도 0). explicit은 앞으로 ruff를 올렸을 때 접두로 고른
  묶음의 preview 규칙이 조용히 들어오지 않게 하려고 둔다. pre-commit과 CI 모두 `uv run ruff`라 판은 `uv.lock`이 고정한다.
- 설정만으로 규칙이 걸리는지 저장소 안의 표본 파일로 봤다. 다섯 문장은 지나가고 여섯 문장은 걸렸고, `except` 없는 여섯 문장은
  지나갔다. 표본은 지웠다.
- `CODING_STANDARDS.md`의 그 줄을 린터가 막는 범위(`except`가 붙은 `try` 몸통이 중첩 블록까지 다섯 문장을 넘음)와 리뷰가 볼
  것(그 몸통 밖에서 예외 처리와 정상 흐름이 섞이는 자리. 예는 `finally`·`else`·`except` 안의 로직, `except` 없는 `try/finally`나
  `contextlib.suppress` 같은 `with`의 몸통, 다섯 문장 이하에 섞인 무관한 문장, 실패 분기 되풀이)으로 줄였다. 예의 `suppress`와
  일반 조항은 셀프 리뷰에서 더했다. 옛 표현의 잔존은 살아 있는 문서에 없다(대기열 행의 인용만 남는다).

## 변이 표

바뀐 파일을 가리키는 변이 표는 19개다. 고치기 전과 뒤의 `tools/mutate.py --check` 출력이 같았다. 15개는 원문이 모두 맞고, 4개
(`conversation/continuation` 5건, `end-user-channel/contract` 4건, `end-user-channel/timeout` 1건, `web-admin/pause_index` 8건)는
이 브랜치 전부터 원문이 어긋나 있어(기점 판에서도 `--check` 출력이 같았다) 두었다. 어긋난 편집 18건 가운데 9건
(`continuation` 4, `pause_index` 5)은 이 브랜치가 고친 `core/run.py`를 가리킨다. 들여쓰기가 바뀌거나 `self.`가 붙은 원문은 표 여섯에서 고쳤다
(`msys_pathconv_hook` 3, `session_usage_hook` 2, `mutate_runners` 1, `mutate_timeout_select` 1, `tidy_checkouts` 2,
`canary` 변이 다섯의 편집 여섯). 고친 표 여섯을 `tools/mutate.py <표> --since HEAD`로 돌려 원문을 고친 변이 열넷을 다시 쟀고,
모두 기대대로 빨개졌다(표마다 종료 0).

## 탐침

- `probe_uvicorn_shutdown.py`와 `run_timeout.py`는 고치기 전 판(`git show HEAD:`)과 고친 판을 같은 인자로 돌려 출력을 견줬다.
  앞의 것은 첫 이벤트 → 멈춤 요청 → 둘째 이벤트 → 유예 시간 초과로 취소 → 클라이언트의 `RemoteProtocolError` 순서가, 뒤의 것은
  안쪽이 약 6초에 `run_failed`(`TimeoutError`)이고 대조군은 결말 없이 끝나며 둘 다 태스크 그룹 예외가 없다는 것이 같았다.
  `run_timeout.py`는 자기 위치에서 루트를 계산해 옛 판을 같은 폴더에 다른 이름으로 꺼내 돌린 뒤 지웠다.
- `nginx_relay/measure.py`는 nginx와 인증서가 필요해 돌리지 않았다.
- pyright는 `.scratch`를 보지 않아 고친 탐침 셋을 경로로 넘겨 따로 돌렸고 오류는 0이었다.

## 셀프 리뷰

기점 `544d59ac`, 바뀐 파일 21개, 커밋 0개, 미추적 1개(이 일지). 리뷰를 띄우기 전에 일지의 "다섯은 어떤 문턱으로도 잡히지
않는다"와 대기열 닫힘 칸의 "셋은 … 문턱과 무관하다"가 서로 어긋난 것을 서브에이전트의 원래 보고로 대 보고 같은 셈으로 고쳤다
(2026-10-01-06은 문턱 4에서 함께 걸린다).

**표준 축**(sonnet·high). Critical·Major 없음. 13곳의 수, 문턱 4의 8곳, 과거 사건의 수, `explicit-preview-rules`의 효과, 변이 표의
수, 동작 보존은 리뷰어가 손으로 다시 봐서 맞았다.

- 고쳤다(Minor) — 일지의 닫는 차례 문단이 `_closing`이 정상 끝과 `break`에서는 닫지 않는다고 썼다. 코드는 `else`에서도 닫는다.
  결론(옛 `break`와 새 `return`이 같은 길)은 그대로이고 근거 문장을 고쳤다.
- 고쳤다(Minor) — 일지의 셈법이 안쪽 `try`는 `finally` 몸통까지 센다고만 썼다. 손으로 다시 보니 `except`·`else` 절을 하나씩,
  `finally` 절을 둘로 세고 그 몸통도 센다.
- 고쳤다(Minor) — 커밋하지 않은 표본으로 본 것을 대기열 337 행과 일지 셋에 "쟀다"로 썼다(`docs/agents/issue-tracker.md` 근거
  절). "손으로 봤다"로 고쳤다. 커밋한 변이 표로 다시 잰 문장은 그대로다.
- 고쳤다(Minor) — `tools/canary.py`의 `_Reading.take`가 `CONTEXT.md` 동사 표의 `take`(상한을 보고 자리를 차지한다)와 뜻이
  달랐다. 표의 `add`(받은 값을 자기 집계에 더한다)로 바꿨다.
- 고쳤다(Nit) — `CODING_STANDARDS.md`의 못 보는 목록에 `with suppress(...)`의 몸통이 빠졌다. 반례를 덧붙이기만 하지 않고 "린터는
  그 몸통의 문장 수만 세므로 그 밖에서 예외 처리와 정상 흐름이 섞이는 자리는 리뷰가 본다"는 조항을 세우고 목록을 그 예로 뒀다.
- 고쳤다(Nit) — `tools/mutate.py`의 새 `_run`이 같은 모듈의 `_Run` 클래스, `_run_of`, `_run_mutated`와 헷갈려 `_run_table`로 바꿨다.
- 남겼다(Nit) — `tools/token_report.py`의 `_run`은 그 모듈에 겹치는 이름이 없고 `tools/canary.py`의 `_run`과 같은 쓰임이라 뒀다.
  `_Body._relay`의 Feature Envy는 옛 `execute`가 `ctx`를 만지던 그대로를 옮긴 것이고 실행의 요청과 식별자를 몸통이 들고 있어 뒀다.
  `token_report._run`과 `tidy_checkouts._dispatch`의 Data Clumps는 이 변경 전의 `main` 지역 변수 그대로라 뒀다.

**명세 축**(본 세션 모델). Critical·Major 없음. 13곳·문턱 4·과거 사건·변이 표의 수와, 옛 계약(관련 pytest 1457개, `read_facts`와
`_segments`를 고치기 전 판과 같은 입력으로 견준 차이 0, 쓰기 실패로 소비 쪽이 닫힐 때 에이전트의 `finally`가 같은 태스크에서 도는
차례)은 리뷰어가 손으로 다시 봐서 맞았다.

- 고쳤다(Minor) — 대기열 닫힘 칸이 "`finally`·`else` 몸통은 보지 않는다"고 넓게 썼다. 재는 `try`의 몸통 안에 든 안쪽 `try`의
  `finally`는 센다. "그 `try` 자신의"로 좁혔다.
- 고쳤다(Minor) — `/proc` 읽기를 "모두 `OSError`의 원천"이라 거짓 양성에 가깝다고 판정했는데, 옛 `try`에 `parent_from_stat`
  파싱이 있었다(`git diff`로 봤다). 일지가 세운 기준대로 참 양성으로 고쳐 셈이 참 양성 10, 거짓 양성 2, 경계 1이 됐다. 일지 표,
  셈 문장, 대기열 닫힘 칸을 함께 고쳤다. 같은 꼴로 문턱 4의 `tail_lines`도 "읽기 넷이 모두 원천"이 아니라 `seek`·`read` 사이의
  계산 한 줄이 있다고 고쳤다.
- 고쳤다(Minor) — 행의 조건 "거짓 양성이 적을 때만 켠다"를 판정한 문장이 없었고, 문턱을 4와만 견줬다. 판정 문장과 문턱 6의
  비교(값이 6인 넷: 참 양성 둘을 놓치고 아닌 것 둘을 덜 내며 과거 사건은 같다)를 일지와 닫힘 칸에 더했다.
- 고쳤다(Minor) — 일지가 어긋난 변이 표 넷을 "다른 파일의 원문"이라 썼다. 18건 가운데 9건이 이 브랜치가 고친 `core/run.py`를
  가리킨다(`tools/mutate.py --check`로 다시 봤다). 기점 판에서도 같았다는 것과 함께 사실대로 고쳤다.
- 고쳤다(Nit) — 337 행의 취소선이 굵은 글만 그었다. 다른 닫힌 행처럼 괄호까지 함께 그었다.
- 고쳤다(Nit) — "`elif`·`else` 절이 하나씩"이 `for`·`while`의 `else`에서 틀렸다. 손으로 다시 보니 `if`의 `else`만 하나로 세고
  `for`·`while`의 `else` 절은 세지 않는다(`while` 머리는 센다).

PR 직전 리뷰에 밀 주장으로 넘길, 반영하며 새로 쓴 문장:

- 일지 "규칙이 세는 것": "`except`가 붙은 `try`만 보고, 그런 `try`마다 따로 잰다", "`with suppress(OSError):`처럼 예외를 삼키는
  `with`의 몸통도 여섯 문장이어도 지나간다", "재는 `try`의 `except`·`else`·`finally` 몸통은 세지 않는다", "몸통 안의 안쪽 `try`는
  머리와 몸통에 더해 `except`·`else` 절을 하나씩, `finally` 절을 둘로 세고 그 절들의 몸통도 센다. 안쪽 `try/finally`의 몸통과
  `finally`가 한 문장씩이면 5이고, 안쪽 `try/except`의 몸통이 하나에 `except` 몸통이 셋이면 6이다".
- 일지 닫는 차례: "`_closing`은 순회를 나올 때 에이전트의 제너레이터를 닫는다. 예외로 빠지면 정리 코드의 `Exception`을 버리며
  닫은 뒤 다시 올리고, 정상으로 나오면(순회 끝, `break`) 그대로 닫는다".
- 일지 문턱: "여덟 사건 가운데 다섯(표의 "아니오")은 지적이 `try` 몸통이 아니라 … 가리켜, 문턱을 내려도 그 지적 자체는 잡히지
  않는다. 2026-10-01-06은 `finally` 안의 중첩 `try`가 5라 문턱 4에서 함께 걸릴 뿐이다. 남은 2026-09-28-01은 규칙이 보는 자리지만
  3이라 문턱 2에서야 잡힌다". 대기열 337 닫힘 칸의 같은 셈.
- `CODING_STANDARDS.md` 15번 줄: "린터는 그 몸통의 문장 수만 세므로, 그 밖에서 예외 처리와 정상 흐름이 섞이는 자리는 리뷰가
  본다"와 `contextlib.suppress`를 든 예.
- 일지 셈법: "`if`·`with`·`while` 머리와 `if`의 `elif`·`else` 절이 하나씩이다", "`for` 머리, `for`·`while`의 `else` 절, `return`은
  세지 않는다".
- 일지 13곳 표의 `/proc` 행("`stat`의 파싱(`parent_from_stat`)이 섞였다", 참 양성)과 "참 양성 10, 거짓 양성 2, 경계 1", "참
  양성이 아닌 셋은 … 셋 모두 함수 하나를 빼서 풀렸다". 대기열 닫힘 칸의 같은 셈과 "그 `try` 자신의 `finally`·`else` 몸통".
- 일지 문턱: `tail_lines`의 "`seek`·`read` 셋과 그 사이에서 다음 `seek`의 자리를 정하는 계산 한 줄", 문턱 6의 "값이 6인 넷 …
  참 양성 둘을 놓치고 아닌 것 둘을 덜 낸다. 과거 사건은 5와 같이 둘을 잡는다".
- 일지 변이 표: "어긋난 편집 18건 가운데 9건(`continuation` 4, `pause_index` 5)은 이 브랜치가 고친 `core/run.py`를 가리킨다",
  "기점 판에서도 `--check` 출력이 같았다".

다시 돌린 명령: 고친 뒤 `tests/tools/test_canary.py`·`test_mutate.py` 385개 통과, 두 파일의 pyright 0 errors. 손으로 치는 다섯은
커밋의 pre-commit 결과로 갈음한다(아래 검사).
