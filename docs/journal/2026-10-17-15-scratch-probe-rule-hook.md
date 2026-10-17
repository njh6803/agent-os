# 2026-10-17 (15) 스크래치 측정 스크립트에 probes.md를 알리는 훅

브랜치 `chore/scratch-probe-rule-hook`. 대기열 336·303·307·323·331을 chore 한 PR로 반영했다. 나란히 연 둘 가운데 둘째
세션이고, 첫 세션은 334(`chore/full-checks-via-runner`)다.

> 사용자: 대기열 336·303·307·323·331(세션 스크래치패드의 측정 스크립트에 .claude/rules/probes.md를 알리는 계기 훅과, 대상
> 파일이 probes.md인 열린 행들)을 chore 한 PR로 반영한다. 각 행의 "어디로" 칸이 원천이고, 336이 307·323의 grilling 문장을
> 대신하는지 정한다

## 판정: 336이 무엇을 대신하나

- 323은 대신한다. 사건은 이 세션(일지 2026-10-16-68)이 스크래치패드에 직접 지은 측정 스크립트였고, Write·Edit로 쓴 파일이면
  새 훅이 쓰는 순간에 알린다. grilling 사실 조사 문단에 323의 문장을 더하지 않았다.
- 307도 대신한다(셀프 리뷰에서 뒤집었다). 앞 세션은 사건(일지 2026-10-16-36)이 스크립트 파일이 아니라 정리 단계의
  `taskkill /F <pid>`라고 보고 grilling 문단에 문장을 남겼다. 그런데 그 일지의 307 승인 문단은 "끄는 호출이 측정 스크립트 안의
  `subprocess`"라고 적고, 측정은 모두 세션 스크래치패드의 스크립트였다고 적는다. 그 스크립트를 Write·Edit로 썼다면 새 훅이
  알린다. 그래서 336 행대로 307의 pid 규칙은 `probes.md` 본문에만 넣고 grilling 문장과 그 카나리아를 뺐다.
- 303은 336 행의 지시대로 그대로 반영했다. 사건 셋 가운데 둘이 `spec-reviewer`의 heredoc이라 훅이 보지 못하고, 그
  에이전트에는 Write가 없다.

## 한 일

- `tools/hook_scratch_probe_rule.py`(새 PostToolUse Write|Edit 계기 훅). 경로 토막에서 `claude` 다음 두 토막 뒤가
  `scratchpad`이고 확장자가 실행 스크립트면, 세션·에이전트마다 한 번 `probes.md`를 Read로 열라고 알린다. 표지는
  `launch_hook.py`의 모양(임시 폴더, `O_EXCL`)이다. 336 행이 먼저 보라고 한 "이미 붙은 훅에 판정 더하기"는 붙은 넷이 모두 다른
  일(일지, ruff, 파일 내용, 도는 커밋)이라 섞지 않고, 새 매처 묶음 없이 첫 `Write|Edit` 묶음에 더했다. 값은 Write·Edit마다
  약 0.2초(어림, 재지 않았다)다.
- `probes.md`: 프로세스를 끄는 탐침 항목(307), 바깥 스냅샷과 맞대는 프로브 항목(331), 머리 문단에 훅 한 문장.
- `spec-reviewer.md` 프로브 문단(303), `issue-tracker.md` 프로브 절의 목록과 스크래치패드 문장,
  `tools.md`의 Write·Edit 훅 목록.
- 테스트 `tests/tools/test_hook_scratch_probe_rule.py`, 페이로드 표 셋(발동 하나, 실제 꼴의 침묵 둘), 변이 표
  `.scratch/harness/probes/scratch_probe_rule_hook_mutations.toml`, 카나리아 명세 셋(`probes_rule_kill_and_snapshot`,
  `spec_reviewer_evidence_kinds`, `tools_rule_scratch_probe_hook`. 넷째였던 `grilling_process_kill_brief`는 셀프 리뷰에서 뺐다).

## 검사

- 손으로 친 다섯 검사와 `tools/run_hooks.py`(127건 어긋남 0), 지침·타입 우회 검사.
- 훅의 `main`을 같은 세션 ID로 두 번 돌려 첫 번만 알리는 것을 손으로 봤다.
- 변이 표를 지으며 코드를 다시 읽다가, 표지 폴더 자리에 파일이 있을 때 `makedirs`의 `FileExistsError`를 "이미 알렸다"로 읽어
  알림을 삼키는 결함을 찾았다. 둘을 갈라 잡고 시험으로 고정했다.
