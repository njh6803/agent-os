// 이미지 안에서 지어 둔 산출물과 깔린 패키지를 들여다보고 JSON 한 줄로 찍는다. 프로브(run.py)의 build 섹션이
// docker run 으로 부른다. 작업 폴더는 위젯 앱 폴더다.
//
// 사용
//   node /probe/inspect.mjs manifest            지어 둔 routes-manifest 원본에서 frame-ancestors 가 든 응답 머리의 자리와,
//                                               값 파일에 걸린 응답 머리 규칙과, .next 아래에서 frame-ancestors 라는 글이 든
//                                               파일의 목록과, BUILD_ID 를 낸다
//   node /probe/inspect.mjs resolvable <이름>...  앱 폴더에서 위로 올라가며 그 패키지가 깔려 있는지와 판을 낸다(없으면 null)

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const APP = process.cwd();
const NEXT = join(APP, ".next");
const NEEDLE = "frame-ancestors";
const [command, ...names] = process.argv.slice(2);

function files(dir) {
  const found = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...files(path));
    } else if (entry.isFile()) {
      found.push(path);
    }
  }
  return found;
}

if (command === "manifest") {
  const manifest = JSON.parse(readFileSync(join(NEXT, "routes-manifest.build.json"), "utf-8"));
  const slots = [];
  const valueFileRules = [];
  for (const rule of manifest.headers ?? []) {
    for (const header of rule.headers ?? []) {
      if (String(header.value).startsWith(NEEDLE)) {
        slots.push({ source: rule.source, key: header.key, value: header.value });
      }
    }
    if (String(rule.source).includes("runtime.json")) {
      valueFileRules.push({ source: rule.source, headers: rule.headers });
    }
  }
  const holding = files(NEXT)
    .filter((path) => statSync(path).size < 32 * 2 ** 20 && readFileSync(path).includes(NEEDLE))
    .map((path) => relative(NEXT, path))
    .sort();
  console.log(
    JSON.stringify({
      slots,
      valueFileRules,
      holding,
      headerRules: (manifest.headers ?? []).length,
      buildId: readFileSync(join(NEXT, "BUILD_ID"), "utf-8").trim(),
    }),
  );
} else if (command === "resolvable") {
  // 패키지의 package.json 을 require 로 풀지 않는다. exports 가 package.json 을 내보내지 않는 패키지
  // (@tailwindcss/vite)는 깔려 있어도 ERR_PACKAGE_PATH_NOT_EXPORTED 로 실패해, 없는 것과 가르지 못한다. 그래서 node 가
  // 패키지를 찾는 순서대로 앱 폴더에서 위로 올라가며 node_modules/<이름>/package.json 파일이 있는지를 본다.
  const found = {};
  for (const name of names) {
    found[name] = null;
    for (let dir = APP; ; dir = dirname(dir)) {
      const manifest = join(dir, "node_modules", name, "package.json");
      if (existsSync(manifest)) {
        found[name] = JSON.parse(readFileSync(manifest, "utf-8")).version;
        break;
      }
      if (dirname(dir) === dir) {
        break;
      }
    }
  }
  console.log(JSON.stringify(found));
} else {
  console.error("사용: node /probe/inspect.mjs manifest | resolvable <이름>...");
  process.exit(2);
}
