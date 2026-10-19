# 2026-10-19 (33) tools 규칙의 허용 목록·다른 견줌 문장과 외부 명령의 시간 제한 검사

브랜치 `chore/tools-rule-batch`. 대상 파일이 `.claude/rules/tools.md`인 열린 대기열 행 가운데 지금 반영할 수 있는 셋(321·342·361)을
chore 한 PR로 반영했다.

> 사용자: 대기열 321·342·361(대상 파일이 .claude/rules/tools.md인 열린 행 셋)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이
> 원천이다

시작 전에 주 체크아웃 세션으로 `tidy-checkouts`를 돌았다. 루트는 main이지만 `.claude/skills/tdd/SKILL.md`가 고쳐져 있어 당기지
않았다(5f38d61c, origin/main은 2a0ebe48). 지운 것은 로컬 브랜치 `worktree-canary-runner-batch`(커밋이 모두 origin/main에 있다)
하나다. 넘긴 것은 분리 HEAD 둘(`confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`, 그 커밋이 origin/main에 없다)과
`skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이 다르다)이다. 나머지 열아홉은 병합된 PR이 없거나 그 폴더를 작업
디렉터리로 쥔 프로세스 때문에 남았다.

## 한 일

- 342. 새 검사를 `tools/check_instructions.py`의 `calls_without_timeout`으로 두었다. `tools/` 아래 파이썬 전부에서 `subprocess`의
  `run`·`call`·`check_call`·`check_output`과 `communicate`·`wait` 메서드에 `timeout`이 없거나 글자 그대로 None인 호출을 잡는다.
  행은 "pre-commit 훅"이라 했는데, 새 훅이나 러너의 새 검사로 두면 게이트가 하나 늘어 `CLAUDE.md`의 게이트 수와 CI를 함께
  고쳐야 한다. 지침 검사는 이미 tools.md 항목 하나(훅의 stdin을 바이트로 읽기, `hooks_reading_text_stdin`)를 AST로 판정하고
  pre-commit의 러너와 CI가 모두 돌리므로, 그 옆에 두면 게이트 수를 바꾸지 않고 같은 자리에서 막는다.
- 342의 사전 집계. 들인 때 잡힌 것은 열셋이었다. 하나씩 판정했다.
  - 기다릴 일이 없는 자리 셋: `tools/run_checks.py`의 `process.wait()` 둘과 `tools/mutate.py`의 `process.wait()` 하나. 모두
    `kill_tree`·`_kill_tree`로 끝낸 자식을 거두는 자리다.
  - 끊으면 안 되는 자리 하나: `tools/tidy_checkouts.py`의 `real_git`. `worktree remove`·`branch -D`도 이 길로 가고, 큰
    `node_modules`를 지우는 중에 끊으면 지우다 만 폴더가 남는다.
  - 나머지 아홉에는 시간 제한을 더하고 넘김을 그 도구의 실패 갈래로 보냈다. `check_instructions`의 주 체크아웃 찾기(None),
    `check_line_separators`·`check_md_tables`의 `git ls-files`(예외로 멈춘다. `check=True`의 실패와 같다), `check_quotes`의 둘
    (git이 실패한 갈래), `gh_run_summary`의 `gh run view`(알리고 1), `hook_git_main_commit`의 `_git`(None, 막지 않는다. 등록의
    20초 안에 두 호출이 들도록 8초), `tidy_checkouts`의 `gh pr list`(`ToolError`, 종료 3)와 `tasklist`(살아 있다고 본다).
  - 앞의 넷은 그 호출이 걸친 줄의 `# 시간 제한 없음: <까닭>` 주석으로 뺀다. 거짓 양성이 넷으로 적고 자리가 고정돼 하드
    게이트로 두었다. `communicate`는 표지로 빼지 않는다. 342의 사건이 바로 끝낸 뒤의 `communicate()`였고, 트리를 떠난 손자가
    파이프를 쥐면 돌아오지 않는다.
- 342의 `.claude/rules/tools.md`. 기다리는 도구 항목에 검사의 이름(`calls_without_timeout`), 사건, 표지와 그 선례(`real_git`)를
  더했다.
- 361. 같은 파일의 지우는 도구 항목 끝에 한 문장(판정을 깨는 입력을 찾으면 같은 값을 견주는 다른 자리에도 넣어 본다)과 사건,
  선례(`same_branch`와 세 호출 자리)를 더했다.
