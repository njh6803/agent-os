# dev-branch-transition: dev 브랜치 전환의 첫 몫. 기준 브랜치 규칙을 정하고 훅과 커밋 검사와 CI 트리거에 싣는다

**What to build:** ADR 0043 Consequences "전환"을 한다. 그 일은 한 세션에 들지 않아 티켓 다섯으로 나눈다(아래 "나눈 티켓"). 이 티켓은 그 첫 몫이고, 나머지 넷이 따를 **기준 브랜치 규칙**을 정해 커밋을 막는 훅, 푸시 훅, 커밋 검사, CI 트리거에 싣는다.

**기준 브랜치 규칙.** 이 티켓이 정하고 나머지 티켓이 그대로 쓴다.

- 브랜치 `main`과 `dev`는 보호 브랜치다. 그 위의 커밋은 훅이 막고, 커밋 검사는 그 브랜치를 지난다.
- 기준 브랜치(PR의 base이고 워크트리를 딸 자리)는 브랜치 접두로 가른다. `hotfix/*`는 `main`이다. 그 밖(`feature/*`, `chore/*`, `docs/*`와 앱이 만든 이름)은 `dev`이다.
- **`origin/dev`가 아직 없으면 그 밖의 기준도 `main`이다.** 전환의 티켓들이 main에 병합되는 동안과 dev를 따기 전까지 도구가 지금처럼 돌게 하는 값이다. dev를 따는 일은 마지막 티켓(`dev-branch-create`)이 하고, 그 순간부터 같은 도구가 dev를 기준으로 쓴다. 도구마다 따로 판정하지 않도록 판정 문장은 여기서 한 번 정한다. 훅은 단독 실행 스크립트라 서로 import하지 않으므로(`.claude/rules/tools.md`) 훅마다 같은 짧은 함수를 둔다.
- dev→main PR(머리가 `dev`)과 main→dev 되돌려 합치기(머리가 `main`)는 티켓 하나를 가리키지 않으므로 커밋 검사의 CI 판정이 지난다(ADR 0043 Consequences "티켓 검사와 봇").

**고치는 곳.**

- `tools/hook_git_main_commit.py`: 보호 브랜치에 `dev`를 더한다. `git merge`가 만드는 병합 커밋은 `git commit` 명령이 아니라 이 훅이 보지 않는다. 그 사실(되돌려 합치기가 이 훅에 걸리지 않는다)을 독스트링의 못 보는 것에 적고 시험으로 고정한다.
- `tools/hook_push_behind_main.py`: 뒤처짐을 `origin/main`이 아니라 위 규칙의 기준 브랜치로 잰다(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main). fetch도 그 브랜치를 받는다. 보호 브랜치(`main`, `dev`) 위에서는 재지 않는다. 안내문의 "origin/main"과 "main을 합쳐야"를 기준 브랜치 이름으로 바꾼다.
- `tools/check_ticket.py`: 로컬 판정의 기준(`BASE`)을 위 규칙으로 정하고, 보호 브랜치(`main`, `dev`)와 CI의 머리 브랜치가 `main`이나 `dev`인 PR을 판정 1로 지나게 한다. CI 판정은 PR의 base 커밋을 받으므로 base 쪽은 바꾸지 않는다. 독스트링의 판정 1·2를 기준 브랜치로 고치고, 아래 "전환" 절 등의 `origin/main`은 판정 2의 한 문장(아래 설명의 `origin/main`은 이 기준 ref로 읽는다는 말)으로 갈음한다.
- `.github/workflows/ci.yml`: 푸시 트리거를 `main`과 `dev`로 넓힌다(PR은 base를 가리지 않고 돈다). 머리 주석에 dev PR과 main PR의 분담을 적는다. LLM 호출 테스트와 실제 이미지의 compose e2e를 main PR에서만 돌리는 일은 이 티켓이 하지 않는다(아래 "하지 않는 것").
- 위 변경마다 `tests/tools/`의 시험, `tools/hook_payloads.toml`의 발동·침묵 입력(막는 훅이 `dev`를 막는 입력과 `feature/x`를 막지 않는 입력), 변이 표가 있으면 그 표를 고친다.

