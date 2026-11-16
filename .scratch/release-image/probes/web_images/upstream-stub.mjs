// 관리 화면의 상류(serve) 자리에 서는 가짜 서버. 누가 답했는지 가르는 표지(token)를 본문에 싣는다.
//
// 사용: node upstream-stub.mjs <host> <port> <token>
//   GET /ping     {"stub": "<token>", "path": "/ping", "authorization": "<받은 Authorization 헤더 또는 null>"}
//   GET /sse      text/event-stream 으로 이벤트 넷을 0.4초 간격으로 낸다(data: <token>-<n>)
//   GET /hits     {"stub": "<token>", "seen": ["<받은 경로>", ...]} (/hits 자신은 세지 않는다)
// 듣기 시작하면 "RI_PROBE stub-listening <host>:<port> <token>" 을 찍는다. SIGTERM 에 바로 끝난다.

import http from "node:http";

const [host, port, token] = process.argv.slice(2);
if (host === undefined || port === undefined || token === undefined) {
  console.error("사용: node upstream-stub.mjs <host> <port> <token>");
  process.exit(2);
}

// 받은 요청의 경로(질의 포함). /hits 로 읽는다. 다른 컨테이너의 중계가 실제로 이 서버에 닿았는지(또는 닿지 않았는지)를
// 응답 본문이 아니라 이 서버가 받은 쪽에서 보려는 것이다.
const seen = [];

const server = http.createServer((request, response) => {
  if (request.url === "/hits") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ stub: token, seen }));
    return;
  }
  seen.push(request.url);
  if (request.url === "/sse") {
    response.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" });
    let sent = 0;
    const timer = setInterval(() => {
      sent += 1;
      response.write(`data: ${token}-${sent}\n\n`);
      if (sent === 4) {
        clearInterval(timer);
        response.end();
      }
    }, 400);
    response.on("close", () => clearInterval(timer));
    return;
  }
  response.writeHead(200, { "Content-Type": "application/json" });
  response.end(
    JSON.stringify({
      stub: token,
      path: request.url,
      authorization: request.headers.authorization ?? null,
    }),
  );
});
server.listen(Number(port), host, () => {
  console.log(`RI_PROBE stub-listening ${host}:${port} ${token}`);
});
process.on("SIGTERM", () => process.exit(0));
