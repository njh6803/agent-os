/**
 * release-image 설계 인터뷰의 프로브. "컨테이너가 시작할 때 그 자리의 사이트 파일로 위젯을 빌드한다"는 선택지가 치르는
 * 값을 잰다. 저장소가 추적하는 파일은 고치지 않고, 빌드 산출물(`.next/`, `public/element.js`, `public/fonts/`)과
 * `node_modules` 만 만든다(모두 뿌리 `.gitignore` 가 무시한다). 원본 출력과 결과 JSON 은 `--out` 폴더(저장소 밖)에 남긴다.
 *
 * 단계(첫 인자):
 *   install  `pnpm -C web install --frozen-lockfile` 에 걸린 시간. 표지: 종료 0, pnpm 의 `Done in` 줄, 설치 표시 파일.
 *   build    위젯의 `node tools/start.ts build` 를 산출물을 지운 채(cold)와 바로 앞 빌드의 산출물을 둔 채(warm)로 번갈아
 *            `--cold`·`--warm` 번씩 돈다. 시간은 프로세스를 띄운 때부터 끝날 때까지이고, Next 의 첫 줄(판을 찍는 머리
 *            줄)이 찍힌 때를 함께 적는다. 그 앞이 node 시작 + 글꼴 복사 + 페이지 안 번들(Vite) + next CLI 적재이고 그
 *            뒤가 `next build` 다. `next build` 안의 단계(컴파일, 타입 검사, 페이지)는 Next 가 찍는 줄의 도착 시각으로 가른다.
 *   phases   `phases.mjs` 를 `--rounds` 번 띄워 글꼴 복사와 페이지 안 번들 빌드만 프로세스 안에서 따로 잰다.
 *   diff     픽스처 사이트 파일로 두 번(A1, A2), `sites_b.toml` 로 두 번(B1, B2) cold 빌드하고 산출물 나무를 `--out` 에
 *            복사한다. `--trees A1,B2` 처럼 주면 그 나무만 다시 짓는다.
 *   compare  복사한 나무를 맞댄다. 입력이 같은 짝(A1↔A2, B1↔B2)에서 달라진 파일은 "빌드마다 달라지는 것"이고, 두 짝
 *            모두에서 같았는데 A2↔B1 에서 다른 파일이 "사이트 파일이 바꾸는 것"이다. 뒤의 것은 B1 의 파일에 사이트
 *            파일의 값(허용 출처, 글자 수 상한)이 글자로 들었으면 "값이 든 파일", 아니면 "따라 바뀐 파일"로 가른다.
 *            사이트 파일의 값과 빌드 ID 와 내용 해시가 든 파일 이름을 자리표로 바꾸면 같아지는지도 함께 적는다.
 *   net      `net_hook.cjs` 를 실어 위젯을 cold 빌드한다. node 쪽에서 루프백 밖으로 거는 연결과 이름 풀기를 적고 막는다.
 *            빌드 앞에 양성 대조(`net_control.mjs`)를 한 번 돈다. 같은 훅을 실은 node 가 루프백 밖으로 건 `fetch` 셋이
 *            훅의 기록에 적히고 훅의 오류로 끝나야 측정이다.
 *   sizes    산출물 폴더의 크기와, 위젯의 의존 묶음(실행만, 래퍼로 실행, 빌드, 개발 전부)이 끌어오는 패키지의 크기.
 *   admin    관리 화면의 `next build` 를 cold 로 `--rounds` 번.
 *
 * 표지를 못 본 회차는 측정이 아니라고 세고, 그런 회차가 하나라도 있으면 종료 코드가 1이다.
 *
 * 전제와 못 보는 것:
 * - Next 의 텔레메트리는 모든 빌드에서 `NEXT_TELEMETRY_DISABLED=1` 로 끈다. 켠 채의 시간은 재지 않는다.
 * - cold 는 이 앱 폴더의 산출물 셋을 지운 것이다. 운영체제의 파일 캐시와 pnpm 스토어, node 의 컴파일 캐시는 그대로다.
 *   그래서 "막 받은 이미지의 첫 시작"보다 빠를 수 있다.
 * - 시간은 이 PC 에서 함께 도는 다른 일의 영향을 받는다. 회차마다 띄우기 직전 1초의 CPU 사용률을 적어 두지만 판정에는
 *   쓰지 않는다.
 * - compare 의 "빌드마다 달라지는 것"은 입력이 같은 짝 둘에서 본 것이다. 가끔만 달라지는 파일은 "사이트 파일이 바꾸는
 *   것"으로 잘못 들 수 있다.
 * - net 의 훅은 node 의 `net.Socket.connect` 와 `dns.lookup` 만 본다. Turbopack(Rust)이 직접 여는 소켓과 node 가 아닌
 *   자식 프로세스는 보지 못한다.
 * - sizes 의 패키지 크기는 이 운영체제에 깔린 플랫폼 패키지(`@next/swc-*` 등)의 것이다.
 *
 * 사용: node .scratch/release-image/probes/widget_build/measure.mjs <단계> --out <저장소 밖 폴더>
 *       [--cold N] [--warm N] [--rounds N] [--trees A1,A2,B1,B2] [--whole]
 */

import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const HERE = import.meta.dirname;
const REPO = path.resolve(HERE, "..", "..", "..", "..");
const WEB = path.join(REPO, "web");
const WIDGET = path.join(WEB, "apps", "widget");
const ADMIN = path.join(WEB, "apps", "admin");
const SITE_A = path.join(REPO, "tests", "fixtures", "site_file", "sites.toml");
const SITE_B = path.join(HERE, "sites_b.toml");
const CALL_TIMEOUT_MS = 20 * 60 * 1000;
const ANSI = /\u001b\[[0-9;]*[A-Za-z]/g;
// 빌드의 환경에서 벗기는 변수. serve 의 토큰은 빌드가 읽지 않고, 상류는 관리 화면이 기본값을 쓰게 한다.
const STRIPPED_ENV = ["AGENT_OS_ADMIN_TOKEN", "AGENT_OS_CHANNEL_TOKEN", "AGENT_OS_UPSTREAM", "AGENT_OS_SITE_FILE"];

// --- 공통 ------------------------------------------------------------------------------------------------------------

function packageName(dir) {
  return JSON.parse(fs.readFileSync(path.join(dir, "package.json"), "utf-8")).name;
}

/** 이 스크립트가 지우는 자리는 위젯과 관리 화면의 산출물뿐이다. 자리를 잘못 계산했으면 아무것도 하지 않고 멈춘다. */
function assertLayout() {
  if (packageName(WIDGET) !== "@agent-os/widget" || packageName(ADMIN) !== "@agent-os/admin") {
    throw new Error(`앱 폴더가 기대한 자리가 아니다: ${WIDGET}, ${ADMIN}`);
  }
}

function buildEnv(extra) {
  const env = { ...process.env };
  for (const name of STRIPPED_ENV) {
    delete env[name];
  }
  return { ...env, NEXT_TELEMETRY_DISABLED: "1", ...extra };
}

/** 프로세스를 띄워 줄마다 받은 시각(띄운 때부터의 ms)을 적는다. 제한 시간을 넘기면 띄운 그 자식을 끈다. */
function runTimed(command, args, { cwd, env, shell = false }) {
  return new Promise((resolve) => {
    const started = performance.now();
    const child = spawn(command, args, { cwd, env, shell, stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    const lines = [];
    let exitMs = null;
    let timedOut = false;
    const rest = { stdout: "", stderr: "" };
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
    }, CALL_TIMEOUT_MS);
    child.on("error", (error) => {
      lines.push({ ms: Math.round(performance.now() - started), stream: "spawn", text: String(error) });
    });
    child.on("exit", () => {
      exitMs = performance.now() - started;
    });
    child.on("close", (code, signal) => {
      clearTimeout(timer);
      const ms = Math.round(performance.now() - started);
      for (const stream of ["stdout", "stderr"]) {
        if (rest[stream] !== "") {
          lines.push({ ms, stream, text: rest[stream].replace(ANSI, "") });
        }
      }
      resolve({ code, signal, timedOut, totalMs: Math.round(exitMs ?? performance.now() - started), lines });
    });
  });
}

/**
 * 회차를 띄우기 직전 1초 동안 이 PC의 CPU 가 바빴던 비율(%). 다른 세션이 함께 돌면 시간이 흔들리므로 회차마다 적어 둔다.
 * 판정에는 쓰지 않는다.
 */
async function cpuBusyPercent(windowMs = 1000) {
  const snapshot = () =>
    os.cpus().reduce(
      (sum, { times }) => ({
        idle: sum.idle + times.idle,
        total: sum.total + times.user + times.nice + times.sys + times.idle + times.irq,
      }),
      { idle: 0, total: 0 },
    );
  const before = snapshot();
  await new Promise((resolve) => setTimeout(resolve, windowMs));
  const after = snapshot();
  const total = after.total - before.total;
  return total <= 0 ? null : Math.round((1 - (after.idle - before.idle) / total) * 100);
}

function mtimeMs(file) {
  try {
    return fs.statSync(file).mtimeMs;
  } catch {
    return null;
  }
}

function readText(file) {
  try {
    return fs.readFileSync(file, "utf-8");
  } catch {
    return null;
  }
}

function remove(target) {
  fs.rmSync(target, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 });
}

