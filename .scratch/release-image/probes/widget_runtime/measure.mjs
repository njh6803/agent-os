/**
 * release-image 설계 인터뷰의 프로브. 위젯(`web/apps/widget`, Next 16.3.6)을 한 번 빌드한 산출물을 그대로 두고 사이트
 * 파일만 바꿔 `start` 했을 때, 허용 출처(`frame-ancestors` 헤더, 페이지가 postMessage 를 거르는 목록)와 요청 글자 수
 * 상한(페이지, `element.js`)이 빌드 때의 사이트 파일을 따르는지 시작할 때의 사이트 파일을 따르는지를 잰다.
 *
 * 나무의 상태가 둘이다. 단계마다 맞는 상태가 아니면 아무것도 하지 않고 멈춘다.
 *   clean    저장소가 추적하는 그대로(지금 코드). `control` 단계가 돈다.
 *   patched  이 폴더의 `runtime.patch` 를 건 상태. `runtime`·`forks`·`startup`·`standalone`·`live` 단계가 돈다.
 *
 * 단계(첫 인자):
 *   control     지금 코드. 사이트 파일 A 로 빌드해 B 로 start, B 로 빌드해 A 로 start, 없는 파일로 start.
 *   runtime     고친 코드의 주 갈래(설정의 `frame-ancestors 'none'` 위에 proxy 가 실행 중의 값을 덮고, 페이지는 요청 때
 *               그리며 props 로 값을 받고, start 가 `element.js` 를 다시 짓는다). A 로 빌드한 산출물 하나로 B·A·사이트
 *               없음·없는 파일로 차례로 start 하고, B 로 빌드해 A 로 start 한다.
 *   forks       고친 코드의 다른 갈래. `connection()` 을 뺀 페이지(빌드 때 미리 그려진다)와 설정의 헤더를 뺀 proxy 만.
 *   element     `element.js` 만. 사이트 파일 셋(A, B, 자리표)으로 따로 지어 시간과 해시를 보고, 자리표로 지은 파일의
 *               숫자를 바꿔 넣은 것이 바로 지은 파일과 같은지 본다. 어느 나무에서도 돌지만 해시는 나무마다 다르다
 *               (고친 나무는 `element/WidgetElement.tsx` 가 달라 번들이 다르다).
 *   startup     고친 코드. 같은 산출물로 `element.js` 를 다시 짓는 start 와 다시 짓지 않는 start 를 번갈아 띄워 Ready
 *               줄까지의 시간을 견준다.
 *   siteread    `buildInput`(사이트 파일 읽기) 한 번에 드는 시간. 나무의 상태와 무관하다.
 *   standalone  고친 코드를 `output: "standalone"` 으로 지어 `server.js` 로 띄운다(시작 래퍼를 거치지 않는다).
 *   live        고친 코드. 서버를 끄지 않은 채 사이트 파일의 내용을 바꾸고 지워, 떠 있는 서버가 따라가는지 본다.
 *
 * 회차의 표지와 결과를 가른다. 표지는 "재려는 상황이 났다"이다. 빌드가 그 사이트 파일로 끝났고(종료 0, 경로 표, 새
 * BUILD_ID), 서버가 Ready 를 찍었고, 그 start 가 `.next` 의 산출물을 건드리지 않았고(시작 전후의 해시가 같다), 응답이
 * 200 이고, 본 값이 알려진 후보(A 의 값, B 의 값, 사이트 없음의 값) 가운데 하나로 갈렸고, 띄운 서버를 명령줄의 표지를
 * 확인한 뒤 껐다. 결과는 본 값이 빌드의 사이트 파일 것인지(build) 시작의 것인지(start)다. 표지를 못 본 회차는 측정이
 * 아니라고 세고, 그런 회차가 하나라도 있으면 종료 코드가 1이다.
 *
 * 전제와 못 보는 것(원본 출력에서 한 번 본 것은 README 의 "전제"에 적었다):
 * - 서버는 `127.0.0.1` 의 빈 포트에만 띄운다. 포트는 운영체제에 물어 받은 뒤 닫고 넘기므로 그 사이에 남이 잡을 수 있다.
 * - 브라우저를 띄우지 않는다. 페이지가 받은 값은 HTML 과 RSC 응답에 실린 props 의 글자로, 번들에 박힌 값은 HTML 이
 *   가리키는 청크의 글자로 본다. 그 값으로 위젯이 실제로 postMessage 를 거르고 글자 수를 세는지는 보지 않는다.
 * - 응답 시간은 같은 PC 에서 `node:http` 로 요청마다 새 연결을 열어 차례로 잰 것이다(연결을 재사용하는 `fetch` 로는
 *   이 PC 에서 값이 16ms 언저리로 뭉쳤다). 다른 세션의 부하에 흔들리므로 범위로만 읽는다.
 * - 모든 빌드와 start 는 `NEXT_TELEMETRY_DISABLED=1` 로 돈다.
 *
 * 사용: node .scratch/release-image/probes/widget_runtime/measure.mjs <단계> --out <저장소 밖 폴더의 절대 경로>
 */

