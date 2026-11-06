# 02: 대기열이 항목마다 파일 하나인 폴더가 된다

**What to build:** 회고 반영 대기열이 표 하나(`.scratch/retro-queue.md`)가 아니라 `.scratch/retro-queue/` 폴더의 항목 파일이 된다. 옛 항목은 `0573.md`처럼 번호를 네 자리로 채운 이름이고, 새 항목은 retro가 지은 영어 제목의 파일(`coderabbit-inline-size.md`)이다. 파일 머리에 `**상태:**`, `**어디로:**`, `**승인:**` 줄이 있고, 닫을 때는 상태 줄 하나를 고친다. 그래서 두 브랜치가 서로 다른 항목을 더하면 부딪히지 않는다. `uv run python tools/queue_open_rows.py`는 지금처럼 열린 항목과 회차·만료 후보를 한 번에 내고, `--search`는 맞은 항목의 파일 경로를 찍는다. 아침 보고의 대기열 절은 이행 전과 같은 수와 이름을 보인다. 지난 글의 "대기열 573" 인용은 글자 그대로 두고 `0573.md`로 풀린다. 번호 대조 도구는 대기열 번호를 보지 않는다. 옛 파일이 다시 생기거나, 라벨 줄이 빠진 항목이나 이름이 규칙 밖인 항목이 생기면 저장소 상태 시험이 막는다.

근거는 `.scratch/retro-queue-per-item/spec.md`의 "대기열 분할", "인용을 푸는 규칙"의 대기열, "전환일과 고정하는 값"의 대기열·다시 합칠 때, "저장소 상태 시험의 실패 문장"의 대기열, "바뀌는 자리"의 대기열 분할, "차례"의 셋째 글머리표, Testing Decisions의 "대기열 도구"·"번호 대조 도구"·"커밋 검사"·"저장소 상태 시험"·"훅"·"아침 보고"·"스킬과 규칙"·"변이 표", Further Notes의 "헌법 판을 올리는 티켓", 사용자 스토리 1~4·6·17·19~22·30·32·34·36·37이다. 결정은 ADR 0045 결정 1, 8의 대기열 몫, 9, 10의 대기열 몫이다. 이 티켓이 병합되면 ADR 0036 이력 2026-11-06의 "행은 항목 파일이다", ADR 0037 이력 2026-11-06의 "대기열을 가리키는 법"(네 자리 번호와 슬러그), ADR 0045 이력 2026-11-06의 대기열 상수·대기열 실패 문장·판 올리기가 선다.

이 티켓은 크다(명세의 고칠 자리 목록에서 가장 크다). 한 세션에 다 못 하면 인계로 이어 간다.

**Blocked by:** 01 (회차 다섯)

**Status:** done

### 시작할 때

- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다
- [x] 명세 "바뀌는 자리"의 대기열 분할 목록을 `git grep`으로 다시 대 본다. 이 티켓이 든 수는 명세가 센 것이고, 근거의 종류는 명세가 그 수를 적은 자리에 있다(따로 적지 않은 수는 6f205c0e에서 조사 서브에이전트가 읽고 센 것이다, 명세 서두). 명세의 수(표 행, 열림·닫힘, 가장 큰 번호, 살아 있는 문서의 "대기열 행")는 6f205c0e나 07d80b96의 것이라 그때의 수를 다시 센다. 목록 밖에서 찾은 자리는 PR 본문에 적는다

### 항목 파일과 폴더 README

- [x] **항목 파일의 모양.** 첫 줄 `# <ID>: <머리 한 문장>`(ID는 파일 이름의 stem), 그 아래 `**상태:**`, `**어디로:**`, `**승인:**` 줄이 이 차례로 있고, 빈 줄 뒤에 본문이 온다. 상태 값은 `열림`, `닫힘 (…)`, `만료 <날짜>` 셋이다. 옛 표의 칸은 명세 "대기열 분할"의 첫 글머리표대로 옮긴다(무엇 칸의 첫 문장이 머리, 나머지가 본문, 취소선과 굵은 닫힘 표지는 상태 줄)
- [x] **새 항목의 제목.** 영어 소문자·숫자·하이픈이고 영어 소문자로 시작한다. 한번 정한 제목은 바꾸지 않는다
- [x] **폴더 README.** 옛 머리말의 규칙(승인 칸 꼴, 닫힘 꼴, 식별자 영구, 넷으로 짧게, 기본 반영 자리)과 파일 모양, 제목 규칙, 인용을 푸는 규칙을 `.scratch/retro-queue/README.md`에 둔다. 색인은 두지 않는다

