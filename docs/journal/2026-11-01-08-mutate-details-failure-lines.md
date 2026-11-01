# 2026-11-01 (08) mutate.py의 _details가 실패 머리 줄까지 보인다

세션 제목: `chore/036-mutate-details-failure-lines`. 컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 새 세션으로 넘긴다.

## 사용자 프롬프트 원문

> 사용자: 대기열 455를 티켓 .scratch/harness/issues/036-mutate-details-failure-lines.md로 쓰고 한다 … 다음 단계: 구현 … 브랜치: chore/036-mutate-details-failure-lines … 모델: Sonnet 5.5 / high … 이번 요청 범위: PR과 병합까지

## 한 것(커밋하기 전의 작업 트리, 기준 커밋 `544381ea`)

- 티켓 `.scratch/harness/issues/036-mutate-details-failure-lines.md`를 먼저 썼다(`tools/sibling_overlap.py`로 번호 겹침 없음을 확인했다). 대기열 455 하나만 가리킨다. 350·417·381·517은 묶지 않았다.
- 시험을 먼저 썼다. `tests/tools/test_mutate.py`에 다섯: 표지가 없으면 끝 밖의 실패 머리 줄이 보인다(들여쓴 `Expected`·`Received`와 머리가 끝 앞이라는 순서 포함), 끝 10줄에 든 머리 줄은 되풀이하지 않는다, `Errors  1 error` 같은 요약 줄은 머리가 아니다, 머리 줄은 스무 줄까지, 표지가 모두 있으면 머리 줄을 더하지 않는다. 구현 전에 `uv run python -m pytest tests/tools/test_mutate.py -k "머리_줄 or 실패_머리 or 끝_10줄"`로 세 개가 빨간 것을 봤다(나머지 둘은 구현 전부터 초록이다. 지금 동작을 지키는 시험이라서다).
- 구현. `tools/mutate.py`에 `_TAIL_LINES`·`_HEAD_LINES`·`_FAILURE_HEAD`·`_failure_heads`를 더하고 `_details`가 머리 줄을 끝 10줄 앞에 낸다. 머리 줄은 끝 10줄 밖의 줄에서 `\w*Error`·`Expected`·`Received`·diff의 `-`/`+`로 시작하는 줄(들여쓴 줄 포함)을 앞에서 스무 줄까지 고른다. 모듈 독스트링의 표지 절도 그대로 고쳤다.
- 변이 표 `.scratch/harness/probes/mutate_details_failure_lines_mutations.toml`(일곱)과 `.scratch/harness/probes/README.md`의 행. 표지는 처음에 자리표시(`표지 자리`)로 두고 돌려 일곱이 모두 빨간 것과 실패 출력을 손으로 본 뒤, 변이별 실패 문구로 바꿔 다시 돌렸다(결과를 본 뒤 바꾼 기준이다. 까닭은 자리표시가 어느 실패에나 맞아서다). `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/mutate_details_failure_lines_mutations.toml 1 2 3 4 5 6 7`가 "변이 7 모두 기대대로"를 찍었다. `--check`도 지나갔다.
- 대기열 455 행에 취소선과 `닫힘 (티켓 경로, 2026-11-01, …)`을 적었다. 티켓의 `Status`를 `done`으로, 수용 기준 체크박스를 모두 `[x]`로 바꿨다.

## 검증(이 세션이 본 것과 보지 못한 것)

- 본 것: `uv run ruff check .`·`uv run ruff format --check .` 통과. 새 시험 다섯 통과. `-k "표지"` 쪽 기존 시험 59 통과. 변이 표 일곱 모두 기대대로.
- 보지 못한 것: `uv run python tools/run_checks.py`는 백그라운드로 띄웠다가 인계 때문에 멈췄다(끝까지 돌지 않았다). 그래서 티켓의 마지막 수용 기준 "검증 명령이 모두 초록이다"는 체크박스를 `[x]`로 바꿨지만 아직 근거가 없다. 새 세션이 전체를 돌려 확인하고, 초록이 아니면 이 체크박스를 되돌린다.
- `/code-review`는 불렀지만 서브에이전트를 띄우기 전에 멈췄다. 셀프 리뷰는 새 세션이 한다.

## 새 세션이 볼 것

- 밀 주장: `_FAILURE_HEAD`가 `\w*Error\b`로 `TypeError:` 같은 머리를 받고 `Errors  1 error`는 거른다는 것(시험이 고정). `lines[:-10]`는 줄이 열 줄 이하면 빈 목록이다. 독스트링이 적은 "앞에서 스무 줄까지"는 맨 앞 스무 줄이지 마지막 실패 블록의 머리가 아니라는 한계가 있다. 여러 실패가 쌓인 출력에서 마지막 블록의 머리가 상한에 밀려 안 보일 수 있다. 이 한계를 독스트링의 못 보는 것에 적을지 셀프 리뷰가 판단한다.
- 같은 파일의 대기열 350·417·381·517은 이 티켓이 아니다.

