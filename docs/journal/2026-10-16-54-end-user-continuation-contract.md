# 2026-10-16 (54) end-user-continuation 티켓 01: 계약

일지 2026-10-16-35의 "다음"이 가리킨 새 세션이다. 제목을 브랜치 이름으로 바꾸고, 주 체크아웃이 미갱신이라
`tidy-checkouts`를 먼저 돌았다(루트를 `dbcdc6d6`에서 `79a23fc7`로 당겼다). 주 체크아웃에서 브랜치를 따지 않고 워크트리
`.claude/worktrees/01-contract-end-user-continuation-and-cause-slots`에 들어가 브랜치를
`feature/01-contract-end-user-continuation-and-cause-slots`로 바꿨다. `implement` 스킬을 Read로 열어 따랐다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자:
> .scratch/end-user-continuation/issues/01-contract-end-user-continuation-and-cause-slots.md
> 다음 작업: … 위젯의 이어 가기 경로와 실패 원인·바로가기 필드의 계약 … 이번 요청 범위: PR과 병합까지"

## 이어받은 것

`tidy-checkouts`가 지운 것은 체크아웃되지 않은 로컬 브랜치 `worktree-code-review-precedent-call` 하나다(끝이
`origin/main`에 있었다). 워크트리 서른둘은 병합된 PR이 없거나, 그 브랜치의 세션이 돌거나, 잠금 pid가 살아 있거나,
`claude.exe`가 작업 디렉터리로 쥐었거나, 다시 만들 수 없는 `.claude/plans/`가 있어 남겼다. 사람에게 넘긴 하나(병합된 PR의
머리와 브랜치 끝이 다른 `skill-check-and-retro-section`)는 지시문대로 보고만 하고 답을 기다리지 않았다. 세 세션 잇달아
넘긴 것이다(일지 2026-10-16-35의 회고 3).

## 지은 이름

티켓이 이 티켓에 넘긴 이름이다. 계약이 바뀌므로 PR에서 사용자가 본다.

- 실패 이벤트의 원인 필드는 `RunFailed.cause`, 시작 이벤트의 바로가기 필드는 `RunStarted.shortcuts`(값은
  `Mapping[AgentName, RunId] | None`)다. 다른 이벤트의 필드 이름과 겹치지 않는다. `reason`은 거부 사유와, `error`는 실패의
  내용과 겹쳐 관리 화면의 필드 이름 표에 용어집의 말을 붙일 칸이 없다(명세 검토).
- 값 집합은 sdk의 `FailureCause`(`type` 별칭의 `Literal`. 계약의 컴포넌트 이름이 된다. `RunStatus`·`TraceSchemaVersion`과
  같은 모양이다)이고 값 아홉은 `conversation_summary`, `timeout`, `tool_connection`, `model_call`, `tool_failure`,
  `loop_limit`, `resume_mismatch`, `agent_code`, `other`다. 순서는 명세 표의 순서다.
- 경로의 `operation_id`는 `continue_end_user_run`이다(운영자 채널의 `continue_run`, 최종 사용자 면의
  `start_end_user_run`의 모양).

## 한 것

- **sdk.** 위 필드 둘과 값 집합. 둘 다 기본값이 없음이라 형식 1·2·3의 옛 줄이 그대로 읽히고 형식은 3 그대로다.
- **core.** 에이전트가 낸 `run_failed`를 원인과 무관하게 막는다(`_reject_runtime_only`, `conversation_summarized`와 한
  자리). 에이전트의 제너레이터를 `_closing`으로 열어 그 자리에서 닫는다. sdk의 `BaseAgent.run`은 `AsyncIterator`를
  돌려준다고만 약속해 `aclose`가 타입에 없으므로, 프로토콜을 바꾸지 않고 `AsyncGenerator`일 때만 닫는다.
- **채널.** `POST /end-user/runs/{run_id}/continuation`. 시작과 앞 실행 하나만 다르게 주는 공통 의존성(`started`)을
  두고 경로마다 감쌌다(운영자 채널의 `started`와 같은 모양). 라우터에 넷째로 등록했다. 실패 항목에 `cause`(required,
  null 허락)를 더하고 투영이 이벤트의 원인을 옮긴다.
