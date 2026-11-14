// 이미지 안의 관리 화면 사본을 고친다(저장소의 파일은 그대로다). 측정용 갈래 둘이 쓴다.
//
// 사용: node patch-admin.mjs <exception|standalone>   (작업 폴더가 apps/admin 의 사본)
//
// - exception: 상류 판정(tools/loopback.ts 의 upstreamProblem)이 환경 변수 RI_PROBE_UPSTREAM_HOST 가 든 호스트 하나를
//   더 받게 한다. 루프백 규칙의 예외를 티켓이 어떻게 짓든, 호스트 이름인 상류가 빌드와 중계를 지나는지 보려는 것이다.
// - standalone: next.config.ts 에 output: "standalone" 과 추적의 뿌리(web/)를 더한다. 크기와 HOSTNAME 을 보려는 것이다.
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
if (mode === "exception") {
  replaceOnce(
    "tools/loopback.ts",
    "  if (host === UPSTREAM_HOST) {\n    return null;\n  }",
    '  if (host === UPSTREAM_HOST || host === process.env["RI_PROBE_UPSTREAM_HOST"]) {\n    return null;\n  }',
  );
} else if (mode === "standalone") {
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
  throw new Error("사용: node patch-admin.mjs <exception|standalone>");
}
