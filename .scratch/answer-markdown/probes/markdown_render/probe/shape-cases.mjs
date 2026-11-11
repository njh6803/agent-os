// 모양 프로브의 입력과 기대. 기대는 결과를 보기 전에 적었다(2026-11-11). 결과를 본 뒤 고친 기대는 그 사례의
// `revised` 에 무엇을 왜 바꿨는지 적는다(README 의 "결과를 본 뒤 바꾼 기준"이 그 목록이다).
//
// 사례의 칸
// - input: 마크다운 원문.
// - want: 목표 모양(답의 안쪽 HTML, shape-html.mjs 의 글). 명세가 정할 일이라 목표를 미리 정하지 않은 사례는 null 이고
//   후보마다 무엇이 나오는지만 적는다.
// - problem: true 면 "대조 갈래(변환 없는 base)는 목표와 다르다"를 기대한다. 그 문제가 실제로 있어야 후보가 고쳤다는
//   말이 측정이 된다. false(기본)면 대조 갈래도 목표와 같다고 기대한다(후보가 원래 되던 것을 깨는지 본다).
// - wantBy: 후보마다 따로 건 기대. 그 후보의 규칙대로라면 나와야 하는 모양이다(목표가 null 인 사례에서 변환의 버그를 잡는다).
// - note: 사례가 재려는 것.
import { a, bq, BR, code, el, em, img, li, ol, p, pre, sources, strong, sup, table, ul } from "./shape-html.mjs";

const FENCE = "```";
const tableMd = (head, ...rows) =>
  [`| ${head.join(" | ")} |`, `| ${head.map(() => "---").join(" | ")} |`, ...rows.map((row) => `| ${row.join(" | ")} |`)].join("\n");

