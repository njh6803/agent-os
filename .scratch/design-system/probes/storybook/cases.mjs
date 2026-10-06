// design-system Storybook 프로브: 스토리 파일과 .storybook/ 이 판정자의 범위에 실제로 드는지, 걸리는 것이 무엇인지 사례로 잰다.
//   node .scratch/design-system/probes/storybook/cases.mjs <작업 루트>/storybook
// setup.mjs 가 지은 트리에서 돈다. 사례 파일은 제자리에 잠깐 쓰고 되돌린다. 결과는 <작업 루트>/storybook/cases.json 에도 쓴다.
//
// lint     web/ 의 ESLint 설정 그대로(new ESLint({ cwd: web })) lintText 로 위반을 넣어 규칙 ID 를 본다. 원칙 III 의 넷
//          (as, any, !, 타입 기반 no-unsafe-*)과, Storybook 의 Globals(`[name: string]: any`)를 그대로 쓸 때. 손대지 않은
//          파일은 lintFiles 로 메시지가 0 인지와 isPathIgnored 가 거짓인지 본다
// scope    packages/ui/tsconfig.json 의 include 에서 `.storybook/**/*` 를 빼면 ESLint 와 tsc 가 그 파일을 어떻게 보는지
//          (TypeScript 의 `**` 는 점으로 시작하는 폴더를 맞추지 않는다). 그리고 check:tsconfig 가 패키지의 빌드용
//          tsconfig 까지 훑는지(strict 계열 하나를 끄고 돌린다)
// format   Prettier 가 .storybook/ 을 보는지(getFileInfo 와, 모양을 깨뜨린 파일로 verify 의 format 명령을 돌린 결과)
// types    `satisfies Meta<typeof Button>` 와 `StoryObj<typeof meta>` 가 잘못된 인자와 빠진 필수 인자를 tsc 에서 잡는지
// stories  @storybook/addon-vitest 로 실제 chromium 에서: 대비가 부족한 스토리(a11y test "error" 와 "todo"), 토큰 색이
//          스토리 테스트에서 실제로 칠해지는지(Tailwind 가 viteFinal 로 vitest 쪽에도 들어갔는지), 그 chromium 의 판

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const ui = join(web, "packages", "ui");
const atoms = join(ui, "src", "components", "atoms");
const sb = join(ui, ".storybook");
const req = createRequire(join(web, "package.json"));
const { ESLint } = await import(pathToFileURL(req.resolve("eslint")).href);
// createRequire 가 푸는 것은 CJS 입구라 import 하면 default 에 든다.
const prettierModule = await import(pathToFileURL(req.resolve("prettier")).href);
const prettier = prettierModule.default ?? prettierModule;

const result = { lint: [], clean: [], scope: {}, format: {}, types: [], stories: {} };

// ---------- lint ----------
const judge = new ESLint({ cwd: web });
const ruleIds = async (path, source) => {
  const [lint] = await judge.lintText(source, { filePath: path });
  return (lint?.messages ?? []).map((message) => ({
    rule: message.ruleId,
    message: message.message.split("\n")[0],
  }));
};
const read = (path) => readFileSync(path, "utf-8");

const LINT_CASES = [
  {
    name: ".storybook/preview.tsx 의 as",
    path: join(sb, "preview.tsx"),
    append: 'export const 수 = JSON.parse("1") as number;\n',
    expect: "@typescript-eslint/consistent-type-assertions",
  },
  {
    name: ".storybook/main.ts 의 any",
    path: join(sb, "main.ts"),
    append: "export function 받는다(값: any): void {\n  void 값;\n}\n",
    expect: "@typescript-eslint/no-explicit-any",
  },
  {
    name: "스토리 파일의 비null 단언",
    path: join(atoms, "Button.stories.tsx"),
    append: "export function 첫째(목록: readonly string[]): string {\n  return 목록[0]!;\n}\n",
    expect: "@typescript-eslint/no-non-null-assertion",
  },
  {
    name: "스토리 파일의 타입 기반 규칙(JSON.parse 의 any 를 number 에)",
    path: join(atoms, "Switch.stories.tsx"),
    append: 'export const 수: number = JSON.parse("1");\n',
    expect: "@typescript-eslint/no-unsafe-assignment",
  },
  {
    name: "데코레이터가 context.globals 의 값을 그대로 쓸 때",
    path: join(sb, "preview.tsx"),
    append:
      'export const 그대로: Decorator = (Story, context) => {\n  document.documentElement.dataset["theme"] = context.globals["theme"];\n  return <Story />;\n};\n',
    expect: "@typescript-eslint/no-unsafe-assignment",
  },
  {
    name: "스토리의 render 에서 as 로 인자를 좁힐 때",
    path: join(atoms, "Button.stories.tsx"),
    append:
      "export const 좁힘: Story = {\n  render: (args) => <Button {...args}>{String(args.children as string)}</Button>,\n};\n",
    expect: "@typescript-eslint/consistent-type-assertions",
  },
];
for (const testCase of LINT_CASES) {
  const messages = await ruleIds(testCase.path, `${read(testCase.path)}\n${testCase.append}`);
  result.lint.push({
    name: testCase.name,
    expect: testCase.expect,
    hit: messages.some((message) => message.rule === testCase.expect),
    messages,
  });
}

