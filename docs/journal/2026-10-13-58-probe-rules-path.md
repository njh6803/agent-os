# 2026-10-13 (58) 프로브 규칙을 프로브 파일을 여는 자리로 옮긴다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 223을 닫는다. 세션은 주 체크아웃에서 열렸고, 지시문대로
`tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=probe-rules-path)`로 들어가 `origin/main`(`4814568`)에서
`chore/probe-rules-path`를 땄다. 일지 번호는 `tools/sibling_overlap.py`가 준 52였다. PR을 열기 전에 main이 일지 54를
병합해 이름순 차례를 지키려고 57로 옮겼고, 그 대조를 다시 치는 사이 형제 워크트리가 57을 먼저 받아 58로 옮겼다.

> 사용자: "대기열 223을 반영한다(.claude/rules/에 paths: .scratch/**/probes/** 규칙을 두고 issue-tracker "프로브와 근거"의 탐침 항목을 그 자리로 옮기거나 가리킨다, 카나리아로 실리는지 본다). 그 행의 "어디로" 칸이 원천이다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `e6eb8df`에서 `4814568`(#225)로 당겼다. 당긴 커밋은 이 스킬 파일을 바꾸지 않았다.
- **지운 것.** 없다. `지운다` 판정이 하나도 없었다.
- **남긴 것.** 잠금 pid가 살아 있는 것, 모듈을 올린 `python.exe` 넷(pid 26656·9996·50252·47188) 때문에 남은 병합된 워크트리,
  작업 디렉터리를 쥔 `claude.exe`가 있는 것, 병합된 PR이 없는 것, 다시 만들 수 없는 무시된 항목이 있는 것.
- **사람에게 넘긴 것.** prunable 둘(`05-admin-hides-decision-for-end-user`, `spec-pipeline-and-pytest-ids`), 옆 이름에 남은
  `spec-pipeline-and-pytest-ids.tidy-probe`, 분리 HEAD 둘, PR 머리가 다른 `skill-check-and-retro-section`. 실행 중 세션 가운데
  제목이 브랜치가 아닌 것("CI 완료 자동 알림")이 있었다. 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **옮긴 항목은 넷이다.** issue-tracker 프로브와 근거 절의 항목 가운데 프로브 자체를 짓는 규칙인 넷(재려는 상황의 표지, 독스트링과
  README의 전제, 해석의 갈래, 사전 등록)을 새 `.claude/rules/probes.md`로 글자 그대로 옮겼다. 절에는 그 자리를 가리키는 한 줄을
  남겼다. 같은 사실을 한 곳에 두려고 가리키기만 하지 않고 옮겼다. 규칙이 issue-tracker를 가리키기만 하면, 프로브 파일을 열 때
  실리는 것은 가리키는 한 줄뿐이고 본문은 다시 Read해야 한다. 그 절을 읽고도 지나친 것이 223의 갈래였다.
- **남긴 항목은 넷이다.** 두는 자리와 README 줄, 근거 문장의 종류, 웹 요약, 소비 지점은 프로브를 짓기 전(명세·ADR을 쓸 때,
  무엇을 잴지 고를 때)에 읽혀야 하고, `implement`·`to-spec`·`grilling` 스킬이 issue-tracker의 그 절을, `tools/hook_webfetch_summary.py`가
  "프로브와 근거"를, `spec-reviewer` 에이전트가 issue-tracker 파일을 인용한다. 옮기면 그 인용이 모두 따라 바뀌어야 했다.
- **옮긴 항목을 가리키던 자리.** `CODING_STANDARDS.md`의 실패를 기대하는 테스트 줄("탐침 쪽은")과 하네스 변이 명세 셋
  (`llm_tokens_mutations.toml`, `line_separators_hook_mutations.toml`, `rewrap_comments_mutations.toml`)의 머리 주석을 새 자리로
  고쳤다. 일지와 대기열의 닫힌 행(144·179·197)은 기록이라 두었다.

## 카나리아

`.scratch/harness/probes/canary/probes_rule.toml`을 더했다. 실험군은 `paths` 안이면서 하위 폴더에 든
`.scratch/harness/probes/commit_msg_hook/time_hook.py`(223의 넷째 회차가 고친 프로브), 대조군은 같은 `.scratch/` 안의 `paths`
밖인 `.scratch/plan.md`다. 대조군을 `.scratch/` 안에 둔 것은 glob이 `.scratch/` 전체로 넓게 맞지 않는지도 보려는 것이다.
카나리아는 규칙의 첫 제목("프로브 규칙")과 "탐침의 종료 코드를 0으로 두지 않는다" 조각이다. 결과는 통과 4(claude 2.1.296)였고,
실험군 세 회차가 둘을 모두 옮겼으며 대조군은 "없음"이었다. 규칙은 커밋하기 전의 워크트리 사본이었다(러너가 찍은 갈래 커밋은
`4814568`이라 그 커밋에는 규칙이 없다).

