// tokens 프로브의 사진 비교 설정. visual.mjs 가 작업 폴더의 probe/ 로 옮겨 컨테이너와 호스트에서 같은 파일로 돈다.
// 직접 부르지 않는다. 환경 변수(visual.mjs 가 넣는다)
//   VISUAL_SITE      Storybook 정적 빌드(storybook-static)의 사본 폴더
//   VISUAL_OUT       이 실행의 산출 폴더(원본 스크린샷, test-results)
//   VISUAL_BASELINE  toHaveScreenshot 정답 폴더. 운영체제 접미사 없이 {이름}.png 로 둔다
//   VISUAL_MODE      baseline 이면 정답을 새로 쓰고, compare 면 건드리지 않는다
import { join } from "node:path";
import { defineConfig } from "@playwright/test";

const out = process.env.VISUAL_OUT;
const baseline = process.env.VISUAL_BASELINE;
if (out === undefined || baseline === undefined) {
  throw new Error("VISUAL_OUT, VISUAL_BASELINE 이 없다. visual.mjs 로 돈다");
}

export default defineConfig({
  testDir: ".",
  testMatch: "visual.spec.mjs",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  outputDir: join(out, "test-results"),
  snapshotDir: baseline,
  snapshotPathTemplate: "{snapshotDir}/{arg}{ext}",
  updateSnapshots: process.env.VISUAL_MODE === "baseline" ? "all" : "none",
  use: {
    browserName: "chromium",
    viewport: { width: 480, height: 320 },
    deviceScaleFactor: 1,
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
  },
});
