---
paths:
  - "tests/**"
---

# tests 규칙

- import 모드가 importlib이라 `__init__.py` 없이 같은 파일명이 여러 디렉터리에 공존한다. 새 테스트 디렉터리를 만들면 그 경로를 잡는 `.claude/rules/*.md`의 `paths`도 넓힌다 — 지침 검사는 죽은 glob만 잡고 빠진 경로는 못 잡는다.
- Fake는 포트 Protocol을 상속하지 않고 시그니처로 만족한다. 픽스처에서 `trace: TraceStore = FakeTrace()`처럼 포트 타입으로 annotate한다. 그 한 줄이 포트 적합성이 검증되는 유일한 지점이고, pyright가 `tests/`를 검사하는 이유다.
- 비동기 테스트는 `async def`로 쓴다. pytest-asyncio가 auto 모드라 데코레이터도 마커도 필요 없고 `asyncio.run()`을 직접 부르지 않는다. 시작과 종료의 수명이 있는 포트는 async 픽스처로 연다. 단 anyio 취소 범위를 쓰는 어댑터(MCP)는 픽스처의 setup과 teardown이 다른 태스크라 터지므로 테스트 본문에서 `async with`로 연다. ADR 0007과 그 이력.
- `RuntimeWarning`은 에러다. `await`나 실행기를 빼먹은 코루틴이 경고만 내고 초록으로 지나가지 않게 하기 위해서다. 경고 전부를 올리지는 않는다.
- LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 명령과 돌리는 계기는 `CLAUDE.md`와 `docs/constitution/operations.md`. 마커는 `pyproject.toml`에 선언된 것만 쓴다(`--strict-markers`).
- skip은 `conftest.py`가 세션 실패로 만든다. 환경이 없으면 skip이 아니라 실패하게 쓴다(LLM 테스트가 그렇다).
- `conftest.py`가 stdout을 UTF-8로 고정한다. 한국어 단언 메시지가 깨지지 않게 하기 위해서다.
- `conftest.py`가 저장소를 가리키는 `GIT_*` 환경(`GIT_DIR` 등)을 벗긴다. pre-commit이 워크트리에서 훅을 돌리면 git이 그 값을 내보내, 임시 디렉터리에 `git init`하는 테스트가 이 저장소를 재초기화했다(2026-09-28, 공유 config의 `core.bare`가 true). 그래서 테스트의 `git init`은 `tmp_path`에 해도 된다.
- `tools/`의 순수 함수는 `tests/tools/`에서 검증한다. `src/` 미러링의 유일한 예외다. 셸이나 `gh`를 부르는 부분은 실제 실행으로 확인한다. 저장소 상태를 보는 검사에는 이 저장소가 지금 통과함을 재는 테스트(`test_이_저장소의_…`)와 위반을 잡는 변이 테스트(`test_…을_잡는다`)를 하나씩 둔다.