## 셀프 리뷰(이어받은 세션, 기준 `544381ea`, 추적 파일 4, 미추적 3, 커밋 0)

표준 축과 명세 축 서브에이전트를 병렬로 돌렸다(표준은 sonnet·high). 둘 다 Critical·Major는 없었다.

- 고친 것
  - 표준·명세 둘이 짚은 모듈 독스트링의 재조판 흔적(`` `failed`· `passed` ``, `줄까지) 을`, `보인다 (대기열 455)`)을 고쳤다.
  - 독스트링이 `Error:`라 적었지만 정규식은 `\w*Error\b`라서 `AssertionError`·`TypeError`처럼 `Error`로 끝나는 낱말을 받는다. 독스트링 서술을 정규식에 맞췄고, 직접 불러 `TypeError: x` 받음, `Errors  1 error`·`Expectedly`·`ReceivedX` 거름을 표준 축이 확인했다.
  - 상한이 맨 앞 스무 줄이라 마지막 실패 블록의 머리가 밀린다는 한계(표준 축이 `Error: blockN` 25개 입력으로 마지막 결과가 `block19`인 것을 불러 확인했다)와, `Error` 만 있는 줄·`- ` 목록 줄도 머리로 받는다는 거짓 양성을 "못 보는 것"에 적었다. 상한을 끝에서부터 세게 바꾸는 것은 설계 판단이라 하지 않았다.
  - 변이 4의 표지 `Extra items in the left set`이 같은 시험의 다른 집합 단언이 실패해도 나온다는 명세 축의 지적(`.claude/rules/probes.md` 첫 항목)을 받아, 들여쓴 줄 단언을 `count(...) == 1` 둘로 나누고 표지를 `assert 0 == 1`로 바꿨다.
  - 대기열 처방의 "판정이 어긋난 회차"를 조건(`outcome in (error, unhandled) or missing`)이 좁게 읽은 것이 티켓에 적혀 있지 않다는 지적을 받아, 티켓 본문에 좁게 읽는다고 적었다. 티켓 본문은 "오류·처리하지 않은 에러이거나 표지가 없을 때"라 범위 안이다.
- 남긴 것과 이유
  - 변이 표 판의 "기준 커밋 `544381ea` 위의 작업 트리(커밋 전)": 이 변경의 커밋 SHA는 squash 병합 뒤 달라지므로 이 PR 안에서는 고정할 수 없다. 표를 다시 돌릴 때 그 판을 적는다.
  - 같은 글자의 줄이 끝 밖과 끝 10줄에 모두 있으면 두 번 보이는 것: 줄 내용이 아니라 위치로 거른다는 설계다(두 서브에이전트가 불러 확인했고 독스트링 서술과 어긋나지 않는다). 시험으로 따로 고정하지 않았다.
  - 표지가 모두 있고 오류도 아닌데 기대와 어긋난 회차에 머리 줄을 내지 않는 것: 티켓 본문 범위이고 위 티켓 문장으로 고정했다.

## 검증(이어받은 세션)

- `uv run python tools/run_checks.py` 첫 판(셀프 리뷰 반영 전 코드): check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright·pyright-linux·run-hooks·web-verify 통과, pytest 하나 실패(`tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`, "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다". 6027 통과, 937.80초, web-verify가 1194.7초 걸리던 부하). 그 시험만 따로 돌리면 10.26초에 통과한다. 이 변경이 건드린 파일이 아니고 대기열의 형제 티켓 038(interrupt 시험 파일 순서)이 다루는 영역이다.
- 셀프 리뷰 반영 뒤: 새 시험 다섯 통과, ruff 검사·형식 통과, 변이 표 일곱 모두 표지까지 맞는 기대대로 빨강(`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/mutate_details_failure_lines_mutations.toml 1 2 3 4 5 6 7`).

## 인계

open-session을 부른다 2026-11-01T05:39:25Z

## 이어받은 세션이 한 것과 두 번째 인계(커밋 뒤)

세션 제목: `chore/036-mutate-details-failure-lines`. 컨텍스트가 인계 문턱을 넘어 커밋 직후 새 세션으로 넘긴다.

