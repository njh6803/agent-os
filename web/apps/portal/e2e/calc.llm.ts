// 위젯 미리보기 페이지의 실제 모델 e2e(pilot-portal 티켓 09). 프로젝트 `llm` 만 이 파일을 돈다(playwright.config.ts). 그 프로젝트는
// 감싸는 파이썬 시험(tests/test_portal_llm.py)이 `AGENT_OS_PORTAL_LLM=1` 을 줄 때만 서고, 준비(stack.ts)가 저장소의 플러그인
// 루트를 함께 옮겨 첫 사이트의 계산 에이전트가 실제 모델을 부른다.
//
// 처음 온 브라우저가 `?site=` 없이 위젯 미리보기 페이지를 열어(첫 사이트) 덮개에서 확인하고 요청 하나를 보낸다. 모델이 도구를 부를지는
// 단언하지 않는다. 화면에 선 출력은 주석(annotation)으로 JSON 리포트에 싣고, 그것이 serve 가 남긴 트레이스의 `run_finished`
// 출력에서 온 글인지(기호를 뗀 글이 원문의 부분열인지)와 `llm_called` 가 있는지는 감싸는 시험이 본다. 실행 주체의 `anon-`
// 접두는 여기서 본다. 출력 요소 머리의 "출력: " 은 화면 읽기 프로그램에만 읽히는 숨긴 글이지만 그대로 싣고, 떼는 것은 견주는
// 규칙(tests/screen_text.py)이 한다.

import { startedRuns } from "@agent-os/e2e-stack";
import { expect, test } from "@playwright/test";
import { stack, traces } from "./env.ts";
import { SITES } from "./sites.ts";

const [FIRST] = SITES;
if (FIRST === undefined) {
  throw new Error("e2e 사이트 목록이 비었다");
}

// 감싸는 시험이 리포트에서 찾는 주석의 이름(tests/test_portal_llm.py 의 SHOWN_ANNOTATION).
const SHOWN_ANNOTATION = "화면의 출력";
const OUTPUT_PREFIX = "출력: ";
const REQUEST = "2 더하기 3은?";
// 실제 모델의 답을 기다리는 시간. 프로젝트의 시험 제한(playwright.config.ts)보다 짧게 둔다.
const ANSWER_MS = 150_000;

test("첫 사이트에서 고지를 확인한 최종 사용자의 요청 하나에 계산 에이전트가 실제 모델로 답한다", async ({
  page,
}) => {
  await page.goto(`${stack().portalOrigin}/portal/`);
  await page
    .getByRole("region", { name: "질문하기 전에 읽어 주세요" })
    .getByRole("button", { name: "확인하고 질문하기" })
    .click();
  await page.getByRole("textbox", { name: "질문" }).fill(REQUEST);
  await page.getByRole("button", { name: "보내기" }).click();

  const conversation = page.getByRole("region", { name: "대화" });
  // 출력은 문단이 아니라, 숨긴 "출력: " 과 마크다운 부품을 함께 감싼 요소다. 숨긴 글의 부모를 찾는다.
  const output = conversation.getByText(OUTPUT_PREFIX.trim(), { exact: true }).locator("xpath=..");
  const failed = conversation.getByRole("alert");
  // 실행이 실패하면 출력 대신 위험 알림이 선다. 그때는 답을 기다리는 시간을 다 쓰지 않는다.
  await expect(output.or(failed)).toBeVisible({ timeout: ANSWER_MS });
  await expect(failed, "출력 대신 실패 알림이 섰다").toHaveCount(0);

  // 숨긴 "출력: " 까지 그대로 싣는다. 떼는 것은 견주는 규칙(tests/screen_text.py)이 한다.
  test.info().annotations.push({
    type: SHOWN_ANNOTATION,
    description: (await output.textContent()) ?? "",
  });

  const runs = startedRuns(traces()).filter((run) => run.request === REQUEST);
  expect(runs.map((run) => run.agent)).toEqual(["calc"]);
  // 주체는 `발급자|sub` 이고 익명 최종 사용자의 sub 는 `anon-` 에 쿠키 값의 해시 앞 32자리가 붙은 이름이다.
  const [issuer, subject = ""] = (runs[0]?.principal ?? "").split("|");
  expect(issuer).toBe(FIRST.issuer);
  expect(subject).toMatch(/^anon-[0-9a-f]{32}$/u);
});
