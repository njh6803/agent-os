# dev-release-pr-step: 기능이 끝나면 출시 PR(dev→main)을 여는 순서를 정한다

**What to build:** ADR 0043은 dev→main을 "기능(`.scratch/plan.md`의 행) 하나가 done이고 main CI가 초록일 때, 그 기능을 끝낸 세션이 PR을 열고 merge 커밋으로 병합한다(사용자 승인 없음)"고 정했다. `dev-base-skills-docs`는 그 PR의 병합 방법(`gh pr merge --merge`)과 병합 뒤 처리를 `next-session` `merge.md`의 "병합 방법"에 적었지만, **PR을 여는 순서와 계기는 어느 티켓도 맡지 않았다.** 이 티켓이 그 순서를 정해 스킬에 싣는다.

정할 것은 셋이다.

- **계기.** 누가 언제 연다고 보장할지. 기능의 마지막 티켓을 닫는 커밋이 끝 줄을 적는 자리(`docs/agents/issue-tracker.md`의 "끝 줄을 적는 때")와 같은 세션인지, `next-session` 결정표에 한 줄을 더할지. 이 일을 잊으면 dev의 완성된 기능이 main에 오르지 않는다.
- **전제 확인.** "main CI가 초록" 확인의 명령(`gh run list --branch main`이나 `gh pr checks`), dev에 이미 올라 있는데 아직 끝나지 않은 다른 기능의 조각이 함께 오르는 것을 어떻게 다룰지(출시 PR은 dev의 머리 전체를 올린다).
- **PR 서식.** 머리가 dev이고 티켓을 가리키지 않는 PR의 제목과 본문. 커밋 검사는 면제로 지난다(`tools/check_ticket.py`). `.github/PULL_REQUEST_TEMPLATE.md`를 그대로 채울지 짧은 서식을 둘지, 출시 PR에 리뷰 봇이 도는지(`dev-review-bot-off`가 정한 것)에 맞춘다.

`dev-base-skills-docs`가 이미 정한 것은 다시 정하지 않는다. 병합은 `--merge`, 사용자 승인 없음, 머리 브랜치를 지우지 않는다.

**`dev-branch-create`가 넘긴 메모(2026-11-12).** 보호 설정이 섰다. main은 strict이고 선형 이력을 강제하지 않으며(`tools/protection.json`), dev는 strict가 아니다(`tools/protection-dev.json`). main이 strict라 출시 PR은 dev가 main의 머리를 품어야 병합되는데, 앞 출시 PR이 main에 남긴 merge 커밋은 dev에 없다. 그래서 둘째 출시 PR부터 `mergeStateStatus`가 `BEHIND`가 될 것으로 본다(커밋 관계로 따진 어림이고 출시 PR로 재 보지 않았다). `merge.md`의 "되돌려 합치기" 1은 diff가 0이면 합치지 않으므로 그 merge 커밋만으로는 dev에 오지 않는다. 후보는 출시 PR을 병합한 뒤 main을 dev에 합치는 단계를 더하는 것(`merge.md`는 PR과 `--merge`로만 합치므로 merge 커밋이 하나 더 생긴다), 출시 PR에서만 관리자 우회로 병합하는 것, main의 strict를 끄는 것이다. 마지막 둘은 보호 설정이라 사용자에게 묻는다. 이 티켓이 첫 출시 PR을 열 때 재 보고 정한다.

CodeRabbit이 `dev-branch-create`의 PR #541 첫 회차에 같은 곳을 Major로 짚었다("출시 PR 병합 뒤 main을 dev에 되돌려 합치는 단계를 `operations.md`에 더하라"). 그 PR은 선택을 정하지 않고 이 티켓에 넘겼으므로, 이 티켓이 후보를 정하면 `operations.md`의 병합 규칙 문단과 `merge.md`를 함께 고친다.

같은 메모의 둘째. 출시 PR 병합 뒤 dev가 원격에 남았는지 `git ls-remote --exit-code --heads origin refs/heads/dev`로 본다. 저장소의 자동 삭제(`delete_branch_on_merge`)가 보호 브랜치인 dev를 지우지 않는다는 것은 GitHub 문서의 웹 요약과 `allow_deletions: false`에서 끌어낸 어림이고 재 보지 않았다. 출시 PR은 `merge.md` "워크트리에서 병합할 때" 3(원격 정리의 `ls-remote`)을 건너뛰므로 다른 자리에서는 dev가 지워져도 알아채지 못하고, 그 뒤 `fetch --prune`이 `origin/dev`를 걷으면 기준 브랜치 규칙(`tools/base_rule.py`)이 조용히 main으로 돌아간다(셀프 리뷰 명세 축의 지적).

**대기열:** 없음

**Status:** done

**막는 티켓:** `dev-branch-create`가 병합된 뒤에 한다. dev가 서기 전에는 출시 PR이 없다.

