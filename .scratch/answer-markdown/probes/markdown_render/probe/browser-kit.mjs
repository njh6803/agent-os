// 브라우저 프로브(browser.mjs, axe.mjs)가 함께 쓰는 도구. 묶기, 스택의 줄을 모듈로 옮기기, 페이지의 글, Chromium 찾기.
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { chromium } from "playwright";

export const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

/**
 * 입구를 최소화하지 않고 묶는다(스택의 함수 이름과 줄을 읽으려는 것이다). React 는 production 으로 품는다.
 * `mustBundle` 의 조각이 묶인 파일 경로에 모두 있고 `.development.js` 가 하나도 없어야 한다. 어긋나면 `problems` 에 적는다.
 */
export async function bundle({ entry, outfile, format, platform, globalName, mustBundle }) {
  mkdirSync(dirname(outfile), { recursive: true });
  const result = await build({
    entryPoints: [entry],
    outfile,
    bundle: true,
    format,
    platform,
    target: "es2022",
    jsx: "automatic",
    ...(globalName === undefined ? {} : { globalName }),
    define: { "process.env.NODE_ENV": '"production"' },
    minify: false,
    legalComments: "none",
    charset: "utf8",
    absWorkingDir: ROOT,
    metafile: true,
    logLevel: "warning",
  });
  const inputs = Object.keys(result.metafile.inputs).map((path) => path.replaceAll("\\", "/"));
  const problems = [];
  for (const piece of mustBundle) {
    if (!inputs.some((path) => path.includes(piece))) problems.push(`${piece} 가 묶이지 않았다`);
  }
  const development = inputs.filter((path) => path.endsWith(".development.js"));
  if (development.length > 0) problems.push(`development 빌드가 묶였다: ${development.join(", ")}`);
  const text = readFileSync(outfile, "utf8");
  if (/\bprocess\.env\.NODE_ENV\b/.test(text)) problems.push("process.env.NODE_ENV 가 남았다");
  return { outfile, text, index: moduleIndex(text), problems };
}

/** esbuild 가 모듈마다 앞에 두는 `// 경로` 줄을 모은다. 줄 번호는 1 부터다. */
export function moduleIndex(text) {
  const index = [];
  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i += 1) {
    const match = /^\s*\/\/ ((?:node_modules|apps|probe)\/\S+)\s*$/.exec(lines[i]);
    if (match !== null) index.push({ line: i + 1, path: match[1] });
  }
  return index;
}

/** 경로에서 패키지 이름을 낸다. node_modules 밖은 "(own) 경로" 다. */
export function packageOf(path) {
  const at = path.lastIndexOf("node_modules/");
  if (at < 0) return `(own) ${path}`;
  const parts = path.slice(at + "node_modules/".length).split("/");
  return parts[0].startsWith("@") ? `${parts[0]}/${parts[1]}` : parts[0];
}

function locate(index, line) {
  let found = null;
  for (const entry of index) {
    if (entry.line > line) break;
    found = entry.path;
  }
  return found;
}

/**
 * 오류의 스택에서 묶음 파일의 프레임을 위에서부터 꺼내, 함수 이름과 그 줄이 든 패키지로 옮긴다.
 * 이웃한 같은 프레임(함수와 패키지가 같은 것)은 하나로 줄인다.
 */
export function framesOf(stack, made) {
  const file = basename(made.outfile);
  const frames = [];
  for (const line of stack.split("\n")) {
    const match = /^\s*at (?:(.*?) \()?(.*?):(\d+):(\d+)\)?\s*$/.exec(line);
    if (match === null || !match[2].replaceAll("\\", "/").endsWith(file)) continue;
    const path = locate(made.index, Number(match[3]));
    const frame = { fn: match[1] ?? "(이름 없음)", pkg: path === null ? "(모름)" : packageOf(path) };
    const last = frames.at(-1);
    if (last === undefined || last.fn !== frame.fn || last.pkg !== frame.pkg) frames.push(frame);
  }
  return frames;
}

// 패키지를 단계로 옮기는 표. 스택 위쪽 프레임의 패키지로 "어느 단계에서 던졌나"를 가른다.
// mdast-util-find-and-replace 는 GFM 의 글자 그대로의 주소 찾기(mdast-util-gfm-autolink-literal)가 파싱의 끝에 나무를
// 한 번 더 도는 데 쓴다. 그래서 파싱이다. react-markdown 의 프레임은 허용 목록 거르기의 방문 함수(`transform`)다.
const STAGE_OF_PACKAGE = [
  [/^(micromark|mdast-util-from-markdown|mdast-util-gfm|mdast-util-find-and-replace|mdast-util-to-string|remark-parse|decode-named-character-reference)/, "파싱"],
  [/^\(own\) apps\/widget\/lib\/answer-markdown/, "직접 짠 변환"],
  [/^(mdast-util-to-hast|remark-rehype|unist-util-position|trim-lines)/, "mdast→hast 변환"],
  [/^react-markdown$/, "허용 목록 거르기"],
  [/^(hast-util-to-jsx-runtime|property-information|style-to-object|style-to-js|hast-util-whitespace|comma-separated-tokens|space-separated-tokens)/, "JSX로 바꾸기"],
  [/^(react-dom|scheduler)$/, "React의 렌더"],
  [/^react$/, "JSX로 바꾸기"],
];

