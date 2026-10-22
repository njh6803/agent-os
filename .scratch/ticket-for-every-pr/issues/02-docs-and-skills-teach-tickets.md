# 02: 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다

**What to build:** 세션과 사람이 읽는 규약이 새 차례를 가르친다. 하네스 일은 `.scratch/harness/issues/NNN-<slug>.md`에 티켓을 쓰고 브랜치는 `chore/NNN-<slug>`, 기능 폴더의 티켓은 `feature/NN-<slug>`이며, 브랜치 이름은 티켓 파일 이름의 stem 그대로다. 설계·명세·티켓을 쓰는 PR과 기록(일지·대기열)만 바꾸는 PR은 지금처럼 `docs/<slug>`이고 티켓을 쓰지 않는다. 티켓은 쓸 때 `in-progress`, `to-tickets`가 미리 쓴 `ready-for-agent` 티켓은 첫 편집에서 `in-progress`, PR을 열기 전에 `done`이다. 이 티켓이 병합되면 `next-session`이 chore 차례에서 고른 대기열 행을 티켓 단위로 나눠 티켓마다 지시문을 내고, 그 지시문의 브랜치는 `chore/NNN-<slug>`, 시작 프롬프트는 티켓 경로를 든다. 셀프 리뷰의 명세 축은 브랜치가 가리키는 티켓 파일을 기준으로 보고, 회고는 반영을 지금 PR의 티켓에 수용 기준 한 줄로 더한다.

근거는 `.scratch/ticket-for-every-pr/spec.md`의 Solution, "티켓 자리와 서식", "쓰는 때와 상태", "상태 표시와 기록 판정", "레벨 스윕", "바뀌는 문서와 스킬"과 그 2026-10-21 명세 검토 주석들, 사용자 스토리 1~4·12·14~19·21·23~28·30·32·33·36·37·40·41이다. 결정은 ADR 0037이다. 이 티켓은 헌법(`docs/constitution/operations.md`)을 고쳐 03·05를 막는다(`CLAUDE.md` 작업 규약 2). 스킬이 브랜치 규약을 그 파일로 돌려보내, 그 절이 옛 정의로 남은 채 커밋 검사가 들어오면 그 절대로 딴 세션이 막힌다.

이 티켓이 하지 않는 것. 면제 모양의 원천이 커밋 검사의 독스트링이라는 문장, 가드레일의 자동 검사 목록, 게이트 수와 러너 검사 수는 03이 고친다(그 전에는 가리킬 것이 없다). CI 잡 수는 04다.

**Blocked by:** 01

**Status:** done

### 규약 원천

- [x] **`docs/agents/issue-tracker.md` 규약 절.** 경계(PR마다 티켓 하나, 면제 둘인 설계·명세·티켓을 쓰는 PR과 기록만 바꾸는 PR을 말로), harness 자리와 세 자리 번호(번호는 번호 도구의 다음 빈 번호이고, 번호를 받은 세션은 티켓 파일을 쓴 직후에 번호 도구를 다시 친다. 형제의 대조는 디스크의 파일로 찬 번호를 보므로 파일을 쓰기 전의 번호는 형제에게 보이지 않는다. 명세 "번호"의 누가 언제 받는가), harness 티켓 서식(머리 `# NNN: <제목>`, `**What to build:**`, `**대기열:**`(행 번호들, 없으면 `없음`), `**Status:**`, 수용 기준. `Blocked by`는 없다), 상태의 흐름, 브랜치 이름이 티켓 stem이라는 것, 기능 밖 제품 고침의 자리(그 동작을 만든 기능 폴더의 다음 두 자리 번호, `plan.md` 상태는 done 그대로), 병합된 티켓을 잇는 일은 다음 번호의 새 티켓이라는 것
- [x] **같은 파일의 전체 계획 절과 화면 디자인 절.** `plan.md`는 제품 기능만이고 하네스 기능과 harness 티켓의 상태는 티켓의 `Status:` 줄이다. 디자인 동기화의 `chore/` 브랜치는 harness 티켓의 `chore/NNN-<slug>`가 된다
- [x] **`docs/constitution/operations.md`.** 브랜치와 병합 절의 세 정의(`chore/<slug>`, `fix/<slug>`, `docs/<slug>`)를 `feature/NN-<slug>`, `chore/NNN-<slug>`, 면제 PR의 `docs/<slug>`로 바꾼다. 문서 위치 절의 기록 판정을 명세 "상태 표시와 기록 판정"대로 넓힌다(하네스 기능 폴더는 티켓이 있고 모두 done일 때, harness 티켓은 하나씩 done일 때 기록이고, done 제품 기능의 열린 고침 티켓만 살아 있다). 리뷰 파이프라인 1의 명세 축은 브랜치가 가리키는 티켓 파일이고 기능 폴더의 티켓이면 그 폴더의 `spec.md`도다. 헌법 patch 판을 올리고 번호는 번호 도구의 "형제가 쓴 가장 높은 헌법 판"보다 높게 고른다
- [x] **`CLAUDE.md` 지도 표.** `.scratch/<slug>/spec.md`, `issues/` 줄의 쓰는 때 칸에 harness 티켓은 그 일을 하는 세션이 쓴다는 것만 더하고 `docs/agents/issue-tracker.md`를 가리킨다. 규칙의 문장은 두지 않는다
- [x] **루트 `README.md` 원천 표**의 미래 배치·기능 순서·상태 줄에 하네스의 상태는 티켓의 `Status:`라는 것을 더한다
- [x] **`.github/PULL_REQUEST_TEMPLATE.md`** "관련 티켓" 절의 주석에 harness 티켓 경로와, 면제 PR이면 면제의 종류를 적는다는 것을 더한다
- [x] **`.scratch/retro-queue.md` 머리.** 어디서 닫혔는지 적는 문장에 티켓으로 닫은 행이면 티켓 경로를 적는다는 것을, "기본 반영 자리는 `chore/<slug>` 브랜치다"를 harness 티켓의 `chore/NNN-<slug>` 브랜치로 고친다
- [x] **`.scratch/harness/probes/model_sweep/README.md` 결과 절**에 "조건 변경(ADR 0037)" 문단을 두어, 스윕 기간 안에 하네스 기능의 티켓이 `feature/NN-`으로 돌면 구현으로 잡히는 것을 받아들인다는 것과 그 문단이 들어간 날을 적는다(선례: 같은 절의 "조건 변경(ADR 0033)"). 해시로 고정한 사전 등록 절과 `tools/model_sweep.py`는 고치지 않는다
- [x] `docs/model-selection.md`의 작업 종류별 기준선 문단은 고치지 않는다(그 `fix/`는 지난 측정의 브랜치를 가른 정의다)

