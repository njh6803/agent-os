# 2026-11-11 (22:50) dev 브랜치 전환의 첫 몫: 기준 브랜치 규칙과 훅·커밋 검사·CI 트리거 (harness dev-branch-transition)

세션 제목 `chore/dev-branch-transition`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/dev-branch-transition`. 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> ADR 0043 Consequences "전환"(dev 브랜치 전환)을 티켓 .scratch/harness/issues/dev-branch-transition.md로 쓰고 한다
>
> 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/dev-branch-transition.md. ADR 0043의 dev 브랜치 전환(dev를 main에서 따고 훅·스킬·CI·규약 문서를 고친다)
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

지시문은 수용 기준에 넣을 것 넷을 일렀다. (가) 실제 이미지의 compose e2e 잡은 이 티켓이 만들지 않는다. (나) 닫을 때 `.scratch/plan-head.md`에서 release-image가 dev 전환을 기다린다는 문장을 걷는다. (다) 닫을 때 같은 전환을 rag-engine에 하라는 지시문을 사용자에게 내고, 얇은 ADR 한 장 요건을 싣고, 대기열 `rag-engine-port-by-hand`에 회차를 더한다. (라) 일지 "다음" 4가 이 줄들을 걷는 시점은 지시문을 낸 뒤다. 크기가 한 세션에 안 들면 티켓을 나누라고 했다.

## 결정

- **티켓을 다섯으로 나눴다.** 전환이 건드리는 곳이 많다. `tools/`에서 `origin/main`이나 `"main"`이 든 파일이 열여섯이고(리뷰 서브에이전트가 Grep으로 센 파일 수다. 그중 기준 브랜치를 뜻하는 곳만 가른 수는 아니다), 스킬 여덟과 규약 문서 넷과 ADR 포인터 둘에 사용자 수준 스킬도 든다. 한 세션에 들지 않는다고 판단했다. 이름은 `dev-branch-transition`(규칙, 훅 둘, 커밋 검사, CI 트리거, 이 PR), `dev-review-bot-off`(리뷰 봇 워크플로. 자기 워크플로 파일을 바꾼 PR은 봇이 건너뛰므로 별도 PR), `dev-base-tools`, `dev-base-skills-docs`, `dev-branch-create`(dev를 따고 닫기)다. 앞의 넷은 나란히 돌 수 있고 다섯째는 앞의 넷이 병합된 뒤다.
- **기준 브랜치 규칙.** 브랜치 접두로 가른다. `hotfix/*`는 `origin/main`이다. 그 밖은 `origin/dev`의 추적 ref가 있으면 dev이고 **없으면 main이다.** 마지막 갈래가 전환의 중심이다. 이 티켓들이 main에 병합되는 동안과 dev를 따기 전까지 모든 도구가 지금처럼 돌고, dev를 따는 마지막 티켓이 병합되는 순간 같은 코드가 dev를 기준으로 쓰기 때문이다. 판정 문장은 티켓 1에서 한 번 정하고 훅은 서로 import하지 않으므로(`.claude/rules/tools.md`) 훅마다 같은 짧은 함수를 둔다.
- **dev는 마지막 티켓이 딴다.** ADR 0043은 harness 티켓이 dev를 딴다고 적었지만, 도구와 스킬이 바뀌기 전에 따면 나란히 도는 세션들이 엉뚱한 base로 간다. 그래서 따는 일을 `dev-branch-create`로 미뤘다.
- **사람의 몫을 찾았다.** `tools/protection.json`의 `required_linear_history: true`가 dev→main의 merge 커밋을 막는다. ADR 0043은 이 설정을 말하지 않았다. 끌지, 관리자 우회(`enforce_admins: false`)에 기댈지를 `dev-branch-create`가 사용자에게 묻는다. LLM 호출 테스트를 main PR의 CI에서 돌리려면 API 키 시크릿도 사람이 넣어야 한다. 이 PR은 둘 다 건드리지 않는다.
- **사용자 수준 스킬은 고치지 않는다.** `git-pr`·`git-pr-merge`·`git-pr-feedback`·`git-branch`는 `~/.claude/skills`에 있어 저장소 밖이다. `dev-base-skills-docs`가 `main`을 박은 곳을 읽어 목록으로 내고 사용자에게 고칠지 묻는다.

## 한 일

- `tools/hook_git_main_commit.py`: 보호 브랜치에 `dev`를 더했다. `git merge`가 만드는 병합 커밋은 `git commit` 명령이 아니라 걸리지 않는다는 것을 독스트링의 못 보는 것에 적고 시험과 훅 페이로드로 고정했다.
- `tools/hook_push_behind_main.py`: 뒤처짐을 기준 브랜치로 잰다(`base_branch`). 보호 브랜치 위에서는 재지 않는다. 안내문이 기준 브랜치 이름을 든다. 로컬 git이 하나 늘어(dev의 유무) `GIT_TIMEOUT`을 5초에서 3초로 낮춰 합을 등록의 20초 안(17초)에 맞췄다.
- `tools/check_ticket.py`: 로컬 판정의 기준을 `base_ref`로 정하고 `main`·`dev` 브랜치와 머리 브랜치가 `main`·`dev`인 PR을 판정 1로 지나게 했다.
- `tools/run_hooks.py`: 자리표시자 `${DEV_REPO}`(커밋이 하나 있는 dev 임시 저장소)를 더했다. `tools/hook_payloads.toml`에 dev 위의 커밋(deny)과 dev 위의 `git merge`(silent)를 더했다.
- `.github/workflows/ci.yml`: 푸시 트리거를 `main`과 `dev`로 넓혔다.
- `tests/tools/`: 세 파일(`test_check_ticket.py`, `test_hook_git_main_commit.py`, `test_hook_push_behind_main.py`)에 갈래마다 시험을 더했다.
- `.scratch/harness/probes/push_behind_hook_mutations.toml`: 원문이 코드와 어긋난 변이(이 변경 전부터 낡은 것 넷과 이 변경이 깬 것)를 현재 코드에 맞추고 새 갈래의 변이 셋을 더했다.
- 티켓 다섯과 이 일지.

## 검증

- 변이 표: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/push_behind_hook_mutations.toml`가 "변이 21 모두 기대대로"로 끝났다(기준선 초록 열네 번, 빨강 기대 스무 개가 모두 빨강이고 대조군 하나가 초록). 돌린 뒤 `git status --porcelain`에 변이가 남지 않았다.
- `uv run ruff check .`와 `uv run ruff format --check .`가 초록이다. 바꾼 도구의 시험 세 파일은 211개가 통과했다(셀프 리뷰 반영 뒤).
- 첫 커밋 시도는 pre-commit의 변이 표 검사(`tools/mutate.py --staged`)에 막혔다. 푸시 훅 표의 빨강 기대 아홉 개에 `expect_output`이 없었고, 이 변경이 `tools/run_hooks.py`와 `tools/check_ticket.py`의 원문을 바꿔 다른 표 둘(`main_commit_hook_mutations.toml`, `check_ticket_mutations.toml`)의 원문이 0번이 됐다. 원문을 현재 코드에 맞추고 표지를 더한 뒤 `--check`로 원문을 확인했고, 고친 변이 둘과 표지를 더한 아홉을 실제로 돌려 모두 기대대로 빨강을 봤다. 같은 pre-commit의 나머지 게이트(ruff, 타입체크, 경계, pytest 전체, web-verify)는 그 시도에서 모두 통과했다.
- 커밋 직전의 pytest 전체, 타입체크, 경계, web은 그 커밋의 pre-commit 결과로 갈음한다(`CLAUDE.md` 검증 명령). 결과는 커밋 뒤 PR 본문에 적는다.

## 셀프 리뷰

범위: 기준 `3a07ba9`, 수정 파일 10개, 커밋 0개, 미추적 6개. 표준 축은 sonnet·high, 명세 축은 세션 모델이다.

- **표준 축.** 하드 위반은 없었다. Minor 넷을 고쳤다.
  - `hook_push_behind_main.py` 독스트링이 "셋의 합(18초)"이라 적었으나 코드는 로컬 호출 셋과 fetch 하나의 합 17초다. "main 이거나"와 `git fetch -q origin main`도 기준 브랜치로 맞췄다.
  - `check_ticket.py`의 `judge` 독스트링("`origin/main` 에 견줘"), "main 의 push" 둘, 포크의 머리 브랜치 `dev`를 빠뜨린 못 보는 것, `git rebase --onto origin/main` 복구 명령을 고쳤다.
  - 일지의 `main` 줄 수(67·30)가 재현되지 않았다. 패턴을 밝히지 않은 수라 파일 수(열여섯)로 바꾸고 Grep으로 센 수임을 적었다.
  - 독스트링이 충돌을 풀고 `git commit`으로 끝내는 병합은 걸린다고 적은 항목에 시험이 없어 `test_충돌을_풀고_git_commit으로_끝내는_병합은_dev_위에서_막는다`를 더했다.
  - 남긴 것: `behind_count`가 `tuple[str, int]`을 돌려주고 인덱싱으로 읽는 Nit(Primitive Obsession), `reason_text(count, base="main")`의 기본값이 시험에서만 쓰이는 Nit. 이유는 한 줄이다: 둘 다 판단 항목이고 고쳐도 동작이 같다.
- **명세 축.** 요구 누락은 없었다. 편차와 빈칸이 셋이었다.
  - 티켓은 `check_ticket`의 "전환" 절의 `origin/main`을 고친다고 했으나 판정 2의 한 문장으로 갈음했다. 티켓 문구를 갈음한 대로 고쳤다.
  - `hotfix/*` 브랜치는 `ticket_stem`이 티켓 모양으로 알아보지 못해, 면제 모양 밖의 파일을 바꾸면 판정 7로 막힌다. ADR 0043은 hotfix→main이 티켓 PR이라 지난다고 적었으나 다섯 티켓 어느 것도 이 이음을 맡지 않았다. `dev-base-tools`에 항목과 수용 기준을 더했다.
  - `dev-branch-create`의 첫 문장(이 PR은 dev가 서기 전에 열렸으므로 main으로 간다는 대목)이 닫을 때 할 일의 편집이 dev를 딴 뒤에 오는 순서와 어긋났다. dev를 따는 일은 푸시 하나이고 닫기 편집 PR은 dev로 간다고 고쳤다. main의 plan-head가 다음 출시까지 옛 문장을 드는 시차를 PR 본문에 적게 했다.
- 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장): 푸시 훅의 git 시간 제한 합이 17초(로컬 3초씩 셋과 fetch 8초)다. `ticket_stem('hotfix/x')`가 None이다. `origin/dev`가 없으면 바뀐 세 도구 모두 main 갈래로 돈다. ci.yml의 잡은 일곱이다. (뒤의 둘은 아래 "PR 직전 리뷰"가 바로잡았다.)

## PR 직전 리뷰

`coderabbit-review` 서브에이전트가 CLI를 끝까지 돌렸다(`review_completed`. `Plan: Free`, `Seat: not assigned`). 지적 둘이 모두 유효한 Minor였고 오탐은 없었다. 둘 다 고쳤다.

- **변이 표지 둘.** `main_commit_hook_mutations.toml`의 "러너의 main 픽스처에 커밋을 두지 않는다"와 `push_behind_hook_mutations.toml`의 새 변이 셋이 `expect_output`으로 시험 함수 이름을 골랐다. 이름은 준비 단계가 깨져도 찍혀서 고른 단언이 실패했다는 표지가 못 된다. 해당 시험의 단언에 실제 값을 넣은 f-string 메시지를 달고(`hotfix 브랜치가 견준 기준: ('dev', 4)` 같은 꼴), 변이를 손으로 넣어 실패 출력의 `E` 줄에 그 문구가 나오는 것을 본 뒤 표지로 바꿨다. 같은 시험의 다른 변이(빈 main 픽스처) 하나가 `expect_output` 없이 있던 것도 같은 방식으로 채웠다. 소스 줄에는 `{result}` 꼴로만 있어서 다른 단언이 실패한 출력과 섞이지 않는다. 같은 표의 앞쪽 여섯도 이 PR이 더한 시험 이름 표지였다(`git diff origin/main`에서 이 PR이 더한 `expect_output`은 아홉이고 셋이 새 변이, 여섯이 앞쪽 변이였다). PR의 CodeRabbit 첫 회차가 짚어서야 알았다. 서브에이전트는 "옛 변이인지는 확인하지 못했다"고 보고했는데, 그 말을 이 세션이 확인하지 않고 옛 변이라서 소급하지 않았다고 적은 것이 틀렸다. 아래 "봇 첫 회차"가 고쳤다.
- **사실 문장 3번이 부정확했다.** `origin/dev`가 없을 때 푸시 훅(`base_branch`)은 "main"을, 커밋 검사(`base_ref`)는 `origin/main`을 기준으로 삼는다. `hook_git_main_commit`은 기준 브랜치를 고르지 않고 현재 브랜치 이름이 `{main, dev}`에 드는지만 보므로 `origin/dev`를 읽지 않는다. 그래서 dev라는 이름의 브랜치가 없으면 사실상 main만 막는다. 코드는 그대로 맞고 문장만 고쳤다. 근거는 코드를 읽은 것이다(서브에이전트의 판정을 `tools/`에서 `PROTECTED|origin/dev`를 Grep해 `hook_git_main_commit.py:44·136`에 `origin/dev`를 읽는 줄이 없는 것으로 대 봤다).
- **사실 문장 4번이 틀렸다.** `ci.yml`의 `jobs:`는 여덟이다(검사 잡 일곱과 그 결과를 모으는 `verify`). 새로 더한 주석의 "같은 잡 일곱"을 "같은 검사 잡 일곱과 그 결과를 모으는 verify"로 고쳤다. 잡 수는 `ci.yml`에서 `jobs:` 아래 키를 Grep으로 세어 확인했다(python, web, e2e, e2e-widget, e2e-portal, visual, ticket, verify). 1번(17초)과 2번(`hotfix/x` → None)은 서브에이전트가 코드를 읽어 맞다고 했고 이 세션은 다시 대지 않았다.

## 봇 첫 회차

CodeRabbit이 이 PR에 낸 첫 리뷰는 줄 코멘트 다섯이고 claude-review는 한 번 돌았다(둘 다 `gh api`로 읽었다). 첫 회차라 Minor까지 지적마다 판단했고 모두 고쳤다. 푸시 한 번에 실었다.

- **[Major] dev를 따기 직전 원격 main을 갱신한다** (`dev-branch-create.md`). `git push origin origin/main:refs/heads/dev`가 로컬 추적 ref를 쓰므로 낡을 수 있다. 맞는 지적이라 3단계에 `git fetch origin`을 먼저 두고 딴 뒤 `git ls-remote`로 원격의 두 브랜치 커밋을 대게 했다. 수용 기준도 같은 말로 고쳤다.
- **[Minor] LLM 테스트 잡의 구현** (`dev-branch-create.md`). `ci.yml`에 그 잡이 없어 시크릿만 넣어서는 돌지 않는다. 맞는 지적이다. 잡 구현(main을 base로 하는 PR과 main 푸시, `verify`에 잇기)을 사용자의 답에 따라 그 티켓이 하거나 후속 티켓 `ci-llm-job`으로 쓰게 했고 `dev-branch-transition.md`의 "하지 않는 것"에도 적었다.
- **[Minor] 다른 클론은 `origin/dev`를 받아야 한다** (`dev-branch-transition.md`). 맞는 지적이다. 티켓 규칙에 "없다"가 이 클론의 추적 ref가 없다는 뜻임을 적고, `dev-branch-create`에 4단계와 수용 기준으로 더했다.
- **[Minor] 변이 표지 여섯** (`push_behind_hook_mutations.toml`). 위 "PR 직전 리뷰"의 같은 지적이 더 있던 것이다. 해당 시험 다섯의 단언에 값을 넣은 메시지를 달고 표지를 바꿨다. 변이를 손으로 넣은 실패 출력의 `E` 줄에서 문구가 나오는 것을 본 뒤에 골랐다.
- **[Minor] `origin/dev` 조회가 시간을 넘기거나 실패해도 dev가 없다고 읽는다** (`hook_push_behind_main.py`). 맞는 지적이다. 이 훅은 `deny`를 내므로 dev에는 최신이고 main에만 없는 브랜치를 잘못 막는다. `ref_state`("present"·"absent"·"unknown"의 `Literal`)를 두고 `base_branch`가 "unknown"이면 None을 내 `behind_count`가 재지 않게 했다. 처음에는 `ref_exists -> bool | None`으로 지었는데 저장소의 `optional_bool_annotations` 검사(`test_이_저장소에는_bool_None_주석이_없다`)가 pre-commit의 pytest에서 빨개져 첫 커밋 시도가 막혔고, `Literal`로 다시 지었다. 시험 둘(`ref_state` 세 갈래, 시간 제한을 0.0001초로 줄여 조회를 반드시 넘기게 한 `base_branch`)과 변이 22번을 더했다. 수동으로 변이를 넣어 출력을 본 일곱과 표 전체(`mutate.py` 22개)가 모두 기대대로 나왔다.
- **claude-review [Minor] `reason_text`의 기본값 `base="main"`.** 맞다. 호출부가 항상 넘기고 시험만 기본값에 기댔으므로 필수 인자로 바꾸고 시험의 호출 둘을 고쳤다. **[Nit] `behind_count`의 반환 튜플**은 셀프 리뷰에서 남긴 것과 같은 지적이라 이번에도 남긴다. 고쳐도 동작이 같고 훅이 단독 스크립트라 이 파일 안에서만 정의해야 한다.
- **CI 실패와 재실행.** 첫 실행에서 python, web, e2e, e2e-widget, e2e-portal이 모두 `apt`의 `Temporary failure resolving`(러너의 DNS)로 `apt-get` 종료 코드 100/1에서 멈췄다. `gh run view --log-failed`를 읽어 다섯 잡 모두 같은 원인임을 보았다. verify는 그 결과를 모아 빨갰다. 이 PR의 코드와 무관한 인프라 실패라 `gh run rerun --failed`로 다시 돌렸고, 새 푸시가 있어 그 재실행은 멈추고 새 헤드로 다시 기다린다.
- **사고 하나.** 변이를 넣어 보려고 쓴 스크래치 스크립트가 `Path.write_text`로 훅 파일을 되돌리며 줄 끝을 CRLF로 바꿨다. 변이 표 실행이 "줄 끝이 다르다"로 알려서 알았고 바이트로 LF로 되돌려 `git diff --stat`이 정상 크기(훅 38줄)임을 확인한 뒤 표 전체를 다시 돌렸다.

- **CI 두 번째 실행의 같은 실패와 복구.** 반영 푸시의 실행에서도 같은 `apt` DNS 실패가 났다. 로그에서 확인했고, 마지막 성공(13:11Z) 뒤 다른 브랜치의 실행도 같은 문구로 모두 빨갛다는 것을 `gh run list`와 한 실행의 로그(문구 218번)로 보았다. 동료 세션(`docs/local-model-design`)이 보낸 알림이 Canonical 쪽 DNS 장애라고 알려 줬는데, 그 알림이 든 `actions/runner-images` 이슈 번호는 이 세션이 확인하지 않았다. `gh run rerun --failed`를 두 번 쳐서 e2e 셋, web, python, verify가 통과했다.
- **main이 움직여 병합(`BEHIND`).** 검사가 모두 통과한 뒤 `mergeStateStatus`가 `BEHIND`였다. main에 들어온 것은 PR 530(문서 전용)이고 이 브랜치와 겹치는 파일이 없었다(`git diff --name-only HEAD...origin/main`). `git merge origin/main`을 쳤고 커밋 메시지의 타입이 `merge`라 커밋 검사가 막아 `chore`로 다시 했다. 푸시 뒤 CI가 다시 모두 통과했다.
- **봇 둘째·셋째 회차.** claude-review의 둘째·셋째 리뷰와 CodeRabbit의 한도 걸린 회차(`Review rate limited`, 리뷰 없음)는 Critical·Major가 없었다. 둘째 회차 이후라 Minor·Nit은 반영하지 않았다. 보류한 것: `behind_count`의 반환 튜플(셀프 리뷰부터 남긴 Nit), `ref_state`가 `run_git`·`quiet_git`과 `subprocess.run` 호출 모양을 되풀이한 것(훅 안의 세 호출이고 각자 다른 결과를 읽어 나중에 묶어도 된다), `behind_count`의 이름(이 PR 이전부터의 이름). 뒤의 작업으로 넘긴 둘(`base_ref`와 `base_branch`의 규칙 중복, `hotfix/*`의 임시 우회)은 `dev-base-tools` 티켓과 위 "다음" 2에 적었다. 판정은 PR 코멘트에도 남겼다.

## 회고

낸 후보 일곱, 판정은 승인 0, 기각 7, 넘김 0이다.

- 변이 표 원문이 코드와 어긋나 있었다(이 변경 전부터 넷). **기각**: 이미 있는 검사가 잡는다(`tools/mutate.py --check`와 pre-commit의 `--staged`, 대기열 0092). 이 세션이 변이를 돌려서야 알았지만 표를 고치는 커밋에서 그 검사가 돈다.
- 독스트링·주석의 낡은 수치와 `main`만 적은 문장. **기각**: `code-review` 두 브리프의 주장 검증 3번(계약 변경 grep)이 잡도록 둔 기준을 어겨 리뷰가 잡았다. 리뷰가 제 몫을 했으므로 회차에서 뺀다.
- 일지에 패턴을 밝히지 않은 줄 수. **기각**: 주장 검증 7번(근거의 종류)이 잡았다. 같은 이유다.
- `hotfix/*` 브랜치의 티켓 이음 빈칸. **기각**: 하네스 후보가 아니라 설계의 빈칸이고 `dev-base-tools` 티켓에 담았다.
- 새 워크트리의 `.venv`가 만들어지는 동안 `rewrap_comments.py`가 120초 제한을 넘은 일. **기각**: 일회성이고 사건 하나도 환경의 첫 기동 비용이다.
- 서브에이전트가 "확인하지 못했다"고 한 것을 이 세션이 확인 없이 "이 변경 전의 것"이라고 일지와 PR 본문에 옮겼다. **기각**: 근거의 종류를 밝히라는 기존 계기(`hook_journal_evidence`)와 주장 검증이 겨냥하는 모양이고, 봇이 잡았다. 사건 하나다.
- 변이를 보려고 쓴 스크래치 스크립트가 추적 중인 소스의 줄 끝을 CRLF로 바꾼 일. **기각**: 변이 표 실행이 알렸고 바이트로 되돌려 확인했다. 첫 사건이고 손상이 없다.
- 대기열 점검: 만료할 항목 없음, 회차 5 이상은 chore 배치의 대상 그대로(`420`, `probe-round-marked-measured-unconditionally` 등 열한 개). 새 항목은 쓰지 않았다.

## 인계: 커밋 뒤

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 커밋 뒤 경계에 왔다. 구현, 셀프 리뷰 반영, 회고, 커밋(pre-commit 통과)까지 했고 열린 PR은 없다. 첫 커밋 시도는 변이 표 검사에 막혀 위 검증 절에 적은 대로 고친 뒤 다시 커밋했다. 새 세션이 할 일은 PR 직전 리뷰(`coderabbit-review`, 밀 주장은 위 셀프 리뷰 절의 새로 쓴 사실 문장), 푸시, PR 열기, 봇 회차, 병합(`merge.md`의 워크트리에서 병합할 때), 병합 뒤 `next-session`으로 아래 다음 절 1~3의 지시문을 내는 것이다.

open-session을 부른다 2026-11-11T15:00:40Z

## 다음

이 PR이 병합된 뒤의 일이다. 앞의 세 티켓은 서로 파일이 겹치지 않아 나란히 돌 수 있고, 넷째는 앞의 셋이 병합된 뒤에 한다.

1. **`dev-review-bot-off`**: 리뷰 봇 워크플로가 머리가 `dev`인 PR을 건너뛰게 한다. 자기 워크플로를 바꾼 PR은 봇이 건너뛰므로 이 티켓만 따로 낸다.
2. **`dev-base-tools`**: 나머지 도구를 기준 브랜치 규칙(`dev-branch-transition`의 절)으로 바꾼다. `ticket_stem`의 hotfix 빈칸이 이 티켓의 몫으로 들어 있다. 기준 브랜치 규칙의 두 구현(`base_ref`, `base_branch`)을 묶는 시험이나 통합도 이 티켓의 몫이다(PR의 claude-review 둘째 회차 이후 Minor를 이 티켓으로 넘겼다).
3. **`dev-base-skills-docs`**: 스킬, `CLAUDE.md`, 운영 규약, 문서, ADR 포인터를 규칙에 맞추고 핫픽스 되돌려 합치기의 순서를 `next-session` `merge.md`에 적는다. 사용자 수준 스킬(`~/.claude/skills`)을 고칠지 사용자에게 묻는다.
4. **`dev-branch-create`**: 위 셋이 병합된 뒤 `origin/dev`를 따고 전환을 닫는다. 사람의 몫(`required_linear_history`, dev 보호, API 키 시크릿)을 사용자에게 먼저 묻는다. 닫을 때 `.scratch/plan-head.md`의 dev 전환 문장을 걷고, rag-engine 지시문(얇은 ADR 한 장 요건 포함)을 사용자에게 낸 뒤 대기열 `rag-engine-port-by-hand`에 회차를 더한다. 지난 일지(2026-11-11-1532)의 "다음" 1과 4가 이 줄들을 걷는 시점은 그 지시문을 낸 뒤다.
5. **전환 뒤의 후보**: 두 저장소의 공통 파일을 비교하는 점검 도구(대기열 `rag-engine-harness-drift`). 결과를 아침 보고에 싣는 것은 사용자가 확인하지 않았으니 그 티켓을 여는 세션이 사용자에게 묻는다. 지난 일지 "다음" 8은 이 전환의 몫이 아니다.
6. **병합 직후**: 이 PR을 워크트리에서 병합하면 주 체크아웃은 갱신되지 않는다. 새 세션이 `tidy-checkouts`를 먼저 돈다(`merge.md`).
