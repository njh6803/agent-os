// 마크다운 부품의 단위 시험이 그린 DOM 을 견주는 방식(answer-markdown 명세 "부품의 단위 시험"). 시험은 바깥 행동만 본다. 그래서
// 그린 DOM 을 "요소의 종류와 차례, 글, 링크의 주소와 속성"만 남긴 글(뼈대)로 바꾸고, 기대도 같은 `el` 로 지은 글과 맞댄다.
// 클래스 이름은 뼈대에 들지 않는다(모양은 사진 비교와 스토리 테스트가 본다).
//
// 뼈대에 드는 속성은 `SHOWN` 뿐이다. 링크의 `href`·`target`·`rel`, 번호 목록의 `start`, 표의 스크롤 칸과 코드 블록의
// 접근성 속성(`role`·`aria-label`·`tabindex`)이다.
//
// 블록 사이의 줄 끝 글자: mdast-util-to-hast 는 블록 요소 사이(와 블록을 품는 요소의 처음·끝)에 `"\n"` 글자 노드를 끼운다.
// 화면에는 보이지 않으므로 견줄 때 뺀다. `<br>` 바로 뒤의 줄 끝 글자도 뺀다(`br` 가 이미 줄을 바꾼다). 문단 안의 줄 끝 글자는
// 뺀 뒤에도 남으면 그대로 견준다(부품이 한 줄 바꿈을 `br` 로 바꾸므로 보통은 남지 않는다).

const VOID = new Set(["br", "hr"]);
/** 자식으로 블록을 품는 요소. 이 요소 바로 아래의 줄 끝 글자만 "블록 사이"로 본다. */
const BLOCK_PARENTS = new Set([
  "div",
  "blockquote",
  "ul",
  "ol",
  "li",
  "table",
  "thead",
  "tbody",
  "tr",
]);
const BLOCKS = new Set([
  "p",
  "div",
  "blockquote",
  "ul",
  "ol",
  "li",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "pre",
  "hr",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
]);
const SHOWN = ["aria-label", "href", "rel", "role", "start", "tabindex", "target"];

export const escText = (value: string): string =>
  value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const escAttr = (value: string): string => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;");

function attrString(entries: readonly (readonly [string, string])[]): string {
  return [...entries]
    .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
    .map(([name, value]) => ` ${name}="${escAttr(value)}"`)
    .join("");
}

/** 요소 하나를 글로 쓴다. `inner` 는 이미 글로 쓴 자식이다. */
export function el(tag: string, attrs: Readonly<Record<string, string>> = {}, inner = ""): string {
  const head = attrString(Object.entries(attrs));
  return VOID.has(tag) ? `<${tag}${head}>` : `<${tag}${head}>${inner}</${tag}>`;
}

function isBlockOrEdge(node: Node | null): boolean {
  return node === null || (node instanceof Element && BLOCKS.has(node.localName));
}

function writeElement(element: Element): string {
  const attrs: (readonly [string, string])[] = [];
  for (const name of SHOWN) {
    const value = element.getAttribute(name);
    if (value !== null) attrs.push([name, value]);
  }
  const head = attrString(attrs);
  const tag = element.localName;
  return VOID.has(tag) ? `<${tag}${head}>` : `<${tag}${head}>${writeChildren(element)}</${tag}>`;
}

function writeChildren(parent: Element): string {
  const children = Array.from(parent.childNodes);
  const blockParent = BLOCK_PARENTS.has(parent.localName);
  let out = "";
  children.forEach((child, index) => {
    if (child instanceof Element) {
      out += writeElement(child);
      return;
    }
    if (!(child instanceof Text)) return;
    const prev = children[index - 1] ?? null;
    const next = children[index + 1] ?? null;
    let value = child.data;
    if (blockParent) {
      if (value.startsWith("\n") && isBlockOrEdge(prev)) value = value.slice(1);
      if (value.endsWith("\n") && isBlockOrEdge(next)) value = value.slice(0, -1);
    }
    if (value.startsWith("\n") && prev instanceof Element && prev.localName === "br")
      value = value.slice(1);
    out += escText(value);
  });
  return out;
}

/** 부품이 그린 뿌리 요소(`container` 의 첫 요소) 안쪽의 뼈대. 뿌리가 없으면 null 이다. */
export function skeletonOf(container: Element): string | null {
  const root = container.firstElementChild;
  return root === null ? null : writeChildren(root);
}

// ── 기대를 짓는 도우미 ──────────────────────────────────────────────────────────────────────────────────────────
/** 한 줄 바꿈. */
export const BR = "<br>";
/** 글을 뼈대의 글로 바꾼다(`&`, `<`, `>`). 기대에 쓰는 글에 이 글자가 있을 때 쓴다. */
export const txt = escText;
export const p = (inner: string): string => el("p", {}, inner);
export const strong = (inner: string): string => el("strong", {}, inner);
export const em = (inner: string): string => el("em", {}, inner);
export const code = (inner: string): string => el("code", {}, inner);
/** 문장 끝 번호. 대괄호를 뗀 숫자만 위첨자에 든다. 이어진 번호의 표지는 DOM 에 남지 않아 뼈대에 들지 않는다. */
export const sup = (n: number): string => el("sup", {}, String(n));
/** 출력 끝의 출처 덩이. 표지와 목록을 감싼 `div` 하나다. */
export const sources = (inner: string): string => el("div", {}, inner);
/** 링크. 새 탭으로 열리고 글 뒤에 화면 읽기 프로그램만 읽는 문구가 붙는다. */
export const a = (href: string, inner: string): string =>
  el(
    "a",
    { href, rel: "noopener noreferrer", target: "_blank" },
    inner + el("span", {}, "(새 탭에서 열림)"),
  );
/** 이미지 자리. 대체 글이 비면 "이미지"만 남는다. */
export const img = (alt: string): string =>
  el("span", {}, alt === "" ? "이미지" : `이미지: ${alt}`);
export const pre = (inner: string): string => el("pre", { tabindex: "0" }, el("code", {}, inner));
export const li = (inner: string): string => el("li", {}, inner);
export const ul = (...items: string[]): string => el("ul", {}, items.map(li).join(""));
export const ol = (...items: string[]): string => el("ol", {}, items.map(li).join(""));
export const bq = (inner: string): string => el("blockquote", {}, inner);
/** 제목. 출력의 제목은 한 단계 낮아져 `#` 은 `h2` 다. */
export const h = (level: 2 | 3 | 4 | 5 | 6, inner: string): string =>
  el(`h${String(level)}`, {}, inner);
/** 표. 감싼 칸은 이름 "표"의 묶음이고 포커스를 받는다. */
export const table = (head: readonly string[], rows: readonly (readonly string[])[]): string =>
  el(
    "div",
    { "aria-label": "표", role: "group", tabindex: "0" },
    el(
      "table",
      {},
      el("thead", {}, el("tr", {}, head.map((cell) => el("th", {}, cell)).join(""))) +
        el(
          "tbody",
          {},
          rows.map((row) => el("tr", {}, row.map((cell) => el("td", {}, cell)).join(""))).join(""),
        ),
    ),
  );
