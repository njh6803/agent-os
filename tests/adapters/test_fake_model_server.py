"""가짜 모델 서버 픽스처(`tests/adapters/fake_model_server.py`) 자신의 시험.

보통의 HTTP 클라이언트(표준 라이브러리의 `http.client`)로 민다. 모델 서버의 어댑터 시험(05)이
이 픽스처에 붙기 전에, 픽스처가 받은 요청과 연결의 셈을 믿을 수 있는지를 여기서 본다.
"""

from __future__ import annotations

import http.client
import json
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable

import pytest
from tests.adapters.fake_model_server import (
    CHAT_PATH,
    FakeModelServer,
    Received,
    Reply,
    completion,
    error_reply,
    tool_call,
)

# 몇 초 안에 닿는다는 단언의 상한. 홀로 돌면 0.1초 안쪽이고, 다른 시험과 겹친 부하를 넉넉히 덮는다
# (`.claude/rules/tests.md`의 시간 단언).
PATIENCE_SECONDS = 20.0
# 답을 늦추는 사례가 서버에 시키는 기다림. 클라이언트가 이보다 짧은 시간에 끊는다.
SLOW_SECONDS = 2.0


def _post(
    connection: http.client.HTTPConnection, path: str, payload: object, **headers: str
) -> tuple[int, bytes]:
    connection.request(
        "POST",
        path,
        body=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    response = connection.getresponse()
    return response.status, response.read()


def _until(condition: Callable[[], bool]) -> bool:
    """기한까지 거듭 견준다. 한 번만 견주면 부하에서 지나가는 순간을 놓친다."""
    end = time.monotonic() + PATIENCE_SECONDS
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


def test_받은_요청의_메서드_경로_헤더_본문이_받은_차례로_적힌다() -> None:
    with FakeModelServer(Reply.text(200, "a"), Reply.text(200, "b")) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        _post(connection, CHAT_PATH, {"n": 1}, Authorization="Bearer first-key")
        connection.request("GET", "/v1/models?limit=1", headers={"X-Probe": "second"})
        connection.getresponse().read()
        connection.close()

        first, second = server.requests
    assert (first.method, first.path) == ("POST", CHAT_PATH)
    assert first.header("authorization") == ["Bearer first-key"]
    assert first.header("Content-Type") == ["application/json"]
    assert first.json() == {"n": 1}
    assert (second.method, second.path, second.target) == (
        "GET",
        "/v1/models",
        "/v1/models?limit=1",
    )
    assert second.header("x-probe") == ["second"]
    assert second.body == b""
    assert second.json() is None


def test_정한_응답이_차례대로_오고_정한_상태_코드와_본문이_그대로_온다() -> None:
    with FakeModelServer(
        completion(content="첫째"), error_reply(401, "bad key"), Reply.json(429, {"slow": "down"})
    ) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        answers = [_post(connection, CHAT_PATH, {}) for _ in range(3)]
        connection.close()

    assert [status for status, _ in answers] == [200, 401, 429]
    first = json.loads(answers[0][1])
    assert first["choices"][0]["message"]["content"] == "첫째"
    assert json.loads(answers[1][1])["error"]["message"] == "bad key"
    assert json.loads(answers[2][1]) == {"slow": "down"}


def test_정한_응답이_바닥나면_정한_응답이_없다고_답하고_그_요청도_적는다() -> None:
    with FakeModelServer() as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        status, body = _post(connection, CHAT_PATH, {})
        connection.close()
        assert len(server.requests) == 1
    assert status == 404
    assert "정한 응답이 없다" in json.loads(body)["error"]["message"]


def test_응답_함수가_받은_요청으로_응답을_짓는다() -> None:
    def echo_key(request: Received) -> Reply:
        key = request.header("authorization")[0].removeprefix("Bearer ")
        return error_reply(401, f"Incorrect API key provided: {key}")

    with FakeModelServer(echo_key) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        status, body = _post(connection, CHAT_PATH, {}, Authorization="Bearer echoed-key-1234")
        connection.close()
    assert status == 401
    assert "echoed-key-1234" in json.loads(body)["error"]["message"]


def test_응답_함수는_요청을_받은_뒤_그_자리에서_돈다() -> None:
    """요청을 받은 뒤 환경을 바꾸는 사례(05의 키 교체)가 기대는 순서: 적고, 함수를 돌리고,
    답한다."""
    seen_before_responding: list[int] = []
    ran_on_test_thread: list[bool] = []

    def inspect(request: Received) -> Reply:
        seen_before_responding.append(len(server.requests))
        ran_on_test_thread.append(threading.current_thread() is test_thread)
        return Reply.text(200, "ok")

    test_thread = threading.current_thread()
    with FakeModelServer(inspect) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        _post(connection, CHAT_PATH, {})
        connection.close()
    assert seen_before_responding == [1], f"응답 함수가 본 요청 수 {seen_before_responding}"
    assert ran_on_test_thread == [False], "응답 함수는 서버 스레드에서 돈다"


def test_답하기_전에_기다릴_시간을_준_응답은_늦게_온다() -> None:
    with FakeModelServer(Reply.text(200, "늦은 답", delay_seconds=0.4)) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        started = time.monotonic()
        status, body = _post(connection, CHAT_PATH, {})
        elapsed = time.monotonic() - started
        connection.close()
    assert (status, body) == (200, "늦은 답".encode())
    assert elapsed >= 0.35, f"기다린 시간 {elapsed:.2f}초"


def test_JSON이_아닌_날_글자_본문이_그대로_온다() -> None:
    with FakeModelServer(Reply.text(200, "<html>not json</html>", content_type="text/html")) as s:
        connection = http.client.HTTPConnection("127.0.0.1", s.port)
        connection.request("POST", CHAT_PATH, body=b"{}")
        response = connection.getresponse()
        body = response.read()
        content_type = response.getheader("Content-Type")
        connection.close()
    assert (response.status, body) == (200, b"<html>not json</html>")
    assert content_type == "text/html"


def test_Chat_Completions_응답_도우미는_글_도구_호출_usage_model을_짓는다() -> None:
    reply = completion(
        content=None,
        tool_calls=[tool_call("add", '{"a": 1, "b": 2}', call_id="call_9")],
        model="served-name",
        usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        finish_reason="tool_calls",
    )
    assert reply.status == 200
    payload = json.loads(reply.body)
    choice = payload["choices"][0]
    assert payload["model"] == "served-name"
    assert payload["usage"]["total_tokens"] == 7
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["tool_calls"] == [
        {
            "id": "call_9",
            "type": "function",
            "function": {"name": "add", "arguments": '{"a": 1, "b": 2}'},
        }
    ]
    assert "model" not in json.loads(completion(model=None).body)
    assert "usage" not in json.loads(completion().body)


def test_연결을_쥔_채_두_번_부르면_연결_하나로_보내고_닫기_전에는_처리를_마친_연결이_없다() -> None:
    with FakeModelServer(Reply.text(200, "a"), Reply.text(200, "b")) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        _post(connection, CHAT_PATH, {})
        _post(connection, CHAT_PATH, {})
        assert (server.opened_connections, server.closed_connections) == (1, 0)
        assert len(server.requests) == 2
        connection.close()
        assert server.connections_settled(PATIENCE_SECONDS)
        assert (server.opened_connections, server.closed_connections) == (1, 1)


def test_연결을_닫고_다시_부르면_받은_연결과_처리를_마친_연결이_함께_는다() -> None:
    with FakeModelServer(Reply.text(200, "a"), Reply.text(200, "b"), Reply.text(200, "c")) as s:
        for _ in range(3):
            connection = http.client.HTTPConnection("127.0.0.1", s.port)
            _post(connection, CHAT_PATH, {})
            connection.close()
        settled = s.connections_settled(PATIENCE_SECONDS)
        assert settled, f"셈이 끝나지 않았다: {s.opened_connections}/{s.closed_connections}"
        assert (s.opened_connections, s.closed_connections) == (3, 3)


def test_서버는_응답마다_연결을_닫지_않고_HTTP_1_1로_답한다() -> None:
    with FakeModelServer(Reply.text(200, "a")) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port)
        connection.request("POST", CHAT_PATH, body=b"{}")
        response = connection.getresponse()
        response.read()
        version, closing = response.version, response.will_close
        connection.close()
    assert (version, closing) == (11, False), f"연결 유지: 버전 {version}, 닫음 {closing}"


