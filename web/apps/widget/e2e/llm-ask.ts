// 실제 모델 e2e 의 사례들(`*.llm.ts`)이 함께 쓰는 도우미. 위젯에서 에이전트에게 질문 하나를 보내 화면에 선 출력을 읽고,
// 감싸는 파이썬 시험(tests/test_widget_llm.py)이 읽을 주석으로 싣는다.
//
// 주석은 JSON 리포트에 실린다. 설명은 JSON 글이고 `agent`(사례가 연 에이전트의 이름)와 `text`(화면에 선 출력)를 든다. 파이썬
// 시험이 에이전트 이름으로 트레이스의 실행(`run_started` 의 `agent`)과 짝짓는다. 출력을 감싼 요소 머리의 "출력: " 은 화면
// 읽기 프로그램에만 읽히는 숨긴 글이지만 그대로 싣고, 떼는 것은 견주는 규칙(tests/screen_text.py)이 한다. 화면의 글은 마크다운 부품이 그린 글이라 원문과 글자 그대로 같지
// 않다(기호가 빠지고 링크마다 "(새 탭에서 열림)" 이, 이미지 자리에 "이미지: " 가 붙는다). 견주는 규칙은 파이썬 시험이 정한다.

import { expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { stack } from "./env";
import { send } from "./helpers";

// 감싸는 파이썬 시험이 리포트에서 찾는 주석의 이름(tests/test_widget_llm.py 의 SHOWN_ANNOTATION).
const SHOWN_ANNOTATION = "화면의 출력";
const OUTPUT_PREFIX = "출력: ";
// 실제 모델의 답을 기다리는 시간. 프로젝트의 시험 제한(playwright.config.ts)보다 짧게 둔다.
const ANSWER_MS = 150_000;

/**
 * 사이트 페이지에서 `agent` 의 위젯을 열어 `question` 을 보내고, 답이 서면 그 출력 요소(숨긴 "출력: " 과 본문을 함께 감싼 요소)를 준다. 실행이 실패하면 출력 대신
 * 위험 알림이 서므로 답을 기다리는 시간을 다 쓰지 않고 실패로 알린다. 화면에 선 출력은 주석으로 싣는다.
 */
export async function askAgent(
  page: Page,
  info: TestInfo,
  agent: string,
  question: string,
): Promise<Locator> {
  await page.goto(`${stack().siteOrigin}/?agent=${agent}`);
  const frame = page.frameLocator('iframe[title="위젯"]');
  await send(frame, question);

  const conversation = frame.getByRole("region", { name: "대화" });
  // 출력은 문단이 아니라, 숨긴 "출력: " 과 마크다운 부품을 함께 감싼 요소다. 숨긴 글의 부모를 찾는다.
  const output = conversation.getByText(OUTPUT_PREFIX.trim(), { exact: true }).locator("xpath=..");
  const failed = conversation.getByRole("alert");
  await expect(output.or(failed)).toBeVisible({ timeout: ANSWER_MS });
  await expect(failed, "출력 대신 실패 알림이 섰다").toHaveCount(0);

  // 숨긴 "출력: " 까지 그대로 싣는다. 떼는 것은 견주는 규칙(tests/screen_text.py)이 한다.
  const text = (await output.textContent()) ?? "";
  info.annotations.push({ type: SHOWN_ANNOTATION, description: JSON.stringify({ agent, text }) });
  return output;
}
