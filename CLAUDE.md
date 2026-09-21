# Agent OS

플러그인 기반 에이전트 런타임. an agent OS. 원칙 다섯은 아래에서 임포트되고, 나머지는 필요할 때 경로로 읽는다. 이 파일은 200줄 이하로 유지한다.

@docs/constitution/principles.md

## 레이어

탐색 전에 이것만 알면 된다. 전체 트리는 `README.md`, 아직 없는 미래 배치는 `.scratch/plan.md`.

- `src/agent_os/sdk/`: 플러그인이 import하는 유일한 표면. 이벤트, 매니페스트, BaseAgent, AgentContext
- `src/agent_os/core/`: 런타임, 로더, 루프, 포트 선언. 바깥을 모른다
- `src/agent_os/channel/`: 실행을 일으키는 면. `cli/`(슬라이스 1), `http/`(슬라이스 2)
- `src/agent_os/admin/`: 구성을 바꾸고 관찰하는 면(슬라이스 2)
- `src/agent_os/adapters/`: 포트 구현. JSONL 트레이스 싱크 등
- `src/agent_os/main.py`: 조합 층. 의존 방향은 `main → server → {channel | admin | adapters} → core → sdk`, `plugins → sdk`
- `plugins/{agents,mcp,skills,models}/`: 플러그인. 코드가 아니라 내용물
- `tests/`: `src/`를 미러링

## 지도

무엇을 언제 읽고 어디에 쓰는지. `@`로 임포트하는 것은 `principles.md` 하나뿐이고 나머지는 경로다. 같은 사실을 두 곳에 두지 않고, 지역 문서는 루트를 요약하지 않고 가리킨다. 헌법, 용어집, ADR 번호열은 하나다.

| 문서 | 읽는 때 | 쓰는 때 |
|---|---|---|
| `docs/constitution/principles.md` | 항상(임포트) | 개정은 ADR과 승인 |
| `docs/constitution/tech.md` | 의존성을 더하거나 스택을 바꿀 때 | ADR 뒤 |
| `docs/constitution/operations.md` | 커밋·병합·리뷰·트래커·LLM 테스트·가드레일을 만질 때 | ADR 뒤 |
| `docs/PRD.md` | 범위를 정하거나 스펙이 충돌할 때 | 사용자 승인으로 |
| `CONTEXT.md` | 용어를 쓰거나 새 개념이 나올 때 | domain-modeling 스킬이 |
| `docs/adr/` | 결정을 바꾸기 전, 그 영역을 처음 만질 때 | 아키텍처 결정 뒤 초안을 보여주고 승인 |
| `CODING_STANDARDS.md` | code-review 때 | 사용자가 "규칙으로"라고 한 뒤 |
| `.scratch/plan.md` | 이어서 할 때, 티켓을 고를 때 | 기능 상태가 바뀔 때 |
| `.scratch/<slug>/spec.md`, `issues/` | 티켓 작업을 시작하기 전 | to-spec, to-tickets 스킬이 |
| `docs/journal/` | 이어서 할 때 최신 파일 끝의 "다음" | 단계를 마칠 때. 사용자 프롬프트 원문 포함 |
| `docs/agents/` | 트래커·도메인 문서 규약이 헷갈릴 때 | setup 스킬이 |
| `.claude/rules/*.md` | 해당 경로의 파일을 열 때 자동 | 아래 로드 시점 표에 따라 |
| `README.md` | 사람이 처음 볼 때 | 구조가 바뀔 때 |

## 검증 명령
- 테스트: `uv run pytest -q` (LLM 호출 테스트는 `uv run --env-file .env pytest -m llm`)
- 린트: `uv run ruff check . && uv run ruff format --check .`
- 타입체크: `uv run pyright`
- 경계: `uv run lint-imports`