def test_기다릴_시간을_준_응답을_먼저_끊으면_처리를_마친_연결은_그_시간이_끝난_뒤에_는다() -> None:
    with FakeModelServer(Reply.text(200, "너무 늦다", delay_seconds=SLOW_SECONDS)) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.port, timeout=0.2)
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            _post(connection, CHAT_PATH, {})
        connection.close()
        # 클라이언트는 끊었지만 서버는 아직 그 요청을 처리하는 중이다. 부하로 이 줄이 기다릴 시간이
        # 끝난 뒤에 돌 수 있으니, 아직 그 시간 안일 때만 처리를 마친 연결이 0임을 단언한다. 받은
        # 연결은 서버 스레드가 굶으면 아직 0일 수 있어 보지 않는다.
        counts_at_cut = (server.opened_connections, server.closed_connections)
        still_waiting = time.monotonic() - started < SLOW_SECONDS - 0.5
        assert counts_at_cut[1] == 0 or not still_waiting, f"끊은 직후 셈 {counts_at_cut}"
        assert server.connections_settled(PATIENCE_SECONDS)
        settled_after = time.monotonic() - started
        assert (server.opened_connections, server.closed_connections) == (1, 1)
        # 처리를 마친 것으로 세어진 시각은 기다릴 시간이 끝난 뒤다(시계의 오차를 0.1초 덮는다)
        assert settled_after >= SLOW_SECONDS - 0.1, f"셈이 끝난 시각 {settled_after:.2f}초"


