// 한 줄 바꿈 30가지(answer-markdown 명세 "한 줄 바꿈"). 원천은 프로브의 사례 파일 `shape-cases.mjs` 의 `BREAKS` 이고 입력은 글자
// 그대로 옮겼다. `want` 는 목표 모양(`skeleton.ts` 의 뼈대)이다. 목표를 적어 둔 입력은 그 모양과 같은지를, `want` 가 null 인
// 입력은 지금의 결과(`pinned`)를 고정한다. 지금의 결과 셋은 같은 라이브러리 판(react-markdown 10.1.0, remark-gfm 4.0.1)에
// 한 줄 바꿈 변환을 더해 생각한 값이고, 라이브러리가 낸 표 모양은 직접 돌려 봤다.
import { a, BR, bq, code, h, ol, p, pre, strong, table, txt, ul } from "./skeleton";

const FENCE = "```";
export const tableMd = (head: readonly string[], ...rows: readonly (readonly string[])[]): string =>
  [
    `| ${head.join(" | ")} |`,
    `| ${head.map(() => "---").join(" | ")} |`,
    ...rows.map((row) => `| ${row.join(" | ")} |`),
  ].join("\n");

export interface ShapeCase {
  readonly id: string;
  readonly input: string;
  /** 목표를 적은 입력은 그 모양이다. 목표를 정하지 않아 지금의 결과를 고정하는 입력은 null. */
  readonly want: string | null;
  /** `want` 가 null 인 입력이 지금 내는 모양. */
  readonly pinned?: string;
  readonly note?: string;
}

export const BREAKS: readonly ShapeCase[] = [
  { id: "g01-paragraph", input: "첫째 줄\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g02-three-lines",
    input: "첫째 줄\n둘째 줄\n셋째 줄",
    want: p(`첫째 줄${BR}둘째 줄${BR}셋째 줄`),
  },
  { id: "g03-two-paragraphs", input: "문단 하나\n\n문단 둘", want: p("문단 하나") + p("문단 둘") },
  {
    id: "g04-list-item",
    input: "- 항목 하나\n  이어지는 줄\n- 항목 둘",
    want: ul(`항목 하나${BR}이어지는 줄`, "항목 둘"),
  },
  {
    id: "g05-list-lazy",
    note: "들여쓰지 않고 이은 줄(lazy continuation)",
    input: "- 항목 하나\n이어지는 줄",
    want: ul(`항목 하나${BR}이어지는 줄`),
  },
  {
    id: "g06-blockquote",
    input: "> 인용 첫 줄\n> 인용 둘째 줄",
    want: bq(p(`인용 첫 줄${BR}인용 둘째 줄`)),
  },
  {
    id: "g07-blockquote-lazy",
    input: "> 인용 첫 줄\n이어지는 줄",
    want: bq(p(`인용 첫 줄${BR}이어지는 줄`)),
  },
  {
    id: "g08-table-cell-br",
    note: "표 칸 안의 줄바꿈은 마크다운으로 쓸 수 없어 모델이 `<br>` 을 쓴다. 원시 HTML 이라 글자로 보인다",
    input: tableMd(["항목", "설명"], ["기간", "첫 줄<br>둘째 줄"]),
    want: null,
    pinned: table(["항목", "설명"], [["기간", txt("첫 줄<br>둘째 줄")]]),
  },
  {
    id: "g09-table-then-line",
    note: "표 바로 다음 줄(빈 줄 없음)은 칸이 하나뿐인 표의 줄이 되고 빈 칸이 채워진다(GFM)",
    input: `${tableMd(["가", "나"], ["1", "2"])}\n표 다음 줄`,
    want: null,
    pinned: table(
      ["가", "나"],
      [
        ["1", "2"],
        ["표 다음 줄", ""],
      ],
    ),
  },
  {
    id: "g10-hard-two-spaces",
    note: "강제 줄바꿈은 `<br>` 하나여야 한다",
    input: "첫째 줄  \n둘째 줄",
    want: p(`첫째 줄${BR}둘째 줄`),
  },
  { id: "g11-hard-backslash", input: "첫째 줄\\\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  { id: "g12-hard-three-spaces", input: "첫째 줄   \n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g13-code-block",
    note: "코드 블록은 그대로",
    input: `${FENCE}\n줄 하나\n줄 둘\n${FENCE}`,
    want: pre("줄 하나\n줄 둘\n"),
  },
  {
    id: "g14-inline-code",
    note: "줄 안 코드의 줄 끝은 빈칸이 된다(CommonMark)",
    input: "`가\n나`",
    want: p(code("가 나")),
  },
  { id: "g15-crlf", input: "첫째 줄\r\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g16-crlf-paragraphs",
    input: "문단 하나\r\n\r\n문단 둘",
    want: p("문단 하나") + p("문단 둘"),
  },
  { id: "g17-cr-only", input: "첫째 줄\r둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  { id: "g18-crlf-hard", input: "첫째 줄  \r\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g19-crlf-code-block",
    input: `${FENCE}\r\n줄 하나\r\n줄 둘\r\n${FENCE}`,
    want: pre("줄 하나\n줄 둘\n"),
  },
  {
    id: "g20-inside-strong",
    input: "**굵은 첫 줄\n굵은 둘째 줄**",
    want: p(strong(`굵은 첫 줄${BR}굵은 둘째 줄`)),
  },
  {
    id: "g21-between-inline",
    input: "**가**\n**나**",
    want: p(`${strong("가")}${BR}${strong("나")}`),
  },
  { id: "g22-heading-then-line", input: "# 제목\n본문 줄", want: h(2, "제목") + p("본문 줄") },
  { id: "g23-one-trailing-space", input: "첫째 줄 \n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g24-ordered-lazy",
    note: "번호 목록 바로 다음 줄은 마지막 항목에 붙는다",
    input: "1. 하나\n2. 둘\n맺는 줄",
    want: ol("하나", `둘${BR}맺는 줄`),
  },
  {
    id: "g25-link-text",
    input: "[링크\n글](https://example.com/)",
    want: p(a("https://example.com/", `링크${BR}글`)),
  },
  { id: "g26-many-blank-lines", input: "가\n\n\n\n나", want: p("가") + p("나") },
  {
    id: "g27-indented-next-line",
    note: "네 칸 들여쓴 다음 줄은 문단을 끊지 못한다",
    input: "가\n    나",
    want: p(`가${BR}나`),
  },
  { id: "g28-leading-spaces", input: "가\n  나", want: p(`가${BR}나`) },
  {
    id: "g29-setext",
    note: "문단 다음 줄의 `---` 는 그 문단을 제목으로 만든다. 제목의 두 줄도 줄바꿈으로 보인다(`---` 는 둘째 단계라 h3)",
    input: "첫 줄\n둘째 줄\n---",
    want: null,
    pinned: h(3, `첫 줄${BR}둘째 줄`),
  },
  { id: "g30-trailing-newline", input: "가\n", want: p("가") },
];