import { spawn, spawnSync } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const HERE = import.meta.dirname;
const REPO = path.resolve(HERE, "..", "..", "..", "..");
const WEB = path.join(REPO, "web");
const WIDGET = path.join(WEB, "apps", "widget");
const NEXT_DIR = path.join(WIDGET, ".next");
const SITE_FILES = {
  A: path.join(REPO, "tests", "fixtures", "site_file", "sites.toml"),
  B: path.join(HERE, "sites_b.toml"),
  sentinel: path.join(HERE, "sites_sentinel.toml"),
};
const SENTINEL = "918273645";
const SITE_NAMES = ["A", "B", "none"];
const BUILD_TIMEOUT_MS = 20 * 60 * 1000;
const READY_TIMEOUT_MS = 3 * 60 * 1000;
const REQUEST_TIMEOUT_MS = 30 * 1000;
const STOP_TIMEOUT_MS = 20 * 1000;
const ANSI = /\u001b\[[0-9;]*[A-Za-z]/g;
// 고친 코드가 읽는 프로브 전용 스위치. 빌드와 start 의 환경에서 먼저 벗기고 회차가 준 것만 싣는다.
const SWITCHES = [
  "AGENT_OS_PROBE_STATIC_PAGE",
  "AGENT_OS_PROBE_CONFIG_CSP",
  "AGENT_OS_PROBE_START_ELEMENT",
  "AGENT_OS_PROBE_OUTPUT",
];
const STRIPPED_ENV = [
  "AGENT_OS_ADMIN_TOKEN",
  "AGENT_OS_CHANNEL_TOKEN",
  "AGENT_OS_UPSTREAM",
  "AGENT_OS_SITE_FILE",
  "PORT",
  "HOSTNAME",
  ...SWITCHES,
];

// --- 공통 ------------------------------------------------------------------------------------------------------------

function readText(file) {
  try {
    return fs.readFileSync(file, "utf-8");
  } catch {
    return null;
  }
}

function packageName(dir) {
  return JSON.parse(fs.readFileSync(path.join(dir, "package.json"), "utf-8")).name;
}

/** 이 스크립트가 지우는 자리는 위젯의 빌드 산출물뿐이다. 자리를 잘못 계산했으면 아무것도 하지 않고 멈춘다. */
function assertLayout() {
  if (packageName(WIDGET) !== "@agent-os/widget") {
    throw new Error(`위젯 앱 폴더가 기대한 자리가 아니다: ${WIDGET}`);
  }
}

/** 나무가 지금 코드인가 `runtime.patch` 를 건 코드인가. 둘이 섞였으면 mixed. */
function treeState() {
  const proxy = fs.existsSync(path.join(WIDGET, "proxy.ts"));
  const dynamicPage = (readText(path.join(WIDGET, "app", "page.tsx")) ?? "").includes("connection(");
  const configHeader = (readText(path.join(WIDGET, "next.config.ts")) ?? "").includes("WIDGET_ORIGINS_ENV");
  if (proxy && dynamicPage && !configHeader) {
    return "patched";
  }
  return !proxy && !dynamicPage && configHeader ? "clean" : "mixed";
}

function cleanEnv(extra) {
  const env = { ...process.env };
  for (const name of STRIPPED_ENV) {
    delete env[name];
  }
  return { ...env, NEXT_TELEMETRY_DISABLED: "1", ...extra };
}

function remove(target) {
  fs.rmSync(target, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 });
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function range(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted.length === 0
    ? null
    : {
        min: sorted[0],
        median: sorted[Math.floor(sorted.length / 2)],
        max: sorted.at(-1),
        mean: Math.round((sorted.reduce((sum, value) => sum + value, 0) / sorted.length) * 1000) / 1000,
        n: sorted.length,
      };
}

function showRange(found, unit = "ms") {
  return found === null
    ? "없음"
    : `${String(found.min)}~${String(found.max)}${unit}(가운데 ${String(found.median)}, 평균 ${String(found.mean)}, ${String(found.n)}번)`;
}

function environment() {
  const pnpm = spawnSync("pnpm --version", { shell: true, encoding: "utf-8", timeout: 60_000 });
  const next = JSON.parse(
    fs.readFileSync(createRequire(path.join(WIDGET, "package.json")).resolve("next/package.json"), "utf-8"),
  ).version;
  return {
    date: new Date().toISOString(),
    platform: `${os.type()} ${os.release()} ${os.arch()}`,
    cpu: `${os.cpus()[0]?.model ?? "?"} x${String(os.cpus().length)}`,
    memoryGb: Math.round(os.totalmem() / 2 ** 30),
    node: process.version,
    pnpm: (pnpm.stdout ?? "").trim(),
    next,
    tree: treeState(),
  };
}

/** 프로세스를 띄워 끝날 때까지 기다리고 줄마다 받은 시각을 적는다. 제한 시간을 넘기면 띄운 그 자식을 끈다. */
function runTimed(command, args, { cwd, env }) {
  return new Promise((resolve) => {
    const started = performance.now();
    const child = spawn(command, args, { cwd, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    const lines = [];
    const rest = { stdout: "", stderr: "" };
    let timedOut = false;
    const feed = (stream) => (chunk) => {
      const ms = Math.round(performance.now() - started);
      const parts = (rest[stream] + chunk).split(/\r?\n/);
      rest[stream] = parts.pop() ?? "";
      for (const text of parts) {
        lines.push({ ms, stream, text: text.replace(ANSI, "") });
      }
    };
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", feed("stdout"));
    child.stderr.on("data", feed("stderr"));
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill();
    }, BUILD_TIMEOUT_MS);
    child.on("error", (error) => {
      lines.push({ ms: Math.round(performance.now() - started), stream: "spawn", text: String(error) });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      const ms = Math.round(performance.now() - started);
      for (const stream of ["stdout", "stderr"]) {
        if (rest[stream] !== "") {
          lines.push({ ms, stream, text: rest[stream].replace(ANSI, "") });
        }
      }
      resolve({ code, timedOut, totalMs: ms, lines });
    });
  });
}

function saveLines(out, name, lines) {
  fs.writeFileSync(
    path.join(out, name),
    lines.map(({ ms, stream, text }) => `${String(ms).padStart(7)} ${stream.padEnd(6)} ${text}`).join("\n") + "\n",
    "utf-8",
  );
}

/** 회차들을 결과 JSON 으로 남기고 측정이 아닌 회차의 수를 돌려준다. */
function report(out, name, result) {
  const file = path.join(out, name);
  fs.writeFileSync(file, `${JSON.stringify({ environment: environment(), ...result }, null, 2)}\n`, "utf-8");
  const unmeasured = result.rounds.filter((round) => !round.measured);
  console.log(`결과: ${file}`);
  console.log(`회차 ${String(result.rounds.length)}, 측정이 아닌 회차 ${String(unmeasured.length)}`);
  for (const round of unmeasured) {
    console.log(`  측정 아님: ${round.label} ${JSON.stringify(round.markers)}`);
  }
  return unmeasured.length;
}

// --- 사이트 파일의 값 ------------------------------------------------------------------------------------------------

/** 사이트 파일에서 위젯이 읽는 두 값. 위젯이 쓰는 그 함수(`@agent-os/site-file` 의 `buildInput`)로 읽는다. */
async function loadSites() {
  const resolved = createRequire(path.join(WIDGET, "package.json")).resolve("@agent-os/site-file");
  const { buildInput } = await import(pathToFileURL(resolved).href);
  return {
    A: buildInput({ AGENT_OS_SITE_FILE: SITE_FILES.A }),
    B: buildInput({ AGENT_OS_SITE_FILE: SITE_FILES.B }),
    none: buildInput({}),
  };
}

function siteEnv(out, name) {
  if (name === "none") {
    return {};
  }
  if (name === "missing") {
    return { AGENT_OS_SITE_FILE: path.join(out, "no-such-site-file.toml") };
  }
  return { AGENT_OS_SITE_FILE: SITE_FILES[name] };
}

function cspOf(input) {
  return `frame-ancestors ${input.allowedOrigins.length === 0 ? "'none'" : input.allowedOrigins.join(" ")}`;
}

/** 헤더 값이 어느 사이트 파일의 것인가. 없으면 absent, 어느 것도 아니면 unknown(값). */
function siteOfCsp(sites, value) {
  if (value === undefined || value === null) {
    return "absent";
  }
  return SITE_NAMES.find((name) => cspOf(sites[name]) === value) ?? `unknown(${value})`;
}

/**
 * HTML 이나 RSC 응답에 실린 클라이언트 컴포넌트의 props 에서 두 값을 꺼낸다. HTML 은 그 글을 스크립트의 문자열로 실어
 * 따옴표가 `\"` 다. 없으면 null.
 */
function propsInPayload(text) {
  const plain = text.replaceAll('\\"', '"');
  const origins = /"allowedOrigins":(\[[^\]]*\])/.exec(plain);
  const chars = /"requestChars":(\d+)/.exec(plain);
  if (origins === null || chars === null) {
    return null;
  }
  try {
    return { allowedOrigins: JSON.parse(origins[1]), requestChars: Number(chars[1]) };
  } catch {
    return null;
  }
}

function siteOfProps(sites, props) {
  if (props === null) {
    return "absent";
  }
  return (
    SITE_NAMES.find(
      (name) =>
        JSON.stringify(sites[name].allowedOrigins) === JSON.stringify(props.allowedOrigins) &&
        sites[name].requestChars === props.requestChars,
    ) ?? `unknown(${JSON.stringify(props)})`
  );
}

/**
 * 번들(청크)에 박힌 값이 어느 사이트 파일의 것인가. 지금 코드의 빌드는 허용 출처를 공백으로 이은 글 하나로, 글자 수
 * 상한을 `requestChars:Number("4000")` 꼴로 박는다(지금 코드로 지은 청크를 Grep 으로 한 번 봤다).
 */
function siteOfBundle(sites, texts) {
  const all = texts.join("\n");
  const withOrigins = ["A", "B"].filter((name) => all.includes(sites[name].allowedOrigins.join(" ")));
  const chars = [...all.matchAll(/requestChars:Number\("(\d+)"\)/g)].map((match) => Number(match[1]));
  const withChars = [...new Set(chars)].map(
    (count) => SITE_NAMES.find((name) => sites[name].requestChars === count) ?? `unknown(${String(count)})`,
  );
  const one = (found) => (found.length === 0 ? "absent" : found.length === 1 ? found[0] : `unknown(${found.join("+")})`);
  return { origins: one(withOrigins), chars: one(withChars) };
}

/** 본 값이 빌드의 사이트 파일 것인가(build) 시작의 것인가(start). 둘이 같은 회차에서는 build=start. */
function relation(seen, buildSite, startSite) {
  if (!SITE_NAMES.includes(seen)) {
    return seen;
  }
  const tags = [...(seen === buildSite ? ["build"] : []), ...(seen === startSite ? ["start"] : [])];
  return tags.length === 0 ? `other(${seen})` : tags.join("=");
}

// --- element.js 의 기준 파일 -----------------------------------------------------------------------------------------

/** `element_build.mjs` 를 띄워 `element.js` 를 `--out` 아래에 한 번 짓는다. */
async function elementBuild(out, label, siteName) {
  const outDir = path.join(out, "element", label);
  fs.mkdirSync(outDir, { recursive: true });
  const siteArg = siteName === "none" ? "-" : SITE_FILES[siteName];
  const run = await runTimed(process.execPath, [path.join(HERE, "element_build.mjs"), WIDGET, siteArg, outDir], {
    cwd: WIDGET,
    env: cleanEnv({}),
  });
  saveLines(out, `element-${label}.log`, run.lines);
  let stats = null;
  try {
    stats = JSON.parse(run.lines.filter(({ stream }) => stream === "stdout").at(-1)?.text ?? "");
  } catch {
    stats = null;
  }
  return { label, siteName, file: path.join(outDir, "element.js"), exitCode: run.code, totalMs: run.totalMs, stats };
}

/** A, B, 사이트 없음으로 바로 지은 `element.js` 의 해시. 서버가 낸 `element.js` 를 이것과 견줘 어느 것인지 가른다. */
async function elementRefs(out) {
  const refs = {};
  for (const name of SITE_NAMES) {
    const built = await elementBuild(out, `ref-${name}`, name);
    if (built.exitCode !== 0 || built.stats === null) {
      throw new Error(`element.js 의 기준 파일(${name})을 짓지 못했다. ${path.join(out, `element-ref-${name}.log`)} 를 본다.`);
    }
    refs[name] = built.stats.sha256;
  }
  if (new Set(Object.values(refs)).size !== SITE_NAMES.length) {
    throw new Error(`element.js 의 기준 파일 셋이 서로 다르지 않다: ${JSON.stringify(refs)}`);
  }
  console.log(`element.js 기준 해시: ${JSON.stringify(refs)}`);
  return refs;
}

