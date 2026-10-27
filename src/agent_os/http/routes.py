"""라우트를 선언하는 쪽이 쓰는 것 셋. 라우트별 에러 문서, 스트림 라우트의 응답 클래스, 경로 변환기
`verbatim` 이다(ADR 0016).

관리와 채널의 라우트가 이것을 import 한다. 미들웨어와 핸들러는 `server` 가 앱 전체에 걸어 모든 면을
함께 덮지만, 라우트가 `responses=` 에 봉투를 적는 것과 `{run_id:verbatim}` 은 라우트 쪽의 일이다.
스트림 라우트의 응답 클래스는 그 에러 문서가 JSON 아래에 실리게 하는 것이라 여기 함께 있다.

**라우트는 `operation_id` 를 손으로 준다.** FastAPI 가 라우트 함수 이름으로 `operationId` 를 짓는데
기본값은 `read_health_health_get` 꼴이라 그대로 생성 클라이언트의 함수 이름이 된다.
"""

from __future__ import annotations

from collections.abc import Mapping

from fastapi.sse import EventSourceResponse
from starlette.convertors import Convertor, register_url_convertor

from agent_os.http.errors import (
    INTERNAL_MESSAGE,
    INVALID_REQUEST_MESSAGE,
    NOT_FOUND_MESSAGE,
    RETRY_AFTER_HEADER,
    UNAUTHORIZED_MESSAGE,
    ErrorEnvelope,
    LimitEnvelope,
)

# 계약에 적는 에러와 그 설명. 라우트가 자기 `responses` 에 적는다. 401 은 미들웨어가 내는 것이라
# 프레임워크가 스키마에 넣어 주지 않고, 422 는 적지 않으면 FastAPI 가 제 모양
# (`HTTPValidationError`)을 붙여 계약이 봉투가 아닌 것을 약속하게 된다. 500 은 라우터가 건다. 409 는
# 요청이 가리킨 것이 있지만 그 상태나 주체가 요청을 허락하지 않는 것을 만나는 라우트만 적는다. 그
# 설명은 운영자 채널과 최종 사용자 면의 라우트가 나눠 쓴다 — 재개 불가와 꺼짐은 상태이고, 남의
# 실행은 주체다(ADR 0022·0023). 429 는 요청하는 쪽의 상한이고 최종 사용자 면의 라우트만 적는다(ADR
# 0023).
_DOCUMENTED_ERRORS: Mapping[int, str] = {
    401: UNAUTHORIZED_MESSAGE,
    404: NOT_FOUND_MESSAGE,
    409: "있지만 상태나 주체가 요청을 허락하지 않는다",
    422: INVALID_REQUEST_MESSAGE,
    429: "요청하는 쪽의 상한을 넘었다. Retry-After 의 초가 지난 뒤 다시 보낸다",
    500: INTERNAL_MESSAGE,
}

# 상태 코드가 요구하는 응답 헤더와 그 설명. 429 는 언제 다시 보낼 수 있는지를 `Retry-After`(초)로
# 싣는다(RFC 9110). 상태 코드에 딸린 것이라 그 상태를 적는 라우트마다 저절로 붙는다. 스키마는
# 정수 하나이고 하한은 설명에 적는다 — `minimum` 을 두면 FastAPI 가 계약을 pydantic 모델로 다시
# 읽으며 라우트 하나에서만 `1.0` 으로 바꿔 같은 헤더가 라우트마다 다르게 실렸다.
_DOCUMENTED_HEADERS: Mapping[int, Mapping[str, str]] = {
    429: {RETRY_AFTER_HEADER: "다시 보내도 되기까지의 초. 1 이상의 정수다"},
}


# 상태 코드마다 봉투의 모양. 429 는 상한의 종류를 더 든 봉투이고 그 밖은 네 필드의 봉투다(ADR 0023
# 의 2026-10-23 이력). 429 를 내는 것은 표의 상한 갈래(`LimitExceeded`)뿐이라 모양이 상태 코드에
# 딸린다 — `Retry-After` 처럼 그 상태를 적는 라우트마다 저절로 붙는다.
_ENVELOPE_OF: Mapping[int, type[ErrorEnvelope]] = {429: LimitEnvelope}


