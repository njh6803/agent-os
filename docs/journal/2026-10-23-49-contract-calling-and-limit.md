# 2026-10-23 (49) web-widget 01: 계약에 calling 항목과 429의 limit을 싣고 위젯 클라이언트를 만든다

티켓 `.scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md`. 브랜치 `feature/01-contract-calling-item-and-limit-kind`. 나란히 여는 둘 가운데 하나이고, 다른 하나는 티켓 03(widget-app-skeleton)이다. 모델은 Opus 5.5 / xhigh(레벨 스윕의 갈래).

## 받은 지시

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md
> 다음 작업: .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md. 최종 사용자 스트림의 `calling` 항목과 429의 `limit` 종류를 계약에 싣고 api-client에 위젯 클라이언트를 만든다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md
> 브랜치: feature/01-contract-calling-item-and-limit-kind
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md 의 "다음" 절. 나란히 도는 티켓은 .scratch/web-widget/issues/03-widget-app-skeleton.md
> 이어받을 상태: 명세와 티켓 열하나가 PR #373(squash 8a026f3c)으로 main에 병합됐다. 원격 브랜치 docs/web-widget-spec-2는 삭제 명령이 자동 모드 분류기에 거부되어 아직 남아 있다. 지우기는 사람이 확인한 뒤에 한다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 시작

- `tidy-checkouts`를 먼저 돌았다. 루트 main을 893e0fe8에서 8a026f3c로 당겼고, 병합된 워크트리 `02-runtime-names-the-failure-cause`를 지웠다. 나머지 워크트리는 병합된 PR이 없거나 쥔 프로세스가 있어 남겼다.
- 원격 브랜치 `docs/web-widget-spec-2`는 지시대로 건드리지 않았다.

## 한 것

### calling 항목

`llm_called`의 `tool_calls`가 비지 않으면 투영이 `CallingItem(tools=도구 이름의 차례)`를 낸다. 빈 것은 지금처럼 항목이 없다. 유니온 멤버가 여덟이 됐고, `.claude/rules/channel.md`의 투영 항목은 "종류로 가르며, `llm_called`에서만 도구를 요청했는지의 조건 하나가 붙는다"로 고쳤다. 계약의 설명은 시점을 말하지 않는다(티켓의 "병합 뒤에 틈").

### 429의 LimitEnvelope

- 공용 층의 상한 열거를 `LimitKind`(값은 계약의 코드, 봉투 문구에 드는 한국어 이름은 `label`)로 바꾸고, `LimitExceeded`가 그것을 든다. `failure_for`의 429 갈래가 `limit`을 `_Failure`로 넘기고 `error_envelope`가 그때만 `LimitEnvelope`를 짓는다. 문구는 그대로다.
- 문서의 모양은 상태 코드에 딸린다(`routes.py`의 `_ENVELOPE_OF = {429: LimitEnvelope}`). 그래서 429를 적는 최종 사용자 경로 넷의 429만 `LimitEnvelope`를 가리키고, 운영자·관리 경로의 계약은 바뀌지 않았다. `openapi.json`을 다시 뽑은 diff로 확인했다.

### 스트림 라우트의 에러 문서

스트림 라우트는 지금까지 `documented_stream_errors`가 봉투의 이름 참조(`_ENVELOPE_REF`)를 손으로 적고, 그 컴포넌트는 관리 라우트의 등록에 기댔다. `LimitEnvelope`는 등록해 주는 관리 라우트가 없어 같은 길을 쓸 수 없었다. FastAPI 0.141.1은 추가 응답의 모델을 라우트 응답 클래스의 미디어 타입 아래에, 그것이 `None`이면 JSON 아래에 싣는다. 그리고 SSE 라우트의 판정은 `issubclass(response_class, EventSourceResponse)`이고 200 문서와 실제 응답의 `text/event-stream`은 하드코딩이다. 이 셋은 스크래치패드의 탐침으로 손으로 봤다. 그래서 미디어 타입만 비운 하위 클래스 `EventSourceWithJsonErrors`를 두고, 스트림 라우트도 관리 라우트와 같은 `documented_errors(...)`를 쓰게 했다. 이름 참조의 우회와 `documented_stream_errors`가 사라졌다. 이 결정은 ADR이 아니라 `.claude/rules/http.md`의 에러 문서 항목에 적었다. 계약은 바뀌지 않고 선언 방식만 바뀌어서다. FastAPI가 동작을 바꾸면 계약 시험이 빨개진다(아래 변이 1).

### 위젯 클라이언트

- `createWidgetClient(baseUrl: URL)`은 최종 사용자 경로 넷만 아는 openapi-fetch 클라이언트이고 토큰을 들지 않는다. 부르는 쪽이 요청마다 `Authorization`을 넘기고, 구독의 `Last-Event-ID`는 계약의 헤더 파라미터로 보낸다.
- `readEndUserFrames`는 블록마다 `item`(십진 정수 `id`와 술어로 좁힌 항목), `raw`(읽은 `id`나 null과 원문), `keepalive`(주석만 든 블록)를 낸다. 운영자 쪽 `readFrames`와 블록 가르기(`splitBlocks`)를 나눠 쓰고, `readFrames`의 동작은 바뀌지 않았다(기존 시험과 변이 표가 초록·기대대로).

