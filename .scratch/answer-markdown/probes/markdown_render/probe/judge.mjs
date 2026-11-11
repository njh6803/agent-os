// 렌더 판정기. `renderToStaticMarkup` 이 낸 HTML 글을 parse5 로 읽어(브라우저와 같은 파서 규격) 요소·링크·속성·글자를
// 내고, 제한을 건 출력이라면 하나도 없어야 하는 것(R1~R5)을 찾는다.
//
// render.mjs 에 있던 것을 그대로 옮겼다(2026-11-11). render.mjs 는 불러오면 측정을 시작하므로, 새 프로브(shape.mjs,
// textcompare.mjs)가 같은 판정기를 쓰려면 따로 떼어야 했다. 규칙의 글은 바꾸지 않았다.
import { parseFragment } from "parse5";

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

/** 판정기 자가 시험. 손으로 쓴 나쁜 HTML 에서 규칙마다 걸리는지 본다. 틀린 것의 목록을 낸다(비면 통과). */
export function selfTest() {
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
