import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { SCREEN_INPUTS } from "../../markdown/cases/combined";
import { expectedFocusRing, focusRingOf, semanticColor } from "../../storybook/expect";
import { Markdown } from "./Markdown";

const meta = {
  title: "molecules/Markdown",
  component: Markdown,
  args: { text: "" },
  // 위젯의 출력 칸 폭에 가깝게 좁힌다. 출력 칸의 폭을 정하는 것은 부품이 아니라 쓰는 쪽이다.
  render: ({ text }) => (
    <div style={{ width: 320 }}>
      <Markdown text={text} />
    </div>
  ),
} satisfies Meta<typeof Markdown>;

export default meta;
type Story = StoryObj<typeof meta>;

const FENCE = "```";

// ---- 입력 ----
// 기본 모양과 그리지 않는 것의 입력은 answer-markdown 프로브의 사례 파일(`probes/markdown_render/probe/shape-cases.mjs`의
// `SCREEN_INPUTS`의 `mk-all`, `mk-unsafe`)과 글자가 같다. 넘치는 표와 코드 블록은 화면 파일 `ch-table-1`, `ch-code-1`의
// 출력 글이고 물러선 원문은 `mk-fallback-320`의 글이다(`SCREEN_INPUTS`에는 그 셋이 없다). 번호와 출처, 부작용의 입력은
// 사례 파일의 `SCREEN_INPUTS`(`mk-cite`, `mk-side-1`, `mk-side-2`)를 그대로 쓴다.

const SIGNUP_TAIL = [
  "신청서 번호는 `LV-2026-000184` 꼴로 옵니다. 시작일은 ~~11월 30일~~ 12월 1일로 바뀌었습니다. 자세한 안내는 [인사 시스템 도움말](https://hr.example.com/help/leave)에 있습니다.",
  "",
  "---",
  "인사 시스템 API로 낼 때는 아래처럼 보냅니다.",
  `${FENCE}bash`,
  `curl -X POST https://hr.example.com/api/v1/leave-requests -H "Content-Type: application/json" -d '{"type":"parental","start":"2026-12-01","end":"2027-11-30"}'`,
  FENCE,
].join("\n");

const DOCUMENTS_TABLE = [
  "### 필요한 서류",
  "| 서류 | 내는 곳 | 기한 | 비고 |",
  "|---|---|---|---|",
  "| 휴직 신청서 | 인사 시스템 | 시작 30일 전 | 부서장 승인 필요 |",
  "| 가족관계증명서 | 인사팀 메일 | 시작 7일 전 | 3개월 안에 뗀 것 |",
  "| 출생증명서 사본 | 인사팀 메일 | 시작 7일 전 | 출산 전이면 출산 뒤 30일 안 |",
  "",
  "> 회사 규정과 법이 다르면 법이 우선합니다.",
].join("\n");

const ALL = [
  "# 육아휴직 신청 안내",
  "## 신청 절차",
  "휴직 시작 **30일 전**까지 인사 시스템에서 신청서를 냅니다.",
  "부서장이 승인하면 인사팀이 *3일 안에* 확정 문자를 보냅니다.",
  "",
  "1. 인사 시스템에 로그인합니다.",
  "2. **휴가·휴직** 메뉴에서 육아휴직을 고릅니다.",
  "   - 시작일과 끝나는 날을 적습니다.",
  "   - 나눠 쓰려면 기간마다 따로 냅니다.",
  "3. 서류를 올리고 냅니다.",
  "",
  DOCUMENTS_TABLE,
  "",
  SIGNUP_TAIL,
].join("\n");

const UNSAFE = [
  "요청하신 영수증입니다.",
  "![영수증 사진](https://tracker.example/r.png?id=184)",
  "<b>배송 지연</b> 보상은 <script>alert(1)</script> 결제한 수단으로 돌아갑니다.",
  "[환불 안내](javascript:alert(1))를 확인해 주세요.",
  "정상 주소는 [주문 내역](https://shop.example.com/orders)입니다.",
  "https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다.",
].join("\n");

// 인용 200겹. 가드(10겹)에 걸려 원문이 글자 그대로 보인다.
const TOO_DEEP = `${">".repeat(200)}\n…`;

