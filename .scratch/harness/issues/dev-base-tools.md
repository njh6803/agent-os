# dev-base-tools: `origin/main`을 기준으로 박은 도구를 기준 브랜치 규칙으로 바꾼다

**What to build:** `dev-branch-transition` 티켓의 "기준 브랜치 규칙"(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main)을 나머지 도구에 싣는다. 대상은 `tools/`에서 `origin/main`·`main`을 기준으로 박은 곳이다.

- `tools/sibling_overlap.py`: 형제(병합된 기준 브랜치, 열린 PR의 head, 다른 워크트리)와 merge-base의 기준을 규칙으로 바꾼다. 이 도구가 가장 크고 독스트링이 `origin/main`을 수십 번 든다. 열린 PR의 head를 모을 때 PR의 base도 본다. dev를 기준으로 할 때 main이 앞서 가진 번호(ADR, 헌법 판)는 main에도 있는 것으로 센다(dev→main 사이에 hotfix가 낀 경우)는 점을 시험으로 고정한다.
- `tools/tidy_checkouts.py`: 병합 판정의 `origin/main`(분리 HEAD가 닿는지, 체크아웃되지 않은 브랜치의 끝이 닿는지)을 규칙의 기준으로 바꾼다. `PROTECTED_BRANCHES`에 `dev`를 더한다. 루트가 main에 있다는 전제(주 체크아웃을 `origin/main`으로 당긴다)는 `dev-base-skills-docs`가 스킬에서 정하므로, 이 티켓은 도구가 기준을 둘 다(`origin/main`과 `origin/dev`)로 보는 것이 안전한지부터 정한다. 지우는 길이므로 `.claude/rules/tools.md`의 반박 시험 항목대로 임시 저장소에서 판정을 깨려는 입력으로 반박한다.
- 나머지: `tools/mutate.py`(`origin/main`이 기본 비교 대상), `tools/wait_ci.py`(충돌 안내 문구), `tools/morning_collect.py`·`tools/morning_sources.py`·`tools/morning_report.py`(어느 브랜치의 병합을 세는지), `tools/rerun_*.py`, `tools/hook_prompt_directive.py`(안내 문구의 "병합한 main"), `tools/hook_pr_head_sync.py`(독스트링의 예), `tools/check_constitution_version.py`(부모 판이나 `origin/main`과 견주는 곳), `tools/export_openapi.py`와 `tools/canary.py`·`tools/run_hooks.py`는 `main`이 브랜치 이름이 아닌 곳(`__main__`, 임시 저장소의 브랜치 이름)을 먼저 가려 바꿀 곳만 바꾼다.

- `tools/check_ticket.py`의 `ticket_stem`: `hotfix/*` 브랜치를 티켓 모양으로 알아보지 못한다(`ticket_stem('hotfix/x')`가 None이라 면제 모양 밖의 파일을 바꾸면 판정 7로 막히고, 막는 글은 `feature/NN-<slug>`나 `chore/<slug>`로 바꾸라고 안내한다). ADR 0043 "티켓 검사와 봇"은 hotfix→main이 티켓 PR이라 그대로 지난다고 적는다. `dev-branch-transition`의 셀프 리뷰 명세 축이 찾은 빈칸이다. 핫픽스가 가리킬 티켓 파일의 자리(`.scratch/harness/issues/<slug>.md`인지 기능 티켓인지)와 브랜치 이름 규칙을 이 티켓이 정해 `ticket_stem`·`_blocked` 안내문·시험에 싣는다. 정하기 어려우면 사용자에게 묻는다. 규칙이 서기 전까지 핫픽스는 티켓 모양 브랜치 이름(`chore/<slug>`와 `.scratch/harness/issues/<slug>.md`)으로 우회한다. 이 우회를 `_blocked` 안내문이 이미 일러 주는지 확인하고, 안내가 핫픽스에 맞지 않으면 고친다(`dev-branch-transition`의 PR claude-review가 짚었다).
- 같은 기준 브랜치 규칙(`hotfix/*`는 main, 그 밖은 `origin/dev` 추적 ref가 있으면 dev)이 `tools/check_ticket.py`의 `base_ref`와 `tools/hook_push_behind_main.py`의 `base_branch` 두 곳에 따로 구현돼 있다. 훅끼리 import하지 않는 규약은 `check_ticket.py`에는 해당하지 않으므로, 한 곳으로 모을지 두 곳을 묶는 시험(같은 입력에 같은 기준을 낸다)만 둘지를 이 티켓이 정한다. 규칙에 갈래가 더해지면(예: `release/*`) 두 곳이 갈라지는 것을 시험이 잡아야 한다.

