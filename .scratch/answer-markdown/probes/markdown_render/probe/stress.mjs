// 부하 프로브(요청 밖에서 더 본 것). 병적인 입력에서 제한을 건 컴포넌트가 멈추거나 던지는지, 보통의 답 하나를
// 그리는 데 얼마나 걸리는지 본다. 모델의 답은 문서에서 온 글을 품을 수 있어, 입력이 늘 얌전하다고 볼 수 없다.
//
// 돌리기: node probe/stress.mjs
// 산출물: out/stress/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 회차마다 자식 프로세스를 띄우고 15초에 끊는다(동기 렌더는 안에서 끊을 수 없다). 끊긴 것(timeout)과 던진 것(threw)은
// 측정 결과다. 자식이 JSON 한 줄을 내지 못한 회차만 측정이 아닌 것으로 세고, 하나라도 있으면 종료 코드 1.
// 시간은 Node 24 의 서버 렌더(react-dom/server, production)로 잰 것이라 브라우저의 값이 아니다. 견줌에만 쓴다.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "stress");
const BUNDLE = join(ROOT, "out", "build", "stress-entry.cjs");
const TIMEOUT_MS = 15_000;
const CANDIDATES = ["react-markdown", "markdown-to-jsx"];
const INPUTS = [
  "typical-1kb", "long-100kb", "stars-10k", "underscores-10k", "brackets-10k", "link-open-3k", "quote-3k",
  "backticks-10k", "lt-10k", "ampersands-10k", "nested-list-200", "emphasis-mix-2k", "pipes-50x200", "bang-brackets-5k",
];

mkdirSync(OUT, { recursive: true });
mkdirSync(dirname(BUNDLE), { recursive: true });
await build({
  entryPoints: [join(ROOT, "probe", "entry.tsx")],
  outfile: BUNDLE,
  bundle: true,
  platform: "node",
  format: "cjs",
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  logLevel: "warning",
});

const rows = [];
const notMeasured = [];
for (const candidate of CANDIDATES) {
  for (const name of INPUTS) {
    const run = spawnSync(process.execPath, [join(ROOT, "probe", "stress-child.mjs"), BUNDLE, candidate, name], {
      encoding: "utf8",
      timeout: TIMEOUT_MS,
      maxBuffer: 64 * 1024 * 1024,
    });
    if (run.error !== undefined && run.error.code === "ETIMEDOUT") {
      rows.push({ candidate, name, timeout: true, timeoutMs: TIMEOUT_MS });
      continue;
    }
    const line = (run.stdout ?? "").trim().split(/\r?\n/).pop() ?? "";
    let parsed = null;
    try {
      parsed = JSON.parse(line);
    } catch {
      parsed = null;
    }
    if (parsed === null || parsed.ok !== true) {
      // 스택이 넘쳐 프로세스가 죽은 경우도 여기로 온다. stderr 의 앞머리로 가른다.
      const stderr = (run.stderr ?? "").slice(0, 300);
      if (/Maximum call stack size exceeded|RangeError/.test(stderr)) {
        rows.push({ candidate, name, crashed: stderr.split(/\r?\n/).find((l) => /RangeError|Maximum/.test(l)) });
      } else {
        notMeasured.push({ candidate, name, status: run.status, signal: run.signal, stderr });
      }
      continue;
    }
    rows.push(parsed);
  }
}

writeFileSync(join(OUT, "summary.json"), JSON.stringify({ timeoutMs: TIMEOUT_MS, notMeasured, rows }, null, 2));
console.log(
  JSON.stringify({
    probe: "stress",
    expectedRounds: CANDIDATES.length * INPUTS.length,
    measuredRounds: rows.length,
    notMeasured: notMeasured.length,
    rows: rows.map((r) => ({
      c: r.candidate,
      n: r.name,
      ...(r.timeout ? { timeout: true } : {}),
      ...(r.threw ? { threw: r.threw } : {}),
      ...(r.crashed ? { crashed: r.crashed } : {}),
      ...(r.medianMs === undefined ? {} : { ms: r.medianMs, in: r.inputBytes, out: r.htmlBytes }),
    })),
  }),
);
if (notMeasured.length > 0) {
  console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
  process.exit(1);
}