// ---- 도우미 ----

function present<T>(value: T | null | undefined, what: string): T {
  if (value === null || value === undefined) {
    throw new Error(`${what} 이 없다`);
  }
  return value;
}

/** 위 요소의 아래쪽과 아래 요소의 위쪽 사이(px). 소수 첫째 자리까지 본다. */
function gapBetween(upper: Element, lower: Element): number {
  const px = lower.getBoundingClientRect().top - upper.getBoundingClientRect().bottom;
  return Math.round(px * 10) / 10;
}

function styleOf(element: Element): CSSStyleDeclaration {
  return getComputedStyle(element);
}

// ---- 변형 스토리 ----

/** 기본 모양. 화면 파일의 완성 화면 열이 그린 입력(`mk-all`)이다. */
export const DefaultShape: Story = {
  name: "기본 모양은 제목이 h2부터 본문 크기의 굵은 글이고 목록·인용·표·코드·링크가 화면 그림대로 놓인다",
  args: { text: ALL },
  play: async ({ canvas, canvasElement }) => {
    // 제목은 한 단계 낮춘다(`#` 은 h2, `##` 은 h3, `###` 은 h4). 여섯 단계 모두 본문 크기에 굵기 600 이다.
    const title = canvas.getByRole("heading", { level: 2, name: "육아휴직 신청 안내" });
    canvas.getByRole("heading", { level: 3, name: "신청 절차" });
    canvas.getByRole("heading", { level: 4, name: "필요한 서류" });
    await expect(styleOf(title).fontWeight).toBe("600");
    await expect(styleOf(title).fontSize).toBe(styleOf(canvas.getByText(/휴직 시작/)).fontSize);

    // 링크는 강조색에 밑줄이고 새 탭으로 열린다. 화면 읽기 프로그램만 읽는 문구가 붙는다.
    const link = canvas.getByRole("link", { name: /인사 시스템 도움말/ });
    await expect(styleOf(link).color).toBe(semanticColor(link, "accent"));
    await expect(styleOf(link).textDecorationLine).toBe("underline");
    await expect({
      href: link.getAttribute("href"),
      target: link.getAttribute("target"),
      rel: link.getAttribute("rel"),
      name: link.textContent,
    }).toEqual({
      href: "https://hr.example.com/help/leave",
      target: "_blank",
      rel: "noopener noreferrer",
      name: "인사 시스템 도움말(새 탭에서 열림)",
    });

    // 인용은 왼쪽 선 2px(border-control)과 선 뒤 12px 이다.
    const quote = present(canvasElement.querySelector("blockquote"), "인용");
    await expect({
      width: styleOf(quote).borderLeftWidth,
      color: styleOf(quote).borderLeftColor,
      padding: styleOf(quote).paddingLeft,
    }).toEqual({
      width: "2px",
      color: semanticColor(quote, "border-control"),
      padding: "12px",
    });

    // 취소선, 줄 안 코드, 가로줄, 코드 블록이 있다.
    await expect(
      styleOf(present(canvasElement.querySelector("del"), "취소선")).textDecorationLine,
    ).toBe("line-through");
    const inline = canvas.getByText("LV-2026-000184");
    await expect(styleOf(inline).backgroundColor).toBe(semanticColor(inline, "bg"));
    await expect(styleOf(present(canvasElement.querySelector("hr"), "가로줄")).borderTopWidth).toBe(
      "1px",
    );
    const block = present(canvasElement.querySelector("pre"), "코드 블록");
    await expect({
      background: styleOf(block).backgroundColor,
      border: styleOf(block).borderTopColor,
      radius: styleOf(block).borderTopLeftRadius,
      padding: styleOf(block).paddingLeft,
    }).toEqual({
      background: semanticColor(block, "bg"),
      border: semanticColor(block, "border"),
      radius: "4px",
      padding: "12px",
    });
  },
};

