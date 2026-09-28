// web-admin 프로브의 SSE 클라이언트. node:http로 부르므로 Accept-Encoding을 스스로 붙이지 않고
// 압축을 풀지도 않는다(fetch/undici는 둘 다 한다). 청크가 소켓에서 올라온 시각을 요청 시작 기준 ms로 찍는다.
//   node next_sse_client.mjs <url> [--ae <Accept-Encoding 값>] [--method POST] [--header "k: v"]... [--json]
// --ae     Accept-Encoding에 넣을 값(예: gzip, "gzip, deflate, br, zstd"). 없으면 보내지 않는다.
//          응답이 gzip·br·deflate면 풀어서 `data:` 줄이 풀려 나온 시각을 찍는다
// --json   마지막에 요약 JSON 한 줄만 낸다
// POST 등 본문이 있는 메서드는 브라우저 fetch처럼 content-length를 붙여 `{}`를 보낸다. 길이 없이 보내면
// node:http는 chunked로 보내고, 그 헤더를 그대로 넘긴 route handler의 fetch(undici)는
// invalid transfer-encoding으로 실패한다(next_measure.mjs headers 섹션이 잰다).
import http from "node:http";
import zlib from "node:zlib";

function parseArgs(argv) {
  const out = { url: undefined, acceptEncoding: undefined, method: "GET", headers: {}, json: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--ae") out.acceptEncoding = argv[++i];
    else if (a === "--json") out.json = true;
    else if (a === "--method") out.method = argv[++i];
    else if (a === "--header") {
      const h = argv[++i];
      const k = h.slice(0, h.indexOf(":")).trim();
      out.headers[k] = h.slice(h.indexOf(":") + 1).trim();
    } else out.url = a;
  }
  return out;
}

function decoderFor(encoding) {
  if (encoding === "gzip") return zlib.createGunzip();
  if (encoding === "br") return zlib.createBrotliDecompress();
  if (encoding === "deflate") return zlib.createInflate();
  return undefined;
}

export function measure({ url, acceptEncoding, method = "GET", headers = {}, timeoutMs = 15000 }) {
  return new Promise((resolve) => {
    const t0 = performance.now();
    const ms = () => Math.round(performance.now() - t0);
    const reqHeaders = { accept: "text/event-stream", ...headers };
    if (acceptEncoding !== undefined) reqHeaders["accept-encoding"] = acceptEncoding;
    const body = method === "GET" || method === "HEAD" ? undefined : "{}";
    if (body !== undefined) {
      reqHeaders["content-type"] ??= "application/json";
      reqHeaders["content-length"] = String(Buffer.byteLength(body));
    }
    const result = { url, method, acceptEncoding, status: null, headers: {}, chunks: [], events: [], error: null, total_ms: null };
    const req = http.request(url, { method, headers: reqHeaders }, (res) => {
      result.status = res.statusCode;
      result.headers = res.headers;
      result.headers_ms = ms();
      const ce = res.headers["content-encoding"];
      const decoder = decoderFor(ce);
      if (ce && !decoder) result.error = `풀 수 없는 content-encoding ${ce}`;
      let text = "";
      const onText = (s) => {
        text += s;
        let idx;
        while ((idx = text.indexOf("\n")) >= 0) {
          const line = text.slice(0, idx);
          text = text.slice(idx + 1);
          if (line.startsWith("data:")) result.events.push({ at_ms: ms(), line: line.slice(0, 60) });
        }
      };
      if (decoder) {
        decoder.on("data", (d) => onText(d.toString("utf8")));
        decoder.on("error", (e) => {
          result.error = `decode: ${e.message}`;
        });
      }
      res.on("data", (chunk) => {
        result.chunks.push({ at_ms: ms(), bytes: chunk.length });
        if (decoder) decoder.write(chunk);
        else onText(chunk.toString("utf8"));
      });
      res.on("end", () => {
        const finish = () => {
          result.total_ms = ms();
          resolve(result);
        };
        if (decoder) decoder.end(finish);
        else finish();
      });
      // 응답이 시작된 뒤 연결이 끊기면 req가 아니라 res에 'error'(aborted)가 온다. end 없이 닫히면 끊긴 것이다
      res.on("error", (e) => {
        result.error ??= `응답 중 끊김: ${e.message}`;
      });
      res.on("close", () => {
        if (!res.complete) {
          result.error ??= "응답 중 끊김";
          result.total_ms = ms();
          resolve(result);
        }
      });
    });
    req.setTimeout(timeoutMs, () => {
      result.error = "timeout";
      req.destroy();
      resolve(result);
    });
    req.on("error", (e) => {
      result.error = e.message;
      resolve(result);
    });
    req.end(body);
  });
}

// 도착 시각 열을 한 줄로 줄인다. 10개가 3.5초 넘게 퍼져 오면 "스트리밍", 0.3초 안에 몰리면 "몰림"
export function verdict(r) {
  const at = r.events.map((e) => e.at_ms);
  if (r.error || at.length === 0) return `오류(${r.error ?? "이벤트 0"}) 상태 ${r.status}`;
  const spread = at[at.length - 1] - at[0];
  const kind = at.length >= 10 && spread >= 3500 ? "스트리밍" : spread < 300 ? "몰림" : "부분";
  return `${kind} 이벤트 ${at.length}개, 첫 ${at[0]}ms 끝 ${at[at.length - 1]}ms, 소켓 청크 ${r.chunks.length}개`;
}

if (process.argv[1]?.endsWith("next_sse_client.mjs")) {
  const args = parseArgs(process.argv.slice(2));
  if (!args.url) {
    console.error("usage: node next_sse_client.mjs <url> [--ae <value>] [--method M] [--header 'k: v'] [--json]");
    process.exit(2);
  }
  const r = await measure(args);
  if (args.json) {
    console.log(JSON.stringify(r));
  } else {
    console.log(
      `status ${r.status}, content-type ${r.headers["content-type"]}, content-encoding ${r.headers["content-encoding"] ?? "-"}, transfer-encoding ${r.headers["transfer-encoding"] ?? "-"}`,
    );
    for (const c of r.chunks) console.log(`  chunk @${c.at_ms}ms ${c.bytes}B`);
    for (const e of r.events) console.log(`  event @${e.at_ms}ms ${e.line}`);
    console.log(verdict(r));
  }
}
