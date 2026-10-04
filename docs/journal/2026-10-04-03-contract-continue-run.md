# 2026-10-04 (03) conversation 티켓 01 — 계약: 운영자가 HTTP로 끝난 실행을 이어 가고, 에이전트는 자기 교환만 받는다

일지 2026-10-04-02의 "다음"이 가리킨 새 세션이다. `/implement .scratch/conversation/issues/01-contract-continue-run-and-own-exchanges.md`로
시작했고 브랜치는 `feature/01-contract-continue-run-and-own-exchanges`, 주 체크아웃이다. 산출물은 여섯이다.

- sdk 넷(컨텍스트 멤버 `conversation`과 값 타입 둘, `run_started`의 `previous_run`, `conversation_summarized` 이벤트, 매니페스트의 `conversation_limit`)과
  트레이스 형식 3
- core의 하위 타입 둘(`DifferentPrincipal`, `NotContinuable`)과 이어 가기 진입점(`run(previous_run=)`), 판정 순서, 거슬러 읽기, 재개의 멤버,
  에이전트가 낸 요약 이벤트의 실패
- 채널의 새 경로 `POST /runs/{run_id}/continuation`, 표의 두 줄, 공유 409 설명, 다시 생성한 계약 파일과 클라이언트 타입, web의 `satisfies` 표
  셋·채널 경로 목록·결정 자리 조건·픽스처
- rules 다섯, 409 정의 문장의 자리 전부, 잔존 grep, `plan.md`의 conversation 행을 in-progress로
- 변이 표 `.scratch/conversation/probes/continuation_mutations.toml`과 그 README 줄
- 티켓 01을 done으로, 티켓 끝에 "이 티켓이 정한 것", 이 일지

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/conversation/issues/01-contract-continue-run-and-own-exchanges.md
> … 확인할 선행 조건: end-user-channel의 계약 티켓이 열려 있는지(로컬·원격 브랜치, 열린 PR, .scratch/end-user-channel/). 열려 있으면 먼저 연
> 쪽이 다른 주체 하위 타입 묶음을 작은 PR로 뗀다 … 이번 요청 범위: PR과 병합까지"

## 이어받은 것

PR #130은 2회차(`33321f0`)에서 CI 여섯이 초록이었고 `300b5f0`으로 병합됐다. CodeRabbit의 Major 하나(02를 값 기반 마스킹에 막아라)는 사용자가 02를
막지 않기로 해 답글만 남겼고 봇이 해결 완료로 닫지 않았다. GitHub 이슈는 만들지 않았다.

선행 조건: 주 체크아웃이 main이고 깨끗했으며 `git fetch` 뒤 `origin/main`과 같았다(`300b5f0`). end-user-channel은 로컬·원격 브랜치도, 열린 PR도,
`.scratch/end-user-channel/`도 없었다. 그래서 다른 주체의 하위 타입은 이 티켓이 짓고 작은 PR은 떼지 않았다. 의존성은 늘지 않아 측정 판과 견줄
것이 없었다.

## 이 티켓이 정한 일곱

일지 02의 "다음"이 01에 넘긴 것이다. 전부 티켓 파일 끝에도 적었다.

1. **컨텍스트 멤버와 값 타입(domain-modeling).** `AgentContext.conversation: Conversation`, `Conversation(summary, exchanges)`, `Exchange(request, output)`.
   용어집의 대화·교환·대화 요약을 그대로 이름으로 썼고 피할 말(히스토리, 턴, 메시지, 컨텍스트)은 쓰지 않았다. 값은 frozen dataclass 둘이고 열은
   튜플이라 불변이다. 새 모듈 `sdk/conversation.py`에 두고 신뢰 경계는 모듈 독스트링과 `AgentContext` 독스트링에 적었다. pydantic 모델로 두지
   않은 이유는 직렬화되지 않는 값이라서다.
2. **`run_started`의 앞 실행 필드와 요약 이벤트.** `previous_run: RunId | None = None`(용어집 "앞 실행"), `ConversationSummarized`(`type`
   `conversation_summarized`, 요약 글 `summary`, 덮는 끝 `last_covered_run`, `model`, `input_tokens`, `output_tokens`). 덮는 끝의 이름은 "덮인 교환
   가운데 가장 최근 실행"을 그대로 적은 것이고, `covers_through`는 범위의 시작이 있는 것처럼 읽혀 쓰지 않았다. 두 식별자 필드에 sdk 패턴을 걸지
   않은 것은 명세 검토대로이고 테스트가 손편집 값으로 그것을 고정한다.
