// 크기 프로브(B4). 제한을 건 컴포넌트를 묶어 지금의 글자 문단(baseline)보다 얼마나 느는지 잰다.
//
// 돌리기: node probe/size.mjs
// 산출물: out/size/esbuild/<이름>.js, out/size/vite/<이름>/app.js, out/size/summary.json, 표준 출력의 마지막 줄(JSON)
//
// 두 가지로 잰다
// 1. esbuild 0.28.2: React(react, react-dom, react/jsx-runtime)를 밖에 두고 최소화한 ESM. 라이브러리의 몫만 본다.
// 2. Vite 8.3.1 라이브러리 빌드(IIFE): element 번들처럼 React 를 품고 한 파일로 묶는다(web/apps/widget/tools/element.ts
//    와 같은 형식). 증분은 "후보 앱 - 기준선 앱"이다. 실제 element 번들에 얼마나 느는지에 더 가깝다.
// 크기는 파일 바이트와 gzip(level 9) 바이트다(.scratch/web-widget/probes/widget_stack/measure.mjs 와 같은 재는 법).
//
// 측정이 아닌 회차(.claude/rules/probes.md)
// - esbuild 회차마다 metafile 로 "기대한 패키지가 실제로 묶였다"와 "react 가 묶이지 않았다"를 단언한다.
// - Vite 회차마다 번들에 React 가 들었는지(기준선이 React 한 벌만큼 큰지)를 단언한다.
// - 하나라도 어긋나면 그 회차를 notMeasured 로 세고 종료 코드 1.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { build as esbuild } from "esbuild";
import { build as viteBuild } from "vite";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const ENTRIES = join(ROOT, "probe", "size-entries");
const OUT = join(ROOT, "out", "size");

const TARGETS = [
  { name: "baseline", file: "baseline.tsx", expect: [], vite: true },
  { name: "react-markdown", file: "react-markdown.tsx", expect: ["react-markdown", "remark-gfm", "micromark"], vite: true },
  { name: "markdown-to-jsx", file: "markdown-to-jsx.tsx", expect: ["markdown-to-jsx"], vite: true },
  { name: "react-markdown-no-gfm", file: "react-markdown-no-gfm.tsx", expect: ["react-markdown", "micromark"], vite: true },
  { name: "marked-lexer", file: "marked-lexer.ts", expect: ["marked"], vite: false },
];

const sizeOf = (bytes) => ({ raw: bytes.length, gzip: gzipSync(bytes, { level: 9 }).length });

/** 경로에서 패키지 이름을 낸다. node_modules 밖(프로브의 자기 코드)은 "(own)" 이다. */
function packageOf(path) {
  const at = path.lastIndexOf("node_modules/");
  if (at < 0) return "(own)";
  const parts = path.slice(at + "node_modules/".length).split("/");
  return parts[0].startsWith("@") ? `${parts[0]}/${parts[1]}` : parts[0];
}

async function measureEsbuild(target) {
  const outfile = join(OUT, "esbuild", `${target.name}.js`);
  const result = await esbuild({
    entryPoints: [join(ENTRIES, target.file)],
    outfile,
    bundle: true,
    minify: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    jsx: "automatic",
    external: ["react", "react-dom", "react/jsx-runtime"],
    define: { "process.env.NODE_ENV": '"production"' },
    metafile: true,
    logLevel: "warning",
  });
  const output = Object.values(result.metafile.outputs)[0];
  const byPackage = {};
  for (const [path, info] of Object.entries(output.inputs)) {
    const name = packageOf(path.replaceAll("\\", "/"));
    byPackage[name] = (byPackage[name] ?? 0) + info.bytesInOutput;
  }
  const packages = Object.keys(byPackage);
  const problems = [];
  for (const wanted of target.expect) {
    if (!packages.some((p) => p === wanted || p.startsWith(`${wanted}-`))) problems.push(`${wanted} 가 묶이지 않았다`);
  }
  for (const banned of ["react", "react-dom", "scheduler"]) {
    if (packages.includes(banned)) problems.push(`${banned} 가 묶였다(밖에 두어야 한다)`);
  }
  if (!output.imports.some((i) => i.external === true) && target.name !== "marked-lexer") {
    problems.push("밖에 둔 import 가 하나도 없다(react 를 쓰지 않는 번들이다)");
  }
  const top = Object.entries(byPackage).sort((a, b) => b[1] - a[1]);
  return {
    ...sizeOf(readFileSync(outfile)),
    packages: packages.filter((p) => p !== "(own)").length,
    topPackages: top.slice(0, 8).map(([name, bytes]) => ({ name, bytes })),
    problems,
  };
}

