# dev-base-skills-docs: 스킬과 규약 문서와 ADR 포인터를 기준 브랜치 규칙에 맞추고 핫픽스를 되돌려 합치는 순서를 적는다

**What to build:** `dev-branch-transition` 티켓의 "기준 브랜치 규칙"(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main)을 스킬과 문서에 싣는다. 하네스는 다음 실행에 바로 영향을 주는 코드이므로(`CLAUDE.md` 작업 규약 4) 바꾼 스킬은 새 세션에서 불러 본다.

- 스킬: `next-session`(`SKILL.md`, `merge.md`, `directive.md`), `tidy-checkouts`, `code-review`, `open-session`, `sync-design-system`(`SKILL.md`, `upload.md`, `import.md`), `retro`, `writing-for-agents`. 곳마다 `main`이 기준 브랜치를 뜻하는지(바꾼다), 운영 브랜치를 뜻하는지(그대로 둔다), 둘 다 가능한지를 가른다. 지시문의 "확인할 선행 조건"과 `merge.md`의 "워크트리에서 병합할 때"는 병합 대상이 dev일 때와 main일 때를 가른다. 병합은 티켓 PR은 dev로 squash, dev→main은 merge 커밋(`gh pr merge --merge`, 사용자 승인 없음)이다.
- **되돌려 합치기를 `next-session`의 `merge.md`에 적는다.** hotfix를 main에 합친 세션이 바로 main을 dev에 merge 커밋으로 합친다(ADR 0043 Consequences "되돌려 합치기"). 이 티켓이 정할 것은 둘이다. (가) 되돌려 합치기를 PR(머리 `main`, base `dev`)로 하는지 로컬 병합 뒤 푸시로 하는지. 직접 푸시는 `dev`를 막는 훅이 `git commit`만 보므로 병합 커밋을 지나가지만, 보호 설정과 맞는지 본다. (나) 잊지 않게 하는 계기. `hook_pr_next_session`이 hotfix 병합 뒤 지시문에 이 단계를 싣게 할지 정한다.
- 문서: `CLAUDE.md`의 환경 함정, `docs/constitution/operations.md`의 "브랜치와 병합"과 "가드레일"과 "리뷰 파이프라인", `docs/agents/issue-tracker.md`(규약 첫 항목의 "main에 들어가는 PR", 전체 계획 절의 "나란히 돈 마지막 티켓 둘" 문단. 그 문단은 ADR 0043 전환을 맡는 harness 티켓이 다시 정한다고 적었다), `.github/PULL_REQUEST_TEMPLATE.md`, `CONTEXT.md`의 용어(이미 든 개발 브랜치 용어와 맞는지).
- ADR 포인터: ADR 0005의 "squash 병합, main 이력은 PR 단위"와 ADR 0037의 "main에 들어가는 PR은 모두 티켓 파일 하나를 가리킨다" 문장 바로 뒤에 ADR 0043을 가리키는 `(바뀜: ADR 0043)`를 단다. `.claude/rules/adr.md`의 규칙대로 `tools/check_adr_pointers.py`가 통과해야 한다.
- 사용자 수준 스킬 `~/.claude/skills/git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`는 저장소 밖이다. 어디서 `main`을 박았는지만 읽어(고치지 않고) 목록으로 만들고 티켓 끝에 적어, 사용자에게 고칠지 묻는다. 고치는 것은 사용자가 승인했을 때만 한다. 읽은 목록에 저장소 밖 파일의 내용을 옮기지 않는다.

**대기열:** 없음

**Status:** done

**막는 티켓:** `dev-branch-transition`이 병합된 뒤에 한다. 크기가 한 세션에 안 들면 스킬 몫과 문서 몫으로 나누고 새 티켓 파일을 쓴다.

## 수용 기준

