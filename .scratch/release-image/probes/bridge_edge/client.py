"""요청을 보내는 쪽에서 도는 도우미. `run.py` 가 이웃 컨테이너와 서버 자신 안에서 부른다.

    python client.py <base64 로 싼 JSON>

JSON 은 일(op)의 목록이고, 일마다 결과 하나를 모아 마지막에 `PROBE-RESULT <JSON>` 한 줄로 낸다.
측정의 판정은 하지 않는다. 본 것(상태, 헤더, 본문, 오류의 종류, 걸린 시간, 서버 인증서의 지문)만
돌려주고 판정과 표지는 `run.py` 가 본다.

일의 종류(`kind`)
- `http`: 요청 `count` 개(기본 1). `parallel` 이 참이면 스레드로 한꺼번에, 아니면 차례로 보낸다.
  요청마다 새 연결이다. 경로는 받은 글자 그대로 보낸다(`http.client` 는 경로를 정규화하지 않는다).
  `ca` 가 있으면 그 파일만 믿고 인증서와 이름(주소)을 검증하고, 없으면 검증하지 않는다.
- `tcp`: TCP 연결만 맺어 본다.
- `sse`: 이벤트 스트림을 읽으며 `data:` 줄마다 받은 시각(요청을 보낸 뒤의 초)을 적는다.
- `bind`: 이 프로세스가 그 포트에 묶을 수 있는지 본다(root 가 아닌 사용자의 낮은 포트).
- `sleep`: 그 초만큼 쉰다(한 번의 호출 안에서 간격을 두려는 것).
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import socket
import ssl
import sys
import threading
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


def headers_of(op: dict[str, Json]) -> dict[str, str]:
    value = op.get("headers")
    if not isinstance(value, dict):
        return {}
    return {name: item for name, item in value.items() if isinstance(item, str)}


def kind_of(error: BaseException) -> str:
    """오류의 갈래. 닿지 않는 까닭을 거부(RST)와 시간 넘김(버려짐)과 TLS 로 가른다."""
    if isinstance(error, ConnectionRefusedError):
        return "refused"
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(error, ssl.SSLError):
        return "tls"
    if isinstance(error, ConnectionResetError):
        return "reset"
    return "error"


def connect(op: dict[str, Json]) -> http.client.HTTPConnection:
    host = text_of(op, "host")
    port = int(number_of(op, "port", 80))
    timeout = number_of(op, "timeout", 5.0)
    source = text_of(op, "source")
    bound = (source, 0) if source else None
    if text_of(op, "scheme", "http") != "https":
        return http.client.HTTPConnection(host, port, timeout=timeout, source_address=bound)
    ca = text_of(op, "ca")
    if ca:
        context = ssl.create_default_context(cafile=ca)
    else:
        # 검증을 끄는 갈래는 하나다. 이웃이 컨테이너의 주소로 바로 거는 갈래이고, 그 주소는 시험용
        # 인증서의 이름에 없다. 거기서 보는 것은 닿는지와 받은 인증서의 지문이지 상대의 신원이
        # 아니다.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return http.client.HTTPSConnection(
        host, port, timeout=timeout, context=context, source_address=bound
    )


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
        headers=headers_of(op),
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
    """요청 하나. 경로의 `{i}` 는 그 요청의 차례로 바꾼다(기록에서 요청마다 찾으려는 것)."""
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
    if op.get("parallel") is not True:
        return [request_once(op, origin, index) for index in range(count)]
    slots: list[dict[str, Json]] = [{} for _ in range(count)]

    def work(index: int) -> None:
        slots[index] = request_once(op, origin, index)

    threads = [threading.Thread(target=work, args=(index,)) for index in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    replies: list[Json] = list(slots)
    return replies


def do_tcp(op: dict[str, Json]) -> Json:
    source = text_of(op, "source")
    started = time.monotonic()
    try:
        connection = socket.create_connection(
            (text_of(op, "host"), int(number_of(op, "port", 80))),
            timeout=number_of(op, "timeout", 3.0),
            source_address=(source, 0) if source else None,
        )
    except OSError as error:
        return {
            "connected": False,
            "error": f"{type(error).__name__}: {error}",
            "error_kind": kind_of(error),
            "ms": round((time.monotonic() - started) * 1000, 1),
        }
    connection.close()
    return {"connected": True, "ms": round((time.monotonic() - started) * 1000, 1)}


def read_events(
    connection: http.client.HTTPConnection,
    op: dict[str, Json],
    started: float,
    arrivals: list[Json],
) -> dict[str, Json]:
    """이벤트 스트림을 끝까지 읽으며 `data:` 줄마다 받은 시각을 arrivals 에 더한다."""
    connection.request("GET", text_of(op, "path", "/"), headers=headers_of(op))
    response = connection.getresponse()
    while line := response.readline():
        if line.startswith(b"data:"):
            arrivals.append(round(time.monotonic() - started, 3))
    headers: dict[str, Json] = {name.lower(): value for name, value in response.getheaders()}
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


def do_bind(op: dict[str, Json]) -> Json:
    port = int(number_of(op, "port", 80))
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind(("0.0.0.0", port))
    except OSError as error:
        return {"bound": False, "uid": os.getuid(), "error": f"{type(error).__name__}: {error}"}
    finally:
        listener.close()
    return {"bound": True, "uid": os.getuid()}


def run_op(op: dict[str, Json]) -> Json:
    kind = text_of(op, "kind", "http")
    if kind == "http":
        return do_http(op)
    if kind == "tcp":
        return do_tcp(op)
    if kind == "sse":
        return do_sse(op)
    if kind == "bind":
        return do_bind(op)
    if kind == "sleep":
        time.sleep(number_of(op, "seconds", 1.0))
        return {"slept": number_of(op, "seconds", 1.0)}
    return {"error": f"모르는 kind: {kind}"}


def main() -> int:
    loaded: Json = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
    ops = loaded if isinstance(loaded, list) else []
    results: list[Json] = [run_op(op) if isinstance(op, dict) else None for op in ops]
    print("PROBE-RESULT " + json.dumps(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
