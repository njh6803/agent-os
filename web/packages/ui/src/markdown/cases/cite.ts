// 문장 끝 번호 48가지(answer-markdown 명세 "문장 끝 번호", 티켓 02). 원천은 프로브의 사례 파일 `shape-cases.mjs` 의 `CITE` 이고
// 입력과 목표는 글자 그대로 옮겼다. 다른 자리는 셋이다.
// - 프로브는 이 묶음에서 번호 변환만 켰다. 부품은 변환을 늘 모두 켜므로, 문단 안의 줄 끝 글자는 줄바꿈(`BR`)으로(`c33`),
//   "출처" 문단과 `[숫자]` 줄 문단으로 끝나는 출력은 출처 덩이로(`c23`) 옮겼다. 두 사례가 재려던 것(번호를 줄마다 위첨자로
//   바꾸는지, 줄 머리의 번호를 글자로 두는지)은 그대로다.
// - 목표를 적지 않은 입력(`want` 가 null)은 지금의 결과를 `pinned` 로 고정한다. 명세 "문장 끝 번호"가 결과를 적은 것은 그
//   글과 맞대어 적었다.
// - 사례 파일에 없는 번호의 경계 입력(`CITE_EDGES`)을 더했다. 명세 "문장 끝 번호"의 받아들이는 한계가 적고 일지
//   2026-11-11-1057 의 "셀프 리뷰" 절이 손으로 본 결과다.
import { a, BR, bq, code, el, img, ol, p, pre, sources, strong, sup, table, ul } from "./skeleton";
import { type ShapeCase, tableMd } from "./breaks";

const FENCE = "```";

