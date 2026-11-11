# dev-base-skills-docs: 스킬과 규약 문서와 ADR 포인터를 기준 브랜치 규칙에 맞추고 핫픽스를 되돌려 합치는 순서를 적는다

**What to build:** `dev-branch-transition` 티켓의 "기준 브랜치 규칙"(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main)을 스킬과 문서에 싣는다. 하네스는 다음 실행에 바로 영향을 주는 코드이므로(`CLAUDE.md` 작업 규약 4) 바꾼 스킬은 새 세션에서 불러 본다.

- 스킬: `next-session`(`SKILL.md`, `merge.md`, `directive.md`), `tidy-checkouts`, `code-review`, `open-session`, `sync-design-system`(`SKILL.md`, `upload.md`, `import.md`), `retro`, `writing-for-agents`. 곳마다 `main`이 기준 브랜치를 뜻하는지(바꾼다), 운영 브랜치를 뜻하는지(그대로 둔다), 둘 다 가능한지를 가른다. 지시문의 "확인할 선행 조건"과 `merge.md`의 "워크트리에서 병합할 때"는 병합 대상이 dev일 때와 main일 때를 가른다. 병합은 티켓 PR은 dev로 squash, dev→main은 merge 커밋(`gh pr merge --merge`, 사용자 승인 없음)이다.
- **되돌려 합치기를 `next-session`의 `merge.md`에 적는다.** hotfix를 main에 합친 세션이 바로 main을 dev에 merge 커밋으로 합친다(ADR 0043 Consequences "되돌려 합치기"). 이 티켓이 정할 것은 둘이다. (가) 되돌려 합치기를 PR(머리 `main`, base `dev`)로 하는지 로컬 병합 뒤 푸시로 하는지. 직접 푸시는 `dev`를 막는 훅이 `git commit`만 보므로 병합 커밋을 지나가지만, 보호 설정과 맞는지 본다. (나) 잊지 않게 하는 계기. `hook_pr_next_session`이 hotfix 병합 뒤 지시문에 이 단계를 싣게 할지 정한다.
- 문서: `CLAUDE.md`의 환경 함정, `docs/constitution/operations.md`의 "브랜치와 병합"과 "가드레일"과 "리뷰 파이프라인", `docs/agents/issue-tracker.md`(규약 첫 항목의 "main에 들어가는 PR", 전체 계획 절의 "나란히 돈 마지막 티켓 둘" 문단. 그 문단은 ADR 0043 전환을 맡는 harness 티켓이 다시 정한다고 적었다), `.github/PULL_REQUEST_TEMPLATE.md`, `CONTEXT.md`의 용어(이미 든 개발 브랜치 용어와 맞는지).
- ADR 포인터: ADR 0005의 "squash 병합, main 이력은 PR 단위"와 ADR 0037의 "main에 들어가는 PR은 모두 티켓 파일 하나를 가리킨다" 문장 바로 뒤에 ADR 0043을 가리키는 `(바뀜: ADR 0043)`를 단다. `.claude/rules/adr.md`의 규칙대로 `tools/check_adr_pointers.py`가 통과해야 한다.
- 사용자 수준 스킬 `~/.claude/skills/git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`는 저장소 밖이다. 어디서 `main`을 박았는지만 읽어(고치지 않고) 목록으로 만들고 티켓 끝에 적어, 사용자에게 고칠지 묻는다. 고치는 것은 사용자가 승인했을 때만 한다. 읽은 목록에 저장소 밖 파일의 내용을 옮기지 않는다.

**대기열:** 없음

**Status:** ready-for-agent

**막는 티켓:** `dev-branch-transition`이 병합된 뒤에 한다. 크기가 한 세션에 안 들면 스킬 몫과 문서 몫으로 나누고 새 티켓 파일을 쓴다.

## 수용 기준

- [ ] 스킬마다 `main`의 뜻을 가른 표가 티켓 끝에 있고, 바꾼 스킬은 새 세션에서 불러 보았다
- [ ] 되돌려 합치기의 순서와 계기가 `merge.md`에 적혀 있고, 위 (가)(나)의 결정과 까닭이 티켓 끝에 있다
- [ ] 규약 문서의 "main에 PR한다"는 문장이 기준 브랜치 규칙으로 바뀌었고 옛 표현의 잔존이 살아 있는 문서에 0이다(`CLAUDE.md` 작업 규약 4의 grep)
- [ ] ADR 0005와 0037에 포인터가 달렸고 `tools/check_adr_pointers.py`가 통과한다
- [ ] 사용자 수준 스킬의 `main` 박힌 곳 목록이 티켓 끝에 있고 사용자에게 고칠지 물었다
- [ ] 검증 명령이 모두 초록이다
