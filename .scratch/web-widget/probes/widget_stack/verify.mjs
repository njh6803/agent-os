// web-widget 위젯 스택 프로브: 임시 트리에서 `pnpm -C web verify` 의 단계를 하나씩 돌려 단계마다 결과를 남긴다.
//   node .scratch/web-widget/probes/widget_stack/verify.mjs <작업 루트>/<후보>
// verify 는 `&&` 사슬이라 앞 단계가 실패하면 뒤 단계를 돌지 않는다. 후보끼리 견주려면 단계마다의 결과가 있어야 해서
// web/package.json 의 verify 를 `&&` 로 갈라 `pnpm run <단계>` 를 차례로 다 돈다. 단계 목록은 그 파일에서 읽는다.
// 결과는 단계마다 종료 코드와 출력의 끝, 테스트 단계는 실패한 테스트 이름이다. <작업 루트>/<후보>/verify.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const verify = JSON.parse(readFileSync(join(web, "package.json"), "utf-8")).scripts.verify;
const steps = verify.split("&&").map((part) => part.trim().replace(/^pnpm run /, ""));

const clean = (text) => text.replace(/\u001b\[[\d;]*m/g, "");
const result = { candidate: relative(dirname(ws), ws), verify, steps: [] };
for (const step of steps) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 단계 이름은 package.json 의 것뿐이다.
  const proc = spawnSync(`pnpm run ${step}`, {
    cwd: web,
    encoding: "utf-8",
    shell: true,
    maxBuffer: 1 << 28,
  });
  const lines = clean(`${proc.stdout}${proc.stderr}`)
    .split(/\r?\n/)
    .filter(
      (line) =>
        line.trim() !== "" && !/TimeoutNaNWarning|Timeout duration|trace-warnings/.test(line),
    );
  const entry = { step, status: proc.status, tail: lines.slice(-6) };
  if (step === "test") {
    entry.failed = lines.filter((line) => /^\s*×/.test(line)).map((line) => line.trim());
    entry.summary = lines
      .filter((line) => /^\s*(Test Files|Tests)\s/.test(line))
      .map((line) => line.trim());
  }
  result.steps.push(entry);
}

writeFileSync(join(ws, "verify.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
process.exitCode = result.steps.every((step) => step.status === 0) ? 0 : 1;
