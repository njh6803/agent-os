# 01: 하네스를 더하는 문턱과 만료 보호선이 다섯 번째로 오른다

**What to build:** 회고가 새 검사·훅·지침 문장·`CODING_STANDARDS.md`의 줄을 더하는 문턱이 같은 실수의 세 번째에서 다섯 번째로 오른다. 손상이 한 번 났을 때 더하는 것과 고침(버그, 틀린 사실, 깨진 경로)을 사건 하나로 하는 것은 그대로다. `uv run python tools/queue_open_rows.py`가 회차 5 이상인 열린 항목을 chore 계기로 묶고, 만료 후보에서 빼는 보호선도 회차 5다. 아침 보고의 이름표도 그 수를 따른다. retro·next-session 스킬, `CLAUDE.md`, `CODING_STANDARDS.md`, 런북의 문턱 문장이 모두 다섯을 말하고, 열린 대기열 항목에서 더하는 문턱을 뜻하던 "세 번째"도 다섯 번째가 된다. 끝이 열린 결함 종류의 "세 번째 사례부터"는 셋 그대로다.

근거는 `.scratch/retro-queue-per-item/spec.md`의 "회차 다섯", "바뀌는 자리"의 회차 다섯, "차례", Testing Decisions의 "빨강을 먼저 본다"·"스킬과 규칙"·"변이 표", 사용자 스토리 5·6·34·36이다. 결정은 ADR 0045 결정 2와 ADR 0036 이력 2026-11-06이다. 이 티켓이 병합되면 ADR 0036 그 이력의 문턱·계기·보호선·옛 문구가 선다("행은 항목 파일이다"는 02가 세운다).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 시작할 때

- [ ] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다
- [ ] 명세 "바뀌는 자리"의 회차 다섯 목록을 `git grep`으로 다시 대 본다. 이 티켓이 든 수는 명세가 센 것이고, 근거의 종류는 명세가 그 수를 적은 자리에 있다(따로 적지 않은 수는 6f205c0e에서 조사 서브에이전트가 읽고 센 것이다, 명세 서두). 명세의 수는 6f205c0e의 것이라 그때의 수를 다시 센다(명세 Further Notes "수의 기준"). 목록 밖에서 찾은 자리는 PR 본문에 적는다

### 도구

- [ ] `tools/queue_open_rows.py`의 상수(`MIN_ROUNDS`) 하나를 5로 바꿔 chore 계기와 만료 보호선이 함께 바뀐다. 독스트링의 "회차 3"도 고친다. 쓰임 문구(`USAGE`)에는 회차가 없고, 출력의 회차 줄은 상수를 따른다
- [ ] 아침 보고(`tools/morning_collect.py`)의 대기열 절과 이름표는 코드가 그 상수를 따른다. 그 독스트링의 "3회차 이상"과 작업 지시(`tools/morning_tasks/environment.md`)의 "(3회차 이상)"은 고정 글이라 손으로 5로 고친다

### 문장

- [ ] 명세 "바뀌는 자리"의 스킬·지침·런북·그 밖(`retro`, `next-session`, `CLAUDE.md`의 교정 루프와 지도의 `CODING_STANDARDS.md` 행, `CODING_STANDARDS.md` 판단 기준의 머리, `KICKOFF.md`, `kickoff/claude-md-template.md`, `.scratch/morning-report-split/design.md`)의 더하는 문턱과 회차 수를 다섯으로 고친다
- [ ] 끝이 열린 결함 종류의 "세 번째 사례부터"와 `retro_threshold_and_expiry`가 든 "가장 큰 회차에 하나를 더한 값"은 그대로 둔다(ADR 0036 이력 2026-11-06 "끝이 열린 결함 종류의 수는 셋 그대로다")
- [ ] 고친 뒤 옛 표현을 저장소 전체에서 grep해, 살아 있는 문서에 남은 것이 셋 그대로 두는 자리뿐인지 본다. 일지, 닫힌 항목, ADR의 지난 이력은 기록이다(`CLAUDE.md` 작업 규약 4)

### 열린 항목의 옛 문구

- [ ] 그때의 옛 표(`.scratch/retro-queue.md`. 이 티켓은 분할 전이다)에서 "세 번째"를 담은 열린 항목(07d80b96에서 43개)과 숫자로 문턱을 적은 467·468·565·579를 하나씩 읽는다. 더하는 문턱을 뜻하는 것만 다섯 번째로 고치고 다른 뜻은 둔다. 고친 목록과 둔 목록을 PR 본문에 적는다(ADR 0036 이력 2026-11-06 "열린 항목의 옛 문구"). 닫힌 항목은 기록이라 고치지 않는다

### 만료

- [ ] 상수를 바꾼 도구를 그날의 `--today`로 돌려 만료 후보를 일지와 PR 본문에 적는다. 명세는 2026-11-06에 435 하나를 셌다. 다르면 그 차이와 까닭을 함께 적는다. 후보를 만료로 닫는 일은 retro가 만료 문단대로 한다

### 시험

- [ ] `tests/tools/test_queue_open_rows.py`의 "회차 3 이상"과 3회차 경계 단언을 5로 옮긴다. 회차 4 항목은 승인 칸의 가장 늦은 날짜(도구의 만료 규칙)가 14일 넘게 지나면 만료 후보가 되고, 회차 5 항목은 되지 않는 사례를 둔다
- [ ] `tests/tools/test_morning_collect.py`의 4회차 표 행(문턱이 다섯이 되면 표에서 빠진다)과 `tests/tools/test_morning_report.py`의 픽스처 글 "대기열 3회 이상 행"을 이름표를 따라 고친다
- [ ] **빨강을 먼저 본다.** 상수를 바꾸기 전의 도구로 회차 4 항목의 만료 사례가 빨간 것을 본다(원칙 II)

### 카나리아와 변이 표

- [ ] 카나리아 명세 `claude_md_addition_threshold`, `claude_md_retro_self_approve`, `retro_threshold_and_expiry`(문턱 문장만)를 고치고, 바꾼 스킬과 지침을 새 `claude -p` 세션에서 불러 본다(`docs/constitution/operations.md` 환경 규약 상세)
- [ ] 바꾼 스킬 본문(`.claude/skills/*/*.md`), 규칙(`.claude/rules/*.md`), 서브에이전트(`.claude/agents/*.md`)마다 그 경로를 `source`로 든 카나리아 명세를 하나 이상 고친다. 번호 대조 도구의 카나리아 검사가 파일마다 보고, 그 경로를 원천으로 든 명세가 없으면 새로 둔다. 위에 이름을 든 명세는 그 예다(이 티켓에서는 `next-session` SKILL.md의 회차 문장도 든다)
- [ ] `queue_open_rows_mutations.toml`의 회차 비교와 기대 출력을 고치고 `tools/mutate.py`로 다시 돌린다

### 검증

- [ ] PR을 열기 전에 이 티켓의 `Status:`를 `done`으로 바꾼다
- [ ] 원칙 III를 지킨다
- [ ] 검증 명령이 모두 초록이다
