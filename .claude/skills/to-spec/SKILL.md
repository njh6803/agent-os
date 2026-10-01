---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 셋을 더했다. 3단계의 측정 규칙(대기열 38, 측정이 가는 범위는 61), Implementation Decisions 의 경로 규칙을 저장소 관행에 맞춘 것(대기열 30), Out of Scope 의 받는 쪽 확인(대기열 3). 이 주석이 `tools/check_instructions.py`의 센티널이라 지우면 검사가 빨강이 된다. -->

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec using the template below, then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

   명세가 측정을 다음 단계에 넘기려 하면("구현 티켓이 잰다", "실패한다면 무엇을 할지는 이력으로 제안한다") 그 결과가 새 결정을 낳을 수 있는지 먼저 본다. 낳을 수 있으면 그 자리에서 잰다. 설계의 ADR이 넘긴 측정도 명세가 받는 자리에서 잰다. 넘기면 티켓이 구현 도중 ADR 승인을 기다리며 멈춘다(대기열 38, 두 번 다 명세 검토가 재고서야 ADR 이력이 됐다). 명세가 재거나 설계에서 받아 쓰는 측정은 명세의 범위까지 간다. 그것을 쓰는 코드가 타입 검사와 실행을 지나는 데까지, 명세가 받을 입력 전부(상류를 IPv4와 `::1`로 받으면 둘 다)까지, 설치할 판으로 잰다. 설계의 측정이 그만큼 가지 않았으면 그 자리에서 다시 잰다. 셋 다 구현 티켓에서야 드러났다(대기열 61). 프로브를 두는 자리와 근거 문장의 종류(쟀다, 손으로 봤다, 코드를 읽었다, 어림)는 `docs/agents/issue-tracker.md`의 프로브와 근거 절이다.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

구현 파일의 경로와 코드 조각은 적지 않는다. 금방 낡는다. 규칙 문서(`.claude/rules/*.md`)·ADR·테스트 선례의 경로는 적는다 — 이 저장소의 명세 셋이 모두 그렇게 했고, 원본 문언대로 리뷰하면 매번 오탐이었다(대기열 30).

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

다른 기능에 넘기는 것은 받는 쪽을 이름으로 적고, `.scratch/plan.md`의 그 기능 행에도 적는다. 그 행의 Blocked by가 이 기능을 포함하는지 본다 — 받는 쪽이 이 기능보다 먼저 돌 수 있다(대기열 3).

## Further Notes

Any further notes about the feature.

</spec-template>
