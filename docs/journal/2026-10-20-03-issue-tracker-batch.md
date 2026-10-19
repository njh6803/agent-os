# 2026-10-20 (03) 트래커 규약의 나란한 마지막 티켓, 화면 데이터, 도구 판

브랜치 `chore/issue-tracker-batch`. 대상 파일이 `docs/agents/issue-tracker.md`인 열린 대기열 행 셋(104·172·371)을 chore 한
PR로 반영했다.

> 사용자: 대기열 104·172·371(대상 파일이 docs/agents/issue-tracker.md인 열린 행 셋)을 chore 한 PR로 반영한다. 행의 "어디로"
> 칸이 정한 자리에 고치고, 반영한 행을 닫는다

시작 전에 주 체크아웃 세션으로 `tidy-checkouts`를 돌았다. 루트를 5e7fa88d에서 7556070c(origin/main)로 빨리감기했다. 병합된
워크트리와 브랜치 열셋(`09-human-verification-close`, `full-checks-via-runner`, `hook-choice-facts`, `mutate-ctrl-c-under-load`,
`next-session-handoff-batch`, `path-pattern-gitignore`, `pre-commit-batch`, `ruff-try-statements`, `sibling-overlap-batch`,
`tests-rule-batch`, `tidy-running-branch`, `token-report-git-timeout`, `wait-ci-review-limit`)을 지웠다. 그중 열하나의 `web/node_modules`는 다른 체크아웃의 esbuild·node 프로세스가 하드링크로 쥐어 휴지통
(`.claude/worktrees/.tidy-trash/`)에 남았고 `empty-trash`도 같은 이유로 막혔다. 넘긴 것은 분리 HEAD 둘(`confident-wright-2d3ebf`,
`elegant-dijkstra-aaddb9`, 그 커밋이 origin/main에 없다)과 `skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이 다르다)이다.
`token-report-blind-spot-tests`는 그 폴더를 작업 디렉터리로 쥔 `claude.exe` 둘과 `pwsh.exe` 때문에 남았다.

## 한 일

- 104. 전체 계획 절의 "`done`은 마지막 티켓이 병합될 때 바꾼다" 뒤에 판정 시점을 넣었다. 행의 후보 문장은 상대가 하나인
  경우라, 셋 이상도 덮게 "나머지 티켓이 모두 `done`이면"으로 넓혔다. 행이 든 "main이 최신 기준"은 `operations.md`의 보호
  브랜치(필수 검사 `verify`, 최신 main 기준(strict))로 가리켰다. 관리자 우회가 허용된 보호라 병합 길이 `--admin`을 쓰는지
  보았다. `next-session`의 "워크트리에서 병합할 때"는 `gh pr merge <번호> --squash --match-head-commit <HEAD>`이고 `--admin`이
  없다(그 스킬을 읽었다). 행의 "각 티켓의 수용 기준에 적는다"는 to-tickets가 이 문서를 트래커 규약으로 받으므로 그 스킬이
  할 일로 적었다.
- 172. "어디로"의 두 자리 가운데 앞의 것(화면 디자인 절의 프롬프트 줄)에 넣었다. 이 묶음이 이 파일의 행이고, 뒤의 자리
  (`kickoff/prompting.md`)는 새 프로젝트가 복사하는 런북이라 그쪽은 그 런북의 묶음이 볼 일이다. 예는 admin-style 와이어프레임
  글의 "틀"(운영자의 이름이나 사진은 두지 않는다)과 "그릴 화면"(실행 목록의 열을 하나씩 적었다)이다.
- 371. 프로브와 근거 절의 둘째 항목에 넣었다. 판을 적으라고만 하면 어느 판을 적을지가 남아, 이 세션에서 손으로 보았다.
  `CLAUDE_CODE_EXECPATH`는 `C:\Users\User\AppData\Roaming\Claude\claude-code\2.1.299\...\claude.exe`였고, 셸의
  `claude --version`은 `2.1.302 (Claude Code)`였다(`which claude`는 `~/.local/bin/claude`). 그래서 데스크톱 앱 세션의 판은
  앞의 것으로 본다고 함께 적었다. 터미널의 CLI 세션에 그 변수가 있는지는 보지 않았다.
- 대기열 104·172·371을 닫았다.

## 이 PR에 넣지 않은 것

- `.claude/skills/grilling/SKILL.md`가 조사 서브에이전트의 보고 종류를 "손으로 봤다(그 명령)"로 줄여 적는다. 규약의 원천은
  이 문서라고 그 줄이 가리키고 어긋나지는 않지만, 도구의 동작을 본 보고에 판이 빠질 수 있다. 행의 "어디로" 밖이라 회고가 판정한다.
- 열린 PR #296(`chore/measure-word-hook`)이 프로브와 근거 절의 같은 둘째 항목 끝에 문장을 덧붙인다. 한 줄이 한 항목이라
  나중에 병합하는 쪽에서 글자 충돌이 난다. 두 변경은 다른 문장이라 둘 다 살리면 된다.
- 셀프 리뷰 표준 축의 Major 1(아래 "셀프 리뷰"). `.claude/skills/to-tickets/SKILL.md` 5단계에 "마지막 티켓이 둘 이상 나란히
  열리면 `plan.md`를 닫는 판정을 그 티켓들의 수용 기준에 적는다(`docs/agents/issue-tracker.md` 전체 계획 절)" 한 줄을 넣을지는
  행의 "어디로" 밖이라 회고가 판정한다.
- 첫 커밋 시도의 pre-commit에서 `tests/tools/test_hook_ruff_line_width.py`의 한글 폭 시험 하나가 실패했다(`context_for`가 `None`).
  그 파일만 `uv run pytest -q`로 다시 돌리면 17개가 통과했다(55.85초). 훅이 ruff를 `RUFF_TIMEOUT = 10`초로 띄우므로, 러너가
  web verify와 pytest를 함께 띄운 부하에서 그 시간을 넘긴 것으로 본다(어림, 재지 않았다). 대기열 306과 같은 갈래의 부하 흔들림이라
  회고가 판정한다.

## 검사

- `uv run ruff check .`와 `uv run ruff format --check .` 통과(셀프 리뷰 전의 판).
- `uv run python tools/run_checks.py`는 check-instructions, zizmor, lint-imports, check-type-escapes, pyright까지 통과한 뒤
  인계로 멈췄다(pytest·web·run-hooks는 결과 없음).

## 인계

`/code-review`를 부른 직후 세션 컨텍스트가 문턱(20만)을 넘어 인계 계기(`셀프 리뷰 직전`)가 왔다. 인계하지 않는 때 다섯에 들지
않았다(요청 범위는 PR과 병합까지, 지시문의 이어받을 상태가 `인계:`로 시작하지 않는다, `인계 못함` 줄이 없다, `get_session`의
`self`에 `parentSessionId`가 없다). 셀프 리뷰는 밟지 않았다. 이 세션의 제목은 `chore/issue-tracker-batch`이고
`chore/issue-tracker-batch (인계함)`으로 바꾼다. 일지 처음 판에 지운 워크트리를 "열둘"로 적었다가 판정 출력을 다시 세어 열셋으로
고쳤다.

지시문:

```
다음 작업: 기능 retro-queue. 대기열 104·172·371(대상 파일이 docs/agents/issue-tracker.md인 열린 행 셋)을 하네스 chore 한 PR로 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 104·172·371(대상 파일이 docs/agents/issue-tracker.md인 열린 행 셋)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 정한 자리에 고치고, 반영한 행을 닫는다
브랜치: chore/issue-tracker-batch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-20-03-issue-tracker-batch.md 의 "한 일", "이 PR에 넣지 않은 것", "인계" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 명세는 대기열 104·172·371 행의 "어디로" 칸이다. 세 자리 반영과 세 행 닫기는 끝났다. 러너(tools/run_checks.py)는 pyright까지 통과한 뒤 인계로 멈췄으니 반영 뒤 다시 돌거나 pre-commit으로 갈음한다. ruff 둘은 통과했다. 일지는 커밋하지 않았고 이어 쓴다. docs/journal/2026-10-20-03-issue-tracker-batch.md
확인할 선행 조건: 실행 중 세션의 시작 프롬프트 검색이 limit 50과 같은 수를 돌려줘 견주지 못했다(보이는 범위에서 104·172·371이나 issue-tracker.md 행을 맡은 세션은 없었다)
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-19T13:57:52Z

