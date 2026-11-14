// 제목·이미지·표·코드·각주·할 일 목록 21가지와 링크 17가지(answer-markdown 명세 "부품의 단위 시험", 티켓 01). 원천은 프로브의
// 사례 파일 `shape-cases.mjs` 의 `SHAPE` 와 `LINKS` 이고 입력은 글자 그대로 옮겼다. 목표 모양은 시제품이 낸 HTML 이라 명세와
// 다른 자리는 명세를 따랐다. 표 스크롤 칸은 이름 "표"의 묶음이고(시제품은 영역), 표 칸의 정렬은 뼈대에 들지 않고(정렬은 클래스로
// 낸다. 아래 `ALIGNED_TABLE` 이 따로 본다), 코드 블록에 `language-*` 가 붙지 않는다.
import { a, h, img, ol, p, pre, strong, table, ul } from "./skeleton";
import type { ShapeCase } from "./breaks";

const FENCE = "```";

export const SHAPE: readonly ShapeCase[] = [
  {
    id: "h01-headings",
    input: "# 하나\n\n## 둘\n\n### 셋\n\n#### 넷\n\n##### 다섯\n\n###### 여섯",
    want: h(2, "하나") + h(3, "둘") + h(4, "셋") + h(5, "넷") + h(6, "다섯") + h(6, "여섯"),
  },
  { id: "h02-setext", input: "제목\n===\n\n부제\n---", want: h(2, "제목") + h(3, "부제") },
  {
    id: "i01-image",
    input: "![영수증 사진](https://tracker.example/r.png?id=184)",
    want: p(img("영수증 사진")),
  },
  { id: "i02-image-no-alt", input: "![](https://tracker.example/r.png)", want: p(img("")) },
  { id: "i03-image-js", input: "![그림](javascript:alert(1))", want: p(img("그림")) },
  {
    id: "i04-image-in-link",
    input: "[![배지](https://img.example/b.svg)](https://example.com/)",
    want: p(a("https://example.com/", img("배지"))),
  },
  {
    id: "i05-image-alt-emphasis",
    input: "![**굵은** 글](https://a.example/x.png)",
    want: p(img("굵은 글")),
  },
  {
    id: "t01-table-align",
    note: "정렬은 클래스로 낸다. 뼈대에는 들지 않고 `ALIGNED_TABLE` 의 시험이 따로 본다",
    input: "| 가 | 나 |\n| :-- | --: |\n| 1 | 2 |",
    want: table(["가", "나"], [["1", "2"]]),
  },
  {
    id: "k01-code-lang",
    input: `${FENCE}bash\ncurl -X POST https://example.com/\n${FENCE}`,
    want: pre("curl -X POST https://example.com/\n"),
  },
  {
    id: "k02-code-indented",
    note: "네 칸 들여쓴 코드 블록",
    input: "    들여쓴 코드",
    want: pre("들여쓴 코드\n"),
  },
  // 각주 문법은 글자 그대로 남는다. 정의는 놓인 자리에 남고 끝으로 옮기지 않는다.
  {
    id: "f01-footnote",
    input: "본문입니다[^1].\n\n[^1]: 각주 글",
    want: p("본문입니다[^1].") + p("[^1]: 각주 글"),
  },
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
  {
    id: "f04-footnote-two-refs",
    input: "하나[^1] 둘[^1]\n\n[^1]: 글",
    want: p("하나[^1] 둘[^1]") + p("[^1]: 글"),
  },
  {
    id: "f05-footnote-multi-block",
    note: "정의가 여러 블록이면 이어서 선다",
    input: "본문[^1]\n\n[^1]: 첫 문단\n\n    둘째 문단",
    want: p("본문[^1]") + p("[^1]: 첫 문단") + p("둘째 문단"),
  },
  // 할 일 목록의 표시(`[ ]`, `[x]`)는 글자 그대로 남는다.
  { id: "g01-task-list", input: "- [ ] 할 일\n- [x] 한 일", want: ul("[ ] 할 일", "[x] 한 일") },
  {
    id: "g02-task-upper",
    note: "대문자 X 도 원문 그대로 둔다",
    input: "- [X] 끝남",
    want: ul("[X] 끝남"),
  },
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
    note: "표시가 아닌 대괄호는 처음부터 글자다",
    input: "- [x]붙은 글\n- 그냥 항목",
    want: ul("[x]붙은 글", "그냥 항목"),
  },
];

export const LINKS: readonly ShapeCase[] = [
  {
    id: "l01-userinfo-host",
    input: "[은행](https://www.law.go.kr@evil.example/login)",
    want: p("은행"),
  },
  { id: "l02-user-password", input: "[가](https://user:pw@host.example/)", want: p("가") },
  { id: "l03-user-only", input: "[가](https://user@host.example/)", want: p("가") },
  {
    id: "l04-empty-userinfo",
    note: "`@` 앞이 빈 주소. 파서가 사용자 정보 없는 주소로 읽으므로 링크가 되고 낸 주소에는 `@` 가 없다",
    input: "[가](https://@host.example/)",
    want: null,
    pinned: p(a("https://host.example/", "가")),
  },
  { id: "l05-empty-password", input: "[가](https://www.law.go.kr:@evil.example/)", want: p("가") },
  {
    id: "l06-angle-autolink",
    input: "<https://www.law.go.kr@evil.example/>",
    want: p("https://www.law.go.kr@evil.example/"),
  },
  {
    id: "l07-bare-autolink",
    note: "화면 파일 mk-unsafe 의 마지막 줄",
    input: "https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다.",
    want: p("https://shop.example.com@phish.example/refund 는 링크가 되지 않습니다."),
  },
  { id: "l08-escaped-at", input: "[가](https://www.law.go.kr\\@evil.example/)", want: p("가") },
  { id: "l09-uppercase", input: "[가](HTTPS://USER@EXAMPLE.COM/)", want: p("가") },
  {
    id: "l10-percent-encoded-at",
    note: "`%40`. 호스트로 풀리지 않는 주소라 링크가 되지 않고 글만 남는다",
    input: "[가](https://www.law.go.kr%40evil.example/)",
    want: null,
    pinned: p("가"),
  },
  {
    id: "l11-normal",
    note: "대조: 정상 링크",
    input: "[법령](https://www.law.go.kr/)",
    want: p(a("https://www.law.go.kr/", "법령")),
  },
  { id: "l12-www-at", input: "www.law.go.kr@evil.example", want: p("www.law.go.kr@evil.example") },
  {
    id: "l13-email",
    input: "문의는 help@example.com 으로",
    want: p("문의는 help@example.com 으로"),
  },
  {
    id: "l14-title",
    note: "title 은 그리지 않는다",
    input: '[가](https://example.com/ "제목")',
    want: p(a("https://example.com/", "가")),
  },
  { id: "l15-reference", input: "[가][r]\n\n[r]: https://u:p@host.example/", want: p("가") },
  {
    id: "l16-http-query",
    input: "[가](http://example.com/a?b=1&c=2)",
    want: p(a("http://example.com/a?b=1&c=2", "가")),
  },
  {
    id: "l17-userinfo-in-path",
    note: "대조: 경로의 `@` 는 사용자 정보가 아니다",
    input: "[가](https://example.com/@user)",
    want: p(a("https://example.com/@user", "가")),
  },
];

/** 표 칸의 정렬을 적은 입력(왼쪽, 가운데, 오른쪽)과 적지 않은 칸. */
export const ALIGNED_TABLE = [
  "| 없음 | 왼쪽 | 가운데 | 오른쪽 |",
  "|---|:--|:-:|--:|",
  "| a | b | c | d |",
].join("\n");
