// web-admin 프로브의 상류 서버. 파이썬 채널의 SSE 흉내만 낸다(인증·CORS 없음).
//   node next_sse_upstream.mjs [port] [host]     기본 8765, 127.0.0.1
// 경로:
//   /sse-gap  이벤트 하나, ?gap=ms 동안 침묵(?ping=ms면 그 간격으로 `: ping`), 이벤트 하나
//   /sse-nt   /sse와 같되 Cache-Control에 no-transform을 더한다
//   /sse...   어느 메서드든 text/event-stream으로 `data:` 한 줄을 500ms마다 10번 내고 닫는다.
//             응답 헤더는 FastAPI EventSourceResponse의 것(Cache-Control: no-cache, X-Accel-Buffering: no)
//   /echo...  받은 메서드·경로·헤더를 JSON으로 돌려준다(OPTIONS 포함, 상태 200)
//   /big      8KB JSON(압축 문턱 1KB를 넘는 보통 응답)
//   그 밖     404
// 받은 요청마다 표준 출력에 JSON 한 줄을 남긴다(메서드, 경로, 헤더).
import http from "node:http";

const port = Number(process.argv[2] ?? 8765);
const host = process.argv[3] ?? "127.0.0.1";
const COUNT = 10;
const INTERVAL_MS = 500;

const server = http.createServer((req, res) => {
  const seen = { t: Date.now(), method: req.method, url: req.url, headers: req.headers };
  console.log(JSON.stringify(seen));
  const path = (req.url ?? "/").split("?")[0];

  if (path.startsWith("/echo")) {
    // 본문은 읽고 버린다(POST가 끝까지 오게)
    req.resume();
    req.on("end", () => {
      const body = JSON.stringify({ upstream: true, method: req.method, url: req.url, headers: req.headers });
      res.writeHead(200, { "content-type": "application/json", "content-length": Buffer.byteLength(body) });
      res.end(body);
    });
    return;
  }

  if (path.startsWith("/big")) {
    req.resume();
    const body = JSON.stringify({ upstream: true, filler: "x".repeat(8192) });
    res.writeHead(200, { "content-type": "application/json", "content-length": Buffer.byteLength(body) });
    res.end(body);
    return;
  }

  if (path.startsWith("/sse-gap")) {
    // 이벤트 하나, gap ms 동안 침묵(ping>0이면 그 간격으로 `: ping` 주석), 이벤트 하나, 닫기.
    // FastAPI의 EventSourceResponse는 15초 침묵마다 `: ping`을 넣는다(fastapi/sse.py _PING_INTERVAL).
    req.resume();
    const q = new URL(req.url ?? "/", "http://x").searchParams;
    const gap = Number(q.get("gap") ?? 35000);
    const ping = Number(q.get("ping") ?? 0);
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache" });
    res.write(`data: {"seq":1,"sent_ms":${Date.now()}}\n\n`);
    const pinger = ping > 0 ? setInterval(() => res.write(": ping\n\n"), ping) : undefined;
    const last = setTimeout(() => {
      if (pinger) clearInterval(pinger);
      res.end(`data: {"seq":2,"sent_ms":${Date.now()}}\n\n`);
    }, gap);
    res.on("close", () => {
      if (pinger) clearInterval(pinger);
      clearTimeout(last);
      console.log(JSON.stringify({ t: Date.now(), closed: req.url, finished: res.writableFinished }));
    });
    return;
  }

  if (path.startsWith("/sse")) {
    req.resume();
    res.writeHead(200, {
      "content-type": "text/event-stream",
      "cache-control": path.startsWith("/sse-nt") ? "no-cache, no-transform" : "no-cache",
      "x-accel-buffering": "no",
      connection: "keep-alive",
    });
    // FastAPI의 EventSourceResponse처럼 헤더를 먼저 보내고 첫 줄은 바로 낸다
    res.flushHeaders();
    let i = 0;
    const send = () => {
      i += 1;
      res.write(`data: {"seq":${i},"sent_ms":${Date.now()}}\n\n`);
      if (i >= COUNT) {
        clearInterval(timer);
        res.end();
      }
    };
    send();
    const timer = setInterval(send, INTERVAL_MS);
    res.on("close", () => {
      clearInterval(timer);
      // 다 보내기 전에 닫혔으면(finished=false) 아래로 끊김이 전해진 것이다
      console.log(JSON.stringify({ t: Date.now(), closed: req.url, finished: res.writableFinished, sent: i }));
    });
    return;
  }

  res.writeHead(404, { "content-type": "text/plain" });
  res.end("not found");
});

server.listen(port, host, () => {
  console.error(`upstream listening on http://${host}:${port}`);
});
