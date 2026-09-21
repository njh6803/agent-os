---
paths:
  - "tests/**"
---

# tests 규칙

- `tests/`는 `src/`를 미러링한다. import 모드가 importlib이라 `__init__.py` 없이 같은 파일명이 여러 디렉터리에 공존한다.
- Fake는 포트 Protocol을 상속하지 않고 시그니처로 만족한다. 픽스처에서 `sink: TraceSink = FakeTraceSink()`처럼 포트 타입으로 annotate한다. 그 한 줄이 포트 적합성이 검증되는 유일한 지점이고, pyright가 `tests/`를 검사하는 이유다.
- 비동기 테스트는 `async def`로 쓴다. pytest-asyncio가 auto 모드라 데코레이터도 마커도 필요 없고 `asyncio.run()`을 직접 부르지 않는다. 시작과 종료의 수명이 있는 포트는 async 픽스처로 연다. ADR 0007.
- `RuntimeWarning`은 에러다. `await`나 실행기를 빼먹은 코루틴이 경고만 내고 초록으로 지나가지 않게 하기 위해서다. 경고 전부를 올리지는 않는다.
- LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 기본 실행에서 제외되고 `uv run --env-file .env pytest -m llm`으로 돈다. 키가 없으면 skip이 아니라 실패한다.
- 환경 부재로 skip된 테스트는 초록이 아니다.
- 테스트가 실패하면 테스트를 고치지 않고 멈춰 보고한다. 같은 테스트가 두 번 연속 실패하면 diagnosing-bugs 스킬을 쓴다.
- `conftest.py`가 stdout을 UTF-8로 고정한다. 한국어 단언 메시지가 깨지지 않게 하기 위해서다.
- `tools/`의 순수 함수는 `tests/tools/`에서 검증한다. `src/` 미러링의 유일한 예외다. 셸이나 `gh`를 부르는 부분은 실제 실행으로 확인한다.
