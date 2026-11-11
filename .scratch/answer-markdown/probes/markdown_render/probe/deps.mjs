// 의존성 프로브(B1). 설치된 node_modules 를 따라가 후보마다 판, 라이선스, peerDependencies, 직접·전이 의존성 수를 센다.
//
// 돌리기: node probe/deps.mjs
// 산출물: out/deps/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 세는 법
// - 뿌리 패키지의 `dependencies` 와 `optionalDependencies` 를 pnpm 의 배치(패키지의 실제 자리 옆 node_modules)에서
//   찾아 끝까지 따라간다. `peerDependencies`(react 등)와 `devDependencies` 는 세지 않는다.
// - "전이 의존성 수"는 뿌리를 뺀 고유한 `이름@판` 의 수다. 타입만 든 패키지(`@types/*`)도 설치되므로 세고, 따로도 적는다.
// - 설치 로그(out/install.log)에서 peer 경고 줄을 찾는다.
//
// 측정이 아닌 회차: 의존성 하나라도 디스크에서 찾지 못하면 그 후보는 센 것이 아니다. 종료 코드 1.
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "deps");

const CANDIDATES = [
  { name: "react-markdown + remark-gfm", roots: ["react-markdown", "remark-gfm"] },
  { name: "react-markdown", roots: ["react-markdown"] },
  { name: "remark-gfm", roots: ["remark-gfm"] },
  { name: "markdown-to-jsx", roots: ["markdown-to-jsx"] },
  { name: "marked", roots: ["marked"] },
  // 2026-11-11 에 더했다. 명세가 정할 (가)·(나)의 플러그인 후보다. `over` 가 있는 줄은 그 조합이 이미 설치하는 것 위에
  // 새로 더하는 패키지(`addedOver`)도 낸다.
  { name: "remark-breaks", roots: ["remark-breaks"], over: "react-markdown + remark-gfm" },
  { name: "remark-cjk-friendly", roots: ["remark-cjk-friendly"], over: "react-markdown + remark-gfm" },
];

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));

/** `from`(패키지 폴더의 실제 경로)에서 `name` 을 Node 의 규칙대로 위로 올라가며 찾는다. */
function resolvePackage(from, name) {
  let dir = from;
  for (;;) {
    const candidate = join(dir, "node_modules", name, "package.json");
    if (existsSync(candidate)) return realpathSync(dirname(candidate));
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

function walk(roots) {
  const seen = new Map();
  const missing = [];
  const queue = roots.map((name) => ({ name, dir: resolvePackage(ROOT, name), depth: 0 }));
  while (queue.length > 0) {
    const item = queue.shift();
    if (item.dir === null) {
      missing.push(item.name);
      continue;
    }
    const manifest = readJson(join(item.dir, "package.json"));
    const key = `${manifest.name}@${manifest.version}`;
    if (seen.has(key)) continue;
    seen.set(key, {
      name: manifest.name,
      version: manifest.version,
      license: typeof manifest.license === "string" ? manifest.license : JSON.stringify(manifest.license ?? null),
      depth: item.depth,
      root: item.depth === 0,
      peerDependencies: manifest.peerDependencies ?? {},
      peerDependenciesMeta: manifest.peerDependenciesMeta ?? {},
      hasInstallScript: ["preinstall", "install", "postinstall"].some((s) => manifest.scripts?.[s] !== undefined),
      direct: Object.keys({ ...manifest.dependencies, ...manifest.optionalDependencies }),
    });
    for (const dep of Object.keys({ ...manifest.dependencies, ...manifest.optionalDependencies })) {
      queue.push({ name: dep, dir: resolvePackage(item.dir, dep), depth: item.depth + 1 });
    }
  }
  return { packages: [...seen.values()], missing };
}

function main() {
  mkdirSync(OUT, { recursive: true });
  const installLog = existsSync(join(ROOT, "out", "install.log")) ? readFileSync(join(ROOT, "out", "install.log"), "utf8") : null;
  const firstLog = existsSync(join(ROOT, "out", "install-first.log")) ? readFileSync(join(ROOT, "out", "install-first.log"), "utf8") : null;
  const peerLines = (log) => (log === null ? null : log.split(/\r?\n/).filter((line) => /peer|WARN/i.test(line)));

  const rows = [];
  const notMeasured = [];
  for (const candidate of CANDIDATES) {
    const { packages, missing } = walk(candidate.roots);
    if (missing.length > 0) notMeasured.push({ name: candidate.name, missing });
    const roots = packages.filter((p) => p.root);
    const rest = packages.filter((p) => !p.root);
    const licenses = {};
    for (const p of packages) licenses[p.license] = (licenses[p.license] ?? 0) + 1;
    rows.push({
      name: candidate.name,
      roots: roots.map((p) => ({
        name: p.name,
        version: p.version,
        license: p.license,
        peerDependencies: p.peerDependencies,
        peerDependenciesMeta: p.peerDependenciesMeta,
        directDependencies: p.direct.length,
      })),
      directDependencies: new Set(roots.flatMap((p) => p.direct)).size,
      transitivePackages: rest.length,
      transitiveTypesOnly: rest.filter((p) => p.name.startsWith("@types/")).length,
      installedPackagesIncludingRoots: packages.length,
      licenses,
      withInstallScripts: packages.filter((p) => p.hasInstallScript).map((p) => `${p.name}@${p.version}`),
      all: packages.map((p) => `${p.name}@${p.version} (${p.license})`).sort(),
    });
  }
  for (const candidate of CANDIDATES) {
    if (candidate.over === undefined) continue;
    const row = rows.find((r) => r.name === candidate.name);
    const base = rows.find((r) => r.name === candidate.over);
    if (row === undefined || base === undefined) {
      notMeasured.push({ name: candidate.name, missing: [`견줄 조합 ${candidate.over}`] });
      continue;
    }
    const already = new Set(base.all);
    row.over = candidate.over;
    row.addedOver = row.all.filter((entry) => !already.has(entry));
  }
  writeFileSync(
    join(OUT, "summary.json"),
    JSON.stringify({ notMeasured, peerLinesInInstallLog: peerLines(installLog), peerLinesInFirstInstallLog: peerLines(firstLog), rows }, null, 2),
  );
  console.log(
    JSON.stringify({
      probe: "deps",
      notMeasured: notMeasured.length,
      peerLinesInInstallLog: peerLines(installLog),
      peerLinesInFirstInstallLog: peerLines(firstLog),
      rows: rows.map(({ all, ...row }) => row),
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
}

main();
