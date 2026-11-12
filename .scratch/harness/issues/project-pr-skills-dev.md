# project-pr-skills-dev: git-pr-merge와 git-pr-feedback의 프로젝트 사본을 dev 모델에 맞게 둔다

**What to build:** 사용자 수준 스킬 `git-pr-merge`와 `git-pr-feedback`은 `main`을 기준 브랜치로 박아 두었다. 기본 브랜치가 dev가 되었으므로(`dev-branch-create`) 이 둘을 그대로 쓰면 병합 뒤 `git checkout main`으로 가고 모든 PR을 squash와 `--delete-branch`로 병합한다. 출시 PR의 머리 dev를 지우려 하고, merge 커밋이어야 하는 PR을 squash한다. 사용자가 둘째 길(프로젝트 사본)을 골랐다. 같은 이름이면 사용자 수준 스킬이 사본을 가려서(결과 1) 사용자가 "다른 이름으로 둔다"를 골랐다. 사용자 수준 파일은 고치지 않는다.

- `.claude/skills/pr-merge/SKILL.md`와 `.claude/skills/pr-feedback/SKILL.md`를 프로젝트 사본으로 둔다. 원본의 단계와 안전장치(병합 가능 여부 확인, 실패한 체크에서 멈춤, 실제 결과대로 보고)는 지킨다. 두 사본은 `프로젝트 사본` 주석을 달고 `tools/check_instructions.py`의 `PATCHED_SKILLS`에 든다.
- `pr-merge`: `main` 고정(`git checkout main`, `git pull`, base가 main이 아니면 되묻기)을 PR 종류별 병합 방법(`merge.md` "병합 방법"의 표를 따른다)과 병합 뒤 체크아웃 규칙으로 바꾼다. 늘 `--squash --delete-branch`인 것을 종류별 `--squash`·`--merge`와 `--match-head-commit`으로 바꾸고 `--delete-branch`는 붙이지 않는다. 병합 뒤 주 체크아웃이면 `tidy-checkouts`를, 워크트리면 `merge.md` "워크트리에서 병합할 때" 3과 4를 따른다.
- `pr-feedback`: 충돌 처리의 `git pull origin main`을 PR의 `baseRefName` 병합으로 바꾼다. 푸시는 PR을 연 세션의 반영 규약에 맞춰 묻지 않는다.
- 이 이름을 부르는 살아 있는 문서를 새 이름으로 바꾼다: `docs/constitution/operations.md`, `next-session`의 `merge.md`, `tidy-checkouts`, `to-tickets`. `merge.md` 4와 `operations.md` 19의 "이 저장소가 고치지 않는다" 문장은 프로젝트 사본이 있다는 사실로 고친다.
- 바꾸지 않은 곳: `KICKOFF.md`와 `kickoff/`의 본문은 main 기준인 새 프로젝트용 런북이라 사용자 수준 원본의 이름(`/git-pr-merge`)을 그대로 둔다. 다만 새 프로젝트가 `next-session/`·`tidy-checkouts`·`operations.md`를 복사하면 그 글이 `/pr-merge`를 부르므로 `KICKOFF.md`의 복사 목록에 두 사본의 항목 한 줄을 더했다(결과 2). 기록(일지, ADR, 옛 티켓, 대기열)도 그대로 둔다.
- 카나리아: 옛 문구를 기대하던 두 명세(`next_session_rate_limit_merge.toml`, `tidy_skill_rate_limit_merge.toml`)를 새 문구로 고치고, 새 스킬마다 명세 하나를 더했다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 같은 이름의 사용자 수준 스킬과 프로젝트 사본 중 어느 쪽이 새 세션에 실리는지 손으로 보고 티켓 끝에 적었다. 가려져서 사용자에게 물었고 "다른 이름으로 둔다"(`pr-merge`, `pr-feedback`)를 받았다(일지 2026-11-12-1353)
- [x] 두 프로젝트 사본이 선 자리와 이름이 위 결정에 맞다
- [x] `pr-merge` 사본에 `main` 고정과 늘 squash가 없고 PR 종류별 병합 방법과 워크트리 규칙이 있다
- [x] `pr-feedback` 사본에 `git pull origin main`이 없다
- [x] `operations.md` 19행과 `merge.md` 4의 "이 저장소가 고치지 않는다" 문장이 사실에 맞게 고쳐졌고 옛 표현의 잔존이 살아 있는 문서에 0이다(`CLAUDE.md` 작업 규약 4의 grep. 셀프 리뷰 두 축과 이 세션의 grep이 `.md` 가운데 이 티켓과 일지(기록)에서만 나옴을 확인했다)
- [x] 바꾼 스킬을 새 세션에서 불러 보았다(카나리아 명세 넷, 결과 3)
- [x] 검증 명령이 모두 초록이다(일지 2026-11-12-1353 "검증")

## 결과

### 1. 이름 우선순위 (2026-11-12, 새 세션에서 손으로 봤다. 커밋한 프로브는 없고 한 번씩만 돌렸다)

이 워크트리에서 `claude -p --model claude-sonnet-5-5 --allowedTools Skill`을 두 번 띄웠다.

