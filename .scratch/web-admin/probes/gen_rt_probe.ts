// gen_run.mjs 가 작업 디렉터리의 probe/rt.ts 로 복사해 esbuild 로 묶어 돌린다. 혼자 돌지 않는다.
// 루프백 스텁 서버 하나를 띄우고, 세 클라이언트가 POST /runs 의 SSE 200 과 409 봉투를
// 실제로 어떻게 다루는지 잰다. 스텁은 agent 이름으로 갈린다: off* 는 409 봉투, drop 은 이벤트 하나 뒤
// 소켓을 끊고, 나머지는 이벤트 둘을 보내고 닫는다. 이름마다 받은 POST 수를 센다.
import http from "node:http";
import type { AddressInfo } from "node:net";
import createClient from "openapi-fetch";
import type { paths } from "../out/ots/v31";
import { startRun as heyStartRun } from "../out/hey/v31";
import { client as heyClient } from "../out/hey/v31/client.gen";
import { startRun as orvalStartRun } from "../out/orval-fetch/v32/api";

const WINDOW_MS = 8000;
const hits: Record<string, number> = {};
const ev = (type: string) =>
  JSON.stringify({ type, run_id: "r1", ts: "2026-09-28T00:00:00Z", agent: "a", request: "hi", principal: "p" });
const server = http.createServer((req, res) => {
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    const agent = (JSON.parse(body || "{}") as { agent?: string }).agent ?? "";
    hits[agent] = (hits[agent] ?? 0) + 1;
    if (agent.startsWith("off")) {
      res.writeHead(409, { "content-type": "application/json" });
      res.end(JSON.stringify({ code: "conflict", message: "off", request_id: "x", violations: [] }));
      return;
    }
    res.writeHead(200, { "content-type": "text/event-stream" });
    res.write(`data: ${ev("run_started")}\n\n`);
    if (agent === "drop") {
      setTimeout(() => res.socket?.destroy(), 50);
      return;
    }
    res.write(`data: ${ev("run_finished")}\n\n`);
    res.end();
  });
});
await new Promise<void>((r) => server.listen(0, "127.0.0.1", () => r()));
const base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
// orval 의 fetch 는 상대 경로("/runs")로 부른다. 스텁의 주소를 앞에 붙인다.
const realFetch = globalThis.fetch;
globalThis.fetch = (input: RequestInfo | URL, init?: RequestInit) =>
  realFetch(typeof input === "string" && input.startsWith("/") ? base + input : input, init);

const out: Record<string, unknown> = {};
const tryit = async (k: string, f: () => Promise<unknown>) => {
  try {
    out[k] = await f();
  } catch (e) {
    out[k] = `THREW ${(e as Error).name}: ${(e as Error).message.slice(0, 80)}`;
  }
};

const ofc = createClient<paths>({ baseUrl: base });
await tryit("openapi-fetch 기본 parseAs, 200", async () => {
  const r = await ofc.POST("/runs", { body: { agent: "ok-ofetch", request: "x" } });
  return { data: r.data, error: r.error };
});
await tryit("openapi-fetch parseAs=stream, 200", async () => {
  const r = await ofc.POST("/runs", { body: { agent: "ok-ofetch-stream", request: "x" }, parseAs: "stream" });
  return (await new Response(r.data ?? null).text()).slice(0, 40);
});
await tryit("openapi-fetch 409", async () => {
  const r = await ofc.POST("/runs", { body: { agent: "off-ofetch", request: "x" } });
  return { status: r.response.status, error: r.error };
});

heyClient.setConfig({ baseUrl: base });
const heyCollect = async (agent: string) => {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), WINDOW_MS);
  const items: string[] = [];
  const r = await heyStartRun({ body: { agent, request: "x" }, signal: ac.signal, onSseError: () => {} });
  for await (const item of r.stream) {
    items.push(
      typeof item === "object" && item !== null ? `object type=${(item as { type?: string }).type}` : typeof item,
    );
  }
  clearTimeout(t);
  return { items, posts: hits[agent] };
};
await tryit("hey sse 200", () => heyCollect("ok-hey"));
await tryit(`hey sse 409 (${WINDOW_MS}ms 창)`, () => heyCollect("off-hey"));
await tryit(`hey sse 스트림 중간 끊김 (${WINDOW_MS}ms 창)`, () => heyCollect("drop"));

await tryit("orval fetch 200", async () => {
  const r = await orvalStartRun({ agent: "ok-orval", request: "x" });
  return { status: r.status, data: r.data };
});
await tryit("orval fetch 409", async () => {
  const r = await orvalStartRun({ agent: "off-orval", request: "x" });
  return { status: r.status, data: r.data };
});

server.close();
console.log(JSON.stringify(out));
