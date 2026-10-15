# 2026-10-16 (16) rules 두 파일에 링크 입력, 스레드 잡 시간 제한, 리눅스 pwsh 시험 문장

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 278·281·282를 한 PR로 닫는다. 대상은
`.claude/rules/tools.md`와 `.claude/rules/tests.md`이고, 각 행의 "어디로" 칸이 원천이다.

> 사용자: "대기열 278·281·282를 한 PR로 반영한다(`.claude/rules/tools.md`·`.claude/rules/tests.md`). 각 행의 "어디로" 칸이 원천이다" (지시문의 시작 프롬프트. 범위는 PR과 병합까지)

## 시작

- **tidy-checkouts.** 루트 main을 `9116978f`에서 `b4335124`로 당겼다. 당긴 커밋은 그 스킬 파일을 바꾸지 않았다. 브랜치
  `worktree-next-session-deferred-merge-running-scope`를 지웠다. `skill-check-and-retro-section`은 병합된 PR의 머리와 브랜치
  끝이 달라 사람에게 넘겼다. 나머지 워크트리는 병합된 PR이 없거나, 그 브랜치가 제목인 세션이 돌거나, 잠금 pid가 살아 있거나,
  `claude.exe`가 작업 디렉터리로 쥐거나, 다시 만들 수 없는 `.claude/plans/`가 있어 남겼다. 휴지통의 `.venv` 넷은 python.exe 셋이
  모듈을 올려 `empty-trash`가 1로 끝났다.
- 그 뒤 `EnterWorktree`(이름 `rules-tools-tests-batch`)로 들어가 브랜치 이름을 `chore/rules-tools-tests-batch`로 바꿨다.

## 어떻게 했나

1. **278.** `tools.md`의 지우거나 덮어쓰는 도구 항목에서 판정을 깨려는 입력의 예에 "지우는 자리 안의 링크(심볼릭 링크,
   junction)"를 더했다. 사건 문장(일지 2026-10-15-19)과 선례 둘을 붙였다. 행이 든 선례 가운데 `tools/tidy_checkouts.py`에는
   `_cut_links`가 없어(그 이름은 `tools/canary.py`에만 있다), 그 파일에서 링크를 따라가지 않고 링크 자체만 지우는 `delete_path`를
   선례로 적었다.
2. **282.** `tools.md`의 시간 제한 항목 끝에 스레드 잡 문장을 더했다. 시간을 넘긴 잡은 지우지 않고 세고, 출력 뒤
   `[Environment]::Exit`로 끝낸다. 선례는 `tools/open_session.ps1`의 `Invoke-PatternTimed`이고 시간은
   `.scratch/harness/probes/hung_thread_job.ps1`이 잰다. 행이 "프로브 넷의 `Timed`"라 적은 것을 grep으로 다시 세니, 지우는 모양이
   남은 것은 `composer_effort_labels.ps1`·`composer_menu_tree.ps1`·`composer_patterns.ps1` 셋이었다. 넷째인 `hung_thread_job.ps1`은
   그 모양을 일부러 재는 갈래다. 셋은 앱 화면을 재는 진단 프로브라 고친 뒤 확인하려면 앱을 띄운 실제 실행이 든다. 그래서 이 PR에서는
   고치지 않았다. 첫 판은 rules 문장에 "다시 쓸 때 고친다"로만 적었고, 셀프 리뷰 뒤 각 프로브 머리 주석으로 옮겼다(아래). `open_session.ps1`의 `Invoke-Row`에도 `finally`의 `Remove-Job -Force`가 있지만,
   그 함수는 프로세스 잡(`Start-Job`)이고 시간을 넘기면 `Stop-Job`으로 먼저 끊으므로 같은 결함이 아니다.
3. **281.** `tests.md`에 `tests/tools/`의 pwsh 시험 본문이 CI의 리눅스 pwsh에서도 돈다는 항목을 더했다. 선례는
   `tests/tools/test_open_session.py`의 `_PATTERN_TIMED`이다.
4. **카나리아(첫 판).** 명세 둘을 더했다(`.scratch/harness/probes/canary/tools_rule_thread_job_and_links.toml`,
   `tests_rule_pwsh_linux.toml`). 사전 확인 통과 2 뒤에 실제로 돌려 둘 다 통과 4였다(claude 2.1.300, 러너가 찍은 커밋 b4335124,
   커밋하기 전의 작업 트리). 실험군 셋은 `[Environment]::Exit`·`delete_path`와 `_PATTERN_TIMED`를 옮겼고, 대조군은 모두 "없음"이었다.
   첫 판에서는 `tidy-checkouts` 스킬 표의 같은 입력 예를 "거짓이 되지 않았다"며 두었는데, 셀프 리뷰가 낡은 목록과 "두 번"을 잡았다.