- **계약.** `openapi.json`과 생성 클라이언트를 다시 뽑았다. 생성기는 바로가기 지도를 `{ [key: string]: string } | null`로
  냈다. api-client의 `EndUserPath`에 이어 가기가 넷째로 들고, 관리 클라이언트가 그 경로를 모른다는 것을 타입 테스트가
  고정한다.
- **관리 화면.** 필드 이름 표에 "바로가기"와 "실패 원인". 실행 상세 페이지 테스트 둘의 시작 이벤트 픽스처와 필드 이름
  목록.
- **바깥 이음매.** 기존 최종 사용자 `-m llm` 테스트에 이어 가기 요청을 붙이고 asker가 대화 멤버를 데이터로 엮게 했다.
- **지침.** rules 다섯(`sdk.md`, `core.md`, `channel.md`, `http.md`, `adapters.md`), 독스트링과 주석, README 트리,
  ADR 0031의 이력(원인 아홉의 이름과 뜻), `plan.md` 행을 `in-progress`로.

## 셀프 리뷰

`/code-review`를 기점 `79a23fc7`(커밋 없음, 바뀐 파일 30, 미추적 1)로 돌렸다. 두 축을 서브에이전트로 나란히 띄웠다.

**표준 축: Major 1, Minor 6, Nit 4.** 판정과 반영은 아래다.

1. Major, 맞다. 변이 표 `contract_mutations.toml`의 pytest 변이 다섯이 모두 표지 `["failed"]`였다. 그 글은 pytest의 요약
   줄과 단언의 dict(`"type": "failed"`)에 늘 실려, 고른 단언이 아닌 것이 빨개져도 맞는다(`.claude/rules/probes.md`의 표지
   항목). 변이를 손으로 넣어 실패 출력을 본 뒤 그 실패에만 나오는 문구로 고친다.
2. Minor, 맞다. `_closing`을 겨누는 변이가 없어 테스트 독스트링의 "닫지 않는 구현에서는 … 아직 돌지 않았다"를 다시 잴
   근거가 없고, `core.md`의 "같은 태스크에서 돈다"는 테스트가 재지 않았다(`closed`만 봤다). 변이 행을 더하고 테스트가
   `finally`를 돈 태스크까지 본다.
3. Minor, 맞다. 프로브 README에 변이 표의 줄이 없다(`docs/agents/issue-tracker.md`의 프로브와 근거 절). 더한다.
4. Minor, 맞다. `sdk.md`가 "바로가기"를 용어집의 말이라 적었는데 용어집에 없다(명세 서두가 넣지 않기로 했다). 고친다.
5. Minor, 맞다. 최종 사용자 면 모듈 독스트링이 이어 가기에서도 "실행의 에이전트와 주체는 트레이스 안에" 있다고 적었다.
   이어 가기의 에이전트는 본문에서 온다. 앞 실행의 주체와 상태로 고친다.
6. Minor, 맞다. CORS 테스트 독스트링이 위젯의 동작(404에 대화를 지운다)을 지금 난다고 적었다. 위젯은 아직 없고 그 동작은
   web-widget이 정한다(`plan.md`의 그 행). `items.py`의 "위젯은 … 내려간다"도 web-widget의 몫이라고 고친다.
7. Minor, 맞다. "재생 구간에서도 같다"를 실패 이벤트에서 재는 사례가 없다. 옛 코드가 쓴 트레이스(지어낸 실패 뒤
   일시정지)를 재개하면 이제 실패한다는 동작의 변화도 고정되지 않았다. 사례를 더한다.
8. Nit, 맞다. 변이 4의 `None if previous_run is None else None`은 시작의 타임아웃까지 뺀다. 이어 가기만 빼게 고친다.
9. Nit(Shotgun Surgery), 남긴다. "시작·결정·이어 가기"를 열 곳 가까이에 적었다. 묶음 말로 바꾸는 것은 이 티켓의 문장
   밖까지 고치는 일이라 다음에 같은 열거가 늘 때 본다.
10. Nit(Duplicated Code), 일부 반영. 원인 없는 실패를 막는 논증이 다섯 곳에 있었다. `core.md`는 독스트링을 가리키게
    줄이고 테스트 독스트링도 줄인다. `events.py`의 한 줄은 계약 모델 곁의 요지라 둔다.
