// 이미지 안의 위젯 사본을 고친다(저장소의 파일은 그대로다). 측정용 갈래 하나(widget-lean-notc)가 쓴다.
//
// 사용: node patch-widget.mjs notypecheck   (작업 폴더가 apps/widget 의 사본)
//
// - notypecheck: next.config.ts 에 typescript.ignoreBuildErrors 를 넣어 next build 의 타입 검사를 건너뛴다. 뜰 때 하는
//   빌드에서 타입 검사가 시간과 메모리의 얼마를 차지하는지 보려는 것이다. 타입 검사는 CI 가 따로 돈다.
//
// 바꿀 자리를 정확히 한 번 찾지 못하면 던진다. 조용히 지나가면 고치지 않은 판을 고친 판으로 잰다.

import { readFileSync, writeFileSync } from "node:fs";

const [mode] = process.argv.slice(2);
if (mode !== "notypecheck") {
  throw new Error("사용: node patch-widget.mjs notypecheck");
}
const path = "next.config.ts";
const from = "  agentRules: false,\n";
const text = readFileSync(path, "utf-8").replaceAll("\r\n", "\n");
const count = text.split(from).length - 1;
if (count !== 1) {
  throw new Error(`${path}: 바꿀 자리를 ${count}번 찾았다(한 번이어야 한다): ${from}`);
}
writeFileSync(path, text.replace(from, `${from}  typescript: { ignoreBuildErrors: true },\n`));
console.log(`RI_PROBE patched ${path}`);