// --- 빌드 ------------------------------------------------------------------------------------------------------------

const NEXT_BANNER = /Next\.js \d+\.\d+\.\d+/;
const ROUTE_LINE = /^[┌├└]\s+(\S)\s+(\S+)/;

function walk(root, visit, relative = "") {
  for (const entry of fs.readdirSync(path.join(root, relative), { withFileTypes: true })) {
    const next = relative === "" ? entry.name : `${relative}/${entry.name}`;
    if (entry.isDirectory()) {
      walk(root, visit, next);
    } else if (entry.isFile()) {
      visit(path.join(root, next), next);
    }
  }
}

// 빌드가 낸 것이 아니거나(다음 빌드의 캐시) 빌드의 기록인 것(trace). 서버가 요청에 답하는 데 읽지 않는다고 봤다.
const NOT_SERVED = ["cache/", "trace", "trace-build", "standalone/"];

function servedArtifact(relative) {
  return !NOT_SERVED.some((prefix) => (prefix.endsWith("/") ? relative.startsWith(prefix) : relative === prefix));
}

/** `.next` 의 산출물(캐시와 trace 는 뺀다)의 파일마다의 해시와 그것을 이은 해시. start 가 산출물을 건드렸는지 본다. */
function artifactDigest(root = NEXT_DIR) {
  const files = new Map();
  if (fs.existsSync(root)) {
    walk(root, (absolute, relative) => {
      if (servedArtifact(relative)) {
        files.set(relative, sha256(fs.readFileSync(absolute)));
      }
    });
  }
  const keys = [...files.keys()].sort();
  return { digest: sha256(keys.map((key) => `${key}:${files.get(key)}`).join("\n")), files };
}

function digestDiff(before, after) {
  const changed = [];
  for (const [key, value] of after.files) {
    if (before.files.get(key) !== value) {
      changed.push(before.files.has(key) ? `바뀜 ${key}` : `생김 ${key}`);
    }
  }
  for (const key of before.files.keys()) {
    if (!after.files.has(key)) {
      changed.push(`없어짐 ${key}`);
    }
  }
  return changed;
}

/** `.next` 의 산출물 가운데 사이트 파일의 허용 출처가 글자로 든 파일. 미리 그린 페이지와 번들과 설정의 사본이 여기 든다. */
function bakedFiles(sites) {
  const found = { A: [], B: [] };
  walk(NEXT_DIR, (absolute, relative) => {
    if (!servedArtifact(relative)) {
      return;
    }
    const text = fs.readFileSync(absolute).toString("latin1");
    for (const name of ["A", "B"]) {
      if (sites[name].allowedOrigins.some((origin) => text.includes(origin))) {
        found[name].push(relative);
      }
    }
  });
  return found;
}

/** 위젯을 산출물을 지운 채 한 번 빌드한다(시작 래퍼의 `build`). */
async function widgetBuild(out, sites, label, siteName, extraEnv = {}) {
  remove(NEXT_DIR);
  remove(path.join(WIDGET, "public", "element.js"));
  const startedAt = Date.now();
  const run = await runTimed(process.execPath, [path.join(WIDGET, "tools", "start.ts"), "build"], {
    cwd: WIDGET,
    env: cleanEnv({ ...siteEnv(out, siteName), ...extraEnv }),
  });
  saveLines(out, `${label}.log`, run.lines);
  const table = [];
  let inTable = false;
  for (const { text } of run.lines) {
    if (/^Route \(app\)/.test(text.trim())) {
      inTable = true;
    } else if (inTable && text.trim() !== "") {
      table.push(text.trim());
    }
  }
  const routes = {};
  for (const line of table) {
    const match = ROUTE_LINE.exec(line);
    if (match !== null) {
      routes[match[2]] = match[1];
    }
  }
  const buildIdFile = path.join(NEXT_DIR, "BUILD_ID");
  const buildIdAt = fs.existsSync(buildIdFile) ? fs.statSync(buildIdFile).mtimeMs : null;
  const elementFile = path.join(WIDGET, "public", "element.js");
  const markers = {
    exitZero: run.code === 0 && !run.timedOut,
    nextBanner: run.lines.some(({ text }) => NEXT_BANNER.test(text)),
    routeTable: routes["/"] !== undefined,
    buildIdFresh: buildIdAt !== null && buildIdAt >= startedAt,
    elementBuilt: fs.existsSync(elementFile) && fs.statSync(elementFile).mtimeMs >= startedAt,
  };
  const measured = Object.values(markers).every(Boolean);
  const build = {
    label,
    kind: "build",
    siteName,
    extraEnv,
    totalMs: run.totalMs,
    buildId: readText(buildIdFile)?.trim() ?? null,
    routes,
    routeTable: table,
    elementSha: fs.existsSync(elementFile) ? sha256(fs.readFileSync(elementFile)) : null,
    baked: measured ? bakedFiles(sites) : null,
    markers,
    measured,
  };
  console.log(
    `${label}: 빌드 ${(run.totalMs / 1000).toFixed(1)}s 사이트=${siteName} 경로=${JSON.stringify(routes)} 측정=${String(measured)}`,
  );
  if (build.baked !== null) {
    console.log(`  허용 출처가 든 산출물: A ${String(build.baked.A.length)}개, B ${String(build.baked.B.length)}개`);
    for (const file of [...build.baked.A, ...build.baked.B]) {
      console.log(`    ${file}`);
    }
  }
  return build;
}

// --- 서버 ------------------------------------------------------------------------------------------------------------

function freePort() {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const address = probe.address();
      probe.close(() => {
        if (address !== null && typeof address === "object") {
          resolve(address.port);
        } else {
          reject(new Error("빈 포트를 받지 못했다"));
        }
      });
    });
  });
}

/**
 * 서버를 띄우고 Ready 줄이나 종료나 제한 시간 가운데 먼저 오는 것까지 기다린다. 명령줄에 이 회차만 쓰는 표지를 node 의
 * `--title` 로 싣는다. 끌 때 그 pid 의 명령줄에 이 표지가 있는지 본다. stdout 과 stderr 는 끝까지 읽어 버퍼가 차지 않는다.
 */
