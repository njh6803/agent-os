// 위젯 테스트 페이지 서버 대역(`portal_stub.mjs`)에 요청을 보내고 요청마다 걸린 시간과 표지를 적는다. 의존성이 없다.
// `run.py` 가 계획 파일을 써서 띄운다: node loadgen.mjs <계획.json>
//
// 계획: { target, out, steps: [...] }. 단계의 종류는 셋이다.
// - rr: 동시 1. 요청 하나마다 갈래를 바꿔 가며(시작 갈래도 돌려 가며) 갈래마다 count 번 보낸다. PC 의 잡음이 한 갈래에
//   쏠리지 않게 하려는 것이다.
// - chunks: 동시 concurrency. 갈래마다 chunk 개씩 묶어 번갈아 보내 갈래마다 count 번이 되게 한다. 한 묶음 안의 요청은
//   모두 같은 갈래라, 대역이 그 갈래의 동시 요청을 받는다.
// - paced: 동시 1. gap_ms 를 쉴 때마다 갈래마다 하나씩 보낸다(첫 요청 앞에는 lead_ms 를 쉰다). prelude 를 주면 쉰 뒤
//   새 연결로 그 갈래를 먼저 한 번 보내고 `warmup: true` 로 적는다.
// warmup 을 주면 재기 전에 갈래마다 그만큼 먼저 보내고 `warmup: true` 로 적는다(통계에서 뺀다).
//
// 걸린 시간은 요청을 쓰기 시작한 때부터 답의 본문을 다 읽은 때까지다(`performance.now()`). 이 프로세스와 대역 사이의
// 연결은 이어 쓴다(keepAlive). 기록은 끝에 out 파일에 한 줄에 하나씩 JSON 으로 쓴다.

import { readFileSync, writeFileSync } from "node:fs";
import { Agent, request as httpRequest } from "node:http";

const planPath = process.argv[2];
if (planPath === undefined) {
  console.error("사용: node loadgen.mjs <계획.json>");
  process.exit(2);
}
const plan = JSON.parse(readFileSync(planPath, "utf8"));
const origin = performance.now();
const records = [];

function parseProbe(raw) {
  if (typeof raw !== "string") return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function get(agent, url, timeoutMs) {
  return new Promise((resolve) => {
    const started = performance.now();
    const fail = (error) => {
      resolve({
        ms: performance.now() - started,
        status: null,
        bytes: 0,
        probe: null,
        client_error: { name: error?.name ?? "unknown", code: error?.code ?? null },
      });
    };
    const outgoing = httpRequest(url, { agent, method: "GET" }, (incoming) => {
      let bytes = 0;
      incoming.on("data", (chunk) => {
        bytes += chunk.length;
      });
      incoming.on("error", fail);
      incoming.on("end", () => {
        resolve({
          ms: performance.now() - started,
          status: incoming.statusCode ?? null,
          bytes,
          probe: parseProbe(incoming.headers["x-probe"]),
          client_error: null,
        });
      });
    });
    outgoing.setTimeout(timeoutMs, () => {
      outgoing.destroy(Object.assign(new Error("client timeout"), { code: "PROBE_CLIENT_TIMEOUT" }));
    });
    outgoing.on("error", fail);
    outgoing.end();
  });
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function one(agent, step, branch, index, warmup) {
  const at = performance.now() - origin;
  const result = await get(agent, `${plan.target}/page?${branch.query}`, step.timeout_ms ?? 30000);
  records.push({ step: step.label, branch: branch.name, index, warmup, at_ms: at, ...result });
}

async function runRoundRobin(step) {
  const agent = new Agent({ keepAlive: true, maxSockets: 1 });
  const { branches } = step;
  for (const [count, warmup] of [[step.warmup ?? 0, true], [step.count, false]]) {
    for (let index = 0; index < count; index += 1) {
      for (let offset = 0; offset < branches.length; offset += 1) {
        await one(agent, step, branches[(index + offset) % branches.length], index, warmup);
      }
    }
  }
  agent.destroy();
}

async function runChunk(agent, step, branch, base, size, warmup) {
  let next = 0;
  const worker = async () => {
    while (next < size) {
      const index = base + next;
      next += 1;
      await one(agent, step, branch, index, warmup);
    }
  };
  await Promise.all(Array.from({ length: step.concurrency }, worker));
}

async function runChunks(step) {
  const agent = new Agent({ keepAlive: true, maxSockets: step.concurrency });
  const { branches } = step;
  if ((step.warmup ?? 0) > 0) {
    for (const branch of branches) await runChunk(agent, step, branch, 0, step.warmup, true);
  }
  const rounds = Math.ceil(step.count / step.chunk);
  for (let round = 0; round < rounds; round += 1) {
    for (let offset = 0; offset < branches.length; offset += 1) {
      const branch = branches[(round + offset) % branches.length];
      const size = Math.min(step.chunk, step.count - round * step.chunk);
      await runChunk(agent, step, branch, round * step.chunk, size, false);
    }
  }
  agent.destroy();
}

async function runPaced(step) {
  let agent = new Agent({ keepAlive: true, maxSockets: 1 });
  const { branches } = step;
  for (let index = 0; index < step.count; index += 1) {
    await sleep(index === 0 ? (step.lead_ms ?? 0) : step.gap_ms);
    if (step.prelude !== undefined) {
      // 오래 쉬면 이 프로세스와 페이지 대역 사이의 연결이 그동안 닫힌다. 닫히는 순간에 그 소켓을 다시 쓰면 요청이
      // ECONNRESET 으로 실패하므로(첫 실행에서 6초 쉰 뒤 봤다) 새 Agent 로 먼저 한 번 보내 연결을 다시 맺는다.
      agent.destroy();
      agent = new Agent({ keepAlive: true, maxSockets: 1 });
      await one(agent, step, step.prelude, index, true);
    }
    for (let offset = 0; offset < branches.length; offset += 1) {
      await one(agent, step, branches[(index + offset) % branches.length], index, false);
    }
  }
  agent.destroy();
}

const RUNNERS = { rr: runRoundRobin, chunks: runChunks, paced: runPaced };

let exitCode = 0;
try {
  for (const step of plan.steps) {
    const runner = RUNNERS[step.kind];
    if (runner === undefined) throw new Error(`모르는 단계 종류: ${step.kind}`);
    await runner(step);
  }
} catch (error) {
  console.error(`loadgen 실패: ${error instanceof Error ? error.message : String(error)}`);
  exitCode = 1;
} finally {
  writeFileSync(plan.out, records.map((record) => JSON.stringify(record)).join("\n") + "\n", "utf8");
}
console.log(JSON.stringify({ records: records.length, elapsed_ms: performance.now() - origin }));
process.exit(exitCode);
