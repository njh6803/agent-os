// registry.mjs 의 실패 길을 가짜 레지스트리로 보는 자가 시험(양성 대조). 바깥에 요청을 보내지 않는다(127.0.0.1 만 쓴다).
//
// 돌리기: node probe/registry-selftest.mjs
// 산출물: out/registry-selftest/<갈래>/summary.json(registry.mjs 가 쓴 것), out/registry-selftest/summary.json,
//         표준 출력의 마지막 줄(JSON 한 줄)
//
// 갈래마다 registry.mjs 를 자식 프로세스로 띄우고 MD_PROBE_REGISTRY 를 가짜 서버로 돌린다.
// - ok: 모든 요청에 맞는 문서를 준다. 가짜 서버와 띄우는 길이 멀쩡하다는 대조다(종료 코드 0, 아홉 줄).
// - refused: 닫힌 포트다. 요청이 곧바로 던진다.
// - hang: 연결만 받고 아무것도 보내지 않는다.
// - body-stall: 200 과 본문의 앞머리만 보내고 멈춘다(제한 시간이 본문을 읽는 동안에도 걸리는지).
// - partial: 앞의 네 패키지에는 맞는 문서를 주고 나머지에는 멈춘다(그때까지 모은 회차가 summary.json 에 쓰이는지).
// - http-500, bad-json: 2xx 가 아닌 응답과 JSON 이 아닌 본문.
//
// 재려는 상황이 실제로 났다는 표지(.claude/rules/probes.md 첫 항목)
// - 자식이 끊기지 않고 스스로 끝났다(이 시험이 건 한도 안). 고치기 전 판은 hang·body-stall·partial 에서 끝나지 않는다.
//   그 서버가 신호 없는 요청을 정말 붙잡는지는 `legacyFetchHangs` 가 따로 본다(신호 없는 fetch 가 3초 안에 끝나지 않는다).
// - 그 실행이 쓴 summary.json 이 있다(`at` 이 띄운 시각보다 뒤다). 고치기 전 판은 refused 에서 쓰기 전에 던져 파일이 없다.
// - 측정이 아닌 회차의 까닭이 갈래가 낸 실패와 맞는다(제한 시간, 던짐, 500, JSON).
// - hang·body-stall·partial·ok·http-500·bad-json 에서는 가짜 서버가 받은 요청 수가 패키지 수와 같다(요청이 이 서버로 왔다).
// 표지가 어긋난 갈래는 측정이 아닌 것으로 세고, 하나라도 있으면 종료 코드 1 이다.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "registry-selftest");
const REQUEST_TIMEOUT_MS = 800;
const PACKAGES = 9;
// 자식이 스스로 끝나야 하는 한도. 패키지마다 제한 시간을 다 써도 9 × 0.8초다.
const CHILD_LIMIT_MS = PACKAGES * REQUEST_TIMEOUT_MS + 15_000;

/** 요청 경로의 패키지에 맞는 문서를 짓는다. 설치한 판이 있으면 그 판의 시각을 넣는다. */
function documentFor(name) {
  const manifest = join(ROOT, "node_modules", name, "package.json");
  const version = existsSync(manifest) ? JSON.parse(readFileSync(manifest, "utf8")).version : "1.0.0";
  return JSON.stringify({
    name,
    "dist-tags": { latest: version },
    time: { [version]: "2025-01-01T00:00:00.000Z" },
    versions: { [version]: { license: "MIT", dependencies: {} } },
  });
}

/** 갈래의 가짜 서버를 띄운다. `seen` 은 받은 요청의 경로다. */
function startServer(mode) {
  const seen = [];
  const sockets = new Set();
  const server = createServer((request, response) => {
    const name = decodeURIComponent((request.url ?? "/").slice(1));
    seen.push(name);
    const answerWell = mode === "ok" || (mode === "partial" && seen.length <= 4);
    if (answerWell) {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(documentFor(name));
    } else if (mode === "http-500") {
      response.writeHead(500, { "content-type": "text/plain" });
      response.end("boom");
    } else if (mode === "bad-json") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end("<html>not json</html>");
    } else if (mode === "body-stall") {
      response.writeHead(200, { "content-type": "application/json" });
      response.write('{"name":');
    }
    // hang, partial 의 뒤쪽: 아무것도 보내지 않는다.
  });
  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({
        url: `http://127.0.0.1:${port}`,
        seen,
        close: () =>
          new Promise((done) => {
            for (const socket of sockets) socket.destroy();
            server.close(() => done());
          }),
      });
    });
  });
}

/** registry.mjs 를 자식으로 띄운다. 한도를 넘기면 자식의 핸들로 끊고 `killed` 로 적는다. */
function runRegistry(registryUrl, outDir) {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    const child = spawn(process.execPath, [join(ROOT, "probe", "registry.mjs")], {
      env: {
        ...process.env,
        MD_PROBE_REGISTRY: registryUrl,
        MD_PROBE_REGISTRY_TIMEOUT_MS: String(REQUEST_TIMEOUT_MS),
        MD_PROBE_REGISTRY_OUT: outDir,
      },
      stdio: ["ignore", "pipe", "ignore"],
    });
    const chunks = [];
    child.stdout.on("data", (chunk) => chunks.push(chunk));
    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      child.kill();
    }, CHILD_LIMIT_MS);
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ code, killed, startedAt, elapsedMs: Date.now() - startedAt, stdout: Buffer.concat(chunks).toString("utf8") });
    });
  });
}

