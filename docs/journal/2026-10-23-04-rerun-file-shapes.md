# 2026-10-23 (04) 다시 풀기의 두 계약 파일의 꼴을 짓는다 (model-rerun 01)

## 사용자 프롬프트

티켓 세션(일지 2026-10-23-02)이 PR을 병합한 뒤 `next-session`의 지시문으로 이 세션을 열었다. 첫 메시지는 아래다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/01-rerun-file-shapes.md
>
> 다음 작업: .scratch/model-rerun/issues/01-rerun-file-shapes.md. 과제 목록과 회차 기록, 두 계약 파일의 꼴을 `tools/`의 모듈 하나에 짓는다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 01-rerun-file-shapes)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/01-rerun-file-shapes.md
> 브랜치: feature/01-rerun-file-shapes
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-02-model-rerun-tickets.md("다음")
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22). 01이 병합되면 결정표대로 02·03·04를 나란히 연다

그 뒤 사용자 프롬프트는 없었다.

## 체크아웃 정리

주 체크아웃(main, 깨끗함)을 b104f8fa에서 9999e83e로 당겼다. 판정으로 브랜치 `worktree-admin-style-screens`를 지웠고, 쉬는 세션만 쥔 워크트리 둘(`01-contrast-module`, `model-rerun-spec`)의 세션 프로세스를 `end-holders`로 끈 뒤 워크트리와 브랜치를 지웠다. 휴지통의 `node_modules` 둘을 비웠고, `worktree-overrides-pc-check~~.venv`는 python.exe(pid 41176)가 모듈을 올려 남았다. 나머지 워크트리는 병합된 PR이 없거나 쥔 프로세스(실행 중 세션, pwsh, sh)가 있어 남겼다.

## 구현

- 모듈 이름은 `tools/rerun_files.py`로 정했다(뒤 티켓들은 "01의 꼴"로만 부르고 이름을 정하지 않았다). 시험은 `tests/tools/test_rerun_files.py`.
- JSON 풀기는 `tools/token_report.py`의 `Json` 별칭과 `isinstance` 좁히기를 따랐다. 키가 정해진 객체 도우미 `_Obj`가 빠진 키·모르는 키·형을 한 자리에서 거부한다. 처음에 메서드 이름을 `str`·`int`·`bool`로 지었다가 클래스 안에서 내장 형 이름을 가려 `text`·`integer`·`flag`로 바꿨다.
- 쓰기는 직렬화한 글을 같은 모듈의 읽기로 다시 풀어 보고 거부되면 쓰지 않는다. `write_record`는 `open("x")`로 이미 있는 파일을 덮지 않는다.
- 끝은 종류와 하위 이유 두 칸이고 명세의 "이유 글"(자유 글)은 두지 않았다. 러너가 지은 글이어도 자유 글 칸은 커밋하는 기록의 허용 목록 밖이라서다. 명세 "회차 기록"의 끝 줄과 "과제 목록의 칸"에 2026-10-23 티켓 01 주석으로 적었다.
- 계정 불일치는 회차를 열지 않아 기록이 없으므로 `측정 아님`의 하위 이유에 넣지 않았다(티켓 목록 그대로).
- 칸 사이의 맞음을 읽기가 본다: 끝남이 아닌 회차와 결과 커밋이 없는 회차에는 준비·게이트·숨은 시험이 없다, 준비가 실패하면 게이트와 숨은 시험이 없다, 결과 커밋과 고른 규칙(`지시문 브랜치`·`하나뿐인 브랜치`·`없음`)의 짝, 숨은 시험의 통과 수 + 실패 노드 수 = 전체 수, 한도가 아닌 끝에는 `resets_at`이 없다.
- 이름 칸(도구, 오염 꼴, 모델, 노력, subtype 등)은 공백·따옴표·`=`가 없는 꼴만 받는다(`.claude/rules/tools.md` 허용 목록 항목).

## 검사

- `uv run pytest -q tests/tools/test_rerun_files.py -p no:xdist`: 81 passed. 구현 전에는 모듈이 없어 수집 오류였다.
- 변이 `.scratch/model-rerun/probes/rerun_files_mutations.toml`: 21 모두 기대대로 빨강(커밋하지 않은 작업 트리, 기준 9999e83e). 프로브 README 표와 "변이" 절에 적었다.
- `ruff check .`, `ruff format --check .`, 두 파일의 pyright, `tools/check_type_escapes.py`: 초록.
- `tools/run_checks.py`는 백그라운드로 띄웠다가 인계하며 멈췄다. 새 세션이 다시 돈다.

## 인계

셀프 리뷰 직전에 인계 계기(컨텍스트 309,514 토큰)가 왔다. 이 세션의 제목은 `feature/01-rerun-file-shapes`였고 `feature/01-rerun-file-shapes (인계함)`으로 바꾼다. 낸 지시문은 아래다.

```
다음 작업: .scratch/model-rerun/issues/01-rerun-file-shapes.md. 과제 목록과 회차 기록, 두 계약 파일의 꼴을 `tools/`의 모듈 하나에 짓는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/01-rerun-file-shapes.md
브랜치: feature/01-rerun-file-shapes
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-04-rerun-file-shapes.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(tools/rerun_files.py, tests/tools/test_rerun_files.py, 변이 표와 프로브 README, 명세 주석 둘, 티켓 Status in-progress, 이 일지)이 워크트리에 있고 셀프 리뷰(/code-review origin/main)부터 한다. 변이 21은 이미 모두 빨갰고, tools/run_checks.py 전체 실행은 아직 끝까지 보지 못했다. 일지 docs/journal/2026-10-23-04-rerun-file-shapes.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22). 01이 병합되면 결정표대로 02·03·04를 나란히 연다
```