- 321. 같은 파일에 새 항목(입력에서 값을 골라 지우지 않는 저장소에 남기는 도구는 허용 목록으로 짓고, 남기면 안 되는 값을 남기려는
  입력으로 반박한다. 받는 꼴을 넓히는 고침도 같다)과 사건, 선례(`program_of`)를 더했다.
- 카나리아 `.scratch/harness/probes/canary/tools_rule_allowlist_comparisons_timeout_check.toml`을 새로 썼다.
- 변이 열다섯을 더했다. `instruction_check_mutations.toml`에 새 판정의 열셋, `tidy_checkouts_mutations.toml`에 시간을 넘긴
  gh·tasklist의 둘이다.
- 대기열 321·342·361을 닫았다.

## 검사

셀프 리뷰 전:

- 변이. `instruction_check_mutations.toml`을 `--since origin/main`으로 열셋 모두 기대대로, `tidy_checkouts_mutations.toml`을
  같은 방식으로 둘 모두 기대대로.
- 카나리아 `tools_rule_allowlist_comparisons_timeout_check.toml`: 통과 4(실험군 3/3이 셋을 모두 옮기고 대조군은 "없음" 셋,
  이 PC, claude 2.1.302, 러너가 찍은 커밋 43a59020 위의 커밋하지 않은 판).
- `uv run python tools/run_checks.py`: 여덟 모두 Passed(zizmor, lint-imports, check-instructions, check-type-escapes, pyright,
  run-hooks, pytest 419.2초, web-verify 498.0초). ruff 둘 0.

셀프 리뷰 반영 뒤:

- 고친 시험 묶음(`-k`로 고른 다섯 파일의 마흔넷) 모두 통과. 이 PC에 다른 Claude 세션이 열 개 남짓 돌아 6분 44초가 걸렸다.
  앞서 훅 시험 셋도 시험은 0.04초 이하인데 전체가 228초였다.
- 변이. 지침 검사 열셋을 다시 `--since origin/main`으로 골라 모두 기대대로. tidy 둘 가운데 140이 어긋났다. 결과는 빨강이었으나
  표지(`where False = <function process_alive`)가 출력에 없었다. 출력을 보지 않고 표지를 짐작한 탓이다
  (`.claude/rules/probes.md`는 손으로 먼저 보라고 한다). 실제 출력의 `where False = process_alive(4242)`로 고쳐 140을 번호로
  다시 돌려 기대대로.
- 카나리아는 사전 확인(`--preflight`) 통과로 갈음.
- ruff 둘: format이 고친 시험 파일 하나를 다시 감은 뒤 0. 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다(아래 커밋 뒤 적는다).

## 셀프 리뷰

`/code-review`, 기점 43a59020, 커밋 0, 바뀐 파일 열아홉, 미추적 둘(카나리아 명세, 이 일지).

명세 축: Critical·Major 0, Minor 2, Nit 3. 재서 맞은 것으로 기점의 열셋(넷과 아홉), 경계 입력, 넘김 갈래 넷, 361의 세 호출
자리, 321의 반박 입력 여섯과 `program_of`의 동작, 카나리아 원본과 `# 최신 결과:` 줄, 변이 표 번호를 들었다.

- Minor 1. `real_git` 표지가 까닭보다 넓다. `tidy_checkouts`의 git은 모두 그 함수로 가서 읽기만 하는 git(`status --ignored`,
  `for-each-ref`, `merge-base`, `rev-parse`)도 시간 제한이 없다. 판정: 맞다. 문구를 고친다(표지, 독스트링, tools.md). 읽기만
  하는 git에 시간 제한을 주려면 지우는 도구의 `Ops.git`을 두 길로 갈라야 하고, 지우는 도구를 바꾸면 tools.md가 임시 저장소의
  반박을 요구해 이 PR에서는 하지 않는다. 회고 후보로 넘긴다(아래 "다음").
- Minor 2. 못 보는 것 목록이 틀리고 시험이 일부만 있다. `asyncio`의 `await p.wait()`·`await p.communicate()`는 잡히고
  (`communicate`는 timeout을 받지 않고 표지로도 못 빼 피할 길 없는 거짓 양성), `from subprocess import *`와
  `getoutput`·`getstatusoutput`은 못 보는데 목록에 없고, `getattr`·`sp = subprocess`·`os.popen`·asyncio는 시험이 없다. 판정:
  맞다. 고친다.