// 나무를 도는 도우미. 파싱(주소 찾기)과 허용 목록 거르기가 함께 써서, 이 패키지의 프레임만으로는 단계를 가를 수 없다.
const TREE_HELPERS = /^(unist-util-visit|unist-util-visit-parents|unist-util-is)$/;

export function stageOfPackage(pkg) {
  for (const [pattern, stage] of STAGE_OF_PACKAGE) {
    if (pattern.test(pkg)) return stage;
  }
  return null;
}

/**
 * 표지(`reached`)와 스택으로 던진 단계를 정한다. 둘이 어긋나면 `agree` 가 false 다(그 회차는 단계를 가른 것이 아니다).
 * 표지로는 넷까지만 가른다: 파싱, 직접 짠 변환, mdast→hast 변환, 그 뒤(허용 목록 거르기나 JSX 로 바꾸기).
 * 스택으로는 나무를 도는 도우미가 아닌 첫 프레임의 패키지를 본다. 받은 프레임이 모두 도우미면(`helperOnly`) 표지를
 * 따르되, 표지가 "그 뒤"면 허용 목록 거르기다(JSX 로 바꾸기는 그 도우미를 쓰지 않는다).
 */
export function stageOfThrow(reached, frames) {
  const byMarker = !reached.includes("parsed")
    ? ["파싱"]
    : !reached.includes("own-done")
      ? ["직접 짠 변환"]
      : !reached.includes("hast-done")
        ? ["mdast→hast 변환"]
        : ["허용 목록 거르기", "JSX로 바꾸기"];
  const telling = frames.find((frame) => !TREE_HELPERS.test(frame.pkg));
  const helperOnly = frames.length > 0 && telling === undefined;
  const byStack =
    telling !== undefined ? stageOfPackage(telling.pkg) : helperOnly ? (byMarker.length === 1 ? byMarker[0] : "허용 목록 거르기") : null;
  return { stage: byStack, byMarker, helperOnly, agree: byStack !== null && byMarker.includes(byStack) };
}

// 디자인 토큰의 값. web/packages/ui/src/styles/theme.css 에서 읽어 옮겼다(기본 테마 녹청의 라이트와 다크, 보통 밀도).
const TOKENS = [
  ':root{--sans:"Noto Sans KR",system-ui,sans-serif;--mono:"Noto Sans Mono",ui-monospace,monospace;',
  "--body-size:15px;--body-lh:22px;--table-size:14px;--table-lh:20px;--mono-size:14px;",
  "--spacing-1:4px;--spacing-2:8px;--spacing-3:12px;--spacing-4:16px;--spacing-6:24px;",
  "--radius-s:4px;--radius-l:12px;--font-weight-semibold:600;--text-small:12px;--text-small--line-height:16px}",
  '[data-mode="light"]{--bg:#f4f8fb;--bg-raised:#ffffff;--text:#171a1c;--text-muted:#606466;--border:#e1e5e8;',
  "--border-control:#898d8f;--accent:#056868;--focus-ring:#056868}",
  '[data-mode="dark"]{--bg:#0f1214;--bg-raised:#171a1c;--text:#ecf1f3;--text-muted:#9b9fa1;--border:#2b2e30;',
  "--border-control:#898d8f;--accent:#5caeae;--focus-ring:#5caeae}",
].join("");

// `.md` 의 모양. 화면 파일(.scratch/answer-markdown/design/mk-all-320, mk-cite-320, mk-unsafe-320 의 <style>)에서 옮겼다.
const MD_CSS = [
  ".sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}",
  ".md{min-width:0;font-size:var(--body-size);line-height:var(--body-lh);color:var(--text);overflow-wrap:anywhere}",
  ".md>*{margin:0}",
  ".md>*+*{margin-top:var(--spacing-3)}",
  ".md h1,.md h2,.md h3,.md h4,.md h5,.md h6{font-size:var(--body-size);line-height:var(--body-lh);font-weight:var(--font-weight-semibold)}",
  ".md>:is(h1,h2,h3,h4,h5,h6)+*{margin-top:var(--spacing-1)}",
  ".md>*+:is(h1,h2,h3,h4,h5,h6){margin-top:var(--spacing-4)}",
  ".md strong{font-weight:var(--font-weight-semibold)}",
  ".md ul,.md ol{padding-left:var(--spacing-6)}",
  ".md ul{list-style:disc}",
  ".md ul ul{list-style:circle}",
  ".md li+li,.md li>ul,.md li>ol{margin-top:var(--spacing-1)}",
  ".md blockquote{padding-left:var(--spacing-3);border-left:2px solid var(--border-control)}",
  ".md blockquote>*{margin:0}",
  ".md code{font-family:var(--mono);font-size:var(--mono-size);background:var(--bg);border-radius:var(--radius-s);padding:0 var(--spacing-1)}",
  ".md pre{padding:var(--spacing-3);background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-s);font-family:var(--mono);font-size:var(--mono-size);line-height:var(--table-lh);overflow-x:auto}",
  ".md pre code{padding:0;background:none;border-radius:0}",
  ".md a{color:var(--accent);text-decoration:underline}",
  ".md hr{height:0;border:0;border-top:1px solid var(--border)}",
  ".md .tbl{overflow-x:auto}",
  ".md table{border-collapse:collapse;font-size:var(--table-size);line-height:var(--table-lh)}",
  ".md th{font-weight:var(--font-weight-semibold);text-align:left}",
  ".md th,.md td{padding:var(--spacing-2) var(--spacing-3);vertical-align:top;border-bottom:1px solid var(--border);min-width:96px;max-width:256px}",
  ".md tr>:first-child{padding-left:0}",
  ".md tbody tr:last-child>*{border-bottom:0}",
  ".md sup{font-size:var(--text-small);line-height:0;color:var(--text-muted);margin-left:2px}",
  ".md .sources{padding-top:var(--spacing-3);border-top:1px solid var(--border);font-size:var(--text-small);line-height:var(--text-small--line-height);color:var(--text-muted)}",
  ".md .sources>*{margin:0}",
  ".md .sources>*+*{margin-top:var(--spacing-1)}",
  ".md .sources li+li{margin-top:0}",
  ".md .img-alt{color:var(--text-muted)}",
].join("\n");

