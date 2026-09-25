---
status: accepted
date: 2026-09-24
---

# HTTP 표면의 공용 배관은 `agent_os.http` 층에 둔다

HTTP 표면을 받치는 것이 전부 `admin/`에 있다. 에러 봉투(`ErrorEnvelope`, `ErrorCode`, `Violation`), 예외를 상태 코드로 옮기는 표(`failure_for`), 에러 핸들러와 요청 식별자 미들웨어, 라우트별 에러 문서(`_documented_errors`), 경로 변환기(`_Verbatim`), 인증 미들웨어다. 채널도 같은 것이 필요한데 원칙 IV가 채널이 관리를 import하는 것을 금한다. 미들웨어와 핸들러는 `server`가 앱 전체에 걸어 채널도 덮지만, 라우트가 `responses=`에 봉투 모델을 적는 것과 `{run_id:verbatim}`은 import가 있어야 한다. **새 층 `agent_os.http`를 두고 공용 배관을 거기로 옮긴다. 채널과 관리와 `server`가 이것을 import하고, 이것은 core와 sdk만 import한다. 원칙 IV의 의존 방향은 `main → server → {channel | admin | adapters} → http → core → sdk`가 되고 어댑터는 `http`를 import하지 않는다.** 화살표는 지금처럼 층의 순서라 위의 층이 아래의 어느 층이든 import할 수 있다. `server`가 인증 미들웨어와 핸들러를 걸며 `http`를 직접 부르는 것도 그 안에 든다. 층을 늘리는 이유는 공용이 된 것이 실제로 공용이기 때문이다. 채널과 관리는 같은 계약 파일에 같은 에러 모양으로 실리고, 그 모양이 두 곳에 있으면 언젠가 어긋난다.

## Considered Options

- **채널에 사본을 두고 대조 테스트로 맞춘다.** 층이 그대로다. 그러나 같은 스키마가 둘이라 openapi 컴포넌트 이름이 충돌하거나 생성 클라이언트가 에러 타입을 둘 받고, 그것을 맞추는 테스트가 또 필요하다. 거부했다.
- **`server`가 `include_router(responses=…)`로 라우터 단위 에러 문서를 채운다.** 층이 그대로다. 그러나 라우트별 정밀도를 잃고(재개만 내는 409가 `/runs`에도 적힌다), 변환기는 누군가 먼저 전역 등록해 두기를 기대는 암묵 결합이 된다. 거부했다.
- **core나 sdk에 둔다.** core는 HTTP를 모르고(원칙 IV), sdk는 플러그인이 import하는 표면이라 에러 봉투가 설 자리가 아니다. 거부했다.

## Consequences

- **헌법 원칙 IV의 문언이 바뀐다.** 의존 방향 열거가 느는 것이라 minor다. 원칙 IV의 문언, `CLAUDE.md`의 레이어 목록(`src/agent_os/http/` 줄)과 의존 방향 줄, import-linter 계약, 헌법 버전은 코드를 옮기는 `http-channel`의 계약 티켓에서 함께 바꾼다. 판정자와 문언과 코드가 한 PR에서 움직여야 어긋난 순간이 없고, 층이 실재하기 전에는 규칙을 바꿔도 판정할 대상이 없다. 이 ADR이 승인한 것은 개정의 내용(열거에 `http`가 는다)이고, 바뀐 문언은 그 티켓의 PR에서 사용자가 본다.
- **import-linter는 층 하나와 금지 하나로 판정한다.** `http`를 `{channel | admin | adapters}` 아래, core 위의 층으로 두고, 어댑터가 `http`를 import하지 못하게 따로 막는다. 어댑터는 HTTP 표면이 아니다.
- **옮기는 것과 남는 것.** 에러 봉투 셋, `failure_for`와 그 표, `install_error_handlers`, `AssignRequestId`, `error_envelope`·`remember_failure`·`request_id_of`, `_documented_errors`, `_Verbatim`, 인증 미들웨어가 간다. 인증 미들웨어는 접두사→토큰 표를 받는 일반형이 되고 표는 `server`가 넘긴다(ADR 0015). 관리 라우터와 관리의 응답 모델(`Health`, 목록과 상세의 행, 커서)은 `admin`에 남는다.
- **`.claude/rules/admin.md`의 HTTP 표면 공통 규칙이 새 층의 rules 파일로 간다.** 봉투와 어휘, 상태 코드 표, 에러 문서, `verbatim`, `operation_id`, 한 줄 독스트링, 테스트 이음매가 그것이다. `paths`는 새 층과 채널과 관리와 `server.py`를 덮는다. 관리에만 걸리는 것(목록과 상세의 모양, 커서)은 `admin.md`에 남는다.
- **채널과 관리는 여전히 서로를 import하지 않는다.** `main`과 `server`가 조립한다는 문장도 그대로다.
- **이름은 `agent_os.http`다.** 들어 있는 것 그대로의 이름이다. 표준 라이브러리 `http`와는 절대 import라 부딪치지 않고, `admin.http`와 `channel.http`는 앞의 접두어가 가른다.

## 이력

### 2026-09-25 표준 라이브러리와 부딪치지 않는 것은 모듈 실행에서만 참이다

계약 티켓(`http-channel` 01)을 구현하며 적는다. 위의 "절대 import라 부딪치지 않고"는 `-m`과 콘솔
스크립트에서만 참이다. `src/agent_os/` 안의 파일을 스크립트로 실행하면 그 디렉터리가 `sys.path`
첫머리에 서서 이 층이 표준 라이브러리 자리에 들어오고, `main.py`에 `__main__` 블록이 있어 그 길이
실재했다(명세 검토가 쟀고, 층을 만든 뒤 `No module named 'http.client'`로 다시 쟀다).

**`agent_os/http/__init__.py`가 자기 이름이 `agent_os.http`가 아니면 처방을 담은 `ImportError`로
막는다.** 이 층의 이름이 만든 문제라 이 층이 소유하고, `src/agent_os/` 바로 아래의 어느 파일을
스크립트로 돌려도 같은 자리에서 걸린다. 스크립트 실행은 되지 않고 이유와 처방(`agent-os`, `python -m
agent_os.main`)을 말하며 끝난다. `__main__` 블록을 빼고 `agent_os/__main__.py`를 두는 안은 `python -m
agent_os.main`을 조용히 아무것도 하지 않는 명령으로 만들어 거부했다. `main.py` 첫머리에서
`sys.path[0]`을 걷어내는 안은 import 앞에 코드를 두어 린트 억제가 들고 `main.py` 하나만 덮어
거부했다. 테스트가 두 길을 나란히 판정한다 — `-m`은 되고, 스크립트는 처방과 함께 막힌다.
