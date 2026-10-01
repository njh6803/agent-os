---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)의 텍스트 라운드 형식을 `AskUserQuestion` 라운드로 바꿨다. 사용자가 설계 인터뷰에서 UI로 고르는 선택지와 추천을 요청했는데 그 선호가 일지에만 있어서, 이 스킬의 텍스트 형식을 따른 세션이 같은 라운드를 UI로 다시 올렸다(일지 2026-09-22-07, 2026-09-24-03, 2026-09-26-06, 대기열 27). 사실을 찾는 서브에이전트의 보고를 근거의 종류로 가르고 조합은 소비 지점까지 재게 하는 문단을 더했다(대기열 45·61). 이 주석이 `tools/check_instructions.py`의 센티널이라 지우면 검사가 빨강이 된다. -->

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round. Then wait for the user's answers before the next round.

라운드는 `AskUserQuestion` 도구로 올린다. 결정 하나가 질문 하나다. 질문마다 네가 추천할 답을 먼저 고르고, 그 선택지를 첫 자리로 옮겨 라벨 끝에 "(Recommended)"를 붙인다. 선택지마다 설명에 그것을 고르면 무엇이 정해지는지 적는다. 한 호출에 넷까지 들어가므로 frontier가 넷을 넘으면 같은 라운드를 호출 여럿으로 잇달아 올린다. 질문 문장은 호출 안에만 쓴다. 호출 곁의 본문에는 선택지가 담지 못하는 것, 곧 네가 찾은 사실과 추천의 근거만 쓴다.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

사실을 찾는 서브에이전트에게는 보고를 근거의 종류로 갈라 달라고 한다. 스크립트로 쟀다(그 파일), 손으로 봤다(그 명령), 코드를 읽었다(파일과 판), 어림이다. 고르는 사실이 라이브러리나 도구의 조합이면 그것을 쓰는 코드가 타입 검사와 실행을 지나는 데까지, 설치할 판으로 재게 한다. 그 보고가 그대로 ADR의 근거가 된다. 규약은 `docs/agents/issue-tracker.md`의 프로브와 근거 절이다(대기열 45·61).

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