function writeJson(out, name, value) {
  const file = path.join(out, name);
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, "utf-8");
  return file;
}

function range(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted.length === 0 ? null : { min: sorted[0], max: sorted.at(-1), all: values };
}

function seconds(ms) {
  return `${(ms / 1000).toFixed(1)}s`;
}

function environment() {
  const pnpm = spawnSync("pnpm --version", { shell: true, encoding: "utf-8", timeout: 60_000 });
  return {
    date: new Date().toISOString(),
    platform: `${os.type()} ${os.release()} ${os.arch()}`,
    cpu: `${os.cpus()[0]?.model ?? "?"} x${String(os.cpus().length)}`,
    memoryGb: Math.round(os.totalmem() / 2 ** 30),
    node: process.version,
    pnpm: (pnpm.stdout ?? "").trim(),
    nodeEnvWasSet: process.env.NODE_ENV !== undefined,
  };
}

/** 회차들을 찍고, 측정이 아닌 회차의 수를 돌려준다. */
function report(out, name, result) {
  const file = writeJson(out, name, { environment: environment(), ...result });
  const unmeasured = (result.rounds ?? []).filter((round) => !round.measured);
  console.log(`결과: ${file}`);
  if (unmeasured.length > 0) {
    console.log(`측정이 아닌 회차 ${String(unmeasured.length)}: ${unmeasured.map(({ label }) => label).join(", ")}`);
  }
  return unmeasured.length;
}

// --- install ---------------------------------------------------------------------------------------------------------

async function stepInstall(out) {
  const marker = path.join(WEB, "node_modules", ".modules.yaml");
  const fresh = !fs.existsSync(path.join(WEB, "node_modules"));
  const run = await runTimed("pnpm -C web install --frozen-lockfile", [], {
    cwd: REPO,
    env: { ...process.env, CI: "true" },
    shell: true,
  });
  const text = run.lines.map(({ text: line }) => line).join("\n");
  const progress = [...text.matchAll(/reused (\d+), downloaded (\d+), added (\d+)/g)].at(-1);
  const round = {
    label: "install",
    totalMs: run.totalMs,
    fresh,
    exitCode: run.code,
    doneLine: /Done in [^\n]+/.exec(text)?.[0] ?? null,
    reused: progress ? Number(progress[1]) : null,
    downloaded: progress ? Number(progress[2]) : null,
    added: progress ? Number(progress[3]) : null,
    markerFile: fs.existsSync(marker),
  };
  round.measured = run.code === 0 && round.doneLine !== null && round.markerFile;
  fs.writeFileSync(path.join(out, "install.log"), `${text}\n`, "utf-8");
  console.log(
    `install: ${seconds(run.totalMs)} (node_modules 없던 상태: ${String(fresh)}, 스토어에서 ${String(round.reused)}, 내려받음 ${String(round.downloaded)})`,
  );
  return report(out, "install.json", { rounds: [round] });
}

// --- 위젯 빌드 -------------------------------------------------------------------------------------------------------

const WIDGET_OUTPUTS = [
  path.join(WIDGET, ".next"),
  path.join(WIDGET, "public", "element.js"),
  path.join(WIDGET, "public", "fonts"),
];
const NEXT_BANNER = /Next\.js \d+\.\d+\.\d+/;
const NEXT_ROUTES = /^Route \(app\)/;

/**
 * `next build` 가 찍는 줄의 도착 시각으로 Next 안의 단계를 가른다(Next 16.3.6 의 출력을 한 번 보고 골랐다). 컴파일은
 * "Creating an optimized production build" 부터 "Compiled successfully" 까지, 타입 검사는 "Running TypeScript" 부터
 * "Finished TypeScript" 까지, 페이지는 그 뒤부터 경로 표("Route (app)")까지다. 줄이 하나라도 없으면 null 이다.
 */
function nextPhases(lines, totalMs) {
  const at = (pattern) => lines.find(({ text }) => pattern.test(text))?.ms ?? null;
  const banner = at(NEXT_BANNER);
  const creating = at(/Creating an optimized production build/);
  const compiled = at(/Compiled successfully/);
  const typesStarted = at(/Running TypeScript/);
  const typesFinished = at(/Finished TypeScript/);
  const routes = lines.find(({ text }) => NEXT_ROUTES.test(text.trim()))?.ms ?? null;
  if ([banner, creating, compiled, typesStarted, typesFinished, routes].includes(null)) {
    return null;
  }
  return {
    configMs: creating - banner,
    compileMs: compiled - creating,
    typescriptMs: typesFinished - typesStarted,
    pagesMs: routes - typesFinished,
    tailMs: totalMs - routes,
    stated: lines
      .filter(({ text }) => /Compiled successfully|Finished TypeScript|Generating static pages.*\bin\b/.test(text))
      .map(({ text }) => text.trim()),
  };
}

