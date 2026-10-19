# 2026-10-19 (19) 변이 도구의 표 가드 넷(대기열 313·317·358·359)

next-session 지시문으로 연 새 세션의 하네스 chore다. 대상 파일이 `tools/mutate.py`인 열린 대기열 행 넷을 한 PR로 닫는다.
이 세션의 지금 제목은 `chore/mutate-table-guards`이고, 셀프 리뷰 직전에 인계 계기가 와서 넘긴다(아래 인계 절).

> 사용자: "대기열 313·317·358·359(대상 파일이 `tools/mutate.py`인 열린 행 넷. 358은 3회차)를 chore 한 PR로 반영한다 / 다음 작업: 대기열 313·317·358·359(대상 파일이 `tools/mutate.py`인 열린 행 넷. 358은 3회차)를 chore 한 PR로 반영한다 / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: 대기열 313·317·358·359(대상 파일이 `tools/mutate.py`인 열린 행 넷. 358은 3회차)를 chore 한 PR로 반영한다 / 브랜치: chore/mutate-table-guards / 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 / 읽을 것: docs/journal/2026-10-19-13-pre-commit-batch.md의 \"회고\"와 \"다음\" / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session \"워크트리에서 병합할 때\"를 Read로 열어 따른다. 열린 PR #301(대기열 306, 브랜치 chore/mutate-ctrl-c-under-load)이 tools/mutate.py와 tests/tools/test_mutate.py를 고친다. 병합됐는지 먼저 본다 / 이번 요청 범위: PR과 병합까지" (첫 메시지의 시작 줄과 지시문 열 줄을 `/`로 이어 옮겼다)

## 시작

- **정리.** 주 체크아웃 세션에서 `tidy-checkouts`를 먼저 돌았다. 루트는 main이고 깨끗해 `b1468314`에서 `a60e2ddd`로
  빨리감기했다. 판정이 지운 것은 로컬 브랜치 `worktree-path-pattern-gitignore` 하나다. 넘긴 것은 분리 HEAD 둘
  (`confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`, 커밋이 origin/main에 없다)과 `skill-check-and-retro-section`(병합된 PR의
  머리와 브랜치 끝이 다르다)이다. 휴지통의 `vigorous-mahavira-ebe993~~web%2Fnode_modules`는 `node.exe`·`esbuild.exe`가 쥐어
  `empty-trash`가 1로 끝났다(다음 정리가 다시 본다).
- **워크트리.** `EnterWorktree(name=mutate-table-guards)`로 들어가 `chore/mutate-table-guards`로 바꿨다. 기점은 `a60e2ddd`다.
- **PR #301.** 아직 열려 있고(`CONFLICTING`) 이 PR과 겹치는 파일은 `tests/tools/test_mutate.py` 하나다. #301은 프로세스 시험
  구역(`_뛰는지`→`_멈추는지`·`_자라는지`)만 고치고, 이 PR은 파일 끝에 시험을 더해 글자 충돌은 없을 것으로 봤다(재지 않았다).
  `tools/mutate.py`는 #301이 고치지 않는다.

## 구현

- **313.** `tools/mutate.py`에 판정마다의 낱말 표 `_VERDICT_WORDS`와 `_verdict_only`를 두고, `expect_output`(변이의 러너 판정)과
  `baseline_output`(러너의 판정)에서 판정 낱말만으로 된 표지를 변이 파일 오류로 낸다. 낱말은 `[^\W\d_]+`이고 대소문자를
  가리지 않아 `1 failed`·`FAILED`도 걸린다. 낱말이 없는 표지(`== 1`)와 exit 판정은 거르지 않는다.
- **317.** `_escape_hint`: 0번인 원문이 글자 그대로의 `\n`·`\t`를 들고 그것을 푼 바이트에서 찾히면 작은따옴표 문자열은
  이스케이프를 풀지 않는다는 까닭과 횟수를 덧붙인다. 줄 끝 힌트가 먼저이고 둘을 함께 맞춰 보지 않는다(시험으로 고정).
- **359.** `_note_uncommitted`: 이름·번호·`--since` 없는 전체 실행이면 기준선 전에, 변이가 고치는 파일과 `tests` 인자 가운데
  러너의 자리 기준으로 있는 파일(`::` 뒤는 뗀다)에 `git status --porcelain`의 변경이 있으면 한 줄로 알린다. 막지 않는다.