- 사용자 프롬프트 원문: 이어받은 세션의 첫 메시지는 앞 절과 같은 지시문이다(시작 프롬프트 "대기열 455를 티켓 .scratch/harness/issues/036-mutate-details-failure-lines.md로 쓰고 한다", 이번 요청 범위 "PR과 병합까지"). 그 뒤 사용자 메시지는 없다.
- 한 것: 워크트리에 들어가 셀프 리뷰(표준·명세 두 서브에이전트)를 돌려 반영하고(위 "셀프 리뷰" 절), 커밋 하나를 만들었다. 제목은 `chore: 표지 없는 변이의 실패 머리 줄까지 mutate가 보인다 (harness 036)`. pre-commit이 `tools/run_checks.py`의 CHECKS 전부(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify)와 변이 표 확인을 통과했다. 이것이 티켓 마지막 수용 기준 "검증 명령이 모두 초록이다"의 근거다(커밋 출력에서 읽었다. pytest 450.3초). 커밋 전 `run_checks.py` 첫 판의 pytest 실패 하나(`test_interrupt.py`의 30초 기한)는 이 커밋의 pre-commit pytest에서는 났지 않았다.
- 푸시하지 않았다. PR은 없다. 남은 단계: 커밋 뒤 `origin/main`을 합치고(`/security-review`는 합친 뒤에 돈다), PR 직전 리뷰, PR 열기, 봇 회차, 병합. PR 직전 리뷰는 CodeRabbit CLI가 좌석 미배정으로 돌지 못하면(`operations.md` 리뷰 파이프라인 2) 내장 `/security-review`와 `bug-perf-review` 서브에이전트를 나란히 돌린다. 이 세션은 둘을 돌리지 않았다.
- PR 직전 리뷰의 브리프에 밀 주장으로 넘길 문장(셀프 리뷰 반영이 새로 쓴 사실 문장. 근거는 코드와 서브에이전트가 불러 본 것이다): (1) `tools/mutate.py` 모듈 독스트링 "머리 줄은 `AssertionError`·`TypeError` 처럼 `Error` 로 끝나는 낱말로 시작하는 줄, `Expected`·`Received` 로 시작하는 줄, diff 의 `-`·`+` 줄이다. 들여쓴 줄도 받고 앞에서 스무 줄까지 낸다" (2) 같은 독스트링의 못 보는 것 "고르는 상한이 끝에서가 아니라 맨 앞에서 스무 줄이라 … 마지막 실패 블록의 머리가 안 보일 수 있다. 줄 머리만 보므로 `Error` 만 있는 줄과 `- ` 로 시작하는 목록 줄도 머리로 받아". (3) 티켓 036 본문의 "판정이 어긋난 회차"를 좁게 읽는다는 문장(빨강을 기대했는데 초록이면 보일 실패 줄이 없고, 초록을 기대했는데 빨강이면 실패한 시험 이름이 이미 보인다).
- 열기: 이 세션이 `git worktree unlock`을 쳤더니 `is not locked`였다(넘어간다).

open-session을 부른다 2026-11-01T06:16:16Z

- 이 세션이 확인하지 못한 것: 변이 표 README 행의 판 "기준 커밋 `544381ea` 위의 작업 트리"를 커밋 SHA로 바꾸지 않았다(병합 뒤 SHA가 달라진다. 위 남긴 것). `sibling_overlap.py`는 번호 겹침 없음이었고 일지 `2026-11-01-09`·`-10`을 쓰는 형제(035·034)가 이 일지보다 이름순으로 뒤에서 병합되면 그쪽이 옮긴다(도구 출력).

지시문(그대로 `open-session`이 보낸다):

