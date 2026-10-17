---
paths:
  - "tests/**"
---

# tests 규칙

- import 모드가 importlib이라 `__init__.py` 없이 같은 파일명이 여러 디렉터리에 공존한다. 새 테스트 디렉터리를 만들면 그 경로를 잡는 `.claude/rules/*.md`의 `paths`도 넓힌다 — 지침 검사는 죽은 glob만 잡고 빠진 경로는 못 잡는다.
- Fake는 포트 Protocol을 상속하지 않고 시그니처로 만족한다. 픽스처에서 `trace: TraceStore = FakeTrace()`처럼 포트 타입으로 annotate한다. 그 한 줄이 포트 적합성이 검증되는 유일한 지점이고, pyright가 `tests/`를 검사하는 이유다.
- 비동기 테스트는 `async def`로 쓴다. pytest-asyncio가 auto 모드라 데코레이터도 마커도 필요 없고 `asyncio.run()`을 직접 부르지 않는다. 시작과 종료의 수명이 있는 포트는 async 픽스처로 연다. 단 anyio 취소 범위를 쓰는 어댑터(MCP)는 픽스처의 setup과 teardown이 다른 태스크라 터지므로 테스트 본문에서 `async with`로 연다. ADR 0007과 그 이력.
- `RuntimeWarning`은 에러다. `await`나 실행기를 빼먹은 코루틴이 경고만 내고 초록으로 지나가지 않게 하기 위해서다. 경고 전부를 올리지는 않는다.
- LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 명령과 돌리는 계기는 `CLAUDE.md`와 `docs/constitution/operations.md`. 마커는 `pyproject.toml`에 선언된 것만 쓴다(`--strict-markers`). 트레이스는 `tmp_path` 아래에 남긴다. 실행 끝의 토큰 합계는 그 아래만 센다(`tools/llm_tokens.py`, 대기열 113).
- skip은 `conftest.py`가 세션 실패로 만든다. 환경이 없으면 skip이 아니라 실패하게 쓴다(LLM 테스트가 그렇다).
- `conftest.py`가 stdout을 UTF-8로 고정한다. 한국어 단언 메시지가 깨지지 않게 하기 위해서다.
- `conftest.py`가 저장소를 가리키는 `GIT_*` 환경(`GIT_DIR` 등)을 벗긴다. pre-commit이 워크트리에서 훅을 돌리면 git이 그 값을 내보내, 임시 디렉터리에 `git init`하는 테스트가 이 저장소를 재초기화했다(2026-09-28, 공유 config의 `core.bare`가 true). 그래서 테스트의 `git init`은 `tmp_path`에 해도 된다.
- `tools/`의 순수 함수는 `tests/tools/`에서 검증한다. `src/` 미러링의 유일한 예외다. 셸이나 `gh`를 부르는 부분은 실제 실행으로 확인한다. 저장소 상태를 보는 검사에는 이 저장소가 지금 통과함을 재는 테스트(`test_이_저장소의_…`)와 위반을 잡는 변이 테스트(`test_…을_잡는다`)를 하나씩 둔다. 훑은 범위가 비면 실패하게 한다. 경로를 잘못 가리키면 위반 0으로 조용히 초록이기 때문이다(대기열 98). 검사의 `main`이 1을 내거나(`tools/check_adr_pointers.py`) 테스트가 범위를 단언한다(`tests/test_plugins_boundary.py`의 `test_플러그인_파일을_하나는_읽는다`).
- 실제 프로세스·스레드·기한을 재는 시간 단언(몇 초 안에 돌아온다, 기한 안에 끝난다)은 상한을 그 시험만 홀로 돌린 시간의 넉넉한 배수로 둔다. pre-commit 러너는 pytest를 xdist로 나눠 돌리고 다른 세션의 커밋과 겹치기도 해서, 홀로 돌면 지나는 단언이 그 시험을 건드리지 않은 커밋을 막았다(서로 다른 시험 넷 이상, 대기열 332·306). `tests/tools/test_mutate.py`의 20초 단언은 한 프로세스에서 4.56초, xdist에서 10.60초였고(ADR 0035), 같은 러너가 함께 띄운 web-verify가 500초를 쓰던 때 27초였다(일지 2026-10-16-52). 짧은 기한을 일부러 넘기게 하는 사례는 기한을 짧게 두고, 기한 전에 끝나야 할 일이 있는 사례만 넉넉한 기한을 쓴다(`tests/core/test_run.py`의 `PACED`, 일지 2026-10-06-06). 끝나기를 한 번만 견주지 말고 기한까지 거듭 견준다(`tests/tools/test_run_checks.py`의 `_stops_growing`).
- `tests/tools/`의 pwsh 시험 본문은 CI의 리눅스 pwsh에서도 돈다. 그래서 윈도 전용 형식(UIAutomation 등)이 없어도 돌게 쓴다. 길은 둘이 있다. 진짜 어셈블리를 `-ErrorAction Stop`으로 먼저 불러 보고 없으면 같은 이름의 대역 형식을 두거나(`tests/tools/test_open_session.py`의 `_PATTERN_TIMED`), 진짜 형식을 부르지 않고 대역 형식과 같은 이름의 함수로만 돈다(같은 파일의 `_FOCUS`). 그 시험의 첫 판이 윈도 전용 어셈블리(`UIAutomationClient`)를 불러, 이 PC에서는 초록이고 CI의 리눅스 pwsh에서만 빨개져 CI 한 바퀴가 더 들었다(PR #250, 일지 2026-10-16-11, 대기열 281).
- `tools/check_*.py`는 CLI 진입점(`main`)을 subprocess로 한 번 실제로 부르는 테스트를 둔다 — 저장소 밖 픽스처로 알려진 빨강을 만들고 그 빨강이 출력에 있는지 본다. 순수 함수 테스트만 있으면 배관이 조용히 비어도 초록이다(check_quotes의 corpus 키 중복, 2026-09-28). 저장소 상태 검사(check_instructions, check_type_escapes)도 `main`이 루트를 CLI 인자로 받아 임시 트리에서 빨강을 만든다.
