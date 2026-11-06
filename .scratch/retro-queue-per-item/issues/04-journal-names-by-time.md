# 04: 일지를 날짜·시각·제목으로 짓고 번호를 받지 않는다

**What to build:** 새 일지는 `docs/journal/2026-11-06-1432-<슬러그>.md`처럼 그 세션이 일지를 만든 로컬 시분을 넣어 짓는다. 세션은 번호 도구를 치지 않고 `date +%Y-%m-%d-%H%M`로 앞부분을 짓고, 먼저 만들고 늦게 병합해도 이름을 옮기지 않는다. 이어서 할 때는 이 브랜치가 더한 일지를 git으로 찾아, main을 합친 뒤 들어온 남의 일지와 섞이지 않는다. 아침 보고는 main에 가장 늦게 더해진 일지 가운데 `## 다음`을 든 첫 일지를 쓴다. 옛 인용 "일지 2026-10-19-21"과 새 인용 "일지 2026-11-06-1432"가 같은 접두 규칙으로 풀린다. 번호 대조 도구는 일지 순번을 보지 않고, 일지 훅은 새 일지의 이름이 새 꼴인지만 본다. 전환일 뒤에 순번 꼴로 만든 일지와, 같은 분에 만든 두 일지는 저장소 상태 시험이 막는다.

근거는 `.scratch/retro-queue-per-item/spec.md`의 "일지 이름", "인용을 푸는 규칙"의 일지, "전환일과 고정하는 값"의 일지·다시 합칠 때·못 보는 것, "저장소 상태 시험의 실패 문장"의 일지, "바뀌는 자리"의 일지 이름, Testing Decisions의 "번호 대조 도구"·"저장소 상태 시험"·"훅"·"아침 보고"·"스킬과 규칙"·"변이 표", Further Notes의 "헌법 판을 올리는 티켓"과 "전환기의 세션", 사용자 스토리 13·27·28·30·32·34·36이다. 결정은 ADR 0045 결정 7, 8의 일지 몫, 10의 일지 상태 시험이다. 이 티켓이 병합되면 ADR 0045 이력 2026-11-06의 최신 일지·일지 이름의 겹침·일지 상수·일지 실패 문장·판 올리기가 선다.

**Blocked by:** 02 (대기열 분할). 03(리뷰 봇 경로 거르기)과 나란히 연다

**Status:** ready-for-agent

### 시작할 때

- [ ] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다
- [ ] 명세 "바뀌는 자리"의 일지 이름 목록을 `git grep`으로 다시 대 본다. 이 티켓이 든 수는 명세가 센 것이고, 근거의 종류는 명세가 그 수를 적은 자리에 있다(따로 적지 않은 수는 6f205c0e에서 조사 서브에이전트가 읽고 센 것이다, 명세 서두). 명세의 수(일지 수, 순번을 쓰는 자리)는 6f205c0e의 것이라 그때의 수를 다시 센다. 목록 밖에서 찾은 자리는 PR 본문에 적는다

### 이름과 최신 일지

- [ ] **이름.** `docs/journal/<YYYY-MM-DD>-<HHMM>-<슬러그>.md`이고 시각은 그 세션이 일지를 만든 로컬 시분이다. 다음 빈 번호를 보라던 문장(`tools/hook_choice_facts.py`, `tools/hook_prompt_directive.py`의 붙여 넣은 지시문 갈래, `code-review`, `next-session` merge.md)과 번호 규칙대로 만들라던 `next-session` handoff.md가 `date +%Y-%m-%d-%H%M`을 가리킨다
- [ ] **이 브랜치의 일지.** `git diff --merge-base origin/main --name-only --diff-filter=A -- docs/journal/`에 커밋하지 않은 새 일지(`git status --porcelain -- docs/journal/`)를 더한 것이고, 여럿이면 이름의 날짜·시각이 가장 늦은 것이다. 다음 일을 잇는 세션과 retro(`## 회고` 절을 쓸 일지)가 쓴다. `retro`의 최신 일지 두 곳을 이것으로 고친다
- [ ] **main의 최신 일지.** origin/main에 가장 늦게 더해진 일지다. 아침 보고(`tools/morning_sources.py`)는 늦게 더한 커밋부터, 한 커밋 안에서는 이름이 늦은 것부터 읽어 `## 다음`을 든 첫 일지를 쓴다. 이름순으로 고르지 않는다(전환일 하루는 옛 이름과 새 이름이 이름순과 시각순에서 어긋난다)
- [ ] **인용.** `일지 <날짜>-<NN 또는 HHMM>`은 `docs/journal/<인용>-*.md`로 푼다. 접두 뒤의 하이픈이 `2026-11-06-14`와 `2026-11-06-1432-…`를 가른다. 이 규칙을 `docs/constitution/operations.md`의 일지 규칙에 적는다. 새 CLI는 두지 않는다