## TDD와 변이

- 투영, 봉투, 계약, 위젯 클라이언트, `readEndUserFrames`의 시험은 빨강을 본 뒤 구현했다. 빨강을 본 적 없는 것은 셋이었다. 스트림 라우트의 미디어 타입 가드(구현 전부터 초록인 계약 시험이 지킨다), 매개변수화 시험의 `failure.limit`, 위젯의 타입 시험이다. 그리고 셀프 리뷰 전에 `readEndUserFrames`가 요청이 끊길 때 에러를 던지고 잠금을 푸는지 보는 시험을 구현 뒤에 더했다. 위젯은 이 길로 연결을 끊는다.
- 그 넷과 위젯 클라이언트가 토큰을 들지 않는 것을 새 변이 표 `.scratch/web-widget/probes/contract_mutations.toml`(8개)로 쟀다. 모두 기대대로 빨개졌다. 미디어 타입을 되돌리면 최종 사용자 경로의 계약 시험이, `limit`을 넘기지 않으면 매개변수화 시험 셋 가운데 첫째가, 위젯이 모든 경로를 알면 `@ts-expect-error` 셋과 경로 목록이, `limit`이 아무 문자열이면 타입 시험 둘이 빨개졌다.
- 이 브랜치가 stream.ts를 다시 쓰고 `Limit`을 `LimitKind`로 바꿔, 옛 변이 표의 원문 열이 깨졌다(`mutate.py --staged`가 막았다). 상한 표의 하나와 관리 화면 api-client 표의 아홉을 지금 코드에 맞췄다. 같은 표의 `관리 클라이언트가 채널 경로도 안다`는 main에서 이미 깨져 있었다(최종 사용자 경로를 `AdminPaths`에서 뺄 때 원문을 고치지 않았다). 이번 커밋도 clients.ts를 고치므로 같이 맞췄다.
- 두 옛 표를 전부 다시 돌렸다. api-client 표는 25개 모두 기대대로였다. 상한 표는 28개 가운데 27개가 기대대로였고, `결정은 칸을 차지하지 않음`이 두 번 모두 600초 제한으로 끊겼다.
- 그 하나를 갈랐다. origin/main을 `git archive`로 스크래치패드에 꺼내 이 워크트리의 가상 환경으로 같은 시험을 돌렸다(커밋하지 않은 스크래치 스크립트로 손으로 봤다). 변이 없는 main은 1 passed였고(대조. 꺼낸 사본의 `agent_os`를 읽은 것을 경로로 확인했다), 같은 변이를 넣은 main은 120초 제한에서 끊겼다(종료 124, 집계 줄 없음). 그래서 이 브랜치가 만든 것이 아니다. 시험을 읽으면 까닭이 보인다. 변이가 결정을 칸에서 빼면 `held-2`에 낸 결정이 429로 거절되지 않고 재개되고, 그 재개가 문에 막힌 도구에서 멈춘다. `ASGITransport`의 `client.post`는 응답을 끝까지 모으므로 문이 열리기 전에 그 자리에서 기다린다. 요청 쪽에 기한을 두면 같은 변이가 실패로 바뀔 것으로 본다(어림, 고치지 않았다). 이 티켓의 몫이 아니라 후속 일로 넘긴다.

## 검사

