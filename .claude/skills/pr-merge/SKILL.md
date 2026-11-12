---
name: pr-merge
description: "PR 병합. 리뷰가 끝난 PR을 종류(티켓 PR, 핫픽스, 출시 PR, 되돌려 합치기 PR)에 맞는 방법(squash나 merge 커밋)으로 병합하고 뒷정리를 잇는다. 사용자가 PR 병합·머지·squash merge를 말할 때와 next-session이 병합을 부를 때 쓴다. 이 저장소는 사용자 수준 git-pr-merge 대신 이 스킬을 쓴다. 그 스킬은 main에 고정하고 늘 squash로 병합한다."
---

<!-- 프로젝트 사본. 사용자 수준 스킬 git-pr-merge(~/.claude/skills)에서 갈라졌다. 같은 이름이면 사용자 수준 스킬이 프로젝트 사본을 가려서(2026-11-12 새 세션에서 손으로 봤다) 이름을 달리했다. 바꾼 것: main 고정(base 되묻기, git checkout main, git pull)을 PR 종류별 병합 방법과 병합 뒤 체크아웃 규칙으로, 늘 squash와 --delete-branch를 종류별 방법과 머리 SHA 대조로. 근거는 .scratch/harness/issues/project-pr-skills-dev.md와 ADR 0043. -->

# PR 병합

리뷰가 끝난 PR을 종류에 맞는 방법으로 병합한다. 병합은 되돌리기 어렵고 모두에게 영향을 주므로, 병합할 수 있는 상태인지 먼저 확인하고 확인이 안 되면 병합하지 않는다. 기준 브랜치의 규칙은 `docs/constitution/operations.md`의 "브랜치와 병합"이, 종류별 표는 `.claude/skills/next-session/merge.md`의 "병합 방법"이 원천이다.

## 1단계: 대상 PR과 종류

```bash
gh pr view [<번호>] --json number,title,url,state,headRefName,baseRefName,mergeable,mergeStateStatus,headRefOid
```

번호 없이 부르면 현재 브랜치의 PR을 읽는다. 읽은 `number`를 이후 `gh` 명령마다 준다. 번호가 없는 `gh pr checks`는 다른 브랜치에서 불렀을 때 엉뚱한 PR을 본다.

- 연결된 PR이 없으면 중단하고 알린다.
- `state`가 `MERGED`이면 이미 병합된 PR이다. 병합 뒤 끊겼다가 이 스킬을 다시 읽는 길이므로 2단계와 3단계를 건너뛰고 4단계로 간다. 병합된 PR은 `mergeable`이 `UNKNOWN`이라 아래 재조회를 하지 않는다. `CLOSED`이면 병합 없이 닫힌 PR이라 알리고 중단한다.
- `mergeable`이나 `mergeStateStatus`가 `UNKNOWN`이면 충돌이 아니라 GitHub가 계산하는 중이다. 몇 초 간격으로 최대 5번 다시 보고, 계속 `UNKNOWN`이면 알리고 중단한다.
- `CONFLICTING`이거나 차단·뒤처진(`BEHIND`) 상태면 병합하지 않는다. 티켓 PR과 핫픽스는 `pr-feedback`으로 먼저 풀라고 안내한다. 출시 PR과 되돌려 합치기 PR은 `pr-feedback`으로 보내지 않고 사용자에게 넘긴다. `pr-feedback`은 머리 브랜치에 base를 병합하는데, 그 동작은 dev를 main에 합치거나 main을 dev에 합친다(`merge.md` "되돌려 합치기" 4). `UNSTABLE`은 차단이 아니다. claude-review의 계정 한도뿐이면 2단계 판정대로 병합할 수 있다.
- 병합 방법과 base를 종류로 정한다. 종류별 표의 원천은 `merge.md` "병합 방법"이다.
  - 티켓 PR(머리가 dev, main, `hotfix/*`가 아닌 브랜치. `feature/*`, `chore/*`, `docs/*`와 앱이 만든 이름)은 base가 기준 브랜치(`origin/dev`가 있으면 dev, 없으면 main)이고 `--squash`다.
  - 핫픽스(머리가 `hotfix/*`)는 base가 main이고 `--squash`다.
  - 출시 PR(머리 dev, base main)과 되돌려 합치기 PR(머리 main, base dev)은 `--merge`다. squash하면 두 브랜치에 같은 변경이 다른 커밋으로 남아 다음 합치기가 충돌한다.
- base가 그 종류의 base가 아니면 병합하지 않고 사용자에게 알린다.

## 2단계: CI 체크

```bash
gh pr checks <번호>
```

