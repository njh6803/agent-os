// design-system Storybook 프로브: 디자인 시스템 패키지(packages/ui)에 Storybook 을 들인 임시 워크스페이스를 짓는다.
//   node .scratch/design-system/probes/storybook/setup.mjs <작업 루트>
//
// <작업 루트>/storybook/ 에 저장소의 web/ 사본과 web/ 이 기대는 뿌리 파일 둘(.gitignore, openapi.json)을 두고(widget_stack
// 의 setup.mjs 와 같은 방식), 그 위에 다음을 얹는다. 저장소의 web/ 은 읽기만 한다. 작업 루트는 저장소 밖이어야 한다.
//   1. ui/ 를 web/ 위에 덮어쓴다(packages/ui: Tailwind v4 테마, atoms 둘과 CSF3 스토리, .storybook/)
//   2. web/vitest.config.ts 에 storybook 프로젝트를 더한다(실제 chromium, @vitest/browser-playwright)
//   3. git init 과 git add(eslint.config.test.ts 가 git 이 추적하는 파일로 판정 범위를 잰다)
//   4. 설치 셋(npm 레지스트리에 닿는다). 단계마다 락을 떠 두어 deps.mjs 가 무엇이 무엇을 더했는지 가른다
//      ui         packages/ui 의 의존(React, Tailwind, Vite)만으로 pnpm install → pnpm-lock.ui.yaml
//      storybook  web/package.json 의 devDependencies 에 Storybook 과 Vitest 브라우저 모드 패키지(ROOT_DEV_DEPS)를,
//                 pnpm-workspace.yaml 에 `allowBuilds: { esbuild: false }` 를 더하고 pnpm install → pnpm-lock.storybook.yaml.
//                 뿌리에 두는 것은 스토리 테스트가 뿌리 vitest.config.ts 의 프로젝트 하나로 돌고 그 설정이 이것들을
//                 import 하기 때문이다
//      cli        packages/ui 에 @tailwindcss/cli 를, allowBuilds 에 `"@parcel/watcher": false` 를 더하고 pnpm install
// 설치 앞의 락과 pnpm-workspace.yaml 은 *.before.* 로 떠 둔다. pnpm 11 의 공급망 유예를 풀지 않는다. 설치가
// pnpm-workspace.yaml 을 이 파일이 더한 줄 밖으로 바꾸면(minimumReleaseAgeExclude 등) 실패로 멈춘다. 그때는 판을 내려
// 다시 잰다.

import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  cpSync,
  readdirSync,
  readFileSync,
  rmSync,
  utimesSync,
  writeFileSync,
} from "node:fs";
import { basename, join, relative, resolve } from "node:path";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const OVERLAY = join(HERE, "ui");

// 뿌리에 더하는 것. @vitest/browser-playwright 는 vitest 와 같은 판을 피어로 고정한다(락의 vitest 5.0.2).
const ROOT_DEV_DEPS = {
  "@storybook/addon-a11y": "^10.6.1",
  "@storybook/addon-vitest": "^10.6.1",
  "@storybook/react-vite": "^10.6.1",
  "@vitest/browser-playwright": "5.0.2",
  playwright: "^1.63.0",
  storybook: "^10.6.1",
};
// 패키지 빌드(@tailwindcss/cli). 따로 설치해 그것이 더하는 것을 가른다.
const BUILD_DEV_DEPS = { "@tailwindcss/cli": "^4.3.3" };
// pnpm-workspace.yaml 에 더하는 것(아래 4의 주석).
const WORKSPACE_ADDITION = "allowBuilds:\n  esbuild: false\n";
const CLI_WORKSPACE_ADDITION = '  "@parcel/watcher": false\n';

// 사본에 들이지 않는 것. 설치물, 빌드와 테스트 산출물.
const SKIPPED = new Set([
  "node_modules",
  ".next",
  "dist",
  "storybook-static",
  "test-results",
  "playwright-report",
  "blob-report",
  "coverage",
]);

