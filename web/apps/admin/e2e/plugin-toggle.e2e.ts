// 켜고 끄기 흐름(web-admin 티켓 06). 스위치로 에이전트를 끄고 다시 켠다. 실제 serve 가 플러그인 루트의 운영자 파일에
// 쓰고, 화면은 다시 읽은 목록을 보인다. 준비는 stack.ts 다.
//
// 흐름들은 serve 하나를 차례로 함께 쓴다(playwright.config.ts). 끈 에이전트는 끝에 다시 켜서 뒤 흐름에 남기지 않는다.

import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { stack } from "./env";
import { enterAdminToken, row } from "./screen";

/** 운영자 파일이 꺼 둔 에이전트의 이름들. 파일은 종류마다 한 줄이다(준비가 쓴 것도, serve 가 쓰는 정규형도). */
function disabledAgents(pluginsRoot: string): string[] {
  const text = readFileSync(join(pluginsRoot, "disabled.toml"), "utf-8");
  const items = /^agent = \[(.*)\]$/m.exec(text)?.[1];
  if (items === undefined) {
    throw new Error(`운영자 파일에 agent 줄이 없다:\n${text}`);
  }
  return Array.from(items.matchAll(/"([^"]*)"/g), (match) => match[1] ?? "");
}

test("스위치로 에이전트를 끄면 운영자 파일에 적히고 목록이 꺼짐을 보이며 다시 켜면 켜짐을 보인다", async ({
  page,
}) => {
  const { adminUrl, adminToken, pluginsRoot } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await page.goto(adminUrl);
  await enterAdminToken(page, adminToken);
  const echo = row(page, "에이전트", "echo");
  await expect(echo).toContainText("켜짐");
  expect(disabledAgents(pluginsRoot)).toEqual([]);

  await echo.getByRole("switch").click();

  await expect(echo).toContainText("꺼짐");
  await expect(echo.getByRole("switch")).not.toBeChecked();
  expect(disabledAgents(pluginsRoot)).toEqual(["echo"]);

  // 열어 보면 서버가 읽은 꺼짐과 매니페스트가 보인다. 목록의 링크와 플러그인 하나의 라우트를 실제 Next 로 지난다.
  await echo.getByRole("link", { name: "echo" }).click();
  await expect(page).toHaveURL(`${adminUrl}/plugins/agent/echo`);
  await expect(page.getByRole("region", { name: "매니페스트" })).toContainText(
    '"entrypoint": "agent:Agent"',
  );
  await expect(page.getByRole("main")).toContainText("꺼짐");
  await page.getByRole("link", { name: "플러그인 목록으로" }).click();

  await echo.getByRole("switch").click();

  await expect(echo).toContainText("켜짐");
  await expect(echo.getByRole("switch")).toBeChecked();
  expect(disabledAgents(pluginsRoot)).toEqual([]);
  expect(crashes).toEqual([]);
});

test("이름이 패턴 밖인 표지를 열면 주소의 조각이 풀린 이름과 422 봉투의 메시지가 보인다", async ({
  page,
}) => {
  // 목록의 링크는 이름을 조각으로 적는다. 라우트가 넘기는 조각이 풀린 이름인지는 실제 Next 에서만 잰다.
  const { adminUrl, adminToken } = stack();
  await page.goto(adminUrl);
  await enterAdminToken(page, adminToken);
  const odd = row(page, "에이전트", "Old Calc");
  await expect(odd).toContainText("디렉터리 이름이 플러그인 이름의 패턴을 어긴다");

  await odd.getByRole("link", { name: "Old Calc" }).click();

  await expect(page).toHaveURL(`${adminUrl}/plugins/agent/Old%20Calc`);
  await expect(page.getByRole("heading", { level: 2, name: "Old Calc" })).toBeVisible();
  // Next 가 페이지에 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(
    page.getByRole("alert").filter({ hasText: "요청의 형식이 올바르지 않다" }),
  ).toBeVisible();
});
