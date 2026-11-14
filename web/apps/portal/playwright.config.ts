// 위젯 미리보기 페이지 e2e(pilot-portal 명세 Testing Decisions "Playwright e2e", 티켓 06). 실제 serve, 같은 사이트 파일로 빌드한 실제
// 위젯 Next, 실제 위젯 미리보기 페이지, 셋을 한 출처 아래에 모으는 시험 안의 중계를 지난다. 준비는 e2e/stack.ts 다. CI 의 e2e-portal
// 잡이 돌고 pre-commit 에는 없다. 로컬에서는 위젯 미리보기 페이지, `@agent-os/e2e-stack`, 서버의 최종 사용자 경로를 건드렸을 때 친다.
// 명령은 CLAUDE.md 의 검증 명령 절에 있다.
//
// 프로젝트는 둘이다. `chromium` 은 픽스처 에이전트로 `*.e2e.ts` 를 돈다. `llm` 은 저장소의 계산 에이전트로 실제 모델을 부르는
// `*.llm.ts` 를 돈다(명세 "실제 모델 e2e 하나", 티켓 09). `llm` 은 `LLM_ENV` 가 `1` 일 때만 목록에 들고, 그 변수는 감싸는
// 파이썬 시험(`uv run --env-file .env pytest -m llm_portal`)만 준다. 그래서 프로젝트를 지정하지 않은 로컬 명령과 CI 의
// e2e-portal 은 실제 모델을 부르지 않는다. playwright.config.test.ts 가 목록을 본다.
//
// 브라우저가 없으면 건너뛰지 않고 실패한다. 출처는 모두 `*.localhost` 이고 chromium 의 이름 풀기 규칙으로 루프백에 묶는다.
// 시스템의 이름 풀기가 `*.localhost` 를 IPv6 로 먼저 풀어도 중계와 다른 페이지는 127.0.0.1 에만 선다.

import { defineConfig, devices, type Project } from "@playwright/test";
import { LLM_ENV } from "./e2e/env.ts";

// 실제 모델의 답과 계산 에이전트가 쓰는 MCP 서버(npx)를 띄우는 시간까지 든다.
const LLM_TIMEOUT_MS = 180_000;

const desktopChrome = { ...devices["Desktop Chrome"] };

// 시험 파일의 이름은 Vitest 의 기본 이름(*.test.*, *.spec.*)과 겹치지 않게 한다.
const projects: Project[] = [{ name: "chromium", testMatch: "**/*.e2e.ts", use: desktopChrome }];
if (process.env[LLM_ENV] === "1") {
  projects.push({
    name: "llm",
    testMatch: "**/*.llm.ts",
    use: desktopChrome,
    timeout: LLM_TIMEOUT_MS,
  });
}

export default defineConfig({
  testDir: "e2e",
  globalSetup: "./e2e/stack.ts",
  // 준비가 띄운 serve 하나와 위젯 미리보기 페이지 하나를 사례들이 함께 쓴다. 차례로 돈다.
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  use: {
    trace: "retain-on-failure",
    launchOptions: { args: ["--host-resolver-rules=MAP *.localhost 127.0.0.1"] },
  },
  projects,
});
