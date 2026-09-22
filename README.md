# Agent OS

플러그인 기반 에이전트 런타임. an agent OS.

규칙은 [docs/constitution/](docs/constitution/README.md), 용어는 [CONTEXT.md](CONTEXT.md), 결정은 [docs/adr/](docs/adr/), 진행 기록은 [docs/journal/](docs/journal/), 전체 계획은 [.scratch/plan.md](.scratch/plan.md).

```bash
uv sync
uv run pre-commit install
uv run pytest -q
```

## 구조

```
src/agent_os/
  main.py          진입점. run·resume → channel. 어댑터를 조립해 넘긴다
  sdk/             플러그인이 import하는 유일한 표면. 이벤트, 매니페스트, BaseAgent
  core/            런타임, 로더, 루프, 재생, 포트 선언
  channel/cli/     실행을 일으키는 면
  admin/           구성을 바꾸고 관찰하는 면 (슬라이스 2)
  adapters/        포트 구현
plugins/
  agents/  mcp/  skills/  models/    각각 <name>/plugin.toml
tests/             src를 미러링
docs/
  constitution/    헌법 (principles, tech, operations)
  adr/  agents/  journal/
.scratch/          로컬 이슈 트래커. plan.md와 기능별 spec·티켓
.claude/
  agents/          프로젝트 서브에이전트. coderabbit-review(트리아지만, 수정 없음)
  rules/           디렉터리별 규칙. 해당 파일을 열 때만 로드
  skills/          엔지니어링 스킬
.coderabbit.yaml   CodeRabbit 설정. PR 봇과 로컬 CLI가 같이 읽는다
```

아직 없는 것(`server.py`, `channel/http`, `web/`)은 [.scratch/plan.md](.scratch/plan.md)의 목표 배치에 있다.

## 원천 표

사실 하나에 원천 하나. 다른 문서는 이 원천을 가리키기만 하고 요약하지 않는다. 두 곳이 다르면 원천이 맞고 나머지가 버그다.

| 사실 | 원천 | 비고 |
|---|---|---|
| 원칙과 거버넌스 | `docs/constitution/principles.md` | `CLAUDE.md`가 임포트 |
| 스택과 의존성의 결정 | `docs/constitution/tech.md` | 구현은 `pyproject.toml`. 둘이 다르면 pyproject를 맞추거나 ADR |
| 검증·운영 규약 | `docs/constitution/operations.md` | 검증 명령 넷은 `CLAUDE.md`, 실행은 `.pre-commit-config.yaml`. 명령이 바뀌면 둘 다 |
| 제품 의도와 성공의 정의 | `docs/PRD.md` | 헌법은 원칙 I의 기한만 |
| 용어 | `CONTEXT.md` | 피할 말 포함 |
| 결정과 이유 | `docs/adr/`, 색인 `docs/adr/README.md` | 헌법과 rules는 번호로 인용만 |
| 판단 기준(리뷰) | `CODING_STANDARDS.md` | "규칙으로" 승인분만 |
| 리뷰 파이프라인(누가 언제 무엇을) | `docs/constitution/operations.md` | 봇 설정은 `.coderabbit.yaml`과 `.github/workflows/claude-code-review.yml`. 기준은 CODING_STANDARDS |
| 디렉터리별 규칙 | `.claude/rules/*.md` | 해당 파일을 열 때만 실림 |
| 현재 구조 | 코드 | 이 README의 트리는 안내 |
| 미래 배치, 기능 순서, 상태 | `.scratch/plan.md` | |
| 기능 명세와 티켓 | `.scratch/<slug>/` | |
| 디스크 형식(매니페스트, 이벤트) | `src/agent_os/sdk/`와 `tests/sdk/` | `rules/sdk.md`는 결정만 |
| 설치된 스킬과 해시 | `skills-lock.json` | |
| 진행 기록 | `docs/journal/` | 이력이지 원천이 아니다 |
| 환경 함정 | `CLAUDE.md`(명령 전에 볼 다섯), `operations.md`(나머지) | 런북 부록 A는 새 프로젝트용 사본 |
| 리뷰 봇 실행의 실제 내용 | Actions 로그. `tools/gh_run_summary.py`가 요약 | 체크의 초록은 원천이 아니다 |
