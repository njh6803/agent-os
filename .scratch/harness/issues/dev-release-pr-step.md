# dev-release-pr-step: 기능이 끝나면 출시 PR(dev→main)을 여는 순서를 정한다

**What to build:** ADR 0043은 dev→main을 "기능(`.scratch/plan.md`의 행) 하나가 done이고 main CI가 초록일 때, 그 기능을 끝낸 세션이 PR을 열고 merge 커밋으로 병합한다(사용자 승인 없음)"고 정했다. `dev-base-skills-docs`는 그 PR의 병합 방법(`gh pr merge --merge`)과 병합 뒤 처리를 `next-session` `merge.md`의 "병합 방법"에 적었지만, **PR을 여는 순서와 계기는 어느 티켓도 맡지 않았다.** 이 티켓이 그 순서를 정해 스킬에 싣는다.

정할 것은 셋이다.

- **계기.** 누가 언제 연다고 보장할지. 기능의 마지막 티켓을 닫는 커밋이 끝 줄을 적는 자리(`docs/agents/issue-tracker.md`의 "끝 줄을 적는 때")와 같은 세션인지, `next-session` 결정표에 한 줄을 더할지. 이 일을 잊으면 dev의 완성된 기능이 main에 오르지 않는다.
- **전제 확인.** "main CI가 초록" 확인의 명령(`gh run list --branch main`이나 `gh pr checks`), dev에 이미 올라 있는데 아직 끝나지 않은 다른 기능의 조각이 함께 오르는 것을 어떻게 다룰지(출시 PR은 dev의 머리 전체를 올린다).
- **PR 서식.** 머리가 dev이고 티켓을 가리키지 않는 PR의 제목과 본문. 커밋 검사는 면제로 지난다(`tools/check_ticket.py`). `.github/PULL_REQUEST_TEMPLATE.md`를 그대로 채울지 짧은 서식을 둘지, 출시 PR에 리뷰 봇이 도는지(`dev-review-bot-off`가 정한 것)에 맞춘다.

`dev-base-skills-docs`가 이미 정한 것은 다시 정하지 않는다. 병합은 `--merge`, 사용자 승인 없음, 머리 브랜치를 지우지 않는다.

**대기열:** 없음

**Status:** ready-for-agent

**막는 티켓:** `dev-branch-create`가 병합된 뒤에 한다. dev가 서기 전에는 출시 PR이 없다.

## 수용 기준

- [ ] 출시 PR을 여는 계기가 스킬 한 곳에 서 있고, 기능을 끝낸 세션이 그 계기를 만난다
- [ ] 전제 확인의 명령과 판정이 적혀 있고, 확인이 빨강이면 어떻게 하는지 적혀 있다
- [ ] 출시 PR의 제목과 본문 서식이 있다
- [ ] 바꾼 스킬을 새 세션에서 불러 보았다
- [ ] 검증 명령이 모두 초록이다
