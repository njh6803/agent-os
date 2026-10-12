---
name: retro
description: "세션 회고. 사용자가 /retro를 치거나 마무리를 말할 때, 일지의 '다음' 절을 갱신하며 단계를 닫을 때 돌린다."
---

<!-- 프로젝트 사본, model-invoked. 원본(mattpocock/skills)은 disable-model-invocation: true. 근거는 일지 2026-09-20. 5단계(승인분을 대기열에 적는다)를 더했다. 근거는 일지 2026-09-22-10의 승인 2. 5단계의 행 형식과 번호 규칙은 2026-09-28 하네스 감사(대기열이 40KB 넘는 둘째 일지가 되고 재번호로 일지 참조 넷이 틀어졌다). 5단계의 `## 회고` 절은 대기열 78(retro 계기 훅이 그 제목을 읽는다). 4단계(후보를 에이전트가 판정한다), 5단계의 판정 기록과 승인 칸의 표지, 머리 문단의 끝 문장은 사용자 요청이다(일지 2026-10-12-41). 원본에서는 사용자가 후보를 고른다. -->

You are running a **retrospective** for this session, either because the user asked or because a stage just closed (the journal's "다음" section was updated, or the user said they are wrapping up). You are suggesting improvements to the coding agent's **environment** to improve future runs. You judge each candidate yourself (step 4); the user is asked only about the candidates step 4 hands to them.

## Steps

1. Call the Skill tool with `writing-for-agents` for the writing style guide.

2. Read the primary sources. In this repo the primary source is the latest file in `docs/journal/` (its "번복" and "갈린 곳" sections first), plus the current session. If the user names another session, search the session logs on this machine.

3. Look for candidates for improvement in these categories.

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? Read the repo's own check command first (its `package.json`/build-tool `lint`/`check` scripts, its CI workflow), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook and no CI job running its lint/typecheck/test command) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no guardrail at all.
- **Coding standards**: should the **reviewer agent** be given a new rule to enforce? Should an existing rule be removed or clarified? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check, full stop: a custom rule in the repo's own linter, a new pre-commit hook, or a new CI job, whichever the repo's language and existing guardrail make cheapest. Default to building the check over writing the rule. Reserve `CODING_STANDARDS.md` for genuine **judgement calls** (cross-file consistency, "matches the surrounding style," anything no guardrail could ever substitute for). _Use when_ the reviewer agent failed to catch a mistake.
- **Global AGENTS.md**: are there any steering instructions that should be moved to coding standards (or automated checks) instead? _Use when_ the AGENTS.md file is particularly large - in the repo OR the user's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't modify the agent's behavior. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

4. **후보마다 판정한다.** 판정은 승인, 기각, 넘김의 셋이고, 사용자에게 묻지 않고 에이전트가 정한다. 넘김은 판정을 사람에게 넘기는 것이고, 넘길 것부터 거른다.

   - **넘김**은 아래 다섯이다. 이 밖이라도 어느 판정인지 서지 않으면 넘긴다.
     - ADR이 필요한 것(`CLAUDE.md` 작업 규약 5).
     - 사용자 승인으로 쓰는 문서(`docs/PRD.md`, 헌법)와 계약(`sdk/`, `openapi.json`)에 닿는 것.
     - 가드레일이나 사람의 확인을 느슨하게 하는 것. 검사·훅·권한 거부를 빼거나 좁히는 것, 권한 허용(`settings.json`의 allow)을 넓히는 것, 리뷰의 기준이나 범위를 좁히는 것, 게이트에 예외를 두는 것, 스킬이 사용자에게 묻거나 확인받는 단계를 빼는 것이다.
     - 스스로 승인하는 기준을 바꾸는 것. 이 4단계와 그 기준을 되풀이한 자리(5단계의 승인 칸 표지, `CLAUDE.md` 교정 루프의 회고 줄, `CODING_STANDARDS.md` 판단 기준 머리, 대기열 머리말)다.
     - 사람만 할 수 있는 것(외부 계정, 결제, 권한 부여).
   - **승인**은 나머지 가운데 넷을 모두 지나는 것이다.
     - 사건: 이 세션이나 일지에 실제로 난 실수나 비용을 하나 든다.
     - 층: `CLAUDE.md` 교정 루프의 사다리에서 강제력이 가장 높은 층으로 고쳐 쓴 꼴로 승인한다. 검사가 잡을 수 있는 것은 검사로 승인한다.
     - 횟수: 고침(도구·훅·스킬의 버그, 틀린 사실, 깨진 경로)과, 행동이 일어나는 자리(그 단계의 스킬, 그 경로의 rules)에 더하는 문장은 사건 하나로 족하다. 교정 루프의 "세 번 반복"은 `CODING_STANDARDS.md`의 줄(규칙)에 거는 문턱이다(사용자가 승인해 온 대기열의 지침 행도 대부분 1회차였다, 일지 2026-10-12-41). 규칙 후보는 세 번째 전에는 회차를 세는 행으로 승인해 대기열에 두고("어디로" 칸은 `CODING_STANDARDS.md`(세 번째 반복에서 retro가 승인할 때)), 세 번째이고 자동 검사로 옮길 수 없을 때 그 줄을 더한다. 막는 훅은 `.claude/rules/tools.md`의 계기 훅·막는 훅 가름을 따른다.
     - 되돌림: PR 하나로 되돌릴 수 있다.
   - **기각**은 남은 것이다. 이미 있는 검사·지침이 잡는 것과 사건 없이 떠올린 것이 여기 든다.

   후보를 심각도 순으로, 판정과 그 근거가 된 조건을 붙여 보인다. 넘긴 것이 있으면 그것만 선택 화면으로 묻고 답을 받아 5단계로 간다. 넘긴 것이 없으면 답을 기다리지 않는다.

5. 결과를 최신 일지의 `## 회고` 절에 적는다. 낸 후보와 판정별 수, 후보마다 판정과 그 근거가 된 4단계의 조건, 승인된 것마다 사건과 간 자리(대기열 번호, 또는 이 세션에서 반영한 자리), 일지에만 남기는 것이다. 넘긴 것에 답하거나 판정을 뒤집은 사용자의 말은 원문을 인용 블록으로 적는다. 제목은 `## 회고` 그대로 쓰고(덧붙일 것은 `## 회고 (…)`), "다음" 절 앞에 둔다. `tools/hook_journal_retro.py`가 이 제목의 절을 retro가 돈 흔적으로 읽어, 자리 표시가 아닌 그 절이 있으면 "다음"을 적는 편집에 계기를 다시 넣지 않는다.

   승인된 것 중 **이 세션에서 반영하지 않는 것**을 `.scratch/retro-queue.md`에 줄로 적는다. 후보와 기각은 일지에만 남고 거기 오지 않는다. 대기열이 일지 산문에만 있으면 다음 세션이 그것을 세느라 파일 열여섯 개를 읽는다. 행은 넷으로 짧게 — 무엇(한 문장), 어디로, 회차 수와 최근 일지 파일명, ADR 필요 여부. 승인 칸은 `자체 승인 <날짜>`로 시작한다(넘겨서 사용자가 승인했으면 `사용자 승인 <날짜>`). 기존 행에 회차를 더할 때는 회차 수와 일지 파일명만 더한다. 사건의 서술과 판정의 근거는 일지 회고 절이 원천이고 대기열은 그 파일명을 가리킨다. 이 세션에서 닫거나 사용자가 되돌린 줄은 취소선을 긋고 어디서 닫혔는지(되돌림이면 `사용자가 되돌림 <날짜>`) 적는다. 번호는 영구 식별자다 — 닫힌 행을 지우거나 번호를 당기지 않는다(일지 백 수십 곳이 번호로 가리킨다). 같은 대상 파일의 열린 항목이 셋 이상이면 `next-session` 결정표의 chore 배치 조건이다.

## Reference

### Implementation vs Review

Remember that all work goes through two stages: implementation and review. The implementation agent has the most **context pressure**. They are responsible for exploration, writing code, and debugging failures.

The review agent has the least context pressure - it receives a diff, so no exploration needed. It often does not need to write code or debug.

This means that the review agent should be responsible for imposing coding standards, not the implementation agent.

### Files

You have access to several files in the repo:

- `CLAUDE.md`/`AGENTS.md`: these files are pushed to the context window of any agent working in this repo. They should be used incredibly sparingly, usually only for **navigation pointers** to other files.
- `CODING_STANDARDS.md`: this file is read during review, not implementation. Add **navigation pointers** to docs folders if the standards file gets more than 1,000 lines long.
- Docs: use docs as references files, pointed to by other files. Look for existing docs before writing new ones.
- Skills: use skills for docs (since their description goes into the agent's context window), or for user-invoked commands. Follow the advice in the `writing-for-agents` skill.
