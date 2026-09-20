# Agent OS 헌법 · 검증과 운영

커밋, 병합, 트래커, LLM 테스트, 가드레일을 만질 때 읽는다. 검증 명령 넷은 `CLAUDE.md`에 있고 실제로 돌려 통과한 명령만 적는다.

## LLM 테스트
LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다. 기본 `pytest -q`는 이 마커를 제외한다. `uv run --env-file .env pytest -m llm`이 돌리며, `.env`의 `ANTHROPIC_API_KEY`가 없으면 skip이 아니라 실패한다. `.env`는 커밋하지 않는다. 원칙 I의 판정은 이 명령이다. CI가 생겨도 매 푸시에서는 돌리지 않는다.

## 가드레일
자동 검사는 둘이고 내용은 같다. 로컬 pre-commit 훅이 커밋마다, GitHub Actions CI(`.github/workflows/ci.yml`)가 푸시와 PR마다 ruff, ruff-format, pyright, import-linter, pytest(기본 마커), 지침 검사를 돈다. 훅은 각자 설치해야 하므로 CI가 최종 판정이고 main은 CI 통과 없이 병합할 수 없다. 클론 뒤 `uv run pre-commit install`을 한 번 하면 pre-commit과 commit-msg 두 훅이 깔린다. 훅이 안 걸린 저장소는 그 자체가 결함이다. 훅 시스템은 pre-commit 하나만 둔다. 둘이면 `.git/hooks/pre-commit` 한 자리를 다퉈 한쪽이 조용히 안 걸린다. 파이썬 파일이 안 바뀐 커밋에서도 pyright·import-linter·pytest는 돈다(`always_run`). CI에 경로 필터를 걸게 되면 미매칭은 skip이 아니라 실패로 만든다.

## 브랜치와 병합
- 원격은 GitHub, main은 보호 브랜치다. 티켓마다 `feature/<NN>-<slug>` 브랜치를 따고 혼자여도 PR을 연다. `/git-pr`이 `.github/PULL_REQUEST_TEMPLATE.md`를 채운다.
- PR 전에 `/code-review main`. 병렬 브랜치는 PR 전에 main에 rebase한다. 병합은 `/git-pr-merge`의 squash이고 main 이력은 PR 단위다. PR 제목이 곧 main의 커밋 제목이므로 컨벤셔널 커밋 형식이다.
- 병렬 작업은 프론티어(막힌 것이 없는 티켓)에서만 하고, 티켓마다 워크트리 하나다. 티켓 세션의 일지는 `docs/journal/<날짜>-<티켓슬러그>.md`에 쓰고 날짜 파일은 조율 세션만 쓴다.
- 커밋 메시지는 컨벤셔널 커밋, 한국어. 형식(`<타입>: <제목>`, 72자, 마침표 없음)은 commit-msg 훅이 판정하고, 본문의 "왜 그렇게 했는지와 남긴 위험"은 리뷰가 본다.

## 이슈 관리
로컬 마크다운. 전체 계획은 `.scratch/plan.md`, 기능별 명세와 티켓은 `.scratch/<feature-slug>/`. 규약은 `docs/agents/issue-tracker.md`. 팀원이 생겨 티켓 번호가 충돌하면 setup 스킬을 다시 돌려 트래커를 바꾼다.

## TODO
`TODO(<기능슬러그>/<티켓번호>): 설명` 형식만 쓴다. ruff TD 규칙이 판정한다. 티켓 없는 TODO는 금지다.

## 문서 위치
문서는 범위가 있는 곳에 둔다. 저장소 전체에 해당하면 루트 `docs/`, 한 앱에만 해당하면 그 앱 안(README, 중첩 `CLAUDE.md`). 같은 사실을 두 곳에 두지 않고, 지역 문서는 루트를 요약하지 않고 가리키며, 루트가 지역 문서를 색인한다. 헌법, 용어집, ADR 번호열은 하나다. 지역 결정도 루트 ADR 열에 넣고 제목에 범위를 적는다.

## 환경 규약 상세
명령을 치기 전에 알아야 하는 다섯은 `CLAUDE.md`에 있다. 그 밖에 선행 저장소가 겪은 것.
- ruff E501은 표시 폭 기준이라 한글 한 글자가 2로 세어진다.
- Docker 같은 환경이 없어 skip된 통합 테스트는 초록이 아니다. CI에서는 에러로 만든다.
- `alembic.ini` 같은 ini 계열은 환경변수로 인코딩을 못 바꾼다. ASCII만.
