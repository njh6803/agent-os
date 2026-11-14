// 출처 덩이 32가지(answer-markdown 명세 "출처 덩이", 티켓 02). 원천은 프로브의 사례 파일 `shape-cases.mjs` 의 `SOURCES` 이고
// 입력은 글자 그대로 옮겼다. 다른 자리는 셋이다.
// - 프로브는 이 묶음에서 출처 덩이 변환만 켰다. 부품은 변환을 늘 모두 켜므로, 본문의 `[1]` 은 위첨자로, 문단 안의 줄 끝 글자는
//   줄바꿈(`BR`)으로 옮겼다. 출처 덩이 안의 `[1]` 은 위첨자가 되지 않는다.
// - 목표를 적지 않은 입력 가운데 프로브가 고른 규칙(`sources-pick`)의 기대를 적어 둔 것은 그 기대를 위와 같이 옮겨
//   `pinned` 로 고정했다. 그 기대가 없는 둘(`s21`, `s31`)은 지금의 결과를 고정한다. 명세 "출처 덩이"의 "마크다운의 문법이
//   정하는 모양"이 그 둘의 결과(출처 덩이가 생기지 않는다)를 적었다.
// - 시제품의 클래스(`sources`)는 뼈대에 들지 않는다. 출처 덩이는 `div` 하나다.
import { a, BR, bq, el, li, ol, p, sources, strong, sup, ul } from "./skeleton";
import type { ShapeCase } from "./breaks";

const SOURCE_LIST = ol("편람", "규정");
const wrapped = (label: string): string => sources(label + SOURCE_LIST);