async function startServer(out, label, { args, cwd, env }) {
  const token = `widget-runtime-probe-${label}-${randomBytes(4).toString("hex")}`;
  const port = await freePort();
  const started = performance.now();
  const child = spawn(process.execPath, [`--title=${token}`, ...args(port)], {
    cwd,
    env: cleanEnv(env(port)),
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  const server = { label, token, port, pid: child.pid ?? null, child, lines: [], readyMs: null, exited: false, exitCode: null };
  const rest = { stdout: "", stderr: "" };
  let settle = () => {};
  const waited = new Promise((resolve) => {
    settle = resolve;
  });
  const feed = (stream) => (chunk) => {
    const ms = Math.round(performance.now() - started);
    const parts = (rest[stream] + chunk).split(/\r?\n/);
    rest[stream] = parts.pop() ?? "";
    for (const raw of parts) {
      const text = raw.replace(ANSI, "");
      server.lines.push({ ms, stream, text });
      if (server.readyMs === null && /Ready in/.test(text)) {
        server.readyMs = ms;
        settle();
      }
    }
  };
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  child.stdout.on("data", feed("stdout"));
  child.stderr.on("data", feed("stderr"));
  child.on("error", (error) => {
    server.lines.push({ ms: Math.round(performance.now() - started), stream: "spawn", text: String(error) });
  });
  server.closed = new Promise((resolve) => {
    child.on("close", (code) => {
      server.exited = true;
      server.exitCode = code;
      server.exitMs = Math.round(performance.now() - started);
      for (const stream of ["stdout", "stderr"]) {
        if (rest[stream] !== "") {
          server.lines.push({ ms: server.exitMs, stream, text: rest[stream].replace(ANSI, "") });
        }
      }
      settle();
      resolve();
    });
  });
  const timer = setTimeout(settle, READY_TIMEOUT_MS);
  await waited;
  clearTimeout(timer);
  server.ready = server.readyMs !== null && !server.exited;
  return server;
}

function commandLineOf(pid) {
  if (process.platform === "win32") {
    const found = spawnSync(
      "powershell.exe",
      ["-NoProfile", "-NonInteractive", "-Command", `(Get-CimInstance Win32_Process -Filter "ProcessId=${String(pid)}").CommandLine`],
      { encoding: "utf-8", timeout: 60_000, windowsHide: true },
    );
    return found.status === 0 ? found.stdout.trim() : null;
  }
  const text = readText(`/proc/${String(pid)}/cmdline`);
  return text === null ? null : text.replaceAll("\0", " ").trim();
}

/**
 * 띄운 서버를 끈다. pid 만 보고 끄지 않는다. 끄기 직전에 그 pid 의 명령줄을 읽어 이 회차의 표지가 있을 때만 끈다. 이미
 * 끝났으면 끄지 않는다. 표지를 보지 못하면 끄지 않고 그 사실을 남긴다(그 회차는 측정이 아니다).
 */
async function stopServer(server) {
  if (server.exited) {
    return { ok: true, how: "스스로 끝났다" };
  }
  const commandLine = server.pid === null ? null : commandLineOf(server.pid);
  if (commandLine === null || !commandLine.includes(server.token)) {
    return { ok: false, how: `pid ${String(server.pid)} 의 명령줄에 표지가 없어 끄지 않았다`, commandLine };
  }
  if (process.platform === "win32") {
    spawnSync("taskkill", ["/PID", String(server.pid), "/T", "/F"], { encoding: "utf-8", timeout: 60_000, windowsHide: true });
  } else {
    server.child.kill("SIGTERM");
  }
  const timer = new Promise((resolve) => setTimeout(resolve, STOP_TIMEOUT_MS));
  await Promise.race([server.closed, timer]);
  return { ok: server.exited, how: server.exited ? "명령줄의 표지를 확인하고 껐다" : "끄라고 했지만 제한 시간 안에 끝나지 않았다" };
}

async function get(port, pathname, headers = {}) {
  const started = performance.now();
  try {
    const response = await fetch(`http://127.0.0.1:${String(port)}${pathname}`, {
      headers,
      redirect: "manual",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    const body = Buffer.from(await response.arrayBuffer());
    return {
      status: response.status,
      headers: Object.fromEntries(response.headers),
      body,
      ms: Math.round((performance.now() - started) * 10) / 10,
    };
  } catch (error) {
    return { status: null, headers: {}, body: Buffer.alloc(0), ms: null, error: String(error) };
  }
}

function saveResponse(out, label, name, response) {
  const dir = path.join(out, label);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, `${name}.headers.json`),
    `${JSON.stringify({ status: response.status, headers: response.headers, error: response.error ?? null }, null, 2)}\n`,
    "utf-8",
  );
  fs.writeFileSync(path.join(dir, `${name}.body`), response.body);
}

/** 뜬 서버에서 값이 드러나는 자리를 모두 읽고, 자리마다 어느 사이트 파일의 값인지 가른다. 원본 응답은 `--out` 에 남긴다. */
async function observe(out, sites, refs, label, port) {
  const page = await get(port, "/widget");
  // 사이트가 iframe 에 실제로 넣는 주소의 꼴(질의가 붙는다).
  const pageQuery = await get(port, "/widget?agent=order-helper&heading=probe");
  const rsc = await get(port, "/widget?_rsc", { RSC: "1" });
  const notFound = await get(port, "/widget/widget-runtime-probe-missing");
  const element = await get(port, "/widget/element.js");
  const configRoute = await get(port, "/widget/config");
  const fontName = fs.readdirSync(path.join(WIDGET, "public", "fonts")).find((name) => name.endsWith(".woff2"));
  const font = fontName === undefined ? null : await get(port, `/widget/fonts/${fontName}`);
  for (const [name, response] of Object.entries({ page, pageQuery, rsc, notFound, element, configRoute })) {
    saveResponse(out, label, name, response);
  }
  const html = page.body.toString("utf-8");
  const chunkPaths = [
    ...new Set(html.replaceAll('\\"', '"').match(/\/widget\/_next\/static\/chunks\/[A-Za-z0-9_.~-]+\.js/g) ?? []),
  ];
  const chunks = [];
  for (const chunkPath of chunkPaths) {
    const chunk = await get(port, chunkPath);
    chunks.push({ path: chunkPath, status: chunk.status, text: chunk.body.toString("utf-8") });
  }
  const bundle = siteOfBundle(
    sites,
    chunks.map(({ text }) => text),
  );
  const elementSha = element.status === 200 ? sha256(element.body) : null;
  let configChars = null;
  try {
    configChars = configRoute.status === 200 ? JSON.parse(configRoute.body.toString("utf-8")).requestChars : null;
  } catch {
    configChars = null;
  }
  return {
    status: {
      page: page.status,
      pageQuery: pageQuery.status,
      rsc: rsc.status,
      notFound: notFound.status,
      element: element.status,
      configRoute: configRoute.status,
      font: font?.status ?? null,
      chunks: chunks.map(({ status }) => status),
    },
    contentType: { page: page.headers["content-type"] ?? null, rsc: rsc.headers["content-type"] ?? null },
    cacheControl: { page: page.headers["cache-control"] ?? null, element: element.headers["cache-control"] ?? null },
    prerenderHeader: page.headers["x-nextjs-prerender"] ?? null,
    allowOrigin: {
      element: element.headers["access-control-allow-origin"] ?? null,
      font: font?.headers["access-control-allow-origin"] ?? null,
      configRoute: configRoute.headers["access-control-allow-origin"] ?? null,
    },
    cspRaw: {
      page: page.headers["content-security-policy"] ?? null,
      pageQuery: pageQuery.headers["content-security-policy"] ?? null,
      rsc: rsc.headers["content-security-policy"] ?? null,
      notFound: notFound.headers["content-security-policy"] ?? null,
      element: element.headers["content-security-policy"] ?? null,
      font: font?.headers["content-security-policy"] ?? null,
      configRoute: configRoute.headers["content-security-policy"] ?? null,
    },
    site: {
      cspPage: siteOfCsp(sites, page.headers["content-security-policy"]),
      cspPageQuery: siteOfCsp(sites, pageQuery.headers["content-security-policy"]),
      cspRsc: siteOfCsp(sites, rsc.headers["content-security-policy"]),
      cspNotFound: siteOfCsp(sites, notFound.headers["content-security-policy"]),
      cspElement: siteOfCsp(sites, element.headers["content-security-policy"]),
      cspFont: siteOfCsp(sites, font?.headers["content-security-policy"]),
      htmlProps: siteOfProps(sites, propsInPayload(html)),
      htmlPropsQuery: siteOfProps(sites, propsInPayload(pageQuery.body.toString("utf-8"))),
      rscProps: siteOfProps(sites, propsInPayload(rsc.body.toString("utf-8"))),
      bundleOrigins: bundle.origins,
      bundleChars: bundle.chars,
      element: elementSha === null ? "absent" : (SITE_NAMES.find((name) => refs[name] === elementSha) ?? "unknown"),
      configRoute:
        configRoute.status === 404
          ? "absent"
          : (SITE_NAMES.find((name) => sites[name].requestChars === configChars) ?? `unknown(${String(configChars)})`),
    },
    chunkCount: chunks.length,
    elementSha,
  };
}

/** 새 연결 하나로 한 번 받는다. 걸린 시간은 연결을 열 때부터 응답의 몸을 다 받을 때까지다. */
function timedGet(port, pathname) {
  return new Promise((resolve) => {
    const started = performance.now();
    const request = http.get(
      { host: "127.0.0.1", port, path: pathname, agent: false, timeout: REQUEST_TIMEOUT_MS },
      (response) => {
        response.resume();
        response.on("end", () => {
          resolve({ status: response.statusCode ?? null, ms: performance.now() - started });
        });
      },
    );
    request.on("timeout", () => {
      request.destroy(new Error("제한 시간"));
    });
    request.on("error", () => {
      resolve({ status: null, ms: null });
    });
  });
}

/**
 * 페이지를 한 번 데운 뒤 `count` 번 차례로 받아 걸린 시간(ms)을 적는다. 요청마다 새 연결을 연다. 첫 판은 `fetch` 의 이어 쓰는
 * 연결로 쟀는데, 미리 그린 페이지와 요청 때 그리는 페이지의 가운데 값이 똑같이 16ms 안팎이었다(Windows 의 타이머 눈금으로
 * 읽었다). 그래서 연결을 이어 쓰지 않게 바꿨다.
 */
async function timePage(port, count) {
  await timedGet(port, "/widget");
  const times = [];
  for (let index = 0; index < count; index += 1) {
    const response = await timedGet(port, "/widget");
    if (response.status === 200 && response.ms !== null) {
      times.push(Math.round(response.ms * 10) / 10);
    }
  }
  return times;
}

const WRAPPER_START = {
  args: (port) => [path.join(WIDGET, "tools", "start.ts"), "start", "--port", String(port)],
  cwd: WIDGET,
  portEnv: () => ({}),
};

/**
 * 빌드해 둔 산출물로 서버를 한 번 띄워 값을 읽고 끈다. 표지: 그 빌드가 측정이고 디스크의 산출물이 그 빌드의 것이고,
 * 서버가 Ready 를 찍었고, 페이지와 RSC 와 `element.js` 가 200 이고, 헤더·값·`element.js` 가 알려진 후보로 갈렸고, 띄우기
 * 전후의 산출물 해시가 같고, 명령줄의 표지를 확인한 뒤 껐다. `launcher` 를 주지 않으면 시작 래퍼의 `start` 다.
 */
async function serverRound(out, sites, refs, label, build, startSite, { extraEnv = {}, launcher = WRAPPER_START, timingCount = 100 } = {}) {
  // 서버가 읽는 산출물의 자리. standalone 은 복사된 나무의 `.next` 다.
  const artifactRoot = launcher.artifactRoot ?? NEXT_DIR;
  const before = artifactDigest(artifactRoot);
  const elementBefore = readElementSha();
  const server = await startServer(out, label, {
    args: launcher.args,
    cwd: launcher.cwd,
    env: (port) => ({ ...siteEnv(out, startSite), ...launcher.portEnv(port), ...extraEnv }),
  });
  let seen = null;
  let times = [];
  let stop;
  try {
    if (server.ready) {
      seen = await observe(out, sites, refs, label, server.port);
      times = await timePage(server.port, timingCount);
    }
  } finally {
    stop = await stopServer(server);
    saveLines(out, `${label}.log`, server.lines);
  }
  const after = artifactDigest(artifactRoot);
  const touched = digestDiff(before, after);
  const classified = (name) => SITE_NAMES.includes(name);
  const markers = {
    buildMeasured: build.measured,
    sameBuild: (readText(path.join(artifactRoot, "BUILD_ID"))?.trim() ?? null) === build.buildId,
    ready: server.ready,
    pageOk: seen?.status.page === 200 && (seen.contentType.page ?? "").startsWith("text/html"),
    rscOk: seen?.status.rsc === 200 && (seen.contentType.rsc ?? "").startsWith("text/x-component"),
    elementOk: seen?.status.element === 200,
    cspClassified: seen !== null && classified(seen.site.cspPage),
    // 값은 응답의 props(고친 코드)나 번들(지금 코드) 가운데 한 곳에서만 갈려야 한다.
    valuesClassified:
      seen !== null &&
      (classified(seen.site.htmlProps) && classified(seen.site.rscProps)
        ? seen.site.bundleOrigins === "absent" && seen.site.bundleChars === "absent"
        : seen.site.htmlProps === "absent" &&
          seen.site.rscProps === "absent" &&
          ["A", "B"].includes(seen.site.bundleOrigins) &&
          classified(seen.site.bundleChars)),
    elementClassified: seen !== null && classified(seen.site.element),
    artifactUntouched: touched.length === 0,
    timed: times.length === timingCount,
    stopped: stop.ok,
  };
  const where =
    seen === null
      ? null
      : Object.fromEntries(Object.entries(seen.site).map(([place, name]) => [place, relation(name, build.siteName, startSite)]));
  const round = {
    label,
    kind: "start",
    build: build.label,
    buildSite: build.siteName,
    startSite,
    extraEnv,
    readyMs: server.readyMs,
    exitCode: server.exitCode,
    stop,
    seen,
    where,
    elementOnDiskBefore: elementBefore,
    elementOnDiskAfter: readElementSha(),
    pageMs: range(times),
    touched,
    markers,
    measured: Object.values(markers).every(Boolean),
  };
  console.log(`${label}: 빌드=${build.siteName} 시작=${startSite} Ready ${String(server.readyMs)}ms 측정=${String(round.measured)}`);
  if (seen !== null) {
    console.log(`  어느 값인가: ${JSON.stringify(where)}`);
    console.log(`  페이지: Cache-Control=${String(seen.cacheControl.page)} x-nextjs-prerender=${String(seen.prerenderHeader)}`);
    console.log(`  CSP 원문: ${JSON.stringify(seen.cspRaw)}`);
    console.log(`  Access-Control-Allow-Origin: ${JSON.stringify(seen.allowOrigin)} 상태: ${JSON.stringify(seen.status)}`);
    console.log(`  페이지 응답 시간: ${showRange(round.pageMs)}`);
  }
  if (touched.length > 0) {
    console.log(`  start 가 건드린 산출물: ${touched.join(", ")}`);
  }
  return round;
}

function readElementSha() {
  const file = path.join(WIDGET, "public", "element.js");
  return fs.existsSync(file) ? sha256(fs.readFileSync(file)) : null;
}

/**
 * 없는 사이트 파일로 서버를 띄운다. 표지는 실패의 까닭이다. 서버가 스스로 0 이 아닌 코드로 끝났고(끄기 전에), 출력에
 * 사이트 파일 읽기의 진단("파일이 없다")과 준 경로가 있다. next 는 설정 파일을 읽기 전에 Ready 를 찍을 수 있어(지금
 * 코드의 start 원본 출력에서 Ready 줄이 설정 줄보다 먼저였다) Ready 줄의 유무는 표지가 아니라 관찰로 적는다. Ready 를
 * 찍었으면 끝나기 전에 페이지를 한 번 받아 본다. 스스로 끝나지 않고 떠 있으면 그 응답까지 적고 끈다(측정 아님).
 */
async function failingStartRound(out, label, build, { extraEnv = {}, launcher = WRAPPER_START } = {}) {
  const missing = siteEnv(out, "missing").AGENT_OS_SITE_FILE;
  const server = await startServer(out, label, {
    args: launcher.args,
    cwd: launcher.cwd,
    env: (port) => ({ AGENT_OS_SITE_FILE: missing, ...launcher.portEnv(port), ...extraEnv }),
  });
  let page = null;
  if (server.ready) {
    page = await get(server.port, "/widget");
    await Promise.race([server.closed, new Promise((resolve) => setTimeout(resolve, STOP_TIMEOUT_MS))]);
  }
  const stop = await stopServer(server);
  saveLines(out, `${label}.log`, server.lines);
  const text = server.lines.map((line) => line.text).join("\n");
  const markers = {
    buildMeasured: build.measured,
    fileIsMissing: !fs.existsSync(missing),
    exitedNonZero: stop.how === "스스로 끝났다" && typeof server.exitCode === "number" && server.exitCode !== 0,
    diagnostic: text.includes("파일이 없다") && text.includes(path.basename(missing)),
  };
  const round = {
    label,
    kind: "failing-start",
    build: build.label,
    startSite: "missing",
    extraEnv,
    readyMs: server.readyMs,
    exitCode: server.exitCode,
    exitMs: server.exitMs ?? null,
    stop,
    readyLineSeen: server.readyMs !== null,
    pageStatusIfReady: page?.status ?? null,
    pageErrorIfReady: page?.error ?? null,
    pageCspIfReady: page?.headers["content-security-policy"] ?? null,
    reachedNext: server.lines.some((line) => NEXT_BANNER.test(line.text)),
    markers,
    measured: Object.values(markers).every(Boolean),
  };
  console.log(
    `${label}: 없는 사이트 파일로 시작. 종료 코드 ${String(server.exitCode)}(${String(round.exitMs)}ms), Ready ${String(server.readyMs)}, next 머리 줄 ${String(round.reachedNext)}, 측정=${String(round.measured)} ${JSON.stringify(markers)}`,
  );
  if (page !== null) {
    console.log(
      `  Ready 뒤에 받은 페이지: 상태 ${String(page.status)}, 오류 ${String(page.error ?? "없음")}, CSP ${String(round.pageCspIfReady)}`,
    );
  }
  return round;
}

function requireTree(expected) {
  const state = treeState();
  if (state !== expected) {
    throw new Error(
      `이 단계는 나무가 ${expected} 일 때 돈다. 지금은 ${state} 다. clean 은 추적하는 그대로, patched 는 runtime.patch 를 건 상태다.`,
    );
  }
}

// --- control ---------------------------------------------------------------------------------------------------------

async function stepControl(out) {
  requireTree("clean");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  const buildA = await widgetBuild(out, sites, "control-build-A", "A");
  rounds.push(buildA);
  rounds.push(await serverRound(out, sites, refs, "control-A-start-B", buildA, "B"));
  rounds.push(await failingStartRound(out, "control-A-start-missing", buildA));
  const buildB = await widgetBuild(out, sites, "control-build-B", "B");
  rounds.push(buildB);
  rounds.push(await serverRound(out, sites, refs, "control-B-start-A", buildB, "A"));
  return report(out, "control.json", { sites, refs, rounds });
}

// --- runtime ---------------------------------------------------------------------------------------------------------

async function stepRuntime(out) {
  requireTree("patched");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  const buildA = await widgetBuild(out, sites, "runtime-build-A", "A");
  rounds.push(buildA);
  const noRebuild = { AGENT_OS_PROBE_START_ELEMENT: "0" };
  // 첫 start 는 `element.js` 를 다시 짓지 않는다. 디스크의 것은 빌드(A)가 낸 것이라, 이 회차가 "다시 짓지 않으면 빌드의 값이
  // 남는다"는 고친 나무 안의 대조다. 헤더와 페이지는 이 회차에서도 시작의 값을 따라야 한다.
  rounds.push(await serverRound(out, sites, refs, "runtime-A-start-B-no-element", buildA, "B", { extraEnv: noRebuild }));
  rounds.push(await serverRound(out, sites, refs, "runtime-A-start-B", buildA, "B"));
  rounds.push(await serverRound(out, sites, refs, "runtime-A-start-A", buildA, "A"));
  rounds.push(await serverRound(out, sites, refs, "runtime-A-start-none", buildA, "none"));
  rounds.push(await serverRound(out, sites, refs, "runtime-A-start-B-again", buildA, "B"));
  rounds.push(await failingStartRound(out, "runtime-A-start-missing", buildA));
  rounds.push(await failingStartRound(out, "runtime-A-start-missing-no-element", buildA, { extraEnv: noRebuild }));
  const buildB = await widgetBuild(out, sites, "runtime-build-B", "B");
  rounds.push(buildB);
  rounds.push(await serverRound(out, sites, refs, "runtime-B-start-A", buildB, "A"));
  const none = await widgetBuild(out, sites, "runtime-build-none", "none");
  rounds.push(none);
  rounds.push(await serverRound(out, sites, refs, "runtime-none-start-B", none, "B"));
  return report(out, "runtime.json", { sites, refs, rounds });
}

// --- forks -----------------------------------------------------------------------------------------------------------

async function stepForks(out) {
  requireTree("patched");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  // 페이지에서 `connection()` 을 빼고(빌드 때 미리 그려진다) 설정의 `frame-ancestors 'none'` 도 뺀다(proxy 만 헤더를 낸다).
  const build = await widgetBuild(out, sites, "forks-build-A-static-proxy-only", "A", {
    AGENT_OS_PROBE_STATIC_PAGE: "1",
    AGENT_OS_PROBE_CONFIG_CSP: "off",
  });
  rounds.push(build);
  rounds.push(await serverRound(out, sites, refs, "forks-A-start-B-static-proxy-only", build, "B"));
  rounds.push(await serverRound(out, sites, refs, "forks-A-start-none-static-proxy-only", build, "none"));
  rounds.push(await manifestRewriteRound(out, sites, refs));
  return report(out, "forks.json", { sites, refs, rounds: rounds.flat() });
}

/**
 * 시작 래퍼가 값을 넘기는 길의 한 꼴. 서버 파일 없이, start 전에 빌드 산출물 `routes-manifest.json` 에 박힌 헤더 값을
 * 바꿔 쓴다. 주 갈래를 사이트 파일 없이 빌드하면 그 파일의 헤더 값은 `frame-ancestors 'none'` 하나다. 그 글자를 B 의
 * 값으로 바꾼 뒤 A 로 start 한다. proxy 가 지나는 페이지는 A(시작의 값)여야 하고, proxy 가 지나지 않는 경로(없는 경로,
 * `element.js`, 글꼴)가 B 를 내면 바꿔 쓴 값이 start 에 반영된 것이다. 끝나면 파일을 되돌린다.
 */
async function manifestRewriteRound(out, sites, refs) {
  const build = await widgetBuild(out, sites, "forks-build-none-for-manifest", "none");
  const file = path.join(NEXT_DIR, "routes-manifest.json");
  const original = readText(file);
  const floor = cspOf(sites.none);
  const occurrences = original === null ? 0 : original.split(floor).length - 1;
  build.markers.manifestHasFloor = occurrences >= 1;
  build.measured = Object.values(build.markers).every(Boolean);
  if (!build.measured || original === null) {
    return [build];
  }
  let round;
  fs.writeFileSync(file, original.replaceAll(floor, cspOf(sites.B)), "utf-8");
  try {
    round = await serverRound(out, sites, refs, "forks-none-manifest-B-start-A", build, "A");
  } finally {
    fs.writeFileSync(file, original, "utf-8");
  }
  round.manifest = {
    replaced: occurrences,
    injected: "B",
    proxyPath: round.seen?.site.cspPage ?? null,
    otherPaths: round.seen === null ? null : [round.seen.site.cspNotFound, round.seen.site.cspElement, round.seen.site.cspFont],
  };
  // 바꿔 쓴 뒤의 값이 응답에 났는지와 무관하게, 가를 수 있는 값(A, B, none)이 났으면 측정이다.
  round.markers.otherPathsClassified =
    round.manifest.otherPaths !== null && round.manifest.otherPaths.every((name) => SITE_NAMES.includes(name));
  round.measured = Object.values(round.markers).every(Boolean);
  console.log(`  routes-manifest.json 을 바꿔 쓴 값(${String(occurrences)}곳, B): ${JSON.stringify(round.manifest)}`);
  return [build, round];
}

// --- startup ---------------------------------------------------------------------------------------------------------

/**
 * start 가 `element.js` 를 다시 짓는 데 드는 시간. 같은 산출물로, 다시 짓지 않는 start 와 다시 짓는 start 를 번갈아 띄워
 * 프로세스를 띄운 때부터 Ready 줄까지를 견준다. 두 갈래 모두 시작 래퍼가 vite 를 적재한다(래퍼가 `element.ts` 를 import 한다).
 */
async function stepStartup(out, { rounds: count }) {
  requireTree("patched");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  const build = await widgetBuild(out, sites, "startup-build-A", "A");
  rounds.push(build);
  for (let index = 1; index <= count; index += 1) {
    rounds.push(
      await serverRound(out, sites, refs, `startup-no-element-${String(index)}`, build, "B", {
        extraEnv: { AGENT_OS_PROBE_START_ELEMENT: "0" },
        timingCount: 0,
      }),
    );
    rounds.push(await serverRound(out, sites, refs, `startup-element-${String(index)}`, build, "B", { timingCount: 0 }));
  }
  const ready = (prefix) =>
    range(rounds.filter((round) => round.measured && round.label.startsWith(prefix)).map((round) => round.readyMs));
  const summary = { readyMsWithoutRebuild: ready("startup-no-element-"), readyMsWithRebuild: ready("startup-element-") };
  console.log(`Ready 까지: 다시 짓지 않음 ${showRange(summary.readyMsWithoutRebuild)}, 다시 지음 ${showRange(summary.readyMsWithRebuild)}`);
  return report(out, "startup.json", { sites, refs, summary, rounds });
}

// --- siteread --------------------------------------------------------------------------------------------------------

/**
 * 요청마다 사이트 파일을 읽는 값. 고친 코드는 페이지 요청 하나에 proxy 와 서버 컴포넌트가 한 번씩, 설정 경로가 한 번
 * `buildInput` 을 부른다. 그 함수를 이 프로세스에서 `--rounds` 묶음, 묶음마다 1000번 불러 한 번에 드는 시간을 낸다. 표지는
 * 읽은 값이 그 사이트 파일의 값인 것이다.
 */
async function stepSiteRead(out, { rounds: count }) {
  const sites = await loadSites();
  const resolved = createRequire(path.join(WIDGET, "package.json")).resolve("@agent-os/site-file");
  const { buildInput } = await import(pathToFileURL(resolved).href);
  const rounds = [];
  for (const name of ["A", "B"]) {
    for (let index = 1; index <= count; index += 1) {
      const started = performance.now();
      let last = null;
      for (let call = 0; call < 1000; call += 1) {
        last = buildInput({ AGENT_OS_SITE_FILE: SITE_FILES[name] });
      }
      const perCallMs = Math.round(((performance.now() - started) / 1000) * 1000) / 1000;
      const markers = { readThatFile: JSON.stringify(last) === JSON.stringify(sites[name]) };
      rounds.push({ label: `siteread-${name}-${String(index)}`, kind: "siteread", perCallMs, bytes: fs.statSync(SITE_FILES[name]).size, markers, measured: markers.readThatFile });
    }
  }
  const summary = { perCallMs: range(rounds.filter((round) => round.measured).map((round) => round.perCallMs)) };
  console.log(`buildInput 한 번: ${showRange(summary.perCallMs)}`);
  return report(out, "siteread.json", { sites, summary, rounds });
}

// --- element ---------------------------------------------------------------------------------------------------------

async function stepElement(out, { rounds: count }) {
  const sites = await loadSites();
  const rounds = [];
  const built = { A: [], B: [], sentinel: [] };
  for (let index = 1; index <= count; index += 1) {
    for (const name of ["A", "B", "sentinel"]) {
      const one = await elementBuild(out, `${name}-${String(index)}`, name);
      built[name].push(one);
      const markers = { exitZero: one.exitCode === 0, stats: one.stats !== null, fileExists: fs.existsSync(one.file) };
      rounds.push({
        label: `element-${name}-${String(index)}`,
        kind: "element-build",
        totalMs: one.totalMs,
        stats: one.stats,
        markers,
        measured: Object.values(markers).every(Boolean),
      });
      console.log(`element-${name}-${String(index)}: 프로세스 ${String(one.totalMs)}ms ${JSON.stringify(one.stats)}`);
    }
  }
  const shaOf = (name) => [...new Set(built[name].map((one) => one.stats?.sha256 ?? null))];
  const text = (name) => fs.readFileSync(built[name][0].file).toString("latin1");
  const sentinelText = text("sentinel");
  const occurrences = sentinelText.split(SENTINEL).length - 1;
  const substituted = (value) => sha256(Buffer.from(sentinelText.replaceAll(SENTINEL, value), "latin1"));
  const direct = { A: shaOf("A")[0], B: shaOf("B")[0] };
  const result = {
    reproducible: { A: shaOf("A").length === 1, B: shaOf("B").length === 1, sentinel: shaOf("sentinel").length === 1 },
    sentinelOccurrences: occurrences,
    // B 의 상한(583927)은 끝에 0 이 없어 압축기가 그대로 쓴다. A 의 상한(4000)은 `4e3` 으로 줄여 쓴다.
    substituteBDecimalEqualsDirect: substituted(String(sites.B.requestChars)) === direct.B,
    substituteADecimalEqualsDirect: substituted(String(sites.A.requestChars)) === direct.A,
    substituteAExponentEqualsDirect: substituted("4e3") === direct.A,
    directAHasExponent: /\breturn 4e3\b/.test(text("A")),
    sentinelContext: /.{40}918273645.{20}/.exec(sentinelText)?.[0] ?? null,
  };
  const markers = {
    allBuilt: rounds.every((round) => round.measured),
    // 자리표가 번들에 정확히 한 번 나와야 바꿔 넣기가 그 자리만 바꾼다.
    sentinelOnce: occurrences === 1,
    // B 로 바로 지은 파일에 B 의 상한이, 자리표로 지은 파일에는 없어야 견주기가 뜻이 있다.
    directBHasValue: text("B").includes(String(sites.B.requestChars)) && !sentinelText.includes(String(sites.B.requestChars)),
    inputsDiffer: direct.A !== direct.B && direct.B !== shaOf("sentinel")[0],
  };
  rounds.push({ label: "element-substitute", kind: "element-substitute", result, markers, measured: Object.values(markers).every(Boolean) });
  const times = (name, key) => range(built[name].filter((one) => one.stats !== null).map((one) => one.stats[key]));
  const summary = {
    processMs: range(Object.values(built).flat().map((one) => one.totalMs)),
    importMs: range(Object.values(built).flat().filter((one) => one.stats !== null).map((one) => one.stats.importMs)),
    buildMs: range(Object.values(built).flat().filter((one) => one.stats !== null).map((one) => one.stats.buildMs)),
    buildMsA: times("A", "buildMs"),
  };
  console.log(`바꿔 넣기: ${JSON.stringify(result)}`);
  console.log(`시간: 프로세스 ${showRange(summary.processMs)}, 모듈 적재 ${showRange(summary.importMs)}, Vite 빌드 ${showRange(summary.buildMs)}`);
  return report(out, "element.json", { sites, summary, substitute: result, rounds });
}

// --- standalone ------------------------------------------------------------------------------------------------------

function sizeOf(root) {
  let bytes = 0;
  let files = 0;
  let links = 0;
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const absolute = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) {
        links += 1;
      } else if (entry.isDirectory()) {
        visit(absolute);
      } else if (entry.isFile()) {
        bytes += fs.statSync(absolute).size;
        files += 1;
      }
    }
  };
  if (fs.existsSync(root)) {
    visit(root);
  }
  return { mb: Math.round((bytes / 2 ** 20) * 10) / 10, files, links };
}

