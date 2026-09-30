// 읽기 흐름의 둘째 조각(web-admin 티켓 07). 05 의 흐름(관리 토큰, 플러그인 목록)에서 이어 실행 목록을 보고 거르고,
// 실행 하나를 열어 모르는 종류의 원문과 형식 1 의 표시를 본다. 트레이스의 HTML 이 요소로 그려지지 않는 것을 실제
// 브라우저에서 한 번 더 본다. 트레이스는 준비가 쓴다(traces.ts).

import { expect, type Page, test } from "@playwright/test";
import { stack } from "./env";
import { enterAdminToken, group, row } from "./screen";
import { HOSTILE_CONTENT, READ_RUNS, UNKNOWN_LINE } from "./traces";

function runRow(page: Page, runId: string) {
  return row(page, "실행", runId);
}

/** 목록에서 실행 하나를 열고, 트레이스를 읽을 때까지 기다린다. 이벤트를 든 자리를 돌려준다. */
async function openRun(page: Page, adminUrl: string, runId: string) {
  await runRow(page, runId).getByRole("link", { name: runId }).click();
  await expect(page).toHaveURL(`${adminUrl}/runs/${runId}`);
  const events = page.getByRole("region", { name: "이벤트" });
  await expect(events).toBeVisible();
  return events;
}

test("실행 목록을 상태로 거르고 실행 하나를 열어 모르는 종류의 원문과 형식 1 과 글자로만 그린 HTML 을 본다", async ({
  page,
}) => {
  const { adminUrl, adminToken } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await page.goto(adminUrl);
  await enterAdminToken(page, adminToken);
  await expect(row(page, "에이전트", "echo")).toContainText("켜짐");

  await page.getByRole("navigation").getByRole("link", { name: "실행 목록", exact: true }).click();

  await expect(page).toHaveURL(`${adminUrl}/runs`);
  await expect(runRow(page, READ_RUNS.finished)).toContainText("끝남");
  await expect(runRow(page, READ_RUNS.failed)).toContainText("실패");
  await expect(runRow(page, READ_RUNS.formatOne)).toContainText("끝남");
  await expect(runRow(page, READ_RUNS.unknown)).toContainText("결말 없음");
  await expect(runRow(page, READ_RUNS.unreadable)).toContainText("읽을 수 없는 트레이스");
  await expect(group(page, "실행")).not.toContainText("실행 중");

  // 거르기가 실제 serve 의 질의까지 간다. 거르면 새 목록을 읽는 동안 자리표시가 서서, 없어야 할 행의 단언은 그 빈 틈에서도
  // 통과한다. 거른 목록이 선 것을 먼저 보고 없어야 할 행을 본다.
  await page.getByRole("radio", { name: "실패", exact: true }).check();
  await expect(runRow(page, READ_RUNS.failed)).toContainText("실패");
  await expect(runRow(page, READ_RUNS.finished)).toHaveCount(0);
  await page.getByRole("radio", { name: "전부", exact: true }).check();

  const unknown = await openRun(page, adminUrl, READ_RUNS.unknown);
  await expect(unknown).toContainText(UNKNOWN_LINE);
  await page.getByRole("link", { name: "실행 목록으로" }).click();

  await openRun(page, adminUrl, READ_RUNS.formatOne);
  await expect(page.getByRole("main")).toContainText("읽을 수 있지만 재개할 수 없다");
  await page.getByRole("link", { name: "실행 목록으로" }).click();

  const finished = await openRun(page, adminUrl, READ_RUNS.finished);
  await expect(finished).toContainText(HOSTILE_CONTENT);
  await expect(page.locator("img")).toHaveCount(0);
  expect(await page.evaluate(() => Reflect.has(window, "__agentOsXss"))).toBe(false);
  expect(crashes).toEqual([]);
});
