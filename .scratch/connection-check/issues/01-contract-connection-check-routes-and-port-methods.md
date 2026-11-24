# 01: 계약 — 접속 확인의 관리 경로 둘과 응답, 포트의 확인 메서드

**What to build:** 관리 토큰을 가진 운영자가 `GET /plugins/{kind}/{name}/connection-check`(스스로 하는 확인)와 `POST /plugins/{kind}/{name}/connection-check`(눌러서 하는 확인)를 부를 수 있다. 접속 확인은 켜 둔 플러그인이 가리키는 바깥 서버에 `serve`가 실제로 붙어 보는 것이다(`CONTEXT.md`). 계약 파일 `openapi.json`과 생성 TS 타입에 두 오퍼레이션(계약에 실리는 메서드와 경로 하나), `kind`의 닫힌 값(`mcp`, `model`), 칸 `status`로 가르는 응답 넷(`reached`, `unreached`, `disabled`, `not_applicable`)이 실린다. 없는 플러그인은 404, 에이전트와 스킬은 422, 깨진 매니페스트와 깨진 운영자 파일은 500, 꺼 둔 플러그인은 `disabled`, 그 오퍼레이션이 확인하지 않는 플러그인은 `not_applicable`로 지금 바로 답한다. 관리 화면 개발자에게는 생성 TS 타입이 `status`로 좁혀져, 좁히지 않고 `reason`을 읽는 코드가 컴파일에서 걸린다. 아직 실제로 붙어 보지는 않는다. 켜 둔 원격 MCP 서버나 켜 둔 모델을 `GET`으로, 켜 둔 stdio MCP 서버를 `POST`로 확인하면 실제 어댑터가 '아직 구현되지 않았다'는 예외를 올려 500이 온다. 화면은 아직 이 경로를 부르지 않는다.

이 기능의 계약 티켓이고 나머지 전부를 막는다. 계약은 `openapi.json`과 생성 TS 타입이다. sdk는 바뀌지 않는다. 끌고 오는 것은 core의 결과 타입 셋, 포트 둘(core가 바깥과 닿는 자리를 선언한 인터페이스)에 느는 확인 메서드 셋, 관리 층이 받는 묶음 둘, 조립 층의 배선, 기존 가짜 포트 전부, 규칙 파일과 독스트링이다. 리뷰의 질문은 "동작하나"가 아니라 이 이름과 모양으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 골랐다).** 포트에 메서드가 늘면 실제 어댑터도 같은 커밋에 그 메서드를 가져야 타입 검사를 지난다. 그래서 이 티켓은 실제 어댑터 둘의 확인 메서드를 '아직 구현되지 않았다'는 예외를 올리는 자리로 둔다. 그 예외는 여는 단계 밖의 예외라 경로가 500으로 답하고 서버 기록에 한 줄이 남는다. 02가 MCP 서버의 몫을, 03이 모델의 몫을 실제 확인으로 바꾼다. 화면 티켓(04)은 둘 뒤라 화면에는 이 틈이 보이지 않는다. 이 티켓이 쓰는 문장(독스트링, 주석, 규칙 파일)은 틈 동안에도 참이어야 한다. 확인 메서드가 있다는 것과 실제 어댑터가 아직 붙어 보지 않는다는 것을 함께 말하고, 붙어 보는 동작은 02와 03이 쓴다. 선례는 `.scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md`의 같은 문단이다.

근거는 명세 `.scratch/connection-check/spec.md`의 "경로와 응답", "판정의 차례", "포트와 층", "결과가 남는 자리"의 첫 항목, Testing Decisions의 첫째와 "타입", Further Notes의 "티켓의 차례"다. 포트 모양의 측정은 `.scratch/connection-check/probes/check_port_split.py`와 `port_split_shape.py`이고 다시 돌리지 않는다. 결정은 ADR 0067의 결정 "확인은 `serve`가 한다"·"붙지 못한 확인은 오류 응답이 아니다"·"포트와 층"과 Consequences "계약 변경이 첫 티켓이다"·"ADR 0010의 성질이 좁아진다"·"구현 티켓이 함께 고칠 자리"다. 이 티켓의 "명세 검토"는 일지 `docs/journal/2026-11-22-0159-connection-check-tickets.md`의 "명세 검토" 절을 가리킨다.

**Blocked by:** None (can start immediately)

**Status:** done

### 계약

