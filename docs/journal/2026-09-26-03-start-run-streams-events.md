# 2026-09-26 (03) `POST /runs`가 실행을 일으켜 그 이벤트를 흘린다 — http-channel 티켓 03

브랜치 `feature/03-start-run-streams-events`, PR #75(`6cf2595`로 squash 병합). 같은 세션에서 fastapi 하한을
`chore/fastapi-lower-bound`로 갈라 PR #76(`7637fec`)으로 병합했다. 채널 라우터가 `{agent, request}`를 받아 실행
하나를 일으키고 이벤트를 `data:` 한 줄씩 흘린다. 실행은 앱의 수명이 소유한다.

사용자 입력은 인계 지시문 하나, 하한을 어디서 올릴지 하나, PR·병합 지시 하나, 선택 다섯(ADR 승인, PR 순서,
PR 감시 둘, 리뷰 한도)이었다.

## 선행 조건

지시문이 확인하라던 것 — learning 모드 지시("코드 5~10줄을 요청하라")는 들어오지 않았다. Explanatory 스타일만
켜져 있었다. 2026-09-26-02 회고에서 끈 플러그인이 새 세션에 적용된 것이다. 첫 메시지의 훅 계기로 앱이 지은
제목이 브랜치 이름으로 바뀌었다.

## 설계

- **첫 이벤트는 의존성이 기다린다.** FastAPI(0.141.1)는 의존성을 전부 푼 뒤에 SSE 제너레이터를 부르고 응답을
  시작한다. 의존성이 실행을 일으키고 첫 이벤트를 받으면 그 전의 예외가 기존 핸들러를 지나 봉투가 된다. 응답을
  직접 만드는 길은 FastAPI가 제너레이터 라우트에만 붙이는 keepalive를 잃는다.
- **라우터 모듈에는 `from __future__ import annotations`가 없다.** 클로저 의존성을 `Depends(...)` 주해로
  가리키는데, 첫 프로브에서 FastAPI가 문자열 주해를 모듈 전역에서만 풀어 스키마 생성이 터졌다.
- **실행의 소유자 `Runs`.** 채널 라우터가 `APIRouter(lifespan=...)`로 수명을 들고 오고, `include_router`가 그것을
  앱의 수명에 합친다. 수명이 anyio 태스크 그룹을 열고 실행 하나가 태스크 하나다. 둘 사이는 `math.inf` 메모리
  흐름이고 `send_nowait`로 넣는다.
- **`Event` 별칭.** 채널 쪽 `type Event = sdk.Event`로 `#/components/schemas/Event`가 생기고 `TraceEvent`와 같은
  멤버를 가리킨다. 프로브로 먼저 봤다.
- **실행 전 실패의 통로.** 두 태스크 사이라 반환값으로 못 건네 칸(`_PreRunFailure`) 하나를 뒀다. anyio
  `TaskGroup.start`가 같은 일을 하지만 `-> Any`라 첫 이벤트가 타입 없이 흐른다(원칙 III).
- **유예 5초.** 결말 직전의 실행이 마지막 이벤트를 흘릴 여유이고 모델 호출 하나를 기다려 주는 길이가 아니다.

## 밟은 것

- **가짜 도구가 서버 없이도 도구를 줬다.** core가 `bind_tools`를 불러 가짜 모델이 `NotImplementedError`를 냈고,
  "모델 실패" 테스트가 그 `run_failed`로 **엉뚱한 이유로 초록**이었다. 가짜를 실제 어댑터처럼 고치고 실패 원인
  문구까지 단언하게 했다.
- **FastAPI가 SSE 라우트의 에러 문서를 `text/event-stream` 아래에 싣는다**(`openapi/utils.py` 499행). 공용 층에
  `documented_stream_errors`를 두어 JSON 봉투로 적는다. `_ENVELOPE_REF`는 관리 라우트의 등록에 기댄다.
- **core 결함.** 트레이스 쓰기가 실패하면 `_drive`가 도구 연결 안에 멈춘 `execute()`를 버리고, 가비지 수집이
  다른 태스크에서 닫아 anyio 취소 범위가 깨졌다. 앱의 수명 태스크 그룹이 통째로 무너지는 모양이다. 실패하는
  core 테스트를 먼저 쓰고 `aclosing`으로 고쳤다. 명세의 "`_drive`가 `async with`로 연 채 도는 구조 그대로"라는
  전제가 이 경로에서 거짓이었다. 소비자가 도중에 닫는 경우의 테스트도 썼다가 걷어냈다 — `run()`이
  `AsyncIterator`라 `aclose()`를 부르려면 core 시그니처를 바꿔야 했다.