- 전체 러너(`tools/run_checks.py`): 15개 검사가 모두 통과했다. 이 실행은 routes.py 줄 끝 수정, 새 시험, 변이 표 수정보다 앞선 것이고, 커밋의 pre-commit이 그 뒤를 다시 본다.
- LLM 시험: 7 passed, 4980 deselected(4분 49초).
- LLM 토큰 합계 54,845(입력 53,790, 출력 1,055). 트레이스 10개, 모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.
- e2e(`pnpm -C web/apps/admin exec playwright test`): 운영자 채널 라우트의 응답 클래스와 api-client의 `readFrames`를 건드려서 로컬에서 쳤다. 처음 두 번은 `decision.e2e.ts`의 첫 시험이 39행(재개 스트림이 끝난 뒤 이벤트 영역에 `run_finished`가 5초 안에 보이는지)에서 빨갰다(전체는 1 failed·6 passed에 1.3분, 그 파일만 돌린 둘째는 1 failed·2 passed). 두 번 연속이라 diagnosing-bugs로 갈랐다. 같은 실행을 채널로 다시 읽으니 재개 스트림에 `approval_granted`(14.715초) → `run_resumed`(17.414초) → `tool_called`(17.580초) → `run_finished`(19.593초)가 모두 있었다. 스트림의 조각과 결말은 맞게 왔고, 허가에서 결말까지 4.9초 가운데 2.7초가 허가 뒤 재개까지의 구간(이 브랜치가 고치지 않은 core의 재개)이었다. 시험의 5초는 `approval_granted`가 보인 뒤부터 세고 결말 뒤 트레이스를 다시 읽는 시간까지 들어, 그 안에 들지 못했다. 그때 이 PC는 CPU 100%였다. 카나리아를 마치고 CPU가 52%일 때 같은 코드로 다시 돌리자 그 파일은 3 passed(1.0분), 전체는 7 passed(36.2초)였다. 같은 코드에서 부하만 다른 두 갈래라 부하에 따른 타이밍으로 본다. 이 브랜치가 재개를 느리게 했는지는 이 둘로 가르지 못하고, 매 푸시의 CI `e2e` 잡이 판정한다.
- 카나리아: rules 둘(`channel.md`의 투영 항목, `http.md`의 봉투·상태 코드 표·에러 문서 항목)을 고쳐서, 두 파일을 원천으로 든 명세 넷(`.scratch/end-user-continuation/probes/canary/`)을 새 `claude -p`(claude 2.1.302, Sonnet)로 돌렸다. 넷 모두 통과 4(실험군 세 회차가 카나리아를 옮기고 대조군 한 회차가 "없음")였고, 명세마다 `# 최신 결과:` 줄을 고쳤다. 넷은 이번에 고친 문장이 아니라 같은 파일의 앞선 문장을 묻는다. 그래서 이 결과가 보이는 것은 고친 뒤에도 두 파일이 `paths`에 맞는 Read에서 실린다는 것이다. 고친 문장마다 새 명세를 두지는 않았다(`sibling_overlap.py`의 알림은 그 파일을 원천으로 든 명세가 있으면 그것을 돌리게 한다). 다만 `http_rule_continuation_422`는 이번에 고친 에러 문서 항목 안의 문장을 묻는다.

## 인계 (셀프 리뷰 직전)

- 세션 컨텍스트가 약 31만 토큰으로 문턱을 넘은 채 `/code-review`를 부르자 인계 계기가 왔다. `next-session` "인계할 때" 1의 다섯에 들지 않아(곁 세션이 아니다. `get_session`의 `self`에 `parentSessionId`가 없다) 새 세션에 넘긴다. 셀프 리뷰는 밟지 않았다.
- 넘기는 세션의 제목은 `feature/01-contract-calling-item-and-limit-kind`이고 `feature/01-contract-calling-item-and-limit-kind (인계함)`으로 바꾼다.
- 이 세션이 고친 것: 카나리아 명세 결과 줄에 고친 항목을 처음에 틀리게 적어 바로잡았다(회고 12). 일지 번호를 45에서 47로 옮겼다. routes.py 줄 끝을 LF로 되돌렸다. 옛 변이 표 원문 열하나를 지금 코드에 맞췄다. 상한 표 #3의 후속 일을 세션 카드로 내려다 훅에 막혀 "다음"과 대기열 453에 적었다.
- 지시문:

```
다음 작업: .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md. 최종 사용자 스트림의 `calling` 항목과 429의 `limit` 종류를 계약에 싣고 api-client에 위젯 클라이언트를 만든다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md
브랜치: feature/01-contract-calling-item-and-limit-kind
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-49-contract-calling-and-limit.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-10-23-49-contract-calling-and-limit.md. 구현·변이·LLM 시험·e2e·카나리아 넷은 끝났다(결과는 일지 "검사"). 회고는 이미 돌아 일지에 `## 회고`와 `## 다음`(후속 한 줄)이 있다. 셀프 리뷰·PR 봇 회차에서 나는 사건은 그 회고 절에 덧붙인다(계기 훅은 다시 걸리지 않는다). 리뷰를 반영한 뒤 티켓의 검증 체크박스와 Status를 done으로 바꾸고 `git add -A`로 미추적 파일(새 변이 표, 일지)과 스테이지하지 않은 수정(옛 변이 표 둘, stream.test.ts, 카나리아 명세 넷, 대기열 453·454)을 함께 싣는다. 지금 `mutate.py --staged`가 빨간 것은 고친 옛 변이 표를 아직 스테이지하지 않아서다. 대기열 453·454는 커밋 직전 `sibling_overlap.py`로 번호를 다시 본다. origin/main이 대기열 끝에 449·450을 더해 병합 때 그 자리가 충돌할 수 있다. 원격 브랜치 docs/web-widget-spec-2는 사람이 확인하기 전에는 지우지 않는다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 워크트리 잠금을 풀었다(`git worktree unlock`, 오류 없음).
- open-session을 부른다 2026-10-23T12:43:36Z

## 셀프 리뷰 (이어받은 세션)

이어받은 세션이 같은 워크트리에 `EnterWorktree(path)`로 들어가 `/code-review`를 돌렸다. 범위는 base 8a026f3c, 바뀐 파일 33개, 미추적 2개(새 변이 표, 이 일지), 커밋 0개다. 명세는 티켓과 `.scratch/web-widget/spec.md`다. FastAPI 0.141.1 설치본의 `openapi/utils.py`·`routing.py` 발췌를 두 브리프에 실었다.

