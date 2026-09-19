# Agent OS 헌법

Agent OS는 커스텀 에이전트, MCP 서버, 스킬을 플러그인으로 동적 로딩해 실행하는 플러그인 기반 에이전트 런타임이다. 태그라인은 "an agent OS". 이 문서는 타협하지 않는 원칙, 스택과 구조, 검증과 운영, 개정 절차를 정한다. 여기 없는 결정은 `docs/adr/`에 쌓인다.

선행 저장소 `ai-agent-platform`(2026-08-30~09-10)과 `agent-runtime-platform`(2026-09-17~18)에서 코드는 가져오지 않고 결정과 교훈만 가져온다. 둘 다 LLM 호출 코드 0줄에서 멈췄다. 원칙 I은 그 사인에 대한 처방이다.

## 핵심 원칙

### I. 실행 먼저
LLM을 실제로 호출하는 테스트 하나가 통과하기 전에는 헌법, 훅, 게이트, 문서를 늘리지 않는다. 기한은 첫 커밋 후 3일이다. 기한을 넘기면 늘어난 것을 되돌리는 것이 아니라 멈추고 원인을 ADR로 남긴다.

### II. 테스트 먼저
구현 전에 실패하는 테스트를 쓴다. 테스트가 실패하면 테스트를 고치지 않고 멈춰 보고한다. 환경 부재로 skip된 테스트는 초록이 아니다.

### III. 타입 우회 금지
`Any`, `cast`, `type: ignore`, `pyright: ignore`를 쓰지 않는다. pyright strict가 판정하며 테스트 코드도 대상이다.

### IV. 코어는 바깥을 모른다
`agent_os.core`는 `agent_os.channel`, `agent_os.admin`, `agent_os.adapters`, DB, 구체 파일 경로를 import하지 않는다. 플러그인은 `agent_os.sdk`만 import한다. 의존 방향은 `main → server → {channel | admin | adapters} → core → sdk`, `plugins → sdk`뿐이다. 채널, 관리, 어댑터는 서로를 import하지 않고 `main`과 `server`가 조립한다. import-linter가 판정한다.

### V. 실행은 이벤트 스트림이다
에이전트 실행은 반환값이 아니라 이벤트의 열이다. 모든 이벤트에 `run_id`가 붙는다. 트레이스는 이벤트를 저장한 것이지 별도 수집 층이 아니다. 이벤트와 로그에 API 키, 토큰, 비밀번호를 싣지 않는다.

## 스택과 구조

### 언어와 도구

| 항목 | 값 |
|---|---|
| 언어 | Python 3.12 고정 (`requires-python = "==3.12.*"`) |
| 패키지 관리 | uv, 단일 패키지, src 레이아웃 |
| 린트·포맷 | ruff |
| 타입 | pyright strict |
| 테스트 | pytest |
| 경계 | import-linter |
| 런타임 의존성 | `langgraph`, `langchain-anthropic`, `langchain-mcp-adapters`, `pydantic`. anthropic SDK와 mcp는 이들 뒤에서 온다(mcp는 어댑터가 정하는 1.x). ADR 0001 |
| CLI | 표준 라이브러리 argparse |
| 웹 | Next.js, pnpm 워크스페이스, `web/`. 슬라이스 3부터. 위젯 기술은 슬라이스 4에서 결정 |

의존성을 추가하려면 ADR을 남긴다.

### 디렉터리

```
src/agent_os/              파이썬 한 패키지
  main.py                  진입점. run → channel, serve → server. 어댑터를 조립해 넘긴다
  server.py                슬라이스 2. FastAPI 앱 조립. 채널·관리 라우터
  sdk/                     플러그인이 import하는 유일한 공개 표면. BaseAgent, 이벤트, 매니페스트
  core/                    runtime, loader, llm, mcp 클라이언트, trace 포트
  channel/                 실행을 일으키는 면
    cli/                   슬라이스 1
    http/                  슬라이스 2. /runs
  admin/                   구성을 바꾸고 관찰하는 면
    http/                  슬라이스 2. /plugins, /traces, 위젯 설정
  adapters/                core 포트의 구현. JSONL 트레이스 싱크(슬라이스 1), 나중의 DB·OTel·체크포인터
web/                       슬라이스 3부터. pnpm 워크스페이스. 파이썬과 루트를 분리한다
  apps/admin/              Next.js 관리 화면
  apps/widget/             슬라이스 4. 채팅 위젯. 기술은 그때 결정
  packages/api-client/     openapi.json에서 생성
plugins/
  agents/<name>/plugin.toml + 코드
  mcp/<name>/plugin.toml        서버 실행 명령이나 URL만. 코드 없음
  skills/<name>/plugin.toml + SKILL.md
  models/<name>/plugin.toml       provider, model id, 기본 파라미터. 키는 환경변수 이름만
tests/
docs/           constitution, adr, agents, journal
.scratch/       이슈 트래커
```

### 플러그인 모델