- **이벤트 사이에 await 하지 않는다.** 크기 제한 큐 변이가 끊김 테스트에서도 빨갰던 이유를 캤다. core가 도구
  연결의 취소 범위 안에서 yield하므로, 소비자가 그 사이의 await에서 취소를 받으면 제너레이터가 범위 안에 남아
  다른 태스크에서 닫힌다. 프로브 둘로 재현했다(스크래치). `runs.py` 독스트링과 `.claude/rules/channel.md`에 적었다.
- 큰 heredoc을 훅이 막았다(설계대로). Edit로 나눴다.

## 테스트와 변이

`tests/channel/http/test_router.py` 34개. 주 이음매는 `ASGITransport`에 앱의 수명을 테스트 본문의 `async with`로
연 것이고, 둘째 구동자는 `app(scope, receive, send)`로 수명 넷만 잰다. 가짜 모델은 `_agenerate`에서 문을 기다린다.
채널 파일을 열 번과 다섯 번 반복해 흔들림이 없었다.

변이는 서로 다른 것 16가지, 반영 뒤 다시 돈 것까지 19번이고 전부 빨강이었다. 크기 제한 큐는 떠난 수신자를
버리는 "자연스러운" 모양까지 넣었다. 느린 수신자 테스트와 끊김 테스트가 함께 잡는다(위 await 항목).

## 하한 측정

티켓대로 lowest-direct로 런타임 의존성만 하한으로 풀어 스크래치 가상환경에서 돌렸다.

- fastapi 0.135.0: 프레임이 공백 있는 `json.dumps`라 트레이스 줄과 문자열로 다르고, 계약의 항목 스키마에
  `contentSchema`(`Event`)가 없다. 잠긴 의존성 위에서 fastapi만 바꿔 이분 탐색하니 0.140.8부터 섰다.
- langchain-core 0.3.36: core 테스트 36개와 모델 테스트 4개가 깬다.
- langchain-mcp-adapters 0.1.0: mcp 상한이 없어 mcp 2.2.0이 따라오고 import에서 깬다.

"프레임이 트레이스 줄과 **문자열로** 같다"는 티켓의 요구가 그대로 판정자가 됐다. 파싱해 비교했다면 fastapi의
차이를 못 봤다. 하한을 올리는 것은 `tech.md`와 ADR 0014가 함께 움직여 티켓("기록만") 밖이라 사용자에게 올렸다.

> 사용자: 별도 브랜치에서 올려
> 사용자: (ADR 승인) "승인하고 커밋 (Recommended)"

`chore/fastapi-lower-bound`가 `>=0.140.8`과 ADR 0014의 2026-09-26 이력을 담았다. 두 langchain 하한은 기록만 했다.

## 셀프 리뷰

- 표준 축: Minor 넷(출력 인자와 try 구조, 용어 "프롬프트"→"요청", `tech.md`와 rules의 중복)과 냄새 몇. 출력
  인자는 셀 이름과 근거를 다듬고 구조를 바꿔 부분 반영했다. 나머지는 고쳤다.
- 명세 축: Critical·Major 0. 실행 중단 기록에 요청 식별자, 04 범위를 선점한 문장("재개 라우트도 같다"), 가르지
  못하던 도구 연결 테스트의 이름을 고쳤다. 의존성이 돌아온 직후의 취소에서 수신 흐름이 안 닫히는 경우는
  추론이라 보류했다.

## PR 리뷰

- **CodeRabbit CLI**는 돌리지 않았다. `Plan: Free`, `Seat: not assigned` 그대로였다.
- **#75.** claude-review 지적 없음(출력 인자를 근거 있는 예외로 봄). CodeRabbit이 Major 둘을 냈다.
  - fastapi 하한 — #76이 잇는다고 답하고 스레드를 닫았다.
  - 무제한 버퍼 — 명세 Further Notes가 보류한 결정이라 답만 하고 스레드를 열어 두었다. 떠난 수신자는 흐름이
    닫혀 버려지고, 상한과 초과 정책(종료냐 트레이스 재생이냐)은 동시 실행 상한·재접속과 함께 web-widget의 몫이다.
- **#76.** CodeRabbit이 한도에 걸렸다(23:24 UTC 기준 43분, 09:07 KST 해제). 절대 시각을 먼저 드렸다.
  claude-review 지적 없음. CodeRabbit 축이 비었다고 PR에 적고 병합했다.
- 병합 전 두 PR 모두 `headSha`가 PR 헤드·로컬 HEAD와 같은지, 봇 코멘트가 실제로 있는지 봤다.