### 표준 축 (sonnet·high)

Critical·Major 없음, Minor 4, Nit 4.

- Minor 1. `tests/channel/http/test_end_user.py`의 시작 시험 독스트링에 "모델 호출은 항목이 없다"가 남았다. `test_main.py`는 '도구를 요청하지 않은'으로 고쳤는데 이 자리가 빠졌다.
- Minor 2. 문서의 `_ENVELOPE_OF = {429: LimitEnvelope}`와 달리 `failure_for(HTTPException(429), …)`는 `limit` 없는 429(`ErrorEnvelope`)를 낸다. 지금은 라우트가 그것을 던지지 않는다는 규칙 문장(`errors.py`의 "`HTTPException(429)` 를 던지지 않는다")만 막는다.
- Minor 3. `EventSourceWithJsonErrors` 독스트링이 FastAPI가 "셋 가운데 하나"를 바꾸면 미디어 타입을 재는 시험이 빨개진다고 하지만, keepalive는 미디어 타입이 아니고 그것을 재는 시험은 운영자 채널의 `test_모델이_조용한_동안_keepalive_주석이_나간다` 하나다.
- Minor 4. `readEndUserFrames`의 "수명과 끊는 길은 `readFrames` 와 같다"에 "루프에서 멈추면 잠금만 풀고 닫지 않는다"가 드는데, 그 길을 밟는 시험이 `readFrames`에만 있다.
- Nit. `errors.py`에서 `LimitEnvelope`가 `LimitKind`보다 앞에 선언돼 import 때 모델이 덜 지어진다. `http.md` 예외 표 항목의 "그것과 사이트의 발급자"의 "그것"이 흐리다. `errors.py`·`limits.py`의 "문구는 어느 상한인지만"이 `limit` 코드를 빼고 읽힐 수 있다. smell(판단): `error_envelope` 삼항식의 인자 되풀이, 시험의 다섯 칸 튜플 `Refusal`, 두 읽기의 try/finally 틀.
- 맞은 것: FastAPI 동작 주장, 고아 컴포넌트 하나, 4xx·5xx의 미디어 타입, 429의 `LimitEnvelope`가 최종 사용자 경로 넷뿐, 운영자·관리 계약 불변, ADR 0039 인용, 변이 표 개수(8·25·28), 프로브 README의 판, 대기열 453·454가 가리키는 이름.

### 명세 축 (본 세션의 모델)

빠진 요구 없음. 범위 넘침 Nit 2, 틀려 보이는 것 Minor 3·Nit 4.

- 다시 돌린 것: vitest 43 passed, 관련 pytest 75 passed, 계약 최신성, `check:api-client`. `readFrames`의 옛 판과 새 판에 무작위 입력 20,000개를 넣어 차이 0(node로 직접 불렀다).
- 범위 넘침 Nit. `EventSourceWithJsonErrors`로 `documented_stream_errors`를 지우고 운영자 라우트까지 바꾼 것은 티켓 밖이지만 `LimitEnvelope`를 계약에 올리는 데 필요했고 계약은 그대로다. `api_client_mutations.toml`의 main부터 깨진 행도 함께 고쳤다.
- Minor 1. 시험 독스트링 "위젯이 지금 부르는 도구를 보일 길이다"가 `calling`의 시점을 말한다(티켓 "병합 뒤에 틈이 있다").
- Minor 2. `items.py` 주석 "지금 core 는 모델 호출의 이벤트를 … 모으고"는 02가 병합되면 거짓이 되는데 02 티켓에 이 주석을 고칠 항목이 없다.
- Minor 3. 빈 줄 없이 끝난 마지막 블록도 항목으로 낸다. 서버가 `id: 123`을 보내다 `id: 12`에서 끊기면 `{kind:"item", id:12}`가 나와 그 `id`가 `pause_index`와 `Last-Event-ID`가 된다. `blocksFrom` 주석의 "위젯이 원문을 건너뛰고"와도 맞지 않는다.
- Nit. `test_end_user.py:563`의 잔존(표준 축 Minor 1과 같다). `stream.ts`의 "두 읽기가 갈리는 것은 `data` 가 없는 블록이다"의 반례(`id`가 없거나 십진 정수가 아닌 data 블록). 일지와 대기열 454가 훅 문구를 옮기며 원문의 큰따옴표를 작은따옴표로 바꿨다. 시험 독스트링이 없는 스토리 이름("상한")을 든다. `readEndUserFrames`의 멈춤 시험 없음(표준 축 Minor 4와 같다).

### 반영

고친 것:

