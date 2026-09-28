#!/usr/bin/env node
// web-admin 설계 인터뷰의 생성기 측정. 저장소 루트의 openapi.json 을 원본(3.1.0), "openapi" 만 3.2.0 으로
// 바꾼 사본, 경로에 admin/channel 태그를 붙인 사본으로 나눠 생성기 넷에 돌리고 결과를 잰다.
//
//   node .scratch/web-admin/probes/gen_run.mjs <작업 디렉터리> [--versions] [--java-home <JDK 경로>]
//
// 작업 디렉터리에 고정 버전으로 npm install 하고(처음 한 번), specs/·out/·logs/·probe/ 를 만들고,
// 끝에 summary.json 을 쓰고 요약을 찍는다. --versions 는 npm view 로 최신 버전 표를 먼저 찍는다.
// openapi-generator 는 Java 11 이상이 있어야 돈다(래퍼가 PATH 의 java 를 부른다). --java-home 이나
// JAVA_HOME 의 bin 을 PATH 앞에 붙인다. 처음 돌 때 래퍼가 Maven Central 에서 jar(약 31MB)를 받는다.
// 네트워크: npm 레지스트리, Maven Central. 루프백 포트 하나를 연다(gen_rt_probe.ts).
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "../../..");
const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const opt = (name) => (argv.includes(name) ? argv[argv.indexOf(name) + 1] : undefined);
const positional = argv.filter((a, i) => !a.startsWith("--") && argv[i - 1] !== "--java-home");
if (positional.length !== 1) {
  console.error("쓰는 법: node gen_run.mjs <작업 디렉터리> [--versions] [--java-home <JDK 경로>]");
  process.exit(2);
}
const WORK = path.resolve(positional[0]);
fs.mkdirSync(WORK, { recursive: true });

// 2026-09-28 에 잰 판. 바꾸면 결과가 바뀐다.
const PINNED = {
  "openapi-typescript": "7.13.0",
  "openapi-fetch": "0.17.0",
  "@hey-api/openapi-ts": "0.99.0",
  orval: "8.38.0",
  swr: "2.5.1",
  "@tanstack/react-query": "5.104.0",
  react: "19.3.0",
  "@types/react": "19.3.0",
  typescript: "5.9.3",
  esbuild: "0.28.2",
  "@openapitools/openapi-generator-cli": "2.41.0",
};
const OGEN_JAR = "7.25.0";
const TS7 = "7.0.2";
const LATEST = [
  "openapi-typescript", "openapi-fetch", "@hey-api/openapi-ts", "orval", "swr", "@tanstack/react-query",
  "next", "react", "typescript", "vitest", "@playwright/test", "msw", "tailwindcss", "eslint",
  "typescript-eslint", "eslint-plugin-boundaries", "@biomejs/biome", "prettier", "lucide-react",
  "zustand", "storybook",
];

