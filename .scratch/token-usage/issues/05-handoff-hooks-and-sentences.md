# 05: 인계 훅 둘과 그것이 바꾸는 문장

**What to build:** 세션 컨텍스트가 20만 토큰을 넘은 세션이 단계 경계(셀프 리뷰 직전, 커밋 뒤, PR 연 뒤)에 오면, 새 훅 `hook_handoff`가 모델에게 인계를 지시한다. 모델은 묻지 않고 일지에 지금까지를 적은 뒤, 백그라운드 대기를 멈추고, 자기 제목을 `<브랜치> (인계함)`으로 바꾼다. 그리고 `next-session`의 인계 줄로 지시문을 내고, `open-session`으로 같은 티켓·브랜치·워크트리의 새 세션을 연 뒤 턴을 끝낸다. 사람은 아무것도 치지 않는다. 턴이 끝날 때 문턱을 넘었으면 새 훅 `hook_handoff_notice`가 사람에게만 한 번 알린다. 이 PR이 병합된 뒤에는 "PR을 연 세션이 반영과 병합까지 한다"가 인계 때는 참이 아니므로, 그 결정을 적은 문장들을 함께 고친다.

계기를 쓰는 쪽(훅 둘, `hook_pr_next_session`의 문장)과 받는 쪽(`next-session`의 인계 줄)은 이 티켓의 한 PR로 병합한다(명세가 정했다).

근거는 `.scratch/token-usage/spec.md`의 "인계 훅", "`next-session`의 인계", "인계가 바꾸는 문장", "레벨 스윕 기록", Testing Decisions의 훅·계기 도달·스킬 항목이다. 결정은 ADR 0033 본문과 두 2026-10-16 이력이고, 경계 셋과 훅 둘은 사용자가 골랐다(일지 2026-10-16-13, 2026-10-16-34).

**Blocked by:** 01(러너가 `notice`를 받는다)

**Status:** ready-for-agent

이 티켓은 헌법(`docs/constitution/operations.md`)에 닿지만 다른 티켓을 막지 않는다. 다른 티켓이 그 문장과 판에 기대지 않고, 헌법 판 patch는 ADR 0033이 2026-10-15에 승인받았다(Consequences "헌법 판"). 병합 때 따로 묻지 않는다(명세 Further Notes, 티켓 분할 승인 일지 2026-10-16-34).

### 훅 둘

- [ ] `hook_handoff`를 PostToolUse에 매처 `Bash|PowerShell|Skill`과 MCP의 PR 만들기 도구 둘(`hook_pr_next_session`의 매처에 있는 이름)로, `hook_handoff_notice`를 Stop에 래퍼 모양으로 등록한다
- [ ] 판정은 명세 "인계 훅"대로다. 경계인지 먼저 가르고 경계일 때만 트랜스크립트 끝 2MiB를 읽는다. 세션 컨텍스트는 메인 세션의 마지막 모델 응답 usage의 세 토큰 합이다. 그 응답 뒤에 압축 경계 기록이 있으면 압축 전의 값이라 침묵한다. 서브에이전트(`agent_id`)와 클라우드 세션(`CLAUDE_CODE_REMOTE`가 `true`)에서는 두 훅 모두 침묵한다
- [ ] 셀프 리뷰 직전은 Skill의 `code-review`와 `.claude`로 시작하는 경로 접두에 `:code-review`가 붙은 것이다. 커밋 뒤는 명령 위치의 `git commit`이고 `--dry-run`·`--help`·`-h`와 `commit-tree`·`commit-graph`는 아니며 `-c`·`-C`·`--no-pager`는 지난다(선례 `tools/hook_git_main_commit.py`의 `_GIT_COMMIT`, `commits_in`). PR 연 뒤는 셸의 `gh pr create`와 MCP의 PR 만들기다
- [ ] 인계 문장(`additionalContext`)은 세션 컨텍스트의 크기, 문턱, 경계의 이름(글자 그대로 `셀프 리뷰 직전`, `커밋 뒤`, `PR 연 뒤`)을 들고, 훅 파일과 같은 체크아웃의 `.claude/skills/next-session/SKILL.md`를 Read로 열어 결정표의 인계 줄을 따르라고 한다. Skill 도구로 부르라고 하지 않는다. 셀프 리뷰 직전이면 방금 불린 `code-review`의 단계를 밟지 않는다고, PR 연 뒤면 봇 회차와 병합도 새 세션이 한다고, 함께 온 `hook_pr_next_session`의 계기보다 이것이 앞선다고 덧붙인다
- [ ] Stop 알림(`systemMessage`)은 크기와 다음 경계에서 넘어간다는 것, 받은 범위가 그 경계에서 끝나거나 같은 경계에 다시 오면 넘기지 않는다는 것을 적는다. 한 번만 알리는 표지는 `tools/launch_hook.py`의 모양이고 임시 폴더는 `tempfile.gettempdir()`다. `hook_handoff`가 인계를 지시할 때도 같은 이름의 표지를 만든다. 표지를 쓰지 못하면 알리지 않는다
- [ ] 두 훅의 문턱, 세션 컨텍스트 셈, 표지 이름은 두 파일에 따로 두고 시험이 같은지 본다(선례 `test_산문_규칙과_문턱은_Stop_훅과_같다`)
- [ ] 독스트링에 못 보는 것을 적고 항목마다 시험으로 고정한다(명세 "인계 훅"의 못 보는 것)

