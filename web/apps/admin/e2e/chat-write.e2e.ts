// 대화를 쓰는 흐름(admin-login 티켓 11). 로그인한 운영자가 새 대화 화면에서 켜진 에이전트를 골라 요청을 보내고, 스트림으로 온
// 답이 대화에 붙고 주소가 새 실행의 대화로 바뀌는 것, 끝난 대화를 이어 가는 것, 승인 대상에서 멈춘 대화를 승인하는 것을 본다.
// 실제 serve, 실제 중계, 실제 MCP 픽스처 서버를 지난다. 모델은 부르지 않는다(픽스처 에이전트 echo 와 gated. stack.ts).

import { expect, test } from "@playwright/test";
import { stack } from "./env";
import { approvalAsk, group, row, signInTo } from "./screen";

test("새 대화에서 에이전트를 골라 보내면 답이 붙고 주소가 바뀌며 이어 가면 둘째 실행이 붙고 목록에 한 줄로 선다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  const firstText = "쓰기 흐름의 첫 요청";
  const secondText = "쓰기 흐름의 둘째 요청";
  await signInTo(page, `${adminUrl}/chat/new`);

  await page.getByLabel("에이전트", { exact: true }).selectOption("echo");
  await page.getByLabel("요청", { exact: true }).fill(firstText);
  await page.getByRole("button", { name: "보내기", exact: true }).click();

  // 답이 대화에 붙고, 주소는 새 실행의 대화로 바뀐다(주소를 바꿔도 화면은 다시 그려지지 않는다).
  const first = page.getByRole("region", { name: "실행 1", exact: true });
  await expect(first).toContainText(firstText);
  await expect(first).toContainText(`echo:${firstText}`);
  await expect(first).toContainText("끝남");
  await expect(page).not.toHaveURL(`${adminUrl}/chat/new`);
  await expect(page).toHaveURL(new RegExp(`/chat/[^/?]+$`));

  // 끝난 대화는 끝 실행에서 이어 간다.
  await page.getByLabel("요청", { exact: true }).fill(secondText);
  await page.getByRole("button", { name: "보내기", exact: true }).click();
  const second = page.getByRole("region", { name: "실행 2", exact: true });
  await expect(second).toContainText(`echo:${secondText}`);
  await expect(first).toContainText(`echo:${firstText}`);

  // 주소만 바꿔 둔 새 대화 화면에서 "새 대화"를 눌러도 이전 대화가 남지 않고 빈 새 대화가 선다.
  await page.getByRole("link", { name: "새 대화", exact: true }).click();
  await expect(page).toHaveURL(`${adminUrl}/chat/new`);
  await expect(page.getByRole("region", { name: "실행 1", exact: true })).toHaveCount(0);
  await expect(page.getByLabel("에이전트", { exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("region", { name: "실행 2", exact: true })).toContainText(
    `echo:${secondText}`,
  );

  // 대화 목록에는 두 실행이 한 줄이다.
  await page.getByRole("link", { name: "대화 목록", exact: true }).click();
  const line = row(page, "대화", firstText);
  await expect(line).toHaveCount(1);
  await expect(line).toContainText("echo");
  await expect(group(page, "대화")).not.toContainText(secondText);
  expect(crashes).toEqual([]);
});

test("새 대화로 승인 대상이 있는 에이전트에 보내면 멈춘 채로 승인 묻기가 서고 승인하면 이어서 끝난다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await signInTo(page, `${adminUrl}/chat/new`);

  await page.getByLabel("에이전트", { exact: true }).selectOption("gated");
  await page.getByLabel("요청", { exact: true }).fill("승인이 필요한 새 대화");
  await page.getByRole("button", { name: "보내기", exact: true }).click();

  // 스트림이 일시정지로 끝나면 대화 안에 승인 묻기가 선다. 그 동안 새 요청은 보낼 수 없다.
  const ask = approvalAsk(page);
  await expect(ask).toContainText("add");
  await expect(ask).toContainText('"a": 2');
  await expect(page.getByRole("button", { name: "보내기", exact: true })).toBeDisabled();

  await ask.getByRole("button", { name: "승인", exact: true }).click();
  const turn = page.getByRole("region", { name: "실행 1", exact: true });
  await expect(turn).toContainText("승인했다");
  await expect(turn).toContainText("끝남");
  await expect(turn).toContainText("도구 1개를 불렀다");
  expect(crashes).toEqual([]);
});