먼저 `tools/`를 `origin/main`·`refs/remotes/origin/main`·`"main"`으로 Grep해 목록을 만들고(`__main__`과 `def main`은 뺀다), 곳마다 기준 브랜치 규칙을 적용할지, 둘 다 볼지, 그대로 둘지를 티켓 끝에 표로 적는다. 크기가 한 세션에 안 들면 이 티켓을 `sibling_overlap`와 `tidy_checkouts`와 나머지 셋으로 나누고 새 티켓 파일을 쓴다.

**대기열:** 없음

**Status:** done

**막는 티켓:** `dev-branch-transition`이 병합된 뒤에 한다. `dev-base-skills-docs`와 파일이 겹치지 않아 나란히 돌 수 있다.

## 수용 기준

- [x] 티켓 끝에 곳마다의 결정표가 있다(바꾼다, 둘 다 본다, 그대로 둔다와 까닭)
- [x] `origin/dev`가 없을 때 모든 도구가 지금과 같은 결과를 낸다는 시험이 있다
- [x] `origin/dev`가 있고 브랜치가 `feature/*`·`chore/*`·`docs/*`일 때는 dev를, `hotfix/*`일 때는 main을 기준으로 한다는 시험이 있다
- [x] `tidy_checkouts`와 `sibling_overlap`의 변경은 임시 저장소에서 판정을 깨려는 입력으로 반박했고 그 결과를 티켓 끝에 적는다
- [x] `hotfix/*` 브랜치가 커밋 검사를 티켓 PR로 지나는 규칙이 서고 `ticket_stem`의 시험이 있다
- [x] 기준 브랜치 규칙의 두 구현(`base_ref`, `base_branch`)이 같은 입력에 같은 기준을 낸다는 시험이 있거나 한 곳으로 모였다
- [x] 독스트링의 `origin/main` 잔존이 기준 브랜치 규칙을 말하는 곳에는 0이다(기록이나 일지 인용은 제외)
- [x] 검증 명령이 모두 초록이다

## 결정표

규칙은 `tools/base_rule.py` 한 곳에 순수 함수(`base_name`)와 git 읽기(`base_for`, `base_ref`)로 서 있다. 같은 규칙이 `tools/hook_push_behind_main.py`(`base_branch`)와 `tools/check_ticket.py`(`base_ref`)에도 따로 있는 까닭은, 앞의 것은 훅이라 다른 파일을 import하지 않고 뒤의 것은 CI가 표준 라이브러리만으로 단독 실행하기 때문이다. 셋을 같은 입력에 같은 기준을 내게 묶는 것은 `tests/tools/test_base_rule.py`가 한다(규칙 갈래가 늘면 그 접두의 이름을 시험의 `BRANCHES`에 더해야 하나만 고친 변경이 빨개진다. `release/x`는 이미 든다). 같은 시험이 `"hotfix/"` 문자열이 규칙을 가르는 세 파일 밖에 없음도 고정한다.