- 카나리아 넷은 사전 확인(`--preflight`)만 통과했다. 실제 회차와 훅 문장이 모델에게 닿는지(`claude -p`)는 계정 주간 한도로
  돌리지 못했다. `tools_rule_scratch_probe_hook`의 첫 카나리아(훅 이름)는 git 상태의 바뀐 경로에도 들어 사전 확인이 막아,
  규칙 문장의 괄호 설명으로 바꿨다.
- 전체 pytest(3458)에서 둘이 빨갰다(`test_check_md_tables`, `test_queue_open_rows`). 대기열 336 행의 닫힘 표기에 쓴
  `Write|Edit`의 `|`가 표의 칸을 갈랐다. `Write·Edit`로 고쳐 둘을 다시 돌려 초록이다. 행을 닫은 스크래치 스크립트가
  `write_text`로 줄 끝을 CRLF로 바꾼 것도 `sed`로 LF로 되돌렸다.
- 변이 표 열 모두 기대대로(첫 판은 TOML 리터럴 문자열의 `\\0` 이 원문과 맞지 않아 2로 끝났다).

## 인계

셀프 리뷰 직전에 인계 계기가 왔다(세션 컨텍스트 약 25.6만 토큰). 이 세션의 제목은 `chore/scratch-probe-rule-hook`이었다.
커밋하지 않은 변경이 워크트리에 있고, 새 세션이 셀프 리뷰(`/code-review origin/main`, 명세는 대기열 다섯 행과 이 일지)부터
한다. origin/main은 이 브랜치의 기점(528bd257) 뒤로 움직였다(`sibling_overlap` 기준 9220d4a). 형제 PR #290과 334·337
워크트리가 `.scratch/retro-queue.md`를 함께 고쳐 합칠 때 글자 충돌 후보다.

인계 지시문:

