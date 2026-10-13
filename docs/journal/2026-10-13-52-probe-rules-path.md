# 2026-10-13 (52) 프로브 규칙을 프로브 파일을 여는 자리로 옮긴다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 223을 닫는다. 세션은 주 체크아웃에서 열렸고, 지시문대로
`tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=probe-rules-path)`로 들어가 `origin/main`(`4814568`)에서
`chore/probe-rules-path`를 땄다. 일지 번호는 `tools/sibling_overlap.py`가 준 52다.

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
- 보류(Minor, 표준 축): "새 프로브는 Write로 만들어지는데 Write로는 규칙이 실리지 않는다(ADR 0004)". 위 Write 갈래에서 claude
  2.1.296은 실렸다. 리뷰어는 그 관찰을 받지 못했다. 규칙 머리의 "Read로 여는 자리"만 "여는 자리(`paths`)"로 넓혔다.
- 보류(Nit, 명세 축): 기능마다의 프로브 README가 머리에 둔 "규약은 issue-tracker" 줄. 그 절이 다시 `probes.md`를 가리키고, 그 README를
  Read하면 규칙이 실려 거짓이 아니다.
