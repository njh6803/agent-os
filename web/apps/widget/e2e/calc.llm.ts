// 위젯의 실제 모델 e2e(web-widget 티켓 11). 프로젝트 `llm` 만 이 파일을 돈다(playwright.config.ts). 그 프로젝트는 감싸는
// 파이썬 시험(tests/test_widget_llm.py)이 `AGENT_OS_WIDGET_LLM=1` 을 줄 때만 서고, 준비(stack.ts)가 저장소의 플러그인
// 루트를 함께 옮겨 계산 에이전트가 실제 모델을 부른다.
//
// 모델이 도구를 부를지는 단언하지 않는다. 화면에 선 출력은 주석(`llm-ask.ts`)으로 JSON 리포트에 싣고, 그것이 serve 가 남긴
// 트레이스의 `run_finished` 출력과 같은지는 감싸는 시험이 본다.

import { LLM_AGENT } from "@agent-os/e2e-stack";
import { test } from "@playwright/test";
import { askAgent } from "./llm-ask";

test("계산 에이전트가 위젯에서 보낸 요청 하나에 실제 모델로 답한다", async ({ page }, info) => {
  await askAgent(page, info, LLM_AGENT, "2 더하기 3은?");
});
