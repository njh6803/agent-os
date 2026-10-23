# 2026-10-23 (51) 측정 아님 가르기 (model-rerun 09)

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/09-not-measured-checks.md
>
> 다음 작업: .scratch/model-rerun/issues/09-not-measured-checks.md. 회차마다 계정·설정·모델·오염·한도를 보고 걸린 회차를 그 이유와 함께 측정 아님으로 적는다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 09-not-measured-checks)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/09-not-measured-checks.md
> 브랜치: feature/09-not-measured-checks
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-48-continue-and-caps.md의 "다음"과 docs/journal/2026-10-23-45-gates-and-official-cost.md의 "다음"(07이 먼저 병합되어 이름순 최신 일지가 48이라 45를 지나치기 쉽다)
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 첫 턴에 `tidy-checkouts`를 돌고 `EnterWorktree`(name `09-not-measured-checks`)로 들어가 브랜치를 바꿨다. 주 체크아웃은 지금 `origin/main`(07c890c5)과 같다(`tools/sibling_overlap.py`의 형제 줄).
- `tools/rerun_checks.py`(새): 회차를 열기 전의 계정과 설정 폴더 확인(`before_round`, `claude auth status --json`의 `loggedIn`·`email`의 `@` 앞·글자 그대로의 `configDirectory`와 `settings.json`의 `env` 키), init 의 설정(빈 `mcp_servers`, 플러그인 `source`가 내장 셋과 클론의 `enabledPlugins` 안), 모델(본 세션은 `<synthetic>`을 뺀 줄이 갈래의 (모델, 노력), 서브에이전트는 모델만 갈래·하네스·Agent 입력의 허용 모임과 견준다), 오염(셸 명령과 웹 도구와 쓰기 내용과 모든 경로 값, 커밋 메시지 떼기, 거부된 호출 빼기, 막은 바깥 도구, Skill 의 `open-session`), 한도(`rejected`·`usage_limit_reached`, 가장 늦은 `resetsAt`, 못 읽으면 비운다)와 사용률을 짓는다. 회차 하나의 판정은 `Screen`이고 `screen_for`가 짓는다.
- `tools/rerun_session.py`: `drive`에 줄 판정(`watch`)을 더했다. 참이면 그 줄에서 읽기를 멈추고 08의 끄기 규칙(명령 줄에 세션 id 가 있을 때만 나무째)으로 끈다. 멈춘 꼴 `Stop.HALTED_KILLED`·`HALTED_LEFT`, 묶음 `CUT_SHORT`(러너가 출력 도중에 끈 호출, `runner_killed`가 선다)를 더했고 `LEFT_RUNNING`에 `HALTED_LEFT`를 넣었다.
- `tools/rerun_continue.py`: `run_sessions`가 `watch`를 받아 넘긴다. `call_end`는 줄 판정이 끈 호출도 측정 아님(호출)으로 본다. 08 메모대로 호출 하나(`_call`)와 다음 메시지(`_opening`)를 뽑았다.
- 시험: `tests/tools/test_rerun_checks.py`(새), `test_rerun_continue.py`(줄 판정으로 끄기, 끄지 않고 남기기, 끈 뒤 잇지 않기, 세션의 끈 표시), `test_rerun_session.py`(가짜의 도구 호출과 거부 꼴을 원본과 견준다), `fake_claude.py`(`tool_use_event`, `denial`, `result_event(denials=)`, `init_event(extra_plugins=)`, `write_script(config_directory=)`).
- 변이: 새 표 `rerun_checks_mutations.toml` 37개를 짓고, `rerun_continue_mutations.toml`의 원문 아홉을 맞추고 줄 판정의 넷을 더했다(51개). 결과와 표지를 고른 과정은 `.scratch/model-rerun/probes/README.md`의 변이 절이다.
- 티켓 09의 체크박스를 "검증 명령이 모두 초록이다" 밖에 모두 표시하고 "구현에서 정한 것"을 더했다. 10·11에 "09에서 넘어온 메모"를 더했다. 09의 Status는 아직 `in-progress`다.

## 결정

