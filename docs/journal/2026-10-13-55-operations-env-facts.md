# 2026-10-13 (55) operations.md에 환경 사실 셋과 EnterWorktree 세션의 실림을 적는다

## 계기

일지 41의 세션이 PR #227을 병합한 뒤 낸 지시문으로 연 새 세션이다. 대상 파일이 `docs/constitution/operations.md`로 같은
대기열 넷(90·147·159·189)을 한 chore PR로 반영한다. 지시문은 222·225(훅)를 열린 PR #225가 들고 있어 고르지 않았다고
적었는데, 두 행의 대상은 operations.md가 아니라 `tools/`의 훅이다. #225는 이 세션 도중 병합됐다(`4814568`).

> 사용자: (지시문의 시작 프롬프트) ".scratch/retro-queue.md의 대기열 90·147·159·189를 docs/constitution/operations.md에
> 반영하는 하네스 chore를 한다. 189는 모드 표를 먼저 재고 next-session 3단계도 함께 본다"

## 앞 세션에서 넘겨받은 기록

지시문의 "이어받을 상태"가 일지 41에 적히지 않은 것을 넘겼다. PR #227은 CI가 두 푸시 모두 초록(ubuntu의 python 잡
포함)이었고, CodeRabbit은 첫 리뷰에 지적이 없었으며 main을 합친 푸시는 Review rate limited였다. claude-review는 첫
회차에 Nit 둘, 둘째 회차에 Minor 셋과 Nit 둘을 냈고, 고치지 않고 이유를 PR 코멘트 둘로 남겼다. 그 뒤 병합(`8871a15`)했다.

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했으며 원격에 없는 커밋이 없어 `1fb0fde`에서 `8871a15`(origin/main)로 당겼다. 당긴 커밋은 이
  스킬 파일을 바꾸지 않았다.
- **판정.** 실행 중인 세션 셋(`chore/open-session-case-server`, `chore/sweep-window-to-tools`,
  `feature/03-runner-and-templates`)의 제목을 넘겨 `judge`를 쳤다. 일지 41 때 돌던 "CI 완료 자동 알림"은 멈춰 있었다.
- **지운 것.** 없다. `지운다` 줄이 하나도 없었다. 남긴 것의 이유는 살아 있는 잠금 pid, 모듈을 올린 프로세스(python·node·
  esbuild 열), 다시 만들 수 없는 무시된 항목, 병합된 PR 없음이었다.
- **사람에게 넘긴 것.** 일지 41과 같은 여섯(prunable 둘, 분리 HEAD 둘, PR 머리가 다른 `skill-check-and-retro-section`,
  `spec-pipeline-and-pytest-ids.tidy-probe`)이다. 지시문대로 답을 기다리지 않았다.

## 한 일

- **90.** `operations.md` 가드레일의 `verify` 판정 문장 뒤에, 필수 검사의 판정을 바꾸는 PR은 draft 동안 빨강 경우를 실험
  커밋으로, 다시 돌린 시도를 `gh run rerun --failed`로 실제 실행해 본다는 것과 PR #119의 두 사례를 적었다. PR 템플릿의
  `.github/` 항목 끝에 같은 확인을 더했다.
- **147.** 환경 규약 상세에 한 항목. 쓰기 전에 넷을 다시 손으로 봤다(아래 잰 것).
- **159.** 환경 규약 상세에 한 항목. 설정은 경로로 넘긴다(게이트의 `--config .github/zizmor.yml`).
- **189.** 먼저 쟀다(아래). 모드 표의 마지막 칸을 "스킬·서브에이전트 정의"와 "rules·`CLAUDE.md`"로 나누고, 표 아래에
  워크트리 사본이 끼어드는 계기를 적은 항목을 더했다. 하네스 확인 항목의 "`EnterWorktree`로 옮겨 온 세션은 주 체크아웃의
  스킬을 실었다"에 그 항목을 가리키는 괄호를 붙였다. `next-session` 3단계에는 주 체크아웃 미갱신일 때 워크트리 사본의
  병합 절을 Skill 도구가 아니라 Read로 여는 까닭 한 문장을 더했다. 프로브 `enter_worktree_loading.py`와 README 행,
  카나리아 명세 `next_session_worktree_copy_read.toml`을 더했다.