- 시작 시험 독스트링의 "모델 호출은 항목이 없다"를 '도구를 요청하지 않은'으로(표준 Minor 1).
- `EventSourceWithJsonErrors` 독스트링이 FastAPI의 셋을 어느 시험이 지키는지 바로 적게 했다(표준 Minor 3). SSE 판정의 주어도 "이 클래스의 하위 타입"에서 "응답 클래스가 `EventSourceResponse` 의 하위 타입"으로 고쳤다.
- `readEndUserFrames`에 "읽는 쪽이 도중에 멈추면 잠금을 풀어 부른 쪽이 스트림을 닫을 수 있다" 시험을 더했다(표준 Minor 4, 명세 Nit). 빨강을 본 적이 없어 새 변이 표에 `최종 사용자 스트림을 읽다 멈추면 잠금을 풀지 않는다`(끝까지 읽거나 에러일 때만 푼다)를 더했고, 변이를 손으로 넣어 그 시험 하나만 빨개지는 출력을 본 뒤 표지를 골랐다.
- 시점을 말하던 문장들을 시점 없는 목적으로 바꿨다(명세 Minor 1·2). 시험 독스트링의 "위젯이 지금 부르는 도구를 보일 길이다"와, `items.py`의 옛 문장 둘(위젯이 지금 부르는 도구를 알 길이 이것뿐이라는 문장, "지금 core 는 모델 호출의 이벤트를 … 모으고")이다. 뒤의 것이 02의 병합으로 거짓이 되지 않으니 02 티켓에 넘길 것이 없다.
- 닫히지 않은 마지막 블록(명세 Minor 3). FastAPI는 `data` 다음에 `id`를 싣는다(`fastapi/sse.py` 223·226행을 읽었다). 블록 가르기가 블록이 빈 줄로 닫혔는지를 함께 넘기고, 최종 사용자 쪽만 닫히지 않은 블록을 늘 `id` 없는 원문으로 낸다(`unclosedFrame`). 운영자 쪽 `readFrames`는 그대로다. 시험 둘을 먼저 고쳐 빨강(2 failed)을 보고 구현했다. 이 수정이 `stream.ts`의 원문을 바꿔 새 변이 표의 넷과 관리 화면 표의 `스트림이 끝날 때 남은 프레임을 버린다`를 지금 코드로 맞췄다.
- `stream.ts` 머리 주석의 닫힌 주장 "두 읽기가 갈리는 것은 `data` 가 없는 블록이다"를, 운영자 쪽은 `data`만 보고 최종 사용자 쪽은 `id`·주석·닫힘도 본다는 일반 조항과 갈리는 블록 셋의 목록으로 바꿨다(명세 Nit).
- `errors.py`에서 `LimitEnvelope`를 `LimitKind` 뒤로 옮겼다. 계약을 다시 뽑아 `openapi.json`이 그대로인 것을 봤다. `errors.py`·`limits.py`의 "문구는 어느 상한인지만"을 "봉투는 어느 상한인지만(`limit` 과 문구)"으로, `http.md`의 "그것과"를 "그 범위와"로 고쳤다(표준 Nit). `http.md`를 원천으로 든 카나리아 명세 둘은 `--preflight`로 갈음했다(통과 2, claude 2.1.302).
- 시험 독스트링의 "(web-widget 스토리 "상한")"을 명세의 "상한" 절과 스토리 34로, 일지와 대기열 454의 훅 문구 인용을 원문의 큰따옴표로 고쳤다(명세 Nit).

남긴 것과 이유:

- 표준 Minor 2(`HTTPException(429)`이 `limit` 없는 429를 낸다). 지금 429를 내는 것은 표의 `LimitExceeded` 갈래뿐이고 `http.md`가 라우트의 `HTTPException(429)`를 막는다. 사건이 0회라 검사를 더하지 않는다(교정 루프).
- smell 셋(`error_envelope` 삼항식, 다섯 칸 튜플 `Refusal`, 두 읽기의 try/finally 틀). 판단 항목이고 작다.
- 명세 축의 범위 넘침 Nit 둘. `EventSourceWithJsonErrors`는 `LimitEnvelope`를 계약에 올리는 데 필요했고 계약은 그대로다. 옛 변이 표의 행은 이 커밋이 그 파일을 고쳐 `mutate.py --staged`가 요구한다.

PR 직전 리뷰에 밀 새 문장(원문):

- `routes.py`: "성공 응답과 에러 응답의 계약의 미디어 타입은 두 면의 계약 시험이, 실제 응답의 `content-type` 과 keepalive 주석은 운영자 채널의 시험이 잰다. 두 면이 같은 클래스를 쓰므로 한 면의 시험이 그 클래스를 지킨다."
- `items.py`: "모델이 어느 도구를 요청했는지를 싣는 항목은 이것뿐이다", "모델 호출의 이벤트가 실행의 어느 때에 나오는지는 core 가 정하고(ADR 0039), 투영은 받은 이벤트를 옮길 뿐이다."
- `stream.ts`: "운영자 쪽은 블록의 `data` 만 보고, 최종 사용자 쪽은 `id` 와 주석과 블록이 빈 줄로 닫혔는지도 본다", "`id` 가 없거나 십진 정수가 아닌 블록. 운영자 쪽은 술어를 지나면 이벤트이고, 최종 사용자 쪽은 원문이다", "닫히지 않은 블록은 스트림이 끝날 때 남은 것뿐이다", "서버는 `data` 다음에 `id` 를 실어(fastapi 0.141.1 의 `sse.py`)".

