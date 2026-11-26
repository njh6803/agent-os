// 이미지 안의 위젯 설정 사본(next.config.ts)에 값 파일의 응답 머리 규칙 하나를 더한다. 저장소의 파일은 고치지 않는다.
//
// 더하는 것: /runtime.json 에 Access-Control-Allow-Origin: * . 페이지 안 번들은 사이트의 문서에서 돌아, 값 파일을 위젯
// 출처에서 교차 출처 요청으로 받는다. 그 머리가 없으면 브라우저가 본문을 스크립트에 주지 않는다. 값은 사이트 파일과
// 무관하게 늘 같아서 빌드 때 굳혀도 된다.
//
// 사용: node patch-config.mjs <next.config.ts 의 경로>. 고칠 자리(element.js 규칙의 머리)가 정확히 한 번 나오지 않으면
// 아무것도 쓰지 않고 종료 1 로 끝난다.

import { readFileSync, writeFileSync } from "node:fs";

const [path] = process.argv.slice(2);
if (path === undefined) {
  console.error("사용: node patch-config.mjs <next.config.ts 의 경로>");
  process.exit(2);
}
const ANCHOR = `      {\n        source: "/element.js",`;
const RULE = [
  "      {",
  '        source: "/runtime.json",',
  '        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],',
  "      },",
  "",
].join("\n");

const text = readFileSync(path, "utf-8").replace(/\r\n/g, "\n");
const found = text.split(ANCHOR).length - 1;
if (found !== 1) {
  console.error(`고칠 자리를 ${String(found)}번 찾았다. 한 번이어야 한다: ${path}`);
  process.exit(1);
}
writeFileSync(path, text.replace(ANCHOR, RULE + ANCHOR));
console.log(`WRV_PROBE patched ${path}`);
