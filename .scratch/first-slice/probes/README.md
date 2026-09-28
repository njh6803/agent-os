# first-slice 프로브

명세·ADR·코드 주석이 근거로 든 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에
세션 스크래치패드에서 그대로 옮겼다(대기열 29). 옮기기 전의 근거는 프로브를 "실측" 같은 말로 가리킨다.
이 표가 그 말을 파일로 잇는다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `test_forgot_await.py` | `asyncio.run`이나 `await`를 빼먹고 코루틴을 받은 테스트를 pyright strict가 잡는지 | ADR 0007 Consequences의 "(2026-09-21 실측)" 가운데 pyright 줄 | pyright 프로브라 `tests/` 아래로 복사해 `uv run pyright --outputjson tests/<파일>`로 재고, `summary.filesAnalyzed`가 1인지 본다(`.scratch/`는 분석 밖이라 "0 errors"가 거짓이 된다). 2026-09-28에 다시 재니 분석 1, 오류 0으로 여전히 잡지 못했다 |
