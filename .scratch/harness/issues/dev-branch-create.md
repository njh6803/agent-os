# dev-branch-create: dev를 main에서 따고 전환을 닫는다

**What to build:** 앞의 네 티켓(`dev-branch-transition`, `dev-review-bot-off`, `dev-base-tools`, `dev-base-skills-docs`)이 병합된 뒤에 `origin/dev`를 `origin/main`의 머리에서 따고, ADR 0043 Consequences "전환"을 닫는다. dev를 따는 일(아래 3)은 PR이 아니라 푸시 하나다. 따는 순간부터 도구가 `origin/dev`를 기준으로 쓴다(`dev-branch-transition`의 규칙). 닫을 때 할 일의 편집(아래)은 dev를 딴 뒤에 하므로, ADR 0043 Consequences "전환"("그 뒤에 연 PR부터 dev로")대로 그 PR은 dev로 간다. 그러면 main의 `.scratch/plan-head.md`는 다음 dev→main 출시 때까지 옛 문장을 든다. release-image 세션은 dev의 사본을 읽으므로 막히지 않지만, 이 시차를 PR 본문에 적는다.

순서는 이렇다.

1. 앞의 네 티켓이 모두 done이고 main에 병합됐는지 본다(`.scratch/harness/issues/`의 `Status:`와 `git log origin/main`).
2. **사람의 몫을 사용자에게 알리고 답을 받는다.** 아래는 GitHub 설정이라 사람이 하거나 사용자가 승인한 뒤에 한다. (가) `main`의 `required_linear_history`(`tools/protection.json`)가 dev→main의 merge 커밋을 막는다. 끌지, 관리자 우회(`enforce_admins: false`)에 기댈지 정한다. (나) `dev`를 보호 브랜치로 둘지와 필수 검사(`verify`), strict 여부. 정하면 `tools/protection.json`에 dev의 설정을 더한다. (다) LLM 호출 테스트를 main PR의 CI에서 돌리려면 API 키 시크릿이 필요하다(ADR 0043 Consequences "CI 분담"). 이 세션은 키를 다루지 않는다. 시크릿만 넣어서는 돌지 않는다. `ci.yml`에 그 테스트를 돌리는 잡이 아직 없기 때문이다. 사용자가 시크릿을 넣겠다고 하면, main을 base로 하는 PR과 main 푸시에서 `-m llm`을 돌리고 그 잡을 `verify`의 `needs`에 잇는 잡 구현을 이 티켓의 일로 하거나 후속 티켓(`ci-llm-job`)으로 쓴다. 넣지 않겠다고 하면 답만 적고 잡은 만들지 않는다. (라) `dev-base-skills-docs`가 찾아 넘긴 것 둘. 하나, dev에 strict 보호를 걸면 머리가 `main`인 되돌려 합치기 PR이 늘 `BEHIND`가 되어 관리자 우회 없이는 병합되지 않는다(`next-session` `merge.md`의 "되돌려 합치기"). (나)에서 strict를 정할 때 함께 답을 받는다. 둘, 원격의 기본 브랜치를 main에 둘지 dev로 옮길지 정한다. `/security-review`가 쓰는 `origin/HEAD`, 사용자 수준 `git-pr` 스킬이 감지하는 base, 앱의 `claude-code-action`이 기본 브랜치를 보는 곳이 거기에 달렸다(`docs/constitution/operations.md` 리뷰 파이프라인 2).
3. 사용자가 승인한 뒤에 먼저 `git fetch origin`으로 `origin/main`을 갱신하고 `git push origin origin/main:refs/heads/dev`로 dev를 딴다. 로컬 추적 ref가 낡았으면 낡은 커밋에서 dev가 선다. 딴 뒤 `git ls-remote origin refs/heads/main refs/heads/dev`의 두 커밋이 같은지 원격에서 본다.
4. dev를 딴 뒤 **다른 체크아웃**(주 체크아웃과 워크트리)은 `git fetch origin`을 쳐서 `origin/dev` 추적 ref를 받아야 한다. 받기 전에는 그 클론의 도구(`dev-branch-transition`이 정한 규칙)가 계속 main을 기준으로 쓴다. 2단계에서 원격의 기본 브랜치를 dev로 옮기기로 했다면 `git remote set-head origin dev`도 친다. `git fetch`는 기존 `origin/HEAD`를 바꾸지 않아, `origin/HEAD`를 기준으로 삼는 `/security-review`가 계속 main과 견준다. 기본 브랜치를 옮기지 않았으면 이 명령은 치지 않는다. 딴 직후의 보고와 새 세션 지시문의 "확인할 선행 조건"에 이 줄들을 싣는다.
5. 딴 뒤에 새 브랜치에서 `uv run python tools/sibling_overlap.py`와 `uv run python tools/check_ticket.py`가 dev를 기준으로 도는지 실제로 본다. 티켓 PR 하나를 dev로 열어 CI의 `ticket` 잡이 지나는지도 본다.

