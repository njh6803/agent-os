"""모델 서버의 접속 확인. 모델 소스(`adapters/models.py`)의 `check` 가 제공사로 갈라 여기를 부른다.

운영자가 켜 둔 모델이 가리키는 서버에 붙는지를 요청 한 건으로 본다. 결정은 ADR 0067 의 결정 "모델을
확인하는 법"·"비밀"·"기한"과 이력 2026-11-21 이고, 측정은 `.scratch/connection-check/probes/` 의
`model_requests_loopback.py` 와 `model_requests_live.py` 다. 두 요청 모두 답변을 만들지 않아 토큰을
쓰지 않는다.

**요청.** 제공사마다 다르다.

- `anthropic`: 그 모델 하나를 묻는 `GET /v1/models/<model_id>` 한 건. 200 이면 돌아온 id 가 물은 id
  와 달라도 붙은 것이다. 날짜를 뗀 이름을 물으면 제공사가 날짜 붙은 id 를 돌려주기 때문이다.
  목록에 그 글자가 있는지로 가르면 날짜를 뗀 이름을 적은 모델 파일이 없는 모델로 보인다.
- `openai-compatible`: 모델 파일의 `base_url` 아래 `GET <base_url>/models` 한 건. 200 이고 첫 쪽의
  목록에 `model_id` 와 글자가 같은 `id` 가 있으면 붙은 것이다. 다음 쪽은 읽지 않는다. 이 결정은
  코드가 아니라 SDK 가 지킨다. `models.list()` 가 돌려주는 쪽(`AsyncPage`)은 다음 쪽이 없어(설치본의
  `openai/pagination.py`, 시험은 서버가 받은 요청이 한 건임을 본다) 목록의 첫 쪽만 돈다. 빌린 서버가
  id 하나를 묻는 요청을 받는지는 본 적이 없어, 준비 확인이 이미 쓰는 목록 요청을 쓴다.

요청은 한 번만 보낸다(`max_retries=0`). 두 라이브러리의 기본 설정은 500 에 세 건을 보냈다
(`anthropic` 은 프로브 `anthropic_default_retries`, `openai` 는 PR 직전 리뷰가 스크래치 가짜 서버로
돌려 본 것이라 커밋한 프로브가 없다). 재시도를 두면 꺼진 서버의 확인이 기한을 채우고 바깥 서버가
받는 요청이 는다.

**실행과 같은 주소와 같은 키.** `anthropic` 은 실행과 같은 인자로 모델 객체(`chat_anthropic`)를
만들고, 그 객체의 주소·키·프록시·덧붙임 헤더 칸으로 확인하는 클라이언트를
짓는다(`anthropic_check_client`). 환경 변수를 따로 읽어 같은 규칙을 다시 짓지 않는다. 그러지 않으면
`ANTHROPIC_API_URL` 로 주소를 바꾼 배포에서 확인과 실행이 다른 서버에 묻는다. `openai-compatible` 은
모델 파일의 `base_url` 로 묻고, 키는 실행이 호출마다 읽는 규칙(`KeySource`)을 그대로 쓴다. 환경의
`OPENAI_API_KEY` 를 싣지 않고 `OPENAI_PROXY` 를 따르지 않으며 환경의 `OPENAI_BASE_URL` 도 따르지
않는다. 실행이 그렇기 때문이다.

**붙지 못한 까닭은 예외의 글이 아니라 `serve` 가 지은 글이다.** 두 라이브러리 모두 서버가 오류
본문에 적은 글과 되울린 키를 예외의 글에 그대로 싣는다. 그래서 예외의 글을 옮기지 않는다. 글은
`모델 <이름>(<주소>)에 붙지 못했다: <뒷부분>` 이고 뒷부분은 닫힌 아홉 갈래 가운데 위에서부터 먼저
맞는 하나다. 바뀌는 자리는 모델 이름, 주소, 응답 상태 번호, 기한의 초, 환경 변수 이름, 예외 종류
이름뿐이다. 갈래는 예외의 종류가 아니라 서버가 준 응답 상태 번호로 가른다. 시간 초과를 닿지 못함보다
먼저 본다. 두 라이브러리 모두 시간 초과의 예외가 연결 오류 예외의 하위 종류이기 때문이다.

1. 키 없음: 요청을 보내지 않는다.
2. 키 모양: `openai-compatible` 만. 요청을 보내지 않는다.
3. 시간 초과
4. 닿지 못함
5. 키 거절: 401, 403
6. 모델 없음(`anthropic`): 하나를 묻는 요청이 404
7. 모델 없음(`openai-compatible`): 목록은 받았는데 `model_id` 와 같은 `id` 가 없다
8. 그 밖의 상태: 429, 5xx, `openai-compatible` 의 404 같은 것
9. 그 밖: 위 어디에도 들지 않는 예외. 예외 종류의 이름만 싣는다.

**예외를 잇지 않고 기록하지 않는다.** 라이브러리 호출에서 난 `Exception` 은 종류를 가리지 않고
갈래의 `Unreached` 로 바꾸고 올리지 않는다. 올리면 서버 기록에 그 예외의 글이 남는다. 서드파티
타입은 이 모듈 밖으로 나가지 않는다. `CancelledError` 는 받지 않아 바깥의 취소가 그대로 듣는다. 접속
확인의 길에서만 HTTP 라이브러리의 로거를 끄는 장치는 두지 않는다. 루트 로거를 INFO 로 낮추면
요청마다 `HTTP Request:` 한 줄이 남는 것은 실행과 같고, 그 줄은 키를 싣지 않는다. 알려진 한계:
그 줄은 요청 주소를 그대로 적으므로 `ANTHROPIC_API_URL` 에 사용자 정보(`user:password@`)를 적었으면
그것이 줄에 남는다(PR 직전 리뷰가 확인하는 길에서 재현했다). 사용자 정보를 떼는
것은 `Unreached.reason` 에 싣는 주소뿐이다.

**기한.** 어댑터를 만들 때 주는 값이고 기본이 10초다. 라이브러리의 시간 제한은 단계마다라서(연결,
읽기) 총 시간을 막지 못하므로 `anyio.move_on_after` 로 총 시간을 따로 막고 라이브러리에도 같은 값을
준다. 기한에 닿으면 요청을 끊고 연결을 닫은 뒤 시간 초과로 돌려준다.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import anthropic
import anyio
import openai
from langchain_anthropic import ChatAnthropic

from agent_os.adapters.anthropic import chat_anthropic
from agent_os.adapters.openai_compatible import KeyProblem, KeySource, own_client
from agent_os.core.ports import CheckOutcome, Reached, Unreached
from agent_os.sdk import PluginManifest

CHECK_DEADLINE_SECONDS = 10.0
ANTHROPIC_KEY_VARIABLE = "ANTHROPIC_API_KEY"
ANTHROPIC_DEFAULT_URL = "https://api.anthropic.com"
MODEL_MISSING_404 = "그 이름의 모델이 없다고 답했다(HTTP 404)"

_TIMEOUTS = (anthropic.APITimeoutError, openai.APITimeoutError)
_CONNECTIONS = (anthropic.APIConnectionError, openai.APIConnectionError)
_STATUSES = (anthropic.APIStatusError, openai.APIStatusError)


def display_address(raw: str) -> str:
    """글에 실을 주소. 사용자 정보(`user:password@`)와 쿼리와 조각을 떼고 끝의 `/` 를 뗀다.

    찍히지 않는 글자는 이스케이프한다. 환경 변수에서 온 주소에는 검사가 걸려 있지 않아서다.
    """
    escaped = "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in raw
    )
    try:
        parts = urlsplit(escaped)
    except ValueError:
        return "주소를 읽지 못함"
    host = parts.netloc.rpartition("@")[2]
    if not parts.scheme or not host:
        return "주소를 읽지 못함"
    return f"{parts.scheme}://{host}{parts.path.rstrip('/')}"


def anthropic_check_client(
    model: ChatAnthropic, deadline_seconds: float
) -> anthropic.AsyncAnthropic:
    """모델 객체의 주소·키·프록시·덧붙임 헤더로 확인하는 클라이언트를 짓는다.

    실행이 쓰는 모델 객체의 공개 칸을 그대로 받아 확인이 실행과 같은 서버에 같은 키로 닿게 한다.
    재시도는 끄고 시간 제한은 기한과 같게 준다. 닫는 것은 부른 쪽의 몫이다.
    """
    proxy = model.anthropic_proxy
    http_client = (
        anthropic.DefaultAsyncHttpxClient(proxy=proxy)
        if proxy
        else anthropic.DefaultAsyncHttpxClient()
    )
    headers = dict(model.default_headers) if model.default_headers else None
    return anthropic.AsyncAnthropic(
        api_key=model.anthropic_api_key.get_secret_value(),
        base_url=model.anthropic_api_url,
        default_headers=headers,
        http_client=http_client,
        max_retries=0,
        timeout=deadline_seconds,
    )


async def check_anthropic(
    manifest: PluginManifest, model_id: str, deadline_seconds: float
) -> CheckOutcome:
    """그 모델 하나를 묻는 요청 한 건으로 확인한다."""
    model = chat_anthropic(model_id, manifest.max_tokens, manifest.temperature)
    address = display_address(model.anthropic_api_url or ANTHROPIC_DEFAULT_URL)
    if not model.anthropic_api_key.get_secret_value():
        return _unreached(manifest.name, address, f"키가 없다(환경 변수 {ANTHROPIC_KEY_VARIABLE})")
    try:
        client = anthropic_check_client(model, deadline_seconds)
    except Exception as error:
        tail = reason_tail(error, deadline_seconds, not_found_tail=MODEL_MISSING_404)
    else:
        return await _ask_anthropic(client, manifest.name, model_id, address, deadline_seconds)
    # 클라이언트를 짓다 난 예외(스킴이 없는 프록시 값 등)도 `except` 밖에서 버린다. 그 예외의 글이
    # 프록시의 사용자 정보를 싣는다.
    return _unreached(manifest.name, address, tail)


async def _ask_anthropic(
    client: anthropic.AsyncAnthropic,
    name: str,
    model_id: str,
    address: str,
    deadline_seconds: float,
) -> CheckOutcome:
    """지은 클라이언트로 그 모델 하나를 묻고, 끝나면 클라이언트를 닫는다."""

    async def ask() -> CheckOutcome:
        await client.models.retrieve(model_id)
        return Reached()

    try:
        return await _bounded(
            ask, name, address, deadline_seconds, not_found_tail=MODEL_MISSING_404
        )
    finally:
        with anyio.CancelScope(shield=True):
            await client.close()


async def check_openai_compatible(
    manifest: PluginManifest, model_id: str, base_url: str, deadline_seconds: float
) -> CheckOutcome:
    """목록을 묻는 요청 한 건으로 확인한다. 첫 쪽에 `model_id` 와 같은 `id` 가 있어야 붙은
    것이다."""
    address = display_address(base_url)
    keys = KeySource(manifest.api_key_env, os.environ)
    key = keys.read()
    if key is KeyProblem.MISSING:
        return _unreached(manifest.name, address, f"키가 없다(환경 변수 {keys.variable})")
    if key is KeyProblem.UNSENDABLE:
        return _unreached(
            manifest.name,
            address,
            f"키에 인증 헤더로 보낼 수 없는 글자가 있다(환경 변수 {keys.variable})",
        )
    try:
        client = openai.AsyncOpenAI(
            api_key=key,
            base_url=base_url,
            http_client=own_client(),
            max_retries=0,
            timeout=deadline_seconds,
        )
    except Exception as error:
        tail = reason_tail(error, deadline_seconds, not_found_tail=None)
    else:
        return await _ask_openai_compatible(
            client, manifest.name, model_id, address, deadline_seconds
        )
    # 클라이언트를 짓다 난 예외(숫자가 아닌 포트, 없는 인증서 파일 등)도 `except` 밖에서 버린다.
    return _unreached(manifest.name, address, tail)


async def _ask_openai_compatible(
    client: openai.AsyncOpenAI,
    name: str,
    model_id: str,
    address: str,
    deadline_seconds: float,
) -> CheckOutcome:
    """지은 클라이언트로 목록을 묻고, 끝나면 클라이언트를 닫는다."""

    async def ask() -> CheckOutcome:
        page = await client.models.list()
        if any(listed.id == model_id for listed in page.data):
            return Reached()
        return _unreached(name, address, "그 이름의 모델이 목록에 없다")

    try:
        return await _bounded(ask, name, address, deadline_seconds, not_found_tail=None)
    finally:
        with anyio.CancelScope(shield=True):
            await client.close()


async def _bounded(
    ask: Callable[[], Awaitable[CheckOutcome]],
    name: str,
    address: str,
    deadline_seconds: float,
    *,
    not_found_tail: str | None,
) -> CheckOutcome:
    """`ask` 를 총 시간 기한 안에서 한 번 부르고, 예외는 갈래의 `Unreached` 로 바꾼다."""
    outcome: CheckOutcome | None = None
    with anyio.move_on_after(deadline_seconds):
        outcome = await _attempt(
            ask, name, address, deadline_seconds, not_found_tail=not_found_tail
        )
    if outcome is None:
        return _unreached(name, address, _timed_out(deadline_seconds))
    return outcome


async def _attempt(
    ask: Callable[[], Awaitable[CheckOutcome]],
    name: str,
    address: str,
    deadline_seconds: float,
    *,
    not_found_tail: str | None,
) -> CheckOutcome:
    """`ask` 를 부르고 그 예외를 갈래의 `Unreached` 로 바꾼다. 취소는 받지 않는다."""
    try:
        return await ask()
    except Exception as error:
        tail = reason_tail(error, deadline_seconds, not_found_tail=not_found_tail)
    # 예외를 `except` 밖에서 버린다. 원인으로 잇지도 기록하지도 않는다.
    return _unreached(name, address, tail)


def reason_tail(error: Exception, deadline_seconds: float, *, not_found_tail: str | None) -> str:
    """예외를 갈래의 뒷부분 글로 바꾼다. 404 를 모델 없음으로 읽는 제공사만 그 글을 `not_found_tail`
    로 준다(없으면 404 도 그 밖의 상태다)."""
    if isinstance(error, _TIMEOUTS):
        return _timed_out(deadline_seconds)
    if isinstance(error, _CONNECTIONS):
        return "서버에 닿지 못했다"
    if isinstance(error, _STATUSES):
        status = error.status_code
        if status in (401, 403):
            return f"키를 받아들이지 않았다(HTTP {status})"
        if status == 404 and not_found_tail is not None:
            return not_found_tail
        return f"서버가 오류로 답했다(HTTP {status})"
    return f"확인하지 못했다({type(error).__name__})"


def _timed_out(deadline_seconds: float) -> str:
    return f"{deadline_seconds:g}초 안에 답이 없었다"


def _unreached(name: str, address: str, tail: str) -> Unreached:
    return Unreached(f"모델 {name}({address})에 붙지 못했다: {tail}")
