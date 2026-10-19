# 2026-10-19 (11) tests 규칙의 리눅스 조항과 시간 단언 카나리아

브랜치 `chore/tests-rule-batch`. 대상 파일이 `.claude/rules/tests.md`인 열린 대기열 행 둘(332·318)을 chore 한 PR로 반영했다.

> 사용자: 대기열 332·318(대상 파일이 .claude/rules/tests.md인 열린 행 둘. 332는 미룬 카나리아 실제 회차만 남았다)을 chore 한
> PR로 반영한다. 행의 "어디로" 칸이 원천이다

시작 전에 주 체크아웃 세션으로 `tidy-checkouts`를 돌았다. 루트를 a7d93133에서 a89ec15c(origin/main)로 빨리감기했다. 판정에는
지울 후보가 없었다. 넘긴 것은 분리 HEAD 셋(`confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`, `vigorous-mahavira-ebe993`,
그 커밋이 origin/main에 없다)과 `skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이 다르다)이다.
`full-checks-via-runner`·`next-session-handoff-batch`·`wait-ci-review-limit`은 그 폴더를 작업 디렉터리로 쥔 `claude.exe` 때문에,
`ruff-try-statements`는 `tail.exe`(pid 27716) 때문에 남았다.

## 한 일

- 318. `.claude/rules/tests.md`의 pwsh 항목을 "`tests/tools/`의 시험은 CI의 리눅스에서도 돈다"는 일반 조항으로 올리고, 윈도에서는
  없어도 도는 것의 예 둘을 그 아래에 두었다. 하나는 시험이 쓰는 스크립트(git 훅)의 실행 권한이고(선례
  `tools/run_hooks.py`의 `committing_repository`가 치는 `chmod(0o755)`, 사건은 `tests/tools/test_hook_edit_during_commit.py`,
  일지 2026-10-16-52), 다른 하나는 기존 pwsh 윈도 전용 형식 항목을 문장 그대로 옮긴 것이다.
- 318의 카나리아 `.scratch/harness/probes/canary/tests_rule_linux_exec_bit.toml`을 새로 썼다. 기존
  `tests_rule_pwsh_linux.toml`은 카나리아와 그 문장이 그대로라 사전 확인으로 갈음하고 머리 주석에 적었다.
- 332. 미룬 카나리아 실제 회차(`tests_rule_timing_margin.toml`)를 돌렸고 `# 최신 결과:` 줄을 그 결과로 바꿨다.
- 대기열 318·332를 닫았다.

## 검사

- 카나리아 실제 회차 둘: `tests_rule_timing_margin.toml` 통과 4, `tests_rule_linux_exec_bit.toml` 통과 4(claude 2.1.302,
  러너가 찍은 커밋 a89ec15c, 커밋하기 전의 작업 트리). 실험군 셋은 카나리아를 옮겼고 대조군(README.md)은 "없음"을 답했다.
- `uv run python tools/run_checks.py` 초록(셀프 리뷰 반영 전의 판).

## 셀프 리뷰

범위: base a89ec15c, 수정 넷, 미추적 둘, 커밋 0. 명세는 대기열 318·332 행의 "어디로" 칸. 두 축 모두 Critical 없음.

- 표준 축(하드 1, 판단 4). 하드: `tests_rule_pwsh_linux.toml`을 사전 확인으로 갈음한 것이 `operations.md`의 갈음 조건(같은 PR
  안에서 같은 claude 판으로 통과했다)을 채우지 못한다. 마지막 실제 통과가 다른 PR의 2.1.300이고 원천 문장의 자리도 바뀌었다.
  판단: 닫은 두 행의 취소선이 기존 닫힌 행(괄호까지 긋는다)과 다르다, "예는 둘이다"가 닫힌 세기로 읽힌다(리눅스 root가 읽기
  전용 `chmod`를 뚫는 `tests/tools/test_mutate.py`의 사례), 하위 pwsh 항목이 부모의 "리눅스에서도 돈다"를 되풀이하고 "윈도에서는
  없어도 도는 것"이 흐리다, pwsh 명세의 머리 주석이 옛 자리를 서술한다.
- 명세 축(Minor 1). "윈도의 git은 권한 없이도 훅을 돌린다"가 넓다. Git for Windows는 실행 비트 대신 셔뱅을 본다.

고친 것:
- pwsh 카나리아를 실제 회차로 다시 돌려 통과 4였다(claude 2.1.302, 러너가 찍은 커밋 a89ec15c, 반영 뒤의 작업 트리). 머리 주석의 갈음 문장을 지우고 옮긴 사실만 적었다.
- 두 행의 취소선을 괄호까지 넓혔다. "예는 둘이다"를 "아래는 실제로 난 예다"로 바꾸고, 부모 문장이 무엇을 가리키는지 괄호로
  적었으며(윈도 전용 형식, 스크립트의 실행 권한), 하위 pwsh 항목의 되풀이를 지웠다.
- 윈도 git 문장을 "이 PC의 git은 실행 권한 없이 쓴 `#!/bin/sh` 훅을 돌렸지만, 리눅스의 git은 실행 권한이 없는 훅을 건너뛴다
  (githooks 문서)"로 좁혔다. 문서 원문은 이 PC의 Git for Windows 문서 `githooks.html`의 "Hooks that don't have the executable
  bit set are ignored"다.
- 문구를 고친 뒤 `tests_rule_timing_margin.toml`·`tests_rule_linux_exec_bit.toml`은 같은 PR·같은 판의 통과라 사전 확인으로
  갈음했다(사전 확인 통과 2).

남긴 것: 332 행의 앞쪽 "사전 확인만 지났다"를 이력으로 둔다(명세 축 참고, 결함 아님).

PR 직전 리뷰에 밀 주장: "이 PC의 git은 실행 권한 없이 쓴 `#!/bin/sh` 훅을 돌렸지만, 리눅스의 git은 실행 권한이 없는 훅을
건너뛴다(githooks 문서)", "아래는 실제로 난 예다".

## 회고

후보 하나, 승인 0·기각 1·넘김 0.

- 기각. 대기열 행을 닫는 파이썬을 Bash heredoc으로 `uv run python -`에 넘기자, 본문에 `git`이 든 글이 있다며 워크트리 가드가
  거부했다. 같은 스크립트를 스크래치패드 파일로 써서 경로로 넘기자 돌았다. 앱 가드가 그 자리에서 막았고, 길은 `CLAUDE.md` 환경
  함정(긴 입력은 파일로 써서 경로로 넘긴다)이 이미 적는다. 비용은 호출 하나였다.

## 다음

- 없음. 이 PR로 `.claude/rules/tests.md`가 대상인 열린 행은 0이다.
