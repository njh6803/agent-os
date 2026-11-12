// 모든 입력에 거는 규칙 하나(answer-markdown 명세 "부품의 단위 시험"). 그려진 DOM 이 이 규칙을 어기면 `violations` 가 어긴 것을
// 글로 돌려준다. 빈 배열이면 지킨 것이다.
//
// - 그려진 요소가 허용 목록 안이다(명세 "그리는 요소와 모양"의 표. 제목은 `h2` 부터 `h6` 까지다).
// - `href` 는 `a` 에만 있고 `http` 나 `https` 의 절대 주소이며 사용자 정보가 없다.
// - 링크의 속성은 `href`·`target`·`rel` 과 부품이 모양으로 고른 `class` 뿐이다.
// - `img`·`input`·`script`·`style`·`iframe` 이 없고, 이벤트 속성(`on…`)과 인라인 `style` 이 없다.
//
// 이 규칙은 `linkHref` 와 따로 짠 눈이다. 같은 함수로 판정하면 판정이 틀렸을 때 부품과 시험이 함께 틀린다.

const ALLOWED_TAGS = new Set([
  "div",
  "p",
  "span",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "strong",
  "em",
  "del",
  "ul",
  "ol",
  "li",
  "blockquote",
  "code",
  "pre",
  "a",
  "hr",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "br",
  "sup",
]);
const BANNED_TAGS = new Set(["img", "input", "script", "style", "iframe"]);
const LINK_ATTRS = new Set(["href", "target", "rel", "class"]);
/** 주소를 싣는 속성. 링크의 `href` 밖에서는 어디에도 없어야 한다. */
const URL_ATTRS = new Set([
  "src",
  "srcset",
  "action",
  "formaction",
  "poster",
  "data",
  "xlink:href",
]);

export function violations(root: ParentNode): string[] {
  const found: string[] = [];
  for (const element of root.querySelectorAll("*")) {
    const tag = element.localName;
    if (BANNED_TAGS.has(tag)) found.push(`금지한 요소 <${tag}>가 그려졌다`);
    else if (!ALLOWED_TAGS.has(tag)) found.push(`허용 목록 밖의 요소 <${tag}>가 그려졌다`);
    for (const attr of Array.from(element.attributes)) {
      const name = attr.name.toLowerCase();
      if (name.startsWith("on")) found.push(`<${tag}>에 이벤트 속성 ${name}이 있다`);
      if (name === "style") found.push(`<${tag}>에 인라인 style이 있다`);
      if (URL_ATTRS.has(name)) found.push(`<${tag}>에 주소 속성 ${name}이 있다`);
      if (name === "href" && tag !== "a") found.push(`<${tag}>에 href가 있다`);
      if (tag === "a" && !LINK_ATTRS.has(name)) found.push(`링크에 속성 ${name}이 있다`);
    }
    if (tag === "a") {
      const href = element.getAttribute("href");
      if (href !== null) found.push(...hrefProblems(href));
    }
  }
  return found;
}

function hrefProblems(href: string): string[] {
  let url: URL;
  try {
    url = new URL(href);
  } catch {
    return [`href가 절대 주소가 아니다: ${JSON.stringify(href)}`];
  }
  const problems: string[] = [];
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    problems.push(`href의 스킴이 http나 https가 아니다: ${JSON.stringify(href)}`);
  }
  if (url.username !== "" || url.password !== "") {
    problems.push(`href에 사용자 정보가 있다: ${JSON.stringify(href)}`);
  }
  return problems;
}

/** "(새 탭에서 열림)"은 링크에 숨겨 붙는 문구라 링크 글을 읽을 때는 뗀다. */
const HIDDEN_NEW_TAB = "(새 탭에서 열림)";

export interface Analysis {
  /** 요소 이름마다의 개수. */
  readonly tags: Readonly<Partial<Record<string, number>>>;
  /** 링크마다 주소와 글(숨긴 문구는 뗀다). */
  readonly anchors: readonly { readonly href: string | null; readonly text: string }[];
  /** 뿌리 아래의 글 전부. */
  readonly text: string;
}

export function analyze(root: Element): Analysis {
  const tags: Partial<Record<string, number>> = {};
  for (const element of root.querySelectorAll("*")) {
    tags[element.localName] = (tags[element.localName] ?? 0) + 1;
  }
  const anchors = Array.from(root.querySelectorAll("a")).map((element) => {
    const text = element.textContent;
    return {
      href: element.getAttribute("href"),
      text: text.endsWith(HIDDEN_NEW_TAB) ? text.slice(0, -HIDDEN_NEW_TAB.length) : text,
    };
  });
  return { tags, anchors, text: root.textContent };
}

/** 요소 이름의 개수가 정확히 `wanted` 와 같은지. 다르면 어긋난 것을 글로 돌려준다. */
export function exactly(result: Analysis, wanted: Readonly<Record<string, number>>): string[] {
  return Object.entries(wanted)
    .filter(([tag, count]) => (result.tags[tag] ?? 0) !== count)
    .map(
      ([tag, count]) =>
        `<${tag}> ${String(count)}개를 기대했는데 ${String(result.tags[tag] ?? 0)}개다`,
    );
}

export function includes(result: Analysis, piece: string): string[] {
  return result.text.includes(piece) ? [] : [`글에 ${JSON.stringify(piece)}가 없다`];
}

export function noAnchors(result: Analysis): string[] {
  return result.anchors.length === 0 ? [] : [`링크가 그려졌다: ${JSON.stringify(result.anchors)}`];
}

export function oneAnchor(result: Analysis, href: string, text?: string): string[] {
  const only = result.anchors[0];
  const ok =
    result.anchors.length === 1 &&
    only !== undefined &&
    only.href === href &&
    (text === undefined || only.text === text);
  return ok ? [] : [`링크 하나(${href})를 기대했다: ${JSON.stringify(result.anchors)}`];
}