11. Nit, 맞다. 테스트 이름에 구현 이름(`finally`, `run`)이 들었다(`CODING_STANDARDS.md`의 테스트 이름). 바꾼다.

**명세 축: Minor 3, Nit 4.** 범위 넘침은 없고, 티켓의 HTTP 사례(404 다섯, 409 넷, 422 셋, 429 둘, 봉투와 CORS)와 계약
테스트, 오퍼레이션 목록 둘, JSONL, 픽스처, 바깥 이음매가 하나씩 있다고 봤다.

1. Minor, 맞다. 잔존 하나가 grep을 빠져나갔다. `limits.py`의 "시작과\n결정 모두 센다"는 줄이 바뀌는 자리라
   `시작과 결정`으로 걸리지 않았다(티켓의 "걸린 것 둘레도 읽는다"). 같은 모듈의 "남의 실행에 낸 결정이나 목록 밖 에이전트로
   보낸 시작도 404 보다 429 가 먼저다"에도 이어 가기를 더한다(Nit). 줄바꿈을 건너는 잔존은 글자 grep이 못 보므로, 걸린
   파일만이 아니라 열거가 사는 모듈(상한·등록부·면)을 통째로 다시 읽는다.
2. Minor, 맞다. `items.py`의 `FAILED_MESSAGE` 주석 "실패가 왜 났는지는 항목의 원인이 종류로 들고"는 틈 동안 거짓이다.
   런타임이 쓰는 실패는 지금 원인이 늘 `null`이다(티켓의 "02~05가 들일 동작을 지금 난다고 적지 않는다"). 원인이 기록된
   실패면 그 종류를 든다고 조건을 단다.
3. Minor, 맞다. 새 테스트의 "스토리 N"이 번호만 써서, 같은 파일이 지금까지 가리키던 end-user-channel 명세(그 13은 너무
   긴 요청이다)와 섞인다. `test_run.py`의 "스토리 35"도 그 파일이 쓰는 conversation 번호와 섞인다. CORS 테스트의 "409 …
   (스토리 21)"은 번호도 틀렸다(409는 11). 모두 "end-user-continuation 스토리 N"으로 적는다.
4. Nit, 맞다. 최종 사용자 면 모듈 독스트링(표준 축 5와 같다).
5. Nit, 맞다. `RunStarted`의 계약 설명에서 "런타임이 낸다"가 빠졌다. 줄 폭 때문에 줄이다 뺐다. 되살린다.
6. Nit, 맞다. `test_end_user.py`의 모듈 독스트링 첫 줄이 아직 "시작하고 결정하고 구독한다"다.
7. Nit. 재생 구간의 실패 이벤트 사례가 없다(표준 축 7과 같다). 티켓의 테스트 목록에는 없지만 더한다.

**반영하며 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다).** 셀프 리뷰를 반영하는 동안 main에 든
code-review 스킬의 새 규약(대기열 260)이다. 원문이다.

- `limits.py`: "그래서 남의 실행에 낸 결정, 남의 앞 실행에 보낸 이어 가기, 목록 밖 에이전트로 보낸 시작도 404 보다 429 가
  먼저다", "최종 사용자 경로가 일으켜(결정과 이어 가기도 든다) 지금 도는 실행 하나가 칸 하나다", "시작·결정·이어 가기 모두
  센다 — 셋 다 모델을 돌리는 요청이다"
- `end_user.py` 모듈 독스트링: "결정과 구독에서 실행의 에이전트와 주체는, 이어 가기에서 앞 실행의 주체와 상태는 트레이스
  안에 있어, 채널이 먼저 보면 트레이스를 먼저 읽어 판정 순서가 core 밖으로 샌다. 이어 가기가 열 에이전트 목록으로 보는
  것은 본문이 요청한 에이전트다."
- `items.py`: "원인이 기록된 실패면 항목의 원인(`FailedItem.cause`)이 그 종류를 들고, 원인마다 보일 말을 정하는 것은
  web-widget 의 몫이다(ADR 0031)", "null 이나 모르는 값에 고정 문구로 내려가는 것은 web-widget 의 몫이다(ADR 0031)"