const BODY = "육아휴직은 최대 1년까지 쓸 수 있습니다";
export const CITE: readonly ShapeCase[] = [
  { id: "c01", input: `${BODY}. [1]`, want: p(`${BODY}.${sup(1)}`) },
  { id: "c02", input: `${BODY}.[1]`, want: p(`${BODY}.${sup(1)}`) },
  { id: "c03", input: `${BODY}[1].`, want: p(`${BODY}${sup(1)}.`) },
  {
    id: "c04",
    note: "문장 가운데의 번호. 후보가 갈린다",
    input: "연구 [1]에 따르면 그렇다",
    want: null,
    pinned: p(`연구${sup(1)}에 따르면 그렇다`),
  },
  { id: "c05", input: "그렇다 [1][2]", want: p(`그렇다${sup(1)}${sup(2)}`) },
  { id: "c06", input: "그렇다 [1] [2]", want: p(`그렇다${sup(1)}${sup(2)}`) },
  { id: "c07", input: "범위는 [1, 2] 이다", want: p("범위는 [1, 2] 이다") },
  { id: "c08", input: "범위는 [1-3] 이다", want: p("범위는 [1-3] 이다") },
  { id: "c09", input: "그렇다. [12]", want: p(`그렇다.${sup(12)}`) },
  {
    id: "c10",
    note: "네 자리 수(연도). 문장 가운데",
    input: "그해는 [2026] 이었다",
    want: null,
    pinned: p("그해는 [2026] 이었다"),
  },
  {
    id: "c11",
    note: "네 자리 수(연도). 줄 끝",
    input: "출간 연도 [2026]",
    want: null,
    pinned: p("출간 연도 [2026]"),
  },
  { id: "c12", note: "0 번", input: "그렇다. [0]", want: null, pinned: p(`그렇다.${sup(0)}`) },
  { id: "c13", input: "보기 [a] 를 고른다", want: p("보기 [a] 를 고른다") },
  { id: "c14", note: "배열 첨자", input: "값은 a[1] 이다", want: p("값은 a[1] 이다") },
  { id: "c15", note: "배열 첨자", input: "arr[0]은 첫 값이다", want: p("arr[0]은 첫 값이다") },
  { id: "c16", note: "배열 첨자", input: "x2[3] 을 읽는다", want: p("x2[3] 을 읽는다") },
  {
    id: "c17",
    note: "한글 바로 뒤. 번호인지 첨자인지 글만으로는 알 수 없다",
    input: "배열[1]",
    want: null,
    pinned: p(`배열${sup(1)}`),
  },
  {
    id: "c18",
    note: "표 칸",
    input: tableMd(["항목", "근거"], ["기간", "1년 [1]"]),
    want: table(["항목", "근거"], [["기간", `1년${sup(1)}`]]),
  },
  { id: "c19", note: "제목", input: "## 휴직 기간 [1]", want: el("h3", {}, `휴직 기간${sup(1)}`) },
  {
    id: "c20",
    note: "링크 글 안. 후보가 갈린다",
    input: "[판례 [1] 보기](https://example.com/)",
    want: null,
    pinned: p(a("https://example.com/", "판례 [1] 보기")),
  },
  {
    id: "c21",
    note: "줄 안 코드",
    input: "값은 `a[1]` 이고 `[1]` 이다",
    want: p(`값은 ${code("a[1]")} 이고 ${code("[1]")} 이다`),
  },
  { id: "c22", note: "코드 블록", input: `${FENCE}\n참고 [1]\n${FENCE}`, want: pre("참고 [1]\n") },
  {
    id: "c23",
    note: "출처 줄이 `[1] 문서 이름` 꼴로 시작한다(줄 머리의 번호는 위첨자가 아니어야 한다)",
    input: "출처\n\n[1] 육아휴직 업무편람\n[2] 인사 규정",
    want: sources(p("출처") + p(`[1] 육아휴직 업무편람${BR}[2] 인사 규정`)),
  },
  {
    id: "c24",
    note: "목록 항목이 `[1] 문서 이름` 꼴로 시작한다",
    input: "- [1] 육아휴직 업무편람\n- [2] 인사 규정",
    want: ul("[1] 육아휴직 업무편람", "[2] 인사 규정"),
  },
  {
    id: "c25",
    note: "사실: `[1]: 주소` 정의가 있으면 `[1]` 은 링크가 된다",
    input: "본문입니다 [1].\n\n[1]: https://example.com/doc",
    want: null,
    pinned: p(`본문입니다 ${a("https://example.com/doc", "1")}.`),
  },
  {
    id: "c26",
    note: "사실: `[1][2]` 에서 2 만 정의가 있을 때",
    input: "본문 [1][2] 끝\n\n[2]: https://example.com/two",
    want: null,
    pinned: p(`본문 ${a("https://example.com/two", "1")} 끝`),
  },
  {
    id: "c27",
    note: "사실: GFM 각주",
    input: "본문입니다[^1].\n\n[^1]: 각주 글",
    want: null,
    pinned: p("본문입니다[^1].") + p("[^1]: 각주 글"),
  },
  {
    id: "c28",
    note: "`[1](주소)` 는 링크다",
    input: "본문 [1](https://example.com/) 끝",
    want: p(`본문 ${a("https://example.com/", "1")} 끝`),
  },
  {
    id: "c29",
    note: "역슬래시로 쓴 대괄호는 글자다",
    input: "본문 \\[1\\] 끝",
    want: p("본문 [1] 끝"),
  },
  {
    id: "c30",
    note: "목록 항목의 끝",
    input: "- 첫째 항목입니다. [1]\n- 둘째 항목입니다. [2]",
    want: ul(`첫째 항목입니다.${sup(1)}`, `둘째 항목입니다.${sup(2)}`),
  },
  {
    id: "c31",
    note: "인용의 끝",
    input: "> 인용문입니다. [3]",
    want: bq(p(`인용문입니다.${sup(3)}`)),
  },
  {
    id: "c32",
    note: "한 줄에 두 문장",
    input: "첫 문장입니다. [1] 둘째 문장입니다. [2]",
    want: p(`첫 문장입니다.${sup(1)} 둘째 문장입니다.${sup(2)}`),
  },
  {
    id: "c33",
    note: "두 줄",
    input: "첫 문장입니다. [1]\n둘째 문장입니다. [2]",
    want: p(`첫 문장입니다.${sup(1)}${BR}둘째 문장입니다.${sup(2)}`),
  },
  {
    id: "c34",
    note: "본문의 줄 머리에 온 번호. 후보가 갈린다",
    input: "[1] 에 따르면 그렇다",
    want: null,
    pinned: p("[1] 에 따르면 그렇다"),
  },
  {
    id: "c35",
    note: "굵게 바로 뒤",
    input: "**중요합니다.** [1]",
    want: p(`${strong("중요합니다.")}${sup(1)}`),
  },
  {
    id: "c36",
    note: "굵게 안",
    input: "**중요합니다. [1]**",
    want: p(strong(`중요합니다.${sup(1)}`)),
  },
  { id: "c37", note: "이차원 배열 첨자", input: "A[1][2]", want: p("A[1][2]") },
  { id: "c38", input: "그렇다 [1], [2].", want: p(`그렇다${sup(1)},${sup(2)}.`) },
  { id: "c39", note: "세 자리 수", input: "그렇다. [123]", want: p(`그렇다.${sup(123)}`) },
  {
    id: "c40",
    note: "전각 대괄호는 번호가 아니다",
    input: "그렇다. ［1］",
    want: p("그렇다. ［1］"),
  },
  {
    id: "c41",
    note: "빈칸이 든 대괄호는 번호가 아니다",
    input: "그렇다. [ 1 ]",
    want: p("그렇다. [ 1 ]"),
  },
  {
    id: "c42",
    note: "이미지의 대체 글 안",
    input: "![그림 [1]](https://example.com/a.png)",
    want: p(img("그림 [1]")),
  },
  {
    id: "c43",
    note: "정의 없는 각주 표기는 글자다",
    input: "각주 [^1] 정의 없음",
    want: p("각주 [^1] 정의 없음"),
  },
  {
    id: "c44",
    note: "사실: 주소 뒤에 붙은 `[1]`",
    input: "주소 https://example.com/a[1] 참고",
    want: null,
    pinned: p(`주소 ${a("https://example.com/a%5B1", "https://example.com/a[1")}] 참고`),
  },
  {
    id: "c45",
    note: "한글 조사 앞의 번호 둘. 후보가 갈린다",
    input: "편람[1]과 규정[2]을 본다",
    want: null,
    pinned: p(`편람${sup(1)}과 규정${sup(2)}을 본다`),
  },
  {
    id: "c46",
    note: "닫는 괄호 앞",
    input: "(자세한 내용은 편람 참고 [1])",
    want: p(`(자세한 내용은 편람 참고${sup(1)})`),
  },
  { id: "c47", note: "빈칸 둘", input: "첫 문장입니다.  [1]", want: p(`첫 문장입니다.${sup(1)}`) },
  {
    id: "c48",
    note: "표 칸에 번호만 있다. 후보가 갈린다",
    input: tableMd(["근거"], ["[1]"]),
    want: null,
    pinned: table(["근거"], [["[1]"]]),
  },
];