### 이행

- [x] 옛 표를 폴더로 옮기는 스크립트는 이 세션이 한 번 돌리고 저장소에 남기지 않는다. 돌린 뒤 항목 수, 열림·닫힘 수, 번호 집합이 옛 표와 같은지 세어 일지와 PR 본문에 적는다. 수는 같아도 필드가 틀릴 수 있어(승인 칸의 회차가 바뀌면 다음 사건을 잘못 센다), 열린 항목과 회차를 이은 항목은 상태·어디로·승인 줄이 옛 칸의 글자와 같은지 항목마다 맞대고, 맞댄 방법과 결과를 함께 적는다
- [x] 이 PR이 마지막으로 origin/main을 합친 뒤 그 main의 옛 표와 다시 맞대어 적는다. main이 그 사이 옛 표의 행을 더하거나 고쳤으면 한쪽은 고치고 한쪽은 지운 충돌이 나고, 지우는 쪽으로만 풀면 그 몫이 조용히 빠진다. 그 몫을 항목 파일로 옮긴다

### 열린 목록 도구와 인용

- [x] `tools/queue_open_rows.py`가 폴더를 읽는다. `--queue`는 폴더를, `--ref <커밋>`은 그 커밋의 폴더를 받는다. 출력의 "행"은 "항목"이 되고, 칸이 넷이 아닌 행의 종료 1은 라벨 줄이 빠진 항목의 종료 1이 된다. `--search`는 맞은 항목마다 파일 경로를 찍고 줄 번호를 찍지 않는다. 식별자는 문자열이다. 쓰임 문구(`USAGE`)의 `--queue <경로>`도 폴더에 맞춘다. `--ref`가 폴더 없는 이행 전 커밋을 받으면 오류로 끝나고 옛 파일로 돌아가지 않는다. 부르는 자리(아침 보고, `retro`·`next-session`의 `--ref origin/main`)는 이행 뒤의 main을 읽는다
- [x] **폴더를 읽는 법.** `--ref`와 아침 보고는 `git ls-tree`로 그 커밋의 폴더 목록을 받고 내용은 `git cat-file --batch` 한 프로세스로 받는다. `README.md`는 항목이 아니다
- [x] **인용을 푸는 함수.** `대기열 <ID>`의 ID가 숫자면 네 자리로 채운 파일, 아니면 그 이름의 파일로 푸는 함수 하나를 이 도구에 두고, 찾기와 아침 보고가 쓴다. 잇기 `<ID>의 k회차`도 같은 규칙이다. 새 CLI는 두지 않는다

### 아침 보고

- [x] `tools/morning_collect.py`(폴더 읽기, 무엇 칸 대신 머리 줄, 문자열 키, "대기열 행")와 `tools/morning_sources.py`가 origin/main의 폴더를 읽고, `tools/morning_report.py`의 대기열 번호 자리(인용 정규식, 정수 번호, 자리표시의 정수 변환)가 문자열 식별자를 받는다. 작업 지시(`tools/morning_tasks/summary.md`·`common.md`·`environment.md`)의 번호 예와 "대기열 행"을 고친다. 만료 경계는 그대로 옮긴다

### 번호 대조 도구

- [x] `tools/sibling_overlap.py`에서 대기열 번호의 읽기·겹침·다음 빈 번호·옮길 번호·`--move`의 행 머리와 인용 고침을 뗀다. merge-base의 대기열 표에 행이 없으면 종료 2로 멈추는 빈 자리 검사에서도 대기열을 뗀다(남기면 분할 뒤에 딴 모든 브랜치에서 대조가 멈춘다)
- [x] 다음 빈 번호 줄은 `일지 X, 티켓 NNN`이 되어, 그 줄을 읽는 일지 훅(`tools/hook_journal_retro.py`)이 기대는 `일지 X,`의 쉼표가 남는다. 훅 러너의 번호 저장소 픽스처(`tools/run_hooks.py`)는 대기열 파일을 심지 않는다

### 커밋 검사와 훅