> 사용자: pr 병합
> 사용자: (PR 범위) "둘 다, 03 먼저 (Recommended)"
> 사용자: (PR #75 감시) "켜다 (Recommended)"
> 사용자: (PR #76 감시) "켜다 (Recommended)"
> 사용자: (리뷰 한도) "CI·claude-review 만으로 병합 (Recommended)"

## 갈린 곳

- 첫 이벤트를 의존성에서 기다렸다(제너레이터 안·응답 직접 생성을 거부).
- 실행 전 실패를 칸으로 건넸다(`TaskGroup.start` 거부, `Any`).
- 소비자 조기 종료 테스트를 걷어냈다(core 시그니처 보존).
- fastapi 하한을 이 티켓에서 올리지 않고 사용자에게 올렸고, 사용자가 별도 브랜치를 골랐다.
- CodeRabbit의 버퍼 상한 Major를 명세의 보류대로 두었다.
- 채널 전용 규칙을 `http.md`가 아니라 새 `channel.md`에 두었다(관리 파일을 만질 때 실리지 않게). HTTP 층
  공통인 둘(프레임과 광고의 불일치, 스트림 에러 문서)만 `http.md`에.

## 번복하거나 고친 것

- 가짜 도구가 서버 없이 도구를 줌 → 실제 어댑터처럼. "모델 실패" 테스트에 원인 단언.
- 스트림 라우트 에러 문서를 모델로 → `documented_stream_errors`.
- `_Outcome`·`started` → `_PreRunFailure`·`run_stream`, `_drive`의 try 안 로직 정리(리뷰).
- 보고에서 변이를 "18개"로 잘못 셌다 → PR 본문에서 16가지·19번으로 바로잡았다.
- ADR 0014 이력의 "티켓 03이 더하는 테스트" → #75 병합 뒤 "더한"으로(#76 안의 둘째 커밋).

## 회고

후보 넷. 둘은 대기열에 올렸고(34, 35), 하나는 29에 근거로 더했고, 하나는 기록만 했다.

> 사용자: (회고 판정) "대기열에 올린다 (Recommended)", "대기열에 올린다 (Recommended)", "기록만 (Recommended)", "29에 더한다 (Recommended)"

1. **선언된 하한을 재는 게이트가 없다(대기열 34).** CI는 잠긴 버전만 돌아 `pyproject.toml`의 하한이 거짓이어도
   초록이다. fastapi 하한 거짓은 티켓이 요구한 측정으로만 드러났고 langchain 둘은 지금도 거짓이다. 기계가
   판정할 수 있어 지침이 아니라 CI 잡이다.
2. **형제 티켓의 몫을 먼저 썼다(3회차, 대기열 35).** 1회차 01, 2회차 02의 `ServeArgs`, 3회차 이번 `channel.md`의
   "재개 라우트도 같다". 셋 다 명세 축이 잡았다. 규약대로 3회차에 규칙 후보가 됐고 자리는 `implement` 스킬이다.
3. **실패를 기대하는 테스트가 엉뚱한 원인으로 초록이었다(2회차).** 1회차는 명세 검토의 500 문구 프로브, 2회차는
   이번 "모델 실패" 파라미터(위 밟은 것). 기록만. 다음이 3회차다.
4. **문서가 스크래치 프로브를 근거로 든다(대기열 29, 3회차).** ADR 0014의 2026-09-26 이력과 `runs.py`
   독스트링. 29에 이번 스크래치 경로와 스크립트 이름을 더했다.

## 검사

PR #75 병합 전: pytest 513 passed·3 deselected, pyright 0 errors(71 files), lint-imports 4 kept, ruff, 지침 검사,
타입 우회 0. PR #76 rebase 뒤 같은 여섯이 초록, fastapi 0.140.8 스크래치 환경에서 513 passed.

## 다음

- **http-channel 티켓 04(`POST /runs/{run_id}/approval`)가 풀렸다.** 05는 04에 막힌다. 시작 프롬프트는
  `/implement .scratch/http-channel/issues/04-approval-resumes-over-http.md`.
- 04가 이 티켓에서 물려받는 것:
  - 재개도 `Runs.start`로 연다. 첫 이벤트는 결정 이벤트이고 그 전의 `Absent`·`NotResumable`·`PluginError`가
    404·409·500으로 갈린다. 라우트는 `documented_stream_errors`로 에러를 적는다.
  - 계약 테스트 `EXISTING_COMPONENTS`와 "새 이름은 `Event`, `StartRun`뿐" 단언을 04가 결정 유니온의 이름으로
    넓힌다(티켓 03의 계약 항목).
  - `CHANNEL_GUARDED = "/runs/unrouted"`는 `/runs/{run_id:verbatim}/approval`에 닿지 않는다. `verbatim`이
    슬래시까지 잡으므로 04가 라우트를 붙인 뒤 한 번 본다.
  - `.claude/rules/channel.md`의 "응답은 첫 이벤트 뒤" 규칙은 재개 라우트에도 걸린다. 03에서는 04 범위라 적지 않았다.
- CodeRabbit PR 리뷰는 시간당 1회다. #76이 09:07 KST 전에 한도에 걸렸다.
