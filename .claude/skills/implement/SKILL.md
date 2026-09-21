---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 셋을 더했다. 시작 전 브랜치 규약 포인터, 루프 중의 린트, 마칠 때 세션 경계(원천은 next-session 스킬). 근거는 일지 2026-09-21 첫 슬라이스 회고 뒤 대화, 인터럽트 설계 뒤 대화, 티켓 01 회고, 세션 경계 일지. -->

Implement the work described by the user in the spec or tickets.

시작 전에 브랜치를 `docs/constitution/operations.md`의 규약대로 딴다. 티켓마다 `feature/<NN>-<slug>` 브랜치 하나, PR 하나. 예외를 제안하려면 이유와 그 이유가 사라지는 조건을 같이 적고, 조건이 차면 규약으로 돌아간다.

Use /tdd where possible, at pre-agreed seams.

Run linting and typechecking regularly, single test files regularly, and the full test suite once at the end. red가 예상보다 넓으면 린트를 먼저 돌린다. 이름 충돌과 import 문제는 테스트 실패로 위장한다.

Once done, use /code-review to review the work.

Commit your work to that branch.

거기서 멈춘다. 다음 티켓은 새 세션이 한다. 이유와 다음 세션 지시문은 next-session 스킬이 원천이고, 사용자가 `/git-pr`로 PR을 열면 훅이 그 계기를 넣는다.
