// visual_docker 프로브의 Playwright 설정. run.mjs 가 작업 폴더의 probe/ 로 옮겨 컨테이너와 호스트에서 같은 파일로 돈다.
// 직접 부르지 않는다. 환경 변수(run.mjs 가 넣는다)
//   VISUAL_OUT       이 실행의 산출 폴더(원본 스크린샷, run-<구성표>.json, test-results)
//   VISUAL_BASELINE  toHaveScreenshot 정답 사진 폴더. 운영체제 접미사 없이 {이름}.png 로 둬서 컨테이너가 만든 정답을
//                    호스트도 그대로 비교한다
//   VISUAL_MODE      baseline 이면 정답을 새로 쓰고(updateSnapshots: all), compare 면 정답을 건드리지 않는다(none)
import { join } from "node:path";
import { defineConfig } from "@playwright/test";

const out = process.env.VISUAL_OUT;
const baseline = process.env.VISUAL_BASELINE;
if (out === undefined || baseline === undefined) {
  throw new Error("VISUAL_OUT, VISUAL_BASELINE 이 없다. run.mjs 로 돈다");
}

export default defineConfig({
  testDir: ".",
  testMatch: "capture.spec.mjs",
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
    viewport: { width: 800, height: 600 },
    deviceScaleFactor: 1,
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
  },
});