def documented_errors(
    *statuses: int, descriptions: Mapping[int, str] | None = None
) -> dict[int | str, dict[str, object]]:
    """라우트의 `responses` 에 적을 에러 응답들(질의). 모양은 언제나 봉투이고 미디어 타입은 JSON
    이다.

    스트림 라우트는 응답 클래스로 `EventSourceWithJsonErrors` 를 써야 이 문서가 JSON 아래에
    실린다(그 독스트링). 모델로 적으므로 봉투의 컴포넌트는 그것을 적는 라우트가 계약에 올린다.

    `descriptions` 는 그 라우트에서만 공유 설명과 다르게 말할 상태 코드의 설명이다. 같은 상태 코드가
    라우트마다 다른 것을 약속하는 자리를 라우트 선언에 두어, 공유 표가 라우트를 알지 않게 한다.
    """
    own = descriptions or {}
    return {
        status: {
            "model": _ENVELOPE_OF.get(status, ErrorEnvelope),
            "description": own.get(status, _DOCUMENTED_ERRORS[status]),
            **_headers_of(status),
        }
        for status in statuses
    }


class EventSourceWithJsonErrors(EventSourceResponse):
    """스트림 라우트의 응답 클래스. 에러 문서가 JSON 아래에 실리도록 미디어 타입을 비운다.

    FastAPI 는 에러 문서의 모델을 라우트 응답 클래스의 미디어 타입 아래에 싣고, 그 클래스에 미디어
    타입이 없으면 `application/json` 아래에 싣는다(fastapi 0.141.1 의 `openapi/utils.py`). 관리의
    `response_class=Response` 라우트가 그 기본값으로 에러 문서를 JSON 에 싣는다.
    `EventSourceResponse` 의 미디어 타입은 `text/event-stream` 이라 그대로 두면 계약이 "봉투가
    스트림으로 온다"고 말한다. 에러는 스트림이 시작되기 전에 JSON 봉투로 나간다.

    성공 응답은 이 값을 읽지 않는다. FastAPI 는 SSE 제너레이터 라우트의 200 을 계약에
    `text/event-stream` 으로 적고, 응답도 그 미디어 타입으로 직접 만든다(같은 판의 `routing.py`).
    keepalive 도 그대로다 — FastAPI 가 SSE 라우트를 응답 클래스가 `EventSourceResponse` 의 하위
    타입인지로 가른다. FastAPI 가 셋 가운데 하나를 바꾸면 이 클래스를 쓰는 라우트의 시험이 빨개진다.
    성공 응답과 에러 응답의 계약의 미디어 타입은 두 면의 계약 시험이, 실제 응답의 `content-type` 과
    keepalive 주석은 운영자 채널의 시험이 잰다. 두 면이 같은 클래스를 쓰므로 한 면의 시험이 그
    클래스를 지킨다.

    모델 대신 컴포넌트의 이름 참조를 손으로 적지 않는 이유는, 그러면 컴포넌트를 계약에 올리는 일이
    모델로 적는 다른 라우트(관리)에 기대기 때문이다. 스트림 라우트만 쓰는 모델(429 의
    `LimitEnvelope`)은 그때 계약에 오를 길이 없다.
    """

    media_type = None


def _headers_of(status: int) -> dict[str, object]:
    """상태 코드가 요구하는 응답 헤더의 문서(질의). 없으면 응답 문서에 키가 없다."""
    headers = _DOCUMENTED_HEADERS.get(status)
    if headers is None:
        return {}
    return {
        "headers": {
            name: {"description": description, "schema": {"type": "integer"}}
            for name, description in headers.items()
        }
    }


class _Verbatim(Convertor[str]):
    """경로 파라미터 자리에 온 것을 슬래시와 개행까지 통째로 잡는다. 판정은 패턴이 한다.

    파일 경로로 조립되는 식별자는 이것으로 받는다. 기본 변환기(`[^/]+`)는 서버가 `%2F` 를 디코딩한
    `/` 앞에서 끊고, `path` 변환기(`.*`)는 개행을 넘지 못하는데 라우팅 정규식이 파이썬 `re` 라
    `$` 가 마지막 개행 앞에서도 맞는다. 어느 쪽이든 형식 위반이 422 가 아니라 라우팅 404 가 되거나
    개행이 떼어진 채 유효한 이름으로 읽힌다. 라우트가 맞은 뒤 패턴이 유일한 판정자여야 한다.
    """

    regex = r"[\s\S]*"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


# Starlette 의 공개 확장점이고 프로세스 전역 표에 키 하나를 둔다. 상태가 없고 같은 키로 다시 불러도
# 같은 것이 들어가므로, import 시점의 부수효과가 테스트와 앱 조립에 새는 것이 없다. 등록이 이 모듈에
# 있는 이유는 `verbatim` 을 쓰는 라우트 모듈이 `documented_errors` 를 쓰려고 이 모듈을 import 하기
# 때문이다. 그래서 등록이 그 라우트보다 늘 먼저이고, 누군가 먼저 등록해 두기를 기대지 않는다.
register_url_convertor("verbatim", _Verbatim())
