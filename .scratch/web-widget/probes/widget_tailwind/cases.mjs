// web-widget 위젯 스타일 프로브: 배치를 바꿨을 때 판정자(ESLint), 타입 검사(tsc), Vitest, element 번들 크기가 어떻게 되는지
// 사례로 잰다.
//   node .scratch/web-widget/probes/widget_tailwind/cases.mjs <작업 루트>/react
// setup.mjs 가 지은(measure.mjs 가 빌드까지 마친) 트리를 받는다. 사례마다 파일을 잠깐 바꾸고 돌린 뒤 원래대로 돌린다.
// 실제 모양이 판정을 지나는지는 verify(widget_stack/verify.mjs)가 본다.
//
// 사례(lint 는 바꾼 파일을 ESLint 로, tsc 는 apps/widget 을 tsc --noEmit 으로, build 는 element 번들을 따로 빌드해 크기를)
//   shape                    바꾸지 않은 모양. 아이콘 서브패스 파일과 선언 파일을 린트하고 tsc 를 친다
//   layout-imports-css       app/layout.tsx 가 전역 CSS(styles/widget.css)를 import 하면
//   icons-root-import        아이콘을 lucide-react 루트에서 다시 내보내면(atoms/icons.ts)
//   organism-root-import     organism 이 lucide-react 루트를 import 하면
//   icons-subpath-mjs        서브패스에 확장자(.mjs)를 붙이면
//   icons-dist-barrel        서브패스가 배포 폴더의 묶음 파일(dist/esm/lucide-react.mjs)이면
//   dts-import-type          lucide-icons.d.ts 가 루트를 `import type` 문으로 읽으면
//   no-lucide-dts            lucide-icons.d.ts 가 없으면
//   no-css-dts               css-inline.d.ts 가 없으면
//   vite-client-types        css-inline.d.ts 대신 tsconfig 의 types 에 vite/client 를 두면
//   no-icons                 아이콘을 아무것도 그리지 않는 함수로 바꾸면(번들 크기의 기준)
// Vitest: apps/widget 에 잠깐 둔 테스트가 `?inline` 과 일반 CSS import 로 받은 것과 shadowSheets 의 결과를 파일로 남긴다.
// 기본 설정과, widget 프로젝트에 `css: true` 를 잠깐 넣은 설정 둘로 돈다.
// 결과는 <작업 루트>/react/cases.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");
const fromWeb = createRequire(join(web, "package.json"));
const fromWidget = createRequire(join(widget, "package.json"));
const { ESLint } = fromWeb("eslint");
const tsc = join(dirname(fromWeb.resolve("typescript/package.json")), "bin", "tsc");
const vite = join(dirname(fromWidget.resolve("vite/package.json")), "bin", "vite.js");
const vitest = join(dirname(fromWeb.resolve("vitest/package.json")), "vitest.mjs");
const baseline = JSON.parse(readFileSync(join(ws, "baseline.json"), "utf-8"));

const ICONS = "apps/widget/components/atoms/icons.ts";
const LUCIDE_DTS = "apps/widget/lucide-icons.d.ts";
const CSS_DTS = "apps/widget/css-inline.d.ts";
const TSCONFIG = "apps/widget/tsconfig.json";
const LAYOUT = "apps/widget/app/layout.tsx";
const read = (path) => readFileSync(join(web, path), "utf-8");

