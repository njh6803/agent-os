// 이미지 안의 관리 화면 사본을 고친다(저장소의 파일은 그대로다). 측정용 갈래 하나가 쓴다.
//
// 사용: node patch-admin.mjs standalone   (작업 폴더가 apps/admin 의 사본)
//
// - standalone: next.config.ts 에 output: "standalone" 과 추적의 뿌리(web/)를 더한다. 크기와 HOSTNAME 을 보려는 것이다.
//
// 옛 판에는 exception 갈래가 있었다. 상류 판정이 호스트 하나를 더 받게 하는 측정용 예외였다. 티켓 03 이 같은 예외를 코드에
// 들이자(표지 파일 + AGENT_OS_CONTAINER_NETWORK=1) 그 줄이 없어져 갈래가 맞지 않게 됐고, 시제품 Dockerfile 의
// admin-exception 단계가 코드의 예외를 그대로 켜게 바꾸고 이 갈래를 뺐다(티켓 08).
//
// 바꿀 자리를 정확히 한 번 찾지 못하면 던진다. 조용히 지나가면 고치지 않은 판을 고친 판으로 잰다.

import { readFileSync, writeFileSync } from "node:fs";

function replaceOnce(path, from, to) {
  const text = readFileSync(path, "utf-8").replaceAll("\r\n", "\n");
  const count = text.split(from).length - 1;
  if (count !== 1) {
    throw new Error(`${path}: 바꿀 자리를 ${count}번 찾았다(한 번이어야 한다): ${from}`);
  }
  writeFileSync(path, text.replace(from, to));
  console.log(`RI_PROBE patched ${path}`);
}

const [mode] = process.argv.slice(2);
if (mode === "standalone") {
  replaceOnce(
    "next.config.ts",
    "  compress: false,\n",
    '  compress: false,\n  output: "standalone",\n  outputFileTracingRoot: join(process.cwd(), "..", ".."),\n',
  );
  replaceOnce(
    "next.config.ts",
    'import type { NextConfig } from "next";\n',
    'import type { NextConfig } from "next";\nimport { join } from "node:path";\n',
  );
} else {
  throw new Error("사용: node patch-admin.mjs standalone");
}