async function stepStandalone(out) {
  requireTree("patched");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  const build = await widgetBuild(out, sites, "standalone-build-A", "A", { AGENT_OS_PROBE_OUTPUT: "standalone" });
  const standalone = path.join(NEXT_DIR, "standalone");
  const app = path.join(standalone, "apps", "widget");
  const serverFile = path.join(app, "server.js");
  build.markers.serverFile = fs.existsSync(serverFile);
  build.measured = Object.values(build.markers).every(Boolean);
  rounds.push(build);
  if (!build.measured) {
    console.log(`standalone 산출물이 없다: ${serverFile}`);
    return report(out, "standalone.json", { sites, refs, rounds });
  }
  const sizes = { beforeCopy: sizeOf(standalone) };
  // 문서대로 public 과 .next/static 을 standalone 아래로 복사한다(Next 16.3.6 설치본의 output 문서).
  fs.cpSync(path.join(WIDGET, "public"), path.join(app, "public"), { recursive: true });
  fs.cpSync(path.join(NEXT_DIR, "static"), path.join(app, ".next", "static"), { recursive: true });
  sizes.afterCopy = sizeOf(standalone);
  sizes.public = sizeOf(path.join(app, "public"));
  sizes.static = sizeOf(path.join(app, ".next", "static"));
  sizes.nodeModules = sizeOf(path.join(standalone, "node_modules"));
  console.log(`standalone 크기: ${JSON.stringify(sizes)}`);
  const launcher = {
    args: () => [serverFile],
    cwd: app,
    portEnv: (port) => ({ PORT: String(port), HOSTNAME: "127.0.0.1" }),
    artifactRoot: path.join(app, ".next"),
  };
  // 지은 그대로 한 번 띄워 본다. 뜨지 않으면 그 까닭을 적고, 깨진 링크가 까닭이면 고친 뒤 회차를 돈다.
  const asBuilt = await startServer(out, "standalone-as-built", {
    args: launcher.args,
    cwd: launcher.cwd,
    env: (port) => ({ ...siteEnv(out, "B"), ...launcher.portEnv(port) }),
  });
  const asBuiltStop = await stopServer(asBuilt);
  saveLines(out, "standalone-as-built.log", asBuilt.lines);
  const links = standaloneLinks(standalone);
  const broken = links.filter((link) => link.broken);
  const firstRun = {
    ready: asBuilt.ready,
    exitCode: asBuilt.exitCode,
    stop: asBuiltStop.how,
    errorLine: asBuilt.lines.find(({ text }) => /^Error: /.test(text.trim()))?.text.trim() ?? null,
    links: links.length,
    brokenLinks: broken.length,
    brokenSample: broken.slice(0, 3).map((link) => `${path.relative(standalone, link.file)} -> ${link.target}`),
  };
  console.log(`지은 그대로 띄우기: ${JSON.stringify(firstRun)}`);
  let linkFix = null;
  if (!asBuilt.ready && broken.length > 0) {
    linkFix = fixLinks(broken);
    console.log(`깨진 링크 ${String(broken.length)}개를 디렉터리 접합(junction)으로 다시 만들었다: ${JSON.stringify(linkFix)}`);
  }
  rounds.push(await serverRound(out, sites, refs, "standalone-A-start-B", build, "B", { launcher }));
  rounds.push(await serverRound(out, sites, refs, "standalone-A-start-A", build, "A", { launcher }));
  rounds.push(await serverRound(out, sites, refs, "standalone-A-start-none", build, "none", { launcher }));
  rounds.push(await standaloneMissingRound(out, build, launcher));
  return report(out, "standalone.json", { sites, refs, sizes, firstRun, linkFix, rounds });
}

