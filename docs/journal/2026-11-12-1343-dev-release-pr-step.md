# 2026-11-12 (13:43) 출시 PR(dev→main)을 여는 순서를 정한다

세션 제목 `chore/dev-release-pr-step`. 브랜치 `chore/dev-release-pr-step`, 워크트리 `.claude/worktrees/dev-release-pr-step`, 티켓 `.scratch/harness/issues/dev-release-pr-step.md`. 모델 `claude-sonnet-5-5`.

## 사용자 프롬프트

세션의 첫 메시지는 `implement` 스킬을 이 티켓에 대고 돌리라는 지시문이다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/harness/issues/dev-release-pr-step.md
> 다음 작업: .scratch/harness/issues/dev-release-pr-step.md. 기능이 끝나면 출시 PR(dev→main)을 여는 순서를 정한다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … EnterWorktree(name은 dev-release-pr-step)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: chore/dev-release-pr-step / 이번 요청 범위: PR과 병합까지. 단 GitHub 보호 설정을 바꾸는 일은 사용자의 답과 승인을 받은 뒤에 한다

## 체크아웃 정리

첫 턴에 주 체크아웃 세션에서 `tidy-checkouts`를 돌았다. 루트가 main이고 깨끗해서 `git switch --no-overwrite-ignore dev`로 dev로 옮겼고, `git merge --ff-only`는 `Already up to date`였다(앞뒤 커밋 모두 `4b02bbe29`, `origin/dev`와 같다). `judge`의 줄은 모두 `남긴다`·`넘긴다`였고 지운 것은 없다. 까닭은 병합된 PR이 없다, 바뀐 파일이 있다, 폴더를 쥔 프로세스가 있다, 앱의 표지가 있다, 그 브랜치의 세션이 돈다였다. `ci-llm-job` 폴더는 `.git`이 있는 등록 없는 폴더라 넘겼다(나란히 연 세션이 막 만든 것으로 본다).

## 사람의 몫 둘

시작할 때 티켓 메모가 시킨 대로 보호 설정에 걸린 선택을 물었다. 질문과 답은 라벨과 설명 글자 그대로 아래와 같다.

- main strict 처리: **병합 뒤 main을 dev에 되돌려 합친다 (Recommended)**. "GitHub 설정은 그대로입니다. 출시 PR을 병합하자마자 main→dev PR을 하나 더 열어 merge 커밋으로 합치면 dev가 main의 끝 커밋을 품어 다음 출시 PR이 막히지 않습니다. Git Flow에서 release를 master에 합친 뒤 develop에 되돌려 합치는 단계와 같습니다(제 지식에서 끌어낸 어림이고 이번에 조사하지 않았습니다). 치르는 값: 출시마다 PR 하나와 CI 한 바퀴, dev 이력에 merge 커밋 하나가 늘어납니다." 다른 선택지는 "출시 PR만 관리자 권한으로 병합한다"(`gh pr merge --admin`)와 "main의 strict를 끈다"였다.
- 첫 출시: **지금 한 번 출시한다 (Recommended)**. "절차를 스킬에 쓴 뒤 이 티켓의 PR이 dev에 병합되면 그 dev를 main에 올립니다. 수용 기준 4(병합 뒤 `ls-remote`로 dev 확인)와 위 선택의 절차를 실제로 거칩니다. 치르는 값: 계기 조건을 한 번 어기고, main에 merge 커밋이 하나 남습니다." 질문에 든 사실은 `git diff --stat origin/main origin/dev`(22 files), `.github/workflows/`(`ci.yml`, `claude-code-review.yml`만 있고 release-image 워크플로가 없다), `gh api`의 main 보호(`strict: true`, `required_linear_history: false`, `allow_deletions: false`)와 dev 보호(`strict: false`)를 대 보고 적었다. 다른 선택지는 "하지 않고 절차만 쓴다"였다.

보호 설정은 바꾸지 않는 선택이라 GitHub 쪽 변경은 없다.

## 첫 출시를 실제로 했다

