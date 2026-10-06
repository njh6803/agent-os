// design-system Storybook 프로브: Storybook 과 패키지 빌드 도구를 들이면 락에 무엇이 새로 드는지, 네이티브가 서는지 본다.
//   node .scratch/design-system/probes/storybook/deps.mjs <작업 루트>/storybook
// 견주는 기준은 setup.mjs 가 뜬 락 넷이다. before(저장소 그대로) → ui(packages/ui 의 React·Tailwind·Vite) →
// storybook(Storybook 과 Vitest 브라우저 모드) → 지금(packages/ui 에 @tailwindcss/cli 까지). 결과는 <작업 루트>/storybook/deps.json 에도 쓴다.
// 내는 것
//   direct     뿌리와 packages/ui 의 직접 의존 지정과 풀린 판
//   steps      단계마다 packages 절에 새로 든 항목 수, 그중 os·cpu·libc 가 붙은 것(플랫폼별 네이티브 패키지), 빠진 항목,
//              이미 있던 이름에 다른 판이 든 것, 이미 있던 패키지의 snapshots 키(피어 접미)가 바뀐 것
//   versions   지금 락에서 판이 둘 이상인 이름
//   workspace  pnpm-workspace.yaml 의 바뀐 줄
//   install    설치 로그의 걸린 시간과 마지막 줄들
//   windows    이 트리에서 네이티브 바이너리(esbuild, oxc-parser, oxc-resolver, @parcel/watcher)를 실제로 불러 돌린 결과.
//              esbuild 와 @parcel/watcher 는 setup.mjs 가 빌드 스크립트를 막은(allowBuilds false) 것이다