## 이어 받은 세션

지시문으로 연 새 세션이 제목을 `chore/issue-tracker-batch`로 바꾸고 `git worktree list`에서 이 브랜치의 워크트리
(`.claude/worktrees/issue-tracker-batch`, HEAD 7556070c)를 찾아 EnterWorktree(path)로 들어갔다. 앞 세션이 병합하지 않고
인계했으므로 `tidy-checkouts`는 돌지 않았다. 커밋하지 않은 변경 둘(`issue-tracker.md`, `retro-queue.md`)과 이 일지가 그대로 있었다.

## 셀프 리뷰

`/code-review`. base 7556070c, 바뀐 추적 파일 2, 커밋 0, 미추적 1(이 일지). 명세는 대기열 104·172·371 행의 "어디로" 칸이고,
앞 세션의 판단(104를 셋 이상으로 넓힌 것, 172의 앞 자리, 371의 판 보는 곳)은 리뷰어 참고로 갈라 넘겼다. 전체 계획 절의 새 문장이
병합 직전에 따르는 절차라 두 브리프에 갈래 밟기 문단을 넣었다.

두 축을 나란히 띄웠는데 표준 축(sonnet·high)은 44분 걸려 끝났고, 명세 축 서브에이전트는 끝나기 전에 사용자가 멈췄다. 이어서
세션이 끊겼다가 다시 열렸고 사용자가 "다시 시도"라고 했다. diff가 문장 셋이라 명세 축은 서브에이전트를 다시 띄우지 않고 본 세션이
보았다(스킬 4단계는 서브에이전트로 띄운다).