- **헌법 판.** 3.0.33(patch, 운영 문구).
- **대기열.** 90·147·159·189를 닫았다.

## 잰 것

### 147(손으로 봤다)

- PowerShell `Get-Command bash -All`: `C:\Windows\system32\bash.exe`가 먼저, 다음이 WindowsApps의 것.
- Git Bash `type -a bash`: `/usr/bin/bash`가 먼저.
- Python(`uv run`) `shutil.which("bash")`: `C:\Program Files\Git\usr\bin\bash.EXE`.
- Python `subprocess.run(["bash", "-c", ...])`: `uname`이 `microsoft-standard-WSL2`, `$PWD`가 `/mnt/c/...`, `TEMP`가 없었다.
- 저장소에서 bash를 띄우는 탐침(`review_workflow.py`)은 이미 `shutil.which`로 찾는다.

### 189(프로브와 손과 코드 읽기)

- **프로브(쟀다).** `.scratch/harness/probes/enter_worktree_loading.py`, claude CLI 2.1.296. 결과는 그 README 행과 같다.
  첫 턴은 넷 모두 스킬과 정의가 주 체크아웃 사본이었다. 주 체크아웃의 스킬·정의 파일을 바꾼 갈래만 둘째 턴에 목록에
  `.claude/worktrees/inner:probe-skill`(워크트리 사본)이 더해지고 맨 이름이 주 체크아웃의 새 판이 되었으며, 정의가 워크트리
  사본으로 바뀌었다. 대조(다음 메시지만), 세션의 Edit, 바깥 편집은 그대로였다.
- **프로브를 고친 경위.** 첫 판은 결과 이벤트를 줄 머리 `{"type":"result"`로 찾았는데, 그 이벤트의 첫 키는
  `duration_api_ms`였다. 턴의 끝을 놓치고 다음 줄을 기다리며 15분 넘게 멈췄다. 제한 시간 검사도 막힌 `readline` 앞에서는
  걸리지 않았다. 읽기를 스레드와 큐로 옮기고 줄을 풀어서 `type`을 보게 고쳤다. 둘째 판은 파서가 `message`가 dict가 아닌
  이벤트에서 넘어져 뒤 두 갈래의 원본을 잃었다. 원본을 먼저 저장하게 고쳤다. 셋째 판은 `acceptEdits`로 띄워 세션의
  Edit가 "you haven't granted it yet"로 거부됐는데, 편집 턴의 성공을 보지 않아 측정으로 셌다. Edit 결과의 오류를 세어
  무효로 찍게 하고 `bypassPermissions`로 띄웠다(도구는 `--tools`로 여섯).
- **이 세션(손으로 봤다).** 데스크톱 앱 세션이고 `EnterWorktree`로 들어왔다. 실행 중인 앱 세션의 명령줄은 앱이 묶은
  `claude-code\2.1.295\...\claude.exe`였다. 들어온 뒤 워크트리 파일을 Read하고 고친 뒤에 부른 `writing-for-agents`의 기준
  폴더는 주 체크아웃이었다. 스킬 밖 파일과 워크트리의 `next-session/SKILL.md`를 Edit로 고친 뒤에도 목록에 경로를 단
  이름이 나타나지 않았다. 도중에 다른 세션이 루트를 #225(`4814568`)와 #228(`2d593dd`)로 두 번 당겼다. 두 커밋은 `.claude/` 아래에서
  `rules/tools.md`와 `settings.json`만 바꿨고(`.claude/skills/`·`.claude/agents/`는 그대로), 그 뒤에도 나타나지 않았다.
  세션 도중 스킬 목록이 두 번 다시 실렸는데 경로를 단 이름은 없었다(어느 당김 뒤였는지는 맞춰 보지 않았다). 프로브와
  어긋나지 않는다.