## 셀프 리뷰

`/code-review` 두 축(표준 축 sonnet, 명세 축은 대기열 세 행이 명세). base b4335124, 바뀐 파일 셋과 미추적 셋, 커밋 0. 두 축 모두
선례 이름과 사건 서술(PR #250, 2026-10-12, git 2.32, 누가 잡았나)을 코드와 일지로 재서 모두 맞다고 했다.

- 표준 축(판단 항목): ① `tidy-checkouts` 스킬 표가 같은 입력 예를 옮겨 적어 링크가 빠졌고 "두 번"이 원천과 어긋났다(작업 규약 4).
  ② 282의 남은 프로브에 후속 기록이 rules 문장뿐이고 수를 다시 세는 지시가 없다. ③ 스레드 잡 문장이 외부 명령 시간 제한 항목에
  섞였다(Divergent Change). ④ `open_session.ps1` 주석과 설명이 겹친다(Duplicated Code).
- 명세 축: ① Minor. "다시 쓸 때 고친다"는 rules에 있어 그 프로브를 열어도 실리지 않는다(`tools.md`의 `paths`에 프로브 폴더가 없다).
  ② Minor. `tests.md`의 길 하나는 보편 주장이고, 같은 파일의 `_FOCUS`는 진짜 어셈블리를 부르지 않고 대역만으로 돈다(직접 봤다).
  ③ Nit. "`finally`에서 잡을 지워"는 지금 코드에도 `finally`의 `Remove-Job`이 있어 결함이 남은 것으로 읽힌다. ④ Nit. 카나리아
  `[Environment]::Exit`는 흔한 API라 사전 지식으로 맞힐 수 있다.

**고친 것.** 스킬 표에 링크 입력과 "세 번"(대기열 116·278)을 넣었다. 스레드 잡 문장을 별도 항목으로 떼고, 측정치는 코드 주석과
프로브에 맡겨 선례로 가리키며, "시간을 넘긴 잡까지 지워(지금은 끝난 잡만 지운다)"로 고쳤다. 남은 프로브는 grep으로 다시 세라는
지시를 붙이고, 각 프로브 머리 주석에 알려진 결함 줄을 넣었다. `tests.md`는 윈도 전용 형식 없이 돌게 쓴다는 일반 조항과 길 둘
(`_PATTERN_TIMED`, `_FOCUS`)로 바꿨다. 카나리아는 1을 `$script:HungCalls`로, tests는 상수 둘로 바꿨고 스킬 명세
`tidy_skill_link_input.toml`을 더했다.
**남긴 것.** 표준 축 ④는 rules가 선례를 가리키는 것으로 줄여 남은 겹침이 이유 한 문장뿐이라 두었다.
**다시 돌린 것.** 사전 확인 통과 3, 실제 실행 셋 모두 통과 4(rules 둘의 대조군은 "없음", 스킬 대조군 주 체크아웃 b4335124는 옛
줄 `116`을 옮겼다). 손으로 치는 검증 다섯은 커밋의 pre-commit으로 갈음한다.

## 검사

- 첫 판 작업 트리에서 `uv run pytest -q -x`가 2877 passed, 7 deselected였다(파이프를 붙여 친 실행이라 종료 코드는 판정에 쓰지 않았다).
- 커밋 `8c24f4d5`의 pre-commit: checks, zizmor, check-instructions, lint-imports, check-type-escapes, pyright, run-hooks, web-verify,
  pytest, markdown tables, line separators, quotes, commit message가 Passed. ruff check·ruff format은 `.py`가 없어 Skipped이고 ruff
  설정도 바꾸지 않았다. mutation tables도 변이 표가 없어 Skipped다.
- 커밋 메시지의 첫 제목이 76자라 `hook_bash_commit_msg`가 pre-commit 전에 막았다. 72자 안으로 줄여 다시 쳤다.

## PR 직전 보안·버그·성능 축

- `coderabbit-review`: CLI 0.7.5, 로그인은 됐고 `Seat : not assigned`(Plan Free)라 리뷰를 돌리지 않았다. 그래서 대체 둘을 돌렸다.
- `/security-review`: 실행되는 코드 변경이 없고(문서, 프로브 머리 주석, 카나리아 명세) 신뢰도 8 이상의 지적이 0건이었다.
- `bug-perf-review`: Minor 둘, 둘 다 유효로 판정했고 PR을 열기 전에 고쳤다.
  1. 스레드 잡 항목이 오류를 던지는 길을 적지 않았다. 선례 `Invoke-Action`은 `catch`에서 남긴 잡이 있으면 stderr에 문구를 낸 뒤
     `Exit(1)`로 끝내고, `hung_thread_job.ps1`도 그 갈래를 잰다. 그 구절을 더했다.
  2. 스킬 표의 "세 번 모두"가 이 스킬의 길이 아닌 canary 사건(278)까지 셌다. `tidy_checkouts.py`의 `delete_path`는 처음부터 링크를
     따라가지 않았다. 이 길의 두 번과 canary에서 온 링크 입력을 갈라 적었다.
  오탐 하나: 카나리아 질문이 항목의 문구를 따라 하는 것은 답을 흘리는 것이 아니라고 닫았다.
- 고친 뒤 카나리아 둘(`tools_rule_thread_job_and_links.toml`, `tidy_skill_link_input.toml`)은 원천 본문만 고쳤고 `expect`와 카나리아의
  자리가 그대로라 `--preflight`(통과 2)로 갈음했다(operations.md 카나리아 항목의 네 조건).

## 회고

후보 일곱, 승인 0, 기각 일곱, 넘김 없음.

1. **기각.** 대기열 278·282 행의 "어디로" 칸이 없는 선례(`tools/tidy_checkouts.py`의 `_cut_links`)와 틀린 수("프로브 넷")를 적었다.
   사건은 있으나, 반영하는 세션이 근거를 열어 바로잡았고 셀프 리뷰 두 축도 같은 주장을 쟀다. 저장소에 해가 남지 않았다.
2. **기각.** 첫 판에서 `tidy-checkouts` 스킬 표의 같은 입력 예를 거짓이 아니라며 두었다. `CLAUDE.md` 작업 규약 4와 셀프 리뷰 표준
   축이 이미 잡는다. 설계대로 잡혔다.
3. **기각.** rules에 적은 "다시 쓸 때 고친다"가 그 프로브를 열 때 실리지 않는 자리였다. `CLAUDE.md`의 로드 시점 표가 이미 말하고,
   명세 축이 잡았다.
4. **기각.** 카나리아 1번에 흔한 pwsh API(`[Environment]::Exit`)를 골라 사전 지식으로 맞힐 수 있었다. 같은 명세의 둘째 카나리아가
   판별했고 셀프 리뷰 뒤 바꿨다. 비용이 남지 않았다.
5. **기각.** 스레드 잡 항목이 오류를 던지는 길을 빠뜨렸고, 스킬 표의 "세 번"이 다른 도구의 사건까지 셌다. PR 직전 `bug-perf-review`가
   잡았다. 파이프라인이 설계대로 돈 것이다.
6. **기각.** 셸의 `for` 반복문과 변수 인자를 워크트리 가드가 두 번 거부했다. `CLAUDE.md` 환경 함정에 이미 있다. Edit 도구로 바꿨다.
7. **기각.** 커밋 제목이 76자라 `hook_bash_commit_msg`가 pre-commit 전에 막았다. 막는 훅이 설계대로 게이트 한 바퀴를 아꼈다.

## PR 봇

- [PR #255](https://github.com/njh6803/agent-os/pull/255). 검사 여섯(python, web, e2e, visual, verify, claude-review)이 모두 초록이었다.
- claude-review는 rules의 선례(`delete_path`, `_cut_links`, `Invoke-PatternTimed`, `_PATTERN_TIMED`, `_FOCUS`)를 코드로 맞춰 보고 지적 없음.
- CodeRabbit은 `Review rate limited`라 리뷰가 없었다. 회차로 세지 않는다.

## 다음

- `skill-check-and-retro-section` 워크트리는 병합된 PR의 머리와 브랜치 끝이 달라 `tidy-checkouts`가 사람에게 넘겼다. 이 세션은 보지 않았다.
- 휴지통(`.claude/worktrees/.tidy-trash/`)의 `.venv` 넷은 python.exe 셋이 모듈을 올려 남았다. 다음 `tidy-checkouts`가 다시 비운다.
- 진단 프로브 셋(`composer_*.ps1`)의 지우는 모양은 머리 주석대로 다시 쓸 때 고친다.
- 이 PR은 워크트리에서 병합한다. 주 체크아웃은 다음 새 세션의 `tidy-checkouts`가 당긴다.
