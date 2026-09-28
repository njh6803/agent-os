# interrupts 프로브

명세·ADR·코드 주석이 근거로 든 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에
옮겼다(대기열 29). 스크립트는 재측정 세션의 스크래치패드에서 사라져, 그 세션 서브에이전트의 트랜스크립트에
남은 마지막 Write 입력으로 되살렸다(그 뒤 Edit은 없었다). 바꾼 것은 ruff를 지나게 한
`from typing import reveal_type` 한 줄이다. pyright는 맨 이름의 `reveal_type`과 같게 다룬다. 독스트링의
"측정이 끝나면 지운다"는 당시의 기록이다.

**다시 재는 법.** pyright 프로브라 `tests/` 아래로 복사해서 잰다. 점 디렉터리와 `include` 밖은 분석하지
않고 "0 errors"를 낸다. langgraph는 저장소 의존성이 아니니 langgraph가 든 가상환경을 따로 만들고, 그
부모 디렉터리를 `--venvpath`로 넘긴다. `--pythonpath`는 `[tool.pyright]`의 `venvPath`·`venv`에 덮여
무시된다(ADR 0001의 함정). 당시 명령은 다음과 같았고, `summary.filesAnalyzed`가 1인지 본 뒤 규칙별로 셌다.
`MSYS_NO_PATHCONV=1 PYTHONUTF8=1 uv run pyright --outputjson --venvpath <가상환경의 부모> tests/probe_langgraph_types.py`
`.json` 둘은 2026-09-21의 출력이다. ADR 0001이 "나아졌는지"를 볼 기준값이다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `probe_langgraph_types.py` + `probe_langgraph_types.2026-09-21.json` | `StateGraph`·`add_node`·`compile(checkpointer=…)`·`ainvoke`·`Command(resume=…)`·`astream`·`aget_state`·`interrupt`를 pyright strict가 어떻게 보는지(`reveal_type`) | ADR 0001의 "같은 프로브로 재는 것이 첫 일"과 2026-09-21 이력 "재측정: 달라진 것이 없다. 인터럽트도 직접 만든다", ADR 0009 Considered Options, 명세 Further Notes | langgraph가 든 가상환경(당시 1.2.11). `tests/` 아래로 복사한다 |
| `probe_lg_imports.py` + `probe_lg_imports.2026-09-21.json` | langgraph 하위 모듈의 `py.typed` 인식(import만) | ADR 0001의 같은 이력 | 위와 같다 |