/** 그리지 않는 것. 원시 HTML과 스크립트는 글자로, 이미지는 "이미지: 대체 글"로, 위험한 주소는 링크가 아닌 글로 보인다. */
export const NotDrawn: Story = {
  name: "그리지 않는 것은 HTML과 스크립트가 글자로, 이미지가 흐린 '이미지: 대체 글'로 보이고 위험한 주소는 링크가 되지 않는다",
  args: { text: UNSAFE },
  play: async ({ canvas, canvasElement }) => {
    await expect(canvasElement.querySelector("img, script, input, iframe, style")).toBeNull();
    await expect(canvasElement.textContent).toContain("<script>alert(1)</script>");
    await expect(canvasElement.textContent).toContain("<b>배송 지연</b>");

    const placeholder = canvas.getByText("이미지: 영수증 사진");
    await expect(styleOf(placeholder).color).toBe(semanticColor(placeholder, "text-muted"));

    // 링크는 정상 주소 하나뿐이다. 환불 안내(javascript:)와 사용자 정보가 든 주소는 글자로 남는다.
    const links = canvas.getAllByRole("link");
    await expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "https://shop.example.com/orders",
    ]);
    await expect(canvasElement.textContent).toContain("환불 안내를 확인해 주세요.");
    await expect(canvasElement.textContent).toContain(
      "https://shop.example.com@phish.example/refund",
    );
    await expect(canvasElement.textContent).not.toContain("javascript:");
  },
};

/** 넘치는 표. 넓은 표는 표만 가로로 스크롤하고 그 칸은 이름 "표"의 묶음으로 포커스를 받는다. */
export const OverflowTable: Story = {
  name: "넘치는 표는 표의 칸만 가로로 스크롤하고 그 칸은 이름이 '표'인 묶음으로 키보드 포커스를 받는다",
  args: { text: DOCUMENTS_TABLE },
  play: async ({ canvas }) => {
    const scroller = canvas.getByRole("group", { name: "표" });
    await expect(scroller.tabIndex).toBe(0);
    await expect(styleOf(scroller).overflowX).toBe("auto");
    await expect(scroller.scrollWidth).toBeGreaterThan(scroller.clientWidth);
    // 문서는 가로로 밀리지 않는다.
    await expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(
      document.documentElement.clientWidth,
    );
    // 머리 칸은 굵고, 가로선은 줄 사이에만 있다(마지막 줄 아래에는 없다).
    const head = canvas.getByRole("columnheader", { name: "서류" });
    await expect(styleOf(head).fontWeight).toBe("600");
    const rows = canvas.getAllByRole("row");
    const lastRow = present(rows.at(-1), "마지막 줄");
    await expect({
      middle: styleOf(present(rows[1], "둘째 줄")).borderBottomWidth,
      last: styleOf(lastRow).borderBottomWidth,
    }).toEqual({ middle: "1px", last: "0px" });
  },
};

/** 넘치는 코드 블록. 줄을 꺾지 않고 칸 안에서 가로로 스크롤하며 포커스를 받는다. */
export const OverflowCode: Story = {
  name: "넘치는 코드 블록은 줄을 꺾지 않고 그 칸 안에서 가로로 스크롤하며 키보드 포커스를 받는다",
  args: { text: SIGNUP_TAIL },
  play: async ({ canvasElement }) => {
    const block = present(canvasElement.querySelector("pre"), "코드 블록");
    await expect(block.tabIndex).toBe(0);
    await expect(styleOf(block).overflowX).toBe("auto");
    await expect(block.scrollWidth).toBeGreaterThan(block.clientWidth);
    await expect(styleOf(block).whiteSpace).toBe("pre");
    await expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(
      document.documentElement.clientWidth,
    );
    // 블록 안의 code 는 줄 안 코드의 바탕을 갖지 않는다.
    const inner = present(block.querySelector("code"), "블록 안의 code");
    await expect(styleOf(inner).backgroundColor).toBe("rgba(0, 0, 0, 0)");
  },
};