표준 축: Critical 0, Major 1, Minor 4, Nit 1.

1. (Major) 전체 계획 절의 "to-tickets는 이 판정을 그 티켓들의 수용 기준에 적는다"를 받치는 길이 없다. `to-tickets`의 SKILL.md에
   이 절을 읽으라는 줄이 없고, 병합 길(`next-session`의 "워크트리에서 병합할 때", `git-pr-merge`)에도 `Status` 확인 단계가 없다.
   `CLAUDE.md` 작업 규약 4 위반이라 했다. **보류.** 받치는 길은 간접이지만 있다. `to-tickets`의 SKILL.md 13행이 트래커 규약을
   받았어야 한다고 적고, 매 세션 실리는 `CLAUDE.md`의 Issue tracker 절이 그 규약을 `docs/agents/issue-tracker.md`로 가리킨다.
   작업 규약 4는 바뀐 결정을 참조하는 글을 맞추라는 것인데, 지금 `to-tickets`에는 이 판정을 참조하는 글이 없다. 행의 "어디로"
   (사용자 승인 2026-10-04)도 `issue-tracker.md` 한 자리다. 스킬에 한 줄을 넣으면 새 세션에서 불러 봐야 하는 하네스 변경이 되므로
   회고 후보로 넘겼다("이 PR에 넣지 않은 것"). 병합 길에 단계가 없는 것은 104가 고르는 길이 아니다. 행은 판정을 각 티켓의 수용
   기준에 두라고 하고, conversation 03·04도 수용 기준으로 판정했다.
2. (Minor) 티켓이 자기 `Status`를 언제 `done`으로 바꾸는지 어디에도 없고, `wontfix`인 형제가 있으면 "모두 `done`"이 영영 거짓이다.
   **고쳤다.** 03은 자기 PR #133에서 자기 `Status`를 `done`으로 바꿨다(`git show 7bba2b6a`로 손으로 봤다). 그것을 판정이 기대는
   것으로 적고 `wontfix`도 닫힌 것으로 보게 했다.