- [x] 스킬마다 `main`의 뜻을 가른 표가 티켓 끝에 있고, 바꾼 스킬은 새 세션에서 불러 보았다
- [x] 되돌려 합치기의 순서와 계기가 `merge.md`에 적혀 있고, 위 (가)(나)의 결정과 까닭이 티켓 끝에 있다
- [x] 규약 문서의 "main에 PR한다"는 문장이 기준 브랜치 규칙으로 바뀌었고 옛 표현의 잔존이 살아 있는 문서에 0이다(`CLAUDE.md` 작업 규약 4의 grep)
- [x] ADR 0005와 0037에 포인터가 달렸고 `tools/check_adr_pointers.py`가 통과한다
- [x] 사용자 수준 스킬의 `main` 박힌 곳 목록이 티켓 끝에 있다. 사용자에게 고칠지 묻는 일은 병합 뒤 마무리 보고가 한다(PR 병합까지가 이 세션의 범위라 이 상자 밖이다)
- [x] 검증 명령이 모두 초록이다(셀프 리뷰 반영 뒤 `run_checks.py`와 ruff 둘, 아래 "셀프 리뷰 반영"에 결과를 적었다)

## 결과

### 1. 곳마다 `main`의 뜻을 가른 표

기준 브랜치는 `docs/constitution/operations.md` "브랜치와 병합"의 첫 항목이 원천이다. 루트 브랜치(주 체크아웃이 따르는 브랜치)는 `tidy-checkouts`가 정하고 `CONTEXT.md`에 올렸다. 판은 "바꾼다"(기준 브랜치나 루트 브랜치로), "그대로"(운영 브랜치거나 main이 브랜치 이름이 아니다), "문장 더함"이다.

| 곳 | `main`의 뜻 | 판 |
|---|---|---|
| `next-session/SKILL.md` 형제 설명 | 병합처(기준 브랜치) | 바꾼다 |
| `next-session/SKILL.md` 칩(`spawn_task`) | 기본 브랜치 = 운영 브랜치. 칩은 거기서 뜨고 티켓 PR은 dev로 병합된다 | 문장을 바꾼다("`origin/<기준 브랜치>`를 받아 시작") |
| `next-session/SKILL.md` 대기열 도구의 `--ref` | 병합처 | 바꾼다 |
| `next-session/SKILL.md` 결정표 | — | 첫 줄을 더한다(되돌려 합칠 것이 남았는가) |
| `next-session/directive.md` 1(티켓 이름 겹침), 3(캐시가 되는 예) | 기준 브랜치 | 바꾼다 |
| `next-session/directive.md` 5(워크트리 문장 조건) | 루트 브랜치 | 바꾼다 |
| `next-session/directive.md` 6(주 체크아웃 미갱신) | 병합 대상이 dev냐 main이냐에 따라 새 세션이 낡은 정도가 다르다 | 둘을 가른 문장을 더한다 |
| `next-session/merge.md` 병합 길(4) | 둘 다(기준 브랜치가 dev일 때 `/git-pr-merge`는 쓰지 않는다) | 문장을 더하고 "병합 방법" 표를 신설한다 |
| `next-session/merge.md` "워크트리에서 병합할 때" 머리말·1·2·3·5 | base(PR 종류마다 main이나 dev) | 바꾼다 |
| `next-session/merge.md` "되돌려 합치기" | main→dev | 신설한다 |
| `tidy-checkouts/SKILL.md` 설명·머리말·2·끝·하지 않는 것 | 루트 브랜치 | 바꾼다. 루트 브랜치 정의를 더한다 |
| `tidy-checkouts/SKILL.md` 3의 병합 판정(`origin/main`에 닿는지) | 병합처 | 그대로 두고 문장을 더한다. 어느 ref들에 닿으면 병합으로 볼지는 `dev-base-tools`가 도구 독스트링에 정한다 |
| `tidy-checkouts/SKILL.md`의 `main.log` | 앱 로그 파일 이름 | 그대로 |
| `code-review/SKILL.md` 고정점 예와 이유 | 예시 ref | 바꾼다. 셀프 리뷰의 고정점이 기준 브랜치임을 더한다 |
| `code-review/SKILL.md` 4단계의 "main session" | 주 세션(브랜치가 아니다) | 그대로 |
| `open-session/SKILL.md` 1(루트가 `[main]`이 아니다), 6(`origin/main`에서 따기) | 루트 브랜치, 기준 브랜치 | 바꾼다 |
| `retro/SKILL.md` 손상 정의 | 둘 다 | "main이나 dev"로 바꾼다 |
| `retro/SKILL.md` 만료의 `--ref origin/main` | 병합처 | 바꾼다 |
| `sync-design-system/SKILL.md` 53·61·79, `import.md` 5·11·12·13·61 | 기준 브랜치와 루트 브랜치 | 바꾼다 |
| `sync-design-system/SKILL.md`의 `main.ts` | 파일 이름 | 그대로 |
| `sync-design-system/upload.md` 1·2(`origin/main`을 분리 HEAD로) | 병합처 | 바꾼다 |
| `sync-design-system/upload.md` 3·5의 `via: agent-os main@<SHA>` | 색인 형식의 고정된 표지. 이미 올라간 색인이 이 꼴이다 | 그대로 두고 표지임을 적는다 |
| `writing-for-agents`, `next-session/handoff.md` | `main`이 든 곳이 영어 낱말이거나 없다 | 그대로 |
| `.claude/agents/bug-perf-review.md` | 기준 | 바꾼다 |
| `.claude/rules/adr.md` | 병합처 | 바꾼다 |
| `.github/PULL_REQUEST_TEMPLATE.md` `/security-review` 줄 | 병합처 | 바꾼다 |
| `CLAUDE.md` 환경 함정 넷 | 기준·병합처 | 바꾼다. 로컬 브랜치 줄에 dev를 더하되 dev로는 재 보지 않았다고 적는다 |
| `docs/constitution/operations.md` 브랜치와 병합 | 기준 브랜치 | 규칙을 한 항목으로 신설하고 병합 방법(squash와 merge 커밋)과 보호 브랜치 둘을 적는다 |
| `docs/constitution/operations.md` 가드레일 | main 보호 설정 | main 문장은 그대로 두고 dev의 보호는 `dev-branch-create`가 정한다고 적는다. 선형 이력과 strict가 부르는 일을 더한다 |
| `docs/constitution/operations.md` 리뷰 파이프라인 | `origin/main`(2026-09 관찰의 명령), `/security-review`의 `origin/HEAD` | 관찰의 명령은 그대로(기록). `/security-review`는 기준 브랜치가 dev일 때 범위를 손으로 좁히라는 문장을 더한다 |
| `docs/constitution/operations.md` 헌법 판 검사의 `origin/main` | 도구의 비교 대상 | 그대로. `dev-base-tools`의 몫 |
| `docs/agents/issue-tracker.md` 첫 항목·병합 충돌·나란히 돈 마지막 티켓 | 기준 브랜치 | 바꾼다. 마지막 문단은 이 티켓이 다시 정했다(dev에 strict가 없으면 늦게 병합하는 세션이 직접 시험을 돈다) |
| `CONTEXT.md` 용어 | 이미 든 용어와 맞다 | "루트 브랜치"를 더하고 "최신 일지"의 `main`을 기준 브랜치로 바꾼다 |
| ADR 0005, 0037 | 포인터 | 이미 `(바뀜: ADR 0043)`가 달려 있었다(ADR 0043을 들인 PR이 달았다). `tools/check_adr_pointers.py`가 통과한다 |