/** 물러선 원문. 인용이 10겹을 넘으면 그리지 않고 원문을 글자 그대로 보인다. */
export const FallbackRaw: Story = {
  name: "인용이 10겹을 넘으면 그리지 않고 원문을 줄바꿈과 공백 그대로 한 문단으로 보인다",
  args: { text: TOO_DEEP },
  play: async ({ canvasElement }) => {
    await expect(canvasElement.querySelector("blockquote")).toBeNull();
    const raw = present(canvasElement.querySelector("p"), "원문 문단");
    await expect(raw.textContent).toBe(TOO_DEEP);
    await expect({
      whiteSpace: styleOf(raw).whiteSpace,
      wrap: styleOf(raw).overflowWrap,
    }).toEqual({ whiteSpace: "pre-wrap", wrap: "anywhere" });
  },
};

/** 다크 모드. 글자, 링크, 코드, 표의 선이 읽힌다(명암비는 스토리 테스트가 여덟 벌로 본다). */
export const Dark: Story = {
  name: "다크 모드에서 글자·링크·코드 바탕이 다크의 쓰임새 토큰으로 칠해진다",
  args: { text: ALL },
  globals: { mode: "dark" },
  play: async ({ canvas, canvasElement }) => {
    const link = canvas.getByRole("link", { name: /인사 시스템 도움말/ });
    await expect(styleOf(link).color).toBe(semanticColor(link, "accent"));
    const inline = canvas.getByText("LV-2026-000184");
    await expect({
      background: styleOf(inline).backgroundColor,
      text: styleOf(inline).color,
    }).toEqual({
      background: semanticColor(inline, "bg"),
      text: semanticColor(inline, "text"),
    });
    const block = present(canvasElement.querySelector("pre"), "코드 블록");
    await expect(styleOf(block).borderTopColor).toBe(semanticColor(block, "border"));
  },
};

/** 번호와 출처. 화면 파일 `mk-cite-320`·`mk-cite-400`이 그린 입력이다. */
export const CitationsAndSources: Story = {
  name: "문장 끝 번호는 대괄호 없는 작은 흐린 위첨자이고 끝의 출처는 선 아래 작은 흐린 글자로 그려진다",
  args: { text: SCREEN_INPUTS["mk-cite"] },
  play: async ({ canvas, canvasElement }) => {
    const numbers = Array.from(canvasElement.querySelectorAll("sup"));
    await expect(numbers.map((number) => number.textContent)).toEqual(["1", "2"]);
    await expect(canvasElement.textContent).not.toContain("[1]");
    const first = present(numbers[0], "첫 번호");
    await expect({
      link: first.closest("a"),
      color: styleOf(first).color,
      fontSize: styleOf(first).fontSize,
      lineHeight: styleOf(first).lineHeight,
      gap: styleOf(first).marginLeft,
    }).toEqual({
      link: null,
      color: semanticColor(first, "text-muted"),
      fontSize: "12px",
      lineHeight: "0px",
      gap: "2px",
    });

    // 출처 덩이는 출력의 마지막 요소다. 위 선 1px 과 선 아래 12px, 작은 흐린 글자이고 항목 사이는 0 이다.
    const label = canvas.getByText("출처");
    const block = present(label.parentElement, "출처 덩이");
    await expect(block.nextElementSibling).toBeNull();
    await expect({
      line: styleOf(block).borderTopWidth,
      lineColor: styleOf(block).borderTopColor,
      below: styleOf(block).paddingTop,
      color: styleOf(block).color,
      fontSize: styleOf(block).fontSize,
    }).toEqual({
      line: "1px",
      lineColor: semanticColor(block, "border"),
      below: "12px",
      color: semanticColor(block, "text-muted"),
      fontSize: "12px",
    });
    const items = Array.from(block.querySelectorAll("li"));
    const list = present(block.querySelector("ol"), "출처 목록");
    await expect({
      labelToList: gapBetween(label, list),
      items: gapBetween(present(items[0], "첫 항목"), present(items[1], "둘째 항목")),
      itemColor: styleOf(present(items[0], "첫 항목")).color,
    }).toEqual({ labelToList: 4, items: 0, itemColor: semanticColor(block, "text-muted") });
  },
};

