---
name: tidy-checkouts
description: "주 체크아웃을 origin/main으로 당기고 병합된 워크트리와 로컬 브랜치를 지운다. 주 체크아웃 세션에서만 돈다(워크트리 세션이면 한 줄을 남기고 멈춘다). 주 체크아웃에서 PR을 병합한 뒤 next-session 1단계가 부르고, 워크트리에서 병합한 세션이 연 새 세션이 지시문대로 워크트리에 들어가기 전에 부르며, 사용자가 /tidy-checkouts를 치거나 주 체크아웃 갱신·워크트리 정리를 말할 때 돈다."
---

# 체크아웃 정리

병합 뒤에 남는 둘을 치운다. 주 체크아웃(저장소 루트, `git worktree list`의 첫 줄)이 `origin/main`보다 뒤에 있는 것과, 병합된 브랜치의 워크트리와 로컬 브랜치다. 앞의 것이 남으면 새 세션과 훅이 주 체크아웃의 옛 하네스로 돈다(`docs/constitution/operations.md` 환경 규약 상세의 모드 표). 뒤의 것이 쌓이면 저장소 전체를 훑는 검색에 옛 사본이 섞인다(대기열 47).

**주 체크아웃 세션에서만 돈다.** 워크트리 세션이 다른 체크아웃을 바꾸지 않는 경계와 그 근거는 `next-session` "워크트리에서 병합할 때"가 원천이다. 이 스킬은 당기고 지우기만 한다. 브랜치를 따거나 커밋하지 않는다.

**git은 모두 `git -c core.longpaths=true`로 친다.** 아래의 `git`은 그 줄임이다. 이 PC의 git(2.32.0.windows.2)은 `core.longpaths`가 꺼져 있다. 꺼진 채로는 `node_modules` 아래 긴 경로 때문에 `git worktree remove`가 지우다 멈추고(`.scratch/harness/probes/worktree_longpath.py`), `git status`는 긴 경로 안의 추적하지 않는 파일을 stderr 경고만 내고 빠뜨린다(반박 검증이 손으로 재현했다, 일지 2026-10-06-03). 둘이 겹치면 커밋하지 않은 파일을 깨끗하다고 보고 지운다.

## 순서

1. **자리.** `git rev-parse --show-toplevel`이 `git worktree list`의 첫 줄 경로와 같아야 한다. 다르면 이 세션은 워크트리에 있다. 아무것도 바꾸지 않고 `주 체크아웃 세션에서 /tidy-checkouts` 한 줄을 보고하고 멈춘다. 같아도 `git rev-parse --show-prefix`가 `.claude/worktrees/`로 시작하면 지우다 만 워크트리에 남은 폴더다. `.git` 파일이 없어 git이 그 폴더를 루트로 읽는다(반박 검증이 손으로 재현했다, 일지 2026-10-06-04). 그 경로를 보고하고 멈춘다. 둘 다 아니면 `git fetch origin`. 끝: 이 세션이 주 체크아웃에 있고 원격을 받아 왔다.
2. **주 체크아웃.** 깨끗하다는 것은 `git status --porcelain`의 stdout과 stderr가 모두 빈 것이다. 추적하지 않는 파일도 센다(`next-session` 3단계와 같은 정의). 당기기는 `git merge --ff-only --no-overwrite-ignore origin/main`이다. `pull`과 `switch`는 무시된 파일(루트의 `.env` 등)을 들어오는 커밋이 같은 경로를 추적하면 묻지 않고 덮어쓰고(`--overwrite-ignore`가 기본값), `pull`은 `--no-overwrite-ignore`를 받지 않는다(반박 검증이 손으로 재현했다, 일지 2026-10-06-03·04). 루트의 브랜치(`git branch --show-current`)에 따라 아래 가운데 하나만 한다.
   - **main이고 깨끗하다.** `git rev-list --count origin/main..HEAD`가 0이 아니면 로컬 main에 원격에 없는 커밋이 있다. 건드리지 않고 사람에게 넘긴다. main 위 커밋은 훅이 막으므로 그것은 사고다. 0이면 당긴다.
   - **main인데 깨끗하지 않다.** 건드리지 않고 바뀐 파일을 보고한다. 누군가 그 체크아웃에서 일하고 있다.
   - **다른 브랜치다.** 셋이 모두 맞을 때만 루트를 main으로 옮긴다. 그 브랜치가 병합됐다(3의 판정 1), 루트가 깨끗하다, 그 브랜치를 맡은 다른 세션이 돌지 않는다(3의 판정 3. 이 세션의 제목이 그 브랜치면 이 세션의 브랜치라 옮겨도 된다). 옮기기는 `git switch --no-overwrite-ignore main`, 당기기, `git branch -D <브랜치>` 순이다. `switch`가 어떤 이유로든 실패하면(main이 다른 워크트리에 체크아웃되어 있다, 덮어써질 파일이 있다) 뒤의 둘을 치지 않고 그 오류를 사람에게 넘긴다. 셋 가운데 하나라도 맞지 않으면 루트는 건드리지 않는다. `주 체크아웃 미갱신: 루트는 <브랜치>(<이유>)` 한 줄과 그 브랜치를 맡은 세션을 보고하고 3으로 간다. 그 세션이 주 체크아웃에서 병합하면 `/git-pr-merge`가 main으로 돌아와 당긴다.
   - **분리 HEAD다.** 건드리지 않고 사람에게 넘긴다.

   끝: 루트가 main이고 `git rev-parse HEAD`가 `git rev-parse origin/main`과 같다. 다르면 당겼다고 보고하지 않고 미갱신 한 줄에 두 커밋을 적는다.
