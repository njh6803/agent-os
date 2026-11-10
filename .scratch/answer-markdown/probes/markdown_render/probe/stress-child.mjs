// stress.mjs 가 회차마다 띄우는 자식. 입력 하나를 제한을 건 컴포넌트로 그리고 걸린 시간을 JSON 한 줄로 낸다.
// 인자: <묶음 경로> <후보> <입력 이름>. 그리다 던지면 `threw` 로 적고 종료 코드 0(던진 것도 측정 결과다).
import { createRequire } from "node:module";
import { performance } from "node:perf_hooks";

const [bundle, candidate, name] = process.argv.slice(2);

const TYPICAL = [
  "## 결론",
  "",
  "임대인이 **보증금을 돌려주지 않으면** 임차권등기명령을 신청할 수 있습니다[1].",
  "",
  "1. 계약이 끝났는지 확인합니다.",
  "2. 관할 법원에 신청서를 냅니다.",
  "   - 임대차계약서",
  "   - 주민등록등본",
  "3. 결정문을 받은 뒤 등기를 확인합니다.",
  "",
  "| 서류 | 발급처 | 비고 |",
  "|---|---|---|",
  "| 등기사항증명서 | 인터넷등기소 | 발급 후 1개월 이내 |",
  "| 주민등록등본 | 정부24 | 주소 변동 포함 |",
  "",
  "> 신청 뒤에 이사해도 대항력이 유지됩니다.",
  "",
  "자세한 절차는 [대한민국 법원 전자소송](https://ecfs.scourt.go.kr/)에서 볼 수 있습니다.",
  "",
  "출처",
  "[1] 주택임대차보호법 제3조의3 (갱신 2026-01-02) https://www.law.go.kr/법령/주택임대차보호법",
  "",
].join("\n");

const INPUTS = {
  "typical-1kb": () => TYPICAL,
  "long-100kb": () => TYPICAL.repeat(Math.ceil(100_000 / Buffer.byteLength(TYPICAL))),
  "stars-10k": () => "*".repeat(10_000),
  "underscores-10k": () => "_".repeat(10_000),
  "brackets-10k": () => "[".repeat(10_000),
  "link-open-3k": () => "[a](".repeat(3_000),
  "quote-3k": () => `${">".repeat(3_000)} a`,
  "backticks-10k": () => "`".repeat(10_000),
  "lt-10k": () => "<".repeat(10_000),
  "ampersands-10k": () => "&".repeat(10_000),
  "nested-list-200": () => Array.from({ length: 200 }, (_, i) => `${" ".repeat(2 * i)}- a`).join("\n"),
  "emphasis-mix-2k": () => "*a **b ".repeat(2_000),
  "pipes-50x200": () => `${"|".repeat(200)}\n`.repeat(50),
  "bang-brackets-5k": () => "![".repeat(5_000),
};

const make = INPUTS[name];
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