## 작업 규약
1. 작업 전에 `.scratch/<slug>/`의 명세와 티켓, 건드릴 영역의 ADR을 읽는다. ADR을 먼저 보는 상황은 넷이다. 스택·라이브러리를 바꿀 때, 디렉터리나 층 경계를 바꿀 때, 디스크 형식(매니페스트·이벤트)을 바꿀 때, 기존 코드가 왜 이런지 이해되지 않을 때. 색인은 `docs/adr/README.md`. 경로를 안다고 추측으로 대신하지 않는다.
2. 고칠 파일과 영향을 세 줄로 적고 시작한다. 계약(`sdk/`, `openapi.json`, 헌법)에 닿으면 그 티켓이 다른 티켓을 막는다.
3. 끝나면 검증 명령 넷을 돌린다. 하네스(스킬, 훅, rules, 설정)를 바꿨으면 실제 실행 결과로 확인한다. 파일이 그럴듯해 보이는 것은 확인이 아니다.
4. 결정이 바뀌면 그것을 참조하는 스킬·훅·rules·워크플로·명세를 같이 고치고, 옛 표현을 저장소 전체에서 grep해 잔존이 0인지 본 뒤 3을 다시 돈다. 하네스는 언젠가 맞출 문서가 아니라 다음 실행에 바로 영향을 주는 코드다.
5. 아키텍처 결정을 내렸으면 `docs/adr/`에 초안을 보여주고 승인을 받는다. 임의로 확정하지 않는다.
6. 같은 테스트가 두 번 연속 실패하면 추측 수정을 멈추고 diagnosing-bugs 스킬을 쓴다.
7. 커밋 전에 `/code-review`로 셀프 리뷰하고 Critical·Major를 고친다. 건너뛰지 않는다. PR 직전 CLI와 PR 봇의 역할 분담과 초록 착시는 `docs/constitution/operations.md`의 리뷰 파이프라인.

## 교정 루프
- 내가 네 결과를 고치거나 되돌리면, 먼저 그 실수를 테스트·린트·훅 같은 자동 검사로 잡을 수 있는지 판단하고 검사를 제안한다.
- 자동 검사로 잡을 수 없는 판단 기준만 CODING_STANDARDS.md에 한 줄로 제안한다. 내가 "규칙으로"라고 말하기 전에는 추가하지 않는다.
- 같은 실수가 세 번 반복될 때 규칙 후보로 올린다. 한 번의 사건으로 규칙을 만들지 않는다. 지침으로 적은 뒤에도 어겨지면 훅 후보다.
- 규칙은 강제력이 가장 높은 층에 둔다. 타입 → 린터·훅 → 아키텍처 테스트 → 지침 → 리뷰. 린터가 잡는 것을 지침에 적지 않고, 거짓 양성이 많은 규칙을 하드 게이트로 만들지 않는다.
- 회고는 retro 스킬이 정해진 계기에 스스로 돈다. 계기는 그 스킬의 설명이 원천이고, 후보만 내놓고 반영은 승인 뒤다.

지침을 추가할 때는 내용보다 로드 시점을 먼저 정한다. 파일을 쪼개도 컨텍스트는 줄지 않는다. `paths` 없는 `.claude/rules/*.md`와 `@` 임포트는 이 파일과 똑같이 매 세션 전부 실린다.

| 성격 | 어디에 |
|---|---|
| 린터·타입체커·훅이 판정할 수 있는 것 | 도구 설정. 문서에는 실행 명령만 |
| 특정 디렉터리·파일 패턴에만 해당 | `.claude/rules/*.md` + `paths` 필수 |
| 순서 있는 다단계 절차 | `.claude/skills/` |
| 가끔 참조하는 자료 | `docs/` + 마크다운 링크. `@`를 쓰지 않는다 |
| 매 세션 필요 | 이 파일. 넣기 전에 "이 줄을 지우면 실수하게 되나"를 묻고, 코드에서 유추 가능한 것은 넣지 않는다 |

## 환경 함정
명령을 치기 전에 알아야 해서 여기 있다. 나머지 운영 규약은 `docs/constitution/operations.md`.
- Python 명령 앞에 `PYTHONUTF8=1`. 없으면 한국어 출력이 cp949로 깨지고 일부 검사가 통째로 안 돈다.
- Git Bash의 `python`은 Windows 스토어 스텁이라 아무것도 하지 않는다. `uv run python`이나 `py`.
- 커밋 메시지는 Bash heredoc이나 파일(`git commit -F`)로 넘긴다. PowerShell here-string은 `@`를 메시지에 흘린다. 긴 스크립트는 파일로 쓰고 셸에는 경로만 넘긴다. 큰 heredoc은 셸 파서가 깨진다.
- 파이프 뒤의 `&&`는 파이프 마지막 명령의 종료 코드만 본다. 판정 명령은 파이프 없이 돌린다.
- ini 계열 파일은 ASCII만 쓴다.
- pyright 프로브 파일은 `tests/` 아래에 둔다. 점 디렉터리(`.scratch/`)와 `include` 밖은 검사 없이 "0 errors"가 나온다(두 세션에서 반복). 분석됐는지는 `--outputjson`의 `summary.filesAnalyzed`로 본다.

## 원칙
- 답변과 문서는 한국어로 쓴다.

## Agent skills
### Issue tracker
이슈는 `.scratch/<feature-slug>/` 아래 로컬 마크다운. `docs/agents/issue-tracker.md` 참조.
### Domain docs
단일 컨텍스트. 루트 `CONTEXT.md`와 `docs/adr/`. `docs/agents/domain.md` 참조.
