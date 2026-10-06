// design-system 사진 비교 도구 프로브: Storybook 정적 빌드의 스토리를 판을 고정한 Playwright Linux Docker 이미지에서
// Playwright 의 toHaveScreenshot 으로 찍고 비교하는 길이 서는지 잰다. visual_docker 프로브(표본 HTML)의 다음이고,
// 이번 표본은 tokens/setup.mjs 가 얹은 실제 디자인 토큰·글꼴(Noto Sans KR 동적 서브셋 등)과 스토리다.
//   node .scratch/design-system/probes/tokens/measure.mjs <작업 루트>/storybook     (먼저. storybook-static 을 짓는다)
//   node .scratch/design-system/probes/tokens/visual.mjs <작업 루트>/storybook --work <작업 폴더> [--image <이미지>]
//
// 하는 일
//   준비  <작업 폴더>(저장소 밖)에 probe/(visual.config.mjs, visual.spec.mjs), site/(storybook-static 사본),
//         node_modules/(사본 web/ 에 깔린 @playwright/test·playwright·playwright-core 를 pnpm 링크를 풀어 실체 복사)
//   실행  A: 컨테이너, 정답을 out/A/baseline 에 쓴다. B: 새 컨테이너, A 의 정답과 비교. H: Windows 호스트, A 와 비교.
//         컨테이너는 `docker run --rm --init --ipc=host --network none` 이고 작업 폴더를 /work 에 bind 한다.
//         L: 사본 web/ 을 같은 이미지의 컨테이너 안에서(네트워크를 쓴다) 설치하고 정적 빌드를 지은 뒤, 그 빌드를 A 의
//         정답과 비교한다(Windows 에서 지은 빌드의 정답을 Linux 에서 지은 빌드가 지나는지)
//   비교  실행마다 원본 사진(raw/*.png)의 sha256 을 쌍(A·B, A·H, A·L)으로 맞대고, toHaveScreenshot(maxDiffPixels 0)의 통과 수
// 결과는 <작업 폴더>/result.json. 이미지는 이미 있어야 한다(visual_docker 의 --pull 이 받았다).

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const args = process.argv.slice(2);
const option = (name) => {
  const i = args.indexOf(name);
  return i === -1 ? null : args[i + 1];
};
const ws = resolve(args[0] ?? ".");
const workOption = option("--work");
const image = option("--image") ?? "mcr.microsoft.com/playwright:v1.63.0-noble";
if (workOption === null) {
  console.error("--work <작업 폴더> 가 필요하다(저장소 밖)");
  process.exit(2);
}
const work = resolve(workOption);
if (!relative(REPO, work).startsWith("..")) {
  console.error(`작업 폴더가 저장소 안이다: ${work}`);
  process.exit(2);
}
const staticDir = join(ws, "web", "packages", "ui", "storybook-static");
if (!existsSync(join(staticDir, "iframe.html"))) {
  console.error(`storybook-static 이 없다. measure.mjs 를 먼저 돌린다: ${staticDir}`);
  process.exit(2);
}

function sh(command, commandArgs, options = {}) {
  const started = Date.now();
  const result = spawnSync(command, commandArgs, { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024, ...options });
  return { status: result.status, ms: Date.now() - started, output: `${result.stdout ?? ""}${result.stderr ?? ""}` };
}
const tail = (text, count = 20) => text.split(/\r?\n/).filter((line) => line.trim() !== "").slice(-count);

// 준비
for (const sub of ["probe", "site", "node_modules", "out"]) {
  rmSync(join(work, sub), { recursive: true, force: true });
}
mkdirSync(join(work, "probe"), { recursive: true });
mkdirSync(join(work, "out"), { recursive: true });
cpSync(staticDir, join(work, "site"), { recursive: true });
for (const file of ["visual.config.mjs", "visual.spec.mjs"]) {
  cpSync(join(HERE, file), join(work, "probe", file));
}
const admin = createRequire(join(ws, "web", "apps", "admin", "package.json"));
const testDir = realpathSync(dirname(admin.resolve("@playwright/test/package.json")));
const playwrightDir = realpathSync(dirname(createRequire(join(testDir, "package.json")).resolve("playwright/package.json")));
const coreDir = realpathSync(dirname(createRequire(join(playwrightDir, "package.json")).resolve("playwright-core/package.json")));
const versions = {};
for (const [name, from] of Object.entries({ "@playwright/test": testDir, playwright: playwrightDir, "playwright-core": coreDir })) {
  cpSync(from, join(work, "node_modules", ...name.split("/")), {
    recursive: true,
    dereference: true,
    filter: (source) => !relative(from, source).split(sep).includes("node_modules"),
  });
  versions[name] = JSON.parse(readFileSync(join(from, "package.json"), "utf-8")).version;
}

function runContainer(label, mode, site = "/work/site") {
  mkdirSync(join(work, "out", label), { recursive: true });
  const result = sh("docker", [
    "run", "--rm", "--init", "--ipc=host", "--network", "none",
    "--mount", `type=bind,source=${work},target=/work`,
    "-e", `VISUAL_SITE=${site}`,
    "-e", `VISUAL_OUT=/work/out/${label}`,
    "-e", "VISUAL_BASELINE=/work/out/A/baseline",
    "-e", `VISUAL_MODE=${mode}`,
    "-w", "/work/probe",
    image,
    "node", "/work/node_modules/@playwright/test/cli.js", "test", "-c", "/work/probe/visual.config.mjs",
  ]);
  return { label, where: "container", mode, status: result.status, ms: result.ms, outputTail: tail(result.output) };
}

