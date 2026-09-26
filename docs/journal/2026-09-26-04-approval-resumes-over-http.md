# 2026-09-26 (04) `POST /runs/{run_id}/approval`로 멈춘 실행을 재개한다 — http-channel 티켓 04

브랜치 `feature/04-approval-resumes-over-http`, PR #78(`3aad492`로 squash 병합). 채널의 둘째 경로가 결정 하나를
받아 core `resume()`을 앱이 소유한 실행으로 넘기고, 첫 이벤트(그 결정)를 받은 뒤 재개된 실행을 흘린다. 동시
재개의 불변식을 처음 테스트로 고정했다. CI가 드러낸 잠복 충돌(종료 중 GC의 세그폴트)을 같은 PR에서 고쳤다.

사용자 입력은 인계 지시문 하나, PR·병합 지시 하나, 진행 확인 하나, 선택 둘(PR 감시, 회고 판정 넷)이었다.

## 설계

- **실행 상태를 채널이 먼저 확인하지 않는다.** 부재·재개 불가·기록 손상은 core가 던진 타입을 공용 표가
  404·409·500으로 옮긴다(ADR 0014). 상태 코드 테스트는 먼저 확인하는 구현으로도 초록이라 명세 축 리뷰가 봤다.
- **본문은 `Decision = Approve | Deny`이고 `Body()`로 받는다.** 첫 프로브에서 PEP 695 별칭을 그대로 받으면
  FastAPI가 본문을 `Body`라는 제목의 익명 `oneOf`로 인라인했다. 이름은 용어집의 "결정"과 core의 것과 같고
  관리의 `Trace`·`RunSummary` 선례를 따랐다. core 쪽은 `CoreApprove`·`CoreDeny` 별칭이다.
- **422의 `violations` 경로에 판별자 값이 든다**(`body.deny.reason`). pydantic이 판별 유니온의 오류 위치에
  태그를 넣는다. `http.md`에 적었다.
- **`operation_id`는 `decide_approval`.**

## 밟은 것

- **동시 재개 테스트가 막아야 할 변이를 다 막지 못했다.** 처음엔 anyio 스레드 쓰기만 쟀고(10/10), 스레드
  읽기는 5/10이었다. 가짜 트레이스의 읽기를 "시작 순간의 스냅숏 + 지연"으로 바꿔 10/10을 만들었는데, 명세 축
  리뷰가 `asyncio.to_thread` 쓰기가 0/10으로 지나간다는 것을 잡았다. 쓰기에도 지연을 두었다(`disk_seconds`).
- **사유 다듬기가 CLI와 달랐다.** pydantic의 `strip_whitespace`(rust)는 U+001C~U+001F를 공백으로 보지 않아
  `"\x1c"` 사유가 core `Deny`까지 가 고정 문구의 500이 됐다(명세 축 리뷰의 프로브). `str.strip`의
  `AfterValidator`로 바꿨다.
- **변이 스크립트가 되돌린 파일의 줄 끝을 바꿨다.** `Path.write_text`가 Windows에서 CRLF로 써 손대지 않은
  `core/run.py`가 수정된 것으로 보였다. 바이트 단위로 고쳤다(대기열 29의 4회차).
- 판별 유니온의 기본값 없는 판별자, `-Input`·`-Output` 갈라짐 없음, 기존 컴포넌트 불변은 계약 테스트가 잰다.

## 테스트와 변이

채널 테스트 66개(03에서 +32). 변이 14가지가 전부 빨강이었다. 동시성 다섯(`sleep(0)` 삽입, anyio·asyncio의 스레드
읽기·쓰기)은 각 10회, 나머지는 사유 다듬기 셋, 승인의 추가 필드 무시, 판별자 기본값, `verbatim` 빠짐, 409 문서
빠짐, `Body()` 빠짐, 거부가 허가로. 초록 쪽은 동시성 테스트 30회 반복에서 흔들림 0이었다.

## CI 종료 코드 139

첫 CI가 pytest 545 passed **뒤에** SIGSEGV로 끝났다. 로컬 Windows, WSL Ubuntu 22.04, CPU 4개·CI 환경변수의 Docker
`ubuntu:24.04`에서 19/19 초록이라, 같은 검사가 두 번 연속 실패한 시점에 diagnosing-bugs 스킬로 가서 CI를 루프로
삼았다. PR을 초안으로 돌려 Claude Code Review가 디버그 푸시마다 돌지 않게 했다.