3. **매니페스트 한도 필드.** `conversation_limit: int | None = Field(default=None, strict=True, ge=1)`. 무엇을 세는지는 필드 주석과 `sdk.md`에
   적고 요약의 동작은 02를 가리켰다.
4. **하위 타입 둘.** `DifferentPrincipal`(다른 주체)과 `NotContinuable`(이어 갈 수 없음). 메시지는 앞 실행의 식별자를 들되 남의 주체 이름은 들지
   않는다(최종 사용자 경로가 404로 덮을 때 새지 않게). `NotContinuable`의 메시지는 `run_status()`의 상태를 든다.
5. **이어 가기 진입점의 시그니처.** 새 함수가 아니라 `run()`의 키워드 인자 `previous_run: RunId | None = None`이다. `resume()`을 따로 둔 논거가
   "입력이 실제로 다르다"였는데 이어 가기는 `run()`의 입력에 앞 실행 하나가 더해진 것이라 그 논거가 반대로 선다. 없음은 새 대화라는 뜻 하나이고
   지금의 모든 `run()` 호출(CLI, 채널, 테스트)이 그대로 돈다.
6. **새 경로의 접미사와 `operation_id`.** `/runs/{run_id}/continuation`, `continue_run`. 용어집 "이어 가기(Continuation)"에서 왔고 결정 경로
   `/approval`과 같은 명사 꼴이다. 라우터 테스트 하나가 두 경로가 서로 가로채지 않는 것을 고정한다.
7. **생성기가 내는 TS 타입.** `anyOf[integer(minimum 1), null]`은 `number | null`로 난다. 최솟값은 타입에 실리지 않는다(openapi-typescript 7.13.0,
   생성물을 읽었다).

## 구현에서 정한 것

- **거슬러 읽기의 모양.** `_read_link`(한 실행을 읽어 손상을 거른다)와 `_walk`(고리를 거슬러 읽는다)와 `_require_link`(실행마다의 검증)로 나눴다.
  `run()`의 `_continued`는 앞 실행을 하위 타입으로 가른 뒤 `_walk`에 넘기고, `resume()`의 `_resumed_conversation`은 시작 이벤트의 `previous_run`에서
  같은 `_walk`를 부른다. 앞 실행은 한 번만 읽는다 — 하위 타입 판정에 쓴 `_Link`를 `_walk`에 그대로 넘긴다.
- **손상 문구의 중립화.** `_sound_events`의 문구가 "재개할 수 없다"였는데 이어 가기의 거슬러 읽기도 같은 함수를 쓰므로 "…트레이스다"로 바꿨다.
  테스트가 그 문구를 매치하지 않아 깨진 것은 없다.
- **에이전트가 낸 요약 이벤트.** `_drive`의 에이전트 이벤트 자리에서 `ConversationSummarized`면 `RuntimeError`를 올려 `run_failed`로 끝낸다.
  재생 구간보다 앞이라 재개에서도 같다.
- **채널 테스트의 가짜 트레이스가 내는 형식은 3이다.** 어댑터가 지금 쓰는 값이고 `legacy`는 1 그대로다. core 테스트의 가짜 트레이스도 기본이 3이고,
  형식 2의 재개는 명시한 사례 하나로 남겼다.
- **gap 동안에도 참인 문장.** 요약 이벤트 타입의 독스트링은 "런타임이 … 접었다. 에이전트가 내면 실행이 실패한다"로, `core.md`는 "런타임만 발행한다.
  내는 계기와 실패는 02가 적는다"로, `sdk.md`의 한도는 "넘었을 때의 동작은 02가 적는다"로 썼다. `02`·`틈`으로 grep할 자리다.

## TDD와 변이