/** 부작용. 화면 파일 `mk-side-320`이 그린 두 출력이다. */
export const SideEffects: Story = {
  name: "숫자 사이 별표와 밑줄은 글자 그대로이고 조사가 붙은 굵게는 닫히며 #으로 시작하는 줄은 제목으로 남는다",
  render: () => (
    <div style={{ width: 320, display: "flex", flexDirection: "column", gap: 24 }}>
      <Markdown text={SCREEN_INPUTS["mk-side-1"]} />
      <Markdown text={SCREEN_INPUTS["mk-side-2"]} />
    </div>
  ),
  play: async ({ canvas, canvasElement }) => {
    canvas.getByText("2*3*4 = 24입니다.");
    await expect(canvasElement.querySelector("em")).toBeNull();
    const bold = present(canvasElement.querySelector("strong"), "굵게");
    await expect(bold.textContent).toBe("민법 제750조(불법행위)");
    await expect(styleOf(bold).fontWeight).toBe("600");
    await expect(canvasElement.textContent).not.toContain("**");
    canvas.getByRole("heading", { level: 2, name: "1번 항목은 다음 쪽에 있습니다." });
    canvas.getByText("설정 파일은 __init__.py 옆에 둡니다.");
  },
};

// ---- 놓인 자리 스토리 ----
// 화면 파일은 출력 칸의 스타일 한 벌(자손과 형제 선택자)로 그렸고 부품은 요소마다 클래스를 준다. 놓인 자리(뿌리, 인용,
// 목록 항목, 출처 덩이)에 따라 클래스가 달라지는 모양과 변환이 단 표지로 고르는 모양은 위의 입력이 다 그리지 않는다. 그
// 모양을 계산된 값으로 잰다(클래스 글자는 단언하지 않는다).

const HEADINGS_TEXT = [
  "# 첫째 제목",
  "## 바로 뒤의 제목",
  "",
  "본문 문단입니다.",
  "",
  "### 문단 뒤의 제목",
  "",
  // 빈 줄이 있어 항목이 느슨해지고 설명이 문단 요소가 된다(촘촘한 목록의 설명은 요소가 없는 글자라 간격을 잴 수 없다).
  "- ## 목록 항목 안의 제목",
  "",
  "  항목의 설명입니다.",
].join("\n");

/** 잇단 제목과 제목·문단·제목, 목록 항목 안의 제목. */
export const HeadingSpacing: Story = {
  name: "제목 바로 뒤의 제목과 문단 뒤의 제목은 모두 위 16px 이고, 제목 아래는 4px, 목록 항목 안의 제목은 항목의 사이 4px 를 따른다",
  args: { text: HEADINGS_TEXT },
  play: async ({ canvas }) => {
    const first = canvas.getByRole("heading", { level: 2, name: "첫째 제목" });
    const after = canvas.getByRole("heading", { level: 3, name: "바로 뒤의 제목" });
    const paragraph = canvas.getByText("본문 문단입니다.");
    const lateHeading = canvas.getByRole("heading", { level: 4, name: "문단 뒤의 제목" });
    const itemHeading = canvas.getByRole("heading", { level: 3, name: "목록 항목 안의 제목" });
    const itemText = canvas.getByText(/항목의 설명입니다/);
    await expect({
      headingToHeading: gapBetween(first, after),
      headingToParagraph: gapBetween(after, paragraph),
      paragraphToHeading: gapBetween(paragraph, lateHeading),
      insideItem: gapBetween(itemHeading, itemText),
    }).toEqual({
      headingToHeading: 16,
      headingToParagraph: 4,
      paragraphToHeading: 16,
      insideItem: 4,
    });
  },
};

const NESTED_LISTS_TEXT = [
  "1. 첫째 단계",
  "   - 안쪽 점 하나",
  "   - 안쪽 점 둘",
  "     - 더 안쪽 점",
  "2. 둘째 단계",
  "",
  "3. 끝낸 뒤",
].join("\n");