- Nit 3. 342 닫힘의 "시험 열여섯"은 지침 검사 시험만 센 수다. 판정: 고친다(스물둘).
- Nit 4. 표지가 같은 줄의 다른 호출도 뺀다. 판정: 못 보는 것에 적고 시험으로 고정한다.
- Nit 5. tools.md의 "더했다(일지 2026-10-17-12)"가 그 일지에서 더한 것처럼 읽힌다. 판정: 고친다.

표준 축(sonnet·high, 앞선 세션 프로세스가 끝나며 멈춘 것을 이어 돌렸다): Critical·Major 0. 명세 축의 다섯과 같은 지적에
`from subprocess import *`·`getoutput`·`p.wait(*args)`를 더했다. 재서 맞은 것으로 기점의 열셋, 훅의 git 많아야 둘과 등록
20초, `same_branch`의 세 자리, `program_of`의 경계 입력 스물둘, tidy의 gh 넘김이 종료 3으로 가는 길, 변이 `old` 원문 399건의
유일함, 카나리아 토큰의 누설 0을 들었다.

- Minor. `check_line_separators`·`check_md_tables`의 "시간을 넘기면 예외로 멈춘다"에 시험이 없다. 판정: 맞다. 고친다.
- Minor. 새 변이의 표지가 `FAILED …::시험` 줄이라 단언이 여럿인 시험에서 어느 단언이 실패했는지 가르지 못하고, 한 시험에
  변이 셋이 붙었다(`.claude/rules/probes.md`의 표지 고르기). 판정: 맞다. 표지 시험을 셋으로 쪼개고, 단언이 여럿이거나
  예외를 기대하는 변이는 값이 찍힌 `E` 줄의 문구로 바꾼다. pytest는 실패한 줄까지의 시험 소스를 함께 찍어 소스의 문구는
  고르지 않는다.
- Minor. 훅 시험이 등록의 20초를 숫자로 박았고, 막는 갈래(main이고 커밋 유무 읽기만 넘김)를 고정하지 않았다. 판정: 맞다.
  `tools.run_hooks.registered_hooks`로 등록을 읽고 그 갈래의 시험을 더한다.
- Nit. 시간 넘김 시험이 timeout의 형만 본다. 판정: 고친다(값을 `CALL_TIMEOUT`과 견준다).
- Nit. "pre-commit 은 훅에 시간 제한을 두지 않는다"의 근거가 저장소에 없다. 판정: 근거는 `tools/run_checks.py` 독스트링(대기열
  333의 11시간)에 있다. 두 주석이 그 자리를 가리키게 고친다.
- Nit. `process_alive`의 tasklist가 워크트리마다 60초라 합의 상한이 없다. 판정: 남긴다. 넘김은 "살아 있다"로 지우지 않는 쪽이고,
  합의 상한은 `tidy_checkouts` 전체의 시간 설계라 이 행의 범위(호출마다의 시간 제한)를 넘는다.
- Nit. 시간 넘김을 내는 가짜 `stuck`이 시험 파일마다, `CALL_TIMEOUT`이 도구마다 있다(Duplicated Code). 판정: 남긴다. `tools/`의
  도구는 단독 실행 스크립트로 서로 import하지 않는 것이 이 저장소의 결정이고(tools.md 첫 항목은 훅을 말하지만 검사도 같은
  꼴로 지어 왔다), 시험 파일은 그 도구를 하나씩 따른다.
- Nit(판단). `check_instructions.py`가 지침 검사와 `tools/`의 AST 검사를 함께 맡는다(Divergent Change). 판정: 남긴다. 같은 파일이
  이미 `hooks_reading_text_stdin`으로 tools.md 항목을 AST로 판정하고, 게이트 수를 바꾸지 않으려고 고른 자리다(위 "한 일").
- Nit(diff 밖). 321의 선례는 `program_of`인데 같은 사건의 `pr_head_of`는 `--head "$(cat f)"`에서 `$(cat f)`를 그대로 돌려준다.
  판정: 손으로 불러 재현했다(스크래치 `pr_head_probe.py`, `--head $(cat …)`는 `$(cat`). 기록에 남는 PR 브랜치라 이번에 더한
  321 항목(허용 목록)에 어긋나지만, 대기열 321의 "어디로"는 규칙 문장이라 고침은 후속으로 넘긴다(아래 "다음").
