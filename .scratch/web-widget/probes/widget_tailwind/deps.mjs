// web-widget 위젯 스타일 프로브: Tailwind 와 lucide-react 를 들이면 무엇이 새로 드는지, 네이티브 바이너리가 서는지 본다.
//   node .scratch/web-widget/probes/widget_tailwind/deps.mjs <작업 루트>/react [--linux]
// 견주는 기준은 setup.mjs 가 덮어쓰기 전에 뜬 락(pnpm-lock.before.yaml, widget_stack 의 react 후보)이다.
// 내는 것
//   direct     apps/widget 의 직접 의존 지정과 풀린 판
//   added      락의 packages 절에 새로 든 항목. 그 가운데 os·cpu·libc 가 붙은 것(플랫폼별 네이티브 패키지)을 따로
//   removed    빠진 항목(같은 이름의 다른 판·피어 접미가 바뀐 것 포함)
//   workspace  pnpm-workspace.yaml 이 설치로 어떻게 바뀌었는지(pnpm 11 의 minimumReleaseAge)
//   windows    이 트리에서 @tailwindcss/oxide 와 lightningcss 를 실제로 불러 돌린 결과와 불러온 바이너리 패키지
//   linux      --linux 일 때만. <작업 루트>/linux-fetch 에 같은 Tailwind 판을 `pnpm install --os linux --cpu x64
//              --libc glibc` 로 받고(npm 레지스트리에 닿는다), WSL 의 Ubuntu 에서 .node 파일마다 ldd 와 요구하는
//              GLIBC 판의 최댓값(objdump -T)을 본다. 리눅스에서 node 로 불러 보지는 않는다(로컬에 리눅스 node 가 없다)
// 결과는 <작업 루트>/react/deps.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve } from "node:path";

const ws = resolve(process.argv[2] ?? ".");
const linux = process.argv.includes("--linux");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");

function lines(path) {
  return readFileSync(path, "utf-8").split(/\r?\n/);
}

/** packages: 절의 항목. 키(이름@판) → { os, cpu, libc } */
function packages(path) {
  const out = new Map();
  let inside = false;
  let key = null;
  for (const line of lines(path)) {
    if (/^\S/.test(line)) {
      inside = line === "packages:";
      key = null;
      continue;
    }
    if (!inside) {
      continue;
    }
    const entry = /^ {2}'?([^'\s][^']*?)'?:$/.exec(line);
    if (entry !== null) {
      key = entry[1];
      out.set(key, {});
      continue;
    }
    const field = /^ {4}(os|cpu|libc): \[(.*)\]$/.exec(line);
    if (field !== null && key !== null) {
      out.get(key)[field[1]] = field[2];
    }
  }
  return out;
}

/** importers: 절에서 한 importer 의 직접 의존. 이름 → { kind, specifier, version } */
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

const before = packages(join(ws, "pnpm-lock.before.yaml"));
const after = packages(join(web, "pnpm-lock.yaml"));
const added = [...after.keys()].filter((key) => !before.has(key)).sort();
const result = {
  candidate: relative(dirname(ws), ws),
  direct: importer(join(web, "pnpm-lock.yaml"), "apps/widget"),
  added: added.filter((key) => Object.keys(after.get(key)).length === 0),
  addedNative: added
    .filter((key) => Object.keys(after.get(key)).length > 0)
    .map((key) => ({ key, ...after.get(key) })),
  removed: [...before.keys()].filter((key) => !after.has(key)).sort(),
  workspace: {
    before: readFileSync(join(ws, "pnpm-workspace.before.yaml"), "utf-8"),
    after: readFileSync(join(web, "pnpm-workspace.yaml"), "utf-8"),
  },
};