/** 위젯을 한 번 빌드한다. 표지를 모두 본 회차만 측정이다. */
async function widgetBuild(label, { siteFile, cold, extraEnv = {} }) {
  if (cold) {
    for (const target of WIDGET_OUTPUTS) {
      remove(target);
    }
  }
  const hadNext = fs.existsSync(path.join(WIDGET, ".next", "BUILD_ID"));
  const cpuBusyBeforePct = await cpuBusyPercent();
  const startedAt = Date.now();
  const run = await runTimed(process.execPath, [path.join(WIDGET, "tools", "start.ts"), "build"], {
    cwd: WIDGET,
    env: buildEnv({ AGENT_OS_SITE_FILE: siteFile, ...extraEnv }),
  });
  const banner = run.lines.find(({ text }) => NEXT_BANNER.test(text));
  const routes = run.lines.find(({ text }) => NEXT_ROUTES.test(text.trim()));
  const buildIdAt = mtimeMs(path.join(WIDGET, ".next", "BUILD_ID"));
  const elementAt = mtimeMs(path.join(WIDGET, "public", "element.js"));
  const markers = {
    exitZero: run.code === 0 && !run.timedOut,
    // cold 는 산출물이 없는 데서, warm 은 앞 빌드의 산출물이 있는 데서 시작했다.
    startState: cold ? !hadNext : hadNext,
    nextBanner: banner !== undefined,
    routeTable: routes !== undefined,
    buildIdFresh: buildIdAt !== null && buildIdAt >= startedAt,
    elementFresh: elementAt !== null && elementAt >= startedAt,
  };
  return {
    label,
    cold,
    siteFile,
    cpuBusyBeforePct,
    totalMs: run.totalMs,
    untilNextBannerMs: banner?.ms ?? null,
    afterNextBannerMs: banner === undefined ? null : run.totalMs - banner.ms,
    nextPhases: nextPhases(run.lines, run.totalMs),
    buildId: readText(path.join(WIDGET, ".next", "BUILD_ID"))?.trim() ?? null,
    markers,
    measured: Object.values(markers).every(Boolean),
    lines: run.lines,
  };
}

async function stepBuild(out, { cold, warm }) {
  // cold 와 warm 을 번갈아 돈다. 몰아서 돌면 그사이 PC 의 부하가 바뀐 것과 캐시의 효과를 가르지 못한다. warm 은 바로 앞
  // cold 가 남긴 산출물 위에서 같은 사이트 파일로 다시 빌드한다. 첫 회차는 cold 다.
  const rounds = [];
  for (let index = 1; index <= Math.max(cold, warm); index += 1) {
    if (index <= cold) {
      rounds.push(await widgetBuild(`cold-${String(index)}`, { siteFile: SITE_A, cold: true }));
      console.log(describeBuild(rounds.at(-1)));
    }
    if (index <= warm) {
      rounds.push(await widgetBuild(`warm-${String(index)}`, { siteFile: SITE_A, cold: false }));
      console.log(describeBuild(rounds.at(-1)));
    }
  }
  const of = (kind, key) =>
    range(rounds.filter((round) => round.measured && round.cold === kind).map((round) => round[key]));
  const phase = (kind, key) =>
    range(
      rounds
        .filter((round) => round.measured && round.cold === kind && round.nextPhases !== null)
        .map((round) => round.nextPhases[key]),
    );
  const summary = {
    coldTotalMs: of(true, "totalMs"),
    coldUntilNextBannerMs: of(true, "untilNextBannerMs"),
    coldAfterNextBannerMs: of(true, "afterNextBannerMs"),
    coldNextCompileMs: phase(true, "compileMs"),
    coldNextTypescriptMs: phase(true, "typescriptMs"),
    coldNextPagesMs: phase(true, "pagesMs"),
    coldCpuBusyBeforePct: of(true, "cpuBusyBeforePct"),
    warmTotalMs: of(false, "totalMs"),
    warmUntilNextBannerMs: of(false, "untilNextBannerMs"),
    warmAfterNextBannerMs: of(false, "afterNextBannerMs"),
    warmNextCompileMs: phase(false, "compileMs"),
    warmNextTypescriptMs: phase(false, "typescriptMs"),
    warmNextPagesMs: phase(false, "pagesMs"),
    warmCpuBusyBeforePct: of(false, "cpuBusyBeforePct"),
  };
  console.log(JSON.stringify(summary));
  return report(out, "build.json", { summary, rounds });
}

function describeBuild(round) {
  const split =
    round.untilNextBannerMs === null
      ? "Next 머리 줄 없음"
      : `Next 머리 줄까지 ${seconds(round.untilNextBannerMs)}, 그 뒤 ${seconds(round.afterNextBannerMs)}`;
  const inside =
    round.nextPhases === null
      ? ""
      : ` [컴파일 ${seconds(round.nextPhases.compileMs)}, 타입 검사 ${seconds(round.nextPhases.typescriptMs)}, 페이지 ${seconds(round.nextPhases.pagesMs)}]`;
  return `${round.label}: ${seconds(round.totalMs)} (${split})${inside} 직전 CPU ${String(round.cpuBusyBeforePct)}% 측정=${String(round.measured)} ${JSON.stringify(round.markers)}`;
}

// --- phases ----------------------------------------------------------------------------------------------------------

async function stepPhases(out, { rounds: count }) {
  const rounds = [];
  for (let index = 1; index <= count; index += 1) {
    remove(path.join(WIDGET, "public", "element.js"));
    remove(path.join(WIDGET, "public", "fonts"));
    const cpuBusyBeforePct = await cpuBusyPercent();
    const startedAt = Date.now();
    const run = await runTimed(process.execPath, [path.join(HERE, "phases.mjs"), WIDGET], {
      cwd: WIDGET,
      env: buildEnv({ AGENT_OS_SITE_FILE: SITE_A, AGENT_OS_PROBE_SPAWNED_AT: String(startedAt) }),
    });
    const last = run.lines.filter(({ stream }) => stream === "stdout").at(-1)?.text ?? "";
    let phases = null;
    try {
      phases = JSON.parse(last);
    } catch {
      phases = null;
    }
    const elementAt = mtimeMs(path.join(WIDGET, "public", "element.js"));
    const markers = {
      exitZero: run.code === 0 && !run.timedOut,
      phasesLine: phases !== null,
      elementFresh: elementAt !== null && elementAt >= startedAt,
      fontsCopied: (phases?.fontFiles ?? 0) > 0,
    };
    rounds.push({
      label: `phases-${String(index)}`,
      cpuBusyBeforePct,
      totalMs: run.totalMs,
      phases,
      markers,
      measured: Object.values(markers).every(Boolean),
      lines: run.lines,
    });
    console.log(`phases-${String(index)}: ${seconds(run.totalMs)} 직전 CPU ${String(cpuBusyBeforePct)}% ${last}`);
  }
  const of = (key) => range(rounds.filter((round) => round.measured).map((round) => Math.round(round.phases[key])));
  const summary = {
    totalMs: range(rounds.filter((round) => round.measured).map((round) => round.totalMs)),
    startupMs: of("startupMs"),
    importMs: of("importMs"),
    copyFontsMs: of("copyFontsMs"),
    buildElementMs: of("buildElementMs"),
    cpuBusyBeforePct: range(rounds.filter((round) => round.measured).map((round) => round.cpuBusyBeforePct)),
  };
  console.log(JSON.stringify(summary));
  return report(out, "phases.json", { summary, rounds });
}

// --- diff 와 compare --------------------------------------------------------------------------------------------------

const TREES = ["A1", "A2", "B1", "B2"];
const TREE_FLAG = ".widget-build-probe-tree";

/** 빌드 산출물(`.next/` 와 `public/`)을 `--out` 아래에 복사한다. 앞 실행의 복사본은 표지 파일이 있을 때만 지운다. */
function copyOutputs(out, name) {
  const target = path.join(out, `tree_${name}`);
  const flag = path.join(target, TREE_FLAG);
  if (fs.existsSync(target)) {
    if (!fs.existsSync(flag)) {
      throw new Error(`${target} 이 이미 있는데 이 프로브가 만든 표지가 없다. 지우지 않고 멈춘다.`);
    }
    remove(target);
  }
  fs.mkdirSync(target, { recursive: true });
  fs.writeFileSync(flag, "", "utf-8");
  fs.cpSync(path.join(WIDGET, ".next"), path.join(target, ".next"), { recursive: true });
  fs.cpSync(path.join(WIDGET, "public"), path.join(target, "public"), { recursive: true });
  return target;
}

