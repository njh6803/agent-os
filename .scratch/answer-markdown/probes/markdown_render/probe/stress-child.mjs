// stress.mjs 가 회차마다 띄우는 자식. 입력 하나를 제한을 건 컴포넌트로 그리고 걸린 시간을 JSON 한 줄로 낸다.
// 인자: <묶음 경로> <후보> <입력 이름>. 그리다 던지면 `threw` 로 적고 종료 코드 0(던진 것도 측정 결과다).
// 입력은 inputs.mjs 가 원천이다(2026-11-11 에 옮겼다. 브라우저 프로브와 같은 글을 쓰려는 것이다).
import { createRequire } from "node:module";
import { performance } from "node:perf_hooks";
import { STRESS_INPUTS } from "./inputs.mjs";

const [bundle, candidate, name] = process.argv.slice(2);

const make = STRESS_INPUTS[name];
if (make === undefined) {
  console.log(JSON.stringify({ ok: false, reason: `없는 입력이다: ${name}` }));
  process.exit(2);
}
const input = make();
const entry = createRequire(import.meta.url)(bundle);
const repeats = name === "typical-1kb" ? 30 : 1;
const times = [];
let htmlBytes = 0;
try {
  if (name === "typical-1kb") entry.render(candidate, "restricted", name, input);
  for (let i = 0; i < repeats; i += 1) {
    const start = performance.now();
    const html = entry.render(candidate, "restricted", name, input);
    times.push(performance.now() - start);
    htmlBytes = Buffer.byteLength(html);
    if (!html.includes(`<div data-probe="${name}">`)) throw new Error("표지가 없다");
  }
  times.sort((a, b) => a - b);
  console.log(
    JSON.stringify({
      ok: true,
      candidate,
      name,
      inputBytes: Buffer.byteLength(input),
      htmlBytes,
      repeats,
      medianMs: Math.round(times[Math.floor(times.length / 2)] * 100) / 100,
      maxMs: Math.round(times[times.length - 1] * 100) / 100,
    }),
  );
} catch (error) {
  console.log(
    JSON.stringify({
      ok: true,
      candidate,
      name,
      inputBytes: Buffer.byteLength(input),
      threw: String(error).slice(0, 200),
    }),
  );
}
