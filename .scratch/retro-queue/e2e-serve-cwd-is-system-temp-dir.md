# e2e-serve-cwd-is-system-temp-dir: e2e가 `serve`를 시스템 임시 폴더에서 띄워, 그 폴더에 남아 있던 `inspect.py`가 표준 라이브러리의 `inspect`를 가리고 `serve`가 서지 않았다

**상태:** 열림
**어디로:** `web/packages/e2e-stack/src/serve.ts`의 `serve`를 띄우는 자리: 작업 폴더로 `tmpdir()` 대신 그 실행이 새로 만든 빈 폴더를 준다(같은 패키지의 `stack.ts`가 `mkdtempSync`로 만드는 폴더가 있다). 고침이라 사건 하나로 한다
**승인:** 자체 승인 2026-11-18, 1회차, 일지 2026-11-17-2031-plain-words-in-written-artifacts.md. ADR 불필요

`uv run --env-file ../../../.env pytest -m llm_widget`이 "1 failed"로 끝났다(2026-11-18, 이 PC). Playwright가 띄운 `serve`가 서지 않았고, 역추적의 끝은 `asyncio`의 `import inspect`가 `C:\Users\User\AppData\Local\Temp\inspect.py`를 읽은 것이다. 그 파일은 전날 다른 작업이 시스템 임시 폴더에 남긴 244바이트 스크립트다. `serve.ts` 75행이 `python -m agent_os.main serve`의 작업 폴더로 `tmpdir()`를 주고, `python -m`은 작업 폴더를 모듈 찾는 길 맨 앞에 둔다. 그래서 시스템 임시 폴더에 표준 라이브러리와 이름이 같은 `.py`가 하나라도 있으면 e2e와 실제 모델 시험(`llm_widget`, `llm_portal`)의 `serve`가 서지 않는다. 같은 명령 앞에 `PYTHONSAFEPATH=1`을 붙여 다시 돌리니 "1 passed"였다(손으로 봤다. 시험도 코드도 고치지 않았다). CI 러너에서는 본 적이 없다. 시스템 임시 폴더는 다른 저장소의 세션과 함께 쓰는 자리라, 이 저장소의 규칙으로는 그 폴더를 비워 둘 수 없다.