```text
다음 작업: 기능 harness. 대기열 336·303·307·323·331(스크래치 측정 스크립트와 probes.md)을 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 336·303·307·323·331(세션 스크래치패드의 측정 스크립트에 .claude/rules/probes.md를 알리는 계기 훅과, 대상 파일이 probes.md인 열린 행들)을 chore 한 PR로 반영한다. 각 행의 "어디로" 칸이 원천이고, 336이 307·323의 grilling 문장을 대신하는지 정한다
브랜치: chore/scratch-probe-rule-hook
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-17-15-scratch-probe-rule-hook.md(판정과 한 일, 검사, 인계)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main, 명세는 대기열 336·303·307·323·331 행과 일지)부터 한다. 손으로 친 다섯 검사, run_hooks, 변이 열은 초록이고 카나리아 넷은 사전 확인만 했다(계정 주간 한도). 리뷰 반영 뒤 origin/main 합치기(retro-queue.md 충돌 후보), 커밋, PR, 병합이 남았다. 일지는 docs/journal/2026-10-17-15-scratch-probe-rule-hook.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-17T14:23:34Z

## 이어받은 세션

인계로 연 세션이 이어 썼다. 첫 턴 훅대로 제목을 바꾸고 주 체크아웃에서 `tidy-checkouts`를 돌았다. 루트를 9220d4a6에서
88fed982로 당겼고, 병합된 로컬 브랜치 둘(`worktree-full-checks-via-runner`, `worktree-next-session-handoff-batch`)을 지웠다.
`skill-check-and-retro-section` 워크트리는 병합된 PR의 머리와 브랜치 끝이 달라 사람에게 넘겼다.

`EnterWorktree(path)`는 `locked: claude session scratch-probe-rule-hook (pid 21944)`로 거부됐다. pid 21944는 넘긴 세션(제목
`chore/scratch-probe-rule-hook (인계함)`)의 `claude.exe`였다. 그 세션이 턴을 끝내고 쉬는 상태가 된 뒤에도 10분 동안 잠금이
풀리지 않았다(잠금 파일을 10초마다 봤다). 주 체크아웃에서 `cd`로 옮기려던 호출은 `hook_bash_cd_outside`가 막았다. 선례(일지
2026-10-16-70, 2026-10-17-04)대로 `git worktree unlock`으로 잠금만 풀고 들어왔다.

## 셀프 리뷰

`/code-review` 기점 9220d4a6, 커밋 0, 수정 9·미추적 9. 표준 축(sonnet·high)과 명세 축.

고친 것:
- 명세 Major: 307 판정의 근거가 원천 일지와 반대였다(위 판정 절). grilling 문장, 카나리아
  `grilling_process_kill_brief.toml`, `probes.md` 307 항목 끝의 grilling 포인터를 빼고, 훅 독스트링의 못 보는 것과 307 행의
  닫힘 표기를 고쳤다.
- 두 축 Major: 카나리아가 사전 확인만 지났는데 행을 닫았다. 이 세션에서 `probes_rule_kill_and_snapshot.toml`을 실제로
  돌렸으나 네 회차 모두 "You've hit your weekly limit · resets Oct 19, 6am (Asia/Seoul)"로 답이 없었다(2026-10-18). 선례(대기열
  122·124)대로 다섯 행의 닫힘 표기에 병합 전에 돌지 못했다고 적었다. 병합할지는 사용자에게 묻는다.
- 명세 Minor: 323의 "결과 한 줄(JSON)"이 어디에도 없었다. 훅 알림 문장에 넣었다.
- 명세 Minor: 독스트링의 "어느 것도 고친 파일의 자리로 알릴 것을 고르지 않는다"에 반례(`hook_journal_retro`의 일지 경로,
  `hook_edit_during_commit`의 체크아웃 판정)와 PreToolUse `hook_midturn_korean`이 있었다. PostToolUse 등록 넷으로 좁히고 둘을
  적었다.
- 표준 Minor·명세 갈래: 한 번 알린 뒤의 측정 스크립트(측정이 아닌 도우미를 먼저 쓴 세션, 압축·이어 하기 뒤)를 못 보는 것에
  적고 `main`으로 시험을 고정했다.
- 표준 Minor: `main`의 표지 길과 `agent_id`를 시험으로 고정했다(stdin과 `tempfile.gettempdir`를 바꿔 끼운다).
- 표준 Minor: `tempfile.gettempdir()`가 `try` 밖이라 임시 폴더가 없으면 종료 1이었다. `OSError`면 호출마다 알리게 하고 시험을
  더했다.
- 표준 Minor: 리눅스 CLI 꼴 경로가 지나간다는 못 보는 것을 시험으로 고정하고, Bash heredoc 시험의 페이로드를 실제 꼴(`command`
  만)로 바꿨다.
- 표준 Nit: `LEAD` 주석의 없는 확인을 가리키던 문장, 323 행 닫힘 표기의 heredoc.

남긴 것:
- 표준 Minor: 변이 표가 `expect_output`을 쓰지 않는다. 변이마다 깨는 판정이 달라 시험 하나만 빨개지고(앞 세션이 변이 열을
  돌려 봤다), 같은 표를 쓰는 기존 훅 표 대부분도 그렇다. 이 PR에서 바꾸지 않는다.
- 표준 Nit: 알림의 `.claude/rules/probes.md`가 상대 경로다. 모델이 Read에 넘길 때 세션의 작업 폴더로 푸는데, 워크트리
  세션에서 그 자리가 그 브랜치의 사본이라 `CLAUDE_PROJECT_DIR`(주 체크아웃)보다 맞다. 그대로 둔다.
- 명세 Nit: `C:\project\claude\a\b\scratchpad\x.py` 같은 스크래치패드가 아닌 경로도 알린다. 세션마다 한 번이라 값이 작다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):
- 훅 독스트링 "그 매처의 PostToolUse 등록은 넷이다", "고친 파일의 자리를 보는 것(앞의 것은 일지 경로, 뒤의 것은 체크아웃
  안인지)도 그 일의 대상을 고를 뿐 스크래치패드를 보지 않는다", "매처가 없는 PreToolUse `hook_midturn_korean`도 Write·Edit에
  붙지만"
- 훅 독스트링 "대기열 307의 사건은 이 꼴이 아니라 측정 스크립트 안의 `subprocess`였고(일지 2026-10-16-36의 307 승인 문단)"
- `probes.md` 307 항목 끝 "그 끄기는 세션 스크래치패드의 측정 스크립트 안의 `subprocess`였다"