**나눈 티켓.** 이름은 `.scratch/harness/issues/`의 파일이고 모두 `ready-for-agent`다. 앞의 넷은 서로 겹치는 파일이 없어 나란히 돌 수 있고, 다섯째는 앞의 넷이 병합된 뒤에 한다.

1. `dev-branch-transition`(이 티켓): 규칙, 훅 둘, 커밋 검사, CI 트리거.
2. `dev-review-bot-off`: 리뷰 봇 워크플로(`claude-code-review.yml`)가 dev→main PR을 건너뛰게 한다. 그 파일을 바꾼 PR은 봇이 건너뛰므로 별도 PR이다(`docs/constitution/operations.md` 리뷰 파이프라인).
3. `dev-base-tools`: 나머지 도구(`sibling_overlap`, `tidy_checkouts`, `mutate`, `wait_ci`, `morning_*`, `rerun_*`, `hook_prompt_directive`, `hook_pr_head_sync`)가 `origin/main`을 기준으로 박은 곳을 규칙으로 바꾼다.
4. `dev-base-skills-docs`: 스킬(`next-session`, `tidy-checkouts`, `code-review`, `open-session`, `sync-design-system`, `retro`), `CLAUDE.md`, `operations.md`, `issue-tracker.md`, PR 서식, ADR 포인터(0005, 0037), 용어집을 규칙에 맞추고 핫픽스를 main에 합친 세션이 main을 dev에 되돌려 합치는 순서를 `next-session`의 merge.md에 적는다.
5. `dev-branch-create`: dev를 main에서 따고 전환을 닫는다(사람의 몫과 문서 검색 서버 저장소의 지시문 포함).

**하지 않는 것.** dev를 따지 않는다(티켓 5). 사용자 수준 스킬(`~/.claude/skills/git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`)은 저장소 밖이라 이 티켓들이 고치지 않고 티켓 4가 어떻게 하는지 정한다. 실제 이미지의 compose e2e 잡은 만들지 않는다(release-image의 첫 티켓이 Dockerfile·compose와 함께 더한다. ADR 0056 결정 "실제 이미지로 띄우는 시험"). LLM 호출 테스트를 CI의 main PR에 더하는 일은 API 키 시크릿을 사람이 넣어야 해서 티켓 5의 사람 몫에 둔다. 메인 보호의 `required_linear_history`가 merge 커밋을 막는 문제도 티켓 5의 사람 몫이다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 기준 브랜치 규칙이 이 티켓의 "기준 브랜치 규칙" 절로 서 있고 나머지 네 티켓이 이 파일을 가리킨다
- [x] `hook_git_main_commit`이 `dev` 위의 `git commit`을 막고 `main`을 그대로 막으며, `git merge`로 만든 병합 커밋은 막지 않는다는 시험이 있다
- [x] `hook_push_behind_main`이 `hotfix/*`는 `origin/main`에, 그 밖은 `origin/dev`가 있으면 그것에, 없으면 `origin/main`에 견주고, 보호 브랜치 위에서는 재지 않는다. 갈래마다 시험이 있다
- [x] `check_ticket`이 로컬에서는 같은 규칙으로 기준을 고르고, `dev`·`main` 브랜치와 머리 브랜치가 `dev`·`main`인 PR을 지나며, `origin/dev`가 없는 저장소는 `origin/main`으로 돈다. 갈래마다 시험이 있다
- [x] `ci.yml`이 `dev` 푸시에서도 돈다. 필수 검사의 모음 잡 `verify`는 그대로다
- [x] `tools/hook_payloads.toml`과 `tools/run_hooks.py`가 통과하고 변이 표가 있는 훅은 `tools/mutate.py`로 새 갈래를 깨어 빨강을 본다
- [x] 나머지 네 티켓 파일이 `ready-for-agent`로 서 있고 `.scratch/harness/issues/`의 서식을 따른다
- [x] 이 티켓은 `origin/dev`가 없는 채로 병합되고 병합 뒤 모든 도구가 지금처럼 `main`을 기준으로 돈다(규칙의 "dev가 아직 없으면" 갈래)
- [x] 검증 명령이 모두 초록이다
