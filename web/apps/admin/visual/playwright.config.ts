// 관리 화면의 사진 비교(admin-style 명세 "Storybook과 사진 비교"). 디자인 시스템 패키지와 위젯의 사진 비교와 같은
// 조건이다(packages/ui/visual/playwright.config.ts). 관리 화면의 Storybook 정적 빌드(`../storybook-static`)를 판을 고정한
// Playwright 이미지 안에서 찍어 이 폴더의 정답 사진(`snapshots/`)과 비교한다. 정답 사진도 그 이미지 안에서만 만든다.
//
// 관리 화면은 밀도를 달지 않아 폭이 밀도를 고르므로, 스토리 테스트와 같은 창 두 벌(../.storybook/viewports.ts)을 프로젝트
// 둘로 찍는다. 프로젝트 이름은 창의 폭이고 사진 이름에 든다.
//
// 로컬은 `pnpm -C web visual:admin`(web/tools/visual.ts 가 컨테이너를 띄운다), CI 는 그 이미지를 잡의 컨테이너로
// 쓰는 visual 잡이다. 정답 사진을 다시 만드는 것은 `pnpm -C web visual:admin:update` 다.
import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";
import { BROWSER_ARGS } from "@agent-os/ui/visual";
import { VIEWPORTS } from "../.storybook/viewports.ts";

const IMAGE_MARKER = "/ms-playwright/.docker-info";
if (!existsSync(IMAGE_MARKER)) {
  throw new Error(
    `사진 비교는 Playwright 이미지 안에서만 돈다(${IMAGE_MARKER} 가 없다). pnpm -C web visual:admin 으로 친다`,
  );
}

export default defineConfig({
  testDir: ".",
  // Vitest 의 기본 이름(*.test.*, *.spec.*)과 겹치지 않게 한다.
  testMatch: "*.visual.ts",
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
    toHaveScreenshot: { maxDiffPixels: 0, threshold: 0 },
  },
  use: {
    browserName: "chromium",
    // 부분 래스터를 끈다. 까닭은 BROWSER_ARGS(`@agent-os/ui/visual`)의 주석이다.
    launchOptions: { args: [...BROWSER_ARGS] },
    deviceScaleFactor: 1,
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
  },
  projects: Object.values(VIEWPORTS).map(({ width, height }) => ({
    name: String(width),
    use: { viewport: { width, height } },
  })),
});
