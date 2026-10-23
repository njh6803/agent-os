# 2026-10-23 (41) 이어 가기와 상한 (model-rerun 08)

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/08-continue-and-caps.md
>
> 다음 작업: .scratch/model-rerun/issues/08-continue-and-caps.md. 06이 띄운 세션의 이어 가기와 끄기·상한을 더한다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 08-continue-and-caps)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/08-continue-and-caps.md
> 브랜치: feature/08-continue-and-caps
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-36-round-drive-record.md의 "다음"
> 이어받을 상태: PR #370 claude-review 셋째 회차(일지만 푸시한 회차)에서 뒤로 넘긴 일은 일지에 없고 여기와 PR 코멘트에만 있다. 08에서 함께 볼 것: tools/rerun_session.py가 800줄을 넘어 이어 가기를 더하기 전에 요약·세션 기록 읽기 쪽을 뗄지, launch가 덧붙인 파일을 다시 읽어 호출 번호를 세는 것을 RoundDir의 한 함수로 옮길지, call_record의 kill_skipped=False 고정값을 채워 없애기. 10에서 볼 것: round_record가 Elsewhere를 Spend의 부분으로 받을지와 claude_version 매개변수가 같은 이름의 함수를 가리는 것. _git·_git_env 사본 셋의 실패 모양(CloneError 대 TimeoutExpired·OSError·RuntimeError)은 07과 06이 모두 병합된 뒤 하나로 맞춘다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 05·07은 제목이 그 브랜치인 세션이 작업 중이라 이 묶음에서 뺐다
> 이번 요청 범위: PR과 병합까지

## 한 것

- `tools/rerun_continue.py`(새): 갈래 셋(같은 브랜치의 인계 지시문이면 새 세션, 결과 커밋이 B 뒤에 있으면 끝남, 그 밖이면 `--resume` 개입), 물으며 끝남(`ends_with_question`), 인계 지시문 옮기기(`handoff_directive`), 호출 앞의 끝(`before_call`: 셋째 개입, 다섯째 세션, $1 미만, 벽시계 4시간)과 호출 뒤의 끝(`call_end`: 시간, `error_max_budget_usd`, 측정 아님(호출)), 주입받는 막는 판정 `screen`(09의 자리)을 먼저 보는 고리 `run_sessions`. 예산은 회차 상한에서 세션마다 마지막 비용의 합을 뺀 값이고, 이어 부를 세션의 몫도 든다.
- `tools/proc_command_line.py`(새): pid 하나의 명령 줄을 낱말로 읽는다(리눅스 `/proc/<pid>/cmdline`, 윈도 PEB). `tools/hook_edit_during_commit.py`의 읽기를 옮긴 사본이다.
- `tools/rerun_session.py`: 끄기를 명령 줄에 그 호출의 세션 id가 있을 때만 나무째 하게 고쳤다(`_stop`·`_kill_tree`, 윈도 `taskkill /F /T`, POSIX `start_new_session`과 `os.killpg`). 끄지 않으면 `Drove.kill_skipped`. 출력을 닫은 뒤의 거두는 기다림을 마감 안으로 묶었다. `session_command`의 `resume`, `launch`가 세션 id·`resume`·첫 메시지를 받게 했다. `Continued`, `call_record`의 `kill_skipped`, `session_record`의 `runner_killed`는 실제로 끈 호출만 본다.
- `tools/rerun_round.py`: `RoundDir.append_session_id`가 덧붙이고 호출 차례를 돌려준다.
- `tools/hook_prompt_directive.py`: `_directive_branch`를 `directive_branch`로 공개했다. 훅 러너(`tools/run_hooks.py`)는 156건 모두 기대대로였다.
- 시험: `tests/tools/test_rerun_continue.py`(새, 32개), `tests/tools/test_proc_command_line.py`(새, 3개), `test_rerun_session.py`(이어 부르는 명령, 입출력이 없을 때와 거둘 시간 안에 끝나지 않을 때의 끄기, 거두는 기다림의 마감), `fake_claude.py`(pid, 세션 id를 실은 자식, 출력 닫기, 런처를 거치지 않는 `claude_direct`).
- 변이: 새 표 `rerun_continue_mutations.toml` 35개와 `rerun_session_mutations.toml` 27개가 모두 표지까지 기대대로 빨갰다. 결과와 표지를 고른 과정은 `.scratch/model-rerun/probes/README.md`의 변이 절이다.
- 티켓 08을 `done`으로, 09·10에 "08에서 넘어온 메모"를 더했다.