### 받는 쪽과 바뀌는 문장

- [ ] `next-session`: 첫 문단의 "PR을 열었으면 이 세션이 반영과 병합까지 마치고"와 프런트매터 `description`에 인계 계기를 더한다. 결정표 맨 위에 인계 줄을 두고 칸(지금, 다음 단계, 시작 프롬프트와 이어받을 상태, 어디서, 이번 요청 범위, 모델)을 명세대로 채운다. 경계마다의 이어받을 상태(셀프 리뷰 직전, 커밋 뒤와 푸시하지 않은 커밋, PR 연 뒤)를 빠짐없이 적는다. 인계 줄에는 2단계의 묶음(나란히 돌 티켓)을 적용하지 않는다고 적는다. 인계하지 않는 때(자동 압축이 받고, 자동 압축 창을 적용하기 전에는 기본 지점이다), 3단계의 갈래(`tools/model_sweep.py`를 치는 조건과 끊는 줄의 `Sonnet 5.5 / high`), 1단계를 건너뛰되 4(일지)는 하는 것을 적는다. 넘기기 전에(차례는 일지, 제목 바꾸기, TaskStop, `open-session`. 제목 바꾸기가 거절되면 열지 않고 알린 뒤 이 세션에서 다음 단계를 잇기, `open-session`이 실패하면 제목을 되돌리고 멈춘 대기를 다시 띄워 잇기, 데스크톱 앱 밖이면 제목을 바꾸지 않고 지시문을 낸 뒤 멈추기), 압축 뒤 이어 할 때(`open-session`을 부르기 직전에 일지에 한 줄을 남기고, 그 줄이 있으면 다시 열지 않기. 새 세션은 첫 턴에 아직 제목이 없을 수 있다), 넘긴 뒤(다른 도구 없이 턴을 끝내고, 다시 깨어나도 일하지 않는다. PR 감시는 끄지 않는다)를 적는다. 1단계 3의 "병합은 PR을 연 세션의 일이다"에 인계로 넘겨받은 세션도 든다고 더한다
- [ ] `tools/hook_pr_next_session.py`는 이름과 판정을 그대로 두고, 계기 문장의 "PR을 열었으면 그 스킬의 1단계가 반영과 병합을 먼저 마친다"에 한 마디를 더한다. 인계 계기가 함께 왔으면 Skill 도구로 부르지 말고 인계 계기의 문장대로 스킬 파일을 Read로 열어 결정표의 인계 줄을 따른다는 것이다. 그 계기 문장의 "Skill 도구로 next-session 을 지금 돌린다"를 따라 옛 사본이 실리면 병합이 앞당겨지기 때문이다(명세 "`hook_pr_next_session`과 함께 올 때"). 바뀐 문장을 시험으로 고정한다
- [ ] 명세 "인계가 바꾸는 문장"의 나머지를 고친다. `docs/constitution/operations.md` 브랜치와 병합의 "PR을 연 세션이 반영과 병합까지 한다"(헌법 판 patch. 값은 그때 `tools/sibling_overlap.py`가 든 가장 높은 판보다 높게), `docs/model-selection.md`의 "PR을 연 세션은 반영과 병합까지 한다" 문단, `KICKOFF.md` 7단계의 `next-session` 항목("PR을 열었으면 그 세션이 반영과 병합까지 마친 뒤다")과 9단계 항목 8의 "반영과 병합은 PR을 연 세션이 하고"다. ADR 0029 이력 안의 같은 문장은 고치지 않는다
- [ ] 고친 뒤 "PR을 연 세션"과 "반영과 병합"을 저장소 전체에서 grep해 살아 있는 문서에 옛 결정이 남지 않았는지 본다(`CLAUDE.md` 작업 규약 4). 기록(일지, 지난 명세와 티켓, ADR 이력)과 이 기능의 명세·티켓, `.claude/worktrees/`는 뺀다