## 수용 기준

- [x] 출시 PR을 여는 계기가 스킬 한 곳에 서 있고, 기능을 끝낸 세션이 그 계기를 만난다
- [x] 전제 확인의 명령과 판정이 적혀 있고, 확인이 빨강이면 어떻게 하는지 적혀 있다
- [x] 출시 PR의 제목과 본문 서식이 있다
- [x] 첫 출시 PR을 병합한 뒤 dev가 원격에 남았는지 `ls-remote`로 봤고, 출시 PR의 병합 뒤 처리에 그 확인이 있다
- [x] 바꾼 스킬을 새 세션에서 불러 보았다
- [x] 검증 명령이 모두 초록이다

## 결과

2026-11-12. 사용자에게 보호 설정이 걸린 선택 둘을 물었고(일지 `docs/journal/2026-11-12-1623-dev-release-pr-step.md` "사람의 몫 둘") 답은 (가) 병합 뒤 main을 dev에 되돌려 합친다, (나) 첫 출시를 지금 한 번 한다였다. GitHub 보호 설정은 바꾸지 않았다.

1. **계기.** `next-session` 결정표에 줄을 더했다. 기능 계획의 `**끝:**` 줄을 적은 커밋이 dev에만 있고(`git log origin/main..origin/dev -G'^\*\*끝:\*\*' -- '.scratch/*/plan.md'`) 열린 출시 PR이 없으면 그 줄을 고른다. 마지막 티켓을 병합한 세션이 보통 그 세션이고 잊어도 다음 병합 뒤의 세션이 같은 상태를 읽는다. 하네스 변경(끝 줄이 없는 harness 티켓)은 계기가 아니다. 명령의 `-G`와 pathspec은 이 저장소의 로그에서 끝 줄을 적은 커밋 넷을 찾았다(`git log origin/main~80..origin/main`, 손으로 봤다).
2. **전제 확인.** main CI(`gh run list --branch main --workflow ci.yml --limit 1`의 `headSha`가 `origin/main`과 같고 `success`)와 dev가 main을 품었는지(`--is-ancestor`)다. 어긋나면 `출시 보류: <까닭>` 한 줄을 쓰고 원래 줄로 돌아간다. 진행 중인 다른 기능의 조각이 함께 오르는 것은 막지 않고 PR 본문에 알린다(dev의 티켓 PR은 dev CI를, 출시 PR은 거기에 main용 검사를 지난 머리이기 때문이다).
3. **서식.** 제목 `chore: <slug들>을 main에 출시한다`, 본문은 `.github/PULL_REQUEST_TEMPLATE.md`가 아니라 올리는 기능 / 함께 오르는 진행 중 조각 / 전제 / 병합 넷이다. 머리가 dev인 PR에서 CodeRabbit과 claude-review는 SKIPPED였고(PR #542 `gh pr view --json statusCheckRollup`, 손으로 봤다) 커밋 검사 `ticket`은 SUCCESS였다.
4. **첫 출시를 실제로 했다(PR #542).** 절차를 쓴 뒤 PR이 dev에 병합되기 전에 dev(`4b02bbe29`, main 위의 #541 하나)를 main에 올려 절차를 거쳐 봤다. 사용자가 고른 일이다. 계기 조건(끝 줄을 적은 기능)은 어겼다. `verify`를 포함한 검사가 모두 SUCCESS, `mergeStateStatus` CLEAN, `gh pr merge 542 --merge --match-head-commit …`로 병합했고 main은 `82297e614`에서 `afe4b7f86`이 됐다.
5. **병합 뒤 `ls-remote`.** `git fetch --prune origin` 뒤 `git ls-remote --exit-code --heads origin refs/heads/dev`가 `4b02bbe29 refs/heads/dev`를 내며 0으로 끝났고, 기본 브랜치도 `gh repo view`가 `dev`였다. 저장소의 자동 삭제는 머리 dev를 지우지 않았다(첫 출시 PR 하나로 본 것이다).
6. **BEHIND 어림을 재 본 정도.** 병합 직후 `gh api repos/njh6803/agent-os/compare/main...dev`가 `behind_by: 1`, `ahead_by: 0`을 냈고 `git diff --quiet origin/dev...origin/main`은 0이었다. 곧 dev가 main의 끝 커밋 하나를 품지 않았고 내용은 같다. 이것은 strict 보호가 보는 관계이지만 둘째 출시 PR이 실제로 `BEHIND`로 막히는지는 보지 못했다(그러려면 dev에 앞선 커밋이 더 있는 PR이 필요하다). 어림이다.
7. **되돌려 합치기 PR(#543).** 내용 diff가 0인 main→dev PR도 GitHub가 열어 주었고(`gh pr create`가 주소를 냈다) 검사가 모두 SUCCESS(`claude-review`도 돌았고 CodeRabbit만 SKIPPED), `mergeStateStatus` CLEAN으로 `--merge`로 병합됐다. 병합 뒤 `git merge-base --is-ancestor origin/main origin/dev`가 0, dev는 `641165ff5`, `ls-remote`도 0이었다. 그래서 판정을 diff가 아니라 `git merge-base --is-ancestor origin/main origin/dev`로 바꿨다. 결정표의 되돌려 합치기 줄과 `merge.md`의 "되돌려 합치기" 1·5, 그 줄을 묻는 카나리아 명세 `dev_base_next_session_backmerge_row.toml`도 맞췄다.
8. **`wait_ci`의 종료 4.** 출시 PR과 되돌려 합치기 PR은 CodeRabbit이 건너뜀 상태로 남아 `tools/wait_ci.py`가 `--expect verify`를 줘도 종료 4와 `끝: CodeRabbit 리뷰가 요청되지 않았다`로 끝났다(PR #542, 손으로 봤다). 이 PR들에서는 그것이 정상이고 나머지 검사 줄이 모두 SUCCESS인지 읽으면 된다. `merge.md`가 `--expect verify`로 이것을 피한다고 적었던 것을 고쳤다.
9. **ADR 0043 이력.** 2026-11-12 "출시 PR 뒤에도 main을 dev에 되돌려 합친다"를 더하고 "되돌려 합치기" 항목에 포인터를 달았다. 이 이력은 사용자 승인이 필요하다(`CLAUDE.md` 작업 규약 5). 승인은 병합 전에 받는다.
10. **보호 JSON 값 시험.** `tests/tools/test_protection_json.py`가 두 파일의 `strict`·`required_linear_history`·삭제와 강제 푸시 금지·`verify`·관리자 우회를 단언한다(`dev-branch-create`의 claude-review Nit). 변이 여섯(`.scratch/harness/probes/protection_json_mutations.toml`: main strict 끄기, dev strict 켜기, main 선형 켜기, dev 삭제 금지 풀기, main·dev 관리자 우회 막기)이 모두 `expect_output` 표지가 있는 채 기대대로 빨강이었다. 변이가 없는 단언은 dev 선형 이력, `allow_force_pushes`, `contexts`다(표 머리에 적었다). GitHub에 적용된 값은 읽지 않는다.
11. **카나리아.** 셀프 리뷰를 반영한 본문으로 넷을 돌렸다. 새 결정표 줄 `dev_release_pr_step_decision_row.toml` 통과 4(대조군 `4b02bbe29`), 새 출시 PR 절 `dev_release_pr_step_section.toml` 통과 4(대조군 `4b02bbe29`), 되돌려 합치기 줄 `dev_base_next_session_backmerge_row.toml` 통과 4(대조군 `82e7a38fb`), 병합 방법 절 `dev_branch_create_merge_protection.toml` 통과 4(대조군 `82297e614`). `"없음"` 섞임은 모두 0이었다(2026-11-12, 이 PC, claude 2.1.322). `merge.md`를 원천으로 든 기존 명세 열하나 가운데 돌린 것은 `dev_branch_create_merge_protection` 하나이고 나머지 열은 이 티켓이 바꾸지 않은 문단을 묻는 명세라 돌리지 않았다. 새 명세 `dev_release_pr_step_section`까지 돌려 결과 줄을 고친 뒤 `sibling_overlap`의 카나리아 알림은 사라졌다. 이것이 돌리지 않은 열 명세가 통과한다는 뜻은 아니다.
12. **판 번호.** 헌법 판을 3.0.87에서 3.0.93으로 올렸다(`ci-llm-job`이 3.0.88과 3.0.92를, `project-pr-skills-dev`가 3.0.90을 쓰고 있어 비켰다. 3.0.89와 3.0.91은 비어 있다. 처음에 3.0.91로 올렸다가 PR #544가 3.0.92로 먼저 병합되어 dev를 합치며 3.0.93으로 비켰다).
13. **셀프 리뷰 반영.** 두 축이 낸 Major를 고쳤다(일지 `## 셀프 리뷰`): 변이 표지, 전제 확인 1의 `--event push`(`gh run list --branch main --workflow ci.yml --limit 3`에서 #543의 `pull_request` 실행이 첫 줄, push 실행이 둘째 줄이었다), 열린 출시 PR 이어받기와 머리 이동 처리, `ci.yml`과 다른 근거 문장, 결정표 출시 줄의 조건. `merge.md` 출시 PR 절은 카나리아 `dev_release_pr_step_section.toml`이 묻는다.

뒤로 넘기는 것: `tools/hook_push_behind_main.py`가 dev에서도 뒤처진 푸시를 막을지는 여전히 정하지 않았다. ADR 0043의 "잊으면 사라진다" 문장 개정은 사용자 승인으로 따로 한다.