const stripAnsi = (s) => s.replace(/\x1b\[[0-9;]*m/g, "");
function sh(cmd, { cwd = WORK, env = process.env, timeout = 600000 } = {}) {
  // openapi-generator-cli 래퍼는 openapitools.json 을 process.cwd() 가 아니라 PWD(없으면 INIT_CWD)에 쓴다.
  // Git Bash 가 넘긴 PWD 가 저장소 루트면 거기에 파일이 생기므로 cwd 로 덮는다.
  const e = { ...env, PWD: cwd, INIT_CWD: cwd };
  const r = spawnSync(cmd, { cwd, env: e, shell: true, encoding: "utf8", timeout, maxBuffer: 256 * 1024 * 1024 });
  return { code: r.status, out: stripAnsi(`${r.stdout ?? ""}${r.stderr ?? ""}`) };
}
const w = (rel, text) => {
  const p = path.join(WORK, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, text);
};
const exists = (rel) => fs.existsSync(path.join(WORK, rel));
const read = (rel) => fs.readFileSync(path.join(WORK, rel), "utf8");
const NODE_BIN = {
  ots: "node node_modules/openapi-typescript/bin/cli.js",
  hey: "node node_modules/@hey-api/openapi-ts/bin/run.js",
  orval: "node node_modules/orval/dist/bin/orval.mjs",
  tsc5: "node node_modules/typescript/bin/tsc",
  tsc7: "node ts7/node_modules/typescript/bin/tsc",
  ogen: "node node_modules/@openapitools/openapi-generator-cli/main.js",
  esbuild: "node node_modules/esbuild/bin/esbuild",
};

// 1. 최신 버전
const summary = { measuredAt: new Date().toISOString(), node: process.version, pinned: PINNED };
if (flag("--versions")) {
  summary.latest = {};
  for (const p of LATEST) summary.latest[p] = sh(`npm view ${p} version`).out.trim().split(/\r?\n/).pop();
  console.log("최신 버전:", summary.latest);
}

// 2. 설치
if (!exists("node_modules/.package-lock.json")) {
  w("package.json", JSON.stringify({ name: "gen-probe", private: true, type: "module", devDependencies: PINNED }, null, 2));
  const r = sh("npm install --no-audit --no-fund");
  if (r.code !== 0) throw new Error(`npm install 실패\n${r.out}`);
}
if (!exists("ts7/node_modules/typescript")) {
  w("ts7/package.json", JSON.stringify({ name: "ts7", private: true }));
  sh(`npm install --no-audit --no-fund typescript@${TS7}`, { cwd: path.join(WORK, "ts7") });
}

// 3. 명세 사본
const src = fs.readFileSync(path.join(REPO, "openapi.json"), "utf8");
const v32 = src.replace('"openapi": "3.1.0"', '"openapi": "3.2.0"');
if (v32 === src) throw new Error('openapi.json 이 "openapi": "3.1.0" 을 선언하지 않는다. 측정의 전제가 바뀌었다');
const withTags = (text) => {
  const d = JSON.parse(text);
  for (const [p, ops] of Object.entries(d.paths))
    for (const op of Object.values(ops)) op.tags = [p.startsWith("/runs") ? "channel" : "admin"];
  return `${JSON.stringify(d, null, 2)}\n`;
};
w("specs/v31.json", src);
w("specs/v32.json", v32);
w("specs/v31-tags.json", withTags(src));
w("specs/v32-tags.json", withTags(v32));

// 4. 생성기 실행
w("cfg/hey-bytags-v31.config.mjs", heyCfg("v31", "hey-bytags", "{ name: '@hey-api/sdk', operations: 'byTags' }"));
w("cfg/hey-bytags-v31-tags.config.mjs", heyCfg("v31-tags", "hey-bytags", "{ name: '@hey-api/sdk', operations: 'byTags' }"));
w("cfg/hey-enums-v31.config.mjs", heyCfg("v31", "hey-enums", "'@hey-api/sdk'", "{ name: '@hey-api/typescript', enums: 'typescript' }"));
w("cfg/orval-enum-v32.config.mjs", orvalCfg("v32", "orval-enum", "{ enumGenerationType: 'enum' }"));
w("cfg/orval-novalid-v31.config.mjs", orvalCfg("v31", "orval-novalid", "{}", "unsafeDisableValidation: true"));
function heyCfg(spec, dir, sdk, ts = "'@hey-api/typescript'") {
  return `export default { input: './specs/${spec}.json', output: './out/${dir}/${spec}', plugins: [${ts}, ${sdk}] };\n`;
}
// orval 은 설정 파일의 경로를 그 파일 기준으로 푼다(hey 는 cwd 기준).
function orvalCfg(spec, dir, override, inputExtra = "") {
  return `export default { api: { input: { target: '../specs/${spec}.json', ${inputExtra} }, output: { target: '../out/${dir}/${spec}/api.ts', client: 'fetch', override: ${override} } } };\n`;
}
const jobs = [];
const job = (id, cmd, out) => jobs.push({ id, cmd, out });
for (const s of ["v31", "v32", "v31-tags"]) {
  job(`ots/${s}`, `${NODE_BIN.ots} specs/${s}.json -o out/ots/${s}.ts`, `out/ots/${s}.ts`);
  job(`hey/${s}`, `${NODE_BIN.hey} -i ./specs/${s}.json -o ./out/hey/${s} --no-log-file`, `out/hey/${s}`);
}
job("ots-immutable/v31", `${NODE_BIN.ots} specs/v31.json -o out/ots-immutable/v31.ts --immutable`, "out/ots-immutable/v31.ts");
job("ots-enum/v31", `${NODE_BIN.ots} specs/v31.json -o out/ots-enum/v31.ts --enum`, "out/ots-enum/v31.ts");
for (const s of ["v31", "v31-tags"])
  job(`hey-bytags/${s}`, `${NODE_BIN.hey} -f ./cfg/hey-bytags-${s}.config.mjs --no-log-file`, `out/hey-bytags/${s}`);
job("hey-enums/v31", `${NODE_BIN.hey} -f ./cfg/hey-enums-v31.config.mjs --no-log-file`, "out/hey-enums/v31");
for (const s of ["v31", "v32", "v32-tags"])
  job(`orval-fetch/${s}`, `${NODE_BIN.orval} -i ./specs/${s}.json -o ./out/orval-fetch/${s}/api.ts --client fetch`, `out/orval-fetch/${s}`);
for (const c of ["swr", "react-query"])
  for (const s of ["v31", "v32"])
    job(`orval-${c}/${s}`, `${NODE_BIN.orval} -i ./specs/${s}.json -o ./out/orval-${c}/${s}/api.ts --client ${c}`, `out/orval-${c}/${s}`);
for (const s of ["v32", "v32-tags"])
  job(`orval-tags-split/${s}`, `${NODE_BIN.orval} -i ./specs/${s}.json -o ./out/orval-tags-split/${s}/api.ts --client fetch --mode tags-split`, `out/orval-tags-split/${s}`);
job("orval-enum/v32", `${NODE_BIN.orval} -c ./cfg/orval-enum-v32.config.mjs`, "out/orval-enum/v32");
job("orval-novalid/v31", `${NODE_BIN.orval} -c ./cfg/orval-novalid-v31.config.mjs`, "out/orval-novalid/v31");

const javaHome = opt("--java-home") ?? process.env.JAVA_HOME;
const env = { ...process.env };
if (javaHome) {
  const key = Object.keys(env).find((k) => k.toUpperCase() === "PATH") ?? "PATH";
  env[key] = `${path.join(javaHome, "bin")}${path.delimiter}${env[key]}`;
}
const javaVersion = sh("java -version", { env }).out.split(/\r?\n/)[0];
summary.java = javaVersion;
const javaMajor = Number((javaVersion.match(/version "(\d+)(?:\.(\d+))?/) ?? []).slice(1).find((n) => n !== "1") ?? 0);
if (javaMajor >= 11) {
  w("openapitools.json", JSON.stringify({ "generator-cli": { version: OGEN_JAR } }, null, 2));
  for (const s of ["v31", "v32"])
    job(`ogen/${s}`, `${NODE_BIN.ogen} generate -i specs/${s}.json -g typescript-fetch -o out/ogen/${s}`, `out/ogen/${s}`);
  for (const s of ["v31", "v32", "v31-tags"])
    job(`ogen-skip/${s}`, `${NODE_BIN.ogen} generate -i specs/${s}.json -g typescript-fetch -o out/ogen-skip/${s} --skip-validate-spec`, `out/ogen-skip/${s}`);
  job("ogen-skip-enum/v31", `${NODE_BIN.ogen} generate -i specs/v31.json -g typescript-fetch -o out/ogen-skip-enum/v31 --skip-validate-spec --additional-properties=stringEnums=true`, "out/ogen-skip-enum/v31");
} else {
  summary.ogen = `Java 11 이상이 없어 돌리지 않았다 (${javaVersion})`;
}

const tsFiles = (rel) => {
  const p = path.join(WORK, rel);
  if (!fs.existsSync(p)) return [];
  if (fs.statSync(p).isFile()) return [rel];
  return fs.readdirSync(p, { recursive: true }).map((f) => path.join(rel, f)).filter((f) => f.endsWith(".ts"));
};
const noteLines = (out) =>
  out.split(/\r?\n/).filter((l) => /error|fail|exception|unexpected|warn|invalid/i.test(l) && !/^\s+at /.test(l)).slice(0, 8);
function escapes(text) {
  const code = text.split(/\r?\n/).filter((l) => !/^\s*(\*|\/\/|\/\*)/.test(l));
  const count = (re) => code.filter((l) => re.test(l)).length;
  return {
    anyLines: count(/\bany\b/),
    asCastLines: count(/\bas (?!const\b)[A-Za-z{(\[]/),
    tsDirectives: count(/@ts-(ignore|expect-error|nocheck)/),
  };
}
summary.jobs = {};
for (const j of jobs) {
  fs.rmSync(path.join(WORK, j.out), { recursive: true, force: true });
  const r = sh(j.cmd, { env });
  w(`logs/${j.id.replace("/", "__")}.log`, `$ ${j.cmd}\n${r.out}`);
  const files = tsFiles(j.out);
  const text = files.map((f) => read(f)).join("\n");
  const imports = [...new Set([...text.matchAll(/from ['"]([^.'"][^'"]*)['"]/g)].map((m) => m[1]))];
  summary.jobs[j.id] = {
    exit: r.code,
    notes: noteLines(r.out),
    files: files.length,
    lines: files.reduce((n, f) => n + (read(f).match(/\n/g) ?? []).length, 0), // wc -l 과 같게
    externalImports: imports,
    escapes: escapes(text),
    readonlyLines: text.split(/\r?\n/).filter((l) => /^\s*readonly\s/.test(l)).length,
    facts: files.length ? facts(j.id.split("/")[0], files, text) : {},
  };
}

// 5. 생성물에서 읽는 사실(SSE 응답의 타입, 유니온과 열거의 선언)
function facts(kind, files, text) {
  const first = (re) => (text.match(re) ?? [])[0]?.replace(/\s+/g, " ").slice(0, 220);
  const decl = (name) =>
    first(new RegExp(`(export (type|interface|const|enum) ${name}\\b[^;{]*[;{]?[^\\n]*|\\b${name}: [^\\n]*)`));
  const f = {};
  if (kind.startsWith("ots")) f.sse = first(/"text\/event-stream": [^;]*;/);
  if (kind.startsWith("hey")) {
    f.sse = first(/export type StartRunResponses = \{[\s\S]*?\};/);
    f.sseCall = first(/startRun[^=\n]*=[^\n]*Promise<[^\n]*?>\s*=>/) ?? first(/static startRun[^\n]*/);
  }
  if (kind.startsWith("orval")) {
    f.sse200 = first(/export type startRunResponse200\b[^\n]*/) ?? "startRunResponse200 없음";
    f.sse = first(/export type startRunResponse = [^\n]*/);
  }
  if (kind.startsWith("ogen")) f.sse = first(/async startRun\([^\n]*/);
  for (const n of ["Event", "PluginRow", "TraceEvent", "PluginKind", "RunStatus", "ErrorCode", "Json"]) f[n] = decl(n);
  f.containers = [...new Set([...text.matchAll(/export class (\w+)/g)].map((m) => m[1]))];
  f.fileNames = files.map((x) => x.split(path.sep).join("/").split("/").slice(3).join("/")).slice(0, 12);
  return f;
}

// 6. 태그를 붙이면 생성물이 바뀌나
const same = (a, b) => {
  const fa = tsFiles(a).map((f) => path.relative(path.join(WORK, a), path.join(WORK, f)));
  const fb = tsFiles(b).map((f) => path.relative(path.join(WORK, b), path.join(WORK, f)));
  if (!fa.length || !fb.length) return "비교할 생성물 없음";
  if (fa.join() !== fb.join()) {
    const gone = fa.filter((f) => !fb.includes(f));
    const added = fb.filter((f) => !fa.includes(f));
    return `파일 구성이 다르다: 빠짐 [${gone.join(", ")}], 생김 [${added.join(", ")}]`;
  }
  const diff = fa.filter((f) => read(path.join(a, f)) !== read(path.join(b, f)));
  return diff.length ? `내용이 다르다: ${diff.join(", ")}` : "같다";
};
summary.tags = {
  "ots 기본": same("out/ots/v31.ts", "out/ots/v31-tags.ts"),
  "hey 기본(flat)": same("out/hey/v31", "out/hey/v31-tags"),
  "hey operations=byTags": same("out/hey-bytags/v31", "out/hey-bytags/v31-tags"),
  "orval fetch 기본(single)": same("out/orval-fetch/v32", "out/orval-fetch/v32-tags"),
  "orval mode=tags-split": same("out/orval-tags-split/v32", "out/orval-tags-split/v32-tags"),
  "ogen(검증 건너뜀)": same("out/ogen-skip/v31", "out/ogen-skip/v31-tags"),
};
summary.threeTwoVsThreeOne = {
  ots: same("out/ots/v31.ts", "out/ots/v32.ts"),
  hey: same("out/hey/v31", "out/hey/v32"),
  "orval(3.1 은 unsafeDisableValidation)": same("out/orval-novalid/v31", "out/orval-fetch/v32"),
};

// 7. 타입 탐침: never 에 대입해 추론된 타입을 에러 문구로 드러내고, 판별 유니온이 좁혀지는지 본다
const NARROW = (E, T, P) => `
export function narrow(e: ${E}, t: ${T}, p: ${P}): string[] {
  const out: string[] = [];
  if (e.type === "run_started") out.push(e.agent);
  if (t.type === "unknown") out.push(t.raw);
  if ("manifest" in p) out.push(p.manifest.name);
  else out.push(p.reason);
  return out;
}
`;
const PROBES = {
  "ots-v31": `import createClient from "openapi-fetch";
import type { components, paths } from "../out/ots/v31";
type S = components["schemas"];
const client = createClient<paths>({ baseUrl: "http://127.0.0.1:1" });
export async function reveal(j: S["Json"]): Promise<void> {
  const r = await client.POST("/runs", { body: { agent: "a", request: "x" } });
  const REVEAL_sse_default_data: never = r.data;
  const s = await client.POST("/runs", { body: { agent: "a", request: "x" }, parseAs: "stream" });
  const REVEAL_sse_stream_data: never = s.data;
  const REVEAL_sse_error: never = r.error;
  const REVEAL_json: never = j;
  void [REVEAL_sse_default_data, REVEAL_sse_stream_data, REVEAL_sse_error, REVEAL_json];
}
${NARROW('S["Event"]', 'S["TraceEvent"]', 'S["PluginRow"]')}`,
  "hey-v31": `import { listPlugins, startRun } from "../out/hey/v31";
import type { Event, Json, PluginRow, TraceEvent } from "../out/hey/v31";
export async function reveal(j: Json): Promise<void> {
  const r = await startRun({ body: { agent: "a", request: "x" } });
  for await (const item of r.stream) {
    const REVEAL_sse_item: never = item;
    void REVEAL_sse_item;
  }
  const p = await listPlugins();
  const REVEAL_plugins_data: never = p.data;
  const REVEAL_json: never = j;
  void [REVEAL_plugins_data, REVEAL_json];
}
${NARROW("Event", "TraceEvent", "PluginRow")}`,
  "orval-fetch-v32": `import { startRun } from "../out/orval-fetch/v32/api";
import type { Event, Json, PluginRow, TraceEvent } from "../out/orval-fetch/v32/api";
export async function reveal(j: Json): Promise<void> {
  const r = await startRun({ agent: "a", request: "x" });
  const REVEAL_sse_status: never = r.status;
  const REVEAL_sse_data: never = r.data;
  const REVEAL_json: never = j;
  void [REVEAL_sse_status, REVEAL_sse_data, REVEAL_json];
}
${NARROW("Event", "TraceEvent", "PluginRow")}`,
  "orval-hooks-v32": `export * as swr from "../out/orval-swr/v32/api";
export * as rq from "../out/orval-react-query/v32/api";
`,
  "ogen-skip-v31": `import { Configuration, DefaultApi } from "../out/ogen-skip/v31";
import type { Event, PluginRow, ToolCall, TraceEvent } from "../out/ogen-skip/v31";
export async function reveal(a: ToolCall["args"]): Promise<void> {
  const api = new DefaultApi(new Configuration({ basePath: "http://127.0.0.1:1" }));
  const r = await api.startRun({ startRun: { agent: "a", request: "x" } });
  const REVEAL_sse_data: never = r;
  const REVEAL_json_args: never = a;
  void [REVEAL_sse_data, REVEAL_json_args];
}
${NARROW("Event", "TraceEvent", "PluginRow")}`,
};
const TSCONFIG = (file, extra = {}) =>
  JSON.stringify({
    compilerOptions: {
      strict: true, noEmit: true, target: "ES2022", module: "ESNext", moduleResolution: "Bundler",
      lib: ["ES2022", "DOM", "DOM.Iterable"], skipLibCheck: true, jsx: "react-jsx", types: [], ...extra,
    },
    files: [file],
  });
const STRICT_PLUS = {
  noUncheckedIndexedAccess: true, exactOptionalPropertyTypes: true, noImplicitOverride: true,
  noPropertyAccessFromIndexSignature: true, verbatimModuleSyntax: true, noImplicitReturns: true,
  noFallthroughCasesInSwitch: true,
};
function tsc(bin, cfg, probeText) {
  const r = sh(`${bin} -p ${cfg}`);
  const lines = probeText.split(/\r?\n/);
  const reveals = {};
  const other = [];
  for (const m of r.out.matchAll(/^(\S+?)\((\d+),\d+\): error (TS\d+): (.*)$/gm)) {
    const [, file, line, codeId, msg] = m;
    const v = /probe[\\/]/.test(file) ? (lines[Number(line) - 1].match(/REVEAL_\w+/) ?? [])[0] : undefined;
    const t = msg.match(/^Type '(.*)' is not assignable to type 'never'\.$/);
    if (v && t) reveals[v] = t[1];
    else other.push(`${file}(${line}) ${codeId} ${msg.slice(0, 160)}`);
  }
  return { exit: r.code, reveals, otherErrors: other };
}
summary.typeProbes = {};
for (const [id, text] of Object.entries(PROBES)) {
  const outDir = { "ots-v31": "out/ots/v31.ts", "hey-v31": "out/hey/v31", "orval-fetch-v32": "out/orval-fetch/v32", "orval-hooks-v32": "out/orval-swr/v32", "ogen-skip-v31": "out/ogen-skip/v31" }[id];
  if (!exists(outDir)) {
    summary.typeProbes[id] = "생성물이 없어 건너뜀";
    continue;
  }
  w(`probe/${id}.ts`, text);
  w(`probe/tsconfig.${id}.json`, TSCONFIG(`${id}.ts`));
  w(`probe/tsconfig.${id}.nolibskip.json`, TSCONFIG(`${id}.ts`, { skipLibCheck: false }));
  w(`probe/tsconfig.${id}.strictplus.json`, TSCONFIG(`${id}.ts`, STRICT_PLUS));
  summary.typeProbes[id] = {
    [`tsc ${PINNED.typescript}`]: tsc(NODE_BIN.tsc5, `probe/tsconfig.${id}.json`, text),
    [`tsc ${TS7}`]: tsc(NODE_BIN.tsc7, `probe/tsconfig.${id}.json`, text),
    [`tsc ${PINNED.typescript} skipLibCheck=false`]: tsc(NODE_BIN.tsc5, `probe/tsconfig.${id}.nolibskip.json`, text),
    [`tsc ${PINNED.typescript} strict+`]: tsc(NODE_BIN.tsc5, `probe/tsconfig.${id}.strictplus.json`, text),
  };
}

// 8. typescript 7 이 설치된 자리에서 생성기가 도나(openapi-typescript 와 hey 는 컴파일러 API 로 코드를 짓는다)
const RT7 = path.join(WORK, "rt7");
fs.mkdirSync(RT7, { recursive: true });
fs.writeFileSync(path.join(RT7, "package.json"), JSON.stringify({ name: "rt7", private: true, type: "module" }));
const gens = `openapi-typescript@${PINNED["openapi-typescript"]} @hey-api/openapi-ts@${PINNED["@hey-api/openapi-ts"]} orval@${PINNED.orval} typescript@${TS7}`;
const strictInstall = sh(`npm install --dry-run --no-audit --no-fund ${gens}`, { cwd: RT7 });
summary.ts7 = { npmInstallWithoutLegacyPeerDeps: { exit: strictInstall.code, eresolve: /ERESOLVE/.test(strictInstall.out), notes: noteLines(strictInstall.out).slice(0, 4) } };
if (!fs.existsSync(path.join(RT7, "node_modules/typescript"))) sh(`npm install --no-audit --no-fund --legacy-peer-deps ${gens}`, { cwd: RT7 });
const rt7 = (cmd) => {
  const r = sh(cmd, { cwd: RT7 });
  return { exit: r.code, notes: r.out.split(/\r?\n/).filter((l) => /Error|error/.test(l) && !/^\s+at /.test(l)).slice(0, 2) };
};
summary.ts7.generators = {
  ots: rt7("node node_modules/openapi-typescript/bin/cli.js ../specs/v31.json -o out/ots.ts"),
  hey: rt7("node node_modules/@hey-api/openapi-ts/bin/run.js -i ../specs/v31.json -o ./out/hey --no-log-file"),
  orval: rt7("node node_modules/orval/dist/bin/orval.mjs -i ../specs/v32.json -o ./out/orval/api.ts --client fetch"),
};

// 9. 실제로 SSE 를 받으면(루프백 스텁)
if (exists("out/ots/v31.ts") && exists("out/hey/v31") && exists("out/orval-fetch/v32")) {
  fs.copyFileSync(path.join(HERE, "gen_rt_probe.ts"), path.join(WORK, "probe/rt.ts"));
  const b = sh(`${NODE_BIN.esbuild} probe/rt.ts --bundle --platform=node --format=esm --outfile=probe/rt.bundle.mjs --log-level=warning`);
  const r = b.code === 0 ? sh("node probe/rt.bundle.mjs", { timeout: 120000 }) : b;
  try {
    summary.runtime = JSON.parse(r.out.trim().split(/\r?\n/).pop());
  } catch {
    summary.runtime = { error: r.out.slice(0, 400) };
  }
}

fs.writeFileSync(path.join(WORK, "summary.json"), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary, null, 2));
console.log(`\n요약을 ${path.join(WORK, "summary.json")} 에 썼다.`);