## 결정과 고친 것

- PR #370이 넘긴 셋. `tools/rerun_session.py`는 쪼개지 않고 이어 가기를 새 모듈에 두었다(그 파일은 828줄에서 906줄로 늘었다. 끄기 밖에 `Continued`와 `resume` 배선도 들었다). 호출 차례 세기는 `RoundDir.append_session_id`로 옮겼고, `kill_skipped` 고정값은 `Drove`에서 옮겨 채웠다. `round_record`의 08 몫 인자 다섯은 `Continued` 하나로 묶었다.
- 출력을 닫은 뒤의 거두는 기다림(`REAP_TIMEOUT` 60초)이 호출의 마감을 넘을 수 있었다. 거두는 기다림을 남은 마감으로 줄이고, 마감이 먼저 오면 시간을 넘긴 호출로 적는다. 시험은 결과 줄이 오면 시계를 마감 2초 전으로 뛰게 해 부하와 상관없이 그 갈래를 밟는다.
- 윈도의 가상 환경 `python.exe`는 런처라 자식이 출력을 닫아도 런처가 끝날 때까지 EOF가 오지 않았다(커밋하지 않은 스크래치 탐침으로 손으로 봤다: 런처 8.09초, 기본 인터프리터 0.03초). 출력을 닫는 시험은 `claude_direct()`로 기본 인터프리터를 띄운다.
- 변이 "인계에 새 세션 id 를 받지 않는다"가 노린 단언보다 앞의 끝 단언에서 빨개져, 시험에서 둘째 호출의 세션 id 단언을 앞으로 옮겼다.
- 남은 경합은 기록만 했다. 명령 줄을 읽기 전에 프로세스가 스스로 끝나면 `kill_skipped`가 선다(10의 메모).

## 실수

- 중간 문장을 영어로 써 훅이 알렸다. 그 뒤로 한국어로 썼다.
- 변이 도구가 도는 동안 같은 체크아웃의 09 티켓을 고쳐 `hook_edit_during_mutate`가 알렸다(변이 대상 파일은 아니었다). 그 뒤로 변이가 도는 동안에는 체크아웃 밖에서만 일했다.
- `rerun_continue.py` 첫 판이 없는 이름(`launch_call`)을 불렀고, 매개변수 `new_session_id`가 같은 이름의 함수를 가렸다. 커밋 전에 보고 `launch`와 `make_session_id`로 고쳤다.
- 시험에서 `subprocess.Popen`을 바꾼 대역이 `_kill_tree`의 `taskkill`까지 받아 TypeError가 났다. 대역을 가짜를 띄운 호출만 세는 `_popen_double`로 모았다.
- 중간 문장을 다시 영어로 써 훅이 두 번 더 알렸다(ruff 명령 직전, 인계 절차의 도구 불러오기 직전). 첫 알림 뒤에도 되풀이했다.

## 검증 (셀프 리뷰 전, 커밋하지 않은 작업 트리)

- 변이: `rerun_continue_mutations.toml` 35개, `rerun_session_mutations.toml` 27개가 모두 표지까지 기대대로였다.
- `uv run python tools/run_hooks.py`: 훅 페이로드 156건, 어긋남 0건.
- `uv run ruff check .`, `uv run ruff format --check .`(1005 files): 초록.
- `uv run python tools/run_checks.py`: 인계로 멈췄다. 멈추기 전에 끝난 것은 check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks이고 모두 Passed였다. pytest와 web은 끝나기 전에 멈췄으니 새 세션이 다시 돈다.

## 인계