바꾼 스킬은 새 세션에서 불러 보았다. `claude -p --model claude-sonnet-5-5`를 이 워크트리에서 띄워 Skill 도구로 `next-session`·`tidy-checkouts`를 불러 새 결정표 첫 줄과 루트 브랜치 문단이 본문에 있는 것을, 다시 `code-review`·`open-session`·`retro`·`sync-design-system`을 불러 고친 문구가 본문에 있는 것을 글자 그대로 인용으로 확인했다.

바꾼 하네스 파일 열둘(스킬 본문과 하위 파일, 규칙, 서브에이전트)마다 카나리아 명세를 `.scratch/harness/probes/canary/dev_base_*.toml`로 새로 쓰고 `claude -p`(2.1.322)로 돌렸다. 모두 통과 4다(실험군 3, 대조군 1). 첫 판은 둘이 실패했다. ADR 규칙 명세는 카나리아 명령이 `CLAUDE.md`에도 있어 대조군이 흘렸고, 결정표 명세는 "다음 단계" 칸을 물어 새 문장이 있는 "시작 프롬프트" 칸을 놓쳤다. 두 명세를 고쳐 다시 돌려 통과했다. open-session 명세는 통과 4 가운데 "없음" 섞인 둘이 있다(질문 표현이 어색해 "없음"으로 시작했다가 정정한 회차이고 셋 모두 새 문구를 옮겼다).

### 2. 되돌려 합치기의 결정 (가)(나)

