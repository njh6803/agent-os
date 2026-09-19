# Agent OS 헌법 · 원칙

Agent OS는 커스텀 에이전트, MCP 서버, 스킬, 모델을 플러그인으로 동적 로딩해 실행하는 플러그인 기반 에이전트 런타임이다. 태그라인은 "an agent OS". 이 파일은 항상 실린다. 스택은 `tech.md`, 검증과 운영은 `operations.md`, 색인은 `README.md`. 여기 없는 결정은 `docs/adr/`에 쌓인다.

선행 저장소 `ai-agent-platform`과 `agent-runtime-platform`에서 코드는 가져오지 않고 결정과 교훈만 가져온다. 둘 다 LLM 호출 코드 0줄에서 멈췄다. 원칙 I은 그 사인에 대한 처방이다.

## I. 실행 먼저
LLM을 실제로 호출하는 테스트 하나가 통과하기 전에는 헌법, 훅, 게이트, 문서를 늘리지 않는다. 기한은 첫 커밋 후 3일이다. 기한을 넘기면 늘어난 것을 되돌리는 것이 아니라 멈추고 원인을 ADR로 남긴다.

## II. 테스트 먼저
구현 전에 실패하는 테스트를 쓴다. 테스트가 실패하면 테스트를 고치지 않고 멈춰 보고한다. 환경 부재로 skip된 테스트는 초록이 아니다.

## III. 타입 우회 금지
`Any`, `cast`, `type: ignore`, `pyright: ignore`를 쓰지 않는다. pyright strict가 판정하며 테스트 코드도 대상이다.

## IV. 코어는 바깥을 모른다
`agent_os.core`는 `agent_os.channel`, `agent_os.admin`, `agent_os.adapters`, DB, 구체 파일 경로를 import하지 않는다. 플러그인은 `agent_os.sdk`만 import한다. 의존 방향은 `main → server → {channel | admin | adapters} → core → sdk`, `plugins → sdk`뿐이다. 채널, 관리, 어댑터는 서로를 import하지 않고 `main`과 `server`가 조립한다. import-linter가 판정한다. 포트와 어댑터의 세부는 `.claude/rules/core.md`와 `adapters.md`.

## V. 실행은 이벤트 스트림이다
에이전트 실행은 반환값이 아니라 이벤트의 열이다. 모든 이벤트에 `run_id`가 붙는다. 트레이스는 이벤트를 저장한 것이지 별도 수집 층이 아니다. 이벤트와 로그에 API 키, 토큰, 비밀번호를 싣지 않는다.

## 거버넌스
- 이 헌법은 다른 모든 관행에 우선한다. 충돌하면 헌법을 고치거나 관행을 버린다.
- 개정은 ADR을 남기고 사용자가 승인한다. 에이전트는 제안만 한다.
- 버전은 semver. 원칙 변경은 major, 절 추가는 minor, 문구 수정은 patch. 버전은 `README.md`에 있다.
- 팀원이 생기면 원격 저장소, CI, PR 필수로 전환하고 ADR을 남긴다. 그때까지는 pre-commit 훅이 유일한 가드레일이다.
- 철수 조건: 연속 10일 커밋 0이면 접은 것으로 본다.
- 성공 임계값: 첫 커밋 후 3일 안에 원칙 I의 테스트 통과. 2주 안에 첫 슬라이스 완료.