## Write 갈래

ADR 0004의 2026-09-29 이력은 "Write(새 파일)로는 `paths` 규칙도 하위 디렉터리의 CLAUDE.md도 실리지 않는다"고 적었다. 그 이력은 근거로
공식 문서와 claude 2.1.281의 `InstructionsLoaded` 훅 로그를 드는데, 그 로그를 내는 `.scratch/harness/probes/instruction_loading/`의
README 행이 설명하는 갈래(R1~R6)에는 Write가 없다. `results.txt`의 R7·R8은 README에도 그날 일지에도 설명이 없고 `session_start`
줄만 있어, 그것이 Write 갈래였는지는 모른다. 그래서 2.1.281에서 Write로 실리지 않았는지는 확인하지 못했다(공식 문서의 어느
문장인지도 찾지 않았다).
새 프로브는 보통 Write로 만들어지니, 규칙이 그 순간에 닿는지가 223의 처방에 걸려 있어 손으로 봤다. 위 카나리아를 양성 대조로
두고(같은 질문으로 Read 갈래가 실렸다) `claude -p --setting-sources project,local --strict-mcp-config --model sonnet
--output-format stream-json --verbose --permission-mode acceptEdits --tools Write`에 질문을 stdin으로 넘겼다.

- `paths` 안에 새 파일(`.scratch/canary-write/probes/tmp.txt`)을 Write한 두 회차: 둘 다 Write 결과가 "File created
  successfully"였고 카나리아 둘을 옮겼다.
- `paths` 밖에 새 파일(`.scratch/canary-write/notes/tmp.txt`)을 Write한 한 회차: Write는 성공했고 답은 "없음"이었다. "Write면
  규칙이 다 실린다"는 해석을 이 갈래가 가른다.

그래서 claude 2.1.296에서는 Write로 새 파일을 만들 때도 `paths` 규칙이 실린다(손으로 봤다, 실험 두 회차와 대조 한 회차). 이 PR의
issue-tracker 줄은 Read 계기만 적었다. ADR 0004 이력과 `README.md`의 "Read 도구로 열 때만"을 고치는 일은 프로브에 Write 갈래를
더해 다시 잰 뒤의 후속이다(아래 "다음").

## 셀프 리뷰

`/code-review`를 base `4814568`, 커밋 전 작업(고친 파일 여섯, 미추적 셋)으로 돌렸다. 소스 파일이 없어 표준 축은 sonnet이었다. 두
축 모두 Critical·Major는 없었다.

- 고쳤다(Minor, 두 축): 카나리아를 돌린 뒤 규칙의 머리 문단을 고쳤는데 `# 최신 결과:` 줄에 갈음 표시가 없었다. 머리말·`expect`·
  카나리아 자리는 그대로라 `--preflight`(통과 1)로 갈음하고 그 줄 뒤에 덧붙였다.
- 고쳤다(Minor, 표준 축): 규칙 머리의 경위가 넷을 모두 "표지를 단언하지 않았다"로 묶었는데, 일지 16은 판정 없이 늘 0으로 끝난
  것, 30은 마지막 질의의 종료 코드를 보지 않은 것이다. 그 절을 읽었다고 적은 것도 16·30뿐이라 "두 번"은 하한이다. "첫 항목을
  어긴 것을 네 번, 적어도 두 번은 그 절을 읽은 세션"으로 고치고, 대기열 223 행과 겹치는 일지 목록을 뺐다. 리뷰 전에 이 세션이
  "표지 없이 0으로 끝냈다"를 한 번 고친 뒤였다.
- 고쳤다(참고, 명세 축): 규칙 머리가 issue-tracker에 남은 항목을 덜 셌다(웹 요약, 소비 지점). 저장소 밖(스크래치패드, 임시
  디렉터리)에서 짓는 프로브에는 규칙이 실리지 않아, issue-tracker의 가리키는 줄에 그때는 규칙 파일을 Read로 열라고 더했다.
- 고쳤다(Nit): issue-tracker 줄의 "그 파일의 머리"를 `probes.md`로, 일지의 인용 서술을 실제 인용 꼴(spec-reviewer는 파일만,
  웹 요약 훅은 "절" 없이)로.
