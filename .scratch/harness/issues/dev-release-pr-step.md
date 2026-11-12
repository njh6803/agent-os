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

**Status:** ready-for-agent

**막는 티켓:** `dev-branch-create`가 병합된 뒤에 한다. dev가 서기 전에는 출시 PR이 없다.

## 수용 기준

- [ ] 출시 PR을 여는 계기가 스킬 한 곳에 서 있고, 기능을 끝낸 세션이 그 계기를 만난다
- [ ] 전제 확인의 명령과 판정이 적혀 있고, 확인이 빨강이면 어떻게 하는지 적혀 있다
- [ ] 출시 PR의 제목과 본문 서식이 있다
- [ ] 첫 출시 PR을 병합한 뒤 dev가 원격에 남았는지 `ls-remote`로 봤고, 출시 PR의 병합 뒤 처리에 그 확인이 있다
- [ ] 바꾼 스킬을 새 세션에서 불러 보았다
- [ ] 검증 명령이 모두 초록이다