- **(가) PR로 한다. 머리가 `main`이고 base가 `dev`인 PR을 열어 merge 커밋으로 병합한다.** 까닭 셋. CI의 `verify`가 합친 결과를 돌려 본다. 로컬 병합 뒤 푸시는 `dev` 위의 커밋을 막는 훅이 `git commit`만 봐서 병합 커밋이 지나가지만(`tools/hook_git_main_commit.py`) 필수 검사 없이 dev의 머리가 바뀌고 관리자 우회에 기댄다. 머리가 `main`인 PR은 커밋 검사가 면제로 지나므로 티켓이 필요 없다(`dev-branch-transition`이 이미 만들었다). 치르는 값 둘. dev에 strict 보호를 걸면 머리가 main인 PR이 늘 `BEHIND`라 관리자 우회 없이는 병합되지 않고, 이때 "Update branch"나 `gh pr update-branch`를 치면 dev를 main에 합치는 사고가 난다(`merge.md`가 막는다). 충돌이 나면 PR 안에서는 풀 수 없다(머리가 보호 브랜치 main이다). 두 경우 모두 병합하지 않고 사용자에게 넘기게 했다. strict와 관리자 우회는 `dev-branch-create`가 사용자와 정하며 그 티켓에 이 사실을 넘겼다.
- **(나) 계기는 스킬 둘이고 훅은 바꾸지 않았다.** 하나, `merge.md`의 병합 길(4)과 끝 줄이 "핫픽스면 되돌려 합치기까지 해야 끝"이라고 말한다. PR을 연 세션은 이 파일을 따르므로 계기가 된다. 둘, `next-session` 결정표의 첫 줄이 `git fetch origin` 뒤 `git diff --quiet origin/dev...origin/main`이 1이면 어느 세션이든 "되돌려 합치기"를 먼저 하게 한다. 첫째를 잊고 세션이 끊겨도 다음 병합 뒤의 어느 세션이 잡는다. 훅(`hook_pr_next_session`)은 명령 한 줄만 보고 PR의 머리 브랜치를 모르므로 바꾸지 않았다. 훅이 `gh pr view`를 부르려면 네트워크 호출이 훅에 들어간다.
- **판정을 쟀다.** `git diff --quiet origin/dev...origin/main`의 종료 코드가 장면 일곱에서 기대대로 나왔다. 출시 직후(main에 merge 커밋만 더 있다)는 0이고 핫픽스가 main에만 있을 때만 1이다. 프로브는 `.scratch/harness/probes/backmerge_diff_check.sh`이고 README 표에 줄을 더했다.

### 3. 루트 브랜치 결정 (`dev-base-tools`가 이 티켓에 넘긴 질문)

주 체크아웃이 따르는 브랜치는 `origin/dev`가 있으면 dev, 없으면 main이다. 까닭은 새 세션과 훅이 루트의 하네스(스킬·훅·규칙)로 돌고 티켓 PR이 dev로 병합되기 때문이다. 루트가 main에 머물면 dev로 병합한 하네스가 출시 PR 전까지 새 세션에 닿지 않는다. 핫픽스는 main으로 병합되지만 루트는 따르지 않는다(핫픽스가 dev에 오는 길은 되돌려 합치기다). 그래서 `tidy-checkouts` 2에 "main인데 루트 브랜치는 dev다" 갈래를 더해, 깨끗하고 로컬 main에 원격에 없는 커밋이 없으면 dev로 옮기게 했다. 병합 판정(`tools/tidy_checkouts.py`의 `origin/main`에 닿는지)에 `origin/dev`를 더할지는 `dev-base-tools`가 도구에서 정한다. 스킬 3의 문장이 그 독스트링을 원천으로 가리킨다.

### 4. 이 티켓이 찾아 다른 곳에 넘긴 것

