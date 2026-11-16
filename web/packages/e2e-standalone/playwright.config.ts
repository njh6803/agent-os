// 단독 배포 e2e(release-image 명세 Testing Decisions, 티켓 09). 실제 이미지 넷과 프록시를 배포 파일 묶음의 compose 로 띄우고
// 실제 브라우저와 HTTP 로 지난다. 준비는 e2e/stack.ts 다. CI 의 e2e-standalone 잡이 돌고 pre-commit 에는 없다. 로컬 명령은
// CLAUDE.md 의 검증 명령 절에 있다.
//
// 프로젝트는 둘이다. `chromium` 은 모델 없이 `*.e2e.ts` 를 돈다. `llm` 은 이미지에 든 계산 에이전트로 실제 모델을 부르는
// `*.llm.ts` 를 돈다. `llm` 은 `LLM_ENV` 가 `1` 일 때만 목록에 들고, CI 의 잡은 그 변수를 주지 않는다. playwright.config.test.ts
// 가 목록을 본다.
//
// 브라우저가 없으면 건너뛰지 않고 실패한다. 출처는 `https://localhost` 이고 배치가 자체 서명 인증서를 내므로 인증서 오류를
// 무시하는 것은 시험 클라이언트의 설정이다(배치의 설정이 아니다).

import { defineConfig, devices, type Project } from "@playwright/test";
import { LLM_ENV } from "./e2e/env.ts";

// 실제 모델의 답과 계산 에이전트의 MCP 서버 시작까지 든다.
const LLM_TIMEOUT_MS = 240_000;
const DEFAULT_TIMEOUT_MS = 90_000;

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
  // 준비가 띄운 배치 하나를 사례들이 함께 쓰고, 발행 포트가 고정이라 차례로 돈다.
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  timeout: DEFAULT_TIMEOUT_MS,
  use: {
    ignoreHTTPSErrors: true,
    // 추적 파일(trace.zip)은 요청 머리를 그대로 남긴다. 관리 화면 사례가 관리 토큰을 Authorization 머리로 보내므로
    // 추적을 켜지 않는다(원칙 V: 토큰을 저장물에 싣지 않는다). 실패 진단은 compose 로그(test-results)로 한다.
    trace: "off",
  },
  projects,
});
