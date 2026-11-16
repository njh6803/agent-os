// 단독 배포의 실제 모델 e2e(release-image 티켓 09). 프로젝트 `llm` 만 이 파일을 돈다(playwright.config.ts). 그 프로젝트는
// `AGENT_OS_STANDALONE_LLM=1` 일 때만 서고, 준비(stack.ts)가 모델 제공사의 API 키를 serve 의 환경 변수 파일에 싣는다.
//
// 이미지에 든 계산 에이전트가 이미지의 예시 MCP 서버를 네트워크 없이 띄워 도구를 쓰고, 실제 모델이 답한다. 모델이 도구를
// 부를지는 단언하지 않는다. 끝이 `finished` 인지와 트레이스에 `llm_called` 가 남았는지만 본다.

import { expect, test } from "@playwright/test";
import { signedDirectToken } from "./direct.ts";
import { Compose } from "./docker.ts";
import { CALC_AGENT, deployment, ORIGIN } from "./env.ts";

const ANSWER_MS = 150_000;
// 429 사례(deployment.e2e.ts)가 토큰 끝점의 상한을 소모했을 수 있어, 끝점이 다시 받을 때까지 기다리는 상한.
const UNTHROTTLE_MS = 90_000;

test("최종 사용자의 요청 하나에 계산 에이전트가 이미지 안의 MCP 서버와 실제 모델로 답한다", async ({
  page,
  request,
}) => {
  const { project, dir, files } = deployment();
  const compose = new Compose(project, dir, files);

  // 토큰 끝점이 429 를 내는 동안은 기다린다.
  await expect
    .poll(async () => (await request.post(`${ORIGIN}/portal/sites/calc/token`)).status(), {
      timeout: UNTHROTTLE_MS,
    })
    .not.toBe(429);

  const response = await request.post(`${ORIGIN}/end-user/runs`, {
    headers: { Authorization: `Bearer ${signedDirectToken(dir)}` },
    data: { agent: CALC_AGENT, request: "2 더하기 3은?" },
    timeout: ANSWER_MS,
  });
  expect(response.status()).toBe(200);
  const body = await response.text();
  expect(body, "실행이 실패로 끝났다").not.toContain('"type":"failed"');
  expect(body).toContain('"type":"finished"');

  const traces = await compose.inService("serve", ["sh", "-c", "cat /data/traces/*.jsonl"]);
  expect(traces).toContain('"type":"llm_called"');
  // 화면 쪽도 같은 배치로 열린다. 위젯 미리보기 페이지가 계산 사이트를 그린다.
  await page.goto(`${ORIGIN}/portal/?site=calc`);
  await expect(page.locator("agent-os-widget")).toHaveAttribute("agent", CALC_AGENT);
});
