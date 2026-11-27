// 컨테이너 안에서 요청 하나를 걸고 본 것을 JSON 한 줄로 찍는다. 프로브(run.py)가 docker exec 로 부른다. 선례는
// .scratch/release-image/probes/web_images/fetch.mjs 이고, 본문을 그대로 싣는 --body 를 더하고 --stream 을 뺐다.
//
// 사용: node fetch.mjs <url> [--body] [--header <이름: 값>]... [--timeout <ms>] [--deadline <ms>]
// 찍는 것: 상태, 응답 머리(소문자 이름), 본문 길이, 본문 sha256, 걸린 시간. --body 면 본문의 글(4096바이트까지)도 싣는다.
// 연결하지 못하면 {"error": "<코드>"} 를 찍는다. 종료 코드는 늘 0 이다(판정은 프로브가 한다).
// --timeout 은 소켓이 그만큼 조용할 때만 끊는 비활성 기한이고, --deadline 은 요청 전체의 기한이다(기본 40000, 부르는
// run.py 의 docker exec 제한 60초보다 짧다). 닿으면 {"error": "deadline"} 을 찍는다.

import { createHash } from "node:crypto";
import http from "node:http";
import { parseArgs } from "node:util";

const BODY_LIMIT = 4096;
const { values, positionals } = parseArgs({
  options: {
    body: { type: "boolean", default: false },
    header: { type: "string", multiple: true, default: [] },
    timeout: { type: "string", default: "10000" },
    deadline: { type: "string", default: "40000" },
  },
  allowPositionals: true,
});
const [url] = positionals;
if (url === undefined) {
  console.error("사용: node fetch.mjs <url> [--body]");
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
  let timer;
  const finish = (value) => {
    clearTimeout(timer);
    resolve(value);
  };
  const request = http.get(url, { agent: false, headers, timeout: Number(values.timeout) }, (response) => {
    const chunks = [];
    response.on("data", (chunk) => chunks.push(chunk));
    response.on("end", () => {
      const body = Buffer.concat(chunks);
      finish({
        status: response.statusCode ?? 0,
        headers: response.headers,
        length: body.length,
        sha256: createHash("sha256").update(body).digest("hex"),
        ...(values.body ? { body: body.subarray(0, BODY_LIMIT).toString("utf-8") } : {}),
      });
    });
    response.on("error", (error) => finish({ error: error.code ?? error.message }));
  });
  request.on("timeout", () => request.destroy(new Error("timeout")));
  request.on("error", (error) => finish({ error: error.code ?? error.message }));
  timer = setTimeout(() => {
    finish({ error: "deadline" });
    request.destroy(new Error("deadline"));
  }, Number(values.deadline));
});

console.log(JSON.stringify({ url, ms: Math.round(performance.now() - started), ...result }));