- [x] 두 오퍼레이션이 명세 "경로와 응답"의 표대로 선다. 메서드와 경로, `operationId`(계약이 오퍼레이션마다 붙이는 이름. `check_connection`, `check_connection_by_launching`)가 그 표와 같다. `POST`는 본문이 없다
- [x] `kind`는 `mcp`와 `model` 둘만 받는 새 열거로 계약에 실린다. `agent`와 `skill`은 422이고 `violations`의 `field`가 `path.kind`다. `name`은 다른 플러그인 경로와 같은 규칙으로 받는다(`.claude/rules/http.md`의 "파일 경로로 조립되는 경로 파라미터")
- [x] 두 오퍼레이션의 200 응답은 같은 모양이고, 판별 유니온(칸 `status`의 값을 보고 네 모양 가운데 어느 것인지 가르는 타입)으로 계약에 실린다. `reason`은 `unreached`에만 있고, "비지 않은 문자열"이 계약에 `minLength: 1`로 실린다(명세 검토의 nit). 열거와 유니온과 멤버 넷의 컴포넌트 이름은 이 티켓이 정하고 리뷰가 본다
- [x] 두 오퍼레이션의 200 응답에 `Cache-Control: no-store`가 실린다. 오류 응답(미들웨어가 내는 401 포함)에도 싣는지는 이 티켓이 정해 시험에 고정한다(명세 검토의 nit)
- [x] 오류 응답은 다른 관리 경로와 같은 것만 낸다. 409와 429는 내지 않고 에러 코드의 어휘 여섯은 그대로다. 응답 모델의 독스트링은 한 줄이고, 라우트는 `operation_id`와 자기가 내는 에러의 문서를 손으로 준다(`.claude/rules/http.md`의 "계약에 박히는 것 둘을 손으로 준다")
- [x] `openapi.json`과 생성한 TS 타입(`web/packages/api-client`)이 같은 커밋에 실린다. `web/packages/api-client/src/clients.test-d.ts`가 관리 경로 목록을 타입으로 고정하므로 함께 고친다(명세 검토의 nit)
- [x] 생성 TS 타입이 `status`로 좁혀진다는 것을 타입 시험으로 고정한다. `status`로 좁히지 않고 `reason`을 읽는 줄이 컴파일에서 걸리는 것을 타입 시험 파일(`*.test-d.ts`)에 `@ts-expect-error`와 그 설명으로 적는다(원칙 III가 그 파일에서만 허용한다)

### 판정과 관리 경로

- [x] 두 오퍼레이션 모두 명세 "판정의 차례"의 1~6을 지난다. 4(`disabled`)와 5(`not_applicable`)는 화면이 보낸 값이 아니라 `serve`가 읽은 켜짐과 매니페스트로 판정하고, 거기서 끝난 요청은 확인 함수를 한 번도 부르지 않는다. 그래서 `GET`은 어떤 입력으로도 프로세스를 띄우지 않는다
- [x] 새 `GET`은 단건 조회(`GET /plugins/{kind}/{name}`)보다 먼저 선언한다. 이름에 슬래시가 든 단건 조회의 422가 아니라 접속 확인의 응답이 오는지를 시험이 고정한다(명세 "경로와 응답"의 "선언의 차례")
- [x] 관리 라우터는 포트를 받지 않고, 조립 층(`server`)이 포트에서 꺼낸 확인 함수를 담은 묶음 둘만 받는다. 스스로 하는 확인의 묶음에는 플러그인 소스와 원격 확인과 모델 확인이, 눌러서 하는 확인의 묶음에는 플러그인 소스와 stdio 확인이 든다. 묶음은 관리 층이 정의하고 core와 adapters는 모른다(명세 "포트와 층"의 "묶음이 사는 층"). `GET`은 앞 묶음만, `POST`는 뒤 묶음만 쓴다
- [x] 묶음은 `create_app()`이 이미 받는 도구 포트와 모델 포트에서 꺼내 채운다
- [x] 새 라우트는 비동기 확인을 기다리므로 `async def`다. 관리 모듈의 독스트링이 "조회 라우트는 동기 `def`"라 적으므로 이 예외를 적고, 그 라우트 안의 플러그인 파일 읽기를 어떻게 다루는지(이벤트 루프에서 그대로 읽을지, 스레드로 넘길지)를 정해 함께 적는다(명세 검토의 nit)
- [x] 두 오퍼레이션은 미들웨어의 기본값(관리 토큰) 뒤에 서고 라우트에 따로 거는 것이 없다(ADR 0011, `.claude/rules/http.md`)

### 포트와 결과 타입

