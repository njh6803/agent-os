// 렌더 프로브(B3). 후보 × 방식(제한/기본) × 입력마다 `renderToStaticMarkup` 의 HTML 을 파일로 남기고 판정한다.
//
// 돌리기: node probe/render.mjs      (md-probe 폴더 밖에서는 절대 경로로)
// 산출물: out/render/<후보>/<방식>/<사례>.html, out/render/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 판정
// - 모든 제한 회차에 거는 규칙(R1~R5): 금지 요소, 이벤트 속성, 링크의 주소·target·rel, 속성에 든 위험한 주소,
//   링크가 아닌 요소의 주소 속성. HTML 은 글자 비교가 아니라 parse5 로 읽은 나무에서 본다(브라우저와 같은 파서 규격).
// - 사례마다의 기대(cases.mjs 의 must)와 관찰(watch).
// - 기본 방식은 대조군이다. 실패로 세지 않고 "제한을 걸지 않으면 무엇이 나오는가"를 적는다.
//
// 측정이 아닌 회차를 따로 센다(.claude/rules/probes.md)
// - 그리다 던진 회차, 표지(`div[data-probe]`)가 없는 회차는 측정이 아니다. 하나라도 있으면 종료 코드 1.
// - 판정기 자가 시험: 손으로 쓴 나쁜 HTML 에서 규칙마다 걸리는지 먼저 본다. 안 걸리면 종료 코드 2.
// - 양성 대조: 기본 방식의 react-markdown 이 추적 이미지 입력에서 실제로 `img[src*=evil.example]` 를 내는지 본다.
//   내지 않으면 "제한한 쪽에 img 가 없다"는 아무것도 재지 못한 것이다. 종료 코드 3.
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { parseFragment } from "parse5";
import { CASES } from "./cases.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "render");
const BUNDLE = join(ROOT, "out", "build", "render-entry.cjs");

const FORBIDDEN_TAGS = new Set([
  "img", "script", "iframe", "style", "svg", "math", "object", "embed", "form", "input", "button", "textarea",
  "select", "link", "meta", "base", "video", "audio", "source", "picture", "track", "frame", "frameset", "applet",
  "details", "summary", "dialog", "template", "slot", "portal", "marquee", "noscript",
]);
const URL_ATTRS = new Set([
  "src", "srcset", "action", "formaction", "poster", "background", "data", "ping", "xlink:href", "cite", "longdesc",
  "manifest", "codebase", "usemap", "icon",
]);
const DANGEROUS_VALUE = /evil\.example|javascript:|vbscript:|data:|blob:|file:/i;

/** HTML 글을 읽어 요소 수, 링크, 속성, 글자를 낸다. */
export function analyze(html) {
  const tags = {};
  const anchors = [];
  const attrs = [];
  let text = "";
  const textOf = (node) =>
    node.nodeName === "#text" ? node.value : (node.childNodes ?? []).map(textOf).join("");
  const walk = (node) => {
    if (node.nodeName === "#text") {
      text += node.value;
      return;
    }
    if (node.tagName !== undefined) {
      tags[node.tagName] = (tags[node.tagName] ?? 0) + 1;
      const own = Object.fromEntries(node.attrs.map((a) => [a.name, a.value]));
      for (const a of node.attrs) attrs.push({ tag: node.tagName, name: a.name, value: a.value });
      if (node.tagName === "a") {
        anchors.push({ href: own.href ?? null, target: own.target ?? null, rel: own.rel ?? null, text: textOf(node) });
      }
    }
    for (const child of node.childNodes ?? []) walk(child);
    if (node.content !== undefined) walk(node.content);
  };
  walk(parseFragment(html));
  return { tags, anchors, attrs, text };
}