- sdk·core·어댑터·채널의 새 테스트는 구현 전에 썼지만 빨강은 전부 import 오류(아직 없는 이름)였다. 단언 하나하나가 무는지는 본 적이 없어
  변이 표 `.scratch/conversation/probes/continuation_mutations.toml`로 열둘을 되돌려 봤다. 판정 순서 둘(다른 주체가 끝나지 않음보다 앞, 고리가
  준비보다 앞), 패턴 거르기, 덮는 끝에서 멈추기, 다른 에이전트의 교환, 에이전트가 낸 요약, 요약 자리, 표의 두 줄, 헤더 3, 엄격 검증,
  결정 자리 조건(vitest), 스트림 술어의 종류 목록(tsc). 열둘 모두 기대대로 빨갰다. 결과는 프로브 README의 2026-10-04 결과 절.
- web은 TS가 먼저 빨갰다. 생성 타입을 다시 만들자 `satisfies` 표 셋과 생성 타입을 단 픽스처 전부가 tsc에서 깨졌고, 매니페스트를 펼친
  문자열 픽스처(`CALC_MANIFEST`)와 시작 이벤트의 필드 이름 목록을 단언한 테스트 하나는 vitest에서 깨졌다. 명세 검토가 짚은 그대로다.
- 구현 중 테스트 쪽 결함 셋을 고쳤다. 두 글자 에이전트 이름이 패턴을 어긴 것, 이어 가기 도우미가 요청한 이름의 에이전트를 저절로 등록해
  "없는 에이전트" 사례가 서지 않은 것, 재개 도우미가 자리를 읽느라 트레이스를 한 번 더 읽어 읽기 목록이 둘인 것.

## 셀프 리뷰

`/code-review main`을 두 축 병렬로 돌렸다. 범위는 base `300b5f0`, 수정 38, 커밋 0, 미추적 4였다.