- 이 세션의 지금 제목: `feature/08-continue-and-caps`.
- 인계 경계: `셀프 리뷰 직전`. 세션 컨텍스트가 문턱(20만)을 넘은 채 `/code-review`를 부른 직후 `hook_handoff`가 들어왔다. 그 리뷰의 단계는 밟지 않았다.
- 티켓 08의 체크박스 가운데 "검증 명령이 모두 초록이다"만 남았다.
- 주 체크아웃은 main이고 `origin/main`(893e0fe8)과 같다(`git worktree list`, `git fetch origin` 뒤 `git rev-parse origin/main`). 이 브랜치에 열린 PR은 없다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/08-continue-and-caps.md. 06이 띄운 세션의 이어 가기와 끄기·상한을 더한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/08-continue-and-caps.md
브랜치: feature/08-continue-and-caps
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-41-continue-and-caps.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-23-41-continue-and-caps.md. 리뷰 범위는 origin/main 이후의 커밋하지 않은 변경과 미추적 파일 전체이고 명세는 티켓 08과 .scratch/model-rerun/spec.md다. tools/run_checks.py는 인계로 pytest·web이 끝나기 전에 멈췄으니 반영 뒤 다시 돈다. 변이 표 둘(rerun_continue 35개, rerun_session 27개)은 셀프 리뷰 전 판으로 모두 표지까지 기대대로였고, 반영이 그 시험이나 대상 코드를 바꾸면 해당 변이를 다시 돈다. 일지 41은 커밋하지 않았으니 이어 쓰고 함께 커밋한다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/08-continue-and-caps (인계함)`으로 바꿨고, 백그라운드 검사(run_checks)를 멈췄고, 워크트리 잠금을 풀었다.
- open-session을 부른다 2026-10-23T09:25:03Z

## 이어받은 세션 (2026-10-23, 셀프 리뷰부터)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/08-continue-and-caps.md
>
> (지시문은 위 인계 절의 "낸 지시문"과 같다)

- `git worktree list`에서 `feature/08-continue-and-caps`가 `.claude/worktrees/08-continue-and-caps`에 있어 `EnterWorktree(path)`로 들어왔다. 커밋하지 않은 변경 11개 파일과 미추적 6개가 그대로였다.

## 셀프 리뷰

범위: base `893e0fe8`, 바뀐 파일 11개, 커밋 0개, 미추적 6개(`tools/rerun_continue.py`, `tools/proc_command_line.py`, `tests/tools/test_rerun_continue.py`, `tests/tools/test_proc_command_line.py`, `.scratch/model-rerun/probes/rerun_continue_mutations.toml`, 이 일지).

### 표준 축 (sonnet·high)

Critical·Major 없음. Minor 이하:

1. Minor CQS: `RoundDir.append_session_id`가 덧붙이고 차례를 돌려준다. `_stop`이 끄면서 끈 여부를 돌려준다.
2. Minor 불리언 플래그: `launch(..., resume)`, `session_command(..., *, resume=False)`, `Drove`의 `timed_out`·`killed`·`kill_skipped` 세 칸.
3. Minor: `drive` 독스트링의 Ctrl+C·`KeyboardInterrupt`에서 끈다는 길(`except BaseException`)을 거는 시험이 없다.
4. Minor: "끄기 몫만 828줄에서 906줄"은 거짓이다(`Continued`와 `resume` 배선도 들었다). 일지와 티켓 08.
5. Minor: `rerun_session.py` 독스트링의 "마감 뒤에 더 쓰는 시간은 거둠과 배출"에 `taskkill`(`KILL_TIMEOUT`)이 빠졌다.
6. Minor: `proc_command_line.py`의 "다른 사용자의 프로세스(열지 못한다)"는 리눅스 `/proc/<pid>/cmdline`에는 틀리다(훅 사본의 `cwd` readlink 때문에 붙은 말).
7. Minor: `handoff_directive`가 `다음 작업:` 앞의 산문은 떼지만, 머리 줄이 없을 때 산문과 코드 펜스까지 싣는다. 시험이 없다.
8. Minor: 8.09초·0.03초를 "스크래치 탐침으로 손으로 쟀다"고 적었다. 커밋한 프로브가 아니면 "손으로 봤다"로 쓴다(`docs/agents/issue-tracker.md`).
9. Nit: 티켓 08의 "갈래 셋으로 잇고"는 같은 티켓의 "갈래 셋으로 가지 않는다"(갈래 3)와 읽기가 갈린다.
10. Minor: 티켓 08 "06에서 넘어온 메모"의 낡은 문장(`launch(ticket=…, directive_text=…)`, `--resume` 호출이 아직 없다, 대신 넣은 세션을 이 티켓이 채운다).
11. Minor 냄새 Duplicated Code: `proc_command_line.py`가 훅의 읽기 약 90줄을 옮긴 사본이고, 빈 낱말을 지키는 까닭이 빠졌다.
12. Nit 냄새: `run_sessions`가 예산 셈·세는 수·메시지 짓기를 한 함수에 섞는다.
13. Minor: `call_end`가 `kill_skipped`를 보지 않아, 끄지 못한 호출이 결과를 냈으면 살아 있는 프로세스의 세션을 `--resume`할 수 있다.

### 명세 축 (주 세션 모델 상속)

Critical·Major 없음. Minor 셋, Nit 셋:

1. Minor: 출력을 닫고 거두는 기다림 안에 끝나지 않아 끈 호출(`killed` 참, `timed_out` 거짓)은 결과 이벤트가 없으면 측정 아님(호출)이 되고, 같은 세션에 `runner_killed`도 선다. 명세 "결과 이벤트 없이 끝난 호출(러너가 끈 것과 한도 표지가 든 것은 뺀다)"와 티켓의 "이 표시로 끈 호출과 결과 이벤트 없이 죽은 호출(측정 아님(호출))을 가른다"가 어긋난다. 이 갈래의 시험이 없다.
2. Minor: 결과 글 앞쪽 설명에 `다음 작업:`·`이번 요청 범위:` 줄이 있고 진짜 지시문이 뒤에 있으면, `next_kind`는 인계를 내는데 `handoff_directive`는 앞의 두 줄만 옮긴다.
3. Minor: `runner_killed`가 참인 기록을 단언하는 시험이 없다.
4. Nit: "끄기 몫만 늘었다"는 끄기 밖의 것도 들었다. 같은 줄의 PR #370 회차 표기.
5. Nit: `rerun_session.py` 독스트링의 "마감 뒤에 더 쓰는 시간"에 `KILL_TIMEOUT`이 빠졌다.
6. Nit: Status가 `done`인데 "검증 명령이 모두 초록이다"가 체크되지 않았다.

요약: 표준 축 13건(Critical·Major 0, 가장 무거운 것은 끄지 못한 호출 뒤의 `--resume`), 명세 축 6건(Critical·Major 0, 가장 무거운 것은 거둠 제한으로 끈 호출의 끝과 표시).

### 판정

고친다:
- 표준 13: 거두는 기다림이 끝났는데 끄지 못한 호출(살아 있는 프로세스)은 결과가 있어도 회차를 이어 가지 않고 측정 아님(호출)으로 끝낸다. 이어 가면 같은 세션을 `--resume`하거나 그 클론에서 새 세션을 연다.
- 명세 1과 표준 2의 `Drove` 몫: 불리언 칸 셋을 열거 하나(`Stop`: 스스로 끝남, 마감에 끊음, 마감인데 끄지 않음, 출력을 닫고 멈춰 끔, 그런데 끄지 않음)로 바꾼다. `runner_killed`는 마감에 끊은 호출에만 선다. 출력을 닫은 뒤 거두려고 끈 호출은 출력이 이미 끝났으므로 명세가 측정 아님(호출)에서 빼는 "러너가 끈 것"(마감에 끊은 호출)이 아니다. 결과 이벤트가 없으면 측정 아님(호출)이다.
- 표준 2의 `resume`: 여는 방법 열거(`Opening`)로 바꾼다.
- 표준 1: `append_session_id`는 덧붙이기만 하고 차례는 따로 센다. `_stop`은 명령 줄 확인(질의)과 끄기(명령)로 나눈다.
- 명세 2와 표준 7: `handoff_directive`가 그 브랜치의 지시문인 덩이를 뒤에서부터 고른다.
- 명세 3, 표준 3: `runner_killed`가 참인 기록과 `KeyboardInterrupt`에서 끄는 길을 시험으로 고정한다.
- 표준 4·5·6·8·9·10, 명세 4·5: 문서의 사실을 고친다.
- 명세 6: 검증이 초록이면 체크박스를 채운다.

남긴다:
- 표준 11(명령 줄 읽기의 사본): 훅은 표준 라이브러리만 쓰는 단독 스크립트라 공유 모듈을 import하지 못한다(`.claude/rules/tools.md`). PEB 를 읽는 다른 사본인 `tools/tidy_checkouts.py`는 다른 칸(작업 폴더, 환경)을 읽는 지우는 도구라 이 티켓에서 고치지 않는다. 훅 독스트링에 되가리킴만 더한다.
- 표준 12(`run_sessions`의 크기, Nit): 판단 항목이고 한 함수 안의 고리라 그대로 둔다.

### 반영

고친 것:
- 멈춘 꼴: `Drove`의 `timed_out`·`killed`·`kill_skipped`를 `Stop` 하나로 바꿨다(`EXITED`, `DEADLINE_KILLED`, `DEADLINE_LEFT`, `HUNG_KILLED`, `HUNG_LEFT`). 묶음 `TIMED_OUT`(마감에 닿은 둘)과 `LEFT_RUNNING`(끄지 않은 둘)을 두고, `_read_process`는 (시간을 넘겼는가, 껐는가)로 `_STOPS` 표에서 꼴을 고른다. `call_end`는 `TIMED_OUT`만 상한(시간)으로 끊고, `Stop.HUNG_LEFT`는 결과가 있어도 측정 아님(호출)으로 끝낸다. `runner_killed`는 `Stop.DEADLINE_KILLED`에만 서고 `kill_skipped`는 `LEFT_RUNNING`일 때 선다.
- 여는 꼴: `resume` 불리언을 `Opening`(`NEW`=`--session-id`, `RESUME`=`--resume`)으로 바꿨다. `run_sessions`는 호출 종류마다 `_OPENINGS` 표에서 고른다. 비교식(`kind == CALL_INTERVENTION`)으로 넘기던 판은 pyright가 고리 안의 좁힘으로 `reportUnnecessaryComparison`을 냈다.
- CQS: `RoundDir.append_session_id`는 덧붙이기만 하고 `RoundDir.call_count`가 센다. `_stop`을 `_ours`(질의)와 `_kill`(명령)로 나눴다. `drive`의 예외 갈래는 자식이 이미 끝났으면 명령 줄을 읽지 않는다(`process.poll() is None and ours()`).
- 덩이 고르기: `handoff_directive(text, branch)`가 덩이를 뒤에서부터 보고 그 덩이만으로 `directive_branch`가 `branch`인 첫 덩이를 옮긴다. 그런 덩이가 없으면 글 전체다.
- 시험: `KeyboardInterrupt`로 끊긴 러너가 자식을 끄는 시험, 출력을 닫고 멈춘 호출의 명령 줄이 다르면 끄지 않고 `Stop.HUNG_LEFT`로 남기는 시험(`test_rerun_session.py`), 덩이 고르기 셋(앞쪽 설명, 다른 브랜치의 덩이, 같은 브랜치의 덩이 둘), 멈춰 끈 호출과 끄지 못한 호출의 끝, 멈춘 꼴 다섯마다의 `runner_killed`·`kill_skipped`(`test_rerun_continue.py`), 마감에 끈 resume 호출의 세션에 `runner_killed`가 서는 단언, 끝났지만 거두지 않은 자식의 명령 줄이 None 인 시험(`test_proc_command_line.py`), `call_count`(`test_rerun_round.py`)를 더했다.
- 변이 표: continue 표는 원문이 어긋난 13을 고친 코드에 맞추고 새 변이 10을 더해 45가 됐다(덩이 고르기 셋, 끄지 못한 호출 뒤 잇기, 멈춰 끈 호출을 시간으로 보기, 끄지 않은 멈춘 호출을 끈 것으로 적기, 러너가 끊김, 세션의 끈 표시 둘, 멈춰 남긴 호출의 호출 칸). session 표는 원문 둘과 표지 하나를 고쳤다.
- 문서: 끄기 몫의 줄 수 문장, `KILL_TIMEOUT`, 리눅스 `/proc`의 다른 사용자, "손으로 봤다", 갈래 셋의 읽기, 06 메모의 낡은 문장, PR #370 회차 표기를 고쳤다(표준 4·5·6·8·9·10, 명세 4·5). 티켓 09·10의 08 메모를 `_ours`·`_kill`·`Stop`으로 고쳤다. 훅 `tools/hook_edit_during_commit.py`의 독스트링에 사본 `tools/proc_command_line.py`를 가리키는 줄을 더했다.

PR 직전 `bug-perf-review`에 밀 주장으로 넘길 문장(반영으로 새로 썼다):
1. 티켓 08: "호출이 멈춘 꼴은 `tools/rerun_session.py`의 `Stop` 다섯이다. 스스로 끝남, 마감에 닿아 끔·끄지 않음, 출력을 닫고도 거두는 기다림(`REAP_TIMEOUT`) 안에 끝나지 않아 끔·끄지 않음이다. 거두는 기다림도 호출의 마감을 넘지 않고, 마감이 먼저 오면 마감에 닿은 호출이다."
2. 티켓 08: "출력을 닫은 뒤 거두려고 끈 호출은 출력이 이미 끝나 끄기가 결과 이벤트를 자르지 않았으므로, 결과 이벤트가 있으면 결과 글로 다음 호출을 고르고(갈래 1·2·3) 없으면 측정 아님(호출)이다."
3. 티켓 08: "출력을 닫고 멈췄는데 끄지 못한 호출(명령 줄이 맞지 않거나 읽지 못했다)은 결과 이벤트가 있어도 회차를 이어 가지 않고 측정 아님(호출)으로 끝낸다. 이어 가면 살아 있는 프로세스 곁에서 같은 세션을 `--resume`하거나 같은 클론에 새 세션을 연다."
4. 티켓 08: "인계 지시문은 결과 글의 덩이(`다음 작업:` 줄부터 그 뒤 첫 `이번 요청 범위:` 줄까지) 가운데 그 덩이만으로 `directive_branch`가 회차의 브랜치인 마지막 덩이를 옮긴다(`handoff_directive`). 그런 덩이가 없으면 글 전체다."
5. 티켓 10: "명령 줄을 읽기 전에 프로세스가 스스로 끝나도 끄지 않은 꼴이 된다(그 사이의 경합, `tools/rerun_session.py`의 `_ours`)."
6. 티켓 10: "호출의 시간 제한은 벽시계의 남은 초이고, 마감 뒤에 더 쓰는 시간은 끄기(윈도 `taskkill` 한 번이 최대 `KILL_TIMEOUT` 60초)와 끈 뒤 거두기(최대 `REAP_TIMEOUT` 60초), 남은 줄 배출(최대 `DRAIN_TIMEOUT` 10초)이다."
7. `tools/rerun_session.py`의 `session_record`: "출력을 닫고 멈춰 끈 호출(`Stop.HUNG_KILLED`)은 세우지 않는다. 출력이 이미 끝나 끄기가 결과 이벤트를 자르지 않았고, 결과 이벤트가 없으면 그 회차는 측정 아님(호출)이다."
8. `tools/rerun_session.py`의 `drive`: "러너가 끊길 때(`KeyboardInterrupt`도) 이 함수가 같은 규칙으로 끈다."
9. `tools/proc_command_line.py`: "못 보는 것: … 윈도에서 다른 사용자의 프로세스(열지 못한다), 끝났지만 거두지 않은 좀비(리눅스는 명령 줄이 비었다). 모두 None 이다. 리눅스의 `/proc/<pid>/cmdline`은 `hidepid`로 숨기지 않았으면 다른 사용자의 것도 읽힌다."
10. 변이 표 머리: "셀프 리뷰 반영에서 고치거나 더한 변이(멈춘 꼴 `Stop`, 덩이 고르기, 러너가 끊김)는 고른 단언의 꼴에서 표지를 고른 뒤 그 변이를 돌려 표지가 출력에 있는지 봤다."

남긴 것: 위 판정의 "남긴다" 둘(표준 11, 12) 그대로다.

다시 돌린 명령과 결과:
- 새 시험 셋(`call_count`, 같은 브랜치의 덩이 둘, 출력을 닫고 멈춘 호출의 `Stop.HUNG_LEFT`)을 이름으로 골라 돌려 초록이었다.
- `PYTHONUTF8=1 uv run python tools/mutate.py --check <두 표>`: continue 45, session 27 모두 원문이 한 번씩 있었다(변이를 돌린 뒤에도 같다).
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_continue_mutations.toml 4 6 7 8 14 16 17 18 19 22 24 25 29 30 32 33 34 35 36 37 38 39 40 41 42`: 바꾸거나 더한 스물다섯이 모두 고른 표지까지 기대대로 빨갰다(`변이 25 모두 기대대로`).
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_session_mutations.toml --since origin/main`: 셋 모두 기대대로(`변이 3 모두 기대대로`).
- 그 실행 동안 이 PC 는 다른 세션들로 CPU 가 100%였고(`Get-Counter`로 두 번 잰 값을 손으로 봤다, python 프로세스 80개) 기준선 `그_밖이면_resume`이 151.66초, `같은_브랜치_지시문이면`이 53.03초였다. 시험이 느려진 까닭을 부하로 읽었고, 부하가 없을 때 그 시험만 다시 재지는 않았다.
- 두 표 전체는 시험을 고쳤으므로 PR 직전 리뷰를 반영해 커밋한 뒤 다시 돈다(`tools/mutate.py` 독스트링).
- `uv run ruff check .`, `uv run ruff format --check .`: 초록.
- `uv run python tools/run_checks.py`: 검사 열 모두 Passed(pytest 421.6초, web-verify 262.0초, Skipped 없음). 티켓 08의 "검증 명령이 모두 초록이다"를 채웠다.
