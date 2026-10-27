// 사진 비교 흔들림 프로브(harness 티켓 016)의 호스트 쪽 러너. 사진 비교와 같은 이미지(web/tools/visual.ts 의 IMAGE)의
// 컨테이너를 같은 모양(네트워크 없음, web/ 읽기 전용, 패키지에 깔린 Playwright 를 tmpfs 의 node_modules 로 복사)으로
// 띄워 flake.probe.mts 를 돌리고, 그 결과(/out/results.jsonl)를 사례 × 갈래 × 사진마다 A·B 수로 묶어 찍는다.
//
//   node .scratch/harness/probes/visual_flake/run.mjs --out <저장소 밖 폴더> [--reps N] [--cases alert,textfield,switch]
//        [--conditions now,wait] [--wait-ms 1500]
//
// 저장소 루트에서 친다. 정적 빌드(web/packages/ui/storybook-static)가 있어야 한다(`pnpm -C web visual` 이나
// `pnpm -C web/packages/ui run build-storybook` 이 짓는다). 이 러너는 짓지 않는다. <out> 은 비었거나 이 러너가 앞서 심은
// 표지 파일(.visual-flake-out)이 있을 때만 비우고 다시 쓴다.
//
// A·B 를 가르는 정답 사진은 작업 트리가 아니라 `--baseline <커밋>`(기본 HEAD)의 web/packages/ui/visual/snapshots 를
// `git show` 로 꺼내 <out>/baseline 에 두고 컨테이너의 /baseline 으로 넘긴다. 같은 브랜치가 정답을 다시 만들어도 앞서
// 적은 결과를 그 커밋으로 다시 낼 수 있다. 커밋은 summary.json 에 남는다.
//
// 측정의 표지는 둘이다. 시험 하나가 results.jsonl 에 한 줄을 쓴다(상태를 확인하고 사진을 하나 이상 찍었을 때만). 기대한 줄
// (되풀이 × 사례 × 갈래)보다 적으면 모자란 수를 측정 아님으로 찍는다. 그리고 뜬 브라우저의 명령줄(meta.json)이 요청한
// --browser-args 대로 부분 래스터를 껐거나 켜야 한다. 명령줄이 없거나 다르면 결과 전부가 측정 아니다. 둘 가운데 하나라도
// 어긋나면 종료 코드가 1 이다. 결과는 <out>/summary.json 에도 쓴다(argsMatched 가 뒤의 표지다).
import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { isAbsolute, join, relative, resolve, sep } from "node:path";
import { IMAGE, playwrightPackages } from "../../../../web/tools/visual.ts";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const WEB = join(REPO, "web");
const PACKAGE = join(WEB, "packages", "ui");
const MARKER = ".visual-flake-out";

const args = process.argv.slice(2);
const option = (name, fallback) => {
  const at = args.indexOf(name);
  return at === -1 ? fallback : args[at + 1];
};
const out = option("--out", null);
const reps = Number(option("--reps", "10"));
const cases = option("--cases", "alert,textfield,switch");
const conditions = option("--conditions", "now,wait");
const waitMs = option("--wait-ms", "1500");
// 브라우저 실행 인자. `config`(기본)는 패키지 설정의 것, `none` 은 인자 없음, 그 밖은 공백으로 가른 인자다. 컨테이너의
// FLAKE_ARGS 로 가서 probe.config.mts 가 고른다. 실제로 뜬 브라우저의 명령줄은 meta.json 에 남고, 아래에서 부분 래스터
// 인자가 그 명령줄에 있었는지 찍는다.
const browserArgs = option("--browser-args", "config");
const baselineRev = option("--baseline", "HEAD");

if (out === null || !isAbsolute(out)) {
  console.error("--out <저장소 밖의 절대 경로> 가 필요하다");
  process.exit(2);
}
if (!relative(REPO, out).startsWith("..")) {
  console.error(`--out 이 저장소 안이다: ${out}`);
  process.exit(2);
}
if (existsSync(out)) {
  const entries = readdirSync(out);
  if (entries.length > 0 && !entries.includes(MARKER)) {
    console.error(`비지 않았고 표지(${MARKER})가 없는 폴더는 비우지 않는다: ${out}`);
    process.exit(2);
  }
  rmSync(out, { recursive: true, force: true });
}
mkdirSync(out, { recursive: true });
writeFileSync(join(out, MARKER), "");
if (!existsSync(join(PACKAGE, "storybook-static", "index.json"))) {
  console.error("정적 빌드가 없다. pnpm -C web/packages/ui run build-storybook 을 먼저 친다");
  process.exit(2);
}

const git = (gitArgs) => spawnSync("git", ["-C", REPO, ...gitArgs], { timeout: 60_000, maxBuffer: 64 * 1024 * 1024 });
const commit = git(["rev-parse", "--verify", `${baselineRev}^{commit}`]);
if (commit.status !== 0) {
  console.error(`--baseline 을 커밋으로 풀지 못했다: ${baselineRev}`);
  process.exit(2);
}
const baselineCommit = commit.stdout.toString().trim();
const SNAPSHOTS = "web/packages/ui/visual/snapshots";
const listed = git(["ls-tree", "-r", "--name-only", baselineCommit, "--", SNAPSHOTS]);
const baselineDir = join(out, "baseline");
mkdirSync(baselineDir, { recursive: true });
let extracted = 0;
for (const path of listed.stdout.toString().split("\n").filter((line) => line.endsWith(".png"))) {
  const blob = git(["show", `${baselineCommit}:${path}`]);
  if (blob.status !== 0) {
    console.error(`정답 사진을 꺼내지 못했다: ${baselineCommit}:${path}`);
    process.exit(2);
  }
  writeFileSync(join(baselineDir, path.slice(SNAPSHOTS.length + 1)), blob.stdout);
  extracted += 1;
}
if (extracted === 0) {
  console.error(`${baselineCommit} 에 정답 사진이 없다`);
  process.exit(2);
}
console.log(`정답 사진 ${extracted}장을 ${baselineCommit.slice(0, 8)} 에서 꺼냈다`);