async function stepDiff(out, { trees }) {
  const previous = readText(path.join(out, "diff.json"));
  const kept = previous === null ? [] : JSON.parse(previous).rounds.filter(({ label }) => !trees.includes(label.slice(5)));
  const rounds = [];
  for (const name of trees) {
    const round = await widgetBuild(`diff-${name}`, { siteFile: name.startsWith("B") ? SITE_B : SITE_A, cold: true });
    console.log(describeBuild(round));
    if (round.measured) {
      round.tree = copyOutputs(out, name);
    }
    rounds.push(round);
  }
  return report(out, "diff.json", { rounds: [...kept, ...rounds] });
}

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

/** 나무의 파일들. 열쇠는 경로에서 그 빌드의 빌드 ID 를 자리표로 바꾼 것이다(`static/<빌드 ID>/` 폴더가 빌드마다 다르다). */
function loadTree(tree) {
  const files = new Map();
  walk(tree.root, (absolute, relative) => {
    if (relative === TREE_FLAG) {
      return;
    }
    const bytes = fs.readFileSync(absolute);
    const key = tree.buildId ? relative.replaceAll(tree.buildId, "<BUILD_ID>") : relative;
    files.set(key, { relative, size: bytes.length, sha: createHash("sha256").update(bytes).digest("hex") });
  });
  return files;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** 사이트 파일에서 빌드가 읽는 두 값. 위젯이 쓰는 그 함수(`@agent-os/site-file` 의 `buildInput`)로 읽는다. */
async function siteInput(siteFile) {
  const resolved = createRequire(path.join(WIDGET, "package.json")).resolve("@agent-os/site-file");
  const { buildInput } = await import(pathToFileURL(resolved).href);
  return buildInput({ AGENT_OS_SITE_FILE: siteFile });
}

/**
 * 글자 수 상한을 산출물에서 찾는 패턴. 미니파이어는 끝에 0 이 셋 이상인 수를 지수 꼴로 줄여 쓴다(페이지 안 번들에서
 * 4000 이 `4e3` 이었다). 두 꼴을 함께 잡고, 다른 수나 이름의 일부인 것은 잡지 않는다.
 */
function charsPattern(count) {
  const text = String(count);
  const zeros = /0+$/.exec(text)?.[0].length ?? 0;
  const forms = [text];
  if (zeros >= 3 && zeros < text.length) {
    forms.push(`${text.slice(0, -zeros)}e${String(zeros)}`);
  }
  return new RegExp(`(?<![0-9A-Za-z_.$])(?:${forms.map(escapeRegExp).join("|")})(?![0-9A-Za-z_$])`, "g");
}

/** 나무 하나의 자리표 규칙. 합친 허용 출처, 글자 수 상한, 빌드 ID 를 같은 자리표로 바꾼다. */
function baseRules(tree) {
  const rules = [];
  if (tree.input.allowedOrigins.length > 0) {
    rules.push([new RegExp(escapeRegExp(tree.input.allowedOrigins.join(" ")), "g"), "<ORIGINS>"]);
  }
  rules.push([charsPattern(tree.input.requestChars), "<CHARS>"]);
  if (tree.buildId) {
    rules.push([new RegExp(escapeRegExp(tree.buildId), "g"), "<BUILD_ID>"]);
  }
  return rules;
}

function normalized(root, relative, rules) {
  let text = fs.readFileSync(path.join(root, relative)).toString("latin1");
  for (const [pattern, placeholder] of rules) {
    text = text.replace(pattern, placeholder);
  }
  return text;
}

function sha(text) {
  return createHash("sha256").update(text, "latin1").digest("hex");
}

function stem(key) {
  return path.posix.basename(key).split(".")[0] ?? "";
}

function area(key) {
  const parts = key.split("/");
  if (parts[0] === "public") {
    return parts.length > 2 ? `public/${parts[1]}/` : key;
  }
  if (parts.length === 2) {
    return ".next/<뿌리 파일>";
  }
  return `${parts[0]}/${parts[1]}/`;
}

/** 파일에 그 나무의 사이트 파일 값이 글자로 들었는가. */
function valueFlags(tree, relative) {
  const text = fs.readFileSync(path.join(tree.root, relative)).toString("latin1");
  return {
    origins: tree.input.allowedOrigins.some((origin) => text.includes(origin)),
    chars: charsPattern(tree.input.requestChars).test(text),
  };
}

function snippet(left, right) {
  let prefix = 0;
  const limit = Math.min(left.length, right.length);
  while (prefix < limit && left[prefix] === right[prefix]) {
    prefix += 1;
  }
  let suffix = 0;
  while (suffix < limit - prefix && left.at(-1 - suffix) === right.at(-1 - suffix)) {
    suffix += 1;
  }
  const cut = (text) =>
    text.slice(Math.max(0, prefix - 60), Math.min(text.length - suffix + 60, prefix + 240)).replace(/\s+/g, " ");
  return {
    differingLeft: left.length - prefix - suffix,
    differingRight: right.length - prefix - suffix,
    leftText: cut(left),
    rightText: cut(right),
  };
}

/**
 * 두 나무를 맞대어 파일마다 상태 하나를 낸다. identical 은 바이트가 같은 것, explained 는 자리표로 바꾸면 같아지는 것,
 * renamed 는 한쪽에만 있는 파일 가운데 자리표로 바꾼 내용이 같은 짝(내용 해시가 든 이름이 바뀐 것), unexplained 는 같은
 * 경로인데 자리표로 바꿔도 다른 것, onlyLeft·onlyRight 는 짝이 없는 것이다. 짝의 이름 줄기도 자리표로 더해 다시 본다.
 */
function compareTrees(left, right) {
  const leftFiles = loadTree(left);
  const rightFiles = loadTree(right);
  const records = [];
  let changed = [];
  let onlyLeft = [];
  let onlyRight = [];
  for (const [key, info] of leftFiles) {
    const other = rightFiles.get(key);
    if (other === undefined) {
      onlyLeft.push(key);
    } else if (other.sha === info.sha) {
      records.push({ key, state: "identical" });
    } else {
      changed.push(key);
    }
  }
  for (const key of rightFiles.keys()) {
    if (!leftFiles.has(key)) {
      onlyRight.push(key);
    }
  }
  // 두 나무의 규칙을 합쳐 양쪽에 똑같이 건다. 한쪽 규칙만 걸면 그 값과 우연히 같은 글자(시간 제한의 `4e3` 등)가 한쪽에서만
  // 자리표로 바뀌어, 같은 파일이 다르다고 나온다(첫 판이 그랬다).
  const rules = [...baseRules(left), ...baseRules(right)];
  const leftText = (key) => normalized(left.root, leftFiles.get(key).relative, rules);
  const rightText = (key) => normalized(right.root, rightFiles.get(key).relative, rules);
  const identity = (key, text) => `${path.posix.dirname(key)}|${path.posix.extname(key)}|${sha(text)}`;
  let names = 0;
  for (let pass = 0; pass < 8; pass += 1) {
    let progressed = false;
    const still = [];
    for (const key of changed) {
      if (leftText(key) === rightText(key)) {
        records.push({ key, state: "explained" });
        progressed = true;
      } else {
        still.push(key);
      }
    }
    changed = still;
    const candidates = new Map();
    for (const key of onlyLeft) {
      const id = identity(key, leftText(key));
      candidates.set(id, [...(candidates.get(id) ?? []), key]);
    }
    const paired = new Set();
    const unpaired = [];
    for (const key of onlyRight) {
      const partner = (candidates.get(identity(key, rightText(key))) ?? []).shift();
      if (partner === undefined) {
        unpaired.push(key);
        continue;
      }
      paired.add(partner);
      records.push({ key, leftKey: partner, state: "renamed" });
      progressed = true;
      const [leftStem, rightStem] = [stem(partner), stem(key)];
      if (leftStem.length >= 8 && rightStem.length >= 8 && leftStem !== rightStem) {
        names += 1;
        const placeholder = `<NAME:${String(names)}>`;
        rules.push([new RegExp(escapeRegExp(leftStem), "g"), placeholder]);
        rules.push([new RegExp(escapeRegExp(rightStem), "g"), placeholder]);
      }
    }
    onlyLeft = onlyLeft.filter((key) => !paired.has(key));
    onlyRight = unpaired;
    if (!progressed) {
      break;
    }
  }
  for (const key of changed) {
    records.push({ key, state: "unexplained", ...snippet(leftText(key), rightText(key)) });
  }
  for (const key of onlyLeft) {
    records.push({ key, state: "onlyLeft" });
  }
  for (const key of onlyRight) {
    records.push({ key, state: "onlyRight" });
  }
  const counts = {};
  for (const { state } of records) {
    counts[state] = (counts[state] ?? 0) + 1;
  }
  return { left: left.name, right: right.name, counts, records, rightFiles };
}

function tally(entries) {
  const counts = {};
  for (const { file } of entries) {
    counts[area(file)] = (counts[area(file)] ?? 0) + 1;
  }
  return counts;
}

async function stepCompare(out) {
  const diff = JSON.parse(fs.readFileSync(path.join(out, "diff.json"), "utf-8"));
  const trees = {};
  for (const name of TREES) {
    const round = diff.rounds.find(({ label }) => label === `diff-${name}`);
    if (!round?.measured || !round.tree) {
      throw new Error(`diff 단계의 ${name} 회차가 없거나 측정이 아니다. diff 를 다시 돈다.`);
    }
    trees[name] = { name, root: round.tree, input: await siteInput(round.siteFile), buildId: round.buildId?.trim() };
  }
  const sameInput = [compareTrees(trees.A1, trees.A2), compareTrees(trees.B1, trees.B2)];
  const effect = compareTrees(trees.A2, trees.B1);
  // 입력이 같은 짝에서 한 번이라도 달라진 파일.
  const varies = new Set();
  for (const pair of sameInput) {
    for (const record of pair.records) {
      if (record.state !== "identical") {
        varies.add(record.key);
        if (record.leftKey !== undefined) {
          varies.add(record.leftKey);
        }
      }
    }
  }
  // 사이트 파일 때문에 이름이 바뀐 파일(내용 해시가 든 청크)의 새 이름 줄기. 이것을 가리키는 파일은 값이 없어도 따라 바뀐다.
  const renamedStems = effect.records
    .filter(({ state, key, leftKey }) => state === "renamed" && !varies.has(key) && !varies.has(leftKey))
    .map(({ key }) => stem(key));
  const classes = { everyBuild: [], siteValue: [], siteFollows: [] };
  for (const record of effect.records) {
    if (record.state === "identical") {
      continue;
    }
    const inRight = effect.rightFiles.get(record.key);
    const flags = inRight === undefined ? { origins: false, chars: false } : valueFlags(trees.B1, inRight.relative);
    const pointsAtRenamed =
      inRight !== undefined &&
      record.state !== "renamed" &&
      renamedStems.some((name) =>
        fs.readFileSync(path.join(trees.B1.root, inRight.relative)).toString("latin1").includes(name),
      );
    const entry = {
      file: record.key,
      state: record.state,
      ...(record.leftKey === undefined ? {} : { renamedFrom: record.leftKey }),
      ...flags,
      pointsAtRenamed,
      ...(record.state === "unexplained"
        ? { differing: [record.differingLeft, record.differingRight], leftText: record.leftText, rightText: record.rightText }
        : {}),
    };
    if (varies.has(record.key) || (record.leftKey !== undefined && varies.has(record.leftKey))) {
      classes.everyBuild.push(entry);
    } else if (flags.origins || flags.chars) {
      classes.siteValue.push(entry);
    } else {
      classes.siteFollows.push(entry);
    }
  }
  const routes = (name) => readText(path.join(trees[name].root, ".next", "routes-manifest.json")) ?? "";
  const joinedA = trees.A2.input.allowedOrigins.join(" ");
  const joinedB = trees.B1.input.allowedOrigins.join(" ");
  // 표지: 두 빌드가 저마다 자기 사이트 파일을 읽었고(헤더 값에 자기 허용 출처가 있고 남의 것은 없다), 맞대기가 그 차이를
  // 실제로 "사이트 파일이 바꾸는 것"으로 냈다.
  const markers = {
    aReadItsSiteFile: routes("A2").includes(`frame-ancestors ${joinedA}`) && !routes("A2").includes(joinedB),
    bReadItsSiteFile: routes("B1").includes(`frame-ancestors ${joinedB}`) && !routes("B1").includes(joinedA),
    inputsDiffer: joinedA !== joinedB && trees.A2.input.requestChars !== trees.B1.input.requestChars,
    routesManifestClassified: classes.siteValue.some(({ file }) => file === ".next/routes-manifest.json"),
  };
  const result = {
    inputs: Object.fromEntries(TREES.map((name) => [name, { ...trees[name].input, buildId: trees[name].buildId }])),
    markers,
    sameInput: sameInput.map(({ left, right, counts, records }) => ({
      left,
      right,
      counts,
      changed: records.filter(({ state }) => state !== "identical").map(({ key, state }) => ({ file: key, state })),
    })),
    effect: { left: effect.left, right: effect.right, counts: effect.counts },
    classes,
    rounds: [{ label: "compare", measured: Object.values(markers).every(Boolean), markers }],
  };
  console.log(`입력: ${JSON.stringify(result.inputs)}`);
  console.log(`표지: ${JSON.stringify(markers)}`);
  for (const pair of result.sameInput) {
    console.log(`입력이 같은 짝 ${pair.left}↔${pair.right}: ${JSON.stringify(pair.counts)}`);
    console.log(`  달라진 것의 영역: ${JSON.stringify(tally(pair.changed))}`);
  }
  console.log(`${effect.left}↔${effect.right}: ${JSON.stringify(effect.counts)}`);
  const show = (entry) =>
    `  ${entry.file}${entry.renamedFrom === undefined ? "" : ` (이름이 바뀜: ${entry.renamedFrom})`} [${entry.state}${entry.origins ? ", 허용 출처" : ""}${entry.chars ? ", 글자 수 상한" : ""}${entry.pointsAtRenamed ? ", 이름이 바뀐 청크를 가리킴" : ""}]`;
  console.log(`사이트 파일의 값이 든 파일 ${String(classes.siteValue.length)}:`);
  for (const entry of classes.siteValue) {
    console.log(show(entry));
  }
  console.log(`값은 없고 따라 바뀐 파일 ${String(classes.siteFollows.length)}:`);
  for (const entry of classes.siteFollows) {
    console.log(show(entry));
  }
  console.log(`입력이 같아도 빌드마다 달라지는 파일 ${String(classes.everyBuild.length)}: ${JSON.stringify(tally(classes.everyBuild))}`);
  for (const entry of classes.everyBuild.filter(({ file }) => !file.startsWith(".next/cache/"))) {
    console.log(show(entry));
  }
  return report(out, "compare.json", result);
}

// --- net -------------------------------------------------------------------------------------------------------------

function isLoopback(host) {
  const name = String(host ?? "").toLowerCase();
  return (
    name === "localhost" || name.endsWith(".localhost") || name === "::1" || name === "[::1]" || /^127\./.test(name)
  );
}

/** 훅의 기록 파일을 줄마다 푼다. 풀지 못한 줄(쓰다 끊긴 줄)은 버리지 않고 `kind: "unparsed"` 로 넘긴다. */
function hookRecords(log) {
  return (readText(log) ?? "")
    .split("\n")
    .filter((line) => line !== "")
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return { kind: "unparsed", line };
      }
    });
}

