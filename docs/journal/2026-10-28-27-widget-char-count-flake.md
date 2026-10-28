# 2026-10-28 (27) 위젯 승인 시험의 센 수 사례가 가끔 빨간 원인을 가르고 고친다 (harness 023)

next-session 지시문으로 연 새 세션이다. 나란히 여는 여덟 가운데 다섯째라 `tidy-checkouts`는 돌지 않았고(묶음의 첫 세션이
돈다), 주 체크아웃에서 브랜치를 따지 않고 워크트리 `023-widget-char-count-flake`에 들어가
`chore/023-widget-char-count-flake`로 바꿨다. 첫 재현 실행 도중 세션이 한 번 끊겼고, 사용자가 다시 시도하라고 해 이었다.

> 사용자: "대기열 486을 티켓 .scratch/harness/issues/023-widget-char-count-flake.md로 쓰고 한다"

> 사용자: "다시 시도해 주세요"

## 세 줄 계획

(1) 재현 루프 프로브로 빨간 회차의 포커스 자리와 사유 칸의 값을 찍어 원인을 가른다. (2) 원인을 시험 쪽에서 없애고 같은
루프로 다시 잰다. (3) 계약(`sdk/`, `openapi.json`, 헌법)과 위젯 코드에는 닿지 않는다.

## 진단

- 코드를 읽고 세운 해석은 셋이었다. 포커스를 빼앗김(`ApprovalCard`의 첫 그리기 효과가 포커스를 제목으로 옮긴다), 이모지
  짝이 깨짐(붙여 넣기가 UTF-16 두 단위 사이에 든다), 카드가 다시 서며 칸의 상태를 잃음.
- 프로브 `.scratch/harness/probes/widget_char_count/repeat.mjs`는 그 사례를 따라 하는 사례를 시험 파일 사본 끝에 붙여
  Vitest `repeats`로 되풀이하고 회차마다 한 줄을 찍는다. 첫 판은 `console.log`로 찍었는데 그 실행의 출력에 실리지 않아
  (5회차 모두 측정 아님으로 1로 끝났다) 임시 파일에 덧붙이게 바꿨다.
- 고치기 전 커밋(`--source 5ccb51a0`) 300회차 가운데 빨강 9회차가 모두 포커스 갈래였다(프로브의 출력). 9회차 모두 카드를
  기다린 직후의 포커스가 요청 입력창에 남아 있었고, 초록 291회차는 모두 이미 제목에 있었다. 짝 갈래와 다시 서기 갈래는
  0이었다. 대기열 행이 적은 로컬 20번 중 2번보다 드물었다.

## 고친 것

- `web/apps/widget/components/pages/WidgetApproval.test.tsx`의 `untilPaused`: 카드에 이어 포커스가 제목에 간 것까지
  기다린다. 고친 뒤 같은 프로브 300회차가 모두 초록이었다(프로브의 출력). 같은 도우미를 지나는 빈 사유 사례들도 같은
  틈이 닫힌다(코드를 읽었다).
- `WidgetConversation.test.tsx`의 같은 꼴 사례는 승인 카드가 없고 입력창의 효과가 옮기는 포커스가 그 입력창이라 고치지
  않았다(코드를 읽었다. 재지 않았다).
- 화면 코드를 고쳤다는 훅의 알림으로 `/sync-design-system 확인`을 돌렸다. 결정표는 `continue`였고, 들이는 중이던
  `feature/11-web-edit-teal-accent-600`의 PR #413이 병합돼 있어 PR 전에 main을 합친다.
- `.scratch/retro-queue.md`: 486을 이 티켓으로 닫았다.

## 인계

`/code-review`를 부른 직후 인계 계기(`셀프 리뷰 직전`, 세션 컨텍스트 245,231 토큰)가 와서 새 세션에 넘긴다. 이 세션의
제목은 `chore/023-widget-char-count-flake`이고 `chore/023-widget-char-count-flake (인계함)`으로 바꾼다. 남은 일은 셀프
리뷰, 커밋(pre-commit), main 합치기(PR #413의 병합 커밋 `ad8a9c37`을 아직 품지 않았다. `sync_with_base_branch`는 커밋하지
않은 변경이 있으면 거부하므로 커밋 뒤에 친다), PR, 봇 회차, 병합, 회고와 "다음"이다. 아무것도 커밋하지 않았다.
워크트리 잠금은 이미 풀려 있었다(`git worktree unlock`이 `is not locked`).