- 탐침 1·2(파이프, faulthandler, 대조군 포함): 앞 단계 없이 돌린 잡에서는 전부 0 — 재현 조건이 원래 잡에 있었다
- 탐침 3(원래 순서): 앞 단계 뒤의 **첫** pytest만 139
- 탐침 4(매트릭스): 방아쇠는 **lint-imports**. faulthandler의 스택은 "Garbage-collecting, no Python frame"
- 탐침 5·6: 새 `test_router.py`가 있어야 죽는데, 서로 다른 두 테스트 묶음이 각각 없애고 `AfterValidator`를
  되돌려도 139 — 특정 객체가 아니라 양과 모양에 민감한 종료 중 충돌
- 탐침 7: `python -m pytest`와 gdb 아래에서는 사라진다. 관찰이 증상을 지운다
- 탐침 8: 같은 명령에 `ulimit -c`만 더한 **코어 덤프**의 C 스택 — `finalize_modules` → `lru_cache_dealloc` →
  캐시 키 → 라우트 함수 → 클로저 → 가짜 트레이스 → `calls` → `Cursor` → `datetime_dealloc` → pydantic-core 안
- 탐침 9: 해독한 시각을 표준 라이브러리 시각대로 바꾸면 충돌 없음, 세션 끝에 FastAPI 캐시를 비우면 0

원인은 FastAPI 0.141의 모듈 전역 `lru_cache(maxsize=4096)`(`fastapi/dependencies/models.py`)가 라우트 함수를 키로
붙잡아 테스트가 만든 포트가 프로세스 끝까지 사는 것과, 관리 API가 pydantic으로 해독한 커서가 pydantic-core의
`TzInfo`를 든 채 core의 `Cursor`로 넘어간 것이다. 종료 중 GC가 그 `TzInfo` 해제에서 죽는다. **사슬은 main에도
있고** 이 PR은 종료 순서를 흔들었을 뿐이다. `decode_cursor`가 같은 순간·같은 오프셋을 `datetime.timezone`으로
든 시각을 넘기게 경계에서 고쳤다(서드파티는 경계에서 감싼다). UTC로 바꾸는 안은 오프셋을 지키는 기존 테스트가
막았다. 회귀 테스트는 포트가 받는 시각대의 타입을 잰다. 고친 뒤 원래 워크플로에서 HEAD 2/2 초록이다.

> 사용자: 끝이야?

CodeRabbit이 수정 커밋의 리뷰를 04:55 UTC에 지적 없이 끝냈는데 PR 감시가 그것을 알리지 않아, 06:48의 이
물음까지 기다리고 있었다(대기열 37).

## 셀프 리뷰

- 표준 축: 불리언 플래그 인자(테스트 헬퍼), 이름 둘(`decided`→`to_core`, `_deciding_model`→`_tool_calling_model`),
  계약 설명의 "승인."→"허가."(용어집), 다섯 곳에 되풀이된 불변식 서술을 가리키는 문장으로. 사유 다듬기의
  CLI·HTTP 중복은 `channel.md`가 적은 설계라 보류했다.
- 명세 축: Major 하나(`asyncio.to_thread` 쓰기 변이 놓침), Minor 하나(`\x1c` 사유 500). 둘 다 고쳤다.

## PR 리뷰

- **CodeRabbit CLI**는 돌리지 않았다. `Plan: Free`, `Seat: not assigned` 그대로다.
- **CodeRabbit PR**: `fbbf7aa`까지(03:36)와 `fbbf7aa..d3849a4`(04:55) 두 번, 둘 다 지적 없음.
- **Claude Code Review**: 첫 번째 지적 없음. 두 번째 Nit 하나 — `_standard_offset` 독스트링이 "PR #78 의 CI"를
  가리킨다. `adapters/jsonl.py`의 `PR #56`처럼 코드 주석이 PR 번호를 근거로 드는 관례가 있고 원인도 이미 적혀
  있어 반영하지 않았다.
- 병합 전 `headRefOid`·로컬 HEAD가 `d3849a4`로 같고, CI 실행 둘이 그 커밋을 검사한 것을 봤다.