- 보류(Minor, 표준 축): 새 프로브는 Write로 만들어지는데 ADR 0004 이력대로면 Write로는 규칙이 실리지 않는다는 지적. 위 Write 갈래에서 claude
  2.1.296은 실렸다. 리뷰어는 그 관찰을 받지 못했다. 규칙 머리의 "Read로 여는 자리"만 "여는 자리(`paths`)"로 넓혔다.
- 보류(Nit, 명세 축): 기능마다의 프로브 README가 머리에 둔 "규약은 issue-tracker" 줄. 그 절이 다시 `probes.md`를 가리키고, 그 README를
  Read하면 규칙이 실려 거짓이 아니다.

## PR 직전 리뷰

`coderabbit auth status`가 `Seat: not assigned`라 CLI 축은 돌지 못했다. 첫 커밋(`5dc2851`) 뒤 origin/main(`2d593dd`)을 합치고
(`4012990`, 충돌 없음) 대체 둘을 나란히 돌렸다.

- `/security-review`: 취약점 없음. 식별 서브태스크가 후보를 내지 않아 거르기 서브태스크는 띄우지 않았다. 카나리아 명세가 닿는
  `tools/canary.py`의 실행 길(인자 목록, `shell=True` 없음, `rule`은 `--tools Read`)을 따라갔다.
- `bug-perf-review`: 유효 Nit 하나, 보류 Minor 하나, 오탐 여섯. Nit("그 절에 있는 동안"이 옮긴 뒤에는 지금도 그 절에 있다고
  읽힌다)은 "있던 동안"으로 고치고 사전 확인(통과 1)으로 다시 갈음했다. Minor는 셀프 리뷰가 보류한 Write 계기와 같은 지적이다.
  변이 명세 셋은 `tools/mutate.py --check`가 통과했다고 그 리뷰가 적었다.