### 스킬

- [x] 스킬을 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [x] **`next-session`.** 결정표의 chore 배치 줄은 고른 행을 티켓 단위(행 하나가 티켓 하나, 같은 파일을 고치는 고침 행만 묶는다)로 나눠 티켓마다 지시문을 낸다. 브랜치는 `chore/NNN-<slug>`, 다음 작업 줄은 `.scratch/harness/issues/NNN-<slug>.md`(받는 세션이 쓴다), 시작 프롬프트는 `대기열 <번호들>을 티켓 .scratch/harness/issues/NNN-<slug>.md로 쓰고 한다` 꼴이다. 대상 파일이 겹치지 않는 티켓은 2단계의 나란히 여는 묶음이고, 앞의 티켓과 대상 파일이 겹치는 행은 이번에 열지 않고 대기열에 남긴다. 3단계는 그 번호를 번호 도구에서 받고 묶음이면 이어 매긴다. "기능의 티켓이 아니라 하네스 chore PR이었고" 줄은 harness 티켓의 PR을 가리키게 고치고, 지시문 형식의 다음 작업 줄에 harness 티켓 경로를 더한다
- [x] **`implement`.** 브랜치를 따는 문장에 브랜치 이름이 티켓 파일 이름의 stem 그대로라는 것, 첫 편집으로 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다는 것, PR을 열기 전에 `done`으로 바꾼다는 것, 티켓 없이 받은 일이면 먼저 티켓을 쓰고 쓴 직후에 번호 도구를 다시 친다는 것(자리와 번호는 `docs/agents/issue-tracker.md`)을 둔다. chore 지시문으로 번호를 받아 온 세션도 티켓 파일을 쓴 직후에 다시 친다
- [x] **`code-review`.** 2단계의 명세 출처 차례에서 인자로 넘긴 경로 다음에 브랜치가 가리키는 티켓 파일을 둔다. 기능 폴더의 티켓이면 그 폴더의 `spec.md`도 명세다
- [x] **`retro`.** 4단계의 반영할 때에 회고 반영의 줄(지금 PR의 티켓에 수용 기준 한 줄 `회고 반영: …, 일지 <파일>`을 더해 같은 PR에 싣는다. 티켓이 없는 면제 PR이면 harness 티켓 한 장을 쓰고 쓴 직후에 번호 도구를 다시 친다. 그 티켓도 쓸 때 in-progress, 반영을 싣는 커밋에서 done)을 둔다. 대기열의 닫힘은 티켓으로 닫은 행이면 브랜치 대신 그 티켓 경로를 적는다(`**닫힘 (<티켓 경로>, <날짜>, <한 것>. …)**`)
- [x] **`to-tickets`.** 파일 이름의 stem이 구현 브랜치(`feature/<NN>-<slug>`)가 된다는 것을 적는다. 프로젝트 사본의 센티널 주석과 `tools/check_instructions.py`의 덧댄 사본 목록을 함께 본다
- [x] **카나리아.** 바꾼 스킬마다 카나리아 명세(`.scratch/harness/probes/canary/*.toml`)를 고치고 새 `claude -p` 세션에서 불러 본다(`CLAUDE.md` 작업 규약 3). 그 결과를 일지의 검사 절에 적는다

### 잔존과 검증

- [x] **잔존이 0이다.** 브랜치 이름의 옛 정의(`chore/<slug>`, `fix/<slug>`)를 든 살아 있는 문서를 저장소 전체에서 grep해 고친다(명세의 목록에 없어도. `CLAUDE.md` 작업 규약 4). 무엇이 살아 있는지는 위에서 고친 `operations.md` 문서 위치다. 기록(일지, 대기열의 닫힌 행, ADR의 지난 이력, 헌법 README의 버전 이력)은 뺀다. `KICKOFF.md`의 `chore/kickoff`는 새 프로젝트의 킥오프 몫이라 두고(명세 "바뀌는 문서와 스킬"의 2026-10-21 주석), 그 밖의 걸린 것은 둘레를 읽고 판정한다
- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣고, PR을 열기 전에 `done`으로 바꾼다
- [x] 검증 명령이 모두 초록이다
