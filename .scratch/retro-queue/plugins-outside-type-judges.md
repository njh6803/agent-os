# plugins-outside-type-judges: **`plugins/`의 파이썬 코드가 원칙 III의 판정자(pyright strict와 `tools/check_type_escapes.py`) 밖에 있는데, 기본 에이전트(base-agent 티켓 03)가 그 아래에 에이전트 코드를 새로 두고 커스텀 에이전트는 그 폴더를 복사해 코드를 고친다**(명세 검토가 nit으로 짚었다. ADR 0013은 넓히는 것을 "필요가 증명되면" 그 ADR의 이력에 쌓는 별개의 결정으로 남겼다)

**상태:** 열림
**어디로:** `pyproject.toml`의 `[tool.pyright]` `include`에 `plugins`를 더한다(`tools/check_type_escapes.py`의 `scanned_roots`가 그 `include`를 읽어 따라온다). `docs/adr/0013-principle-iii-has-its-own-judge.md`에 이력을 더하고 사용자 승인을 받는다. base-agent 티켓 03보다 먼저 들어가면 그 에이전트 코드가 첫 커밋부터 판정된다
**승인:** 사용자 승인 2026-11-11, 1회차, 일지 2026-11-11-1555-base-agent-tickets.md. ADR 필요(0013 이력)

2026-11-11에 `plugins/`의 파이썬 파일은 `plugins/agents/calc/agent.py` 하나였고, 그 파일을 pyright strict로 돌리면 오류가 0이었다(일지의 회고 절에 명령과 함께 적었다).
