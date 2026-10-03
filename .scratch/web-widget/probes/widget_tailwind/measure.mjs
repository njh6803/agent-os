// web-widget 위젯 스타일 프로브: 빌드하고, 산출물의 크기와 Tailwind 가 낸 CSS 를 읽는다.
//   node .scratch/web-widget/probes/widget_tailwind/measure.mjs <작업 루트>/react
// setup.mjs 가 지은 트리를 받는다. 빌드는 다섯이다.
//   element           vite build --mode element           @tailwindcss/vite. postcss.config.mjs 도 Vite 가 읽는다(모양 그대로)
//   element-viteonly  vite build --mode element-viteonly  @tailwindcss/vite 만(PostCSS 설정을 읽지 않는다)
//   element-postcss   vite build --mode element-postcss   postcss.config.mjs 만(Next 와 같은 길)
//   page              vite build --mode page              iframe 용 정적 페이지. CSS 를 파일로 뽑는다
//   next              next build                          iframe 페이지. postcss.config.mjs 로 같은 CSS 원본을 빌드
// 내는 것
//   sizes     파일 바이트(min)와 gzip(zlib 9단계). element 는 baseline.json(덮어쓰기 전 기준)과의 차이도
//   css       element 번들에 글자로 든 CSS 를 꺼내(번들의 문자열 리터럴) 크기를 재고, 셋이 같은 바이트인지 본다.
//             page·Next 의 CSS 파일과는 PostCSS 로 파싱해 유틸리티 선택자, `@property` 이름, 테마 변수 이름의 집합을 견준다
//   anatomy   element CSS 를 읽은 것. 테마 변수·preflight 가 어느 선택자에 나오는지(`:root`, `:host`), `@property` 의 자리와
//             목록, Tailwind 가 `@property` 를 모르는 브라우저에 내는 대체 블록의 `@supports` 조건과 선택자
//   afterBuild  빌드 산출물이 남은 채로 verify 의 lint 인자와 prettier --check 를 apps/widget 에 친 결과
// 결과는 <작업 루트>/react/measure.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";
import { runInNewContext } from "node:vm";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");
const fromWidget = createRequire(join(widget, "package.json"));
const fromWeb = createRequire(join(web, "package.json"));
const postcss = createRequire(fromWidget.resolve("@tailwindcss/postcss"))("postcss");
const baseline = JSON.parse(readFileSync(join(ws, "baseline.json"), "utf-8"));

const ELEMENT_MODES = ["element", "element-viteonly", "element-postcss"];
const result = {
  candidate: relative(dirname(ws), ws),
  builds: {},
  sizes: {},
  css: {},
  afterBuild: {},
};

function run(label, bin, args, cwd) {
  const started = Date.now();
  const proc = spawnSync(process.execPath, [bin, ...args], {
    cwd,
    encoding: "utf-8",
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
  });
  const output = `${proc.stdout}${proc.stderr}`.replace(/\u001b\[[\d;]*m/g, "");
  result.builds[label] = {
    status: proc.status,
    ms: Date.now() - started,
    tail: output.split(/\r?\n/).filter(Boolean).slice(-12),
  };
  return proc.status === 0;
}

const size = (bytes) => ({ min: bytes.length, gzip: gzipSync(bytes, { level: 9 }).length });

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true })
    .flatMap((entry) =>
      entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
    )
    .sort();
}

/** 번들에서 Tailwind CSS 가 든 문자열 리터럴을 꺼낸다. 표지(`@layer theme`)를 감싼 따옴표 쌍을 찾아 평가한다. */
function cssLiteral(js) {
  const mark = js.indexOf("@layer theme");
  if (mark < 0) {
    return null;
  }
  let open = mark;
  while (open > 0 && !(`"'\``.includes(js[open]) && js[open - 1] !== "\\")) {
    open -= 1;
  }
  const quote = js[open];
  let close = open + 1;
  while (close < js.length && js[close] !== quote) {
    close += js[close] === "\\" ? 2 : 1;
  }
  return runInNewContext(js.slice(open, close + 1));
}