const CASES = [
  { name: "shape", files: {}, lint: [ICONS, LUCIDE_DTS, CSS_DTS], tsc: true },
  {
    name: "layout-imports-css",
    files: { [LAYOUT]: `import "../styles/widget.css";\n${read(LAYOUT)}` },
    lint: [LAYOUT],
  },
  {
    name: "icons-root-import",
    files: { [ICONS]: 'export { Send as SendIcon, X as CloseIcon } from "lucide-react";\n' },
    lint: [ICONS],
    tsc: true,
    build: true,
  },
  {
    name: "organism-root-import",
    files: {
      "apps/widget/components/organisms/Probe.ts":
        'import { Send } from "lucide-react";\n\nexport const 아이콘 = Send;\n',
    },
    lint: ["apps/widget/components/organisms/Probe.ts"],
  },
  {
    name: "icons-subpath-mjs",
    files: { [ICONS]: read(ICONS).replaceAll(/icons\/(\w+)"/g, 'icons/$1.mjs"') },
    lint: [ICONS],
    tsc: true,
    build: true,
  },
  {
    name: "icons-dist-barrel",
    files: {
      [ICONS]:
        'export { Send as SendIcon, X as CloseIcon } from "lucide-react/dist/esm/lucide-react.mjs";\n',
    },
    lint: [ICONS],
    tsc: true,
    build: true,
  },
  {
    name: "dts-import-type",
    files: {
      [LUCIDE_DTS]:
        'declare module "lucide-react/dist/esm/icons/*" {\n  import type { LucideIcon } from "lucide-react";\n  const icon: LucideIcon;\n  export default icon;\n}\n',
    },
    lint: [LUCIDE_DTS],
    tsc: true,
  },
  { name: "no-lucide-dts", files: { [LUCIDE_DTS]: null }, tsc: true },
  { name: "no-css-dts", files: { [CSS_DTS]: null }, tsc: true },
  {
    name: "vite-client-types",
    files: {
      [CSS_DTS]: null,
      [TSCONFIG]: read(TSCONFIG).replace('"types": ["node"]', '"types": ["node", "vite/client"]'),
    },
    tsc: true,
  },
  {
    name: "no-icons",
    files: {
      [ICONS]:
        "export function CloseIcon(): null {\n  return null;\n}\n\nexport function SendIcon(): null {\n  return null;\n}\n",
    },
    build: true,
  },
];

const clean = (text) => text.replace(/\u001b\[[\d;]*m/g, "");
const size = (bytes) => ({ min: bytes.length, gzip: gzipSync(bytes, { level: 9 }).length });

/** 파일을 바꾸고 fn 을 돌린 뒤 원래대로 돌린다. null 은 지운다. */
async function withFiles(files, fn) {
  const saved = Object.keys(files).map((path) => {
    const full = join(web, path);
    return [full, existsSync(full) ? readFileSync(full) : null];
  });
  try {
    for (const [path, text] of Object.entries(files)) {
      const full = join(web, path);
      if (text === null) {
        rmSync(full, { force: true });
      } else {
        writeFileSync(full, text);
      }
    }
    return await fn();
  } finally {
    for (const [full, bytes] of saved) {
      if (bytes === null) {
        rmSync(full, { force: true });
      } else {
        writeFileSync(full, bytes);
      }
    }
  }
}

const result = { candidate: relative(dirname(ws), ws), cases: [], vitest: {}, sizes: {} };

for (const spec of CASES) {
  const entry = { name: spec.name };
  await withFiles(spec.files, async () => {
    if (spec.lint !== undefined) {
      // 사례마다 판정자를 새로 세운다. 프로젝트 서비스가 앞 사례의 파일을 들고 있지 않게 한다.
      const reports = await new ESLint({ cwd: web }).lintFiles(
        spec.lint.map((path) => join(web, path)),
      );
      entry.lint = reports.flatMap((report) =>
        report.messages.map((message) => ({
          file: relative(web, report.filePath).split(sep).join("/"),
          rule: message.ruleId,
          message: message.message.split("\n")[0].slice(0, 160),
        })),
      );
    }
    if (spec.tsc) {
      const proc = spawnSync(process.execPath, [tsc, "--noEmit", "-p", "apps/widget"], {
        cwd: web,
        encoding: "utf-8",
      });
      entry.tsc = {
        status: proc.status,
        errors: clean(`${proc.stdout}${proc.stderr}`)
          .split(/\r?\n/)
          .filter((line) => /error TS\d+/.test(line))
          .map((line) =>
            line.replace(/'[A-Z]:[^']*node_modules[^']*'/g, "'<node_modules>'").slice(0, 220),
          ),
      };
    }
    if (spec.build) {
      const outDir = join(widget, "dist", `case-${spec.name}`);
      const proc = spawnSync(
        process.execPath,
        [vite, "build", "--mode", "element", "--outDir", outDir],
        { cwd: widget, encoding: "utf-8" },
      );
      entry.build = { status: proc.status };
      if (proc.status === 0) {
        const own = size(readFileSync(join(outDir, "widget.js")));
        result.sizes[spec.name] = {
          ...own,
          vsBaseline: { min: own.min - baseline.min, gzip: own.gzip - baseline.gzip },
        };
      } else {
        entry.build.tail = clean(`${proc.stdout}${proc.stderr}`).split(/\r?\n/).slice(-8);
      }
      rmSync(outDir, { recursive: true, force: true });
    }
  });
  result.cases.push(entry);
}

// 모양 그대로의 element 번들(measure.mjs 의 것)을 같은 표에 둔다.
const shaped = join(widget, "dist", "element", "widget.js");
if (existsSync(shaped)) {
  const own = size(readFileSync(shaped));
  result.sizes.shape = {
    ...own,
    vsBaseline: { min: own.min - baseline.min, gzip: own.gzip - baseline.gzip },
  };
}
result.sizes.baseline = baseline;

// ---------- Vitest 가 CSS import 를 어떻게 다루는가 ----------
const PROBE_TEST = "apps/widget/css-probe.test.ts";
const PROBE_SOURCE = `import { writeFileSync } from "node:fs";
import { expect, test } from "vitest";
import { shadowSheets } from "./lib/shadow-styles";
import "./styles/widget.css";
import inline from "./styles/widget.css?inline";

test("CSS import 가 무엇을 주는가", () => {
  const out: Record<string, unknown> = {
    inlineType: typeof inline,
    inlineLength: inline.length,
    inlineHead: inline.slice(0, 60),
    styleElements: document.querySelectorAll("style").length,
    hasCSSLayerBlockRule: "CSSLayerBlockRule" in globalThis,
  };
  try {
    const sheets = shadowSheets(inline);
    out.sheets = sheets.map((sheet) => sheet.cssRules.length);
  } catch (error) {
    out.sheetsError = String(error);
  }
  writeFileSync(process.env.CSS_PROBE_OUT ?? "", JSON.stringify(out));
  expect(out.inlineType).toBe("string");
});
`;
// Vitest 5.0.2 의 CLI 에는 --css 가 없다(Unknown option). CSS 처리는 widget 프로젝트 설정에 `css: true` 를 잠깐 넣어 켠다.
const VITEST_CONFIG = "vitest.config.ts";
const WIDGET_NAME = '          name: "widget",\n';
if (!read(VITEST_CONFIG).includes(WIDGET_NAME)) {
  throw new Error("vitest.config.ts 에 widget 프로젝트가 없다(setup.mjs 가 넣는다)");
}
for (const [label, config] of [
  ["default", {}],
  [
    "css-enabled",
    {
      [VITEST_CONFIG]: read(VITEST_CONFIG).replace(
        WIDGET_NAME,
        `${WIDGET_NAME}          css: true,\n`,
      ),
    },
  ],
]) {
  const out = join(ws, `css-probe-${label}.json`);
  rmSync(out, { force: true });
  await withFiles({ [PROBE_TEST]: PROBE_SOURCE, ...config }, () => {
    const proc = spawnSync(process.execPath, [vitest, "run", "--project", "widget", PROBE_TEST], {
      cwd: web,
      encoding: "utf-8",
      env: { ...process.env, CSS_PROBE_OUT: out },
    });
    result.vitest[label] = {
      status: proc.status,
      seen: existsSync(out) ? JSON.parse(readFileSync(out, "utf-8")) : null,
      tail: clean(`${proc.stdout}${proc.stderr}`)
        .split(/\r?\n/)
        .filter((line) => line.trim() !== "")
        .slice(-6),
    };
  });
  rmSync(out, { force: true });
}

writeFileSync(join(ws, "cases.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
