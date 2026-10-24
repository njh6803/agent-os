// 위젯의 실제 모델 e2e(web-widget 티켓 11). 프로젝트 `llm` 만 이 파일을 돈다(playwright.config.ts). 그 프로젝트는 감싸는
// 파이썬 시험(tests/test_widget_llm.py)이 `AGENT_OS_WIDGET_LLM=1` 을 줄 때만 서고, 준비(stack.ts)가 저장소의 플러그인
// 루트를 함께 옮겨 계산 에이전트가 실제 모델을 부른다.
//
// 모델이 도구를 부를지는 단언하지 않는다. 화면에 선 출력은 주석(annotation)으로 JSON 리포트에 싣고, 그것이 serve 가 남긴
// 트레이스의 `run_finished` 출력과 같은지는 감싸는 시험이 본다. 출력 문단 머리의 "출력: " 은 화면 읽기 프로그램에만
// 읽히는 숨긴 글이라 떼고 싣는다.

import { expect, test } from "@playwright/test";
import { stack } from "./env";
import { LLM_AGENT } from "./plugins";

// 감싸는 시험이 리포트에서 찾는 주석의 이름(tests/test_widget_llm.py 의 SHOWN_ANNOTATION).
const SHOWN_ANNOTATION = "화면의 출력";
const OUTPUT_PREFIX = "출력: ";
// 실제 모델의 답을 기다리는 시간. 프로젝트의 시험 제한(playwright.config.ts)보다 짧게 둔다.
const ANSWER_MS = 150_000;

test("계산 에이전트가 위젯에서 보낸 요청 하나에 실제 모델로 답한다", async ({ page }) => {
  await page.goto(`${stack().siteOrigin}/?agent=${LLM_AGENT}`);
  const frame = page.frameLocator('iframe[title="위젯"]');
  await frame.getByRole("textbox", { name: "요청" }).fill("2 더하기 3은?");
  await frame.getByRole("button", { name: "보내기" }).click();

  const conversation = frame.getByRole("region", { name: "대화" });
  const output = conversation.getByRole("paragraph").filter({ hasText: OUTPUT_PREFIX });
  const failed = conversation.getByRole("alert");
  // 실행이 실패하면 출력 대신 위험 알림이 선다. 그때는 답을 기다리는 시간을 다 쓰지 않는다.
  await expect(output.or(failed)).toBeVisible({ timeout: ANSWER_MS });
  await expect(failed, "출력 대신 실패 알림이 섰다").toHaveCount(0);

  const shown = (await output.textContent()) ?? "";
  test.info().annotations.push({
    type: SHOWN_ANNOTATION,
    description: shown.startsWith(OUTPUT_PREFIX) ? shown.slice(OUTPUT_PREFIX.length) : shown,
  });
});
