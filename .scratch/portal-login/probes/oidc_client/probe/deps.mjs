// 의존성 프로브. 설치된 node_modules 를 따라가 후보마다 판, 라이선스, 전이 의존성까지의 패키지 수, 설치 크기를 센다.
//
// 돌리기: node probe/deps.mjs
// 산출물: out/deps/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 세는 법
// - 뿌리 패키지의 `dependencies` 와 `optionalDependencies` 를 pnpm 의 배치(패키지의 실제 자리 옆 node_modules)에서
//   찾아 끝까지 따라간다. `peerDependencies` 와 `devDependencies` 는 세지 않는다.
// - "패키지 수"는 뿌리를 넣은 고유한 `이름@판` 의 수다.
// - "설치 크기"는 패키지 폴더마다 그 안의 파일 크기(`stat` 의 size)를 더한 것이다. 안쪽 `node_modules` 는 들어가지
//   않는다(pnpm 은 의존성을 옆에 둔다). 디스크의 할당 단위나 pnpm 의 하드 링크로 실제 쓰는 자리는 이 수와 다를 수 있다.
// - 후보 다(직접 구현)와 가짜 서버 ㄱ(직접 만든 것)은 뿌리가 없어 0 이다. 세는 길이 같다는 것을 보이려고 줄로 둔다.
//
// 측정이 아닌 회차: 의존성 하나라도 디스크에서 찾지 못하면 그 후보는 센 것이 아니다. 종료 코드 1.
import { existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "deps");

const CANDIDATES = [
  { name: "가 openid-client", roots: ["openid-client"] },
  { name: "나 oauth4webapi + jose", roots: ["oauth4webapi", "jose"] },
  { name: "나 가운데 oauth4webapi 만", roots: ["oauth4webapi"] },
  { name: "나 가운데 jose 만", roots: ["jose"] },
  { name: "다 직접 구현", roots: [] },
  { name: "ㄱ 직접 만든 가짜 서버", roots: [] },
  { name: "ㄴ oidc-provider", roots: ["oidc-provider"] },
  { name: "ㄴ 의 타입 선언 @types/oidc-provider", roots: ["@types/oidc-provider"] },
  { name: "ㄴ oidc-provider + @types/oidc-provider", roots: ["oidc-provider", "@types/oidc-provider"] },
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

function sizeOf(dir) {
  let bytes = 0;
  let files = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules") continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      const inner = sizeOf(path);
      bytes += inner.bytes;
      files += inner.files;
    } else if (entry.isFile()) {
      bytes += statSync(path).size;
      files += 1;
    }
  }
  return { bytes, files };
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
    const direct = Object.keys({ ...manifest.dependencies, ...manifest.optionalDependencies });
    seen.set(key, {
      name: manifest.name,
      version: manifest.version,
      license: typeof manifest.license === "string" ? manifest.license : JSON.stringify(manifest.license ?? null),
      root: item.depth === 0,
      engines: manifest.engines ?? null,
      type: manifest.type ?? "commonjs",
      types: manifest.types ?? manifest.typings ?? (manifest.exports?.["."]?.types ?? null),
      hasInstallScript: ["preinstall", "install", "postinstall"].some((s) => manifest.scripts?.[s] !== undefined),
      direct,
      ...sizeOf(item.dir),
    });
    for (const dep of direct) queue.push({ name: dep, dir: resolvePackage(item.dir, dep), depth: item.depth + 1 });
  }
  return { packages: [...seen.values()], missing };
}

function main() {
  mkdirSync(OUT, { recursive: true });
  const rows = [];
  const notMeasured = [];
  for (const candidate of CANDIDATES) {
    const { packages, missing } = walk(candidate.roots);
    if (missing.length > 0) notMeasured.push({ name: candidate.name, missing });
    const licenses = {};
    for (const p of packages) licenses[p.license] = (licenses[p.license] ?? 0) + 1;
    rows.push({
      name: candidate.name,
      roots: packages
        .filter((p) => p.root)
        .map((p) => ({ name: p.name, version: p.version, license: p.license, engines: p.engines, type: p.type, types: p.types, direct: p.direct })),
      packages: packages.length,
      transitive: packages.filter((p) => !p.root).length,
      bytes: packages.reduce((sum, p) => sum + p.bytes, 0),
      files: packages.reduce((sum, p) => sum + p.files, 0),
      licenses,
      withInstallScripts: packages.filter((p) => p.hasInstallScript).map((p) => `${p.name}@${p.version}`),
      all: packages.map((p) => `${p.name}@${p.version} (${p.license}, ${String(p.bytes)}B)`).sort(),
    });
  }
  writeFileSync(join(OUT, "summary.json"), JSON.stringify({ notMeasured, rows }, null, 2));
  console.log(JSON.stringify({ probe: "deps", notMeasured, rows }));
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
}

main();