async function measureVite(target) {
  const outDir = join(OUT, "vite", target.name);
  const entry = join(OUT, "vite-entries", `app-${target.name}.tsx`);
  mkdirSync(dirname(entry), { recursive: true });
  writeFileSync(
    entry,
    [
      "// size.mjs 가 쓴 파일이다. element 번들처럼 React 를 품고 한 파일(IIFE)로 묶이는 입구다.",
      'import { createRoot } from "react-dom/client";',
      `import { Answer } from ${JSON.stringify(`../../../probe/size-entries/${target.file.replace(/\.tsx$/, "")}`)};`,
      "",
      "export function mount(host: Element, text: string): void {",
      "  createRoot(host).render(<Answer text={text} />);",
      "}",
      "",
    ].join("\n"),
  );
  await viteBuild({
    configFile: false,
    root: ROOT,
    logLevel: "warn",
    define: { "process.env.NODE_ENV": JSON.stringify("production") },
    build: {
      outDir,
      emptyOutDir: true,
      copyPublicDir: false,
      lib: { entry, formats: ["iife"], name: "MdProbe", fileName: () => "app.js" },
    },
  });
  const bytes = readFileSync(join(outDir, "app.js"));
  const text = bytes.toString("utf8");
  const problems = [];
  // React 한 벌이 든 번들은 최소화해도 150KB 를 넘는다. 넘지 않으면 React 가 밖으로 빠졌거나 빌드가 비었다.
  if (bytes.length < 150_000) problems.push(`React 가 든 번들치고 작다: ${bytes.length}`);
  if (!text.includes("createRoot") && !text.includes("react.dev/errors")) problems.push("React 의 표지가 없다");
  if (/\bprocess\.env\b/.test(text)) problems.push("process.env 가 남았다");
  return { ...sizeOf(bytes), problems };
}

async function main() {
  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(join(OUT, "esbuild"), { recursive: true });
  const rows = [];
  const notMeasured = [];
  for (const target of TARGETS) {
    const row = { name: target.name, esbuild: await measureEsbuild(target) };
    if (row.esbuild.problems.length > 0) notMeasured.push({ name: target.name, tool: "esbuild", problems: row.esbuild.problems });
    if (target.vite) {
      row.vite = await measureVite(target);
      if (row.vite.problems.length > 0) notMeasured.push({ name: target.name, tool: "vite", problems: row.vite.problems });
    }
    rows.push(row);
  }
  const base = rows.find((r) => r.name === "baseline");
  const table = rows.map((r) => ({
    name: r.name,
    esbuildExternalReact: { raw: r.esbuild.raw, gzip: r.esbuild.gzip },
    esbuildDelta: { raw: r.esbuild.raw - base.esbuild.raw, gzip: r.esbuild.gzip - base.esbuild.gzip },
    packagesBundled: r.esbuild.packages,
    ...(r.vite === undefined
      ? {}
      : {
          viteIifeWithReact: { raw: r.vite.raw, gzip: r.vite.gzip },
          viteDelta: { raw: r.vite.raw - base.vite.raw, gzip: r.vite.gzip - base.vite.gzip },
        }),
  }));
  writeFileSync(join(OUT, "summary.json"), JSON.stringify({ notMeasured, table, rows }, null, 2));
  console.log(JSON.stringify({ probe: "size", notMeasured: notMeasured.length, table }));
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
}

await main();