// ── (가) 한 줄 바꿈 ─────────────────────────────────────────────────────────────────────────────────────────────
const BREAKS = [
  { id: "g01-paragraph", input: "첫째 줄\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`), problem: true },
  { id: "g02-three-lines", input: "첫째 줄\n둘째 줄\n셋째 줄", want: p(`첫째 줄${BR}둘째 줄${BR}셋째 줄`), problem: true },
  { id: "g03-two-paragraphs", input: "문단 하나\n\n문단 둘", want: p("문단 하나") + p("문단 둘") },
  {
    id: "g04-list-item",
    input: "- 항목 하나\n  이어지는 줄\n- 항목 둘",
    want: ul(`항목 하나${BR}이어지는 줄`, "항목 둘"),
    problem: true,
  },
  {
    id: "g05-list-lazy",
    note: "들여쓰지 않고 이은 줄(lazy continuation)",
    input: "- 항목 하나\n이어지는 줄",
    want: ul(`항목 하나${BR}이어지는 줄`),
    problem: true,
  },
  { id: "g06-blockquote", input: "> 인용 첫 줄\n> 인용 둘째 줄", want: bq(p(`인용 첫 줄${BR}인용 둘째 줄`)), problem: true },
  {
    id: "g07-blockquote-lazy",
    input: "> 인용 첫 줄\n이어지는 줄",
    want: bq(p(`인용 첫 줄${BR}이어지는 줄`)),
    problem: true,
  },
  {
    id: "g08-table-cell-br",
    note: "표 칸 안의 줄바꿈은 마크다운으로 쓸 수 없어 모델이 `<br>` 을 쓴다. 무엇이 보이는지 적는다",
    input: tableMd(["항목", "설명"], ["기간", "첫 줄<br>둘째 줄"]),
    want: null,
  },
  {
    id: "g09-table-then-line",
    note: "표 바로 다음 줄(빈 줄 없음)이 어디로 가는지 적는다",
    input: `${tableMd(["가", "나"], ["1", "2"])}\n표 다음 줄`,
    want: null,
  },
  { id: "g10-hard-two-spaces", note: "강제 줄바꿈은 `<br>` 하나여야 한다", input: "첫째 줄  \n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  { id: "g11-hard-backslash", input: "첫째 줄\\\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  { id: "g12-hard-three-spaces", input: "첫째 줄   \n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  { id: "g13-code-block", note: "코드 블록은 그대로", input: `${FENCE}\n줄 하나\n줄 둘\n${FENCE}`, want: pre("줄 하나\n줄 둘\n") },
  { id: "g14-inline-code", note: "줄 안 코드의 줄 끝은 빈칸이 된다(CommonMark)", input: "`가\n나`", want: p(code("가 나")) },
  { id: "g15-crlf", input: "첫째 줄\r\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`), problem: true },
  { id: "g16-crlf-paragraphs", input: "문단 하나\r\n\r\n문단 둘", want: p("문단 하나") + p("문단 둘") },
  { id: "g17-cr-only", input: "첫째 줄\r둘째 줄", want: p(`첫째 줄${BR}둘째 줄`), problem: true },
  { id: "g18-crlf-hard", input: "첫째 줄  \r\n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`) },
  {
    id: "g19-crlf-code-block",
    input: `${FENCE}\r\n줄 하나\r\n줄 둘\r\n${FENCE}`,
    want: pre("줄 하나\n줄 둘\n"),
  },
  { id: "g20-inside-strong", input: "**굵은 첫 줄\n굵은 둘째 줄**", want: p(strong(`굵은 첫 줄${BR}굵은 둘째 줄`)), problem: true },
  { id: "g21-between-inline", input: "**가**\n**나**", want: p(`${strong("가")}${BR}${strong("나")}`), problem: true },
  { id: "g22-heading-then-line", input: "# 제목\n본문 줄", want: el("h2", {}, "제목") + p("본문 줄") },
  { id: "g23-one-trailing-space", input: "첫째 줄 \n둘째 줄", want: p(`첫째 줄${BR}둘째 줄`), problem: true },
  {
    id: "g24-ordered-lazy",
    note: "번호 목록 바로 다음 줄은 마지막 항목에 붙는다",
    input: "1. 하나\n2. 둘\n맺는 줄",
    want: ol("하나", `둘${BR}맺는 줄`),
    problem: true,
  },
  {
    id: "g25-link-text",
    input: "[링크\n글](https://example.com/)",
    want: p(a("https://example.com/", `링크${BR}글`)),
    problem: true,
  },
  { id: "g26-many-blank-lines", input: "가\n\n\n\n나", want: p("가") + p("나") },
  { id: "g27-indented-next-line", note: "네 칸 들여쓴 다음 줄은 문단을 끊지 못한다", input: "가\n    나", want: p(`가${BR}나`), problem: true },
  { id: "g28-leading-spaces", input: "가\n  나", want: p(`가${BR}나`), problem: true },
  { id: "g29-setext", note: "문단 다음 줄의 `---` 는 그 문단을 제목으로 만든다. 무엇이 나오는지 적는다", input: "첫 줄\n둘째 줄\n---", want: null },
  { id: "g30-trailing-newline", input: "가\n", want: p("가") },
];

// ── (나) 한국어에서 닫히지 않는 굵게 ────────────────────────────────────────────────────────────────────────────
const CJK = [
  {
    id: "n01-paren",
    input: "**민법 제750조(불법행위)**는 고의나 과실로 남에게 손해를 입힌 사람이 갚아야 한다고 정합니다.",
    want: p(`${strong("민법 제750조(불법행위)")}는 고의나 과실로 남에게 손해를 입힌 사람이 갚아야 한다고 정합니다.`),
    problem: true,
  },
  { id: "n02-quote", input: '이것은 **"인용"**이라고 한다', want: p(`이것은 ${strong('"인용"')}이라고 한다`), problem: true },
  { id: "n03-intraword", note: "이미 되는 것", input: "값은**굵게**입니다", want: p(`값은${strong("굵게")}입니다`) },
  { id: "n04-normal", note: "이미 되는 것", input: "**굵게**입니다", want: p(`${strong("굵게")}입니다`) },
  {
    id: "n05-link-inside",
    input: "**[규정](https://example.com)(참고)**을 보세요",
    want: p(`${strong(`${a("https://example.com/", "규정")}(참고)`)}을 보세요`),
    problem: true,
  },
  { id: "n06-code-inside", input: "**`코드`(참고)**를 쓴다", want: p(`${strong(`${code("코드")}(참고)`)}를 쓴다`), problem: true },
  { id: "n07-unmatched", note: "짝이 없는 `**` 하나", input: "**열기만 한 글", want: p("**열기만 한 글") },
  { id: "n08-in-list", input: "- **항목(가)**은 설명", want: ul(`${strong("항목(가)")}은 설명`), problem: true },
  {
    id: "n09-in-table",
    input: tableMd(["이름", "뜻"], ["**용어(가)**는", "설명"]),
    want: table(["이름", "뜻"], [[`${strong("용어(가)")}는`, "설명"]]),
    problem: true,
  },
  { id: "n10-in-blockquote", input: "> **인용(가)**은 설명", want: bq(p(`${strong("인용(가)")}은 설명`)), problem: true },
  {
    id: "n11-normal-then-unclosed",
    input: "**정상** 굵게와 **닫히지 않는(것)**이 함께",
    want: p(`${strong("정상")} 굵게와 ${strong("닫히지 않는(것)")}이 함께`),
    problem: true,
  },
  {
    id: "n12-unclosed-then-normal",
    input: "**닫히지 않는(것)**이 먼저 오고 **정상** 굵게",
    want: p(`${strong("닫히지 않는(것)")}이 먼저 오고 ${strong("정상")} 굵게`),
    problem: true,
  },
  {
    id: "n13-parser-mispairs",
    note: "파서가 가운데 둘을 먼저 짝지어 버리는 모양. 파싱 뒤의 변환은 고치지 못할 것으로 본다",
    input: "**가(1)**는 나**다** 끝",
    want: p(`${strong("가(1)")}는 나${strong("다")} 끝`),
    problem: true,
  },
  { id: "n14-italic-paren", input: "*기울임(주)*은 이렇다", want: p(`${em("기울임(주)")}은 이렇다`), problem: true },
  { id: "n15-italic-quote", input: '*"인용"*이라고 한다', want: p(`${em('"인용"')}이라고 한다`), problem: true },
  { id: "n16-open-side", note: "여는 쪽도 같은 규칙에 걸린다", input: "한국어**(괄호)**로 쓴다", want: p(`한국어${strong("(괄호)")}로 쓴다`), problem: true },
  { id: "n17-escaped", note: "역슬래시로 쓴 별표는 글자여야 한다", input: "\\*\\*민법(가)\\*\\*는", want: p("**민법(가)**는") },
  { id: "n18-char-ref", note: "문자 참조로 쓴 별표는 글자여야 한다", input: "&#42;&#42;민법(가)&#42;&#42;는", want: p("**민법(가)**는") },
  { id: "n19-inline-code", input: "`**민법(가)**는`", want: p(code("**민법(가)**는")) },
  { id: "n20-spaced", note: "별표 안쪽에 빈칸이 있으면 굵게가 아니다", input: "** 띄운 글 **은", want: p("** 띄운 글 **은") },
  { id: "n21-corner-brackets", input: "**「민법」**에 따르면", want: p(`${strong("「민법」")}에 따르면`), problem: true },
  { id: "n22-strikethrough", note: "취소선(`~~`)도 같은 모양에서 닫히지 않는지 적는다", input: "~~취소(예)~~는", want: null },
  {
    id: "n23-multiline",
    input: "**첫 줄(가)\n둘째 줄(나)**는",
    want: p(`${strong("첫 줄(가)\n둘째 줄(나)")}는`),
    problem: true,
  },
  {
    id: "n24-lone-asterisks",
    note: "짝이 아닌 별표 둘(뒤의 것 앞이 빈칸)",
    input: "곱셈 기호 *와 나눗셈 기호 /가 있고 별표 *도 쓴다",
    want: p("곱셈 기호 *와 나눗셈 기호 /가 있고 별표 *도 쓴다"),
  },
  { id: "n25-five-stars", input: "별 5개(*****)와 **굵게(가)**는", want: p(`별 5개(*****)와 ${strong("굵게(가)")}는`), problem: true },
  { id: "n26-with-multiply", input: "가격은 2*3이고 **합계(원)**는 6", want: p(`가격은 2*3이고 ${strong("합계(원)")}는 6`), problem: true },
  {
    id: "n27-two-unclosed",
    input: "**가(1)**는 그리고 **나(2)**도",
    want: p(`${strong("가(1)")}는 그리고 ${strong("나(2)")}도`),
    problem: true,
  },
  { id: "n28-period", input: "**가격: 1,000원.**을", want: p(`${strong("가격: 1,000원.")}을`), problem: true },
  { id: "n29-line-end", note: "이미 되는 것(닫는 별표 뒤가 줄 끝)", input: "**주의하세요.**", want: p(strong("주의하세요.")) },
  { id: "n30-then-punct", note: "이미 되는 것(닫는 별표 뒤가 문장부호)", input: "**주의(중요)**, 그리고", want: p(`${strong("주의(중요)")}, 그리고`) },
  { id: "n31-heading", input: "## **제목(가)**의 뜻", want: el("h3", {}, `${strong("제목(가)")}의 뜻`), problem: true },
  { id: "n32-english", note: "영어는 그대로", input: "**bold**text and a*b*c", want: p(`${strong("bold")}text and a${em("b")}c`) },
  { id: "n33-list-like-stars", note: "짝이 아닌 별표 셋", input: "목록은 *가, *나, *다 로 적는다", want: p("목록은 *가, *나, *다 로 적는다") },
  {
    id: "n34-glob-false-positive",
    note: "글자로 쓴 `**` 둘(경로의 와일드카드)이 굵게로 잘못 묶이는지 본다. 후보가 원래 되던 것을 깨는 사례로 미리 적었다",
    input: "경로는 src/**(전부)와 test/**입니다",
    want: p("경로는 src/**(전부)와 test/**입니다"),
  },
];

// ── (다) 숫자 사이의 별표와 밑줄 강조 ───────────────────────────────────────────────────────────────────────────
const LITERAL = [
  { id: "d01", input: "2*3*4 = 24입니다.", want: p("2*3*4 = 24입니다."), problem: true },
  { id: "d02", input: "1*2 = 2, 3*4 = 12", want: p("1*2 = 2, 3*4 = 12"), problem: true },
  { id: "d03", input: "2**3**4", want: p("2**3**4"), problem: true },
  { id: "d04", note: "R1 과 R2 가 갈리는 사례(안쪽이 글자)", input: "2*x*4", want: null },
  { id: "d05", note: "빈칸이 있으면 원래 글자다", input: "2 * 3 * 4", want: p("2 * 3 * 4") },
  { id: "d06", input: "*기울임*", want: p(em("기울임")) },
  { id: "d07", input: "**굵게**", want: p(strong("굵게")) },
  { id: "d08", input: "***둘 다***", want: p(em(strong("둘 다"))) },
  { id: "d09", input: "__init__.py", want: p("__init__.py"), problem: true },
  { id: "d10", note: "치르는 값: 일부러 쓴 밑줄 기울임도 글자로 남는다", input: "_기울임_", want: p("_기울임_"), problem: true },
  { id: "d11", note: "치르는 값: 일부러 쓴 밑줄 굵게도 글자로 남는다", input: "__굵게__", want: p("__굵게__"), problem: true },
  { id: "d12", input: "snake_case_name", want: p("snake_case_name") },
  { id: "d13", input: "a_b_c", want: p("a_b_c") },
  { id: "d14", note: "`_b_가` 는 원래 강조가 아니다(밑줄 뒤가 글자)", input: "*a*와 _b_가 함께", want: p(`${em("a")}와 _b_가 함께`) },
  { id: "d15", input: "___x___", want: p("___x___"), problem: true },
  { id: "d16", note: "바깥 굵게는 두고 안쪽 숫자 사이 별표만 글자로", input: "**2*3*4**", want: p(strong("2*3*4")), problem: true },
  { id: "d17", note: "목록 안", input: "- 2*3*4", want: ul("2*3*4"), problem: true },
  { id: "d18", note: "인용 안", input: "> 2*3*4", want: bq(p("2*3*4")), problem: true },
  { id: "d19", note: "표 칸 안", input: tableMd(["식", "값"], ["2*3*4", "24"]), want: table(["식", "값"], [["2*3*4", "24"]]), problem: true },
  { id: "d20", input: "10*20*30", want: p("10*20*30"), problem: true },
  { id: "d21", input: "3*4*5*6", want: p("3*4*5*6"), problem: true },
  // 위치(오프셋)가 맞는지 보는 사례
  { id: "d22", note: "한글 뒤", input: "값은 2*3*4입니다", want: p("값은 2*3*4입니다"), problem: true },
  { id: "d23", note: "대리 쌍 글자(이모지) 뒤", input: "😀 2*3*4", want: p("😀 2*3*4"), problem: true },
  { id: "d24", note: "CRLF 의 둘째 줄", input: "첫 줄\r\n2*3*4\r\n끝", want: p("첫 줄\n2*3*4\n끝"), problem: true },
  { id: "d25", note: "CRLF 인용의 둘째 줄", input: "> 첫 줄\r\n> 2*3*4", want: bq(p("첫 줄\n2*3*4")), problem: true },
  { id: "d26", note: "강조가 인용의 두 줄에 걸친다", input: "> 2*3\n> 4*5", want: bq(p("2*3\n4*5")), problem: true },
  { id: "d27", note: "겹친 목록 안", input: "- 가\n  - 2*3*4", want: ul(`가${ul("2*3*4")}`), problem: true },
  { id: "d28", note: "같은 줄 앞에 문자 참조", input: "&amp; 2*3*4", want: p("&amp; 2*3*4"), problem: true },
  { id: "d29", note: "같은 줄 앞에 역슬래시 이스케이프", input: "\\# 2*3*4", want: p("# 2*3*4"), problem: true },
  { id: "d30", note: "역슬래시로 쓴 별표는 원래 글자다", input: "2\\*3\\*4", want: p("2*3*4") },
  { id: "d31", note: "같은 줄 앞에 탭", input: "가\t2*3*4", want: p("가\t2*3*4"), problem: true },
  { id: "d32", note: "원문 맨 앞의 BOM", input: "﻿2*3*4", want: p("2*3*4"), problem: true },
  { id: "d33", note: "둘째 문단", input: "첫 문단\n\n둘째 문단 2*3*4", want: p("첫 문단") + p("둘째 문단 2*3*4"), problem: true },
  { id: "d34", input: "*강조*와 2*3*4", want: p(`${em("강조")}와 2*3*4`), problem: true },
  { id: "d35", note: "앞이 글자인 곱셈. 결정의 범위 밖이라 무엇이 나오는지 적는다", input: "x*2 + y*2", want: null },
  { id: "d36", note: "R1 과 R2 가 갈리는 사례", input: "3*x = 12, x*2 = 8", want: null },
  { id: "d37", note: "거듭제곱 표기. 결정의 범위 밖이라 적는다", input: "x**2 + y**2", want: null },
  { id: "d38", note: "글자 사이는 그대로 강조", input: "a*b*c", want: p(`a${em("b")}c`) },
  { id: "d39", note: "한글 사이는 그대로 강조", input: "가*나*다", want: p(`가${em("나")}다`) },
  { id: "d40", note: "R1 과 R2 가 갈리는 사례(숫자 사이에 일부러 쓴 강조)", input: "1*강조*2", want: null },
  { id: "d41", input: "2*3*4*5*6", want: p("2*3*4*5*6"), problem: true },
  { id: "d42", input: "5*5*5와 **굵게**", want: p(`5*5*5와 ${strong("굵게")}`), problem: true },
  { id: "d43", input: "__init__.py와 __main__.py", want: p("__init__.py와 __main__.py"), problem: true },
  { id: "d44", input: "2***3***4", want: p("2***3***4"), problem: true },
  {
    id: "d45",
    note: "링크 글 안의 밑줄 강조와 주소 안의 밑줄",
    input: "[_링크_](https://example.com/a_b_c)",
    want: p(a("https://example.com/a_b_c", "_링크_")),
    problem: true,
  },
  { id: "d46", note: "밑줄 안의 별표 굵게는 남는다", input: "_**둘 다**_", want: p(`_${strong("둘 다")}_`), problem: true },
  { id: "d47", note: "전각 숫자는 ASCII 숫자가 아니다. 무엇이 나오는지 적는다", input: "２*３*４", want: null },
  { id: "d48", note: "소수", input: "1.5*2.0*3", want: p("1.5*2.0*3"), problem: true },
  { id: "d49", note: "괄호 앞의 별표는 원래 글자다", input: "2*(3+4)*5", want: p("2*(3+4)*5") },
  { id: "d50", input: "`2*3*4`", want: p(code("2*3*4")) },
  { id: "d51", note: "별표 목록 기호 뒤", input: "* 2*3*4", want: ul("2*3*4"), problem: true },
  { id: "d52", note: "강조 안에 문자 참조", input: "2*3&amp;3*4", want: p("2*3&amp;3*4"), problem: true },
  { id: "d53", note: "강조 안에 역슬래시 이스케이프", input: "2*3\\_3*4", want: p("2*3_3*4"), problem: true },
  { id: "d54", note: "한쪽만 숫자 사이. 무엇이 나오는지 적는다", input: "2*3 그리고 x*4", want: null },
  { id: "d55", note: "짝 없는 숫자 사이 별표와 정상 굵게", input: "2*3 그리고 **굵게**", want: p(`2*3 그리고 ${strong("굵게")}`) },
  { id: "d56", input: "2*3 곱하기 *강조*", want: p(`2*3 곱하기 ${em("강조")}`) },
  { id: "d57", note: "여는 별표 앞이 없다. 적는다", input: "*2*3", want: null },
  { id: "d58", note: "닫는 별표 뒤가 없다. 적는다", input: "2*3*", want: null },
  // 아래 둘은 사람이 별표 규칙을 넓힌 규칙(R1)으로 고른 뒤 더했다(2026-11-11). 넓힌 규칙이 잡지 않는 식을 적는다.
  { id: "d59", note: "글자가 둘 낀 식. 무엇이 나오는지 적는다", input: "2*x*y*4", want: null },
  { id: "d60", note: "닫는 별표 뒤가 글자인 식. 무엇이 나오는지 적는다", input: "2*3*x", want: null },
];

// ── (나)와 (다)를 함께 켰을 때 ──────────────────────────────────────────────────────────────────────────────────
const INTERPLAY = [
  { id: "x01", note: "(다)가 글자로 둔 것을 (나)가 다시 굵게 만들지 않아야 한다", input: "2**3**4", want: p("2**3**4"), problem: true },
  {
    id: "x02",
    input: "2*3*4 = 24이고 **민법(가)**는 그렇다",
    want: p(`2*3*4 = 24이고 ${strong("민법(가)")}는 그렇다`),
    problem: true,
  },
  { id: "x03", input: "**민법(가)**는 2*3*4", want: p(`${strong("민법(가)")}는 2*3*4`), problem: true },
  { id: "x04", input: "__init__.py와 **민법(가)**는", want: p(`__init__.py와 ${strong("민법(가)")}는`), problem: true },
  { id: "x05", note: "닫히지 않는 굵게 안의 숫자 사이 별표", input: "**2*3*4(계산)**은", want: p(`${strong("2*3*4(계산)")}은`), problem: true },
  {
    id: "x06",
    input: "2**3**4 그리고 **참고(1)**를",
    want: p(`2**3**4 그리고 ${strong("참고(1)")}를`),
    problem: true,
  },
  { id: "x07", input: "3*4*5와 *기울임(주)*은", want: p(`3*4*5와 ${em("기울임(주)")}은`), problem: true },
  { id: "x08", input: "2*3*4와 5*는", want: p("2*3*4와 5*는"), problem: true },
  { id: "x09", input: "2*3 = 6이고 *참고(주)*는", want: p(`2*3 = 6이고 ${em("참고(주)")}는`), problem: true },
  { id: "x10", note: "밑줄은 닫히지 않는 모양이어도 글자다", input: "__민법(가)__는", want: p("__민법(가)__는") },
  { id: "x11", input: "**굵게** 2*3*4", want: p(`${strong("굵게")} 2*3*4`), problem: true },
];

// ── (라) 문장 끝 번호 ───────────────────────────────────────────────────────────────────────────────────────────
const BODY = "육아휴직은 최대 1년까지 쓸 수 있습니다";
const CITE = [
  { id: "c01", input: `${BODY}. [1]`, want: p(`${BODY}.${sup(1)}`), problem: true },
  { id: "c02", input: `${BODY}.[1]`, want: p(`${BODY}.${sup(1)}`), problem: true },
  { id: "c03", input: `${BODY}[1].`, want: p(`${BODY}${sup(1)}.`), problem: true },
  { id: "c04", note: "문장 가운데의 번호. 후보가 갈린다", input: "연구 [1]에 따르면 그렇다", want: null },
  { id: "c05", input: "그렇다 [1][2]", want: p(`그렇다${sup(1)}${sup(2)}`), problem: true },
  { id: "c06", input: "그렇다 [1] [2]", want: p(`그렇다${sup(1)}${sup(2)}`), problem: true },
  { id: "c07", input: "범위는 [1, 2] 이다", want: p("범위는 [1, 2] 이다") },
  { id: "c08", input: "범위는 [1-3] 이다", want: p("범위는 [1-3] 이다") },
  { id: "c09", input: "그렇다. [12]", want: p(`그렇다.${sup(12)}`), problem: true },
  { id: "c10", note: "네 자리 수(연도). 문장 가운데", input: "그해는 [2026] 이었다", want: null },
  { id: "c11", note: "네 자리 수(연도). 줄 끝", input: "출간 연도 [2026]", want: null },
  { id: "c12", note: "0 번", input: "그렇다. [0]", want: null },
  { id: "c13", input: "보기 [a] 를 고른다", want: p("보기 [a] 를 고른다") },
  { id: "c14", note: "배열 첨자", input: "값은 a[1] 이다", want: p("값은 a[1] 이다") },
  { id: "c15", note: "배열 첨자", input: "arr[0]은 첫 값이다", want: p("arr[0]은 첫 값이다") },
  { id: "c16", note: "배열 첨자", input: "x2[3] 을 읽는다", want: p("x2[3] 을 읽는다") },
  { id: "c17", note: "한글 바로 뒤. 번호인지 첨자인지 글만으로는 알 수 없다", input: "배열[1]", want: null },
  {
    id: "c18",
    note: "표 칸",
    input: tableMd(["항목", "근거"], ["기간", "1년 [1]"]),
    want: table(["항목", "근거"], [["기간", `1년${sup(1)}`]]),
    problem: true,
  },
  { id: "c19", note: "제목", input: "## 휴직 기간 [1]", want: el("h3", {}, `휴직 기간${sup(1)}`), problem: true },
  { id: "c20", note: "링크 글 안. 후보가 갈린다", input: "[판례 [1] 보기](https://example.com/)", want: null },
  { id: "c21", note: "줄 안 코드", input: "값은 `a[1]` 이고 `[1]` 이다", want: p(`값은 ${code("a[1]")} 이고 ${code("[1]")} 이다`) },
  { id: "c22", note: "코드 블록", input: `${FENCE}\n참고 [1]\n${FENCE}`, want: pre("참고 [1]\n") },
  {
    id: "c23",
    note: "출처 줄이 `[1] 문서 이름` 꼴로 시작한다(줄 머리의 번호는 위첨자가 아니어야 한다)",
    input: "출처\n\n[1] 육아휴직 업무편람\n[2] 인사 규정",
    want: p("출처") + p("[1] 육아휴직 업무편람\n[2] 인사 규정"),
  },
  {
    id: "c24",
    note: "목록 항목이 `[1] 문서 이름` 꼴로 시작한다",
    input: "- [1] 육아휴직 업무편람\n- [2] 인사 규정",
    want: ul("[1] 육아휴직 업무편람", "[2] 인사 규정"),
  },
  { id: "c25", note: "사실: `[1]: 주소` 정의가 있으면 `[1]` 은 링크가 된다", input: "본문입니다 [1].\n\n[1]: https://example.com/doc", want: null },
  { id: "c26", note: "사실: `[1][2]` 에서 2 만 정의가 있을 때", input: "본문 [1][2] 끝\n\n[2]: https://example.com/two", want: null },
  { id: "c27", note: "사실: GFM 각주", input: "본문입니다[^1].\n\n[^1]: 각주 글", want: null },
  { id: "c28", note: "`[1](주소)` 는 링크다", input: "본문 [1](https://example.com/) 끝", want: p(`본문 ${a("https://example.com/", "1")} 끝`) },
  { id: "c29", note: "역슬래시로 쓴 대괄호는 글자다", input: "본문 \\[1\\] 끝", want: p("본문 [1] 끝") },
  {
    id: "c30",
    note: "목록 항목의 끝",
    input: "- 첫째 항목입니다. [1]\n- 둘째 항목입니다. [2]",
    want: ul(`첫째 항목입니다.${sup(1)}`, `둘째 항목입니다.${sup(2)}`),
    problem: true,
  },
  { id: "c31", note: "인용의 끝", input: "> 인용문입니다. [3]", want: bq(p(`인용문입니다.${sup(3)}`)), problem: true },
  {
    id: "c32",
    note: "한 줄에 두 문장",
    input: "첫 문장입니다. [1] 둘째 문장입니다. [2]",
    want: p(`첫 문장입니다.${sup(1)} 둘째 문장입니다.${sup(2)}`),
    problem: true,
  },
  {
    id: "c33",
    note: "두 줄",
    input: "첫 문장입니다. [1]\n둘째 문장입니다. [2]",
    want: p(`첫 문장입니다.${sup(1)}\n둘째 문장입니다.${sup(2)}`),
    problem: true,
  },
  { id: "c34", note: "본문의 줄 머리에 온 번호. 후보가 갈린다", input: "[1] 에 따르면 그렇다", want: null },
  { id: "c35", note: "굵게 바로 뒤", input: "**중요합니다.** [1]", want: p(`${strong("중요합니다.")}${sup(1)}`), problem: true },
  { id: "c36", note: "굵게 안", input: "**중요합니다. [1]**", want: p(strong(`중요합니다.${sup(1)}`)), problem: true },
  { id: "c37", note: "이차원 배열 첨자", input: "A[1][2]", want: p("A[1][2]") },
  { id: "c38", input: "그렇다 [1], [2].", want: p(`그렇다${sup(1)},${sup(2)}.`), problem: true },
  { id: "c39", note: "세 자리 수", input: "그렇다. [123]", want: p(`그렇다.${sup(123)}`), problem: true },
  { id: "c40", note: "전각 대괄호는 번호가 아니다", input: "그렇다. ［1］", want: p("그렇다. ［1］") },
  { id: "c41", note: "빈칸이 든 대괄호는 번호가 아니다", input: "그렇다. [ 1 ]", want: p("그렇다. [ 1 ]") },
  { id: "c42", note: "이미지의 대체 글 안", input: "![그림 [1]](https://example.com/a.png)", want: p(img("그림 [1]")) },
  { id: "c43", note: "정의 없는 각주 표기는 글자다", input: "각주 [^1] 정의 없음", want: p("각주 [^1] 정의 없음") },
  { id: "c44", note: "사실: 주소 뒤에 붙은 `[1]`", input: "주소 https://example.com/a[1] 참고", want: null },
  { id: "c45", note: "한글 조사 앞의 번호 둘. 후보가 갈린다", input: "편람[1]과 규정[2]을 본다", want: null },
  { id: "c46", note: "닫는 괄호 앞", input: "(자세한 내용은 편람 참고 [1])", want: p(`(자세한 내용은 편람 참고${sup(1)})`), problem: true },
  { id: "c47", note: "빈칸 둘", input: "첫 문장입니다.  [1]", want: p(`첫 문장입니다.${sup(1)}`), problem: true },
  { id: "c48", note: "표 칸에 번호만 있다. 후보가 갈린다", input: tableMd(["근거"], ["[1]"]), want: null },
];

// ── (마) 출처 덩이 ──────────────────────────────────────────────────────────────────────────────────────────────
const SOURCE_LIST = ol("편람", "규정");
const wrapped = (label) => sources(label + SOURCE_LIST);
const SOURCES = [
  {
    id: "s01-base",
    input: "본문입니다. [1]\n\n출처\n\n1. 편람\n2. 규정",
    want: p("본문입니다. [1]") + wrapped(p("출처")),
    problem: true,
  },
  {
    id: "s02-no-blank-before-list",
    note: "사실: `출처` 바로 다음 줄이 `1. …` 이면 문단과 목록으로 갈리는가",
    input: "본문입니다.\n\n출처\n1. 편람\n2. 규정",
    want: p("본문입니다.") + wrapped(p("출처")),
    problem: true,
  },
  {
    id: "s03-label-is-last-line",
    note: "사실: 앞 문단과 `출처` 사이에 빈 줄이 없으면 `출처` 가 앞 문단의 마지막 줄로 붙는가. 문단을 갈라 알아볼 수 있는가",
    input: "본문입니다. [2]\n출처\n1. 편람\n2. 규정",
    want: null,
    wantBy: {
      "sources-narrow": p("본문입니다. [2]\n출처") + SOURCE_LIST,
      "sources-base": p("본문입니다. [2]\n출처") + SOURCE_LIST,
      "sources-wide": p("본문입니다. [2]") + wrapped(p("출처")),
      "sources-pick": p("본문입니다. [2]") + wrapped(p("출처")),
    },
  },
  {
    id: "s04-bold-label",
    input: "본문입니다.\n\n**출처**\n\n1. 편람\n2. 규정",
    want: null,
    wantBy: {
      "sources-base": p("본문입니다.") + p(strong("출처")) + SOURCE_LIST,
      "sources-pick": p("본문입니다.") + wrapped(p(strong("출처"))),
    },
  },
  {
    id: "s05-heading-label",
    input: "본문입니다.\n\n## 출처\n\n1. 편람\n2. 규정",
    want: null,
    wantBy: {
      "sources-narrow": p("본문입니다.") + el("h3", {}, "출처") + SOURCE_LIST,
      "sources-base": p("본문입니다.") + wrapped(el("h3", {}, "출처")),
      "sources-pick": p("본문입니다.") + wrapped(el("h3", {}, "출처")),
    },
  },
  {
    id: "s06-colon",
    input: "본문입니다.\n\n출처:\n\n1. 편람\n2. 규정",
    want: null,
    wantBy: {
      "sources-base": p("본문입니다.") + p("출처:") + SOURCE_LIST,
      "sources-pick": p("본문입니다.") + wrapped(p("출처:")),
    },
  },
  {
    id: "s07-unordered",
    input: "본문입니다.\n\n출처\n\n- 편람\n- 규정",
    want: null,
    wantBy: {
      "sources-base": p("본문입니다.") + p("출처") + ul("편람", "규정"),
      "sources-pick": p("본문입니다.") + p("출처") + ul("편람", "규정"),
      "sources-wide": p("본문입니다.") + sources(p("출처") + ul("편람", "규정")),
    },
  },
  {
    id: "s08-paragraph-after-list",
    note: "목록 뒤에 문단이 더 있으면 알아보지 않아야 한다",
    input: "본문입니다.\n\n출처\n\n1. 편람\n2. 규정\n\n더 궁금한 점이 있으면 물어보세요.",
    want: p("본문입니다.") + p("출처") + SOURCE_LIST + p("더 궁금한 점이 있으면 물어보세요."),
  },
  {
    id: "s09-in-the-middle",
    note: "`출처` 가 문서 가운데에 있으면 알아보지 않아야 한다",
    input: "출처\n\n1. 편람\n2. 규정\n\n## 본문\n\n내용입니다.",
    want: p("출처") + SOURCE_LIST + el("h3", {}, "본문") + p("내용입니다."),
  },
  { id: "s10-other-word-list", note: "다른 말", input: "본문입니다.\n\n출처 목록\n\n1. 편람\n2. 규정", want: p("본문입니다.") + p("출처 목록") + SOURCE_LIST },
  { id: "s11-other-word-ref", note: "다른 말", input: "본문입니다.\n\n참고\n\n1. 편람\n2. 규정", want: p("본문입니다.") + p("참고") + SOURCE_LIST },
  { id: "s12-other-word-english", note: "다른 말", input: "본문입니다.\n\nSources\n\n1. 편람\n2. 규정", want: p("본문입니다.") + p("Sources") + SOURCE_LIST },
  {
    id: "s13-bracket-lines-same-paragraph",
    note: "출처가 목록이 아니라 `[1] …` 줄들이고 `출처` 와 한 문단이다",
    input: "본문입니다. [1]\n\n출처\n[1] 편람\n[2] 규정",
    want: null,
    wantBy: {
      "sources-base": p("본문입니다. [1]") + p("출처\n[1] 편람\n[2] 규정"),
      "sources-pick": p("본문입니다. [1]") + sources(p("출처") + p("[1] 편람\n[2] 규정")),
    },
  },
  {
    id: "s14-bracket-lines-own-paragraph",
    input: "본문입니다. [1]\n\n출처\n\n[1] 편람\n[2] 규정",
    want: null,
    wantBy: {
      "sources-base": p("본문입니다. [1]") + p("출처") + p("[1] 편람\n[2] 규정"),
      "sources-pick": p("본문입니다. [1]") + sources(p("출처") + p("[1] 편람\n[2] 규정")),
    },
  },
  {
    id: "s15-only-sources",
    note: "출력 전체가 `출처` 와 목록뿐이다",
    input: "출처\n\n1. 편람\n2. 규정",
    want: null,
    wantBy: { "sources-narrow": wrapped(p("출처")), "sources-base": wrapped(p("출처")), "sources-pick": wrapped(p("출처")) },
  },
  { id: "s16-crlf", input: "본문입니다.\r\n\r\n출처\r\n1. 편람\r\n2. 규정", want: p("본문입니다.") + wrapped(p("출처")), problem: true },
  {
    id: "s17-loose-list",
    note: "항목 사이에 빈 줄이 있는 목록",
    input: "본문입니다.\n\n출처\n\n1. 편람\n\n2. 규정",
    want: p("본문입니다.") + sources(p("출처") + ol(p("편람"), p("규정"))),
    problem: true,
  },
  {
    id: "s18-after-rule",
    input: "본문입니다.\n\n---\n\n출처\n\n1. 편람\n2. 규정",
    want: p("본문입니다.") + el("hr") + wrapped(p("출처")),
    problem: true,
  },
  {
    id: "s19-inside-blockquote",
    note: "최상위가 아닌 자리(인용 안)는 알아보지 않는다",
    input: "본문입니다.\n\n> 출처\n> 1. 편람\n> 2. 규정",
    want: p("본문입니다.") + bq(p("출처") + SOURCE_LIST),
  },
  {
    id: "s20-list-starts-at-2",
    input: "본문입니다.\n\n출처\n\n2. 규정\n3. 세칙",
    want: null,
    wantBy: {
      "sources-pick": p("본문입니다.") + sources(p("출처") + el("ol", { start: "2" }, li("규정") + li("세칙"))),
    },
  },
  {
    id: "s21-list-starts-at-2-no-blank",
    note: "사실: 1 로 시작하지 않는 번호 목록은 문단을 끊지 못한다",
    input: "본문입니다.\n\n출처\n2. 규정\n3. 세칙",
    want: null,
  },
  { id: "s22-paren-delimiter", input: "본문입니다.\n\n출처\n1) 편람\n2) 규정", want: p("본문입니다.") + wrapped(p("출처")), problem: true },
  { id: "s23-label-trailing-spaces", input: "본문입니다.\n\n출처  \n1. 편람\n2. 규정", want: p("본문입니다.") + wrapped(p("출처")), problem: true },
  {
    id: "s24-bold-colon",
    input: "**출처:**\n\n1. 편람\n2. 규정",
    want: null,
    wantBy: { "sources-base": p(strong("출처:")) + SOURCE_LIST, "sources-pick": wrapped(p(strong("출처:"))) },
  },
  {
    id: "s25-heading-bracket-lines",
    input: "## 출처\n\n[1] 편람\n[2] 규정",
    want: null,
    wantBy: { "sources-pick": sources(el("h3", {}, "출처") + p("[1] 편람\n[2] 규정")) },
  },
  {
    id: "s26-plain-list-no-label",
    note: "표지 없는 번호 목록으로 끝나는 출력은 알아보지 않는다",
    input: "준비물은 다음과 같습니다.\n\n1. 신분증\n2. 신청서",
    want: p("준비물은 다음과 같습니다.") + ol("신분증", "신청서"),
  },
  {
    id: "s27-link-in-item",
    input: "출처\n\n1. [편람](https://example.com/a)\n2. 규정",
    want: null,
    wantBy: { "sources-pick": sources(p("출처") + ol(a("https://example.com/a", "편람"), "규정")) },
  },
  { id: "s28-inline-label", note: "`출처: …` 한 줄은 덩이가 아니다", input: "출처: 육아휴직 업무편람 12쪽", want: p("출처: 육아휴직 업무편람 12쪽") },
  {
    id: "s29-design-input",
    note: "화면 파일 mk-cite 의 원문",
    input:
      "육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다. [1]\n신청서는 휴직 시작 30일 전까지 내야 합니다. [2]\n\n출처\n1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)\n2. 인사 규정, 제3장 제14조 (갱신일 2026-08-15)",
    want:
      p("육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다. [1]\n신청서는 휴직 시작 30일 전까지 내야 합니다. [2]") +
      sources(p("출처") + ol("육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)", "인사 규정, 제3장 제14조 (갱신일 2026-08-15)")),
    problem: true,
  },
  { id: "s30-trailing-blank-lines", input: "출처\n\n1. 편람\n2. 규정\n\n", want: null, wantBy: { "sources-pick": wrapped(p("출처")) } },
  {
    id: "s31-label-joins-previous-list",
    note: "사실: 본문이 목록으로 끝나고 빈 줄 없이 `출처` 가 오면 `출처` 는 마지막 항목에 붙는다",
    input: "1. 첫째 단계\n2. 둘째 단계\n출처\n1. 편람",
    want: null,
  },
  {
    id: "s32-body-list-then-sources",
    input: "1. 첫째 단계\n2. 둘째 단계\n\n출처\n\n1. 편람\n2. 규정",
    want: ol("첫째 단계", "둘째 단계") + wrapped(p("출처")),
    problem: true,
  },
];

// ── 링크 주소의 사용자 정보 ─────────────────────────────────────────────────────────────────────────────────────
const LINKS = [
  { id: "l01-userinfo-host", note: "기존 사례 x28 과 같은 입력", input: "[은행](https://www.law.go.kr@evil.example/login)", want: p("은행") },
  { id: "l02-user-password", input: "[가](https://user:pw@host.example/)", want: p("가") },
  { id: "l03-user-only", input: "[가](https://user@host.example/)", want: p("가") },
  { id: "l04-empty-userinfo", note: "`@` 앞이 빈 주소. 무엇이 나오는지 적는다", input: "[가](https://@host.example/)", want: null },
  { id: "l05-empty-password", input: "[가](https://www.law.go.kr:@evil.example/)", want: p("가") },
  { id: "l06-angle-autolink", input: "<https://www.law.go.kr@evil.example/>", want: p("https://www.law.go.kr@evil.example/") },
  {
    id: "l07-bare-autolink",
    note: "화면 파일 mk-unsafe 의 마지막 줄",
    input: "https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다.",
    want: p("https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다."),
  },
  { id: "l08-escaped-at", input: "[가](https://www.law.go.kr\\@evil.example/)", want: p("가") },
  { id: "l09-uppercase", input: "[가](HTTPS://USER@EXAMPLE.COM/)", want: p("가") },
  { id: "l10-percent-encoded-at", note: "`%40`. 무엇이 나오는지 적는다", input: "[가](https://www.law.go.kr%40evil.example/)", want: null },
  { id: "l11-normal", note: "대조: 정상 링크", input: "[법령](https://www.law.go.kr/)", want: p(a("https://www.law.go.kr/", "법령")) },
  { id: "l12-www-at", input: "www.law.go.kr@evil.example", want: p("www.law.go.kr@evil.example") },
  { id: "l13-email", input: "문의는 help@example.com 으로", want: p("문의는 help@example.com 으로") },
  { id: "l14-title", note: "title 은 그리지 않는다", input: '[가](https://example.com/ "제목")', want: p(a("https://example.com/", "가")) },
  { id: "l15-reference", input: "[가][r]\n\n[r]: https://u:p@host.example/", want: p("가") },
  { id: "l16-http-query", input: "[가](http://example.com/a?b=1&c=2)", want: p(a("http://example.com/a?b=1&c=2", "가")) },
  { id: "l17-userinfo-in-path", note: "대조: 경로의 `@` 는 사용자 정보가 아니다", input: "[가](https://example.com/@user)", want: p(a("https://example.com/@user", "가")) },
];

// ── 목표 모양의 나머지(제목, 이미지, 표, 코드 블록) ─────────────────────────────────────────────────────────────
const SHAPE = [
  {
    id: "h01-headings",
    input: "# 하나\n\n## 둘\n\n### 셋\n\n#### 넷\n\n##### 다섯\n\n###### 여섯",
    want:
      el("h2", {}, "하나") + el("h3", {}, "둘") + el("h4", {}, "셋") + el("h5", {}, "넷") + el("h6", {}, "다섯") + el("h6", {}, "여섯"),
  },
  { id: "h02-setext", input: "제목\n===\n\n부제\n---", want: el("h2", {}, "제목") + el("h3", {}, "부제") },
  { id: "i01-image", input: "![영수증 사진](https://tracker.example/r.png?id=184)", want: p(img("영수증 사진")) },
  { id: "i02-image-no-alt", input: "![](https://tracker.example/r.png)", want: p(img("")) },
  { id: "i03-image-js", input: "![그림](javascript:alert(1))", want: p(img("그림")) },
  { id: "i04-image-in-link", input: "[![배지](https://img.example/b.svg)](https://example.com/)", want: p(a("https://example.com/", img("배지"))) },
  { id: "i05-image-alt-emphasis", input: "![**굵은** 글](https://a.example/x.png)", want: p(img("굵은 글")) },
  {
    id: "t01-table-align",
    input: "| 가 | 나 |\n| :-- | --: |\n| 1 | 2 |",
    want: el(
      "div",
      { class: "tbl", role: "region", "aria-label": "표", tabindex: "0" },
      el(
        "table",
        {},
        el("thead", {}, el("tr", {}, el("th", { style: "text-align:left" }, "가") + el("th", { style: "text-align:right" }, "나"))) +
          el("tbody", {}, el("tr", {}, el("td", { style: "text-align:left" }, "1") + el("td", { style: "text-align:right" }, "2"))),
      ),
    ),
  },
  { id: "k01-code-lang", input: `${FENCE}bash\ncurl -X POST https://example.com/\n${FENCE}`, want: pre("curl -X POST https://example.com/\n", "bash") },
  { id: "k02-code-indented", note: "네 칸 들여쓴 코드 블록", input: "    들여쓴 코드", want: pre("들여쓴 코드\n") },
  // 각주 문법은 글자 그대로 남는다(footnotes.ts). 다섯 사례의 기대는 그 변환을 넣고 결과를 보기 전에 적었다(2026-11-11).
  { id: "f01-footnote", input: "본문입니다[^1].\n\n[^1]: 각주 글", want: p("본문입니다[^1].") + p("[^1]: 각주 글") },
  {
    id: "f02-footnote-before-body",
    note: "정의는 놓인 자리에 남는다(끝으로 옮기지 않는다)",
    input: "첫 문장입니다[^a].\n\n[^a]: 각주의 글\n\n둘째 문단입니다.",
    want: p("첫 문장입니다[^a].") + p("[^a]: 각주의 글") + p("둘째 문단입니다."),
  },
  {
    id: "f03-footnote-with-marks",
    note: "정의 안의 서식은 그린다",
    input: "근거[^1]\n\n[^1]: **민법** 제750조",
    want: p("근거[^1]") + p(`[^1]: ${strong("민법")} 제750조`),
  },
  { id: "f04-footnote-two-refs", input: "하나[^1] 둘[^1]\n\n[^1]: 글", want: p("하나[^1] 둘[^1]") + p("[^1]: 글") },
  {
    id: "f05-footnote-multi-block",
    note: "정의가 여러 블록이면 이어서 선다",
    input: "본문[^1]\n\n[^1]: 첫 문단\n\n    둘째 문단",
    want: p("본문[^1]") + p("[^1]: 첫 문단") + p("둘째 문단"),
  },
  // 할 일 목록의 표시(`[ ]`, `[x]`)는 글자 그대로 남는다(task-marks.ts). 사례의 기대는 그 변환을 넣기 전에(g06 은 변환의
  // 첫 판을 돌리기 전에) 적었다(2026-11-11). 변환이 없는 판에서는 표시가 사라져 g05 를 뺀 사례가 목표와 달라야 한다
  // (README 가 그 실행을 적는다).
  { id: "g01-task-list", input: "- [ ] 할 일\n- [x] 한 일", want: ul("[ ] 할 일", "[x] 한 일") },
  { id: "g02-task-upper", note: "대문자 X 도 원문 그대로 둔다", input: "- [X] 끝남", want: ul("[X] 끝남") },
  {
    id: "g03-task-with-marks",
    note: "항목 안의 서식은 그린다",
    input: "- [x] **서류** 제출",
    want: ul(`[x] ${strong("서류")} 제출`),
  },
  { id: "g04-task-ordered", input: "1. [x] 하나\n2. [ ] 둘", want: ol("[x] 하나", "[ ] 둘") },
  {
    id: "g06-task-upper-then-strong",
    note: "표시 바로 뒤가 굵게이면 파서가 문단의 시작 위치를 옮기지 않는다. 그때도 대문자 X 를 원문 그대로 둔다",
    input: "- [X] **굵게** 뒤",
    want: ul(`[X] ${strong("굵게")} 뒤`),
  },
  {
    id: "g05-task-not-a-task",
    note: "표시가 아닌 대괄호는 처음부터 글자다(변환이 없어도 목표와 같다)",
    input: "- [x]붙은 글\n- 그냥 항목",
    want: ul("[x]붙은 글", "그냥 항목"),
  },
];

// ── 합친 시제품 ─────────────────────────────────────────────────────────────────────────────────────────────────
export const SCREEN_INPUTS = {
  "mk-cite":
    "육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다. [1]\n신청서는 휴직 시작 30일 전까지 내야 합니다. [2]\n\n출처\n1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)\n2. 인사 규정, 제3장 제14조 (갱신일 2026-08-15)",
  "mk-side-1": "2*3*4 = 24입니다.",
  "mk-side-2":
    "**민법 제750조(불법행위)**는 고의나 과실로 남에게 손해를 입힌 사람이 갚아야 한다고 정합니다.\n# 1번 항목은 다음 쪽에 있습니다.\n설정 파일은 __init__.py 옆에 둡니다.",
  "mk-unsafe": [
    "요청하신 영수증입니다.",
    "![영수증 사진](https://tracker.example/r.png?id=184)",
    "<b>배송 지연</b> 보상은 <script>alert(1)</script> 결제한 수단으로 돌아갑니다.",
    "[환불 안내](javascript:alert(1))를 확인해 주세요.",
    "정상 주소는 [주문 내역](https://shop.example.com/orders)입니다.",
    "https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다.",
  ].join("\n"),
  "mk-all": [
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
    "### 필요한 서류",
    "| 서류 | 내는 곳 | 기한 | 비고 |",
    "|---|---|---|---|",
    "| 휴직 신청서 | 인사 시스템 | 시작 30일 전 | 부서장 승인 필요 |",
    "| 가족관계증명서 | 인사팀 메일 | 시작 7일 전 | 3개월 안에 뗀 것 |",
    "| 출생증명서 사본 | 인사팀 메일 | 시작 7일 전 | 출산 전이면 출산 뒤 30일 안 |",
    "",
    "> 회사 규정과 법이 다르면 법이 우선합니다.",
    "",
    "신청서 번호는 `LV-2026-000184` 꼴로 옵니다. 시작일은 ~~11월 30일~~ 12월 1일로 바뀌었습니다. 자세한 안내는 [인사 시스템 도움말](https://hr.example.com/help/leave)에 있습니다.",
    "",
    "---",
    "인사 시스템 API로 낼 때는 아래처럼 보냅니다.",
    `${FENCE}bash`,
    `curl -X POST https://hr.example.com/api/v1/leave-requests -H "Content-Type: application/json" -d '{"type":"parental","start":"2026-12-01","end":"2027-11-30"}'`,
    FENCE,
  ].join("\n"),
};

/** 화면 파일과 그 안의 몇째 `div.md` 가 어느 입력의 목표인지. */
export const SCREENS = [
  { file: "mk-cite-320.dc.html", index: 0, input: "mk-cite" },
  { file: "mk-side-320.dc.html", index: 0, input: "mk-side-1" },
  { file: "mk-side-320.dc.html", index: 1, input: "mk-side-2" },
  { file: "mk-unsafe-320.dc.html", index: 0, input: "mk-unsafe" },
  { file: "mk-all-320.dc.html", index: 0, input: "mk-all" },
];

const CITE_BODY_1 = "육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다.";
const CITE_BODY_2 = "신청서는 휴직 시작 30일 전까지 내야 합니다.";
const COMBINED = [
  {
    id: "m01-mk-cite",
    input: SCREEN_INPUTS["mk-cite"],
    want:
      p(`${CITE_BODY_1}${sup(1)}${BR}${CITE_BODY_2}${sup(2)}`) +
      sources(p("출처") + ol("육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)", "인사 규정, 제3장 제14조 (갱신일 2026-08-15)")),
    problem: true,
  },
  { id: "m02-mk-side-1", input: SCREEN_INPUTS["mk-side-1"], want: p("2*3*4 = 24입니다."), problem: true },
  {
    id: "m03-mk-side-2",
    input: SCREEN_INPUTS["mk-side-2"],
    want:
      p(`${strong("민법 제750조(불법행위)")}는 고의나 과실로 남에게 손해를 입힌 사람이 갚아야 한다고 정합니다.`) +
      el("h2", {}, "1번 항목은 다음 쪽에 있습니다.") +
      p("설정 파일은 __init__.py 옆에 둡니다."),
    problem: true,
  },
  {
    id: "m04-mk-unsafe",
    input: SCREEN_INPUTS["mk-unsafe"],
    want: p(
      [
        "요청하신 영수증입니다.",
        img("영수증 사진"),
        "&lt;b&gt;배송 지연&lt;/b&gt; 보상은 &lt;script&gt;alert(1)&lt;/script&gt; 결제한 수단으로 돌아갑니다.",
        "환불 안내를 확인해 주세요.",
        `정상 주소는 ${a("https://shop.example.com/orders", "주문 내역")}입니다.`,
        "https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다.",
      ].join(BR),
    ),
    problem: true,
  },
  {
    id: "m05-mk-all",
    input: SCREEN_INPUTS["mk-all"],
    want:
      el("h2", {}, "육아휴직 신청 안내") +
      el("h3", {}, "신청 절차") +
      p(
        `휴직 시작 ${strong("30일 전")}까지 인사 시스템에서 신청서를 냅니다.${BR}부서장이 승인하면 인사팀이 ${em("3일 안에")} 확정 문자를 보냅니다.`,
      ) +
      ol(
        "인사 시스템에 로그인합니다.",
        `${strong("휴가·휴직")} 메뉴에서 육아휴직을 고릅니다.${ul("시작일과 끝나는 날을 적습니다.", "나눠 쓰려면 기간마다 따로 냅니다.")}`,
        "서류를 올리고 냅니다.",
      ) +
      el("h4", {}, "필요한 서류") +
      table(
        ["서류", "내는 곳", "기한", "비고"],
        [
          ["휴직 신청서", "인사 시스템", "시작 30일 전", "부서장 승인 필요"],
          ["가족관계증명서", "인사팀 메일", "시작 7일 전", "3개월 안에 뗀 것"],
          ["출생증명서 사본", "인사팀 메일", "시작 7일 전", "출산 전이면 출산 뒤 30일 안"],
        ],
      ) +
      bq(p("회사 규정과 법이 다르면 법이 우선합니다.")) +
      p(
        `신청서 번호는 ${code("LV-2026-000184")} 꼴로 옵니다. 시작일은 ${el("del", {}, "11월 30일")} 12월 1일로 바뀌었습니다. 자세한 안내는 ${a("https://hr.example.com/help/leave", "인사 시스템 도움말")}에 있습니다.`,
      ) +
      el("hr") +
      p("인사 시스템 API로 낼 때는 아래처럼 보냅니다.") +
      pre(
        `curl -X POST https://hr.example.com/api/v1/leave-requests -H "Content-Type: application/json" -d '{"type":"parental","start":"2026-12-01","end":"2027-11-30"}'\n`,
        "bash",
      ),
    problem: true,
  },
  {
    id: "m06-all-five",
    note: "다섯 처리가 한 출력에 다 걸린다",
    input: "**요건(가)**은 다음과 같습니다. [1]\n계산은 2*3*4입니다. [2]\n\n출처\n1. 민법 해설\n2. 계산 편람",
    want:
      p(`${strong("요건(가)")}은 다음과 같습니다.${sup(1)}${BR}계산은 2*3*4입니다.${sup(2)}`) +
      sources(p("출처") + ol("민법 해설", "계산 편람")),
    problem: true,
  },
  {
    id: "m07-label-is-last-line",
    note: "`출처` 가 앞 문단의 마지막 줄이다",
    input: "첫 문장입니다. [1]\n둘째 문장입니다. [2]\n출처\n1. 편람\n2. 규정",
    want: p(`첫 문장입니다.${sup(1)}${BR}둘째 문장입니다.${sup(2)}`) + sources(p("출처") + SOURCE_LIST),
    problem: true,
  },
  {
    id: "m08-bracket-sources",
    note: "출처가 `[1] …` 줄들이다. 출처 덩이 안의 `[1]` 은 번호로 바꾸지 않는다",
    input: "가능합니다[1][2].\n\n출처\n[1] 민법 제750조 (갱신 2026-01-02)\n[2] 안내문",
    want: p(`가능합니다${sup(1)}${sup(2)}.`) + sources(p("출처") + p(`[1] 민법 제750조 (갱신 2026-01-02)${BR}[2] 안내문`)),
    problem: true,
  },
  {
    id: "m09-code-block-untouched",
    input: `${FENCE}\n값 [1] 2*3*4 **민법(가)**는 __init__\n${FENCE}`,
    want: pre("값 [1] 2*3*4 **민법(가)**는 __init__\n"),
  },
  {
    id: "m10-inline-code-untouched",
    input: "`a[1]` 과 `2*3*4` 와 `__init__`",
    want: p(`${code("a[1]")} 과 ${code("2*3*4")} 와 ${code("__init__")}`),
  },
  { id: "m11-heading", input: "## **요약(가)**의 결과 [1]", want: el("h3", {}, `${strong("요약(가)")}의 결과${sup(1)}`), problem: true },
  {
    id: "m12-table",
    input: tableMd(["식", "근거"], ["2*3*4", "**편람(가)**는 [1]"]),
    want: table(["식", "근거"], [["2*3*4", `${strong("편람(가)")}는${sup(1)}`]]),
    problem: true,
  },
  { id: "m13-empty", input: "", want: "" },
  { id: "m14-blank", input: "  \n\n", want: "" },
  { id: "m15-single", input: "4", want: p("4") },
  {
    id: "m16-text-after-sources",
    note: "목록 뒤에 문단이 더 있으면 출처 덩이가 아니다",
    input: "본문 [1]\n\n출처\n1. 편람\n\n감사합니다.",
    want: p(`본문${sup(1)}`) + p("출처") + ol("편람") + p("감사합니다."),
    problem: true,
  },
  {
    id: "m17-brackets-inside-sources",
    input: "본문입니다. [1]\n\n출처\n1. 편람 [개정 3판]\n2. 규정 [2]",
    want: p(`본문입니다.${sup(1)}`) + sources(p("출처") + ol("편람 [개정 3판]", "규정 [2]")),
    problem: true,
  },
];

export const GROUPS = [
  { name: "breaks", title: "(가) 한 줄 바꿈", control: "base", candidates: ["breaks-plugin", "breaks-own"], cases: BREAKS },
  { name: "cjk", title: "(나) 닫히지 않는 굵게", control: "base", candidates: ["cjk-plugin", "cjk-plugin-first", "cjk-own"], cases: CJK },
  { name: "literal", title: "(다) 숫자 사이 별표와 밑줄", control: "base", candidates: ["literal-r2", "literal-r1", "literal-syntax"], cases: LITERAL },
  {
    name: "interplay",
    title: "(나)와 (다)를 함께",
    control: "base",
    // `syntax+own-cjk` 는 첫 결과를 본 뒤 더했다(2026-11-11). 뒤의 두 갈래(R1)는 사람이 별표 규칙을 넓힌 규칙으로 고른 뒤
    // 더했다(같은 날). 두 번 모두 기대는 바꾸지 않았다.
    candidates: [
      "own-cjk>r2",
      "r2>own-cjk",
      "cjk-plugin+r2",
      "cjk-plugin>syntax",
      "syntax>cjk-plugin",
      "syntax+own-cjk",
      "own-cjk>r1",
      "r1>own-cjk",
    ],
    cases: INTERPLAY,
  },
  { name: "cite", title: "(라) 문장 끝 번호", control: "base", candidates: ["cite-a", "cite-b", "cite-c", "cite-d"], cases: CITE },
  {
    name: "sources",
    title: "(마) 출처 덩이",
    control: "base",
    candidates: ["sources-narrow", "sources-base", "sources-wide", "sources-pick", "breaks>sources-pick", "sources-pick>breaks"],
    // 줄바꿈 변환을 함께 켠 두 갈래는 `<br>` 을 줄 끝 글자로 되돌린 뒤 같은 기대와 견준다(출처를 알아보는지만 본다).
    undoBreaks: ["breaks>sources-pick", "sources-pick>breaks"],
    sameAs: { "breaks>sources-pick": "sources-pick", "sources-pick>breaks": "sources-pick" },
    cases: SOURCES,
  },
  { name: "links", title: "링크 주소의 사용자 정보", control: null, candidates: ["combined"], cases: LINKS },
  { name: "shape", title: "제목·이미지·표·코드 블록", control: null, candidates: ["combined"], cases: SHAPE },
  {
    name: "combined",
    title: "합친 시제품",
    control: "base",
    candidates: ["combined", "combined-breaks-plugin", "combined-cjk-plugin"],
    cases: COMBINED,
  },
];

/** 기존 입력 52가지(cases.mjs)를 합친 시제품으로 그렸을 때, 목표 모양 때문에 기존 기대(must)가 어긋날 자리. 미리 적었다. */
export const EXPECTED_MUST_FAILURES = {
  "r06-normal-link": "링크 글 뒤에 `(새 탭에서 열림)` 이 붙어 링크의 글이 `정상` 과 같지 않다",
  "r10-korean-bold-footnote": "`[1]` 이 위첨자가 되어 글에 `[1]` 이 없다",
  "x14-source-list": "본문의 `[1][2]` 가 위첨자가 되어 글에 `[1][2]` 가 없다",
  "x53-blocks": "제목을 한 단계 낮춰 `h1` 이 없다",
};
