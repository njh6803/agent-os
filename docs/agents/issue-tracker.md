# 이슈 트래커: 로컬 마크다운

이 저장소의 이슈와 명세는 `.scratch/` 아래 마크다운 파일로 산다. 원격 트래커는 쓰지 않는다.

## 규약

- 기능 하나에 디렉터리 하나: `.scratch/<feature-slug>/`
- 명세는 `.scratch/<feature-slug>/spec.md`
- 구현 티켓은 티켓 하나에 파일 하나: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`. `01`부터 번호를 매기고, 여러 티켓을 한 파일에 합치지 않는다
- 상태는 각 이슈 파일 상단의 `Status:` 줄에 적는다. 값은 `ready-for-agent`(to-tickets가 발행 시 씀), `in-progress`, `done`, `wontfix` 넷 중 하나
- 코멘트와 대화 이력은 파일 끝 `## Comments` 제목 아래에 덧붙인다
- `.scratch/`는 git에 커밋한다. 이 저장소의 유일한 작업 기록이기 때문이다

## 스킬이 "이슈 트래커에 발행하라"고 할 때

`.scratch/<feature-slug>/` 아래에 새 파일을 만든다. 디렉터리가 없으면 만든다.

## 스킬이 "해당 티켓을 가져오라"고 할 때

참조된 경로의 파일을 읽는다. 사용자는 보통 경로나 이슈 번호를 직접 넘긴다.