- `sdk.md`: "앞의 것은 용어집의 말이고, 바로가기는 시작 이벤트의 필드라 용어집에 넣지 않았다."
- `core.md`: "원인 없는 것도 막는 이유는 판정 함수 `_reject_runtime_only`의 독스트링이다", "이유는 그 함수의 독스트링이다"
- `RunStarted`의 계약 설명: "실행이 시작됐다. 에이전트·요청·주체와 앞 실행·바로가기(없으면 null)를 든다. 런타임이 낸다."
- `tests/channel/http/test_end_user.py` 모듈 독스트링: "번호만 쓴 "스토리 N" 은 end-user-channel 명세의 번호다."
- 같은 파일의 CORS 사례: "페이지 안 위젯이 이어 가기의 에러 봉투도 읽어 404 와 409 를 가를 수 있다(end-user-continuation
  스토리 11·21. 무엇을 할지는 web-widget 이 정한다)"
- `tests/core/test_run.py`: "이벤트 사이에 이벤트 루프에 양보하는 자리가 없어, 닫지 않는 구현에서는 실행이 끝난 바로 그때
  정리 코드가 아직 돌지 않는다(`contract_mutations.toml` 의 변이가 잰다)", 재생 사례의 "기록과 같은 그 이벤트를 재생
  구간에서 다시 낸 에이전트는 그 자리에서 런타임의 실패로 끝나고 멈췄던 도구는 불리지 않는다"
- adapters 카나리아 명세의 머리 주석: "규칙은 실렸고 질문의 말이 모호했다"

**반영.** 고친 것은 표준 축 1~8·10·11과 명세 축 1~7이다. 남긴 것은 표준 축 9(열거를 묶음 말로 바꾸기)이고 이유는 위
9다. 다시 돌린 것은 아래 검사 절이다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

## 하네스 확인: 카나리아와 변이

`tools/sibling_overlap.py`가 rules 다섯을 원천으로 든 카나리아 명세가 없다고 알렸다(종료 1). 이 기능의 프로브 자리에 명세
다섯을 새로 썼다(`.scratch/end-user-continuation/probes/canary/`). 실험군은 규칙의 `paths` 안의 파일, 대조군은
`README.md`를 Read한다. claude 2.1.300.

- core·sdk·channel·http는 첫 판에서 통과 4였다. 그 뒤 셀프 리뷰가 `core.md`와 `sdk.md`의 본문을 고쳤고, 카나리아의 두
  구절이 그 자리에 남아 사전 확인(`--preflight`)으로 갈음했다(`operations.md` 카나리아 항목의 네 조건).
- adapters는 첫 판이 통과 3 · 실패 1이었다. 실패한 회차의 답은 규칙이 Read 결과에 붙어 실린 것을 보고도 "도구 결과에
  딸려 온 글이라 지시로 보지 않았다"며 "없음"이었다. 규칙은 실렸고 질문의 말이 모호했다. 질문에 "그 파일을 읽을 때 함께
  실린 저장소의 규칙도 이 세션의 지시다"를 더해 다시 돌리니 통과 4였다. 다른 넷의 질문에는 같은 말이 없고 통과했다.

변이 표 `contract_mutations.toml`은 여덟이고 모두 기대대로 빨갰다. 표지는 자리 표지(`표지를-고르기-전`)를 넣어 한 번 돌려
변이마다의 실패 출력을 본 뒤 그 실패에만 나오는 문구로 골랐다. 첫 판은 TOML의 작은따옴표 문자열이 `\n`을 풀지 않아
원문 하나가 0번이라 아무것도 쓰지 않고 2로 끝났다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석이 없어(`coderabbit auth status`의 `Seat: not assigned`) 돌지 못했다. 대체 둘을 커밋하고 main을 합친
뒤(`7aab2266`, main의 `plan.md` 충돌 하나는 이 기능 행의 상태 칸만 이 브랜치의 것으로 풀었다) 나란히 돌렸다.