### 시험과 실행 확인

- [ ] 명세 Testing Decisions의 `hook_handoff`, `hook_handoff_notice`, 두 훅의 같음, `hook_pr_next_session` 항목을 시험으로 고정한다. 경계가 아닌 호출이 트랜스크립트를 열지 않는 것은 읽기 함수를 바꿔 끼워 보고(선례 `tests/tools/test_hook_git_main_commit.py`), 표지를 쓰지 못하는 것은 환경으로 쓸 수 없는 임시 폴더를 줘 본다(선례 `tests/tools/test_launch_hook.py`)
- [ ] 러너에 자리표시자를 더하고 러너 독스트링의 자리표시자 목록과 수를 고친다. 문턱을 넘는 usage가 든 트랜스크립트, 넘지 않는 usage가 든 트랜스크립트, 표지를 쓸 빈 임시 폴더다. `tools/hook_payloads.toml`에 두 훅마다 발동 하나(`hook_handoff`는 `context`, `hook_handoff_notice`는 `notice`)와 침묵 하나를 실제 입력으로 더한다. 페이로드는 실제 세션에서 저장한 것을 쓴다
- [ ] `hook_handoff`의 `additionalContext`가 실제 세션의 모델에게 닿는지 모델이 그 문장을 옮기게 해서 본다(`.claude/rules/tools.md`의 새 훅이 함께 하는 넷). 시험 세션은 20만을 넘기 어려워 문턱을 낮춘 커밋하지 않는 임시 사본으로 잰다. 같은 자리에서 워크트리 세션이 주 체크아웃의 스킬 파일을 Read할 때 승인 질문이 뜨는지도 보고 일지에 적는다. 뜨면 승인할 사람이 없는 세션은 인계 첫 단계에서 멈추므로, 문장이 가리킬 자리를 이 티켓이 다시 정하고 그 근거를 일지에 적는다
- [ ] 인계 줄의 규칙을 카나리아 명세로 고정한다. 스윕 브랜치의 갈래, 같은 경계에서는 넘기지 않음, 받은 범위가 그 경계에서 끝나면 넘기지 않음, PR을 연 직후 두 계기가 함께 오면 인계가 이김, PR 연 뒤의 이어받을 상태, 제목이 이미 `(인계함)`인 채 압축 뒤 이어 할 때, 제목 바꾸기가 거절될 때다(선례 `.scratch/harness/probes/canary/next_session_model_sweep.toml`). 바꾼 `next-session`과 `.claude/rules/tools.md`를 원천으로 든 기존 카나리아도 돌려 결과 줄을 고친다(`tools/sibling_overlap.py`가 본다)
- [ ] `tools/mutate.py`로 경계 판정, 문턱, 표지를 바꾸면 시험이 빨개지는지 본다
- [ ] 경계가 아닌 호출, 경계의 호출, Stop에서 두 훅이 쓰는 시간을 재서 `.claude/rules/tools.md`의 시간 목록에 더한다
- [ ] `KICKOFF.md` 7단계의 `.claude/settings.json` 항목에 이 두 등록은 새 프로젝트에 복사하지 않는다고 적고, 그 항목이 늘어놓은 매처를 맞춘다(명세 Out of Scope)
- [ ] 레벨 스윕 README의 조건 변경 절에 인계 훅 줄을 이 PR 번호로 적는다. 절이 없으면 만들고 절 머리에 효과가 서는 때를 한 번 적는다(명세 "레벨 스윕 기록"). `sweep.py prereg`가 0으로 끝난다
- [ ] 바꾼 `next-session`을 새 세션에서 불러 본다(`CLAUDE.md` 작업 규약 3)
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 받는 쪽

- [ ] 병합 뒤 주 체크아웃을 당겨야 새 세션의 훅과 스킬이 이 판으로 돈다(`.claude/rules/tools.md`의 `CLAUDE_PROJECT_DIR`). 처음 일어난 실제 인계는 09가 본다

### 이 티켓이 정할 것

1. 인계 문장과 Stop 알림의 그 밖의 문구
2. 표지 파일의 이름
3. 새 카나리아 명세의 갈래 구성