- [x] 결과 타입 `Reached`, `Unreached`, `CheckOutcome`을 core의 포트 선언 옆에 둔다. `Unreached.reason`은 `str`이다. 응답의 `disabled`와 `not_applicable`은 관리 층의 응답 모델에만 있고 포트의 값이 아니다(명세 "포트와 층")
- [x] 도구 포트에 `check_remote`와 `check_stdio`가, 모델 포트에 `check`가 명세 "포트와 층"의 시그니처대로 는다. 포트는 다섯 그대로다. 메서드의 약속(붙지 못한 것은 예외가 아니라 `Unreached`, 기한에 닿으면 연 것을 닫고 `Unreached`, 취소는 삼키지 않음, 구성 오류는 실행과 같은 예외)을 `src/agent_os/core/ports.py`의 두 포트 독스트링에 적는다. 모델 포트의 "메서드는 하나이고 동기다"는 모델을 만드는 메서드의 불변식으로 좁혀 적는다(ADR 0067 Consequences "구현 티켓이 함께 고칠 자리")
- [x] 실제 어댑터 둘의 확인 메서드는 '아직 구현되지 않았다'는 예외를 올린다. 그 어댑터의 독스트링과 `.claude/rules/adapters.md`의 해당 항목은 메서드가 있다는 것과 아직 붙어 보지 않는다는 것을 함께 적는다(위 "병합 뒤에 틈이 있다")
- [x] 기존 가짜 포트 전부가 새 메서드를 시그니처로 만족한다. 가짜는 포트를 상속하지 않고 픽스처가 포트 타입으로 적는다(`.claude/rules/tests.md`). 빠뜨리면 pyright가 잡는다(명세 Testing Decisions의 "타입")
- [x] core의 런타임은 확인 메서드를 부르지 않는다. 부르는 것은 관리뿐이다

### 시험(명세 Testing Decisions의 첫째)

- [x] 가짜 포트를 끼운 `create_app()`으로 본다(선례 `tests/test_server.py`). 상태 넷이 응답에 실리는 모양, `unreached`의 `reason`이 가짜가 준 글 그대로인 것, 판정의 차례(없는 플러그인 404, `agent`와 `skill`은 422이고 필드가 `path.kind`, 깨진 매니페스트 500, 깨진 운영자 파일 500, 운영자 파일이 깨졌어도 없는 플러그인은 404), 확인 함수가 구성 오류를 예외로 올리면 500인 것, 새 `GET`이 단건 조회에 가로채이지 않는 것, 꺼 둔 플러그인과 대상이 아닌 플러그인에서 확인 함수의 호출 횟수가 0인 것, stdio 서버를 `GET`으로 확인하면 `not_applicable`이고 stdio 확인이 불리지 않는 것, 원격 서버와 모델을 `POST`로 확인하면 `not_applicable`인 것, 두 응답의 `Cache-Control`, 토큰 없는 요청의 401
- [x] `unreached`는 성공 응답이라 서버 표준 에러에 한 줄도 남지 않는다. 표준 에러를 받는 앱으로 0줄을 잰다(명세 "결과가 남는 자리", 이야기 27, 명세 검토 S9)
- [x] 계약 파일의 최신성과 세 면의 전수 검사는 기존 시험이 새 오퍼레이션 둘을 함께 보는지 확인한다

### 규칙과 독스트링

- [x] 규칙 파일을 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [x] `.claude/rules/admin.md`의 첫 항목을 "관리 라우터는 도구 연결을 여는 길(`ToolSource.connect`)을 받지 않고 접속 확인만 받는다"로 좁힌다. 조회 하나가 MCP 서버의 프로세스를 띄우는 길이 닫혀 있다는 성질은 그대로다(ADR 0067 Consequences "ADR 0010의 성질이 좁아진다")
- [x] `.claude/rules/core.md`의 포트 표에서 도구 포트와 모델 포트의 행에 확인 메서드를 적는다. 모델 포트 행의 "동기 메서드 하나"는 모델을 만드는 메서드의 것으로 좁힌다(위 `ports.py`의 독스트링과 같은 까닭)
- [x] `src/agent_os/server.py`의 `create_app()` 독스트링("관리 라우터는 … 도구 포트를 받지 않으므로")과 `src/agent_os/admin/http.py`의 "이 라우터는 도구 포트를 받지 않는다" 주석을 새 성질로 고친다
- [x] 결정이 바뀐 문장 둘(관리 라우터가 도구 포트를 받지 않는다, 모델 포트의 메서드가 하나이고 동기다)을 저장소 전체에서 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4)

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [x] api-client와 서버 라우트를 건드리므로 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`)를 로컬에서 친다
- [x] 실제 어댑터 파일을 고치므로 LLM 시험의 병합 조건 범위에 든다(`docs/constitution/operations.md` LLM 테스트의 "범위"). `-m llm`을 치고, 로컬 모델 시험은 `--yes` 없이 쳐 예상 비용을 사용자에게 보이고 확인받은 뒤 돌린다