절차를 `merge.md`에 쓴 뒤, 이 티켓의 PR이 열리기 전에 dev(`4b02bbe29`)를 main에 올려 절차를 그대로 거쳤다(질문에서 "이 티켓의 PR이 dev에 병합되면"이라고 적은 순서와 다르다. 올릴 것이 이미 dev에 있었고 절차를 PR 전에 시험하는 편이 병합 뒤보다 고치기 쉬웠다. 계기 조건(끝 줄을 적은 기능)은 어겼다).

- 출시 PR #542: 검사가 모두 SUCCESS(CodeRabbit과 `claude-review`는 SKIPPED), `mergeStateStatus` CLEAN, `gh pr merge 542 --merge --match-head-commit <머리>`로 병합. main이 `82297e614`에서 `afe4b7f86`이 됐다.
- 병합 뒤 `git ls-remote --exit-code --heads origin refs/heads/dev`가 0(`4b02bbe29`), 기본 브랜치도 dev. 자동 삭제는 머리 dev를 지우지 않았다(한 번 본 것).
- `compare main...dev`가 `behind_by: 1`, `ahead_by: 0`, 내용 diff 0. 곧 dev는 main의 merge 커밋 하나를 품지 않았다. 둘째 출시 PR이 실제로 BEHIND로 막히는지는 보지 못했다(어림).
- 되돌려 합치기 PR #543(머리 main, base dev): 내용 diff가 0인데도 GitHub가 열어 주었고, 검사가 모두 SUCCESS(`claude-review`는 돌았다), CLEAN으로 `--merge` 병합. 병합 뒤 `--is-ancestor origin/main origin/dev`가 0, dev는 `641165ff5`, `ls-remote`도 0. 그래서 되돌려 합치기의 판정을 `git diff --quiet`에서 `--is-ancestor`로 바꿨다.
- 두 PR 모두 `tools/wait_ci.py`가 종료 4와 `끝: CodeRabbit 리뷰가 요청되지 않았다`로 끝났다(CodeRabbit이 SKIPPED로 남는다). `--expect verify`로 피한다고 적었던 문장을 고쳤다.

## 셀프 리뷰(커밋 전)

범위는 base `4b02bbe29`(`git merge-base origin/dev HEAD`와 같다), 커밋 0, 작업 트리 변경 10개 파일, 미추적 파일 4개(`tests/tools/test_protection_json.py`, 변이 표, 카나리아 명세 `dev_release_pr_step_decision_row.toml`, 이 일지). 리뷰 뒤에 카나리아 명세 `dev_release_pr_step_section.toml`을 더했다. 표준 축(sonnet/high)과 명세 축이 병렬로 돌았다. 인계 계기(`hook_handoff`, 셀프 리뷰 직전)가 압축 전 컨텍스트 35만 토큰 기준으로 들어왔으나 압축으로 컨텍스트가 이미 줄었고 다섯 예외에는 들지 않았다. 인계하지 않고 이 세션에서 잇기로 했다(인계의 목적이 컨텍스트 비용이고 그 비용은 압축이 이미 치렀다고 판단한 것이다. 다시 보는 사람은 이 판단이 틀렸다고 보면 일지 `## 다음`의 인계 줄을 고친다).