- 같은 무렵 데스크톱 앱의 백그라운드 보안 검토가 이 브랜치가 고치지 않은 `tools/hook_bash_commit_msg.py`(#225)를 짚었다. 그 훅은
  커밋 대상 저장소의 `tools/check_commit_msg.py`를 PreToolUse에서, 사람이 그 Bash 명령을 승인하기 전에 실행한다. 그 저장소의
  pre-commit 설정이 그 스크립트를 부를 때만이라 보통은 그 커밋이 어차피 돌릴 스크립트지만, 신뢰하지 않는 저장소에 커밋을 시도만
  해도 돈다(코드를 읽었다). 이 PR의 범위가 아니라 후속으로 넘긴다(아래 "다음").

## PR 봇

PR #230. 첫 푸시(`e1b94b3`)에서 검사는 모두 통과했고, CodeRabbit은 `@coderabbitai review`를 남겼는데도 "Review rate limited"였다.
보안·버그·성능 축은 위 PR 직전 리뷰가 대신한다.

- claude-review 첫 회차: Critical·Major 없음, Minor 하나와 Nit 하나.
  - 고쳤다(Minor): issue-tracker의 가리키는 줄이 "Read로 열 때 실린다"만 적어, 이 PR이 새로 쓴 문장인데 읽는 사람은 Write로 새
    프로브를 만들 때는 안 실린다고 받는다. 손으로 본 Write 갈래와 대기열 247을 그 줄에 더했다.
  - 보류(Nit): 규칙 첫 항목 끝의 마침표. 옮겨 온 목록의 항목이 모두 마침표 없이 끝나는 꼴이라 한 항목만 고치면 어긋난다. PR
    코멘트에 이유를 남겼다.

## 바꾼 것

- `.claude/rules/probes.md`(새 파일, `paths: .scratch/**/probes/**`): issue-tracker에서 옮긴 항목 넷과 머리 문단.
- `docs/agents/issue-tracker.md`: 프로브와 근거 절의 항목 넷을 가리키는 한 줄로 바꿨다.
- `CODING_STANDARDS.md`: 실패를 기대하는 테스트 줄의 "탐침 쪽은"을 새 자리로.
- `.scratch/harness/probes/{llm_tokens,line_separators_hook,rewrap_comments}_mutations.toml`: 머리 주석의 가리키는 자리.
- `.scratch/harness/probes/canary/probes_rule.toml`(새 파일): 카나리아 명세.
- `.scratch/retro-queue.md`: 223 행을 닫았다.

## 검사

- 손으로 친 다섯: `uv run pytest -q`는 2594 통과, 7 deselect(`llm` 마커)였다. ruff check·format, pyright(0 errors), lint-imports(계약
  다섯 유지), 지침 검사가 모두 통과했다.
- 첫 커밋의 pre-commit은 모든 검사가 Passed였다(pytest 514.1초, web-verify 379.5초). 인용 대조가 일지에서 경고 둘을 냈다. 하나는 ADR
  0004의 그 문장이 원문에서 줄이 접혀 있던 것이고, 다른 하나는 리뷰 지적을 풀어 쓴 문장에 따옴표를 붙인 것이라 따옴표를 뗐다.
- 그 커밋은 일지 2026-10-13-47의 "다음"이 볼 것으로 남긴 새 훅 `hook_bash_commit_msg`가 `git commit -F <파일>`에서 처음 돈 사례다.
  제목이 판정을 지나 막지 않았다. 막혀야 할 제목으로는 보지 않았다.
- 카나리아 `probes_rule.toml`: 통과 4, 그 뒤 머리 문단만 여러 번 고쳐 마지막 고침 뒤의 사전 확인(통과 1)으로
  갈음했다.

## 회고

후보 다섯, 승인 둘(하나는 넘겨 사용자가 승인했다), 기각 셋.

1. **넘김 → 사용자 승인, 대기열 247.** ADR 0004 이력과 `README.md`가 `paths` 규칙은 Read로 열 때만 실린다고 적는데, 이 세션의
   Write 갈래(claude 2.1.296)에서는 Write로 새 파일을 만들 때도 실렸다. 그것을 재려고 `tools/canary.py`에 없는 갈래를 스크래치
   스크립트와 손 명령으로 돌렸다. ADR 이력을 고치는 일이라 넘겼다. 층은 커밋한 측정(카나리아의 새 갈래)과 그 뒤의 ADR 이력이다.

   > 사용자: "대기열에 올린다 (Recommended)"

2. **승인, 대기열 246.** `tools/hook_bash_commit_msg.py`가 커밋 대상 저장소의 판정 스크립트를 사람의 승인 전에 실행한다. 사건은
   이 세션에서 백그라운드 보안 검토가 짚은 것이다. 층은 그 훅의 코드와 시험(고침이라 사건 하나로 반영한다)이고, PR 하나로 되돌릴
   수 있다. 이 PR의 범위(문서와 규칙)가 아니라 대기열에 둔다.
3. **기각.** 규칙 머리의 경위 문장이 처음에 네 회차를 모두 "표지 없이 0으로 끝냈다", "그 절을 읽은 세션"으로 넓게 적었다. 한
   번은 리뷰 전에 이 세션이, 나머지는 셀프 리뷰 표준 축이 잡았다. code-review의 주장 검증 목록(닫힌 주장)이 이미 잡는다.
4. **기각.** 항목을 옮긴 스크래치 스크립트가 `Path.write_text`로 issue-tracker를 CRLF로 바꿨다. git이 스테이지할 때 경고를 내며 LF로
   되돌리고, 바로 알아채 한 명령으로 고쳤다. 이미 있는 장치가 잡는다.
5. **기각.** origin/main을 합칠 때 커밋하지 않은 일지 수정을 `git stash push -m`으로 비켰다. 표지를 달고 SHA로 되살려 다른 세션의
   항목과 섞이지 않았다. 앞서 커밋했으면 필요 없던 단계지만 비용은 명령 넷이고, 공유 stash의 안전한 쓰임은 세션 환경 안내에 있다.

## 다음

- **223의 효과는 다음에 새 프로브를 쓰는 세션에서 처음 본다.** 그 세션의 셀프 리뷰가 다시 표지 없는 첫 판을 잡으면 223의
  5회차다. 지침으로 옮긴 뒤에도 어겨진 것이니 `CLAUDE.md` 교정 루프대로 계기 훅(예: `.scratch/**/probes/**`에 Write할 때
  표지 항목을 짚는 PostToolUse)을 후보로 올린다.
- **이 PR 뒤의 다음 작업은 일지 2026-10-13-47 "다음"의 훅 묶음(130·145·162·216)이다.** 넷 다 아직 열려 있다. 새로 든
  246(`hook_bash_commit_msg`의 보안 고침)은 대상 파일이 달라 그 묶음의 조건에 들지 않지만, 같은 `tools/` 훅 둘레라 그 세션이
  함께 볼지 정한다. 247은 ADR 이력 초안과 사용자 승인이 들어 따로 간다.
