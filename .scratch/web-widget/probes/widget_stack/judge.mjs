// web-widget 위젯 스택 프로브: 위젯 앱의 배치가 판정자(web/eslint.config.mjs)의 층 경계를 우회 없이 지나는지 사례로 잰다.
//   node .scratch/web-widget/probes/widget_stack/judge.mjs <작업 루트>/<후보>
// setup.mjs 가 지은(설치까지 마친) 트리를 받는다. 사례 파일은 그 트리에 잠깐 쓰고 린트한 뒤 지운다. 실제 위젯 파일이 판정을
// 지나는지는 verify(pnpm -C web verify)가 보고, 여기서는 배치를 바꿨을 때를 본다.
//
// 사례
//   entry-in-app       커스텀 요소 입구(Vite 라이브러리 빌드의 entry)를 app/ 아래에 두면
//   cross-app          커스텀 요소 번들을 따로 앱(apps/widget-element)으로 내고 apps/widget 의 파일을 import 하면
//   app-imports-ui     app/ 의 파일이 packages/widget-ui(공유 컴포넌트 패키지)를 바로 import 하면(react-pkg 만)
//   pages-imports-ui   components/pages 의 파일이 packages/widget-ui 를 import 하면(react-pkg 만)
//   intrinsic-ts       React 의 JSX.IntrinsicElements 에 커스텀 요소를 더하는 보강을 .ts 에 두면(react 가 깔린 후보만)
//   intrinsic-dts      같은 보강을 .d.ts 에 두면
// 결과는 사례마다 보고된 규칙 ID 와 메시지 앞부분이다. 판정은 하지 않는다. <작업 루트>/<후보>/judge.json 에도 쓴다.

import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");
const { ESLint } = createRequire(join(web, "package.json"))("eslint");

const INTRINSIC = `import type { DetailedHTMLProps, HTMLAttributes } from "react";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "agent-os-widget": DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        readonly "api-base"?: string;
        readonly agent?: string;
        readonly token?: string;
      };
    }
  }
}
`;

const entry = ["element.tsx", "element.ts"].map((name) => join(widget, name)).find(existsSync);
const hasPackage = existsSync(join(web, "packages", "widget-ui"));
const hasReact = existsSync(join(widget, "node_modules", "@types", "react"));
// apps/widget 안에서 import 할 실제 파일. react-pkg 는 lib/ 을 패키지로 옮겼다.
const crossTarget = ["lib/styles.ts", "components/pages/WidgetPage.tsx"].find((path) =>
  existsSync(join(widget, path)),
);

const cases = [];
if (entry !== undefined) {
  const source = readFileSync(entry, "utf-8").replaceAll('from "./', 'from "../');
  cases.push({
    name: "entry-in-app",
    files: { [`apps/widget/app/widget-entry${entry.endsWith("x") ? ".tsx" : ".ts"}`]: source },
  });
}
if (crossTarget !== undefined) {
  const tsconfig = readFileSync(join(widget, "tsconfig.json"), "utf-8");
  const specifier = `../widget/${crossTarget.replace(/\.tsx?$/, "")}`;
  cases.push({
    name: "cross-app",
    files: {
      "apps/widget-element/tsconfig.json": tsconfig,
      "apps/widget-element/element.ts": `import * as 위젯 from "${specifier}";\n\nexport const 가져온_것 = 위젯;\n`,
    },
  });
}
if (hasPackage) {
  const ui =
    'import { ChatWidget } from "@agent-os/widget-ui";\n\nexport const 위젯 = ChatWidget;\n';
  cases.push({ name: "app-imports-ui", files: { "apps/widget/app/probe/page.tsx": ui } });
  cases.push({ name: "pages-imports-ui", files: { "apps/widget/components/pages/Probe.tsx": ui } });
}
if (hasReact) {
  cases.push({ name: "intrinsic-ts", files: { "apps/widget/lib/intrinsic.ts": INTRINSIC } });
  cases.push({ name: "intrinsic-dts", files: { "apps/widget/lib/intrinsic.d.ts": INTRINSIC } });
}

const result = { candidate: relative(dirname(ws), ws), cases: [] };
for (const { name, files } of cases) {
  const written = Object.keys(files).map((path) => join(web, path));
  const made = [];
  try {
    for (const [path, text] of Object.entries(files)) {
      const full = join(web, path);
      const dir = dirname(full);
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
        made.push(dir);
      }
      writeFileSync(full, text);
    }
    // 사례마다 판정자를 새로 세운다. 프로젝트 서비스가 앞 사례의 파일 목록을 들고 있지 않게 한다.
    const eslint = new ESLint({ cwd: web });
    const linted = written.filter((path) => /\.tsx?$/.test(path));
    const reports = await eslint.lintFiles(linted);
    result.cases.push({
      name,
      files: Object.keys(files),
      messages: reports.flatMap((report) =>
        report.messages.map((message) => ({
          file: relative(web, report.filePath).split(sep).join("/"),
          rule: message.ruleId,
          message: message.message.split("\n")[0].slice(0, 160),
        })),
      ),
    });
  } finally {
    for (const path of written) {
      rmSync(path, { force: true });
    }
    for (const dir of made.reverse()) {
      rmSync(dir, { recursive: true, force: true });
    }
  }
}

writeFileSync(join(ws, "judge.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