| 곳 | 결정 | 까닭 |
|---|---|---|
| `tools/sibling_overlap.py` | 바꾼다 + 둘 다 본다 | 기준은 규칙대로(`trunk_names`의 앞). 기준이 아닌 오래 사는 브랜치(dev가 기준이면 main, hotfix 브랜치면 dev)도 형제로 번호와 고친 파일을 견준다. dev에 없고 main에만 있는 번호(hotfix)를 놓치지 않기 위해서다. fetch도 두 브랜치를 받는다. `--journal`은 기준 ref의 merge-base를 쓴다. 열린 PR의 base는 읽지 않는다(`gh api`의 jq에 `.base`를 더하지 않는다). 대신 PR의 새 번호에서 기준이 아닌 오래 사는 브랜치가 쥔 번호를 뺀다. dev가 기준일 때 main에서 딴 hotfix PR의 head가 main만 쥔 번호를 품어도 PR 줄에 이중으로 뜨지 않는다(`test_…main에서_딴_열린_PR…`이 고정하고 변이 15번이 빨강을 본다) |
| `tools/tidy_checkouts.py` | 둘 다 본다 | 지우는 판정의 "병합됐다"는 `origin/main`이나 `origin/dev` 어느 쪽에서든 닿으면 참이다. 닿은 커밋은 그 추적 ref가 쥐고 있어 잃는 것이 이름뿐이고(원격에서 dev를 보호할지는 ADR 0043이 사람의 몫으로 남겨 두었으니 보호를 근거로 삼지 않는다. 그 ref가 사라지면 `remove-branch`가 다시 판정해 지우지 않는다), 없는 ref는 무시되어 dev가 없으면 지금과 같다. 기준 규칙을 따르면 hotfix 브랜치(main)에서 dev에 병합된 커밋을 못 알아봐 넘겨진 채 쌓인다. `PROTECTED_BRANCHES`에 `dev`를 더했고 대소문자를 가리지 않는다. dev가 없을 때 판정(지운다·남긴다·넘긴다)은 같지만 "어디에도 없다" 류의 이유 줄 글은 `origin/main 이나 origin/dev 어디에도 없다`로 바뀌었다(시험의 기대 문자열이 같이 바뀌었다) |
| `tools/check_ticket.py` | 바꾼다 | `base_ref`는 이미 규칙이었다. 빠진 것은 `hotfix/<slug>`였다. `ticket_stem`이 알아보고 티켓은 `.scratch/harness/issues/<slug>.md`(chore와 같은 harness 자리)다. 기능 코드를 고치는 핫픽스도 이 자리를 쓴다. 안내문은 hotfix 브랜치에는 `hotfix/<slug>`를 권하고 접두를 바꾸면 기준이 main에서 dev로 바뀐다고 일러 주며, chore 브랜치에는 hotfix를 권하지 않는다 |
| `tools/hook_push_behind_main.py` | 그대로 둔다 | `base_branch`가 이미 규칙이다. 단독 실행 훅이라 import하지 않고 `test_base_rule.py`가 모듈과 같은 기준을 내는지 본다 |
| `tools/hook_git_main_commit.py` | 그대로 둔다 | 이미 `dev-branch-transition`이 고쳤다(`PROTECTED = {main, dev}`) |
| `tools/check_constitution_version.py` | 바꾼다 | 견주는 판의 기준을 `trunk_names`의 앞으로 바꾸고 보고에 기준 ref 이름을 싣는다. hotfix 브랜치는 main의 판과 견준다 |
| `tools/mutate.py` | 그대로 둔다(독스트링만) | 기본 비교 대상은 사용자가 `--base`로 정하는 값이다. 안내만 "기준 ref"로 바꿨다 |
| `tools/wait_ci.py`, `tools/hook_prompt_directive.py` | 바꾼다(글만) | 충돌 안내와 첫 턴 안내의 "병합한 main"을 기준 ref로 읽게 했다. 동작은 같다 |
| `tools/morning_sources.py`, `tools/morning_collect.py` | 바꾼다 | 보고에는 작업 브랜치가 없어 `integration_ref`(= `base_ref(root, None)`)를 둔다. 대기열·티켓·일지·CI(`gh run list --branch`)를 그 브랜치에서 읽고, dev가 없으면 지금과 같다. `morning_report.py`는 브랜치를 가리지 않아 손대지 않았다 |
| `tools/queue_open_rows.py`, `tools/rerun_select.py` | 그대로 둔다(글만) | `--ref`와 `--rev`는 호출자가 주는 값이다. 기본값 `origin/main`은 규칙의 hotfix 쪽과 같고, 안내에 dev일 때 `origin/dev`를 준다고 적었다 |
| `tools/rerun_round.py`, `tools/rerun_session.py` | 그대로 둔다 | `main`은 측정이 만드는 샌드박스 저장소의 브랜치 이름이다. 이 저장소의 기준과 무관하다 |
| `tools/run_hooks.py`, `tools/canary.py`, `tools/export_openapi.py` | 그대로 둔다 | `main`은 임시 저장소의 브랜치 이름이거나 `__main__`이다 |
| `tools/hook_pr_head_sync.py`, `tools/hook_bash_msys_pathconv.py` | 그대로 둔다 | `origin/main`은 명령 예시 글이다 |