- `no checks reported`와 함께 exit code 1이 나오면 CI가 없다는 뜻이지 실패가 아니다. 확인할 체크가 없는 것으로 보고 3단계로 간다.
- 실패한 체크가 있으면 병합하지 않고 중단해, 어떤 체크가 왜 실패했는지 보고한다. 실패를 무시하는 `--admin`은 사용자가 그 상황에서 명시적으로 요청했을 때만 쓴다. 실패가 claude-review의 계정 한도뿐이면 실패로 세지 않는다. 알아보는 법과 PR 코멘트에 남길 것은 `docs/constitution/operations.md`의 리뷰 파이프라인 3이다.
- pending이 있으면 끝나기를 기다린다. `next-session` 절차 안이면 `merge.md` "병합 전" 2의 `tools/wait_ci.py`를 백그라운드로 띄우고, 아니면 `gh pr checks --watch`를 쓴다.
- 모든 체크가 통과했거나 체크가 없을 때만 3단계로 간다.

## 3단계: 병합

1. 머리 SHA를 다시 읽는다. 2단계에서 기다리는 사이 푸시가 있었을 수 있어 1단계의 값을 쓰지 않는다.

   ```bash
   gh pr view <번호> --json headRefOid
   ```

   티켓 PR과 핫픽스는 현재 브랜치가 이 PR의 머리이므로 `git rev-parse HEAD`가 이 값과 같은지 본다. 다르면 푸시하지 않은 커밋이 병합에서 빠지거나 원격이 앞섰으므로 중단하고 알린다. 출시 PR과 되돌려 합치기 PR은 머리가 dev나 main이라 로컬 HEAD와 대지 않고 이 값을 그대로 쓴다. 주 체크아웃의 dev가 원격보다 뒤처졌다는 이유로 멈추지 않는다(`merge.md` "병합 방법").
2. 병합한다. `<방법>`은 1단계에서 정한 `--squash`나 `--merge`다.

   ```bash
   gh pr merge <번호> <방법> --match-head-commit <방금 읽은 headRefOid>
   ```

3. 머리 브랜치 삭제는 저장소의 자동 삭제(`delete_branch_on_merge`)에 맡기고 `--delete-branch`는 붙이지 않는다. 그 플래그는 병합 뒤 작업 폴더에서 base 브랜치로 `git checkout`을 쳐서 워크트리에서 깨지고, 출시 PR의 머리 dev를 지우려 한다(`merge.md` "워크트리에서 병합할 때" 2).
4. 명령이 실패하면(권한, 보호 설정, merge queue 등) gh의 에러 메시지를 그대로 전하고 여기서 멈춘다. 출시 PR과 되돌려 합치기 PR이 보호 설정에 거절되면 병합하지 않고 사용자에게 넘긴다. merge queue를 쓰는 저장소는 즉시 병합하지 않고 큐에 올리거나 auto-merge를 켤 수 있으니 그 결과를 그대로 알리고, 4단계는 실제 병합이 끝난 뒤에만 한다. 병합이 끝난 뒤 이 스킬을 다시 부르면 1단계의 `MERGED` 갈래로 4단계에 닿는다.

## 4단계: 병합 뒤

병합이 실제로 성공했을 때만 한다. 작업 폴더가 워크트리인지는 `git rev-parse --git-dir`와 `git rev-parse --git-common-dir`을 따로 쳐서 다르면 워크트리다.

- **머리 브랜치가 티켓 PR이나 핫픽스의 것이면** 원격에 그 브랜치가 남았는지 `merge.md` "워크트리에서 병합할 때" 3으로 본다(자동 삭제를 믿고 확인하지 않는 길을 막는다). 출시 PR과 되돌려 합치기 PR은 머리가 dev나 main이라 이 정리를 건너뛰고, 그 브랜치를 지우지 않는다.
- **주 체크아웃이면** Skill 도구로 `tidy-checkouts`를 돈다. 루트 브랜치를 당기고 병합된 워크트리와 로컬 브랜치를 지운다.
- **워크트리이면** 다른 체크아웃을 바꾸지 않는다. `주 체크아웃 미갱신` 보고는 `merge.md` "워크트리에서 병합할 때" 4가 정한다.
- **핫픽스였으면** `merge.md`의 "되돌려 합치기"까지 해야 끝이다.
- **출시 PR이었으면** `merge.md` "출시 PR"의 병합 뒤 1~3(dev가 원격에 남았는지 보기, main을 dev에 되돌려 합치기, 보고에 `출시: PR <번호>, main <SHA>`)까지 해야 끝이다. 되돌려 합치지 않으면 둘째 출시 PR부터 막힌다.

## 5단계: 최종 보고

각 단계가 실제로 어떻게 됐는지 그대로 보고한다. 병합한 PR 번호와 제목, 쓴 병합 방법, 4단계에서 한 일을 적는다. 멈춘 단계가 있으면 그 사실과 이유를 적고, 건너뛰거나 실패한 단계를 성공으로 쓰지 않는다.