export const SOURCES: readonly ShapeCase[] = [
  {
    id: "s01-base",
    input: "본문입니다. [1]\n\n출처\n\n1. 편람\n2. 규정",
    want: p(`본문입니다.${sup(1)}`) + wrapped(p("출처")),
  },
  {
    id: "s02-no-blank-before-list",
    note: "`출처` 바로 다음 줄이 `1. …` 이면 문단과 목록으로 갈린다",
    input: "본문입니다.\n\n출처\n1. 편람\n2. 규정",
    want: p("본문입니다.") + wrapped(p("출처")),
  },
  {
    id: "s03-label-is-last-line",
    note: "앞 문단과 `출처` 사이에 빈 줄이 없으면 `출처` 가 앞 문단의 마지막 줄로 붙고, 문단을 갈라 알아본다",
    input: "본문입니다. [2]\n출처\n1. 편람\n2. 규정",
    want: null,
    pinned: p(`본문입니다.${sup(2)}`) + wrapped(p("출처")),
  },
  {
    id: "s04-bold-label",
    input: "본문입니다.\n\n**출처**\n\n1. 편람\n2. 규정",
    want: null,
    pinned: p("본문입니다.") + wrapped(p(strong("출처"))),
  },
  {
    id: "s05-heading-label",
    input: "본문입니다.\n\n## 출처\n\n1. 편람\n2. 규정",
    want: null,
    pinned: p("본문입니다.") + wrapped(el("h3", {}, "출처")),
  },
  {
    id: "s06-colon",
    input: "본문입니다.\n\n출처:\n\n1. 편람\n2. 규정",
    want: null,
    pinned: p("본문입니다.") + wrapped(p("출처:")),
  },
  {
    id: "s07-unordered",
    note: "번호 없는 글머리 목록은 알아보지 않는다",
    input: "본문입니다.\n\n출처\n\n- 편람\n- 규정",
    want: null,
    pinned: p("본문입니다.") + p("출처") + ul("편람", "규정"),
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
  {
    id: "s10-other-word-list",
    note: "다른 말",
    input: "본문입니다.\n\n출처 목록\n\n1. 편람\n2. 규정",
    want: p("본문입니다.") + p("출처 목록") + SOURCE_LIST,
  },
  {
    id: "s11-other-word-ref",
    note: "다른 말",
    input: "본문입니다.\n\n참고\n\n1. 편람\n2. 규정",
    want: p("본문입니다.") + p("참고") + SOURCE_LIST,
  },
  {
    id: "s12-other-word-english",
    note: "다른 말",
    input: "본문입니다.\n\nSources\n\n1. 편람\n2. 규정",
    want: p("본문입니다.") + p("Sources") + SOURCE_LIST,
  },
  {
    id: "s13-bracket-lines-same-paragraph",
    note: "출처가 목록이 아니라 `[1] …` 줄들이고 `출처` 와 한 문단이다",
    input: "본문입니다. [1]\n\n출처\n[1] 편람\n[2] 규정",
    want: null,
    pinned: p(`본문입니다.${sup(1)}`) + sources(p("출처") + p(`[1] 편람${BR}[2] 규정`)),
  },
  {
    id: "s14-bracket-lines-own-paragraph",
    input: "본문입니다. [1]\n\n출처\n\n[1] 편람\n[2] 규정",
    want: null,
    pinned: p(`본문입니다.${sup(1)}`) + sources(p("출처") + p(`[1] 편람${BR}[2] 규정`)),
  },
  {
    id: "s15-only-sources",
    note: "출력 전체가 `출처` 와 목록뿐이다",
    input: "출처\n\n1. 편람\n2. 규정",
    want: null,
    pinned: wrapped(p("출처")),
  },
  {
    id: "s16-crlf",
    input: "본문입니다.\r\n\r\n출처\r\n1. 편람\r\n2. 규정",
    want: p("본문입니다.") + wrapped(p("출처")),
  },
  {
    id: "s17-loose-list",
    note: "항목 사이에 빈 줄이 있는 목록",
    input: "본문입니다.\n\n출처\n\n1. 편람\n\n2. 규정",
    want: p("본문입니다.") + sources(p("출처") + ol(p("편람"), p("규정"))),
  },
  {
    id: "s18-after-rule",
    note: "바로 앞의 가로줄은 그대로 그린다",
    input: "본문입니다.\n\n---\n\n출처\n\n1. 편람\n2. 규정",
    want: p("본문입니다.") + el("hr") + wrapped(p("출처")),
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
    pinned:
      p("본문입니다.") + sources(p("출처") + el("ol", { start: "2" }, li("규정") + li("세칙"))),
  },
  {
    id: "s21-list-starts-at-2-no-blank",
    note: "1 로 시작하지 않는 번호 목록은 문단을 끊지 못해 `출처` 와 한 문단이 된다",
    input: "본문입니다.\n\n출처\n2. 규정\n3. 세칙",
    want: null,
    pinned: p("본문입니다.") + p(`출처${BR}2. 규정${BR}3. 세칙`),
  },
  {
    id: "s22-paren-delimiter",
    input: "본문입니다.\n\n출처\n1) 편람\n2) 규정",
    want: p("본문입니다.") + wrapped(p("출처")),
  },
  {
    id: "s23-label-trailing-spaces",
    input: "본문입니다.\n\n출처  \n1. 편람\n2. 규정",
    want: p("본문입니다.") + wrapped(p("출처")),
  },
  {
    id: "s24-bold-colon",
    input: "**출처:**\n\n1. 편람\n2. 규정",
    want: null,
    pinned: wrapped(p(strong("출처:"))),
  },
  {
    id: "s25-heading-bracket-lines",
    input: "## 출처\n\n[1] 편람\n[2] 규정",
    want: null,
    pinned: sources(el("h3", {}, "출처") + p(`[1] 편람${BR}[2] 규정`)),
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
    pinned: sources(p("출처") + ol(a("https://example.com/a", "편람"), "규정")),
  },
  {
    id: "s28-inline-label",
    note: "`출처: …` 한 줄은 덩이가 아니다",
    input: "출처: 육아휴직 업무편람 12쪽",
    want: p("출처: 육아휴직 업무편람 12쪽"),
  },
  {
    id: "s29-design-input",
    note: "화면 파일 mk-cite 의 원문",
    input:
      "육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다. [1]\n신청서는 휴직 시작 30일 전까지 내야 합니다. [2]\n\n출처\n1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)\n2. 인사 규정, 제3장 제14조 (갱신일 2026-08-15)",
    want:
      p(
        `육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다.${sup(1)}${BR}신청서는 휴직 시작 30일 전까지 내야 합니다.${sup(2)}`,
      ) +
      sources(
        p("출처") +
          ol(
            "육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)",
            "인사 규정, 제3장 제14조 (갱신일 2026-08-15)",
          ),
      ),
  },
  {
    id: "s30-trailing-blank-lines",
    input: "출처\n\n1. 편람\n2. 규정\n\n",
    want: null,
    pinned: wrapped(p("출처")),
  },
  {
    id: "s31-label-joins-previous-list",
    note: "본문이 목록으로 끝나고 빈 줄 없이 `출처` 가 오면 `출처` 는 마지막 항목에 붙는다",
    input: "1. 첫째 단계\n2. 둘째 단계\n출처\n1. 편람",
    want: null,
    pinned: ol("첫째 단계", `둘째 단계${BR}출처`, "편람"),
  },
  {
    id: "s32-body-list-then-sources",
    input: "1. 첫째 단계\n2. 둘째 단계\n\n출처\n\n1. 편람\n2. 규정",
    want: ol("첫째 단계", "둘째 단계") + wrapped(p("출처")),
  },
];

/**
 * 출처 덩이의 경계 입력. 시제품의 32가지에 없던 꼴이고 모두 목표를 적은 입력이다. `t01`·`t02` 는 이 부품의 셀프 리뷰가 더했고
 * 명세 "출처 덩이"의 표지 다섯째 꼴(앞 문단의 마지막 줄로 붙은 `출처`)과 목록 둘째 꼴(줄마다 `[숫자]` 로 시작하는 문단)이 함께 온
 * 것이다. `t03` 은 PR 봇 리뷰가 더했고, 화면에 그려지지 않는 참조형 링크 정의가 출력 끝에 있어도 그 앞의 표지와 목록을 마지막
 * 두 블록으로 보는 것이다.
 */
export const SOURCE_EDGES: readonly ShapeCase[] = [
  {
    id: "t01-attached-label-bracket-paragraph",
    note: "앞 문단에 붙은 `출처` 뒤에 빈 줄을 두고 `[숫자]` 줄 문단이 온다",
    input: "본문입니다. [1]\n출처\n\n[1] 편람\n[2] 규정",
    want: p(`본문입니다.${sup(1)}`) + sources(p("출처") + p(`[1] 편람${BR}[2] 규정`)),
  },
  {
    id: "t02-attached-strong-label-bracket-paragraph",
    note: "굵게 쓰고 콜론을 붙인 표지도 같다",
    input: "본문입니다.\n**출처:**\n\n[1] 편람",
    want: p("본문입니다.") + sources(p(strong("출처:")) + p("[1] 편람")),
  },
  {
    id: "t03-trailing-link-definition",
    note: "목록 뒤의 참조형 링크 정의는 그려지지 않아 블록으로 세지 않고, 출처 안의 `[2]` 는 글자로 남는다",
    input: "본문입니다. [1]\n\n출처\n\n1. [편람][r] [2]\n2. 규정\n\n[r]: https://example.com/",
    want:
      p(`본문입니다.${sup(1)}`) +
      sources(p("출처") + ol(`${a("https://example.com/", "편람")} [2]`, "규정")),
  },
];