/** CSS 를 파싱해 견줄 집합을 낸다. 선택자의 클래스, `@property` 이름, `:root`/`:host` 규칙의 변수 이름. */
function inventory(css) {
  const tree = postcss.parse(css);
  const classes = new Set();
  const properties = new Set();
  const themeVars = new Set();
  tree.walkRules((rule) => {
    for (const match of rule.selector.matchAll(/\.((?:\\.|[\w-])+)/g)) {
      classes.add(match[1].replace(/\\/g, ""));
    }
    if (/:root|:host/.test(rule.selector)) {
      rule.walkDecls(/^--/, (decl) => themeVars.add(decl.prop));
    }
  });
  tree.walkAtRules("property", (atRule) => properties.add(atRule.params.trim()));
  return { classes, properties, themeVars };
}

function compareInventories(a, b) {
  const out = {};
  for (const key of ["classes", "properties", "themeVars"]) {
    out[key] = {
      count: [a[key].size, b[key].size],
      onlyFirst: [...a[key]].filter((item) => !b[key].has(item)).sort(),
      onlySecond: [...b[key]].filter((item) => !a[key].has(item)).sort(),
    };
  }
  return out;
}

/** element CSS 를 읽는다. 테마 변수·preflight·`@property`·대체 블록이 어디에 어떻게 나오는지. */
function anatomy(css) {
  const tree = postcss.parse(css);
  const out = {
    layerOrder: [],
    themeSelectors: [],
    hostSelectors: [],
    properties: [],
    fallback: null,
  };
  // 층의 순서는 처음 나온 자리가 정한다. 압축기는 `@layer a; @layer b, c;` 문을 블록으로 접기도 한다.
  for (const node of tree.nodes) {
    if (node.type === "atrule" && node.name === "layer") {
      for (const name of node.params.split(",").map((part) => part.trim())) {
        if (!out.layerOrder.includes(name)) {
          out.layerOrder.push(name);
        }
      }
    }
  }
  tree.walkRules((rule) => {
    const layer =
      rule.parent?.type === "atrule" ? `@${rule.parent.name} ${rule.parent.params}` : "";
    if (layer === "@layer theme") {
      out.themeSelectors.push(rule.selector);
    }
    if (/:host/.test(rule.selector)) {
      out.hostSelectors.push({ selector: rule.selector, in: layer });
    }
  });
  tree.walkAtRules("property", (atRule) => {
    const field = (name) => atRule.nodes.find((node) => node.prop === name)?.value ?? null;
    out.properties.push({
      name: atRule.params.trim(),
      parent: atRule.parent?.type === "root" ? "root" : `@${atRule.parent.name}`,
      syntax: field("syntax"),
      inherits: field("inherits"),
      initial: field("initial-value"),
    });
  });
  tree.walkAtRules("supports", (atRule) => {
    if (atRule.parent?.type === "atrule" && atRule.parent.params === "properties") {
      const rule = atRule.nodes.find((node) => node.type === "rule");
      const declared = new Map(rule?.nodes.map((decl) => [decl.prop, decl.value]) ?? []);
      out.fallback = {
        supports: atRule.params,
        selector: rule?.selector ?? null,
        count: declared.size,
        // `@property` 의 초기값(없으면 initial)과 대체 블록의 값이 같은지. 다르면 그 이름을 든다.
        differs: out.properties
          .filter((property) => declared.get(property.name) !== (property.initial ?? "initial"))
          .map((property) => ({
            name: property.name,
            property: property.initial,
            fallback: declared.get(property.name) ?? null,
          })),
      };
    }
  });
  out.propertyCount = out.properties.length;
  return out;
}

// ---------- 빌드 ----------
const vite = join(dirname(fromWidget.resolve("vite/package.json")), "bin", "vite.js");
const cssOf = {};
for (const mode of ELEMENT_MODES) {
  if (run(mode, vite, ["build", "--mode", mode], widget)) {
    const bytes = readFileSync(join(widget, "dist", mode, "widget.js"));
    const own = size(bytes);
    result.sizes[mode] = {
      ...own,
      vsBaseline: { min: own.min - baseline.min, gzip: own.gzip - baseline.gzip },
    };
    const css = cssLiteral(bytes.toString("utf-8"));
    cssOf[mode] = css;
    result.css[mode] = css === null ? null : size(Buffer.from(css, "utf-8"));
  }
}
result.sizes.baseline = baseline;
const [first, ...rest] = ELEMENT_MODES.map((mode) => cssOf[mode]);
result.css.elementModesIdentical = rest.every((css) => css === first);
result.css.firstDiff = rest.map((css) => {
  if (typeof css !== "string" || typeof first !== "string") {
    return null;
  }
  let at = 0;
  while (at < css.length && css[at] === first[at]) {
    at += 1;
  }
  return at === css.length && at === first.length
    ? null
    : { at, lengths: [first.length, css.length] };
});
const elementCss = cssOf.element;
if (typeof elementCss === "string") {
  result.anatomy = anatomy(elementCss);
}