/** standalone 나무의 심볼릭 링크와, 그것을 따라갔을 때 `stat` 이 되는지. */
function standaloneLinks(root) {
  const links = [];
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const file = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) {
        const target = fs.readlinkSync(file);
        let broken = false;
        try {
          fs.statSync(file);
        } catch {
          broken = true;
        }
        links.push({ file, target, resolved: path.resolve(dir, target), broken });
      } else if (entry.isDirectory()) {
        visit(file);
      }
    }
  };
  visit(root);
  return links;
}

/**
 * 따라가지 못하는 링크 가운데 가리키는 곳이 실제로 있는 디렉터리인 것을 디렉터리 접합으로 다시 만든다. Windows 에서 Next 의
 * standalone 복사가 디렉터리를 가리키는 링크를 파일 링크로 만들어 `stat` 이 EPERM 으로 끝나는 것을 돌아가는 조치다. 이
 * 스크립트가 방금 지은 `.next/standalone` 안의 링크만 건드린다.
 */
function fixLinks(broken) {
  let fixed = 0;
  let skipped = 0;
  for (const link of broken) {
    const isDirectory = fs.existsSync(link.resolved) && fs.lstatSync(link.resolved).isDirectory();
    if (!isDirectory || !link.file.startsWith(path.join(NEXT_DIR, "standalone"))) {
      skipped += 1;
      continue;
    }
    fs.unlinkSync(link.file);
    fs.symlinkSync(link.resolved, link.file, "junction");
    fixed += 1;
  }
  return { fixed, skipped };
}