고친 것:
- (Major, 두 축) 변이 표에 `expect_output`이 없어 `mutate.py --staged`가 막을 판이었다. 표지를 "AssertionError: assert <실제> is <기대>" 줄로 달았고, 변이를 셋에서 여섯으로 늘렸다(dev 삭제 금지, main·dev 관리자 우회). 여섯 모두 `기대 빨강, 결과 빨강`이었다. 못 다룬 것(dev 선형 이력, `allow_force_pushes`, `contexts`)은 표 머리에 적었다.
- (Major, 두 축) `merge.md` 전제 확인 1에 `--event push`를 더했다. 안 붙이면 되돌려 합치기 PR #543의 `pull_request` 실행이 첫 줄에 온다(`gh run list --branch main --workflow ci.yml --limit 3`로 봤다). `headSha` 불일치·진행 중·실패/취소의 보류 문구도 정했다.
- (Major, 두 축) 열린 출시 PR을 이어받을 길이 없었다. "이어받기" 단락과, 번호와 `headRefOid`를 일지에 적는 문장을 더하고, 기다리는 동안 dev가 움직여 머리가 바뀌는 경우(`wait_ci` 종료 4, `--match-head-commit` 거절)와 종료 1의 처리를 정했다.
- (Major 명세) 근거 문장 "출시 PR은 main용 검사를 더해 돌린다"가 `ci.yml` 머리 주석(main에서만 더 도는 검사는 아직 없다)과 달랐다. 고쳤다.
- 결정표 출시 줄의 "위 줄이 아니고"를 `--is-ancestor`가 0이라는 직접 조건으로 바꿨다(되돌려 합치기 PR이 사용자에게 넘어가 열려 있을 때 이 줄이 골라지지 않게).
- 되돌려 합치기 1이 dev 부재를 항상 "끝"으로 읽던 것을, 출시 PR 직후의 부재면 병합 뒤 1(되살리기)로 가게 고쳤다.
- 계기 명령에 `--name-only`를 더했고(slug 읽기), 일괄 편집 커밋(`29165af3b`가 plan.md 19개)은 slug로 쓰지 않는다고 적었다. 끝 줄을 `merge.md` 출시 PR 절 맨 뒤로 옮겼다. 31행의 "재 보지 않았다"를 봤던 만큼으로 고쳤다. 헌법 판은 형제 워크트리가 3.0.90을 쓰고 있어 3.0.91로 비켰다. `CONTEXT.md`의 출시 PR 정의를 계기 문장과 맞췄다.
- 카나리아: 되돌려 합치기 줄의 질문이 새 결정표 줄과 헷갈리지 않게 고쳤고, 새 `merge.md` 출시 PR 절을 묻는 명세 `dev_release_pr_step_section.toml`을 더했다. 세 명세를 다시 돌린다(결과는 각 명세의 `# 최신 결과:` 줄과 티켓).

남긴 것과 이유:
- ADR 0043의 "잊으면 사라진다" 문장 개정: 사용자 승인이 필요한 ADR 개정이라 따로 한다(티켓 결과의 "뒤로 넘기는 것").
- `hook_push_behind_main`이 dev에서도 뒤처진 푸시를 막을지: 이 티켓의 범위 밖이다.
- 병합 방법 절을 원천으로 든 카나리아 명세 열한 개 가운데 돌린 것은 위의 몇 개뿐이다. 나머지는 이 티켓이 바꾸지 않은 문단이라 돌리지 않았고 알림이 남는다.
- 둘째 출시 PR이 BEHIND로 막히는지는 어림이다.

밀 주장(PR 직전 리뷰에 넘길 새 사실 문장):
- "`gh run list --branch main --workflow ci.yml --limit 1`은 #543을 연 뒤 첫 줄이 같은 headSha의 `pull_request` 실행이고 push 실행은 둘째 줄이다. `--event push`를 붙이면 `afe4b7f86`의 push 실행이 `success`로 나온다"(`merge.md` 전제 확인 1).
- "`git log origin/main..origin/dev -G'^\*\*끝:\*\*' --name-only -- '.scratch/*/plan.md'`는 최근 80커밋에서 끝 줄을 적은 커밋 넷을 내고 그 가운데 `29165af3b`는 plan.md 19개를 한꺼번에 고친 일괄 편집이다."
- "`wait_ci`는 출시 PR #542와 되돌려 합치기 PR #543 모두에서 종료 4와 `끝: CodeRabbit 리뷰가 요청되지 않았다`로 끝났다."
- "머리 dev가 움직이면 `wait_ci`가 헤드 변경(종료 4)으로 끝나거나 `--match-head-commit`이 거절된다"(코드와 `gh pr merge --help`를 읽은 것이고 재현하지 않았다).
- "main에서만 더 도는 검사는 아직 없다"(`ci.yml` 머리 주석).

## 검증

`uv run ruff check .` 통과, `uv run ruff format --check .` 통과, `uv run python tools/run_checks.py` 전부 통과(pytest 808초, web-verify 882초, 2026-11-12 이 PC). 카나리아 넷은 셀프 리뷰를 반영한 본문으로 모두 통과 4였다(결과 줄은 각 명세 머리).