- 줄 판정이 끈 호출은 `Stop.HALTED_*`로 따로 적고, 껐으면 마감의 끄기처럼 `runner_killed`를 세운다(08 메모가 이 티켓에 넘긴 결정). 출력 도중에 끊어 결과 이벤트를 잘랐을 수 있기 때문이다. 결과가 있어도 그 호출 뒤로 잇지 않는다.
- init 은 첫 호출만이 아니라 모든 호출의 모든 init 을 본다. 세션이 클론의 설정을 고쳐 다음 호출에 플러그인을 싣는 길까지 막으려는 것이다.
- 04 메모의 두 길(같은 뿌리 아래 다른 회차 폴더, 전용 설정 폴더)을 오염 꼴로 더했다. 자기 회차 폴더와 자기 세션 기록 폴더는 뺀다. 경로마다 링크를 풀지 않은 꼴과 푼 꼴을 둘 다 본다.
- 셸 도구에 명세의 둘(Bash, PowerShell)과 함께 `Monitor`를 넣었다. 셸 명령을 돌리고 `Bash(gh:*)`에 막히지 않는다.
- 판정 차례는 설정, 모델, 오염, 한도다. 모델과 오염도 호출마다 보아 걸리면 다음 호출을 하지 않는다.

## 실수와 고친 것

- `_object`에 BOM 떼기를 넣을 때 Edit 도구가 날것 U+FEFF를 저장해 훅이 알렸고, sed 로 바꾸려다 `\u`가 대문자 변환이라 `Feff`가 됐다. 스크래치 파이썬 스크립트로 `"﻿"` 이스케이프를 되살렸다.
- 리팩터링(`_call`, `_opening`, `CUT_SHORT`) 뒤 continue 변이 표의 원문 아홉이 0번 나왔다. 고친 코드에 맞췄다.
- checks 변이 표의 첫 판에서 셋이 초록이었다(시험이 그 길을 밟지 않았다). 사례를 더했다.
- 변이 표 머리 주석에 실제 프로세스 시험을 고르지 않는 까닭을 "4시간 벽시계까지 기다린다"로 적었다. 그 시험의 가짜는 `hang=600`이라 600초를 기다린 뒤 빨개진다. README 행을 쓰다 가짜를 읽고 고쳤다.
- 중간 문장을 영어로 써 훅이 세 번 알렸다(압축 전 둘, README 편집 직전 하나).

## 검증 (셀프 리뷰 전, 커밋하지 않은 작업 트리, 기준 07c890c5)

- 변이: `rerun_checks_mutations.toml` 표 전체를 돌려 `변이 37 모두 기대대로`. `rerun_continue_mutations.toml`은 바꾸거나 더한 열셋을 번호로 골라 `변이 13 모두 기대대로`. `--check`로 checks 37, continue 51, session 27 모두 원문이 한 번씩 있다.
- `uv run pytest -q -n 4`로 `test_rerun_checks.py`·`test_rerun_continue.py`·`test_rerun_session.py`·`test_rerun_files.py`: 448 passed.
- `uv run ruff check .`, `uv run ruff format --check .`(1035 files): 초록.
- `uv run python tools/run_checks.py`: 인계로 멈췄다. 멈추기 전에 끝난 것은 check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright이고 모두 Passed였다. pytest·web·run-hooks 등은 끝나기 전에 멈췄으니 새 세션이 다시 돈다(커밋의 pre-commit 으로 갈음할 수 있다).

## 인계