- **358.** `_running_marker`: `measure`를 감싸 그 체크아웃의 git 디렉터리(워크트리면 `.git` 파일의 `gitdir:`)에
  `mutate-running-<pid>.json`(pid, 표의 절대 경로)을 두고 끝나면 예외로 끝나도 지운다. 새 PostToolUse 계기 훅
  `tools/hook_edit_during_mutate.py`(Write|Edit|NotebookEdit, `hook_edit_during_commit` 다음에 등록)가 고친 파일의 체크아웃에서
  산 pid의 표지를 찾으면 알린다. 처방은 `bash.exe`·`uv.exe`·`python.exe`를 명령 줄로 찾아 가장 위를 `taskkill /T`로 끝내고
  `git diff`를 보는 것이다. 훅의 페이로드 둘(`${MUTATING_REPO}` 발동, `${STALE_MUTATING_REPO}` 침묵)은 `tools/run_hooks.py`의
  `_mutating_repository`·`_ended_pid`가 만든다. 도구 독스트링의 `TaskStop` 처방에도 무엇을 찾을지 적었다.
- **고친 시험 하나.** `test_출력을_파이프로_받아도_도는_동안_줄마다_내보낸다`는 실제 저장소(`ROOT`)에서 도구를 띄워, 커밋하지
  않은 `tools/mutate.py`가 있으면 359의 알림이 첫 줄에 왔다. 번호 `1 2`로 둘 다 골라 알림이 나지 않게 했다.
- **문서.** `.claude/rules/tools.md` 훅 시간 문단에 새 훅 한 문장(시간은 재지 않은 어림), 새 카나리아
  `.scratch/harness/probes/canary/tools_rule_edit_during_mutate.toml`(통과 4), 새 변이 표
  `.scratch/harness/probes/mutate_table_guards_mutations.toml`(열넷, `--check` 원문 모두 한 번씩. 아직 돌리지 않았다), 대기열
  네 행 닫힘.

## 검사(커밋 전)

- `tests/tools/test_mutate.py`·`test_hook_edit_during_mutate.py`·`test_run_hooks.py`·`test_hook_edit_during_commit.py`를
  `-n 4`로: 초록(종료 0).
- `tools/run_hooks.py`: 131건 어긋남 0(새 훅의 발동·침묵 둘 다 ok).
- `ruff check .`·`ruff format`: 초록. `pyright`(바뀐 파일 다섯): 0 오류. `check_type_escapes`: 0.
- `tools/sibling_overlap.py`: 번호 겹침 없음. 1로 끝난 까닭은 카나리아였고 새 명세를 쓰고 돌렸다.
- `tools/run_checks.py` 전체는 아직 돌리지 않았다.

## 인계

셀프 리뷰 직전(`code-review`를 부른 직후)에 인계 계기가 왔다. 세션 컨텍스트 약 33만 토큰. 셀프 리뷰는 새 세션이 한다.
변이 표 전체 실행은 독스트링대로 셀프 리뷰와 PR 직전 리뷰를 반영해 커밋한 뒤 다른 워크트리에서 한 번 돈다. 프로브
README(`.scratch/harness/probes/README.md`)의 새 표 행은 그 결과와 함께 쓴다.