// 패키지에 깔린 Playwright 셋을 링크를 풀어 임시 폴더로 복사한다(web/tools/visual.ts 의 copyPlaywright 와 같은 일).
const staged = mkdtempSync(join(tmpdir(), "visual-flake-"));
let status = 1;
try {
  for (const [name, from] of Object.entries(playwrightPackages(PACKAGE))) {
    cpSync(from, join(staged, "node_modules", ...name.split("/")), {
      recursive: true,
      dereference: true,
      filter: (source) => !relative(from, source).split(sep).includes("node_modules"),
    });
  }
  const script = [
    "set -e",
    "cp -R /staged/node_modules/. node_modules/",
    "exec node node_modules/@playwright/test/cli.js test -c /probe/probe.config.mts",
  ].join("\n");
  const started = Date.now();
  const run = spawnSync(
    "docker",
    [
      "run",
      "--rm",
      "--init",
      "--ipc=host",
      "--network",
      "none",
      "--mount",
      `type=bind,source=${WEB},target=/web,readonly`,
      "--mount",
      `type=bind,source=${staged},target=/staged,readonly`,
      "--mount",
      "type=tmpfs,target=/web/packages/ui/node_modules",
      "--mount",
      `type=bind,source=${HERE},target=/probe,readonly`,
      "--mount",
      `type=bind,source=${out},target=/out`,
      "--mount",
      `type=bind,source=${baselineDir},target=/baseline,readonly`,
      "--workdir",
      "/web/packages/ui",
      "-e",
      `FLAKE_REPS=${reps}`,
      "-e",
      `FLAKE_CASES=${cases}`,
      "-e",
      `FLAKE_CONDITIONS=${conditions}`,
      "-e",
      `FLAKE_WAIT_MS=${waitMs}`,
      "-e",
      `FLAKE_ARGS=${browserArgs}`,
      IMAGE,
      "sh",
      "-c",
      script,
    ],
    { stdio: "inherit" },
  );
  const seconds = Math.round((Date.now() - started) / 1000);
  console.log(`컨테이너 종료 ${String(run.status)}, ${seconds}초`);

  const lines = existsSync(join(out, "results.jsonl"))
    ? readFileSync(join(out, "results.jsonl"), "utf-8").split("\n").filter(Boolean)
    : [];
  const records = lines.map((line) => JSON.parse(line));
  const expected = reps * cases.split(",").length * conditions.split(",").length;
  const table = {};
  for (const { case: caseName, condition, shots } of records) {
    for (const { name, verdict, sha256, pixels, step } of shots) {
      const key = `${caseName} ${condition} ${name}${step === undefined ? "" : ` @${step}ms`}`;
      table[key] ??= { A: 0, B: 0, variants: {} };
      table[key][verdict] += 1;
      if (verdict === "B") {
        table[key].variants[`${sha256.slice(0, 12)} (${pixels}px)`] =
          (table[key].variants[`${sha256.slice(0, 12)} (${pixels}px)`] ?? 0) + 1;
      }
    }
  }
  for (const [key, { A, B, variants }] of Object.entries(table)) {
    const shown = Object.entries(variants).map(([variant, count]) => `${variant}×${count}`);
    console.log(`${key}: A ${A}, B ${B}${shown.length > 0 ? ` — ${shown.join(", ")}` : ""}`);
  }
  const missing = expected - records.length;
  console.log(`시험 ${records.length}/${expected}${missing > 0 ? `, 측정 아님 ${missing}` : ""}`);
  const meta = existsSync(join(out, "meta.json")) ? JSON.parse(readFileSync(join(out, "meta.json"), "utf-8")) : null;
  const partialOff = meta === null ? null : meta.commandLine.split(" ").includes("--disable-partial-raster");
  console.log(`브라우저 ${meta?.version ?? "모름"}, 래스터 ${meta?.featureStatus?.rasterization ?? "모름"}, 부분 래스터 끔 ${String(partialOff)}`);
  // 재려는 상황의 표지: 뜬 브라우저의 명령줄이 요청한 인자대로 부분 래스터를 껐거나 켰다. `config` 는 패키지 설정의
  // BROWSER_ARGS 가 그 인자를 든다고 본다. 명령줄이 없거나 요청과 다르면 결과 전부를 측정 아님으로 센다.
  const expectedOff =
    browserArgs === "none"
      ? false
      : browserArgs === "config" || browserArgs.split(" ").includes("--disable-partial-raster");
  const argsMatched = partialOff === expectedOff;
  if (!argsMatched) {
    console.log(`측정 아님: 브라우저의 명령줄이 요청(--browser-args ${browserArgs})과 다르거나 없다`);
  }
  writeFileSync(
    join(out, "summary.json"),
    JSON.stringify(
      {
        image: IMAGE,
        reps,
        cases,
        conditions,
        waitMs,
        browserArgs,
        partialOff,
        argsMatched,
        baselineCommit,
        seconds,
        expected,
        records: records.length,
        table,
      },
      null,
      2,
    ),
  );
  status = missing === 0 && argsMatched ? 0 : 1;
} finally {
  rmSync(staged, { recursive: true, force: true });
}
process.exit(status);
