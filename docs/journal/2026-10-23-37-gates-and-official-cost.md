# 2026-10-23 (37) 게이트와 숨은 시험, 공식 단가를 짓는다 (model-rerun 07)

## 사용자 프롬프트

티켓 04의 세션(일지 2026-10-23-32)이 PR #369를 병합한 뒤 `next-session`의 지시문으로 06·07을 나란히 열었고, 이 세션은 그 둘째다. 첫 메시지는 아래다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/07-gates-and-official-cost.md
>
> 다음 작업: .scratch/model-rerun/issues/07-gates-and-official-cost.md. 결과 커밋을 새로 꺼낸 작업 트리에서 게이트 셋과 원래 PR의 숨은 시험을 돌고, 세션 기록으로 공식 단가의 비용을 셈한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 07-gates-and-official-cost)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/07-gates-and-official-cost.md
> 브랜치: feature/07-gates-and-official-cost
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-32-round-clone.md의 "다음", 나란히 여는 나머지 티켓 .scratch/model-rerun/issues/06-round-drive-record.md
> 이어받을 상태: 티켓의 "04에서 넘어온 메모" 셋째 항목은 링크를 끊는 `_cut_links`의 사본을 둘(`tools/canary.py`, `tools/rerun_round.py`)로 적었지만, 그 메모를 쓴 뒤 합친 #363이 `tools/rerun_hidden.py`에 셋째 사본을 들였다(PR #369 claude-review 둘째 회차의 Minor, 보류 이유는 그 PR 코멘트). 그래서 메모의 "셋째로 쓰게 되면 둘을 모은다"는 전제가 틀렸고, 셋을 모을지는 이 티켓이 정한다. 같은 회차의 Nit(`SetupFailed.exit_code`가 `SetupEnd.EXITED`일 때만 값이 있다는 불변식을 주석으로만 적었다)도 메모 둘째 항목(01의 `SetupFailure`와 끝난 꼴을 맞추는 자리)에서 함께 정한다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

그 뒤 사용자 프롬프트는 없었다. 구현 도중 컨텍스트가 한 번 자동 압축됐다.

## 구현

- 게이트와 숨은 시험은 `tools/rerun_gates.py`의 `check_result`이고, 시험은 `tests/tools/test_rerun_gates.py`다. 원본에서 M의 숨은 시험 파일과 지원 파일을 `git cat-file`로 먼저 읽고, 회차 폴더의 `gate`에 결과 커밋을 `git worktree add --detach`로 꺼내 04의 `run_setup`으로 준비한 뒤 게이트 셋을 돈다. 그 뒤 M의 파일을 덮어 숨은 시험의 노드만 pytest로 돌리고 junit xml로 센다. 어느 길에서도 `finally`에서 작업 트리를 걷는다.
- 게이트 셋은 30분 몫 하나를 함께 쓰고, 앞 게이트가 실패하거나 시간을 넘겨도 셋을 다 돈다. 넘긴 게이트는 프로세스 트리째 끈다. 숨은 시험은 게이트가 실패해도 돈다(판정 03이 두 결과를 따로 본다).
- junit 셈은 노드 ID를 pytest가 junit에 쓰는 꼴(pytest의 `mangle_test_address`: 매개변수 `[` 앞에서 자르고 `::`로 나눈다)로 옮겨 `classname`과 `name`으로 찾는다. 같은 노드의 `testcase`가 여럿이면(호출과 정리 단계의 오류) 하나라도 나쁘면 실패다. XML은 표준 라이브러리 파서로 푼다. 이 PC의 파이썬 3.12.10은 expat 2.7.1이라 엔터티 증폭이 막히고, `ElementTree`는 바깥 엔터티를 풀지 않는다(새 의존성 defusedxml은 ADR이 들어 들이지 않았다).
- 자식(준비, 게이트, pytest, git)은 부르는 쪽이 넘긴 환경으로 띄우고, 거기서 `REPO_LOCATION_VARS`와 `VIRTUAL_ENV`를 벗기며 git에는 `GIT_TERMINAL_PROMPT=0`을 더한다. 결과 커밋과 클론의 `.git`이 세션이 쓴 것이라 그 안의 코드가 이 환경으로 돌기 때문이다.
- 공식 단가는 `tools/rerun_cost.py`이고, 시험은 `tests/tools/test_rerun_cost.py`다. 세션 하나(본 세션 기록과 그 `subagents/`)의 셈 `session_cost`, 값만 받는 `cost_of`, 회차의 합 `round_cost`다. 응답은 message id로 한 번만 세고 출력이 가장 큰 usage를 쓴다(장부 `read_stream`과 같다). 캐시 쓰기는 5분과 1시간 몫으로 나누고 합이 맞지 않으면 남는 몫을 5분으로 본다. Haiku 5.5는 응답마다 프롬프트가 10만 토큰을 넘으면 높은 단가다. 기록에 응답이 없는 모델은 `modelUsage`를 5분 배수로 대신 셈해 따로 적는다. 커밋한 프로브 원본의 응답 usage에 생각 토큰 칸이 없어 생각 합은 빈 값이다.
- 01의 `SetupFailure`에 시간 넘김 칸을 더했고(`tools/rerun_files.py`), 읽기는 시간을 넘긴 명령에 종료 코드가 있거나 실패한 준비의 종료 코드가 0이면 거부한다. 명세 "회차 기록"의 결과 줄과 숨은 시험 줄에 2026-10-23 주석을 달았다.

## 정한 것

- 링크 끊기를 모았다. `tools/tidy_checkouts.py`에 공개 함수 `cut_links`를 두고 다시 풀기 도구 셋(`tools/rerun_round.py`, `tools/rerun_hidden.py`, `tools/rerun_gates.py`)이 함께 쓴다. `tools/canary.py`의 사본은 두었다. canary는 경로로 띄우는 스크립트라 `tools.` 패키지를 import하면 깨지고(같은 모양인 `tools/rerun_round.py`를 경로로 띄워 import 오류를 손으로 봤다), 그래서 `.claude/rules/tools.md`의 선례 문장도 그대로다. `tools/rerun_hidden.py`의 프로세스 트리 끄기는 `kill_tree`로 공개해 게이트가 함께 쓴다.
- PR #369의 Nit는 `SetupFailed.__post_init__`이 끝난 꼴과 종료 코드의 짝이 맞지 않으면 `ValueError`를 내게 해 닫았다.
- 04 메모의 `NOT_STARTED`는 위의 시간 넘김 칸으로, 덮는 경로의 링크는 02의 `overlay_target`으로, 01 메모의 남은 게이트는 셋을 다 도는 것으로 정했다(티켓의 구현 메모).
- 10이 부를 꼴과 `GateError`를 무엇으로 적을지의 판단은 10의 "07에서 넘어온 메모"로 넘겼다.