const CLEAN = [
  join(sb, "main.ts"),
  join(sb, "preview.tsx"),
  join(sb, "shadow.tsx"),
  join(sb, "css-inline.d.ts"),
  join(atoms, "Button.stories.tsx"),
  join(atoms, "Switch.stories.tsx"),
  join(web, "vitest.config.ts"),
];
const linted = await judge.lintFiles(CLEAN);
for (const path of CLEAN) {
  const found = linted.find((entry) => resolve(entry.filePath) === resolve(path));
  result.clean.push({
    file: rel(path),
    ignored: await judge.isPathIgnored(path),
    linted: found !== undefined,
    messages: (found?.messages ?? []).map((message) => `${message.ruleId}: ${message.message}`),
  });
}

// ---------- scope: tsconfig 의 include ----------
const tsconfigPath = join(ui, "tsconfig.json");
const tsconfig = read(tsconfigPath);
const tsc = join(web, "node_modules", "typescript", "bin", "tsc");
const listFiles = () =>
  spawnSync(process.execPath, [tsc, "-p", tsconfigPath, "--listFilesOnly"], {
    cwd: ui,
    encoding: "utf-8",
  })
    .stdout.split(/\r?\n/)
    .filter((line) => line.includes("/packages/ui/") && !line.includes("node_modules"))
    .map((line) => line.slice(line.indexOf("packages/ui/")));
// typescript-eslint 의 project service 는 프로세스에 하나라, 같은 프로세스에서 tsconfig 를 바꿔도 앞의 판을 쓴다
// (이 프로브의 첫 실행에서 메시지 0 으로 나왔다). verify 의 린트 명령을 따로 띄워 잰다.
const eslintCli = (path) => {
  const run = spawnSync(
    process.execPath,
    [join(web, "node_modules", "eslint", "bin", "eslint.js"), "--max-warnings", "0", path],
    { cwd: web, encoding: "utf-8" },
  );
  return {
    status: run.status,
    lines: run.stdout
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => /error|warning/.test(line)),
  };
};
result.scope.withStorybookInclude = {
  tscFiles: listFiles(),
  eslintOnMainTs: eslintCli(join(sb, "main.ts")),
};
try {
  writeFileSync(tsconfigPath, tsconfig.replace(', ".storybook/**/*"', ""));
  result.scope.withoutStorybookInclude = {
    tsconfigInclude: JSON.parse(read(tsconfigPath)).include,
    tscFiles: listFiles(),
    eslintOnMainTs: eslintCli(join(sb, "main.ts")),
  };
  // `**` 가 점 폴더를 맞추는지 따로 본다.
  writeFileSync(tsconfigPath, tsconfig.replace('".storybook/**/*"', '"**/*"'));
  result.scope.withDoubleStar = {
    tsconfigInclude: JSON.parse(read(tsconfigPath)).include,
    storybookFilesInProgram: listFiles().filter((file) => file.includes("/.storybook/")),
  };
} finally {
  writeFileSync(tsconfigPath, tsconfig);
}

// check:tsconfig 가 패키지의 tsconfig 둘을 실제로 훑는지. 빌드용 tsconfig 에서 strict 계열 하나를 끄고 돌린다.
const buildTsconfigPath = join(ui, "tsconfig.build.json");
const buildTsconfig = read(buildTsconfigPath);
try {
  writeFileSync(
    buildTsconfigPath,
    buildTsconfig.replace('"noEmit": false,', '"noEmit": false,\n    "strictNullChecks": false,'),
  );
  const run = spawnSync(process.execPath, [join(web, "tools", "check-tsconfig.ts")], {
    cwd: web,
    encoding: "utf-8",
  });
  result.scope.checkTsconfigWithStrictOff = {
    status: run.status,
    lines: run.stdout.split(/\r?\n/).filter(Boolean),
  };
} finally {
  writeFileSync(buildTsconfigPath, buildTsconfig);
}

// ---------- format ----------
const ignorePath = [join(ws, ".gitignore"), join(web, ".prettierignore")];
for (const path of [
  join(sb, "main.ts"),
  join(sb, "preview.tsx"),
  join(atoms, "Button.stories.tsx"),
]) {
  const info = await prettier.getFileInfo(path, { ignorePath });
  result.format[rel(path)] = { ignored: info.ignored, parser: info.inferredParser };
}
const mainTs = read(join(sb, "main.ts"));
try {
  writeFileSync(join(sb, "main.ts"), mainTs.replace("const config = {", "const config = {   "));
  const run = pnpm(["run", "format"], web);
  result.format.misformattedMainTs = {
    status: run.status,
    reported: run.output.split(/\r?\n/).filter((line) => line.includes(".storybook")),
  };
} finally {
  writeFileSync(join(sb, "main.ts"), mainTs);
}

