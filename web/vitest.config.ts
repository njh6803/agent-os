import { join } from "node:path";
import { storybookTest } from "@storybook/addon-vitest/vitest-plugin";
import { playwright } from "@vitest/browser-playwright";
import { configDefaults, defineConfig } from "vitest/config";
import type { ViewportKey } from "./apps/admin/.storybook/viewports.ts";

// 관리 화면과 위젯의 페이지 테스트(web-admin·web-widget 명세의 주 이음매)는 jsdom 에서 돈다. 그 밖의 테스트(판정자,
// 생성 스크립트, 시작 래퍼와 설정의 단위 테스트)는 node 환경에 남는다. 화면을 그리는 테스트는 components/ 아래의
// .test.tsx 다. 위젯의 커스텀 요소(element/)도 DOM 이 있어야 해 .test.tsx 를 jsdom 에서 돌린다.
const PAGES = "apps/admin/components/**/*.test.tsx";
const WIDGET_PAGES = ["apps/widget/components/**/*.test.tsx", "apps/widget/element/**/*.test.tsx"];
// 디자인 시스템, 위젯, 관리 화면의 스토리 테스트(design-system·web-widget·admin-style 명세의 주 이음매). 스토리마다 실제
// chromium 에서 그리고 play, 미리보기의 afterEach(클래스 판정), axe(addon-a11y)를 돈다. 브라우저는 Playwright 의 브라우저
// 캐시에 깔린 것을 쓴다. 프로젝트의 이름이 겹치면 Vitest 가 거부한다.
const STORYBOOK = join(import.meta.dirname, "packages", "ui", ".storybook");
const WIDGET_STORYBOOK = join(import.meta.dirname, "apps", "widget", ".storybook");
// 관리 화면은 같은 Storybook 을 창 두 벌(apps/admin/.storybook/viewports.ts)로 돈다. 창은 미리보기의 viewport 항목을
// `initialGlobals` 로 고른다. `test.browser.viewport` 는 스토리마다 1200×900 으로 덮였다
// (.scratch/admin-style/probes/storybook_viewport.mjs).
const ADMIN_STORYBOOK = join(import.meta.dirname, "apps", "admin", ".storybook");
const ADMIN_VIEWPORTS = ["wide", "narrow"] as const satisfies readonly ViewportKey[];

function chromium() {
  return {
    enabled: true,
    headless: true,
    provider: playwright(),
    instances: [{ browser: "chromium" as const }],
  };
}

export default defineConfig({
  test: {
    // 판정자 테스트가 web/ 아래에 임시 트리를 쓰고, tsconfig 검사의 저장소 상태 테스트가 web/ 를 훑는다.
    // 파일을 나란히 돌리면 쓰는 도중의 tsconfig 를 읽을 수 있어 파일은 차례로 돈다.
    fileParallelism: false,
    // 타입 기반 린트는 TypeScript 프로그램을 세우느라 첫 호출이 수 초 걸린다.
    testTimeout: 60_000,
    hookTimeout: 120_000,
    projects: [
      {
        extends: true,
        test: { name: "node", exclude: [...configDefaults.exclude, PAGES, ...WIDGET_PAGES] },
      },
      {
        extends: true,
        test: {
          name: "pages",
          include: [PAGES],
          environment: "jsdom",
          setupFiles: ["apps/admin/testing/setup.ts"],
        },
      },
      {
        extends: true,
        test: {
          name: "widget-pages",
          include: WIDGET_PAGES,
          environment: "jsdom",
          setupFiles: ["apps/widget/testing/setup.ts"],
        },
      },
      {
        extends: true,
        plugins: [storybookTest({ configDir: STORYBOOK })],
        test: { name: "storybook", browser: chromium() },
      },
      {
        extends: true,
        plugins: [storybookTest({ configDir: WIDGET_STORYBOOK })],
        test: { name: "widget-storybook", browser: chromium() },
      },
      ...ADMIN_VIEWPORTS.map((viewport) => ({
        extends: true,
        plugins: [
          storybookTest({
            configDir: ADMIN_STORYBOOK,
            initialGlobals: { viewport: { value: viewport, isRotated: false } },
          }),
        ],
        test: { name: `admin-storybook-${viewport}`, browser: chromium() },
      })),
    ],
  },
});
