# 07: 새 하네스 티켓을 제목으로 부르고 브랜치는 chore/<제목>이다

**What to build:** 새 하네스 티켓은 번호를 받지 않고 `.scratch/harness/issues/<slug>.md`로 쓰며, 첫 줄은 `# <slug>: <제목>`, 브랜치는 `chore/<slug>`, 커밋과 PR 제목의 꼬리는 `(harness <slug>)`다. 티켓 이름만 보고 무엇을 하는 티켓인지 안다. 옛 티켓 45장은 번호를 지킨다. 커밋 검사는 `chore/` 뒤의 글자를 그대로 티켓 파일의 stem으로 보아 옛 꼴 `chore/045-ci-python-runner-pin`과 새 꼴 `chore/<slug>`를 같은 규칙 하나로 맞댄다. next-session 지시문과 implement·retro에서 번호를 받고 다시 치는 단계가 사라지고, 지시문을 내는 세션이 slug를 짓는다. 번호 대조 도구는 티켓 번호를 보지 않아, 커밋 직전의 번호 대조가 번호로는 ADR 번호와 헌법 판만 본다. 전환 때의 마지막 번호보다 큰 번호로 시작하는 티켓은 저장소 상태 시험이 막는다.

근거는 `.scratch/retro-queue-per-item/spec.md`의 "티켓 이름", "전환일과 고정하는 값"의 티켓·다시 합칠 때·못 보는 것, "저장소 상태 시험의 실패 문장"의 티켓, "바뀌는 자리"의 티켓 이름, Testing Decisions의 "커밋 검사"·"번호 대조 도구"·"저장소 상태 시험"·"훅"·"스킬과 규칙"·"변이 표", Further Notes의 "헌법 판을 올리는 티켓"과 "전환기의 세션", 사용자 스토리 14·29·30·32·34·36이다. 결정은 ADR 0045 결정 6, 8의 티켓 몫, 10의 티켓 상태 시험이다. 이 티켓이 병합되면 ADR 0037 이력 2026-11-06의 자리와 번호·브랜치·번호 겹침의 알림과, ADR 0045 이력 2026-11-06의 티켓 상수·티켓 실패 문장·판 올리기가 선다.

**Blocked by:** 06 (헌법 README)

**Status:** done

### 시작할 때

- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다
- [x] 명세 "바뀌는 자리"의 티켓 이름 목록을 `git grep`으로 다시 대 본다. 이 티켓이 든 수는 명세가 센 것이고, 근거의 종류는 명세가 그 수를 적은 자리에 있다(따로 적지 않은 수는 6f205c0e에서 조사 서브에이전트가 읽고 센 것이다, 명세 서두). 명세의 수(옛 티켓 045까지, 번호 대조 도구의 티켓 사례 스물, 변이 마흔다섯)는 6f205c0e의 것이라 그때의 수를 다시 센다. 목록 밖에서 찾은 자리는 PR 본문에 적는다

### 커밋 검사

- [x] `tools/check_ticket.py`가 `chore/` 뒤의 글자를 그대로 stem으로 보고 `.scratch/harness/issues/<stem>.md`가 이 브랜치의 변경에 있는지 본다. 세 자리 숫자를 요구하던 갈래(지금 `chore/<slug>`를 막는다)를 걷는다. `docs/` 브랜치에서 harness 티켓을 세는 판정과 CI의 done 판정도 같은 규칙이다. 판정 문장과 막는 글의 할 일(번호를 받는 명령 대신 slug를 짓는 규칙)을 고친다
- [x] slug 규칙은 대기열 항목과 같다(영어 소문자로 시작). 숫자 세 자리와 하이픈으로 시작하는 slug는 옛 꼴로 읽힌다

### 번호 대조 도구와 아침 보고

- [x] `tools/sibling_overlap.py`에서 티켓 번호의 읽기·겹침·다음 빈 번호·누가 옮기나·브랜치 이름 바꾸기와 원격 명령을 뗀다. ADR 번호 겹침의 `--move`와 PR 본문 옮기기는 남긴다(ADR 0045 결정 8. 통째로 걷는 안은 명세의 거부한 안이다)
- [x] `tools/morning_collect.py`의 브랜치 맞춤이 세 자리 번호를 요구하지 않고 `chore/<stem>`을 받는다. 번호 없는 `chore/<slug>`를 티켓이 없는 하네스 브랜치로 적은 곁 주석을 고친다(뜻이 뒤집힌다)
- [x] `tools/hook_prompt_directive.py`의 첫 턴 알림에서 티켓 번호를 받으라는 줄을 고친다

### 저장소 상태 시험