- 종류는 넷이다. `agent`, `mcp`, `skill`, `model`. 매니페스트는 `plugin.toml` 하나이고 `kind`, `name`, `version`을 가지며 `agent`만 `entrypoint = "모듈:속성"`을 가진다. 디렉터리와 `kind`가 어긋나면 로더가 에러를 낸다.
- 에이전트는 개발자가 코드로 쓰는 플러그인이다. 그래프가 아니다. (선행 저장소 ADR 0002 상속)
- 모델은 이름을 가진 LLM 설정이다. 첫 슬라이스는 `kind`와 디렉터리만 예약하고 `--model`에 원시 문자열을 쓴다.
- 진실의 원천은 파일시스템이다. 관리 API와 화면은 매니페스트 파일을 읽고 쓰는 클라이언트다(ADR 0003).
- 스킬은 절차 지식이다. `SKILL.md`와 부속 파일의 폴더이고, 에이전트의 컨텍스트에 주입되어 모델이 읽는다. 함수가 아니다.
- 툴 경로는 MCP 하나다. in-process 함수 툴 종류를 두지 않는다. 로컬 파이썬 툴이 필요하면 MCP 서버로 감싼다.
- 매니페스트와 이벤트 스키마는 디스크에 남는 형식이므로 버전을 가진다. 매니페스트는 `schema_version` 필드, 트레이스는 첫 줄 헤더의 `schema_version`. 모르는 버전은 거부하고, 모르는 이벤트 type은 읽는 쪽이 원문으로 보존한다. 바꾸면 ADR을 남긴다.
- 런타임은 LangGraph로 루프를 돌린다. 플러그인은 그것을 모른다(ADR 0001).
- 에이전트는 쓸 MCP 서버를 매니페스트에 명시한다. 비어 있으면 도구가 없다(ADR 0002).
- 에이전트의 `run()`은 재실행 가능해야 한다. 파일, 시각, 난수, 네트워크 같은 부작용은 `ctx`를 통해서만 일으킨다. 둘째 슬라이스의 멈춤과 재개가 이 성질에 기댄다.
- `AgentContext`의 메서드는 인자와 반환이 JSON으로 직렬화 가능해야 한다. 파이썬 객체를 넘기지 않는다. 원격 실행이 이 성질에 기댄다.

### 첫 슬라이스와 비목표

첫 슬라이스: `plugins/agents/`의 파이썬 에이전트 하나를 CLI로 실행하면, Anthropic 모델을 호출하고 MCP stdio 서버 하나의 도구를 써서 답을 내며, 실행 전체가 이벤트 스트림으로 나오고 JSONL 트레이스로 남는다.

첫 슬라이스가 끝나기 전에는 만들지 않는 것: 선언적 그래프 정의, 원격·WASM·FaaS 실행, 메모리·RAG, 멀티테넌시, UI, 스케줄러, HTTP 채널, 스킬 로더와 모델 로더(디렉터리와 `kind`만 예약).

## 검증과 운영

### 검증 명령

- 테스트: `uv run pytest -q`
- 린트: `uv run ruff check . && uv run ruff format --check .`
- 타입체크: `uv run pyright`
- 경계: `uv run lint-imports`

`CLAUDE.md`의 검증 명령 칸은 이 목록을 복사한다. 실제로 돌려 통과한 명령만 적는다.

### LLM 테스트

LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 기본 `pytest -q`는 이 마커를 제외한다. `uv run --env-file .env pytest -m llm`이 돌리며, `.env`의 `ANTHROPIC_API_KEY`가 없으면 skip이 아니라 실패한다. `.env`는 커밋하지 않는다. 원칙 I의 판정은 이 명령이다.

### 가드레일

원격 저장소가 없어 CI가 없다. pre-commit 프레임워크 훅 하나가 유일한 자동 검사이며 ruff, ruff-format, pyright, pytest(기본 마커)를 커밋마다 돈다. 클론 뒤 `uv run pre-commit install`을 한 번 한다. 훅이 안 걸린 저장소는 그 자체가 결함이다.

### 브랜치와 병합

- 티켓마다 `feature/<NN>-<slug>` 브랜치. 혼자 작업하는 동안은 PR이 없다. 팀원이 생기면 거버넌스의 전환 규칙을 따른다.
- 병합 전 `/code-review main`. 병합은 main에 fast-forward.
- 커밋 메시지는 컨벤셔널 커밋, 한국어.

### 이슈 관리

로컬 마크다운. `.scratch/<feature-slug>/`. 규약은 `docs/agents/issue-tracker.md`.

### 환경 규약 (선행 저장소가 겪은 것)

- `PYTHONUTF8=1`을 `.env`와 훅에 고정한다. 없으면 한국어 출력이 cp949로 깨지고 일부 검사가 통째로 안 돈다.
- 커밋 메시지는 Bash heredoc이나 파일(`git commit -F`)로 넘긴다. PowerShell here-string은 `@`를 메시지에 흘린다.
- 파이프 뒤의 `&&`는 파이프 마지막 명령의 종료 코드만 본다. 판정 명령은 파이프 없이 돌린다.
- ini 계열 파일은 ASCII만 쓴다.
- ruff E501은 표시 폭 기준이라 한글 한 글자가 2로 세어진다.

## 거버넌스

- 이 헌법은 다른 모든 관행에 우선한다. 충돌하면 헌법을 고치거나 관행을 버린다.
- 개정은 ADR을 남기고 사용자가 승인한다. 에이전트는 제안만 한다.
- 버전은 semver. 원칙 변경은 major, 절 추가는 minor, 문구 수정은 patch.
- 팀원이 생기면 원격 저장소, CI, PR 필수로 전환하고 ADR을 남긴다. 그때까지는 pre-commit 훅이 유일한 가드레일이다.
- 철수 조건: 연속 10일 커밋 0이면 접은 것으로 본다.
- 성공 임계값: 첫 커밋 후 3일 안에 원칙 I의 테스트 통과. 2주 안에 첫 슬라이스 완료.

**Version**: 1.3.0 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-19 (ADR 0001, 0002, 0003)
