"""web-widget 의 nginx 중계를 잰다. 결정은 하지 않고 표만 낸다.

저장소 루트에서

    uv run python .scratch/web-widget/probes/nginx_relay/measure.py \\
        --nginx <nginx 실행 파일> [--nginx <다른 판> ...] \\
        --next-app <next_app/ 사본에 pnpm install 을 마친 폴더> \\
        [--sections headers,stream,silence,truncate,abort,allow] [--silence-s 90] \\
        [--work <작업 폴더를 만들 곳>]

- 파이썬 상류는 sse_app.py 다. 이 스크립트가 같은 인터프리터로 띄운다(저장소가 잠근 fastapi).
- Next 는 --next-app 폴더에서 `next build`(상류를 박는다) 뒤 `next start` 로 띄운다.
- nginx 는 판마다 임시 prefix 에 nginx.conf 를 채워 띄우고 섹션을 돈 뒤 내린다.
- TLS 는 실행마다 만드는 자체 서명 인증서다. 클라이언트는 그 인증서로 검증한다.
- HTTP/1.1 클라이언트는 이 파일의 asyncio 소켓 코드다. 요청 줄을 글자 그대로 보내고
  (허용 목록), 청크와 gzip 을 받는 대로 풀어 프레임마다 도착 시각을 찍는다. 브라우저처럼
  늘 `Accept-Encoding: gzip, deflate, br` 을 보낸다.
- HTTP/2 클라이언트는 h2_client.mjs(node 의 http2)다. 도착 시각은 node 가 찍는다.

섹션
- headers  파이썬·Next 를 직접, nginx 를 거쳐 부른 응답 헤더(X-Accel-Buffering 등).
- stream   프레임 10개를 500ms 간격으로. 변형마다 평문·TLS·HTTP/2 로 도착 시각을 잰다.
- silence  첫 프레임 뒤 --silence-s 초 침묵. keepalive 가 있는 것과 없는 대조군.
- truncate 상류가 응답 도중 죽을 때 클라이언트에게 정상 종료로 보이는가(상류 HTTP 판별).
- abort    클라이언트가 흐르는 중·침묵 중에 끊으면 파이썬이 상류 연결의 끊김을 언제 보는가.
           끊는 모양은 다섯이다(평문 FIN, TLS close_notify 뒤 FIN, TLS 알림 없이 소켓 닫기,
           h2 RST_STREAM, h2 세션째 닫기).
- allow    허용 목록 후보(a_default, b_default)에 요청 줄을 그대로 보내 누가 답했는지.

포트 18700(파이썬), 18701(Next), 18710~18799(nginx)가 비어 있어야 한다. 띄운 프로세스는
끝에서 트리째 내린다(윈도우는 taskkill /T /F, 그 밖은 프로세스 그룹). 판 셋을 한 번에
돌린 것이 10분 24초였다(2026-10-03, next build 한 번 포함, 셸의 date 로 봤다).

2026-10-03 결과(윈도우 10, nginx.org 의 윈도우 zip 1.24.0·1.28.3·1.30.5, 두 번 돌려 같았다)
- headers: 파이썬·Next 직접은 X-Accel-Buffering: no 를 낸다. nginx 를 지나면 빠진다.
- stream: 그 헤더를 따르는 변형은 평문·TLS·h2 모두 흐른다(gzip 을 켜도). 헤더를
  무시시키면 끝에 몰린다. 다만 상류가 HTTP/1.1 이면(1.30.5 의 기본값, *_h11) 평문과
  h2 는 흐르고 TLS 위 HTTP/1.1 만 몰린다.
- silence: keepalive 가 있으면 90초를 버틴다(ping 5개). 없으면 a 는 60초
  (proxy_read_timeout), b 는 30초(Next)에 끊긴다. b 의 끊김은 nginx 의 상류가
  HTTP/1.0 이면(1.24.0·1.28.3 의 기본값, b_h10) 클라이언트에게 정상 종료로 보인다.
- truncate: 상류 연결이 응답 도중 닫히면 상류가 HTTP/1.0 일 때 정상 종료로 보이고
  1.1 일 때 드러난다. EventSourceResponse 생성기의 예외는 어느 길에서든 정상 종료다.
- abort: 평문 FIN, TLS 알림 없이, h2 RST_STREAM, h2 세션째는 0.01초 안에 상류가
  닫힌다. TLS close_notify 뒤 FIN 은 nginx 가 쓰기에 실패할 때까지 상류를 열어 둔다
  (흐르는 중 1.5초, 침묵 중 43초로 세 번째 ping). 헤더를 무시시킨 변형의 TLS
  close_notify 는 50초 안에 닫히지 않았다.
- allow: 두 후보 모두 차단 대상에는 nginx 가 답했다. 파이썬이 /chat/ 밖을 본 것은
  a_default 의 /CHAT/x 하나다(윈도우 nginx 는 위치를 대소문자 없이 맞춘다). b 에서는
  Next 가 그것을 /chat/x 로 바꿔 넘겼다. TLS 와 평문의 결과가 같았다.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime
import importlib.metadata
import ipaddress
import json
import os
import re
import secrets
import signal
import ssl
import subprocess
import sys
import tempfile
import time
import zlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

HERE = Path(__file__).resolve().parent
PY_PORT = 18700
NEXT_PORT = 18701
VARIANTS = (
    "a_default",
    "a_buffering_off",
    "a_ignore_xab",
    "a_gzip_on",
    "a_gzip_sse",
    "a_gzip_sse_ignore_xab",
    "a_gzip_sse_buffering_off",
    "b_default",
    "b_buffering_off",
    "b_ignore_xab",
    "b_gzip_sse",
    "w_slash_only",
    "a_h10",
    "a_h11",
    "a_ignore_xab_h10",
    "a_ignore_xab_h11",
    "b_h10",
    "b_h11",
)
STREAM_VARIANTS = tuple(v for v in VARIANTS if v != "w_slash_only")
ABORT_VARIANTS = ("a_default", "a_buffering_off", "a_ignore_xab", "b_default", "b_ignore_xab")
CLOSINGS = ("평문 FIN", "TLS close_notify", "TLS 알림 없이", "h2 RST_STREAM", "h2 세션째")
BASE = {"http": 18710, "tls": 18740, "h2": 18770}
WINDOWS = os.name == "nt"
COUNT = 10
INTERVAL_MS = 500


def now_ms() -> float:
    return time.time() * 1000


def port_of(scheme: str, variant: str) -> int:
    return BASE[scheme] + VARIANTS.index(variant)


def probe_id(label: str) -> str:
    return f"{label}-{secrets.token_hex(3)}"


# ---------- 프로세스 ----------


def spawn(
    args: list[str], log: Path, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.Popen[bytes]:
    out = log.open("wb")
    return subprocess.Popen(
        args,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        stdout=out,
        stderr=subprocess.STDOUT,
        start_new_session=not WINDOWS,
    )


def kill_tree(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait(10)


async def wait_port(port: int, proc: subprocess.Popen[bytes], seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"포트 {port} 가 서기 전에 프로세스가 끝났다({proc.returncode})")
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            return
        except OSError:
            await asyncio.sleep(0.3)
    raise RuntimeError(f"포트 {port} 가 {seconds}초 안에 서지 않았다")


def make_cert(directory: Path) -> tuple[Path, Path]:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    start = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
    san = x509.SubjectAlternativeName(
        [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(start)
        .not_valid_after(start + datetime.timedelta(days=1))
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_path = directory / "cert.pem"
    key_path = directory / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


def render_conf(prefix: Path, cert: Path, key: Path) -> None:
    text = (HERE / "nginx.conf").read_text(encoding="utf-8")
    text = text.replace("@CERT@", cert.as_posix()).replace("@KEY@", key.as_posix())
    text = text.replace("@PY_PORT@", str(PY_PORT)).replace("@NEXT_PORT@", str(NEXT_PORT))

    def port_for(match: re.Match[str]) -> str:
        return str(port_of(match.group(1).lower(), match.group(2)))

    text = re.sub(r"@(HTTP|TLS|H2)_(\w+)@", port_for, text)
    left = re.findall(r"@\w+@", text)
    if left:
        raise RuntimeError(f"채우지 못한 자리: {left}")
    for sub in ("conf", "logs", "temp"):
        (prefix / sub).mkdir(parents=True, exist_ok=True)
    (prefix / "conf" / "nginx.conf").write_text(text, encoding="utf-8")


class Nginx:
    def __init__(self, exe: Path, prefix: Path) -> None:
        self.exe = exe
        self.prefix = prefix
        self.proc: subprocess.Popen[bytes] | None = None

    def args(self, *extra: str) -> list[str]:
        prefix = str(self.prefix) + os.sep
        conf = "conf/nginx.conf"
        return [str(self.exe), "-p", prefix, "-c", conf, "-e", "logs/error.log", *extra]

    def version(self) -> str:
        done = subprocess.run([str(self.exe), "-v"], capture_output=True, text=True)
        return (done.stderr or done.stdout).strip()

    def test(self) -> str:
        done = subprocess.run(self.args("-t"), capture_output=True, text=True, cwd=self.prefix)
        return (done.stderr + done.stdout).strip()

    async def start(self) -> None:
        log = self.prefix / "logs" / "stdout.log"
        self.proc = spawn(self.args(), log, cwd=self.prefix)
        await wait_port(port_of("http", "a_default"), self.proc)

    def stop(self) -> None:
        if self.proc is None:
            return
        subprocess.run(self.args("-s", "stop"), capture_output=True, cwd=self.prefix)
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            kill_tree(self.proc)
        kill_tree(self.proc)

    def errors_for(self, probe: str) -> str:
        """오류 기록에서 그 probe 의 요청 줄이 든 줄의 메시지만 모은다. 오류 번호의 설명은 뺀다."""
        path = self.prefix / "logs" / "error.log"
        if not path.exists():
            return ""
        found: list[str] = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if probe not in line:
                continue
            match = re.search(r"\*\d+ (.*?), client:", line)
            message = match.group(1) if match else line
            message = re.sub(r"\((\d+): [^)]*\)", r"(\1)", message).strip()
            if message not in found:
                found.append(message)
        return "; ".join(found)


# ---------- 파이썬 기록 ----------


class PythonLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def events(self, probe: str) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        out: list[dict[str, object]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if f"probe={probe}" in str(record.get("query", "")):
                out.append(record)
        return out

    def disconnect(self, probe: str) -> dict[str, object] | None:
        """응답을 다 보내기 전에 받은 http.disconnect. 다 보낸 뒤의 것은 끊김이 아니다."""
        for event in self.events(probe):
            if event.get("event") == "disconnect" and event.get("finished") is False:
                return event
        return None


# ---------- 클라이언트 ----------


@dataclass
class Frame:
    at_ms: float
    seq: int
    sent_ms: float


@dataclass
class Exchange:
    status: int = 0
    version: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    started_ms: float = 0.0
    frames: list[Frame] = field(default_factory=list)
    pings: list[float] = field(default_factory=list)
    end: str = ""
    end_ms: float = 0.0
    error: str = ""
    body: bytes = b""


class SseParser:
    def __init__(self, exchange: Exchange) -> None:
        self.exchange = exchange
        self.buffer = ""

    def feed(self, data: bytes, at_ms: float) -> None:
        self.buffer += data.decode("utf-8", errors="replace").replace("\r\n", "\n")
        while "\n\n" in self.buffer:
            block, self.buffer = self.buffer.split("\n\n", 1)
            lines = [line for line in block.split("\n") if line]
            datas = [line[5:].strip() for line in lines if line.startswith("data:")]
            if datas:
                payload = json.loads("\n".join(datas))
                frame = Frame(at_ms, int(payload["seq"]), float(payload["sent_ms"]))
                self.exchange.frames.append(frame)
            elif lines and all(line.startswith(":") for line in lines):
                self.exchange.pings.append(at_ms)


class Body:
    """Content-Encoding: gzip 이면 받은 조각을 받는 대로 푼다."""

    def __init__(self, headers: dict[str, str]) -> None:
        gzip = headers.get("content-encoding") == "gzip"
        self.inflate = zlib.decompressobj(wbits=31) if gzip else None

    def decode(self, chunk: bytes) -> bytes:
        return self.inflate.decompress(chunk) if self.inflate is not None else chunk


def client_tls(cert: Path) -> ssl.SSLContext:
    return ssl.create_default_context(cafile=str(cert))


async def h1_connect(
    port: int, cert: Path | None
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    context = client_tls(cert) if cert is not None else None
    hostname = "localhost" if context is not None else None
    return await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1", port, ssl=context, server_hostname=hostname), 10
    )


def h1_request(method: str, target: str) -> bytes:
    body = b"{}" if method == "POST" else b""
    lines = [
        f"{method} {target} HTTP/1.1",
        "Host: localhost",
        "User-Agent: nginx-relay-probe",
        "Accept: text/event-stream, */*",
        "Accept-Encoding: gzip, deflate, br",
        "Connection: close",
    ]
    if method == "POST":
        lines += ["Content-Type: application/json", f"Content-Length: {len(body)}"]
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1") + body


async def h1_head(reader: asyncio.StreamReader, exchange: Exchange) -> None:
    head = await reader.readuntil(b"\r\n\r\n")
    status_line, *header_lines = head.decode("latin-1").split("\r\n")
    exchange.version, status, *_ = status_line.split(" ")
    exchange.status = int(status)
    for line in header_lines:
        if line:
            name, _, value = line.partition(":")
            key = name.strip().lower()
            old = exchange.headers.get(key)
            exchange.headers[key] = value.strip() if old is None else f"{old}, {value.strip()}"


async def body_chunks(
    reader: asyncio.StreamReader, headers: dict[str, str]
) -> AsyncIterator[bytes]:
    if "chunked" in headers.get("transfer-encoding", "").lower():
        while True:
            line = await reader.readuntil(b"\r\n")
            size = int(line.split(b";")[0].strip(), 16)
            if size == 0:
                await reader.readuntil(b"\r\n")
                return
            data = await reader.readexactly(size)
            await reader.readexactly(2)
            yield data
    elif "content-length" in headers:
        remaining = int(headers["content-length"])
        while remaining > 0:
            data = await reader.read(min(remaining, 65536))
            if not data:
                raise asyncio.IncompleteReadError(b"", remaining)
            remaining -= len(data)
            yield data
    else:
        while data := await reader.read(65536):
            yield data


async def h1(
    port: int,
    target: str,
    *,
    cert: Path | None,
    method: str = "POST",
    limit_s: float = 30,
    sse: bool = True,
) -> Exchange:
    """HTTP/1.1 요청 하나. cert 가 있으면 TLS. sse 가 거짓이면 본문을 풀어 body 에 모은다."""
    exchange = Exchange(started_ms=now_ms())
    try:
        reader, writer = await h1_connect(port, cert)
    except (OSError, TimeoutError) as error:
        exchange.end = "연결 실패"
        exchange.error = repr(error)
        return exchange
    writer.write(h1_request(method, target))

    async def read() -> None:
        await h1_head(reader, exchange)
        body = Body(exchange.headers)
        parser = SseParser(exchange)
        async for chunk in body_chunks(reader, exchange.headers):
            data = body.decode(chunk)
            if not sse:
                exchange.body += data
            elif data:
                parser.feed(data, now_ms())
        exchange.end = "끝남"

    try:
        await writer.drain()
        await asyncio.wait_for(read(), limit_s)
    except TimeoutError:
        exchange.end = "시간 초과"
    except asyncio.IncompleteReadError:
        exchange.end = "조기 종료"
    except (OSError, ssl.SSLError) as error:
        exchange.end = "연결 오류"
        exchange.error = repr(error)
    finally:
        exchange.end_ms = now_ms()
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 5)
        except (OSError, TimeoutError, ssl.SSLError):
            pass
    return exchange


class H2Client:
    """h2_client.mjs 하나를 부린다. 메시지의 시각은 node 가 찍은 것이다."""

    def __init__(self, proc: asyncio.subprocess.Process) -> None:
        self.proc = proc

    @classmethod
    async def start(cls, port: int, target: str, cert: Path) -> H2Client:
        proc = await asyncio.create_subprocess_exec(
            "node",
            str(HERE / "h2_client.mjs"),
            str(port),
            target,
            str(cert),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        return cls(proc)

    async def read(self, timeout: float) -> dict[str, object] | None:
        assert self.proc.stdout is not None
        line = await asyncio.wait_for(self.proc.stdout.readline(), max(timeout, 0.01))
        return json.loads(line) if line else None

    async def command(self, name: str) -> float:
        """명령을 보내고 node 가 그것을 실행한 시각을 돌려준다."""
        assert self.proc.stdin is not None
        self.proc.stdin.write(f"{name}\n".encode())
        await self.proc.stdin.drain()
        while (message := await self.read(10)) is not None:
            if message.get("type") in ("cancelled", "destroyed"):
                return float(str(message["t"]))
        raise RuntimeError(f"h2_client 가 {name} 에 답하지 않았다")

    def kill(self) -> None:
        if self.proc.returncode is None:
            self.proc.kill()


class H2Stream:
    """h2_client 메시지를 Exchange 에 옮긴다."""

    def __init__(self) -> None:
        self.exchange = Exchange(started_ms=now_ms(), version="HTTP/2")
        self.parser = SseParser(self.exchange)
        self.body = Body({})

    def apply(self, message: dict[str, object]) -> bool:
        """메시지 하나를 옮긴다. 스트림이 끝났으면 참."""
        exchange = self.exchange
        kind = message.get("type")
        at = float(str(message.get("t")))
        if kind == "headers":
            raw = message.get("headers")
            headers = {str(k): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}
            exchange.status = int(headers.get(":status", "0"))
            exchange.headers = {k: v for k, v in headers.items() if not k.startswith(":")}
            self.body = Body(exchange.headers)
        elif kind == "data":
            chunk = base64.b64decode(str(message.get("b64")))
            self.parser.feed(self.body.decode(chunk), at)
        elif kind in ("end", "error"):
            exchange.end = "끝남" if kind == "end" else "오류"
            exchange.error = str(message.get("message", ""))
            exchange.end_ms = at
            return True
        return False


async def h2(port: int, target: str, *, cert: Path, limit_s: float) -> Exchange:
    stream = H2Stream()
    exchange = stream.exchange
    client = await H2Client.start(port, target, cert)
    deadline = time.monotonic() + limit_s
    try:
        while True:
            message = await client.read(deadline - time.monotonic())
            if message is None:
                exchange.end = "h2_client 가 끝남"
                break
            if stream.apply(message):
                break
    except TimeoutError:
        exchange.end = "시간 초과"
    finally:
        client.kill()
        if not exchange.end_ms:
            exchange.end_ms = now_ms()
    return exchange


# ---------- 표 ----------


def table(headers: list[str], rows: list[list[str]]) -> None:
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        print("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    print()


def stream_verdict(exchange: Exchange) -> tuple[str, str, str, str]:
    frames = exchange.frames
    if not frames:
        return "-", "-", "-", f"프레임 없음({exchange.end} {exchange.error})".strip()
    lags = [f.at_ms - f.sent_ms for f in frames]
    spread = frames[-1].at_ms - frames[0].at_ms
    first, worst = f"{lags[0]:.0f}", f"{max(lags):.0f}"
    if len(frames) < COUNT:
        verdict = f"잘림({len(frames)}개, {exchange.end})"
    elif max(lags) <= 250:
        verdict = "흐른다"
    elif spread <= 1000:
        verdict = "끝에 몰린다"
    else:
        verdict = "늦게 흐른다"
    return first, worst, f"{spread:.0f}", verdict


# ---------- 섹션 ----------


@dataclass
class Context:
    cert: Path
    nginx: Nginx
    pylog: PythonLog
    silence_s: float


async def exchange_over(
    ctx: Context, scheme: str, port: int, target: str, limit_s: float
) -> Exchange:
    if scheme == "h2":
        return await h2(port, target, cert=ctx.cert, limit_s=limit_s)
    return await h1(port, target, cert=ctx.cert if scheme == "tls" else None, limit_s=limit_s)


async def section_headers(ctx: Context) -> None:
    print("### headers: 응답 헤더(POST /chat/stream, Accept-Encoding: gzip, deflate, br)\n")
    target = "/chat/stream?count=2&interval_ms=100"
    cases: list[tuple[str, str, int]] = [
        ("파이썬 직접", "http", PY_PORT),
        ("Next 직접(rewrites)", "http", NEXT_PORT),
        ("nginx a_default 평문", "http", port_of("http", "a_default")),
        ("nginx a_default TLS", "tls", port_of("tls", "a_default")),
        ("nginx a_default h2", "h2", port_of("h2", "a_default")),
        ("nginx b_default TLS", "tls", port_of("tls", "b_default")),
    ]
    results = await asyncio.gather(*(exchange_over(ctx, s, p, target, 10) for _, s, p in cases))
    names = ["content-type", "cache-control", "x-accel-buffering", "content-encoding"]
    names += ["transfer-encoding", "server", "x-probe-upstream"]
    rows = [
        [label, f"{r.version} {r.status}"] + [r.headers.get(n, "(없음)") for n in names]
        for (label, _, _), r in zip(cases, results, strict=True)
    ]
    table(["경로", "상태", *names], rows)


async def section_stream(ctx: Context) -> None:
    print(f"### stream: 프레임 {COUNT}개를 {INTERVAL_MS}ms 간격으로(POST /chat/stream)\n")
    print("지연은 도착 시각 - 파이썬이 프레임을 만든 시각(ms).")
    print("펼침은 첫 프레임과 끝 프레임의 도착 간격(ms).\n")
    rows: list[list[str]] = []
    query = f"count={COUNT}&interval_ms={INTERVAL_MS}"

    async def one(label: str, scheme: str, port: int) -> list[str]:
        target = f"/chat/stream?{query}&probe={probe_id('stream')}"
        r = await exchange_over(ctx, scheme, port, target, 20)
        first, worst, spread, verdict = stream_verdict(r)
        encoding = r.headers.get("content-encoding", "-")
        status = f"{r.version} {r.status}"
        return [label, scheme, status, encoding, str(len(r.frames)), first, worst, spread, verdict]

    baseline = [one("파이썬 직접", "http", PY_PORT), one("Next 직접", "http", NEXT_PORT)]
    rows += await asyncio.gather(*baseline)
    for scheme in ("http", "tls", "h2"):
        jobs = [one(v, scheme, port_of(scheme, v)) for v in STREAM_VARIANTS]
        rows += await asyncio.gather(*jobs)
    headers = ["변형", "방식", "상태", "압축", "프레임", "첫 지연", "최대 지연", "펼침", "판정"]
    table(headers, rows)


async def section_silence(ctx: Context) -> None:
    silence = ctx.silence_s
    print(f"### silence: 첫 프레임 뒤 {silence:.0f}초 침묵, 그다음 프레임 하나\n")
    print("quiet 는 EventSourceResponse(15초마다 `: ping`), quiet-raw 는 keepalive 없는")
    print("대조군. 끝의 초는 요청을 보낸 때부터다.\n")
    limit = silence + 30

    async def one(variant: str, scheme: str, endpoint: str) -> list[str]:
        probe = probe_id("silence")
        target = f"/chat/{endpoint}?silence_s={silence}&probe={probe}"
        r = await exchange_over(ctx, scheme, port_of(scheme, variant), target, limit)
        seconds = (r.end_ms - r.started_ms) / 1000
        got = ",".join(str(f.seq) for f in r.frames) or "-"
        outcome = f"{r.end} {seconds:.1f}초"
        if r.error:
            outcome += f" ({r.error[:90]})"
        errors = ctx.nginx.errors_for(probe) or "-"
        return [variant, scheme, endpoint, got, str(len(r.pings)), outcome, errors]

    jobs = [
        one(variant, scheme, endpoint)
        for variant in ("a_default", "b_default", "b_h10", "b_h11")
        for scheme in ("http", "tls", "h2")
        for endpoint in ("quiet", "quiet-raw")
    ]
    rows = await asyncio.gather(*jobs)
    table(["변형", "방식", "엔드포인트", "받은 프레임", "ping", "끝", "nginx 오류 기록"], rows)


async def section_truncate(ctx: Context) -> None:
    print("### truncate: 상류가 응답 도중 죽을 때(프레임 2개 뒤 예외) 클라이언트가 아는가\n")
    print("broken 은 EventSourceResponse 생성기의 예외, broken-raw 는 uvicorn 이 연결을 그냥")
    print("닫는 것이다. 끝이 '끝남'이면 클라이언트에게 정상 종료로 보인 것이다(HTTP/1.1 의")
    print("마지막 청크나 h2 의 END_STREAM). '조기 종료'·'오류'는 잘림이 드러난 것이다.\n")
    variants = ("a_default", "a_h10", "a_h11", "b_default", "b_h10", "b_h11")

    async def one(label: str, scheme: str, port: int, endpoint: str) -> list[str]:
        probe = probe_id("truncate")
        r = await exchange_over(ctx, scheme, port, f"/chat/{endpoint}?after=2&probe={probe}", 15)
        outcome = r.end + (f" ({r.error[:90]})" if r.error else "")
        errors = ctx.nginx.errors_for(probe) or "-"
        return [label, scheme, endpoint, str(len(r.frames)), outcome, errors]

    endpoints = ("broken", "broken-raw")
    jobs = [one("파이썬 직접", "http", PY_PORT, e) for e in endpoints]
    jobs += [one("Next 직접", "http", NEXT_PORT, e) for e in endpoints]
    jobs += [
        one(variant, scheme, port_of(scheme, variant), endpoint)
        for variant in variants
        for scheme in ("http", "tls", "h2")
        for endpoint in endpoints
    ]
    rows = await asyncio.gather(*jobs)
    table(["변형", "방식", "엔드포인트", "받은 프레임", "끝", "nginx 오류 기록"], rows)


@dataclass
class Closed:
    variant: str
    closing: str
    kind: str
    probe: str
    close_ms: float
    received: int
    error: str = ""
    h2_client: H2Client | None = None


async def abort_case(ctx: Context, variant: str, closing: str, kind: str) -> Closed:
    """흐르는 중이면 3번째 프레임을 받자마자, 침묵 중이면 첫 프레임 뒤 2초 기다렸다 끊는다."""
    probe = probe_id("abort")
    if kind == "흐르는 중":
        target = f"/chat/stream?count=120&interval_ms=500&probe={probe}"
        needed, delay = 3, 0.0
    else:
        target = f"/chat/quiet?silence_s=120&probe={probe}"
        needed, delay = 1, 2.0
    if closing.startswith("h2"):
        return await abort_h2(ctx, variant, closing, kind, probe, target, needed, delay)
    scheme = "http" if closing == "평문 FIN" else "tls"
    cert = ctx.cert if scheme == "tls" else None
    reader, writer = await h1_connect(port_of(scheme, variant), cert)
    writer.write(h1_request("POST", target))
    await writer.drain()
    received = b""
    error = ""
    try:
        while received.count(b"data: ") < needed:
            chunk = await asyncio.wait_for(reader.read(65536), 30)
            if not chunk:
                error = "상류가 먼저 닫음"
                break
            received += chunk
    except TimeoutError:
        error = "30초 안에 프레임이 오지 않음"
    if delay:
        await asyncio.sleep(delay)
    close_ms = now_ms()
    if closing == "TLS 알림 없이":
        writer.transport.abort()
    else:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 5)
        except (OSError, TimeoutError, ssl.SSLError):
            pass
    return Closed(variant, closing, kind, probe, close_ms, received.count(b"data: "), error)


async def abort_h2(
    ctx: Context,
    variant: str,
    closing: str,
    kind: str,
    probe: str,
    target: str,
    needed: int,
    delay: float,
) -> Closed:
    client = await H2Client.start(port_of("h2", variant), target, ctx.cert)
    stream = H2Stream()
    exchange = stream.exchange
    error = ""
    deadline = time.monotonic() + 30
    try:
        while len(exchange.frames) < needed:
            message = await client.read(deadline - time.monotonic())
            if message is None or stream.apply(message):
                error = f"스트림이 먼저 끝남({exchange.end} {exchange.error})"
                break
    except TimeoutError:
        error = "30초 안에 프레임이 오지 않음"
    if delay:
        await asyncio.sleep(delay)
    command = "cancel" if closing == "h2 RST_STREAM" else "destroy"
    close_ms = await client.command(command)
    closed = Closed(variant, closing, kind, probe, close_ms, len(exchange.frames), error)
    closed.h2_client = client
    return closed


async def section_abort(ctx: Context) -> None:
    print("### abort: 클라이언트가 끊은 뒤 파이썬이 상류 연결의 끊김을 본 시간\n")
    print("흐르는 중: 500ms 간격 120개 중 3개를 받고 끊는다. 침묵 중: 첫 프레임 뒤 2초를")
    print("기다렸다 끊는다(파이썬의 다음 쓰기는 첫 프레임 15초 뒤의 ping 이다). 끊김은")
    print("sse_app.py 기록의 disconnect(응답을 다 보내기 전) 시각이다. h2 RST_STREAM 은")
    print("세션을 열어 둔 채 스트림만 닫는다. 30초 안에 프레임이 오지 않으면 그때 끊는다.\n")
    wait_s = 50.0
    cases = [
        (variant, closing, kind)
        for variant in ABORT_VARIANTS
        for closing in CLOSINGS
        for kind in ("흐르는 중", "침묵 중")
    ]
    closed = await asyncio.gather(*(abort_case(ctx, v, c, k) for v, c, k in cases))
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if all(ctx.pylog.disconnect(c.probe) is not None for c in closed):
            break
        await asyncio.sleep(1)
    for c in closed:
        if c.h2_client is not None:
            c.h2_client.kill()
    rows: list[list[str]] = []
    for c in closed:
        event = ctx.pylog.disconnect(c.probe)
        if event is None:
            seen, sent = f"{wait_s:.0f}초 안에 못 봄", "-"
        else:
            delay = max(0.0, float(str(event.get("t"))) - c.close_ms) / 1000
            seen = f"{delay:.2f}초"
            sent = f"프레임 {event.get('frames')}, ping {event.get('pings')}"
        received = f"{c.received}" + (f" ({c.error})" if c.error else "")
        errors = ctx.nginx.errors_for(c.probe) or "-"
        rows.append([c.variant, c.closing, c.kind, received, seen, sent, errors])
    headers = ["변형", "끊는 모양", "상황", "받은 프레임", "끊김을 본 시간", "파이썬이 보낸 것"]
    table([*headers, "nginx 오류 기록"], rows)


ALLOW_TARGETS: list[tuple[str, str]] = [
    ("/chat/x", "파이썬"),
    ("/widget", "위젯"),
    ("/widget/", "위젯"),
    ("@ASSET@", "위젯"),
    ("/plugins", "차단"),
    ("/traces", "차단"),
    ("/runs", "차단"),
    ("/health", "차단"),
    ("/openapi.json", "차단"),
    ("/", "차단"),
    ("/chat", "차단"),
    ("/chatx", "차단"),
    ("/chatx/x", "차단"),
    ("/widgetx", "차단"),
    ("/_next/static/x.js", "차단"),
    ("/chat/../plugins", "차단"),
    ("/chat/%2e%2e/plugins", "차단"),
    ("/chat/%2E%2E/plugins", "차단"),
    ("/chat/x/../../plugins", "차단"),
    ("/chat/../../plugins", "차단"),
    ("/chat%2f..%2fplugins", "차단"),
    ("//plugins", "차단"),
    ("/./plugins", "차단"),
    ("/widget/../plugins", "차단"),
    ("/widget/%2e%2e/runs", "차단"),
    ("http://localhost/plugins", "차단"),
    ("/Chat/../plugins", "차단"),
    ("/chat/..%2fplugins", "경계"),
    ("/chat/%2e%2e%2fplugins", "경계"),
    ("/chat/%252e%252e/plugins", "경계"),
    ("/chat/..\\plugins", "경계"),
    ("/chat/..%5cplugins", "경계"),
    ("/CHAT/x", "경계"),
]


async def allow_one(ctx: Context, variant: str, scheme: str, target: str, expect: str) -> list[str]:
    probe = probe_id("allow")
    joiner = "&" if "?" in target else "?"
    full = f"{target}{joiner}probe={probe}"
    cert = ctx.cert if scheme == "tls" else None
    r = await h1(port_of(scheme, variant), full, cert=cert, method="GET", sse=False, limit_s=10)
    seen = [e for e in ctx.pylog.events(probe) if e.get("event") == "request"]
    upstream = r.headers.get("x-probe-upstream", "")
    if seen:
        who = "파이썬" + (" (Next 경유)" if upstream.endswith(f":{NEXT_PORT}") else "")
    elif upstream.endswith(f":{NEXT_PORT}"):
        who = "Next"
    elif upstream:
        who = f"상류 {upstream}"
    elif r.body.startswith(b"nginx-allowlist: blocked"):
        who = "nginx 허용 목록"
    elif r.status:
        who = "nginx"
    else:
        who = f"? ({r.end} {r.error})"
    py_path = ", ".join(f"{e.get('path')} ({e.get('raw_path')})" for e in seen) or "-"
    py_outside = any(not str(e.get("path", "")).startswith("/chat/") for e in seen)
    if expect == "파이썬":
        ok = bool(seen) and r.status == 200 and not py_outside
    elif expect == "위젯":
        ok = who == "Next" and r.status in (200, 308)
    elif expect == "차단":
        ok = not seen and not upstream
    else:
        ok = not py_outside
    location = r.headers.get("location", "-")
    verdict = "기대대로" if ok else "어긋남"
    return [target, str(r.status), who, py_path, location, expect, verdict]


async def section_allow(ctx: Context) -> None:
    print("### allow: 허용 목록 후보에 요청 줄을 글자 그대로 보낸다\n")
    print("GET 이고 리다이렉트를 따르지 않는다. 답한 곳: 파이썬(기록에 probe 가 남음), Next")
    print("(X-Probe-Upstream 이 Next 포트), nginx(그 헤더가 없음. 허용 목록의 404 이거나 nginx")
    print("자신의 3xx·400). 경계는 상류에 닿아도 되지만 파이썬이 본 경로가 /chat/ 밖이면")
    print("어긋남이다.\n")
    page = await h1(port_of("http", "a_default"), "/widget", cert=None, method="GET", sse=False)
    assets = re.findall(r'"(/widget/_next/static/[^"]+?\.js)"', page.body.decode(errors="replace"))
    asset = assets[0] if assets else "/widget/_next/static/없음.js"
    for variant in ("a_default", "b_default"):
        rows: list[list[str]] = []
        differs: list[str] = []
        for raw, expect in ALLOW_TARGETS:
            target = asset if raw == "@ASSET@" else raw
            row = await allow_one(ctx, variant, "http", target, expect)
            tls_row = await allow_one(ctx, variant, "tls", target, expect)
            if row[1:3] + row[5:] != tls_row[1:3] + tls_row[5:]:
                differs.append(target)
            rows.append(row)
        same = "모두 같다" if not differs else f"다른 대상: {', '.join(differs)}"
        print(f"#### {variant} (평문. TLS 와 상태·답한 곳·판정이 {same})\n")
        headers = ["요청 대상", "상태", "답한 곳", "파이썬이 본 경로(raw)", "Location", "기대"]
        table([*headers, "판정"], rows)
    print("#### 슬래시 함정: w_slash_only(위치가 /widget/ 하나) 와 a_default 의 리다이렉트\n")
    rows = []
    for variant in ("w_slash_only", "a_default"):
        for target in ("/widget", "/widget/"):
            r = await h1(port_of("http", variant), target, cert=None, method="GET", sse=False)
            upstream = r.headers.get("x-probe-upstream", "")
            who = "Next" if upstream.endswith(f":{NEXT_PORT}") else "nginx"
            rows.append([variant, target, str(r.status), who, r.headers.get("location", "-")])
    table(["변형", "요청 대상", "상태", "답한 곳", "Location"], rows)


SECTIONS = {
    "headers": section_headers,
    "stream": section_stream,
    "silence": section_silence,
    "truncate": section_truncate,
    "abort": section_abort,
    "allow": section_allow,
}


# ---------- 본체 ----------


def versions(next_app: Path) -> list[str]:
    lines = [f"Python {sys.version.split()[0]}"]
    for dist in ("fastapi", "starlette", "uvicorn", "h11"):
        lines.append(f"{dist} {importlib.metadata.version(dist)}")
    package = json.loads((next_app / "node_modules/next/package.json").read_text("utf-8"))
    node = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout
    lines.append(f"next {package['version']}, node {node.strip()}")
    return lines


async def start_next(next_app: Path, work: Path) -> subprocess.Popen[bytes]:
    next_bin = str(next_app / "node_modules/next/dist/bin/next")
    env = {"PROBE_UPSTREAM": f"http://127.0.0.1:{PY_PORT}", "NEXT_TELEMETRY_DISABLED": "1"}
    build = subprocess.run(
        ["node", next_bin, "build"], cwd=next_app, env={**os.environ, **env}, capture_output=True
    )
    if build.returncode != 0:
        output = build.stdout.decode(errors="replace") + build.stderr.decode(errors="replace")
        raise RuntimeError(f"next build 실패:\n{output}")
    start = ["node", next_bin, "start", "-H", "127.0.0.1", "-p", str(NEXT_PORT)]
    proc = spawn(start, work / "next.log", cwd=next_app, env=env)
    await wait_port(NEXT_PORT, proc)
    return proc


async def run(args: argparse.Namespace) -> int:
    sections: list[str] = args.sections.split(",")
    work = Path(tempfile.mkdtemp(prefix="nginx-relay-", dir=args.work))
    cert, key = make_cert(work)
    pylog = PythonLog(work / "python.jsonl")
    next_app: Path = args.next_app
    print("## 판\n")
    for line in versions(next_app):
        print(f"- {line}")
    print(f"- 작업 폴더 {work}\n")
    procs: list[subprocess.Popen[bytes]] = []
    try:
        app = [sys.executable, str(HERE / "sse_app.py"), str(PY_PORT), str(pylog.path)]
        python = spawn(app, work / "py.log")
        procs.append(python)
        await wait_port(PY_PORT, python)
        procs.append(await start_next(next_app, work))
        for index, exe in enumerate(args.nginx):
            prefix = work / f"nginx-{index}"
            render_conf(prefix, cert, key)
            nginx = Nginx(Path(exe), prefix)
            print(f"## {nginx.version()}\n")
            print("```\n" + nginx.test() + "\n```\n")
            ctx = Context(cert, nginx, pylog, args.silence_s)
            await nginx.start()
            try:
                for name in sections:
                    await SECTIONS[name](ctx)
            finally:
                nginx.stop()
    finally:
        for proc in reversed(procs):
            kill_tree(proc)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nginx", action="append", required=True)
    parser.add_argument("--next-app", type=Path, required=True)
    parser.add_argument("--sections", default=",".join(SECTIONS))
    parser.add_argument("--silence-s", type=float, default=90)
    # 인증서·nginx prefix·기록이 생기는 곳. 없으면 시스템 임시 폴더다. 지우지 않고 남긴다.
    parser.add_argument("--work", type=Path)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
