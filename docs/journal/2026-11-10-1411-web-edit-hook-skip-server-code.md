# 2026-11-10 (14:11) 웹 편집 훅이 서버 코드에도 울리는 일을 대기열에 올린다

세션 제목 `feature/05-acknowledgement-and-token-endpoints`(PR 513을 병합한 세션이 이어 쓴다). 이 일의 브랜치는 `chore/web-edit-hook-skip-server-code`이고 워크트리는 같은 `.claude/worktrees/05-acknowledgement-and-token-endpoints`다(PR 513 병합 뒤 `git switch -c chore/web-edit-hook-skip-server-code origin/main`으로 땄다). 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

05 병합 뒤 마지막 보고에서 이 세션이 물었다. 05 회고가 사용자 판정으로 넘긴 한 건이다. 웹 편집 훅(`tools/hook_web_edit_check.py`)이 `web/apps/portal/server/*.ts`처럼 화면이 없는 서버 코드의 편집에도 `sync-design-system` 확인을 권한다는 것이고, 대기열에 올릴지를 물었다. 사용자의 답(원문):

> 대기열에 올림

## 한 일

- `uv run python tools/queue_open_rows.py --search hook_web_edit_check --search sync-design-system`로 같은 일의 항목을 찾았다. 8개가 맞았으나 모두 `sync-design-system` 스킬 자체를 다룬 항목이고 이 훅의 경로 판정을 다룬 것은 없다(0485·0488·0489·0525·0529가 열림, 0483·0495·0520이 닫힘).
- `.scratch/retro-queue/web-edit-hook-skips-server-code.md`를 새로 썼다(상태 열림, 사용자 승인 2026-11-10, 1회차, ADR 불필요). 어디로는 `tools/hook_web_edit_check.py`, `tools/hook_payloads.toml`, `tests/tools/`다. 본문에 고칠 때 정할 것(화면 폴더로 좁힐지, 서버·도구 폴더를 빼는지)을 적었다.
- `queue_open_rows.py --search`로 새 파일이 열림 1회차로 읽히는 것을 보았다.
- 커밋 `f53d6037`(pre-commit 통과. 검사 열 개, 마크다운 표·줄 구분 문자·변이 표·인용·커밋 메시지 검사). 아직 푸시하지 않았고 PR도 없다.

## 이어받은 세션이 한 일

- 인계 지시문으로 열린 새 세션이다. `tidy-checkouts`는 지시문의 "확인할 선행 조건"이 06 세션이 돈다고 적었고, 스킬 문서(`tidy-checkouts` "부르는 곳")가 나란히 연 묶음은 첫 세션만 돌린다고 적어서 이 세션은 건너뛰었다(문서에서 읽은 것이고 이 세션이 06 세션의 실행을 확인하지는 않았다). `EnterWorktree`로 이 브랜치의 워크트리에 들어갔다.
- `uv run python tools/sibling_overlap.py`를 손으로 쳤고 출력이 "번호 겹침 없음", "함께 고친 파일 없음"이었다. 같은 출력의 origin/main은 `cb26ca5`로 이 브랜치의 기준(`git log`의 `cb26ca5c`)과 같다.
- PR 직전 리뷰로 `coderabbit-review` 서브에이전트를 돌렸다(문서만 바뀐 PR도 면제가 아니다). 서브에이전트의 보고에 따르면 CLI 0.7.5가 `Seat: not assigned`인데도 `coderabbit review --agent --include-untracked`가 종료 코드 0으로 끝났고 마지막 이벤트가 `review_completed`, findings 0건이었다(이 세션이 CLI를 직접 치지 않았고 보고를 옮긴 것이다). 보고가 손으로 대 본 것은 대기열 항목 파일의 형식(`.scratch/retro-queue/README.md`의 모양)과 인용한 일지의 존재, 훅 독스트링의 판정과 본문 서술이 맞는지다.
- 보고의 사소한 지적 하나는 고치지 않고 보류한다. 대기열 항목 본문이 훅 독스트링의 판정을 "1~39행"이라 적었는데 판정 절은 33~39행이라는 것이다(서브에이전트가 독스트링을 읽고 한 말이고 이 세션은 그 행을 다시 세지 않았다). 인용 범위만 넓을 뿐 서술이 틀리지는 않고, 이 항목을 실제로 고치는 세션이 독스트링을 다시 열기 때문에 그 세션이 본다.

## 하지 않은 것

- 훅을 직접 고치지 않았다. 대기열 항목이 맡는다(`next-session` 결정표의 chore 배치 차례에 오면 고른다).
- 이 일지는 커밋하지 않았다. 새 세션이 같은 파일을 이어 쓰고 첫 푸시에 싣는다.

## 다음

- PR을 병합하면 05 회고의 넘김은 이 항목으로 닫힌다. 이 PR에 남는 후속은 없다.
- 대기열 항목 `web-edit-hook-skips-server-code`(열림 1회차)는 `next-session` 결정표의 chore 배치 차례에 오면 고른다. 고칠 때 정할 것(화면 폴더로 좁힐지, 서버·도구 폴더를 빼는지)과 인용 범위 "1~39행"을 33~39행으로 바로잡는 일은 그 항목의 몫이다.
- 06 세션(`feature/06-portal-page-draws-widget`)이 따로 돈다. 주 체크아웃을 당기고 병합된 워크트리를 지우는 `tidy-checkouts`도 그 세션이 돈다.

open-session을 부른다 2026-11-10T05:12Z