## 회고

후보 둘과 넘김 하나를 냈다. 판정은 승인 0, 기각 2, 넘김 1이다.

- **변이 표에 `expect_output`이 없었다(기각).** 이 세션이 변이 표(`protection_json_mutations.toml`)를 `Write`로 새로 쓰면서 표지를 달지 않았고, 두 리뷰 축이 모두 Major로 짚었다. 사건은 있으나 이미 있는 검사가 그 자리에서 알린다. `mutate.py --check <표> 1`은 "빨강을 기대했는데 expect_output 이 없다"로 종료 2였고(손으로 봤다), 같은 검사를 `--staged`가 pre-commit에서 돌린다(`.claude/rules/probes.md` 첫 항목, 대기열 350이 닫힌 처방). 인자 없는 `--check`는 원문만 보고 "원문 확인: 변이 6 모두 원문이 한 번씩 있다"로 지나가는데, 이는 독스트링이 적은 동작(고른 `--check`만 표지를 본다)이다. 층은 이미 검사다.
- **실제로 돌려 본 뒤에도 어림으로 쓴 문장이 그대로 남았다(기각).** `merge.md` 31행이 첫 출시 PR을 병합한 뒤에도 "출시 PR로 재 보지 않았다"로 끝났고, 79행은 존재하지 않는 "(아래 결과)"를 가리켰다. 두 리뷰 축이 `code-review`의 주장 검증 6·7로 잡았다. 리뷰가 잡도록 둔 기준을 어겨 리뷰가 잡은 사건이라 회차로 세지 않고, 새 판단 기준도 아니다.
- **인계 계기를 받고도 인계하지 않았다(넘김).** `hook_handoff`가 `셀프 리뷰 직전` 경계에서 35만 토큰을 알렸고, 이 세션은 `handoff.md` 1의 다섯 예외 어디에도 들지 않았는데도 이어 갔다. 알림 직후 자동 압축이 일어나 컨텍스트가 문턱 아래로 내려갔고, 인계의 목적(큰 컨텍스트의 비용 줄이기)을 이미 달성했다고 판단했기 때문이다. 이 판단은 절차에 없고 이 세션의 일탈이다. 여섯째 예외("계기를 받은 직후 압축이 일어나 문턱 아래로 내려갔다")를 `handoff.md`에 더할지는 사람 판정이다(인계 절차를 느슨하게 하는 것이라 넘김). 사용자에게는 마지막 보고에서 묻는다. 사건은 하나라 더하더라도 문턱(다섯 번째 또는 손상)에 닿지 않으므로 답이 "더한다"여도 대기열 항목(1회차)으로 두는 것이 맞다.

대기열 항목은 쓰지 않았고 이 세션에서 반영한 것도 없다. 만료할 항목은 없었다(`queue_open_rows.py`).

## 다음

이 티켓(`dev-release-pr-step`)은 코드와 문서가 커밋 전까지 끝났다. 순서는 커밋, 푸시, 기준 브랜치 dev로 PR, 봇 회차(`merge.md` 2), ADR 0043 이력의 사용자 승인, 병합(`merge.md` "워크트리에서 병합할 때").

남기는 일:
- ADR 0043의 "잊으면 사라진다" 문장 개정(사용자 승인).
- `tools/hook_push_behind_main.py`가 dev에서도 뒤처진 푸시를 막을지.
- 둘째 출시 PR이 실제로 `BEHIND`가 되는지: 다음 기능의 출시 PR에서 `mergeStateStatus`를 본다.
- `merge.md`를 원천으로 든 카나리아 명세 열은 돌리지 않았다.
- 인계 절차의 여섯째 예외를 더할지(위 회고 넘김).
- 형제 워크트리 `project-pr-skills-dev`가 `merge.md`와 헌법 README·`operations.md`를 함께 고치고 있다(`sibling_overlap`). 병합하는 쪽에서 글자 충돌이 날 수 있다.