/**
 * standalone 의 `server.js` 를 없는 사이트 파일로 띄우면 어떻게 되는지 본다. 시작 래퍼와 설정 파일을 거치지 않으므로 시작
 * 때의 검사가 없을 수 있다. 표지는 둘 가운데 하나다. 스스로 진단을 찍고 끝났거나, 떴고 페이지 요청이 응답을 받았다.
 */
async function standaloneMissingRound(out, build, launcher) {
  const label = "standalone-A-start-missing";
  const missing = siteEnv(out, "missing").AGENT_OS_SITE_FILE;
  const server = await startServer(out, label, {
    args: launcher.args,
    cwd: launcher.cwd,
    env: (port) => ({ AGENT_OS_SITE_FILE: missing, ...launcher.portEnv(port) }),
  });
  let page = null;
  let element = null;
  let configRoute = null;
  if (server.ready) {
    page = await get(server.port, "/widget");
    element = await get(server.port, "/widget/element.js");
    configRoute = await get(server.port, "/widget/config");
  }
  const stillUp = server.ready && !server.exited;
  const stop = await stopServer(server);
  saveLines(out, `${label}.log`, server.lines);
  const text = server.lines.map((line) => line.text).join("\n");
  const diagnostic = text.includes("파일이 없다") && text.includes(path.basename(missing));
  const markers = {
    buildMeasured: build.measured,
    fileIsMissing: !fs.existsSync(missing),
    outcomeSeen: (stillUp && page !== null && page.status !== null) || (!server.ready && server.exited && diagnostic),
    stopped: stop.ok,
  };
  const round = {
    label,
    kind: "standalone-missing",
    build: build.label,
    startSite: "missing",
    readyMs: server.readyMs,
    stillUpAfterRequests: stillUp,
    exitCode: server.exitCode,
    diagnosticInOutput: diagnostic,
    pageStatus: page?.status ?? null,
    pageCsp: page?.headers["content-security-policy"] ?? null,
    pageHasWidgetProps: page === null ? null : propsInPayload(page.body.toString("utf-8")) !== null,
    elementStatus: element?.status ?? null,
    configRouteStatus: configRoute?.status ?? null,
    stop,
    markers,
    measured: Object.values(markers).every(Boolean),
  };
  console.log(
    `${label}: Ready ${String(server.readyMs)}, 요청 뒤에도 떠 있음 ${String(stillUp)}, 페이지 ${String(round.pageStatus)}(CSP ${String(round.pageCsp)}, props ${String(round.pageHasWidgetProps)}), element.js ${String(round.elementStatus)}, 설정 경로 ${String(round.configRouteStatus)}, 출력에 진단 ${String(diagnostic)}, 측정=${String(round.measured)}`,
  );
  return round;
}

