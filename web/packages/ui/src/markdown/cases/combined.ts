// 합친 사례 17가지(answer-markdown 명세 "부품의 단위 시험", 티켓 02). 원천은 프로브의 사례 파일 `shape-cases.mjs` 의 `COMBINED`
// 와 `SCREEN_INPUTS` 이고 입력과 목표는 글자 그대로 옮겼다. 프로브도 이 묶음에서는 변환을 모두 켰다. 다른 자리는 시제품의
// 클래스와 속성(`sources`, `data-cite`, `language-*`)이 뼈대에 들지 않는 것뿐이다.
import {
  a,
  BR,
  bq,
  code,
  el,
  em,
  img,
  ol,
  p,
  pre,
  sources,
  strong,
  sup,
  table,
  ul,
} from "./skeleton";
import { type ShapeCase, tableMd } from "./breaks";

const FENCE = "```";
const SOURCE_LIST = ol("편람", "규정");

/** 화면 파일(`.scratch/answer-markdown/design/`)이 그린 출력의 원문. 스토리의 입력과 글자가 같다. */
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

const CITE_BODY_1 = "육아휴직은 자녀 1명당 최대 1년까지 쓸 수 있습니다.";
const CITE_BODY_2 = "신청서는 휴직 시작 30일 전까지 내야 합니다.";
export const COMBINED: readonly ShapeCase[] = [
  {
    id: "m01-mk-cite",
    input: SCREEN_INPUTS["mk-cite"],
    want:
      p(`${CITE_BODY_1}${sup(1)}${BR}${CITE_BODY_2}${sup(2)}`) +
      sources(
        p("출처") +
          ol(
            "육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)",
            "인사 규정, 제3장 제14조 (갱신일 2026-08-15)",
          ),
      ),
  },
  { id: "m02-mk-side-1", input: SCREEN_INPUTS["mk-side-1"], want: p("2*3*4 = 24입니다.") },
  {
    id: "m03-mk-side-2",
    input: SCREEN_INPUTS["mk-side-2"],
    want:
      p(
        `${strong("민법 제750조(불법행위)")}는 고의나 과실로 남에게 손해를 입힌 사람이 갚아야 한다고 정합니다.`,
      ) +
      el("h2", {}, "1번 항목은 다음 쪽에 있습니다.") +
      p("설정 파일은 __init__.py 옆에 둡니다."),
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
      ),
  },
  {
    id: "m06-all-five",
    note: "다섯 처리가 한 출력에 다 걸린다",
    input:
      "**요건(가)**은 다음과 같습니다. [1]\n계산은 2*3*4입니다. [2]\n\n출처\n1. 민법 해설\n2. 계산 편람",
    want:
      p(`${strong("요건(가)")}은 다음과 같습니다.${sup(1)}${BR}계산은 2*3*4입니다.${sup(2)}`) +
      sources(p("출처") + ol("민법 해설", "계산 편람")),
  },
  {
    id: "m07-label-is-last-line",
    note: "`출처` 가 앞 문단의 마지막 줄이다",
    input: "첫 문장입니다. [1]\n둘째 문장입니다. [2]\n출처\n1. 편람\n2. 규정",
    want:
      p(`첫 문장입니다.${sup(1)}${BR}둘째 문장입니다.${sup(2)}`) + sources(p("출처") + SOURCE_LIST),
  },
  {
    id: "m08-bracket-sources",
    note: "출처가 `[1] …` 줄들이다. 출처 덩이 안의 `[1]` 은 번호로 바꾸지 않는다",
    input: "가능합니다[1][2].\n\n출처\n[1] 민법 제750조 (갱신 2026-01-02)\n[2] 안내문",
    want:
      p(`가능합니다${sup(1)}${sup(2)}.`) +
      sources(p("출처") + p(`[1] 민법 제750조 (갱신 2026-01-02)${BR}[2] 안내문`)),
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
  {
    id: "m11-heading",
    input: "## **요약(가)**의 결과 [1]",
    want: el("h3", {}, `${strong("요약(가)")}의 결과${sup(1)}`),
  },
  {
    id: "m12-table",
    input: tableMd(["식", "근거"], ["2*3*4", "**편람(가)**는 [1]"]),
    want: table(["식", "근거"], [["2*3*4", `${strong("편람(가)")}는${sup(1)}`]]),
  },
  { id: "m13-empty", input: "", want: "" },
  { id: "m14-blank", input: "  \n\n", want: "" },
  { id: "m15-single", input: "4", want: p("4") },
  {
    id: "m16-text-after-sources",
    note: "목록 뒤에 문단이 더 있으면 출처 덩이가 아니다",
    input: "본문 [1]\n\n출처\n1. 편람\n\n감사합니다.",
    want: p(`본문${sup(1)}`) + p("출처") + ol("편람") + p("감사합니다."),
  },
  {
    id: "m17-brackets-inside-sources",
    input: "본문입니다. [1]\n\n출처\n1. 편람 [개정 3판]\n2. 규정 [2]",
    want: p(`본문입니다.${sup(1)}`) + sources(p("출처") + ol("편람 [개정 3판]", "규정 [2]")),
  },
];