실행 중 세션 확인(2026-10-19T07:13Z, `list_sessions` 50): 실행 중인 것은 `chore/sibling-overlap-batch`·
`chore/path-pattern-gitignore`·`chore/mutate-ctrl-c-under-load`(#301, 대기열 306)와 그 인계함 세션들이고, 이 브랜치나 네 행을
제목으로 든 세션은 없다.

낸 지시문:

```
다음 작업: 대기열 313·317·358·359(대상 파일이 `tools/mutate.py`인 열린 행 넷. 358은 3회차)를 chore 한 PR로 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 313·317·358·359(대상 파일이 `tools/mutate.py`인 열린 행 넷. 358은 3회차)를 chore 한 PR로 반영한다
브랜치: chore/mutate-table-guards
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-19-mutate-table-guards.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, 기준 origin/main, 명세는 대기열 네 행과 일지 2026-10-19-13의 회고·다음 절)부터 한다. docs/journal/2026-10-19-19-mutate-table-guards.md. 그 뒤 남은 것: 프로브 README의 새 변이 표 행, 커밋 뒤 다른 워크트리에서 `mutate_table_guards_mutations.toml` 전체 실행, `tools/run_checks.py` 전체
확인할 선행 조건: 열린 PR #301(대기열 306, chore/mutate-ctrl-c-under-load)이 tests/tools/test_mutate.py를 고친다. 먼저 병합되면 이 브랜치와 겹치는지 병합 전에 본다(글자 충돌은 재지 않았다)
이번 요청 범위: PR과 병합까지
```

제목을 `chore/mutate-table-guards (인계함)`으로 바꿨고, 백그라운드 작업은 없었고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-19T07:14:52Z

## 이어받은 세션: 셀프 리뷰

> 사용자: 지시문 그대로(위 "낸 지시문"과 같다)

새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어왔다. PR #301은 아직 열려 있다(`CONFLICTING`). origin/main은 `a60e2ddd`
그대로다.

범위: base `a60e2ddd`, 바뀐 파일 일곱, 커밋 0, 미추적 다섯. 표준 축(sonnet·high)과 명세 축을 함께 띄웠다.

- **명세 축.** 네 행의 처방이 모두 들었다. Critical·Major 없음. 시험 220 통과, 변이 표 `--check` 원문 열넷 모두 한 번.
  Minor 넷: (1) 대기열 네 행의 셋째 칸을 닫힘으로 통째로 바꿔 "자체 승인…3회차, 일지…"가 사라졌다(이웃 311·312·318은 원래
  문구 뒤에 닫힘을 덧붙인다). (2) 표지 지우기 시험이 도구 안에서 잡히는 `OSError` 길만 밟아, `finally`를 빼는 변이가 지나간다.
  (3) 판정 낱말이 아닌 낱말이 섞인 늘 실리는 문구(`1 failed in`)는 받는다(못 보는 것에 적혀 있다). (4) "exit 판정은 요약을 읽지
  않아 낱말이 없다"는 판정기에만 참이고, exit 러너의 명령이 pytest면 `["failed"]`가 지나간다. Nit: 매처가 처방의
  "Write·Edit"보다 넓다(`hook_edit_during_commit`의 꼴).
- **표준 축.** Major 하나: 훅의 처방이 "그 pid 와 표의 경로가 든 줄"로 찾으라 하는데, 표지는 절대 경로이고 놓친 프로세스의
  명령 줄은 상대 경로였으며(일지 2026-10-19-13), 표지의 pid는 python의 것이라 `bash.exe`의 명령 줄에 없다. 처방의
  `taskkill /T /F`와 도구 독스트링의 `taskkill /T`도 어긋난다. Minor: 변이 표의 한 표지가 단언 메시지 문자열이라 같은 시험의
  다른 단언이 실패해도 pytest가 코드를 보여 실린다, `_running_marker`가 쓰기 실패를 조용히 삼킨다, 판정 낱말 검사 세 줄의
  중복, `_note_uncommitted`가 표 파일 자체는 보지 않는다, 표를 돌리기 전의 닫힘, 훅 독스트링의 "표를 읽고 원문을 보는 동안"이
  틈이라는 서술(원문 확인은 `measure` 안이라 표지 안이다), 시험 모양 셋. Nit 셋.

판정:

- 고친다: 표준 Major(처방), 명세 (1)(2)(4), 표준의 표 파일 감시·훅 독스트링의 틈·변이 표지.
- 남긴다: `_running_marker`의 구조와 쓰기 실패 알림(표지는 계기 훅을 위한 보조라 쓰지 못해도 변이는 돌아야 하고, 훅과 같은
  fail-open이다), 검사 세 줄의 중복(두 자리, 각 두 줄), 시험 모양 셋과 Nit 셋(판단 항목), 명세 (3)(못 보는 것에 적혀 시험으로
  고정됨), 표를 돌리기 전의 닫힘(이 PR 안에서 전체 실행을 돌리고 README 행에 결과를 적는다).

고친 것:

- **훅 처방.** `context_for`가 표 파일 이름(`_file_name`, 윈도·POSIX 구분자 둘 다)을 찾을 열쇠로 주고, 표지의 pid가 python의
  것이며 그 위에 `uv.exe`·`bash.exe`가 있다고 적는다. 시험 `test_남은_묶음은_절대_경로가_아니라_표_파일_이름으로_찾게_한다`(먼저
  빨강을 봤다). 도구 독스트링의 처방도 "표 파일 이름이나 묶음 스크립트"와 `taskkill /T /F`로 맞췄다.
- **표 자체 감시.** `_note_uncommitted`가 표 파일(저장소 안이면)도 본다. 시험 도우미 `_시험이_든_저장소`가 표를 커밋하게 바꾸고
  `[표_자체]` 사례를 더했다(먼저 빨강을 봤다).
- **잡지 않는 예외.** `test_도구가_잡지_않는_예외로_끝나도_표지는_지운다`.
- **exit 판정 문구.** 독스트링과 시험 독스트링을 "거를 낱말을 두지 않는다"와 못 보는 것(exit 러너의 명령이 pytest여도 받는다)으로
  고치고, 시험 id 둘에 `못_보는_것_`을 붙였다.
- **훅 독스트링의 틈.** "표를 읽고 고르고 시작 줄의 알림을 내는 동안(원문 확인은 표지를 둔 뒤다)".
- **대기열 네 행.** 원래 셋째 칸을 되살리고 그 뒤에 닫힘을 덧붙였다(일지 이름 포함).
- **변이 표.** 호출 모양을 바꾼 원문 하나를 고치고, 단언 메시지 표지에 `AssertionError: ` 머리를 붙이고, 넷을 더해 열여덟이다(표
  자체를 보지 않기, `finally` 없이 지우기, 훅이 절대 경로로 찾게 하기, 이름을 뗄 때 윈도 구분자를 보지 않기). `--check` 원문 모두
  한 번.

PR 직전 리뷰에 밀 새 사실 문장(원문):

- 훅 `context_for`: "위의 pid 는 변이 도구를 돌리는 `python.exe` 의 것이고 그 위에 `uv.exe` 와 묶음을 돌리던 `bash.exe` 가 있다",
  "명령 줄의 경로는 상대 경로일 수 있어 위의 절대 경로로는 찾지 않는다"
- `tools/mutate.py` 독스트링: "`uv run` 이 띄운 python 의 명령줄 경로는 상대 경로였다", "exit 러너의 명령이 pytest 여도 그 출력의
  판정 낱말을 거르지 않는다(`["failed"]` 를 받는다)", "표 자체(표지가 여기 있다)"
- 훅 독스트링: "원문 확인은 표지를 둔 뒤다"

다시 돌린 것: 바꾼 시험 세 파일(`-n 4`)이 처음에 하나 빨갰다. 표를 커밋하게 바꾼 도우미 때문에 `--since HEAD`로 고를 변이가
없어진 `[since]` 사례라, 그 사례에서 표의 변이 이름을 바꿔 고르게 하고 다시 초록(6 통과)을 봤다. `run_hooks.py` 131건 어긋남 0,
pyright(바뀐 파일 다섯) 0, ruff 초록.

첫 커밋 시도는 pre-commit의 변이 표 검사(`--staged`)에 막혔다. `_mutated`의 `hint` 줄을 바꿔 `mutate_buffer_eol_retry_mutations.toml`의
원문 둘(줄 끝 힌트를 빼기, 두 번에도 붙이기)이 0번이 됐다. 각 변이가 빼려던 판정만 빼게 원문과 새 글을 지금 줄에 맞췄다. 둘은 전체
실행 때 번호로 골라 다시 잰다. 나머지 검사(pytest·web-verify·pyright 등 열)는 그 시도에서 초록이었다.

둘째 시도는 부하 실패 둘에 막혔다. web-verify는 vitest가 `RunPage.decision.test.tsx`의 forks 워커를 띄우지 못했고, pytest는
`test_실제_러너는_기다리는_동안_Ctrl_C_가_나도_손자_프로세스까지_끝낸다`의 `assert not _뛰는지(심장)` 하나(3599 통과)였다. 그 단언은
열린 PR #301(대기열 306)이 부하 아래에서 흔들린다고 고치는 자리이고, 이 브랜치는 그 시험과 `run_command`를 고치지 않는다. 같은
변경으로 첫 시도에서 둘 다 초록이어서 그대로 다시 커밋했다.

셋째 시도는 run-hooks(340.2초, 첫 시도는 278.9초)에서 이 브랜치가 고치지 않은 `hook_choice_facts`의 발동 사례 하나가 출력 없이
종료 코드 1이었다(같은 시도의 pytest 968.9초·web-verify 672.9초는 초록). 곧바로 `tools/run_hooks.py`를 홀로 돌리니
131건 어긋남 0이었다. 세 시도가 서로 다른 자리에서 흔들려 같은 변경으로 넷째를 쳤다.

넷째 시도도 이 브랜치가 고치지 않은 시간 시험 둘에 막혔다. web-verify는 vitest 한 시험의 `Test timed out in 60000ms`, pytest는
`tests/tools/test_hook_midturn_korean.py::test_트랜스크립트_파일이_없으면_기다리지_않는다` 하나(3599 통과)였다. 그때 이 PC는 CPU
부하 80%, node 106·python 18·bash 20·pwsh 17 프로세스였다(PowerShell `Get-Process`·`Win32_Processor`로 손으로 봤다). 다섯째를
치고, 또 막히면 멈추고 사람에게 알린다.