- **코드 읽기.** claude 2.1.296 실행 파일을 grep으로 읽었다. Read·Edit·Write가 파일을 건드리기 전에 그 파일의 조상
  폴더에서 `.claude/skills`를 찾는 함수가 있고, 처음 폴더 기준으로 `git check-ignore`가 무시한다고 하는 폴더는
  건너뛴다. 주 체크아웃에서 `git check-ignore`를 쳐 보니 이 워크트리 폴더와 그 `.claude/skills`가 무시된다고 나왔다(손).
  옮겨 간 폴더의 스킬을 다시 읽는 함수도 있고, 스킬 폴더의 파일 변경 이벤트와 세션 초기화가 그것을 부른다(로그 문구
  "re-reading the moved directory's skills"). 실행 파일을 더 읽는 명령은 자동 모드 분류기가 자기 수정 범주로 막아 거기서
  멈췄다.
- **어림.** 일지 14·18·43의 앱 세션에서 경로 단 이름이 PR 뒤나 셀프 리뷰 중에 나타나고 정의가 워크트리 사본으로 돈
  것은, 그 사이 다른 세션이 루트를 당겨서로 보인다. 그 세션들의 그때 루트 이력은 보지 않았다.

### 카나리아

`next_session_worktree_copy_read.toml` 통과 4(실험군 이 워크트리 `e6eb8df`, 대조군 주 체크아웃 `4814568`). 실험군 첫
회차는 앞 문장을 먼저 옮기고 새 문장도 옮겼다. 셀프 리뷰가 그 문장의 계기 구절을 고친 뒤에는 사전 확인으로 갈음했다.
같은 claude 판, 본문만 고침, 명세 그대로이고, `expect` 조각이 병합 문장 뒤 둘째 문장에 남았다.

## 판단

- **189의 문서 자리.** 계기는 판이 바뀌면 달라질 수 있는 Claude Code의 동작이라 표의 칸에 길게 쓰지 않고, 칸에는 "주
  체크아웃. 그 뒤 … 끼어든다(아래 항목)"만 두고 근거와 판을 표 아래 항목에 모았다.
- **next-session 3단계.** Read로 여는 지시는 그대로 둔다. 경로 단 이름은 주 체크아웃의 파일 변경 같은 세션 밖의 계기로
  생겨 받는 세션이 기댈 수 없다. 까닭 한 문장만 더했다. operations.md의 처방도 셀프 리뷰 뒤 Read 하나로 맞췄다.
- **`CLAUDE.md` 환경 함정의 "main을 합친 뒤 바뀐 스킬" 줄은 고치지 않았다.** 워크트리 세션이 main을 워크트리에 합쳐도
  주 체크아웃의 파일은 바뀌지 않으므로 Skill 도구는 그대로 주 체크아웃 사본을 싣는다. 측정과 맞는다.

## 셀프 리뷰

`/code-review`, base `e6eb8df`, 수정 파일 여섯, 미추적 셋, 커밋 0. 소스 파이썬(`src/`·`tests/`·`tools/`)이 바뀌지 않아
표준 축은 sonnet이었다. 명세는 지시문의 시작 프롬프트와 대기열 네 행이고, 리뷰어 참고(앱 판을 재지 못함, `CLAUDE.md` 줄을
두기로 한 판단)를 따로 넘겼다. 표준 축은 Major 하나·Minor 다섯·Nit 셋, 명세 축은 Minor 넷·Nit 셋이었다.