백그라운드의 `tools/run_checks.py`를 멈추고 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-22T17:14:22Z

## 이어받은 세션

지시문대로 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 셀프 리뷰(`/code-review`, base 9999e83e)를 띄우며 `tools/run_checks.py`를 백그라운드로 다시 돌렸고, 열 검사 모두 Passed(종료 0, pytest 275.1초, web-verify 249.9초)였다.

## 셀프 리뷰

`/code-review` base 9999e83e, diff 파일 셋(명세, 프로브 README, 티켓), 커밋 0, 미추적 넷(모듈, 시험, 변이 표, 이 일지). 표준 축은 sonnet·high, 명세 축은 본 세션 모델이었다. 표준 축 서브에이전트가 이 워크트리에서 `tools/mutate.py`를 돌려 그동안 명세 축의 pytest가 흔들렸고(명세 축이 알렸다), 변이가 끝난 뒤 소스가 원상태인 것을 81 passed로 확인하고 편집했다.

- 표준 축: Major 하나(`dumps_*`의 `check` 플래그, `CODING_STANDARDS.md` "불리언 플래그 인자"), Minor 하나(`match` 없는 거부 시험), 거짓 주장 둘(`_NAME`이 토큰·URL·경로를 받는다, 명세 주석의 "자유 글 칸을 두지 않는다"와 어긋난 명령·경로 칸), 깊은 중첩의 `RecursionError`, `NaN`·무한대, 유니코드 숫자의 과제 id, 실패 노드의 중복, 냄새 다섯(판단).
- 명세 축: Major 둘(빈 게이트가 초록으로 읽힌다, 명세 주석과 코드의 어긋남), Minor 둘(실수 꼴 판·`NaN`, 실패 노드의 중복), 끝남인데 결과 커밋이 없는 기록을 받는다, `check=False`가 범위 밖의 길이다, 명세 263행 주석이 계정을 멈추는 까닭으로 든 것.

고친 것.
- 쓰는 함수 둘에서 `check` 인자를 뺐다. 거부 사례는 올바른 글을 풀어 한 칸만 바꾼 글로 짓는다(`_바꿔`, `_지워`로 나눴다).
- 글 칸을 칸마다의 꼴로 좁혔다(모델 `claude-…`·`<synthetic>`, 영소문자 식별자, 영문 도구 이름, 계정, 오염 꼴 이름, `claude --version`). 정규식은 ASCII 숫자만 받는다.
- 게이트는 `GATE_COMMANDS` 셋이 그 차례로 들고, 준비 실패 명령은 `SETUP_COMMANDS`의 하나다. 회차 폴더 경로는 마지막 조각이 그 회차의 폴더 이름이고 줄바꿈·따옴표·`=`가 없다. 실패 노드는 노드 ID 꼴이고 겹치지 않는다. 끝남인 회차에는 결과 커밋이 있다.
- 꼴 판은 정수만, 돈은 유한한 수만 받고, 쓰기는 `allow_nan=False`다. 깊은 중첩과 UTF-8이 아닌 파일은 `ShapeError`다.
- 거부 시험마다 `match`를 달았고, 다른 거부가 먼저 걸리던 시험 넷을 그 갈림만 재게 고쳤다(변이가 찾았다).
- 명세 "회차 기록"의 끝 주석에 글 칸의 꼴, 끝남의 결과 커밋, 계정이 하위 이유에 없는 까닭을 더했다.
- 변이 표를 39로 늘려 모두 기대대로 빨간 것을 봤다(프로브 README "변이").

남긴 것.
- `write_record`가 쓰다 실패하면 반쯤 쓴 파일이 남는 것(경미): 빨강을 볼 시험을 짓기 어려워 이 티켓에서 고치지 않고 06의 메모로 넘겼다. 06은 04를 거쳐 01 뒤에 돈다.
- 게이트가 셋이 아닌 갈래를 07이 정할 것: 07의 메모로 넘겼다(07은 04를 거쳐 01 뒤).
- 냄새(판단): `(task_id, arm, round_no)` 데이터 뭉치, 칸 하나에 네 자리를 고치는 산탄총, 문자열 갈래·층, `arm_label`·`read_judge_view`의 얇은 위임, 한 모듈의 여러 까닭. 티켓이 "모듈 하나"와 "함수"를 정했고 뒤 티켓이 이 이름으로 부르므로 두었다. 상수를 리터럴과 견주는 시험 둘은 명세의 값 모임을 고정하는 몫이라 두었다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장).
- 모듈 독스트링: "글 칸은 칸마다 그 값이 나오는 꼴만 받는다", "회차 폴더 경로는 마지막 조각이 그 기록의 과제 id·갈래·회차 번호로 지은 회차 폴더 이름이고, 줄바꿈·따옴표·`=`가 없다", "꼴로 좁힌 글 칸도 그 꼴 안의 글은 받는다. 도구 이름, 오염 꼴의 이름, 계정 이름 칸은 식별자 꼴이라 `sk-ant-…` 같은 토큰 꼴의 글도 받는다".
- 명세 주석: "게이트와 준비의 명령은 명세가 정한 세 명령의 상수와 같아야 하고, 게이트는 셋이 그 차례로 든다", "계정 불일치는 회차를 열지 않아 기록이 없으므로 하위 이유에 없다".
- 프로브 README: "변이 39 모두 기대대로 빨갰다(표지를 단 서른셋은 `DID NOT RAISE` 서른하나, `RecursionError`·`UnicodeDecodeError` 하나씩이 맞았고, 표지 없는 여섯은 빨강만 본다)".