- [x] **최대 번호 상수.** `tests/test_harness_ticket_names.py`가 번호 하나를 상수로 고정하고, 그보다 큰 번호로 시작하는 티켓을 빨갛게 한다. 상수는 이 PR이 마지막으로 origin/main을 합친 때의 가장 큰 `NNN`이다(6f205c0e에서 045). main을 다시 합치면 그때의 값으로 옮긴다. 상수보다 큰 번호가 main에 들어오면 이 시험이 빨개져 옮길 때를 알린다. 지금의 번호 중복 판정은 남는다
- [x] **실패 문장.** 명세 "저장소 상태 시험의 실패 문장"의 티켓 뜻대로 그 이름과 상수, 새 꼴(`<slug>.md`, `chore/<slug>`), 원천(`docs/agents/issue-tracker.md`), 파일·브랜치·세션 제목에서 번호를 떼라는 할 일을 든다. 시험이 그 뜻을 단언한다

### 시험

- [x] `tests/tools/test_check_ticket.py`에서 `chore/<slug>`가 그 티켓을 실은 커밋으로 지나고 빠뜨린 커밋으로 막히는 사례, 옛 꼴 `chore/NNN-<slug>`가 그대로 지나는 사례, harness 폴더에서 티켓이 아닌 모양(`issues/` 바로 아래의 `.md`가 아닌 파일과 `issues/README.md`. 지금 판정 6이 티켓이 아니라고 적는다)이 티켓으로 세지지 않는 사례를 진짜 `git commit`과 `--ci`로 본다
- [x] `tests/tools/test_sibling_overlap.py`의 티켓 사례를 걷고, 남는 것(ADR 번호와 그 `--move`, 헌법 판, 카나리아, 없는 인용, 함께 고친 파일)이 초록인지 본다
- [x] `tests/tools/test_hook_prompt_directive.py`(알림과 원문 대조)와 `tests/tools/test_morning_collect.py`(`chore/c`가 맞지 않는다는 단언이 뒤집힌다)를 고친다. 첫 턴 알림은 실제 입력 표(`tools/hook_payloads.toml`)를 `tools/run_hooks.py`로 돌린다
- [x] **빨강을 먼저 본다.** 바꾸기 전의 커밋 검사로 `chore/<slug>` 커밋 사례가 빨간 것을 본다(원칙 II)

### 스킬과 문서

- [x] `next-session` directive.md(다음 작업 틀의 티켓 경로, "1. 티켓 번호" 단계)와 SKILL.md(결정표의 chore 브랜치), `code-review`(chore 브랜치의 티켓 경로), `retro`(다음 번호의 새 harness 티켓, 다시 치기), `implement`(chore 브랜치, 번호를 받은 뒤 다시 치기), `sync-design-system` upload.md(티켓 모양의 브랜치)를 고친다
- [x] `docs/agents/issue-tracker.md`(자리·번호·머리·브랜치·다음 번호의 새 티켓, 커밋과 PR 제목의 꼬리 `(harness <slug>)`), `.github/PULL_REQUEST_TEMPLATE.md`(주석의 티켓 경로), `CLAUDE.md`(환경 함정의 커밋 전 대조에서 티켓 몫. 02·04와 이 티켓으로 그 문장은 ADR 번호와 헌법 판만 남는다)를 고친다
- [x] `docs/constitution/operations.md`(harness 티켓의 브랜치)를 고치고 헌법 판을 올린다. 06 뒤의 규칙대로 판 줄만 올리고 까닭은 그 변경의 ADR 이력이나 일지에 적는다
- [x] 런북 `KICKOFF.md`(첫 턴 알림의 번호 명령, 번호 대조의 서술)를 고친다
- [x] 고친 뒤 옛 표현(`티켓 NNN`의 다음 빈 번호, `chore/NNN-<slug>`만 받는 문장)을 저장소 전체에서 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4). 옛 티켓 45장의 이름은 기록이라 둔다

### 카나리아, 변이 표, 페이로드

- [x] 카나리아 명세 `implement_ticket_status`를 고치고, 바꾼 스킬을 새 `claude -p` 세션에서 불러 본다. 바꾼 스킬 본문(`.claude/skills/*/*.md`), 규칙(`.claude/rules/*.md`), 서브에이전트(`.claude/agents/*.md`)마다 그 경로를 `source`로 든 카나리아 명세를 하나 이상 고친다. 번호 대조 도구의 카나리아 검사가 파일마다 보고, 그 경로를 원천으로 든 명세가 없으면 새로 둔다. 위에 이름을 든 명세는 그 예다
- [x] 변이 표 `sibling_overlap_mutations.toml`의 티켓 변이(셋은 티켓 이름 시험을 고친다), `.scratch/ticket-for-every-pr/probes/prompt_directive_mutations.toml`의 번호 명령 변이, `check_ticket_mutations.toml`의 판정 5·6 맞대기를 고치고 `tools/mutate.py`로 다시 돌린다. `tools/hook_payloads.toml`의 첫 턴 알림 사례를 고친다

### 검증

- [x] PR을 열기 전에 이 티켓의 `Status:`를 `done`으로 바꾼다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다