**닫을 때 할 일 넷.**

- `.scratch/plan-head.md`에서 release-image가 dev 전환을 기다린다고 적은 문장을 걷고, `.scratch/release-image/plan.md` 본문의 첫 문장과 ADR 0056 Consequences "dev 전환이 먼저다"가 가리키는 세 곳(전체 계획 머리, 기능 계획 본문, 일지 "다음"과 지시문)이 더는 전환을 기다리라고 말하지 않게 맞춘다. 걷은 뒤 `uv run python tools/plan_table.py`를 돌려 결과를 같은 커밋에 싣는다.
- 같은 전환을 문서 검색 서버 저장소(rag-engine)에 하라고 그 저장소의 세션에 줄 지시문을 **사용자에게 낸다**(그 저장소는 건드리지 않는다). 지시문에는 그 저장소가 agent-os의 규약 ADR을 따른다고 적고 다른 점만 적는 **얇은 ADR 한 장**을 두라는 요건을 싣는다. 공통 ADR 저장소와 공통 하네스 저장소는 두지 않고 일하는 방식의 원천은 agent-os이다(일지 2026-11-11-1532 "인계한 세션에서 사용자가 정했다").
- 지시문을 낼 때 대기열 `rag-engine-port-by-hand`(`.scratch/retro-queue/rag-engine-port-by-hand.md`)에 회차를 더한다(지금 0회차). 지시문 하나가 회차 하나다.
- 일지의 "다음"이 이 줄들을 걷는 시점은 지시문을 낸 뒤다. 지시문을 내기 전에는 `.scratch/plan-head.md`의 dev 전환 문단과 release-image 기능 계획 본문의 그 대목(지시문을 낸다는 문장)을 걷지 않는다.

**전환 뒤의 후보.** 두 저장소(`C:\project\agent`, `C:\project\rag-engine`)의 공통 파일을 비교해 벌어진 곳을 알리는 점검 도구가 다음 하네스 일이다(대기열 `rag-engine-harness-drift`, 사용자 승인 2026-11-11). 이 티켓이 하지 않고, 결과를 아침 보고에 싣는 것은 사용자가 확인하지 않았으니 그 티켓을 여는 세션이 사용자에게 묻는다.

**대기열:** rag-engine-port-by-hand, rag-engine-harness-drift

**Status:** done

**막는 티켓:** 앞의 네 티켓이 모두 done이다.

## 수용 기준

- [x] 사람의 몫 (가)~(다)를 사용자에게 알렸고 답을 티켓 끝에 적었다
- [x] `origin/dev`가 사용자 승인 뒤에 `origin/main`의 머리에서 섰고, 원격에서 읽은(`git ls-remote`) 두 브랜치의 커밋이 같다
- [x] 다른 체크아웃이 `git fetch origin`으로 `origin/dev`를 받아야 한다는 한 줄을 보고와 새 세션 지시문에 실었다
- [x] LLM 테스트 잡: 사용자가 시크릿을 넣겠다고 했으면 잡 구현(또는 후속 티켓 `ci-llm-job`)이 있고, 넣지 않겠다고 했으면 그 답이 티켓 끝에 있다
- [x] dev를 기준으로 `sibling_overlap`·`check_ticket`이 돌고 dev로 연 티켓 PR의 CI가 지났다
- [x] `.scratch/plan-head.md`에서 release-image가 dev 전환을 기다린다고 적은 문장이 걷혔고 `uv run python tools/plan_table.py` 결과가 같은 커밋에 실렸다
- [x] 문서 검색 서버 저장소에 줄 지시문을 사용자에게 냈고, 얇은 ADR 한 장 요건이 들었으며, `rag-engine-port-by-hand`에 회차를 더했다
- [x] 실제 이미지의 compose e2e 잡은 이 티켓이 만들지 않았다(release-image의 첫 티켓이 더한다)
- [x] 검증 명령이 모두 초록이다

## 결과

### 1. 사람의 몫의 답 (2026-11-12)

첫 선택 화면에서 사용자가 일반적인 관행을 조사한 뒤 다시 물어 달라고 해, 웹을 조사해 선택지 설명에 넣고 다시 물었다. 두 번 모두 같은 답이었다. 화면의 글과 답은 일지 2026-11-12-1148 "사람의 몫 (가)~(라)"에 글자 그대로 있다.