- 이 세션의 지금 제목: `feature/09-not-measured-checks`.
- 인계 경계: `셀프 리뷰 직전`. 세션 컨텍스트가 문턱(20만)을 넘은 채 `/code-review`를 부른 직후 `hook_handoff`가 들어왔다. 그 리뷰의 단계는 밟지 않았다.
- 이 브랜치에 열린 PR은 없다.
- 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/09-not-measured-checks.md. 회차마다 계정·설정·모델·오염·한도를 보고 걸린 회차를 그 이유와 함께 측정 아님으로 적는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/09-not-measured-checks.md
브랜치: feature/09-not-measured-checks
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-51-not-measured-checks.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-23-51-not-measured-checks.md. 리뷰 범위는 origin/main(07c890c5) 이후의 커밋하지 않은 변경과 미추적 파일 전체이고 명세는 티켓 09와 .scratch/model-rerun/spec.md다. tools/run_checks.py는 인계로 멈춰 pytest·web 등이 끝나지 않았다(끝난 검사는 일지의 검증 절). 티켓 09는 "검증 명령이 모두 초록이다"만 남았고 Status는 in-progress다(PR 전에 done)
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/09-not-measured-checks (인계함)`으로 바꿨고, 백그라운드 검사(run_checks)를 멈췄고, 워크트리 잠금을 풀었다.
- open-session을 부른다 2026-10-23T14:49:48Z

## 셀프 리뷰 (이어받은 세션)

새 세션이 지시문대로 `EnterWorktree(path)`로 이 워크트리에 들어와 `/code-review`를 불렀다. 범위는 기준 07c890c5, diff 파일 10개, 커밋 0개, 미추적 4개(`tools/rerun_checks.py`, `tests/tools/test_rerun_checks.py`, `.scratch/model-rerun/probes/rerun_checks_mutations.toml`, 이 일지)다.

### 표준 축 (sonnet·high)

하드 위반과 Critical·Major는 없었다. 지적과 판정은 아래와 같다.

- Minor. `BOUNDARY` 서술("glob 글자를 더했다")이 코드보다 넓다. glob 글자는 `*?`뿐이라 `~/.claude{,.bak}`, `${X:-~/.claude}`가 걸리지 않는다. 판정: 고친다. 중괄호(`{}`)를 `BOUNDARY`에 더하고 시험으로 고정한다. 대괄호는 한 글자에 맞아 `~/.claude[a]`가 이웃 이름(`~/.claudea`)이라 더하지 않고 그 까닭을 독스트링에 적는다.
- Minor. 셸 명령의 절대 경로에 든 `..`·`.`(`<뿌리>/<자기 회차>/../<다른 회차>`는 지나가고 `<뿌리>/./<자기 회차>`는 걸린다)가 못 보는 것에 없다. 판정: 고친다. 못 보는 것에 적고 시험으로 고정한다(`.claude/rules/tools.md`의 못 보는 것 항목).
- Minor. "`Monitor`는 `Bash(gh:*)`에 막히지 않는다"가 잰 것처럼 적혔다. `FIXED_DENY_RULES`를 읽은 것이다. 그리고 `Monitor`의 `ws.url`(웹소켓 주소)은 주소 검사를 받지 않는다. 판정: 고친다. 문장을 코드를 읽은 것으로 고치고, `ws` 입력은 웹 도구처럼 여섯 꼴을 찾는다. `ws` 입력이 있다는 것은 이 세션이 불러온 Monitor 도구의 입력 스키마(`ws.url`, `ws.protocols`)에서 봤다.
- Minor. `test_웹_도구의_입력은_여섯_꼴을_모두_찾는다`가 셋만 단언한다. 판정: 고친다. 여섯을 모두 단언한다.
- 판단. `HAIKU`가 `tools/rerun_cost.py`에 이미 있다. 판정: 고친다. 그 모듈에서 가져온다(그 모듈은 `tools/rerun_files.py`만 가져와 순환이 없다).
- 판단. `command_patterns`와 `_web_patterns`의 같은 3단 모양. 판정: 고친다. 낱말 `gh`를 찾을 글만 달리 받는 함수 하나로 모은다.
- 판단. `_split_heredocs`가 인자 리스트를 고친다(`CODING_STANDARDS.md`의 출력 인자 줄). 판정: 고친다. 받은 리스트를 복사해 고친다.
- 판단. `Screen.__call__`이 상태를 쌓으면서 `End`를 돌려준다(CQS). 판정: 남긴다. 08이 정한 `run_sessions(..., screen=...)`의 계약이 호출마다 끝을 돌려주는 콜백이고, 세션을 넘는 모델 수와 오염 적중을 보려면 그 콜백이 상태를 쌓아야 한다.
- 판단. `_without_messages`의 긴 인덱스 루프, `(clone, config_dir, main_checkout, home)`의 Data Clumps, `_resolved`·`_content_watched`의 접기 중복. 판정: 남긴다. 파서의 루프는 git 의 옵션 읽기를 그대로 따르는 모양이고, 나머지 둘은 판단 항목만이라 커밋을 막지 않는다.
- Nit. 독스트링의 "바깥을 읽는 몫"에 `screen_for`가 없고, `drive` 독스트링의 줄바꿈이 어색하고, `test_rerun_continue.py`의 `read(_pid)`가 같은 파일의 `_pid()`를 가리고, `assert CODE_REVIEW_MODEL == "sonnet"`이 구현을 옮긴다. 판정: 넷 다 고친다.

### 명세 축 (본 세션 모델 상속)

빠진 요구와 범위 넘침은 없었다. 티켓 사례의 입력은 함수를 직접 불러 모두 티켓대로였다. 지적과 판정은 아래와 같다.

- Minor. 설정 폴더 `settings.json`의 `env` 키를 계정처럼 다룬다. 명세 "설정 폴더의 설정"은 `env` 키와 init 을 묶어 "하나라도 아니면 … 회차를 '측정 아님(설정)'으로 적은 뒤" 멈추라고 하고, 기록 없이 멈추는 것은 계정 불일치뿐이다. 판정: 고친다. `before_round`가 까닭과 함께, 설정 폴더의 잘못이면 그 회차의 끝(측정 아님(설정))을 돌려준다. 10 메모도 고친다.
- Minor. Agent 입력으로 고른 모델을 회차 단위로 허용한다. 티켓은 "그 세션이 Agent 도구 입력의 `model`로 직접 고른 모델"이다. 판정: 고친다. 고른 모델을 세션마다 쌓고 그 세션의 서브에이전트 줄과만 견준다.
- Minor. 11 메모와 모듈 독스트링의 거짓 음성 목록이 닫혀 있는데 반례가 있다(`~/.claude-rerun/projects`, `$HOME/.claude-rerun/...`). 판정: 고친다. 홈 아래의 찾는 경로(설정 폴더, 뿌리, 주 체크아웃)도 대신하는 이름의 꼴을 본다. 목록은 "셸이 글을 풀어야 나오는 경로는 풀지 않는다"는 조항의 예시로 다시 적는다(code-review 6단계 1).
- Minor. 거짓 양성 목록도 닫혀 있는데 반례 다섯이 있다(따옴표 없는 구분자의 `$(cat <<EOF`, `-F - <<<`, `echo … | git commit -F -`, `{ git commit -m gh; }`, 작은따옴표 안의 `$(gh)`). 판정: 둘은 고친다(치환 없는 본문의 따옴표 없는 구분자, 명령 앞의 셸 예약어). 나머지 셋은 "커밋 메시지 떼기가 나열한 길 밖으로 넘긴 메시지는 떼지 않는다"는 조항의 예시로 못 보는 것에 적고 시험으로 고정한다.
- Nit. 프로브 README 의 "끄기 자체는 continue 표의 줄 판정 변이가 본다"와 달리 `drive`의 `if watch(line):`를 없애는 변이가 없다. 판정: 고친다. 그 변이를 더하고 빨강을 본다.
- Nit. 쓰기 대상을 Git Bash 꼴(`/d/…/clone/tests/x.py`)로 적으면 클론 밖으로 본다. 판정: 고친다. 클론도 `head_forms`의 꼴로 견준다.

### 반영

- 고친 것: 위에서 "고친다"로 판정한 것 전부. 코드는 `tools/rerun_checks.py`(`Refusal`, `_SETTINGS_END`, 세션마다의 `_chosen`, `_RESERVED_WORDS`, 치환 없는 본문의 `$(cat`, `_with_home_aliases`, `BOUNDARY`의 중괄호, `SOCKET_KEY`, `_six_patterns`, `_summed`, `_content_watched`의 `head_forms`, `HAIKU` 가져오기, `_split_heredocs`의 복사), 시험은 `tests/tools/test_rerun_checks.py`와 `tests/tools/test_rerun_session.py`의 `test_줄_판정이_참이면_마감_전에_그_줄에서_끈다`, 변이는 checks 표 아홉과 continue 표 하나를 더했다. 티켓 09의 "구현에서 정한 것", 10과 11의 09 메모, 프로브 README 의 두 행과 변이 절을 맞췄다.
- 남긴 것: `Screen`의 CQS(08의 `run_sessions(screen=)` 계약), `_without_messages`의 루프, Data Clumps, 접기 중복. 까닭은 위 표준 축 판정에 적었다. 넘기는 것은 없다.
- 밀 주장(PR 직전 `bug-perf-review`에 나열할, 반영으로 새로 쓴 사실 문장의 원문):
  1. 모듈 독스트링 "자리 둘": "설정 폴더의 잘못이면 그 회차의 끝(측정 아님(설정))도 싣는다. 명세 "설정 폴더의 설정"이 `env` 키와 init 을 묶어 측정 아님(설정)으로 적으라고 하고, 기록 없이 멈추는 것은 계정 불일치뿐이다."
  2. `Refusal` 독스트링: "`end`가 있으면 그 회차를 그 끝으로 적는다(설정 폴더의 잘못, 측정 아님(설정)). 없으면 회차를 열지 않아 기록이 없다(계정과 세션 환경). 걸리면 새 회차를 열지 않고 러너를 멈춘다(10)."
  3. 모듈 독스트링 "모델": "앞 세션이 고른 모델은 인계 뒤 세션으로 물려주지 않는다."
  4. 모듈 독스트링 "오염": "명세의 셸(Bash, PowerShell)에 `Monitor`를 더했다. 셸 명령을 돌리는 도구이고, `Bash(gh:*)` 꼴의 막는 규칙이 그 명령에도 걸리는지는 재지 않았다." 그리고 "웹소켓 입력이 있다는 것은 Claude Code 가 주는 `Monitor` 도구의 입력 스키마(`ws.url`, `ws.protocols`)에서 봤다."
  5. 모듈 독스트링 "경로": "명세의 넷(경로 구분자, 따옴표, 공백, 끝)에 셸의 제어 글자, glob 글자(`*?`), 중괄호(`{}`. 중괄호 확장과 `${X:-…}`)를 더했다. 대괄호는 더하지 않았다. 대괄호 glob 은 한 글자에 맞아 `~/.claude[a]`는 이웃 이름(`~/.claudea`)이다." 그리고 "홈 아래의 찾는 경로(`~/.claude`, 홈 아래에 둔 설정 폴더와 뿌리)는 `~`, `$HOME`, `%USERPROFILE%` 같은 홈을 대신하는 이름(`HOME_ALIASES`)으로 적은 꼴도 … 본다."
  6. 모듈 독스트링 "커밋 메시지 떼기": "명령 앞의 셸 예약어(`{`, `!`, `if`, `then`, `do`, `time` 등)와 환경 대입과 git 의 전역 옵션(…)을 지난다." 그리고 "`$(cat`이 메시지 옵션 바로 뒤에 있고, 구분자에 따옴표가 있거나 본문에 명령 치환이 없으며, 종결자 다음 줄이 `)`로 시작할 때다."
  7. 모듈 독스트링 "못 보는 것"의 두 조항: "커밋 메시지 떼기가 나열한 길(위) 밖으로 넘긴 메시지는 떼지 않아, 그 안의 낱말 `gh`가 걸린다(거짓 양성). 예: …" 그리고 "셸이 글을 풀어야 나오는 경로는 풀지 않는다(거짓 음성). 예: … 같은 까닭으로 절대 경로 안의 `.` 조각(`<뿌리>/./<자기 회차>`)을 회차 폴더 이름으로 읽어 다른 회차로 건다(거짓 양성)."
  8. 티켓 10의 09 메모: "`Refusal.end`가 있으면(설정 폴더의 `settings.json`에 `env` 키가 있거나, JSON 이 아니거나, 읽지 못했을 때) 그 회차를 그 끝(측정 아님(설정))으로 적는다. … 호출 전이라 쓴 비용은 0이다. `end`가 없으면(계정 불일치, 세션 환경에 설정 폴더가 없음, `auth status`를 띄우지 못함) 회차를 열지 않아 기록이 없다."
  9. 티켓 11의 09 메모: 오염 꼴이 틀리게 가르는 길의 두 조항과 그 예(독스트링 7과 같은 것), "그 세션의 Agent 입력이 고른 모델(앞 세션이 고른 모델은 인계 뒤 세션으로 물려주지 않는다)".
  10. 프로브 README checks 행: "줄 판정이 허용 밖 init 에서 참인지는 이 표의 "줄 판정이 허용 밖 init 에서도 끄라고 하지 않는다"가, 참인 줄에서 읽기를 멈추고 끄는지는 continue 표의 "줄 판정이 참이어도 읽기를 멈추지 않는다"가 본다." continue 행: "그 시험이 마감 30초에 끌 때까지 기다려 약 31초다(2026-10-24 그 변이만 돌린 도구 출력에서 30.88초)."
- 다시 돌린 명령(2026-10-24, 커밋하지 않은 작업 트리): `uv run pytest tests/tools/test_rerun_checks.py` 211 passed, `tests/tools/test_rerun_session.py`·`test_rerun_continue.py` 265 passed, `uv run pyright`와 바꾼 파일의 ruff 는 오류 0. 변이는 세 표의 `--check`가 모두 원문을 찾았고(checks 46, continue 52, session 27), checks 표 전체에서 마흔셋이 표지까지 기대대로, 셋은 표지가 어긋나 고친 뒤 다시 돌려 기대대로였다(`변이 3 모두 기대대로`). continue 표의 새 변이(46번)도 기대대로였다(`변이 1 모두 기대대로`, 30.88초). 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음하고, 그 결과는 커밋 뒤에 적는다.
