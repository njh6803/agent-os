# 017: tidy_checkouts 가 접힌 무시 폴더와 막 딴 브랜치를 바로 가른다

**What to build:** `tools/tidy_checkouts.py` 의 판정 두 자리를 고친다. 하나(대기열 464)는 판정 2의 무시된 항목이다. `status --porcelain --ignored`(기본 `traditional`)는 무시된 것만 든 미추적 폴더를 그 폴더 하나로 접어 찍는다. 위젯을 한 번 띄운 워크트리에서는 `web/apps/widget/public/`(안에 `fonts/` 와 `element.js` 뿐)이 그렇게 찍혀 `RECREATABLE_PATHS` 와 맞지 않았고, 병합된 위젯 워크트리 아홉이 정리에서 남았다(일지 2026-10-26-01 "정리"). 무시 패턴에 맞은 자리만 찍는 `--ignored=matching` 으로 읽고, 티켓 web-widget 10 이 더한 `web/apps/widget/public/element.js` 를 다시 만들 수 있는 자리에 넣는다. 다른 하나(대기열 440)는 체크아웃되지 않은 브랜치의 판정 1이다. PR 없이 끝이 `origin/main` 에 있는 브랜치는 지운다고 내는데, `judge` 는 워크트리 목록을 읽은 뒤에 브랜치 목록을 읽어, 나란히 연 형제 세션이 그사이에 딴 브랜치(`EnterWorktree` 뒤 워크트리 안의 `git switch -c`·`git branch -m`, 등록보다 브랜치를 먼저 만드는 `git worktree add -b`)는 체크아웃되지 않은 브랜치로 보인다(일지 2026-10-23-13). 그 브랜치의 reflog 마지막 기록이 최근이면 `judge` 와 `remove-branch` 모두 남긴다. 둘 다 지우는 판정이라 `.claude/rules/tools.md` 의 반박 시험을 거친다.

**대기열:** 464, 440

**Status:** done

## 수용 기준

- [x] `judge` 와 `remove` 의 다시 판정이 무시된 항목을 `--ignored=matching` 으로 읽는다. `web/apps/widget/public/` 안에 `fonts/` 와 `element.js` 만 든 병합된 워크트리를 `judge` 가 지울 후보로 찍고 `remove` 가 지운다(실제 git 시험)
- [x] `web/apps/widget/public/element.js` 가 다시 만들 수 있는 자리다. 워크트리 판정(`unrecreatable`)과 등록 없는 폴더 판정(`_recreatable_file`)이 `RECREATABLE_PATHS` 의 그 자리를 함께 본다
- [x] 반박 시험: 접힌 폴더 안에 무시되지 않은 미추적 파일이 있거나, 무시됐지만 다시 만들 수 없는 파일(`.env`)이 있으면 남긴다. 자리째로 보는 경로와 이름만 같은 다른 자리의 `element.js` 는 다시 만들 수 없는 것이다. 안쪽 `.gitignore` 로만 무시되는 폴더(`.grimp_cache/`)는 `matching` 이 그 안을 하나씩 찍으므로 조상 폴더로 접어 한 번에 옮기고, 같은 꼴의 다른 폴더는 남긴다(셀프 리뷰 명세 축). 윈도의 git 이 따라가 찍는 링크(정션) 안의 항목은 링크째로 접어, 링크 바깥의 파일을 옮기지 않는다(PR 직전 bug-perf-review). 추적 파일이 든 자리는 옮기지 않는다. 다시 만들 수 있는 이름의 폴더에 커밋된 파일이 있으면 그 폴더로 접지 않아 그 안의 `.env` 는 남기고 그 안의 다시 만들 수 있는 폴더만 옮기며(PR 봇 CodeRabbit), 추적 폴더를 갈음한 링크로 접은 자리가 있으면 그 워크트리를 남긴다(셀프 리뷰 명세 축)
- [x] PR 없이 끝이 `origin/main` 에 있는 체크아웃되지 않은 브랜치 가운데 reflog 의 마지막 기록이 정한 창 안인 것을 `judge` 와 `remove-branch` 가 남기고, 이유 줄에 막 딴 브랜치라고 적는다. 병합된 PR 로 지우는 브랜치는 창을 보지 않는다
- [x] 반박 시험: `git branch -m` 으로 이름을 바꾼 브랜치는 막 딴 것이다. 창 밖의 기록, reflog 가 없는 브랜치(`core.logAllRefUpdates=false`)는 지운다(못 보는 것으로 독스트링에 적는다). 앞날 시각의 기록은 남긴다
- [x] 모듈 독스트링의 판정 2·체크아웃되지 않은 브랜치·못 보는 것이 바뀐 동작을 적고, 이 동작을 옛 표현으로 적은 살아 있는 문서가 grep 으로 0이다
- [x] 대기열 464·440 을 닫는다
- [x] 검증 명령이 모두 초록이다