- [x] `tools/check_ticket.py`의 면제 모양에 `.scratch/retro-queue/` 바로 아래의 `.md`를 더하고, 기능 폴더의 갈래가 `retro-queue`를 기능 slug로 읽지 않게 `harness`처럼 뺀다. `.scratch/retro-queue/issues/x.md`는 면제가 아니다. 옛 `.scratch/retro-queue.md`의 면제는 지운다. 독스트링(면제 모양의 원천)을 함께 고친다
- [x] `tools/hook_measure_word.py`의 근거 문서 맞대기를 `.scratch/retro-queue/`의 `.md`로 옮기고 취소선 편집의 못 보는 것을 고친다. `tools/hook_session_card.py`의 막는 까닭의 경로, `tools/hook_journal_retro.py`의 번호 줄 정규식(줄 꼴만 확인), 독스트링의 "대기열 행"(`hook_bash_commit_msg`, `hook_webfetch_summary`, `hook_measure_word`)을 고친다

### 스킬과 문서

- [x] `retro`의 쓰기 문단 전체, 회차를 더하는 잇기, 회고 절의 식별자, 사람 몫, 만료 문단을 항목 파일과 상태 줄로 고친다. 새 항목은 다음 빈 번호를 받지 않고 제목으로 쓴다
- [x] `next-session` SKILL.md(chore 줄, 실행 중 세션 확인의 "대기열 행"과 "행 번호", "대기열에 적은 행")와 `directive.md`("대기열 항목은 번호로만 가리키며")를 고친다. 2단계의 맡음 기록은 실행 중 세션의 시작 프롬프트에서 맡은 항목을 찾는 검색어만 식별자로 바꾼다(ADR 0045 결정 9). 다른 스킬의 "대기열 N" 인용은 글자 그대로 둔다
- [x] `CLAUDE.md`(지도의 대기열 행, 교정 루프, 환경 함정의 커밋 전 대조에서 대기열 몫), `CODING_STANDARDS.md` 판단 기준의 머리, `docs/agents/issue-tracker.md`(harness 티켓 서식의 `**대기열:**`은 항목 식별자를 든다, 대기열 행 하나가 티켓 하나, 근거 문서 훅의 경로), 살아 있는 문서의 "대기열 행", 런북(`KICKOFF.md`, `kickoff/claude-md-template.md`)을 고친다
- [x] `docs/constitution/operations.md`(문서 위치의 닫힌 행·열린 행, 하네스를 닫는 대기열 행의 닫힘 표지)를 고치고 헌법 판을 올린다(번호 대조 도구가 내는 형제 판보다 높게)
- [x] 고친 뒤 옛 표현(`.scratch/retro-queue.md`, "대기열 행", 대기열의 다음 빈 번호)을 저장소 전체에서 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4)

### 저장소 상태 시험

- [x] **옛 파일.** `.scratch/retro-queue.md`가 있으면 빨갛다. 같은 자리에서 모든 항목 파일이 라벨 줄 셋을 갖는지 본다. 지금 `tests/tools/test_queue_open_rows.py`의 이 저장소의 대기열을 빠짐없이 읽는 시험을 옮긴 것이다
- [x] **항목 이름.** 이름이 상수 이하인 네 자리 숫자이거나 새 항목의 제목 규칙을 따라야 한다. 상수는 이 PR이 마지막으로 origin/main을 합친 때 옛 표의 가장 큰 번호다(07d80b96에서 581). main을 다시 합치면 그때의 값으로 옮긴다. 상수보다 큰 번호가 main에 들어오면 이 시험이 빨개져 옮길 때를 알린다(main이 옛 표에 더한 행을 이행에 다시 맞댄 뒤다)
- [x] **실패 문장.** 명세 "저장소 상태 시험의 실패 문장"의 대기열 뜻대로, 옛 파일이면 무엇이 틀렸는지와 새 꼴과 옮겨 적고 옛 파일을 지우라는 할 일과 폴더 README를, 라벨 줄이 빠진 항목은 그 경로와 빠진 줄을, 이름이 규칙 밖인 항목은 그 경로와 상수를 들고 폴더 README를 가리킨다. 시험이 그 뜻을 단언한다

### 시험