/**
 * 사례 파일에 없는 번호의 경계 입력 열셋. `k1`~`k12` 의 입력과 목표는 일지 2026-11-11-1057 의 "손으로 본 것: 문장 끝 번호의
 * 경계 입력"이 시제품에 넣어 본 열둘과 같다. `k13` 은 이 부품이 더했다. 출처 덩이의 변환이 표지 앞의 본문을 갈라도 본문의
 * 원문 위치가 남아 역슬래시로 쓴 대괄호를 알아본다(시제품은 가른 문단의 위치를 잃었다). 모두 목표를 적은 입력이다.
 */
export const CITE_EDGES: readonly ShapeCase[] = [
  { id: "k1-control-sup", input: "근거는 [1] 이다", want: p(`근거는${sup(1)} 이다`) },
  {
    id: "k2-strong-first",
    note: "굵게의 첫 글자로 시작하는 번호는 줄 머리로 본다",
    input: "근거는 **[1]** 이다",
    want: p(`근거는 ${strong("[1]")} 이다`),
  },
  {
    id: "k3-strong-inner",
    input: "근거는 **중요[1]** 이다",
    want: p(`근거는 ${strong(`중요${sup(1)}`)} 이다`),
  },
  { id: "k4-control-escaped", input: "값 \\[1\\] 이다", want: p("값 [1] 이다") },
  {
    id: "k5-close-escaped",
    note: "닫는 대괄호만 역슬래시로 쓴 것은 번호로 본다",
    input: "값 [1\\] 이다",
    want: p(`값${sup(1)} 이다`),
  },
  {
    id: "k6-open-escaped",
    note: "여는 대괄호를 역슬래시로 쓴 것은 글자다",
    input: "값 \\[1] 이다",
    want: p("값 [1] 이다"),
  },
  {
    id: "k7-after-literal-marks",
    note: "받아들이는 한계. 숫자 사이 별표를 벗긴 문단에서는 역슬래시로 쓴 번호도 위첨자가 된다",
    input: "2*3*4 = 24 \\[1\\]",
    want: p(`2*3*4 = 24${sup(1)}`),
  },
  {
    id: "k8-after-cjk-repair",
    note: "받아들이는 한계. 닫히지 않은 굵게를 되살린 문단에서는 역슬래시로 쓴 번호도 위첨자가 된다",
    input: "**민법 제750조(불법행위)**는 \\[1\\] 이다",
    want: p(`${strong("민법 제750조(불법행위)")}는${sup(1)} 이다`),
  },
  {
    id: "k9-after-task-mark",
    note: "할 일 표시를 되돌린 항목의 역슬래시로 쓴 번호는 글자로 남는다",
    input: "- [x] 한 일 \\[1\\]",
    want: ul("[x] 한 일 [1]"),
  },
  {
    id: "k10-same-node-other",
    note: "역슬래시로 쓴 대괄호가 든 글자 노드는 통째로 건너뛴다",
    input: "값 \\[1\\] 그리고 [2]",
    want: p("값 [1] 그리고 [2]"),
  },
  {
    id: "k11-em-first",
    note: "기울임의 첫 글자로 시작하는 번호도 줄 머리로 본다",
    input: "근거는 *[1]* 이다",
    want: p(`근거는 ${el("em", {}, "[1]")} 이다`),
  },
  { id: "k12-after-strong", input: "**굵게** [1]", want: p(`${strong("굵게")}${sup(1)}`) },
  {
    id: "k13-escaped-before-label",
    note: "표지가 붙은 문단을 갈라도 본문의 역슬래시 대괄호는 글자로 남는다",
    input: "값은 \\[1\\] 이다. [2]\n출처\n1. 편람",
    want: p("값은 [1] 이다. [2]") + sources(p("출처") + ol("편람")),
  },
];