// ---------- types ----------
const TYPE_CASES = [
  {
    name: "Button 스토리에 없는 변형",
    path: join(atoms, "Button.stories.tsx"),
    change: (text) =>
      text.replace(
        'export const Secondary: Story = { args: { variant: "secondary" } };',
        'export const Secondary: Story = { args: { variant: "tertiary" } };',
      ),
  },
  {
    name: "Switch 의 필수 인자 label 을 meta 에서 뺐을 때",
    path: join(atoms, "Switch.stories.tsx"),
    change: (text) =>
      text.replace(
        'args: { label: "알림 받기", onCheckedChange: fn() },',
        "args: { onCheckedChange: fn() },",
      ),
  },
];
for (const testCase of TYPE_CASES) {
  const original = read(testCase.path);
  const changed = testCase.change(original);
  if (changed === original) {
    throw new Error(`사례를 넣을 자리를 못 찾았다: ${testCase.name}`);
  }
  try {
    writeFileSync(testCase.path, changed);
    const run = spawnSync(process.execPath, [tsc, "--noEmit", "-p", tsconfigPath], {
      cwd: ui,
      encoding: "utf-8",
    });
    result.types.push({
      name: testCase.name,
      status: run.status,
      errors: run.stdout.split(/\r?\n/).filter((line) => /error TS\d+/.test(line)),
    });
  } finally {
    writeFileSync(testCase.path, original);
  }
}

// ---------- stories: 실제 chromium ----------
const STORY_FILES = {
  "Contrast.stories.tsx": `import type { Meta, StoryObj } from "@storybook/react-vite";

const meta = { title: "probe/Contrast" } satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const LowContrastError: Story = {
  render: () => <p style={{ color: "#a1a1aa", backgroundColor: "#ffffff" }}>흐린 글자</p>,
};

export const LowContrastTodo: Story = {
  parameters: { a11y: { test: "todo" } },
  render: () => <p style={{ color: "#a1a1aa", backgroundColor: "#ffffff" }}>흐린 글자</p>,
};
`,
  "Painted.stories.tsx": `import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { Button } from "./Button";

const meta = {
  title: "probe/Painted",
  component: Button,
  args: { children: "보내기", variant: "primary" },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Light: Story = {
  play: async ({ canvas }) => {
    // Playwright 1.63.0 의 browsers.json 이 적은 chromium 빌드에서 도는지.
    await expect(navigator.userAgent).toMatch(/Chrome\\/153\\.0\\.8010\\.12/);
    const style = getComputedStyle(canvas.getByRole("button"));
    await expect(style.backgroundColor).toBe("rgb(29, 78, 216)");
    await expect(style.paddingLeft).toBe("16px");
  },
};

export const Dark: Story = {
  globals: { theme: "dark" },
  play: async ({ canvas }) => {
    const style = getComputedStyle(canvas.getByRole("button"));
    await expect(style.backgroundColor).toBe("rgb(96, 165, 250)");
  },
};
`,
};
const reportFile = join(ws, "cases-vitest.json");
try {
  for (const [name, source] of Object.entries(STORY_FILES)) {
    writeFileSync(join(atoms, name), source);
  }
  const started = Date.now();
  const run = spawnSync(
    process.execPath,
    [
      join(web, "node_modules", "vitest", "vitest.mjs"),
      "run",
      "--project",
      "storybook",
      "--reporter=json",
      `--outputFile=${reportFile}`,
    ],
    { cwd: web, encoding: "utf-8", maxBuffer: 1 << 28 },
  );
  const report = JSON.parse(read(reportFile));
  result.stories = {
    status: run.status,
    wallMs: Date.now() - started,
    tests: report.testResults.flatMap((file) =>
      file.assertionResults.map((test) => ({
        file: file.name.slice(file.name.indexOf("atoms")),
        title: test.title,
        status: test.status,
        failure: (test.failureMessages ?? [])
          .join("\n")
          .split("\n")
          .map((line) => line.replace(/\u001b\[[\d;]*m/g, "").trim())
          .filter((line) => /violations|contrast|Expected|Received|expected/.test(line))
          .slice(0, 6),
      })),
    ),
  };
} finally {
  for (const name of Object.keys(STORY_FILES)) {
    rmSync(join(atoms, name), { force: true });
  }
  if (existsSync(reportFile)) {
    rmSync(reportFile);
  }
}

writeFileSync(join(ws, "cases.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));

function rel(path) {
  return path.slice(web.length + 1).replaceAll("\\", "/");
}

function pnpm(args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수뿐이다.
  const run = spawnSync(`pnpm ${args.join(" ")}`, { cwd, encoding: "utf-8", shell: true });
  return { status: run.status, output: `${run.stdout}${run.stderr}` };
}