def test_서버_둘은_받은_요청과_연결의_셈이_따로다() -> None:
    with (
        FakeModelServer(Reply.text(200, "a")) as used,
        FakeModelServer(Reply.text(200, "b")) as decoy,
    ):
        assert used.port != decoy.port
        connection = http.client.HTTPConnection("127.0.0.1", used.port)
        _post(connection, CHAT_PATH, {})
        connection.close()
        assert used.connections_settled(PATIENCE_SECONDS)
        assert len(used.requests) == 1
        assert decoy.requests == []
        assert (decoy.opened_connections, decoy.closed_connections) == (0, 0)


def test_핸들로_끈_뒤에는_그_포트에_붙으면_연결이_거부된다() -> None:
    server = FakeModelServer(Reply.text(200, "a"))
    server.start()
    port = server.port
    with socket.create_connection(("127.0.0.1", port), timeout=PATIENCE_SECONDS):
        pass
    server.stop()
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(("127.0.0.1", port), timeout=PATIENCE_SECONDS)


def test_뜨기_전이나_끈_뒤에_주소를_읽거나_이미_뜬_서버를_또_띄우면_알아듣게_실패한다() -> None:
    server = FakeModelServer()
    with pytest.raises(RuntimeError, match="아직 뜨지 않았다"):
        _ = server.base_url
    server.start()
    with pytest.raises(RuntimeError, match="이미 떠 있다"):
        server.start()
    server.stop()
    with pytest.raises(RuntimeError, match="아직 뜨지 않았다"):
        _ = server.port


def test_이미_끈_서버를_다시_꺼도_실패하지_않는다() -> None:
    server = FakeModelServer().start()
    server.stop()
    server.stop()


def test_주소는_모델_파일의_base_url로_쓰는_v1_경로까지다() -> None:
    with FakeModelServer() as server:
        assert server.base_url == f"http://127.0.0.1:{server.port}/v1"


def test_자식_프로세스에서도_그_주소로_요청이_닿는다() -> None:
    child = (
        "import http.client, sys\n"
        "host, port = sys.argv[1].split(':')\n"
        "connection = http.client.HTTPConnection(host, int(port), timeout=30)\n"
        "connection.request('POST', sys.argv[2], body=b'{\"from\": \"child\"}',\n"
        "                   headers={'Authorization': 'Bearer child-key'})\n"
        "response = connection.getresponse()\n"
        "sys.stdout.buffer.write(f'{response.status} '.encode() + response.read())\n"
    )
    with FakeModelServer(Reply.text(200, "자식에게")) as server:
        done = subprocess.run(
            [sys.executable, "-I", "-c", child, f"127.0.0.1:{server.port}", CHAT_PATH],
            capture_output=True,
            timeout=PATIENCE_SECONDS * 3,
            check=False,
        )
        assert _until(lambda: len(server.requests) == 1)
        received = server.requests[0]
    assert done.returncode == 0, done.stderr.decode()
    assert done.stdout.decode("utf-8") == "200 자식에게"
    assert received.json() == {"from": "child"}
    assert received.header("authorization") == ["Bearer child-key"]
