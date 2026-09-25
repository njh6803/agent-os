"""라우트를 선언하는 쪽이 쓰는 것 둘. 라우트별 에러 문서와 경로 변환기 `verbatim` 이다(ADR 0016).

관리와 채널의 라우트가 이것을 import 한다. 미들웨어와 핸들러는 `server` 가 앱 전체에 걸어 두 면을
함께 덮지만, 라우트가 `responses=` 에 봉투를 적는 것과 `{run_id:verbatim}` 은 라우트 쪽의 일이다.

**라우트는 `operation_id` 를 손으로 준다.** FastAPI 가 라우트 함수 이름으로 `operationId` 를 짓는데
기본값은 `read_health_health_get` 꼴이라 그대로 생성 클라이언트의 함수 이름이 된다.
"""

from __future__ import annotations

from collections.abc import Mapping

from starlette.convertors import Convertor, register_url_convertor

from agent_os.http.errors import (
    INTERNAL_MESSAGE,
    INVALID_REQUEST_MESSAGE,
    UNAUTHORIZED_MESSAGE,
    ErrorEnvelope,
)

# 계약에 적는 에러와 그 설명. 라우트가 자기 `responses` 에 적는다. 401 은 미들웨어가 내는 것이라
# 프레임워크가 스키마에 넣어 주지 않고, 422 는 적지 않으면 FastAPI 가 제 모양
# (`HTTPValidationError`)을 붙여 계약이 봉투가 아닌 것을 약속하게 된다. 500 은 라우터가 건다.
_DOCUMENTED_ERRORS: Mapping[int, str] = {
    401: UNAUTHORIZED_MESSAGE,
    404: "찾는 것이 없다",
    422: INVALID_REQUEST_MESSAGE,
    500: INTERNAL_MESSAGE,
}


def documented_errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    """라우트의 `responses` 에 적을 에러 응답들(질의). 모양은 언제나 봉투다."""
    return {
        status: {"model": ErrorEnvelope, "description": _DOCUMENTED_ERRORS[status]}
        for status in statuses
    }


# 봉투 컴포넌트의 참조. `documented_errors` 를 쓰는 라우트가 모델로 그 컴포넌트를 등록하고(관리
# 라우트가 늘 그렇다), 스트림 라우트는 이름으로 가리킨다. 둘이 같은 것을 가리킨다는 것은 에러 문서의
# 전수 테스트가 모든 경로에서 잰다.
_ENVELOPE_REF = f"#/components/schemas/{ErrorEnvelope.__name__}"


def documented_stream_errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    """스트림 라우트의 에러 응답들(질의). 모양은 봉투이고 미디어 타입은 JSON 이다.

    FastAPI 는 에러 문서의 모델을 라우트 응답 클래스의 미디어 타입 아래에 싣는다(fastapi 0.141.1
    의 `openapi/utils.py`). 스트림 라우트(`EventSourceResponse`)에서 그것은 `text/event-stream`
    이라, 모델로 적으면 봉투가 스트림으로 온다고 계약이 말한다. 에러는 스트림이 시작되기 전에 JSON
    봉투로 나가므로 미디어 타입을 손으로 적고 모델 대신 참조를 둔다.
    """
    return {
        status: {
            "description": _DOCUMENTED_ERRORS[status],
            "content": {"application/json": {"schema": {"$ref": _ENVELOPE_REF}}},
        }
        for status in statuses
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
