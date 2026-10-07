# Agent OS 헌법 · 스택

의존성을 더하거나 스택을 바꿀 때 읽는다. 의존성을 추가하려면 ADR을 남긴다.

| 항목 | 값 |
|---|---|
| 언어 | Python 3.12 고정 (`requires-python = "==3.12.*"`) |
| 패키지 관리 | uv, 단일 패키지, src 레이아웃 |
| 린트·포맷 | ruff |
| 타입 | pyright strict |
| 테스트 | pytest, import 모드 importlib. 비동기 테스트는 pytest-asyncio `asyncio_mode = "auto"`이고 `RuntimeWarning`을 에러로 올린다. ADR 0007. HTTP 표면은 `httpx`의 `AsyncClient`와 `ASGITransport`로 민다(dev 전용, ADR 0010의 2026-09-22 이력). 채널 스트림의 수명만 같은 앱을 ASGI로 직접 부르는 둘째 구동자로 잰다(예외의 범위는 `.claude/rules/http.md`) |
| 경계 | import-linter |
| 런타임 의존성 | core: `langchain-core`, `pydantic`, `anyio`. adapters: `langchain-anthropic`, `langchain-mcp-adapters`. server: `fastapi`, `uvicorn`. 최종 사용자의 서명 토큰 검증은 `pyjwt[crypto]`이고 RS256 하나로 고정한다(ADR 0023. end-user-channel 티켓 01이 직접 의존으로 선언했고 `mcp`가 기대던 것과 같은 판이라 락의 패키지와 판은 바뀌지 않았다). `anyio`는 core의 실행 타임아웃과 채널의 실행 수명이 그 취소 범위에 직접 기대 선언하고 major 4로 묶는다 — 5는 실행 타임아웃의 테스트와 측정을 다시 돌린 뒤에 들인다(ADR 0014의 2026-10-06 이력. 전이 의존성으로 오던 것과 같은 판이라 락의 판은 바뀌지 않았다). anthropic SDK와 mcp는 이들 뒤에서 온다(mcp는 어댑터가 정하는 1.x). `langgraph`는 pyright strict 마찰로 2026-09-21에 뺐다. ADR 0001과 그 이력 |
| CLI | 표준 라이브러리 argparse |
| HTTP | FastAPI(0.140.8 이상, 채널의 스트림이 서는 버전. `fastapi.sse`는 0.135에 들어왔지만 그 사이는 프레임 직렬화와 계약의 항목 스키마가 다르다. ADR 0014와 그 2026-09-26 이력), uvicorn. 조립은 `server.py`의 `create_app()` 하나이고 전역 `app`을 두지 않는다. 채널과 관리가 같이 쓰는 배관은 `agent_os.http`(ADR 0016). `openapi.json`은 저장소 루트에 커밋된 계약이고 최신성을 테스트가 판정한다. ADR 0010 |
| 원격·CI | GitHub, GitHub Actions(`ci.yml`, ubuntu, uv, Node 24와 pnpm). 로컬 훅과 같은 검사이고 파이썬, web, e2e(Playwright), 사진 비교(visual)가 잡 넷으로 함께 돌며 필수 검사 `verify`가 그 결과를 모은다. 사진 비교 잡은 판을 고정한 Playwright 이미지를 잡의 컨테이너로 쓴다. LLM 테스트 제외. e2e와 사진 비교는 pre-commit에는 없다(ADR 0021 이력, ADR 0026). 원격 노출은 같은 기계의 nginx가 TLS를 끝내고 최종 사용자 접두사와 위젯만 넘기며, 설정은 `deploy/nginx/`이고 CI e2e가 러너의 nginx로 판정한다(ADR 0024, ADR 0011 이력) |
| 로깅 | 표준 라이브러리. 구조화 기록은 이벤트가 담당한다 |
| 웹 | `web/`, pnpm 11 워크스페이스(`apps/*`, `packages/*`), Node 24, TypeScript 5.9 고정(7은 typescript-eslint가 거부한다, ADR 0020). 관리 화면은 Next 16과 React 19이고 아직 스타일과 아이콘이 없다(admin-style이 들인다, ADR 0021 이력). 위젯은 React 19 컴포넌트로 Next 16 iframe 페이지와 Vite 라이브러리 빌드의 Shadow DOM 커스텀 요소 번들을 낸다(ADR 0024). 스타일은 Tailwind v4, 아이콘은 lucide-react를 서브패스로 하고 둘 다 design-system 티켓 01이 `web/packages/ui`에 처음 들였다. 디자인 시스템은 두 앱이 하나를 나누고 원천은 코드이며 Claude Design에는 `/design-sync`로 올린다(ADR 0025). 디자인 토큰은 px이고 Tailwind의 기본 `@theme` 값을 비우며, 테마는 색과 글꼴의 한 벌로 다섯이고 테마마다 라이트·다크 모드를 가진다. 미리보기와 실제 브라우저 테스트는 Storybook 10(`@storybook/react-vite`, addon-vitest, addon-a11y의 axe)이고 스토리 테스트는 Vitest 브라우저 모드로 `pnpm -C web verify` 안에서 돈다. 시각 회귀는 Storybook 정적 빌드를 판을 고정한 Playwright Linux Docker 이미지 안에서만 Playwright의 `toHaveScreenshot`으로 찍고 비교하며, CI에서는 `visual` 잡이 돈다. 글꼴은 Noto Sans KR과 테마마다 JetBrains Mono 또는 IBM Plex Mono이고, `@fontsource/noto-sans-kr`·`@fontsource/jetbrains-mono`·`@ibm/plex-mono`(설치 스크립트는 `allowBuilds`에서 끈다)에서 받아 자가 호스팅한다. Storybook과 글꼴은 design-system 티켓 01이, 시각 회귀는 그 티켓 02가 들였다(ADR 0026과 그 2026-10-06 이력). 관리 화면의 서버 데이터는 SWR, 클라이언트 상태는 Zustand(persist는 sessionStorage에, 토큰만). `packages/api-client`는 openapi-typescript와 openapi-fetch로 `openapi.json`에서 생성해 커밋한다. 린트는 ESLint(typescript-eslint, eslint-plugin-boundaries), 포맷은 Prettier, 테스트는 Vitest(jsdom)·Testing Library·MSW, e2e는 Playwright. ADR 0021 |
| 프론트 구성 | 아토믹 디자인. `components/{atoms,molecules,organisms,templates,pages}`. 화면은 `components/pages/`의 클라이언트 컴포넌트이고 `app/**/page.tsx`는 라우팅과 레이아웃만 한다(ADR 0021). API 호출은 organisms 이상만 하고 atoms·molecules는 순수. 층 경계는 ESLint가 판정한다. 두 앱이 나누는 디자인 토큰과 atoms·molecules는 `web/packages/ui`에 두고 organisms 이상은 앱에 남는다. 앱은 그 패키지의 소스를 그대로 import한다. 스토리와 컴포넌트별 쓰임(`<Name>.md`)은 컴포넌트와 같은 폴더에 둔다(ADR 0026). 앱의 스토리는 앱마다의 Storybook에 두고 패키지의 미리보기(`@agent-os/ui/storybook`)를 나눠 쓴다(ADR 0026의 2026-10-07 이력) |

파이썬 한 패키지를 유지하고 배포가 갈릴 때만 나눈다. sdk는 첫 원격 에이전트를 만들 때 별도 배포로 분리한다. 파이썬(`src/`)과 노드(`web/`)는 루트를 분리한다. 두 도구의 `apps/*` 글롭이 서로의 앱을 오인하기 때문이다.
