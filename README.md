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
  main.py          진입점. run → channel. 어댑터를 조립해 넘긴다
  sdk/             플러그인이 import하는 유일한 표면. 이벤트, 매니페스트, BaseAgent
  core/            런타임, 로더, 루프, 포트 선언
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
  rules/           디렉터리별 규칙. 해당 파일을 열 때만 로드
  skills/          엔지니어링 스킬
```

아직 없는 것(`server.py`, `channel/http`, `web/`)은 [.scratch/plan.md](.scratch/plan.md)의 목표 배치에 있다.
