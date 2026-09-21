# Agent OS 헌법 · 스택

의존성을 더하거나 스택을 바꿀 때 읽는다. 의존성을 추가하려면 ADR을 남긴다.

| 항목 | 값 |
|---|---|
| 언어 | Python 3.12 고정 (`requires-python = "==3.12.*"`) |
| 패키지 관리 | uv, 단일 패키지, src 레이아웃 |
| 린트·포맷 | ruff |
| 타입 | pyright strict |
| 테스트 | pytest, import 모드 importlib. 비동기 테스트는 pytest-asyncio `asyncio_mode = "auto"`이고 `RuntimeWarning`을 에러로 올린다. ADR 0007 |
| 경계 | import-linter |
| 런타임 의존성 | core: `langgraph`, `langchain-core`, `pydantic`. adapters: `langchain-anthropic`, `langchain-mcp-adapters`. anthropic SDK와 mcp는 이들 뒤에서 온다(mcp는 어댑터가 정하는 1.x). ADR 0001 |
| CLI | 표준 라이브러리 argparse |
| 원격·CI | GitHub, GitHub Actions(`ci.yml`, ubuntu, uv). 로컬 훅과 같은 검사. LLM 테스트 제외 |
| 로깅 | 표준 라이브러리. 구조화 기록은 이벤트가 담당한다 |
| 웹 | Next.js, pnpm 워크스페이스, `web/`. 슬라이스 3부터. 위젯 기술은 슬라이스 4에서 결정 |
| 프론트 구성 | 아토믹 디자인. `components/{atoms,molecules,organisms,templates}`. API 호출은 organisms 이상만 하고 atoms·molecules는 순수. 위젯과 공유하는 atoms는 `web/packages/ui`. pages를 `components/pages/`로 둘지 `app/`에 맡길지는 슬라이스 3 인터뷰에서 결정(테스트 경계 근거는 `docs/journal/` 09-20) |

파이썬 한 패키지를 유지하고 배포가 갈릴 때만 나눈다. sdk는 첫 원격 에이전트를 만들 때 별도 배포로 분리한다. 파이썬(`src/`)과 노드(`web/`)는 루트를 분리한다. 두 도구의 `apps/*` 글롭이 서로의 앱을 오인하기 때문이다.
