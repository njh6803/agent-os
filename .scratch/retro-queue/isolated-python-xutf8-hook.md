# isolated-python-xutf8-hook: **484의 4회차. CodeRabbit 인라인 지적을 읽는 스크래치 스크립트를 `uv run python -I -c`로 돌려 한글이 깨져 나왔다. `-X utf8`을 함께 주라는 `operations.md` 환경 규약 상세의 줄은 이 세션에 실려 있지 않았다**

**상태:** 열림
**어디로:** `tools/hook_bash_python_stub.py`(맨 `python`을 막는 기존 Bash 훅): `python -I`나 `uv run python -I`에 `-X utf8`이 없으면 계기를 넣는 갈래와 그 판정의 시험과 `tools/hook_payloads.toml`의 페이로드 표. 훅 하나를 새로 더하는 쪽이 낫다고 판단되면 그쪽이 우선이다. 새 훅이라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다
**승인:** 자체 승인 2026-11-09, 484의 4회차(40, 484의 둘째, 484의 셋째에 이은 넷째), 일지 2026-11-09-2138-mcp-http-tickets.md. ADR 불필요

본 것은 이 세션의 사건이다. `gh api`로 받은 CodeRabbit 인라인 지적의 JSON을 `uv run python -I -c`로 풀어 `print`했더니 한글이 모두 깨져 나왔다. 파일을 UTF-8로 쓰고 읽는 길로 돌아가 호출 둘이 더 들었다. 처방은 닫힌 484가 `operations.md`에 한 줄 지침으로 적었다(`-I`는 `PYTHON*` 환경 변수를 모두 무시하니 `-X utf8`을 함께 준다). 이 세션은 `operations.md`의 그 절을 열지 않아 그 줄이 컨텍스트에 없었다. 지침이 있는데도 어겨졌으므로 `CLAUDE.md` 교정 루프의 사다리대로 다음 층은 훅이다.