/**
 * 훅의 양성 대조. 같은 훅을 실은 node 로 `net_control.mjs` 를 띄워 루프백이 아닌 대상 셋에 `fetch` 를 건다(어디에도 닿지
 * 않는 문서용 주소와 `.invalid` 이름). 표지: 훅이 실렸고, 세 대상이 모두 훅의 기록에 밖으로 가는 연결로 적혔고, 세 fetch 가
 * 모두 응답 없이 훅의 문구가 든 오류로 끝났다. 이 회차가 측정이어야 빌드 회차의 "밖으로 가는 시도 0"을 "훅이 fetch 의 시도를
 * 적는데 시도가 없었다"로 읽는다.
 */
async function netControl(out, nodeOptions) {
  const label = "net-control";
  const log = path.join(out, `${label}.jsonl`);
  remove(log);
  const run = await runTimed(process.execPath, [path.join(HERE, "net_control.mjs")], {
    cwd: HERE,
    env: buildEnv({ NODE_OPTIONS: nodeOptions, AGENT_OS_PROBE_NET_LOG: log }),
  });
  const records = hookRecords(log);
  const lastLine = run.lines.filter(({ stream }) => stream === "stdout").at(-1)?.text ?? "";
  let fetches = [];
  try {
    const parsed = JSON.parse(lastLine);
    fetches = Array.isArray(parsed) ? parsed : [];
  } catch {
    fetches = [];
  }
  const hosts = fetches.map(({ url }) => new URL(url).hostname);
  const recorded = records.filter(({ kind, canary, pipe }) => kind === "connect" && !canary && !pipe);
  const round = {
    label,
    totalMs: run.totalMs,
    exitCode: run.code,
    fetches,
    recorded: recorded.map(({ host, port }) => `${String(host)}:${String(port)}`),
    lines: run.lines,
    markers: {
      hookLoaded: records.some(({ kind }) => kind === "loaded"),
      logParsed: records.every(({ kind }) => kind !== "unparsed"),
      // 세 대상이 모두 훅의 기록에 루프백 밖의 연결로 적혔다.
      controlRecorded:
        hosts.length === 3 &&
        hosts.every((host) => recorded.filter((entry) => entry.host === host && !isLoopback(entry.host)).length > 0) &&
        recorded.filter(({ host }) => hosts.includes(host)).length >= 3,
      // 세 fetch 가 모두 응답을 받지 못했고 오류에 훅의 문구가 있다. 훅 없이 실패한 것(시간 초과, 이름 풀기 실패)과 갈린다.
      controlRefused: fetches.length === 3 && fetches.every(({ reached, refusedByHook }) => !reached && refusedByHook),
    },
  };
  round.measured = Object.values(round.markers).every(Boolean);
  console.log(`${label}: ${seconds(run.totalMs)} 측정=${String(round.measured)} ${JSON.stringify(round.markers)}`);
  console.log(`  적힌 연결: ${round.recorded.join(", ")}`);
  for (const { url, reached, error } of fetches) {
    console.log(`  ${url} 닿음=${String(reached)} ${error ?? ""}`);
  }
  return round;
}