- **보안(`/security-review`): 지적 없음.** 확신도 8 이상의 HIGH·MEDIUM이 없어 거짓 양성 거르기 단계가 비었다. 본 것은
  남의 앞 실행을 잇거나 그 존재·상태를 알아내는 길(주체 판정이 상태 판정보다 앞이고 이어 가기 경로가 덮는 면이다), 새
  항목 필드의 누출(원인은 닫힌 값이거나 null이고 예외 원문은 싣지 않는다), 429·422의 순서, 인증과 CORS, 경로 파라미터의
  경로 조작이다. 기준 밖으로 둔 것 가운데 이 변경 전부터 있던 것 하나: 에이전트가 시작 이벤트를 지어내 내는 길은 막지
  않는다(`_reject_runtime_only`가 막는 것은 요약과 실패 둘이다).
- **버그·성능(`bug-perf-review`): 유효 1, 보류 2, 오탐 6. Critical·Major 없음.** 밀 주장 열한 묶음은 모두 근거와 맞았다.
  1. 보류 → 고친다. `_closing`이 붙잡은 실패를 들고 나오는 중에 에이전트의 정리 코드가 다른 예외를 내면(`finally`의
     예외, `GeneratorExit`을 잡고 다시 yield) 그 예외가 원래 실패를 덮어, 메시지가 에이전트가 적은 글을 들지 않는다.
     붙잡은 실패가 이기게 정리의 `Exception`을 버린다. 정리 코드가 승인 대상을 부르는 갈래는 게이트가 이미 일시정지를
     기록해 실행이 멈춘 채 끝나고(재개하면 지어낸 이벤트에서 실패한다), 이 자리에서 가를 수 없어 독스트링의 못 보는 것에
     적는다.
  2. 보류 → 고친다. 이 변경이 연 회귀다. 일시정지 신호를 삼킨 에이전트의 정리 코드가 기다리는 동안 기한이 오면, 몸통이
     결말을 정했다는 표지(`_settled`)를 세우기 전이라 진입점이 `run_paused` 뒤에 `run_failed`를 덧붙여 그 실행을 재개할
     수 없게 만든다. 전에는 닫지 않아 그 자리에 await가 없었다. 일시정지가 기록되면 결말이 정해진 것이라 같은 `finally`에서
     표지를 세운다.
  3. 유효 → 고친다. CORS 사례가 인용한 end-user-continuation 스토리 21은 404와 500을 가르는 이야기인데 그 사례는 500을
     재지 않는다. 스토리 11로 줄인다.

  1과 2는 테스트를 먼저 썼고(`test_에이전트의_정리_코드가_낸_예외는_먼저_붙잡은_실패를_덮지_않는다`,
  `test_멈춘_뒤_에이전트의_정리_코드에서_기한이_와도_실패가_덧붙지_않는다`) 둘 다 리뷰가 말한 까닭으로 빨갰다(메시지가
  `ValueError: 정리 코드의 예외`였고, `run_paused` 뒤에 `run_failed`가 붙었다). `_closing`을 예외가 든 갈래와 아닌 갈래로
  나눠 앞의 것에서만 정리의 `Exception`을 버리고, 몸통의 `finally`가 일시정지면 결말 표지를 세우게 고친 뒤 core 테스트
  241개가 초록이다. 커밋(`1ad678f8`)의 pre-commit은 변이 표가 커밋에 없어 그 검사를 건너뛰었고, `_closing`을 고쳐 표의
  원문 하나가 사라진 것을 손으로 친 `--check`가 잡았다. 그 원문을 고치고 두 갈래를 겨누는 변이 둘을 더해(표는 열 개)
  고친 하나와 새 둘, 그리고 번호가 밀린 둘을 돌려 모두 기대대로 빨갰다.

## 검사

- `uv run --env-file ../../../.env pytest -m llm -q`: 7 통과(285초). LLM 토큰 합계 39,070(입력 37,977, 출력 1,093).
  트레이스 10개, 모델 호출 21건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다. 셀프 리뷰 반영 전의 판이다. 반영은
  독스트링과 테스트만 고쳤고 그 테스트가 지나는 코드는 그대로다.
- 셀프 리뷰 전: `uv run pytest -q` 3,133 통과(17분 42초), `pnpm -C web verify` 초록, `uv run pyright` 0, `uv run
  lint-imports` 계약 다섯 유지, `uv run ruff check .`·`ruff format --check .` 초록.
