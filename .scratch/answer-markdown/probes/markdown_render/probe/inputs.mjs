// 부하 입력의 원천. stress-child.mjs(Node 의 서버 렌더), stage-child.mjs(Node 에서 던지는 단계), browser.mjs(Chromium)가
// 같은 글을 쓴다. 2026-11-10 의 열넷은 stress-child.mjs 에 있던 것을 글자 그대로 옮겼다(이름과 만드는 식이 같다).
const bytes = (value) => new TextEncoder().encode(value).length;

export const TYPICAL = [
  "## 결론",
  "",
  "임대인이 **보증금을 돌려주지 않으면** 임차권등기명령을 신청할 수 있습니다[1].",
  "",
  "1. 계약이 끝났는지 확인합니다.",
  "2. 관할 법원에 신청서를 냅니다.",
  "   - 임대차계약서",
  "   - 주민등록등본",
  "3. 결정문을 받은 뒤 등기를 확인합니다.",
  "",
  "| 서류 | 발급처 | 비고 |",
  "|---|---|---|",
  "| 등기사항증명서 | 인터넷등기소 | 발급 후 1개월 이내 |",
  "| 주민등록등본 | 정부24 | 주소 변동 포함 |",
  "",
  "> 신청 뒤에 이사해도 대항력이 유지됩니다.",
  "",
  "자세한 절차는 [대한민국 법원 전자소송](https://ecfs.scourt.go.kr/)에서 볼 수 있습니다.",
  "",
  "출처",
  "[1] 주택임대차보호법 제3조의3 (갱신 2026-01-02) https://www.law.go.kr/법령/주택임대차보호법",
  "",
].join("\n");

/** 2026-11-10 의 병적인 입력 열넷. 값은 글을 만드는 함수다. */
export const STRESS_INPUTS = {
  "typical-1kb": () => TYPICAL,
  "long-100kb": () => TYPICAL.repeat(Math.ceil(100_000 / bytes(TYPICAL))),
  "stars-10k": () => "*".repeat(10_000),
  "underscores-10k": () => "_".repeat(10_000),
  "brackets-10k": () => "[".repeat(10_000),
  "link-open-3k": () => "[a](".repeat(3_000),
  "quote-3k": () => `${">".repeat(3_000)} a`,
  "backticks-10k": () => "`".repeat(10_000),
  "lt-10k": () => "<".repeat(10_000),
  "ampersands-10k": () => "&".repeat(10_000),
  "nested-list-200": () => Array.from({ length: 200 }, (_, i) => `${" ".repeat(2 * i)}- a`).join("\n"),
  "emphasis-mix-2k": () => "*a **b ".repeat(2_000),
  "pipes-50x200": () => `${"|".repeat(200)}\n`.repeat(50),
  "bang-brackets-5k": () => "![".repeat(5_000),
};

export const STRESS_NAMES = Object.keys(STRESS_INPUTS);

/** 깊이 훑기의 깊이. */
export const DEPTHS = [50, 100, 200, 500, 1_000, 2_000, 3_000];

/**
 * 깊이 훑기의 입력 꼴. `depth` 겹의 인용이나 목록 하나를 만든다.
 * - quote: `>` 를 한 줄에 `depth` 번(`quote-3k` 와 같은 꼴).
 * - list-inline: `- ` 를 한 줄에 `depth` 번. 한 줄이 `depth` 겹의 목록이 된다.
 * - list-indent: 줄마다 두 칸씩 더 들여 쓴 `- a`(`nested-list-200` 과 같은 꼴). 글의 크기가 깊이의 제곱으로 는다.
 */
export const DEPTH_KINDS = {
  quote: (depth) => `${">".repeat(depth)} a`,
  "list-inline": (depth) => `${"- ".repeat(depth)}a`,
  "list-indent": (depth) => Array.from({ length: depth }, (_, i) => `${" ".repeat(2 * i)}- a`).join("\n"),
};

/** 깊이 훑기 입력이 실제로 그 깊이까지 겹쳤는지 볼 때 세는 요소. */
export const DEPTH_ELEMENT = { quote: "blockquote", "list-inline": "ul", "list-indent": "ul" };

/** `quote:3000` 이나 `stress:quote-3k` 꼴의 이름을 글로 바꾼다. 없는 이름이면 null. */
export function inputOf(name) {
  const [kind, rest] = name.split(/:(.*)/s);
  if (kind === "stress") {
    const make = STRESS_INPUTS[rest];
    return make === undefined ? null : make();
  }
  const make = DEPTH_KINDS[kind];
  const depth = Number(rest);
  if (make === undefined || !Number.isInteger(depth) || depth <= 0) return null;
  return make(depth);
}
