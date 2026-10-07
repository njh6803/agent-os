// 사진 비교(design-system 명세의 "사진 비교 게이트", ADR 0026). Storybook 정적 빌드(`../storybook-static`)를 판을
// 고정한 Playwright 이미지 안에서 찍어 이 폴더의 정답 사진(`snapshots/`)과 비교한다. 정답 사진도 그 이미지 안에서만
// 만든다. 같은 이미지의 컨테이너 둘은 바이트까지 같은 사진을 냈고(측정 visual_docker, tokens/visual.mjs), Windows
// 호스트는 스토리 사진 14장 모두 바이트가 달랐다(tokens/visual.mjs). 그래서 이미지 밖에서는 돌지 않는다. 이미지의 표지
// 파일로 가른다.
//
// 로컬은 `pnpm -C web visual`(web/tools/visual.ts 가 컨테이너를 띄운다), CI 는 그 이미지를 잡의 컨테이너로 쓰는
// visual 잡이다. pre-commit 에는 없다. 정답 사진을 다시 만드는 것은 `pnpm -C web visual:update` 다.
import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

const IMAGE_MARKER = "/ms-playwright/.docker-info";
if (!existsSync(IMAGE_MARKER)) {
  throw new Error(
    `사진 비교는 Playwright 이미지 안에서만 돈다(${IMAGE_MARKER} 가 없다). pnpm -C web visual 로 친다`,
  );
}

export default defineConfig({
  testDir: ".",
  // Vitest 의 기본 이름(*.test.*, *.spec.*)과 겹치지 않게 한다.
  testMatch: "*.visual.ts",
  // 측정과 같은 조건으로 하나씩 돈다.
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  // 실패한 사진의 실제·정답·차이 그림이 여기 남는다. CI 는 실패하면 이 폴더를 아티팩트로 올린다.
  outputDir: "test-results",
  snapshotPathTemplate: "{testDir}/snapshots/{arg}{ext}",
  // 정답이 없으면 쓰지 않고 실패한다. 다시 만드는 명령만 --update-snapshots 를 준다.
  updateSnapshots: "none",
  expect: {
    // 픽셀 하나, 색 차이 하나도 허용하지 않는다. 같은 이미지의 사진은 바이트까지 같았다(측정).
    toHaveScreenshot: { maxDiffPixels: 0, threshold: 0 },
  },
  use: {
    browserName: "chromium",
    viewport: { width: 480, height: 320 },
    deviceScaleFactor: 1,
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
  },
});