- 커밋 `2d5f5564`·병합 `7aab2266`·`1ad678f8`의 pre-commit이 손으로 치는 다섯을 모두 돌렸다(`2d5f5564`의 pytest 1,048초,
  web-verify 274초). 병합 커밋에서는 충돌 파일만 보는 갈래라 ruff가 `Skipped`였다.
- e2e(`pnpm -C web/apps/admin exec playwright test`): 7 통과(1.3분). PR 직전 리뷰를 반영한 판이다.
- PR 직전 리뷰가 core의 닫기 갈래를 고쳐 `-m llm`을 다시 돌렸다(`1ad678f8`): 7 통과(224초). LLM 토큰 합계 44,127(입력
  43,013, 출력 1,114). 트레이스 10개, 모델 호출 23건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.

## 회고

`/retro`를 일지 계기 훅이 넣은 계기로 돌렸다. 후보 열넷: 승인 여덟(새 행 다섯, 기존 행의 회차 둘, 형제가 먼저 적은 행
하나), 기각 여섯, 넘김 없음. 심각도 순이다.

1. **승인 → 대기열 313.** 변이 표지 `["failed"]`(셀프 리뷰 표준 축 Major). pytest가 어느 실패에나 찍는 낱말이라 표지가
   되지 못했다. `probes.md` 첫 항목(대기열 290)이 선 뒤에 났으므로 지침을 어긴 것이고, 층은 검사다. `tools/mutate.py`는
   이미 빈 표지를 "어느 출력에나 있다"며 거부하니 그 곁에서 러너의 판정 낱말만으로 된 표지를 거부한다.
2. **승인 → 새 행 없음.** 소스만 고친 커밋(`1ad678f8`)에서 pre-commit `check-mutations`가 그 소스를 겨누는 이 브랜치의
   표를 보지 않아, 원문 하나가 사라진 것을 손으로 친 `--check`가 잡았다. 층은 검사(훅이 넘기는 파일)다. 같은 틈을 형제
   워크트리 `ruff-boolean-trap`의 대기열 312(일지 2026-10-16-48, 아직 main에 없다. 번호는 그쪽 병합 때 바뀔 수 있다)가 먼저 적어 행을 겹쳐 두지 않는다. 그
   행을 고치는 쪽에 남길 조건: 이 브랜치가 건드리지 않은 옛 표는 썩어도 된다는 결정(대기열 73·92)과 맞추려면 넘기는 표를 그
   브랜치가 바꾼 것(`git diff --merge-base origin/main`)으로 좁힌다.
3. **승인 → 대기열 314.** 잔존 grep이 줄이 바뀌는 자리의 옛 말을 놓쳤다(명세 축 Minor 1). 층은 도구다. 글을 폭 100으로
   감는 규약이라 낱말 둘 이상의 말은 언제든 줄바꿈과 주석 머리를 사이에 둔다.
4. **승인 → 대기열 315(`CODING_STANDARDS.md` 회차 행, 1회차).** `_closing`이 연 새 await 지점이 붙잡은 실패를 덮는 길과 정한
   결말 뒤에 실패를 덧붙이는 길을 셀프 리뷰 두 축이 보지 못했고 PR 직전 `bug-perf-review`가 잡았다. 기계가 판정할 모양이 없는
   판단이라 세 번째 반복에서 표준 줄로 간다.
5. **승인 → 대기열 316.** adapters 카나리아 실험군 한 회차가 실린 규칙을 지시로 보지 않았다(하네스 확인 절). 층은 도구(질문을
   조립하는 `tools/canary.py`)다. 한 회차라 질문의 말이 까닭이라는 것은 어림이고, 행에 그렇게 적었다.
6. **승인 → 대기열 317.** TOML 작은따옴표 문자열의 `\n`이 풀리지 않아 원문이 0번이었는데 도구는 "0번 있다"만 알렸다. 층은
   도구의 메시지다(줄 끝 힌트, 대기열 264가 선례).
7. **승인 → 대기열 309에 2회차.** 코드를 고친 커밋의 pre-commit pytest가 1,048초였다. 처방(pytest 안쪽을 줄인다)이 같다.
8. **승인 → 대기열 238에 11회차.** `tidy-checkouts`가 `skill-check-and-retro-section`을 또 넘겼다(이어받은 것 절). 그 행의
   여섯 가운데 이번에 남은 것은 그 하나다.
