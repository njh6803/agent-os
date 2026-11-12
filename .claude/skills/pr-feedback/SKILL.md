---
name: pr-feedback
description: "PR 피드백 반영. 열린 PR의 CI 결과와 리뷰 코멘트(인라인 코멘트 포함)를 읽어 지적된 내용을 코드에 반영한다. 반영 도중 PR의 base 브랜치가 앞서 충돌이 나면 base를 머리 브랜치에 병합하고 충돌 마커를 논리적으로 푼다. 사용자가 리뷰 코멘트·PR 피드백 반영이나 CI 실패 확인을 말할 때와 next-session이 반영을 부를 때 쓴다. 이 저장소는 사용자 수준 git-pr-feedback 대신 이 스킬을 쓴다. 그 스킬은 충돌을 main에서만 푼다."
---

<!-- 프로젝트 사본. 사용자 수준 스킬 git-pr-feedback(~/.claude/skills)에서 갈라졌다. 같은 이름이면 사용자 수준 스킬이 프로젝트 사본을 가려서(2026-11-12 새 세션에서 손으로 봤다) 이름을 달리했다. 바꾼 것: 충돌 처리의 git pull origin main을 PR의 base(baseRefName) 병합으로, 푸시 확인을 PR을 연 세션의 반영 규약(operations.md 리뷰 파이프라인)에 맞춰 건너뛰는 것으로. 근거는 .scratch/harness/issues/project-pr-skills-dev.md와 ADR 0043. -->

# PR 피드백 반영

열린 PR의 CI 상태와 리뷰 코멘트를 확인해 지적된 내용을 코드에 반영한다. 반영하는 동안 PR의 base 브랜치가 앞서 충돌이 나면 병합과 해결까지 이어서 한다.

`gh pr diff`는 코드 diff만 보여 주고 리뷰 코멘트는 포함하지 않는다. 특정 라인에 달린 인라인 코멘트는 `gh pr view`와 `gh api`로 따로 읽는다.

## 명령

| 목적 | 명령 |
|---|---|
| CI와 체크 상태 | `gh pr checks <번호>` |
| 리뷰 요약(승인과 변경 요청, 본문) | `gh pr view <번호> --json reviews --jq '.reviews[] \| {author: .author.login, state, body}'` |
| 인라인 코멘트 | `gh api repos/{owner}/{repo}/pulls/<번호>/comments --paginate --jq '.[] \| {path, line, body, user: .user.login}'` |
| 일반 코멘트 | `gh pr view <번호> --comments` |
| 코드 diff(코멘트 위치의 맥락) | `gh pr diff <번호>` |

`{owner}`와 `{repo}`는 gh가 현재 저장소의 값으로 채운다. `<번호>`는 1단계에서 읽은 PR 번호다. 번호 없이 부르면 현재 브랜치의 PR을 보므로, 다른 브랜치에서 부르면 엉뚱한 PR을 읽는다.

## 1단계: 대상 PR

```bash
gh pr view [<번호>] --json number,title,url,headRefName,baseRefName,mergeStateStatus
```

연결된 PR이 없으면 멈추고 알린다. PR 번호를 받거나 먼저 `git-pr` 스킬로 PR을 만들도록 안내한다. 여기서 읽은 `baseRefName`이 5단계의 병합 대상이다.

## 2단계: CI 상태

```bash
gh pr checks <번호>
```

실패한 체크는 어떤 체크가 왜 실패했는지 읽는다. 로그가 필요하면 `gh run view <run-id> --log-failed`를 쓴다. lint나 타입체크나 테스트처럼 코드로 고칠 수 있는 실패는 4단계에서 반영할 지적에 넣는다. `no checks reported`와 함께 exit code 1이 나오면 CI가 없다는 뜻이지 실패가 아니니 넘어간다.

## 3단계: 리뷰 피드백 수집

명령 표의 인라인 코멘트, 리뷰 요약, 일반 코멘트 셋을 모두 읽는다. 인라인 코멘트는 `path`와 `line`이 있으므로 그 위치의 코드를 열어 무엇을 지적했는지 읽고, 맥락이 더 필요하면 `gh pr diff`로 변경 범위를 본다.

## 4단계: 코드에 반영

- 코멘트마다 항목 하나로 놓고 차례로 처리한다. 봇 리뷰의 둘째 회차부터는 Critical·Major만 고치고 나머지는 보류 이유를 PR 코멘트에 남긴다(회차를 세는 법은 `next-session` `merge.md` 2의 "회차 세기").
- 지적이 명확하면 바로 고친다.
- 지적이 모호해 해석이 갈리거나 리뷰어들의 지적이 서로 부딪치면 임의로 정하지 않고 사용자에게 묻는다.
- 고친 뒤에는 `CLAUDE.md`의 검증 명령 가운데 바꾼 곳에 걸리는 것을 돌린다.

## 5단계: base와의 충돌

반영하는 동안 base가 앞서 나갔으면(다른 PR이 먼저 병합된 경우 등) PR의 base를 머리 브랜치에 병합한다. 푸시한 PR의 이력을 다시 쓰지 않으려고 rebase가 아니라 병합이다.

```bash
git fetch origin
git merge origin/<baseRefName>
```

충돌이 나면 `git status`로 파일 목록을 보고, 파일마다 `<<<<<<<`, `=======`, `>>>>>>>` 사이의 두 변경을 모두 읽는다. 한쪽을 기계적으로 고르지 않고 지금 반영 중인 피드백의 취지를 해치지 않는 선에서 두 변경을 논리적으로 합친다. `.scratch/plan.md`의 충돌은 표지를 손으로 풀지 않고 `uv run python tools/plan_table.py`를 다시 돌려 푼다(`docs/agents/issue-tracker.md`). 마커를 지우고 정리한 뒤 이어서 한다.

```bash
git add <푼 파일>
git commit --no-edit
```

병합 커밋 뒤 나머지 피드백을 반영하고, 충돌을 푸는 사이 반영하려던 수정이 되돌아가지 않았는지 마지막에 다시 본다.

## 6단계: 커밋과 푸시

- 커밋 메시지는 `git-commit` 스킬 규칙(컨벤셔널 커밋, 한국어)을 따른다. 피드백 반영은 보통 `fix:`나 `refactor:`다.
- PR을 연 세션이 반영하는 것이 이 저장소의 규약이므로(`docs/constitution/operations.md`의 리뷰 파이프라인) 푸시는 사용자에게 묻지 않는다. 묻고 턴을 끝내면 `next-session`의 대기가 뜨지 않아 세션이 깨어나지 않는다. 다른 사람이 연 PR이거나 사용자가 푸시를 미루라고 했으면 푸시 전에 묻는다.
- 푸시한 뒤에는 `gh pr checks --watch`나 `tools/wait_ci.py`로 체크가 통과하는지 이어서 본다.

## 주의사항

- 푸시한 이력은 강제 푸시로 다시 쓰지 않는다. 리뷰어가 이미 본 이력이다.
- 충돌을 풀 때 한쪽 변경을 통째로 버리지 않고 두 변경의 의도를 모두 읽어 합친다.
- 리뷰 코멘트는 `gh pr view`와 `gh api`로 읽는다. `gh pr diff`만 보고 코멘트를 확인했다고 여기지 않는다.