const [workRoot] = process.argv.slice(2);
if (workRoot === undefined) {
  console.error("사용: node setup.mjs <작업 루트>");
  process.exit(2);
}
const ws = resolve(workRoot, "storybook");
if (ws.startsWith(REPO)) {
  console.error(`작업 루트는 저장소 밖이어야 한다: ${ws}`);
  process.exit(2);
}
rmSync(ws, { recursive: true, force: true });

for (const file of [".gitignore", "openapi.json"]) {
  cpSync(join(REPO, file), join(ws, file));
}
cpSync(join(REPO, "web"), join(ws, "web"), {
  recursive: true,
  filter: (source) => !SKIPPED.has(basename(source)) && !basename(source).startsWith("judge-"),
});
const web = join(ws, "web");
const ui = join(web, "packages", "ui");
copyFileSync(join(web, "pnpm-lock.yaml"), join(ws, "pnpm-lock.before.yaml"));
copyFileSync(join(web, "pnpm-workspace.yaml"), join(ws, "pnpm-workspace.before.yaml"));

// 1. 덮어쓰기. 윈도우의 복사는 수정 시각을 원본 그대로 둔다. pnpm 11 은 package.json 이 마지막 검사보다 오래됐으면
// 설치를 건너뛰므로 시각을 지금으로 바꾼다(widget_tailwind/setup.mjs 와 같다).
cpSync(OVERLAY, web, { recursive: true });
const now = new Date();
for (const path of filesUnder(OVERLAY)) {
  utimesSync(join(web, relative(OVERLAY, path)), now, now);
}

// 2. 스토리 테스트 프로젝트. Prettier 가 고치지 않을 모양으로 쓴다(verify 의 format 단계).
const STORYBOOK_PROJECT = `      {
        extends: true,
        plugins: [storybookTest({ configDir: STORYBOOK })],
        test: {
          name: "storybook",
          browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            instances: [{ browser: "chromium" }],
          },
        },
      },
`;
// 설정 파일(setProjectAnnotations)은 두지 않는다. 10.3 부터 플러그인이 미리보기 주해를 스스로 싣는다(설치본
// dist/vitest-plugin/index.js 의 requiresProjectAnnotations 를 읽었다).
patch(join(web, "vitest.config.ts"), (text) =>
  replaceOnce(
    replaceOnce(
      replaceOnce(
        text,
        'import { configDefaults, defineConfig } from "vitest/config";\n',
        'import { join } from "node:path";\nimport { storybookTest } from "@storybook/addon-vitest/vitest-plugin";\nimport { playwright } from "@vitest/browser-playwright";\nimport { configDefaults, defineConfig } from "vitest/config";\n',
      ),
      'const PAGES = "apps/admin/components/**/*.test.tsx";\n',
      'const PAGES = "apps/admin/components/**/*.test.tsx";\n// 디자인 시스템의 스토리. 스토리마다 실제 chromium 에서 그리고 play 와 axe(addon-a11y)를 돈다.\nconst STORYBOOK = join(import.meta.dirname, "packages", "ui", ".storybook");\n',
    ),
    '          setupFiles: ["apps/admin/testing/setup.ts"],\n        },\n      },\n',
    `          setupFiles: ["apps/admin/testing/setup.ts"],\n        },\n      },\n${STORYBOOK_PROJECT}`,
  ),
);

// 3. git
run("git", ["init", "-q"], ws);
run("git", ["add", "-A"], ws);

// 4. 설치 셋
// ui: packages/ui 의 의존만. Tailwind 의 네이티브(oxide, lightningcss)는 빌드 스크립트가 없다(widget_tailwind).
writeFileSync(join(ws, "install-ui.log"), timed("pnpm", ["install"], web));
assertWorkspace("packages/ui 설치", "");
copyFileSync(join(web, "pnpm-lock.yaml"), join(ws, "pnpm-lock.ui.yaml"));

