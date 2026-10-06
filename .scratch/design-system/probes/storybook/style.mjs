// design-system Storybook 프로브: Storybook 정적 빌드와 그 안의 스토리가 그리는 스타일을 잰다.
//   node .scratch/design-system/probes/storybook/style.mjs <작업 루트>/storybook
// setup.mjs 가 지은 트리에서 돈다. 포트 8795~8799 가운데 빈 것 하나를 쓰고, 사본의 web/ 에 깔린 Playwright 의
// chromium 이 %LOCALAPPDATA%\ms-playwright 에 있어야 한다(아무것도 설치하지 않는다). 결과는 <작업 루트>/storybook/style.json.
//
// build    packages/ui 에서 `pnpm run build-storybook`(storybook build)의 성패와 걸린 시간, index.json 의 판과 entries
//          (/design-sync 의 storybook 모양이 읽는 것), 생성 CSS 의 크기
// theme    light DOM 에서 data-theme 을 light 와 dark 로 바꿨을 때 쓰임새 변수와 배경·글자색의 계산값. 그리고 data-theme 을
//          지우고 prefers-color-scheme: dark 를 흉내 냈을 때(문서와 shadow 호스트 둘 다)
// shadow   같은 스토리를 .storybook/shadow.tsx 의 틀(globals shadow=on: 보정 시트까지, raw: Tailwind 시트만)로 shadow root
//          안에 그려, light DOM(shadow=off)과 계산 스타일 전부(표준 속성과 사용자 정의 속성을 갈라)를 견준다. 문서에 실린
//          전역 CSS(preview 의 import)를 그대로 둔 것(doc)과 끈 것(nodoc) 둘 다. 끈 것이 사이트 페이지에 든 위젯의 자리다
// rem      Storybook 이 빌드한 패키지 CSS 와 iframe.html(Storybook 자신의 틀)에 남은 rem 의 자리

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { extname, join, normalize, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const ui = join(web, "packages", "ui");
const out = join(ui, "storybook-static");
const req = createRequire(join(web, "package.json"));
const result = {};

// ---------- build ----------
rmSync(out, { recursive: true, force: true });
const started = Date.now();
const build = spawnSync("pnpm run build-storybook", {
  cwd: ui,
  encoding: "utf-8",
  shell: true,
  env: { ...process.env, STORYBOOK_DISABLE_TELEMETRY: "1" },
});
const assets = existsSync(join(out, "assets")) ? readdirSync(join(out, "assets")) : [];
const packageCss = assets
  .filter((name) => name.endsWith(".css"))
  .map((name) => ({ name, text: readFileSync(join(out, "assets", name), "utf-8") }))
  .filter(({ text }) => text.includes("tailwindcss v4"));
result.build = {
  status: build.status,
  ms: Date.now() - started,
  tail: clean(`${build.stdout}${build.stderr}`)
    .split(/\r?\n/)
    .filter((line) => /error|warn|completed|built in/i.test(line))
    .slice(-6),
  packageCss: packageCss.map(({ name, text }) => ({
    name,
    bytes: Buffer.byteLength(text),
    gzip: gzipSync(text, { level: 9 }).length,
  })),
};
if (build.status !== 0) {
  finish();
  process.exit(1);
}
const index = JSON.parse(readFileSync(join(out, "index.json"), "utf-8"));
const entries = Object.values(index.entries);
result.index = {
  v: index.v,
  count: entries.length,
  types: [...new Set(entries.map((entry) => entry.type))],
  ids: entries.map((entry) => entry.id),
  importPaths: [...new Set(entries.map((entry) => entry.importPath))],
  sample: entries[0],
};

// ---------- rem ----------
const remSites = (text) =>
  [...text.matchAll(/([^{};]*)\{([^{}]*?(-?\d*\.?\d+rem\b)[^{}]*)\}/g)].map((match) => ({
    selector: match[1].trim().slice(-80),
    declaration: match[2]
      .split(";")
      .filter((part) => /\d*\.?\d+rem\b/.test(part))
      .map((part) => part.trim()),
  }));
result.rem = {
  packageCss: packageCss.map(({ name, text }) => ({ name, sites: remSites(text) })),
  iframeHtml: remSites(readFileSync(join(out, "iframe.html"), "utf-8")),
};

// ---------- 정적 서버와 chromium ----------
const TYPES = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
};
const server = createServer((request, response) => {
  const path = normalize(join(out, decodeURIComponent(new URL(request.url, "http://x").pathname)));
  if (!path.startsWith(out) || !existsSync(path) || statSync(path).isDirectory()) {
    response.writeHead(404).end();
    return;
  }
  response.writeHead(200, { "content-type": TYPES[extname(path)] ?? "application/octet-stream" });
  response.end(readFileSync(path));
});
const port = await listen(server, [8795, 8796, 8797, 8798, 8799]);
const { chromium } = req("playwright");
const browser = await chromium.launch();
result.browser = { version: browser.version(), executable: chromium.executablePath() };