import { existsSync, readdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const LOCKS = {
  before: join(ws, "pnpm-lock.before.yaml"),
  ui: join(ws, "pnpm-lock.ui.yaml"),
  storybook: join(ws, "pnpm-lock.storybook.yaml"),
  now: join(web, "pnpm-lock.yaml"),
};

function lines(path) {
  return readFileSync(path, "utf-8").split(/\r?\n/);
}

/** 최상위 절 하나의 항목. 키 → { os, cpu, libc } */
function section(path, name) {
  const out = new Map();
  let inside = false;
  let key = null;
  for (const line of lines(path)) {
    if (/^\S/.test(line)) {
      inside = line === `${name}:`;
      key = null;
      continue;
    }
    if (!inside) {
      continue;
    }
    const entry = /^ {2}'?([^'\s][^']*?)'?:( \{\})?$/.exec(line);
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
    const kindLine = /^ {4}(\w+):$/.exec(line);
    if (kindLine !== null) {
      kind = kindLine[1];
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

const nameOf = (key) => key.slice(0, key.indexOf("@", 1));
const baseOf = (key) => key.replace(/\(.*$/, "");

function step(fromPath, toPath) {
  const from = section(fromPath, "packages");
  const to = section(toPath, "packages");
  const added = [...to.keys()].filter((key) => !from.has(key)).sort();
  const fromNames = new Set([...from.keys()].map(nameOf));
  const fromSnapshots = section(fromPath, "snapshots");
  const toSnapshots = section(toPath, "snapshots");
  const fromBases = new Set([...fromSnapshots.keys()].map(baseOf));
  return {
    added: added.length,
    addedPlain: added.filter((key) => Object.keys(to.get(key)).length === 0),
    addedNative: added
      .filter((key) => Object.keys(to.get(key)).length > 0)
      .map((key) => ({ key, ...to.get(key) })),
    removed: [...from.keys()].filter((key) => !to.has(key)).sort(),
    newVersionOfExisting: added.filter((key) => fromNames.has(nameOf(key))),
    // 같은 이름·판인데 snapshots 의 키(피어 접미)가 바뀐 것. 이미 있던 패키지가 다른 피어 묶음으로 풀렸다
    reinstanced: [...toSnapshots.keys()]
      .filter((key) => !fromSnapshots.has(key) && fromBases.has(baseOf(key)))
      .map((key) => ({
        now: key,
        before: [...fromSnapshots.keys()].filter((old) => baseOf(old) === baseOf(key)),
      })),
  };
}

const now = section(LOCKS.now, "packages");
const byName = new Map();
for (const key of now.keys()) {
  byName.set(nameOf(key), [...(byName.get(nameOf(key)) ?? []), key.slice(nameOf(key).length + 1)]);
}
const snapshotsNow = section(LOCKS.now, "snapshots");

const workspaceBefore = readFileSync(join(ws, "pnpm-workspace.before.yaml"), "utf-8").split(
  /\r?\n/,
);
const workspaceNow = readFileSync(join(web, "pnpm-workspace.yaml"), "utf-8").split(/\r?\n/);

const result = {
  direct: {
    root: importer(LOCKS.now, "."),
    ui: importer(LOCKS.now, "packages/ui"),
  },
  steps: {
    ui: step(LOCKS.before, LOCKS.ui),
    storybook: step(LOCKS.ui, LOCKS.storybook),
    cli: step(LOCKS.storybook, LOCKS.now),
  },
  versions: Object.fromEntries([...byName].filter(([, versions]) => versions.length > 1)),
  storybookInstances: [...snapshotsNow.keys()].filter((key) => /^storybook@/.test(key)),
  viteInstances: [...snapshotsNow.keys()].filter((key) => /^vite@/.test(key)),
  vitestInstances: [...snapshotsNow.keys()].filter((key) => /^vitest@/.test(key)),
  reactInstances: [...snapshotsNow.keys()].filter((key) => /^react(-dom)?@/.test(key)),
  workspace: {
    added: workspaceNow.filter((line) => !workspaceBefore.includes(line) && line !== ""),
  },
  install: Object.fromEntries(
    ["install-ui.log", "install-storybook.log", "install-cli.log"].map((name) => {
      const text = existsSync(join(ws, name)) ? readFileSync(join(ws, name), "utf-8") : "";
      const kept = text
        .split(/\r?\n/)
        .filter((line) => /걸린 시간|Packages:|Done in|supply-chain|IGNORED|WARN/.test(line));
      return [name, kept];
    }),
  ),
};

// ---------- 윈도우: 이 트리에서 실제로 불러 돌린다 ----------
const packageDir = (from, name) => {
  const direct = join(from, "node_modules", name);
  return existsSync(direct) ? realpathSync(direct) : null;
};
const requireFrom = (dir) => createRequire(join(dir, "package.json"));
const windows = { platform: `${process.platform}-${process.arch}`, node: process.version };
const storybookDir = packageDir(web, "storybook");
const fromStorybook = requireFrom(storybookDir);
windows.esbuild = await attempt(() => {
  const esbuild = fromStorybook("esbuild");
  const out = esbuild.transformSync("const a: number = 1;", { loader: "ts" });
  return {
    version: esbuild.version,
    binary: binaryOf(fromStorybook.resolve("esbuild"), "esbuild", "@esbuild/"),
    output: out.code.trim(),
  };
});
windows.oxcParser = await attempt(async () => {
  const entry = fromStorybook.resolve("oxc-parser");
  const parser = await import(pathToFileURL(entry).href);
  const parsed = parser.parseSync("probe.ts", "const a: number = 1;");
  return {
    version: versionNear(entry, "oxc-parser"),
    binary: binaryOf(entry, "oxc-parser", "@oxc-parser/"),
    statements: parsed.program.body.length,
    errors: parsed.errors.length,
  };
});
windows.oxcResolver = await attempt(async () => {
  const entry = fromStorybook.resolve("oxc-resolver");
  const resolver = await import(pathToFileURL(entry).href);
  const factory = new resolver.ResolverFactory({});
  const found = factory.sync(storybookDir, "./package.json");
  return {
    version: versionNear(entry, "oxc-resolver"),
    binary: binaryOf(entry, "oxc-resolver", "@oxc-resolver/"),
    resolved: found.path !== undefined,
  };
});
const cliDir = packageDir(join(web, "packages", "ui"), "@tailwindcss/cli");
windows.parcelWatcher = await attempt(() => {
  const fromCli = requireFrom(cliDir);
  const watcher = fromCli("@parcel/watcher");
  return {
    version: versionNear(fromCli.resolve("@parcel/watcher"), "@parcel/watcher"),
    binary: binaryOf(fromCli.resolve("@parcel/watcher"), "@parcel/watcher", "@parcel/watcher-"),
    subscribe: typeof watcher.subscribe,
  };
});
result.windows = windows;

writeFileSync(join(ws, "deps.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));

async function attempt(work) {
  try {
    return await work();
  } catch (error) {
    return { error: String(error).split("\n")[0] };
  }
}

/** 패키지 입구 파일에서 위로 올라가며 그 이름의 package.json 판을 찾는다. */
function versionNear(entry, name) {
  let dir = dirname(entry);
  while (dir !== dirname(dir)) {
    const manifest = join(dir, "package.json");
    if (existsSync(manifest)) {
      const parsed = JSON.parse(readFileSync(manifest, "utf-8"));
      if (parsed.name === name) {
        return parsed.version;
      }
    }
    dir = dirname(dir);
  }
  return null;
}

/** 패키지 뿌리의 형제(.pnpm/<패키지>/node_modules 아래)로 깔린 윈도우용 플랫폼 바이너리 패키지 이름. */
function binaryOf(entry, name, prefix) {
  let root = dirname(entry);
  while (root !== dirname(root)) {
    const manifest = join(root, "package.json");
    if (existsSync(manifest) && JSON.parse(readFileSync(manifest, "utf-8")).name === name) {
      break;
    }
    root = dirname(root);
  }
  const modules = name.startsWith("@") ? dirname(dirname(root)) : dirname(root);
  const scope = prefix.slice(0, prefix.indexOf("/"));
  if (!existsSync(join(modules, scope))) {
    return [];
  }
  return readdirSync(join(modules, scope))
    .map((entryName) => `${scope}/${entryName}`)
    .filter((full) => full.startsWith(prefix) && /win32/.test(full));
}