- 독스트링의 `asyncio`. 명세 축 Minor 2를 고치며, 판정을 바꾸지 않고 잘못 막는 것으로 옮겼다. `tools/`에 asyncio가 없어 지금
  거짓 양성이 0이고, 들일 때 함께 고친다고 적었다(Speculative Generality를 피했다).

고친 것: 위에서 "고친다"로 판정한 열. 시험은 서른둘이 됐다(`test_check_instructions.py` 스물둘, 나머지 도구 여섯의 열). 카나리아는
원천 본문의 문구만 고쳐 사전 확인으로 갈음했다(조건 넷: 같은 PR·같은 claude 2.1.302의 통과, 머리말 그대로, 명세의 칸 그대로,
카나리아 셋이 묻는 자리에 남음).

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장, 원문):

- `tools/tidy_checkouts.py`의 `real_git` 독스트링: "이 도구의 git 은 모두 이 함수 하나로 가서 읽기만 하는 git(`status --ignored`,
  `for-each-ref`, `merge-base`, `rev-parse`)도 함께 시간 제한이 없다. 그것만 끊으려면 `Ops.git` 을 지우는 길과 읽는 길로 갈라야
  한다."
- `.claude/rules/tools.md`: "끊으면 안 되는 자리(지우는 git까지 그 도구의 git을 모두 맡은 `tools/tidy_checkouts.py`의 `real_git`.
  읽기만 하는 git도 함께 빠진다)"와 "이 항목을 어긴 것을 셀프 리뷰를 지나 PR 직전 `bug-perf-review`가 잡아(일지 2026-10-17-12)
  이 검사를 더했다(일지 2026-10-19-33)".
- `calls_without_timeout` 독스트링: "`asyncio` 하위 프로세스의 `wait`·`communicate` 는 timeout 을 받지 않아 `asyncio.wait_for` 로
  감싸도 잡히고, `communicate` 는 표지로도 뺄 수 없다", "`*`·`**` 로 펼친 인자는 timeout 이 든지 몰라 없는 것으로 본다", 못 보는
  것의 "`from subprocess import *` 뒤의 이름, `getoutput`·`getstatusoutput`(timeout 을 받지 않는다)", "표지는 줄 단위라 표지가
  걸린 줄의 다른 호출도 함께 뺀다".
- `tools/check_line_separators.py`·`tools/check_md_tables.py`의 주석: "pre-commit 은 훅에 시간 제한을 두지 않는다(`tools/run_checks.py`
  독스트링의 대기열 333, 대기열 342)".
- 훅 시험 독스트링: "`reason_at` 은 git 을 많아야 둘(브랜치, 커밋의 유무) 부른다."
- 변이 표 머리 주석: "pytest 는 실패한 줄까지의 시험 소스를 함께 찍어, 소스에 있는 문구는 표지로 고르지 않는다."

## 인계

커밋 `eb416d39`가 pre-commit을 모두 지났다(묶음 검사 584초, pytest 581.3초. 이 PC에 다른 세션이 여럿 돌던 때다). 막지 않는 인용 대조
경고 셋은 그대로 두었다. 대기열 354행의 것은 그 행이 처음부터 제안한 문장이고, 이 일지 84행과 128행의 것은 고치기 전의 규칙 문구와
독스트링을 옮긴 것이다(128행은 검사가 `*`를 벗겨 대조했다). 커밋 직후 인계 계기가 왔다(세션 컨텍스트 347,996 토큰, 경계 `커밋 뒤`).
인계하지 않는 때 다섯에 들지 않는다. 이 세션은 곁 세션이 아니고(`get_session`의 `self`에 `parentSessionId`가 없다), 요청 범위는
"PR과 병합까지"다. 인계 전 제목은 `chore/tools-rule-batch`다.

