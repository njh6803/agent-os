# 2026-10-12 (04) PR 템플릿의 `.github/` 줄을 158 뒤의 가드로 고친다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 164를 닫는다. PR #173이 claude-review 워크플로의 코멘트 0개
가드를 바꿨는데, PR 템플릿은 그 가드의 허용 경로 밖이라 #173에 실을 수 없어 이 PR로 따로 왔다. 이 PR은
`claude-code-review.yml`을 바꾸지 않으므로, #173이 바꾼 프롬프트(5·6단계)와 권한 규칙(`--allowedTools`·`--disallowedTools`)으로
claude-review가 처음 도는 PR이기도 하다. 세션은 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤
`EnterWorktree(name=pr-template-review-guard)`로 들어가 `origin/main`(`2a3964f`, #173)에서 `chore/pr-template-review-guard`를 땄다.
순번은 04다. 처음에는 01로 썼으나 커밋 전의 `tools/sibling_overlap.py`가 워크트리 `admin-style-design`도 01을 쓴다고 알려
그 도구가 고른 04로 옮겼다.

## 계기

> 사용자: "대기열 164(PR 템플릿의 `.github/` 줄)를 chore PR로 반영한다. 이 PR은 claude-code-review.yml을 바꾸지 않아 PR #173이 바꾼 프롬프트와 권한 규칙으로 claude-review가 처음 도는 PR이니 그 실행도 본다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `57efd62`에서 `2a3964f`로 당겼다. 스킬 파일은 바뀌지 않았다.
- **종료 1로 남은 것.** `review-workflow-guards`는 다른 프로세스가 폴더를 쥐어 이름 바꾸기가 막혔다(WinError 32).
  `spec-pipeline-and-pytest-ids`는 다시 만들 수 있는 `.venv/`를 지우다 `.pyd` 하나에서 막혔다(WinError 5). 등록과 `.git`은
  남았다. 둘 다 그 세션들이 멈춘 뒤에도 무언가가 파일을 쥐고 있다는 뜻이고, 다음 정리가 다시 본다.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`,
  분리 HEAD 넷(`agent-canary-58969f7`, `confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`),
  등록 없는 폴더 여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 바꾼 것

- `.github/PULL_REQUEST_TEMPLATE.md`의 `.github/` 줄. 옛 줄은 그 워크플로를 바꾼 PR에서 "코멘트 0개 가드도 꺼지므로"라고
  적었다. 158 뒤로 그 PR에서 가드는 코멘트를 세지 않는 대신 그 파일과 허용 경로(`docs/journal/`,
  `.scratch/retro-queue.md`, `.scratch/harness/probes/`) 밖의 파일이 함께 실리면 실패한다. 줄은 이제 그것을 적고,
  허용 경로는 "일지·대기열 등"의 예시와 원천(가드 스텝의 `grep -vE` 패턴)으로 가리킨다. 그래서 그 워크플로의 동작을
  서술한 문서 가운데 허용 경로 밖의 것(이 템플릿, `operations.md` 등)은 그 PR이 병합된 뒤 따로 고친다고 안내한다. 끝
  문장은 "리뷰도 가드도 돈다"에서 "리뷰가 돌고 가드가 코멘트를 센다"로 바꿨다. 이제는 그 PR에서도 가드가 돌기 때문이다.
- `.scratch/retro-queue.md`: 164를 닫았다. 열린 행 31의 2026-10-07 정정 괄호 "코멘트 0개 가드도 그 파일을 바꾼 PR에서만
  건너뛴다"를 "코멘트를 세지 않는다(대기열 50·158)"로 고쳤다.

## 잔존 grep

`가드도 꺼`, `가드가 꺼`, `코멘트 0개 가드`, 그리고 `가드`와 20자 안의 `건너뛴`(앞뒤 양쪽)을 md·yml·yaml·py·toml·json·ts에서
찾았다. 살아 있는 문서의 옛
서술은 템플릿 37행과 열린 행 31 둘이었고 둘 다 고쳤다. 일지 2026-10-07-21의 잔존 grep은 "37행 하나"로 닫았는데,
`건너뛴다`를 찾지 않아 행 31을 놓쳤다(명세 축이 찾았다). 나머지 적중은 일지, 닫힌 행(50·84·158·161), done인 web-admin의
명세·티켓이라 기록이다. `operations.md` 리뷰 파이프라인의 "그 파일의 변경은 별도 PR로 먼저 병합한다"와 워크플로 주석,
`review_workflow.py` 독스트링, 탐침 README는 지금의 동작과 같다.

## 검사

- 검증 명령: `uv run pytest -q` 1875 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(28파일 356개)가 모두 초록이다. 셀프 리뷰를 반영한 뒤 모두 다시 돌렸고 같은 결과였다. 이 워크트리에는
  web 의존성이 없어 `pnpm -C web install --frozen-lockfile`을 먼저 쳤다. pytest를 처음에 `| tail`로 이어 쳤다가 훅이 종료
  코드를 가린다고 짚어, 멈추고 파일로 리다이렉트해 다시 돌렸다.

## 셀프 리뷰

`/code-review`(기준 `2a3964f`, 수정 2·미추적 0, 커밋 0). 소스가 없어 표준 축은 sonnet이다. 명세는 대기열 164 행과
지시문이고, 가드의 실제 동작과 이 세션이 할 일을 리뷰어 참고로 갈라 넘겼다. 두 축 모두 Critical·Major는 없었다. 표준 축은
Minor 1·Nit 3, 명세 축은 Minor 2·Nit 3이었다.

- **고친 것.**
  - 명세 Minor: 가드 문장에 "그 PR에서"라는 한정이 없어 가드가 어떤 PR에서도 코멘트를 세지 않는다고 읽혔다. 끝 문장
    "리뷰도 가드도 돈다"는 옛 "가드도 꺼지므로"와의 대비라, 이제는 그 PR에서 가드가 돌지 않는다고 읽혔다. 둘 다 고쳤다.
  - 명세 Minor: "그 워크플로의 동작을 서술한 다른 문서는 병합 뒤 따로 고친다"가 넓었다. 탐침의 독스트링과 README도 그
    동작을 서술하지만 허용 경로 안이라 같은 PR에 실을 수 있다. "허용 경로 밖의 것"으로 좁혔다.
  - 명세 Nit·표준 Nit(겹침): "(허용 범위는 그 가드 스텝의 주석)"이 판정자를 가리키지 않았다. 주석은 범주만 적고 경로는
    `run:`의 패턴에만 있다. "원천은 그 스텝의 패턴"으로 고쳤다. 대기열 164의 닫힘 메모도 같이.
  - 표준 Nit: "코멘트 0개 가드"는 워크플로에 없는 이름이라 스텝 이름(`Fail when Claude left no comment`)을 붙였다.
  - 명세 Nit: 열린 행 31의 정정 괄호(위 잔존 grep).
  - 표준 Minor(Duplicated Code, 판단 항목)와 표준 Nit(괄호 열거가 "기록"의 오독을 줄인다)이 서로 당겼다. 닫힌 열거
    "기록(일지·대기열·하네스 탐침)"을 "일지·대기열 등"의 예시로 줄이고 원천을 가리키게 했다. 이 줄이 가드의 목록을 그대로
    옮겨 적다 낡은 것이 164였다.
- **남긴 것.**
  - 명세 Nit: 161의 갈래(목록을 얻지 못하면 실패)가 템플릿에 없다. 가드가 실패할 때 스스로 "잡을 다시 돌린다"를 찍고,
    템플릿은 PR을 짤 때 보는 것이라 옮기지 않았다.
  - 표준 Nit: 병합 뒤로 미룬 일을 어디에 적는지가 없다. next-session의 "다음"과 retro가 이미 맡는 일이고, 164의 범위를
    넘는 새 규칙이라 넣지 않았다.
  - 표준 참고: 열린 행 163은 워크플로, `operations.md`, ADR을 한 칸에 적는다. 새 문장대로면 `operations.md`는 워크플로
    PR이 병합된 뒤의 PR이다. 이 diff의 문제가 아니고 163을 할 세션이 템플릿에서 읽는다.
