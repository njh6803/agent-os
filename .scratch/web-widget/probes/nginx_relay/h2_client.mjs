// nginx 중계 측정의 HTTP/2 클라이언트. measure.py 가 띄우고 표준 입출력으로 부린다.
//   node h2_client.mjs <port> <path> <ca.pem>
//
// https://127.0.0.1:<port> 에 POST <path>(본문 {}, Accept-Encoding: gzip, deflate, br)를 하나 보낸다.
// 표준 출력에 JSON 한 줄씩 낸다. t 는 이 프로세스가 찍은 epoch 밀리초다(파이프 지연을 빼려고).
//   {"type":"headers","headers":{...}}   응답 헤더
//   {"type":"data","b64":"..."}          받은 DATA 그대로(압축이면 압축된 채). 푸는 것은 measure.py 다
//   {"type":"end"} | {"type":"error","message":...}
//   {"type":"cancelled"} | {"type":"destroyed"}
// 표준 입력의 명령 한 줄
//   cancel   그 스트림만 RST_STREAM(CANCEL)로 닫는다. 세션(TCP·TLS)은 열어 둔다. 브라우저가 h2 위의
//            EventSource 를 닫거나 fetch 를 abort 하는 모양이다
//   destroy  세션째 소켓을 닫는다
// end·error 뒤에는 스스로 끝난다. cancel·destroy 뒤에는 measure.py 가 거둘 때까지 산다.
import { readFileSync } from "node:fs";
import http2 from "node:http2";
import readline from "node:readline";

const [port, path, ca] = process.argv.slice(2);
const out = (message) => process.stdout.write(`${JSON.stringify({ t: Date.now(), ...message })}\n`);

const session = http2.connect(`https://127.0.0.1:${port}`, { ca: readFileSync(ca), servername: "localhost" });
session.on("error", (error) => out({ type: "error", message: String(error) }));

const request = session.request({
  ":method": "POST",
  ":path": path,
  "content-type": "application/json",
  accept: "text/event-stream",
  "accept-encoding": "gzip, deflate, br",
});
request.end("{}");

let settled = false;
request.on("response", (headers) => out({ type: "headers", headers }));
request.on("data", (chunk) => out({ type: "data", b64: chunk.toString("base64") }));
request.on("end", () => {
  if (settled) return;
  settled = true;
  out({ type: "end" });
  session.close();
  process.exit(0);
});
request.on("error", (error) => {
  if (settled) return;
  settled = true;
  out({ type: "error", message: String(error) });
  session.destroy();
  process.exit(0);
});

readline.createInterface({ input: process.stdin }).on("line", (line) => {
  const command = line.trim();
  if (command === "cancel") {
    settled = true;
    request.close(http2.constants.NGHTTP2_CANCEL);
    out({ type: "cancelled" });
  } else if (command === "destroy") {
    settled = true;
    session.destroy();
    out({ type: "destroyed" });
  }
});
