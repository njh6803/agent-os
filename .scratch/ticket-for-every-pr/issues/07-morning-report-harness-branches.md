# 07: 아침 보고가 harness 티켓의 PR도 티켓으로 센다

**What to build:** 아침 보고의 티켓 절(병합된 티켓 PR마다 수락 조건 수, 비용, 인계를 한 행에 적는 표)에 `chore/NNN-<slug>` 브랜치의 PR도 그 harness 티켓(`.scratch/harness/issues/NNN-<slug>.md`)과 맞춰 든다. 지금은 `feature/NN-<slug>`만 맞춰, 이 기능 뒤의 하네스 일은 티켓이 있어도 그 절에 나오지 않는다. 번호 없는 `chore/<slug>`(규약 전의 브랜치)는 지금처럼 맞추지 않는다.

근거는 `.scratch/ticket-for-every-pr/spec.md` "바뀌는 문서와 스킬"의 `tools/morning_collect.py` 항목과 Testing Decisions의 "아침 보고 도구"다. 결정은 ADR 0037이다. 짝인 `tools/morning_sources.py`의 `ticket_paths`는 `.scratch` 아래 `/issues/`의 stem으로 찾으므로 harness 티켓도 그대로 찾는다(명세가 코드를 읽었다).

**Blocked by:** None (can start immediately)

**Status:** in-progress

### 도구

- [x] **`tools/morning_collect.py`의 `TICKET_BRANCH`**가 `chore/NNN-<slug>`(세 자리 번호)도 맞추고, 맞춘 브랜치에서 티켓 파일 이름의 stem(`NNN-<slug>`)을 꺼내 `ticket_paths`의 열쇠로 쓴다. `feature/NN-<slug>`의 동작은 그대로다
- [x] 그 상수나 그것을 쓰는 함수의 독스트링에 두 브랜치 모양과 stem이 열쇠라는 것을 적는다

### 시험

- [x] `tests/tools/test_morning_collect.py`에 사례를 더한다. `chore/NNN-<slug>` 브랜치의 병합된 PR이 harness 티켓과 맞춰져 티켓 행에 드는 것, `chore/<slug>`(번호 없음)가 맞춰지지 않는 것, 기존 `feature/NN-<slug>` 사례가 그대로인 것
- [x] **빨강을 먼저 본다.** 지금 도구로 `chore/NNN-<slug>` 사례가 빨간 것을 본다

### 검증

- [ ] 이 워크트리에서 아침 보고 수집을 한 번 돌려 오류 없이 끝나는 것을 본다. `tools/morning_tasks/common.md`의 명령은 `--directory`로 주 체크아웃을 가리켜 그대로 치면 주 체크아웃의 도구가 돈다. 그래서 워크트리 루트에서 `--directory` 없이 `uv run python -m tools.morning_collect --reports <폴더> --day <어제>`로 친다. `--reports`는 세션 스크래치패드의 폴더로 주어 사람의 보고 폴더를 덮지 않는다. 수집은 몇 분 걸리므로 Bash의 `timeout`을 600000으로 주고, 10분을 넘겨 백그라운드로 넘어가면 다시 치지 않고 끝 알림을 기다린다(`common.md`의 수집 단계. 다시 치면 수집이 둘 돌아 서로 느려진다). 이 티켓을 쓸 때 main에는 `chore/NNN-` 브랜치로 병합된 PR이 없었으므로(#335의 머리는 `chore/morning-report-followup`이었다, `gh pr view`로 손으로 봤다), 그때까지 없으면 새 행이 실제로 드는지는 시험이 본다고 일지에 적는다
- [ ] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣고, PR을 열기 전에 `done`으로 바꾼다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다