/** 신호 없는 fetch(고치기 전 판의 요청)가 이 서버에서 끝나지 않는지 본다. 3초 안에 끝나지 않으면 true 다. */
async function legacyFetchHangs(url) {
  const controller = new AbortController();
  const pending = fetch(`${url}/react-markdown`, { signal: controller.signal })
    .then((response) => response.text())
    .then(
      () => "finished",
      () => "threw",
    );
  const winner = await Promise.race([pending, new Promise((resolve) => setTimeout(() => resolve("still-waiting"), 3000))]);
  controller.abort();
  await pending;
  return winner === "still-waiting";
}

const MODES = [
  { mode: "ok", exit: 0, rows: PACKAGES, reason: null, serverSees: PACKAGES },
  { mode: "refused", exit: 1, rows: 0, reason: /요청이 던졌다/, serverSees: null },
  { mode: "hang", exit: 1, rows: 0, reason: /제한 시간/, serverSees: PACKAGES, legacyHangs: true },
  { mode: "body-stall", exit: 1, rows: 0, reason: /제한 시간/, serverSees: PACKAGES, legacyHangs: true },
  { mode: "partial", exit: 1, rows: 4, reason: /제한 시간/, serverSees: PACKAGES },
  { mode: "http-500", exit: 1, rows: 0, reason: /응답이 500/, serverSees: PACKAGES },
  { mode: "bad-json", exit: 1, rows: 0, reason: /요청이 던졌다: SyntaxError/, serverSees: PACKAGES },
];

async function main() {
  rmSync(OUT, { recursive: true, force: true, maxRetries: 5 });
  mkdirSync(OUT, { recursive: true });
  const rounds = [];
  const notMeasured = [];
  for (const expected of MODES) {
    const outDir = join(OUT, expected.mode);
    const server = await startServer(expected.mode);
    const url = server.url;
    if (expected.mode === "refused") {
      // 방금 닫은 포트다. 듣는 프로세스가 없어 연결이 거부된다.
      await server.close();
    }
    const legacyHangs = expected.legacyHangs === true ? await legacyFetchHangs(url) : null;
    const seenBefore = server.seen.length;
    const run = await runRegistry(url, outDir);
    const requestsSeen = server.seen.length - seenBefore;
    if (expected.mode !== "refused") await server.close();

    const summaryPath = join(outDir, "summary.json");
    let summary = null;
    try {
      summary = JSON.parse(readFileSync(summaryPath, "utf8"));
    } catch {
      summary = null;
    }
    let lastLine = null;
    try {
      lastLine = JSON.parse(run.stdout.trim().split(/\r?\n/).pop() ?? "");
    } catch {
      lastLine = null;
    }
    const problems = [];
    if (run.killed) problems.push(`자식이 ${CHILD_LIMIT_MS}ms 안에 끝나지 않아 끊었다`);
    if (run.code !== expected.exit) problems.push(`종료 코드 ${String(run.code)} (기대 ${expected.exit})`);
    if (summary === null) problems.push("summary.json 이 없거나 JSON 이 아니다");
    else {
      if (Date.parse(summary.at) < run.startedAt) problems.push("summary.json 이 이 실행의 것이 아니다");
      if (summary.rows.length !== expected.rows) problems.push(`잰 줄 ${summary.rows.length} (기대 ${expected.rows})`);
      if (summary.rows.length + summary.notMeasured.length !== PACKAGES) problems.push("잰 줄과 측정 아님의 합이 패키지 수와 다르다");
      const wrongReason = summary.notMeasured.filter((item) => expected.reason === null || !expected.reason.test(item.reason));
      if (wrongReason.length > 0) problems.push(`까닭이 갈래와 맞지 않는다: ${JSON.stringify(wrongReason.slice(0, 2))}`);
    }
    if (lastLine === null || lastLine.probe !== "registry") problems.push("표준 출력의 마지막 줄이 요약 JSON 이 아니다");
    if (expected.serverSees !== null && requestsSeen !== expected.serverSees) {
      problems.push(`가짜 서버가 받은 요청 ${requestsSeen} (기대 ${expected.serverSees})`);
    }
    if (expected.legacyHangs === true && legacyHangs !== true) problems.push("신호 없는 fetch 가 이 서버에서 3초 안에 끝났다(붙잡는 서버가 아니다)");
    const round = {
      mode: expected.mode,
      exit: run.code,
      killed: run.killed,
      elapsedMs: run.elapsedMs,
      rows: summary?.rows.length ?? null,
      notMeasuredInChild: summary?.notMeasured.length ?? null,
      reasons: [...new Set((summary?.notMeasured ?? []).map((item) => item.reason))],
      requestsSeen,
      legacyFetchHangs: legacyHangs,
      problems,
    };
    rounds.push(round);
    if (problems.length > 0) notMeasured.push({ mode: expected.mode, problems });
  }
  writeFileSync(join(OUT, "summary.json"), JSON.stringify({ requestTimeoutMs: REQUEST_TIMEOUT_MS, childLimitMs: CHILD_LIMIT_MS, notMeasured, rounds }, null, 2));
  console.log(JSON.stringify({ probe: "registry-selftest", expectedRounds: MODES.length, measuredRounds: rounds.length - notMeasured.length, notMeasured, rounds }));
  if (notMeasured.length > 0) process.exitCode = 1;
}

await main();
