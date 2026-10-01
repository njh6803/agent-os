// 관리 화면의 e2e(web-admin 명세 "e2e", ADR 0021 이력). 실제 serve 와 실제 중계를 지난다. 준비는 e2e/stack.ts 다.
// CI 의 e2e 잡이 돌고(필수 검사 안), pre-commit 에는 없다. 로컬에서는 중계, 시작 래퍼, api-client, 서버 라우트를
// 건드렸을 때 친다. 명령은 CLAUDE.md 의 검증 명령 절에 있다.
//
// 브라우저가 없으면 건너뛰지 않고 실패한다. Playwright 가 브라우저를 찾지 못하면 테스트가 에러로 끝난다.

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  // Vitest 의 기본 이름(*.test.*, *.spec.*)과 겹치지 않게 한다.
  testMatch: "**/*.e2e.ts",
  globalSetup: "./e2e/stack.ts",
  // 준비가 띄운 serve 하나와 관리 화면 하나를 흐름들이 함께 쓴다. 흐름이 서로의 상태(켜짐, 트레이스)를 건드리므로
  // 차례로 돈다.
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  use: { trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