const SAMPLES = [
  { id: "atoms-button--primary", targets: [["button", null]] },
  { id: "atoms-button--secondary", targets: [["button", null]] },
  { id: "atoms-button--danger", targets: [["button", null]] },
  {
    id: "atoms-switch--on",
    targets: [
      ["label", null],
      ["span[aria-hidden]", null],
      ["span[aria-hidden]", "::after"],
    ],
  },
  {
    id: "atoms-switch--off",
    targets: [
      ["label", null],
      ["span[aria-hidden]", null],
      ["span[aria-hidden]", "::after"],
    ],
  },
];
const VARIANTS = [
  { name: "off", shadow: "off", doc: true },
  { name: "on/doc", shadow: "on", doc: true },
  { name: "raw/doc", shadow: "raw", doc: true },
  { name: "on/nodoc", shadow: "on", doc: false },
  { name: "raw/nodoc", shadow: "raw", doc: false },
];

result.shadow = [];
result.theme = [];
try {
  for (const sample of SAMPLES) {
    for (const theme of ["light", "dark"]) {
      const styles = {};
      for (const variant of VARIANTS) {
        styles[variant.name] = await capture(sample, theme, variant);
      }
      const reference = styles.off;
      for (const variant of VARIANTS.slice(1)) {
        const got = styles[variant.name];
        result.shadow.push({
          story: sample.id,
          theme,
          variant: variant.name,
          docSheetsDisabled: got.disabled,
          documentAfterDisable: got.documentProbe,
          diffs: reference.targets.map((target, at) => ({
            target: target.key,
            standard: diff(target.standard, got.targets[at].standard),
            custom: diff(pickTw(target.custom), pickTw(got.targets[at].custom)),
          })),
        });
      }
      const first = reference.targets[0];
      result.theme.push({
        story: sample.id,
        theme,
        target: first.key,
        vars: Object.fromEntries(
          ["--color-surface", "--color-text", "--color-accent", "--color-border"].map((name) => [
            name,
            first.custom[name] ?? null,
          ]),
        ),
        backgroundColor: first.standard["background-color"],
        color: first.standard.color,
      });
    }
  }
  result.system = await systemPreference();
} finally {
  await browser.close();
  server.close();
  finish();
}

async function capture(sample, theme, variant) {
  const page = await browser.newPage();
  const url = `http://127.0.0.1:${String(port)}/iframe.html?id=${sample.id}&viewMode=story&globals=theme:${theme};shadow:${variant.shadow}`;
  await page.goto(url);
  const selector = sample.targets[0][0];
  await page.waitForFunction(
    ({ shadow, selector }) => {
      const root =
        shadow === "off"
          ? document.querySelector("#storybook-root")
          : document.querySelector("[data-shadow-frame]")?.shadowRoot;
      return root?.querySelector(selector) != null;
    },
    { shadow: variant.shadow, selector },
  );
  const got = await page.evaluate(
    ({ shadow, doc, targets }) => {
      let disabled = 0;
      if (!doc) {
        for (const sheet of document.styleSheets) {
          let text = "";
          try {
            text = Array.from(sheet.cssRules, (rule) => rule.cssText).join("\n");
          } catch {
            text = "";
          }
          if (text.includes("--color-surface")) {
            sheet.disabled = true;
            disabled += 1;
          }
        }
      }
      const documentProbe = {
        rootColorSurface: getComputedStyle(document.documentElement).getPropertyValue(
          "--color-surface",
        ),
        bodyTwBorderStyle: getComputedStyle(document.body).getPropertyValue("--tw-border-style"),
      };
      const root =
        shadow === "off"
          ? document.querySelector("#storybook-root")
          : document.querySelector("[data-shadow-frame]").shadowRoot;
      return {
        disabled,
        documentProbe,
        targets: targets.map(([selector, pseudo]) => {
          const element = root.querySelector(selector);
          const style = getComputedStyle(element, pseudo);
          const standard = {};
          const custom = {};
          for (const name of style) {
            (name.startsWith("--") ? custom : standard)[name] = style.getPropertyValue(name).trim();
          }
          return { key: `${selector}${pseudo ?? ""}`, standard, custom };
        }),
      };
    },
    { shadow: variant.shadow, doc: variant.doc, targets: sample.targets },
  );
  await page.close();
  return got;
}