async function stepNet(out) {
  const variants = [
    { label: "net-telemetry-off", extraEnv: {} },
    // 텔레메트리를 끄지 않되 보내는 대신 stderr 에 찍게 한다(NEXT_TELEMETRY_DEBUG. Next 16.3.6 의 telemetry/storage.js 는
    // 이 변수가 있으면 보내기 전에 찍고 돌아간다). 훅은 이 회차에서도 밖으로 가는 연결을 막는다.
    { label: "net-telemetry-debug", extraEnv: { NEXT_TELEMETRY_DISABLED: undefined, NEXT_TELEMETRY_DEBUG: "1" } },
  ];
  const hook = path.join(HERE, "net_hook.cjs").replaceAll("\\", "/");
  const nodeOptions = [process.env.NODE_OPTIONS, `--require=${hook}`].filter(Boolean).join(" ");
  const rounds = [await netControl(out, nodeOptions)];
  for (const { label, extraEnv } of variants) {
    const log = path.join(out, `${label}.jsonl`);
    remove(log);
    const env = { NODE_OPTIONS: nodeOptions, AGENT_OS_PROBE_NET_LOG: log, ...extraEnv };
    const round = await widgetBuild(label, { siteFile: SITE_A, cold: true, extraEnv: env });
    const records = hookRecords(log);
    const loaded = records.filter(({ kind }) => kind === "loaded");
    const canaries = records.filter(({ kind, canary }) => kind === "connect" && canary);
    const connects = records.filter(({ kind, canary }) => kind === "connect" && !canary);
    const lookups = records.filter(({ kind }) => kind === "lookup");
    const external = [
      ...connects.filter(({ pipe, host }) => !pipe && !isLoopback(host)),
      ...lookups.filter(({ host }) => !isLoopback(host)),
    ];
    round.net = {
      hookedThreads: loaded.length,
      hookedPids: [...new Set(loaded.map(({ pid }) => pid))].length,
      hookedScripts: [...new Set(loaded.map(({ argv }) => path.basename(String(argv?.[0] ?? "?"))))],
      canaries: canaries.length,
      pipes: connects.filter(({ pipe }) => pipe).length,
      loopbackConnects: connects
        .filter(({ pipe, host }) => !pipe && isLoopback(host))
        .map(({ host, port }) => `${host}:${String(port)}`),
      external: external.map(({ kind, host, port }) => `${kind} ${host}${port === undefined ? "" : `:${String(port)}`}`),
      telemetryLines: round.lines.filter(({ text }) => text.includes("[telemetry]")).length,
    };
    // 표지: 훅이 빌드의 프로세스에 실렸고, 실린 스레드마다 미끼 연결이 적혔다(바꿔 끼운 connect 가 그 스레드에서 돈다).
    round.markers.hookLoaded = loaded.length > 0;
    round.markers.canaryPerThread = canaries.length === loaded.length;
    // 기록의 모든 줄을 풀었다. 풀지 못한 줄이 있으면 밖으로 가는 시도가 그 줄에 묻혔을 수 있다.
    round.markers.logParsed = records.every(({ kind }) => kind !== "unparsed");
    round.measured = Object.values(round.markers).every(Boolean);
    rounds.push(round);
    console.log(describeBuild(round));
    console.log(`  ${JSON.stringify(round.net)}`);
  }
  return report(out, "net.json", { rounds });
}