- **표준 축**: Critical·Major 0, Minor 6, Nit 7. **명세 축**: Critical·Major 0, Minor 2, Nit 3. 두 축이 같은 Minor 하나를 냈다.
  - **Minor(둘 다, 반영): 틈 동안 거짓인 현재형 둘.** 매니페스트 필드 주석의 "넘으면 런타임이 … 접는다"와 `core.md`·`run.py` 모듈 독스트링의
    "`conversation_summarized`는 런타임이 발행한다". 02 전에는 아무것도 접지 않고 내지 않는다. "넘긴 것이 요약의 대상이고 동작은 02가
    적는다", "런타임만 낼 수 있다(계기는 02)"로 고쳤다. 틈 규칙을 티켓이 세 번 적었는데도 `sdk.md`에는 지키고 그 옆 주석에는 놓쳤다.
  - **Minor(명세 축, 반영): `_walk`의 순환 검사가 멈춤 조건 뒤였다.** 되돌아가는 간선의 목적지가 요약이 덮는 끝과 같은 손편집 트레이스는
    명세의 "순환 → `PluginError`"인데 조용히 섰다. 정상 고리에서 덮는 끝은 요약보다 오래돼 지나온 실행일 수 없으므로 순환 검사를 앞으로
    옮겨도 기존 사례는 그대로다. 사례 `_cycle_at_covered_end`를 더했고, 그 자리를 겨눴던 덮는 끝 변이는 `--check`가 원문이 옮겨 간 것을 잡아
    새 모양으로 고치고 다시 돌렸다.
  - **Minor(표준 축, 반영) 넷.** 라우터의 `run_stream`과 `continue_stream`이 한 줄만 다른 중복이라 `started(body, request, previous_run)` 하나로
    모았다. 채널의 409 테스트가 "메시지가 가른다"를 단언하지 않아 사례마다 가르는 낱말(주체·paused·꺼진)과 남의 주체 이름이 없는 것을
    단언했다. 변이 결과가 어디에도 적히지 않아 프로브 README의 결과 절과 이 일지에 적었다. 불변 테스트의 `setattr`에 왜 직접 대입이 아닌지
    (pyright가 먼저 막는 타입 쪽 효과와 런타임 효과의 가름)를 주석으로 뒀다. 타입 우회 주석은 없다.
  - **Nit(반영) 다섯.** `Disabled` 독스트링의 409 자리(넷이 선 자리로), 어댑터 모듈 독스트링의 "헤더에서 파일째 거부된다"를 실측처럼 읽히지
    않게 형식 목록이 막는 것으로, 가려진 픽스처 인자 하나, 티켓의 "가짜 컨텍스트 둘"에 셋이 된 것, 이 일지의 옛 문구 인용("재개할 수
    없다"는 셋 중 하나이고 다른 하나는 "재생할 수 없다"였다).
  - **보류 넷.** `_continued`와 `_resumed_conversation`의 셋 줄 중복(예외 타입이 다른 것이 곧 뜻이라 두 함수가 읽기 쉽다), `_output_of`의
    도달 불가 분기(타입 좁힘이 필요한 자리라 남겼다가 PR 리뷰 뒤 지웠다), `CONTEXT.md`에 "덮는 끝"·"갈래"·"고리의 처음"을 올릴지(표현이지 새 개념은 아니라 보고
    02·04가 같은 말을 쓰면 그때 domain-modeling으로 본다), 프로브 README의 변이 행이 가리키는 일지 문장(이 절이 그 문장이다).

## PR 리뷰

PR #131. PR 직전 CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않았다. 푸시 뒤 `@coderabbitai review`를 남겼다.

> 사용자: "ci 끝났어"

1회차(`07bd70d`). CI 여섯이 초록이었다(`gh run list`로 그 커밋의 실행인 것을 봤다). CodeRabbit은 `300b5f0..07bd70d`를 실제로 보고(파일 42, 생성
타입은 경로 필터로 제외) 지적이 없었다. 시간당 포함 리뷰 1회를 썼다. claude-review는 Critical·Major 0, Minor 4, Nit 2를 냈고 전부 `core/run.py`의
구조다.

- **Minor 셋(반영): `_walk`의 책임, `_summary_of`의 중복 호출, `_output_of`의 도달 불가 분기.** 셀프 리뷰가 보류했던 둘을 리뷰어가 같은 자리에서
  다시 짚었고 처방(`_Link`에 필드로 들고, `_require_link`가 좁힌 값을 돌려준다)이 셋을 한 번에 지웠다. `_Link.summary`를 `_read_link`가 한 번
  구하고, `_require_link`가 끝남을 본 `run_finished`를 돌려주며, 다음 실행을 읽을지 멈출지는 `_next_link`가 가른다. `_summary_of`와 `_output_of`는
  사라졌다. 옮겨 간 코드를 겨눈 변이 둘의 원문을 `--check`가 잡아 새 모양으로 고치고 둘만 다시 돌려 빨강을 봤다.
- **Minor 하나(보류): `_continued`와 `_require_link`가 주체·끝남 두 조건을 다른 예외 타입으로 되풀이한다.** 리뷰어도 지금은 갈라지는 이유가
  분명해 허용한다고 했다. 셋째 판정이 더해질 때(02의 요약 계기는 판정이 아니라 거슬러 읽기 뒤의 일이라 아직 아니다) 한 함수로 모은다. 02의
  티켓이 "거슬러 읽기가 모은 원문 교환"에서 시작하므로 그때 이 자리를 지난다.
- **Nit 하나(반영): `run()` 독스트링의 "그다음" 홀로 선 줄.** 모듈 독스트링을 다시 흘리다 남긴 것이다.
- **Nit 하나(보류): `_Context.__init__`의 위치 인자 여덟.** 다음 멤버가 늘 때 키워드 전용으로 바꾼다. 부르는 자리가 `_drive` 하나다.
- 용어집의 "덮는 끝"·"갈래"는 셀프 리뷰 보류와 같은 판단이고 02·04가 같은 말을 쓰면 올린다.

> 사용자: "ci 끝났어"

2회차(`e33bacd`). CI 여섯이 초록이었다. CodeRabbit은 "Review rate limited"라 둘째 커밋(리팩터와 일지)을 보지 않았다. 1회차가 시간당 포함 리뷰
하나를 썼다. claude-review는 Critical·Major 0, Minor 2, Nit 1이었다.

- **Minor 둘(보류, 리뷰어도 후속으로 허용).** `_continued`와 `_resumed_conversation`의 셋 줄 중복(1회차와 같은 자리), 그리고 `_walk`가 첫
  링크에 `_require_link`를 다시 돌려 주체·끝남 두 검사가 그 링크에서는 죽은 분기인 것. 둘 다 02가 거슬러 읽기를 지날 때 한 번에 본다. 02의
  티켓이 "거슬러 읽기가 모은 원문 교환"에서 시작하므로 그 세션이 이 자리를 읽는다.
- **Nit 하나(반영): `run_stream`이 `started(body, request, None)` 한 줄 래퍼인 이유.** `started`를 바로 의존성으로 걸면 FastAPI가 `previous_run`을
  질의 파라미터로 읽는다. 독스트링에 적었다.

> 사용자: "ci 끝났어"

3회차(`39af1bc`). CI 여섯이 초록이었다. CodeRabbit은 "Review finished"였고 인라인 코멘트가 0이라 둘째·셋째 커밋에도 지적이 없다. claude-review는
Critical·Major 0, Minor 2, Nit 1이고 회차마다 새 자리를 냈다. 고리 읽기를 별도 모듈로 옮길지는 02 전에 정하라는 것이라 티켓 02 끝에 "01이 넘긴
메모"로 적었고, 재개가 같은 멤버를 준다는 동등성 테스트는 이미 있는 재개 테스트(재생 대조가 통과하는 것)가 그것이라 더하지 않았다. `_require_link`의
이름(값을 돌려주는 `require`)도 그 메모에 들었다. 여기서 반영 루프를 멈추고 병합한다 — 셋 다 02가 지나는 자리이고 받는 쪽에 적혔다.

## 갈린 곳

- 시그니처는 새 함수가 아니라 `run(previous_run=)`으로 갔다. 일지 02는 "새 함수인지 `run()`의 인자인지"로 열어 두었고, `resume()`을 따로 둔
  논거("재개일 때는 이 인자 셋이 무시된다")가 이어 가기에는 반대로 선다고 봤다.
- 채널 테스트의 가짜 트레이스가 내는 형식을 2에서 3으로 바꿨다. 티켓이 요구한 것은 아니지만 "어댑터가 지금 쓰는 값"이라는 그 가짜의
  설명이 거짓이 되는 자리였다.

## 번복하거나 고친 것

- 손상 문구를 재개 전용("재개할 수 없다")에서 중립("…트레이스다")으로 바꿨다. 이어 가기의 거슬러 읽기가 같은 함수를 쓴다.
- 잔존 grep이 내가 새로 쓴 문장 넷을 잡았다(`두 경로`, `형식 2 트레이스` 둘, `plan.md`의 옛 조건 문구). 뜻은 맞았지만 글자 그대로 0이어야
  해서 고쳤다. 남은 것은 세 원소 리터럴 `Literal["1", "2", "3"]`, 옛 형식 둘을 도는 parametrize `["1", "2"]`, 무관한 스트림 테스트 데이터, 그리고
  ADR 0023 본문이 ADR 0014의 2026-09-26 이력을 따옴표로 인용한 자리다. 인용은 글자 그대로여야 하므로 두었다.

## 회고

후보 둘을 냈다. 사용자가 자리에 없어 묻지 못했고 승인 대기다(PR 본문과 마지막 보고에 같은 둘을 올린다). 승인되면 대기열에 적는다. 이미
승인된 행 하나(56)에는 회차를 더했다. 나머지는 기록만 남긴다.

- **후보 1(승인 대기): 주석·독스트링 감기 도구를 `tools/`에 둔다.** 대기열 53이 "또는 `tools/`의 감기 도구"로 열어 둔 길이다. 편집 직후 훅
  (`hook_ruff_line_width`)이 넘친 줄을 알려 주지만 고치는 것은 손이라, 이 세션은 한글 주석을 폭 100에 맞추느라 스크래치의 감기 스크립트를
  아홉 번 돌렸다(주석 문단과 모듈 독스트링 문단을 가르는 둘). 2회차(일지 2026-10-01-02, 이 일지). 자리는 `tools/rewrap_comments.py`이고 훅의
  additionalContext가 그 명령을 함께 알려 주면 고치는 데 한 번이다. 변이 표의 원문이 ruff format 뒤에 옮겨 가는 것도 같은 가족이라, 변이 표는
  코드를 포맷한 뒤에 쓴다는 한 줄을 `tools/mutate.py` 독스트링에 둘지 함께 본다.
- **후보 2(승인 대기): `operations.md` LLM 테스트 절에 토큰 합계를 내는 법 한 줄.** "돌렸으면 일지 검사 절에 통과 수와 트레이스의 토큰 합계를
  적는다"가 있지만 어떻게 세는지는 없어 앞선 일지(2026-09-29-02)를 grep해 `--basetemp`로 트레이스를 남기는 길을 찾았고 모델을 한 번 더 불렀다.
  그 일지는 도구를 올리지 않기로 했었다. 2회차. 한 줄 후보: "`--basetemp=<스크래치>`로 돌려 남긴 트레이스의 `llm_called` 토큰을 더한다".
- **회차 추가, 대기열 56: pytest의 한국어 매개변수 id 이스케이프.** 변이 도구의 출력이 `[다른 주체]`로 찍혀 어느 사례인지
  못 읽었다. 2회차(일지 2026-09-29-02, 이 일지).
- **기록만: 가드레일이 일한 사례 넷.** 셀프 리뷰 브리프의 주장 검증 4(미래형)가 틈 동안 거짓인 현재형 둘을 두 축에서 모두 잡았다. 변이 표의
  `--check`가 리팩터로 옮겨 간 원문을 잡았다(대기열 92). heredoc 상한 훅이 두 번 막아 편집을 스크립트 파일로 옮겼다. 파이프를 단 판정 명령을
  훅이 잡았다.
- **기록만: 테스트 도우미가 요청한 이름의 에이전트를 저절로 등록해 "없는 에이전트" 사례가 서지 않았다.** 도우미의 기본값이 사례의 전제를
  지웠다. 한 번이고 그 테스트에서 명시 플러그인으로 고쳤다.
- **기록만: 잔존 grep이 내가 새로 쓴 문장 넷을 잡았다.** 뜻은 맞았지만 글자 그대로 0이어야 해서 고쳤다. 글자 grep의 값이 그것이라 규칙은 그대로다.
- **기록만: 비용.** 셀프 리뷰 두 축 합 52만 토큰(표준 28만·도구 36회, 명세 24만·도구 30회). 변이 열둘 약 6분(vitest·tsc 포함). web verify
  약 3분을 세 번.

## 검사

리뷰 반영 뒤 전부 다시 돌렸다. 판정 명령은 파이프 없이 스크립트 파일(`gates.sh`)로 돌리고 종료 코드를 모았다.

- pytest 1381 passed, 4 deselected(경고 셋은 변경 전부터 있던 pytest-asyncio의 것)
- ruff check와 ruff format 통과
- pyright 0 errors
- lint-imports 5 kept
- 지침 검사와 타입 우회 검사 통과
- `pnpm -C web verify` 통과(테스트 파일 15, 테스트 265)
- `uv run --env-file .env pytest -m llm` 4 passed. core 실행 모듈·어댑터·채널을 건드렸으므로 돌렸다. `--basetemp`로 남긴 트레이스 여섯이
  모두 형식 3이고 `llm_called` 12건의 토큰 합계는 14,210(입력 13,790, 출력 420)이다.
- 변이 12 모두 기대대로(프로브 README).

PR 직전 CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않는다.

## 다음

- **PR과 병합은 이 세션이다**(지시문의 범위). 병합 뒤 `next-session`.
- **그다음 `/implement .scratch/conversation/issues/02-runtime-summarizes-over-limit.md`.** 새 세션, `feature/02-runtime-summarizes-over-limit`
  브랜치. 01이 02로 넘긴 것은 `02`·`틈`으로 grep해 다시 읽는다 — `core.md`의 "내는 계기와 실패", 재개되는 실행 자신의 요약 읽기와 재생 기록
  열(`_BOUNDARY`), `sdk.md`·매니페스트 주석의 "동작은 02". 값 기반 마스킹의 ADR 0009·0022 이력 초안이 02보다 먼저 서면 02가 따른다
  (`plan.md`의 conversation 행).
- **04(관리 화면 링크)는 01 뒤라 지금 열린다.** 02·03과 나란히 돌 수 있다. 03은 01·02 뒤다. 03과 04 가운데 뒤에 병합되는 쪽이 `plan.md`를
  `done`으로 바꾼다.
- end-user-channel은 main을 들이며 `DifferentPrincipal`을 쓴다. 결정의 주체 판정도 같은 타입이다.
- 프론티어는 셋이다. conversation(02·04), end-user-channel(명세), design-system(설계 인터뷰).
- 하네스 쪽에 남은 것: 대기열 100~104.