## 반박 결과

`.claude/rules/tools.md`의 지우는 도구 반박 항목대로, 시험이 고른 입력이 아니라 판정을 깨려는 입력을 임시 저장소에서 쳤다. 모두 `tests/tools/`에 시험으로 남았다.

`tidy_checkouts`(`tests/tools/test_tidy_checkouts.py`):

- 이름만 dev인 로컬 브랜치는 밀지 않은 커밋을 쥘 수 있다. 그 커밋을 가리킨 분리 HEAD 워크트리와 `worktree-*` 브랜치는 `origin/dev`에 없으므로 남기고 넘겼다(지우는 쪽으로 읽히지 않았다).
- 다른 원격 ref(`origin/feature`)나 태그에만 있는 커밋은 오래 사는 브랜치에 든 것이 아니라 남겼다.
- `origin/dev`를 지우자(prune, 원격 브랜치 삭제) dev에만 있던 커밋은 다시 남았고, `judge`가 지울 후보로 찍은 뒤라도 `remove-branch`가 다시 판정해 지우지 않았다.
- 머리가 `dev`인 병합된 PR(dev→main 릴리스)이 있을 때 `dev`를 체크아웃한 깨끗한 워크트리는 첫 판의 `judge`가 `지운다`로 냈다(PR 직전 CodeRabbit 리뷰가 찾았다). 보호 이름 검사가 체크아웃되지 않은 브랜치에만 있었기 때문이다. 워크트리 판정에도 같은 검사를 더했고 `remove`가 종료 1로 거절한다.
- `Dev`·`DEV`·`Main`처럼 대소문자가 바뀐 보호 브랜치 이름은 첫 판에서는 지울 후보가 될 수 있었다(윈도의 `for-each-ref`가 이름의 대소문자를 바꿔 찍을 수 있다는 같은 파일의 `same_branch` 주석). 비교를 `casefold`로 고쳐 막았다. 이것이 이 반박이 찾은 빈칸이다.
- 루트가 다른 브랜치에 있어 체크아웃되지 않은 `dev` 브랜치는 끝이 `origin/dev`에 들어도 지우지 않는다.
- `origin/dev`에만 든 분리 HEAD와 브랜치는 지울 후보가 되고, 어느 쪽에도 없는 분리 HEAD는 dev가 있어도 넘긴다.

`sibling_overlap`(`tests/tools/test_sibling_overlap.py`):

- dev가 main보다 뒤처졌을 때 main에서 딴 브랜치의 merge-base는 dev 끝이라 main이 더한 번호가 새 번호로 읽힐 수 있다. 같은 번호에 같은 파일은 겹침이 아니라 0으로 끝났다.
- 이력이 갈라진 dev(고아 브랜치)는 merge-base가 없어 견줄 수 없다. 겹침 없음으로 조용히 지나가지 않고 2로 멈췄다.
- dev 브랜치 자체에서는 새 번호가 없어 겹치지 않는다.
- dev의 추적 ref가 없으면 원격에 dev가 있어도 main만 대조한다(못 보는 것으로 시험이 고정한다).
- dev가 기준일 때 main에만 있는 번호(hotfix)와 부딪히면 `origin/main` 줄로 알리고 옮길 번호가 그 뒤로 간다. hotfix 브랜치는 main을 기준으로 하고 dev의 번호도 견준다. 일지는 dev와의 merge-base 뒤에 더한 것만 든다.
- dev가 기준일 때 main에서 딴 hotfix PR(base가 main)의 head는 main만 쥔 번호를 품는다. 그 번호는 PR이 더한 것이 아니라 `origin/main` 줄이 이미 알린다. 셀프 리뷰 명세 축이 짚었고 시험이 빨간 것을 보고 고쳤다(PR 줄에 같은 번호가 이중으로 떴다).