/** 제한을 건 출력이라면 하나도 없어야 하는 것. */
export function violations(r) {
  const found = [];
  for (const tag of Object.keys(r.tags)) {
    if (FORBIDDEN_TAGS.has(tag)) found.push({ rule: "R1-forbidden-tag", detail: tag });
  }
  for (const a of r.attrs) {
    if (/^on/i.test(a.name)) found.push({ rule: "R2-event-attr", detail: `${a.tag}[${a.name}]` });
    // 링크의 href 는 R3 이 스킴으로 본다. http(s) 링크는 어느 호스트로든 허용이라(눌러야 간다) 여기서 빼고,
    // 나머지 속성에 위험한 스킴이나 추적 호스트가 들면 잡는다(누르지 않아도 요청이 나갈 수 있는 자리).
    if (!(a.tag === "a" && a.name === "href") && DANGEROUS_VALUE.test(a.value)) {
      found.push({ rule: "R4-dangerous-attr-value", detail: `${a.tag}[${a.name}=${a.value}]` });
    }
    if (URL_ATTRS.has(a.name.toLowerCase())) found.push({ rule: "R5-url-attr", detail: `${a.tag}[${a.name}=${a.value}]` });
    if (a.name === "href" && a.tag !== "a") found.push({ rule: "R5-url-attr", detail: `${a.tag}[href=${a.value}]` });
  }
  for (const a of r.anchors) {
    const rel = new Set((a.rel ?? "").split(/\s+/));
    if (a.href === null || !/^https?:\/\//.test(a.href)) found.push({ rule: "R3-anchor-href", detail: String(a.href) });
    if (a.target !== "_blank") found.push({ rule: "R3-anchor-target", detail: String(a.target) });
    if (!rel.has("noopener") || !rel.has("noreferrer")) found.push({ rule: "R3-anchor-rel", detail: String(a.rel) });
  }
  return found;
}

function selfTest() {
  const samples = [
    ['<div data-probe="x"><img src="https://evil.example/p.png"></div>', ["R1-forbidden-tag", "R4-dangerous-attr-value", "R5-url-attr"]],
    ['<a href="javascript:alert(1)" target="_blank" rel="noopener noreferrer">x</a>', ["R3-anchor-href"]],
    ['<a href="https://a.example/" title="javascript:alert(1)" target="_blank" rel="noopener noreferrer">x</a>', ["R4-dangerous-attr-value"]],
    ['<link rel="preload" as="image" href="https://evil.example/p.png"/><div data-probe="x"><p>x</p></div>', ["R1-forbidden-tag", "R4-dangerous-attr-value", "R5-url-attr"]],
    ['<a href="https://a.example/">x</a>', ["R3-anchor-target", "R3-anchor-rel"]],
    ['<a href="/admin" target="_blank" rel="noopener noreferrer">x</a>', ["R3-anchor-href"]],
    ['<p onclick="alert(1)">x</p>', ["R2-event-attr"]],
    ["<p>a</p><script>alert(1)</script>", ["R1-forbidden-tag"]],
    ['<ul><li><input type="checkbox" disabled=""> x</li></ul>', ["R1-forbidden-tag"]],
    ['<blockquote cite="https://a.example/">x</blockquote>', ["R5-url-attr"]],
    ['<p>&lt;img src=x onerror=alert(1)&gt; javascript:alert(1)</p><a href="https://www.law.go.kr/" target="_blank" rel="noopener noreferrer">정상</a>', []],
  ];
  const wrong = [];
  for (const [html, expected] of samples) {
    const got = [...new Set(violations(analyze(html)).map((v) => v.rule))].sort();
    if (JSON.stringify(got) !== JSON.stringify([...expected].sort())) wrong.push({ html, expected, got });
  }
  return wrong;
}

const fileName = (id) => `${id}.html`;

async function main() {
  const wrong = selfTest();
  if (wrong.length > 0) {
    console.error("판정기 자가 시험이 틀렸다", JSON.stringify(wrong, null, 2));
    process.exit(2);
  }

  mkdirSync(dirname(BUNDLE), { recursive: true });
  await build({
    entryPoints: [join(ROOT, "probe", "entry.tsx")],
    outfile: BUNDLE,
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    define: { "process.env.NODE_ENV": '"development"' },
    logLevel: "warning",
  });
  const entry = createRequire(import.meta.url)(BUNDLE);

  rmSync(OUT, { recursive: true, force: true });
  const rounds = [];
  const notMeasured = [];
  // React 의 개발 경고(key 누락, 알 수 없는 속성 등)를 회차마다 모은다.
  const original = console.error;
  for (const candidate of entry.CANDIDATES) {
    for (const mode of entry.MODES) {
      mkdirSync(join(OUT, candidate, mode), { recursive: true });
      for (const item of CASES) {
        const warnings = [];
        console.error = (...args) => warnings.push(args.map(String).join(" ").slice(0, 300));
        let html;
        try {
          html = entry.render(candidate, mode, item.id, item.input);
        } catch (error) {
          notMeasured.push({ candidate, mode, id: item.id, reason: `던졌다: ${String(error)}` });
          continue;
        } finally {
          console.error = original;
        }
        writeFileSync(join(OUT, candidate, mode, fileName(item.id)), html);
        // React 19 의 서버 렌더는 `img` 를 만나면 `<link rel="preload" as="image">` 를 맨 앞으로 끌어올린다. 그래서
        // 표지는 "맨 앞"이 아니라 "있다"로 보고, 표지 앞에 온 것은 `hoisted` 로 적는다(판정은 HTML 전체에 건다).
        const marker = `<div data-probe="${item.id}">`;
        const at = html.indexOf(marker);
        if (at < 0 || !html.endsWith("</div>")) {
          notMeasured.push({ candidate, mode, id: item.id, reason: "표지가 없다" });
          continue;
        }
        const r = analyze(html);
        rounds.push({
          candidate,
          mode,
          id: item.id,
          group: item.group,
          input: item.input,
          html,
          hoisted: html.slice(0, at),
          violations: violations(r),
          mustFailures: item.must(r),
          watch: item.watch(r),
          tags: r.tags,
          anchors: r.anchors,
          reactWarnings: warnings,
        });
      }
    }
  }

  const find = (candidate, mode, id) => rounds.find((x) => x.candidate === candidate && x.mode === mode && x.id === id);
  const controls = [];
  const control = (name, ok) => controls.push({ name, ok });
  const rmDefaultImage = find("react-markdown", "default", "r05-tracking-image");
  control(
    "react-markdown 기본 방식은 추적 이미지를 img 로 그린다",
    rmDefaultImage !== undefined && rmDefaultImage.violations.some((v) => v.rule === "R1-forbidden-tag" && v.detail === "img") && rmDefaultImage.html.includes("evil.example"),
  );
  const mjDefaultImage = find("markdown-to-jsx", "default", "r05-tracking-image");
  control(
    "markdown-to-jsx 기본 방식은 추적 이미지를 img 로 그린다",
    mjDefaultImage !== undefined && mjDefaultImage.violations.some((v) => v.rule === "R1-forbidden-tag" && v.detail === "img") && mjDefaultImage.html.includes("evil.example"),
  );
  for (const candidate of entry.CANDIDATES) {
    const link = find(candidate, "default", "r06-normal-link");
    control(
      `${candidate} 기본 방식의 링크에는 target 이 없다`,
      link !== undefined && link.anchors.length === 1 && link.anchors[0].target === null,
    );
  }

  const summary = {};
  for (const candidate of entry.CANDIDATES) {
    summary[candidate] = {};
    for (const mode of entry.MODES) {
      const mine = rounds.filter((x) => x.candidate === candidate && x.mode === mode);
      summary[candidate][mode] = {
        rounds: mine.length,
        withViolations: mine.filter((x) => x.violations.length > 0).map((x) => x.id),
        withMustFailures: mine.filter((x) => x.mustFailures.length > 0).map((x) => x.id),
        withReactWarnings: mine.filter((x) => x.reactWarnings.length > 0).map((x) => x.id),
      };
    }
  }

  writeFileSync(
    join(OUT, "summary.json"),
    JSON.stringify({ cases: CASES.length, notMeasured, controls, summary, rounds }, null, 2),
  );

  const failedControls = controls.filter((c) => !c.ok);
  console.log(
    JSON.stringify({
      probe: "render",
      cases: CASES.length,
      expectedRounds: CASES.length * entry.CANDIDATES.length * entry.MODES.length,
      measuredRounds: rounds.length,
      notMeasured: notMeasured.length,
      failedControls: failedControls.map((c) => c.name),
      summary,
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
  if (failedControls.length > 0) process.exit(3);
}

await main();