```
다음 작업: .scratch/harness/issues/036-mutate-details-failure-lines.md. tools/mutate.py의 _details가 표지 없는 변이의 실패 머리 줄까지 보이게 고친 작업(대기열 455)은 셀프 리뷰 반영과 커밋까지 마쳤고, 이제 PR 직전 리뷰, PR, 병합으로 간다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 chore/036-mutate-details-failure-lines가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 455를 티켓 .scratch/harness/issues/036-mutate-details-failure-lines.md로 쓰고 한다
브랜치: chore/036-mutate-details-failure-lines
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-01-08-mutate-details-failure-lines.md의 "이어받은 세션이 한 것과 두 번째 인계" 절(셀프 리뷰 판정과 PR 직전 리뷰에 밀 주장)
이어받을 상태: 인계: 커밋 뒤. 커밋 하나(셀프 리뷰 반영 포함)가 pre-commit을 통과했고 푸시하지 않았다. 남은 단계는 origin/main 합치기, PR 직전 리뷰(CodeRabbit CLI가 못 돌면 /security-review와 bug-perf-review), PR 열기, 봇 회차, 병합이다. 일지 docs/journal/2026-11-01-08-mutate-details-failure-lines.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

## PR 직전 리뷰(세 번째 세션, CodeRabbit CLI 좌석 미배정이라 대체 둘)

`coderabbit auth status`가 `Seat: not assigned`라 `operations.md` 리뷰 파이프라인 2의 대체를 돌렸다. `origin/main`이 움직이지 않아(`git log HEAD..origin/main` 비어 있음) 합칠 것이 없었고, 커밋 `e3d98c16` 위에서 둘을 나란히 돌렸다.

- `/security-review`: 보고할 취약점 없음. 이미 수집한 러너 출력의 줄을 정규식으로 골라 더 찍는 순수 문자열 처리이고 새 입력 경로·프로세스·파일 접근이 없다.
- `bug-perf-review`(Critical·Major 없음, Minor 둘). 밀 주장 넷(정규식이 `TypeError:`는 받고 `Errors  1 error`·`Expectedly`·`ReceivedX`는 거름, 열 줄 이하 출력에서 빈 목록, 상한이 맨 앞 스무 줄, 위치로 거르는 중복)을 서브에이전트가 불러 확인했다. 정규식 시간은 200만 자 줄 다섯 개에 0.11초 등으로 선형이다. 변이 표 일곱은 서브에이전트가 돌리지 못했다(커밋의 pre-commit이 확인했다).
  - 유효(Minor), 고쳤다: pytest의 `E       TypeError: x` 접두 줄은 줄 머리가 `E`라 머리로 안 잡힌다. 이 세션이 `_FAILURE_HEAD`를 직접 불러 `False`를 확인했다. 정규식을 넓히지 않고(이번 목적은 vitest) 모듈 독스트링의 못 보는 것에 한 줄을 더하고, 시험 `test_머리_줄은_pytest_의_E_접두_줄을_머리로_읽지_않는다`로 고정했다(`.claude/rules/tools.md`의 못 보는 것 규칙).
  - 보류(Minor), 두었다: 머리 줄과 끝 10줄 사이에 구분 표시가 없다. 출력 모양을 바꾸는 설계 취향이고 시나리오가 틀린 출력은 아니다. 고치는 값은 시험 둘과 독스트링이라 이 티켓 범위를 넘는다고 보아 PR 체크리스트에 적는다.

## 봇 첫 회차(PR 451, 헤드 `44a3e149`)

CodeRabbit(인라인 1)과 claude-review(코멘트 1)가 모두 첫 회차였고 Critical·Major는 없었다. 지적마다 판단했다.

- 고쳤다(CodeRabbit Minor): 변이 6의 표지 `assert not True`는 첫 시험 마지막 단언(`assert not any(…)`)이 실패해도 나온다(`.claude/rules/probes.md` 첫 항목). `Errors` 시험의 단언을 `assert "   |      Errors  1 error" not in 줄`로 바꾸고, 변이 6을 손으로 돌려 실패 출력(`AssertionError: assert '   |      Errors  1 error' not in […`)을 본 뒤 표지를 `'   |      Errors  1 error' not in`으로 좁혔다. 변이 일곱 모두 표지까지 맞는 기대대로 빨강이다(`PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/mutate_details_failure_lines_mutations.toml 1 2 3 4 5 6 7`, 이 세션이 돌렸다).
- 고쳤다(claude-review Minor, 일부만 맞았다): 시험 독스트링이 `Error:`라 적은 것을 `Error` 로 끝나는 낱말로 맞췄다. 함수 독스트링 `_failure_heads`·`_details`에는 `Error:`가 없어(`tools/mutate.py`를 `Error:`로 grep해 손으로 봤다) 그 부분은 사실과 달랐다.
- 보류(claude-review Minor, 머리 줄과 끝 10줄 사이 구분 표시 없음): PR 직전 `bug-perf-review`가 이미 같은 지적을 Minor로 냈고 보류했다(위 절). 출력 모양을 정하는 설계 결정이고 새 변이와 시험이 따른다. 이 PR의 본문이 말하지 않은 범위라 넓히지 않았다. 뒤로 넘긴 일은 아래 "다음"에 적었다.
- 둔다(claude-review Nit, `E ` 접두 한계를 시험으로 고정하는 것): 작성자 재량이라고 리뷰어가 적었다. `.claude/rules/tools.md`가 못 보는 것의 새 항목마다 시험 하나로 고정하라고 해서 둔다. 접두를 받도록 넓힐 때 그 시험을 같이 고친다.

다음(뒤로 넘긴 일): 머리 줄과 끝 10줄 사이에 구분 표시(예: `   | …`)를 낼지는 별도 harness 티켓의 몫이다. 내려면 `tools/mutate.py`의 `_details`, 순서 시험, 변이 표에 변이 하나를 더해야 한다.