/** 번호 목록 안의 점 목록과 점 목록 안의 점 목록. */
export const NestedLists: Story = {
  name: "점 목록은 어디에 놓여도 검은 점이고 안쪽 목록은 들여쓰기 24px 로 단계가 갈린다",
  args: { text: NESTED_LISTS_TEXT },
  play: async ({ canvasElement }) => {
    const lists = Array.from(canvasElement.querySelectorAll("ul, ol"));
    const [ordered, inner, deepest] = lists;
    await expect(lists).toHaveLength(3);
    await expect({
      ordered: styleOf(present(ordered, "번호 목록")).listStyleType,
      inner: styleOf(present(inner, "안쪽 점 목록")).listStyleType,
      deepest: styleOf(present(deepest, "더 안쪽 점 목록")).listStyleType,
    }).toEqual({ ordered: "decimal", inner: "disc", deepest: "disc" });
    await expect({
      ordered: styleOf(present(ordered, "번호 목록")).paddingLeft,
      inner: styleOf(present(inner, "안쪽 점 목록")).paddingLeft,
      deepest: styleOf(present(deepest, "더 안쪽 점 목록")).paddingLeft,
    }).toEqual({ ordered: "24px", inner: "24px", deepest: "24px" });
    // 항목을 flex 로 만들면 글머리 표시가 사라진다.
    const item = present(canvasElement.querySelector("li"), "목록 항목");
    await expect(styleOf(item).display).toBe("list-item");
  },
};

const QUOTE_TEXT = ["> 첫 문단입니다.", ">", "> 둘째 문단입니다.", ">", "> - 인용 안의 목록"].join(
  "\n",
);

/** 블록이 둘 이상인 인용. */
export const QuoteBlocks: Story = {
  name: "인용 안의 블록 사이는 뿌리와 같은 12px 이다",
  args: { text: QUOTE_TEXT },
  play: async ({ canvas, canvasElement }) => {
    const first = canvas.getByText("첫 문단입니다.");
    const second = canvas.getByText("둘째 문단입니다.");
    const list = present(canvasElement.querySelector("blockquote ul"), "인용 안의 목록");
    await expect({
      paragraphs: gapBetween(first, second),
      toList: gapBetween(second, list),
    }).toEqual({ paragraphs: 12, toList: 12 });
  },
};

const ALIGN_TEXT = ["| 왼쪽 | 가운데 | 오른쪽 |", "|:---|:---:|---:|", "| 가 | 나 | 다 |"].join(
  "\n",
);

/** 정렬을 적은 표 칸. */
export const TableAlignment: Story = {
  name: "원문이 정렬을 적은 표 칸은 왼쪽·가운데·오른쪽 정렬로 그려지고 머리 칸의 기본 정렬은 왼쪽이다",
  args: { text: ALIGN_TEXT },
  play: async ({ canvas }) => {
    const heads = ["왼쪽", "가운데", "오른쪽"].map((name) =>
      canvas.getByRole("columnheader", { name }),
    );
    const cells = ["가", "나", "다"].map((name) => canvas.getByRole("cell", { name }));
    await expect({
      heads: heads.map((cell) => styleOf(cell).textAlign),
      cells: cells.map((cell) => styleOf(cell).textAlign),
    }).toEqual({
      heads: ["left", "center", "right"],
      cells: ["left", "center", "right"],
    });
  },
};

const PLAIN_HEAD_TEXT = ["| 이름 | 값 |", "|---|---|", "| 가 | 1 |"].join("\n");

/** 정렬을 적지 않은 표 칸. 머리 칸은 왼쪽 정렬이고 보통 칸은 정렬을 두지 않는다. */
export const TableWithoutAlignment: Story = {
  name: "정렬을 적지 않은 표의 머리 칸은 왼쪽 정렬이고 칸은 위로 붙는다",
  args: { text: PLAIN_HEAD_TEXT },
  play: async ({ canvas }) => {
    const head = canvas.getByRole("columnheader", { name: "이름" });
    const cell = canvas.getByRole("cell", { name: "가" });
    await expect({
      head: styleOf(head).textAlign,
      verticalAlign: styleOf(cell).verticalAlign,
      minWidth: styleOf(cell).minWidth,
      maxWidth: styleOf(cell).maxWidth,
    }).toEqual({
      head: "left",
      verticalAlign: "top",
      minWidth: "96px",
      maxWidth: "256px",
    });
  },
};