## 변이

- `.scratch/model-rerun/probes/rerun_gates_mutations.toml`(38)과 `rerun_cost_mutations.toml`(23)을 지었다. 결과와 표지를 바꾼 까닭은 그 디렉터리 README의 변이 절이다.
- 게이트 표는 처음 돌린 판에서 서른넷 모두 빨갰지만 열여섯이 표지가 어긋났다. 표지를 출력을 보기 전에 짐작으로 달았고, pytest가 긴 비교를 줄여 찍어 `assert Hidden(...)` 줄이 출력에 실리지 않았다. 펼친 줄(`passed: 0 != 5`)은 변이 도구가 판정 낱말뿐이라고 받지 않았고, `-vv`로는 여전히 줄여 찍혀 `-vvv`를 줬다.
- 공식 단가 표는 셋 이상 `isclose`를 단언하는 시험의 변이에 미리 셈한 값을 표지로 넣었고, 둘은 diff 방향을 거꾸로 짐작해 어긋났다.

## 커밋 전 반박 검증

`.claude/rules/tools.md`의 "지우거나 덮어쓰는 도구와 그 절차는 커밋 전에 임시 저장소에서 반박해 본다"를 따라, 서브에이전트 하나에 게이트 작업 트리를 걷는 길을 깨려는 입력을 실제 폴더와 프로세스로 재현하게 했다. 같은 체크아웃에서 변이 표가 소스를 바꾸고 있어, 변이가 없을 때 뜬 `tools/` 사본을 세션 스크래치패드에 두고 그것을 import하게 했다. 스크립트는 커밋하지 않았다.

- 깬 것은 둘이다. 하나는 클론의 관리 폴더(`.git/worktrees/gate/`) 안에 게이트 명령이 심은 junction이다. `git worktree remove --force --force`가 관리 폴더를 지우며 따라가, 바깥 파일과 원본 저장소의 `.git`을 알림 없이 지웠다(이 PC의 git 2.32). 다른 하나는 숨은 시험 뒤에 `gate` 자리가 바깥을 가리키는 junction으로 바뀐 경우다. `cut_links`가 그 뿌리를 따라가 바깥 트리 안의 링크를 깊이와 상관없이 모두 끊었다. 둘 다 결과 커밋의 코드가 일부러 심어야 닿는 길이지만, 원본을 지울 수 있어 막았다.
- 고친 것: 걷기 전에 관리 폴더 안의 링크도 끊고, 작업 트리 자리나 클론의 `.git`이나 관리 폴더 자체가 링크면 걷지 않고 알린다. `cut_links`는 뿌리가 링크면 따라가지 않고 그 뿌리를 돌려준다. 새 시험 셋은 고치기 전에 빨간 것을 봤고, 클론의 `.git` 갈래는 구현 뒤에 매개변수로 더해 변이로 빨강을 봤다.
- 지킨 것: 작업 트리 안의 여러 링크(클론·회차 폴더·원본·조상을 가리키는 junction, 바깥 파일을 가리키는 파일 심볼릭 링크), 원본을 가리키게 고친 `gate/.git` 파일과 링크로 바꾼 관리 폴더 자체, 커밋하지 않은 파일과 읽기 전용·260자를 넘는 경로, 파일을 쥔 손자, 등록만 남은 자리, 짧은 이름과 대소문자가 다른 회차 폴더 경로. 끝이 점이나 공백인 이름과 파일을 쥔 손자는 git이 걷지 못했고, 둘 다 `out`으로 알리고 폴더를 남겼다.
- `tools/canary.py`의 사본 `_cut_links`도 코드를 읽으면 뿌리가 링크일 때 따라간다(돌려 보지는 않았다). canary가 걷는 대조군 워크트리는 이 티켓의 경로가 아니라 이번에는 고치지 않았고, 회고의 후보로 둔다.

## 인계

- 이 세션의 제목은 `feature/07-gates-and-official-cost`였다. 컨텍스트가 약 36만 토큰으로 문턱(20만)을 넘은 채 `셀프 리뷰 직전`에 와 인계 계기가 왔고, `next-session`의 인계 줄로 넘긴다. 셀프 리뷰는 새 세션이 하고, 이 세션은 커밋하지 않았다.
- 이 세션이 번복하거나 고친 것: 처음 쓴 걷기 시험이 private `_hidden`을 `# pyright: ignore`로 건드려, 공개 `count_hidden`을 monkeypatch하는 쪽으로 고쳤다(원칙 III). 변이 표지는 위 변이 절대로 출력을 본 뒤 다시 달았고, 반박 검증이 낸 두 결함은 위 절대로 고쳤다.
- 인계 직전에 `uv run python tools/run_checks.py`를 백그라운드로 띄웠고, 인계하며 멈췄다. 멈추기 전에 끝난 검사 가운데 check-instructions만 빨갰다: `tools/rerun_gates.py:294: listed 의 반환이 bool | None 이다. 세 값으로 갈래를 고르는 꼴이라 열거(enum.Enum)로 둔다(CODING_STANDARDS.md 불리언 플래그 인자)`. check-ticket, zizmor, lint-imports, check-type-escapes, pyright, pyright-linux는 통과했고, pytest와 web은 결과를 보기 전에 멈췄다.
- 회고 후보(단계를 닫는 세션의 retro가 판정한다)
  - 변이 표지를 출력을 보기 전에 짐작으로 달아 열여섯이 어긋났다. `.claude/rules/probes.md` 첫 항목의 "고르기 전에 변이를 손으로 넣어 실패 출력을 한 번 보고"를 어겼다.
  - `git worktree remove --force --force`가 관리 폴더(`.git/worktrees/<이름>/`) 안의 junction도 따라가 지운다는 것(이 PC의 git 2.32, 반박 검증이 재현했다)을 `.claude/rules/tools.md`의 지우는 도구 항목에 보탤지.
  - `tools/canary.py`의 `_cut_links`도 뿌리 링크를 따라간다(코드를 읽어 봤고 돌려 보지 않았다).
