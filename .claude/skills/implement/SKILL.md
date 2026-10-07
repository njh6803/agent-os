---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 일곱을 더했다. 시작 전 브랜치 규약 포인터, 워크트리 먼저(next-session 3단계와 주 체크아웃의 자기 점검), 루프 중의 린트, 빨강을 본 적 없는 테스트의 변이 도구 포인터(pytest 밖, 다른 워크트리, `--check`), 이 티켓의 몫만 쓰기(대기열 35), 설치한 판과 측정한 판의 견줌(대기열 61), 마칠 때 세션 경계(원천은 next-session 스킬). 근거는 일지 2026-09-21 첫 슬라이스 회고 뒤 대화, 인터럽트 설계 뒤 대화, 티켓 01 회고, 세션 경계 일지, 대기열 29·35·59·61. -->

Implement the work described by the user in the spec or tickets.

시작 전에 브랜치를 `docs/constitution/operations.md`의 규약대로 딴다. 티켓마다 `feature/<NN>-<slug>` 브랜치 하나, PR 하나. 지시문의 "어디서" 줄이 워크트리를 말하면(조건은 next-session 3단계) 그 문장대로 워크트리에 먼저 들어가고 거기서 브랜치를 다룬다. 지시문이 없어도, 작업 폴더가 주 체크아웃인데 `git branch --show-current`가 main도 이 티켓의 브랜치도 아니거나, main인데 `git status --porcelain`이 비지 않았으면 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`로 간다(이 티켓의 브랜치면 주 체크아웃에서 끊은 작업을 잇는 것이다) — 같은 체크아웃의 다른 세션이 그 브랜치 전환으로 커밋 대상을 잃는다(일지 2026-09-23-02). 새 워크트리에 들어가면 먼저 `uv sync`와 `pnpm -C web install --frozen-lockfile`을 친다. 스토리 테스트의 chromium은 워크트리마다가 아니라 기계마다 깔리므로, `pnpm -C web verify`가 브라우저가 없다며 빨가면 그때 `pnpm -C web exec playwright install --only-shell chromium`을 친다(`docs/constitution/operations.md` 가드레일). 예외를 제안하려면 이유와 그 이유가 사라지는 조건을 같이 적고, 조건이 차면 규약으로 돌아간다.

Use /tdd where possible, at pre-agreed seams.

이 티켓의 체크박스가 요구하는 것만 쓴다. 다음 티켓에 걸릴 것(형제 티켓이 붙일 라우트의 독스트링, "재개 라우트도 같다" 같은 미래형 문장)은 그 티켓 파일의 메모로 넘긴다. 세 번 명세 축 리뷰가 잡아 한 바퀴씩 들었다(대기열 35).

의존성을 더하거나 올리면 설치된 판을 명세·ADR이 근거로 든 측정의 판(그 프로브의 README 줄)과 견준다. major가 다르면 그 측정을 다시 돌린다(대기열 61, 규약은 `docs/agents/issue-tracker.md`의 프로브와 근거 절).

Run linting and typechecking regularly, single test files regularly, and the full test suite once at the end. red가 예상보다 넓으면 린트를 먼저 돌린다. 이름 충돌과 import 문제는 테스트 실패로 위장한다.

구현 전부터 초록인 테스트(순서나 경계를 고정하는 가드)와 구현 뒤에 쓴 테스트는 빨강을 본 적이 없다. 그 테스트가 지키는 코드에 `tools/mutate.py`로 변이를 넣어 빨강을 본다. pytest 밖의 테스트(Vitest, Playwright, tsc)도 같은 도구다. 변이마다 기대를 변이 파일(TOML)에 적는다. 수십 분 도는 변이 열은 커밋한 뒤 다른 워크트리에서 돌리고 이 체크아웃에서는 계속 일한다. 코드를 옮기거나 고쳤으면 그 코드를 겨누던 변이 파일을 `--check`로 본다. 형식과 절차는 그 도구의 독스트링이다.

Once done, use /code-review to review the work.

Commit your work to that branch.

거기서 멈춘다. 다음 티켓은 새 세션이 한다. 이유와 다음 세션 지시문은 next-session 스킬이 원천이고, 사용자가 `/git-pr`로 PR을 열면 훅이 그 계기를 넣는다.