/** data-theme 을 지우고 prefers-color-scheme: dark 를 흉내 냈을 때의 쓰임새 변수. */
async function systemPreference() {
  const rows = [];
  for (const shadow of ["off", "on"]) {
    for (const scheme of ["light", "dark"]) {
      const page = await browser.newPage();
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(
        `http://127.0.0.1:${String(port)}/iframe.html?id=atoms-button--primary&viewMode=story&globals=theme:light;shadow:${shadow}`,
      );
      await page.waitForFunction(
        (shadow) =>
          (shadow === "off"
            ? document.querySelector("#storybook-root")
            : document.querySelector("[data-shadow-frame]")?.shadowRoot
          )?.querySelector("button") != null,
        shadow,
      );
      rows.push({
        shadow,
        scheme,
        ...(await page.evaluate((shadow) => {
          const host = document.querySelector("[data-shadow-frame]");
          const button = (
            shadow === "off" ? document.querySelector("#storybook-root") : host.shadowRoot
          ).querySelector("button");
          const read = () => ({
            surface: getComputedStyle(button).getPropertyValue("--color-surface"),
            background: getComputedStyle(button).backgroundColor,
          });
          const withAttribute = read();
          document.documentElement.removeAttribute("data-theme");
          host?.removeAttribute("data-theme");
          return { withDataThemeLight: withAttribute, withoutDataTheme: read() };
        }, shadow)),
      });
      await page.close();
    }
  }
  return rows;
}

function pickTw(custom) {
  return Object.fromEntries(
    Object.entries(custom).filter(
      ([name]) => name.startsWith("--tw-") || name.startsWith("--color-"),
    ),
  );
}

function diff(a, b) {
  const names = [...new Set([...Object.keys(a), ...Object.keys(b)])].sort();
  return names
    .filter((name) => a[name] !== b[name])
    .map((name) => ({ name, light: a[name] ?? null, shadow: b[name] ?? null }));
}

function clean(text) {
  return text.replace(/\u001b\[[\d;]*m/g, "");
}

function listen(target, ports) {
  return new Promise((resolvePort, reject) => {
    const tryAt = (at) => {
      if (at >= ports.length) {
        reject(new Error(`빈 포트가 없다: ${ports.join(", ")}`));
        return;
      }
      target.once("error", () => tryAt(at + 1));
      target.listen(ports[at], "127.0.0.1", () => resolvePort(ports[at]));
    };
    tryAt(0);
  });
}

function finish() {
  writeFileSync(join(ws, "style.json"), `${JSON.stringify(result, null, 2)}\n`);
  const summary = {
    build: result.build,
    index: result.index && {
      v: result.index.v,
      count: result.index.count,
      types: result.index.types,
    },
    browser: result.browser,
    rem: result.rem,
    theme: result.theme,
    system: result.system,
    shadow: (result.shadow ?? []).map((row) => ({
      story: row.story,
      theme: row.theme,
      variant: row.variant,
      disabled: row.docSheetsDisabled,
      standardDiffs: row.diffs.reduce((sum, target) => sum + target.standard.length, 0),
      props: row.diffs
        .filter((target) => target.standard.length > 0)
        .map(
          (target) =>
            `${target.target}: ${target.standard.map((d) => `${d.name} ${String(d.light)} → ${String(d.shadow)}`).join(", ")}`,
        ),
      customDiffs: [
        ...new Set(
          row.diffs.flatMap((target) =>
            target.custom.map((d) => `${d.name} ${String(d.light)} → ${String(d.shadow)}`),
          ),
        ),
      ],
    })),
  };
  console.log(JSON.stringify(summary, null, 2));
}
