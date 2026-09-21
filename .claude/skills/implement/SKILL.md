---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 브랜치 규약 포인터를 더했다. 근거는 일지 2026-09-21 첫 슬라이스 회고 뒤 대화. -->

Implement the work described by the user in the spec or tickets.

시작 전에 브랜치를 `docs/constitution/operations.md`의 규약대로 딴다. 티켓마다 `feature/<NN>-<slug>` 브랜치 하나, PR 하나. 예외를 제안하려면 이유와 그 이유가 사라지는 조건을 같이 적고, 조건이 차면 규약으로 돌아간다.

티켓 하나를 마치면 거기서 멈춘다. 다음 티켓은 새 세션에서 시작한다. 티켓은 신선한 컨텍스트 하나에 맞게 잘려 있고 티켓 파일 하나가 자족적이라, 앞 티켓을 지나온 컨텍스트는 도움이 아니라 잡음이다. 이어서 해야 할 이유가 있으면 그 이유를 적는다.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work to that branch.