남은 단계는 origin/main 합치기(`5e7fa88`, #301이 프로브 README와 대기열을 고쳐 충돌 후보다), PR 직전 리뷰(위 "PR 직전 리뷰에 밀
주장"을 넘긴다), 푸시와 PR, 봇 회차, 워크트리에서 병합, 일지 "다음"과 회고다. 일지 "다음"에 넘길 후속 후보는 셋이다. 위 셀프 리뷰의
`token_report.py` `pr_head_of` 허용 목록, `tidy_checkouts`의 읽기만 하는 git에 시간 제한을 두는 갈래(`Ops.git` 가르기), 변이 140의
표지를 출력을 보지 않고 짐작한 일(`.claude/rules/probes.md`의 "고르기 전에 변이를 손으로 넣어 실패 출력을 한 번 보고"를 어겼다)이다.
같은 대상 파일의 대기열 57·141·238은 앞 지시문이 범위에서 뺀 그대로 열려 있다. 57은 실행 중 세션
`chore/worktree-overrides-pc-check`가 settings 쪽을 맡았는지 가르지 못했고, 141은 클라우드 세션에서 재야 하고, 238은 사람 몫이다.

낸 지시문:

```
다음 작업: 기능 하네스 chore. 대기열 321·342·361(대상 파일이 .claude/rules/tools.md인 열린 행 가운데 지금 반영할 수 있는 셋)을 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 321·342·361(대상 파일이 .claude/rules/tools.md인 열린 행 셋)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/tools-rule-batch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-33-tools-rule-batch.md 의 "셀프 리뷰"와 "인계"
이어받을 상태: 인계: 커밋 뒤. 커밋 eb416d39까지 구현, 셀프 리뷰 반영, 검증을 마쳤고 pre-commit을 모두 지났다. 아직 푸시하지 않았고 PR이 없다. 남은 단계는 origin/main 합치기(#301이 .scratch/harness/probes/README.md와 .scratch/retro-queue.md를 고쳐 충돌 후보다), PR 직전 리뷰(일지의 "PR 직전 리뷰에 밀 주장"을 넘긴다), 푸시와 PR, 봇 회차, 워크트리에서 병합, 일지 "다음"과 회고다. 일지의 "인계" 절은 커밋하지 않았고 일지 "다음"에 넘길 후속 후보 셋이 거기 있다. 일지 docs/journal/2026-10-19-33-tools-rule-batch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tools-rule-batch (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었고, 잠금 풀기는 `is not locked`로 이미 풀려 있었다.

open-session을 부른다 2026-10-19T13:01:49Z

## 이어받은 세션

> 사용자: 대기열 321·342·361(대상 파일이 .claude/rules/tools.md인 열린 행 셋)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이
> 원천이다

위 지시문으로 연 세션이다. 제목을 `chore/tools-rule-batch`로 바꾸고 `git worktree list`에서 그 브랜치가 체크아웃된
`.claude/worktrees/tools-rule-batch`로 `EnterWorktree(path)` 해 들어갔다(거부되지 않았다).

- origin/main 합치기. `7556070c`(#301, #309)를 합쳤다. 충돌 후보였던 `.scratch/harness/probes/README.md`와
  `.scratch/retro-queue.md`는 저절로 합쳐졌다(main은 README에 새 행 셋과 한 행의 문구, 대기열에 306·339 행의 문구와 새 행
  367·368을 더했고, 이 브랜치가 고친 행과 겹치지 않는다). main이 고친 `tools/token_report.py`는 하위 프로세스를 새로 띄우지
  않아, 합친 뒤 `tools/check_instructions.py`가 0으로 끝났다.
- 일지 번호. 합친 뒤 `tools/sibling_overlap.py`가 이 일지(28)가 main의 최신 일지 2026-10-19-29보다 이름순으로 앞이라고 알려
  `--move`로 33으로 옮겼다. 인용을 고친 파일은 `.claude/rules/tools.md`, 프로브 README, 카나리아 명세, 대기열, 이 일지다(위
  지시문 블록의 경로도 함께 바뀌었다). 옛 번호의 남은 인용은 grep으로 0이다.
- 번호를 옮긴 커밋의 pre-commit에서 pytest 하나가 빨갰다. `tests/tools/test_hook_midturn_korean.py`의
  `test_트랜스크립트_파일이_없으면_기다리지_않는다`가 2초 상한에 2.55초였다(`1 failed, 3658 passed`, pytest 882.1초, 묶음 검사
  947.8초. 이 PC에 다른 세션이 여럿 돌던 때다). 나머지 일곱 검사는 모두 지났다. 그 시험만 따로 돌리면 0.97초에 지났다. 이
  커밋은 문서와 일지 번호만 고쳐 그 시험을 건드리지 않았고, 대기열 306이 적은 같은 종류의 사례다. 빨간 것은 일지
  2026-10-19-25의 셋(3.34초, 2.6초, 2.30초)에 이어 네 번째다. 그 일지의 선례대로 고치지 않고 다시 커밋한다.
- 멈춤 지시. PR 직전 리뷰를 도는 동안 '하네스 작업 진행' 세션이 사용자의 요청을 전달했다. 그 세션이 retro의 승인 기준과
  next-session 결정표(chore 배치 조건)를 바꾸는 중이라, 이 PR은 병합과 일지까지 마치되 next-session으로 새 세션을 열지 않고
  같은 세션에서 다음 일을 시작하지도 않으며 재개 메시지를 기다린다. 재개되면 main을 당긴 뒤 바뀐 스킬은 디스크의 `SKILL.md`를
  Read로 열어 따른다. 전달된 사용자 원문은 아래와 같다.

> 사용자: 이 세션"하네스 작업 진행"의 모든 작업이 끝날 때 까지 현재 열린 세션들에게 현재 작업중인 것 까지만 마무리하고 다음
> 작업은 이어하지 않도록 지시하고 통제할 수 있어?
> 이 세션"하네스 작업 진행"의 모든 작업이 끝나면 재개할 수 있도록 해줘.

### PR 직전 리뷰

`coderabbit auth status`가 `Seat: not assigned`라 대체 둘을 돌렸다. 둘 다 첫 실행이 네트워크 오류(`ENOTFOUND`)로 멈춰 다시
돌렸다(`bug-perf-review`는 멈춘 자리에서 이었다).

- `/security-review`(합친 뒤 커밋 `e7b9294e` 기준): 지적 없음. 바뀐 `subprocess.run`이 모두 리스트 인자이고 `shell=True`가
  없으며, 새 AST 검사는 파싱만 하고, 지우기를 정하는 읽기는 넘기면 지우지 않는 쪽이라고 봤다.
- `bug-perf-review`: Critical·Major·Minor 0, Nit 넷. 위 "PR 직전 리뷰에 밀 주장" 여섯은 모두 사실이고, 1과 4에 한 군데씩 고칠
  곳이 있다고 했다. 관련 시험 일곱 파일 452개 통과(214초).
  - Nit. `check_line_separators`·`check_md_tables`의 시간 제한 주석이 까닭을 pre-commit에 시간 제한이 없다는 것으로 들지만,
    pre-commit 훅은 파일 이름을 넘겨 `git ls-files`에 닿지 않는다. 판정: 맞다(등록의 `types`와 `main`의 `paths`를 읽었다.
    인자 없이 `main()`을 부르는 것은 pytest의 저장소 상태 시험이다). 주석을 "인자 없이 돌 때만 부른다"로 고쳤다.
  - Nit. `calls_without_timeout`의 못 보는 것에 `Popen` 파이프 직접 읽기, `os.waitpid`, `functools.partial`, None이 될 수
    있는 조건식 timeout이 빠졌다. 판정: 맞다. 그 넷이 지나간다는 시험을 먼저 더해 통과를 본 뒤 독스트링에 적었다.
  - Nit. `real_git` 독스트링의 "갈라야 한다"가 단정이고 읽기 git 목록이 닫혀 있다(`rev-list`, `worktree list`도 읽기).
    판정: 맞다(두 하위 명령이 쓰이는 줄을 grep으로 봤다). 목록에 둘과 "등"을 더하고 "이 함수가 하위 명령으로 가르는" 길을
    함께 적었다.
  - Nit(보류). `check_quotes`에서 git이 멈추면 `added_lines`가 파일마다 60초를 기다리고, `tracked_text_files`가 넘기면 트리
    걷기로 가서 무시된 파일까지 말뭉치에 든다. 판정: 남긴다. 경고만 내는 검사이고 이 PR 전에는 끝없이 기다리던 자리다.
    고치려면 한 번 넘기면 뒤의 git을 건너뛰는 모듈 전역 상태를 들여야 하는데, git이 멈추는 상황을 재현하지 않았다. PR
    체크리스트에 적는다.

## 다음
