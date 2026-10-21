# ticket-for-every-pr 프로브

명세가 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/ticket-for-every-pr/spec.md`의 "카드 막는 훅"과 "커밋 검사" 결정이다. ADR 0037은 PreToolUse 훅이 세션 카드 도구(`start_session`)를 막을 수 있는지를 어림으로 두고 명세가 재라고 넘겼다. 병합 커밋의 프로브는 명세의 셀프 리뷰가 짚은 갈래(충돌을 풀고 친 커밋이 거짓으로 막힌다)를 잰다.

## 돌리는 법

앱 세션은 스크립트로 띄울 수 없어, 절차는 사람과 그 세션이 손으로 하고 `card_block_app.py`는 판정만 한다. 절차(등록, 새 세션, 세 호출, 판정, 등록 지우기)는 그 독스트링에 있다. 판정은 저장소 루트에서 돈다.

```sh
uv run --no-project python .scratch/ticket-for-every-pr/probes/card_block/card_block_app.py <탐침 세션의 기록 jsonl> <훅 기록 jsonl>
```

병합 커밋의 프로브는 사람 없이 돈다. 저장소 루트에서 친다.

```sh
uv run --no-project python .scratch/ticket-for-every-pr/probes/merge_commit/merge_commit.py
```

등록은 탐침할 워크트리의 `.claude/settings.local.json`(git이 추적하지 않는다)에 넣는다. 훅 설정을 고치는 일이라 자동 모드의 분류기가 자기 수정으로 거부할 수 있으니, 등록하기 전에 사람의 허락을 받는다(이 기능의 명세 일지 2026-10-21-05 "사건").

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `card_block/`(탐침 훅 `log_hook.py`, 판정 `card_block_app.py`, 2026-10-21 기록 `2026-10-21-hook-log.jsonl`·`2026-10-21-result.json`) | 데스크톱 앱 세션에서 매처 `mcp__ccd_session__start_session`의 PreToolUse 훅이 `initiation: own_initiative` 호출을 받는지, 그 입력에 `initiation`이 실리는지, `permissionDecision: deny`로 막으면 카드가 생기지 않고 이유가 모델에게 가는지. 양성 대조로 훅이 지나보낸 호출(없는 `proposal_id`)은 도구가 스스로 거절하는지 | `spec.md` "카드 막는 훅" | 사람 한 번(워크트리 폴더에서 새 앱 세션을 열고 정해진 글을 보낸다)과 그 앱 세션 하나. 표준 라이브러리만 쓴다 | Claude Code 2.1.299(판정 때 탐침 세션 기록의 `version`을 손으로 봤다. 그 기록이 지워져 커밋한 출력에는 판이 없다), Windows 데스크톱 앱 |
| `merge_commit/`(`merge_commit.py`, 2026-10-21 기록 `2026-10-21-result.json`) | 브랜치가 `origin/main`을 합치다 충돌을 풀고 친 커밋의 pre-commit에서, HEAD만으로 구한 merge-base의 색인 차이에 main이 들여온 파일이 섞이는지와, `git merge-base origin/main HEAD <MERGE_HEAD>`로 구하면 빠지는지. 같은 병합을 링크드 워크트리에서 치면 `MERGE_HEAD`를 어디서 찾을 수 있는지(작업 트리 루트의 `.git/MERGE_HEAD`, git 디렉터리의 파일, ref 이름). 충돌 없는 `git merge`에서 pre-commit 훅이 도는지. 양성 대조로 보통 커밋에서 같은 훅이 도는지 | `spec.md` "커밋 검사"의 바뀐 파일(C) | 맨 원격과 클론을 임시 폴더에 넷 만든다(시간은 재지 않았다). 표준 라이브러리만 쓴다 | git 2.32.0.windows.2(결과 줄의 `git`) |

## 2026-10-21 결과: 카드 막기

측정이었다. 판정 출력(`2026-10-21-result.json`)의 `measured`가 참이고 `missing`이 비었다. 세 호출이 모두 훅 기록에 같은 `tool_use_id`로 있었다(`2026-10-21-hook-log.jsonl`).

- **막혔다.** `own_initiative` 호출을 훅이 받았고(기록의 `denied: true`), 그 입력의 키는 `background`, `context`, `initiation`, `prompt`, `title`이었다. 그래서 훅은 `tool_input.initiation`으로 가를 수 있다. 도구 결과는 `PreToolUse:mcp__ccd_session__start_session hook error: ` 뒤에 훅의 이유 글을 그대로 붙인 꼴이었고, 카드 id(`task_id`)가 없었다.
- **양성 대조.** 없는 `proposal_id` 호출은 훅이 지나보냈고(`denied: false`), 도구가 스스로 `proposal_id must be the task_id …`로 거절했다. 그 결과에는 표지가 없다.
- **갈래.** 결과에 표지 `CARD-BLOCK-PROBE-7f3a`가 있다는 것이 "훅이 막았다"를 "앱이 다른 까닭으로 거절했다"와 가른다. 그 문구는 이 탐침의 훅 이유에만 있다. 훅이 지나보낸 호출의 결과에 표지가 없다는 것이, 표지가 훅을 거친 모든 결과에 실리는 것이 아님을 보인다.

못 본 것.

- 판정에 쓴 탐침 세션의 기록 원본은 남지 않았다. 판정 뒤 그 세션이 지워져(같은 폴더의 `bcd9a5c6-….desktop-released.json`이 `reason: delete`, `2026-10-21T04:32:02Z`) 기록 파일이 사라졌다. 저장소에는 훅 기록과, 도구 결과의 글을 400자까지 옮긴 판정 출력만 있다.
- 표본은 호출 하나씩이다. `user_asked`와 `offer`는 부르지 않았다(세션을 열거나 사람에게 묻는다). 그 둘을 지나보내는 것은 훅의 판정 함수가 가르고, 그 함수의 테스트가 본다.
- 등록은 래퍼(`tools/launch_hook.py`)를 거치지 않고 탐침 훅을 바로 불렀다. 래퍼가 훅의 표준 출력을 그대로 넘기는 것은 지금 PreToolUse에서 막는 다른 훅들이 쓰는 길이다(코드를 읽었다. 이 탐침으로 재지 않았다).
- 등록한 자리는 추적하지 않는 `settings.local.json`이고, 실제 훅이 들 `settings.json`에서는 재지 않았다. 두 파일의 훅이 같은 길로 실린다는 것은 어림이다.
- 막힌 뒤 모델이 `initiation`을 바꿔 다시 부르는지는 보지 않았다. 탐침 세션은 값을 바꾸지 말라는 글을 받았다.

손으로 본 것. 세션 도중에 `settings.local.json`에 더한 등록은 그 세션에 실리지 않았다. 명세 세션이 등록한 뒤 `list_start_targets`를 두 번 불렀는데(등록을 한 번 지웠다가 다시 넣은 앞뒤) 두 번 다 훅 기록 파일이 생기지 않았다. 같은 등록이 그 폴더에서 새로 연 탐침 세션에서는 돌았으므로, 등록의 명령이 틀렸다는 해석은 서지 않는다. 그래서 실제 카드 훅을 들이는 티켓은 그 훅을 새 세션에서 확인한다.

## 2026-10-21 결과: 병합 커밋

측정이었다. 결과 줄(`merge_commit/2026-10-21-result.json`)의 `measured`와 `expected`가 참이다. 표지는 넷 다 있었다. 충돌 갈래와 워크트리 갈래의 병합 출력에 `CONFLICT`가 있었고 훅 기록이 생겼으며, 충돌 없는 갈래의 HEAD는 부모가 둘이었고, 양성 대조의 보통 커밋에서 훅 기록이 생겼다. 워크트리 갈래에서는 워크트리의 `.git`이 파일이었고 훅이 본 git 디렉터리가 `…/work/.git/worktrees/linked`였다. 이 결과 파일은 PR 직전 `bug-perf-review`가 짚어 워크트리 갈래를 더한 판의 것이고, 앞 판(갈래 셋)의 값은 이 판의 같은 갈래와 같았다.

- **HEAD만으로 구하면 main의 파일이 섞인다.** 충돌을 풀고 친 커밋의 pre-commit에서 `MERGE_HEAD`가 있었고, `git merge-base origin/main HEAD`에서 색인까지의 차이는 `queue.md`와 `tools/x.py`였다. `tools/x.py`는 main만 더한 파일이다. 워크트리 갈래도 같았다.
- **`MERGE_HEAD`까지 넣으면 빠진다.** `git merge-base origin/main HEAD <MERGE_HEAD>`에서 색인까지의 차이는 `queue.md`뿐이었다. `MERGE_HEAD`를 git 디렉터리의 파일에서 읽어 넣은 것과 ref 이름 그대로 넣은 것이 같았고, 두 갈래 모두 그랬다.
- **링크드 워크트리에서는 작업 트리 루트의 경로로 `MERGE_HEAD`를 찾지 못한다.** 워크트리 갈래에서 `<작업 트리 루트>/.git/MERGE_HEAD`는 없었고(`top_merge_head_present`가 거짓), git 디렉터리의 파일과 ref 이름(`git rev-parse -q --verify MERGE_HEAD`)으로는 있었다. 같은 경로 검사가 충돌 갈래(일반 클론)에서는 참이었으므로, 경로 검사가 늘 거짓을 내서 그렇다는 해석은 서지 않는다. 양성 대조의 보통 커밋에서는 두 길 모두 `MERGE_HEAD`가 없었다.
- **충돌 없는 병합에서는 pre-commit 훅이 돌지 않았다.** 이 갈래의 저장소에는 pre-commit 훅만 두었다. 같은 훅이 양성 대조의 보통 커밋에서는 돌았으므로, 훅을 실행하지 못해서 돌지 않았다는 해석은 서지 않는다.

손으로 본 것. 이 명세의 브랜치가 `origin/main`을 합친 커밋 `bd7a6a24`(`git merge --no-commit --no-ff` 뒤 `git commit`, 충돌 없음)에서, 이 저장소의 pre-commit은 `[INFO] Checking merge-conflict files only.`를 찍고 파일을 받는 ruff 둘은 `(no files to check)`로 건너뛰었지만 러너(`always_run`)는 돌아 여덟 검사가 모두 지났다(그 커밋의 출력을 세션 스크래치패드에 받아 읽었다). 그래서 러너에 둔 검사는 `--no-commit` 병합을 마무리하는 커밋에서도 돈다. 충돌을 풀고 친 커밋도 `MERGE_HEAD`가 있는 커밋이라 pre-commit이 같은 모드로 돌 것으로 보지만 어림이다(그 커밋은 이 프레임워크로 치지 않았다).

못 본 것.

- 이 저장소의 pre-commit 프레임워크(`.pre-commit-config.yaml`의 `default_install_hook_types`)가 까는 훅으로 충돌을 풀고 친 커밋은 재지 않았다. 탐침의 훅은 셸 스크립트 하나다. 그 프레임워크가 pre-merge-commit을 깔지 않는다는 것은 설정 파일을 읽은 것이다.
- `MERGE_HEAD`가 main이 아닌 다른 브랜치인 병합은 돌리지 않았다.
