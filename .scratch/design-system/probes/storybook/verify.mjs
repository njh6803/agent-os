// design-system Storybook 프로브: 임시 트리에서 `pnpm -C web verify` 의 단계를 하나씩 돌려 단계마다 결과와 걸린 시간을 남긴다.
//   node .scratch/design-system/probes/storybook/verify.mjs <작업 루트>/storybook
// widget_stack/verify.mjs 와 같은 방식이다. verify 는 `&&` 사슬이라 앞 단계가 실패하면 뒤 단계를 돌지 않으므로, web/package.json
// 의 verify 를 `&&` 로 갈라 `pnpm run <단계>` 를 차례로 다 돈다. 단계 목록은 그 파일에서 읽는다. test 단계만 같은
// `vitest run` 에 JSON 보고기를 더해 부른다(<작업 루트>/storybook/test-report.json).
// 그 뒤 스토리 테스트(vitest 의 storybook 프로젝트)만 두 번 돈다. 처음은 Storybook 의 vitest 캐시
// (web/node_modules/.cache/storybook)를 지우고, 다음은 그대로 둔다. 결과는 <작업 루트>/storybook/verify.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const verify = JSON.parse(readFileSync(join(web, "package.json"), "utf-8")).scripts.verify;
const steps = verify.split("&&").map((part) => part.trim().replace(/^pnpm run /, ""));

const result = { verify, steps: [], storybookOnly: [] };
const REPORT = join(ws, "test-report.json");
for (const step of steps) {
  // test 단계(vitest run)는 같은 명령에 JSON 보고기를 더해 돈다. 비 TTY 의 기본 보고기는 통과한 파일을 적지 않아서
  // 스토리 테스트가 그 단계에 들었는지를 보고서의 파일 이름으로 센다.
  const run = timed(
    step === "test"
      ? `pnpm exec vitest run --reporter=default --reporter=json --outputFile=${REPORT}`
      : `pnpm run ${step}`,
  );
  const entry = { step, status: run.status, ms: run.ms, tail: run.lines.slice(-6) };
  if (step === "test") {
    entry.failed = run.lines.filter((line) => /^\s*×/.test(line)).map((line) => line.trim());
    entry.summary = run.lines
      .filter((line) => /^\s*(Test Files|Tests|Duration)\s/.test(line))
      .map((line) => line.trim());
    const report = JSON.parse(readFileSync(REPORT, "utf-8"));
    const stories = report.testResults.filter((file) => file.name.endsWith(".stories.tsx"));
    entry.report = {
      files: report.numTotalTestSuites,
      tests: report.numTotalTests,
      passed: report.numPassedTests,
      storyFiles: stories.map((file) => file.name.slice(file.name.indexOf("packages/ui"))),
      storyTests: stories.reduce((sum, file) => sum + file.assertionResults.length, 0),
    };
    entry.warnings = [
      ...new Set(run.lines.filter((line) => /defines Vite-specific hooks/.test(line))),
    ];
  }
  result.steps.push(entry);
}

for (const cache of ["cold", "warm"]) {
  if (cache === "cold") {
    rmSync(join(web, "node_modules", ".cache", "storybook"), { recursive: true, force: true });
  }
  const run = timed("pnpm exec vitest run --project storybook");
  result.storybookOnly.push({
    cache,
    status: run.status,
    wallMs: run.ms,
    summary: run.lines
      .filter((line) => /^\s*(Test Files|Tests|Duration)\s/.test(line))
      .map((line) => line.trim()),
  });
}

writeFileSync(join(ws, "verify.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
process.exitCode = result.steps.every((step) => step.status === 0) ? 0 : 1;

function timed(command) {
  const started = Date.now();
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 명령은 package.json 의 단계 이름과 이 파일의 상수뿐이다.
  const run = spawnSync(command, {
    cwd: web,
    encoding: "utf-8",
    shell: true,
    maxBuffer: 1 << 28,
    env: { ...process.env, STORYBOOK_DISABLE_TELEMETRY: "1" },
  });
  const lines = `${run.stdout}${run.stderr}`
    .replace(/\u001b\[[\d;]*m/g, "")
    .split(/\r?\n/)
    .filter(
      (line) =>
        line.trim() !== "" && !/TimeoutNaNWarning|Timeout duration|trace-warnings/.test(line),
    );
  return { status: run.status, ms: Date.now() - started, lines };
}