| 몫 | 답 | 반영 |
|---|---|---|
| (가) main의 `required_linear_history` | 끈다 | `tools/protection.json`을 고쳐 `gh api -X PUT .../branches/main/protection --input tools/protection.json`. 응답의 `required_linear_history.enabled`가 false |
| (나) dev 보호와 strict | 보호하되 strict는 끈다 | 새 파일 `tools/protection-dev.json`(필수 검사 `verify`, strict 끔, 선형 이력 끔, 강제 푸시·삭제 금지, 관리자 우회 허용)으로 PUT. 응답이 그 값 |
| (다) LLM 테스트 시크릿 | 넣겠다, 잡은 후속 티켓으로 | 후속 티켓 `.scratch/harness/issues/ci-llm-job.md`(ready-for-agent). 시크릿은 사용자가 넣는다 |
| (라) 원격의 기본 브랜치, 되돌려 합치기 PR의 strict | 기본 브랜치를 dev로 옮긴다. strict는 (나)에서 끔 | `gh api -X PATCH repos/njh6803/agent-os -f default_branch=dev`가 `dev`를 돌려줬다. `git remote set-head origin dev` 뒤 `git symbolic-ref refs/remotes/origin/HEAD`가 `refs/remotes/origin/dev` |

dev 보호를 `tools/protection.json`에 키로 더하지 않고 파일을 따로 둔 것은, 그 파일이 `gh api --input`이 그대로 읽는 브랜치 하나의 보호 본문이기 때문이다(KICKOFF.md 8단계를 읽었다). 근거의 종류: 응답 값은 명령의 `--jq` 출력이다.

### 2. dev를 땄다

`git fetch origin` 뒤 `git rev-parse origin/main`이 `82297e614`였고, `git push origin origin/main:refs/heads/dev`가 `[new branch]`로 끝났다. `git ls-remote origin refs/heads/main refs/heads/dev`의 두 줄이 모두 `82297e614241419f27290782641414d6a7fdecfc`였다(명령의 출력).

같은 클론의 워크트리는 주 체크아웃의 `.git`을 함께 쓴다(`git rev-parse --git-common-dir`가 `C:/project/agent/.git`). 그래서 이 워크트리의 fetch가 받은 `origin/dev`와 set-head가 바꾼 `origin/HEAD`는 주 체크아웃과 다른 워크트리에도 같다. `C:\project\agent\.git\refs\remotes\origin\HEAD`를 Read로 열어 `ref: refs/remotes/origin/dev`를 봤다. 기본 브랜치를 옮기기 전에 만든 다른 클론은 `git fetch origin`과 `git remote set-head origin dev`를 쳐야 한다. 그 뒤에 만든 클론은 원격의 HEAD(`git ls-remote --symref origin HEAD`가 `ref: refs/heads/dev`)를 따라 dev일 것으로 본다(어림이고 새 클론으로 재 보지 않았다). 주 체크아웃의 루트 브랜치는 아직 main이고, 다음 `tidy-checkouts`의 "main인데 루트 브랜치는 dev다" 갈래가 dev로 옮긴다.

### 3. dev를 기준으로 도는 도구

- `uv run python tools/sibling_overlap.py`가 형제 줄을 `origin/dev 82297e6`로 시작했고 겹침 없음으로 끝났다. `--journal`은 이 브랜치의 일지를 찍었다.
- `uv run python tools/check_ticket.py`가 종료 0이었다. `base_ref`를 직접 불러 보니 `chore/dev-branch-create`는 `refs/remotes/origin/dev`, `hotfix/01-x`는 `refs/remotes/origin/main`이었다(`uv run python -c`로 함수를 부른 출력).
- `dev-base-skills-docs` 결과 4가 넘긴 것: `hook_prompt_directive`의 안내 문구는 "기준 브랜치(main 이나 dev)"로 바뀌어 있었고, `sibling_overlap`의 `--journal`과 `check_constitution_version`은 `tools/base_rule.py`의 규칙을 쓴다(Grep으로 읽었다). 머리가 main인 되돌려 합치기 PR에서 claude-review가 도는지는 `.github/workflows/claude-code-review.yml`이 dev→main만 건너뛰므로 돈다(31~32행을 읽었다). `merge.md`는 그 PR에서 봇 회차를 하지 않으므로 리뷰는 돌되 반영하지 않는다. 바꾸지 않았다.
- dev로 연 이 티켓의 PR #541(base `dev`)이 머리 `bf761cfae`에서 CI를 지났다. `ticket` 잡이 9초에 통과했고, 필수 검사 `verify`와 `python`·`web`·`e2e`·`e2e-widget`·`e2e-portal`·`visual`이 모두 통과했으며, `tools/wait_ci.py`의 끝 줄이 `모두 통과. CodeRabbit: Finished`였다(명령의 출력).
- CodeRabbit의 첫 회차 Major 하나("출시 PR 병합 뒤 main을 dev에 되돌려 합치는 단계를 `operations.md`에 더하라")는 이 PR에서 고치지 않고 `dev-release-pr-step`에 넘겼다. 그 단계를 더할지, 출시 PR에서만 관리자 우회로 병합할지, main의 strict를 끌지는 사용자가 정할 보호 설정이 걸려 있고, 그 티켓이 첫 출시 PR로 재 보고 정한다. 그 티켓의 메모가 이미 같은 후보를 든다.

