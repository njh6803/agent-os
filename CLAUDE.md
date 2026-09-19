# Agent OS

## 지도
- 헌법(타협 불가 원칙, 스택, 저장소 구조, 검증 의무): @docs/constitution.md
- 코딩 표준(리뷰 시 적용): CODING_STANDARDS.md
- 용어집: CONTEXT.md, 결정 기록: docs/adr/
- 진행 일지: docs/journal/

## 검증 명령
- 테스트: `uv run pytest -q` (LLM 호출 테스트는 `uv run pytest -m llm`)
- 린트: `uv run ruff check . && uv run ruff format --check .`
- 타입체크: `uv run pyright`
- 경계: `uv run lint-imports`

## 교정 루프
- 내가 네 결과를 고치거나 되돌리면, 먼저 그 실수를 테스트·린트·훅 같은 자동 검사로 잡을 수 있는지 판단하고 검사를 제안한다.
- 자동 검사로 잡을 수 없는 판단 기준만 CODING_STANDARDS.md에 한 줄로 제안한다. 내가 "규칙으로"라고 말하기 전에는 추가하지 않는다.
- 이 파일에는 규칙을 쓰지 않는다. 다른 파일을 가리키는 포인터만 둔다.
- 의미 있는 세션이 끝나면 /retro를 권한다.

## 원칙
- 답변과 문서는 한국어로 쓴다.

## Agent skills
### Issue tracker
이슈는 `.scratch/<feature-slug>/` 아래 로컬 마크다운. `docs/agents/issue-tracker.md` 참조.
### Domain docs
단일 컨텍스트. 루트 `CONTEXT.md`와 `docs/adr/`. `docs/agents/domain.md` 참조.