if (run("page", vite, ["build", "--mode", "page"], widget)) {
  const dir = join(widget, "dist", "page");
  const files = filesUnder(dir);
  result.sizes.page = Object.fromEntries(
    files.map((path) => [relative(dir, path).split(sep).join("/"), size(readFileSync(path))]),
  );
  const cssFile = files.find((path) => path.endsWith(".css"));
  if (cssFile !== undefined && typeof elementCss === "string") {
    result.css.pageVsElement = compareInventories(
      inventory(elementCss),
      inventory(readFileSync(cssFile, "utf-8")),
    );
  }
}

const next = join(dirname(fromWidget.resolve("next/package.json")), "dist", "bin", "next");
if (run("next", next, ["build"], widget)) {
  const html = join(widget, ".next", "server", "app", "index.html");
  const text = readFileSync(html, "utf-8");
  const assets = [
    ...new Set(
      [...text.matchAll(/<(?:script|link)\b[^>]*>/g)]
        .map((match) => match[0])
        .filter((tag) => !/\bnoModule\b/i.test(tag))
        .flatMap((tag) => {
          const found = /(?:src|href)="\/_next\/(static\/[^"]+\.(?:js|css))"/.exec(tag);
          return found === null ? [] : [found[1]];
        }),
    ),
  ];
  const each = Object.fromEntries(
    [["index.html", html], ...assets.map((asset) => [asset, join(widget, ".next", asset)])].map(
      ([name, path]) => [name, size(readFileSync(path))],
    ),
  );
  result.sizes.next = {
    total: Object.values(each).reduce(
      (acc, one) => ({ min: acc.min + one.min, gzip: acc.gzip + one.gzip }),
      { min: 0, gzip: 0 },
    ),
    files: each,
  };
  const nextCss = assets
    .filter((asset) => asset.endsWith(".css"))
    .map((asset) => readFileSync(join(widget, ".next", asset), "utf-8"))
    .join("\n");
  result.css.next = size(Buffer.from(nextCss, "utf-8"));
  if (typeof elementCss === "string") {
    result.css.nextVsElement = compareInventories(inventory(elementCss), inventory(nextCss));
    result.css.nextHasProperty = /@property\s+--tw-/.test(nextCss);
    result.css.nextThemeSelectors = anatomy(nextCss).themeSelectors;
  }
}

// ---------- 빌드 산출물이 남은 채로 판정 ----------
const eslint = join(dirname(fromWeb.resolve("eslint/package.json")), "bin", "eslint.js");
const lint = spawnSync(
  process.execPath,
  [eslint, "--max-warnings", "0", "--format", "json", "apps/widget"],
  { cwd: web, encoding: "utf-8", maxBuffer: 1 << 28 },
);
const reports = lint.stdout.trim() === "" ? [] : JSON.parse(lint.stdout);
result.afterBuild.eslint = {
  status: lint.status,
  files: reports
    .filter((report) => report.messages.length > 0)
    .map((report) => ({
      file: relative(web, report.filePath).split(sep).join("/"),
      count: report.messages.length,
      rules: [
        ...new Set(report.messages.map((message) => message.ruleId ?? message.message)),
      ].slice(0, 6),
    })),
};
const prettier = join(dirname(fromWeb.resolve("prettier/package.json")), "bin", "prettier.cjs");
const format = spawnSync(
  process.execPath,
  [
    prettier,
    "--check",
    "apps/widget",
    "--ignore-path",
    "../.gitignore",
    "--ignore-path",
    ".prettierignore",
  ],
  { cwd: web, encoding: "utf-8" },
);
result.afterBuild.prettier = {
  status: format.status,
  flagged: `${format.stdout}${format.stderr}`
    .replace(/\u001b\[\d+m/g, "")
    .split(/\r?\n/)
    .filter((line) => line.includes("[warn]") && !line.includes("Code style issues"))
    .map((line) => line.replace(/.*\[warn\]\s*/, "")),
};
result.distExists = existsSync(join(widget, "dist"));

writeFileSync(join(ws, "measure.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
const failed = Object.entries(result.builds).filter(([, build]) => build.status !== 0);
process.exitCode = failed.length > 0 ? 1 : 0;
