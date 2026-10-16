# 07: 셀프 리뷰의 표준 축을 sonnet·high로 돌리고 쓰지 않는 플러그인 넷을 끈다

**What to build:** `/code-review`를 부르면 표준 축 서브에이전트가 변경 종류와 상관없이 Sonnet `high`로 돈다. 명세 축은 지금처럼 메인 세션의 모델과 노력을 물려받는다. 이 저장소에서 새 세션을 열면 쓰지 않는 플러그인 넷(`document-skills`, `example-skills`, `skill-creator`, `code-review` 플러그인판)의 스킬이 스킬 목록에 실리지 않는다. 다른 프로젝트에서는 그대로 켜져 있다. 리뷰 비용과 모든 호출에 실리는 시작 컨텍스트가 병합하는 대로 줄어든다.

근거는 `.scratch/token-usage/spec.md`의 "셀프 리뷰의 표준 축", "시작 컨텍스트"의 플러그인, "레벨 스윕 기록", Testing Decisions의 스킬 항목이다. 결정은 ADR 0033 본문("셀프 리뷰의 표준 축은 변경 종류와 상관없이 `sonnet`·`high`로 돈다", "시작 컨텍스트를 줄인다")이다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 표준 축

- [x] `code-review` 스킬 4단계의 첫 문장(소스 파일이 없는 diff에서만 표준 축을 `sonnet`으로 띄운다)을 "표준 축 서브에이전트는 변경 종류와 상관없이 `model: sonnet`, `effort: high`로 띄운다"는 뜻으로 바꾼다. 명세 축은 모델과 노력을 주지 않는다. 스킬 머리의 센티널 주석이 든 "4단계의 sonnet 규칙"을 바뀐 규칙으로 고친다
- [x] `docs/model-selection.md`의 표준 축 서브에이전트 행에서 손잡이를 "모델"에서 "모델과 노력"으로, 설명을 언제나 `sonnet`·`high`(ADR 0033)로 고친다
- [x] `KICKOFF.md`의 `code-review` 사본 항목에서 덧댄 것 목록의 "소스 없는 변경은 sonnet"을 바뀐 규칙으로 고친다
- [x] 옛 규칙(스킬 4단계의 영어 문구 "touches no source file", 한국어 "소스 파일이 없는", "소스 없는 변경은 sonnet" 등)을 저장소 전체에서 grep해 살아 있는 문서에 남지 않았는지 본다. 기록(일지, 지난 명세와 티켓, ADR 이력)과 ADR 0006 본문의 포인터가 붙은 문장, `.claude/worktrees/`는 뺀다
- [x] 바꾼 `code-review`를 새 세션에서 불러 본다(`CLAUDE.md` 작업 규약 3). 그것을 원천으로 든 카나리아 명세를 새 `claude -p` 세션에서 돌려 결과 줄을 고친다(`tools/sibling_overlap.py`가 본다)

### 플러그인

- [x] `.claude/settings.json`의 `enabledPlugins`에 넷을 `false`로 더한다. `document-skills@anthropic-agent-skills`, `example-skills@anthropic-agent-skills`, `skill-creator@claude-plugins-official`, `code-review@claude-plugins-official`이다
- [x] 이 저장소의 지침이나 스킬이 그 넷의 스킬을 부르는 자리가 없는지 grep으로 본다. 있으면 멈추고 사람에게 묻는다
- [x] 이 워크트리에서 새 `claude -p` 세션을 열어, 스킬 목록에 넷의 스킬이 없는지 모델이 옮기게 해서 본다. 그 세션은 사용자 설정을 싣는다. 카나리아처럼 사용자 설정을 빼고 띄우면(`--setting-sources project,local`) 사용자 설정의 `true`가 처음부터 실리지 않아 늘 없다고 나온다. 양성 대조로, 바꾸기 전의 설정(origin/main의 `.claude/settings.json`)으로 띄운 같은 세션에서는 넷의 스킬이 보이는 것을 먼저 본다(`.claude/rules/probes.md`의 표지와 갈래 항목). 손으로 본 것으로 일지에 적는다. 프로젝트 설정의 `false`가 사용자 설정의 `true`를 이긴다는 것은 웹 요약이었다(ADR 0033). 보고서 9절로 보는 확인은 09다

### 기록

- [x] 레벨 스윕 README의 조건 변경 절에 플러그인 끄기와 표준 축 `sonnet`·`high`의 두 줄을 이 PR 번호로 적는다. 절이 없으면 만들고 절 머리에 효과가 서는 때를 한 번 적는다(명세 "레벨 스윕 기록"). `sweep.py prereg`가 0으로 끝난다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 받는 쪽

- [ ] 리뷰 서브에이전트가 실제로 Sonnet 5.5 `high`로 도는지는 보고서 4절이, 넷의 스킬 목록이 0자인지는 보고서 9절이 보인다. 둘 다 09가 본다