### 번호 대조 도구

- [ ] `tools/sibling_overlap.py`에서 일지 순번의 읽기·겹침·다음 빈 번호·앞섬(이름순)·옮길 번호와 머리 한 줄 파일 안내를 떼고, 빈 자리 검사에서 일지를 뗀다. 없는 일지 인용 검사(종료 1의 한 갈래)는 남기고 위 인용 규칙으로 두 꼴을 모두 읽는다
- [ ] 02 뒤의 다음 빈 번호 줄(`일지 X, 티켓 NNN`)에서 일지 몫이 빠진다. 그 줄을 읽던 일지 훅은 아래에서 순번 대조를 걷으므로 기댈 것이 사라진다. 훅 러너(`tools/run_hooks.py`)의 `${TODAY}`·`${NUMBERED_REPO}` 설명과 번호 저장소를 함께 고친다

### 일지 훅

- [ ] `tools/hook_journal_retro.py`의 순번 대조(번호 도구를 자식 프로세스로 돌리는 몫)를 걷고, 일지를 Write할 때 이름이 새 꼴인지만 본다. retro 계기는 그대로다
- [ ] 새 훅을 지은 뒤 그 훅의 실행 시간을 손으로 재어(명령과 결과를 일지에 적는다) `.claude/settings.json`의 등록 제한(지금 45초)과 `.claude/rules/tools.md`의 그 항목을 다시 정한다. 명세가 이 측정을 이 티켓에 넘겼다

### 상태 시험

- [ ] **새 꼴.** `tests/test_journal_names.py`가 새 꼴 이름을 받고, 상수 날짜 뒤 날짜의 순번 꼴 일지를 빨갛게 한다. 상수는 이 PR이 마지막으로 origin/main을 합친 날(로컬 날짜)이다. 세션이 main을 다시 합칠 때마다 상수를 그날로 옮긴다(날짜는 알리는 시험이 없다). 지금 시험의 순번 규약 전 이름 목록과 같은 자리의 상수다
- [ ] **이름의 겹침.** `<날짜>-<HHMM>` 앞부분이 겹치는 일지 둘을 빨갛게 한다. 옛 꼴 일지의 순번 겹침 판정도 남는다. 늦게 병합되는 PR이 main을 합친 뒤의 CI에서 막혀 그 세션이 분을 바꾸고 이 브랜치가 들인 인용을 고친다
- [ ] **실패 문장.** 명세 "저장소 상태 시험의 실패 문장"의 일지 뜻대로 무엇이 틀렸는지(전환일 뒤의 순번 꼴, 또는 같은 앞부분), 새 꼴과 짓는 명령, 원천(`docs/constitution/operations.md` 일지 규칙), `git mv`와 인용을 고치라는 할 일을 든다. 시험이 그 뜻을 단언한다

### 시험