- 인계 줄로 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/07-gates-and-official-cost.md. 결과 커밋을 새로 꺼낸 작업 트리에서 게이트 셋과 원래 PR의 숨은 시험을 돌고, 세션 기록으로 공식 단가의 비용을 셈한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/07-gates-and-official-cost.md
브랜치: feature/07-gates-and-official-cost
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-37-gates-and-official-cost.md의 "인계" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-23-37-gates-and-official-cost.md. 구현·변이·커밋 전 반박 검증은 마쳤고 일지에 셀프 리뷰·회고·다음 절이 아직 없다. 인계 직전에 돌던 run_checks를 멈췄고, 멈추기 전에 check-instructions가 tools/rerun_gates.py:294의 listed 반환(bool | None)을 열거로 두라고 빨갰다. 셀프 리뷰 반영에 함께 고치고, 고친 뒤 rerun_gates_mutations.toml의 원문이 그 자리를 가리키면 맞춘다. pytest와 web은 결과를 보지 못했다. 리뷰 반영 뒤 손댄 변이 표 넷(rerun_gates, rerun_cost, rerun_hidden, rerun_round)을 다시 돈다. 회고 후보 셋은 일지 인계 절
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/07-gates-and-official-cost (인계함)`으로 바꿨고, run_checks 대기를 멈췄고, 워크트리 잠금을 풀었다.
- open-session을 부른다 2026-10-23T06:17:57Z

## 이어 받은 세션

인계 지시문으로 연 새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 사용자 프롬프트는 위 인계 줄의 지시문 그대로였다. 먼저 인계가 남긴 check-instructions의 빨강을 고쳤다. `_Git.listed`(반환 `bool | None`)를 세 값 열거 `Registration`(`LISTED`·`ABSENT`·`UNKNOWN`)을 돌려주는 `registration`으로 바꾸고, 그 자리를 가리키던 `rerun_gates_mutations.toml`의 원문을 맞춰 `tools/mutate.py --check`로 38 모두 원문이 있음을 봤다. 바뀐 시험 파일 일곱(`test_rerun_gates`, `test_rerun_cost`, `test_rerun_files`, `test_rerun_judge`, `test_rerun_round`, `test_tidy_checkouts`, `test_rerun_hidden`)은 616 통과였다(335초).

## 셀프 리뷰

범위: 기준 `c2c03eae`, 바뀐 파일 14, 커밋 0, 미추적 7. 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다. 표준 축은 Critical·Major 없이 Minor·Nit만 냈고, 명세 축은 Major 하나를 냈다.

표준 축이 낸 것과 판정.
- Minor, 고친다: `tools/rerun_gates.py`의 XML 문장이 출처를 "파이썬 문서의 XML 취약점 표"로만 적었다. 이 세션이 그 표를 읽은 것은 웹 요약이다. 웹 요약이라고 주소와 함께 적고, 이 PC의 동작은 시험으로 고정한다.
- Minor, 고친다: 못 보는 것의 "`--continue-on-collection-errors`를 줘도 같았다"를 이 모듈의 시험이 고정한다고 읽힌다. 시험은 기본 인자만 쓴다. 손으로 본 것과 시험이 고정한 것을 가른다. 나머지 못 보는 것 넷을 시험으로 고정하라는 몫은 남긴다. 그 규칙(`.claude/rules/tools.md`의 못 보는 것 항목)은 훅과 검사의 독스트링이 대상이다.
- Minor, 고친다: `tools/rerun_cost.py`의 "장부 `read_stream`과 같은 셈"은 넘친다. 장부는 기록 파일마다 세고 시각이 없는 응답을 버리며, 모델이 없는 줄을 `(모름)`으로 센다.
- Minor, 고친다: 프로브 원본의 셈이 `costUSD`와 맞지 않는 까닭("출력 토큰이 끝까지 쌓이기 전의 값")은 재지 않은 해석이다. 어림이라고 적는다.
- Minor, 고친다: `.scratch/model-rerun/issues/05-task-selection.md`의 메모가 `rerun_hidden`의 `_cut_links` 사본을 아직 미결로 적는다(명세 축도 같은 것을 냈다). 07의 "04에서 넘어온 메모"는 받은 메모의 기록이고 답은 같은 티켓의 구현 메모에 있어 두었다.
- Nit, 고친다: 걷기 차례 7의 "반박 검증에서 지워졌다"에 근거의 종류(서브에이전트가 임시 저장소로 재현, 스크립트는 커밋하지 않음)가 없다.
- Nit, 고친다: `SetupFailed.__post_init__`이 `EXITED`에 종료 코드 0을 막지 않는다.
- smell, 고친다: `_overlay`가 파일을 쓰며 참·거짓을 돌려준다(`CODING_STANDARDS.md` CQS). `_Git.logged`는 실패를 글로, 같은 클래스의 `read`는 `GateError`로 낸다(실패의 형태는 층마다 하나). `check_result`의 `finally`에 조건이 있다(에러 처리와 정상 흐름 분리).
- smell, 남긴다: `rerun_gates`의 등록 열거·걷기·`_run`·`_last_line`·환경 벗기기가 `rerun_hidden`의 같은 모양의 둘째 사본이다. 05의 세션이 지금 `tools/rerun_hidden.py`를 고치고 있고(형제 워크트리 `05-task-selection`), `rerun_hidden`이 걷는 작업 트리는 원본 저장소 자신의 커밋이라 결과 커밋의 코드가 링크를 심는 위협이 없다. 05의 메모로 넘긴다.
- smell, 남긴다: 한 파일에 junit 셈·러너·git·걷기·조립이 함께 있다. 위 사본을 모을 때 함께 나눈다.
- smell, 남긴다: `(exit_code, timed_out)` 두 칸은 01의 기록 꼴(`Gate`)이다. 디스크 꼴을 바꾸는 일이라 이 티켓의 몫이 아니다.
- smell, 남긴다: 시험의 `_usd`가 셈을 다시 적는다. 시험 쪽 셈은 코드와 따로 적었고 단가와 배수 상수는 다른 시험이 값으로 못 박아, 코드의 셈을 바꾸면 빨개진다. `count_hidden`·`cut_links`를 monkeypatch하는 시험은 공개 이름이라 둔다.

명세 축이 낸 것과 판정.
- Major, 고친다: 덮기 전에 `gate` 자리 자체가 링크인지 보지 않는다. `overlay_target`은 뿌리 아래 조각만 본다. 게이트 뒤 덮기 전에 그 자리가 바깥을 가리키는 링크로 바뀌면 M의 파일이 바깥에 쓰이고 pytest도 거기서 돈다. 서브에이전트가 `overlay_target(<junction인 gate>, "tests/test_calc.py")`이 바깥 아래 경로를 돌려주는 것을 스크래치로 봤다.
- Minor, 고친다: "숨은 시험은 게이트가 실패해도 돈다"의 근거("판정 03이 두 결과를 따로 본다")가 틀렸다. `tools/rerun_judge.py`의 `solved`와 `solved_without_hidden`은 둘 다 게이트 초록을 요구하고, 숨은 시험 결과는 `solved`만 읽는다. 명세의 "끝남인 회차에서만" 주석과 같은 까닭(판정과 되풀이에 쓰이지 않는 결과는 짓지 않는다)으로, 게이트가 하나라도 0으로 끝나지 않으면 숨은 시험을 돌지 않는다. 01의 읽기는 게이트가 있고 숨은 시험이 빈 회차를 받는다.
- Minor, 고친다: 10에 넘긴 메모에 `session_cost`의 `FileNotFoundError`와 `check_result`가 `GateError` 밖으로 올리는 예외(회차 폴더에 로그를 쓰지 못한 `OSError`)가 없다. 서브에이전트가 든 셋 가운데 UTF-8이 아닌 junit xml의 `UnicodeDecodeError`는 메모가 아니라 코드를 고친다. 세션의 코드가 쓴 xml이라 풀지 못하면 모든 노드가 실패여야 한다.
- Nit, 고친다: `rerun_cost`가 `message.model`이 없는 응답을 조용히 뺀다. 비용이 낮게 나오는 길이라 `PriceError`로 올린다.
- Nit, 넘긴다: `rerun_hidden._remove_checkout`은 뿌리가 링크면 걷지 않는데 알림은 "안의 링크를 끊지 못해"다. 05의 세션이 그 파일을 고치고 있어 05의 메모로 넘긴다.

반영.
- 고친 것: 위의 "고친다"를 모두 고쳤다. 명세 축의 Major는 두 자리에서 막는다. `overlay_target`이 작업 트리 자리 자체가 링크인지 보고, `_run`이 띄우기 전에 작업 자리가 링크인지 본다(뒤의 것은 준비 뒤에 자리가 링크로 바뀌면 게이트가 바깥에서 도는 길이다). 그 시험의 첫 판은 게이트 명령이 스스로 자리를 옮기게 지었는데 윈도에서 `WinError 32`로 실패해, 준비(`run_setup`)를 감싸 그 뒤에 옮기는 판으로 바꿨다. CQS와 실패의 형태는 `_overlay`가 `_NotOverlaid`를 던지고, `_Git.logged`가 `GateError`를 던지며, 꺼내기와 걷기를 컨텍스트 관리자 `_gate_worktree`로 묶어 고쳤다. 반영으로 새로 쓴 사실 문장은 PR 직전 `bug-perf-review`의 밀 주장이다. 원문은 아래와 같다.
  - `tools/rerun_gates.py` 차례 4: "작업 트리 자리가 링크로 바뀌어 띄우지 않은 게이트는 종료 코드도 시간 넘김도 없다. 링크인 자리에서 띄우면 결과 커밋이 아니라 그 링크가 가리키는 바깥에서 돈다."
  - 같은 파일 차례 5: "게이트가 모두 0으로 끝났을 때만 숨은 시험을 돈다. 판정(`tools/rerun_judge.py`의 `solved`)이 게이트가 초록일 때만 숨은 시험을 읽어, 다른 회차의 숨은 시험은 쓰이지 않는다." "작업 트리 자리나 덮을 자리의 상위 폴더나 그 자리가 링크면 (`tools/rerun_hidden.py`의 `overlay_target`) 덮지 않고 모든 노드를 실패로 센다."
  - 같은 파일 차례 7: "이 티켓의 커밋 전 반박 검증에서 서브에이전트가 임시 저장소로 재현했고, 바깥 파일과 원본 저장소의 `.git`이 지워졌다. 그 스크립트는 커밋하지 않았고, 이 모듈의 시험이 그 길을 고정한다"
  - 같은 파일 junit의 셈: "XML이 없거나 UTF-8로 읽히지 않거나 풀리지 않는 것은 실패다." "파이썬 문서의 XML 취약점 표(https://docs.python.org/3.12/library/xml.html. 이 티켓은 웹 요약으로 읽었다)는 `ElementTree`가 바깥 엔터티를 풀지 않고 expat 2.4.1부터 엔터티 증폭(billion laughs)이 막힌다고 적는다. 이 PC의 파이썬 3.12.10(expat 2.7.1)에서 그 둘을 이 모듈의 시험이 고정한다."
  - 같은 파일 못 보는 것: "`--continue-on-collection-errors`를 줘도 같았다(이 PC의 pytest에서 스크래치로 손으로 봤다. 기본 인자로 돌린 그 동작은 이 모듈의 시험이 고정한다)" "준비 명령 사이에 자리가 바뀌는 일도 막지 않는다. 04의 `run_setup`은 명령마다 그 자리를 보지 않는다."
  - `tools/rerun_cost.py`: "모델이 없는 응답은 `PriceError`다. 빼면 그 응답의 비용이 셈에서 빠져 낮게 나온다." "여기까지는 사용량 장부(`tools/token_report.py`의 `read_stream`)와 같다. 장부와 달리 세션의 기록 파일을 모두 이어 붙여 한 번에 세고, 시각이 없는 응답도 세며, 모델이 없는 응답을 `(모름)`으로 세지 않는다." "(셀프 리뷰의 두 서브에이전트가 손으로 대 0.03766과 0.03946을 봤다)" "까닭은 어림이고 재지 않았다."
  - `tests/tools/test_rerun_gates.py`의 링크로 바뀐 자리 시험: "가상 환경의 `python.exe`로 띄운 자식은 옮기지 못했고 기반 인터프리터로 띄운 자식은 옮겼다(2026-10-23 스크래치로 손으로 봤다). 가상 환경의 `python.exe`는 기반 인터프리터를 자식으로 띄우는 런처라, 그 런처가 자리를 쥔 것으로 본다."
  - `.scratch/model-rerun/spec.md` 숨은 시험 줄의 주석: "숨은 시험은 게이트 셋이 모두 0으로 끝난 회차에서만 돈다. 판정의 "풀었다"(`tools/rerun_judge.py`의 `solved`)가 게이트가 초록일 때만 숨은 시험을 읽어, 다른 회차의 숨은 시험은 판정과 되풀이에 쓰이지 않는다." "(작업 트리 자리 자체가 링크로 바뀐 때 포함)". 결과 줄의 주석: "작업 트리 자리가 링크로 바뀌어 띄우지 않았다(시간 넘김 거짓)".
  - `.scratch/model-rerun/issues/10-schedule-and-budget.md`의 "07에서 넘어온 메모": "게이트가 하나라도 0으로 끝나지 않으면 `hidden`이 빈 값이다." "`check_result`는 회차 폴더에 로그를 쓰지 못하면 `GateError`가 아니라 `OSError`를 그대로 올린다." "단가가 없는 모델과 모델이 없는 응답은 `PriceError`다. 본 세션 기록 파일이 없으면 `FileNotFoundError`다."
  - `.scratch/model-rerun/issues/05-task-selection.md`의 2026-10-23 괄호: "07의 `tools/rerun_gates.py`가 `rerun_hidden`의 작업 트리 등록 열거(`_Registration`)·걷기(`_remove_checkout`)·`_run`·`_last_line`·환경 벗기기(`_env`)와 같은 모양의 둘째 사본을 두었고" "`_remove_checkout`은 이제 뿌리가 링크면 걷지 않는데(`cut_links`가 뿌리를 돌려준다) 알림은 "안의 링크를 끊지 못해"라고 적는다."
  - 티켓 07의 구현 메모: 덮는 경로 항목과 숨은 시험이 게이트가 모두 0일 때만 도는 항목.
  - 프로브 README 변이 절의 2026-10-23 셀프 리뷰 반영 문단 넷(hidden, round, gates, cost).
- 남긴 것과 이유: 표준 축의 "남긴다" 넷(둘째 사본, 파일 크기, 두 칸의 기록 꼴, 시험의 `_usd`와 monkeypatch)과 명세 축의 "넘긴다" 하나는 위 판정의 까닭대로 두었다. 못 보는 것 넷을 시험으로 고정하라는 몫도 위 까닭대로 남겼다. 엔터티 시험 둘은 표준 라이브러리의 동작을 고정하는 시험이라 이 저장소 코드의 변이로는 빨개지지 않는다. 그래서 변이 표에 넣지 않았다.
- 다시 돌린 명령과 결과: 변이 표 넷을 전부 다시 돌렸다(`PYTHONUTF8=1 uv run python tools/mutate.py <표>`). hidden 24와 cost 23은 모두 기대대로였다. gates 38은 둘, round 57은 둘이 어긋났다. 까닭과 고친 것은 프로브 README 변이 절이다. round의 하나는 07이 모은 `cut_links`의 뿌리 확인이 지우기 직전의 확인과 겹쳐 초록이었고, 시험에 까닭의 단언을 더해 빨강을 되찾았다. 리뷰가 더한 갈림을 겨누는 변이 다섯(gates 셋, hidden 하나, cost 하나)을 더했다. 고친 것과 더한 것을 번호로 다시 돌려 모두 고른 표지까지 기대대로 빨갰다(gates 41, cost 24, hidden 25, round 57, 대조군 하나). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고, 그 결과는 커밋 뒤에 적는다. 커밋 전에 린트 둘(`uv run ruff check .`, `uv run ruff format --check .`)이 초록이었고, `uv run python tools/run_checks.py`가 종료 0으로 열 모두 통과했다(pytest 336.2초, web-verify 262.2초, run-hooks 103.5초).

회고 후보(단계를 닫는 세션의 retro가 판정한다).
- 인계 절의 셋(짐작으로 단 변이 표지, `git worktree remove`가 관리 폴더 안의 junction을 따라가는 것, `tools/canary.py`의 `_cut_links`가 뿌리 링크를 따라가는 것).
- 리뷰를 반영하며 두 겹으로 막은 자리(`cut_links`의 뿌리 확인과 04의 지우기 직전 확인)가 옛 변이 하나를 초록으로 만들었다. 겹친 방어는 실패의 까닭까지 단언해야 변이가 그 겹을 가른다. 같은 모양이 다시 나면 `.claude/rules/probes.md` 첫 항목에 보탤 후보다.
- 새 시험이 옛 변이의 `-k`(`링크로_바뀌면 and gate`)에 걸려 먼저 빨개져 표지가 어긋났다. 모듈 이름에 든 낱말(`gate`)을 `-k`의 거르는 낱말로 쓴 것이 원인이라고 어림한다.
- 링크로 바뀐 자리 시험의 첫 판이 윈도에서 게이트 명령이 제 작업 자리를 옮기지 못해(`WinError 32`) 실패했다. 가상 환경의 `python.exe` 런처가 자리를 쥐는 것으로 보고, 자리를 바꾸는 일을 준비를 감싼 대역에 맡겼다.

## 커밋

- 5030de40 `feat: 결과 커밋을 꺼낸 작업 트리에서 게이트와 숨은 시험을 돌고 공식 단가로 셈한다 (model-rerun 07)`. pre-commit이 모두 통과했다(ruff 둘, 러너의 열: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright·pyright-linux·run-hooks 175.3초·web-verify 340.8초·pytest 449.0초, 마크다운 표, 줄 구분 문자, 변이 표 원문, 커밋 메시지). 카나리아 명세와 헌법 판은 대상 파일이 없어 `Skipped`였다.
- 인용 대조가 막지 않는 경고 셋을 냈다. 이 일지 46행의 `.claude/rules/tools.md` 인용은 그 항목의 괄호(도구를 부르는 스킬의 단계 포함)를 뺀 줄임이다. 이 일지 91행의 인용은 표준 축 보고의 말이고, 프로브 README 변이 절의 인용은 시험 출력이라 저장소에 글자 그대로 없다. 커밋한 판에서는 고치지 않았다.

## 인계(커밋 뒤)

- 이 세션의 제목은 `feature/07-gates-and-official-cost`였다. 커밋 직후 컨텍스트가 약 30만 토큰으로 문턱(20만)을 넘은 채 `커밋 뒤`에 와 인계 계기가 왔다. 넘겨받은 경계(`셀프 리뷰 직전`)와 달라 `next-session`의 인계 줄로 넘긴다. `get_session`의 `self`에 `parentSessionId`가 없었다.
- 이 세션이 번복하거나 고친 것: 변이 표 넷을 다시 돌려 어긋난 넷(gates 3·16, round 30·45)을 고쳤다. round 45는 시험이 이름만 보던 단언에 까닭의 단언을 더해 빨강을 되찾았다(시험 고침, 위 반영 줄). 리뷰가 더한 갈림을 겨누는 변이 다섯을 더했다.
- 남은 단계: origin/main(db92d68, #366. 이 브랜치의 파일과 겹치지 않는다)을 합치고, PR 직전 리뷰를 한다. CodeRabbit CLI는 `Seat: not assigned`라 대체 둘(`/security-review`, `bug-perf-review`)이다. `bug-perf-review`의 브리프에는 위 반영의 "고친 것" 줄에 원문으로 옮긴 문장을 밀 주장으로 나열한다. 그 뒤 PR, 봇 회차, 워크트리 병합 길, `next-session`이다. 회고 후보는 인계 절과 셀프 리뷰 절의 둘이다.
- 인계 줄로 낸 지시문:

```
다음 작업: .scratch/model-rerun/issues/07-gates-and-official-cost.md. 결과 커밋을 새로 꺼낸 작업 트리에서 게이트 셋과 원래 PR의 숨은 시험을 돌고, 세션 기록으로 공식 단가의 비용을 셈한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-rerun/issues/07-gates-and-official-cost.md
브랜치: feature/07-gates-and-official-cost
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-37-gates-and-official-cost.md의 "인계(커밋 뒤)" 절과 셀프 리뷰 절의 "반영"
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영과 변이 표 넷의 재실행을 마치고 5030de40으로 커밋했다(pre-commit 모두 통과). 아직 푸시하지 않았고 PR이 없다. 일지의 커밋 절과 인계 절은 커밋하지 않았다. 남은 단계는 origin/main 합치기, PR 직전 리뷰(CodeRabbit CLI는 좌석이 없어 /security-review와 bug-perf-review. bug-perf-review의 밀 주장은 일지 셀프 리뷰 절 "고친 것" 줄의 원문), /git-pr, 봇 회차, 워크트리 병합 길이다. docs/journal/2026-10-23-37-gates-and-official-cost.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/07-gates-and-official-cost (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었고, 워크트리 잠금은 이미 풀려 있었다(`is not locked`).
- open-session을 부른다 2026-10-23T07:46:15Z

## 이어 받은 세션(둘째)

인계(커밋 뒤) 절의 지시문으로 연 새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 사용자 프롬프트는 그 지시문 그대로였고, 그 뒤 사용자 프롬프트는 없었다. PR 직전 리뷰를 반영하던 도중에 컨텍스트가 한 번 자동 압축됐다.

- origin/main을 합쳤다(90f9f675). 그때 origin/main은 인계 절이 적은 db92d68 뒤에 06의 PR #370(893e0fe8)이 더 병합된 상태였다. 충돌은 둘(`.scratch/model-rerun/probes/README.md`, `.scratch/model-rerun/issues/10-schedule-and-budget.md`)이고, 둘 다 06의 행·메모를 앞에, 07의 것을 뒤에 두어 풀었다. 합치기 커밋의 pre-commit은 모두 통과했다.

## PR 직전 리뷰

CodeRabbit CLI는 `Seat: not assigned`라 대체 둘(`/security-review`, `bug-perf-review`)로 했다. `bug-perf-review`는 게이트 쪽(`tools/rerun_gates.py`와 링크 끊기)과 공식 단가 쪽(`tools/rerun_cost.py`) 둘로 나눠 띄웠고, 브리프에 셀프 리뷰 절 "고친 것" 줄의 원문을 밀 주장으로 나열했다.

- `/security-review`: 지적 0. 찾기 서브태스크가 확신도 0.7을 넘는 후보를 내지 않아 걸러 낼 것도 없었다. 지적이 아닌 참고로, 이 도구가 세션이 쓴 결과 커밋의 코드를 샌드박스 없이 돈다는 점을 들었다. 모듈 독스트링이 적은 설계다.
- 공식 단가 쪽(유효 2, 보류 1, 오탐 5)과 판정.
  - Major, 고친다: `transcript_lines`가 `splitlines()`로 기록 줄을 가른다. Node의 JSON 직렬화는 U+2028·U+2029·U+0085를 이스케이프하지 않아, 글에 그 글자가 든 응답 줄이 둘로 갈려 풀리지 않고 셈에서 조용히 빠진다. 형제 `tools/rerun_session.py`와 장부 `tools/token_report.py`는 같은 까닭으로 `\n`으로만 가른다. 밀 주장 2("여기까지는 장부와 같다")의 다른 점 목록에서도 이것이 빠졌다.
  - Minor, 고친다: 10의 "07에서 넘어온 메모" 셋째 줄(걷지 못하면 결과를 그대로 돌려주고 `out`으로만 알린다)은 걷는 git의 로그를 쓰지 못하는 길에서 거짓이다. `_remove`는 `GateError`만 잡아 `OSError`가 알림 없이 오른다.
  - 보류였으나 고친다: `modelUsage`에 `X`와 `X[1m]`이 함께 있고 기록에 `X`의 응답이 없으면 세션 하나의 `Cost.substitutes`에 이름이 같은 항목이 둘 든다. 회차 합(`round_cost`)은 이미 합치므로 세션 하나도 같이 합치는 것이 한 줄이었다.
  - 선택 제안, 하지 않는다: 풀지 못한 줄 수를 `Cost`에 싣는 일. 줄 가르기를 고치면 남는 풀지 못한 줄은 잘린 마지막 줄뿐이고, 그것은 독스트링의 못 보는 것에 있다.
  - 밀 주장 대조: 1·3·4·6은 맞았다. 3은 커밋한 원본으로 다시 셈해 0.03766223과 0.03945573을 보고 차이 0.0017935가 출력 칸에서만 난다고 덧붙였다. 7은 수가 모두 맞고, hidden 문단이 22에서 "변이 24 전부"로 건너뛰어 둘의 출처가 없다(Nit).
- 게이트 쪽(유효 5, 보류 2, 오탐 6)과 판정.
  - Major, 고친다: `cut_links`가 `long_path`를 쓰지 않는다. 이 PC는 `LongPathsEnabled=0`이라 MAX_PATH에 걸리는 깊은 폴더(게이트 작업 트리의 `web/node_modules/.pnpm` 아래)를 `os.scandir`하지 못해 그 폴더가 끊지 못한 것으로 세어지고, `_remove`가 작업 트리를 걷지 않는다. 서브에이전트가 452자 트리로 재현했다(스크래치, 실제 pnpm 설치로는 돌리지 않았다).
  - Minor, 고친다: 바깥 엔터티 시험이 엔터티를 속성 값에 써서, 푸는 파서에서도 오류라 주장을 가르지 못한다.
  - Minor, 고친다: `hidden_tests`가 빈 과제면 pytest를 노드 없이 띄워 결과 커밋의 시험 전체를 돈다.
  - Minor, 고친다: `count_hidden`이 겹친 노드를 `failed`에 두 번 넣고, 01의 기록 읽기가 그것을 거부한다.
  - Minor, 고친다: 모듈 독스트링 차례 5의 "다른 회차의 숨은 시험"은 가리키는 것이 코드에 없다(명세의 같은 주석도).
  - 보류, PR 체크리스트에 남긴다: 밀 주장 5의 `--continue-on-collection-errors` 문장과 밀 주장 6의 런처 문장은 스크래치로 손으로 본 기록이고 재현하지 못했다. 두 문장 모두 손으로 봤다고 적혀 있어 측정처럼 읽히지 않고, 코드 위험이 없다.
  - Minor, 남긴다: 로그(`gate.log`, `hidden.log`)에 크기 상한이 없다. 결과 커밋의 코드가 30분 몫 동안 끝없이 찍어야 닿는 길이라 이 티켓에서는 두고 PR 체크리스트에 적는다.
- 반영.
  - 고친 것: 위의 "고친다"를 모두 고쳤다. 새 시험 다섯(cost 둘, 링크 끊기 하나, 게이트 둘)은 고치기 전에 빨강을 봤고, 엔터티 시험 둘은 엔터티를 요소 본문(`&case;`가 `testcase`로 풀리는 자리)에 쓰게 바꿔 통과를 봤다. 고친 코드를 겨누던 변이 원문(gates 셋, cost 둘)을 맞추고, 변이 둘("링크 끊기가 긴 경로를 평범한 경로로 훑는다", "대신 셈에서 같은 모델을 더하지 않고 덮는다")을 더했다. 반영으로 새로 쓴 사실 문장은 아래이고, 이 반영의 셀프 리뷰 두 축에 밀 주장으로 나열했다.
    - `tools/rerun_cost.py` 독스트링: "꼬리만 다른 이름(`X`와 `X[1m]`)은 한 항목으로 더한다." "줄은 `\n`으로만 가른다. 글 안의 U+2028에서 가르면 그 응답이 셈에서 빠진다(장부의 `read_records`와 `tools/rerun_session.py`의 기록 줄 읽기와 같다)." 주석: "`splitlines`는 Node 가 이스케이프하지 않은 글 안의 U+2028 에서도 가른다"
    - `tools/tidy_checkouts.py`의 `cut_links` 독스트링: "훑기와 끊기는 `long_path` 로 한다. 윈도에서 긴 경로가 꺼져 있으면 MAX_PATH(260자)에 걸리는 깊은 폴더(게이트 작업 트리의 `web/node_modules/.pnpm` 아래)를 평범한 경로로 읽지 못해 그 폴더를 끊지 못한 것으로 냈다(티켓 07의 PR 직전 bug-perf-review). 돌려주는 경로는 넘긴 `folder` 의 꼴로 되돌린다."
    - `tools/rerun_gates.py`의 `count_hidden` 독스트링: "`nodes`에 겹친 노드는 한 번만 센다. 회차 기록 읽기가 겹친 실패 노드를 거부한다." `_hidden`의 주석: "노드 없이 띄우면 결과 커밋의 시험 전체를 돈다" 모듈 독스트링 차례 5: "판정(`tools/rerun_judge.py`의 `solved`)이 게이트 초록을 먼저 요구해, 게이트가 초록이 아닌 회차의 숨은 시험은 판정에 쓰이지 않는다. 노드가 없는 과제면 돌지 않고 0개로 센다. 노드 없이 띄운 pytest는 결과 커밋의 시험 전체를 돈다."
    - `.scratch/model-rerun/spec.md` 숨은 시험 줄의 주석: "게이트 초록을 먼저 요구해, 게이트가 초록이 아닌 회차의 숨은 시험은"
    - `.scratch/model-rerun/issues/10-schedule-and-budget.md`의 07 메모 셋째 줄: "다만 걷는 git의 로그(`gate-git.log`)를 쓰지 못하면 알림 없이 `OSError`가 오르고 그 회차의 결과도 돌려받지 못한다(위 `OSError` 줄)."
  - 다시 돌린 명령과 결과: 바뀐 시험 파일 다섯은 223 통과(`test_tidy_checkouts`, `test_rerun_cost`, 61.9초)와 186 통과(`test_rerun_gates`, `test_rerun_round`, `test_rerun_hidden`, 190.7초)였다. 변이 표 넷의 `--check`는 모두 원문이 한 번씩 있었다(gates 42, cost 25, round 57, hidden 25). 린트 둘과 줄 구분 문자 검사가 초록이었다.

## 반영분의 셀프 리뷰

범위: 기준 90f9f675, 바뀐 파일 11, 커밋 0, 미추적 0. 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다. 명세는 티켓 07과 `spec.md`이고, 요구는 위 PR 직전 리뷰에서 "고친다"로 판정한 여덟이다. 표준 축은 하드 위반 0, 밀 주장 열 가운데 아홉이 맞았다. 명세 축은 유효 하나와 판단 셋을 냈다.

표준 축이 낸 것과 판정.
- Minor, 고친다: 새 문구("게이트 초록을 먼저 요구해")가 두 자리(`tools/rerun_gates.py`의 `check_result` 주석, 게이트 시험 하나의 독스트링)에 퍼지지 않아 옛 문구("게이트가 모두 0일 때만 숨은 시험을 읽는다")와 갈렸다. 명세 축도 같은 둘과 티켓 07의 구현 메모 하나를 냈다.
- Nit, 고친다: 밀 주장 4("돌려주는 경로는 넘긴 `folder` 의 꼴로 되돌린다")는 끝에 구분자가 붙은 상대 경로(`a\`)에서 구분자가 겹쳐 거짓이다. 서브에이전트가 윈도에서 `cut_links`를 불러 봤다.
- Nit, 고친다: 새 시험 셋(노드 없음, 겹친 노드, 줄 가르기)에 짝 변이가 없다. 명세 축의 유효 하나와 같다.
- 판단, 남긴다: `cost_of`의 대신 셈 합치기와 `round_cost`의 합치기가 같은 두 줄 모양이다. 뽑으면 넘겨받은 사전을 채우는 도우미(`CODING_STANDARDS.md`의 출력 인자)가 되어 두 줄을 그대로 둔다.
- 판단, 남긴다: "줄은 `\n`으로만 가른다"가 세 모듈(`token_report`, `rerun_session`, `rerun_cost`)에 따로 적혀 있다. 모듈마다 읽는 기록이 다르고, `rerun_session`의 읽기는 비공개 함수다.
- 판단, 회고 후보로 넘긴다: `tools/canary.py`의 `_cut_links` 사본에는 이번 `long_path` 고침이 없다. 대조군 워크트리는 의존성을 깔지 않아 깊은 폴더가 덜하다고 어림한다. 인계 절의 회고 후보(그 사본이 뿌리 링크를 따라간다)에 붙인다.

명세 축이 낸 것과 판정.
- 유효, 고친다: 요구 1의 "변이 표에 항목을 더한다"가 빠졌다. `split("\n")`을 `splitlines()`로 되돌리는 변이가 없었다.
- 판단, 고친다: 프로브 README의 겨누는 것 목록과 변이 수(마흔하나, 스물넷)가 반영 전 그대로다.
- 판단, 고친다(독스트링): `..`이 든 절대 경로를 넘기면 `long_path`가 풀지 않아 `cut_links`가 그 뿌리를 읽지 못한 폴더로 준다. 고치기 전에는 그 폴더를 훑었다. 세 호출 자리 모두 남은 것이 있으면 지우거나 걷지 않고 알리므로 안전한 쪽의 실패다. 커밋하지 않은 스크래치(`dotdot_probe.py`)로 `tree\sub\..`을 넘겨 그 경로 하나가 돌아오는 것을 손으로 봤다. 코드는 두고 독스트링에 적는다.
- Nit, 고친다: 옛 문구 셋(표준 축의 Minor와 같다).
- 범위 넘침 둘(엔터티 증폭 시험도 `_CASE`로 바꿨다, 빈 노드 길에서 `hidden.log`에 한 줄을 쓴다)은 해가 없어 둔다.

반영.
- 고친 것: 옛 문구 셋을 새 문구에 맞췄다. `cut_links` 독스트링의 돌려주는 꼴 문장을 넘긴 `folder`를 머리로 두고 운영 체제의 구분자로 잇는다는 문장으로 바꾸고, 끝 구분자와 `..`의 두 예외를 적었다. 짝 변이 셋(기록 줄을 splitlines 로 가른다, 숨은 시험 노드가 없어도 pytest 를 띄운다, 겹친 노드를 겹친 채 센다)을 더했다. 프로브 README의 겨누는 것 두 칸과 변이 문단 둘을 맞추고, hidden 문단의 22에서 24로 건너뛴 둘의 출처(PR #363의 CodeRabbit Minor와 그 반영분의 셀프 리뷰, 일지 2026-10-23-18)를 적었다. 반영으로 새로 쓴 사실 문장은 아래다.
  - `tools/tidy_checkouts.py`의 `cut_links` 독스트링: "돌려주는 경로는 넘긴 `folder` 를 머리로 두고 그 아래를 운영 체제의 구분자로 잇는다. 끝에 구분자가 붙은 상대 경로면 구분자가 겹친다. `..` 이 든 절대 경로는 `long_path` 가 풀지 않아 `folder` 를 읽지 못한 폴더로 준다. 그러면 다시 풀기의 세 도구는 지우거나 걷지 않고 알린다."
  - `tools/rerun_gates.py`의 `check_result` 주석: "판정(`tools/rerun_judge.py`의 `solved`)이 게이트 초록을 먼저 요구해, 게이트가 초록이 아닌 회차의 숨은 시험은 판정에 쓰이지 않는다"
  - 티켓 07의 구현 메모: "`tools/rerun_judge.py`의 `solved`만 숨은 시험을 읽고, 게이트 초록을 먼저 요구한다."
  - 프로브 README의 gates·cost 변이 문단 끝과 hidden 문단의 PR #363 문장.
- 남긴 것과 이유: 위 "남긴다" 둘과 회고 후보로 넘긴 하나는 각 판정의 까닭대로 두었다.
- 다시 돌린 명령과 결과: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/model-rerun/probes/rerun_cost_mutations.toml`로 변이 26 전부가 고른 표지까지 기대대로 빨갰다. 게이트 표는 번호로 골라(18, 39~44) 일곱 모두 고른 표지까지 기대대로 빨갰고, `--check`는 44 모두 원문이 있었다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고, 그 결과는 커밋 뒤에 적는다.
