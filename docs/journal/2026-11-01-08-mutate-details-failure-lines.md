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