// --- sizes -----------------------------------------------------------------------------------------------------------

function sizeOf(root, skip = () => false) {
  let bytes = 0;
  let files = 0;
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const absolute = path.join(dir, entry.name);
      if (entry.isSymbolicLink() || skip(absolute, entry)) {
        continue;
      }
      if (entry.isDirectory()) {
        visit(absolute);
      } else if (entry.isFile()) {
        bytes += fs.statSync(absolute).size;
        files += 1;
      }
    }
  };
  if (fs.existsSync(root)) {
    if (fs.statSync(root).isDirectory()) {
      visit(root);
    } else {
      bytes = fs.statSync(root).size;
      files = 1;
    }
  }
  return { bytes, files };
}

function mb(bytes) {
  return Math.round((bytes / 2 ** 20) * 10) / 10;
}

/** 패키지 폴더에서 이름으로 의존 패키지의 실제 폴더를 찾는다. pnpm 의 배치에서는 자기 `node_modules` 이거나 형제 자리다. */
function dependencyDir(packageDir, name) {
  const candidates = [path.join(packageDir, "node_modules", name)];
  const parts = packageDir.split(path.sep);
  const at = parts.lastIndexOf("node_modules");
  if (at >= 0) {
    candidates.push(path.join(parts.slice(0, at + 1).join(path.sep), name));
  }
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "package.json"))) {
      return fs.realpathSync(candidate);
    }
  }
  return null;
}

// 워크스페이스 패키지의 크기에서 빼는 것(설치본과 산출물). 바깥 패키지는 자기 안의 node_modules 만 뺀다.
const WORKSPACE_SKIPPED = ["node_modules", ".next", "storybook-static", "dist", "public", "test-results"];

/** 뿌리 이름들에서 닿는 패키지의 닫힌 묶음. 뿌리는 위젯에서 찾고, 그 아래는 dependencies·optional·peer 를 따라간다. */
function closure(rootNames) {
  const seen = new Map();
  const missing = [];
  const queue = [];
  for (const name of rootNames) {
    const dir = dependencyDir(WIDGET, name);
    if (dir === null) {
      missing.push(name);
    } else {
      queue.push(dir);
    }
  }
  while (queue.length > 0) {
    const dir = queue.pop();
    if (seen.has(dir)) {
      continue;
    }
    const manifest = JSON.parse(fs.readFileSync(path.join(dir, "package.json"), "utf-8"));
    const workspace = !dir.split(path.sep).includes("node_modules");
    const skipped = workspace ? WORKSPACE_SKIPPED : ["node_modules"];
    const size = sizeOf(
      dir,
      (absolute, entry) => path.dirname(absolute) === dir && entry.isDirectory() && skipped.includes(entry.name),
    );
    seen.set(dir, { name: manifest.name, version: manifest.version ?? null, workspace, ...size });
    // 선택 peer(peerDependenciesMeta 의 optional)는 따라가지 않는다. 이 설치본에는 다른 패키지의 devDependencies 덕에 깔려
    // 있어도(next 의 @playwright/test 등) 그 묶음만 설치하면 없는 것이다. 첫 판은 따라가서 실행 묶음에 playwright 가 들었다.
    const optionalPeers = Object.entries(manifest.peerDependenciesMeta ?? {})
      .filter(([, meta]) => meta?.optional === true)
      .map(([name]) => name);
    const names = new Set([
      ...Object.keys(manifest.dependencies ?? {}),
      ...Object.keys(manifest.optionalDependencies ?? {}),
      ...Object.keys(manifest.peerDependencies ?? {}).filter((name) => !optionalPeers.includes(name)),
    ]);
    for (const name of names) {
      const next = dependencyDir(dir, name);
      if (next !== null) {
        queue.push(next);
      }
    }
  }
  const packages = [...seen.values()];
  const external = packages.filter((item) => !item.workspace);
  return {
    roots: rootNames,
    missingRoots: missing,
    packages: external.length,
    mb: mb(external.reduce((sum, item) => sum + item.bytes, 0)),
    files: external.reduce((sum, item) => sum + item.files, 0),
    workspacePackages: packages
      .filter((item) => item.workspace)
      .map((item) => `${item.name} ${String(mb(item.bytes))}MB`),
    largest: external
      .sort((a, b) => b.bytes - a.bytes)
      .slice(0, 12)
      .map((item) => `${item.name}@${String(item.version)} ${String(mb(item.bytes))}MB`),
  };
}

/**
 * Next 가 빌드 때 추적한 "실행에 읽는 파일"의 목록(`.next` 아래의 `*.nft.json`)을 모아 `.next` 밖의 것만 센다. Next 의
 * `output: "standalone"` 이 복사하는 기준이 이 목록이다. 위젯은 그 출력을 쓰지 않으므로 이 수는 "그만큼만 있으면 뜬다"는
 * 측정이 아니라 Next 가 적은 목록의 크기다. 시작 래퍼(tools/start.ts)가 import 하는 것은 이 목록에 없다.
 */
function tracedRuntime(next) {
  const seen = new Map();
  let manifests = 0;
  walk(next, (absolute, relative) => {
    if (!relative.endsWith(".nft.json")) {
      return;
    }
    manifests += 1;
    for (const listed of JSON.parse(fs.readFileSync(absolute, "utf-8")).files ?? []) {
      const target = path.resolve(path.dirname(absolute), listed);
      if (!path.relative(next, target).startsWith("..")) {
        continue;
      }
      let stat;
      try {
        stat = fs.statSync(target);
      } catch {
        continue;
      }
      if (stat.isFile()) {
        seen.set(fs.realpathSync(target), stat.size);
      }
    }
  });
  const byPackage = {};
  for (const [file, size] of seen) {
    const parts = file.split(path.sep);
    const at = parts.lastIndexOf("node_modules");
    const name =
      at < 0 ? "<워크스페이스>" : parts[at + 1].startsWith("@") ? `${parts[at + 1]}/${parts[at + 2]}` : parts[at + 1];
    byPackage[name] = (byPackage[name] ?? 0) + size;
  }
  return {
    manifests,
    files: seen.size,
    mb: mb([...seen.values()].reduce((sum, size) => sum + size, 0)),
    largest: Object.entries(byPackage)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, size]) => `${name} ${String(mb(size))}MB`),
  };
}

// 위젯의 devDependencies 가운데 빌드가 실제로 import 하는 것(tools/element.ts, postcss.config.mjs)과 next build 의 타입
// 검사가 요구하는 것(typescript 와 @types). 시험·스토리 파일이 요구하는 것은 여기 넣지 않았다.
const BUILD_DEV = [
  "@tailwindcss/postcss",
  "@tailwindcss/vite",
  "tailwindcss",
  "typescript",
  "vite",
  "@types/node",
  "@types/react",
  "@types/react-dom",
];