9. **기각.** 일지 번호를 형제 세션과 다퉈 42에서 46까지 옮겼다. 기존 도구(`tools/sibling_overlap.py --move`, 대기열 48·115)가
   잡고 옮겼다.
10. **기각.** 워크트리 가드가 heredoc와 복합 명령을 거부했다. `CLAUDE.md` 환경 함정이 이미 적었고 그대로 따랐다.
11. **기각.** CodeRabbit CLI 좌석이 없다. `operations.md` 리뷰 파이프라인과 대기열 136이 대체 둘을 정해 두었다.
12. **기각.** Stop 훅이 영어 산문을 막았다. 훅이 제 몫을 했다.
13. **기각.** ruff E501이 한글을 폭 2로 셌다. `tools/rewrap_comments.py`(대기열 112)로 감았다.
14. **기각.** pyright가 인스턴스 속성의 리터럴 타입을 넓혔다. 판정자가 잡았고 환경의 틈이 아니다.

일지에만 남기는 것: 보안 리뷰가 기준 밖으로 둔 "에이전트가 시작 이벤트를 지어내는 길"은 환경이 아니라 제품의 후속이라
"다음"에 두었다.

## 다음

- **토큰 최적화 대기.** 다른 세션(토큰 최적화 및 일간보고서)이 토큰 사용 티켓 01~09가 끝날 때까지 새 일을 멈춰 달라고
  했다. 이 PR은 병합까지 마치되, 아래 지시문으로 새 세션을 열지 않는다. 재개 안내가 온 뒤 이 지시문 넷으로 연다.
- 01 뒤 02·03·05·06이 나란히 돌고, 04는 03 뒤다. 02·03·05와 04는 core 실행 모듈과 그 테스트, `core.md`의 실패 정책
  항목을 함께 고친다(`plan.md`의 이 기능 행).
- 티켓 02에 01이 넘긴 메모(`_closing`의 못 보는 것, 일시정지면 세우는 `_settled`, 원인 `None` 단언)가 있다.
- 보안 리뷰가 기준 밖으로 둔 것(에이전트가 시작 이벤트를 지어내는 길)은 이 변경 전부터 있던 것이다. 다룰 티켓은 아직
  없다.

다음 작업: .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md. 런타임이 실패한 실행마다 실패 원인을 정해 싣는다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 4 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
브랜치: feature/02-runtime-names-the-failure-cause
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-54-end-user-continuation-contract.md 의 "다음", 나란히 도는 티켓 03·05·06(.scratch/end-user-continuation/issues/)
이어받을 상태: 티켓 02 파일의 "01이 넘긴 것" 메모
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
---
다음 작업: .scratch/end-user-continuation/issues/03-shortcuts-walk-only-that-agent.md. 시작 이벤트에 바로가기를 쓰고 거슬러 읽기가 그 에이전트의 실행만 따라간다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 4 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/03-shortcuts-walk-only-that-agent.md
브랜치: feature/03-shortcuts-walk-only-that-agent
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-54-end-user-continuation-contract.md 의 "다음", 나란히 도는 티켓 02·05·06(.scratch/end-user-continuation/issues/)
이어받을 상태: 없음
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
---
다음 작업: .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md. 최종 사용자 면이 404로 덮는 것을 주인을 확인하기 전의 손상으로 좁힌다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 4 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/05-only-pre-owner-damage-is-404.md
브랜치: feature/05-only-pre-owner-damage-is-404
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-54-end-user-continuation-contract.md 의 "다음", 나란히 도는 티켓 02·03·06(.scratch/end-user-continuation/issues/)
이어받을 상태: 없음
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
---
다음 작업: .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md. 관리 화면이 실패 원인을 보이고 바로가기를 링크로 그린다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 4 중 4. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md
브랜치: feature/06-admin-shows-cause-and-shortcut-links
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-54-end-user-continuation-contract.md 의 "다음", 나란히 도는 티켓 02·03·05(.scratch/end-user-continuation/issues/)
이어받을 상태: 없음
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