- `dev-base-tools`: `tidy_checkouts`의 병합처(위 3), `hook_prompt_directive`의 안내 문구 "병합한 main", `sibling_overlap`의 `--journal`과 CONTEXT.md "최신 일지" 정의의 기준 브랜치 읽기, `check_constitution_version`의 `origin/main`.
- `dev-review-bot-off`: 머리가 `main`인 되돌려 합치기 PR에도 claude-review가 도는지. 합치는 내용은 main에서 이미 리뷰한 핫픽스뿐이다. 이 티켓의 `merge.md`는 그 PR에서 봇 회차를 하지 않는다고 적었다.
- `dev-branch-create`: dev의 strict와 선형 이력, 원격의 기본 브랜치(main에 둘지 dev로 옮길지). 기본 브랜치는 `/security-review`의 `origin/HEAD`와 사용자 수준 `git-pr`의 base 감지가 달렸다. 티켓에 항목 (라)로 더했다.
- 새 티켓 `dev-release-pr-step`: 출시 PR을 여는 계기와 순서를 어느 티켓도 맡지 않았다. ADR 0043은 "기능을 끝낸 세션이 연다"고만 적었다. `merge.md`는 그 PR의 병합 방법만 정했다.

### 5. 사용자 수준 스킬에서 `main`이 박힌 곳 (읽기만 했고 고치지 않았다)

저장소 밖 `~/.claude/skills/<이름>/SKILL.md`다. 줄 번호와 어떤 박힘인지만 적고 내용은 옮기지 않았다. 고치는 것은 사용자가 승인했을 때만 한다.

| 스킬 | 줄 | 박힘의 종류 | dev가 서면 생기는 일 |
|---|---|---|---|
| `git-pr` | 22, 28 | base를 원격 HEAD로 감지하고 실패하면 `main`. 현재 브랜치가 base면 멈춘다 | 원격의 기본 브랜치가 main이면 티켓 PR이 base `main`으로 열린다 |
| `git-pr-merge` | 11, 28, 46~47, 82~86 | 병합 뒤 `main`으로 돌아가 당긴다. base가 `main`이 아니면 사용자에게 알린다 | base가 dev인 PR에서 멈추거나 루트를 main으로 되돌린다 |
| `git-pr-feedback` | 3, 11, 85, 89 | 충돌 때 `main`을 당겨 합친다 | 티켓 PR의 충돌을 dev가 아니라 main으로 푼다 |
| `git-branch` | 56, 60, 100 | 기본 브랜치를 감지하고 실패하면 `main`. `main`에 직접 커밋하지 않는다는 문장 | 새 브랜치를 main에서 딴다 |

`merge.md`와 `operations.md`는 지금 이 스킬들이 dev를 가르치지 못하므로 base가 dev인 PR은 `/git-pr-merge`를 쓰지 않고 "워크트리에서 병합할 때" 길을 쓰게 했다. `git-pr`의 base 감지와 `git-branch`의 브랜치 따기는 같은 우회가 없다. 원격의 기본 브랜치를 바꾸거나(`dev-branch-create`의 결정) 이 스킬들을 고쳐야 한다.

**사용자에게 묻는다:** 위 네 스킬을 기준 브랜치 규칙에 맞게 고칠지. 이 세션의 마무리 보고가 묻는다.

### 6. 셀프 리뷰 반영

표준 축과 명세 축이 지적한 것을 고쳤다. 판정과 근거는 일지 `2026-11-12-0407-dev-base-skills-docs.md`의 "셀프 리뷰"와 "셀프 리뷰 반영"에 있다. 이 표의 1절에 더 적는 가름은 둘이다.

| 곳 | `main`의 뜻 | 판 |
|---|---|---|
| `implement/SKILL.md` 11행(주 체크아웃이 main도 이 티켓의 브랜치도 아닐 때) | 루트 브랜치 | 바꾼다 |
| `.claude/rules/adr.md` 17행("main에 이미 있던 같은 번호") | 기준 브랜치 | 바꾼다 |

`merge.md`에서 바꾼 것: 출시 PR을 `/git-pr-merge` 예외에 넣었고, 병합 명령의 머리 SHA를 PR 종류마다 정했으며, 보호 설정(`required_linear_history`)에 걸리면 사용자에게 넘기게 했고, "되돌려 합치기"에 dev가 없을 때의 갈래와 대기 명령(`wait_ci.py --head … --expect verify`)과 사용자에게 넘긴 뒤의 열린 PR 처리를 적었다. 결정표 첫 줄은 병합 뒤에만, 열린 PR이 없을 때만 고르고 끝나면 표로 돌아가게 했다. 핫픽스가 dev에 없을 때의 해를 "되돌린다"에서 "충돌할 수 있다"로 고쳤다(ADR 0043 33행의 "사라진다"와 어긋나며, ADR은 이 PR에서 고치지 않았다).
