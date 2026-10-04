// web-widget 위젯 스택 프로브: 후보를 설치하면 워크스페이스의 락에 무엇이 새로 드는지 본다.
//   node .scratch/web-widget/probes/widget_stack/deps.mjs <작업 루트>/<후보>
// 견주는 기준은 저장소의 web/pnpm-lock.yaml(읽기만 한다)이고, 후보의 것은 setup.mjs 의 pnpm install 이 고친 사본의 락이다.
// 내는 것
//   direct   위젯 앱(과 react-pkg 의 packages/widget-ui)이 직접 드는 패키지의 지정과 풀린 판
//   added    락의 packages 절에 새로 든 항목(이름@판). removed 는 빠진 항목(다른 판으로 바뀐 것 포함)
//   vsAdmin  관리 화면(apps/admin)도 드는 이름인데 판이 다른 것
// 결과는 <작업 루트>/<후보>/deps.json 에도 쓴다.

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const ws = resolve(process.argv[2] ?? ".");

function lines(path) {
  return readFileSync(path, "utf-8").split(/\r?\n/);
}

/** packages: 절의 항목 키(이름@판). */
function packages(path) {
  const keys = new Set();
  let inside = false;
  for (const line of lines(path)) {
    if (/^\S/.test(line)) {
      inside = line === "packages:";
      continue;
    }
    const match = inside ? /^ {2}'?([^'\s][^']*?)'?:$/.exec(line) : null;
    if (match !== null) {
      keys.add(match[1]);
    }
  }
  return keys;
}

/** importers: 절에서 한 importer 의 직접 의존. 이름 → { specifier, version, kind } */
function importer(path, name) {
  const out = {};
  let state = "out";
  let kind = "";
  let dep = "";
  for (const line of lines(path)) {
    if (/^\S/.test(line)) {
      state = line === "importers:" ? "importers" : "out";
      continue;
    }
    if (state === "out") {
      continue;
    }
    const top = /^ {2}(\S.*):$/.exec(line);
    if (top !== null) {
      state = top[1] === name ? "mine" : "importers";
      continue;
    }
    if (state !== "mine") {
      continue;
    }
    const section = /^ {4}(\w+):$/.exec(line);
    if (section !== null) {
      kind = section[1];
      continue;
    }
    const entry = /^ {6}'?([^']+?)'?:$/.exec(line);
    if (entry !== null) {
      dep = entry[1];
      out[dep] = { kind };
      continue;
    }
    const field = /^ {8}(specifier|version): (.+)$/.exec(line);
    if (field !== null && dep !== "") {
      out[dep][field[1]] = field[2].replace(/\(.*$/, "");
    }
  }
  return out;
}

const base = join(REPO, "web", "pnpm-lock.yaml");
const mine = join(ws, "web", "pnpm-lock.yaml");
const before = packages(base);
const after = packages(mine);
const admin = importer(mine, "apps/admin");
const direct = {
  "apps/widget": importer(mine, "apps/widget"),
  "packages/widget-ui": importer(mine, "packages/widget-ui"),
};
const vsAdmin = Object.entries(direct["apps/widget"])
  .filter(([name, dep]) => admin[name] !== undefined && admin[name].version !== dep.version)
  .map(([name, dep]) => ({ name, widget: dep.version, admin: admin[name].version }));

const result = {
  candidate: relative(dirname(ws), ws),
  base: relative(REPO, base),
  direct,
  added: [...after].filter((key) => !before.has(key)).sort(),
  removed: [...before].filter((key) => !after.has(key)).sort(),
  vsAdmin,
};
writeFileSync(join(ws, "deps.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