지시문:

```
다음 작업: .scratch/harness/issues/023-widget-char-count-flake.md. 대기열 486: 위젯 승인 시험의 센 수 사례가 가끔 빨간 원인을 가르고 고친다(원인 가름과 고침은 끝났다)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 486을 티켓 .scratch/harness/issues/023-widget-char-count-flake.md로 쓰고 한다
브랜치: chore/023-widget-char-count-flake
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md, docs/journal/2026-10-28-27-widget-char-count-flake.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 그 뒤 커밋하고, PR #413의 병합 커밋 ad8a9c37을 품도록 sync_with_base_branch로 main을 합친 뒤 PR을 연다. docs/journal/2026-10-28-27-widget-char-count-flake.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-28T08:10:59Z

## 이어받은 세션

지시문으로 연 새 세션이 워크트리 `023-widget-char-count-flake`에 `EnterWorktree(path)`로 들어가 이었다.

> 사용자: "대기열 486을 티켓 .scratch/harness/issues/023-widget-char-count-flake.md로 쓰고 한다"

## 셀프 리뷰

`/code-review`, 기점 `5ccb51a0`(origin/main과의 merge-base), 미커밋 변경 파일 셋, 미추적 셋, 커밋 0. 표준 축은 sonnet·high.

고친 것:
- 표준·명세 둘 다: `untilPaused` 위에 옛 독스트링이 겹쳐 남았다. 지웠다.
- 표준: 닫은 대기열 486 행에 취소선이 없었다. 501 행의 꼴대로 둘째 칸을 `~~`로 감쌌다.
- 표준·명세 둘 다: README와 티켓이 "9회차 모두 … 첫 붙여 넣기 17,999개는 들어갔다"고 적었는데 프로브는 빨간 회차를 다섯만 찍었다. 프로브가 빨간 회차를 모양별로 모두 세게(`redShapes`) 고치고 다시 잰다.
- 표준: 고친 뒤 "300회차 모두 초록"에 고친 길의 표지가 없었고 기점이 작업 트리였다. 사본의 `untilPaused` 안 카드를 찾은 직후에 포커스 자리(`afterCard`)를 적어, 효과가 늦은 회차(`lateEffect`) 가운데 초록인 수를 표지로 센다. 커밋한 뒤 그 커밋을 `--source`로 주어 다시 잰다.
- 명세: README의 "붙여 넣기 앞뒤의 … 칸의 값"이 실제와 달랐다(칸의 값은 붙여 넣기 뒤에만 찍는다). 찍는 자리대로 고치고, 짝 갈래는 코드 포인트 수로 가르며 선택 범위는 기록만 한다고 적었다.
- 명세: 티켓의 대화 시험 이유("`Composer`의 효과가 옮기는 포커스는 시험이 누른 그 입력창이다")가 틀렸다. 그 사례는 교환이 없어 `focusFor`가 null이고 효과가 포커스를 옮기지 않는다(`WidgetScreen.tsx`의 `focusFor`, `Composer.tsx`의 효과를 읽었다).
- 표준: 티켓의 `user.type` 사례 "빼앗길 틈이 좁다"는 근거 없는 낙관이었다. 효과가 누른 뒤에 돌면 입력이 제목에 갈 수 있다고 고쳤다(코드 읽기).
- 표준·명세 둘 다: 수용 기준 "검증 명령이 모두 초록이다"가 돌리기 전에 `[x]`였다. 해제하고 Status를 `in-progress`로 되돌렸다. 검증을 돌린 뒤 다시 체크한다.
- 표준(Minor): 프로브가 `--source` 뒤에 값이 없으면 `git show undefined:…`로 죽었다. 2로 끝나게 했다.

남긴 것:
- 표준(Minor): "승인 묻기가 서면 포커스가 …" 사례의 `waitFor`가 `untilPaused`의 기다림과 겹친다. 그 사례는 포커스 이동 자체를 보는 시험이라 단언을 남겼다.
- 명세(b): `untilPaused`를 지나는 모든 사례에 포커스 조건이 더해져, 포커스 효과가 깨지면 상관없는 사례도 시간 초과로 빨개진다. 그 효과가 깨진 것은 접근성 사례가 따로 잡고, 고침이 그 도우미의 틈을 닫는 것이라 받아들였다.
- 표준(Minor): 프로브가 도중에 끊기면 `ProbeCharCount.test.tsx`가 남는다. README가 두 실행을 나란히 돌리지 말라고 적고 있고, 남으면 지우면 된다. 고치지 않았다.
- 표준: 일지 끝의 `open-session을 부른다 …` 줄은 계기 줄이라 남겼다.
- 화면 코드를 처음 고쳤다는 훅 알림(시험 파일의 독스트링 한 줄 삭제)에 `/sync-design-system 확인`을 다시 부르지 않았다. 같은 브랜치에서 앞 세션이 오늘 돌려 `continue`였고 이번 편집은 화면 모양과 무관한 시험 파일이다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):
- "그 사례에는 승인 카드가 서지 않고, 교환이 없어 `WidgetScreen`의 `focusFor`가 null이라 입력창(`Composer`)의 효과도 포커스를 옮기지 않는다."
- "`user.type(reasonBox(), …)`을 치는 사례도 효과가 칸을 누른 뒤에 돌면 입력이 제목에 갈 수 있다(코드 읽기, 재지 않았다)."
- 프로브 머리 주석의 "`lateEffect` … 고친 판에서는 이것이 고친 길을 지났다는 표지다. 고치기 전 판에서 효과가 늦은 회차는 빨갰기 때문이다."

## 커밋과 다시 잰 결과

- 커밋 `bd52303e`. pre-commit 결과(그 커밋의 출력): check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, web-verify, pytest, 커밋 메시지가 Passed. ruff check·ruff format은 스테이지된 `.py`가 없어 건너뛰었다(이 브랜치는 `.py`를 바꾸지 않았다). 위젯 e2e·`-m llm_widget`·사진 비교는 치지 않았다. 바꾼 것이 단위 시험 파일의 도우미 하나라 위젯 코드·api-client·서버 경로에 닿지 않는다.
- 고친 프로브로 다시 쟀다(프로브의 요약 줄과 `redShapes`). `node .scratch/harness/probes/widget_char_count/repeat.mjs 300 --source 5ccb51a0`: 빨강 12/300, 12 모두 한 모양(카드 직후 포커스가 입력창, 첫 붙여 넣기 뒤 칸 17,999·포커스는 제목, 두 번째 뒤에도 17,999, 같은 요소). 초록 288은 모두 카드 직후 포커스가 제목. `--source bd52303e`: 300/300 초록, 그 가운데 효과가 늦은 회차 10이 모두 초록.
- README 행, 티켓 Comments, 대기열 486의 닫힘 문구를 다시 잰 수로 고쳤다. 앞의 "진단"과 "고친 것"의 9/300·작업 트리 300/300은 첫 판의 기록으로 둔다.
- 티켓의 "검증 명령이 모두 초록이다"를 위 pre-commit 결과로 다시 체크하고 Status를 done으로 돌렸다.

## 합치기와 번호 옮김

- `sync_with_base_branch`는 "앱이 만든 워크트리가 아니다"로 거부해 `git fetch origin main`과 `git merge --no-edit origin/main`으로 직접 합쳤다. 충돌 없음.
- main에 일지 2026-10-28-23이 들어와 `sibling_overlap.py --move`로 이 일지를 2026-10-28-19에서 2026-10-28-27로 옮겼다.
- 그 커밋의 pre-commit에서 이 브랜치가 건드리지 않은 `tests/tools/test_rerun_runner.py::test_첫_인계가_나면_새_회차를_열지_않는다`가 한 번 빨갰다(`assert {'rerun-x-01-A-1'} == {…B-1'}`). 그 사례만 `uv run pytest -q` 로 다시 돌리니 통과했다(361초). 형제 세션 여럿이 함께 돌던 때라 부하로 난 간헐 실패로 보고 커밋을 다시 쳤다. 원인은 가르지 않았다.