다시 돌린 것:

- 변이 표 둘을 전부 다시 돌렸다. 새 계약 표 9개, 관리 화면 api-client 표 25개 모두 기대대로였다.
- 전체 러너(`tools/run_checks.py`)는 web 검사 하나만 빨갰다. 새 시험의 한 줄이 Prettier 서식에 맞지 않았다. 고친 뒤 `pnpm -C web verify`가 초록이었다(vitest 423 passed). 나머지 검사는 pytest까지 그 실행에서 모두 통과했다.
- LLM 시험은 다시 돌리지 않았다. 앞 "검사"의 실행 뒤에 셀프 리뷰가 고친 파이썬은 주석·독스트링과 `errors.py`의 클래스 자리뿐이고, 계약을 다시 뽑아 `openapi.json`이 그대로인 것을 봤다.
- e2e: 전체가 1 failed·6 passed(2.5분), 결정 파일만 다시 돌린 것이 1 failed·2 passed(1.2분)였다. 둘 다 앞 "검사"의 그 시험이 39행에서 빨갰고, 그때 CPU는 77~98%였다(다른 세션들이 돌았다). 두 번 연속이라 diagnosing-bugs로 갈랐다. 가설은 셋이었다. (1) 부하에서 서버의 재개가 늦어 결말이 시험의 5초 뒤에 난다. (2) 셀프 리뷰가 바꾼 `blocksFrom`이 `readFrames`의 마지막 프레임을 늦추거나 놓친다. (3) 중계가 스트림을 끝에 몰아 보낸다. 첫 실행이 teardown에서 EPERM으로 지우지 못한 임시 폴더(`agent-os-e2e-HSpNAB`)에 그 실행의 트레이스가 남아 있었다. 실패한 실행(4d9be1d0)의 시각은 `approval_granted` 16.84초 → `run_resumed` 21.47초 → `tool_called` 22.45초 → `run_finished` 24.48초였다. 서버가 결말을 허가 7.6초 뒤에 냈으므로 화면이 무엇으로 읽든 5초 안에는 보일 수 없어 (2)는 기각된다. 재개 스트림 영역에 `approval_granted`가 결말보다 먼저 보였으므로(36·37행 통과) (3)도 기각된다. 남은 것은 (1)이다. 지연의 대부분(4.6초)은 허가 뒤 재개까지의 구간이고, 앞 "검사"의 진단과 같은 구간이다. 같은 실행에서 통과한 시험의 두 실행도 그 구간이 4.2~4.5초였다. 고칠 것이 없어 회귀 시험은 없고, 판정은 CI의 `e2e` 잡에 맡긴다. teardown의 EPERM은 부하에서 프로세스가 임시 폴더를 늦게 놓은 것으로 보고 따로 가르지 않았다.

## 인계 (커밋 뒤)

