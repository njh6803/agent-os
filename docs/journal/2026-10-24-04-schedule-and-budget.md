# 2026-10-24 (04) 러너 명령: 과제 차례, 동시에 둘, 예산, 한도 기다림, 다시 돌기, 멈춤 (model-rerun 10)

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/10-schedule-and-budget.md
>
> 다음 작업: .scratch/model-rerun/issues/10-schedule-and-budget.md. 러너 명령이 과제 목록을 실행 차례대로 돌며 동시에 둘, 예산 상한, 한도 기다림, 다시 돌기, 멈춤을 지킨다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 10-schedule-and-budget)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/10-schedule-and-budget.md
> 브랜치: feature/10-schedule-and-budget
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-24-03-not-measured-checks.md의 "다음"과 docs/journal/2026-10-23-36-round-drive-record.md의 "다음"(PR #370 claude-review 둘째 회차가 10에 넘긴 budget_text의 nan·inf 막기는 그 일지에만 있고 티켓 10의 메모에는 없다)
> 이어받을 상태: PR #377의 claude-review 셋째 회차(c37730be)에서 보류한 둘은 티켓 11의 몫이고 10에서 할 일이 아니다. _without_messages의 tuple[list[str], bool] 반환과, 커밋 메시지 떼기와 tools/hook_bash_commit_msg.py 두 파서를 잇는 상호 참조 주석이나 같은 입력 시험이다. 티켓 11 "09에서 넘어온 메모"의 마지막 줄(그 계열을 별도 모듈로 빼기)을 할 때 함께 판단한다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 첫 턴에 `tidy-checkouts`를 돌고 `EnterWorktree`(name `10-schedule-and-budget`)로 들어가 브랜치를 바꿨다.
- `tools/rerun_runner.py`(새): 러너 명령. 시작 전 점검(본 측정 목록의 사전 등록 해시, 죽은 러너가 남긴 회차의 측정 아님(중단), 확인 없는 인계, 아직 오지 않은 한도의 풀리는 시각), 과제마다 다시 띄우기의 판정(`plan_task`)과 예산(`estimate_usd`), 동시에 둘의 회차 고리, 회차 하나의 조립(04 준비, 09 판정, 08 이어 가기, 07 게이트와 공식 단가, 01 쓰기), 명령 줄 입구(`main`).
- `tools/rerun_round.py`: 기록 없는 회차 폴더를 찾는 `unrecorded_round_dirs`를 지우기의 판정과 같은 자리(`_root_entries`, `_is_round_dir`, `_recorded`)로 꺼냈다.
- `tools/rerun_session.py`: `budget_text`가 `nan`과 무한대를 `ValueError`로 막는다(PR #370 claude-review 둘째 회차가 넘긴 것).
- `tools/proc_command_line.py`: 실행 파일 이름으로 pid를 훑는 `pids_named`(리눅스 `/proc/*/comm`, 윈도 Toolhelp). 윈도 갈래의 정의는 `tools/hook_edit_during_commit.py`의 것을 그대로 옮겨 훅 사본 대조 시험이 함께 본다.
- 시험: `tests/tools/test_rerun_runner.py`(새, 가짜 `claude`와 임시 원본 저장소로 회차를 끝까지 돈다), `fake_claude.py`(회차 폴더마다의 각본 `rounds`, 함께 도는 부름의 수 `running`, `EMAIL`), `test_rerun_round.py`·`test_rerun_session.py`·`test_proc_command_line.py`에 하나씩.
- 티켓 10에 "구현에서 정한 것"을, 11에 "10에서 넘어온 메모"를 더했다.

## 결정

티켓 10의 "구현에서 정한 것"이 원천이다. 줄이면 다음과 같다.

- 회차를 열기 전의 확인, 번호 잡기, 폴더 만들기는 주 스레드에서, 준비부터 기록 쓰기까지는 일꾼 스레드에서 한다.
- 결과 이벤트가 없는 호출이 든 세션은 공식 단가를 대신 넣고, 본 세션 기록 파일이 없으면 `modelUsage`만으로 셈한다.
- 게이트의 `GateError`·`OSError`는 측정 아님(준비)으로 적고 멈춘다. 끄지 못한 호출이 남은 회차 뒤에도 멈춘다.
- 기록의 게이트·준비 명령은 정해진 이름으로 적는다.
- 07의 열거화, `round_record` 정리, `_git` 사본 맞추기는 11로 넘겼다.

## 실수와 고친 것

- 시험 파일과 러너를 한 번에 쓰고 시험을 돌려, 러너가 없을 때의 빨강(ImportError)을 보지 못했다. 새 시험의 빨강은 변이 표로 본다.
- 시험판의 명령 줄 읽기 기본값을 늘 빈 값으로 두어, 줄 판정이 끄려던 호출이 "끄지 않고 남김"이 됐다. 진짜 `command_line`을 기본값으로 바꿨다.
- 설정 멈춤 시험의 각본이 init 과 결과 이벤트를 함께 내, 끈 호출에도 결과가 남아 대신 넣기가 일어나지 않았다. 규칙은 맞고 각본을 init 뒤에 매달리는 호출로 고쳤다.
- 큰 heredoc 으로 여러 곳을 고치려다 훅(상한 40줄)에 막혀 Edit 로 나눠 고쳤다.
- 변이 표(`rerun_runner_mutations.toml`, 22개)의 첫 실행에서 셋이 초록이었다. "동시에 셋까지 연다"는 자리 판정만 넓혀 일꾼 수(`ThreadPoolExecutor(MAX_PARALLEL)`)가 둘을 지켰고, 일꾼 수까지 넓히게 고쳤다. "풀리는 시각을 모르는 한도에서 멈추지 않는다"의 `halt = None or (` 는 halt 가 비었을 때 원문과 같은 동치 변이라 `halt and (` 로 고쳤다. "인계 확인을 판과 견주지 않는다(돌던 동안)"는 다른 판의 확인을 쥐고 도는 시험이 없어, `test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다`를 더했다. 그 시험의 표지를 처음에 `where 0 = run()` 으로 골랐는데 변이 판에서는 각본 없는 C 회차가 열려 다른 까닭으로 1 을 내, 실패한 단언은 안내 문구 단언이었다. 표지를 그 단언의 실패 문구로 바꿨다. 다시 돌린 표는 22 모두 기대대로였다.
- `test_rerun_round.py`의 import 차례를 ruff 가 잡아 고쳤다.

## 셀프 리뷰

`/code-review`(base 7496a830, 커밋 없음, 수정 파일 10개와 미추적 4개). 표준 축은 sonnet·high, 명세 축은 상속.

고친 것.
- 표준 Major·명세 Major: "`PriceError`면 폴더가 남아 다음에 측정 아님(중단)으로 적힌다"가 코드와 달랐다. 중단 기록을 쓸 때도 같은 세션을 다시 셈해 같은 자리에서 멈춘다. 모듈 독스트링과 티켓 10을 그 동작으로 고치고(단가표에 그 모델을 더한 뒤 다시 띄우면 중단으로 적힌다), 두 번 모두 멈추는 시험을 더했다.
- 표준 Major: 모듈 독스트링의 못 보는 것 넷(`.tmp`, 다른 이름의 프로세스, `which`로 풀기, 같은 뿌리의 러너 둘)을 시험 하나씩으로 고정했다. `pids_named`의 못 보는 것은 리눅스의 셋(링크로 띄운 이름, 스스로 바꾼 이름, 앞 15바이트)을 리눅스에서만 단언하는 시험으로 고정하고, 재지 않은 윈도 런처의 자식 문장은 지웠다.
- 표준 Major: 게이트를 돌지 못한 회차(`GateError`), 끄지 못하고 남긴 호출, `PriceError`의 멈춤에 시험이 없었다. 시험 셋을 더하고 앞의 둘은 변이(24·25번)로 빨강을 봤다.
- 명세 Minor: `plan_task`가 id를 주면 V > C에서도 멈추지 않았다. 티켓 노트대로 V > C를 id 갈래보다 먼저 보게 고치고, 시험과 변이(23번)를 더했다.
- 표준 Minor(Duplicated Code): 기록의 비용을 넣는 `replace` 두 곳을 `_spend`로 모았다.

남긴 것과 이유.
- 표준 Minor: 표지 `where N = run()`은 종료 코드 단언에서만 나와 고른 단언은 가리지만 까닭은 가리지 않는다. 프로브 README의 변이 절에 적었다.
- 표준 Minor: 함께 돌던 회차의 순서가 `hang` 초에 기대는 시험(인계·오염)이 부하가 큰 러너에서 뒤집힐 수 있다. 지금까지 어긋난 적이 없고, 어긋나면 기다림을 이벤트로 바꾼다.
- 명세 Minor: 준비 멈춤 시험이 함께 돌던 회차의 두 꼴을 함께 받는다. 끝까지 두는 것은 설정 멈춤 시험이 단언한다.
- 표준 smell(긴 `_run_task`, `s`/`w` 이름, `Plan`의 감싸기)과 Nit(가짜의 `fake-running` 표지가 끈 호출에서 남는다)은 판단 항목이라 두었다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장).
- "단가표(`tools/rerun_cost.py`)에 그 모델을 더한 뒤 다시 띄우면 중단으로 적힌다."
- "셋은 리눅스에서만 나고, 리눅스 CI 에서 시험이 고정한다."(`pids_named` 독스트링)
- "V > C인 기록이 있으면 id를 줬어도 멈춘다(판을 내린 러너)."

## 검증 (셀프 리뷰 반영 뒤, 커밋하지 않은 작업 트리, 기준 7496a830)

- `uv run ruff check .`, `uv run ruff format --check .`: 초록.
- `uv run python tools/run_checks.py`: 열 가지 모두 Passed(pytest 410.9초, web-verify 237.7초, run-hooks 64.0초, pyright 39.2초).
- 변이 표 `rerun_runner_mutations.toml` 25: 프로브 README 변이 절대로 모두 고른 표지까지 기대대로 빨갰다.
