// 컨테이너 안에서 요청 하나를 걸고 본 것을 JSON 한 줄로 찍는다. 프로브(run.py)가 docker exec 로 부른다.
//
// 사용: node fetch.mjs <url> [--needle <글>]... [--header <이름: 값>]... [--timeout <ms>] [--deadline <ms>] [--stream]
// 찍는 것: 상태, 응답 헤더(소문자 이름), 본문 길이, 본문 sha256, needle 마다 본문에 그 글이 있는지, 걸린 시간.
// --stream 이면 본문 조각이 도착한 시각(요청을 건 뒤 ms)과 조각의 글을 함께 찍는다(SSE 가 생기는 대로 흐르는지 본다).
// 연결하지 못하면 {"error": "<코드>"} 를 찍는다. 종료 코드는 늘 0 이다(판정은 프로브가 한다).
// --timeout 은 소켓이 그만큼 조용할 때만 끊는 비활성 기한이라, 조각이 계속 오는 응답은 끊지 못한다. --deadline 은 요청
// 전체의 기한이다(기본 40000, 부르는 run.py 의 docker exec 제한 60초보다 짧다). 닿으면 그때까지 본 것을
// {"error": "deadline", "partial": {...}} 로 찍는다. partial 안의 값은 맨 위 칸(status, needles)이 아니어서 프로브가
// 표지로 읽지 않는다(그 회차는 측정이 아니다).

import { createHash } from "node:crypto";
import http from "node:http";
import { parseArgs } from "node:util";

const { values, positionals } = parseArgs({
  options: {
    needle: { type: "string", multiple: true, default: [] },
    header: { type: "string", multiple: true, default: [] },
    timeout: { type: "string", default: "10000" },
    deadline: { type: "string", default: "40000" },
    stream: { type: "boolean", default: false },
  },
  allowPositionals: true,
});
const [url] = positionals;
if (url === undefined) {
  console.error("사용: node fetch.mjs <url> [--needle <글>]...");
  process.exit(2);
}
const headers = Object.fromEntries(
  values.header.map((line) => {
    const mark = line.indexOf(":");
    return [line.slice(0, mark).trim(), line.slice(mark + 1).trim()];
  }),
);
const started = performance.now();

const result = await new Promise((resolve) => {
  // 응답을 받기 시작한 뒤 그때까지 본 것을 내는 함수. 받기 전이면 null.
  let observed = () => null;
  let timer;
  const finish = (value) => {
    clearTimeout(timer);
    resolve(value);
  };
  const request = http.get(
    url,
    { agent: false, headers, timeout: Number(values.timeout) },
    (response) => {
      const chunks = [];
      const arrivals = [];
      observed = () => {
        const body = Buffer.concat(chunks);
        const text = body.toString("utf-8");
        return {
          status: response.statusCode ?? 0,
          headers: response.headers,
          length: body.length,
          sha256: createHash("sha256").update(body).digest("hex"),
          needles: Object.fromEntries(values.needle.map((needle) => [needle, text.includes(needle)])),
          ...(values.stream ? { arrivals } : {}),
        };
      };
      response.on("data", (chunk) => {
        chunks.push(chunk);
        if (values.stream) {
          arrivals.push({ ms: Math.round(performance.now() - started), text: chunk.toString("utf-8") });
        }
      });
      response.on("end", () => finish(observed()));
      response.on("error", (error) => finish({ error: error.code ?? error.message }));
    },
  );
  request.on("timeout", () => request.destroy(new Error("timeout")));
  request.on("error", (error) => finish({ error: error.code ?? error.message }));
  timer = setTimeout(() => {
    finish({ error: "deadline", partial: observed() });
    request.destroy(new Error("deadline"));
  }, Number(values.deadline));
});

console.log(JSON.stringify({ url, ms: Math.round(performance.now() - started), ...result }));