> 사용자: pr열고 병합
> 사용자: (PR #78 감시) "켜다 (Recommended)"

## 갈린 곳

- 재개도 `Runs.start`로 열고 첫 이벤트를 의존성에서 기다렸다(03 그대로).
- 결정의 이름을 core와 겹치게 두었다(가르는 안 거부).
- 139를 테스트 쪽(세션 끝에 FastAPI 캐시 비우기)이 아니라 경계(커서 해독)에서 고쳤다. 테스트 쪽은 사적 API이고
  pyright strict가 막는다. 경계 쪽은 `CODING_STANDARDS.md`의 기준이 따로 선다.
- 수정을 별도 `fix/` PR이 아니라 이 PR에 담았다(티켓 03의 `aclosing` 선례).
- Claude Code Review의 Nit(독스트링의 PR 번호)을 저장소 관례로 보류했다.

## 번복하거나 고친 것

- 사유 다듬기 `StringConstraints(strip_whitespace=True)` → `str.strip`의 `AfterValidator`(명세 축).
- 동시 재개 가짜의 `read_seconds` → `disk_seconds`(명세 축의 Major).
- 커서 수정 첫 안 "UTC로" → "같은 오프셋의 표준 시각대로"(기존 테스트가 막음).
- 탐침 1이 변수 셋을 한꺼번에 바꿔 해석할 수 없었다 → 탐침 2부터 대조군을 먼저 두고 하나씩.
- 변이 스크립트의 CRLF 되돌림 → 바이트 단위.

## 회고

후보 넷. 둘은 대기열에 올렸고(36, 37), 하나는 기록만 했고, 하나는 29에 근거로 더했다.

> 사용자: (회고 판정) "대기열에 올린다 (Recommended)", "대기열에 올린다 (Recommended)", "기록만 (Recommended)", "29에 근거를 더한다 (Recommended)"

1. **CI가 인터프리터 충돌에서 단서를 남기지 않는다(대기열 36).** 첫 로그가 종료 코드 하나뿐이라 탐침 아홉 번이
   들었다. `PYTHONFAULTHANDLER`와 실패 시 코어 덤프 백트레이스 스텝. 정보 접근이라 검사다.
2. **PR 감시가 CodeRabbit의 "지적 없음" 완료를 알리지 않는다(대기열 37).** 약 두 시간 멈췄다. 행동이
   일어나는 자리(`next-session` 1단계)에 한 줄.
3. **FastAPI 캐시가 테스트 가짜를 프로세스 끝까지 붙잡는다(기록만, 1회차).** 가짜가 pydantic이 JSON에서 만든
   시각을 쌓으면 같은 충돌이 다시 날 수 있다. JSONL 어댑터가 읽은 이벤트의 시각도 `TzInfo`를 든다(PR #78의
   "남긴 위험"). 다음이 2회차다.
4. **탐침·변이 스크립트를 또 스크래치에서 지었다(대기열 29의 4회차).** 바이트 그대로 되돌리는 변이 도구를
   `tools/`에 두는 안을 함께 적었다.

## 검사

PR #78 병합 전(HEAD `d3849a4`): pytest 546 passed·3 deselected, pyright 0 errors(71 files), lint-imports 4 kept,
ruff, 지침 검사, 타입 우회 0. CI는 원래 워크플로로 2/2 초록.

## 다음

- **http-channel 티켓 05(`05-real-serve-pauses-and-approves.md`)가 풀렸다.** 이 기능의 마지막 티켓이다. 시작
  프롬프트는 `/implement .scratch/http-channel/issues/05-real-serve-pauses-and-approves.md`.
- 05가 이 티켓에서 물려받는 것:
  - 승인 본문은 `{"decision": "approve"}`이고 경로는 `/runs/{run_id}/approval`, 응답은 `/runs`와 같은 SSE다.
    첫 이벤트가 결정이고 재생된 사실은 나오지 않는다.
  - 테스트 프로세스에서는 FastAPI 캐시가 만든 앱의 포트를 끝까지 붙잡는다. 05는 서브프로세스 `serve`라 이
    사슬 밖이지만, 같은 pytest 세션에서 가짜를 쓰는 앱이 늘면 종료 중 충돌이 다시 드러날 수 있다(회고 3).
    CI에서 139가 보이면 이 일지의 "CI 종료 코드 139" 절부터 본다.
