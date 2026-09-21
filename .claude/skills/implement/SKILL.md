---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 브랜치 규약 포인터를 더했다. 근거는 일지 2026-09-21 첫 슬라이스 회고 뒤 대화. -->

Implement the work described by the user in the spec or tickets.

시작 전에 브랜치를 `docs/constitution/operations.md`의 규약대로 딴다. 티켓마다 `feature/<NN>-<slug>` 브랜치 하나, PR 하나. 예외를 제안하려면 이유와 그 이유가 사라지는 조건을 같이 적고, 조건이 차면 규약으로 돌아간다.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work to that branch.