// 프로브가 더한 것. 위젯 칸의 틀(폭 320px, 테두리 1px, 안쪽 여백 16px)과 원문을 보이는 문단이다. 칸은 넘치는 것을
// 자르지 않는다(자르면 문서의 scrollWidth 로 넘침을 볼 수 없다).
const FRAME_CSS = [
  "html,body{margin:0}",
  "body{background:var(--bg);color:var(--text);font-family:var(--sans)}",
  "#widget{width:320px;box-sizing:border-box;background:var(--bg-raised);color:var(--text);border:1px solid var(--border)}",
  "#talk{margin:0;padding:var(--spacing-4);list-style:none}",
  ".raw{margin:0;font-size:var(--body-size);line-height:var(--body-lh);white-space:pre-wrap;overflow-wrap:anywhere}",
].join("\n");

/**
 * 페이지의 글. 위젯 칸 안에 대화 목록과 항목 하나를 두고, 그 항목 안의 `#host` 에 시제품을 그린다.
 * `conversation` 이 "region" 이면 목록을 `div[role=region][aria-label=대화][tabindex=0]` 으로 감싼다(접근성 검사가
 * 쓰는 바깥 구조). "list" 면 화면 파일처럼 `ol[aria-label=대화]` 만 둔다.
 */
export function pageHtml({ mode = "light", extraCss = "", conversation = "list" } = {}) {
  const list =
    conversation === "region"
      ? '<div role="region" aria-label="대화" tabindex="0"><ol id="talk"><li><span class="sr-only">출력: </span><div id="host"></div></li></ol></div>'
      : '<ol id="talk" aria-label="대화"><li><span class="sr-only">출력: </span><div id="host"></div></li></ol>';
  return [
    "<!doctype html>",
    `<html lang="ko" data-mode="${mode}">`,
    '<head><meta charset="utf-8"><title>답의 마크다운 표시 프로브</title>',
    `<style>${TOKENS}\n${MD_CSS}\n${FRAME_CSS}\n${extraCss}</style></head>`,
    `<body><main><h1 class="sr-only">프로브</h1><div id="widget">${list}</div></main></body></html>`,
  ].join("\n");
}

/** 이미 내려받아져 있는 Chromium 의 경로. 없으면 null 이다(내려받지 않는다). */
export function chromiumPath() {
  const path = chromium.executablePath();
  return existsSync(path) ? path : null;
}

/** 약속을 제한 시간과 겨룬다. 던지거나 시간이 지나도 예외로 끝내지 않고 결과로 돌려준다. */
export async function settle(promise, ms) {
  let timer;
  const timeout = new Promise((resolve) => {
    timer = setTimeout(() => resolve({ timedOut: true }), ms);
  });
  const run = promise.then(
    (value) => ({ value }),
    (error) => ({ error: String(error).slice(0, 300) }),
  );
  const result = await Promise.race([run, timeout]);
  clearTimeout(timer);
  return result;
}

/** 페이지를 열고 콘솔·페이지 오류·크래시를 받아 적는다. `events` 는 살아 있는 배열이다. */
export async function openPage(browser, html, script) {
  const context = await browser.newContext({ viewport: { width: 320, height: 640 } });
  const page = await context.newPage();
  const events = { console: [], pageErrors: [], crashed: false };
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") {
      events.console.push({ type: message.type(), text: message.text().slice(0, 300) });
    }
  });
  page.on("pageerror", (error) => {
    events.pageErrors.push({ name: error.name, message: error.message.slice(0, 200) });
  });
  page.on("crash", () => {
    events.crashed = true;
  });
  await page.setContent(html);
  await page.addScriptTag({ path: script });
  return { context, page, events };
}

export function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export const PLAYWRIGHT_VERSION = readJson(join(ROOT, "node_modules", "playwright", "package.json")).version;