// storybook: Storybook 이 의존하는 esbuild 는 postinstall 이 있고, pnpm 11 은 정하지 않은 빌드 스크립트를 만나면
// ERR_PNPM_IGNORED_BUILDS 로 실패하며 pnpm-workspace.yaml 에 `esbuild: set this to true or false` 자리를 써 둔다
// (2026-10-06 이 프로브의 첫 실행). 스크립트를 돌리지 않는 쪽(false)을 미리 적는다. esbuild 는 플랫폼 패키지
// (@esbuild/<플랫폼>)의 바이너리를 직접 불러 postinstall 없이 돈다. deps.mjs 가 이 트리에서 실제로 불러 본다.
addDevDeps(join(web, "package.json"), ROOT_DEV_DEPS);
appendWorkspace(WORKSPACE_ADDITION);
writeFileSync(join(ws, "install-storybook.log"), timed("pnpm", ["install"], web));
assertWorkspace("Storybook 설치", WORKSPACE_ADDITION);
copyFileSync(join(web, "pnpm-lock.yaml"), join(ws, "pnpm-lock.storybook.yaml"));

// cli: 패키지 빌드 도구. @tailwindcss/cli 가 의존하는 @parcel/watcher 도 빌드 스크립트(install: build-from-source.js)가
// 있어 같은 실패를 냈다(2026-10-06 이 프로브의 둘째 실행). 미리 빌드된 플랫폼 패키지를 쓰는 쪽(false)을 적는다.
addDevDeps(join(ui, "package.json"), BUILD_DEV_DEPS);
appendWorkspace(CLI_WORKSPACE_ADDITION);
writeFileSync(join(ws, "install-cli.log"), timed("pnpm", ["install"], web));
assertWorkspace("@tailwindcss/cli 설치", `${WORKSPACE_ADDITION}${CLI_WORKSPACE_ADDITION}`);

run("git", ["add", "-A"], ws);
console.log(`준비됨: ${ws}`);

function appendWorkspace(text) {
  const path = join(web, "pnpm-workspace.yaml");
  writeFileSync(path, `${readFileSync(path, "utf-8")}${text}`);
}

function assertWorkspace(when, added) {
  const expected = `${readFileSync(join(ws, "pnpm-workspace.before.yaml"), "utf-8")}${added}`;
  const after = readFileSync(join(web, "pnpm-workspace.yaml"), "utf-8");
  if (expected !== after) {
    throw new Error(
      `${when}이 pnpm-workspace.yaml 을 바꿨다. 유예를 풀지 않는다. 판을 내려 다시 잰다:\n${after}`,
    );
  }
}

function addDevDeps(path, deps) {
  const manifest = JSON.parse(readFileSync(path, "utf-8"));
  const merged = { ...manifest.devDependencies, ...deps };
  manifest.devDependencies = Object.fromEntries(
    Object.keys(merged)
      .sort()
      .map((name) => [name, merged[name]]),
  );
  writeFileSync(path, `${JSON.stringify(manifest, null, 2)}\n`);
  utimesSync(path, new Date(), new Date());
}

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

function patch(path, change) {
  writeFileSync(path, change(readFileSync(path, "utf-8")));
}

function replaceOnce(text, anchor, replacement) {
  const count = text.split(anchor).length - 1;
  if (count !== 1) {
    throw new Error(`고칠 자리가 ${String(count)}개다(1이어야 한다): ${anchor}`);
  }
  return text.replace(anchor, replacement);
}

/** 명령을 돌리고 출력과 걸린 시간을 글자로 돌려준다. 실패하면 던진다. */
function timed(command, args, cwd) {
  const started = Date.now();
  const output = run(command, args, cwd);
  return `${output}\n[걸린 시간] ${String(Date.now() - started)}ms\n`;
}

function run(command, args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수뿐이다.
  const viaShell = process.platform === "win32" && command === "pnpm";
  const result = viaShell
    ? spawnSync([command, ...args].join(" "), { cwd, encoding: "utf-8", shell: true })
    : spawnSync(command, args, { cwd, encoding: "utf-8" });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`;
  process.stdout.write(output);
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} 가 ${String(result.status)} 로 끝났다(${cwd})`);
  }
  return output;
}