const ORDERED_START_TEXT = [
  "3. 셋째 항목",
  "4. 넷째 항목",
  "",
  "~~지운 글~~ 과 *기울임* 과 **굵게**",
].join("\n");

/** 1이 아닌 수로 시작하는 번호 목록과 줄 안의 서식 셋. */
export const OrderedStart: Story = {
  name: "1이 아닌 수로 시작하는 번호 목록은 그 수를 지키고 줄 안의 서식은 취소선·기울임·굵게로 그려진다",
  args: { text: ORDERED_START_TEXT },
  play: async ({ canvasElement }) => {
    const list = present(canvasElement.querySelector("ol"), "번호 목록");
    await expect(list.getAttribute("start")).toBe("3");
    await expect({
      del: styleOf(present(canvasElement.querySelector("del"), "취소선")).textDecorationLine,
      em: styleOf(present(canvasElement.querySelector("em"), "기울임")).fontStyle,
      strong: styleOf(present(canvasElement.querySelector("strong"), "굵게")).fontWeight,
    }).toEqual({ del: "line-through", em: "italic", strong: "600" });
  },
};

const CITATION_GAPS_TEXT = [
  "가능합니다[1][2].",
  "",
  "그렇습니다 [1] [2].",
  "",
  "앞 근거 [1] 그리고 뒤 근거 [2].",
  "",
  "번호가 없는 줄입니다.",
].join("\n");

/** 이어진 번호(`[1][2]`, `[1] [2]`)와 사이에 글이 낀 번호(`[1] 글 [2]`). 이어진 번호의 둘째만 변환이 단 표지로 틈을 넓힌다. */
export const CitationGaps: Story = {
  name: "번호의 왼쪽 틈은 2px 이고 바로 앞이 번호인 번호만 4px 이며 번호가 든 줄과 없는 줄의 높이가 같다",
  args: { text: CITATION_GAPS_TEXT },
  play: async ({ canvas }) => {
    const gaps = (text: RegExp): string[] =>
      Array.from(canvas.getByText(text).querySelectorAll("sup")).map(
        (number) => styleOf(number).marginLeft,
      );
    await expect({
      joined: gaps(/^가능합니다/),
      spaced: gaps(/^그렇습니다/),
      apart: gaps(/^앞 근거/),
    }).toEqual({
      joined: ["2px", "4px"],
      spaced: ["2px", "4px"],
      apart: ["2px", "2px"],
    });
    const withNumber = canvas.getByText(/^가능합니다/).getBoundingClientRect().height;
    const without = canvas.getByText("번호가 없는 줄입니다.").getBoundingClientRect().height;
    await expect(withNumber).toBe(without);
  },
};

const SOURCES_HEADING_TEXT = [
  "본문입니다. [1]",
  "",
  "## 출처",
  "1. 육아휴직 업무편람",
  "2. 인사 규정",
].join("\n");

/** 출처 덩이 안의 제목. 표지를 제목으로 쓴 출력이다. */
export const SourcesHeading: Story = {
  name: "출처 덩이 안의 제목은 여백 없이 덩이의 작은 흐린 글자를 물려받고 굵기만 다르다",
  args: { text: SOURCES_HEADING_TEXT },
  play: async ({ canvas, canvasElement }) => {
    const heading = canvas.getByRole("heading", { level: 3, name: "출처" });
    const block = present(heading.parentElement, "출처 덩이");
    const list = present(block.querySelector("ol"), "출처 목록");
    await expect(block.nextElementSibling).toBeNull();
    await expect(canvasElement.querySelectorAll("sup")).toHaveLength(1);
    await expect({
      marginTop: styleOf(heading).marginTop,
      marginBottom: styleOf(heading).marginBottom,
      fontSize: styleOf(heading).fontSize,
      color: styleOf(heading).color,
      fontWeight: styleOf(heading).fontWeight,
      toList: gapBetween(heading, list),
    }).toEqual({
      marginTop: "0px",
      marginBottom: "0px",
      fontSize: styleOf(block).fontSize,
      color: semanticColor(block, "text-muted"),
      fontWeight: "600",
      toList: 4,
    });
  },
};

// ---- 보여 주기용 ----

