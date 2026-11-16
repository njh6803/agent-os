"""요청을 보내는 쪽에서 도는 도우미. `run.py` 가 클라이언트 컨테이너 안에서 `docker exec` 로 부른다.

    python client.py <base64 로 싼 JSON>

`bridge_edge/client.py` 를 옮겨 일 둘(`poll`, `resolve`)을 더하고 쓰지 않는 일(`tcp`,
`bind`)을 뺐다. JSON 은 일(op)의 목록이고, 일마다 결과 하나를 모아 마지막에 `PROBE-RESULT
<JSON>` 한 줄로 낸다.
판정은 하지 않는다. 본 것(상태, 헤더, 본문, 오류의 종류, 걸린 시간, 서버 인증서의 지문)만 돌려주고
판정과 표지는 `run.py` 가 본다.

일의 종류(`kind`)
- `http`: 요청 `count` 개(기본 1)를 차례로 보낸다. 요청마다 새 연결이다. 경로와 헤더 값의 `{i}` 는
  그 요청의 차례로 바꾼다(기록에서 요청마다 찾으려는 것). 경로는 받은 글자 그대로 보낸다
  (`http.client` 는 경로를 정규화하지 않는다). `ca` 가 있으면 그 파일만 믿고 인증서와 이름을
  검증한다.
- `sse`: 이벤트 스트림을 읽으며 `data:` 줄마다 받은 시각(연결을 열기 직전부터의 초)을 적는다.
- `poll`: `window` 초 동안 `gap` 초 간격으로 요청 하나씩을 보내, 응답 본문의 `instance` 가
  `until_instance` 와 같아지면 멈춘다. 표본마다 결과 하나다(다시 만든 뒷단에 언제 닿는지).
- `resolve`: 그 이름을 `getaddrinfo` 로 풀어 주소 갈래(IPv4·IPv6)와 주소를 적는다.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import socket
import ssl
import sys
import time

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def text_of(op: dict[str, Json], key: str, default: str = "") -> str:
    value = op.get(key)
    return value if isinstance(value, str) else default


def number_of(op: dict[str, Json], key: str, default: float) -> float:
    value = op.get(key)
    return (
        float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default
    )


def headers_of(op: dict[str, Json], index: int) -> dict[str, str]:
    value = op.get("headers")
    if not isinstance(value, dict):
        return {}
    return {
        name: item.replace("{i}", str(index))
        for name, item in value.items()
        if isinstance(item, str)
    }


def kind_of(error: BaseException) -> str:
    """오류의 갈래. 닿지 않는 까닭을 거부(RST)와 시간 넘김과 TLS 와 끊김으로 가른다."""
    if isinstance(error, ConnectionRefusedError):
        return "refused"
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(error, ssl.SSLError):
        return "tls"
    if isinstance(error, (ConnectionResetError, BrokenPipeError)):
        return "reset"
    if isinstance(error, http.client.RemoteDisconnected):
        return "closed"
    return "error"


def connect(op: dict[str, Json]) -> http.client.HTTPConnection:
    host = text_of(op, "host")
    port = int(number_of(op, "port", 80))
    timeout = number_of(op, "timeout", 5.0)
    if text_of(op, "scheme", "http") != "https":
        return http.client.HTTPConnection(host, port, timeout=timeout)
    context = ssl.create_default_context(cafile=text_of(op, "ca"))
    return http.client.HTTPSConnection(host, port, timeout=timeout, context=context)


def exchange(
    connection: http.client.HTTPConnection, op: dict[str, Json], index: int
) -> dict[str, Json]:
    """요청을 보내고 응답을 읽는다. TLS 면 응답을 읽기 전에 서버 인증서의 지문과 판을 적는다."""
    seen: dict[str, Json] = {}
    size = int(number_of(op, "body_bytes", 0))
    connection.request(
        text_of(op, "method", "GET"),
        text_of(op, "path", "/").replace("{i}", str(index)),
        body=b"x" * size if size else None,
        headers=headers_of(op, index),
    )
    sock = connection.sock
    if isinstance(sock, ssl.SSLSocket):
        der = sock.getpeercert(binary_form=True)
        seen["cert_sha256"] = hashlib.sha256(der).hexdigest() if der else ""
        seen["tls"] = sock.version() or ""
    response = connection.getresponse()
    body = response.read()
    seen["status"] = response.status
    seen["headers"] = {name.lower(): value for name, value in response.getheaders()}
    seen["body"] = body[:4000].decode("utf-8", errors="replace")
    return seen


def request_once(op: dict[str, Json], origin: float, index: int) -> dict[str, Json]:
    started = time.monotonic()
    result: dict[str, Json] = {"t": round(started - origin, 4), "status": 0}
    connection = connect(op)
    try:
        result.update(exchange(connection, op, index))
    except (OSError, http.client.HTTPException) as error:
        result["error"] = f"{type(error).__name__}: {error}"
        result["error_kind"] = kind_of(error)
    finally:
        connection.close()
    result["ms"] = round((time.monotonic() - started) * 1000, 1)
    return result


def do_http(op: dict[str, Json]) -> Json:
    count = int(number_of(op, "count", 1))
    origin = time.monotonic()
    replies: list[Json] = [request_once(op, origin, index) for index in range(count)]
    return replies


def instance_of(reply: dict[str, Json]) -> str:
    body = reply.get("body")
    if not isinstance(body, str):
        return ""
    try:
        loaded: Json = json.loads(body)
    except ValueError:
        return ""
    value = loaded.get("instance") if isinstance(loaded, dict) else None
    return value if isinstance(value, str) else ""


def do_poll(op: dict[str, Json]) -> Json:
    window = number_of(op, "window", 40.0)
    gap = number_of(op, "gap", 0.5)
    wanted = text_of(op, "until_instance")
    origin = time.monotonic()
    samples: list[Json] = []
    index = 0
    while time.monotonic() - origin < window:
        reply = request_once(op, origin, index)
        samples.append(reply)
        index += 1
        if wanted and instance_of(reply) == wanted:
            break
        time.sleep(gap)
    return samples


def read_events(
    connection: http.client.HTTPConnection,
    op: dict[str, Json],
    started: float,
    arrivals: list[Json],
) -> dict[str, Json]:
    """이벤트 스트림을 끝까지 읽으며 `data:` 줄마다 받은 시각을 arrivals 에 더한다."""
    connection.request("GET", text_of(op, "path", "/"), headers=headers_of(op, 0))
    response = connection.getresponse()
    headers: dict[str, Json] = {name.lower(): value for name, value in response.getheaders()}
    while line := response.readline():
        if line.startswith(b"data:"):
            arrivals.append(round(time.monotonic() - started, 3))
    return {"status": response.status, "headers": headers}


def do_sse(op: dict[str, Json]) -> Json:
    started = time.monotonic()
    result: dict[str, Json] = {"status": 0}
    arrivals: list[Json] = []
    connection = connect(op)
    try:
        result.update(read_events(connection, op, started, arrivals))
    except (OSError, http.client.HTTPException) as error:
        result["error"] = f"{type(error).__name__}: {error}"
        result["error_kind"] = kind_of(error)
    finally:
        connection.close()
    result["arrivals"] = arrivals
    return result


def do_resolve(op: dict[str, Json]) -> Json:
    try:
        infos = socket.getaddrinfo(text_of(op, "host"), 80, type=socket.SOCK_STREAM)
    except OSError as error:
        return {"error": f"{type(error).__name__}: {error}"}
    found: list[Json] = []
    for family, _, _, _, address in infos:
        found.append([family.name, str(address[0])])
    return {"addresses": found}


def run_op(op: dict[str, Json]) -> Json:
    kind = text_of(op, "kind", "http")
    if kind == "http":
        return do_http(op)
    if kind == "sse":
        return do_sse(op)
    if kind == "poll":
        return do_poll(op)
    if kind == "resolve":
        return do_resolve(op)
    return {"error": f"모르는 kind: {kind}"}


def main() -> int:
    loaded: Json = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
    ops = loaded if isinstance(loaded, list) else []
    results: list[Json] = [run_op(op) if isinstance(op, dict) else None for op in ops]
    print("PROBE-RESULT " + json.dumps(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
