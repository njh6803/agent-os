# merge-commit-message-type-rejected: 푸시 훅이 기준 브랜치를 합치라고 안내하면서 병합 커밋 메시지의 타입 규약을 말하지 않아, `git merge origin/dev`가 commit-msg 검사에서 막혀 병합을 커밋하지 않은 채 멈췄다

**상태:** 열림
**어디로:** `tools/hook_push_behind_main.py`의 `reason_text`(안내 문장에 `git merge origin/<기준 브랜치> -m "chore: origin/<기준 브랜치>를 합쳐 기준을 맞춘다 (<티켓 이름>)"`처럼 commit-msg가 받는 제목의 꼴을 보인다). 훅의 안내 문장이라 고치는 자리는 하나이고, 계기 훅이라 막는 쪽은 바뀌지 않는다.
**승인:** 자체 승인 2026-11-28, 1회차, 일지 2026-11-28-0125-build-closes-frame-ancestors-and-start-fills-them.md. ADR 불필요

widget-runtime-values 02의 세션이 푸시 훅의 안내대로 `git merge origin/dev`를 쳤더니 기본 병합 메시지의 타입 `merge:`가 commit-msg 검사(허용 타입은 feat, fix, docs, style, refactor, test, chore, perf)에 막혀 병합이 커밋되지 않은 채 멈췄다. 이어 `git commit -F`로 마칠 때는 pre-commit 러너가 돌아 Bash의 600초 제한을 넘겼다. 안내의 "충돌 없는 합치기에는 pre-commit이 돌지 않는다"는 병합이 스스로 끝날 때의 이야기이고, 메시지가 거절되어 손으로 커밋하는 길에서는 맞지 않는다. 안내가 올바른 제목의 꼴을 보이면 첫 시도에서 스스로 끝난다. 같은 사건이 되풀이되면 이 항목이 회차를 센다.
