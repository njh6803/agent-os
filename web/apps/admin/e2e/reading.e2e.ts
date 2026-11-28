// 읽기 흐름의 셋째 조각(web-admin 티켓 07, admin-login 티켓 11). 옛 실행 화면의 주소(`/runs`, `/runs/<id>`)가 대화 화면으로
// 옮겨 가는 것과, 준비가 쓴 트레이스(traces.ts)를 대화 화면과 실행 패널에서 읽는 것을 본다. 실패한 실행의 "다시 보내기"는
// 실제 serve 가 새 실행을 만드는 데까지 본다. 트레이스의 HTML 이 요소로 그려지지 않는 것을 실제 브라우저에서 한 번 더 본다.

import { expect, test } from "@playwright/test";
import { stack } from "./env";
import { signInTo } from "./screen";
import { HOSTILE_CONTENT, READ_RUNS, UNKNOWN_LINE } from "./traces";

test("옛 주소 /runs 는 대화 목록으로, /runs/<id> 는 그 대화와 열린 패널로 옮겨 간다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  await signInTo(page, `${adminUrl}/runs`);
  await expect(page).toHaveURL(`${adminUrl}/chat`);
  await expect(page.getByRole("heading", { level: 1, name: "대화" })).toBeVisible();

  await page.goto(`${adminUrl}/runs/${READ_RUNS.finished}`);
  await expect(page).toHaveURL(`${adminUrl}/chat/${READ_RUNS.finished}?run=${READ_RUNS.finished}`);
  await expect(page.getByRole("complementary", { name: "실행 패널" })).toContainText(
    READ_RUNS.finished,
  );
});

test("트레이스의 HTML 은 글자로만 그려지고 모르는 종류의 줄은 원문으로 보이며 끝맺지 못한 실행이 알려진다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await signInTo(page, `${adminUrl}/chat/${READ_RUNS.finished}?run=${READ_RUNS.finished}`);

  const panel = page.getByRole("complementary", { name: "실행 패널" });
  await expect(panel).toContainText(HOSTILE_CONTENT);
  await expect(page.locator("img")).toHaveCount(0);
  expect(await page.evaluate(() => Reflect.has(window, "__agentOsXss"))).toBe(false);
  await expect(page.getByRole("region", { name: "실행 1", exact: true })).toContainText("끝났다");

  // 이 런타임이 모르는 종류의 줄은 원문이 그대로 보이고, 결말이 없는 채 오래된 실행은 끝맺지 못한 것으로 알린다.
  await page.goto(`${adminUrl}/chat/${READ_RUNS.unknown}?run=${READ_RUNS.unknown}`);
  await expect(page.getByRole("complementary", { name: "실행 패널" })).toContainText(UNKNOWN_LINE);
  await expect(page.getByRole("region", { name: "실행 1", exact: true })).toContainText(
    "끝맺지 못한 것으로 보입니다",
  );
  expect(crashes).toEqual([]);
});

test("실패한 실행에서 다시 보내기를 누르면 같은 요청이 새 실행으로 이어지고 echo 가 답한다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await signInTo(page, `${adminUrl}/chat/${READ_RUNS.failed}`);

  const first = page.getByRole("region", { name: "실행 1", exact: true });
  await expect(first).toContainText("도구 연결이 끊겼다");
  await expect(first).toContainText("실패");
  await first.getByRole("button", { name: "다시 보내기" }).click();

  // 앞 실행이 없는 실패라 같은 에이전트의 새 대화로 같은 요청을 다시 보낸다. 준비가 쓴 실패 트레이스의 에이전트가 echo 이고
  // 요청은 `<실행 식별자> 의 요청` 이다. 주소는 새 실행의 대화로 바뀐다.
  await expect(page.getByText(`echo:${READ_RUNS.failed} 의 요청`)).toBeVisible();
  await expect(page).not.toHaveURL(`${adminUrl}/chat/${READ_RUNS.failed}`);
  expect(crashes).toEqual([]);
});