// 기본 에이전트의 출력처럼 문장 끝 번호와 출처를 든다. 디자인 시스템 카드에는 보여 주기용 스토리만 오르므로, 번호의 위첨자와
// 출처 덩이가 카드에 보이려면 이 글에 있어야 한다.
const SHOWCASE_TEXT = [
  "휴직 시작 **30일 전**까지 인사 시스템에서 신청서를 냅니다. [1]",
  "",
  "1. 인사 시스템에 로그인합니다.",
  "2. **휴가·휴직** 메뉴에서 육아휴직을 고릅니다.",
  "",
  "자세한 안내는 [인사 시스템 도움말](https://hr.example.com/help/leave)에 있습니다.",
  "",
  "출처",
  "1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)",
].join("\n");

/** 보여 주기용(`showcase`). 위젯의 대화에서 에이전트의 출력이 놓이는 자리다. 화면 읽기 프로그램만 읽는 "출력: "이 앞에 놓인다. */
export const ShowcaseWidgetOutput: Story = {
  name: "쓰임: 위젯 대화의 에이전트 출력",
  tags: ["showcase"],
  render: () => (
    <div style={{ width: 360 }}>
      <div>
        <span className="sr-only">출력: </span>
        <Markdown text={SHOWCASE_TEXT} />
      </div>
    </div>
  ),
};

// ---- 포커스 ----

/** 링크는 키보드 포커스를 받으면 포커스 링을 그린다. 표의 스크롤 칸과 코드 블록도 같다(사진 비교의 상호작용이 찍는다). */
export const FocusRings: Story = {
  name: "링크·표의 스크롤 칸·코드 블록은 키보드 포커스를 받으면 2px 포커스 링을 2px 띄워 그린다",
  args: {
    text: [
      DOCUMENTS_TABLE,
      "",
      "[도움말](https://hr.example.com/help)",
      "",
      `${FENCE}\nnpm test\n${FENCE}`,
    ].join("\n"),
  },
  play: async ({ canvas, canvasElement, userEvent }) => {
    const link = canvas.getByRole("link", { name: /도움말/ });
    const scroller = canvas.getByRole("group", { name: "표" });
    const block = present(canvasElement.querySelector("pre"), "코드 블록");
    for (const target of [scroller, link, block]) {
      target.focus();
      await userEvent.keyboard("{Shift>}{/Shift}");
      await expect(target.matches(":focus-visible")).toBe(true);
      await expect(focusRingOf(target)).toEqual(expectedFocusRing(target));
    }
  },
};

/** 코드 블록 하나만 든 출력. 링크 때와 같은 까닭으로 코드 블록이 첫 요소여야 한다. */
export const CodeFocus: Story = {
  name: "코드 블록은 키보드 포커스를 받으면 포커스 링을 그린다",
  args: {
    text: `${FENCE}bash\ncurl -X POST https://hr.example.com/api/v1/leave-requests -H "Content-Type: application/json"\n${FENCE}`,
  },
  play: async ({ canvasElement, userEvent }) => {
    const block = present(canvasElement.querySelector("pre"), "코드 블록");
    block.focus();
    await userEvent.keyboard("{Shift>}{/Shift}");
    await expect(block.matches(":focus-visible")).toBe(true);
    await expect(focusRingOf(block)).toEqual(expectedFocusRing(block));
  },
};

/** 링크 하나만 든 출력. 사진 비교의 상호작용은 Tab 한 번으로 처음 받는 요소를 찍으므로 링크가 첫 요소여야 한다. */
export const LinkFocus: Story = {
  name: "링크는 키보드 포커스를 받으면 포커스 링을 그린다",
  args: { text: "[인사 시스템 도움말](https://hr.example.com/help/leave)에서 확인하세요." },
  play: async ({ canvas, userEvent }) => {
    const link = canvas.getByRole("link", { name: /인사 시스템 도움말/ });
    link.focus();
    await userEvent.keyboard("{Shift>}{/Shift}");
    await expect(link.matches(":focus-visible")).toBe(true);
    await expect(focusRingOf(link)).toEqual(expectedFocusRing(link));
  },
};
