// 위젯 e2e(web-widget 명세 Testing Decisions 4, 티켓 06). 실제 serve, 같은 사이트 파일로 빌드한 실제 위젯 Next, 둘을 한
// 출처 아래에 모으는 시험 안의 중계를 지난다. 준비는 e2e/stack.ts 다. CI 의 e2e-widget 잡이 돌고(필수 검사 안),
// pre-commit 에는 없다. 로컬에서는 위젯, api-client 의 위젯 몫, 서버의 최종 사용자 경로를 건드렸을 때 친다. 명령은
// CLAUDE.md 의 검증 명령 절에 있다. 사진 비교의 설정(visual/playwright.config.ts)과는 따로다.
//
// 브라우저가 없으면 건너뛰지 않고 실패한다. 출처는 모두 `*.localhost` 이고 chromium 의 이름 풀기 규칙으로 루프백에
// 묶는다. 시스템의 이름 풀기가 `*.localhost` 를 IPv6 로 먼저 풀어도 중계와 사이트는 127.0.0.1 에만 선다.

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  // Vitest 의 기본 이름(*.test.*, *.spec.*)과 겹치지 않게 한다.
  testMatch: "**/*.e2e.ts",
  globalSetup: "./e2e/stack.ts",
  // 준비가 띄운 serve 하나와 위젯 하나를 사례들이 함께 쓴다. 차례로 돈다.
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  use: {
    trace: "retain-on-failure",
    launchOptions: { args: ["--host-resolver-rules=MAP *.localhost 127.0.0.1"] },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