function stepSizes(out, { whole }) {
  const next = path.join(WIDGET, ".next");
  const manifest = JSON.parse(fs.readFileSync(path.join(WIDGET, "package.json"), "utf-8"));
  const runtime = Object.keys(manifest.dependencies);
  const dev = Object.keys(manifest.devDependencies);
  const outputs = {
    next: sizeOf(next),
    nextWithoutCache: sizeOf(next, (absolute) => absolute === path.join(next, "cache")),
    nextTopLevel: Object.fromEntries(
      (fs.existsSync(next) ? fs.readdirSync(next) : []).map((name) => [name, sizeOf(path.join(next, name))]),
    ),
    publicElement: sizeOf(path.join(WIDGET, "public", "element.js")),
    publicFonts: sizeOf(path.join(WIDGET, "public", "fonts")),
    widgetSource: sizeOf(
      WIDGET,
      (absolute, entry) => path.dirname(absolute) === WIDGET && WORKSPACE_SKIPPED.includes(entry.name),
    ),
  };
  const closures = {
    runtimeDirect: closure(runtime),
    runtimeThroughWrapper: closure([...runtime, "vite", "@tailwindcss/vite"]),
    build: closure([...runtime, ...dev.filter((name) => BUILD_DEV.includes(name))]),
    allDev: closure([...runtime, ...dev]),
  };
  const result = { outputs, closures, traced: tracedRuntime(next) };
  if (whole) {
    result.wholeWebNodeModules = sizeOf(path.join(WEB, "node_modules"));
  }
  const markers = {
    buildExists: fs.existsSync(path.join(next, "BUILD_ID")),
    noMissingRoots: Object.values(closures).every((item) => item.missingRoots.length === 0),
    nextInClosure: closures.runtimeDirect.largest.some((line) => line.startsWith("next@")),
    tracedListed: result.traced.files > 0 && result.traced.largest.some((line) => line.startsWith("next ")),
    // 묶음이 넓어질수록 패키지가 늘어야 한다. 아니면 의존을 따라가지 못한 것이다.
    closuresGrow:
      closures.runtimeDirect.packages < closures.runtimeThroughWrapper.packages &&
      closures.runtimeThroughWrapper.packages <= closures.build.packages &&
      closures.build.packages < closures.allDev.packages,
  };
  result.rounds = [{ label: "sizes", measured: Object.values(markers).every(Boolean), markers }];
  const show = ({ bytes, files }) => `${String(mb(bytes))}MB (${String(files)} 파일)`;
  console.log(`.next 전체 ${show(outputs.next)}, cache 빼고 ${show(outputs.nextWithoutCache)}`);
  for (const [name, size] of Object.entries(outputs.nextTopLevel)) {
    console.log(`  .next/${name}: ${show(size)}`);
  }
  console.log(`public/element.js ${show(outputs.publicElement)}, public/fonts ${show(outputs.publicFonts)}`);
  console.log(`위젯 소스(node_modules·산출물 빼고) ${show(outputs.widgetSource)}`);
  for (const [name, item] of Object.entries(closures)) {
    console.log(`${name}: 패키지 ${String(item.packages)}, ${String(item.mb)}MB, 파일 ${String(item.files)}`);
    console.log(`  큰 것: ${item.largest.join(", ")}`);
    console.log(`  워크스페이스: ${item.workspacePackages.join(", ")}`);
  }
  console.log(
    `Next 가 추적한 실행 파일(nft ${String(result.traced.manifests)}개, .next 밖): 파일 ${String(result.traced.files)}, ${String(result.traced.mb)}MB`,
  );
  console.log(`  큰 것: ${result.traced.largest.join(", ")}`);
  if (whole) {
    console.log(`web/node_modules 전체 ${show(result.wholeWebNodeModules)}`);
  }
  console.log(`표지: ${JSON.stringify(markers)}`);
  return report(out, "sizes.json", result);
}

// --- admin -----------------------------------------------------------------------------------------------------------

async function stepAdmin(out, { rounds: count }) {
  const bin = createRequire(path.join(ADMIN, "package.json")).resolve("next/dist/bin/next");
  const rounds = [];
  for (let index = 1; index <= count; index += 1) {
    remove(path.join(ADMIN, ".next"));
    const cpuBusyBeforePct = await cpuBusyPercent();
    const startedAt = Date.now();
    const run = await runTimed(process.execPath, [bin, "build"], { cwd: ADMIN, env: buildEnv({}) });
    const buildIdAt = mtimeMs(path.join(ADMIN, ".next", "BUILD_ID"));
    const banner = run.lines.find(({ text }) => NEXT_BANNER.test(text));
    const markers = {
      exitZero: run.code === 0 && !run.timedOut,
      nextBanner: banner !== undefined,
      routeTable: run.lines.some(({ text }) => NEXT_ROUTES.test(text.trim())),
      buildIdFresh: buildIdAt !== null && buildIdAt >= startedAt,
    };
    const round = {
      label: `admin-cold-${String(index)}`,
      cpuBusyBeforePct,
      totalMs: run.totalMs,
      untilNextBannerMs: banner?.ms ?? null,
      nextPhases: nextPhases(run.lines, run.totalMs),
      markers,
      measured: Object.values(markers).every(Boolean),
      lines: run.lines,
    };
    rounds.push(round);
    const inside =
      round.nextPhases === null
        ? ""
        : ` [컴파일 ${seconds(round.nextPhases.compileMs)}, 타입 검사 ${seconds(round.nextPhases.typescriptMs)}, 페이지 ${seconds(round.nextPhases.pagesMs)}]`;
    console.log(
      `${round.label}: ${seconds(run.totalMs)}${inside} 직전 CPU ${String(cpuBusyBeforePct)}% 측정=${String(round.measured)} ${JSON.stringify(markers)}`,
    );
  }
  const measured = rounds.filter((round) => round.measured);
  const summary = {
    coldTotalMs: range(measured.map((round) => round.totalMs)),
    cpuBusyBeforePct: range(measured.map((round) => round.cpuBusyBeforePct)),
  };
  console.log(JSON.stringify(summary));
  return report(out, "admin.json", { summary, rounds });
}

// --- 진입 ------------------------------------------------------------------------------------------------------------

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: {
    out: { type: "string" },
    cold: { type: "string", default: "3" },
    warm: { type: "string", default: "3" },
    rounds: { type: "string", default: "3" },
    trees: { type: "string", default: TREES.join(",") },
    whole: { type: "boolean", default: false },
  },
});
const [step] = positionals;
if (step === undefined || values.out === undefined || !path.isAbsolute(values.out)) {
  console.error("사용: node measure.mjs <install|build|phases|diff|compare|net|sizes|admin> --out <절대 경로>");
  process.exit(2);
}
const out = path.resolve(values.out);
const fromRepo = path.relative(REPO, out);
if (!fromRepo.startsWith("..") && !path.isAbsolute(fromRepo)) {
  console.error(`--out 은 저장소 밖이어야 한다: ${out}`);
  process.exit(2);
}
const trees = values.trees.split(",");
if (trees.some((name) => !TREES.includes(name))) {
  console.error(`--trees 는 ${TREES.join(",")} 가운데서 고른다: ${values.trees}`);
  process.exit(2);
}
assertLayout();
fs.mkdirSync(out, { recursive: true });
const steps = {
  install: () => stepInstall(out),
  build: () => stepBuild(out, { cold: Number(values.cold), warm: Number(values.warm) }),
  phases: () => stepPhases(out, { rounds: Number(values.rounds) }),
  diff: () => stepDiff(out, { trees }),
  compare: () => stepCompare(out),
  net: () => stepNet(out),
  sizes: () => stepSizes(out, { whole: values.whole }),
  admin: () => stepAdmin(out, { rounds: Number(values.rounds) }),
};
if (!(step in steps)) {
  console.error(`모르는 단계: ${step}`);
  process.exit(2);
}
const unmeasured = await steps[step]();
process.exit(unmeasured === 0 ? 0 : 1);