- **고쳤다, 표준 Major(일지 번호).** 그 사이 origin/main의 최신 일지가 50이 되어 48이 이름순으로 앞섰다.
  `tools/sibling_overlap.py`가 낸 대로 55로 옮기고 인용 다섯(대기열 닫힘 넷, 카나리아 명세)을 고쳤다.
- **고쳤다, 두 축 Minor(닫힌 주장이 프로브보다 넓다).** operations.md의 "바뀌면(다른 세션이 루트를 당겼다)"을 "함께
  바꾸자"와 재지 않은 셋(한쪽 폴더만, git으로 당김, 5초 뒤의 다시 읽기)으로, 대기열 189 닫힘의 "바뀔 때만"을 "잰 갈래 넷
  가운데 … 바꾼 갈래에서만"으로, next-session의 "루트를 당길 때만"을 "파일이 바뀌는 것 같은 세션 밖의 계기로"로 바꿨다.
  실행 파일에서 세션을 초기화하는 길도 다시 읽는 함수를 부르는 것을 앞서 읽었으므로 "때만"은 틀릴 수 있었다. 그것을
  operations.md에 코드 읽기로 적었다.
- **고쳤다, 두 축 Minor(같은 처방이 세 곳에서 갈렸다).** operations.md의 "경로 단 이름이 있으면 그 이름으로"를 지우고 Read
  하나로 맞췄다. 경로 단 사본이 끼어든 때의 판이라 그 뒤 편집을 싣지 않을 수 있다(일지 2026-10-12-18의 자료)는 것을 적었다.
- **고쳤다, 표준 Minor(근거의 종류).** "그 실행 파일"에 판을, 앱이 묶은 2.1.295에 손으로 봤다는 표지를, 90의 PR #119
  사례에 손으로 봤다는 표지를 붙였다. 159의 zizmor 세부는 `tech.md`·ADR 0027과 겹쳐 그쪽을 가리키게 줄였다.
- **고쳤다, 명세 Minor(모드 표 셋째 행의 출처).** 표 머리의 출처에 서브에이전트 카나리아 `bug_perf_review_budget.toml`을
  더했다. "어느 판부터"는 항목 첫 문장(처음에는 둘 다 주 체크아웃 사본, 일지 2026-10-01-03과 같다)으로 답했다.
- **고쳤다, 표준 Minor(일지의 사실 오류 넷).** #225가 바꾼 것을 `.claude/` 아래로 좁히고, 계기 문단과 222·225의 대상을
  바로잡았다.
- **고쳤다, 표준 Minor 일부(프로브).** 편집 턴이 Edit의 대상 경로와 새 표지까지 단언하게 하고(issue-tracker의 상황 표지),
  `measured`의 인자를 첫 턴 여부로 바꿨다. 지금 판정을 마지막 실행 원본에 다시 대 보니 같았고, 편집이 거부된 셋째 실행
  원본은 무효로 잡았다.
- **고쳤다, Nit 넷.** "검사 도구가 … 봤는지" 인용을 원문 글자대로, 프로브 README와 독스트링의 "모든 턴이 측정"을 측정
  턴과 편집 턴으로, PR 템플릿 문장을 이웃 항목처럼 의문형으로, 5초 창을 operations.md에 적었다.
- **남겼다, 표준 판단 항목(프로브 냄새 넷).** `clean_env`·`git`·`remove_tree`가 `claude_md_parent.py`와 같은 것,
  표지 사전의 한글 키와 `branch` 이름, `send_and_wait`이 보내며 결과를 돌려주는 것, `main`이 조립과 출력을 섞는 것이다.
  한 번 다시 도는 커밋 프로브이고 이웃 프로브와 같은 모양이다(일지 2026-10-07-14가 같은 판단을 했다).
- **남겼다, 표준 Nit(next-session 3단계가 긴 한 줄).** 이 PR은 한 문장만 더했다. 단계를 나누는 것은 이 범위 밖이다.

검증은 커밋의 pre-commit으로 갈음한다(결과는 아래 검사 절).