3. (Minor) 판정에서 `plan.md`를 고치면 병합 직전에 새 커밋이 생겨 CI와 claude-review가 다시 돈다. **남겼다.** 필수 검사 `verify`와
   `--match-head-commit <HEAD>`가 새 HEAD를 기다리게 하므로 틀린 동작이 나지 않는다. 값이 드는 것뿐이다.
4. (Minor) strict라서 뒤처진 브랜치는 병합되지 않는다는 첫 판의 문장에는 `operations.md`의 관리자 우회(`gh pr merge --admin`)라는
   반례가 있다. **고쳤다.** 관리자 우회를 쓰지 않으면 그렇다고 좁혔다. 병합 길 둘에 `--admin`이 없는 것은 표준 축이 grep으로 보았다.
5. (Minor) `CLAUDE_CODE_EXECPATH`가 같은 세션의 PowerShell 도구에는 없고, 문장에 친 명령이 없으며 "앞의 것/뒤의 것"이 모호하다.
   **고쳤다.** 이 세션에서도 Bash 도구의 `echo "$CLAUDE_CODE_EXECPATH"`는
   `C:\Users\User\AppData\Roaming\Claude\claude-code\2.1.299\f0584be0fbaf\claude.exe`, PowerShell 도구의
   `"[$env:CLAUDE_CODE_EXECPATH]"`는 `[]`, Bash의 `claude --version`은 `2.1.302 (Claude Code)`였다(손으로 봤다). 문장에 도구와
   명령을 적었다.
6. (Nit) 지금 `CLAUDE.md`의 Glob·Grep 줄에는 판이 있어 "판 없이 서서"를 아직 없다고 읽을 수 있다. **고쳤다.** 일지 2026-10-19-21의
   claude-review 회차 절(반영 커밋 a160ec98)이 그 PR에서 판을 더했다고 적는다.

표준 축이 문제없다고 확인한 것: conversation 03·04 초안의 인용과 사례(일지 2026-10-04-02), `openapi.json`의 `RunSummary` 필드에
"요청"이 없음(일지 2026-10-12-01), `screens-prompt.md`의 "틀:"·"그릴 화면:" 줄머리, 대기열 세 행의 닫힘 표지 모양.

명세 축(본 세션):

- 누락: 없다. 세 행 모두 "어디로"가 정한 자리에 들었고(104는 그 문장 바로 뒤, 172는 앞 자리, 371은 둘째 항목) 세 행을 닫았다.
  104의 "각 티켓의 수용 기준에 적는다"는 `to-tickets`가 할 일로 적었다(위 1의 보류).
- 범위 넘침: 371에서 데스크톱 앱 세션의 판을 어디서 보는지는 행 글에 없다. "판을 적는다"를 따르려면 어느 판인지가 필요해 두었다.
  104는 "한 줄"이라 했는데 규칙·근거·할 일·사례의 네 문장이다. 같은 항목 안이라 둔다.
- 잘못된 구현: 표준 축 2·4와 같다.

반영으로 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장):

- "각 티켓은 자기 PR에서 자기 `Status`를 `done`으로 바꾸고, 병합 직전에 `git fetch` 뒤 `origin/main`에서 나머지 티켓의 `Status`를
  보아 모두 `done`이나 `wontfix`이면 그 PR에서 `plan.md`의 행을 `done`으로 바꾼다"
- "main은 최신 기준(strict)이라 관리자 우회(`gh pr merge --admin`)를 쓰지 않으면 뒤처진 브랜치가 병합되지 않으므로"
- "`CLAUDE.md` 환경 함정의 Glob·Grep 줄이 처음에 판 없이 서서 PR 봇이 짚었고, 그 PR에서 판을 더했다"
- "데스크톱 앱 세션의 Claude Code 판은 Bash 도구에서 `echo "$CLAUDE_CODE_EXECPATH"`가 내는 실행 파일 경로의 판 폴더
  (`claude-code\<판>\`)로 본다. 같은 세션의 PowerShell 도구에서는 `$env:CLAUDE_CODE_EXECPATH`가 비어 있었고"

다시 돌린 명령: 커밋의 pre-commit으로 갈음한다. 결과는 아래 검사 절에 커밋 뒤 적는다.
