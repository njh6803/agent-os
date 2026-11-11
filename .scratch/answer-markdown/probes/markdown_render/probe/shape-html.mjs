// 모양 프로브가 HTML 을 견주는 방식. 기대(shape-cases.mjs)와 실제(shape.mjs)가 같은 함수로 글을 만든다.
//
// - 실제: `renderToStaticMarkup` 의 HTML 을 parse5 로 읽어 `div[data-answer="markdown"]` 의 안쪽을 다시 글로 쓴다
//   (`normalize`). 속성은 이름 차례로 쓰고, 블록 사이의 줄 끝 글자는 뺀다.
// - 기대: 같은 `el` 로 지은 글이다. 글자는 `&`, `<`, `>` 만 엔티티로 쓴다.
//
// 블록 사이의 줄 끝 글자: mdast-util-to-hast 는 블록 요소 사이(와 블록을 품는 요소의 처음·끝)에 `"\n"` 글자 노드를
// 끼운다. 화면에는 보이지 않으므로(보통의 `white-space` 에서) 견줄 때 뺀다. 얼마나 뺐는지는 `structuralNewlines` 로
// 세어 돌려준다. (가)의 CSS 후보가 그 수를 쓴다. 문단 안의 줄 끝 글자(한 줄 바꿈)와 `<br>` 뒤의 줄 끝 글자는 빼지 않는다.
import { parseFragment } from "parse5";

const VOID = new Set(["br", "hr"]);
/** 자식으로 블록을 품는 요소. 이 요소 바로 아래의 줄 끝 글자만 "블록 사이"로 본다. */
const BLOCK_PARENTS = new Set(["div", "blockquote", "ul", "ol", "li", "table", "thead", "tbody", "tr"]);
const BLOCKS = new Set([
  "p", "div", "blockquote", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "pre", "hr",
  "h1", "h2", "h3", "h4", "h5", "h6",
]);

export const escText = (value) => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const escAttr = (value) => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;");

/** 요소 하나를 글로 쓴다. `inner` 는 이미 글로 쓴 자식이다. */
export function el(tag, attrs = {}, inner = "") {
  const head = Object.keys(attrs)
    .sort()
    .map((name) => ` ${name}="${escAttr(attrs[name])}"`)
    .join("");
  return VOID.has(tag) ? `<${tag}${head}>` : `<${tag}${head}>${inner}</${tag}>`;
}

const isBlockOrEdge = (node) => node === undefined || (node.tagName !== undefined && BLOCKS.has(node.tagName));

function write(node, counter) {
  if (node.nodeName === "#text") return escText(node.value);
  const attrs = Object.fromEntries(node.attrs.map((a) => [a.name, a.value]));
  return el(node.tagName, attrs, writeChildren(node, counter));
}

function writeChildren(parent, counter) {
  const children = parent.childNodes ?? [];
  const blockParent = BLOCK_PARENTS.has(parent.tagName);
  let out = "";
  children.forEach((child, index) => {
    if (child.nodeName !== "#text" || !blockParent) {
      out += write(child, counter);
      return;
    }
    let value = child.value;
    if (value.startsWith("\n") && isBlockOrEdge(children[index - 1])) {
      value = value.slice(1);
      counter.structuralNewlines += 1;
    }
    if (value.endsWith("\n") && isBlockOrEdge(children[index + 1])) {
      value = value.slice(0, -1);
      counter.structuralNewlines += 1;
    }
    out += escText(value);
  });
  return out;
}

function find(node, test) {
  if (test(node)) return node;
  for (const child of node.childNodes ?? []) {
    const found = find(child, test);
    if (found !== null) return found;
  }
  return null;
}

/**
 * 그린 HTML 에서 답의 안쪽을 견줄 글로 바꾼다. 답의 칸(`div[data-answer="markdown"]`)이 없으면 null 이다.
 * @returns {{ html: string, structuralNewlines: number, softNewlines: number, br: number } | null}
 */