function runHost(label, mode) {
  mkdirSync(join(work, "out", label), { recursive: true });
  const result = sh(process.execPath, [join(work, "node_modules", "@playwright", "test", "cli.js"), "test", "-c", join(work, "probe", "visual.config.mjs")], {
    cwd: join(work, "probe"),
    env: {
      ...process.env,
      VISUAL_SITE: join(work, "site"),
      VISUAL_OUT: join(work, "out", label),
      VISUAL_BASELINE: join(work, "out", "A", "baseline"),
      VISUAL_MODE: mode,
    },
  });
  return { label, where: "host", mode, status: result.status, ms: result.ms, outputTail: tail(result.output) };
}

// Linux 빌드: 사본 web/ 을(설치물과 산출물을 빼고) 컨테이너 안으로 복사해 설치하고 정적 빌드를 짓는다. 설치는 네트워크를
// 쓴다(corepack 이 pnpm 11.24.0 을, pnpm 이 Linux 네이티브 패키지를 받는다). 설치물은 컨테이너 안에만 두고 정적 빌드만
// 밖으로 낸다. CI 의 사진 잡이 Linux 에서 지을 것과 같은 길이다.
function buildLinux() {
  const src = join(work, "linux-src");
  rmSync(src, { recursive: true, force: true });
  const skipped = new Set(["node_modules", ".next", "dist", "storybook-static", "test-results", "playwright-report", "blob-report", "coverage"]);
  cpSync(join(ws, "web"), join(src, "web"), { recursive: true, filter: (source) => !skipped.has(source.split(/[\\/]/).pop() ?? "") });
  const script = [
    "set -e",
    "export COREPACK_ENABLE_DOWNLOAD_PROMPT=0",
    "corepack enable",
    "cp -r /src/web /build",
    "cd /build",
    "pnpm install --frozen-lockfile > /src/install.log 2>&1",
    "cd packages/ui",
    "pnpm exec storybook build -o /src/site-linux --quiet > /src/build.log 2>&1",
  ].join(" && ");
  const result = sh("docker", ["run", "--rm", "--init", "--mount", `type=bind,source=${src},target=/src`, image, "sh", "-c", script]);
  return { status: result.status, ms: result.ms, outputTail: tail(result.output), installTail: existsSync(join(src, "install.log")) ? tail(readFileSync(join(src, "install.log"), "utf-8"), 6) : [] };
}

const runs = [runContainer("A", "baseline"), runContainer("B", "compare"), runHost("H", "compare")];
const linux = buildLinux();
if (linux.status === 0) {
  runs.push(runContainer("L", "compare", "/work/linux-src/site-linux"));
}
console.log(`[linux build] exit ${String(linux.status)} ${String(linux.ms)}ms`, linux.status === 0 ? "" : JSON.stringify(linux));
const hashes = (label) => {
  const dir = join(work, "out", label, "raw");
  if (!existsSync(dir)) {
    return {};
  }
  return Object.fromEntries(
    readdirSync(dir)
      .filter((name) => name.endsWith(".png"))
      .map((name) => [name, createHash("sha256").update(readFileSync(join(dir, name))).digest("hex")]),
  );
};
const shots = { A: hashes("A"), B: hashes("B"), H: hashes("H"), L: hashes("L") };
const pair = (x, y) => {
  const names = Object.keys(shots[x]);
  return { shots: names.length, bytesEqual: names.filter((name) => shots[x][name] === shots[y][name]).length };
};
const outside = (label) => {
  const dir = join(work, "out", label, "raw");
  return existsSync(dir)
    ? readdirSync(dir)
        .filter((name) => name.endsWith(".outside.json"))
        .flatMap((name) => JSON.parse(readFileSync(join(dir, name), "utf-8")))
    : [];
};
const passed = (run) => {
  const line = run.outputTail.find((text) => /\d+ passed/.test(text)) ?? "";
  const failedLine = run.outputTail.find((text) => /\d+ failed/.test(text)) ?? "";
  return { passed: Number(/(\d+) passed/.exec(line)?.[1] ?? 0), failed: Number(/(\d+) failed/.exec(failedLine)?.[1] ?? 0) };
};
const result = {
  image,
  versions,
  runs: runs.map((run) => ({ ...run, ...passed(run) })),
  linuxBuild: linux,
  pairs: { "A·B": pair("A", "B"), "A·H": pair("A", "H"), "A·L": pair("A", "L") },
  outside: { A: outside("A"), H: outside("H"), L: outside("L") },
};
writeFileSync(join(work, "result.json"), `${JSON.stringify(result, null, 2)}\n`);
for (const run of result.runs) {
  console.log(`[${run.label}] ${run.where} ${run.mode} exit ${String(run.status)} ${String(run.ms)}ms passed ${String(run.passed)} failed ${String(run.failed)}`);
}
console.log("[pairs]", JSON.stringify(result.pairs), "[outside]", JSON.stringify(result.outside));
console.log(`결과: ${join(work, "result.json")}`);