// ---------- 윈도우: 이 트리에서 실제로 불러 돌린다 ----------
const fromWidget = createRequire(join(widget, "package.json"));
const fromNode = createRequire(
  createRequire(fromWidget.resolve("@tailwindcss/postcss")).resolve("@tailwindcss/node"),
);
const windows = { platform: `${process.platform}-${process.arch}`, node: process.version };
try {
  const oxidePath = fromNode.resolve("@tailwindcss/oxide");
  const oxide = fromNode("@tailwindcss/oxide");
  const scanner = new oxide.Scanner({
    sources: [{ base: join(widget, "components"), pattern: "**/*", negated: false }],
  });
  const candidates = scanner.scan();
  const fromOxide = createRequire(oxidePath);
  // 윈도우 x64 의 바이너리 패키지 이름. 다른 플랫폼에서 돌면 null 이다.
  const binary = `@tailwindcss/oxide-${process.platform}-${process.arch}-msvc`;
  let binaryDir = null;
  try {
    binaryDir = dirname(fromOxide.resolve(`${binary}/package.json`));
  } catch {
    binaryDir = null;
  }
  windows.oxide = {
    version: fromOxide("./package.json").version,
    binary: binaryDir !== null && existsSync(binaryDir) ? binary : null,
    candidates: candidates.length,
    sawWidgetClass: candidates.includes("bg-linear-to-r"),
  };
} catch (error) {
  windows.oxide = { error: String(error).split("\n")[0] };
}
try {
  const lightning = fromNode("lightningcss");
  const out = lightning.transform({
    filename: "probe.css",
    code: Buffer.from(".a { color: oklch(0.5 0.1 200); }"),
    minify: true,
  });
  // lightningcss 의 exports 는 ./package.json 을 내지 않는다. 풀린 파일에서 패키지 뿌리를 찾아 읽는다.
  const entry = fromNode.resolve("lightningcss");
  const root = entry.slice(0, entry.lastIndexOf("lightningcss") + "lightningcss".length);
  windows.lightningcss = {
    version: JSON.parse(readFileSync(join(root, "package.json"), "utf-8")).version,
    output: out.code.toString("utf-8"),
  };
} catch (error) {
  windows.lightningcss = { error: String(error).split("\n")[0] };
}
result.windows = windows;

// ---------- 리눅스: 바이너리를 받아 WSL 에서 링크를 본다 ----------
if (linux) {
  const fetchDir = join(dirname(ws), "linux-fetch");
  rmSync(fetchDir, { recursive: true, force: true });
  mkdirSync(fetchDir, { recursive: true });
  const tailwind = result.direct.tailwindcss?.version ?? "4.3.3";
  writeFileSync(
    join(fetchDir, "package.json"),
    `${JSON.stringify(
      {
        private: true,
        devDependencies: {
          tailwindcss: tailwind,
          "@tailwindcss/postcss": result.direct["@tailwindcss/postcss"]?.version ?? tailwind,
          "@tailwindcss/vite": result.direct["@tailwindcss/vite"]?.version ?? tailwind,
          vite: result.direct.vite?.version ?? "8.3.2",
        },
      },
      null,
      2,
    )}\n`,
  );
  const install = spawnSync("pnpm install --os linux --cpu x64 --libc glibc", {
    cwd: fetchDir,
    encoding: "utf-8",
    shell: true,
  });
  const nodeFiles = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(path);
      } else if (entry.name.endsWith(".node")) {
        nodeFiles.push(path);
      }
    }
  };
  walk(join(fetchDir, "node_modules", ".pnpm"));
  const toWsl = (path) =>
    path.replace(/^([A-Za-z]):/, (_, drive) => `/mnt/${drive.toLowerCase()}`).replaceAll("\\", "/");
  const wsl = (script) =>
    spawnSync("wsl", ["-d", "Ubuntu", "--", "sh", "-c", script], { encoding: "utf-8" });
  result.linux = {
    install: {
      status: install.status,
      tail: `${install.stdout}${install.stderr}`.split(/\r?\n/).filter(Boolean).slice(-4),
    },
    host: wsl("ldd --version | head -1; grep PRETTY /etc/os-release").stdout.trim(),
    binaries: nodeFiles.map((path) => {
      const unix = toWsl(path);
      const ldd = wsl(`ldd '${unix}'`);
      const glibc = wsl(`objdump -T '${unix}' | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1`);
      return {
        file: relative(fetchDir, path)
          .replaceAll("\\", "/")
          .replace(/^node_modules\/\.pnpm\//, ""),
        lddStatus: ldd.status,
        notFound: ldd.stdout.split("\n").filter((line) => line.includes("not found")),
        maxGlibc: glibc.stdout.trim(),
      };
    }),
  };
  rmSync(fetchDir, { recursive: true, force: true });
}

writeFileSync(join(ws, "deps.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