- [ ] `tests/tools/test_sibling_overlap.py`에서 일지·순번·이름순 사례와 일지 꼴을 예로 쓴 옮기기 사례를 걷거나 다른 꼴로 옮긴다. merge-base에 순번 일지가 없어도 2로 끝나지 않는 사례와, 일지 인용 `2026-11-06-14`가 `2026-11-06-1432-…`에 맞지 않는 사례를 더한다
- [ ] `tests/tools/test_hook_journal_retro.py`(순번 시험을 이름 꼴 시험으로), `tests/tools/test_hook_choice_facts.py`, `tests/tools/test_run_hooks.py`(번호 저장소 모양)를 고친다. 훅은 순수 함수 시험과 실제 입력 표(`tools/hook_payloads.toml`의 순번 대조 두 사례, choice_facts 사례)를 `tools/run_hooks.py`로 돌린다
- [ ] **아침 보고.** 임시 git 저장소에 `origin/main` ref를 두고, 가장 늦게 더한 일지에 `## 다음`이 없으면 그 앞의 일지를 고르는 사례와, 같은 날 옛 이름 일지(`-12-`)보다 늦은 커밋이 더한 새 이름 일지(`-0930-`)를 고르는 사례를 본다
- [ ] **빨강을 먼저 본다.** 바꾸기 전의 시험과 도구로 새 꼴 일지 이름 사례가 빨간 것을 본다(원칙 II)

### 스킬, 문서, 런북

- [ ] `next-session` merge.md와 handoff.md, `code-review`, `retro`를 위 이름과 최신 일지로 고친다
- [ ] `CLAUDE.md`(지도의 `docs/journal/` 행, 환경 함정의 커밋 전 대조에서 일지 몫), `README.md`(형제 번호 대조 문구), `docs/constitution/operations.md`(일지 규칙 문장)를 고치고 헌법 판을 올린다(번호 대조 도구가 내는 형제 판보다 높게)
- [ ] 런북 `KICKOFF.md`(첫 일지 이름, 일지 훅의 순번 계기, 번호 대조의 서술), `kickoff/runner.md`, `kickoff/claude-md-template.md`를 고친다. 새 프로젝트의 첫 일지 이름은 `<날짜>-<HHMM>-kickoff.md`다
- [ ] 고친 뒤 옛 표현(일지의 다음 빈 번호, 순번 규칙, 이름순 최신 일지)을 저장소 전체에서 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4)

### 카나리아, 변이 표, 프로브

- [ ] 카나리아 명세 `next_session_number_body_batch`를 고치고, 바꾼 스킬을 새 `claude -p` 세션에서 불러 본다. 바꾼 스킬 본문(`.claude/skills/*/*.md`), 규칙(`.claude/rules/*.md`), 서브에이전트(`.claude/agents/*.md`)마다 그 경로를 `source`로 든 카나리아 명세를 하나 이상 고친다. 번호 대조 도구의 카나리아 검사가 파일마다 보고, 그 경로를 원천으로 든 명세가 없으면 새로 둔다. 위에 이름을 든 명세는 그 예다
- [ ] 변이 표 `journal_names_mutations.toml`, `journal_number_and_guards_mutations.toml`의 순번 몫, `existing_hook_fixes_mutations.toml`의 순번 셋, `choice_facts_hook_mutations.toml`의 원문 인용, `sibling_overlap_mutations.toml`의 일지 몫을 고치고 `tools/mutate.py`로 다시 돌린다
- [ ] 프로브 `journal_number_hook/run.py`, `guard_hooks_time.py`, `journal_cite_scan.py`, `sibling_overlap_merge_cost.sh`, `mutate_231/measure.sh`와 두 프로브 README의 해당 행을 고친다. `.scratch/harness/probes/README.md`에서 04가 고치는 `journal_cite_scan.py` 행과 03이 고치는 `review_workflow.py` 행이 바로 붙어 있어(지금 103·104행), 나란히 돌면 늦게 병합되는 쪽이 main을 합치며 글자 충돌을 풀고 두 행을 모두 남긴다

### 열린 항목

- [ ] 열린 항목 439·476·569는 이 조각으로 할 일이 사라져 닫을 후보다. 그때 다시 읽어 이 PR에서 닫을 것을 가리고, 그 목록을 PR 본문에 적는다

### 검증

- [ ] PR을 열기 전에 이 티켓의 `Status:`를 `done`으로 바꾼다
- [ ] 원칙 III를 지킨다
- [ ] 검증 명령이 모두 초록이다
