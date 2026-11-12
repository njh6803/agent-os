// 병적인 입력 14가지(answer-markdown 명세 "부품의 단위 시험", 사용자 이야기 22). 원천은 프로브의 `inputs.mjs` 의
// `STRESS_INPUTS` 이고 이름과 만드는 식을 글자 그대로 옮겼다. 걸린 시간은 단언하지 않는다(시간은 기기마다 달라 시험으로 두면
// 거짓 빨강이 난다).

const bytes = (value: string): number => new TextEncoder().encode(value).length;

const TYPICAL = [
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

/** 이름 → 글을 만드는 함수. */
export const STRESS_INPUTS: Readonly<Record<string, () => string>> = {
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
  "nested-list-200": () =>
    Array.from({ length: 200 }, (_, i) => `${" ".repeat(2 * i)}- a`).join("\n"),
  "emphasis-mix-2k": () => "*a **b ".repeat(2_000),
  "pipes-50x200": () => `${"|".repeat(200)}\n`.repeat(50),
  "bang-brackets-5k": () => "![".repeat(5_000),
};

/** 원문으로 물러서야 하는 둘. 가드에 걸리든, 그보다 앞의 파싱이 던져 받아지든 원문이다. */
export const STRESS_FALLBACK_NAMES: readonly string[] = ["quote-3k", "nested-list-200"];