- [x] `tests/tools/test_queue_open_rows.py`의 행 픽스처를 모두 항목 파일로 옮기고, 지금 사례(닫힘, 회차, 사람 몫, 만료, 대상 묶음, 찾기)를 임시 폴더와 임시 git 저장소(`--ref`)로 본다. 인용을 푸는 함수(573과 0573이 같은 파일, 슬러그 ID)와, 만료된 번호 항목을 잇는 슬러그 항목이 회차를 이어 세는 사례(사용자 스토리 6)를 더한다
- [x] `tests/tools/test_sibling_overlap.py`에서 대기열 몫의 사례와 다음 빈 번호 줄을 글자 그대로 단언하는 줄(07d80b96에서 15줄)을 고치고, 씨앗 저장소에서 대기열 파일을 뗀다. merge-base에 대기열 파일이 없어도 2로 끝나지 않는 사례를 더하고, 남는 것(ADR 번호, 헌법 판, 카나리아, 없는 인용, 함께 고친 파일)이 초록인지 본다
- [x] `tests/tools/test_check_ticket.py`에서 대기열 폴더 면제를 진짜 `git commit`과 `--ci`로 보고, 비슷한 이름 `.scratch/retro-queue-x/`와 `.scratch/retro-queue/issues/x.md`가 막히는 사례를 둔다
- [x] `tests/tools/test_hook_measure_word.py`, `tests/tools/test_hook_journal_retro.py`(도구 출력 픽스처), `tests/tools/test_hook_session_card.py`, `tests/tools/test_morning_collect.py`, `tests/tools/test_morning_report.py`(슬러그 사례)를 폴더와 문자열 식별자에 맞춘다
- [x] **아침 보고.** 임시 git 저장소에 `origin/main` ref를 두고 폴더 읽기와 슬러그 식별자 사례를 본다
- [x] **이행 전후의 대기열 절.** 이행 전의 옛 표로 낸 대기열 절과 이행 뒤의 폴더로 낸 대기열 절의 수와 이름이 같은지는 시험으로 두지 않는다. 이행 뒤에는 옛 파일이 없고(위 저장소 상태 시험이 막는다) CI의 python 잡은 `fetch-depth` 없이 체크아웃해(actions/checkout의 기본은 깊이 1이다), 시험으로 두면 어떤 구현에서도 초록이다. 이행을 돌린 세션이 한 번 맞대고 그 명령과 결과를 일지와 PR 본문에 적는다
- [x] **빨강을 먼저 본다.** 바꾸기 전의 도구로 폴더를 읽는 열린 목록 사례와 옛 파일 시험이 빨간 것을 본다(원칙 II)

### 카나리아, 변이 표, 프로브

- [x] 카나리아 명세 `retro_self_approve`, `retro_row_search`, `retro_reject_and_same_rows`, `retro_ticket_reflection`, `next_session_product_first`, `next_session_deferred_merge_running_scope`, `next_session_chore_tickets`, `next_session_queue_open_rows`를 새 꼴에 맞추고, 바꾼 스킬을 새 `claude -p` 세션에서 불러 본다. 바꾼 스킬 본문(`.claude/skills/*/*.md`), 규칙(`.claude/rules/*.md`), 서브에이전트(`.claude/agents/*.md`)마다 그 경로를 `source`로 든 카나리아 명세를 하나 이상 고친다. 번호 대조 도구의 카나리아 검사가 파일마다 보고, 그 경로를 원천으로 든 명세가 없으면 새로 둔다. 위에 이름을 든 명세는 그 예다
- [x] 변이 표 `queue_open_rows_mutations.toml`(다시 쓴다), `sibling_overlap_mutations.toml`의 대기열 몫, `measure_word_hook_mutations.toml`, `.scratch/ticket-for-every-pr/probes/check_ticket_mutations.toml`(새 면제 갈래의 변이를 더하고, 판정을 옮긴 줄의 원문이 남는지 먼저 본다)을 고치고 `tools/mutate.py`로 다시 돌린다
- [x] 프로브 `msys_pathconv/run.sh`(origin/main에 옛 파일이 있다는 데 기댄 절), `session_cost/collect.py`(다시 돌릴 프로브면 폴더로), `journal_number_hook/run.py`의 픽스처 서술, `.scratch/harness/probes/README.md`의 해당 행을 고친다

### 열린 항목

- [x] 열린 항목 가운데 분할이 해소하는 것을 이 티켓이 가려(명세 "바뀌는 자리"의 대기열 분할 "그 밖"), 이 PR에서 상태 줄로 닫고 그 목록을 PR 본문에 적는다

### 검증

- [x] PR을 열기 전에 이 티켓의 `Status:`를 `done`으로 바꾼다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다

### PR을 연 뒤

이 절은 `Status:`를 `done`으로 바꾸고 PR을 연 다음에 한다.

- [ ] 병합 직전에 `gh pr list --state open`으로 옛 파일을 고친 열린 PR을 세어 PR 본문에 적고, 그 수가 적을 때 병합한다(명세 "차례", 사용자 스토리 17)
