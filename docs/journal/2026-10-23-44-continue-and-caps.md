# 2026-10-23 (44) 이어 가기와 상한 (model-rerun 08)

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
읽을 것: docs/journal/2026-10-23-44-continue-and-caps.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-23-44-continue-and-caps.md. 리뷰 범위는 origin/main 이후의 커밋하지 않은 변경과 미추적 파일 전체이고 명세는 티켓 08과 .scratch/model-rerun/spec.md다. tools/run_checks.py는 인계로 pytest·web이 끝나기 전에 멈췄으니 반영 뒤 다시 돈다. 변이 표 둘(rerun_continue 35개, rerun_session 27개)은 셀프 리뷰 전 판으로 모두 표지까지 기대대로였고, 반영이 그 시험이나 대상 코드를 바꾸면 해당 변이를 다시 돈다. 일지 44는 커밋하지 않았으니 이어 쓰고 함께 커밋한다
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
5. Minor: `rerun_session.py` 독스트링에서 마감 뒤에 더 쓰는 시간을 적은 문장이 거둠과 배출만 들고 `taskkill`(`KILL_TIMEOUT`)을 빠뜨렸다.
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

## 커밋 (셀프 리뷰 반영 뒤)

- 커밋 직전 `uv run python tools/sibling_overlap.py`가 1로 끝났다. origin/main 에 일지 2026-10-23-40 이 먼저 들어가 이 일지(39)가 이름순으로 앞이 되어, `--move`로 39를 41로 옮겼다(파일 이름, 머리 줄, 티켓 08과 continue 변이 표와 이 일지 안의 인용). 도구가 옮기지 않는 줄인 꼴 하나(위 인계 절 지시문의 "일지 39는")는 손으로 고쳤다.
- origin/main 이 893e0fe8 에서 8a026f3 으로 움직였다. `git diff --name-only HEAD...origin/main`의 파일은 web-widget 의 명세·티켓·ADR·일지 40과 `CONTEXT.md`·`.scratch/plan.md`·`.scratch/retro-queue.md`이고, 이 브랜치가 고치거나 이름으로 든 파일과 겹치지 않았다. 06의 PR도 `plan.md`를 고치지 않아(기능을 닫는 티켓이 아니다) 이 PR도 건드리지 않는다.
- f614f00c `feat: 회차의 세션을 갈래 셋으로 잇고 상한과 끄기를 더한다 (model-rerun 08)`. pre-commit 이 모두 지났다(카나리아 명세와 헌법 판은 해당 파일이 없어 Skipped). 인용 대조가 막지 않는 경고 둘을 냈다. 티켓 10의 76행 메모(같은 티켓 37행 체크박스의 문구를 끝을 바꿔 따옴표로 옮겼다)와, 이 일지 96행 셀프 리뷰 표준 축 5(리뷰어가 고치기 전의 독스트링을 줄여 옮긴 말을 따옴표로 적었다)다. 이 커밋에서는 고치지 않고 넘겼다(아래 PR 직전 절에서 고쳤다).
- PR 직전 리뷰의 길: `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 CLI 는 돌지 못한다. 대체 둘(`/security-review`, `bug-perf-review`)을 돈다.

## 인계 (커밋 뒤)

- 이 세션의 지금 제목: `feature/08-continue-and-caps`.
- 인계 경계: `커밋 뒤`. 세션 컨텍스트가 문턱(20만)을 넘은 채 f614f00c 커밋을 친 직후 `hook_handoff`가 들어왔다. 인계하지 않는 다섯 때에 들지 않는다. 커밋은 성공했고, 범위는 PR과 병합까지이며, 이 세션이 이어받은 경계는 `셀프 리뷰 직전`이었고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다.
- 커밋은 푸시하지 않았고 이 브랜치에 열린 PR 은 없다. 주 체크아웃은 main 이고 origin/main(8a026f3)과 같다(`git worktree list --porcelain`).
- `tools/model_sweep.py feature/08-continue-and-caps`는 `Opus 5.5 / xhigh`였다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/08-continue-and-caps.md. 06이 띄운 세션의 이어 가기와 끄기·상한을 더한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/08-continue-and-caps.md
브랜치: feature/08-continue-and-caps
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-44-continue-and-caps.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 f614f00c로 커밋했고 푸시하지 않았으며 열린 PR은 없다. 남은 단계는 PR 직전 리뷰부터다. docs/journal/2026-10-23-44-continue-and-caps.md. CodeRabbit CLI는 좌석이 없어(coderabbit auth status의 Seat: not assigned) 대체 둘을 나란히 돈다. origin/main을 합친 뒤 /security-review를 돌리고, bug-perf-review 서브에이전트의 브리프에는 이 일지 "### 반영"의 밀 주장 열 개를 나열한다. 그 반영을 커밋한 뒤 변이 표 둘(rerun_continue 45개, rerun_session 27개)의 전체를 다시 돈다(시험을 고쳤으므로, tools/mutate.py 독스트링). 커밋의 인용 대조 경고 둘(티켓 10의 76행, 이 일지 "### 표준 축"의 5)은 막지 않는 경고라 넘겼으니 원문과 대 본다. 이 일지는 이어 쓰고 다음 커밋에 싣는다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/08-continue-and-caps (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업 셋(변이 묶음, run_checks, 커밋)은 모두 끝나 있어 멈출 것이 없었다. `git worktree unlock`은 `is not locked`로 끝나 넘어갔다.
- open-session을 부른다 2026-10-23T10:52:49Z

## 이어받은 세션 (2026-10-23, PR 직전 리뷰부터)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/08-continue-and-caps.md
>
> (지시문은 위 "인계 (커밋 뒤)" 절의 "낸 지시문"과 같다)

- `git worktree list`에서 `feature/08-continue-and-caps`가 `.claude/worktrees/08-continue-and-caps`에 있어 `EnterWorktree(path)`로 들어왔다. HEAD 는 f614f00c 이고 커밋하지 않은 변경은 이 일지 하나였다.
- `git merge origin/main`으로 8a026f3c 를 합쳤다(2746ac57). 충돌은 없었다.
- 인용 대조 경고 둘을 원문과 대 봤다. 티켓 10의 76행은 같은 티켓 37행 체크박스의 "훑어"를 "훑는"으로 바꿔 옮긴 인용이었고, 이 일지 96행은 커밋하지 않은 판의 독스트링(지금은 `KILL_TIMEOUT`이 든 문장으로 바뀌었다)을 리뷰어가 줄여 옮긴 말이었다. 둘 다 따옴표를 떼고 서술로 고쳤고, 그 둘을 다시 적은 위 커밋 절의 줄도 같이 고쳤다. `tools/check_quotes.py`가 두 파일에서 경고 없음이었다.

## PR 직전 리뷰

CodeRabbit CLI 는 좌석이 없어(`Seat: not assigned`) 대체 둘을 나란히 돌렸다. 기준은 합친 뒤의 merge-base `8a026f3c`다.

- `/security-review`: 식별 서브태스크가 후보 0건을 냈다(확신 7 이상 없음). 그래서 오탐 거르기 서브태스크는 띄울 것이 없었다. 하위 프로세스는 모두 리스트 인자이고, 결과 글은 다음 세션의 stdin 메시지로만 가며 명령 인자·경로·git 인자에 들지 않는다. 기준 아래로 남긴 관찰은 `taskkill`을 이름으로 띄우는 것(하드닝, `tools/mutate.py`에도 같은 모양)이다.
- `bug-perf-review`(sonnet, 호출 37): 유효 1(Minor), 보류 0, 오탐 4. 밀 주장 열 개는 모두 근거와 맞았다.
  - 유효(Minor): 마감에 닿아 끈 호출(`Stop.DEADLINE_KILLED`)은 결과 이벤트가 나기 전에 끊겨 비용을 모른다는 문장이 한 길에서 거짓이다. 결과 이벤트를 내고 출력을 닫은 뒤 거두는 기다림 중에 마감이 오면(마감까지 60초 미만) `reap < REAP_TIMEOUT`이라 마감에 닿은 호출이 되는데, 결과 이벤트와 비용이 있다. 시험 `test_출력을_닫은_뒤_거두는_기다림도_호출의_마감을_넘지_않는다`가 그 둘을 함께 단언한다. 티켓 10의 체크박스는 `runner_killed`로 대신 넣을 세션을 고르라고 하므로, 그대로 따르면 아는 비용을 덮어쓴다.
  - 판정: 코드의 분류(마감이 먼저 오면 마감에 닿은 호출, 회차는 상한(시간))는 밀 주장 1대로 의도한 것이라 두고, 문장을 고쳤다. `session_record`와 `tools/rerun_continue.py`의 독스트링, 티켓 08 "구현에서 정한 것"에 한 항목, 티켓 10 "08에서 넘어온 메모"에 한 항목(대신 넣을지는 끈 호출의 `Call.results`가 빈지로 가른다)과 한 낱말(대개)이다. 리뷰어는 세션의 `cost_usd`가 빈지로 가르자고 제안했으나, `--resume`으로 이어 부른 호출이 끊긴 세션은 앞 호출의 값이 남아 그 기준으로는 대신 넣지 않으므로 끈 호출 자신의 결과 이벤트로 적었다(시간의 끄기는 회차를 끝내므로 끈 호출은 그 세션의 마지막 호출이다).
  - 남긴 판단: 그 길의 회차는 결과 글이 끝남(갈래 2)이어도 상한(시간)으로 적힌다. 세션은 일을 마쳤고 프로세스의 종료만 멈춘 경우다. 마감이 먼저 오면 마감에 닿은 호출이라는 설계를 따른 것이고, 마감까지 60초 미만에서만 나는 드문 길이라 바꾸지 않았다.
  - 오탐 넷: `.cmd` 심의 명령 줄(이 PC 의 `claude`는 `claude.exe`), POSIX `start_new_session`의 고아(운영 러너는 윈도, 고아는 10의 몫), 일지 22행의 옛 `Drove.kill_skipped`(뒤의 반영 절이 대체), `_directive_branch` 옛 이름의 잔존(명세·티켓의 이름 바꾸기 설명뿐).
- 반영 뒤 `tools/mutate.py --check`가 두 표(continue 45, session 27)에서 원문이 모두 한 번씩이었다(고친 것은 독스트링뿐이다).

## 커밋 (PR 직전 리뷰 반영 뒤)

- 커밋 직전 `tools/sibling_overlap.py`가 1로 끝났다. origin/main 이 062e9734(model-rerun 05, #371)로 움직여 일지 2026-10-23-43 이 먼저 들어갔고, 이 일지(41)가 이름순으로 앞이 됐다. `git merge origin/main`을 다시 쳤고 `.scratch/model-rerun/probes/README.md`의 표 한 곳이 충돌했다. main 쪽은 행 셋(`branches.json`, `candidates.md`, `rerun_select_mutations.toml`)을 더했고, 이 브랜치는 `rerun_session` 행에서 "첫 줄의 연 저장소" 항목을 `rerun_continue` 행으로 옮기고 그 행을 더했다. 두 `rerun_session` 행이 그 한 항목만 다른 것을 낱말 diff 로 본 뒤, main 의 새 행 셋 뒤에 이 브랜치의 두 행을 두어 풀었다(세션 스크래치의 커밋하지 않은 스크립트, `tools/check_md_tables.py` 초록). main 이 고친 명세 줄은 숨은 시험 가르기(티켓 02·05)의 한 줄이라 08과 상관없었다.
- `--move`로 41을 44로 옮겼다(파일 이름, 머리 줄, 티켓 08·10과 continue 변이 표와 이 일지 안의 인용). 도구가 옮기지 않는 꼴 하나(첫 인계 절 지시문의 "일지 41은")는 손으로 고쳤다.
- 33785252 `docs: 마감에 끈 호출의 결과 이벤트 문장을 고치고 main 을 합친다 (model-rerun 08)`. pre-commit 이 합치는 중의 커밋에서 충돌 파일만 본다고 알려(`Checking merge-conflict files only`) ruff 둘을 손으로 다시 쳐 초록이었다. 러너(`parallel-checks`)는 모두 Passed(pytest 381.9초, web-verify 251.9초)였고, Skipped 는 해당 파일이 없는 카나리아 명세와 헌법 판 둘이다. 이 커밋에서 인계 계기(`커밋 뒤`)가 들어왔지만 이 세션의 지시문이 `인계: 커밋 뒤`로 시작해(넘겨받은 경계에 다시 왔다) next-session "인계할 때" 1대로 넘기지 않았다.
- 변이 표 둘의 전체를 33785252 에서 차례로 돌렸다(두 표가 `tools/rerun_session.py`를 함께 바꾸므로 나란히 돌리지 않았다). `rerun_continue_mutations.toml`은 `변이 45 모두 기대대로`, `rerun_session_mutations.toml`은 `변이 27 모두 기대대로`였고 두 번 다 끝난 뒤 작업 트리가 깨끗했다. 프로브 README 의 변이 절에 적었다.
- 3c4623c8 `docs: 리뷰 반영 뒤 변이 표 둘의 전체 실행을 적는다 (model-rerun 08)`. pre-commit 이 모두 지났다(`.py`가 없어 ruff 둘, 해당 파일이 없어 카나리아 명세와 헌법 판이 Skipped). 이 커밋에서도 `커밋 뒤` 인계 계기가 들어왔고 같은 까닭으로 넘기지 않았다.

## PR

- 열기 전 `git fetch origin main` 뒤 `git log HEAD..origin/main`이 비어 rebase 할 것이 없었다. 커밋 넷(f614f00c, 병합 2746ac57, 33785252, 3c4623c8)을 `git push -u origin feature/08-continue-and-caps`로 올리고 `gh pr create`로 PR #374 를 열었다. 본문은 템플릿을 채웠고, PR 직전 리뷰의 결과와 변이 표 둘의 전체 실행을 체크리스트와 확인 방법에 적었다.

## 인계 (PR 연 뒤)

- 이 세션의 지금 제목: `feature/08-continue-and-caps`.
- 인계 경계: `PR 연 뒤`. 세션 컨텍스트가 문턱(20만)을 넘은 채(약 31.8만) `gh pr create`가 성공한 직후 `hook_handoff`와 `hook_pr_next_session`이 함께 들어왔고 인계 줄을 따랐다. 인계하지 않는 다섯 때에 들지 않는다. PR 은 열렸고, 범위는 PR과 병합까지이며, 이 세션이 이어받은 경계는 `커밋 뒤`였고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다.
- PR #374 는 `OPEN`이고 아직 `@coderabbitai review` 코멘트를 남기지 않았으며 CI 대기(`tools/wait_ci.py`)도 띄우지 않았다. 봇 회차는 새 세션이 처음부터 한다.
- 이 인계 절은 커밋하지 않았다. 병합 전 `headRefOid` 대조를 지나려면 새 세션이 이 일지를 이어 쓰고 봇 회차의 커밋에 실어 푸시한다.
- `tools/model_sweep.py feature/08-continue-and-caps`는 `Opus 5.5 / xhigh`였다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/08-continue-and-caps.md. 06이 띄운 세션의 이어 가기와 끄기·상한을 더한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/08-continue-and-caps.md
브랜치: feature/08-continue-and-caps
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-44-continue-and-caps.md
이어받을 상태: 인계: PR 연 뒤. PR #374를 열고 푸시까지 했으나 @coderabbitai review 코멘트와 CI 대기는 아직이다. next-session 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. docs/journal/2026-10-23-44-continue-and-caps.md. 이 일지의 인계 절은 커밋하지 않았으니 이어 쓰고 봇 회차의 커밋에 실어 병합 전에 푸시한다. PR #372(티켓 07)가 같은 파일 넷(티켓 10, 프로브 README, tools/rerun_round.py와 그 시험)을 고쳐 나중에 병합하는 쪽이 글자 충돌을 푼다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/08-continue-and-caps (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업(리뷰 서브에이전트 둘, 커밋 둘, 변이 실행 둘)은 모두 끝나 있어 멈출 것이 없었다. `git worktree unlock`은 `is not locked`로 끝나 넘어갔다.
- open-session을 부른다 2026-10-23T11:48:27Z

## 이어받은 세션 (2026-10-23, 봇 회차부터)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/08-continue-and-caps.md
>
> (지시문은 위 "인계 (PR 연 뒤)" 절의 "낸 지시문"과 같다)

- 제목을 `feature/08-continue-and-caps`로 바꾸고, `git worktree list`에서 그 브랜치가 `.claude/worktrees/08-continue-and-caps`에 있어 `EnterWorktree(path)`로 들어왔다. HEAD 는 3c4623c8 로 PR 의 `headRefOid`와 같았고, 커밋하지 않은 변경은 이 일지 하나였다.
- `@coderabbitai review` 코멘트를 남기고 `gh pr checks`를 한 번 읽었다. claude-review·e2e·web·ticket 은 통과, python·visual 은 pending 이었고, CodeRabbit 줄은 코멘트 전의 `Review skipped: manual review required for this OSS repository`였다. `tools/wait_ci.py 374`를 백그라운드로 띄웠다.

## 봇 첫 회차

- 대기의 끝 줄(3c4623c8): `끝: 모두 통과. CodeRabbit: Review rate limited`. CodeRabbit 은 PR 을 연 때의 자동 리뷰도 `Review limit reached`였고 요청 코멘트에도 `Review rate limited`로 답해, 이 PR 에 낸 리뷰가 없어 회차로 세지 않는다.
- claude-review 첫 회차(3c4623c8 의 실행, 코멘트 2026-10-23T11:48:16Z): Critical·Major 없음, Minor 하나와 Nit 둘. 첫 회차라 지적마다 판단했다.
  - Minor `tools/rerun_continue.py`의 `run_sessions`가 한 함수에서 호출 앞의 끝, `launch`, 비용 누적, 기록 짓기, 갈래 고르기, 다음 메시지 짓기를 모두 한다(`CODING_STANDARDS.md`의 추상화 수준 줄): 넘긴다. 09 가 `screen` 자리를 채우며 그 함수를 고치고, 지금 뽑으면 continue 변이 표의 원문이 옮겨 가 표 전체를 다시 돌아야 한다. 리뷰어도 후속 정리로 충분하다고 적었다. 티켓 09 "08에서 넘어온 메모"의 마지막 줄과 아래 "다음"에 적었다.
  - Nit 훅 `tools/hook_edit_during_commit.py`와 사본 `tools/proc_command_line.py`가 같은 입력에서 같은 낱말을 내는지 견주는 시험이 없다: 고쳤다. `test_훅에서_옮긴_명령_줄_읽기가_훅의_것과_같다`가 두 파일을 `ast`로 풀어, 맨 위와 그 바로 아래 `if`(플랫폼 갈래)의 이름이 같은 정의 열하나를 독스트링을 뗀 덤프로 대고, `_windows_api`는 사본의 문장이 모두 훅에 있는지 본다(훅은 Toolhelp 와 실행 파일 경로의 원형을 더 적는다). import 대신 소스를 푸는 것은 윈도 갈래가 `sys.platform` 아래에서만 정의되어 리눅스 CI 에서는 import 로 볼 수 없기 때문이다. 두 사본의 이름이 같은 함수 여섯 가운데 `_windows_api`만 본문이 다른 것은 커밋하지 않은 스크래치 스크립트로 손으로 먼저 봤다. 변이 둘(46·47번)이 고른 표지까지 기대대로 빨갰고, 두 독스트링에 이 시험을 가리키는 문장을 더했다.
  - Nit `tools/hook_prompt_directive.py`의 `directive_branch` 독스트링에 러너가 import 한다는 줄이 있으면 이름을 바꿀 때 놓치지 않는다: 그 줄은 이미 있다(독스트링 둘째 문단 "공개 이름인 것은 다시 풀기 러너(`tools/rerun_continue.py`)가 … import 하기 때문이다"). 고치지 않고 PR 코멘트로 알린다.
- 다시 돌린 명령: `uv run pytest -q tests/tools/test_proc_command_line.py`(5 passed), `tools/mutate.py`로 46·47번(`변이 2 모두 기대대로`), `tools/mutate.py --check` 두 표(continue 47, session 27 모두 원문이 한 번씩), 고친 파이썬 셋의 `ruff check`, `tools/check_md_tables.py` 프로브 README.

## 회고

후보 여덟, 승인 하나(회차로 세는 것), 기각 일곱, 넘김 없음. 대기열 만료는 `uv run python tools/queue_open_rows.py`를 그대로와 `git fetch origin` 뒤 `--ref origin/main`으로 두 번 돌려 둘 다 만료할 행이 없었다.

1. 승인(회차로 세는 것): 첫 세션이 커밋하지 않은 스크래치 탐침으로 본 런처의 시간(8.09초, 0.03초)을 "손으로 쟀다"로 적었고, 셀프 리뷰 표준 축 8 이 `docs/agents/issue-tracker.md` 프로브와 근거 절대로 "손으로 봤다"로 고치게 했다. `CLAUDE.md`의 Issue tracker 줄이 근거 문장에서 따르라고 가리키는 구현 때의 지침을 어겨 리뷰가 잡은 사건이다. 손으로 돌린 것을 잰 것처럼 적은 같은 실수의 열린 행 227 에 회차를 더했다(6회차). 227 이 처방한 계기 훅의 조건은 같은 줄에 `손으로`가 있으면 알리지 않아 이 꼴("손으로 쟀다")을 놓친다. 반영하는 세션이 그 조건을 볼 것이다.
2. 기각: 중간 문장을 영어로 써 `hook_midturn_korean`이 앞 세션들에서 세 번(위 "실수"의 첫째와 다섯째), 이 세션에서 두 번(일지의 회고 절을 쓰는 Edit 직전과 대기열을 여는 Read 직전) 알렸다. 이미 있는 훅이 그 자리에서 알렸다(닫힌 83·94 의 처방이 그 훅이다).
3. 기각: 변이가 도는 동안 같은 체크아웃의 티켓 09 를 고쳐 `hook_edit_during_mutate`가 알렸다. 이미 있는 훅이 알렸고 변이 대상 파일이 아니었다.
4. 기각: `rerun_continue.py` 첫 판의 없는 이름(`launch_call`)과 함수를 가린 매개변수. 커밋 전에 스스로 봤고 pyright 와 시험이 잡는 꼴이다.
5. 기각: 이 세션의 일지 덧붙이기(heredoc 뒤 `git status`)와 스크래치 스크립트 짓기(`mkdir`·heredoc·`uv run`의 사슬)를 워크트리 가드가 거부했다. `CLAUDE.md` 환경 함정이 이미 적은 모양이고 앱 가드가 그 자리에서 막았다. Edit·Write 도구로 옮겨 호출이 한 번씩 더 들었다.
6. 기각: 셀프 리뷰를 지나 PR 직전 `bug-perf-review`가 잡은 Minor(마감에 끈 호출의 결과 이벤트 문장)와 PR claude-review 의 Minor(`run_sessions`의 추상화 수준)·Nit(사본 대조 시험). 리뷰가 제 몫을 한 것이다. 사본 대조를 `.claude/rules/tools.md`의 사본 항목으로 올릴지 보았으나 사본이 실제로 갈린 사건이 없다. `tools/tidy_checkouts.py`의 PEB 사본은 다른 칸(작업 폴더, 환경)을 읽어 견줄 짝이 아니다.
7. 기각: claude-review Nit(러너가 import 한다는 독스트링 줄)은 이미 있는 줄을 리뷰어가 놓친 것이고, 든 비용은 확인 한 번이다.
8. 기각: 커밋 f614f00c 의 인용 대조 경고 둘. 이미 있는 검사(`tools/check_quotes.py`)가 그 자리에서 알렸다.

## 다음

- 08 이 병합되면 09(Blocked by 08)가 열린다. 07 은 PR #372 로 옆 세션이 하고, 10 은 07·09 를, 11 은 10 을 기다린다.
- PR #374 claude-review 첫 회차에서 뒤로 넘긴 일: `run_sessions` 쪼개기는 09 가 그 함수를 고칠 때 한다(티켓 09 "08에서 넘어온 메모"의 마지막 줄).
- PR #370 에서 넘어와 아직 남은 일: `_git`·`_git_env` 사본 셋의 실패 모양은 07 과 06 이 모두 병합된 뒤 하나로 맞춘다(일지 2026-10-23-36 "다음"). 10 에서 볼 둘(`Elsewhere`를 `Spend`의 부분으로 받을지, `claude_version` 매개변수의 가림)은 티켓 10 "08에서 넘어온 메모"에 있다.
- PR #372(07)가 이 PR 과 같은 파일 넷(티켓 10, 프로브 README, `tools/rerun_round.py`와 그 시험)을 고쳐, 나중에 병합하는 쪽이 글자 충돌을 푼다.