### 4. 닫을 때 할 일

- `.scratch/plan-head.md`의 dev 전환 문단과 `.scratch/release-image/plan.md` 본문의 첫 문장이 더는 전환을 기다리라고 말하지 않는다. ADR 0056 Consequences "dev 전환이 먼저다"는 조건문이라 고치지 않았다.
- 결정이 바뀐 곳을 참조하던 살아 있는 문서를 고쳤다. `next-session` `merge.md`("병합 방법"의 보호 설정 문단, "되돌려 합치기" 4의 `BEHIND`와 보호 설정 거절), `docs/constitution/operations.md`(가드레일의 보호 브랜치 줄, 병합 규칙의 거절 문장, 리뷰 파이프라인의 `origin/HEAD` 문단), `docs/agents/issue-tracker.md`(dev에 strict가 없을 때), `.github/workflows/ci.yml` 머리 주석(LLM 잡은 `ci-llm-job`).
- 리뷰 파이프라인의 `origin/HEAD` 문단은 "set-head로 옮기는 길은 쓰지 않는다"였다. 사용자가 (라)에서 그 비용(핫픽스 브랜치의 범위)을 보고 옮기기로 골라, 핫픽스 브랜치에서 범위를 `git merge-base origin/main HEAD` 이후로 좁히는 문장으로 바꿨다.
- PR 537 claude-review의 Nit 4(`merge.md` "되돌려 합치기" 3의 `--expect verify`가 이름을 박았다)는 dev의 필수 검사도 `verify`라 고칠 것이 없다.
- main이 strict라 둘째 출시 PR부터 `BEHIND`가 날 것이라는 어림을 `merge.md`와 `dev-release-pr-step`의 메모에 넘겼다. 출시 PR 뒤 dev가 원격에 남았는지 보는 확인도 그 티켓의 메모와 수용 기준에 넘겼다.
- What to build의 시차(main의 `plan-head.md`는 다음 출시 PR까지 옛 문장을 든다)는 이 티켓의 PR 본문에 적는다.

### 5. 문서 검색 서버 저장소에 줄 지시문

2026-11-12에 사용자에게 냈다. 대기열 `rag-engine-port-by-hand`의 1회차다. 그 세션에는 이 티켓의 PR이 dev에 병합된 뒤에 주라고 사용자에게 알렸다. 지시문이 읽으라는 파일 가운데 `tools/protection-dev.json`과 고친 `tools/protection.json`, 이 결과 절은 그 병합 전의 `origin/dev`에 없거나 옛 판이다(`git cat-file -e origin/dev:tools/protection-dev.json`이 128로 끝났고, `git show origin/dev:tools/protection.json`이 `"required_linear_history":true`였다). 지시문을 짓기 전에 그 저장소를 읽기만 했다(`tools/`의 이름, `.scratch/`·`.claude/skills/`·`docs/adr/`의 목록, ADR 0015의 머리, `git -C C:/project/rag-engine branch --show-current`가 main, `ls-remote --symref origin HEAD`가 main).

