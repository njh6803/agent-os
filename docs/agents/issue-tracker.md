# 이슈 트래커: 로컬 마크다운

이 저장소의 이슈와 명세는 `.scratch/` 아래 마크다운 파일로 산다. 원격 트래커는 쓰지 않는다.

## 규약

- 기능 하나에 디렉터리 하나: `.scratch/<feature-slug>/`
- 명세는 `.scratch/<feature-slug>/spec.md`
- 구현 티켓은 티켓 하나에 파일 하나: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`. `01`부터 번호를 매기고, 여러 티켓을 한 파일에 합치지 않는다
- 상태는 각 이슈 파일 상단의 `Status:` 줄에 적는다. 값은 `ready-for-agent`(to-tickets가 발행 시 씀), `in-progress`, `done`, `wontfix` 넷 중 하나
- 코멘트와 대화 이력은 파일 끝 `## Comments` 제목 아래에 덧붙인다
- 명세·ADR·코드 주석이 근거로 드는 프로브(측정 스크립트)는 `.scratch/<feature-slug>/probes/`에 커밋한다. 하네스(`tools/`, `.claude/`)를 받치는 것은 slug 자리에 `harness`를 쓴다. 세션 스크래치패드는 임시 디렉터리라 사라지고, 근거를 다시 재거나 반박하려면 스크립트가 있어야 한다. 근거를 드는 자리는 프로브를 파일 이름으로 가리키고, 같은 디렉터리의 `README.md` 표에 프로브마다 한 줄(무엇을 재는지, 어디가 근거로 드는지, 다시 돌 때 필요한 것)을 둔다. 여러 파일로 된 프로브는 한 줄이다. `ruff check .`와 `ruff format --check .`가 이 디렉터리도 보므로 통과해야 한다. pyright와 타입 우회 검사는 보지 않는다
- `.scratch/`는 git에 커밋한다. 이 저장소의 유일한 작업 기록이기 때문이다

## 전체 계획

- `.scratch/plan.md`가 전체 계획이다. 슬라이스와 기능(slug) 목록, 기능마다 `Blocked by`와 `Status`(`todo`, `in-progress`, `done`).
- 기능 하나가 `.scratch/<slug>/` 하나다. `Blocked by`가 비었거나 전부 `done`인 기능이 프론티어이고, 프론티어는 병렬로 돌린다.
- 계약(`sdk/`, `openapi.json`, 헌법)을 바꾸는 티켓은 그 기능의 첫 티켓이며 다른 티켓을 막는다.

## 스킬이 "이슈 트래커에 발행하라"고 할 때

`.scratch/<feature-slug>/` 아래에 새 파일을 만든다. 디렉터리가 없으면 만든다.

## 스킬이 "해당 티켓을 가져오라"고 할 때

참조된 경로의 파일을 읽는다. 사용자는 보통 경로나 이슈 번호를 직접 넘긴다.