export function normalize(rendered) {
  const box = find(
    parseFragment(rendered),
    (node) => node.tagName === "div" && (node.attrs ?? []).some((a) => a.name === "data-answer" && a.value === "markdown"),
  );
  if (box === null) return null;
  const counter = { structuralNewlines: 0 };
  const html = writeChildren(box, counter);
  return {
    html,
    structuralNewlines: counter.structuralNewlines,
    // 블록 사이의 것을 뺀 뒤에 남은 줄 끝 글자 가운데 `<br>` 바로 뒤가 아니고 코드 블록 안도 아닌 것.
    softNewlines: countSoftNewlines(box),
    br: (html.match(/<br>/g) ?? []).length,
  };
}

/** 문단처럼 줄 안 내용을 든 요소 안에 남은 줄 끝 글자의 수(`pre` 안과 `<br>` 바로 뒤는 뺀다). */
function countSoftNewlines(box) {
  let count = 0;
  const walk = (parent, inPre) => {
    const children = parent.childNodes ?? [];
    children.forEach((child, index) => {
      if (child.nodeName !== "#text") {
        walk(child, inPre || child.tagName === "pre");
        return;
      }
      if (inPre) return;
      let value = child.value;
      if (BLOCK_PARENTS.has(parent.tagName)) {
        if (value.startsWith("\n") && isBlockOrEdge(children[index - 1])) value = value.slice(1);
        if (value.endsWith("\n") && isBlockOrEdge(children[index + 1])) value = value.slice(0, -1);
      }
      if (value.startsWith("\n") && children[index - 1]?.tagName === "br") value = value.slice(1);
      count += (value.match(/\n/g) ?? []).length;
    });
  };
  walk(box, false);
  return count;
}

/** 요소의 종류와 차례만 남긴 모양(글자와 속성은 버린다). 화면 파일의 구조와 견줄 때 쓴다. */
export function skeleton(node) {
  return (node.childNodes ?? [])
    .filter((child) => child.tagName !== undefined)
    .map((child) => {
      const inner = skeleton(child);
      return inner === "" ? child.tagName : `${child.tagName}(${inner})`;
    })
    .join(" ");
}

/** 요소 아래의 글자를 이어 붙이고 공백을 하나로 줄인다. */
export function plainText(node) {
  const textOf = (n) => (n.nodeName === "#text" ? n.value : (n.childNodes ?? []).map(textOf).join(""));
  return textOf(node).replace(/\s+/g, " ").trim();
}

export { find };

// ── 기대를 짓는 도우미 ──────────────────────────────────────────────────────────────────────────────────────────
/** 변환이 낸 줄바꿈. mdast-util-to-hast 는 `break` 를 `<br>` 과 줄 끝 글자로 낸다. */
export const BR = "<br>\n";
export const p = (inner) => el("p", {}, inner);
export const strong = (inner) => el("strong", {}, inner);
export const em = (inner) => el("em", {}, inner);
export const code = (inner) => el("code", {}, inner);
export const a = (href, inner) =>
  el("a", { href, target: "_blank", rel: "noopener noreferrer" }, inner + el("span", { class: "sr-only" }, "(새 탭에서 열림)"));
export const sup = (n) => el("sup", { "data-cite": "" }, String(n));
export const img = (alt) => el("span", { class: "img-alt" }, alt === "" ? "이미지" : `이미지: ${alt}`);
export const pre = (inner, lang) =>
  el("pre", { tabindex: "0" }, el("code", lang === undefined ? {} : { class: `language-${lang}` }, inner));
export const li = (inner) => el("li", {}, inner);
export const ul = (...items) => el("ul", {}, items.map(li).join(""));
export const ol = (...items) => el("ol", {}, items.map(li).join(""));
export const bq = (inner) => el("blockquote", {}, inner);
export const sources = (inner) => el("div", { class: "sources" }, inner);
export const table = (head, rows) =>
  el(
    "div",
    { class: "tbl", role: "region", "aria-label": "표", tabindex: "0" },
    el(
      "table",
      {},
      el("thead", {}, el("tr", {}, head.map((cell) => el("th", {}, cell)).join(""))) +
        el("tbody", {}, rows.map((row) => el("tr", {}, row.map((cell) => el("td", {}, cell)).join(""))).join("")),
    ),
  );