```text
다음 작업: 문서 검색 서버 저장소(rag-engine)를 agent-os의 브랜치 모델로 옮긴다. 티켓 PR은 dev로 가고, 기능이 끝나면 dev를 main에 병합 커밋으로 올리며, 핫픽스는 main에서 따서 main에 합친 뒤 dev에 되돌려 합친다(agent-os ADR 0043). 먼저 이 저장소에 얇은 ADR 한 장과 harness 티켓을 정한다
다음 단계: 짧은 설계 인터뷰. agent-os의 ADR 0043과 전환 티켓 다섯을 입력으로 받고, 새로 정할 것은 아래 "이 저장소가 정할 것"뿐이다
어디서: 새 세션. C:\project\rag-engine에서 연다
시작 프롬프트: /grill-with-docs rag-engine을 agent-os ADR 0043의 브랜치 모델(dev 전환)로 옮긴다
모델: Opus 5.5 / high
읽을 것: agent-os는 읽기만 하고 고치지 않는다. 아래 파일은 agent-os의 origin/dev에 있으니 `git -C C:/project/agent show origin/dev:<경로>`로 읽는다. docs/adr/0043-dev-integrates-and-main-releases.md(결정의 원천), .scratch/harness/issues/의 dev-branch-transition.md·dev-review-bot-off.md·dev-base-tools.md·dev-base-skills-docs.md·dev-branch-create.md(나눈 순서와 각 티켓의 결과 절. dev-branch-create의 결과 절은 그 PR이 dev에 병합된 뒤에 실린다), tools/base_rule.py(기준 브랜치 규칙), tools/protection.json과 tools/protection-dev.json(agent-os가 건 보호 설정)
이어받을 상태: (1) 공통 ADR 저장소와 공통 하네스 저장소는 두지 않고 일하는 방식의 원천은 agent-os다(사용자가 2026-11-11에 정했다). 그래서 이 저장소에는 agent-os ADR 0043을 따른다고 적고 다른 점만 적는 얇은 ADR 한 장을 둔다. 결정 본문을 옮겨 적지 않는다. (2) agent-os는 전환을 티켓 다섯으로 나눴다. 훅·커밋 검사·CI에 기준 브랜치 규칙(hotfix/*는 main, 그 밖은 origin/dev가 있으면 dev, 없으면 main)을 싣고, 리뷰 봇이 dev→main PR을 건너뛰게 하고, 나머지 도구를 그 규칙으로 바꾸고, 스킬과 규약 문서와 되돌려 합치기 순서(next-session merge.md)를 맞춘 뒤, 마지막 티켓이 사람의 몫을 정하고 dev를 땄다. 도구가 dev를 따는 순간부터 origin/dev를 기준으로 쓰므로, dev는 앞의 넷이 병합된 뒤에 땄다. (3) agent-os가 2026-11-12에 고른 GitHub 설정이다. 이 저장소의 설정은 사용자가 다시 정한다. main의 선형 이력 강제를 껐다(출시 PR이 병합 커밋이라서다). dev는 verify를 필수로 두되 엄격 모드와 선형 이력 강제를 끄고, 강제 푸시와 삭제를 막았다(엄격 모드에서는 머리가 main인 되돌려 합치기 PR이 늘 BEHIND가 된다). 기본 브랜치를 dev로 옮기고 git remote set-head origin dev를 쳤다. 그 뒤로 base를 주지 않은 gh pr create는 dev로 열리므로 핫픽스 PR은 --base main으로 연다. LLM 테스트의 CI 잡은 후속 티켓으로 미뤘다. (4) ADR 0043의 "잊으면 다음 dev→main에서 hotfix가 사라진다"는 agent-os 세션이 임시 저장소로 손으로 본 것과 어긋났다(커밋한 프로브는 없다, agent-os 일지 2026-11-12-0407-dev-base-skills-docs. 핫픽스를 main에만 두고 dev를 합쳐도 핫픽스는 남았다. 같은 곳을 고쳤으면 충돌이 난다). 이 문장은 옮기지 않는다. (5) 이 저장소가 정할 것: 스킬·도구·CI에서 main을 전제한 곳(이름이 같은 도구 check_ticket, hook_git_main_commit, hook_push_behind_main, sibling_overlap, tidy_checkouts, plan_table이 있다. agent-os와 내용이 같은지는 비교하지 않았다), CI 워크플로(ci.yml, claude-code-review.yml)의 트리거와 필수 검사 이름, GitHub 보호와 기본 브랜치(지금 main), 전환 때 열린 PR을 main으로 끝낼지. agent-os가 고친 도구를 복사할지 이 저장소에 맞게 고칠지는 이 저장소의 세션이 판단한다. (6) 두 저장소의 공통 파일을 비교해 벌어진 곳을 알리는 점검 도구는 agent-os의 다음 하네스 일이다(agent-os 대기열 rag-engine-harness-drift). 이 저장소의 일이 아니다
이번 요청 범위: 얇은 ADR 초안과 harness 티켓까지. ADR은 셀프 리뷰를 반영한 뒤 보여주고 승인을 받는다. dev를 따는 푸시와 GitHub 설정은 그 뒤의 티켓이 사용자의 답과 승인을 받고 한다
```