- 이 세션의 첫 메시지는 위 "인계 (셀프 리뷰 직전)"의 지시문을 `implement` 스킬로 감싼 것이고, 사람의 다른 프롬프트는 없었다. 이 세션의 제목은 `feature/01-contract-calling-item-and-limit-kind`이고 `feature/01-contract-calling-item-and-limit-kind (인계함)`으로 바꾼다.
- 셀프 리뷰를 반영한 뒤 이 세션이 한 것: 티켓을 done으로, `.scratch/plan.md`의 web-widget을 `in-progress`로 바꾸고 프론티어 문단에 한 문장을 더했다(앞선 사례는 design-reverse-sync 01의 커밋 19bbfa06). `sibling_overlap.py`가 main이 일지 48을 먼저 가져간 것을 알려 `--move`로 일지를 47에서 49로 옮겼다. 커밋 제목이 72자를 넘어 줄였다. 커밋 77417bcc의 pre-commit은 모두 통과했고, 인용 대조가 이 일지의 인용 다섯을 경고해 원문대로 고쳤다(커밋하지 않았다). origin/main(07c890c5)을 합쳤고, 대기열 끝의 충돌은 main의 449~452 뒤에 이 브랜치의 453·454를 두어 풀었다. main이 바꾼 파일은 model-rerun 도구와 하네스 프로브뿐이라 이 브랜치가 든 파일·규약과 겹치지 않았다. 병합 커밋 1e7348d0의 pre-commit도 모두 통과했다.
- 그 커밋 뒤 세션 컨텍스트가 약 25만 토큰으로 문턱을 넘어 인계 계기가 왔다. `next-session` "인계할 때" 1의 다섯에 들지 않는다(요청 범위가 병합까지, 이어받은 경계는 `셀프 리뷰 직전`, `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음).
- 지시문:

```
다음 작업: .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md. 최종 사용자 스트림의 `calling` 항목과 429의 `limit` 종류를 계약에 싣고 api-client에 위젯 클라이언트를 만든다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md
브랜치: feature/01-contract-calling-item-and-limit-kind
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-49-contract-calling-and-limit.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 커밋했고 origin/main을 합쳤다(일지 "인계 (커밋 뒤)"). 커밋하지 않은 변경은 이 일지뿐이다(인용 다섯의 고침과 인계 절). 남은 단계는 일지를 커밋하고, PR 직전 리뷰를 돌고(CodeRabbit CLI는 좌석이 없어 `/security-review`와 `bug-perf-review` 서브에이전트를 나란히. 일지 셀프 리뷰 절의 "PR 직전 리뷰에 밀 새 문장"을 브리프에 넣는다), 트리아지한 지적을 고치고, `/git-pr`로 연 뒤 봇 회차와 워크트리에서 병합하는 것이다. e2e 결정 시험이 로컬 부하에서 빨간 것은 서버 재개 지연으로 진단했고(일지 셀프 리뷰 절의 "다시 돌린 것") CI `e2e` 잡이 판정한다. 원격 브랜치 docs/web-widget-spec-2는 사람이 확인하기 전에는 지우지 않는다. docs/journal/2026-10-23-49-contract-calling-and-limit.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 워크트리 잠금은 이미 풀려 있었다(`is not locked`).
- open-session을 부른다 2026-10-23T13:46:03Z

## PR 직전 리뷰와 PR (셋째 세션)

- 위 지시문을 `implement` 스킬로 감싼 첫 메시지로 열렸고, 사람의 다른 프롬프트는 없었다. 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 같은 워크트리에 들어왔다. `sibling_overlap.py`는 번호 겹침이 없었다(다음 빈 번호는 일지 51, 대기열 456).
- 일지를 커밋했다(6fc685ff). pre-commit은 모두 통과했고, 러너의 pytest가 585.6초였다.
- `coderabbit auth status`는 이번에도 `Plan: Free`, `Seat: not assigned`였다. 그래서 대체 둘을 나란히 돌렸다. 기준은 merge-base 07c890c5다.
  - `/security-review`(보안): 후보 0건. 하위 작업이 물은 넷을 근거와 함께 닫았다. `calling` 항목은 도구 이름만 싣고(`ToolCall`의 `id`·`args`는 싣지 않는다) 도구 이름은 전부터 `progress`·`paused`가 실었다. 429 봉투는 종류와 문구만 싣는다. 위젯 클라이언트는 토큰을 들지 않고 URL에 싣지 않는다. 미디어 타입을 비운 응답 클래스는 실제 응답을 바꾸지 않는다(fastapi 0.141.1 `routing.py`가 `text/event-stream`을 직접 단다).
  - `bug-perf-review`(버그·성능): 유효 Minor 2, 보류 0, 오탐 5. 밀 주장은 둘을 빼고 근거와 맞았다. 어긋난 둘이 유효 2다.
    - Minor 1. `items.py` 주석의 "이것뿐이다"가 넓었다. `PausedItem`도 모델이 요청한 도구 하나의 이름을 든다. 주석을 "모델 호출 하나가 요청한 도구를 모두 싣는 항목은 이것뿐이다"로 좁히고 `PausedItem`이 싣는 것을 함께 적었다.
    - Minor 2. `stream.ts` 머리 주석과 `EndUserFrame` 독스트링이 `idOf`의 `Number.isSafeInteger` 갈래를 빠뜨렸다. 두 문장에 안전한 정수의 범위를 더했다. 그 갈래를 재는 시험이 없어 `id: 9007199254740993` 시험을 더했다. 구현 뒤에 쓴 시험이라 변이 표에 `안전한 정수의 범위를 넘는 id 를 반올림한 채 쓴다`를 더했고, `mutate.py`로 그 줄을 돌려 그 시험 하나만 빨개지는 것을 봤다(1 failed·40 passed). 표지는 실패 줄의 시험 이름이다. 표는 10개가 됐고, 셀프 리뷰가 하나를 더할 때 그대로 둔 프로브 README의 개수(8)도 맞췄다.
    - 오탐: 표의 첫 갈래로 가는 `HTTPException(429)`(`src`에 던지는 곳이 없다), 빈 `tool_calls`(None이 없고 빈 것은 거른다), 청크 경계, 읽기 중 에러와 멈춤의 자원(두 읽기 모두 `finally`), 응답 클래스의 `media_type`(문서에만 쓰인다).
  - 고친 파일을 겨누는 변이 표 넷(`web-widget`·`web-admin`·`end-user-channel`·`end-user-continuation`)을 `--check`로 보니 원문이 모두 한 번씩 있었다.

## 회고

셀프 리뷰와 PR 앞에서 돌았다. 세션 카드 훅의 거부 문구대로 후속 일을 "다음"에 적자 retro 계기가 걸렸다(아래 2). 그래서 리뷰와 PR 봇 회차에서 나는 사건은 이 절에 덧붙인다. 후보 열일곱, 승인 2·일지에만 2·기각 13, 넘김 0.

1. 승인(고침). 상한 변이 표의 `결정은 칸을 차지하지 않음`이 빨개지지 못하고 600초 제한에서 끊긴다(위 "TDD와 변이"). main에서도 그래서 이 티켓의 몫이 아니다. 사건: 변이 표가 그 변이를 재지 못한다. 층: 시험에 기한을 두는 고침이다. 되돌림: PR 하나. 대기열 453(1회차).
2. 승인(고침). 앱의 세션 카드(`start_session`, `own_initiative`)를 1의 후속 일로 내자 `tools/hook_session_card.py`가 막고 후속 일을 `지금 일지의 "다음"이나 대기열 행`에 적으라 했다. 그대로 "다음"에 적자 `tools/hook_journal_retro.py`가 단계를 닫은 것으로 보고 retro를 걸었다. 훅이 단계를 닫지 않은 편집에 울린 28·62와 달리 이번 편집은 실제로 "다음"을 썼으니, 고칠 자리는 앞 훅의 문구다. 대기열 454(1회차).
3. 일지에만. e2e 결정 시험이 부하에서 두 번 빨갰다(위 "검사"). 306이 받아들여 닫은 종류(부하에서만 빨간 시간 시험)의 새 사례다.
4. 기각. 스크래치 스크립트의 `Path.write_text`가 Windows에서 `src/agent_os/http/routes.py`의 줄 끝을 CRLF로 바꿨다. git이 스테이지할 때 알려 되돌렸다(2026-10-23-33 회고 4와 같은 판정).
5. 기각. 워크트리 가드가 `awk -v`, 변수가 든 `sed`, 반복문을 거부했다(이 회고 중에도 한 번). 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정에 있다.
6. 기각. 이 브랜치가 stream.ts를 다시 쓰고 `Limit`을 `LimitKind`로 바꿔 옛 변이 표 원문 열이 깨졌다. `mutate.py --staged`가 막았다.
7. 기각. 모든 변이 표를 `--check`로 훑자 문제가 난 표가 열넷 나왔다(`pause_index_mutations.toml`의 8개 등. `checker_mutations.toml`은 이 워크트리에 없는 `.design-sync/`·`ds-bundle/`을 읽지 못한 것이다). 원문이 깨진 것은 모두 부모 판에서 이미 깨진 것이고(이 브랜치가 고친 파일을 가리키는 변이는 `--staged`가 보고, 거기 걸린 것은 6의 둘뿐이었다), `--staged`는 그런 원문을 받아들인다(`tools/mutate.py` 독스트링, 대기열 73·92). 이 브랜치가 새로 깬 것은 6뿐이다.
8. 기각. 일지 번호 45가 형제와 겹쳤다. `sibling_overlap.py --move`가 47로 옮겼다.
9. 기각. 큰 heredoc, `cd web`, 판정 명령의 파이프, Grep의 생략된 줄을 훅이 그 자리에서 막거나 알렸다.
10. 기각. ruff가 한글 폭을 2로 세는 E501을 잡았다.
11. 기각. main 사본으로 상한 #3을 가르는 스크래치 스크립트에서 `tar`가 `C:`를 원격 호스트로 읽었고, 꺼낸 사본의 conftest가 `tools`를 import하지 못했다. 한 번 쓴 대조 스크립트의 설정이고 재시도 둘이라 고칠 환경이 서지 않는다.
12. 기각. 카나리아 명세의 결과 줄에 고친 항목을 처음에 틀리게 적었다(바뀌지 않은 `channel.md`의 봉투 항목). 커밋 전에 diff로 바로잡았다.
13. 기각. 빨강을 본 적 없는 시험 셋(위 "TDD와 변이")은 절차대로 새 변이 표로 쟀다.
14. 기각. 세션 카드가 막힌 것 자체는 훅이 그 자리에서 막았다(그 뒤의 일은 2).
15. 일지에만. 3과 같은 결정 시험이 셀프 리뷰 뒤 부하(CPU 77~98%)에서 두 번 더 빨갰다. 서버 트레이스로 결말이 기한 뒤에 났음을 봤다(셀프 리뷰 절의 "다시 돌린 것"). 3과 같은 종류다.
16. 기각. 셀프 리뷰가 더한 시험 한 줄이 Prettier 서식에 맞지 않았다. 전체 러너의 web 검사가 그 자리에서 잡았다.
17. 기각. 커밋 제목 초안이 72자를 넘었다. 커밋 전에 `tools/check_commit_msg.py`로 대 봐서 잡았다(커밋 훅도 막는다, 대기열 222).

`queue_open_rows.py`는 로컬과 `--ref origin/main` 모두 만료할 행이 없었다.

## 다음

- 후속(이 티켓 밖): 대기열 453(상한 변이 표 #3의 시간 초과).