// --- live ------------------------------------------------------------------------------------------------------------

/**
 * 떠 있는 서버가 사이트 파일의 바뀐 내용을 따라가는지. 고친 코드는 요청마다 `buildInput` 을 부른다. `--out` 아래에 사이트
 * 파일의 사본(A 의 내용)을 두고 그 경로로 start 한 뒤, 서버를 끄지 않은 채 사본의 내용을 B 로 바꾸고, 그다음에 사본을 지운다.
 * 표지: 바꾸기 전에 세 자리(헤더, 페이지의 props, 설정 경로)가 모두 A 였고(서버가 그 사본을 읽는다는 양성 대조), 사본의
 * 바이트가 실제로 B 의 것으로 바뀌었고, 바꾼 뒤의 값이 알려진 후보로 갈렸고, 그동안 서버가 끝나지 않았다(같은 프로세스다).
 * 결과는 바꾼 뒤의 값이 A(시작 때 읽은 값이 남는다)인지 B(다시 띄우지 않아도 따라간다)인지다. 지운 뒤의 응답은 관찰로 적는다.
 */
async function stepLive(out) {
  requireTree("patched");
  const sites = await loadSites();
  const refs = await elementRefs(out);
  const rounds = [];
  const build = await widgetBuild(out, sites, "live-build-A", "A");
  rounds.push(build);
  const copy = path.join(out, "live-site.toml");
  fs.copyFileSync(SITE_FILES.A, copy);
  const label = "live-A-then-B-then-removed";
  const server = await startServer(out, label, {
    args: WRAPPER_START.args,
    cwd: WRAPPER_START.cwd,
    env: () => ({ AGENT_OS_SITE_FILE: copy }),
  });
  const places = (seen) =>
    seen === null ? null : { cspPage: seen.site.cspPage, htmlProps: seen.site.htmlProps, rscProps: seen.site.rscProps, configRoute: seen.site.configRoute, element: seen.site.element };
  let before = null;
  let after = null;
  let removed = null;
  let swapped = false;
  let upThroughout = false;
  let stop;
  try {
    if (server.ready) {
      before = await observe(out, sites, refs, "live-before", server.port);
      fs.copyFileSync(SITE_FILES.B, copy);
      swapped = sha256(fs.readFileSync(copy)) === sha256(fs.readFileSync(SITE_FILES.B));
      after = await observe(out, sites, refs, "live-after", server.port);
      const upAfterSwap = !server.exited;
      fs.rmSync(copy);
      const page = await get(server.port, "/widget");
      const configRoute = await get(server.port, "/widget/config");
      const element = await get(server.port, "/widget/element.js");
      removed = {
        fileGone: !fs.existsSync(copy),
        pageStatus: page.status,
        pageCsp: page.headers["content-security-policy"] ?? null,
        pageHasWidgetProps: propsInPayload(page.body.toString("utf-8")) !== null,
        configRouteStatus: configRoute.status,
        elementStatus: element.status,
        stillUp: !server.exited,
      };
      upThroughout = upAfterSwap;
    }
  } finally {
    stop = await stopServer(server);
    saveLines(out, `${label}.log`, server.lines);
    fs.rmSync(copy, { force: true });
  }
  const followed = ["cspPage", "htmlProps", "rscProps", "configRoute"];
  const markers = {
    buildMeasured: build.measured,
    ready: server.ready,
    beforeIsA: before !== null && followed.every((place) => before.site[place] === "A"),
    swapped,
    afterClassified: after !== null && followed.every((place) => SITE_NAMES.includes(after.site[place])),
    sameProcess: upThroughout,
    removedSeen: removed !== null && removed.fileGone && removed.pageStatus !== null,
    stopped: stop.ok,
  };
  const round = {
    label,
    kind: "live",
    build: build.label,
    readyMs: server.readyMs,
    pid: server.pid,
    before: places(before),
    after: places(after),
    afterCspRaw: after?.cspRaw.page ?? null,
    removed,
    stop,
    markers,
    measured: Object.values(markers).every(Boolean),
  };
  rounds.push(round);
  console.log(`${label}: 측정=${String(round.measured)}`);
  console.log(`  바꾸기 전: ${JSON.stringify(round.before)}`);
  console.log(`  B 로 바꾼 뒤(같은 프로세스): ${JSON.stringify(round.after)}`);
  console.log(`  지운 뒤: ${JSON.stringify(removed)}`);
  return report(out, "live.json", { sites, refs, rounds });
}

// --- 진입 ------------------------------------------------------------------------------------------------------------

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: { out: { type: "string" }, rounds: { type: "string", default: "3" } },
});
const [step] = positionals;
const steps = {
  control: (out) => stepControl(out),
  runtime: (out) => stepRuntime(out),
  forks: (out) => stepForks(out),
  element: (out) => stepElement(out, { rounds: Number(values.rounds) }),
  startup: (out) => stepStartup(out, { rounds: Number(values.rounds) }),
  siteread: (out) => stepSiteRead(out, { rounds: Number(values.rounds) }),
  standalone: (out) => stepStandalone(out),
  live: (out) => stepLive(out),
};
if (step === undefined || !(step in steps) || values.out === undefined || !path.isAbsolute(values.out)) {
  console.error(`사용: node measure.mjs <${Object.keys(steps).join("|")}> --out <절대 경로> [--rounds N]`);
  process.exit(2);
}
const outDir = path.resolve(values.out);
const fromRepo = path.relative(REPO, outDir);
if (!fromRepo.startsWith("..") && !path.isAbsolute(fromRepo)) {
  console.error(`--out 은 저장소 밖이어야 한다: ${outDir}`);
  process.exit(2);
}
assertLayout();
fs.mkdirSync(outDir, { recursive: true });
const unmeasuredCount = await steps[step](outDir);
process.exit(unmeasuredCount === 0 ? 0 : 1);