- 탐침 하나는 `.claude/skills/git-pr-merge/SKILL.md`(설명과 제목에 표지 `PROBE-PROJECT-COPY`)를 두고 Skill 도구로 `git-pr-merge`를 불렀다. 본문의 첫 제목 줄이 사용자 수준 원본의 `# Git PR 병합기`로 나왔다. 프로젝트 사본의 표지는 나오지 않았다.
- 대조군은 다른 이름의 `.claude/skills/zz-probe-ctl/SKILL.md`를 두고 불렀다. 본문 제목 `# PROBE-CONTROL-BODY`가 그대로 나왔다. 프로젝트 수준 스킬이 발견되는 것은 맞다. 같은 호출에서 `git-pr-merge`의 설명 첫 단어는 `gh`로 나와 원본 설명(`gh pr merge …`)이 실렸다.

결론: 같은 이름이면 사용자 수준 스킬이 프로젝트 사본을 가린다. 사본을 같은 이름으로 두면 쓰이지 않는다. 탐침 파일은 지웠다.

### 2. 결정

사용자가 "다른 이름으로 둔다"를 골랐다(일지 2026-11-12-1353에 질문과 답이 글자 그대로 있다). 이름은 `pr-merge`와 `pr-feedback`이다. 선택지 설명은 이 이름을 부르는 살아 있는 파일에 킥오프 런북 셋을 넣었지만, 런북은 main 기준인 새 프로젝트가 복사해 가서 그 프로젝트에는 프로젝트 사본이 없다. 이름을 바꾸면 그 프로젝트의 병합 단계가 없는 스킬을 가리키므로 런북 본문(`KICKOFF.md`의 단계, `kickoff/runner.md`, `kickoff/pitfalls.md`)은 바꾸지 않았다. 셀프 리뷰 명세 축이 짚은 틈이 있었다. 복사 목록(`KICKOFF.md` 308행 `next-session/`, 310행 `tidy-checkouts`, 314행 `operations.md` 리뷰 파이프라인 절)이 새 프로젝트로 옮기는 글은 이제 `/pr-merge`와 `/pr-feedback`을 부르는데 두 사본은 목록에 없어, 새 프로젝트에서 `Unknown skill`이 난다. 그래서 목록에 두 사본의 항목을 더했다(`PATCHED_SKILLS`에도 더하라고 적었다). 새 프로젝트는 사용자 수준 원본과 사본을 둘 다 갖게 되고 런북 본문은 원본의 이름을 계속 부른다. 이 두 갈래의 이름 불일치는 남긴다(런북 본문을 `/pr-merge`로 바꾸는 일은 새 프로젝트가 사본을 들인 다음에야 맞다).

치르는 값(선택지에 적은 것): 습관대로 `/git-pr-merge`를 치면 사용자 수준 원본이 돈다. 이 값을 줄이는 훅은 이 티켓에 넣지 않았다. 계기를 넣을 만한 후보는 일지 "다음"에 적는다.

### 3. 카나리아

`tools/canary.py`로 명세 넷을 돌렸다(2026-11-12, 이 PC, claude 2.1.322). 실험군은 이 워크트리의 커밋하지 않은 본문(러너가 찍은 커밋은 `4b02bbe29`)이다. 넷 모두 통과 4, "없음" 섞임 0이다.

| 명세 | 대조군 커밋 | 실험군 | 대조군 |
|---|---|---|---|
| `next_session_rate_limit_merge.toml`(고침) | `37759ef2` | 셋 모두 새 문구를 옮겼다 | "없음" |
| `tidy_skill_rate_limit_merge.toml`(고침) | `4b02bbe29` | 셋 모두 새 문구를 옮겼다 | 옛 `/git-pr-merge` 문장을 옮겼다 |
| `pr_merge_skill_kinds.toml`(새) | `4b02bbe29` | 셋 모두 두 구절을 옮겼다 | `Unknown skill: pr-merge` |
| `pr_feedback_skill_base.toml`(새) | `4b02bbe29` | 셋 모두 두 구절을 옮겼다 | `Unknown skill: pr-feedback` |

`next_session_rate_limit_merge.toml`을 `4b02bbe29`로 돌리면 사전 확인이 실패한다. 첫 두 기대 문구가 그 커밋의 `merge.md`에도 있어서이고, 그래서 이 명세는 본문을 `merge.md`로 옮기기 전 커밋 `37759ef2`를 대조군으로 쓴다(명세 머리 주석이 적은 대로).

셀프 리뷰 반영으로 `pr-merge`·`pr-feedback`·`merge.md` 본문을 고친 뒤 `pr_merge_skill_kinds.toml`을 같은 방식으로 한 번 더 돌렸다(같은 날, 같은 커밋 지정). 통과 4, "없음" 섞임 0이고 실험군 셋이 고친 본문에서 두 구절을 글자 그대로 옮겼으며 대조군은 `Unknown skill`이었다. 나머지 셋은 고친 문장이 기대 구절을 건드리지 않아(grep으로 확인) 다시 돌리지 않았다.

이 카나리아는 새 세션이 본문을 싣는지를 보는 것이고, 스킬이 병합을 올바르게 하는지는 보지 않는다. `pr-merge`로 실제 PR을 병합하는 길은 이 PR의 병합에서 처음 쓴다.