3. **병합된 워크트리.** `git worktree list --porcelain`의 워크트리를 첫 항목(주 체크아웃)을 빼고 하나씩 보고, 판정 1~3이 모두 맞는 것만 4로 지운다(대기열 47).
   1. **병합됐다.** 브랜치의 병합된 PR이 있고(`gh pr list --state merged --head <브랜치> --json headRefOid`) 그 `headRefOid`가 브랜치 끝과 같다.
      - 브랜치 끝은 워크트리면 그 워크트리의 HEAD이고, 체크아웃되지 않은 브랜치면 `git rev-parse refs/heads/<브랜치>`다.
      - `--head`는 브랜치 이름만 봐서 포크의 같은 이름 브랜치 PR도 돌려주지만(`gh pr list --help`를 읽었다) `headRefOid`와 브랜치 끝의 비교가 그것을 거르므로, 이 비교를 빼지 않는다.
      - squash라 `git log origin/main..HEAD`로는 판정이 되지 않는다. 브랜치 끝이 `origin/main`의 조상인 것으로도 판정하지 않는다. 막 따고 아직 커밋하지 않은 브랜치도 조상이라, 다른 세션이 막 들어간 워크트리를 지운다(일지 2026-10-05-05).
      - 분리 HEAD와 PR 머리가 다른 것은 지우지 않고 후보로 사람에게 넘긴다.
   2. **깨끗하다.** 둘 다 맞아야 한다. 하나라도 어긋나면 지우지 않고 남긴 이유를 보고한다.
      - `git -C <경로> status --porcelain --untracked-files=all`의 stdout과 stderr가 모두 비었다. stderr의 경고(`could not open directory … Filename too long` 등)는 git이 그 아래를 보지 못했다는 뜻이다.
      - `git -C <경로> status --porcelain --ignored`의 `!!` 항목이 아래의 다시 만들 수 있는 것뿐이다. `git worktree remove`는 무시된 파일을 묻지 않고 지우므로, `.env`나 `traces/`가 있으면 남긴다(반박 검증이 손으로 재현했다, 일지 2026-10-06-04).
        - 파이썬: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.import_linter_cache/`, `.grimp_cache/`
        - web: `node_modules/`, `.next/`, `next-env.d.ts`, `test-results/`, `playwright-report/`, `blob-report/`, `coverage/`
        - 설정: 루트와 내용이 같은 `.claude/settings.local.json`
   3. **주인이 없다.** `list_sessions`(limit 50)에서 이 세션을 뺀 `isRunning` 세션을 본다.
      - 제목이 그 브랜치인 세션이 있으면 그 워크트리를 지우지 않는다.
      - 제목이 지금 체크아웃된 어느 브랜치와도 맞지 않는 세션이 있으면 어느 워크트리도 지우지 않는다. 그 세션이 어느 워크트리에 있는지 알 수 없다. 같은 워크트리에서 병합하고 다음 브랜치를 따 가며 일하는 세션은 제목이 첫 브랜치이거나 앱이 지은 이름이고, 그 워크트리는 다음 브랜치를 따기 전까지 판정 1·2를 지난다(이 스킬을 들인 세션이 그랬다, 일지 2026-10-06-03). 후보와 그 세션을 사람에게 넘기고, 사람이 그 세션이 후보에 없다고 답하면 지운다(새 세션의 첫 턴에서 불렸으면 답을 기다리지 않는다, 아래 "부르는 곳").
      - 잠금의 사유는 `claude session <이름> (pid <N>)` 모양이고, `<이름>`은 그 워크트리를 연 세션이 준 EnterWorktree 이름이다. 그 pid가 살아 있으면(`Get-Process -Id <N>`) 지우지 않고 그 세션을 사람에게 알린다. 죽었으면 `git worktree unlock <경로>`. 잠금이 없다고 주인이 없는 것은 아니다. `git worktree add`로 판 워크트리와 `EnterWorktree(path)`로 들어간 워크트리는 잠기지 않는다(일지 2026-10-06-04).
   4. **지운다.** 지우기 직전에 `git -C <경로> branch --show-current`와 `git -C <경로> rev-parse HEAD`를 다시 보고, 판정 때와 다르면 지우지 않는다. 같으면 `git worktree remove <경로>`. 그것이 0이 아닌 코드로 끝나면 이유와 상관없이 `git branch -D`도 다른 삭제도 하지 않고 멈춘다. 경로와 메시지를 보고하고 그 경로를 쓰던 세션을 사람에게 알린다. git 2.32는 지우다 실패해도 등록을 지운다(`.scratch/harness/probes/worktree_longpath.py`). 그 폴더의 `.git` 파일도 지워져, 남은 폴더 안에서 친 git은 루트 저장소에 닿는다(반박 검증이 손으로 재현했다, 일지 2026-10-06-04). `remove`가 성공하면 `git branch -D <브랜치>`. 병합 여부는 판정 1이 정하고 `-d`는 squash 병합을 알아보지 못한다.

   어디에도 체크아웃되지 않은 로컬 브랜치도 판정 1이 맞으면 `git branch -D`로 지운다. `.claude/worktrees/` 아래인데 `git worktree list`에 없는 디렉터리는 사람에게 넘긴다. 앱 자신의 정리(`[WorktreePool]`)는 표지 `claude-desktop-worktree`가 있고, 잠금과 실행 중인 세션과 `.worktree-keep`이 없고, 24시간 바뀌지 않았고, 깨끗한 것만 지우고 브랜치는 남긴다(검증 서브에이전트가 앱 번들 2.19675.0.0의 `reapUntrackedWorktreeDir`를 읽었다). 이 저장소의 워크트리에는 그 표지가 없어 2026-10-05까지 앱이 지운 것이 없었다(앱 로그 `main.log`를 읽었다). 끝: 워크트리와 로컬 브랜치마다 지웠거나 남긴 이유가 있다.
4. **보고.** 루트 한 줄(당겼으면 앞뒤 커밋, 남겼으면 이유), 지운 워크트리와 브랜치, 남긴 것과 그 이유를 한 줄씩 적는다. 끝: 보고가 나갔다.

## 부르는 곳

- 주 체크아웃 세션이 `/git-pr-merge`로 병합한 뒤 `next-session` 1단계가 Skill 도구로 부른다. 루트는 그 스킬이 이미 당겼으니 2는 확인으로 끝난다.
- 워크트리 세션이 병합하면 그 세션은 부르지 않는다(1에서 멈춘다). 그 세션이 연 새 세션이 첫 턴에 `EnterWorktree`보다 먼저 부른다. 계기는 지시문 "어디서" 줄의 워크트리 문장 머리이고, 첫 턴 훅(`tools/hook_prompt_directive.py`)이 다시 짚는다. 나란히 여는 묶음이면 첫 세션만 부른다. 순서와 첫 세션만인 이유는 `next-session` 3단계가 원천이다. 새 세션이 주 체크아웃이 아닌 폴더에서 열렸으면 1에서 멈춘다. 이때 사람에게 넘기는 것은 무엇이든 4의 보고에 남기고 답을 기다리지 않는다. 지시문의 일이 그 뒤에 있고, 지우지 못한 워크트리는 다음 정리가 다시 본다. 그 새 세션을 연 세션이 아직 돌면 그 워크트리는 판정 3이 남긴다.
- 사람은 아무 때나 주 체크아웃 세션에서 `/tidy-checkouts`를 친다.

## 하지 않는 것

| 하지 않는다 | 대신 |
|---|---|
| 워크트리 세션에서 당기거나 지우기 | 1에서 한 줄을 남기고 멈춘다 |
| 깨끗하지 않은 워크트리를 `--force`로 지우기, `git clean`, `Remove-Item`으로 대신 지우기 | 깨끗한 것만 git으로 지운다. git이 거부하거나 실패하면 사람에게 넘긴다 |
| `git worktree prune` | 등록 하나는 `git worktree remove <경로>`로 걷는다. 폴더가 없어도 그 등록만 걷는다. `prune`은 폴더가 옮겨진 다른 워크트리의 등록까지 걷어, 그 분리 HEAD 커밋이 참조를 잃었다(반박 검증이 손으로 재현했다, 일지 2026-10-06-04) |
| `git pull`, 옵션 없는 `git switch` | `git merge --ff-only --no-overwrite-ignore origin/main`, `git switch --no-overwrite-ignore main` |
| 남의 브랜치에 있는 루트를 main으로 옮기기 | 병합됐고, 깨끗하고, 주인이 없을 때만 옮긴다. 아니면 그 세션을 알린다 |
| 잠금 pid가 살아 있는 워크트리의 unlock | 그 세션을 사람에게 알린다 |
| 앱의 `clean_up_worktrees` | 이 스킬의 3으로 지운다. 그 도구는 30·60·90일 넘게 쓰지 않은 세션의 워크트리만 지워(도구 설명을 읽었다) 병합 직후의 정리에 맞지 않는다 |
| 루트에서 브랜치를 따거나 커밋하기 | 이 스킬은 당기고 지우기만 한다 |
