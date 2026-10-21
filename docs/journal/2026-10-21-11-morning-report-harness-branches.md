# 2026-10-21 (11) 아침 보고가 harness 티켓의 PR도 티켓으로 센다 (ticket-for-every-pr 07)

next-session 지시문으로 연 새 세션이다. 나란히 여는 셋 가운데 셋째라 `tidy-checkouts`는 돌지 않았다. 제목을 브랜치 이름으로 바꾸고, 주 체크아웃에서 브랜치를 따지 않고 워크트리 `.claude/worktrees/07-morning-report-harness-branches`에 들어가 브랜치를 `feature/07-morning-report-harness-branches`로 바꿨다. `implement` 스킬을 따랐다.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/ticket-for-every-pr/issues/07-morning-report-harness-branches.md / 다음 작업: … 아침 보고가 harness 티켓의 PR도 티켓으로 센다. 기능 ticket-for-every-pr의 티켓이고 PR #339로 명세 검토와 티켓 일곱이 병합됐다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 3 중 3. … EnterWorktree(name은 07-morning-report-harness-branches)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 … 이번 요청 범위: PR과 병합까지"

## 한 것

- `tools/morning_collect.py`의 `TICKET_BRANCH`가 `feature/NN-<slug>`에 더해 `chore/NNN-<slug>`도 맞춘다. 전방 탐색으로 접두마다 자릿수를 보고 묶음은 하나로 두어, 부르는 쪽의 `m.group(1)`은 그대로다. 상수 위 주석에 두 모양과 묶음 1이 `ticket_paths`의 열쇠라는 것을 적었다.
- 시험에서 부르려고 `_gather_tickets`를 `gather_tickets`로 공개했다(`gather_limit`, `gather_works`와 같은 결). 이 이름 바꾸기는 동작을 바꾸지 않는 첫 걸음으로 먼저 하고, 그 뒤 시험을 썼다.
- `tests/tools/test_morning_collect.py`에 `ticket_paths`와 `main_text`를 바꿔 끼운 사례 하나를 더했다. `feature/01-a`와 `chore/001-b`는 행이 되고, `chore/c`, `chore/01-a`, `chore/0001-d`, `chore/001-`, `feature/001-e`는 열쇠가 `paths`에 있어도 행이 되지 않는다.
- 빨강을 먼저 봤다. 고치기 전 판에서 그 시험은 `(2, '001-b', 2)`가 빠져 실패했다.

## 검증

- 워크트리 루트에서 `uv run python -m tools.morning_collect --reports <세션 스크래치패드>/reports --day 2026-10-20`을 돌렸다. 첫 시도는 전체 검사 러너와 함께 띄워 `MemoryError`로 종료 1이었다. 같은 때 러너의 pytest(`MemoryError`)와 web-verify(Node의 `process out of memory`)도, Stop 훅의 `python` 띄우기(os error 8)도 메모리 부족으로 실패했다. 나란히 여는 세 세션이 함께 돌던 때다. 단독으로 다시 돌리자 수집은 종료 0으로 끝났고, 러너도 단독으로 다시 돌려 여덟 검사가 모두 Passed였다.
- `gh pr list --state merged --search "head:chore/"` 최근 스물 가운데 머리가 `chore/NNN-`인 PR은 없었다. 그래서 새 행이 실제로 드는지는 보고가 아니라 위 시험이 본다. 명세 축 리뷰가 `ticket_paths(Path('.'))`를 실제로 불러 `001-morning-unusual-ties`가 `.scratch/harness/issues/`에서 찾아지는 것을 봤다. 이 짝은 시험이 바꿔 끼우므로 시험으로는 고정되지 않는다.

## 셀프 리뷰

`/code-review`를 기준 `303e8fb5`, 작업 트리 변경 파일 셋, 커밋 0, 미추적 0으로 돌렸다. 표준 축은 hard 0, Minor 셋, 명세 축은 Major 둘, 경미 둘이었다.

- 고친 것
  - 체크박스를 이르게 닫았다(명세 Major 둘, 표준 Minor). `done` 반영과 일지 항목을 되돌렸다가, 이 일지를 쓰고 `done`으로 바꾼 커밋에서 닫았다.
  - 주석의 "번호 없는 `chore/<slug>`는 규약 전의 하네스 브랜치"가 지금의 `docs/constitution/operations.md` 14행("티켓 밖의 하네스·설정 변경은 `chore/<slug>`")과 어긋났다(표준 Minor). "티켓이 없는 하네스 브랜치"로 고쳤다.
  - 주석의 "묶음 1은 티켓 파일 이름의 stem"이 과했다(명세 경미). ADR 0037이 든 `feature/09-human-verification-checks`처럼 이름이 다르면 맞지 않는다. 새 문장: "규약대로 지은 브랜치면 그 값이 티켓 파일 이름의 stem이고, 이름이 다르면 티켓 파일을 찾지 못한 행이 된다."
  - 경계 입력 셋(`chore/0001-d`, `chore/001-`, `feature/001-e`)을 시험에 더했다(표준 Minor).
- 남긴 것
  - 명세 97줄의 "이미 있는 시험을 넓힌다"는 전제와 달리, 기점의 시험 파일에는 티켓 브랜치 맞춤 시험이 없어 새로 썼다(명세 범위 넘침 지적). 결과는 명세가 요구한 사례와 같아 고치지 않았다.
  - 독스트링이 아니라 상수 주석에 적었다. 상수에는 독스트링이 없고 티켓이 "상수나 함수"를 허용한다(두 축 모두 충족으로 봤다).
- 다시 돌린 명령: 새 시험 단독은 초록이었다. 손으로 치는 다섯은 커밋 `bf5e2b4a`의 pre-commit으로 갈음했다. ruff 둘과 러너 여덟(pytest 414.6s, web-verify 291.9s)이 모두 Passed였고, 카나리아 명세와 헌법 판은 대상 파일이 없어 Skipped였다.

PR 직전 리뷰에 밀 주장은 위 고친 것의 새 문장이다.
