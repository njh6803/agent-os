# 2026-10-23 (18) 후보 하나의 원래 PR 시험에서 숨은 시험을 가른다 (model-rerun 02)

## 사용자 프롬프트

티켓 01의 세션(일지 2026-10-23-15)이 PR #361을 병합한 뒤 `next-session`의 지시문으로 나란히 여는 세 세션 가운데 첫째로 이 세션을 열었다. 첫 메시지는 아래다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/02-hidden-test-filter.md
>
> 다음 작업: .scratch/model-rerun/issues/02-hidden-test-filter.md. 후보 하나의 원래 PR 시험 가운데 흔들리지 않고 B에서 단언으로 실패하며 새 이름에 기대지 않는 노드만 숨은 시험으로 남긴다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/02-hidden-test-filter.md
> 브랜치: feature/02-hidden-test-filter
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-15-rerun-file-shapes.md 끝의 "다음", .scratch/model-rerun/issues/03-rerun-judge.md, .scratch/model-rerun/issues/04-round-clone.md
> 이어받을 상태: 01(PR #361)의 봇 셋째 회차가 보류한 일: tools/rerun_files.py의 Task.hidden_tests·support_files 경로 칸이 꼴을 좁히지 않는다(절대 경로, .., 줄 구분 문자가 읽기를 지난다). 숨은 시험 노드를 짓는 이 티켓에서 회차 기록의 글 칸처럼 허용 목록으로 좁힐지 정한다. 04도 같은 칸을 꺼내 쓰므로 고치면 그 세션과 겹치지 않게 rerun_files.py의 그 칸만 건드린다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

그 뒤 사용자 프롬프트는 없었다.

## 체크아웃 정리

주 체크아웃(main, 깨끗함)을 e205147d에서 d0e696c9로 당겼다. 쉬는 세션만 쥔 워크트리 셋(`003-probe-conclusion-evidence-kind`, `004-optional-bool-annotation-check`, `008-quote-wrap-slash-comment`)의 세션 프로세스를 `end-holders`로 끈 뒤 워크트리와 브랜치를 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 python.exe(pid 41176)가 모듈을 올려 남았다. 나머지 워크트리는 병합된 PR이 없거나 쥔 프로세스나 실행 중 세션이 있어 남겼다.

## 구현

- 가르기는 새 모듈 `tools/rerun_hidden.py`에 두었다. 값만 받는 층(`changed_tests`, `read_junit`, `node_facts`, `sort_nodes`)과 git·pytest를 부르는 바깥 층(`sort_candidate`, `term_in`)이다. 05의 고르기 모듈이 `sort_candidate`를 부른다(티켓 05의 메모).
- 바뀐 시험은 AST 덤프로 견준다. 조건 3의 찾기는 작업 트리 없이 `git grep -q -F [-w] -e <글> <커밋> [-- ":(top,exclude)tests"]`로 한다.
- pytest에는 노드 ID가 아니라 바뀐 시험이 든 파일을 넘긴다. 모으지 못한 파일의 노드 ID를 받은 pytest가 `--continue-on-collection-errors`가 있어도 `found no collectors`로 실행 전체를 멈춰, B의 모음 오류 하나가 모든 노드를 "결과 없음"으로 만들었다(끝까지 시험이 처음에 숨은 시험 0으로 빨갰다).
- 01이 보류한 경로 칸은 허용 목록으로 좁혔다(`tools/rerun_files.py`의 `is_test_file`·`is_support_file`). 숨은 시험 노드 ID의 파일 부분은 `tests/` 아래 `test_*.py`, 지원 파일은 어디의 `conftest.py`이거나 `tests/` 아래 시험 파일이 아닌 `.py`다.
- 꺼낸 작업 트리는 `tools/canary.py`처럼 걷기 전에 링크를 끊고, 덮을 자리의 상위가 B의 링크면 덮지 않는다. 시간을 넘긴 준비와 pytest는 프로세스 트리째 끈다.

## 검사

- 변이 `.scratch/model-rerun/probes/rerun_hidden_mutations.toml` 17과 `rerun_files_mutations.toml`의 11·47·48이 표지까지 기대대로 빨갰다(16·17은 표에 고친 줄을 맞바꿔 적은 것을 고친 뒤).
- `tools/run_checks.py`: 열 검사 모두 Passed(종료 0, pytest 320.4초, web-verify 319.0초). ruff 두 줄 초록.

## 셀프 리뷰

`/code-review` base d0e696c9, diff 파일 여섯, 커밋 0, 미추적 셋(모듈, 시험, 변이 표). 표준 축은 sonnet·high, 명세 축은 본 세션 모델이었다.

- 명세 축: Minor 하나(M에서 돌지 않은 바뀐 시험이 결과에서 까닭 없이 사라진다. 마커로 빠진 시험을 임시 저장소로 재현했다), 범위 넘침 Minor 하나(명세 "자리와 모듈"의 모듈 수 넷), 거짓이 된 독스트링 Minor·Nit 둘, Nit 둘(같은 이름의 `Hidden`, `hidden.failed` 칸이 함께 좁아진 것).
- 표준 축: Major 둘(`_overlay`의 `OSError`가 `Failure`가 아닌 예외로 샌다, 변이 표지 셋이 시험 소스의 조각이다), Minor 일곱(NUL·긴 문자열의 실패 갈래, 시험으로 고정하지 않은 못 보는 것과 적히지 않은 한계, 중복·이름·원시값 냄새, `_git_ok`의 하위 명령 이름), 문서 주장 둘(티켓 07의 실패 노드 칸 문장, README의 변이 시간), Nit 넷.

고친 것.
- M 두 실행 어디에도 결과가 없는 바뀐 시험을 함수 노드 ID로 넣어 조건 1의 "결과 없음"으로 빼게 했다. 노드를 짓는 부분을 순수 함수 `node_facts`로 떼고 시험을 더했다(고치기 전에 빨갰다).
- `_overlay`의 `mkdir`·`write_bytes`의 `OSError`를 `CandidateError`로 바꿔 `Failure`가 되게 했다. B에서 `tests/sub`가 파일인 저장소로 시험을 더했다(고치기 전에 `FileExistsError`로 빨갰다).
- 변이 표지: 낱말 경계와 `tests/` 빼기, 덮을 자리의 링크 단언에 메시지를 달고 표지를 `AssertionError: <메시지>`로, 같은 노드 둘의 표지는 손으로 변이를 넣어 본 diff 줄로, 저장소 변수의 표지는 `AssertionError: Failure(reason=`로 바꿨다. 변이 둘(위 두 결함의 되돌림)을 더해 열아홉 모두 표지까지 기대대로 빨갰다.
- 모듈 독스트링 "못 보는 것"에 docstring이 문자열로 세어지는 것, NUL·긴 문자열이 후보 전체의 실패 갈래인 것, `*_test.py`가 지원 파일인 것, `if` 안의 정의를 보지 않는 것을 더했고, 인자 기본값·docstring·중첩 클래스·`testfoo`·`if` 안 정의·NUL·`*_test.py`를 시험으로 고정했다. 손자 프로세스 항목은 시험을 짓지 않았다.
- `rerun_files.py` 독스트링: 조각이 `-`로도 시작하지 않는 것, 실패 노드 ID가 숨은 시험 ID와 같은 꼴인 것. 함수를 불러 `tests/_x/test_a.py`(받음), `tests/-x/test_a.py`·`tests/.x/test_a.py`·`-x/conftest.py`(거부)로 대 봤다. 티켓 07의 "노드 ID 꼴과 줄바꿈 없음만 본다"도 같은 꼴로 고쳤다.
- `_git_name`으로 `-c` 설정 뒤의 하위 명령을 알림에 쓴다. README의 변이 시간을 표준 축이 잰 값으로, 시험 이름 둘을 행동으로 바꿨고, 티켓 02·05 끝의 빈 줄을 지웠다.
- 반영 중 사고: 변이를 덧붙이는 스크래치 스크립트가 `Path.write_text(..., newline="\\n")`로 쓰다 `ValueError`로 끝났는데, 파이썬이 파일을 `"w"`로 연 뒤 newline 값을 거부해 미추적 변이 표가 비었다. 표준 축 서브에이전트가 스크래치에 복사해 둔 사본(변이 17, 끝 항목이 지워지기 전에 본 원본과 같다)으로 되살렸고, 그 뒤로는 `open("a")`로 덧붙였다.

남긴 것.
- 명세 "자리와 모듈"의 모듈 수(넷): 명세는 to-spec 스킬의 몫이라 고치지 않았고, 다섯째 모듈의 까닭은 티켓 02 메모에 있다.
- 같은 이름의 `Hidden`·`Outcome`, `tools/canary.py`와 겹치는 작업 트리 걷기: 판단 항목. 두 모듈을 함께 쓰는 05의 메모로 넘겼다(05는 02를 기다린다).
- `kind`·`condition`의 문자열과 정수, `term_in`의 `outside_tests` 플래그, `(repo, limits, out)` 뭉치, `_classname`의 위치, `_test_defs`의 겹친 `isinstance`, 윈도 예약 이름을 받는 경로 꼴: 판단 항목이고 동작이 맞다.
- `hidden.failed` 칸이 함께 좁아진 것(Nit): 실패 노드는 숨은 시험 ID에서 옮기는 값이라 둘이 맞다.

다시 돌린 것. 두 시험 파일 208 passed, 변이 19 모두 기대대로, `rerun_files` 변이 표 `--check` 통과, ruff 두 줄과 표 검사 초록. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

반영으로 새로 쓴 문장(PR 직전 리뷰에 밀 주장).
- `tools/rerun_hidden.py` 독스트링: "M 두 실행 어디에도 결과가 없는 바뀐 시험(마커로 빠졌거나 M에서 모으지 못했다)은 함수 노드 ID 하나로 조건 1에서 빠진다", "B의 작업 트리에 덮지 못한 것(B에서 상위 자리가 파일이다 등)은 그 후보의 실패 갈래", "본문의 docstring도 문자열 상수로 세어, M이 새로 쓴 문서에 같은 글이 있으면 그 시험이 빠진다", "조건 3의 문자열에 NUL이 들었거나 명령 줄에 넘기지 못할 만큼 길면 `git grep`을 띄우지 못해, 그 노드가 아니라 후보 전체가 실패 갈래다", "pytest 설정이 `python_files`로 더 모으는 `tests/` 아래 `*_test.py`는 시험 파일이 아니라 지원 파일로 덮인다", "`if` 같은 문 안에서 정의한 시험은 보지 않는다".
- `tools/rerun_files.py` 독스트링: "조각은 영문·숫자·`_.-`로 되며 영문·숫자·`_`로 시작한다(`..`, 숨은 폴더, `-`로 시작하는 조각을 받지 않는다)", "실패한 숨은 시험의 노드 ID는 겹치지 않고, 숨은 시험 ID와 같은 꼴", "숨은 시험과 실패한 노드 ID의 매개변수 부분(`::` 뒤)은 공백과 따옴표가 들 수 있어 제어 문자 밖의 꼴로 좁히지 않고".
- 티켓 07 메모의 실패 노드 칸 문장, 티켓 05 메모의 넘긴 판단 항목, 프로브 README의 변이 결과 문단과 시간 문장.

## 커밋과 인계

fbcd6239로 커밋했다. pre-commit의 검사가 모두 Passed였고(pytest 308.7초, web-verify 271.6초, 변이 표 원문 확인 포함) 이것이 손으로 치는 다섯을 갈음한다. 커밋 직후 인계 계기(컨텍스트 297,764 토큰, `커밋 뒤`)가 왔다. 곁 세션이 아니고(`get_session`의 `self`에 `parentSessionId`가 없다) 인계하지 않는 다른 때에도 들지 않아 넘긴다. 이 세션의 제목은 `feature/02-hidden-test-filter`였고 `feature/02-hidden-test-filter (인계함)`으로 바꾼다. 낸 지시문은 아래다.

```
다음 작업: .scratch/model-rerun/issues/02-hidden-test-filter.md. 후보 하나의 원래 PR 시험 가운데 흔들리지 않고 B에서 단언으로 실패하며 새 이름에 기대지 않는 노드만 숨은 시험으로 남긴다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/02-hidden-test-filter.md
브랜치: feature/02-hidden-test-filter
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-18-hidden-test-filter.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 fbcd6239로 커밋했고(티켓 Status done, pre-commit 모두 Passed, 변이 19 모두 빨강) 아직 푸시하지 않았고 PR도 없다. 남은 것은 PR 직전 리뷰(일지 "셀프 리뷰"의 "반영으로 새로 쓴 문장"을 밀 주장으로 브리프에 넣는다), 푸시와 /git-pr, 봇 회차, 병합, 회고와 next-session이다. 형제 워크트리 03-rerun-judge·04-round-clone이 프로브 README와 티켓 07을 함께 고쳐 나중에 병합하는 쪽에서 글자 충돌 후보다. 일지는 이 인계 절이 커밋되지 않은 채 워크트리에 있다. 일지 docs/journal/2026-10-23-18-hidden-test-filter.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)
```

워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-22T22:31:34Z

## 이어받은 세션: 체크아웃 정리

인계받은 새 세션이 첫 턴에 `tidy-checkouts`를 돌았다. 루트는 이미 main이고 origin/main(d0e696c9)과 같았다. 쉬는 세션만 쥔 워크트리 둘(`006-eslint-judge-tree-cleanup`, `01-rerun-file-shapes`)의 세션 프로세스를 `end-holders`로 끈 뒤 워크트리와 브랜치를 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 python.exe(pid 41176)가 모듈을 올려 여전히 남았다. 나머지 워크트리는 병합된 PR이 없거나 쥔 프로세스가 있거나 앱의 표지가 있어 남겼다. 그 뒤 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

## PR 직전 리뷰

CodeRabbit CLI는 `Seat: not assigned`라 돌지 못해 대체 둘을 나란히 돌렸다.

- `/security-review`: 확신 8 이상의 지적이 없다. 서브프로세스는 모두 리스트 인자이고 `git grep`의 패턴은 `-e`로 넘기며, junit은 expat이라 외부 엔터티를 풀지 않고, 덮을 경로는 허용 꼴과 조각마다의 링크 검사를 지난다.
- `bug-perf-review`: Critical·Major 없음. 유효 셋(Minor 둘, Nit 하나), 보류 하나. 밀어 달라고 브리프에 넣은 "반영으로 새로 쓴 문장" 아홉은 모두 코드와 맞았다(NUL·긴 문자열은 그 에이전트가 `term_in`을 불러 확인했다).

고친 것.
- BOM으로 시작하는 시험 파일의 시험이 모두 사라지던 것(`_test_defs`가 `ast.parse`에 BOM을 그대로 넘겨 `SyntaxError`를 삼켰다): BOM을 벗기고 푼다. 시험은 고치기 전에 빨갰다.
- 이어 붙이거나 이스케이프가 든 문자열이 조건 3을 지나는 것: 소스 글자와 값이 달라 찾지 못한다는 것을 독스트링 "못 보는 것"에 적고 시험으로 고정했다. 고치려면 M의 `tests/` 밖 소스를 AST로 풀어 상수를 대조해야 해서 값이 크다.
- 보류였던 conftest의 import 실패: 커밋하지 않은 스크래치 스크립트(`conftest_junit.py`)로 임시 폴더에서 pytest를 띄워 보니 종료 4이고 junit xml을 남기지 않았다(손으로 봤다). 그래서 후보 전체가 실패 갈래인 것을 "못 보는 것"에 적고 임시 저장소의 `sort_candidate` 시험으로 고정했다.
- 위 셋을 지키는 변이 셋을 변이 표에 더했고, 그 셋만 담은 표로 돌려 모두 표지까지 기대대로 빨갰다. 전체 표는 `--check`로 원문 22가 한 번씩 있음을 봤다.

남긴 것.
- Nit: `tools/rerun_files.py`의 조각 꼴이 윈도에서 같은 자리를 가리키는 별칭(끝이 `.`인 조각, `nul` 같은 장치 이름)을 받는다. 작업 트리 바깥으로 쓰는 길이 아니고 덮은 파일이 없다는 실패나 같은 폴더로 합쳐지는 정도라 PR 체크리스트에 두는 지적으로 적는다.
